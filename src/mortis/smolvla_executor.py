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
from PIL import Image as PILImage

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
        # Create dummy state
        dummy_state = torch.zeros(1, 6, dtype=torch.float32, device=self.device)
        
        # Create dummy images
        dummy_image = self._create_dummy_image()
        
        return {
            "observation.images.camera1": dummy_image,
            "observation.images.camera2": dummy_image.clone(),
            "observation.images.camera3": dummy_image.clone(),
            "observation.state": dummy_state,
            "task": ["dummy task"]  # Task as list of strings
        }
    
    def _init_camera(self):
        """
        Initialize camera for visual observations.
        
        Attempts to initialize cameras in the following order:
        1. Intel RealSense camera (if available)
        2. OpenCV camera (fallback)
        
        Raises:
            SmolVLAError: If camera initialization fails
        """
        if self.camera is not None:
            return  # Already initialized
        
        try:
            # Try Intel RealSense first (preferred for depth sensing)
            try:
                from lerobot.common.robot_devices.cameras.intelrealsense import IntelRealSenseCamera
                logger.info("Attempting to initialize Intel RealSense camera...")
                self.camera = IntelRealSenseCamera(
                    camera_index=0,
                    fps=30,
                    width=640,
                    height=480,
                    use_depth=False  # RGB only for now
                )
                self.camera.connect()
                logger.info("Intel RealSense camera initialized successfully")
                return
            except Exception as e:
                logger.debug(f"Intel RealSense not available: {e}")
            
            # Fallback to OpenCV camera
            try:
                from lerobot.common.robot_devices.cameras.opencv import OpenCVCamera
                logger.info("Attempting to initialize OpenCV camera...")
                self.camera = OpenCVCamera(
                    camera_index=0,
                    fps=30,
                    width=640,
                    height=480
                )
                self.camera.connect()
                logger.info("OpenCV camera initialized successfully")
                return
            except Exception as e:
                logger.debug(f"OpenCV camera not available: {e}")
            
            # If both fail, log warning but don't raise error
            # This allows the system to run with dummy images for testing
            logger.warning("No camera available. Using dummy images for observations.")
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
        
        Captures:
        - Visual observations from camera(s)
        - Robot joint state (positions)
        
        Returns:
            Dictionary with observation tensors formatted for SmolVLA:
            - observation.images.camera1: RGB image tensor [1, 3, H, W]
            - observation.images.camera2: RGB image tensor [1, 3, H, W] (if available)
            - observation.images.camera3: RGB image tensor [1, 3, H, W] (if available)
            - observation.state: Joint positions tensor [1, 6]
        """
        # 1. Capture robot state
        state_tensor = self._capture_robot_state()
        
        # 2. Capture visual observations
        image_tensors = self._capture_camera_images()
        
        # 3. Format observation dictionary for SmolVLA
        observation = {
            "observation.state": state_tensor
        }
        
        # Add camera images
        for i, img_tensor in enumerate(image_tensors, start=1):
            observation[f"observation.images.camera{i}"] = img_tensor
        
        return observation
    
    def _capture_robot_state(self) -> torch.Tensor:
        """
        Capture current robot joint state.
        
        Returns:
            Tensor of joint positions [1, 6] with batch dimension
        """
        try:
            # Get robot observation (includes joint positions)
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
            state_tensor = torch.tensor(
                state_values,
                dtype=torch.float32,
                device=self.device
            )
            
            # Add batch dimension
            state_tensor = state_tensor.unsqueeze(0)
            
            logger.debug(f"Robot state captured: {state_values}")
            
        except Exception as e:
            logger.warning(f"Failed to get robot observation: {e}. Using zero state.")
            # Fallback to zero state with batch dimension
            state_tensor = torch.zeros(1, 6, dtype=torch.float32, device=self.device)
        
        return state_tensor
    
    def _capture_camera_images(self) -> list:
        """
        Capture images from available cameras.
        
        Returns:
            List of image tensors [1, 3, H, W] with batch dimension
        """
        image_tensors = []
        
        if self.camera is not None:
            try:
                # Read image from camera
                image = self.camera.read()
                
                # Convert to tensor and preprocess
                image_tensor = self._preprocess_image(image)
                
                # Add to list (camera1)
                image_tensors.append(image_tensor)
                
                logger.debug(f"Camera image captured: shape={image.shape}")
                
            except Exception as e:
                logger.warning(f"Failed to capture camera image: {e}. Using dummy image.")
                # Fallback to dummy image
                image_tensors.append(self._create_dummy_image())
        else:
            # No camera available, use dummy image
            logger.debug("No camera available, using dummy image")
            image_tensors.append(self._create_dummy_image())
        
        # For now, duplicate the first image for camera2 and camera3
        # In a multi-camera setup, these would be separate captures
        while len(image_tensors) < 3:
            image_tensors.append(image_tensors[0].clone())
        
        return image_tensors
    
    def _preprocess_image(self, image: np.ndarray) -> torch.Tensor:
        """
        Preprocess camera image for SmolVLA input.
        
        Args:
            image: Raw image from camera (H, W, 3) in BGR or RGB format
            
        Returns:
            Preprocessed image tensor [1, 3, H, W] with batch dimension
        """
        # Convert BGR to RGB if needed (OpenCV uses BGR)
        if image.shape[2] == 3:
            # Assume BGR from OpenCV, convert to RGB
            image = image[:, :, ::-1].copy()
        
        # Resize to expected input size (256x256 based on training config)
        pil_image = PILImage.fromarray(image)
        pil_image = pil_image.resize((256, 256), PILImage.BILINEAR)
        image = np.array(pil_image)
        
        # Convert to tensor: (H, W, C) -> (C, H, W)
        image_tensor = torch.from_numpy(image).permute(2, 0, 1).float()
        
        # Normalize to [0, 1]
        image_tensor = image_tensor / 255.0
        
        # Move to device
        image_tensor = image_tensor.to(self.device)
        
        # Add batch dimension
        image_tensor = image_tensor.unsqueeze(0)
        
        return image_tensor
    
    def _create_dummy_image(self) -> torch.Tensor:
        """
        Create a dummy image tensor for testing without camera.
        
        Returns:
            Dummy image tensor [1, 3, 256, 256] with batch dimension
        """
        # Create black image
        dummy_image = torch.zeros(1, 3, 256, 256, dtype=torch.float32, device=self.device)
        return dummy_image
    
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
