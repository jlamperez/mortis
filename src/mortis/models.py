"""
Data models for Gemini API responses and intent routing.

This module defines the structured data types used throughout the Mortis system
for parsing Gemini responses, routing intents, and managing execution tasks.
"""

import json
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any


class ResponseType(Enum):
    """Type of response from Gemini API."""
    CONVERSATION = "conversation"
    MANIPULATION = "manipulation"


class Mood(Enum):
    """Emotional mood for Mortis character responses."""
    OMINOUS = "ominous"
    PLAYFUL = "playful"
    ANGRY = "angry"
    NERVOUS = "nervous"
    TRIUMPHANT = "triumphant"
    MISCHIEVOUS = "mischievous"
    SINISTER = "sinister"
    CURIOUS = "curious"
    NEUTRAL = "neutral"


class Gesture(Enum):
    """Available gesture actions for the SO101 robotic arm."""
    IDLE = "idle"
    WAVE = "wave"
    POINT_LEFT = "point_left"
    POINT_RIGHT = "point_right"
    GRAB = "grab"
    DROP = "drop"


@dataclass
class GeminiResponse:
    """
    Structured response from Gemini API.
    
    Attributes:
        type: Whether this is a conversation or manipulation response
        message: The text message to display/speak to the user
        mood: The emotional mood of the response
        gesture: Optional gesture to execute (for conversation type)
        command: Optional manipulation command (for manipulation type)
    """
    type: ResponseType
    message: str
    mood: Mood
    gesture: Optional[Gesture] = None
    command: Optional[str] = None
    
    @classmethod
    def from_json(cls, json_data: Dict[str, Any]) -> "GeminiResponse":
        """
        Parse a GeminiResponse from JSON data returned by Gemini API.
        
        Args:
            json_data: Dictionary containing the JSON response from Gemini
            
        Returns:
            GeminiResponse object with validated fields
            
        Raises:
            ValueError: If required fields are missing or invalid
            KeyError: If JSON structure is malformed
        """
        # Validate required fields
        if "type" not in json_data:
            raise ValueError("Missing required field: 'type'")
        if "message" not in json_data:
            raise ValueError("Missing required field: 'message'")
        if "mood" not in json_data:
            raise ValueError("Missing required field: 'mood'")
        
        # Parse response type
        try:
            response_type = ResponseType(json_data["type"])
        except ValueError:
            raise ValueError(f"Invalid response type: {json_data['type']}. Must be 'conversation' or 'manipulation'")
        
        # Parse mood
        try:
            mood = Mood(json_data["mood"])
        except ValueError:
            raise ValueError(f"Invalid mood: {json_data['mood']}. Must be one of: {[m.value for m in Mood]}")
        
        # Parse optional fields based on response type
        gesture = None
        command = None
        
        if response_type == ResponseType.CONVERSATION:
            # Conversation responses should have a gesture
            if "gesture" in json_data:
                try:
                    gesture = Gesture(json_data["gesture"])
                except ValueError:
                    raise ValueError(f"Invalid gesture: {json_data['gesture']}. Must be one of: {[g.value for g in Gesture]}")
            else:
                # Default to idle if no gesture specified
                gesture = Gesture.IDLE
        
        elif response_type == ResponseType.MANIPULATION:
            # Manipulation responses must have a command
            if "command" not in json_data:
                raise ValueError("Manipulation responses must include 'command' field")
            command = json_data["command"]
            if not isinstance(command, str) or not command.strip():
                raise ValueError("Command must be a non-empty string")
        
        # Validate message
        message = json_data["message"]
        if not isinstance(message, str) or not message.strip():
            raise ValueError("Message must be a non-empty string")
        
        return cls(
            type=response_type,
            message=message,
            mood=mood,
            gesture=gesture,
            command=command
        )
    
    @classmethod
    def from_json_string(cls, json_string: str) -> "GeminiResponse":
        """
        Parse a GeminiResponse from a JSON string.
        
        Args:
            json_string: JSON string containing the Gemini response
            
        Returns:
            GeminiResponse object with validated fields
            
        Raises:
            json.JSONDecodeError: If the string is not valid JSON
            ValueError: If required fields are missing or invalid
        """
        try:
            json_data = json.loads(json_string)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON string: {e.msg}", e.doc, e.pos)
        
        return cls.from_json(json_data)
    
    def validate(self) -> bool:
        """
        Validate the response structure and content.
        
        Returns:
            True if the response is valid
            
        Raises:
            ValueError: If validation fails
        """
        # Check message length constraints (per product requirements)
        if len(self.message) > 120:
            raise ValueError(f"Message exceeds 120 characters: {len(self.message)} chars")
        
        word_count = len(self.message.split())
        if word_count > 30:
            raise ValueError(f"Message exceeds 30 words: {word_count} words")
        
        # Validate type-specific requirements
        if self.type == ResponseType.CONVERSATION:
            if self.gesture is None:
                raise ValueError("Conversation responses must have a gesture")
            if self.command is not None:
                raise ValueError("Conversation responses should not have a command")
        
        elif self.type == ResponseType.MANIPULATION:
            if self.command is None or not self.command.strip():
                raise ValueError("Manipulation responses must have a non-empty command")
            if self.gesture is not None:
                raise ValueError("Manipulation responses should not have a gesture")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the response to a dictionary.
        
        Returns:
            Dictionary representation of the response
        """
        result = {
            "type": self.type.value,
            "message": self.message,
            "mood": self.mood.value,
        }
        
        if self.gesture is not None:
            result["gesture"] = self.gesture.value
        
        if self.command is not None:
            result["command"] = self.command
        
        return result
    
    def to_json(self) -> str:
        """
        Convert the response to a JSON string.
        
        Returns:
            JSON string representation of the response
        """
        return json.dumps(self.to_dict(), indent=2)
