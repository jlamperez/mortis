"""
Speech-to-Text service for Mortis voice input.

This module provides the STTService class for converting audio input to text,
with support for Gemini native audio processing and fallback to Google Cloud Speech-to-Text.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Literal
from enum import Enum
from dotenv import load_dotenv

from google import genai
from google.genai import types

# Load environment variables
REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / ".env")

# Configure logging
logger = logging.getLogger(__name__)


class STTProvider(Enum):
    """Available Speech-to-Text providers."""
    GEMINI = "gemini"
    GOOGLE_STT = "google_stt"


class AudioFormat(Enum):
    """Supported audio formats."""
    WAV = "wav"
    MP3 = "mp3"
    WEBM = "webm"
    OGG = "ogg"
    FLAC = "flac"


class AudioProcessingError(Exception):
    """Base exception for audio processing errors."""
    pass


class STTService:
    """
    Speech-to-Text service for converting audio input to text.
    
    Supports multiple STT providers:
    - Gemini native audio (primary, recommended)
    - Google Cloud Speech-to-Text (fallback)
    
    The service automatically handles audio format validation and conversion.
    """
    
    def __init__(
        self,
        provider: Optional[STTProvider] = None,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        language_code: str = "en-US",
        enable_fallback: bool = True
    ):
        """
        Initialize STT service.
        
        Args:
            provider: STT provider to use (defaults to GEMINI from env or GEMINI)
            api_key: API key for Gemini (defaults to GEMINI_API_KEY env var)
            model_name: Gemini model to use (defaults to GEMINI_MODEL env var or gemini-1.5-flash)
            language_code: Language code for transcription (default: en-US)
            enable_fallback: Whether to enable fallback to Google STT on Gemini failure
        """
        # Determine provider from environment or default to Gemini
        if provider is None:
            provider_str = os.getenv("STT_PROVIDER", "gemini").lower()
            try:
                provider = STTProvider(provider_str)
            except ValueError:
                logger.warning(f"Invalid STT_PROVIDER '{provider_str}', defaulting to GEMINI")
                provider = STTProvider.GEMINI
        
        self.provider = provider
        self.language_code = language_code
        self.enable_fallback = enable_fallback
        
        # Initialize Gemini client for audio processing
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY must be provided or set in environment")
        
        self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        self.client = genai.Client(api_key=self.api_key)
        
        # Initialize Google Cloud STT client (lazy loading)
        self._google_stt_client = None
        
        logger.info(
            f"STTService initialized with provider: {self.provider.value}, "
            f"model: {self.model_name}, language: {self.language_code}, "
            f"fallback: {self.enable_fallback}"
        )
    
    def transcribe(self, audio_path: str) -> str:
        """
        Transcribe audio file to text.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcribed text
            
        Raises:
            AudioProcessingError: If transcription fails with all providers
            FileNotFoundError: If audio file doesn't exist
        """
        # Validate audio file exists
        audio_file = Path(audio_path)
        if not audio_file.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Validate audio format
        if not self._validate_audio_format(audio_file):
            raise AudioProcessingError(
                f"Unsupported audio format: {audio_file.suffix}. "
                f"Supported formats: {[fmt.value for fmt in AudioFormat]}"
            )
        
        logger.info(f"Transcribing audio file: {audio_path} using {self.provider.value}")
        
        # Try primary provider
        try:
            if self.provider == STTProvider.GEMINI:
                return self._transcribe_with_gemini(audio_path)
            elif self.provider == STTProvider.GOOGLE_STT:
                return self._transcribe_with_google_stt(audio_path)
        except Exception as e:
            logger.warning(f"Primary STT provider ({self.provider.value}) failed: {e}")
            
            # Try fallback if enabled
            if self.enable_fallback:
                logger.info("Attempting fallback STT provider...")
                try:
                    if self.provider == STTProvider.GEMINI:
                        # Fallback to Google STT
                        return self._transcribe_with_google_stt(audio_path)
                    else:
                        # Fallback to Gemini
                        return self._transcribe_with_gemini(audio_path)
                except Exception as fallback_error:
                    logger.error(f"Fallback STT provider also failed: {fallback_error}")
                    raise AudioProcessingError(
                        f"All STT providers failed. Primary: {e}, Fallback: {fallback_error}"
                    ) from fallback_error
            else:
                raise AudioProcessingError(f"STT transcription failed: {e}") from e
    
    def _validate_audio_format(self, audio_file: Path) -> bool:
        """
        Validate that audio file format is supported.
        
        Args:
            audio_file: Path to audio file
            
        Returns:
            True if format is supported, False otherwise
        """
        suffix = audio_file.suffix.lstrip('.').lower()
        supported_formats = [fmt.value for fmt in AudioFormat]
        return suffix in supported_formats
    
    def _transcribe_with_gemini(self, audio_path: str) -> str:
        """
        Transcribe audio using Gemini native audio support.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcribed text
            
        Raises:
            Exception: If Gemini API call fails
        """
        logger.debug(f"Transcribing with Gemini: {audio_path}")
        
        try:
            # Upload audio file to Gemini
            audio_file = self.client.files.upload(file=audio_path)
            logger.debug(f"Audio file uploaded: {audio_file.name}")
            
            # Create prompt for transcription
            prompt = (
                "Transcribe this audio accurately. "
                "Return only the transcribed text without any additional commentary or formatting."
            )
            
            # Generate content with audio
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[prompt, audio_file]
            )
            
            # Extract transcribed text
            if response.text is None:
                logger.warning("Gemini returned None for transcription")
                logger.debug(f"Response object: {response}")
                # Check if there are candidates with parts
                if hasattr(response, 'candidates') and response.candidates:
                    logger.debug(f"Response has {len(response.candidates)} candidates")
                    for i, candidate in enumerate(response.candidates):
                        logger.debug(f"Candidate {i}: {candidate}")
                transcript = ""
            else:
                transcript = response.text.strip()
            
            if transcript:
                logger.info(f"Gemini transcription successful: '{transcript[:50]}...'")
            else:
                logger.warning("Gemini transcription returned empty result")
            
            # Clean up uploaded file
            try:
                self.client.files.delete(name=audio_file.name)
                logger.debug(f"Deleted uploaded audio file: {audio_file.name}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to delete uploaded audio file: {cleanup_error}")
            
            return transcript
            
        except Exception as e:
            logger.error(f"Gemini transcription failed: {type(e).__name__}: {e}")
            raise
    
    def _transcribe_with_google_stt(self, audio_path: str) -> str:
        """
        Transcribe audio using Google Cloud Speech-to-Text API.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcribed text
            
        Raises:
            Exception: If Google STT API call fails
            ImportError: If google-cloud-speech is not installed
        """
        logger.debug(f"Transcribing with Google STT: {audio_path}")
        
        try:
            from google.cloud import speech_v1
        except ImportError:
            raise ImportError(
                "google-cloud-speech is not installed. "
                "Install it with: pip install google-cloud-speech"
            )
        
        # Initialize Google STT client (lazy loading)
        if self._google_stt_client is None:
            self._google_stt_client = speech_v1.SpeechClient()
            logger.debug("Google STT client initialized")
        
        # Read audio file
        with open(audio_path, "rb") as audio_file:
            audio_content = audio_file.read()
        
        # Determine audio encoding from file extension
        audio_path_obj = Path(audio_path)
        suffix = audio_path_obj.suffix.lstrip('.').lower()
        
        encoding_map = {
            "wav": speech_v1.RecognitionConfig.AudioEncoding.LINEAR16,
            "mp3": speech_v1.RecognitionConfig.AudioEncoding.MP3,
            "flac": speech_v1.RecognitionConfig.AudioEncoding.FLAC,
            "ogg": speech_v1.RecognitionConfig.AudioEncoding.OGG_OPUS,
            "webm": speech_v1.RecognitionConfig.AudioEncoding.WEBM_OPUS,
        }
        
        encoding = encoding_map.get(suffix, speech_v1.RecognitionConfig.AudioEncoding.LINEAR16)
        
        # Configure recognition
        audio = speech_v1.RecognitionAudio(content=audio_content)
        config = speech_v1.RecognitionConfig(
            encoding=encoding,
            language_code=self.language_code,
            enable_automatic_punctuation=True,
        )
        
        # Perform transcription
        try:
            response = self._google_stt_client.recognize(config=config, audio=audio)
            
            # Extract transcript from results
            if not response.results:
                logger.warning("Google STT returned no results")
                return ""
            
            # Combine all alternatives (usually just one)
            transcript = " ".join(
                result.alternatives[0].transcript
                for result in response.results
                if result.alternatives
            )
            
            logger.info(f"Google STT transcription successful: '{transcript[:50]}...'")
            return transcript.strip()
            
        except Exception as e:
            logger.error(f"Google STT transcription failed: {type(e).__name__}: {e}")
            raise
    
    def configure(
        self,
        provider: Optional[STTProvider] = None,
        language_code: Optional[str] = None,
        enable_fallback: Optional[bool] = None
    ):
        """
        Reconfigure STT service settings.
        
        Args:
            provider: New STT provider to use
            language_code: New language code
            enable_fallback: Whether to enable fallback
        """
        if provider is not None:
            self.provider = provider
            logger.info(f"STT provider changed to: {provider.value}")
        
        if language_code is not None:
            self.language_code = language_code
            logger.info(f"Language code changed to: {language_code}")
        
        if enable_fallback is not None:
            self.enable_fallback = enable_fallback
            logger.info(f"Fallback {'enabled' if enable_fallback else 'disabled'}")


# Example usage
if __name__ == "__main__":
    import sys
    
    # Configure logging for testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Check for audio file argument
    if len(sys.argv) < 2:
        print("Usage: python -m mortis.stt_service <audio_file>")
        print("Example: python -m mortis.stt_service test_audio.wav")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    
    try:
        # Create STT service
        stt_service = STTService()
        
        # Transcribe audio
        print(f"\nTranscribing: {audio_file}")
        print("-" * 60)
        transcript = stt_service.transcribe(audio_file)
        print(f"Transcript: {transcript}")
        print("-" * 60)
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except AudioProcessingError as e:
        print(f"Audio processing error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Please set GEMINI_API_KEY in your .env file")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {type(e).__name__}: {e}")
        sys.exit(1)
