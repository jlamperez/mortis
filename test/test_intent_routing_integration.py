#!/usr/bin/env python3
"""
Integration test for intent routing in the main flow.

This script tests that ask_mortis() correctly:
1. Uses IntentRouter to parse Gemini responses
2. Routes to gesture execution for conversation intents
3. Routes to SmolVLA execution for manipulation intents
4. Falls back to gestures for invalid manipulation commands
"""

import sys
import logging
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mortis.tools import ask_mortis, _get_intent_router
from mortis.models import ResponseType


def setup_logging():
    """Set up logging for test output."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    return logging.getLogger(__name__)


def test_conversation_intent_routing():
    """Test that conversation intents route to gesture execution."""
    print("\n" + "=" * 70)
    print("TEST 1: Conversation Intent Routing")
    print("=" * 70)
    
    try:
        # Mock Gemini response for conversation
        conversation_response = {
            "type": "conversation",
            "message": "Beware, mortal...",
            "mood": "ominous",
            "gesture": "wave"
        }
        
        # Mock the _get_gemini_client function to return a mock client
        with patch('mortis.tools._get_gemini_client') as mock_get_client:
            # Mock the client
            mock_client = Mock()
            mock_client.send_message.return_value = conversation_response
            mock_get_client.return_value = mock_client
            
            # Mock robot arm to prevent actual movement
            with patch('mortis.tools.mortis_arm') as mock_arm:
                mock_arm.connected = True
                mock_arm.move_arm = Mock()
                
                # Call ask_mortis
                print("\nCalling ask_mortis with conversation input...")
                message, mood, gesture = ask_mortis("Hello Mortis!")
                
                print(f"✓ Message: {message}")
                print(f"✓ Mood: {mood}")
                print(f"✓ Gesture: {gesture}")
                
                # Verify response
                assert message == "Beware, mortal..."
                assert mood == "ominous"
                assert gesture == "wave"
                
                # Verify gesture was executed
                mock_arm.move_arm.assert_called_once_with("wave")
                print("✓ Gesture execution called")
        
        print("\n✓ Conversation intent routing test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Conversation intent routing test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_valid_manipulation_intent_routing():
    """Test that valid manipulation intents route to SmolVLA execution."""
    print("\n" + "=" * 70)
    print("TEST 2: Valid Manipulation Intent Routing")
    print("=" * 70)
    
    try:
        # Mock Gemini response for manipulation
        manipulation_response = {
            "type": "manipulation",
            "message": "As you wish...",
            "mood": "sinister",
            "command": "Pick up the skull and place it in the green cup"
        }
        
        # Mock the _get_gemini_client function
        with patch('mortis.tools._get_gemini_client') as mock_get_client:
            # Mock the client
            mock_client = Mock()
            mock_client.send_message.return_value = manipulation_response
            mock_get_client.return_value = mock_client
            
            # Mock robot arm
            with patch('mortis.tools.mortis_arm') as mock_arm:
                mock_arm.connected = True
                
                # Mock SmolVLA executor
                with patch('mortis.tools._get_smolvla_executor') as mock_get_executor:
                    mock_executor = Mock()
                    mock_executor.execute.return_value = True
                    mock_get_executor.return_value = mock_executor
                    
                    # Call ask_mortis
                    print("\nCalling ask_mortis with manipulation command...")
                    message, mood, gesture = ask_mortis("Move the skull to the green cup")
                    
                    print(f"✓ Message: {message}")
                    print(f"✓ Mood: {mood}")
                    print(f"✓ Gesture: {gesture}")
                    
                    # Verify response
                    assert message == "As you wish..."
                    assert mood == "sinister"
                    assert gesture == "manipulation"  # Special gesture for manipulation
                    
                    # Verify SmolVLA execution was called
                    mock_executor.execute.assert_called_once_with(
                        "Pick up the skull and place it in the green cup"
                    )
                    print("✓ SmolVLA execution called")
        
        print("\n✓ Valid manipulation intent routing test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Valid manipulation intent routing test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_invalid_manipulation_fallback():
    """Test that invalid manipulation commands fall back to gestures."""
    print("\n" + "=" * 70)
    print("TEST 3: Invalid Manipulation Fallback")
    print("=" * 70)
    
    try:
        # Mock Gemini response for invalid manipulation
        invalid_manipulation_response = {
            "type": "manipulation",
            "message": "I cannot do that...",
            "mood": "nervous",
            "command": "Pick up the pumpkin and throw it"  # Not in trained set
        }
        
        # Mock the _get_gemini_client function
        with patch('mortis.tools._get_gemini_client') as mock_get_client:
            # Mock the client
            mock_client = Mock()
            mock_client.send_message.return_value = invalid_manipulation_response
            mock_get_client.return_value = mock_client
            
            # Mock robot arm
            with patch('mortis.tools.mortis_arm') as mock_arm:
                mock_arm.connected = True
                mock_arm.move_arm = Mock()
                
                # Mock SmolVLA executor (should not be called)
                with patch('mortis.tools._get_smolvla_executor') as mock_get_executor:
                    mock_executor = Mock()
                    mock_get_executor.return_value = mock_executor
                    
                    # Call ask_mortis
                    print("\nCalling ask_mortis with invalid manipulation command...")
                    message, mood, gesture = ask_mortis("Throw the pumpkin")
                    
                    print(f"✓ Message: {message}")
                    print(f"✓ Mood: {mood}")
                    print(f"✓ Gesture: {gesture}")
                    
                    # Verify response
                    assert message == "I cannot do that..."
                    assert mood == "nervous"
                    assert gesture == "idle"  # Falls back to idle
                    
                    # Verify SmolVLA was NOT called
                    mock_executor.execute.assert_not_called()
                    print("✓ SmolVLA execution NOT called (correct)")
                    
                    # Verify gesture fallback was executed
                    mock_arm.move_arm.assert_called_once_with("idle")
                    print("✓ Gesture fallback executed")
        
        print("\n✓ Invalid manipulation fallback test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Invalid manipulation fallback test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_smolvla_unavailable_fallback():
    """Test fallback when SmolVLA executor is not available."""
    print("\n" + "=" * 70)
    print("TEST 4: SmolVLA Unavailable Fallback")
    print("=" * 70)
    
    try:
        # Mock Gemini response for manipulation
        manipulation_response = {
            "type": "manipulation",
            "message": "I'll try...",
            "mood": "mischievous",
            "command": "Pick up the skull and place it in the green cup"
        }
        
        # Mock the _get_gemini_client function
        with patch('mortis.tools._get_gemini_client') as mock_get_client:
            # Mock the client
            mock_client = Mock()
            mock_client.send_message.return_value = manipulation_response
            mock_get_client.return_value = mock_client
            
            # Mock robot arm
            with patch('mortis.tools.mortis_arm') as mock_arm:
                mock_arm.connected = True
                mock_arm.move_arm = Mock()
                
                # Mock SmolVLA executor as unavailable
                with patch('mortis.tools._get_smolvla_executor') as mock_get_executor:
                    mock_get_executor.return_value = None  # No executor available
                    
                    # Call ask_mortis
                    print("\nCalling ask_mortis with SmolVLA unavailable...")
                    message, mood, gesture = ask_mortis("Move the skull")
                    
                    print(f"✓ Message: {message}")
                    print(f"✓ Mood: {mood}")
                    print(f"✓ Gesture: {gesture}")
                    
                    # Verify response
                    assert message == "I'll try..."
                    assert mood == "mischievous"
                    assert gesture == "idle"  # Falls back to idle
                    
                    # Verify gesture fallback was executed
                    mock_arm.move_arm.assert_called_once_with("idle")
                    print("✓ Gesture fallback executed when SmolVLA unavailable")
        
        print("\n✓ SmolVLA unavailable fallback test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ SmolVLA unavailable fallback test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_intent_router_initialization():
    """Test that IntentRouter is properly initialized."""
    print("\n" + "=" * 70)
    print("TEST 5: IntentRouter Initialization")
    print("=" * 70)
    
    try:
        print("\nGetting IntentRouter instance...")
        router = _get_intent_router()
        
        print(f"✓ Router type: {type(router).__name__}")
        print(f"✓ Valid commands count: {len(router.get_valid_commands())}")
        
        # Verify it has the expected commands
        valid_commands = router.get_valid_commands()
        assert len(valid_commands) == 6
        assert "Pick up the skull and place it in the green cup" in valid_commands
        print("✓ Valid commands loaded correctly")
        
        print("\n✓ IntentRouter initialization test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ IntentRouter initialization test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all integration tests."""
    logger = setup_logging()
    
    print("\n" + "=" * 70)
    print("INTENT ROUTING INTEGRATION TEST SUITE")
    print("=" * 70)
    
    results = []
    
    # Run tests
    results.append(("IntentRouter Initialization", test_intent_router_initialization()))
    results.append(("Conversation Intent Routing", test_conversation_intent_routing()))
    results.append(("Valid Manipulation Intent Routing", test_valid_manipulation_intent_routing()))
    results.append(("Invalid Manipulation Fallback", test_invalid_manipulation_fallback()))
    results.append(("SmolVLA Unavailable Fallback", test_smolvla_unavailable_fallback()))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    print("\n" + "=" * 70)
    print(f"RESULTS: {passed}/{total} tests passed")
    print("=" * 70)
    
    if passed == total:
        print("\n✓ All integration tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
