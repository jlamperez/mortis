"""
LeRobot async inference client wrapper for Mortis manipulation tasks.

This module provides a high-level interface to LeRobot's async inference system
(PolicyServer + RobotClient) for executing SmolVLA manipulation tasks while
keeping the Gradio UI responsive.

Architecture:
- PolicyServer: Runs in a separate thread, loads SmolVLA model, performs inference
- RobotClient: Controls the SO101 robot, captures observations, executes actions
- This wrapper: Manages lifecycle and provides simple API for Mortis
"""

import logging
import threading
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, Callable

from lerobot.robots.so101_follower import SO101FollowerConfig
from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig
from lerobot.cameras.realsense import RealSenseCameraConfig
from lerobot.async_inference.configs import PolicyServerConfig, RobotClientConfig
from lerobot.async_inference.policy_server import serve
from lerobot.async_inference.robot_client import RobotClient


logger = logging.getLogger(__name__)


class ManipulationStatus(Enum):
    """Status of a manipulation task execution."""
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"
    STOPPED = "stopped"


@dataclass
class ManipulationTask:
    """
    Represents a manipulation task for LeRobot async execution.
    
    Attributes:
        task: Natural language task description
        max_steps: Maximum number of action steps to execute
        started_at: Timestamp when task started
        completed_at: Timestamp when task completed
        status: Current task status
        error: Error message if task failed
    """
    task: str
    max_steps: int = 1000  # At 30fps, ~33 seconds of execution
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    status: ManipulationStatus = ManipulationStatus.IDLE
    error: Optional[str] = None
    
    @property
    def duration(self) -> Optional[float]:
        """Get task execution duration in seconds."""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None


class LeRobotAsyncClient:
    """
    High-level wrapper for LeRobot async inference system.
    
    This class manages the PolicyServer and RobotClient lifecycle, providing
    a simple interface for executing manipulation tasks asynchronously.
    
    Usage:
        # Create client
        client = LeRobotAsyncClient(
            robot_port="/dev/ttyACM1",
            model_path="jlamperez/kiroween-potion-smolvla",
            camera_configs={...}
        )
        
        # Start the system
        client.start()
        
        # Execute a task
        client.execute_task("Pick up the skull and place it in the green cup")
        
        # Check status
        status = client.get_status()
        
        # Stop when done
        client.stop()
    """
    
    def __init__(
        self,
        robot_port: str = "/dev/ttyACM1",
        robot_id: str = "my_follower_robot_arm",  # Must match calibration file name
        model_path: str = "jlamperez/kiroween-potion-smolvla",
        policy_device: str = "cuda",
        camera_configs: Optional[Dict[str, Any]] = None,
        server_host: str = "127.0.0.1",
        server_port: int = 8080,
        actions_per_chunk: int = 50,
        chunk_size_threshold: float = 0.5,
        aggregate_fn_name: str = "weighted_average",
    ):
        """
        Initialize the LeRobot async client.
        
        Args:
            robot_port: Serial port for SO101 robot (e.g., "/dev/ttyACM1")
            robot_id: Identifier for the robot
            model_path: HuggingFace model path or local checkpoint
            policy_device: Device for model inference ("cuda" or "cpu")
            camera_configs: Dictionary of camera configurations
            server_host: PolicyServer host address
            server_port: PolicyServer port
            actions_per_chunk: Number of actions per inference chunk
            chunk_size_threshold: Threshold for action chunk aggregation
            aggregate_fn_name: Function name for aggregating action chunks
        """
        self.robot_port = robot_port
        self.robot_id = robot_id
        self.model_path = model_path
        self.policy_device = policy_device
        self.server_host = server_host
        self.server_port = server_port
        self.actions_per_chunk = actions_per_chunk
        self.chunk_size_threshold = chunk_size_threshold
        self.aggregate_fn_name = aggregate_fn_name
        
        # Use default camera configs if not provided
        self.camera_configs = camera_configs or self._get_default_camera_configs()
        
        # Server and client instances
        self.server_thread: Optional[threading.Thread] = None
        self.robot_client: Optional[RobotClient] = None
        self.action_receiver_thread: Optional[threading.Thread] = None
        self.control_thread: Optional[threading.Thread] = None
        
        # Current task tracking
        self.current_task: Optional[ManipulationTask] = None
        self._running = False
        self._stop_event = threading.Event()
        self._task_stop_event = threading.Event()  # Event to signal task cancellation
        self._idle_callback: Optional[Callable] = None  # Callback to move robot to idle
        
        logger.info(f"LeRobotAsyncClient initialized with model: {model_path}")
    
    def _get_default_camera_configs(self) -> Dict[str, Any]:
        """
        Get default camera configuration for Mortis setup.
        
        IMPORTANT: This configuration MUST match the cameras used during training!
        If you trained with IntelRealSense + OpenCV, use the same setup here.
        
        Returns:
            Dictionary of camera configurations
        """
        # Default camera configuration matching training setup
        # This should match your training configuration exactly!
        
        # Configuration with RealSense + OpenCV (matches training setup)
        return {
            "camera1": RealSenseCameraConfig(
                serial_number_or_name="030522070314",
                width=640,
                height=480,
                fps=30
            ),
            "camera2": OpenCVCameraConfig(
                index_or_path=8,
                width=640,
                height=480,
                fps=30
            )
        }
    
    def start(self) -> bool:
        """
        Start the PolicyServer only.
        
        The RobotClient will be created lazily when the first task is executed.
        This avoids loading the model unnecessarily at startup.
        
        Returns:
            True if startup successful, False otherwise
        """
        if self._running:
            logger.warning("LeRobotAsyncClient is already running")
            return True
        
        try:
            logger.info("Starting PolicyServer...")
            
            # Configure and start PolicyServer
            server_config = PolicyServerConfig(
                host=self.server_host,
                port=self.server_port
            )
            
            self.server_thread = threading.Thread(
                target=serve,
                args=(server_config,),
                daemon=True,
                name="PolicyServer"
            )
            self.server_thread.start()
            
            # Give server time to start
            time.sleep(2.0)
            logger.info(f"PolicyServer started on {self.server_host}:{self.server_port}")
            
            self._running = True
            self._stop_event.clear()
            
            logger.info("LeRobotAsyncClient started (RobotClient will be created on first task)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start LeRobotAsyncClient: {e}", exc_info=True)
            self.stop()
            return False
    
    def stop(self) -> None:
        """
        Stop the PolicyServer and RobotClient.
        
        This method gracefully shuts down all components.
        """
        if not self._running:
            logger.warning("LeRobotAsyncClient is not running")
            return
        
        logger.info("Stopping LeRobotAsyncClient...")
        
        self._running = False
        self._stop_event.set()
        
        # Stop control thread if running
        if self.control_thread and self.control_thread.is_alive():
            logger.info("Waiting for control thread to finish...")
            self.control_thread.join(timeout=5.0)
        
        # Stop robot client
        if self.robot_client:
            try:
                self.robot_client.stop()
                logger.info("RobotClient stopped")
            except Exception as e:
                logger.error(f"Error stopping RobotClient: {e}")
        
        # Action receiver thread should stop automatically (daemon)
        # Server thread should stop automatically (daemon)
        
        self.robot_client = None
        self.server_thread = None
        self.action_receiver_thread = None
        self.control_thread = None
        
        logger.info("LeRobotAsyncClient stopped")
    
    def execute_task(
        self,
        task: str,
        max_steps: int = 1000,
        blocking: bool = False,
        timeout: float = 60.0
    ) -> bool:
        """
        Execute a manipulation task asynchronously.
        
        This method stops any running task and creates a fresh RobotClient
        for the new task, ensuring clean state.
        
        Args:
            task: Natural language task description
            max_steps: Maximum number of action steps
            blocking: If True, wait for task to complete before returning
            timeout: Maximum execution time in seconds (default: 60.0)
            
        Returns:
            True if task started successfully, False otherwise
        """
        if not self._running:
            logger.error("Cannot execute task: client not running")
            return False
        
        # Always need a fresh client for each task because control_loop can only run once
        # But we keep the PolicyServer alive so the model stays loaded
        need_new_client = True
        
        if self.robot_client is None:
            # First task - need to create client
            logger.info("First task - creating RobotClient...")
        elif self.current_task and self.current_task.status == ManipulationStatus.RUNNING:
            # Task is running - stop it first
            logger.info(f"Stopping previous task: {self.current_task.task}")
            self._stop_robot_client()
        else:
            # Previous task finished - recreate client for new task
            logger.info("Recreating RobotClient for new task (PolicyServer keeps model loaded)")
        
        # Wait for previous control thread to finish
        if self.control_thread and self.control_thread.is_alive():
            logger.info("Waiting for previous control thread to finish...")
            self.control_thread.join(timeout=3.0)
            if self.control_thread.is_alive():
                logger.warning("Previous control thread still running, proceeding anyway")
        
        # Create new task
        self.current_task = ManipulationTask(
            task=task,
            max_steps=max_steps,
            status=ManipulationStatus.STARTING
        )
        
        # Clear any previous stop signal
        self._task_stop_event.clear()
        
        logger.info(f"Executing task: {task}")
        logger.info(f"Limits: max_steps={max_steps}, timeout={timeout}s")
        
        # Create/recreate robot client only if needed
        if need_new_client:
            if not self._recreate_robot_client(task):
                logger.error("Failed to create robot client")
                self.current_task.status = ManipulationStatus.FAILED
                self.current_task.error = "Failed to initialize robot client"
                return False
        
        # Start control loop in separate thread
        self.control_thread = threading.Thread(
            target=self._run_control_loop,
            args=(task, max_steps, timeout),
            daemon=True,
            name="ControlLoop"
        )
        self.control_thread.start()
        
        if blocking:
            self.control_thread.join()
        
        return True
    
    def _stop_robot_client(self) -> None:
        """
        Stop the robot client cleanly.
        
        This stops the robot client and waits for threads to finish.
        """
        if self.robot_client:
            try:
                logger.info("Stopping robot client...")
                self.robot_client.stop()
                
                # Wait for action receiver thread
                if self.action_receiver_thread and self.action_receiver_thread.is_alive():
                    self.action_receiver_thread.join(timeout=2.0)
                
                logger.info("Robot client stopped")
            except Exception as e:
                logger.error(f"Error stopping robot client: {e}")
    
    def _recreate_robot_client(self, task: str) -> bool:
        """
        Recreate the robot client with a new task.
        
        This creates a fresh RobotClient instance for the new task,
        ensuring clean state.
        
        Args:
            task: Task description for the new client
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Stop existing client if any
            self._stop_robot_client()
            
            # Small delay to ensure port is released
            time.sleep(0.5)
            
            # Reconfigure robot
            from pathlib import Path
            from lerobot.robots.so101_follower import SO101FollowerConfig
            from lerobot.async_inference.configs import RobotClientConfig
            from lerobot.async_inference.robot_client import RobotClient
            
            calibration_dir = Path(".cache/calibration/so101")
            robot_config = SO101FollowerConfig(
                port=self.robot_port,
                id=self.robot_id,
                cameras=self.camera_configs,
                calibration_dir=calibration_dir
            )
            
            client_config = RobotClientConfig(
                robot=robot_config,
                server_address=f"{self.server_host}:{self.server_port}",
                policy_device=self.policy_device,
                policy_type="smolvla",
                pretrained_name_or_path=self.model_path,
                chunk_size_threshold=self.chunk_size_threshold,
                actions_per_chunk=self.actions_per_chunk,
                aggregate_fn_name=self.aggregate_fn_name,
                task=task  # Set the task in the config
            )
            
            # Create new robot client
            self.robot_client = RobotClient(client_config)
            
            if not self.robot_client.start():
                raise RuntimeError("Failed to start RobotClient")
            
            # Start action receiver thread
            self.action_receiver_thread = threading.Thread(
                target=self.robot_client.receive_actions,
                daemon=True,
                name="ActionReceiver"
            )
            self.action_receiver_thread.start()
            
            logger.info("Robot client recreated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to recreate robot client: {e}", exc_info=True)
            return False
    
    def stop_current_task(self) -> bool:
        """
        Stop the currently running task by stopping the robot client.
        
        This cleanly stops the robot client, which will cause the control
        loop to exit. The client will be recreated for the next task.
        
        Returns:
            True if task was stopped successfully
        """
        if not self.current_task or self.current_task.status != ManipulationStatus.RUNNING:
            logger.warning("No task currently running to stop")
            return False
        
        logger.info("Stopping current task...")
        
        try:
            # Mark task as stopped
            self.current_task.status = ManipulationStatus.STOPPED
            self.current_task.completed_at = time.time()
            self.current_task.error = "Task stopped by user"
            
            # Signal task stop
            self._task_stop_event.set()
            
            # Stop the robot client (this will interrupt the control loop)
            try:
                self._stop_robot_client()
            except Exception as e:
                logger.warning(f"Error stopping client (expected): {e}")
            
            # Move robot to idle position
            if self._idle_callback:
                logger.info("Moving robot to idle position...")
                try:
                    self._idle_callback()
                    logger.info("Robot moved to idle position")
                except Exception as e:
                    logger.error(f"Failed to move to idle: {e}")
            
            logger.info("Task stopped successfully")
            
            # Clear the task after a delay
            def clear_task():
                time.sleep(3.0)
                if self.current_task and self.current_task.status == ManipulationStatus.STOPPED:
                    self.current_task = None
                    logger.info("Cleared stopped task from status")
            
            clear_thread = threading.Thread(target=clear_task, daemon=True)
            clear_thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop task: {e}", exc_info=True)
            return False
    
    def _run_control_loop(self, task: str, max_steps: int, timeout: float) -> None:
        """
        Run the control loop for task execution with timeout.
        
        This runs in a separate thread and executes the task using
        the RobotClient's control_loop method. The timeout will stop
        the task, and recreating the client for each task ensures clean state.
        
        Note: max_steps is not directly enforced by LeRobot's control_loop,
        but the timeout provides a time-based limit.
        
        Args:
            task: Task description
            max_steps: Maximum steps (informational, not enforced)
            timeout: Maximum execution time in seconds (default: 60.0)
        """
        if not self.current_task:
            return
        
        try:
            self.current_task.status = ManipulationStatus.RUNNING
            self.current_task.started_at = time.time()
            
            logger.info(f"Starting control loop for: {task}")
            logger.info(f"Timeout: {timeout}s (max_steps={max_steps} is informational)")
            
            # Clear task stop event
            self._task_stop_event.clear()
            
            # Run control_loop in a separate thread so we can timeout
            control_thread = threading.Thread(
                target=lambda: self.robot_client.control_loop(task=task, verbose=False),
                daemon=True,
                name="ControlLoopInner"
            )
            control_thread.start()
            
            # Wait for completion or timeout
            control_thread.join(timeout=timeout)
            
            # Check if thread is still alive (timeout occurred)
            if control_thread.is_alive():
                logger.warning(f"Task timed out after {timeout}s")
                
                # Mark task as stopped first
                self.current_task.status = ManipulationStatus.STOPPED
                self.current_task.completed_at = time.time()
                self.current_task.error = f"Task exceeded timeout of {timeout}s"
                
                # Signal stop event
                self._task_stop_event.set()
                
                # Stop the robot client to interrupt the control loop
                # This will cause the control thread to error out, but we catch it
                logger.info("Stopping robot client to interrupt control loop...")
                try:
                    self._stop_robot_client()
                except Exception as e:
                    logger.warning(f"Error stopping client (expected): {e}")
                
                # Wait a bit for thread to die
                control_thread.join(timeout=2.0)
                
                logger.info("Task stopped due to timeout")
                
                # Move robot to idle position using callback if provided
                if hasattr(self, '_idle_callback') and self._idle_callback:
                    logger.info("Moving robot to idle position...")
                    try:
                        self._idle_callback()
                        logger.info("Robot moved to idle position")
                    except Exception as e:
                        logger.error(f"Failed to move to idle: {e}")
                
                # Clear the task after a delay so UI can show the stopped status
                def clear_task():
                    time.sleep(3.0)  # Show stopped status for 3 seconds
                    if self.current_task and self.current_task.status == ManipulationStatus.STOPPED:
                        self.current_task = None
                        logger.info("Cleared stopped task from status")
                
                clear_thread = threading.Thread(target=clear_task, daemon=True)
                clear_thread.start()
                
            else:
                # Task completed successfully
                self.current_task.status = ManipulationStatus.COMPLETE
                self.current_task.completed_at = time.time()
                logger.info(f"Task completed in {self.current_task.duration:.2f}s")
                
                # Clear completed task after showing status
                def clear_task():
                    time.sleep(3.0)  # Show completed status for 3 seconds
                    if self.current_task and self.current_task.status == ManipulationStatus.COMPLETE:
                        self.current_task = None
                        logger.info("Cleared completed task from status")
                
                clear_thread = threading.Thread(target=clear_task, daemon=True)
                clear_thread.start()
            
        except KeyboardInterrupt:
            logger.info("Task interrupted by user")
            self.current_task.status = ManipulationStatus.STOPPED
            self.current_task.completed_at = time.time()
            
        except Exception as e:
            logger.error(f"Task failed: {e}", exc_info=True)
            self.current_task.status = ManipulationStatus.FAILED
            self.current_task.error = str(e)
            self.current_task.completed_at = time.time()
    
    def get_status(self) -> ManipulationStatus:
        """
        Get the current task status.
        
        Returns:
            Current ManipulationStatus
        """
        if self.current_task:
            return self.current_task.status
        return ManipulationStatus.IDLE
    
    def get_current_task(self) -> Optional[ManipulationTask]:
        """
        Get the currently executing task.
        
        Returns:
            Current ManipulationTask or None if idle
        """
        return self.current_task
    
    def is_busy(self) -> bool:
        """
        Check if a task is currently executing.
        
        Returns:
            True if a task is running
        """
        return (
            self.current_task is not None and
            self.current_task.status == ManipulationStatus.RUNNING
        )
    
    def is_running(self) -> bool:
        """
        Check if the client is running (server and robot connected).
        
        Returns:
            True if client is running
        """
        return self._running
    
    def set_idle_callback(self, callback: Callable) -> None:
        """
        Set a callback function to move the robot to idle position.
        
        This callback will be called when a task times out, to safely
        return the robot to a neutral position.
        
        Args:
            callback: Function to call (e.g., lambda: mortis_arm.move_arm("idle"))
        """
        self._idle_callback = callback
        logger.info("Idle callback configured")
    
    def __enter__(self):
        """Context manager entry: start the client."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit: stop the client."""
        self.stop()
        return False
