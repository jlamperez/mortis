#!/usr/bin/env python3
"""
Test to determine actual joint limits of the SO101 robot.

This script helps you find the safe operational limits for each joint
by checking the calibration data and current positions.
"""

import sys
from pathlib import Path

# Add parent directory to path to import mortis package
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from src.mortis.robot import MortisArm

def load_calibration():
    """Load calibration data to see servo ranges."""
    calib_path = Path(".cache/calibration/so101/my_follower_robot_arm.json")
    if calib_path.exists():
        with open(calib_path, 'r') as f:
            return json.load(f)
    return None

def test_joint_limits():
    """Test and display joint limit information."""
    print("\n" + "="*60)
    print("SO101 Joint Limits Analysis")
    print("="*60 + "\n")
    
    # Load calibration
    print("1. Loading calibration data...")
    calib = load_calibration()
    if calib:
        print("   ✓ Calibration loaded\n")
        print("   Servo ranges (in steps):")
        for joint, data in calib.items():
            range_steps = data['range_max'] - data['range_min']
            print(f"     {joint}: {data['range_min']} - {data['range_max']} ({range_steps} steps)")
    else:
        print("   ✗ Calibration not found\n")
    
    # Connect to robot
    print("\n2. Connecting to robot...")
    arm = MortisArm()
    arm.connect()
    
    if not arm.connected:
        print("   ✗ Failed to connect to robot")
        return False
    
    print("   ✓ Robot connected\n")
    
    # Get current positions
    print("3. Current joint positions (in degrees):")
    obs = arm.robot.get_observation()
    
    joint_positions = {}
    for key, val in obs.items():
        joint_positions[key] = val
        print(f"     {key}: {val:.2f}°")
    
    # Recommended limits based on typical SO101 range
    print("\n4. Recommended safety limits:")
    print("   Based on SO101 specifications and calibration:\n")
    
    recommended_limits = {
        "shoulder_pan.pos": (-180, 180),
        "shoulder_lift.pos": (-120, 120),  # Extended for SO101
        "elbow_flex.pos": (-135, 135),
        "wrist_flex.pos": (-100, 100),     # Slightly extended
        "wrist_roll.pos": (-180, 180),
        "gripper.pos": (0, 100),
    }
    
    for joint, (min_deg, max_deg) in recommended_limits.items():
        current = joint_positions.get(joint, 0)
        within = min_deg <= current <= max_deg
        status = "✓" if within else "✗"
        print(f"   {status} {joint}: [{min_deg}, {max_deg}]° (current: {current:.2f}°)")
    
    # Disconnect
    print("\n5. Disconnecting...")
    arm.disconnect()
    print("   ✓ Disconnected\n")
    
    print("="*60)
    print("Analysis complete!")
    print("="*60)
    print("\nRecommendation:")
    print("Update JOINT_LIMITS in smolvla_executor.py with the values above")
    print("if all current positions are within the recommended ranges.\n")
    
    return True

if __name__ == "__main__":
    try:
        success = test_joint_limits()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
