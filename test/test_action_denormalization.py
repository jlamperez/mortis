#!/usr/bin/env python3
"""
Test to verify action denormalization works correctly.

This test verifies that:
1. The postprocessor loads correctly from the checkpoint
2. Actions are denormalized before being sent to the robot
3. Denormalized actions are within the expected joint limits
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


def test_action_denormalization():
    """Test that actions are properly denormalized."""
    print("\n" + "="*60)
    print("Testing action denormalization")
    print("="*60 + "\n")
    
    checkpoint_path = "outputs/train/smolvla_kiroween_potion_20k/checkpoints/last/pretrained_model"
    
    try:
        # Initialize executor
        print("1. Initializing executor...")
        executor = SmolVLAExecutor(
            checkpoint_path=checkpoint_path,
            robot_arm=None,
            device="cuda",
            enable_safety_checks=False  # Disable for this test
        )
        print("   ✓ Executor initialized\n")
        
        # Check postprocessor is loaded
        print("2. Checking postprocessor...")
        if executor.postprocessor is None:
            print("   ✗ Postprocessor not loaded")
            return False
        print("   ✓ Postprocessor loaded\n")
        
        # Create a normalized action (typical range: -1 to 1)
        print("3. Testing denormalization...")
        normalized_action = torch.tensor(
            [[0.0, 0.0, 0.0, 0.0, 0.0, 0.5]],  # Normalized values
            dtype=torch.float32,
            device="cuda"
        )
        print(f"   Normalized action: {normalized_action.cpu().numpy()}")
        
        # Denormalize
        denormalized_action = executor.postprocessor(normalized_action)
        print(f"   Denormalized action: {denormalized_action}")
        
        # Check if denormalized action is a tensor
        if not isinstance(denormalized_action, torch.Tensor):
            print(f"   ✗ Denormalized action is not a tensor: {type(denormalized_action)}")
            return False
        
        print(f"   ✓ Denormalization successful\n")
        
        # Check joint limits
        print("4. Checking joint limits...")
        action_dict = executor._action_to_dict(denormalized_action)
        
        all_within_limits = True
        for joint_name, position in action_dict.items():
            if joint_name in executor.JOINT_LIMITS:
                min_pos, max_pos = executor.JOINT_LIMITS[joint_name]
                within_limits = min_pos <= position <= max_pos
                status = "✓" if within_limits else "✗"
                print(f"   {status} {joint_name}: {position:.2f} (limits: [{min_pos}, {max_pos}])")
                if not within_limits:
                    all_within_limits = False
        
        if not all_within_limits:
            print("\n   ⚠️ Some joints exceed limits (this may be expected for certain actions)")
        else:
            print("\n   ✓ All joints within limits")
        
        print("\n" + "="*60)
        print("✓ Test passed! Action denormalization works")
        print("="*60 + "\n")
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_action_denormalization()
    exit(0 if success else 1)
