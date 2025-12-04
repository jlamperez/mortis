#!/usr/bin/env python3
"""
Integration test for hybrid execution system in app.py.

This script tests that the hybrid execution system correctly:
1. Initializes AsyncExecutor and LeRobotAsyncClient
2. Routes gestures to AsyncExecutor
3. Routes manipulation to LeRobotAsyncClient
4. Handles errors from both systems gracefully
"""

import sys
import logging
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def setup_logging():
    """Set up logging for test output."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    return logging.getLogger(__name__)


def test_async_executor_initialization():
    """Test that AsyncExecutor is properly initialized."""
    print("\n" + "=" * 70)
    print("TEST 1: AsyncExecutor Initialization")
    print("=" * 70)
    
    try:
        from mortis.app import get_async_executor
        
        print("\nInitializing AsyncExecutor...")
        executor = get_async_executor()
        
        print(f"✓ Executor type: {type(executor).__name__}")
        print(f"✓ Executor has task_queue: {hasattr(executor, 'task_queue')}")
        print(f"✓ Executor has status_queue: {hasattr(executor, 'status_queue')}")
        
        assert executor is not None
        assert hasattr(executor, 'start')
        assert hasattr(executor, 'stop')
        assert hasattr(executor, 'submit_task')
        
        print("\n✓ AsyncExecutor initialization test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ AsyncExecutor initialization test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_lerobot_client_initialization():
    """Test that LeRobotAsyncClient initialization is handled correctly."""
    print("\n" + "=" * 70)
    print("TEST 2: LeRobotAsyncClient Initialization")
    print("=" * 70)
    
    try:
        import os
        from mortis.app import get_lerobot_client
        
        # Test with manipulation disabled
        print("\nTesting with ENABLE_MANIPULATION=false...")
        os.environ["ENABLE_MANIPULATION"] = "false"
        
        # Reset the global client
        import mortis.app
        mortis.app.lerobot_client = None
        
        client = get_lerobot_client()
        
        assert client is None
        print("✓ Returns None when manipulation disabled")
        
        # Test with manipulation enabled (but don't actually start it)
        print("\nTesting with ENABLE_MANIPULATION=true...")
        os.environ["ENABLE_MANIPULATION"] = "true"
        
        # Reset the global client
        mortis.app.lerobot_client = None
        
        # Mock the LeRobotAsyncClient to avoid actual initialization
        with patch('mortis.app.LeRobotAsyncClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            client = get_lerobot_client()
            
            assert client is not None
            print("✓ Returns client instance when manipulation enabled")
        
        # Clean up
        os.environ["ENABLE_MANIPULATION"] = "false"
        
        print("\n✓ LeRobotAsyncClient initialization test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ LeRobotAsyncClient initialization test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_gesture_routing_to_async_executor():
    """Test that gestures are routed to AsyncExecutor."""
    print("\n" + "=" * 70)
    print("TEST 3: Gesture Routing to AsyncExecutor")
    print("=" * 70)
    
    try:
        from mortis.app import mortis_reply_with_audio, get_async_executor
        from mortis.async_executor import Task, TaskType
        
        # Mock Gemini response for conversation
        conversation_response = {
            "type": "conversation",
            "message": "Beware, mortal...",
            "mood": "ominous",
            "gesture": "wave"
        }
        
        # Mock GeminiClient (imported inside mortis_reply_with_audio)
        with patch('mortis.gemini_client.GeminiClient') as mock_client_class:
            mock_client = Mock()
            mock_client.send_message.return_value = conversation_response
            mock_client_class.return_value = mock_client
            
            # Mock AsyncExecutor
            with patch('mortis.app.get_async_executor') as mock_get_executor:
                mock_executor = Mock()
                mock_executor.running = True
                mock_executor.submit_task = Mock()
                mock_get_executor.return_value = mock_executor
                
                # Mock TTS
                with patch('mortis.app.get_tts_service_instance') as mock_get_tts:
                    mock_tts = Mock()
                    mock_tts.synthesize.return_value = "/tmp/audio.mp3"
                    mock_get_tts.return_value = mock_tts
                    
                    # Call mortis_reply_with_audio
                    print("\nCalling mortis_reply_with_audio with conversation input...")
                    message, audio_path = mortis_reply_with_audio(
                        "Hello Mortis!",
                        [],
                        "gemini-2.0-flash-exp"
                    )
                    
                    print(f"✓ Message: {message}")
                    print(f"✓ Audio path: {audio_path}")
                    
                    # Verify response
                    assert message == "Beware, mortal..."
                    
                    # Verify AsyncExecutor.submit_task was called
                    mock_executor.submit_task.assert_called_once()
                    
                    # Verify the task is a gesture task
                    submitted_task = mock_executor.submit_task.call_args[0][0]
                    assert submitted_task.type == TaskType.GESTURE
                    assert submitted_task.gesture == "wave"
                    
                    print("✓ Gesture task submitted to AsyncExecutor")
        
        print("\n✓ Gesture routing test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Gesture routing test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_manipulation_routing_to_lerobot_client():
    """Test that manipulation tasks are routed to LeRobotAsyncClient."""
    print("\n" + "=" * 70)
    print("TEST 4: Manipulation Routing to LeRobotAsyncClient")
    print("=" * 70)
    
    try:
        from mortis.app import mortis_reply_with_audio
        
        # Mock Gemini response for manipulation
        manipulation_response = {
            "type": "manipulation",
            "message": "As you wish...",
            "mood": "sinister",
            "command": "Pick up the skull and place it in the green cup"
        }
        
        # Mock GeminiClient (imported inside mortis_reply_with_audio)
        with patch('mortis.gemini_client.GeminiClient') as mock_client_class:
            mock_client = Mock()
            mock_client.send_message.return_value = manipulation_response
            mock_client_class.return_value = mock_client
            
            # Mock LeRobotAsyncClient
            with patch('mortis.app.get_lerobot_client') as mock_get_client:
                mock_lerobot_client = Mock()
                mock_lerobot_client.is_running.return_value = True
                mock_lerobot_client.execute_task = Mock()
                mock_get_client.return_value = mock_lerobot_client
                
                # Mock TTS
                with patch('mortis.app.get_tts_service_instance') as mock_get_tts:
                    mock_tts = Mock()
                    mock_tts.synthesize.return_value = "/tmp/audio.mp3"
                    mock_get_tts.return_value = mock_tts
                    
                    # Call mortis_reply_with_audio
                    print("\nCalling mortis_reply_with_audio with manipulation command...")
                    message, audio_path = mortis_reply_with_audio(
                        "Move the skull to the green cup",
                        [],
                        "gemini-2.0-flash-exp"
                    )
                    
                    print(f"✓ Message: {message}")
                    print(f"✓ Audio path: {audio_path}")
                    
                    # Verify response
                    assert message == "As you wish..."
                    
                    # Verify LeRobotAsyncClient.execute_task was called
                    mock_lerobot_client.execute_task.assert_called_once_with(
                        "Pick up the skull and place it in the green cup",
                        blocking=False
                    )
                    
                    print("✓ Manipulation task submitted to LeRobotAsyncClient")
        
        print("\n✓ Manipulation routing test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Manipulation routing test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_handling():
    """Test that errors from both systems are handled gracefully."""
    print("\n" + "=" * 70)
    print("TEST 5: Error Handling")
    print("=" * 70)
    
    try:
        from mortis.app import mortis_reply_with_audio
        
        # Mock Gemini response
        conversation_response = {
            "type": "conversation",
            "message": "Test message",
            "mood": "neutral",
            "gesture": "idle"
        }
        
        # Mock GeminiClient (imported inside mortis_reply_with_audio)
        with patch('mortis.gemini_client.GeminiClient') as mock_client_class:
            mock_client = Mock()
            mock_client.send_message.return_value = conversation_response
            mock_client_class.return_value = mock_client
            
            # Mock AsyncExecutor that raises an error
            with patch('mortis.app.get_async_executor') as mock_get_executor:
                mock_executor = Mock()
                mock_executor.running = True
                mock_executor.submit_task.side_effect = Exception("Test error")
                mock_get_executor.return_value = mock_executor
                
                # Mock TTS
                with patch('mortis.app.get_tts_service_instance') as mock_get_tts:
                    mock_tts = Mock()
                    mock_tts.synthesize.return_value = "/tmp/audio.mp3"
                    mock_get_tts.return_value = mock_tts
                    
                    # Call mortis_reply_with_audio - should not crash
                    print("\nCalling mortis_reply_with_audio with failing AsyncExecutor...")
                    message, audio_path = mortis_reply_with_audio(
                        "Hello",
                        [],
                        "gemini-2.0-flash-exp"
                    )
                    
                    print(f"✓ Message: {message}")
                    print(f"✓ Audio path: {audio_path}")
                    
                    # Should still return a response
                    assert message == "Test message"
                    
                    print("✓ Error handled gracefully, response still returned")
        
        print("\n✓ Error handling test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Error handling test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all integration tests."""
    logger = setup_logging()
    
    print("\n" + "=" * 70)
    print("HYBRID EXECUTION INTEGRATION TEST SUITE")
    print("=" * 70)
    
    results = []
    
    # Run tests
    results.append(("AsyncExecutor Initialization", test_async_executor_initialization()))
    results.append(("LeRobotAsyncClient Initialization", test_lerobot_client_initialization()))
    results.append(("Gesture Routing to AsyncExecutor", test_gesture_routing_to_async_executor()))
    results.append(("Manipulation Routing to LeRobotAsyncClient", test_manipulation_routing_to_lerobot_client()))
    results.append(("Error Handling", test_error_handling()))
    
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
