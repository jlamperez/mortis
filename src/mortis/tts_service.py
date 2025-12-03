"""
Text-to-Speech service for Mortis voice output.

Provides TTS capabilities using Google Cloud Text-to-Speech API with
fallback to local gTTS for offline scenarios.
"""

import os
import time
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class TTSService:
    """
    Text-to-Speech service for converting Mortis responses to audio.
    
    Uses Google Cloud TTS as primary service with gTTS as fallback.
    Configured for a deep, ominous voice suitable for Mortis character.
    """
    
    def __init__(
        self,
        output_dir: str = "outputs",
        use_google_tts: bool = True,
        voice_name: str = "en-US-Neural2-D",
        speaking_rate: float = 0.9,
        pitch: float = -2.0
    ):
        """
        Initialize TTS service.
        
        Args:
            output_dir: Directory for generated audio files
            use_google_tts: Whether to use Google Cloud TTS (requires credentials)
            voice_name: Google TTS voice name (Neural2-D is deep male voice)
            speaking_rate: Speech speed (0.9 = slightly slower for ominous effect)
            pitch: Voice pitch (-2.0 = lower for spooky voice)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.use_google_tts = use_google_tts
        self.voice_name = voice_name
        self.speaking_rate = speaking_rate
        self.pitch = pitch
        
        # Try to initialize Google TTS client
        self.google_client = None
        self.texttospeech = None
        if self.use_google_tts:
            try:
                from google.cloud import texttospeech
                self.google_client = texttospeech.TextToSpeechClient()
                self.texttospeech = texttospeech
                logger.info("Google Cloud TTS initialized successfully")
            except ImportError as e:
                logger.warning(f"Google Cloud TTS not available: {e}. Will use gTTS fallback.")
                self.use_google_tts = False
            except Exception as e:
                logger.warning(f"Failed to initialize Google TTS: {e}. Will use gTTS fallback.")
                self.use_google_tts = False
        
        logger.info(f"TTS Service initialized (Google TTS: {self.use_google_tts})")
    
    def synthesize(self, text: str, filename: Optional[str] = None) -> Optional[str]:
        """
        Convert text to speech audio file.
        
        Args:
            text: Text to convert to speech
            filename: Optional custom filename (without extension)
        
        Returns:
            Path to generated audio file, or None if synthesis fails
        """
        if not text or not text.strip():
            logger.warning("Empty text provided to TTS service")
            return None
        
        # Generate filename if not provided
        if filename is None:
            timestamp = int(time.time() * 1000)
            filename = f"mortis_response_{timestamp}"
        
        # Try Google TTS first
        if self.use_google_tts and self.google_client:
            try:
                audio_path = self._synthesize_google_tts(text, filename)
                logger.info(f"Generated audio with Google TTS: {audio_path}")
                return audio_path
            except Exception as e:
                logger.error(f"Google TTS failed: {e}. Falling back to gTTS.")
        
        # Fallback to gTTS
        try:
            audio_path = self._synthesize_gtts(text, filename)
            logger.info(f"Generated audio with gTTS: {audio_path}")
            return audio_path
        except Exception as e:
            logger.error(f"gTTS also failed: {e}. No audio generated.")
            return None
    
    def _synthesize_google_tts(self, text: str, filename: str) -> str:
        """
        Synthesize speech using Google Cloud TTS.
        
        Args:
            text: Text to synthesize
            filename: Base filename (without extension)
        
        Returns:
            Path to generated MP3 file
        """
        # Prepare synthesis input
        synthesis_input = self.texttospeech.SynthesisInput(text=text)
        
        # Configure voice parameters for Mortis character
        voice = self.texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name=self.voice_name,
            ssml_gender=self.texttospeech.SsmlVoiceGender.MALE
        )
        
        # Configure audio output
        audio_config = self.texttospeech.AudioConfig(
            audio_encoding=self.texttospeech.AudioEncoding.MP3,
            speaking_rate=self.speaking_rate,
            pitch=self.pitch
        )
        
        # Perform synthesis
        response = self.google_client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        # Save audio file
        output_path = self.output_dir / f"{filename}.mp3"
        with open(output_path, "wb") as out:
            out.write(response.audio_content)
        
        return str(output_path)
    
    def _synthesize_gtts(self, text: str, filename: str) -> str:
        """
        Synthesize speech using gTTS (local fallback).
        
        Args:
            text: Text to synthesize
            filename: Base filename (without extension)
        
        Returns:
            Path to generated MP3 file
        """
        from gtts import gTTS
        
        # Create TTS object with slower speech for ominous effect
        tts = gTTS(text=text, lang='en', slow=True)
        
        # Save audio file
        output_path = self.output_dir / f"{filename}.mp3"
        tts.save(str(output_path))
        
        return str(output_path)
    
    def cleanup_old_files(self, max_age_seconds: int = 3600):
        """
        Remove old audio files to prevent disk space issues.
        
        Args:
            max_age_seconds: Maximum age of files to keep (default: 1 hour)
        """
        current_time = time.time()
        removed_count = 0
        
        for audio_file in self.output_dir.glob("mortis_response_*.mp3"):
            try:
                file_age = current_time - audio_file.stat().st_mtime
                if file_age > max_age_seconds:
                    audio_file.unlink()
                    removed_count += 1
            except Exception as e:
                logger.warning(f"Failed to remove old file {audio_file}: {e}")
        
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old audio files")


# Global TTS service instance
_tts_service: Optional[TTSService] = None


def get_tts_service() -> TTSService:
    """
    Get or create global TTS service instance.
    
    Returns:
        Singleton TTSService instance
    """
    global _tts_service
    if _tts_service is None:
        # Check if Google Cloud credentials are available
        use_google = bool(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
        _tts_service = TTSService(use_google_tts=use_google)
    return _tts_service


def synthesize_speech(text: str, filename: Optional[str] = None) -> Optional[str]:
    """
    Convenience function to synthesize speech using global TTS service.
    
    Args:
        text: Text to convert to speech
        filename: Optional custom filename
    
    Returns:
        Path to generated audio file, or None if synthesis fails
    """
    service = get_tts_service()
    return service.synthesize(text, filename)
