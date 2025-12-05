# SmolVLA Training Guide

This guide explains how to train the SmolVLA vision-language-action model for Mortis manipulation tasks.

## Overview

The `setup-train` command generates training scripts using the native `lerobot-train` command with optimized configurations for SmolVLA models.

### Features

- Generates ready-to-use training scripts with `lerobot-train`
- Uses LeRobot's battle-tested training pipeline
- Configurable training hyperparameters
- Automatic checkpoint saving and resumption
- Training progress logging with Weights & Biases integration
- GPU acceleration with CUDA support and memory optimization
- Multiple training configurations (quick, standard, full)

## Prerequisites

### Hardware Requirements

- **Minimum**: NVIDIA GPU with 8GB VRAM
- **Recommended**: NVIDIA GPU with 16GB+ VRAM (e.g., RTX 3090, RTX 4090)
- CPU: 4+ cores
- RAM: 16GB+
- Storage: 50GB+ for models and datasets

### Software Requirements

- Python 3.12+
- PyTorch with CUDA support
- LeRobot with SmolVLA support
- Dataset on Hugging Face Hub or local

All dependencies are managed through `uv` and specified in `pyproject.toml`.

## Quick Start

### 1. Collect Dataset

First, collect demonstration data for the manipulation tasks:

```bash
# Setup dataset infrastructure
make setup-dataset

# Record episodes using LeRobot
# See data_collector.py for generated scripts
```

### 2. Generate Training Scripts

Generate training scripts for your dataset:

```bash
# Basic usage
make setup-train ARGS="--dataset-repo-id username/dataset-name"

# With model repository for pushing trained model
uv run setup-train \
    --dataset-repo-id username/dataset-name \
    --model-repo-id username/model-name \
    --job-name my_training_job

# Generate multiple configurations (quick, standard, full)
uv run setup-train \
    --dataset-repo-id username/dataset-name \
    --generate-configs
```

### 3. Start Training

Run the generated training script:

```bash
# Navigate to training scripts directory
cd train

# Run standard training (20k steps)
./train_standard.sh

# Or quick test (1k steps)
./train_quick.sh

# Or full training (100k steps)
./train_full.sh
```

Training outputs (checkpoints, logs) will be saved to `outputs/train/<job_name>/`

## Training Configuration

### Using setup-train (Recommended)

The `setup-train` command generates training scripts with optimized configurations:

```bash
# Basic usage
uv run setup-train --dataset-repo-id username/dataset-name

# Custom configuration
uv run setup-train \
    --dataset-repo-id username/dataset-name \
    --model-repo-id username/model-name \
    --job-name my_training \
    --batch-size 16 \
    --steps 20000 \
    --output-dir outputs/train

# Generate multiple configurations
uv run setup-train \
    --dataset-repo-id username/dataset-name \
    --generate-configs
```

### Available Options

- `--dataset-repo-id`: (Required) Hugging Face dataset repository ID
- `--model-repo-id`: Hugging Face model repository for pushing trained model
- `--job-name`: Name for the training job (default: derived from dataset)
- `--batch-size`: Training batch size (default: 16)
- `--steps`: Total training steps (default: 20000)
- `--policy-path`: Base policy path (default: lerobot/smolvla_base)
- `--output-dir`: Output directory (default: outputs/train)
- `--no-wandb`: Disable Weights & Biases logging
- `--generate-configs`: Generate quick/standard/full configurations

### Manual Training with lerobot-train

You can also manually run `lerobot-train` with custom parameters:

```bash
PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
lerobot-train \
  --policy.path=lerobot/smolvla_base \
  --dataset.repo_id=username/dataset-name \
  --dataset.image_transforms.enable=true \
  --policy.device=cuda \
  --policy.use_amp=true \
  --policy.n_action_steps=50 \
  --policy.chunk_size=50 \
  --batch_size=16 \
  --steps=20000 \
  --save_checkpoint=true \
  --save_freq=5000 \
  --eval_freq=5000 \
  --wandb.enable=true \
  --output_dir=outputs/train/my_job \
  --job_name=my_job \
  --policy.repo_id=username/model-name \
  --rename_map='{"observation.images.camera1": "observation.images.camera1", "observation.images.camera2": "observation.images.camera2"}'
```



## Monitoring Training

### Weights & Biases Integration

The training script integrates with Weights & Biases for comprehensive monitoring:

1. **Setup W&B**:
   ```bash
   # Add WANDB_API_KEY to .env
   echo "WANDB_API_KEY=your_api_key" >> .env
   ```

2. **View Training**:
   - Visit https://wandb.ai
   - Navigate to your project (default: `mortis-smolvla`)
   - View real-time metrics, loss curves, and system stats

3. **Logged Metrics**:
   - Training loss
   - Evaluation loss
   - Learning rate
   - Training step and epoch
   - GPU memory usage
   - System metrics

### Console Logging

Training progress is also logged to the console:

```
Step 100/100000 | Epoch 1 | Loss: 0.1234 | LR: 1.00e-04
Step 200/100000 | Epoch 1 | Loss: 0.1123 | LR: 1.00e-04
...
💾 Checkpoint saved: checkpoints/checkpoint_step_10000.pt
📊 Running evaluation at step 10000...
   Eval Loss: 0.0987
```

## Generated Training Scripts

When you run `setup-train --generate-configs`, three training scripts are created in the `train/` directory:

### train_quick.sh
- **Purpose**: Quick test to verify setup
- **Steps**: 1,000
- **Batch size**: 8
- **Save/Eval frequency**: 500 steps
- **Use case**: Testing configuration before full training

### train_standard.sh
- **Purpose**: Standard training run
- **Steps**: 20,000
- **Batch size**: 16
- **Save/Eval frequency**: 5,000 steps
- **Use case**: Most common training scenario

### train_full.sh
- **Purpose**: Full training for best performance
- **Steps**: 100,000
- **Batch size**: 16
- **Save/Eval frequency**: 10,000 steps
- **Use case**: Production model training

All scripts include:
- CUDA memory optimization (`PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`)
- Automatic mixed precision training (`--policy.use_amp=true`)
- Image transformations for data augmentation
- Checkpoint saving and evaluation
- Weights & Biases logging

### Directory Structure

```
train/                          # Training scripts (generated)
├── train_quick.sh
├── train_standard.sh
└── train_full.sh

outputs/train/                  # Training outputs
└── <job_name>/
    ├── checkpoints/           # Saved model checkpoints
    ├── logs/                  # Training logs
    └── wandb/                 # W&B logs (if enabled)
```

## Checkpoints

### Automatic Saving

Checkpoints are automatically saved:

- Every `save_freq` steps (default: 10,000)
- As `checkpoint_step_N.pt` where N is the step number
- As `last_model.pt` (always the most recent checkpoint)
- As `final_model.pt` when training completes

### Checkpoint Contents

Each checkpoint contains:

```python
{
    "step": 10000,
    "epoch": 5,
    "model_state_dict": {...},
    "optimizer_state_dict": {...},
    "scheduler_state_dict": {...},
    "loss": 0.1234,
    "config": {...}
}
```

### Resuming Training

Resume from any checkpoint by editing the training script and adding:

```bash
--resume=true
```

Or specify a specific checkpoint:

```bash
--resume_from=outputs/train/<job_name>/checkpoints/last/pretrained_model.safetensors
```

## Training Interruption

If training is interrupted (Ctrl+C), LeRobot automatically saves checkpoints. To resume:

1. Edit your training script
2. Add `--resume=true` to the lerobot-train command
3. Run the script again

## Hyperparameter Tuning

### Recommended Starting Points

```yaml
batch_size: 8-16          # Adjust based on GPU memory
learning_rate: 1e-4       # Standard for vision-language models
num_steps: 100000         # ~100k steps for convergence
warmup_steps: 1000        # 1% of total steps
gradient_clip_norm: 10.0  # Prevent gradient explosion
```

### GPU Memory Optimization

If you encounter out-of-memory errors:

1. **Reduce batch size**: Edit the training script and change `--batch_size=16` to `--batch_size=8` or `--batch_size=4`
2. **Use gradient accumulation**: Add `--gradient_accumulation_steps=2` to the lerobot-train command
3. **Reduce image resolution**: Modify dataset configuration
4. **Mixed precision is already enabled**: The scripts use `--policy.use_amp=true`

### Learning Rate Schedule

The training script uses:

1. **Linear warmup**: 0.1x → 1.0x over `warmup_steps`
2. **Cosine annealing**: 1.0x → 0.1x over remaining steps

## Troubleshooting

### Dataset Not Found

```
❌ Failed to validate dataset: Dataset not found
```

**Solution**: Ensure dataset exists on Hugging Face Hub or locally:
```bash
# Check dataset
huggingface-cli repo info username/dataset-name

# Or verify local path
ls -la data/mortis_manipulation/
```

### CUDA Out of Memory

```
torch.cuda.OutOfMemoryError: CUDA out of memory
```

**Solution**: Edit the training script and reduce batch size:
```bash
# Change --batch_size=16 to --batch_size=4
# Then run the script again
./train_standard.sh
```

### W&B Not Logging

```
⚠️  WANDB_API_KEY not found in environment
```

**Solution**: Add API key to `.env`:
```bash
echo "WANDB_API_KEY=your_key" >> .env
```

### Slow Training

**Possible causes**:
- CPU bottleneck in data loading → Increase `--num-workers`
- Slow disk I/O → Use SSD for dataset storage
- Network latency → Download dataset locally first

## Best Practices

### 1. Start Small

Begin with a small experiment to verify everything works:

```bash
# Use the quick training script
cd train
./train_quick.sh
```

### 2. Monitor Early Training

Watch the first few hundred steps closely:

- Loss should decrease steadily
- Learning rate should increase during warmup
- No NaN or Inf values

### 3. Use Checkpoints

Checkpoints are automatically saved at the frequency specified in the training script (default: every 5,000 steps for standard training, 10,000 for full training).

### 4. Track Experiments

Use descriptive job names when generating training scripts:

```bash
uv run setup-train \
    --dataset-repo-id username/dataset \
    --job-name "smolvla-bs16-20k-v2"
```

### 5. Validate Dataset Quality

Before training, ensure:

- Sufficient episodes per task (5-10 minimum)
- Clear, well-lit images
- Smooth, consistent demonstrations
- Proper task labels

## Complete Workflow Example

Here's a complete example from dataset collection to training:

```bash
# 1. Setup dataset infrastructure
make setup-dataset
# Follow prompts to configure dataset

# 2. Record demonstrations
cd data/mortis_manipulation/scripts
./record_task_0.sh  # Record first task
./record_task_1.sh  # Record second task
# ... continue for all tasks

# 3. Verify dataset on Hugging Face
# Visit https://huggingface.co/datasets/username/dataset-name

# 4. Generate training scripts
uv run setup-train \
    --dataset-repo-id username/mortis_manipulation \
    --model-repo-id username/mortis-smolvla \
    --generate-configs

# 5. Start training
cd train
./train_standard.sh

# 6. Monitor training
# - Watch console output
# - Visit https://wandb.ai for metrics
# - Check outputs/train/smolvla_*/checkpoints/ for saved models

# 7. Use trained model
# The model will be automatically pushed to HuggingFace if --model-repo-id was specified
```

## Next Steps

After training completes:

1. **Evaluate Model**: Test on validation tasks
2. **Deploy Model**: Use in SmolVLA executor
3. **Fine-tune**: Adjust hyperparameters if needed
4. **Collect More Data**: Improve performance with additional demonstrations

## Additional Resources

- [LeRobot Documentation](https://github.com/huggingface/lerobot)
- [SmolVLA Paper](https://arxiv.org/abs/2409.15041)
- [Weights & Biases Docs](https://docs.wandb.ai)
- [PyTorch Training Guide](https://pytorch.org/tutorials/beginner/basics/optimization_tutorial.html)

## Support

For issues or questions:

1. Check the [troubleshooting section](#troubleshooting)
2. Review training logs in `logs/` directory
3. Check W&B dashboard for metrics
4. Consult LeRobot documentation
