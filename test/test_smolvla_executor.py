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

# Import the module to test
from mortis.smolvla_executor import (
    SmolVLAExecutor,
    SmolVLAError,
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
            
            # Test at different steps
            assert not executor._is_task_complete(obs, step=0)
            assert not executor._is_task_complete(obs, step=200)
            assert executor._is_task_complete(obs, step=400)
            assert executor._is_task_complete(obs, step=500)
    
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
                with patch.object(executor, '_execute_task', side_effect=Exception("Test error")):
                    # Execute should handle error and call emergency stop
                    result = executor.execute("Pick up the skull and place it in the green cup")
                    
                    # Should return False on error
                    assert result is False
                    
                    # Should call move_arm to return to idle
                    mock_robot.move_arm.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
