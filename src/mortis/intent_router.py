"""
Intent router for parsing Gemini responses and routing to appropriate execution paths.

This module handles the routing logic between conversational gestures and manipulation
tasks based on Gemini API responses. It validates commands against the trained task set
and provides structured intent representation.
"""

import json
import logging
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from .models import GeminiResponse, ResponseType, Gesture

logger = logging.getLogger(__name__)


@dataclass
class Intent:
    """
    Structured representation of user intent parsed from Gemini response.
    
    Attributes:
        type: The type of intent (conversation or manipulation)
        message: The text message to display/speak to the user
        mood: The emotional mood of the response
        gesture: Optional gesture to execute (for conversation type)
        command: Optional manipulation command (for manipulation type)
        is_valid: Whether the intent is valid and can be executed
        validation_error: Optional error message if validation failed
    """
    type: ResponseType
    message: str
    mood: str
    gesture: Optional[str] = None
    command: Optional[str] = None
    is_valid: bool = True
    validation_error: Optional[str] = None
    
    @classmethod
    def from_gemini_response(cls, response: GeminiResponse, is_valid: bool = True, 
                            validation_error: Optional[str] = None) -> "Intent":
        """
        Create an Intent from a GeminiResponse.
        
        Args:
            response: The parsed GeminiResponse object
            is_valid: Whether the intent passed validation
            validation_error: Optional error message if validation failed
            
        Returns:
            Intent object with all fields populated
        """
        return cls(
            type=response.type,
            message=response.message,
            mood=response.mood.value,
            gesture=response.gesture.value if response.gesture else None,
            command=response.command,
            is_valid=is_valid,
            validation_error=validation_error
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the intent to a dictionary.
        
        Returns:
            Dictionary representation of the intent
        """
        result = {
            "type": self.type.value,
            "message": self.message,
            "mood": self.mood,
            "is_valid": self.is_valid,
        }
        
        if self.gesture is not None:
            result["gesture"] = self.gesture
        
        if self.command is not None:
            result["command"] = self.command
        
        if self.validation_error is not None:
            result["validation_error"] = self.validation_error
        
        return result


class IntentRouter:
    """
    Routes user intents to appropriate execution paths based on Gemini responses.
    
    The IntentRouter parses Gemini API responses, validates manipulation commands
    against the trained task set, and creates structured Intent objects for execution.
    """
    
    # Valid manipulation task commands that SmolVLA is trained on
    VALID_COMMANDS = [
        "Pick up the skull and place it in the green cup",
        "Pick up the skull and place it in the orange cup",
        "Pick up the skull and place it in the purple cup",
        "Pick up the eyeball and place it in the green cup",
        "Pick up the eyeball and place it in the orange cup",
        "Pick up the eyeball and place it in the purple cup",
    ]
    
    def __init__(self, valid_commands: Optional[List[str]] = None):
        """
        Initialize the IntentRouter.
        
        Args:
            valid_commands: Optional list of valid manipulation commands.
                          If not provided, uses the default VALID_COMMANDS.
        """
        self.valid_commands = valid_commands if valid_commands is not None else self.VALID_COMMANDS
        logger.info(f"IntentRouter initialized with {len(self.valid_commands)} valid commands")
    
    def parse_gemini_response(self, response_data: Dict[str, Any]) -> Intent:
        """
        Parse a Gemini API response and create an Intent.
        
        This method:
        1. Parses the JSON response into a GeminiResponse object
        2. Validates manipulation commands against the trained task set
        3. Creates an Intent object with validation results
        
        Args:
            response_data: Dictionary containing the JSON response from Gemini
            
        Returns:
            Intent object with parsed data and validation status
            
        Raises:
            ValueError: If the response structure is invalid
            json.JSONDecodeError: If response_data is a string and not valid JSON
        """
        try:
            # Parse the Gemini response
            gemini_response = GeminiResponse.from_json(response_data)
            
            # Validate the response structure
            try:
                gemini_response.validate()
            except ValueError as e:
                logger.warning(f"Response validation warning: {e}")
                # Continue anyway - validation warnings are not fatal
            
            # For manipulation intents, validate the command
            if gemini_response.type == ResponseType.MANIPULATION:
                is_valid = self.validate_command(gemini_response.command)
                
                if not is_valid:
                    logger.warning(
                        f"Invalid manipulation command: '{gemini_response.command}'. "
                        f"Not in trained task set."
                    )
                    validation_error = (
                        f"Command '{gemini_response.command}' is not in the trained task set. "
                        f"Valid commands are: {', '.join(self.valid_commands)}"
                    )
                    return Intent.from_gemini_response(
                        gemini_response,
                        is_valid=False,
                        validation_error=validation_error
                    )
                else:
                    logger.info(f"Valid manipulation command: '{gemini_response.command}'")
            
            # For conversation intents, always valid (gestures are predefined)
            else:
                logger.info(f"Conversation intent with gesture: {gemini_response.gesture.value}")
            
            # Create and return valid intent
            return Intent.from_gemini_response(gemini_response, is_valid=True)
            
        except (ValueError, KeyError) as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            raise ValueError(f"Invalid Gemini response structure: {e}")
    
    def parse_gemini_response_string(self, response_string: str) -> Intent:
        """
        Parse a Gemini API response from a JSON string.
        
        Args:
            response_string: JSON string containing the Gemini response
            
        Returns:
            Intent object with parsed data and validation status
            
        Raises:
            json.JSONDecodeError: If the string is not valid JSON
            ValueError: If the response structure is invalid
        """
        try:
            response_data = json.loads(response_string)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON string: {e}")
            raise
        
        return self.parse_gemini_response(response_data)
    
    def validate_command(self, command: str) -> bool:
        """
        Validate that a manipulation command is in the trained task set.
        
        This performs exact string matching against the list of valid commands.
        Commands must match exactly (case-sensitive) to be considered valid.
        
        Args:
            command: The manipulation command string to validate
            
        Returns:
            True if the command is valid, False otherwise
        """
        if not command or not isinstance(command, str):
            logger.warning(f"Invalid command type: {type(command)}")
            return False
        
        # Exact match required
        is_valid = command in self.valid_commands
        
        if not is_valid:
            # Log for debugging - maybe it's close to a valid command
            logger.debug(f"Command '{command}' not found in valid commands")
            logger.debug(f"Valid commands: {self.valid_commands}")
        
        return is_valid
    
    def get_valid_commands(self) -> List[str]:
        """
        Get the list of valid manipulation commands.
        
        Returns:
            List of valid command strings
        """
        return self.valid_commands.copy()
    
    def add_valid_command(self, command: str) -> None:
        """
        Add a new valid manipulation command to the router.
        
        This is useful when training new tasks and expanding the command set.
        
        Args:
            command: The new command string to add
        """
        if command not in self.valid_commands:
            self.valid_commands.append(command)
            logger.info(f"Added new valid command: '{command}'")
        else:
            logger.warning(f"Command already exists: '{command}'")
    
    def remove_valid_command(self, command: str) -> bool:
        """
        Remove a valid manipulation command from the router.
        
        Args:
            command: The command string to remove
            
        Returns:
            True if the command was removed, False if it wasn't found
        """
        if command in self.valid_commands:
            self.valid_commands.remove(command)
            logger.info(f"Removed valid command: '{command}'")
            return True
        else:
            logger.warning(f"Command not found: '{command}'")
            return False
    
    def route_intent(self, intent: Intent) -> str:
        """
        Determine the execution path for an intent.
        
        Args:
            intent: The Intent object to route
            
        Returns:
            String indicating the execution path: "gesture", "manipulation", or "invalid"
        """
        if not intent.is_valid:
            logger.warning(f"Invalid intent: {intent.validation_error}")
            return "invalid"
        
        if intent.type == ResponseType.CONVERSATION:
            logger.info(f"Routing to gesture execution: {intent.gesture}")
            return "gesture"
        elif intent.type == ResponseType.MANIPULATION:
            logger.info(f"Routing to manipulation execution: {intent.command}")
            return "manipulation"
        else:
            logger.error(f"Unknown intent type: {intent.type}")
            return "invalid"
