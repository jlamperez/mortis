"""
Demo script showing the hybrid execution system.

This example demonstrates:
1. Using AsyncExecutor for quick gestures
2. Using LeRobotAsyncClient for complex manipulation
3. Coordinating both systems
4. Monitoring status from both executors
"""

import time
import logging
from mortis.async_executor import AsyncExecutor, Task, TaskType
from mortis.lerobot_async_client import LeRobotAsyncClient, ManipulationStatus
from mortis.robot import MortisArm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Initialize the real robot arm
mortis_arm = MortisArm()


def real_gesture_executor(task: Task):
    """Real gesture executor using mortis_arm."""
    if task.type == TaskType.GESTURE:
        logger.info(f"Executing gesture: {task.gesture}")
        if mortis_arm.connected:
            mortis_arm.move_arm(task.gesture)
        else:
            logger.warning("Robot not connected, skipping gesture")


def main():
    """Main demo function."""
    print("=" * 70)
    print("Hybrid Execution System Demo")
    print("Gestures (AsyncExecutor) + Manipulation (LeRobot Async)")
    print("=" * 70)
    
    # Initialize both systems
    print("\n1. Initializing systems...")
    
    # Connect to robot for gestures
    print("   Connecting to robot for gestures...")
    mortis_arm.connect()
    print("   ✓ Robot connected")
    
    gesture_executor = AsyncExecutor(task_executor=real_gesture_executor)
    print("   ✓ AsyncExecutor created")
    
    manipulation_client = LeRobotAsyncClient(
        robot_port="/dev/ttyACM1",
        robot_id="my_follower_robot_arm",  # Must match your calibration file
        model_path="jlamperez/kiroween-potion-smolvla",
        policy_device="cuda"
    )
    print("   ✓ LeRobotAsyncClient created")

    
    try:
        # Start both systems
        print("\n2. Starting both systems...")
        gesture_executor.start()
        print("   ✓ Gesture executor started")
        
        if not manipulation_client.start():
            print("   ✗ Failed to start manipulation client")
            return
        print("   ✓ Manipulation client started")
        
        # Move robot to idle position
        print("\n2.1. Moving robot to idle position...")
        gesture_executor.submit_gesture("idle")
        time.sleep(2.0)  # Wait for idle gesture to complete
        print("   ✓ Robot ready")
        
        # Execute some gestures (fast)
        print("\n3. Executing gestures (fast)...")
        gesture_executor.submit_gesture("wave")
        print("   ✓ Submitted: wave")
        
        gesture_executor.submit_gesture("point_left")
        print("   ✓ Submitted: point_left")
        
        # Wait for gestures to complete
        time.sleep(10.0)
        print("   ✓ Gestures completed")
        
        # Execute manipulation task (slow)
        print("\n4. Executing manipulation task (slow)...")
        task = "Pick up the eyeball and place it in the purple cup"
        print(f"   Task: {task}")
        
        if not manipulation_client.execute_task(task):
            print("   ✗ Failed to start manipulation")
            return
        print("   ✓ Manipulation started")
        
        # Execute more gestures while manipulation runs
        print("\n5. Executing more gestures while manipulation runs...")
        gesture_executor.submit_gesture("idle")
        print("   ✓ Submitted: idle")
        
        # Monitor both systems
        print("\n6. Monitoring both systems...")
        print("   (Manipulation may take 30-60 seconds, max 120s timeout)")
        print("   Press Ctrl+C to interrupt")
        
        last_manip_status = None
        start_time = time.time()
        max_wait = 120  # Maximum 2 minutes
        
        while manipulation_client.is_busy():
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed > max_wait:
                print(f"\n   ⏱️  Timeout after {elapsed:.0f}s - stopping...")
                break
            
            # Check gesture status
            gesture_update = gesture_executor.get_status(block=False)
            if gesture_update:
                print(f"   ✋ Gesture: {gesture_update.message}")
            
            # Check manipulation status
            manip_status = manipulation_client.get_status()
            if manip_status != last_manip_status:
                status_icon = {
                    ManipulationStatus.IDLE: "💤",
                    ManipulationStatus.STARTING: "🔄",
                    ManipulationStatus.RUNNING: "🤖",
                    ManipulationStatus.COMPLETE: "✅",
                    ManipulationStatus.FAILED: "❌",
                    ManipulationStatus.STOPPED: "⏹️"
                }.get(manip_status, "❓")
                
                print(f"   {status_icon} Manipulation: {manip_status.value} (elapsed: {elapsed:.0f}s)")
                last_manip_status = manip_status
            
            time.sleep(1.0)
        
        # Final status
        print("\n7. Final status:")
        print(f"   Gesture queue size: {gesture_executor.get_queue_size()}")
        print(f"   Gesture is busy: {gesture_executor.is_busy()}")
        
        final_task = manipulation_client.get_current_task()
        if final_task:
            print(f"   Manipulation status: {final_task.status.value}")
            if final_task.duration is not None:
                print(f"   Manipulation duration: {final_task.duration:.2f}s")
            else:
                print(f"   Manipulation duration: N/A (still running or timed out)")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        logger.error("Demo failed", exc_info=True)
        
    finally:
        # Return robot to idle before stopping
        print("\n8. Returning robot to idle position...")
        gesture_executor.submit_gesture("idle")
        time.sleep(2.0)
        print("   ✓ Robot at idle")
        
        # Stop both systems
        print("\n9. Stopping both systems...")
        gesture_executor.stop()
        print("   ✓ Gesture executor stopped")
        
        manipulation_client.stop()
        print("   ✓ Manipulation client stopped")
        
        # Disconnect robot
        print("\n10. Disconnecting robot...")
        mortis_arm.disconnect()
        print("   ✓ Robot disconnected")
    
    print("\n" + "=" * 70)
    print("Demo Complete!")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("  • Gestures execute quickly (1-2s) using AsyncExecutor")
    print("  • Manipulations take longer (30-60s) using LeRobot async")
    print("  • Both systems run independently and concurrently")
    print("  • UI remains responsive throughout")


if __name__ == "__main__":
    main()
