"""
LLM integration for Mortis conversational AI.

This module provides the ask_mortis() function that integrates with the Gemini API
to generate character-driven responses and coordinate gesture execution.
"""

import logging
from typing import Tuple

from .robot import MortisArm
from .gemini_client import GeminiClient
from .models import GeminiResponse

# Configure logging
logger = logging.getLogger(__name__)

# Global instances
mortis_arm = MortisArm()
gemini_client = None  # Lazy initialization


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


def ask_mortis(user_msg: str, model_name: str = None) -> Tuple[str, str, str]:
    """
    Send user message to Gemini API and get Mortis response with gesture.
    
    This function:
    1. Connects to the robot arm if not already connected
    2. Sends the user message to Gemini API
    3. Parses the structured JSON response
    4. Returns message, mood, and gesture for execution
    
    Args:
        user_msg: User's input message
        model_name: Optional Gemini model name (uses default from env if not provided)
        
    Returns:
        Tuple of (message, mood, gesture) where:
            - message: Text response from Mortis
            - mood: Emotional mood (e.g., "ominous", "playful")
            - gesture: Gesture to execute (e.g., "wave", "idle")
            
    Note:
        This function maintains backward compatibility with the previous API.
        The gesture is returned but not automatically executed - the caller
        is responsible for executing the gesture via mortis_arm.move_arm().
    """
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
    logger.info(f"Asking Mortis: {user_msg[:50]}...")
    response_json = client.send_message(user_msg)
    
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
        
        logger.info(f"Mortis responds (type: {response.type.value}, mood: {mood}, gesture: {gesture})")
        
        return message, mood, gesture
        
    except (ValueError, KeyError) as e:
        # If parsing fails, return safe defaults
        logger.error(f"Failed to parse Gemini response: {e}")
        logger.error(f"Response JSON: {response_json}")
        
        # Return fallback response
        return "The spirits are confused... try again.", "ominous", "idle"



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