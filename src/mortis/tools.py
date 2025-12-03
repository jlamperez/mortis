"""
LLM integration for Mortis conversational AI.

This module provides the ask_mortis() function that integrates with the Gemini API
to generate character-driven responses and coordinate gesture execution.
"""

import logging
import time
from typing import Tuple, Optional
from pathlib import Path

from .robot import MortisArm
from .gemini_client import GeminiClient
from .models import GeminiResponse

# Configure logging
logger = logging.getLogger(__name__)

# Global instances
mortis_arm = MortisArm()
gemini_client = None  # Lazy initialization
stt_service = None  # Lazy initialization
tts_service = None  # Lazy initialization


def _get_gemini_client() -> GeminiClient:
    """
    Get or create the global GeminiClient instance.
    
    Returns:
        GeminiClient instance
    """
    global gemini_client
    if gemini_client is None:
        gemini_client = GeminiClient()
        logger.info("GeminiClient initialized")
    return gemini_client


def _get_stt_service():
    """
    Get or create the global STTService instance.
    
    Returns:
        STTService instance
    """
    global stt_service
    if stt_service is None:
        from .stt_service import STTService
        stt_service = STTService()
        logger.info("STTService initialized")
    return stt_service


def _get_tts_service():
    """
    Get or create the global TTSService instance.
    
    Returns:
        TTSService instance
    """
    global tts_service
    if tts_service is None:
        from .tts_service import get_tts_service
        tts_service = get_tts_service()
        logger.info("TTSService initialized")
    return tts_service


def ask_mortis(
    user_msg: Optional[str] = None,
    model_name: Optional[str] = None,
    audio_path: Optional[str] = None
) -> Tuple[str, str, str]:
    """
    Send user message to Gemini API and get Mortis response with gesture.
    
    This function supports both text and voice input through a unified interface.
    It implements the complete voice-to-text-to-Gemini-to-TTS pipeline with
    latency monitoring.
    
    Processing flow:
    1. If audio_path provided, transcribe to text using STT
    2. Connect to robot arm if not already connected
    3. Send text message to Gemini API
    4. Parse structured JSON response
    5. Return message, mood, and gesture for execution
    
    Args:
        user_msg: User's input message text (optional if audio_path provided)
        model_name: Optional Gemini model name (uses default from env if not provided)
        audio_path: Optional path to audio file for voice input
        
    Returns:
        Tuple of (message, mood, gesture) where:
            - message: Text response from Mortis
            - mood: Emotional mood (e.g., "ominous", "playful")
            - gesture: Gesture to execute (e.g., "wave", "idle")
            
    Raises:
        ValueError: If neither user_msg nor audio_path is provided
        
    Note:
        This function maintains backward compatibility with the previous API.
        The gesture is returned but not automatically executed - the caller
        is responsible for executing the gesture via mortis_arm.move_arm().
        
        Latency monitoring logs are generated for voice processing pipeline.
    """
    pipeline_start = time.time()
    
    # Validate input
    if user_msg is None and audio_path is None:
        raise ValueError("Either user_msg or audio_path must be provided")
    
    # Voice input processing
    if audio_path is not None:
        logger.info(f"🎤 Processing voice input from: {audio_path}")
        stt_start = time.time()
        
        try:
            # Get STT service
            stt = _get_stt_service()
            
            # Transcribe audio to text
            user_msg = stt.transcribe(audio_path)
            
            stt_latency = time.time() - stt_start
            logger.info(f"⏱️ STT latency: {stt_latency:.2f}s")
            logger.info(f"📝 Transcribed: '{user_msg[:50]}...'")
            
            if not user_msg or not user_msg.strip():
                logger.warning("⚠️ STT returned empty transcription")
                return "I couldn't hear you... speak again.", "nervous", "idle"
                
        except Exception as e:
            logger.error(f"❌ Voice input processing failed: {e}")
            return "The spirits couldn't understand... try again.", "ominous", "idle"
    
    # Ensure robot is connected
    if not mortis_arm.connected:
        try:
            mortis_arm.connect()
            logger.info("Robot arm connected")
        except Exception as e:
            logger.error(f"Failed to connect to robot arm: {e}")
            # Continue anyway - we can still generate responses
    
    # Get Gemini client
    client = _get_gemini_client()
    
    # Reconfigure model if specified
    if model_name:
        client.configure_model(model_name=model_name)
        logger.info(f"Using Gemini model: {model_name}")
    
    # Send message to Gemini
    logger.info(f"💬 Asking Mortis: {user_msg[:50]}...")
    gemini_start = time.time()
    
    response_json = client.send_message(user_msg)
    
    gemini_latency = time.time() - gemini_start
    logger.info(f"⏱️ Gemini latency: {gemini_latency:.2f}s")
    
    # Parse response using GeminiResponse model
    try:
        response = GeminiResponse.from_json(response_json)
        
        # Extract fields for backward compatibility
        message = response.message
        mood = response.mood.value
        
        # For conversation type, return gesture
        # For manipulation type, return "idle" as gesture (manipulation handled separately)
        if response.gesture:
            gesture = response.gesture.value
        else:
            gesture = "idle"
        
        # Calculate total pipeline latency
        total_latency = time.time() - pipeline_start
        logger.info(f"⏱️ Total pipeline latency: {total_latency:.2f}s")
        logger.info(f"👻 Mortis responds (type: {response.type.value}, mood: {mood}, gesture: {gesture})")
        
        return message, mood, gesture
        
    except (ValueError, KeyError) as e:
        # If parsing fails, return safe defaults
        logger.error(f"Failed to parse Gemini response: {e}")
        logger.error(f"Response JSON: {response_json}")
        
        # Return fallback response
        return "The spirits are confused... try again.", "ominous", "idle"


def ask_mortis_with_voice(
    user_msg: Optional[str] = None,
    model_name: Optional[str] = None,
    audio_path: Optional[str] = None,
    generate_audio: bool = True
) -> Tuple[str, str, str, Optional[str]]:
    """
    Complete voice-to-text-to-Gemini-to-TTS pipeline with audio output.
    
    This is a convenience function that wraps ask_mortis() and adds TTS
    generation for the response. It provides the full multi-modal experience.
    
    Args:
        user_msg: User's input message text (optional if audio_path provided)
        model_name: Optional Gemini model name
        audio_path: Optional path to audio file for voice input
        generate_audio: Whether to generate audio output (default: True)
        
    Returns:
        Tuple of (message, mood, gesture, audio_path) where:
            - message: Text response from Mortis
            - mood: Emotional mood
            - gesture: Gesture to execute
            - audio_path: Path to generated audio file (None if generation fails)
            
    Note:
        This function logs latency for the complete voice processing pipeline
        including STT, Gemini inference, and TTS generation.
    """
    pipeline_start = time.time()
    
    # Get text response from Gemini (handles STT if audio_path provided)
    message, mood, gesture = ask_mortis(
        user_msg=user_msg,
        model_name=model_name,
        audio_path=audio_path
    )
    
    # Generate audio response if requested
    response_audio_path = None
    if generate_audio:
        tts_start = time.time()
        
        try:
            # Get TTS service
            tts = _get_tts_service()
            
            # Generate audio
            response_audio_path = tts.synthesize(message)
            
            tts_latency = time.time() - tts_start
            logger.info(f"⏱️ TTS latency: {tts_latency:.2f}s")
            
            if response_audio_path:
                logger.info(f"🔊 Audio generated: {response_audio_path}")
            else:
                logger.warning("⚠️ TTS returned None")
                
        except Exception as e:
            logger.error(f"❌ TTS generation failed: {e}")
            # Continue without audio - text response is still valid
    
    # Log total pipeline latency including TTS
    total_latency = time.time() - pipeline_start
    logger.info(f"⏱️ Complete voice pipeline latency: {total_latency:.2f}s")
    
    return message, mood, gesture, response_audio_path



if __name__ == "__main__":
    # Configure logging for testing
    logging.basicConfig(level=logging.INFO)
    
    # Test conversational interactions
    print("=== Test 1: Greeting ===")
    message, mood, gesture = ask_mortis("Mortis, someone is entering the lab… act!")
    print(f"Message: {message}")
    print(f"Mood: {mood}")
    print(f"Gesture: {gesture}")
    print()
    
    print("=== Test 2: Introduction ===")
    message, mood, gesture = ask_mortis("Introduce yourself with a sinister bow.")
    print(f"Message: {message}")
    print(f"Mood: {mood}")
    print(f"Gesture: {gesture}")
    print()
    
    print("=== Test 3: Action sequence ===")
    message, mood, gesture = ask_mortis("Grab the cursed vial and then release it.")
    print(f"Message: {message}")
    print(f"Mood: {mood}")
    print(f"Gesture: {gesture}")
    print()
    
    print("=== Test 4: Manipulation command ===")
    message, mood, gesture = ask_mortis("Can you move the skull to the green cup?")
    print(f"Message: {message}")
    print(f"Mood: {mood}")
    print(f"Gesture: {gesture}")
    print()