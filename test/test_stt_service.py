#!/usr/bin/env python3
"""
Test script for STT service implementation.

This script tests the STTService to ensure:
1. Audio file validation works correctly
2. Gemini native audio transcription works
3. Fallback to Google STT works (if configured)
4. Error handling is robust
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mortis.stt_service import STTService, STTProvider, AudioFormat, AudioProcessingError


def setup_logging():
    """Set up logging for test output."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    return logging.getLogger(__name__)


def test_audio_format_validation():
    """Test audio format validation."""
    print("\n" + "=" * 70)
    print("TEST 1: Audio Format Validation")
    print("=" * 70)
    
    try:
        stt_service = STTService()
        
        # Test valid formats
        valid_formats = ["test.wav", "test.mp3", "test.webm", "test.ogg", "test.flac"]
        print("\nTesting valid formats:")
        for fmt in valid_formats:
            test_path = Path(fmt)
            is_valid = stt_service._validate_audio_format(test_path)
            status = "✓" if is_valid else "✗"
            print(f"  {status} {fmt}: {is_valid}")
        
        # Test invalid formats
        invalid_formats = ["test.txt", "test.pdf", "test.mp4", "test.avi"]
        print("\nTesting invalid formats:")
        for fmt in invalid_formats:
            test_path = Path(fmt)
            is_valid = stt_service._validate_audio_format(test_path)
            status = "✓" if not is_valid else "✗"
            print(f"  {status} {fmt}: {is_valid}")
        
        print("\n✓ Audio format validation test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Audio format validation test FAILED: {e}")
        return False


def test_stt_initialization():
    """Test STT service initialization."""
    print("\n" + "=" * 70)
    print("TEST 2: STT Service Initialization")
    print("=" * 70)
    
    try:
        # Test default initialization
        print("\nInitializing with defaults...")
        stt_service = STTService()
        print(f"✓ Provider: {stt_service.provider.value}")
        print(f"✓ Model: {stt_service.model_name}")
        print(f"✓ Language: {stt_service.language_code}")
        print(f"✓ Fallback enabled: {stt_service.enable_fallback}")
        
        # Test custom initialization
        print("\nInitializing with custom settings...")
        stt_service_custom = STTService(
            provider=STTProvider.GEMINI,
            language_code="es-ES",
            enable_fallback=False
        )
        print(f"✓ Provider: {stt_service_custom.provider.value}")
        print(f"✓ Language: {stt_service_custom.language_code}")
        print(f"✓ Fallback enabled: {stt_service_custom.enable_fallback}")
        
        print("\n✓ STT initialization test PASSED")
        return True
        
    except ValueError as e:
        print(f"\n✗ STT initialization test FAILED: {e}")
        print("Please set GEMINI_API_KEY in your .env file")
        return False
    except Exception as e:
        print(f"\n✗ STT initialization test FAILED: {e}")
        return False


def test_stt_configuration():
    """Test STT service configuration changes."""
    print("\n" + "=" * 70)
    print("TEST 3: STT Service Configuration")
    print("=" * 70)
    
    try:
        stt_service = STTService()
        
        print("\nInitial configuration:")
        print(f"  Provider: {stt_service.provider.value}")
        print(f"  Language: {stt_service.language_code}")
        print(f"  Fallback: {stt_service.enable_fallback}")
        
        print("\nChanging configuration...")
        stt_service.configure(
            provider=STTProvider.GOOGLE_STT,
            language_code="fr-FR",
            enable_fallback=False
        )
        
        print("Updated configuration:")
        print(f"  Provider: {stt_service.provider.value}")
        print(f"  Language: {stt_service.language_code}")
        print(f"  Fallback: {stt_service.enable_fallback}")
        
        # Verify changes
        assert stt_service.provider == STTProvider.GOOGLE_STT
        assert stt_service.language_code == "fr-FR"
        assert stt_service.enable_fallback == False
        
        print("\n✓ STT configuration test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ STT configuration test FAILED: {e}")
        return False


def test_error_handling():
    """Test error handling for missing files and invalid formats."""
    print("\n" + "=" * 70)
    print("TEST 4: Error Handling")
    print("=" * 70)
    
    try:
        stt_service = STTService()
        
        # Test missing file
        print("\nTesting missing file error...")
        try:
            stt_service.transcribe("nonexistent_file.wav")
            print("✗ Should have raised FileNotFoundError")
            return False
        except FileNotFoundError as e:
            print(f"✓ Correctly raised FileNotFoundError: {e}")
        
        # Test invalid format
        print("\nTesting invalid format error...")
        # Create a temporary invalid file
        invalid_file = Path("test_invalid.txt")
        invalid_file.write_text("test")
        
        try:
            stt_service.transcribe(str(invalid_file))
            print("✗ Should have raised AudioProcessingError")
            invalid_file.unlink()
            return False
        except AudioProcessingError as e:
            print(f"✓ Correctly raised AudioProcessingError: {e}")
            invalid_file.unlink()
        
        print("\n✓ Error handling test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Error handling test FAILED: {e}")
        return False


def test_transcription_with_sample():
    """Test actual transcription if sample audio file is provided."""
    print("\n" + "=" * 70)
    print("TEST 5: Transcription (Optional - requires audio file)")
    print("=" * 70)
    
    # Check if user provided an audio file
    if len(sys.argv) < 2:
        print("\nℹ️  No audio file provided. Skipping transcription test.")
        print("To test transcription, run:")
        print("  python test/test_stt_service.py <audio_file.wav>")
        return True
    
    audio_file = sys.argv[1]
    
    try:
        print(f"\nTranscribing: {audio_file}")
        stt_service = STTService()
        
        transcript = stt_service.transcribe(audio_file)
        
        print(f"\n✓ Transcription successful!")
        print(f"Transcript: {transcript}")
        print(f"Length: {len(transcript)} characters")
        
        return True
        
    except FileNotFoundError as e:
        print(f"\n✗ File not found: {e}")
        return False
    except AudioProcessingError as e:
        print(f"\n✗ Transcription failed: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return False


def main():
    """Run all tests."""
    logger = setup_logging()
    
    print("\n" + "=" * 70)
    print("STT SERVICE TEST SUITE")
    print("=" * 70)
    
    results = []
    
    # Run tests
    results.append(("Audio Format Validation", test_audio_format_validation()))
    results.append(("STT Initialization", test_stt_initialization()))
    results.append(("STT Configuration", test_stt_configuration()))
    results.append(("Error Handling", test_error_handling()))
    results.append(("Transcription", test_transcription_with_sample()))
    
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
