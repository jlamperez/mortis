# Training Scripts

This directory contains generated training scripts for SmolVLA models.

## Generated Scripts

### Quick Test Training
```bash
./train_quick.sh
```
- 1,000 steps
- Batch size: 8
- For testing configuration

### Standard Training
```bash
./train_standard.sh
```
- 20,000 steps
- Batch size: 16
- Recommended for most use cases

### Full Training
```bash
./train_full.sh
```
- 100,000 steps
- Batch size: 16
- For production models

## Configuration

All scripts use:
- **Policy**: `lerobot/smolvla_base`
- **Device**: CUDA with automatic mixed precision
- **Memory optimization**: `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`
- **Image transforms**: Enabled for data augmentation
- **Checkpoints**: Saved periodically
- **Evaluation**: Run periodically during training
- **Logging**: Weights & Biases (if configured)

## Training Outputs

Training outputs (checkpoints, logs, metrics) are saved to:
```
outputs/train/<job_name>/
├── checkpoints/
│   ├── last/
│   └── <step>/
├── logs/
└── wandb/
```

## Monitoring Training

### Console Output
Watch the terminal for:
- Training loss
- Evaluation metrics
- Checkpoint saves
- GPU memory usage

### Weights & Biases
If W&B is enabled:
1. Visit https://wandb.ai
2. Navigate to your project
3. View real-time metrics and system stats

### Checkpoints
Saved models are stored in:
```
outputs/train/<job_name>/checkpoints/
```

## Resuming Training

To resume from a checkpoint, edit the training script and add:
```bash
--resume=true
```

Or specify a specific checkpoint:
```bash
--resume_from=outputs/train/<job_name>/checkpoints/last/pretrained_model.safetensors
```

## Customizing Training

To modify training parameters:

1. Edit the generated script directly, or
2. Generate a new script with custom parameters:
   ```bash
   uv run setup-train \
       --dataset-repo-id your/dataset \
       --batch-size 8 \
       --steps 50000
   ```

## Generating New Scripts

To regenerate or create new training scripts:

```bash
# From project root
make setup-train ARGS="--dataset-repo-id user/dataset --model-repo-id user/model --generate-configs"

# Or directly
uv run setup-train \
    --dataset-repo-id user/dataset \
    --model-repo-id user/model \
    --job-name my_training \
    --generate-configs
```

## Troubleshooting

### CUDA Out of Memory
- Reduce `--batch_size` (try 8 or 4)
- Close other GPU applications
- Check GPU memory: `nvidia-smi`

### Training Not Starting
- Verify dataset exists: `huggingface-cli repo info dataset-repo-id`
- Check CUDA availability: `nvidia-smi`
- Verify LeRobot installation: `uv run python -c "import lerobot; print(lerobot.__version__)"`

### Slow Training
- Increase `--num_workers` for data loading
- Use SSD for dataset storage
- Check GPU utilization: `watch -n 1 nvidia-smi`

## Additional Resources

- [Training Guide](../docs/TRAINING_GUIDE.md)
- [LeRobot Documentation](https://github.com/huggingface/lerobot)
- [SmolVLA Paper](https://arxiv.org/abs/2409.15041)
