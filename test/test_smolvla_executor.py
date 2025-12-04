"""
Tests for SmolVLA executor module.

These tests verify the SmolVLA executor initialization, configuration,
and basic functionality without requiring a trained model or robot hardware.
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import numpy as np

# Import the module to test
from mortis.smolvla_executor import (
    SmolVLAExecutor,
    SmolVLAError,
    SafetyViolationError,
    TimeoutError,
    GPUOutOfMemoryError,
    init_smolvla_executor
)


@pytest.fixture
def temp_checkpoint_dir():
    """Create a temporary directory to use as checkpoint path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestSmolVLAExecutor:
    """Test suite for SmolVLAExecutor class."""
    
    def test_valid_commands_defined(self):
        """Test that valid commands are properly defined."""
        assert len(SmolVLAExecutor.VALID_COMMANDS) == 6
        assert "Pick up the skull and place it in the green cup" in SmolVLAExecutor.VALID_COMMANDS
        assert "Pick up the eyeball and place it in the purple cup" in SmolVLAExecutor.VALID_COMMANDS
    
    def test_validate_command_valid(self, temp_checkpoint_dir):
        """Test command validation with valid commands."""
        # Create a mock executor (without loading model)
        with patch.object(SmolVLAExecutor, '_load_model'):
            executor = SmolVLAExecutor(
                checkpoint_path=temp_checkpoint_dir,
                device="cpu"
            )
            
            # Test valid commands
            assert executor.validate_command("Pick up the skull and place it in the green cup")
            assert executor.validate_command("Pick up the eyeball and place it in the orange cup")
    
    def test_validate_command_invalid(self, temp_checkpoint_dir):
        """Test command validation with invalid commands."""
        with patch.object(SmolVLAExecutor, '_load_model'):
            executor = SmolVLAExecutor(
                checkpoint_path=temp_checkpoint_dir,
                device="cpu"
            )
            
            # Test invalid commands
            assert not executor.validate_command("Pick up the banana")
            assert not executor.validate_command("Do a backflip")
            assert not executor.validate_command("")
    
    def test_init_invalid_checkpoint_path(self):
        """Test initialization with non-existent checkpoint path."""
        with pytest.raises(SmolVLAError, match="Checkpoint path does not exist"):
            SmolVLAExecutor(
                checkpoint_path="/nonexistent/path/to/checkpoint",
                device="cpu"
            )
    
    def test_device_auto_detection(self, temp_checkpoint_dir):
        """Test automatic device detection."""
        with patch.object(SmolVLAExecutor, '_load_model'):
            with patch('torch.cuda.is_available', return_value=False):
                executor = SmolVLAExecutor(
                    checkpoint_path=temp_checkpoint_dir,
                    device=None
                )
                assert executor.device == "cpu"
    
    def test_device_explicit_cuda(self, temp_checkpoint_dir):
        """Test explicit CUDA device selection."""
        with patch.object(SmolVLAExecutor, '_load_model'):
            executor = SmolVLAExecutor(
                checkpoint_path=temp_checkpoint_dir,
                device="cuda"
            )
            assert executor.device == "cuda"
    
    def test_action_to_dict_conversion(self, temp_checkpoint_dir):
        """Test conversion of action tensor to robot command dictionary."""
        import torch
        
        with patch.object(SmolVLAExecutor, '_load_model'):
            executor = SmolVLAExecutor(
                checkpoint_path=temp_checkpoint_dir,
                device="cpu"
            )
            
            # Create a dummy action tensor
            action = torch.tensor([10.0, -20.0, 30.0, -40.0, 50.0, 60.0])
            
            # Convert to dictionary
            action_dict = executor._action_to_dict(action)
            
            # Verify structure
            assert len(action_dict) == 6
            assert "shoulder_pan.pos" in action_dict
            assert "gripper.pos" in action_dict
            
            # Verify values
            assert action_dict["shoulder_pan.pos"] == 10.0
            assert action_dict["shoulder_lift.pos"] == -20.0
            assert action_dict["gripper.pos"] == 60.0
    
    def test_action_to_dict_with_batch_dimension(self, temp_checkpoint_dir):
        """Test action conversion with batch dimension."""
        import torch
        
        with patch.object(SmolVLAExecutor, '_load_model'):
            executor = SmolVLAExecutor(
                checkpoint_path=temp_checkpoint_dir,
                device="cpu"
            )
            
            # Create action with batch dimension
            action = torch.tensor([[10.0, -20.0, 30.0, -40.0, 50.0, 60.0]])
            
            # Should handle batch dimension correctly
            action_dict = executor._action_to_dict(action)
            assert len(action_dict) == 6
            assert action_dict["shoulder_pan.pos"] == 10.0
    
    def test_action_to_dict_invalid_shape(self, temp_checkpoint_dir):
        """Test action conversion with invalid shape raises error."""
        import torch
        
        with patch.object(SmolVLAExecutor, '_load_model'):
            executor = SmolVLAExecutor(
                checkpoint_path=temp_checkpoint_dir,
                device="cpu"
            )
            
            # Create action with wrong number of dimensions
            invalid_action = torch.tensor([10.0, -20.0, 30.0])  # Only 3 dimensions
            
            # Should raise SmolVLAError
            with pytest.raises(SmolVLAError, match="Invalid action shape"):
                executor._action_to_dict(invalid_action)
    
    def test_is_task_complete_heuristic(self, temp_checkpoint_dir):
        """Test task completion heuristic."""
        import torch
        
        with patch.object(SmolVLAExecutor, '_load_model'):
            executor = SmolVLAExecutor(
                checkpoint_path=temp_checkpoint_dir,
                device="cpu"
            )
            
            # Create dummy observation
            obs = {
                "observation.image": torch.zeros((1, 3, 224, 224)),
                "observation.state": torch.zeros((1, 6))
            }
            
            # Create dummy action
            action = torch.zeros((1, 6))
            
            # Test at different steps
            assert not executor._is_task_complete(obs, step=0, action=action)
            assert not executor._is_task_complete(obs, step=200, action=action)
            assert executor._is_task_complete(obs, step=450, action=action)
            assert executor._is_task_complete(obs, step=500, action=action)
    
    def test_is_task_complete_stability_detection(self, temp_checkpoint_dir):
        """Test task completion via action stability detection."""
        import torch
        
        with patch.object(SmolVLAExecutor, '_load_model'):
            executor = SmolVLAExecutor(
                checkpoint_path=temp_checkpoint_dir,
                device="cpu"
            )
            
            # Reset tracking variables
            executor._previous_action = None
            executor._stable_count = 0
            
            # Create dummy observation
            obs = {
                "observation.image": torch.zeros((1, 3, 224, 224)),
                "observation.state": torch.zeros((1, 6))
            }
            
            # Create stable action (same action repeated)
            stable_action = torch.tensor([[1.0, 2.0, 3.0, 4.0, 5.0, 6.0]])
            
            # First call at step 100 - not complete yet
            assert not executor._is_task_complete(obs, step=100, action=stable_action)
            
            # Repeat same action 30 times (should trigger stability detection)
            for i in range(30):
                result = executor._is_task_complete(obs, step=100 + i, action=stable_action)
                if i < 29:
                    assert not result, f"Should not complete at iteration {i}"
                else:
                    assert result, "Should complete after 30 stable steps"
    
    def test_is_task_complete_stability_reset(self, temp_checkpoint_dir):
        """Test that stability counter resets when action changes."""
        import torch
        
        with patch.object(SmolVLAExecutor, '_load_model'):
            executor = SmolVLAExecutor(
                checkpoint_path=temp_checkpoint_dir,
                device="cpu"
            )
            
            # Reset tracking variables
            executor._previous_action = None
            executor._stable_count = 0
            
            # Create dummy observation
            obs = {
                "observation.image": torch.zeros((1, 3, 224, 224)),
                "observation.state": torch.zeros((1, 6))
            }
            
            # Create stable action
            stable_action = torch.tensor([[1.0, 2.0, 3.0, 4.0, 5.0, 6.0]])
            
            # Build up stability count
            for i in range(20):
                executor._is_task_complete(obs, step=100 + i, action=stable_action)
            
            # Verify stability count is building
            # Note: First iteration doesn't increment (no previous action to compare)
            assert executor._stable_count == 19
            
            # Now change action significantly
            different_action = torch.tensor([[10.0, 20.0, 30.0, 40.0, 50.0, 60.0]])
            executor._is_task_complete(obs, step=120, action=different_action)
            
            # Stability count should reset
            assert executor._stable_count == 0
    
    def test_create_dummy_observation(self, temp_checkpoint_dir):
        """Test creation of dummy observation for warmup."""
        import torch
        
        with patch.object(SmolVLAExecutor, '_load_model'):
            executor = SmolVLAExecutor(
                checkpoint_path=temp_checkpoint_dir,
                device="cpu"
            )
            
            obs = executor._create_dummy_observation()
            
            # Verify structure
            assert "observation.images.camera1" in obs
            assert "observation.state" in obs
            assert "task" in obs
            
            # Verify shapes (default is 256x256)
            assert obs["observation.images.camera1"].shape == (1, 3, 256, 256)
            assert obs["observation.state"].shape == (1, 6)
            assert obs["task"] == ["dummy task"]


class TestInitSmolVLAExecutor:
    """Test suite for init_smolvla_executor factory function."""
    
    def test_init_with_explicit_path(self):
        """Test initialization with explicit checkpoint path."""
        with patch.object(SmolVLAExecutor, '_load_model'):
            with patch.object(SmolVLAExecutor, '__init__', return_value=None) as mock_init:
                # Create a temporary directory to use as checkpoint path
                import tempfile
                with tempfile.TemporaryDirectory() as tmpdir:
                    executor = init_smolvla_executor(
                        checkpoint_path=tmpdir,
                        device="cpu"
                    )
                    
                    # Verify __init__ was called with correct arguments
                    mock_init.assert_called_once()
    
    def test_init_with_env_var(self):
        """Test initialization using environment variable."""
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Set environment variable
            os.environ["SMOLVLA_CHECKPOINT_PATH"] = tmpdir
            
            try:
                with patch.object(SmolVLAExecutor, '_load_model'):
                    with patch.object(SmolVLAExecutor, '__init__', return_value=None):
                        executor = init_smolvla_executor(device="cpu")
                        # Should not raise an error
            finally:
                # Clean up environment variable
                if "SMOLVLA_CHECKPOINT_PATH" in os.environ:
                    del os.environ["SMOLVLA_CHECKPOINT_PATH"]
    
    def test_init_without_checkpoint_path(self):
        """Test initialization fails without checkpoint path."""
        # Ensure env var is not set
        if "SMOLVLA_CHECKPOINT_PATH" in os.environ:
            del os.environ["SMOLVLA_CHECKPOINT_PATH"]
        
        with pytest.raises(SmolVLAError, match="No checkpoint path provided"):
            init_smolvla_executor()
    
    def test_init_with_device_env_var(self):
        """Test device selection from environment variable."""
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ["SMOLVLA_CHECKPOINT_PATH"] = tmpdir
            os.environ["SMOLVLA_DEVICE"] = "cuda"
            
            try:
                with patch.object(SmolVLAExecutor, '_load_model'):
                    executor = init_smolvla_executor()
                    assert executor.device == "cuda"
            finally:
                # Clean up
                if "SMOLVLA_CHECKPOINT_PATH" in os.environ:
                    del os.environ["SMOLVLA_CHECKPOINT_PATH"]
                if "SMOLVLA_DEVICE" in os.environ:
                    del os.environ["SMOLVLA_DEVICE"]


class TestSmolVLAExecutorExecution:
    """Test suite for execution methods."""
    
    def test_execute_invalid_command(self, temp_checkpoint_dir):
        """Test execution with invalid command raises error."""
        with patch.object(SmolVLAExecutor, '_load_model'):
            executor = SmolVLAExecutor(
                checkpoint_path=temp_checkpoint_dir,
                device="cpu"
            )
            
            with pytest.raises(SmolVLAError, match="Invalid command"):
                executor.execute("Invalid command")
    
    def test_execute_requires_robot_connection(self, temp_checkpoint_dir):
        """Test execution ensures robot is connected."""
        with patch.object(SmolVLAExecutor, '_load_model'):
            # Create mock robot arm
            mock_robot = Mock()
            mock_robot.connected = False
            
            # Make connect() set connected to True
            def mock_connect():
                mock_robot.connected = True
            mock_robot.connect.side_effect = mock_connect
            
            executor = SmolVLAExecutor(
                checkpoint_path=temp_checkpoint_dir,
                robot_arm=mock_robot,
                device="cpu"
            )
            
            # Mock the execution methods
            with patch.object(executor, '_init_camera'):
                with patch.object(executor, '_execute_task', return_value=True):
                    # Execute should try to connect
                    executor.execute("Pick up the skull and place it in the green cup")
                    
                    # Verify connect was called
                    mock_robot.connect.assert_called_once()
    
    def test_emergency_stop_on_error(self, temp_checkpoint_dir):
        """Test emergency stop is called on execution error."""
        with patch.object(SmolVLAExecutor, '_load_model'):
            mock_robot = Mock()
            mock_robot.connected = True
            
            executor = SmolVLAExecutor(
                checkpoint_path=temp_checkpoint_dir,
                robot_arm=mock_robot,
                device="cpu"
            )
            
            # Mock methods to simulate error
            with patch.object(executor, '_init_camera'):
                with patch.object(executor, '_execute_task_with_timeout', side_effect=Exception("Test error")):
                    # Execute should handle error and call emergency stop
                    with pytest.raises(SmolVLAError, match="Execution failed"):
                        executor.execute("Pick up the skull and place it in the green cup")
                    
                    # Should call move_arm to return to idle (emergency stop)
                    mock_robot.move_arm.assert_called()


class TestObservationCapture:
    """Test suite for observation capture functionality."""
    
    def test_capture_robot_state_success(self, temp_checkpoint_dir):
        """Test successful robot state capture."""
        import torch
        
        with patch.object(SmolVLAExecutor, '_load_model'):
            # Create mock robot arm
            mock_robot = Mock()
            mock_robot.robot.get_observation.return_value = {
                "shoulder_pan.pos": 10.0,
                "shoulder_lift.pos": -20.0,
                "elbow_flex.pos": 30.0,
                "wrist_flex.pos": -40.0,
                "wrist_roll.pos": 50.0,
                "gripper.pos": 60.0
            }
            
            executor = SmolVLAExecutor(
                checkpoint_path=temp_checkpoint_dir,
                robot_arm=mock_robot,
                device="cpu"
            )
            
            # Capture state
            state_tensor = executor._capture_robot_state()
            
            # Verify shape and values
            assert state_tensor.shape == (1, 6)
            assert state_tensor[0, 0].item() == 10.0
            assert state_tensor[0, 5].item() == 60.0
    
    def test_capture_robot_state_failure_fallback(self, temp_checkpoint_dir):
        """Test robot state capture falls back to zeros on error."""
        import torch
        
        with patch.object(SmolVLAExecutor, '_load_model'):
            # Create mock robot that raises error
            mock_robot = Mock()
            mock_robot.robot.get_observation.side_effect = Exception("Connection error")
            
            executor = SmolVLAExecutor(
                checkpoint_path=temp_checkpoint_dir,
                robot_arm=mock_robot,
                device="cpu"
            )
            
            # Should not raise, should return zeros
            state_tensor = executor._capture_robot_state()
            
            # Verify fallback to zeros
            assert state_tensor.shape == (1, 6)
            assert torch.all(state_tensor == 0.0)
    
    def test_capture_camera_images_with_camera(self, temp_checkpoint_dir):
        """Test camera image capture with available camera."""
        import torch
        import numpy as np
        
        with patch.object(SmolVLAExecutor, '_load_model'):
            executor = SmolVLAExecutor(
                checkpoint_path=temp_checkpoint_dir,
                device="cpu"
            )
            
            # Mock camera
            mock_camera = Mock()
            mock_camera.read.return_value = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            executor.camera = mock_camera
            
            # Capture images
            image_tensors = executor._capture_camera_images()
            
            # Should return 3 images
            assert len(image_tensors) == 3
            
            # Verify shape (should be resized to 256x256)
            for img_tensor in image_tensors:
                assert img_tensor.shape == (1, 3, 256, 256)
    
    def test_capture_camera_images_without_camera(self, temp_checkpoint_dir):
        """Test camera image capture without camera (dummy images)."""
        import torch
        
        with patch.object(SmolVLAExecutor, '_load_model'):
            executor = SmolVLAExecutor(
                checkpoint_path=temp_checkpoint_dir,
                device="cpu"
            )
            
            # No camera
            executor.camera = None
            
            # Capture images
            image_tensors = executor._capture_camera_images()
            
            # Should return 3 dummy images
            assert len(image_tensors) == 3
            
            # Verify shape
            for img_tensor in image_tensors:
                assert img_tensor.shape == (1, 3, 256, 256)
                # Dummy images should be all zeros
                assert torch.all(img_tensor == 0.0)
    
    def test_preprocess_image(self, temp_checkpoint_dir):
        """Test image preprocessing."""
        import torch
        import numpy as np
        
        with patch.object(SmolVLAExecutor, '_load_model'):
            executor = SmolVLAExecutor(
                checkpoint_path=temp_checkpoint_dir,
                device="cpu"
            )
            
            # Create test image (640x480x3)
            test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            
            # Preprocess
            processed = executor._preprocess_image(test_image)
            
            # Verify output shape (should be resized to 256x256)
            assert processed.shape == (1, 3, 256, 256)
            
            # Verify normalization (values should be in [0, 1])
            assert processed.min() >= 0.0
            assert processed.max() <= 1.0
    
    def test_get_observation_complete(self, temp_checkpoint_dir):
        """Test complete observation capture."""
        import torch
        import numpy as np
        
        with patch.object(SmolVLAExecutor, '_load_model'):
            # Create mock robot
            mock_robot = Mock()
            mock_robot.robot.get_observation.return_value = {
                "shoulder_pan.pos": 0.0,
                "shoulder_lift.pos": 0.0,
                "elbow_flex.pos": 0.0,
                "wrist_flex.pos": 0.0,
                "wrist_roll.pos": 0.0,
                "gripper.pos": 0.0
            }
            
            executor = SmolVLAExecutor(
                checkpoint_path=temp_checkpoint_dir,
                robot_arm=mock_robot,
                device="cpu"
            )
            
            # Mock camera
            mock_camera = Mock()
            mock_camera.read.return_value = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            executor.camera = mock_camera
            
            # Get observation
            obs = executor._get_observation()
            
            # Verify structure
            assert "observation.state" in obs
            assert "observation.images.camera1" in obs
            assert "observation.images.camera2" in obs
            assert "observation.images.camera3" in obs
            
            # Verify shapes
            assert obs["observation.state"].shape == (1, 6)
            assert obs["observation.images.camera1"].shape == (1, 3, 256, 256)
            assert obs["observation.images.camera2"].shape == (1, 3, 256, 256)
            assert obs["observation.images.camera3"].shape == (1, 3, 256, 256)
    
    def test_create_dummy_image(self, temp_checkpoint_dir):
        """Test dummy image creation."""
        import torch
        
        with patch.object(SmolVLAExecutor, '_load_model'):
            executor = SmolVLAExecutor(
                checkpoint_path=temp_checkpoint_dir,
                device="cpu"
            )
            
            # Create dummy image
            dummy = executor._create_dummy_image()
            
            # Verify shape
            assert dummy.shape == (1, 3, 256, 256)
            
            # Should be all zeros
            assert torch.all(dummy == 0.0)


class TestSafetyFeatures:
    """Test suite for safety and error handling features."""
    
    def test_safety_constants_defined(self):
        """Test that safety constants are properly defined."""
        assert hasattr(SmolVLAExecutor, 'JOINT_LIMITS')
        assert hasattr(SmolVLAExecutor, 'MAX_JOINT_VELOCITY')
        assert hasattr(SmolVLAExecutor, 'DEFAULT_TIMEOUT')
        
        # Verify joint limits structure
        assert len(SmolVLAExecutor.JOINT_LIMITS) == 6
        assert "shoulder_pan.pos" in SmolVLAExecutor.JOINT_LIMITS
        assert "gripper.pos" in SmolVLAExecutor.JOINT_LIMITS
        
        # Verify limits are tuples of (min, max)
        for joint, limits in SmolVLAExecutor.JOINT_LIMITS.items():
            assert len(limits) == 2
            assert limits[0] < limits[1]
    
    def test_init_with_safety_configuration(self, temp_checkpoint_dir):
        """Test initialization with safety configuration."""
        with patch.object(SmolVLAExecutor, '_load_model'):
            executor = SmolVLAExecutor(
                checkpoint_path=temp_checkpoint_dir,
                device="cpu",
                enable_safety_checks=True,
                timeout=60.0
            )
            
            assert executor.enable_safety_checks is True
            assert executor.timeout == 60.0
            assert hasattr(executor, '_emergency_stop_flag')
            assert hasattr(executor, '_execution_lock')
    
    def test_init_with_safety_disabled(self, temp_checkpoint_dir):
        """Test initialization with safety checks disabled."""
        with patch.object(SmolVLAExecutor, '_load_model'):
            executor = SmolVLAExecutor(
                checkpoint_path=temp_checkpoint_dir,
                device="cpu",
                enable_safety_checks=False
            )
            
            assert executor.enable_safety_checks is False
    
    def test_check_action_safety_valid_action(self, temp_checkpoint_dir):
        """Test safety check with valid action."""
        import torch
        
        with patch.object(SmolVLAExecutor, '_load_model'):
            executor = SmolVLAExecutor(
                checkpoint_path=temp_checkpoint_dir,
                device="cpu",
                enable_safety_checks=True
            )
            
            # Create valid action (within limits)
            valid_action = torch.tensor([[0.0, 0.0, 0.0, 0.0, 0.0, 50.0]])
            
            # Create observation
            obs = {
                "observation.state": torch.zeros(1, 6)
            }
            
            # Should not raise
            executor._check_action_safety(valid_action, obs)
    
    def test_check_action_safety_position_limit_violation(self, temp_checkpoint_dir):
        """Test safety check detects position limit violations."""
        import torch
        
        with patch.object(SmolVLAExecutor, '_load_model'):
            executor = SmolVLAExecutor(
                checkpoint_path=temp_checkpoint_dir,
                device="cpu",
                enable_safety_checks=True
            )
            
            # Create action that exceeds shoulder_pan limit (>180)
            invalid_action = torch.tensor([[200.0, 0.0, 0.0, 0.0, 0.0, 50.0]])
            
            obs = {
                "observation.state": torch.zeros(1, 6)
            }
            
            # Should raise SafetyViolationError
            with pytest.raises(SafetyViolationError, match="exceeds limits"):
                executor._check_action_safety(invalid_action, obs)
    
    def test_check_action_safety_velocity_limit_violation(self, temp_checkpoint_dir):
        """Test safety check detects velocity limit violations."""
        import torch
        
        with patch.object(SmolVLAExecutor, '_load_model'):
            executor = SmolVLAExecutor(
                checkpoint_path=temp_checkpoint_dir,
                device="cpu",
                enable_safety_checks=True
            )
            
            # Set previous state
            executor._previous_state = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
            
            # Create action with large velocity change (>10 degrees)
            obs = {
                "observation.state": torch.tensor([[20.0, 0.0, 0.0, 0.0, 0.0, 0.0]])
            }
            
            action = torch.tensor([[20.0, 0.0, 0.0, 0.0, 0.0, 0.0]])
            
            # Should raise SafetyViolationError
            with pytest.raises(SafetyViolationError, match="velocity.*exceeds limit"):
                executor._check_action_safety(action, obs)
    
    def test_emergency_stop_flag(self, temp_checkpoint_dir):
        """Test emergency stop flag functionality."""
        with patch.object(SmolVLAExecutor, '_load_model'):
            executor = SmolVLAExecutor(
                checkpoint_path=temp_checkpoint_dir,
                device="cpu"
            )
            
            # Initially not set
            assert not executor._emergency_stop_flag.is_set()
            
            # Trigger emergency stop
            executor.trigger_emergency_stop()
            
            # Should be set
            assert executor._emergency_stop_flag.is_set()
    
    def test_is_executing_flag(self, temp_checkpoint_dir):
        """Test execution status tracking."""
        with patch.object(SmolVLAExecutor, '_load_model'):
            executor = SmolVLAExecutor(
                checkpoint_path=temp_checkpoint_dir,
                device="cpu"
            )
            
            # Initially not executing
            assert not executor.is_executing()
            
            # Simulate execution
            executor._is_executing = True
            assert executor.is_executing()
            
            executor._is_executing = False
            assert not executor.is_executing()
    
    def test_execution_lock_prevents_concurrent_execution(self, temp_checkpoint_dir):
        """Test that execution lock prevents concurrent task execution."""
        with patch.object(SmolVLAExecutor, '_load_model'):
            mock_robot = Mock()
            mock_robot.connected = True
            
            executor = SmolVLAExecutor(
                checkpoint_path=temp_checkpoint_dir,
                robot_arm=mock_robot,
                device="cpu"
            )
            
            # Acquire lock manually
            executor._execution_lock.acquire()
            
            try:
                # Try to execute - should fail immediately
                with pytest.raises(SmolVLAError, match="already running"):
                    executor.execute("Pick up the skull and place it in the green cup")
            finally:
                executor._execution_lock.release()
    
    def test_timeout_handling(self, temp_checkpoint_dir):
        """Test timeout detection during execution."""
        import torch
        
        with patch.object(SmolVLAExecutor, '_load_model'):
            mock_robot = Mock()
            mock_robot.connected = True
            
            executor = SmolVLAExecutor(
                checkpoint_path=temp_checkpoint_dir,
                robot_arm=mock_robot,
                device="cpu",
                timeout=0.1  # Very short timeout
            )
            
            # Mock methods
            with patch.object(executor, '_init_camera'):
                with patch.object(executor, '_execute_task_with_timeout', side_effect=TimeoutError("Timeout")):
                    with patch.object(executor, '_emergency_stop'):
                        # Should raise TimeoutError
                        with pytest.raises(TimeoutError):
                            executor.execute("Pick up the skull and place it in the green cup")
    
    def test_gpu_oom_handling(self, temp_checkpoint_dir):
        """Test GPU out-of-memory error handling."""
        import torch
        
        with patch.object(SmolVLAExecutor, '_load_model'):
            executor = SmolVLAExecutor(
                checkpoint_path=temp_checkpoint_dir,
                device="cuda"
            )
            
            # Mock policy to raise OOM
            executor.policy = Mock()
            executor.policy.select_action.side_effect = torch.cuda.OutOfMemoryError()
            
            obs = {"test": "observation"}
            
            # Should raise GPUOutOfMemoryError
            with pytest.raises(GPUOutOfMemoryError):
                executor._run_inference_with_oom_handling(obs)
    
    def test_gpu_oom_recovery(self, temp_checkpoint_dir):
        """Test GPU OOM recovery after clearing cache."""
        import torch
        
        with patch.object(SmolVLAExecutor, '_load_model'):
            executor = SmolVLAExecutor(
                checkpoint_path=temp_checkpoint_dir,
                device="cuda"
            )
            
            # Mock policy to fail once then succeed
            executor.policy = Mock()
            call_count = [0]
            
            def mock_select_action(obs):
                call_count[0] += 1
                if call_count[0] == 1:
                    raise torch.cuda.OutOfMemoryError()
                return torch.zeros(1, 6)
            
            executor.policy.select_action.side_effect = mock_select_action
            
            obs = {"test": "observation"}
            
            # Should recover after first failure
            with patch('torch.cuda.empty_cache'):
                result = executor._run_inference_with_oom_handling(obs)
                assert result is not None
                assert call_count[0] == 2  # Called twice
    
    def test_handle_gpu_oom_clears_cache(self, temp_checkpoint_dir):
        """Test that GPU OOM handler clears CUDA cache."""
        with patch.object(SmolVLAExecutor, '_load_model'):
            executor = SmolVLAExecutor(
                checkpoint_path=temp_checkpoint_dir,
                device="cuda"
            )
            
            with patch('torch.cuda.empty_cache') as mock_empty_cache:
                with patch('torch.cuda.is_available', return_value=True):
                    executor._handle_gpu_oom()
                    
                    # Should call empty_cache
                    mock_empty_cache.assert_called_once()
    
    def test_safe_return_home(self, temp_checkpoint_dir):
        """Test safe return to home position."""
        with patch.object(SmolVLAExecutor, '_load_model'):
            mock_robot = Mock()
            
            executor = SmolVLAExecutor(
                checkpoint_path=temp_checkpoint_dir,
                robot_arm=mock_robot,
                device="cpu"
            )
            
            # Should call move_arm with "idle"
            executor._safe_return_home()
            mock_robot.move_arm.assert_called_once_with("idle")
    
    def test_safe_return_home_with_fallback(self, temp_checkpoint_dir):
        """Test safe return home with fallback on error."""
        with patch.object(SmolVLAExecutor, '_load_model'):
            mock_robot = Mock()
            mock_robot.move_arm.side_effect = Exception("Move failed")
            
            executor = SmolVLAExecutor(
                checkpoint_path=temp_checkpoint_dir,
                robot_arm=mock_robot,
                device="cpu"
            )
            
            # Should try fallback (direct command)
            executor._safe_return_home()
            
            # Should have tried move_arm first
            mock_robot.move_arm.assert_called_once()
            # Should have tried direct command as fallback
            mock_robot.robot.send_action.assert_called_once()
    
    def test_emergency_stop_sets_flag(self, temp_checkpoint_dir):
        """Test emergency stop sets the flag."""
        with patch.object(SmolVLAExecutor, '_load_model'):
            mock_robot = Mock()
            
            executor = SmolVLAExecutor(
                checkpoint_path=temp_checkpoint_dir,
                robot_arm=mock_robot,
                device="cpu"
            )
            
            # Initially not set
            assert not executor._emergency_stop_flag.is_set()
            
            # Call emergency stop
            executor._emergency_stop()
            
            # Flag should be set
            assert executor._emergency_stop_flag.is_set()
            
            # Should have tried to return home
            mock_robot.move_arm.assert_called()
    
    def test_command_validation_against_trained_set(self, temp_checkpoint_dir):
        """Test command validation ensures only trained commands are executed."""
        with patch.object(SmolVLAExecutor, '_load_model'):
            mock_robot = Mock()
            mock_robot.connected = True
            
            executor = SmolVLAExecutor(
                checkpoint_path=temp_checkpoint_dir,
                robot_arm=mock_robot,
                device="cpu"
            )
            
            # Valid command should not raise during validation
            assert executor.validate_command("Pick up the skull and place it in the green cup")
            
            # Invalid command should raise during execute
            with pytest.raises(SmolVLAError, match="Invalid command"):
                executor.execute("Pick up the banana")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
