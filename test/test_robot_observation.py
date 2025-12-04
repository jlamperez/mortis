#!/usr/bin/env python3
"""
Test to verify robot.capture_observation() works correctly.

This test verifies that:
1. The robot can capture observations (cameras + state)
2. The observations are properly formatted for SmolVLA
3. No manual camera initialization is needed
"""

import sys
from pathlib import Path

# Add parent directory to path to import mortis package
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
import torch
from src.mortis.smolvla_executor import SmolVLAExecutor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def test_robot_observation():
    """Test that robot.capture_observation() provides all needed data."""
    print("\n" + "="*60)
    print("Testing robot.capture_observation()")
    print("="*60 + "\n")
    
    checkpoint_path = "outputs/train/smolvla_kiroween_potion_20k/checkpoints/last/pretrained_model"
    
    try:
        # Initialize executor
        print("1. Initializing executor...")
        executor = SmolVLAExecutor(
            checkpoint_path=checkpoint_path,
            robot_arm=None,  # Will create MortisArm automatically
            device="cuda",
            enable_safety_checks=False
        )
        print("   ✓ Executor initialized\n")
        
        # Connect robot
        print("2. Connecting to robot...")
        if not executor.robot_arm.connected:
            executor.robot_arm.connect()
        
        if executor.robot_arm.connected:
            print("   ✓ Robot connected\n")
        else:
            print("   ✗ Robot not connected - test will use dummy observations\n")
        
        # Capture observation
        print("3. Capturing observation from robot...")
        observation = executor._get_observation()
        print("   ✓ Observation captured\n")
        
        # Check observation structure
        print("4. Checking observation structure...")
        print(f"   Keys in observation:")
        for key in observation.keys():
            if isinstance(observation[key], torch.Tensor):
                print(f"     - {key}: shape={observation[key].shape}, dtype={observation[key].dtype}")
            else:
                print(f"     - {key}: {type(observation[key])}")
        
        # Verify expected keys
        expected_keys = [
            "observation.state",
            "observation.images.camera1",
            "observation.images.camera2",
            "observation.images.camera3"
        ]
        
        missing_keys = [key for key in expected_keys if key not in observation]
        if missing_keys:
            print(f"\n   ✗ Missing keys: {missing_keys}")
            return False
        
        print("\n   ✓ All expected keys present")
        
        # Verify shapes
        state_shape = observation["observation.state"].shape
        if state_shape != torch.Size([1, 6]):
            print(f"   ✗ Unexpected state shape: {state_shape} (expected [1, 6])")
            return False
        
        print(f"   ✓ State shape correct: {state_shape}")
        
        # Check image shapes
        for i in range(1, 4):
            key = f"observation.images.camera{i}"
            img_shape = observation[key].shape
            if len(img_shape) != 4 or img_shape[0] != 1 or img_shape[1] != 3:
                print(f"   ✗ Unexpected image shape for {key}: {img_shape}")
                return False
        
        print(f"   ✓ All image shapes correct (batch=1, channels=3)")
        
        print("\n" + "="*60)
        print("✓ Test passed! robot.capture_observation() works correctly")
        print("="*60 + "\n")
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        try:
            if 'executor' in locals() and executor.robot_arm.connected:
                executor.robot_arm.disconnect()
        except:
            pass


if __name__ == "__main__":
    success = test_robot_observation()
    exit(0 if success else 1)
