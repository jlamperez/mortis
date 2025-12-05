#!/usr/bin/env python3
"""
Test script for Mortis simulation mode.

This script demonstrates how to use Mortis in simulation mode
without a physical robot. It tests the gesture system and shows
how gestures are logged instead of executed.

Usage:
    python examples/test_simulation.py
"""

import os
import sys
import logging
from pathlib import Path

# Add src to path
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger(__name__)


def test_simulation_mode():
    """Test Mortis robot in simulation mode."""
    
    # Force simulation mode
    os.environ['ROBOT_MODE'] = 'simulation'
    
    logger.info("=" * 60)
    logger.info("🎭 Testing Mortis Simulation Mode")
    logger.info("=" * 60)
    
    # Import after setting env var
    from mortis.robot import MortisArm
    
    # Create robot arm
    logger.info("\n1. Creating MortisArm instance...")
    arm = MortisArm()
    
    logger.info(f"   Mode: {arm.mode}")
    logger.info(f"   Connected: {arm.connected}")
    
    # Connect (should be instant in simulation)
    logger.info("\n2. Connecting to robot...")
    arm.connect()
    logger.info(f"   Connected: {arm.connected}")
    
    # Test various gestures
    gestures_to_test = ["idle", "wave", "point_left", "point_right", "grab", "drop"]
    
    logger.info("\n3. Testing gestures...")
    for gesture in gestures_to_test:
        logger.info(f"\n   Testing gesture: {gesture}")
        arm.move_arm(gesture)
    
    # Test invalid gesture (should fallback to idle)
    logger.info("\n4. Testing invalid gesture (should fallback to idle)...")
    arm.move_arm("invalid_gesture_name")
    
    # Disconnect
    logger.info("\n5. Disconnecting...")
    arm.disconnect()
    logger.info(f"   Connected: {arm.connected}")
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ Simulation mode test completed successfully!")
    logger.info("=" * 60)
    logger.info("\nNote: In simulation mode, gestures are logged but not")
    logger.info("physically executed. This is perfect for testing without hardware.")


def test_physical_mode_detection():
    """Test that physical mode is detected correctly."""
    
    logger.info("\n" + "=" * 60)
    logger.info("🤖 Testing Physical Mode Detection")
    logger.info("=" * 60)
    
    # Set physical mode
    os.environ['ROBOT_MODE'] = 'physical'
    
    # Import fresh (need to reload module)
    import importlib
    import mortis.robot
    importlib.reload(mortis.robot)
    from mortis.robot import MortisArm
    
    logger.info("\n1. Creating MortisArm in physical mode...")
    arm = MortisArm()
    
    logger.info(f"   Mode: {arm.mode}")
    logger.info(f"   Expected: physical")
    
    if arm.mode == "physical":
        logger.info("   ✅ Physical mode detected correctly")
    else:
        logger.error("   ❌ Physical mode not detected")
    
    logger.info("\nNote: Physical mode will attempt to connect to USB serial port.")
    logger.info("If no robot is connected, connection will fail (expected behavior).")


if __name__ == "__main__":
    try:
        # Test simulation mode
        test_simulation_mode()
        
        # Test physical mode detection
        test_physical_mode_detection()
        
    except Exception as e:
        logger.error(f"\n❌ Test failed with error: {e}", exc_info=True)
        sys.exit(1)
