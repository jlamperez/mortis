"""
SmolVLA Executor for vision-language-action robotic manipulation.

This module implements the SmolVLA model executor that performs inference
for manipulation tasks using the trained SmolVLA policy from LeRobot.
"""

import os
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any

import torch
import numpy as np
from PIL import Image

# LeRobot imports
from lerobot.policies.smolvla.modeling_smolvla import SmolVLAPolicy
from lerobot.policies.smolvla.configuration_smolvla import SmolVLAConfig

# Local imports
from .robot import MortisArm, HOME_POSE


# Configure logging
logger = logging.getLogger(__name__)


class SmolVLAError(Exception):
    """Base exception for SmolVLA executor errors."""
    pass


class SmolVLAExecutor:
    """
    Executor for SmolVLA vision-language-action model inference.
    
    This class handles loading the trained SmolVLA model, capturing observations
    from the robot and camera, running inference, and executing predicted actions
    on the SO101 robotic arm.
    
    Attributes:
        checkpoint_path: Path to the trained model checkpoint
        device: Device to run inference on ('cuda' or 'cpu')
        policy: Loaded SmolVLA policy model
        robot_arm: Reference to MortisArm instance for action execution
        camera: Camera interface for visual observations (to be implemented)
        valid_commands: List of trained manipulation task commands
    """
    
    # Valid manipulation commands that the model was trained on
    VALID_COMMANDS = [
        "Pick up the skull and place it in the green cup",
        "Pick up the skull and place it in the orange cup",
        "Pick up the skull and place it in the purple cup",
        "Pick up the eyeball and place it in the green cup",
        "Pick up the eyeball and place it in the orange cup",
        "Pick up the eyeball and place it in the purple cup",
    ]
    
    def __init__(
        self,
        checkpoint_path: str,
        robot_arm: Optional[MortisArm] = None,
        device: Optional[str] = None
    ):
        """
        Initialize the SmolVLA executor.
        
        Args:
            checkpoint_path: Path to the trained SmolVLA model checkpoint
            robot_arm: Optional MortisArm instance (will create if not provided)
            device: Device to run inference on ('cuda', 'cpu', or None for auto-detect)
            
        Raises:
            SmolVLAError: If checkpoint path doesn't exist or model loading fails
        """
        # Initialize attributes first (for cleanup in case of early failure)
        self.camera = None
        self.policy = None
        
        self.checkpoint_path = Path(checkpoint_path)
        
        # Validate checkpoint path
        if not self.checkpoint_path.exists():
            raise SmolVLAError(f"Checkpoint path does not exist: {checkpoint_path}")
        
        # Set device
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        logger.info(f"Initializing SmolVLA executor on device: {self.device}")
        
        # Initialize robot arm
        self.robot_arm = robot_arm
        if self.robot_arm is None:
            logger.info("No robot arm provided, creating new MortisArm instance")
            self.robot_arm = MortisArm()
        
        # Load the model
        self._load_model()
        
        # Model is ready
        logger.info("SmolVLA executor initialized successfully")
    
    def _load_model(self):
        """
        Load the SmolVLA model from checkpoint.
        
        Raises:
            SmolVLAError: If model loading fails
        """
        try:
            logger.info(f"Loading SmolVLA model from: {self.checkpoint_path}")
            
            # Load configuration - handle extra fields in config.json
            import json
            config_path = self.checkpoint_path / "config.json"
            
            if config_path.exists():
                # Load config manually and filter out non-standard fields
                with open(config_path, 'r') as f:
                    config_dict = json.load(f)
                
                # Remove 'type' field if present (not part of SmolVLAConfig)
                config_dict.pop('type', None)
                
                # Create config from filtered dict
                config = SmolVLAConfig(**config_dict)
            else:
                # Fallback to standard loading
                config = SmolVLAConfig.from_pretrained(str(self.checkpoint_path))
            
            # Load policy
            self.policy = SmolVLAPolicy.from_pretrained(
                str(self.checkpoint_path),
                config=config
            )
            
            # Move to device
            self.policy.to(self.device)
            
            # Set to evaluation mode
            self.policy.eval()
            
            logger.info("SmolVLA model loaded successfully")
            
            # Perform warmup inference
            self._warmup()
            
        except Exception as e:
            logger.error(f"Failed to load SmolVLA model: {e}")
            raise SmolVLAError(f"Model loading failed: {e}")
    
    def _warmup(self):
        """
        Perform warmup inference to initialize CUDA kernels and caches.
        
        This reduces latency for the first real inference call.
        """
        if self.device == "cuda":
            logger.info("Performing model warmup...")
            try:
                # Create dummy observation
                dummy_obs = self._create_dummy_observation()
                
                # Run dummy inference
                with torch.no_grad():
                    # SmolVLA expects a batch of observations
                    _ = self.policy.select_action(dummy_obs)
                
                # Clear cache
                torch.cuda.empty_cache()
                
                logger.info("Model warmup complete")
            except Exception as e:
                # Warmup is optional - log but don't fail
                logger.debug(f"Warmup skipped: {e}")
                pass
    
    def _create_dummy_observation(self) -> Dict[str, torch.Tensor]:
        """
        Create a dummy observation for warmup.
        
        Returns:
            Dictionary with dummy observation tensors
        """
        # Get image shape from config if available
        try:
            # Try to get image shape from input_features
            if hasattr(self.policy, 'config') and hasattr(self.policy.config, 'input_features'):
                # Find first visual input
                for key, feature in self.policy.config.input_features.items():
                    if 'image' in key.lower():
                        img_shape = feature['shape']
                        break
                else:
                    img_shape = [3, 256, 256]  # Default
            else:
                img_shape = [3, 256, 256]  # Default
        except Exception:
            img_shape = [3, 256, 256]  # Default fallback
        
        # Create dummy image
        dummy_image = torch.zeros(img_shape, dtype=torch.float32, device=self.device)
        
        # Create dummy robot state (6 joints)
        dummy_state = torch.zeros(6, dtype=torch.float32, device=self.device)
        
        return {
            "observation.images.camera1": dummy_image.unsqueeze(0),  # Add batch dimension
            "observation.state": dummy_state.unsqueeze(0),
            "task": ["dummy task"]  # Task as list of strings
        }
    
    def _init_camera(self):
        """
        Initialize camera for visual observations.
        
        This will be implemented when camera integration is added.
        For now, it's a placeholder.
        
        Raises:
            SmolVLAError: If camera initialization fails
        """
        if self.camera is not None:
            return  # Already initialized
        
        try:
            # TODO: Implement camera initialization
            # from lerobot.common.robot_devices.cameras.opencv import OpenCVCamera
            # self.camera = OpenCVCamera(camera_index=0, fps=30, width=640, height=480)
            # self.camera.connect()
            logger.warning("Camera initialization not yet implemented")
            self.camera = None
        except Exception as e:
            logger.error(f"Failed to initialize camera: {e}")
            raise SmolVLAError(f"Camera initialization failed: {e}")
    
    def validate_command(self, command: str) -> bool:
        """
        Validate that a command is in the trained task set.
        
        Args:
            command: The manipulation command to validate
            
        Returns:
            True if command is valid, False otherwise
        """
        return command in self.VALID_COMMANDS
    
    def execute(self, command: str, max_steps: int = 500) -> bool:
        """
        Execute a manipulation task using SmolVLA inference.
        
        This is the main entry point for executing manipulation commands.
        It runs the inference loop, capturing observations and executing
        predicted actions until the task is complete or max_steps is reached.
        
        Args:
            command: Natural language task description (must be in VALID_COMMANDS)
            max_steps: Maximum number of inference steps to execute
            
        Returns:
            True if execution completed successfully, False otherwise
            
        Raises:
            SmolVLAError: If command is invalid or execution fails critically
        """
        # Validate command
        if not self.validate_command(command):
            raise SmolVLAError(
                f"Invalid command: '{command}'. "
                f"Must be one of: {self.VALID_COMMANDS}"
            )
        
        # Ensure robot is connected
        if not self.robot_arm.connected:
            logger.info("Robot not connected, attempting to connect...")
            self.robot_arm.connect()
            if not self.robot_arm.connected:
                raise SmolVLAError("Failed to connect to robot arm")
        
        # Initialize camera if needed
        if self.camera is None:
            self._init_camera()
        
        logger.info(f"Starting SmolVLA execution: '{command}'")
        logger.info(f"Max steps: {max_steps}")
        
        try:
            # Execute the task
            success = self._execute_task(command, max_steps)
            
            if success:
                logger.info(f"Task completed successfully: '{command}'")
            else:
                logger.warning(f"Task did not complete within {max_steps} steps")
            
            # Return to home position
            logger.info("Returning to home position...")
            self.robot_arm.move_arm("idle")
            
            return success
            
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            # Emergency stop - return to safe position
            self._emergency_stop()
            return False
    
    def _execute_task(self, command: str, max_steps: int) -> bool:
        """
        Internal method to execute the task inference loop.
        
        Args:
            command: The manipulation command to execute
            max_steps: Maximum number of steps
            
        Returns:
            True if task completed, False if max steps reached
        """
        with torch.no_grad():
            for step in range(max_steps):
                # Capture current observation
                observation = self._get_observation()
                
                # Add task instruction
                observation["task"] = command
                
                # Run inference
                action = self.policy.select_action(observation)
                
                # Send action to robot
                self._send_action(action)
                
                # Check if task is complete
                if self._is_task_complete(observation, step):
                    logger.info(f"Task completed at step {step}")
                    return True
                
                # Small delay between steps
                time.sleep(0.033)  # ~30 FPS
        
        return False
    
    def _get_observation(self) -> Dict[str, torch.Tensor]:
        """
        Get current robot observation (image + state).
        
        Returns:
            Dictionary with observation tensors
        """
        # Get robot observation (includes joint positions)
        try:
            robot_obs = self.robot_arm.robot.get_observation()
            
            # Extract joint positions in order
            joint_names = [
                "shoulder_pan.pos",
                "shoulder_lift.pos",
                "elbow_flex.pos",
                "wrist_flex.pos",
                "wrist_roll.pos",
                "gripper.pos"
            ]
            
            # Build state vector from joint positions
            state_values = [robot_obs[name] for name in joint_names]
            state_tensor = torch.tensor(state_values, dtype=torch.float32, device=self.device)
            
        except Exception as e:
            logger.warning(f"Failed to get robot observation: {e}. Using zero state.")
            # Fallback to zero state
            state_tensor = torch.zeros(6, dtype=torch.float32, device=self.device)
        
        # TODO: Implement actual camera capture
        # For now, return dummy images
        if self.camera is not None:
            # image = self.camera.read()
            pass
        else:
            # Create dummy images (256x256x3 RGB) for each camera
            # This matches the training configuration
            dummy_image = np.zeros((256, 256, 3), dtype=np.uint8)
        
        # Convert image to tensor
        image_tensor = torch.from_numpy(dummy_image).permute(2, 0, 1).float().to(self.device)
        image_tensor = image_tensor / 255.0  # Normalize to [0, 1]
        
        # Ensure state has batch dimension
        if state_tensor.dim() == 1:
            state_tensor = state_tensor.unsqueeze(0)
        
        return {
            "observation.images.camera1": image_tensor.unsqueeze(0),  # Add batch dimension
            "observation.images.camera2": image_tensor.unsqueeze(0),  # Duplicate for now
            "observation.images.camera3": image_tensor.unsqueeze(0),  # Duplicate for now
            "observation.state": state_tensor
        }
    
    def _send_action(self, action: torch.Tensor):
        """
        Send predicted action to robot.
        
        Args:
            action: Action tensor from policy (shape: [batch, action_dim])
        """
        # Convert action tensor to robot command dictionary
        action_dict = self._action_to_dict(action)
        
        # Send to robot
        self.robot_arm.robot.send_action(action_dict)
    
    def _action_to_dict(self, action: torch.Tensor) -> Dict[str, float]:
        """
        Convert action tensor to SO101 command format.
        
        Args:
            action: Action tensor from policy
            
        Returns:
            Dictionary mapping joint names to positions
        """
        # Remove batch dimension if present
        if action.dim() > 1:
            action = action.squeeze(0)
        
        # Convert to numpy
        action_np = action.cpu().numpy()
        
        # Map action dimensions to joint names
        joint_names = [
            "shoulder_pan.pos",
            "shoulder_lift.pos",
            "elbow_flex.pos",
            "wrist_flex.pos",
            "wrist_roll.pos",
            "gripper.pos"
        ]
        
        # Create action dictionary
        action_dict = {
            name: float(action_np[i])
            for i, name in enumerate(joint_names)
        }
        
        return action_dict
    
    def _is_task_complete(self, observation: Dict[str, torch.Tensor], step: int) -> bool:
        """
        Determine if the task is complete.
        
        This is a simple heuristic based on step count. In a production system,
        this could use a learned termination classifier or other criteria.
        
        Args:
            observation: Current observation
            step: Current step number
            
        Returns:
            True if task should be considered complete
        """
        # Simple heuristic: assume task takes ~400 steps
        # This should be replaced with a learned termination condition
        return step >= 400
    
    def _emergency_stop(self):
        """
        Emergency stop: return robot to safe idle position.
        
        This is called when an error occurs during execution.
        """
        logger.warning("Emergency stop triggered")
        try:
            self.robot_arm.move_arm("idle")
            logger.info("Robot returned to safe position")
        except Exception as e:
            logger.error(f"Emergency stop failed: {e}")
    
    def cleanup(self):
        """
        Clean up resources (camera, GPU memory, etc.).
        
        Should be called when the executor is no longer needed.
        """
        logger.info("Cleaning up SmolVLA executor...")
        
        # Disconnect camera
        if hasattr(self, 'camera') and self.camera is not None:
            try:
                self.camera.disconnect()
            except Exception as e:
                logger.warning(f"Camera disconnect failed: {e}")
        
        # Clear GPU memory
        if hasattr(self, 'device') and self.device == "cuda":
            torch.cuda.empty_cache()
        
        logger.info("Cleanup complete")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self.cleanup()
        except Exception:
            # Silently ignore cleanup errors in destructor
            pass


def init_smolvla_executor(
    checkpoint_path: Optional[str] = None,
    robot_arm: Optional[MortisArm] = None,
    device: Optional[str] = None
) -> SmolVLAExecutor:
    """
    Factory function to initialize SmolVLA executor with environment configuration.
    
    Args:
        checkpoint_path: Path to model checkpoint (uses env var if not provided)
        robot_arm: Optional MortisArm instance
        device: Device to use (uses env var or auto-detect if not provided)
        
    Returns:
        Initialized SmolVLAExecutor instance
        
    Raises:
        SmolVLAError: If initialization fails
    """
    # Get checkpoint path from environment if not provided
    if checkpoint_path is None:
        checkpoint_path = os.getenv("SMOLVLA_CHECKPOINT_PATH")
        if checkpoint_path is None:
            raise SmolVLAError(
                "No checkpoint path provided and SMOLVLA_CHECKPOINT_PATH not set"
            )
    
    # Get device from environment if not provided
    if device is None:
        device = os.getenv("SMOLVLA_DEVICE")
    
    logger.info(f"Initializing SmolVLA executor with checkpoint: {checkpoint_path}")
    
    return SmolVLAExecutor(
        checkpoint_path=checkpoint_path,
        robot_arm=robot_arm,
        device=device
    )
