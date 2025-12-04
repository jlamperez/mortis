"""
Demo script showing how to use LeRobotAsyncClient for manipulation tasks.

This example demonstrates:
1. Starting the PolicyServer and RobotClient
2. Executing manipulation tasks with SmolVLA
3. Monitoring task status
4. Handling task completion and errors
"""

import time
import logging
from mortis.lerobot_async_client import LeRobotAsyncClient, ManipulationStatus
from mortis.robot import MortisArm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Initialize the robot arm for gestures
mortis_arm = MortisArm()


def main():
    """Main demo function."""
    print("=" * 60)
    print("LeRobot Async Client Demo")
    print("=" * 60)
    
    # Create client
    print("\n1. Creating LeRobotAsyncClient...")
    client = LeRobotAsyncClient(
        robot_port="/dev/ttyACM1",
        robot_id="my_follower_robot_arm",  # Must match your calibration file
        model_path="jlamperez/kiroween-potion-smolvla",
        policy_device="cuda"
    )
    print("   ✓ Client created")

    
    try:
        # Connect to robot for initial idle gesture
        print("\n2. Connecting to robot...")
        mortis_arm.connect()
        print("   ✓ Robot connected")
        
        # Move robot to idle position before starting
        print("\n2.1. Moving robot to idle position...")
        mortis_arm.move_arm("idle")
        time.sleep(1.0)  # Give robot time to stabilize
        print("   ✓ Robot at idle")
        
        # Disconnect mortis_arm so LeRobot can take control
        mortis_arm.disconnect()
        print("   ✓ Robot released for LeRobot control")
        
        # Start the LeRobot async system
        print("\n2.2. Starting PolicyServer and RobotClient...")
        if not client.start():
            print("   ✗ Failed to start client")
            return
        print("   ✓ System started")
        
        # Execute a manipulation task
        print("\n3. Executing manipulation task...")
        task = "Pick up the skull and place it in the green cup"
        print(f"   Task: {task}")
        
        if not client.execute_task(task, max_steps=200):
            print("   ✗ Failed to start task")
            return
        print("   ✓ Task started")
        
        # Monitor task execution
        print("\n4. Monitoring task execution...")
        print("   (This may take 30-60 seconds, max 100s timeout)")
        print("   Press Ctrl+C to interrupt")
        
        last_status = None
        start_time = time.time()
        max_wait = 120  # Maximum 2 minutes
        
        while client.is_busy():
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed > max_wait:
                print(f"\n   ⏱️  Timeout after {elapsed:.0f}s - stopping...")
                break
            
            status = client.get_status()
            
            if status != last_status:
                status_icon = {
                    ManipulationStatus.IDLE: "💤",
                    ManipulationStatus.STARTING: "🔄",
                    ManipulationStatus.RUNNING: "🤖",
                    ManipulationStatus.COMPLETE: "✅",
                    ManipulationStatus.FAILED: "❌",
                    ManipulationStatus.STOPPED: "⏹️"
                }.get(status, "❓")
                
                print(f"   {status_icon} Status: {status.value} (elapsed: {elapsed:.0f}s)")
                last_status = status
            
            time.sleep(1.0)
        
        # Check final status
        print("\n5. Task completed!")
        final_task = client.get_current_task()
        if final_task:
            print(f"   Status: {final_task.status.value}")
            if final_task.duration is not None:
                print(f"   Duration: {final_task.duration:.2f}s")
            else:
                print(f"   Duration: N/A (still running or timed out)")
            
            if final_task.error:
                print(f"   Error: {final_task.error}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        logger.error("Demo failed", exc_info=True)
        
    finally:
        # Stop the LeRobot system first
        print("\n6. Stopping LeRobotAsyncClient...")
        client.stop()
        print("   ✓ Client stopped")
        
        # Reconnect mortis_arm to move to idle
        print("\n7. Returning robot to idle position...")
        mortis_arm.connect()
        mortis_arm.move_arm("idle")
        time.sleep(1.0)
        print("   ✓ Robot at idle")
        
        # Disconnect robot
        print("\n8. Disconnecting robot...")
        mortis_arm.disconnect()
        print("   ✓ Robot disconnected")
    
    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
