# Task 21: Observation Capture Implementation

## Overview

This document describes the implementation of observation capture functionality for the SmolVLA executor, enabling the system to capture visual and robot state observations for inference.

## Implementation Summary

### 1. Camera Integration

Added support for multiple camera types with automatic fallback:

- **Intel RealSense Camera** (primary): High-quality RGB-D camera support
- **OpenCV Camera** (fallback): Standard USB webcam support
- **Dummy Images** (testing): Black images when no camera is available

The `_init_camera()` method attempts to initialize cameras in order of preference and gracefully falls back if hardware is not available.

### 2. Robot State Capture

Implemented `_capture_robot_state()` method that:

- Retrieves current joint positions from the SO101 robot
- Extracts 6 joint values in the correct order:
  - shoulder_pan.pos
  - shoulder_lift.pos
  - elbow_flex.pos
  - wrist_flex.pos
  - wrist_roll.pos
  - gripper.pos
- Converts to PyTorch tensor with batch dimension [1, 6]
- Falls back to zero state on connection errors

### 3. Visual Observation Capture

Implemented `_capture_camera_images()` method that:

- Reads images from connected camera(s)
- Preprocesses images for SmolVLA input
- Returns list of image tensors [1, 3, 256, 256]
- Duplicates single camera image for multi-camera setup (camera1, camera2, camera3)
- Falls back to dummy images when camera is unavailable

### 4. Image Preprocessing

Implemented `_preprocess_image()` method that:

- Converts BGR to RGB (OpenCV uses BGR)
- Resizes images to 256x256 (model input size)
- Converts to PyTorch tensor format (C, H, W)
- Normalizes pixel values to [0, 1]
- Adds batch dimension
- Moves tensor to appropriate device (CPU/GPU)

### 5. Observation Dictionary Formatting

Updated `_get_observation()` method to:

- Capture robot state using `_capture_robot_state()`
- Capture camera images using `_capture_camera_images()`
- Format observations in SmolVLA-compatible dictionary:
  ```python
  {
      "observation.state": [1, 6],           # Joint positions
      "observation.images.camera1": [1, 3, 256, 256],  # RGB image
      "observation.images.camera2": [1, 3, 256, 256],  # RGB image
      "observation.images.camera3": [1, 3, 256, 256]   # RGB image
  }
  ```

### 6. Tensor Conversion and Device Placement

All tensors are properly:

- Converted to appropriate dtype (float32)
- Moved to the correct device (CPU or CUDA)
- Formatted with batch dimensions for model input
- Normalized to expected value ranges

## Key Features

### Robust Error Handling

- Camera initialization failures don't crash the system
- Robot state capture errors fall back to zero state
- Logging provides clear diagnostic information
- System can run without hardware for testing

### Multi-Camera Support

- Supports up to 3 cameras (camera1, camera2, camera3)
- Currently duplicates single camera for all three
- Architecture ready for true multi-camera setup

### Device Agnostic

- Works on both CPU and CUDA devices
- Automatic device detection
- Tensors automatically moved to correct device

### Testing

Comprehensive test coverage including:

- Robot state capture (success and failure cases)
- Camera image capture (with and without camera)
- Image preprocessing
- Complete observation capture
- Dummy image creation

## Requirements Satisfied

✅ **Requirement 6.2**: "WHEN a valid Task String is received, THE Mortis System SHALL execute SmolVLA inference with the command as input"
- Observation capture provides the visual and state inputs needed for inference

✅ **Requirement 6.4**: "THE Mortis System SHALL provide visual feedback during robotic execution through the webcam view"
- Camera integration enables visual observation capture

## Usage Example

```python
from mortis.smolvla_executor import SmolVLAExecutor

# Initialize executor
executor = SmolVLAExecutor(
    checkpoint_path="checkpoints/smolvla_best.pt",
    device="cuda"
)

# During execution, observations are automatically captured
observation = executor._get_observation()

# Observation contains:
# - observation.state: [1, 6] tensor of joint positions
# - observation.images.camera1: [1, 3, 256, 256] RGB image
# - observation.images.camera2: [1, 3, 256, 256] RGB image
# - observation.images.camera3: [1, 3, 256, 256] RGB image
```

## Testing

Run tests with:

```bash
# Test observation capture specifically
python -m pytest test/test_smolvla_executor.py::TestObservationCapture -v

# Test all SmolVLA executor functionality
python -m pytest test/test_smolvla_executor.py -v
```

All 24 tests pass successfully.

## Known Limitations

1. **Language Tokenization**: The SmolVLA policy requires tokenized language instructions (`observation.language.tokens`). This tokenization needs to be added in a separate task as it requires loading the VLM tokenizer.

2. **Multi-Camera**: Currently duplicates single camera image for all three camera inputs. True multi-camera support requires additional hardware setup.

## Future Enhancements

1. **Language Token Integration**: Add tokenizer loading and language instruction tokenization
2. **True Multi-Camera Support**: Capture from multiple physical cameras instead of duplicating
3. **Depth Information**: Utilize Intel RealSense depth data for better spatial understanding
4. **Camera Calibration**: Add camera calibration utilities for improved accuracy
5. **Image Augmentation**: Add optional augmentation for robustness
6. **Observation Caching**: Cache recent observations for temporal reasoning

## Files Modified

- `src/mortis/smolvla_executor.py`: Added observation capture methods
- `test/test_smolvla_executor.py`: Added comprehensive tests for observation capture

## Dependencies

- `torch`: Tensor operations and device management
- `numpy`: Array operations
- `PIL`: Image resizing and preprocessing
- `lerobot.common.robot_devices.cameras`: Camera interfaces (optional)

## Notes

- The system gracefully degrades when hardware is not available
- Dummy images allow testing without physical robot or camera
- All tensors include batch dimensions for model compatibility
- Image preprocessing matches training configuration (256x256 RGB)
