# Why No Local Episodes Directory?

You might notice that the Mortis dataset infrastructure doesn't create a local `episodes/` directory. This is intentional and by design.

## How LeRobot Works

When you run `lerobot-record`, it:

1. **Records episodes** using your robot and cameras
2. **Stores temporarily** in LeRobot's cache (usually `~/.cache/lerobot/`)
3. **Uploads directly** to Hugging Face Hub
4. **Cleans up** temporary files after upload

## Why Cloud-First?

### ✅ Advantages

**No Local Storage Issues**
- Robot demonstrations can be 10-50 GB per task
- No need for large local disk space
- No risk of running out of space mid-recording

**Automatic Backup**
- Data is safe in the cloud immediately
- No risk of losing data if your machine crashes
- Version controlled by Hugging Face

**Easy Sharing**
- Share datasets with team members instantly
- Access from any machine
- No need to transfer large files manually

**Training Flexibility**
- Train on different machines (e.g., cloud GPU)
- Download only what you need
- LeRobot handles caching automatically

### ❌ What You Lose

**Offline Access**
- Need internet to record (for upload)
- Need internet to train (for download)
- Can't work completely offline

**Privacy**
- Data is uploaded to Hugging Face
- Can make datasets private, but still cloud-hosted
- Not suitable for highly sensitive data

## What We DO Store Locally

```
data/mortis_manipulation/
├── metadata/
│   ├── dataset_info.json    # Task definitions
│   └── dataset_summary.txt  # Human-readable summary
└── scripts/
    ├── record_task_0.sh     # Recording scripts
    └── ...
```

**Why these?**
- **metadata/**: Lightweight task definitions and configuration
- **scripts/**: Generated helper scripts for convenience
- Both are small (< 1 MB) and useful for reference

## Where Is My Data?

Your recorded episodes live at:
```
https://huggingface.co/datasets/{HF_USER}/mortis_manipulation
```

You can:
- View episodes in the browser
- Download specific episodes
- Share the dataset URL
- Manage privacy settings

## How to Access Episode Data

### For Training

LeRobot automatically downloads and caches data:

```python
from lerobot.common.datasets.lerobot_dataset import LeRobot Dataset

# Downloads from HF Hub automatically
dataset = LeRobotDataset("your-username/mortis_manipulation")

# Data is cached locally in ~/.cache/lerobot/
# Subsequent loads are fast
```

### For Inspection

Download specific episodes:

```python
from huggingface_hub import hf_hub_download

# Download a specific file
file_path = hf_hub_download(
    repo_id="your-username/mortis_manipulation",
    filename="episode_000000/observation.images.camera1/frame_000000.png",
    repo_type="dataset"
)
```

### For Backup

Clone the entire dataset:

```bash
# Clone with git-lfs
git lfs install
git clone https://huggingface.co/datasets/your-username/mortis_manipulation
```

## Alternative: Local-First Approach

If you REALLY need local storage, you can:

1. **Disable auto-upload** in lerobot-record (check LeRobot docs)
2. **Store episodes locally** in a custom directory
3. **Upload manually** when ready

But this is NOT recommended for Mortis because:
- More complex workflow
- Risk of data loss
- Harder to share and collaborate
- No automatic backup

## Summary

**The Mortis approach:**
- ✅ Simple: Just run the scripts
- ✅ Safe: Data backed up immediately
- ✅ Shareable: Easy collaboration
- ✅ Flexible: Train anywhere

**Local episodes/ directory:**
- ❌ Not needed: LeRobot handles it
- ❌ Wastes space: Large files
- ❌ Adds complexity: Manual management
- ❌ Risk: No automatic backup

## Questions?

**Q: What if I lose internet during recording?**
A: The episode will fail to upload. You'll need to re-record it.

**Q: Can I record offline and upload later?**
A: Not with the default setup. Check LeRobot docs for offline mode.

**Q: How much does Hugging Face storage cost?**
A: Free tier includes generous storage. Check https://huggingface.co/pricing

**Q: Can I delete episodes from Hugging Face?**
A: Yes, you can manage your dataset through the web interface.

**Q: What if Hugging Face is down?**
A: You can't record or train until it's back up. This is rare.

## Related Documentation

- [RECORDING_GUIDE.md](RECORDING_GUIDE.md) - How to record episodes
- [HUGGINGFACE_SETUP.md](HUGGINGFACE_SETUP.md) - Authentication setup
- [LeRobot Documentation](https://github.com/huggingface/lerobot) - Official docs
