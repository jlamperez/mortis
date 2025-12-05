#!/usr/bin/env python3
"""
Unit tests for simulation mode functionality.

Tests that simulation mode properly disables hardware-dependent features
and that physical mode enables them correctly.
"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src to path
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


class TestSimulationMode:
    """Test simulation mode behavior."""
    
    def test_robot_arm_simulation_mode(self):
        """Test that MortisArm initializes correctly in simulation mode."""
        os.environ['ROBOT_MODE'] = 'simulation'
        
        from mortis.robot import MortisArm
        
        arm = MortisArm()
        
        assert arm.mode == "simulation"
        assert arm.robot is None
        assert arm.connected == True  # Always "connected" in simulation
    
    def test_robot_arm_physical_mode(self):
        """Test that MortisArm initializes correctly in physical mode."""
        os.environ['ROBOT_MODE'] = 'physical'
        
        # Need to reload module to pick up new env var
        import importlib
        import mortis.robot
        importlib.reload(mortis.robot)
        from mortis.robot import MortisArm
        
        arm = MortisArm()
        
        assert arm.mode == "physical"
        assert arm.robot is not None
        assert arm.connected == False  # Not connected until connect() is called
    
    def test_robot_arm_default_mode(self):
        """Test that MortisArm defaults to physical mode."""
        # Remove ROBOT_MODE if set
        if 'ROBOT_MODE' in os.environ:
            del os.environ['ROBOT_MODE']
        
        # Reload module
        import importlib
        import mortis.robot
        importlib.reload(mortis.robot)
        from mortis.robot import MortisArm
        
        arm = MortisArm()
        
        assert arm.mode == "physical"
    
    def test_simulation_connect(self):
        """Test that connect() works in simulation mode."""
        os.environ['ROBOT_MODE'] = 'simulation'
        
        import importlib
        import mortis.robot
        importlib.reload(mortis.robot)
        from mortis.robot import MortisArm
        
        arm = MortisArm()
        arm.connect()
        
        assert arm.connected == True
    
    def test_simulation_disconnect(self):
        """Test that disconnect() works in simulation mode."""
        os.environ['ROBOT_MODE'] = 'simulation'
        
        import importlib
        import mortis.robot
        importlib.reload(mortis.robot)
        from mortis.robot import MortisArm
        
        arm = MortisArm()
        arm.connect()
        arm.disconnect()
        
        assert arm.connected == False
    
    def test_simulation_move_arm(self):
        """Test that move_arm() works in simulation mode."""
        os.environ['ROBOT_MODE'] = 'simulation'
        
        import importlib
        import mortis.robot
        importlib.reload(mortis.robot)
        from mortis.robot import MortisArm
        
        arm = MortisArm()
        arm.connect()
        
        # Should not raise any errors
        arm.move_arm("wave")
        arm.move_arm("idle")
        arm.move_arm("grab")
    
    def test_lerobot_client_disabled_in_simulation(self):
        """Test that LeRobotAsyncClient is disabled in simulation mode."""
        os.environ['ROBOT_MODE'] = 'simulation'
        os.environ['ENABLE_MANIPULATION'] = 'true'  # Even if enabled
        
        # Mock the LeRobotAsyncClient import
        with patch('mortis.app.LeRobotAsyncClient') as mock_client:
            import importlib
            import mortis.app
            
            # Reset global state
            mortis.app.lerobot_client = None
            
            # Reload to pick up new env vars
            importlib.reload(mortis.app)
            
            from mortis.app import get_lerobot_client
            
            client = get_lerobot_client()
            
            # Should return None in simulation mode
            assert client is None
            
            # Should not have tried to create client
            mock_client.assert_not_called()
    
    def test_smolvla_executor_disabled_in_simulation(self):
        """Test that SmolVLA executor is disabled in simulation mode."""
        os.environ['ROBOT_MODE'] = 'simulation'
        os.environ['SMOLVLA_CHECKPOINT_PATH'] = '/fake/path'
        
        # Mock the SmolVLAExecutor import
        with patch('mortis.tools.SmolVLAExecutor') as mock_executor:
            import importlib
            import mortis.tools
            
            # Reset global state
            mortis.tools.smolvla_executor = None
            
            # Reload to pick up new env vars
            importlib.reload(mortis.tools)
            
            from mortis.tools import _get_smolvla_executor
            
            executor = _get_smolvla_executor()
            
            # Should return None in simulation mode
            assert executor is None
            
            # Should not have tried to create executor
            mock_executor.assert_not_called()
    
    def test_lerobot_client_enabled_in_physical_mode(self):
        """Test that LeRobotAsyncClient can be enabled in physical mode."""
        os.environ['ROBOT_MODE'] = 'physical'
        os.environ['ENABLE_MANIPULATION'] = 'true'
        
        # Mock the LeRobotAsyncClient
        with patch('mortis.app.LeRobotAsyncClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            import importlib
            import mortis.app
            
            # Reset global state
            mortis.app.lerobot_client = None
            
            # Reload to pick up new env vars
            importlib.reload(mortis.app)
            
            from mortis.app import get_lerobot_client
            
            client = get_lerobot_client()
            
            # Should return client instance in physical mode
            assert client is not None
            assert client == mock_client
            
            # Should have tried to create client
            mock_client_class.assert_called_once()


class TestSimulationModeIntegration:
    """Integration tests for simulation mode."""
    
    def test_full_simulation_workflow(self):
        """Test complete workflow in simulation mode."""
        os.environ['ROBOT_MODE'] = 'simulation'
        
        import importlib
        import mortis.robot
        importlib.reload(mortis.robot)
        from mortis.robot import MortisArm
        
        # Create and connect
        arm = MortisArm()
        assert arm.mode == "simulation"
        
        arm.connect()
        assert arm.connected == True
        
        # Execute gestures
        arm.move_arm("wave")
        arm.move_arm("point_left")
        arm.move_arm("grab")
        arm.move_arm("idle")
        
        # Disconnect
        arm.disconnect()
        assert arm.connected == False
    
    def test_simulation_mode_with_invalid_gesture(self):
        """Test that invalid gestures fall back to idle in simulation."""
        os.environ['ROBOT_MODE'] = 'simulation'
        
        import importlib
        import mortis.robot
        importlib.reload(mortis.robot)
        from mortis.robot import MortisArm
        
        arm = MortisArm()
        arm.connect()
        
        # Should not raise error, should fall back to idle
        arm.move_arm("invalid_gesture_name")
        
        assert arm.connected == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
