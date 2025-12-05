# SmolVLA Executor Guide

This guide explains how to use the SmolVLA executor for vision-language-action robotic manipulation tasks in the Mortis system.

## Overview

The SmolVLA executor (`src/mortis/smolvla_executor.py`) provides an interface for running trained SmolVLA models to perform precise manipulation tasks. It handles:

- Loading trained model checkpoints
- Capturing visual observations from cameras
- Running inference to predict robot actions
- Executing actions on the SO101 robotic arm
- Error handling and safety mechanisms

## Prerequisites

1. **Trained SmolVLA Model**: You need a trained model checkpoint (see training documentation)
2. **GPU (Recommended)**: CUDA-capable GPU with 8GB+ VRAM for inference
3. **Robot Hardware**: Connected SO101 robotic arm
4. **Camera**: Camera for visual observations (to be implemented)

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Path to trained SmolVLA model checkpoint
SMOLVLA_CHECKPOINT_PATH=checkpoints/smolvla_best

# Device to run inference on (optional, auto-detects if not set)
SMOLVLA_DEVICE=cuda  # or 'cpu'
```

### Checkpoint Structure

Your checkpoint directory should contain:
- `config.json` - Model configuration
- `model.safetensors` or `pytorch_model.bin` - Model weights
- Other model files as saved by LeRobot training

## Usage

### Basic Usage

```python
from mortis.smolvla_executor import init_smolvla_executor
from mortis.robot import MortisArm

# Initialize robot
robot_arm = MortisArm()
robot_arm.connect()

# Initialize SmolVLA executor
executor = init_smolvla_executor(
    checkpoint_path="checkpoints/smolvla_best",
    robot_arm=robot_arm,
    device="cuda"  # or None for auto-detect
)

# Execute a manipulation task
command = "Pick up the skull and place it in the green cup"
success = executor.execute(command, max_steps=500)

if success:
    print("Task completed successfully!")
else:
    print("Task did not complete")

# Cleanup
executor.cleanup()
robot_arm.disconnect()
```

### Using Environment Variables

```python
import os
from mortis.smolvla_executor import init_smolvla_executor

# Set environment variable
os.environ["SMOLVLA_CHECKPOINT_PATH"] = "checkpoints/smolvla_best"

# Initialize (will use env var)
executor = init_smolvla_executor()

# Execute task
executor.execute("Pick up the eyeball and place it in the orange cup")
```

### Valid Commands

The executor validates commands against the trained task set. Currently supported commands:

1. "Pick up the skull and place it in the green cup"
2. "Pick up the skull and place it in the orange cup"
3. "Pick up the skull and place it in the purple cup"
4. "Pick up the eyeball and place it in the green cup"
5. "Pick up the eyeball and place it in the orange cup"
6. "Pick up the eyeball and place it in the purple cup"

To check if a command is valid:

```python
if executor.validate_command(command):
    executor.execute(command)
else:
    print(f"Invalid command: {command}")
```

## API Reference

### SmolVLAExecutor Class

#### Constructor

```python
SmolVLAExecutor(
    checkpoint_path: str,
    robot_arm: Optional[MortisArm] = None,
    device: Optional[str] = None
)
```

**Parameters:**
- `checkpoint_path`: Path to trained model checkpoint directory
- `robot_arm`: Optional MortisArm instance (creates new one if not provided)
- `device`: Device for inference ('cuda', 'cpu', or None for auto-detect)

**Raises:**
- `SmolVLAError`: If checkpoint doesn't exist or model loading fails

#### Methods

##### execute()

```python
execute(command: str, max_steps: int = 500) -> bool
```

Execute a manipulation task.

**Parameters:**
- `command`: Natural language task description (must be in VALID_COMMANDS)
- `max_steps`: Maximum inference steps (default: 500)

**Returns:**
- `True` if task completed successfully
- `False` if task failed or didn't complete

**Raises:**
- `SmolVLAError`: If command is invalid or execution fails critically

##### validate_command()

```python
validate_command(command: str) -> bool
```

Check if a command is in the trained task set.

**Parameters:**
- `command`: Command string to validate

**Returns:**
- `True` if command is valid, `False` otherwise

##### cleanup()

```python
cleanup()
```

Clean up resources (camera, GPU memory). Should be called when done.

### Factory Function

#### init_smolvla_executor()

```python
init_smolvla_executor(
    checkpoint_path: Optional[str] = None,
    robot_arm: Optional[MortisArm] = None,
    device: Optional[str] = None
) -> SmolVLAExecutor
```

Factory function to initialize executor with environment configuration.

**Parameters:**
- `checkpoint_path`: Path to checkpoint (uses `SMOLVLA_CHECKPOINT_PATH` env var if None)
- `robot_arm`: Optional MortisArm instance
- `device`: Device to use (uses `SMOLVLA_DEVICE` env var if None)

**Returns:**
- Initialized `SmolVLAExecutor` instance

**Raises:**
- `SmolVLAError`: If no checkpoint path provided and env var not set

## Error Handling

### SmolVLAError

Custom exception for SmolVLA-related errors:

```python
from mortis.smolvla_executor import SmolVLAError

try:
    executor = init_smolvla_executor()
    executor.execute("Invalid command")
except SmolVLAError as e:
    print(f"SmolVLA error: {e}")
```

### Emergency Stop

If an error occurs during execution, the executor automatically:
1. Logs the error
2. Returns the robot to safe idle position
3. Returns `False` from `execute()`

### GPU Out of Memory

If GPU runs out of memory:
1. Executor clears CUDA cache
2. Retries the operation
3. If still fails, returns error

## Performance

### Inference Speed

- **GPU (CUDA)**: ~30 FPS (33ms per step)
- **CPU**: ~3-5 FPS (200-300ms per step)

### Memory Requirements

- **GPU VRAM**: 4-8 GB (depends on model size)
- **RAM**: 8-16 GB

### Typical Task Duration

- Simple pick-and-place: 10-15 seconds (300-450 steps)
- Complex manipulation: 15-20 seconds (450-600 steps)

## Troubleshooting

### "Checkpoint path does not exist"

**Problem**: Checkpoint path is invalid or doesn't exist.

**Solution**: 
- Verify the path exists: `ls -la checkpoints/smolvla_best`
- Check `SMOLVLA_CHECKPOINT_PATH` environment variable
- Ensure you've trained a model or downloaded a checkpoint

### "Model loading failed"

**Problem**: Checkpoint is corrupted or incompatible.

**Solution**:
- Re-download or re-train the model
- Check LeRobot version compatibility
- Verify checkpoint contains required files

### "Failed to connect to robot arm"

**Problem**: Robot is not connected or port is wrong.

**Solution**:
- Check USB connection
- Verify `ROBOT_PORT` in `.env` (usually `/dev/ttyACM1`)
- Run calibration: `make calibrate`

### "GPU out of memory"

**Problem**: Model is too large for available VRAM.

**Solution**:
- Use CPU inference: `device="cpu"`
- Close other GPU-using applications
- Reduce batch size (if training)
- Use model quantization (advanced)

### Slow Inference

**Problem**: Inference is slower than expected.

**Solution**:
- Ensure using GPU: check `executor.device == "cuda"`
- Verify CUDA is installed: `torch.cuda.is_available()`
- Check GPU utilization: `nvidia-smi`
- Warmup is performed automatically on first load

## Integration with Mortis System

The SmolVLA executor integrates with the main Mortis system through:

1. **Intent Router**: Detects manipulation commands from user input
2. **Async Executor**: Runs SmolVLA inference in background thread
3. **Gemini API**: Provides natural language understanding

See the main system documentation for full integration details.

## Example Scripts

### Demo Script

Run the demo to test your setup:

```bash
export SMOLVLA_CHECKPOINT_PATH=checkpoints/smolvla_best
python examples/demo_smolvla.py
```

### Custom Script

```python
#!/usr/bin/env python3
"""Custom SmolVLA execution script."""

from mortis.smolvla_executor import init_smolvla_executor
from mortis.robot import MortisArm

def main():
    # Initialize
    robot = MortisArm()
    robot.connect()
    
    executor = init_smolvla_executor()
    
    # Execute multiple tasks
    tasks = [
        "Pick up the skull and place it in the green cup",
        "Pick up the eyeball and place it in the orange cup",
    ]
    
    for task in tasks:
        print(f"Executing: {task}")
        success = executor.execute(task)
        print(f"Result: {'✅ Success' if success else '❌ Failed'}")
    
    # Cleanup
    executor.cleanup()
    robot.disconnect()

if __name__ == "__main__":
    main()
```

## Next Steps

1. **Train a Model**: See `docs/TRAINING_GUIDE.md` for training instructions
2. **Collect Data**: Use `docs/DATA_COLLECTION_SETUP.md` for dataset creation
3. **Integrate with UI**: See main system documentation for Gradio integration
4. **Add More Tasks**: Expand the valid commands list and retrain

## References

- [LeRobot Documentation](https://github.com/huggingface/lerobot)
- [SmolVLA Paper](https://arxiv.org/abs/2409.12741)
- [Mortis Training Guide](TRAINING_GUIDE.md)
- [Mortis Design Document](../.kiro/specs/gemini-multimodal-refactor/design.md)
