"""
Asynchronous task execution system for Mortis.

This module provides infrastructure for executing robot tasks asynchronously
in a background worker thread, allowing the Gradio UI to remain responsive
during long-running operations like SmolVLA inference.
"""

import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from queue import Queue, Empty
from threading import Thread, Event
from typing import Optional, Callable, Dict, Any


logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Status of a task in the execution queue."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


class TaskType(Enum):
    """Type of robot task to execute."""
    GESTURE = "gesture"
    MANIPULATION = "manipulation"


@dataclass
class Task:
    """
    Represents a robot task for asynchronous execution.
    
    Attributes:
        id: Unique identifier for the task
        type: Type of task (gesture or manipulation)
        status: Current execution status
        created_at: Timestamp when task was created
        started_at: Timestamp when task execution started
        completed_at: Timestamp when task execution completed
        error: Error message if task failed
        gesture: Gesture name for GESTURE type tasks
        command: Command string for MANIPULATION type tasks
        metadata: Additional task-specific data
    """
    id: str
    type: TaskType
    status: TaskStatus
    created_at: float
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error: Optional[str] = None
    
    # Task-specific data
    gesture: Optional[str] = None
    command: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def create_gesture_task(cls, gesture: str, metadata: Optional[Dict[str, Any]] = None) -> "Task":
        """
        Create a gesture execution task.
        
        Args:
            gesture: Name of the gesture to execute (e.g., "wave", "idle")
            metadata: Optional additional task data
            
        Returns:
            Task configured for gesture execution
        """
        task_id = f"gesture_{time.time()}"
        return cls(
            id=task_id,
            type=TaskType.GESTURE,
            status=TaskStatus.QUEUED,
            created_at=time.time(),
            gesture=gesture,
            metadata=metadata or {}
        )
    
    @classmethod
    def create_manipulation_task(cls, command: str, metadata: Optional[Dict[str, Any]] = None) -> "Task":
        """
        Create a manipulation execution task.
        
        Args:
            command: Natural language command for SmolVLA (e.g., "Pick up the skull")
            metadata: Optional additional task data
            
        Returns:
            Task configured for manipulation execution
        """
        task_id = f"manipulation_{time.time()}"
        return cls(
            id=task_id,
            type=TaskType.MANIPULATION,
            status=TaskStatus.QUEUED,
            created_at=time.time(),
            command=command,
            metadata=metadata or {}
        )
    
    def start(self) -> None:
        """Mark task as started and record start time."""
        self.status = TaskStatus.RUNNING
        self.started_at = time.time()
        logger.info(f"Task {self.id} started")
    
    def complete(self) -> None:
        """Mark task as completed and record completion time."""
        self.status = TaskStatus.COMPLETE
        self.completed_at = time.time()
        logger.info(f"Task {self.id} completed in {self.duration:.2f}s")
    
    def fail(self, error: str) -> None:
        """
        Mark task as failed and record error.
        
        Args:
            error: Error message describing the failure
        """
        self.status = TaskStatus.FAILED
        self.completed_at = time.time()
        self.error = error
        logger.error(f"Task {self.id} failed: {error}")
    
    @property
    def duration(self) -> Optional[float]:
        """
        Get task execution duration in seconds.
        
        Returns:
            Duration in seconds if task has started and completed, None otherwise
        """
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None
    
    @property
    def wait_time(self) -> float:
        """
        Get time task spent waiting in queue before execution.
        
        Returns:
            Wait time in seconds, or time since creation if not started
        """
        if self.started_at:
            return self.started_at - self.created_at
        return time.time() - self.created_at
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert task to dictionary representation.
        
        Returns:
            Dictionary containing task data
        """
        return {
            "id": self.id,
            "type": self.type.value,
            "status": self.status.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration": self.duration,
            "wait_time": self.wait_time,
            "error": self.error,
            "gesture": self.gesture,
            "command": self.command,
            "metadata": self.metadata
        }


@dataclass
class StatusUpdate:
    """
    Status update message from the async executor.
    
    Attributes:
        task_id: ID of the task this update relates to
        status: Current task status
        message: Human-readable status message
        progress: Optional progress percentage (0-100)
        error: Optional error message
        timestamp: When this update was created
    """
    task_id: str
    status: TaskStatus
    message: str
    progress: Optional[float] = None
    error: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert status update to dictionary."""
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "message": self.message,
            "progress": self.progress,
            "error": self.error,
            "timestamp": self.timestamp
        }


class AsyncExecutor:
    """
    Asynchronous task executor for robot operations.
    
    This class manages a background worker thread that processes robot tasks
    from a queue, allowing the main application thread (Gradio UI) to remain
    responsive during long-running operations.
    
    Attributes:
        task_queue: Queue of tasks waiting to be executed
        status_queue: Queue of status updates from the worker
        worker_thread: Background thread that processes tasks
        running: Flag indicating if the executor is running
        stop_event: Event to signal worker thread to stop
        task_executor: Callable that executes tasks
        current_task: Currently executing task (if any)
    """
    
    def __init__(self, task_executor: Optional[Callable[[Task], None]] = None):
        """
        Initialize the async executor.
        
        Args:
            task_executor: Optional callable that executes tasks. If not provided,
                          tasks will be logged but not executed (useful for testing).
        """
        self.task_queue: Queue[Task] = Queue()
        self.status_queue: Queue[StatusUpdate] = Queue()
        self.worker_thread: Optional[Thread] = None
        self.running: bool = False
        self.stop_event: Event = Event()
        self.task_executor: Optional[Callable[[Task], None]] = task_executor
        self.current_task: Optional[Task] = None
        
        logger.info("AsyncExecutor initialized")
    
    def start(self) -> None:
        """
        Start the background worker thread.
        
        This method starts a daemon thread that continuously processes tasks
        from the queue until stop() is called.
        
        Raises:
            RuntimeError: If the executor is already running
        """
        if self.running:
            raise RuntimeError("AsyncExecutor is already running")
        
        self.running = True
        self.stop_event.clear()
        self.worker_thread = Thread(target=self._worker_loop, daemon=True, name="AsyncExecutor")
        self.worker_thread.start()
        
        logger.info("AsyncExecutor started")
    
    def stop(self, timeout: float = 5.0) -> None:
        """
        Stop the background worker thread.
        
        This method signals the worker thread to stop and waits for it to finish.
        If the worker is currently executing a task, it will complete that task
        before stopping.
        
        Args:
            timeout: Maximum time to wait for worker to stop (seconds)
        """
        if not self.running:
            logger.warning("AsyncExecutor is not running")
            return
        
        logger.info("Stopping AsyncExecutor...")
        self.running = False
        self.stop_event.set()
        
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=timeout)
            
            if self.worker_thread.is_alive():
                logger.warning(f"Worker thread did not stop within {timeout}s timeout")
            else:
                logger.info("AsyncExecutor stopped")
        
        self.worker_thread = None
    
    def _worker_loop(self) -> None:
        """
        Main worker loop that processes tasks from the queue.
        
        This method runs in a background thread and continuously pulls tasks
        from the queue, executes them, and posts status updates.
        """
        logger.info("Worker thread started")
        
        while self.running:
            try:
                # Try to get a task from the queue (with timeout to check stop_event)
                try:
                    task = self.task_queue.get(timeout=1.0)
                except Empty:
                    # No task available, check if we should stop
                    if self.stop_event.is_set():
                        break
                    continue
                
                # Execute the task
                self._execute_task(task)
                
                # Mark task as done in queue
                self.task_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in worker loop: {e}", exc_info=True)
                # Continue processing other tasks
                continue
        
        logger.info("Worker thread stopped")
    
    def _execute_task(self, task: Task) -> None:
        """
        Execute a single task and post status updates.
        
        Args:
            task: Task to execute
        """
        self.current_task = task
        
        try:
            # Mark task as started
            task.start()
            self._post_status(
                task.id,
                TaskStatus.RUNNING,
                f"Executing {task.type.value}: {task.gesture or task.command}"
            )
            
            # Execute the task using the provided executor
            if self.task_executor:
                self.task_executor(task)
            else:
                # No executor provided, just simulate execution
                logger.info(f"Simulating execution of task {task.id}")
                time.sleep(0.5)  # Simulate work
            
            # Mark task as complete
            task.complete()
            self._post_status(
                task.id,
                TaskStatus.COMPLETE,
                f"Completed {task.type.value}: {task.gesture or task.command}"
            )
            
        except Exception as e:
            # Mark task as failed
            error_msg = str(e)
            task.fail(error_msg)
            self._post_status(
                task.id,
                TaskStatus.FAILED,
                f"Failed {task.type.value}: {error_msg}",
                error=error_msg
            )
        
        finally:
            self.current_task = None
    
    def _post_status(
        self,
        task_id: str,
        status: TaskStatus,
        message: str,
        progress: Optional[float] = None,
        error: Optional[str] = None
    ) -> None:
        """
        Post a status update to the status queue.
        
        Args:
            task_id: ID of the task
            status: Current task status
            message: Human-readable status message
            progress: Optional progress percentage
            error: Optional error message
        """
        update = StatusUpdate(
            task_id=task_id,
            status=status,
            message=message,
            progress=progress,
            error=error
        )
        self.status_queue.put(update)
        logger.debug(f"Status update: {message}")
    
    def submit_task(self, task: Task) -> str:
        """
        Submit a task for asynchronous execution.
        
        Args:
            task: Task to execute
            
        Returns:
            Task ID for tracking
            
        Raises:
            RuntimeError: If the executor is not running
        """
        if not self.running:
            raise RuntimeError("AsyncExecutor is not running. Call start() first.")
        
        self.task_queue.put(task)
        logger.info(f"Task {task.id} submitted to queue")
        
        # Post initial status
        self._post_status(
            task.id,
            TaskStatus.QUEUED,
            f"Queued {task.type.value}: {task.gesture or task.command}"
        )
        
        return task.id
    
    def submit_gesture(self, gesture: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Submit a gesture task for execution.
        
        Args:
            gesture: Name of the gesture to execute
            metadata: Optional additional task data
            
        Returns:
            Task ID for tracking
        """
        task = Task.create_gesture_task(gesture, metadata)
        return self.submit_task(task)
    
    def submit_manipulation(self, command: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Submit a manipulation task for execution.
        
        Args:
            command: Natural language command for SmolVLA
            metadata: Optional additional task data
            
        Returns:
            Task ID for tracking
        """
        task = Task.create_manipulation_task(command, metadata)
        return self.submit_task(task)
    
    def get_status(self, block: bool = False, timeout: Optional[float] = None) -> Optional[StatusUpdate]:
        """
        Get the latest status update from the queue.
        
        Args:
            block: If True, wait for a status update. If False, return immediately.
            timeout: Maximum time to wait for status update (only used if block=True)
            
        Returns:
            StatusUpdate if available, None otherwise
        """
        try:
            if block:
                return self.status_queue.get(timeout=timeout)
            else:
                return self.status_queue.get_nowait()
        except Empty:
            return None
    
    def get_all_status_updates(self) -> list[StatusUpdate]:
        """
        Get all pending status updates from the queue.
        
        Returns:
            List of status updates (may be empty)
        """
        updates = []
        while True:
            update = self.get_status(block=False)
            if update is None:
                break
            updates.append(update)
        return updates
    
    def get_current_task(self) -> Optional[Task]:
        """
        Get the currently executing task.
        
        Returns:
            Current task if one is executing, None otherwise
        """
        return self.current_task
    
    def get_queue_size(self) -> int:
        """
        Get the number of tasks waiting in the queue.
        
        Returns:
            Number of queued tasks
        """
        return self.task_queue.qsize()
    
    def is_busy(self) -> bool:
        """
        Check if the executor is currently processing a task.
        
        Returns:
            True if a task is currently executing
        """
        return self.current_task is not None
    
    def clear_queue(self) -> int:
        """
        Clear all pending tasks from the queue.
        
        Note: This does not stop the currently executing task.
        
        Returns:
            Number of tasks that were cleared
        """
        count = 0
        while True:
            try:
                self.task_queue.get_nowait()
                self.task_queue.task_done()
                count += 1
            except Empty:
                break
        
        if count > 0:
            logger.info(f"Cleared {count} tasks from queue")
        
        return count
    
    def __enter__(self):
        """Context manager entry: start the executor."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit: stop the executor."""
        self.stop()
        return False
