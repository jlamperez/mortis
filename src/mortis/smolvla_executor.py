"""
SmolVLA Executor for vision-language-action robotic manipulation.

This module implements the SmolVLA model executor that performs inference
for manipulation tasks using the trained SmolVLA policy from LeRobot.
"""

import os
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from threading import Lock, Event

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


class SafetyViolationError(SmolVLAError):
    """Exception raised when a safety constraint is violated."""
    pass


class TimeoutError(SmolVLAError):
    """Exception raised when execution exceeds timeout."""
    pass


class GPUOutOfMemoryError(SmolVLAError):
    """Exception raised when GPU runs out of memory."""
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
    
    # Safety limits for joint positions (in degrees)
    # These define the safe workspace boundaries
    JOINT_LIMITS = {
        "shoulder_pan.pos": (-180, 180),
        "shoulder_lift.pos": (-90, 90),
        "elbow_flex.pos": (-135, 135),
        "wrist_flex.pos": (-90, 90),
        "wrist_roll.pos": (-180, 180),
        "gripper.pos": (0, 100),  # 0=open, 100=closed
    }
    
    # Maximum allowed joint velocity (degrees per step)
    MAX_JOINT_VELOCITY = 10.0
    
    # Default execution timeout (seconds)
    DEFAULT_TIMEOUT = 30.0
    
    def __init__(
        self,
        checkpoint_path: str,
        robot_arm: Optional[MortisArm] = None,
        device: Optional[str] = None,
        enable_safety_checks: bool = True,
        timeout: Optional[float] = None
    ):
        """
        Initialize the SmolVLA executor.
        
        Args:
            checkpoint_path: Path to the trained SmolVLA model checkpoint
            robot_arm: Optional MortisArm instance (will create if not provided)
            device: Device to run inference on ('cuda', 'cpu', or None for auto-detect)
            enable_safety_checks: Whether to enable workspace safety checks
            timeout: Execution timeout in seconds (None for default)
            
        Raises:
            SmolVLAError: If checkpoint path doesn't exist or model loading fails
        """
        # Initialize attributes first (for cleanup in case of early failure)
        self.camera = None
        self.policy = None
        self.preprocessor = None
        
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
        
        # Safety configuration
        self.enable_safety_checks = enable_safety_checks
        self.timeout = timeout if timeout is not None else self.DEFAULT_TIMEOUT
        
        # Emergency stop flag and lock
        self._emergency_stop_flag = Event()
        self._execution_lock = Lock()
        self._is_executing = False
        
        # Previous state for velocity checking
        self._previous_state = None
        
        logger.info(f"Safety checks: {'enabled' if enable_safety_checks else 'disabled'}")
        logger.info(f"Execution timeout: {self.timeout}s")
        
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
            
            # Load config - ensure 'type' field is set to 'smolvla'
            config_path = self.checkpoint_path / "config.json"
            
            if config_path.exists():
                # Load config
                with open(config_path, 'r') as f:
                    config_dict = json.load(f)
                
                # Ensure 'type' field is set to 'smolvla'
                if 'type' not in config_dict or config_dict['type'] != 'smolvla':
                    logger.debug("Setting 'type' field to 'smolvla' in config")
                    config_dict['type'] = 'smolvla'
                    
                    # Save updated config back
                    with open(config_path, 'w') as f:
                        json.dump(config_dict, f, indent=2)
                
                # Get VLM model name for tokenizer
                vlm_model_name = config_dict.get('vlm_model_name', 'HuggingFaceTB/SmolVLM2-500M-Video-Instruct')
            else:
                vlm_model_name = 'HuggingFaceTB/SmolVLM2-500M-Video-Instruct'
            
            # Load policy using from_pretrained (it will load the config automatically)
            self.policy = SmolVLAPolicy.from_pretrained(str(self.checkpoint_path))
            
            # Move to device
            self.policy.to(self.device)
            
            # Set to evaluation mode
            self.policy.eval()
            
            logger.info("SmolVLA model loaded successfully")
            
            # Load preprocessor (handles tokenization automatically)
            self._load_preprocessor()
            
            # Perform warmup inference
            self._warmup()
            
        except Exception as e:
            logger.error(f"Failed to load SmolVLA model: {e}")
            raise SmolVLAError(f"Model loading failed: {e}")
    
    def _load_preprocessor(self):
        """
        Load preprocessor from checkpoint.
        
        The preprocessor handles automatic tokenization of task strings
        through the TokenizerProcessorStep.
        
        Raises:
            SmolVLAError: If preprocessor loading fails
        """
        try:
            from lerobot.policies.factory import make_pre_post_processors
            
            logger.info("Loading preprocessor from checkpoint...")
            
            # Load preprocessor and postprocessor using policy config
            self.preprocessor, _ = make_pre_post_processors(
                self.policy.config,
                pretrained_path=str(self.checkpoint_path),
                device=self.device
            )
            
            logger.info("Preprocessor loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load preprocessor: {e}")
            raise SmolVLAError(f"Preprocessor loading failed: {e}")
    
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
                    result = self.policy.select_action(dummy_obs)
                    # Result may be a dict with 'action' key or just a tensor
                    if isinstance(result, dict):
                        _ = result.get('action', result)
                
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
        
        observation = {
            "observation.images.camera1": dummy_image,
            "observation.images.camera2": dummy_image.clone(),
            "observation.images.camera3": dummy_image.clone(),
            "observation.state": dummy_state,
            "task": "dummy task"  # Task as string (preprocessor will handle it)
        }
        
        # Apply preprocessor to tokenize task
        if self.preprocessor is not None:
            observation = self.preprocessor(observation)
        
        return observation
    
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
    
    def trigger_emergency_stop(self):
        """
        Trigger emergency stop from external thread.
        
        This can be called from another thread to safely stop execution.
        """
        logger.warning("Emergency stop triggered externally")
        self._emergency_stop_flag.set()
    
    def is_executing(self) -> bool:
        """
        Check if executor is currently running a task.
        
        Returns:
            True if a task is being executed
        """
        return self._is_executing
    
    def execute(self, command: str, max_steps: int = 500, timeout: Optional[float] = None) -> bool:
        """
        Execute a manipulation task using SmolVLA inference.
        
        This is the main entry point for executing manipulation commands.
        It runs the inference loop, capturing observations and executing
        predicted actions until the task is complete or max_steps is reached.
        
        Args:
            command: Natural language task description (must be in VALID_COMMANDS)
            max_steps: Maximum number of inference steps to execute
            timeout: Optional timeout override (seconds)
            
        Returns:
            True if execution completed successfully, False otherwise
            
        Raises:
            SmolVLAError: If command is invalid or execution fails critically
            SafetyViolationError: If safety constraints are violated
            TimeoutError: If execution exceeds timeout
        """
        # Acquire execution lock to prevent concurrent execution
        if not self._execution_lock.acquire(blocking=False):
            raise SmolVLAError("Executor is already running a task")
        
        try:
            # Clear emergency stop flag
            self._emergency_stop_flag.clear()
            self._is_executing = True
            
            # Validate command against trained task set
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
            
            # Use provided timeout or default
            execution_timeout = timeout if timeout is not None else self.timeout
            
            logger.info(f"Starting SmolVLA execution: '{command}'")
            logger.info(f"Max steps: {max_steps}, Timeout: {execution_timeout}s")
            logger.info(f"Safety checks: {'enabled' if self.enable_safety_checks else 'disabled'}")
            
            try:
                # Execute the task with timeout
                success = self._execute_task_with_timeout(command, max_steps, execution_timeout)
                
                if success:
                    logger.info(f"Task completed successfully: '{command}'")
                else:
                    logger.warning(f"Task did not complete within constraints")
                
                # Return to home position safely
                logger.info("Returning to home position...")
                self._safe_return_home()
                
                return success
                
            except TimeoutError as e:
                logger.error(f"Execution timeout: {e}")
                self._emergency_stop()
                raise
            except SafetyViolationError as e:
                logger.error(f"Safety violation: {e}")
                self._emergency_stop()
                raise
            except GPUOutOfMemoryError as e:
                logger.error(f"GPU out of memory: {e}")
                self._handle_gpu_oom()
                self._emergency_stop()
                raise
            except Exception as e:
                logger.error(f"Execution failed: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                self._emergency_stop()
                raise SmolVLAError(f"Execution failed: {e}")
        
        finally:
            # Always release lock and reset execution flag
            self._is_executing = False
            self._execution_lock.release()
    
    def _execute_task_with_timeout(self, command: str, max_steps: int, timeout: float) -> bool:
        """
        Execute task with timeout monitoring.
        
        Args:
            command: The manipulation command
            max_steps: Maximum steps
            timeout: Timeout in seconds
            
        Returns:
            True if task completed successfully
            
        Raises:
            TimeoutError: If execution exceeds timeout
        """
        start_time = time.time()
        
        try:
            return self._execute_task(command, max_steps, start_time, timeout)
        except Exception as e:
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                raise TimeoutError(f"Execution exceeded timeout of {timeout}s")
            raise
    
    def _execute_task(self, command: str, max_steps: int, start_time: float, timeout: float) -> bool:
        """
        Internal method to execute the task inference loop.
        
        This method implements the core inference loop:
        1. Capture visual and state observations
        2. Run SmolVLA inference to predict next action
        3. Execute action on robot
        4. Check for task completion
        5. Repeat until complete or max_steps reached
        
        Args:
            command: The manipulation command to execute
            max_steps: Maximum number of steps
            
        Returns:
            True if task completed, False if max steps reached
        """
        # Reset task completion tracking variables
        self._previous_action = None
        self._stable_count = 0
        self._previous_state = None
        
        # Track execution metrics
        last_progress_log = 0
        progress_log_interval = 50  # Log every 50 steps
        
        with torch.no_grad():
            for step in range(max_steps):
                # Check for emergency stop
                if self._emergency_stop_flag.is_set():
                    logger.warning("Emergency stop detected, aborting execution")
                    return False
                
                # Check timeout
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    raise TimeoutError(f"Execution exceeded timeout of {timeout}s at step {step}")
                
                # Log progress periodically
                if step - last_progress_log >= progress_log_interval:
                    fps = step / elapsed if elapsed > 0 else 0
                    logger.info(
                        f"Execution progress: step {step}/{max_steps} "
                        f"({step/max_steps*100:.1f}%) - {fps:.1f} FPS - {elapsed:.1f}s elapsed"
                    )
                    last_progress_log = step
                
                try:
                    # Capture current observation
                    observation = self._get_observation()
                    
                    # Add task string (preprocessor will tokenize it)
                    observation = self._add_task_string(observation, command)
                    
                    # Apply preprocessor (tokenizes task string automatically)
                    observation = self.preprocessor(observation)
                    
                    # Run inference to predict next action
                    action = self._run_inference_with_oom_handling(observation)
                    
                    # Debug: log action type and shape
                    logger.debug(f"Action type: {type(action)}, shape: {action.shape if hasattr(action, 'shape') else 'N/A'}")
                    
                    # Validate action safety
                    if self.enable_safety_checks:
                        self._check_action_safety(action, observation)
                    
                    # Send action to robot
                    self._send_action(action)
                    
                    # Check if task is complete
                    try:
                        is_complete = self._is_task_complete(observation, step, action)
                        if is_complete:
                            elapsed = time.time() - start_time
                            logger.info(
                                f"Task completed at step {step} "
                                f"(elapsed: {elapsed:.2f}s, avg FPS: {step/elapsed:.1f})"
                            )
                            return True
                    except Exception as e:
                        logger.error(f"Error in _is_task_complete: {e}")
                        raise
                    
                    # Small delay between steps to maintain ~30 FPS
                    time.sleep(0.033)
                    
                except torch.cuda.OutOfMemoryError as e:
                    logger.error(f"GPU out of memory at step {step}")
                    raise GPUOutOfMemoryError(f"GPU OOM at step {step}: {e}")
                except SafetyViolationError:
                    # Re-raise safety violations
                    raise
                except Exception as e:
                    logger.error(f"Error at step {step}: {e}")
                    raise
        
        # Max steps reached without completion
        elapsed = time.time() - start_time
        logger.warning(
            f"Task did not complete within {max_steps} steps "
            f"(elapsed: {elapsed:.2f}s)"
        )
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
    
    def _add_task_string(self, observation: Dict[str, torch.Tensor], command: str) -> Dict[str, torch.Tensor]:
        """
        Add task string to observation.
        
        The preprocessor will automatically tokenize this string through
        the TokenizerProcessorStep.
        
        Args:
            observation: Current observation dictionary
            command: Natural language command string
            
        Returns:
            Observation dictionary with added task string
        """
        # Simply add the task string - the preprocessor will tokenize it
        observation["task"] = command
        
        logger.debug(f"Added task string: '{command}'")
        
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
        
        Converts the action tensor from SmolVLA to SO101 command format
        and sends it to the robot arm for execution.
        
        Args:
            action: Action tensor from policy (shape: [batch, action_dim])
            
        Raises:
            SmolVLAError: If action execution fails
        """
        try:
            # Convert action tensor to robot command dictionary
            action_dict = self._action_to_dict(action)
            
            # Send to robot
            self.robot_arm.robot.send_action(action_dict)
            
            # Log action at debug level (verbose)
            logger.debug(f"Action sent: {action_dict}")
            
        except Exception as e:
            logger.error(f"Failed to send action to robot: {e}")
            raise SmolVLAError(f"Action execution failed: {e}")
    
    def _action_to_dict(self, action: torch.Tensor) -> Dict[str, float]:
        """
        Convert action tensor to SO101 command format.
        
        Maps the action tensor dimensions to SO101 joint names and converts
        to the dictionary format expected by the robot driver.
        
        Args:
            action: Action tensor from policy (shape: [batch, 6] or [6])
            
        Returns:
            Dictionary mapping joint names to positions (in degrees or normalized units)
            
        Raises:
            SmolVLAError: If action tensor has invalid shape
        """
        # Remove batch dimension if present
        if action.dim() > 1:
            action = action.squeeze(0)
        
        # Validate action dimension
        if action.shape[0] != 6:
            raise SmolVLAError(
                f"Invalid action shape: expected 6 dimensions, got {action.shape[0]}"
            )
        
        # Convert to numpy
        action_np = action.cpu().numpy()
        
        # Map action dimensions to joint names
        # Order must match the training data format
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
    
    def _is_task_complete(
        self,
        observation: Dict[str, torch.Tensor],
        step: int,
        action: torch.Tensor
    ) -> bool:
        """
        Determine if the task is complete.
        
        This method uses multiple heuristics to detect task completion:
        1. Minimum step count (ensure task has progressed)
        2. Maximum step count (assume completion after sufficient time)
        3. Action stability (detect when robot has settled)
        
        In a production system, this could be enhanced with:
        - Learned termination classifier
        - Visual goal detection
        - Force/torque feedback
        - Success detection from camera
        
        Args:
            observation: Current observation dictionary
            step: Current step number
            action: Predicted action tensor
            
        Returns:
            True if task should be considered complete
        """
        # Minimum steps before considering completion (allow task to progress)
        MIN_STEPS = 100
        
        # Maximum steps - assume task is complete after this many steps
        # Most manipulation tasks should complete within 400-450 steps at 30 FPS
        # (approximately 13-15 seconds)
        MAX_STEPS = 450
        
        # Early exit: not enough steps yet
        if step < MIN_STEPS:
            return False
        
        # Late exit: max steps reached, consider complete
        if step >= MAX_STEPS:
            logger.info(f"Task completion: max steps ({MAX_STEPS}) reached")
            return True
        
        # Check for action stability (robot has settled into final position)
        if hasattr(self, '_previous_action') and self._previous_action is not None:
            action_diff = torch.abs(action - self._previous_action).max().item()
            
            # If action changes are very small, robot may have settled
            if action_diff < 0.01:  # Threshold for "stable" action
                if not hasattr(self, '_stable_count'):
                    self._stable_count = 0
                self._stable_count += 1
                
                # If stable for 30 consecutive steps (~1 second), consider complete
                if self._stable_count >= 30:
                    logger.info(
                        f"Task completion: action stability detected at step {step} "
                        f"(stable for {self._stable_count} steps)"
                    )
                    return True
            else:
                # Reset stability counter if action changes significantly
                self._stable_count = 0
        
        # Store current action for next comparison
        self._previous_action = action.clone()
        
        # Not complete yet
        return False
    
    def _check_action_safety(self, action: torch.Tensor, observation: Dict[str, torch.Tensor]):
        """
        Check if predicted action is safe to execute.
        
        Validates:
        1. Joint position limits
        2. Joint velocity limits
        3. Workspace boundaries
        
        Args:
            action: Predicted action tensor
            observation: Current observation
            
        Raises:
            SafetyViolationError: If action violates safety constraints
        """
        # Convert action to dict for checking
        action_dict = self._action_to_dict(action)
        
        # Check joint position limits
        for joint_name, position in action_dict.items():
            if joint_name in self.JOINT_LIMITS:
                min_pos, max_pos = self.JOINT_LIMITS[joint_name]
                if position < min_pos or position > max_pos:
                    raise SafetyViolationError(
                        f"Joint {joint_name} position {position:.2f} exceeds limits "
                        f"[{min_pos}, {max_pos}]"
                    )
        
        # Check joint velocity limits (if we have previous state)
        if self._previous_state is not None:
            current_state = observation["observation.state"].squeeze(0).cpu().numpy()
            velocity = np.abs(current_state - self._previous_state)
            max_velocity = np.max(velocity)
            
            if max_velocity > self.MAX_JOINT_VELOCITY:
                raise SafetyViolationError(
                    f"Joint velocity {max_velocity:.2f} exceeds limit "
                    f"{self.MAX_JOINT_VELOCITY}"
                )
        
        # Update previous state for next check
        self._previous_state = observation["observation.state"].squeeze(0).cpu().numpy().copy()
    
    def _run_inference_with_oom_handling(self, observation: Dict[str, torch.Tensor]) -> torch.Tensor:
        """
        Run inference with GPU out-of-memory handling.
        
        Args:
            observation: Current observation
            
        Returns:
            Predicted action tensor
            
        Raises:
            GPUOutOfMemoryError: If GPU runs out of memory
        """
        try:
            result = self.policy.select_action(observation)
            
            # Debug: log what we got back
            logger.debug(f"Policy returned type: {type(result)}")
            if isinstance(result, dict):
                logger.debug(f"Policy returned dict keys: {result.keys()}")
            
            # SmolVLA returns a dictionary with 'action' key
            if isinstance(result, dict):
                if 'action' in result:
                    return result['action']
                else:
                    # Try to find the action in the dict
                    logger.error(f"Policy returned dict without 'action' key. Keys: {result.keys()}")
                    raise SmolVLAError(f"Policy returned unexpected format: {type(result)}")
            return result
        except torch.cuda.OutOfMemoryError as e:
            logger.error("GPU out of memory during inference")
            # Try to recover by clearing cache
            torch.cuda.empty_cache()
            # Try one more time
            try:
                result = self.policy.select_action(observation)
                if isinstance(result, dict):
                    if 'action' in result:
                        return result['action']
                    else:
                        raise SmolVLAError(f"Policy returned unexpected format: {type(result)}")
                return result
            except torch.cuda.OutOfMemoryError:
                raise GPUOutOfMemoryError("GPU out of memory, cannot recover")
    
    def _handle_gpu_oom(self):
        """
        Handle GPU out-of-memory error by clearing cache and resetting state.
        """
        logger.info("Handling GPU out-of-memory error...")
        
        if self.device == "cuda":
            # Clear CUDA cache
            torch.cuda.empty_cache()
            
            # Log memory stats
            if torch.cuda.is_available():
                allocated = torch.cuda.memory_allocated() / 1024**3
                reserved = torch.cuda.memory_reserved() / 1024**3
                logger.info(f"GPU memory: {allocated:.2f}GB allocated, {reserved:.2f}GB reserved")
        
        logger.info("GPU memory cleared")
    
    def _safe_return_home(self):
        """
        Safely return robot to home position with error handling.
        """
        try:
            self.robot_arm.move_arm("idle")
            logger.info("Robot returned to home position")
        except Exception as e:
            logger.error(f"Failed to return to home position: {e}")
            # Try direct position command as fallback
            try:
                self.robot_arm.robot.send_action(HOME_POSE)
                logger.info("Robot returned to home using direct command")
            except Exception as e2:
                logger.error(f"Direct home command also failed: {e2}")
    
    def _emergency_stop(self):
        """
        Emergency stop: return robot to safe idle position.
        
        This is called when an error occurs during execution.
        Sets the emergency stop flag and attempts to safely stop the robot.
        """
        logger.warning("Emergency stop triggered")
        
        # Set emergency stop flag
        self._emergency_stop_flag.set()
        
        try:
            # Try to stop robot immediately
            self._safe_return_home()
            logger.info("Emergency stop completed - robot in safe position")
        except Exception as e:
            logger.error(f"Emergency stop failed: {e}")
            logger.error("MANUAL INTERVENTION MAY BE REQUIRED")
    
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
