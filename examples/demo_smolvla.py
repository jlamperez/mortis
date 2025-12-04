"""
Demo script for SmolVLA executor.

This script demonstrates how to initialize and use the SmolVLA executor
for robotic manipulation tasks. It requires a trained model checkpoint.

Usage:
    python examples/demo_smolvla.py --checkpoint /path/to/checkpoint
    
Or set environment variable:
    export SMOLVLA_CHECKPOINT_PATH=/path/to/checkpoint
    python examples/demo_smolvla.py
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
REPO_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(REPO_ROOT / ".env")

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mortis.smolvla_executor import init_smolvla_executor, SmolVLAError
from mortis.robot import MortisArm


def main():
    """Main demo function."""
    print("=" * 60)
    print("SmolVLA Executor Demo")
    print("=" * 60)
    
    # Check for checkpoint path
    checkpoint_path = os.getenv("SMOLVLA_CHECKPOINT_PATH")
    print(checkpoint_path)
    if checkpoint_path is None:
        print("\n❌ Error: No checkpoint path provided")
        print("\nPlease set SMOLVLA_CHECKPOINT_PATH environment variable:")
        print("  export SMOLVLA_CHECKPOINT_PATH=/path/to/checkpoint")
        print("\nOr provide it as an argument:")
        print("  python examples/demo_smolvla.py --checkpoint /path/to/checkpoint")
        return 1
    
    print(f"\n📁 Checkpoint path: {checkpoint_path}")
    
    # Check if checkpoint exists
    if not Path(checkpoint_path).exists():
        print(f"\n❌ Error: Checkpoint path does not exist: {checkpoint_path}")
        return 1
    
    try:
        # Initialize robot arm
        print("\n🤖 Initializing robot arm...")
        robot_arm = MortisArm()
        robot_arm.connect()
        
        if not robot_arm.connected:
            print("❌ Failed to connect to robot arm")
            return 1
        
        print("✅ Robot arm connected")
        
        # Initialize SmolVLA executor
        print("\n🧠 Loading SmolVLA model...")
        executor = init_smolvla_executor(
            checkpoint_path=checkpoint_path,
            robot_arm=robot_arm
        )
        
        print("✅ SmolVLA executor initialized")
        print(f"   Device: {executor.device}")
        print(f"   Valid commands: {len(executor.VALID_COMMANDS)}")
        
        # Display available commands
        print("\n📋 Available manipulation commands:")
        for i, cmd in enumerate(executor.VALID_COMMANDS, 1):
            print(f"   {i}. {cmd}")
        
        # Demo: Execute a command
        print("\n" + "=" * 60)
        print("Demo Execution")
        print("=" * 60)
        
        # Use the first command as demo
        demo_command = executor.VALID_COMMANDS[0]
        print(f"\n🎯 Executing: {demo_command}")
        print("   Note: Using dummy camera images (camera integration pending)")
        print("   Limiting to 10 steps for demo purposes...")
        
        # Execute with limited steps for demo
        success = executor.execute(demo_command, max_steps=10)
        if success:
            print("✅ Task completed successfully")
        else:
            print("⚠️ Task did not complete (expected with dummy images)")
        
        print("\n💡 To execute a command, use:")
        print("   executor.execute(command, max_steps=500)")
        
        # Cleanup
        print("\n🧹 Cleaning up...")
        executor.cleanup()
        robot_arm.disconnect()
        
        print("\n✅ Demo complete!")
        return 0
        
    except SmolVLAError as e:
        print(f"\n❌ SmolVLA Error: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
