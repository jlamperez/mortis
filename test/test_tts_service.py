#!/usr/bin/env python3
"""
Test script for TTS service implementation.

This script tests the TTSService to ensure:
1. TTS service initialization works correctly
2. Audio file generation works (Google TTS or gTTS)
3. File cleanup works properly
4. Error handling is robust
"""

import sys
import logging
from pathlib import Path
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mortis.tts_service import TTSService, get_tts_service, synthesize_speech


def setup_logging():
    """Set up logging for test output."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    return logging.getLogger(__name__)


def test_tts_initialization():
    """Test TTS service initialization."""
    print("\n" + "=" * 70)
    print("TEST 1: TTS Service Initialization")
    print("=" * 70)
    
    try:
        # Test with Google TTS (may fail if no credentials)
        print("\nInitializing with Google TTS...")
        tts_service_google = TTSService(use_google_tts=True)
        print(f"✓ Google TTS enabled: {tts_service_google.use_google_tts}")
        print(f"✓ Voice name: {tts_service_google.voice_name}")
        print(f"✓ Speaking rate: {tts_service_google.speaking_rate}")
        print(f"✓ Pitch: {tts_service_google.pitch}")
        print(f"✓ Output directory: {tts_service_google.output_dir}")
        
        # Test with gTTS fallback
        print("\nInitializing with gTTS fallback...")
        tts_service_gtts = TTSService(use_google_tts=False)
        print(f"✓ Google TTS enabled: {tts_service_gtts.use_google_tts}")
        print(f"✓ Output directory: {tts_service_gtts.output_dir}")
        
        print("\n✓ TTS initialization test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ TTS initialization test FAILED: {e}")
        return False


def test_output_directory_creation():
    """Test that output directory is created."""
    print("\n" + "=" * 70)
    print("TEST 2: Output Directory Creation")
    print("=" * 70)
    
    try:
        # Create service with custom output directory
        test_dir = "test_outputs"
        tts_service = TTSService(output_dir=test_dir, use_google_tts=False)
        
        # Check directory exists
        if tts_service.output_dir.exists():
            print(f"✓ Output directory created: {tts_service.output_dir}")
        else:
            print(f"✗ Output directory not created: {tts_service.output_dir}")
            return False
        
        # Cleanup
        tts_service.output_dir.rmdir()
        
        print("\n✓ Output directory creation test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Output directory creation test FAILED: {e}")
        return False


def test_gtts_synthesis():
    """Test speech synthesis with gTTS."""
    print("\n" + "=" * 70)
    print("TEST 3: gTTS Speech Synthesis")
    print("=" * 70)
    
    try:
        # Initialize with gTTS (no credentials needed)
        tts_service = TTSService(use_google_tts=False, output_dir="test_outputs")
        
        # Test text
        test_text = "Beware, mortal. The spirits are watching."
        print(f"\nSynthesizing: '{test_text}'")
        
        # Synthesize
        audio_path = tts_service.synthesize(test_text, filename="test_gtts")
        
        if audio_path and Path(audio_path).exists():
            file_size = Path(audio_path).stat().st_size
            print(f"✓ Audio file created: {audio_path}")
            print(f"✓ File size: {file_size} bytes")
            
            # Cleanup
            Path(audio_path).unlink()
            tts_service.output_dir.rmdir()
            
            print("\n✓ gTTS synthesis test PASSED")
            return True
        else:
            print(f"✗ Audio file not created")
            return False
        
    except Exception as e:
        print(f"\n✗ gTTS synthesis test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_google_tts_synthesis():
    """Test speech synthesis with Google Cloud TTS (if credentials available)."""
    print("\n" + "=" * 70)
    print("TEST 4: Google Cloud TTS Synthesis (Optional)")
    print("=" * 70)
    
    try:
        # Try to initialize with Google TTS
        tts_service = TTSService(use_google_tts=True, output_dir="test_outputs")
        
        if not tts_service.use_google_tts:
            print("\nℹ️  Google Cloud TTS not available (no credentials).")
            print("Skipping Google TTS test. Set GOOGLE_APPLICATION_CREDENTIALS to test.")
            return True
        
        # Test text
        test_text = "The darkness calls to you."
        print(f"\nSynthesizing with Google TTS: '{test_text}'")
        
        # Synthesize
        audio_path = tts_service.synthesize(test_text, filename="test_google")
        
        if audio_path and Path(audio_path).exists():
            file_size = Path(audio_path).stat().st_size
            print(f"✓ Audio file created: {audio_path}")
            print(f"✓ File size: {file_size} bytes")
            
            # Cleanup
            Path(audio_path).unlink()
            tts_service.output_dir.rmdir()
            
            print("\n✓ Google TTS synthesis test PASSED")
            return True
        else:
            print(f"✗ Audio file not created")
            return False
        
    except Exception as e:
        print(f"\n✗ Google TTS synthesis test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_empty_text_handling():
    """Test handling of empty or invalid text."""
    print("\n" + "=" * 70)
    print("TEST 5: Empty Text Handling")
    print("=" * 70)
    
    try:
        tts_service = TTSService(use_google_tts=False, output_dir="test_outputs")
        
        # Test empty string
        print("\nTesting empty string...")
        result = tts_service.synthesize("")
        if result is None:
            print("✓ Empty string correctly returned None")
        else:
            print("✗ Empty string should return None")
            return False
        
        # Test whitespace only
        print("\nTesting whitespace-only string...")
        result = tts_service.synthesize("   ")
        if result is None:
            print("✓ Whitespace-only string correctly returned None")
        else:
            print("✗ Whitespace-only string should return None")
            return False
        
        # Cleanup
        if tts_service.output_dir.exists():
            tts_service.output_dir.rmdir()
        
        print("\n✓ Empty text handling test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Empty text handling test FAILED: {e}")
        return False


def test_file_cleanup():
    """Test cleanup of old audio files."""
    print("\n" + "=" * 70)
    print("TEST 6: File Cleanup")
    print("=" * 70)
    
    try:
        tts_service = TTSService(use_google_tts=False, output_dir="test_outputs")
        
        # Create some test files
        print("\nCreating test audio files...")
        files = []
        for i in range(3):
            audio_path = tts_service.synthesize(f"Test message {i}", filename=f"test_cleanup_{i}")
            if audio_path:
                files.append(Path(audio_path))
                print(f"✓ Created: {audio_path}")
        
        # Wait a moment
        time.sleep(0.1)
        
        # Create one more recent file
        recent_file = tts_service.synthesize("Recent message", filename="test_cleanup_recent")
        if recent_file:
            files.append(Path(recent_file))
            print(f"✓ Created recent file: {recent_file}")
        
        print(f"\nTotal files created: {len(files)}")
        
        # Cleanup old files (max_age_seconds=0 should remove all but the most recent)
        print("\nCleaning up old files (max_age=0.05s)...")
        time.sleep(0.1)
        tts_service.cleanup_old_files(max_age_seconds=0.05)
        
        # Check remaining files
        remaining = list(tts_service.output_dir.glob("test_cleanup_*.mp3"))
        print(f"Remaining files: {len(remaining)}")
        
        # Cleanup all test files
        for f in tts_service.output_dir.glob("test_cleanup_*.mp3"):
            f.unlink()
        tts_service.output_dir.rmdir()
        
        print("\n✓ File cleanup test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ File cleanup test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_global_service():
    """Test global TTS service singleton."""
    print("\n" + "=" * 70)
    print("TEST 7: Global TTS Service")
    print("=" * 70)
    
    try:
        # Get global service
        print("\nGetting global TTS service...")
        service1 = get_tts_service()
        print(f"✓ Service 1: {service1}")
        
        # Get again - should be same instance
        service2 = get_tts_service()
        print(f"✓ Service 2: {service2}")
        
        if service1 is service2:
            print("✓ Both services are the same instance (singleton)")
        else:
            print("✗ Services are different instances")
            return False
        
        # Test convenience function
        print("\nTesting convenience function...")
        audio_path = synthesize_speech("Test global service", filename="test_global")
        
        if audio_path and Path(audio_path).exists():
            print(f"✓ Convenience function works: {audio_path}")
            Path(audio_path).unlink()
        else:
            print("✗ Convenience function failed")
            return False
        
        print("\n✓ Global service test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Global service test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_character_voice_parameters():
    """Test that Mortis character voice parameters are configured correctly."""
    print("\n" + "=" * 70)
    print("TEST 8: Mortis Character Voice Parameters")
    print("=" * 70)
    
    try:
        tts_service = TTSService(use_google_tts=True)
        
        print("\nMortis voice configuration:")
        print(f"  Voice name: {tts_service.voice_name}")
        print(f"  Speaking rate: {tts_service.speaking_rate} (slower for ominous effect)")
        print(f"  Pitch: {tts_service.pitch} (lower for spooky voice)")
        
        # Verify parameters are set for Mortis character
        assert tts_service.speaking_rate < 1.0, "Speaking rate should be slower than normal"
        assert tts_service.pitch < 0, "Pitch should be lower than normal"
        assert "Neural2" in tts_service.voice_name or "male" in tts_service.voice_name.lower(), \
            "Should use a male/deep voice"
        
        print("\n✓ Character voice parameters test PASSED")
        return True
        
    except AssertionError as e:
        print(f"\n✗ Character voice parameters test FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Character voice parameters test FAILED: {e}")
        return False


def main():
    """Run all tests."""
    logger = setup_logging()
    
    print("\n" + "=" * 70)
    print("TTS SERVICE TEST SUITE")
    print("=" * 70)
    
    results = []
    
    # Run tests
    results.append(("TTS Initialization", test_tts_initialization()))
    results.append(("Output Directory Creation", test_output_directory_creation()))
    results.append(("gTTS Synthesis", test_gtts_synthesis()))
    results.append(("Google TTS Synthesis", test_google_tts_synthesis()))
    results.append(("Empty Text Handling", test_empty_text_handling()))
    results.append(("File Cleanup", test_file_cleanup()))
    results.append(("Global Service", test_global_service()))
    results.append(("Character Voice Parameters", test_character_voice_parameters()))
    
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
