"""
Demo script showing how to use the AsyncExecutor for robot tasks.

This example demonstrates:
1. Creating an async executor with a custom task executor
2. Submitting gesture and manipulation tasks
3. Monitoring task status updates
4. Handling task completion and errors
"""

import time
import logging
from mortis.async_executor import AsyncExecutor, Task, TaskStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def mock_robot_executor(task: Task):
    """
    Mock robot task executor that simulates robot operations.
    
    In a real application, this would:
    - Execute gestures via mortis_arm.move_arm()
    - Execute manipulation tasks via smolvla_executor.execute()
    """
    logger.info(f"Executing task: {task.id}")
    
    if task.type.value == "gesture":
        # Simulate gesture execution
        logger.info(f"  Performing gesture: {task.gesture}")
        time.sleep(1.0)  # Simulate gesture duration
        
    elif task.type.value == "manipulation":
        # Simulate SmolVLA inference
        logger.info(f"  Running SmolVLA for: {task.command}")
        time.sleep(3.0)  # Simulate longer manipulation task
    
    logger.info(f"Task {task.id} completed")


def monitor_status(executor: AsyncExecutor, duration: float = 10.0):
    """
    Monitor and display status updates from the executor.
    
    Args:
        executor: AsyncExecutor instance to monitor
        duration: How long to monitor (seconds)
    """
    start_time = time.time()
    
    print("\n=== Monitoring Status Updates ===")
    
    while time.time() - start_time < duration:
        # Get all pending status updates
        updates = executor.get_all_status_updates()
        
        for update in updates:
            status_icon = {
                TaskStatus.QUEUED: "⏳",
                TaskStatus.RUNNING: "🔄",
                TaskStatus.COMPLETE: "✅",
                TaskStatus.FAILED: "❌"
            }.get(update.status, "❓")
            
            print(f"{status_icon} [{update.status.value.upper()}] {update.message}")
            
            if update.error:
                print(f"   Error: {update.error}")
        
        # Check current task
        current = executor.get_current_task()
        if current:
            print(f"📍 Current: {current.type.value} - {current.gesture or current.command}")
        
        # Check queue size
        queue_size = executor.get_queue_size()
        if queue_size > 0:
            print(f"📋 Queue: {queue_size} tasks waiting")
        
        time.sleep(0.5)
    
    print("\n=== Monitoring Complete ===\n")


def main():
    """Main demo function."""
    print("=" * 60)
    print("AsyncExecutor Demo")
    print("=" * 60)
    
    # Create executor with mock robot executor
    executor = AsyncExecutor(task_executor=mock_robot_executor)
    
    try:
        # Start the executor
        print("\n1. Starting AsyncExecutor...")
        executor.start()
        print("   ✓ Executor started")
        
        # Submit some gesture tasks
        print("\n2. Submitting gesture tasks...")
        task_id1 = executor.submit_gesture("wave")
        print(f"   ✓ Submitted gesture task: {task_id1}")
        
        task_id2 = executor.submit_gesture("point_left")
        print(f"   ✓ Submitted gesture task: {task_id2}")
        
        # Submit a manipulation task
        print("\n3. Submitting manipulation task...")
        task_id3 = executor.submit_manipulation("Pick up the skull and place it in the green cup")
        print(f"   ✓ Submitted manipulation task: {task_id3}")
        
        # Submit another gesture
        task_id4 = executor.submit_gesture("idle")
        print(f"   ✓ Submitted gesture task: {task_id4}")
        
        # Monitor status for a while
        print("\n4. Monitoring task execution...")
        monitor_status(executor, duration=8.0)
        
        # Check if executor is still busy
        if executor.is_busy():
            print("⏳ Executor is still processing tasks...")
            time.sleep(2.0)
        
        # Get final status
        print("\n5. Final status:")
        print(f"   Queue size: {executor.get_queue_size()}")
        print(f"   Is busy: {executor.is_busy()}")
        
        # Get any remaining status updates
        remaining_updates = executor.get_all_status_updates()
        if remaining_updates:
            print(f"   Remaining updates: {len(remaining_updates)}")
            for update in remaining_updates:
                print(f"     - {update.status.value}: {update.message}")
        
    finally:
        # Stop the executor
        print("\n6. Stopping AsyncExecutor...")
        executor.stop()
        print("   ✓ Executor stopped")
    
    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
