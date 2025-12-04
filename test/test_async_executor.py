"""
Tests for the asynchronous task executor.
"""

import time
import pytest
from src.mortis.async_executor import (
    AsyncExecutor,
    Task,
    TaskStatus,
    TaskType,
    StatusUpdate
)


def test_task_creation():
    """Test creating gesture and manipulation tasks."""
    # Test gesture task creation
    gesture_task = Task.create_gesture_task("wave")
    assert gesture_task.type == TaskType.GESTURE
    assert gesture_task.status == TaskStatus.QUEUED
    assert gesture_task.gesture == "wave"
    assert gesture_task.command is None
    assert gesture_task.id.startswith("gesture_")
    
    # Test manipulation task creation
    manip_task = Task.create_manipulation_task("Pick up the skull")
    assert manip_task.type == TaskType.MANIPULATION
    assert manip_task.status == TaskStatus.QUEUED
    assert manip_task.command == "Pick up the skull"
    assert manip_task.gesture is None
    assert manip_task.id.startswith("manipulation_")


def test_task_lifecycle():
    """Test task status transitions."""
    task = Task.create_gesture_task("wave")
    
    # Initial state
    assert task.status == TaskStatus.QUEUED
    assert task.started_at is None
    assert task.completed_at is None
    assert task.duration is None
    
    # Start task
    task.start()
    assert task.status == TaskStatus.RUNNING
    assert task.started_at is not None
    assert task.wait_time > 0
    
    # Complete task
    time.sleep(0.1)
    task.complete()
    assert task.status == TaskStatus.COMPLETE
    assert task.completed_at is not None
    assert task.duration is not None
    assert task.duration > 0


def test_task_failure():
    """Test task failure handling."""
    task = Task.create_gesture_task("wave")
    task.start()
    
    error_msg = "Robot connection lost"
    task.fail(error_msg)
    
    assert task.status == TaskStatus.FAILED
    assert task.error == error_msg
    assert task.completed_at is not None


def test_task_to_dict():
    """Test task serialization to dictionary."""
    task = Task.create_manipulation_task("Pick up the skull", metadata={"priority": "high"})
    task_dict = task.to_dict()
    
    assert task_dict["type"] == "manipulation"
    assert task_dict["status"] == "queued"
    assert task_dict["command"] == "Pick up the skull"
    assert task_dict["metadata"]["priority"] == "high"


def test_async_executor_lifecycle():
    """Test starting and stopping the async executor."""
    executor = AsyncExecutor()
    
    # Initially not running
    assert not executor.running
    assert executor.worker_thread is None
    
    # Start executor
    executor.start()
    assert executor.running
    assert executor.worker_thread is not None
    assert executor.worker_thread.is_alive()
    
    # Stop executor
    executor.stop()
    assert not executor.running
    # After stopping, worker_thread is set to None
    assert executor.worker_thread is None


def test_async_executor_context_manager():
    """Test using async executor as context manager."""
    with AsyncExecutor() as executor:
        assert executor.running
        assert executor.worker_thread.is_alive()
    
    # Should be stopped after exiting context
    assert not executor.running


def test_task_submission():
    """Test submitting tasks to the executor."""
    executed_tasks = []
    
    def mock_executor(task: Task):
        """Mock task executor that records executed tasks."""
        executed_tasks.append(task)
        time.sleep(0.05)  # Simulate work
    
    with AsyncExecutor(task_executor=mock_executor) as executor:
        # Submit gesture task
        task_id1 = executor.submit_gesture("wave")
        assert task_id1.startswith("gesture_")
        
        # Submit manipulation task
        task_id2 = executor.submit_manipulation("Pick up the skull")
        assert task_id2.startswith("manipulation_")
        
        # Wait for tasks to complete
        time.sleep(0.5)
        
        # Verify tasks were executed
        assert len(executed_tasks) == 2
        assert executed_tasks[0].gesture == "wave"
        assert executed_tasks[1].command == "Pick up the skull"


def test_status_updates():
    """Test receiving status updates from the executor."""
    def mock_executor(task: Task):
        time.sleep(0.05)
    
    with AsyncExecutor(task_executor=mock_executor) as executor:
        # Submit a task
        task_id = executor.submit_gesture("wave")
        
        # Collect status updates
        updates = []
        timeout = time.time() + 2.0
        while time.time() < timeout:
            update = executor.get_status(block=False)
            if update:
                updates.append(update)
            time.sleep(0.05)
            
            # Stop when we get a complete status
            if updates and updates[-1].status == TaskStatus.COMPLETE:
                break
        
        # Should have received queued, running, and complete updates
        assert len(updates) >= 2
        assert any(u.status == TaskStatus.QUEUED for u in updates)
        assert any(u.status == TaskStatus.RUNNING for u in updates)
        assert any(u.status == TaskStatus.COMPLETE for u in updates)


def test_get_current_task():
    """Test getting the currently executing task."""
    def slow_executor(task: Task):
        time.sleep(0.2)
    
    with AsyncExecutor(task_executor=slow_executor) as executor:
        # Submit a task
        executor.submit_gesture("wave")
        
        # Wait a bit for task to start
        time.sleep(0.1)
        
        # Should have a current task
        current = executor.get_current_task()
        assert current is not None
        assert current.status == TaskStatus.RUNNING
        
        # Wait for task to complete
        time.sleep(0.3)
        
        # Should have no current task
        current = executor.get_current_task()
        assert current is None


def test_queue_size():
    """Test getting the queue size."""
    def slow_executor(task: Task):
        time.sleep(0.3)
    
    with AsyncExecutor(task_executor=slow_executor) as executor:
        # Submit multiple tasks
        executor.submit_gesture("wave")
        executor.submit_gesture("point_left")
        executor.submit_gesture("point_right")
        
        # Queue should have tasks (minus the one being executed)
        time.sleep(0.1)
        queue_size = executor.get_queue_size()
        assert queue_size >= 1  # At least one task should be queued


def test_is_busy():
    """Test checking if executor is busy."""
    def slow_executor(task: Task):
        time.sleep(0.2)
    
    with AsyncExecutor(task_executor=slow_executor) as executor:
        # Initially not busy
        assert not executor.is_busy()
        
        # Submit a task
        executor.submit_gesture("wave")
        
        # Wait for task to start
        time.sleep(0.1)
        assert executor.is_busy()
        
        # Wait for task to complete
        time.sleep(0.3)
        assert not executor.is_busy()


def test_clear_queue():
    """Test clearing the task queue."""
    def slow_executor(task: Task):
        time.sleep(0.5)
    
    with AsyncExecutor(task_executor=slow_executor) as executor:
        # Submit multiple tasks
        executor.submit_gesture("wave")
        executor.submit_gesture("point_left")
        executor.submit_gesture("point_right")
        
        # Wait a bit for first task to start
        time.sleep(0.1)
        
        # Clear the queue
        cleared = executor.clear_queue()
        assert cleared >= 1  # Should have cleared at least one task
        
        # Queue should be empty now
        assert executor.get_queue_size() == 0


def test_error_handling():
    """Test error handling in task execution."""
    def failing_executor(task: Task):
        raise RuntimeError("Simulated failure")
    
    with AsyncExecutor(task_executor=failing_executor) as executor:
        # Submit a task that will fail
        task_id = executor.submit_gesture("wave")
        
        # Wait for task to fail
        time.sleep(0.5)
        
        # Should have received a failed status update
        updates = executor.get_all_status_updates()
        failed_updates = [u for u in updates if u.status == TaskStatus.FAILED]
        assert len(failed_updates) > 0
        assert "Simulated failure" in failed_updates[0].error


def test_submit_without_start():
    """Test that submitting a task without starting raises an error."""
    executor = AsyncExecutor()
    
    with pytest.raises(RuntimeError, match="not running"):
        executor.submit_gesture("wave")


def test_double_start():
    """Test that starting an already running executor raises an error."""
    executor = AsyncExecutor()
    executor.start()
    
    try:
        with pytest.raises(RuntimeError, match="already running"):
            executor.start()
    finally:
        executor.stop()
