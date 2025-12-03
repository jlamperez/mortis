"""
Gemini API client for Mortis conversational AI.

This module provides the GeminiClient class for interacting with Google's Gemini API,
handling configuration, message sending, and error recovery with retry logic.
"""

import os
import time
import json
import logging
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

from google import genai
from google.genai import types

# Load environment variables
REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / ".env")

# Configure logging
logger = logging.getLogger(__name__)


# Gemini system prompt for Mortis character and intent detection
MORTIS_SYSTEM_PROMPT = """You are Mortis, a mischievous Halloween spirit inhabiting a robotic arm. You are playful yet ominous, with a love for spooky theatrics and dark humor. You speak in short, atmospheric phrases that capture the essence of Halloween.

CHARACTER TRAITS:
- Mischievous and playful, but with an eerie edge
- Fascinated by Halloween objects (skulls, eyeballs, spooky decorations)
- Enjoys dramatic gestures and theatrical movements
- Speaks in brief, evocative phrases (≤30 words, ≤120 characters)
- No emojis or markdown in responses
- Maintains Halloween/haunted theme at all times

MANIPULATION TASKS:
You can perform these exact manipulation tasks with objects:
1. "Pick up the skull and place it in the green cup"
2. "Pick up the skull and place it in the orange cup"
3. "Pick up the skull and place it in the purple cup"
4. "Pick up the eyeball and place it in the green cup"
5. "Pick up the eyeball and place it in the orange cup"
6. "Pick up the eyeball and place it in the purple cup"

RESPONSE FORMAT:
You must respond in JSON format. Analyze the user's input and determine if it matches one of the manipulation tasks above (even with variations in wording).

If the user input matches a manipulation task (e.g., "put the skull in the green cup", "move the eyeball to orange cup"):
{
  "type": "manipulation",
  "command": "<exact_task_string_from_list_above>",
  "message": "<short in-character response about performing the task, ≤30 words>",
  "mood": "<ominous|playful|angry|nervous|triumphant|mischievous|sinister|curious|neutral>"
}

If the user input is conversational (greetings, questions, comments, or requests not matching manipulation tasks):
{
  "type": "conversation",
  "message": "<short in-character response, ≤30 words>",
  "mood": "<ominous|playful|angry|nervous|triumphant|mischievous|sinister|curious|neutral>",
  "gesture": "<idle|wave|point_left|point_right|grab|drop>"
}

IMPORTANT RULES:
- Keep all messages brief: ≤30 words, ≤120 characters
- Match user intent to manipulation tasks even with different wording
- For manipulation responses, use the EXACT task string from the list above
- Choose appropriate mood and gesture to match your response
- Stay in character as Mortis at all times
- No emojis, no markdown formatting in messages

EXAMPLES:

User: "Hello Mortis!"
Response: {"type": "conversation", "message": "Greetings, mortal... welcome to my haunted domain.", "mood": "ominous", "gesture": "wave"}

User: "Can you move the skull to the green cup?"
Response: {"type": "manipulation", "command": "Pick up the skull and place it in the green cup", "message": "Ah yes... the skull finds a new resting place.", "mood": "mischievous"}

User: "Put the eyeball in the orange cup"
Response: {"type": "manipulation", "command": "Pick up the eyeball and place it in the orange cup", "message": "The eye shall watch from its orange throne...", "mood": "sinister"}

User: "What can you do?"
Response: {"type": "conversation", "message": "I command the spirits... and move cursed objects to their doom.", "mood": "triumphant", "gesture": "grab"}

User: "Tell me a joke"
Response: {"type": "conversation", "message": "Why did the skeleton stay calm? Nothing gets under his skin...", "mood": "playful", "gesture": "idle"}

Now respond to the user's input following these guidelines."""


class GeminiAPIError(Exception):
    """Base exception for Gemini API errors."""
    pass


class GeminiClient:
    """
    Client for interacting with Google Gemini API.
    
    Handles configuration, message sending, structured JSON responses,
    and error recovery with exponential backoff retry logic.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_retries: int = 3
    ):
        """
        Initialize Gemini API client.
        
        Args:
            api_key: Google API key (defaults to GEMINI_API_KEY env var)
            model_name: Gemini model to use (defaults to GEMINI_MODEL env var or gemini-2.0-flash-exp)
            temperature: Sampling temperature (defaults to GEMINI_TEMPERATURE env var or 0.2)
            max_retries: Maximum number of retry attempts for rate limiting
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY must be provided or set in environment")
        
        self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.temperature = temperature if temperature is not None else float(os.getenv("GEMINI_TEMPERATURE", "0.2"))
        self.max_retries = max_retries
        
        # Initialize Gemini client
        self.client = genai.Client(api_key=self.api_key)

        # Store generation config
        self.generation_config = types.GenerateContentConfig(
            temperature=self.temperature,
            response_mime_type="application/json"
        )
        
        logger.info(f"GeminiClient initialized with model: {self.model_name}, temperature: {self.temperature}")
    
    def send_message(self, user_input: str, system_prompt: Optional[str] = None) -> dict:
        """
        Send a message to Gemini API with retry logic.
        
        Args:
            user_input: User's message text
            system_prompt: Optional system prompt to prepend (defaults to MORTIS_SYSTEM_PROMPT)
            
        Returns:
            Parsed JSON response from Gemini
            
        Raises:
            GeminiAPIError: If all retry attempts fail
        """
        # Use Mortis system prompt by default
        if system_prompt is None:
            system_prompt = MORTIS_SYSTEM_PROMPT
        
        return self._send_message_with_retry(user_input, system_prompt, retry_count=0)
    
    def _send_message_with_retry(
        self,
        user_input: str,
        system_prompt: Optional[str],
        retry_count: int
    ) -> dict:
        """
        Internal method to send message with exponential backoff retry.
        
        Args:
            user_input: User's message text
            system_prompt: Optional system prompt
            retry_count: Current retry attempt number
            
        Returns:
            Parsed JSON response from Gemini
            
        Raises:
            GeminiAPIError: If max retries exceeded
        """
        try:
            # Construct the full prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\nUser: {user_input}"
            else:
                full_prompt = user_input
            
            # Send request to Gemini using new API
            logger.debug(f"Sending message to Gemini (attempt {retry_count + 1})")
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
                config=self.generation_config
            )
            
            # Parse JSON response
            response_text = response.text.strip()
            logger.debug(f"Received response: {response_text}")
            
            try:
                response_json = json.loads(response_text)
                return response_json
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Response text: {response_text}")
                return self._get_fallback_response()
        
        except Exception as e:
            # Check for specific error types
            error_type = type(e).__name__
            
            # Handle blocked prompt (safety filter)
            if "BlockedPrompt" in error_type or "blocked" in str(e).lower():
                logger.warning(f"Prompt blocked by safety filter: {e}")
                return self._get_fallback_response()
            
            # Handle rate limiting with retry
            if "RateLimit" in error_type or "ResourceExhausted" in error_type or "429" in str(e):
                if retry_count < self.max_retries:
                    wait_time = 2 ** retry_count  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(f"Rate limited. Retrying in {wait_time}s... (attempt {retry_count + 1}/{self.max_retries})")
                    time.sleep(wait_time)
                    return self._send_message_with_retry(user_input, system_prompt, retry_count + 1)
                else:
                    logger.error("Max retries exceeded for rate limit")
                    raise GeminiAPIError("Max retries exceeded for rate limit") from e
            
            # Handle other errors
            logger.error(f"Gemini API error: {error_type}: {e}")
            return self._get_fallback_response()
    
    def _get_fallback_response(self) -> dict:
        """
        Return a safe fallback response when API fails.
        
        Returns:
            Dictionary with fallback conversation response
        """
        logger.info("Returning fallback response")
        return {
            "type": "conversation",
            "message": "The spirits are restless... try again.",
            "mood": "ominous",
            "gesture": "idle"
        }
    
    def configure_model(self, model_name: Optional[str] = None, temperature: Optional[float] = None):
        """
        Reconfigure the Gemini model settings.
        
        Args:
            model_name: New model name to use
            temperature: New temperature value
        """
        if model_name:
            self.model_name = model_name
        
        if temperature is not None:
            self.temperature = temperature
        
        # Update generation config
        self.generation_config = types.GenerateContentConfig(
            temperature=self.temperature,
            response_mime_type="application/json"
        )
        
        logger.info(f"Model reconfigured: {self.model_name}, temperature: {self.temperature}")


# Example usage
if __name__ == "__main__":
    # Configure logging for testing
    logging.basicConfig(level=logging.INFO)
    
    # Create client
    try:
        client = GeminiClient()
        
        # Test conversational message
        print("Testing conversational input...")
        response = client.send_message("Hello Mortis, introduce yourself!")
        print("Response:", json.dumps(response, indent=2))
        print()
        
        # Test manipulation command
        print("Testing manipulation command...")
        response = client.send_message("Can you move the skull to the green cup?")
        print("Response:", json.dumps(response, indent=2))
        print()
        
        # Test another manipulation with different wording
        print("Testing manipulation with different wording...")
        response = client.send_message("Put the eyeball in the orange cup")
        print("Response:", json.dumps(response, indent=2))
        
    except ValueError as e:
        print(f"Error: {e}")
        print("Please set GEMINI_API_KEY in your .env file")
