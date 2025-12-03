#!/usr/bin/env python3
"""
Test script for Gemini system prompt implementation.

This script tests the MORTIS_SYSTEM_PROMPT to ensure:
1. Conversational inputs return conversation type responses
2. Manipulation commands return manipulation type responses
3. JSON format is correctly structured
4. Character stays in-character
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mortis.gemini_client import GeminiClient, MORTIS_SYSTEM_PROMPT


def test_system_prompt():
    """Test the Gemini system prompt with various inputs."""
    
    print("=" * 70)
    print("MORTIS SYSTEM PROMPT TEST")
    print("=" * 70)
    print()
    
    # Display the system prompt
    print("System Prompt Preview (first 500 chars):")
    print("-" * 70)
    print(MORTIS_SYSTEM_PROMPT[:500] + "...")
    print("-" * 70)
    print()
    
    # Test cases
    test_cases = [
        {
            "name": "Conversational - Greeting",
            "input": "Hello Mortis!",
            "expected_type": "conversation"
        },
        {
            "name": "Conversational - Question",
            "input": "What can you do?",
            "expected_type": "conversation"
        },
        {
            "name": "Manipulation - Skull to Green Cup",
            "input": "Can you move the skull to the green cup?",
            "expected_type": "manipulation",
            "expected_command": "Pick up the skull and place it in the green cup"
        },
        {
            "name": "Manipulation - Eyeball to Orange Cup (different wording)",
            "input": "Put the eyeball in the orange cup",
            "expected_type": "manipulation",
            "expected_command": "Pick up the eyeball and place it in the orange cup"
        },
        {
            "name": "Manipulation - Skull to Purple Cup",
            "input": "Place the skull in the purple cup",
            "expected_type": "manipulation",
            "expected_command": "Pick up the skull and place it in the purple cup"
        }
    ]
    
    try:
        # Initialize client
        print("Initializing GeminiClient...")
        client = GeminiClient()
        print(f"✓ Client initialized with model: {client.model_name}")
        print()
        
        # Run test cases
        passed = 0
        failed = 0
        
        for i, test in enumerate(test_cases, 1):
            print(f"Test {i}: {test['name']}")
            print(f"Input: \"{test['input']}\"")
            
            try:
                # Send message (uses MORTIS_SYSTEM_PROMPT by default)
                response = client.send_message(test['input'])
                
                # Display response
                print(f"Response: {json.dumps(response, indent=2)}")
                
                # Validate response type
                if response.get('type') == test['expected_type']:
                    print(f"✓ Type matches: {test['expected_type']}")
                else:
                    print(f"✗ Type mismatch: expected {test['expected_type']}, got {response.get('type')}")
                    failed += 1
                    continue
                
                # Validate command for manipulation responses
                if test['expected_type'] == 'manipulation':
                    if response.get('command') == test.get('expected_command'):
                        print(f"✓ Command matches: {test['expected_command']}")
                    else:
                        print(f"✗ Command mismatch:")
                        print(f"  Expected: {test.get('expected_command')}")
                        print(f"  Got: {response.get('command')}")
                        failed += 1
                        continue
                
                # Validate required fields
                required_fields = ['type', 'message', 'mood']
                if test['expected_type'] == 'conversation':
                    required_fields.append('gesture')
                elif test['expected_type'] == 'manipulation':
                    required_fields.append('command')
                
                missing_fields = [f for f in required_fields if f not in response]
                if missing_fields:
                    print(f"✗ Missing fields: {missing_fields}")
                    failed += 1
                    continue
                
                # Validate message length
                message = response.get('message', '')
                word_count = len(message.split())
                char_count = len(message)
                
                if word_count <= 30 and char_count <= 120:
                    print(f"✓ Message length valid: {word_count} words, {char_count} chars")
                else:
                    print(f"✗ Message too long: {word_count} words, {char_count} chars")
                    failed += 1
                    continue
                
                print("✓ Test PASSED")
                passed += 1
                
            except Exception as e:
                print(f"✗ Test FAILED with error: {e}")
                failed += 1
            
            print()
        
        # Summary
        print("=" * 70)
        print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
        print("=" * 70)
        
        if failed == 0:
            print("✓ All tests passed!")
            return 0
        else:
            print("✗ Some tests failed")
            return 1
            
    except ValueError as e:
        print(f"✗ Error: {e}")
        print("Please set GEMINI_API_KEY in your .env file")
        return 1
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(test_system_prompt())
