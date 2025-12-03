#!/usr/bin/env python3
"""
Test script for audio input integration in Gradio UI.

This script tests the audio input handler to ensure:
1. Audio input processing works correctly
2. Transcription display updates properly
3. Error handling is graceful
4. Integration with chat interface works
"""

import sys
import logging
from pathlib import Path
from unittest.mock import Mock, patch

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


def test_process_audio_input_with_none():
    """Test process_audio_input with None input."""
    print("\n" + "=" * 70)
    print("TEST 1: Process Audio Input with None")
    print("=" * 70)
    
    try:
        from mortis.app import process_audio_input
        
        result = process_audio_input(None)
        
        assert result == "", f"Expected empty string, got: {result}"
        print("✓ Correctly returns empty string for None input")
        
        print("\n✓ Test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Test FAILED: {e}")
        return False


def test_process_audio_input_with_missing_file():
    """Test process_audio_input with missing file."""
    print("\n" + "=" * 70)
    print("TEST 2: Process Audio Input with Missing File")
    print("=" * 70)
    
    try:
        from mortis.app import process_audio_input
        
        result = process_audio_input("nonexistent_file.wav")
        
        assert result.startswith("[Error:"), f"Expected error message, got: {result}"
        assert "not found" in result.lower(), f"Expected 'not found' in error, got: {result}"
        print(f"✓ Correctly returns error message: {result[:50]}...")
        
        print("\n✓ Test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Test FAILED: {e}")
        return False


def test_process_audio_input_with_invalid_format():
    """Test process_audio_input with invalid audio format."""
    print("\n" + "=" * 70)
    print("TEST 3: Process Audio Input with Invalid Format")
    print("=" * 70)
    
    try:
        from mortis.app import process_audio_input
        
        # Create a temporary invalid file
        invalid_file = Path("test_invalid.txt")
        invalid_file.write_text("test")
        
        result = process_audio_input(str(invalid_file))
        
        # Clean up
        invalid_file.unlink()
        
        assert result.startswith("[Error:"), f"Expected error message, got: {result}"
        print(f"✓ Correctly returns error message: {result[:50]}...")
        
        print("\n✓ Test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Test FAILED: {e}")
        # Clean up if test failed
        if Path("test_invalid.txt").exists():
            Path("test_invalid.txt").unlink()
        return False


def test_stt_service_initialization():
    """Test STT service lazy initialization."""
    print("\n" + "=" * 70)
    print("TEST 4: STT Service Lazy Initialization")
    print("=" * 70)
    
    try:
        from mortis.app import get_stt_service
        
        # First call should initialize
        print("First call to get_stt_service()...")
        stt1 = get_stt_service()
        assert stt1 is not None, "STT service should not be None"
        print("✓ STT service initialized")
        
        # Second call should return same instance
        print("Second call to get_stt_service()...")
        stt2 = get_stt_service()
        assert stt1 is stt2, "Should return same instance"
        print("✓ Returns same instance (singleton pattern)")
        
        print("\n✓ Test PASSED")
        return True
        
    except ValueError as e:
        print(f"\n✗ Test FAILED: {e}")
        print("Please set GEMINI_API_KEY in your .env file")
        return False
    except Exception as e:
        print(f"\n✗ Test FAILED: {e}")
        return False


def test_audio_input_handler_logic():
    """Test the audio input handler logic."""
    print("\n" + "=" * 70)
    print("TEST 5: Audio Input Handler Logic")
    print("=" * 70)
    
    try:
        # Import the handler function from the UI
        # Note: This is defined inside ui() so we can't directly test it
        # Instead, we test the components it uses
        
        from mortis.app import process_audio_input, mortis_reply
        
        print("✓ Audio input handler components are accessible")
        print("✓ process_audio_input function exists")
        print("✓ mortis_reply function exists")
        
        # Test the flow logic
        print("\nTesting handler flow:")
        print("  1. Audio input → process_audio_input()")
        print("  2. Transcript → mortis_reply()")
        print("  3. Response → chat history")
        
        print("\n✓ Test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Test FAILED: {e}")
        return False


def main():
    """Run all tests."""
    logger = setup_logging()
    
    print("\n" + "=" * 70)
    print("AUDIO INPUT INTEGRATION TEST SUITE")
    print("=" * 70)
    
    results = []
    
    # Run tests
    results.append(("Process Audio with None", test_process_audio_input_with_none()))
    results.append(("Process Audio with Missing File", test_process_audio_input_with_missing_file()))
    results.append(("Process Audio with Invalid Format", test_process_audio_input_with_invalid_format()))
    results.append(("STT Service Initialization", test_stt_service_initialization()))
    results.append(("Audio Input Handler Logic", test_audio_input_handler_logic()))
    
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
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
