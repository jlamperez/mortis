#!/usr/bin/env python3
"""
Test script for IntentRouter implementation.

This script tests the IntentRouter to ensure:
1. Gemini response parsing works correctly
2. Command validation works for valid and invalid commands
3. Intent routing logic is correct
4. Error handling is robust
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mortis.intent_router import IntentRouter, Intent
from mortis.models import ResponseType, Mood, Gesture


def setup_logging():
    """Set up logging for test output."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    return logging.getLogger(__name__)


def test_intent_router_initialization():
    """Test IntentRouter initialization."""
    print("\n" + "=" * 70)
    print("TEST 1: IntentRouter Initialization")
    print("=" * 70)
    
    try:
        # Test default initialization
        print("\nInitializing with defaults...")
        router = IntentRouter()
        print(f"✓ Valid commands count: {len(router.get_valid_commands())}")
        print(f"✓ Valid commands: {router.get_valid_commands()}")
        
        # Test custom initialization
        print("\nInitializing with custom commands...")
        custom_commands = ["Test command 1", "Test command 2"]
        router_custom = IntentRouter(valid_commands=custom_commands)
        print(f"✓ Custom commands count: {len(router_custom.get_valid_commands())}")
        print(f"✓ Custom commands: {router_custom.get_valid_commands()}")
        
        print("\n✓ IntentRouter initialization test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ IntentRouter initialization test FAILED: {e}")
        return False


def test_parse_conversation_response():
    """Test parsing of conversation responses."""
    print("\n" + "=" * 70)
    print("TEST 2: Parse Conversation Response")
    print("=" * 70)
    
    try:
        router = IntentRouter()
        
        # Test valid conversation response
        print("\nTesting valid conversation response...")
        response_data = {
            "type": "conversation",
            "message": "Beware, mortal...",
            "mood": "ominous",
            "gesture": "wave"
        }
        
        intent = router.parse_gemini_response(response_data)
        
        print(f"✓ Type: {intent.type.value}")
        print(f"✓ Message: {intent.message}")
        print(f"✓ Mood: {intent.mood}")
        print(f"✓ Gesture: {intent.gesture}")
        print(f"✓ Is valid: {intent.is_valid}")
        
        # Verify fields
        assert intent.type == ResponseType.CONVERSATION
        assert intent.message == "Beware, mortal..."
        assert intent.mood == "ominous"
        assert intent.gesture == "wave"
        assert intent.is_valid == True
        assert intent.command is None
        
        print("\n✓ Parse conversation response test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Parse conversation response test FAILED: {e}")
        return False


def test_parse_manipulation_response_valid():
    """Test parsing of valid manipulation responses."""
    print("\n" + "=" * 70)
    print("TEST 3: Parse Valid Manipulation Response")
    print("=" * 70)
    
    try:
        router = IntentRouter()
        
        # Test valid manipulation response
        print("\nTesting valid manipulation response...")
        response_data = {
            "type": "manipulation",
            "message": "As you wish...",
            "mood": "sinister",
            "command": "Pick up the skull and place it in the green cup"
        }
        
        intent = router.parse_gemini_response(response_data)
        
        print(f"✓ Type: {intent.type.value}")
        print(f"✓ Message: {intent.message}")
        print(f"✓ Mood: {intent.mood}")
        print(f"✓ Command: {intent.command}")
        print(f"✓ Is valid: {intent.is_valid}")
        
        # Verify fields
        assert intent.type == ResponseType.MANIPULATION
        assert intent.message == "As you wish..."
        assert intent.mood == "sinister"
        assert intent.command == "Pick up the skull and place it in the green cup"
        assert intent.is_valid == True
        assert intent.gesture is None
        
        print("\n✓ Parse valid manipulation response test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Parse valid manipulation response test FAILED: {e}")
        return False


def test_parse_manipulation_response_invalid():
    """Test parsing of invalid manipulation responses."""
    print("\n" + "=" * 70)
    print("TEST 4: Parse Invalid Manipulation Response")
    print("=" * 70)
    
    try:
        router = IntentRouter()
        
        # Test invalid manipulation response (command not in trained set)
        print("\nTesting invalid manipulation response...")
        response_data = {
            "type": "manipulation",
            "message": "I cannot do that...",
            "mood": "nervous",
            "command": "Pick up the pumpkin and throw it"
        }
        
        intent = router.parse_gemini_response(response_data)
        
        print(f"✓ Type: {intent.type.value}")
        print(f"✓ Message: {intent.message}")
        print(f"✓ Mood: {intent.mood}")
        print(f"✓ Command: {intent.command}")
        print(f"✓ Is valid: {intent.is_valid}")
        print(f"✓ Validation error: {intent.validation_error}")
        
        # Verify fields
        assert intent.type == ResponseType.MANIPULATION
        assert intent.command == "Pick up the pumpkin and throw it"
        assert intent.is_valid == False
        assert intent.validation_error is not None
        
        print("\n✓ Parse invalid manipulation response test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Parse invalid manipulation response test FAILED: {e}")
        return False


def test_command_validation():
    """Test command validation logic."""
    print("\n" + "=" * 70)
    print("TEST 5: Command Validation")
    print("=" * 70)
    
    try:
        router = IntentRouter()
        
        # Test valid commands
        print("\nTesting valid commands:")
        valid_commands = [
            "Pick up the skull and place it in the green cup",
            "Pick up the eyeball and place it in the orange cup",
        ]
        
        for cmd in valid_commands:
            is_valid = router.validate_command(cmd)
            status = "✓" if is_valid else "✗"
            print(f"  {status} '{cmd}': {is_valid}")
            assert is_valid == True
        
        # Test invalid commands
        print("\nTesting invalid commands:")
        invalid_commands = [
            "Pick up the pumpkin",
            "Wave at the user",
            "",
            None,
            "pick up the skull and place it in the green cup",  # Case sensitive
        ]
        
        for cmd in invalid_commands:
            is_valid = router.validate_command(cmd)
            status = "✓" if not is_valid else "✗"
            print(f"  {status} '{cmd}': {is_valid}")
            assert is_valid == False
        
        print("\n✓ Command validation test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Command validation test FAILED: {e}")
        return False


def test_intent_routing():
    """Test intent routing logic."""
    print("\n" + "=" * 70)
    print("TEST 6: Intent Routing")
    print("=" * 70)
    
    try:
        router = IntentRouter()
        
        # Test conversation intent routing
        print("\nTesting conversation intent routing...")
        conv_data = {
            "type": "conversation",
            "message": "Hello there!",
            "mood": "playful",
            "gesture": "wave"
        }
        conv_intent = router.parse_gemini_response(conv_data)
        route = router.route_intent(conv_intent)
        print(f"✓ Conversation routed to: {route}")
        assert route == "gesture"
        
        # Test manipulation intent routing
        print("\nTesting manipulation intent routing...")
        manip_data = {
            "type": "manipulation",
            "message": "Doing it now...",
            "mood": "mischievous",
            "command": "Pick up the skull and place it in the green cup"
        }
        manip_intent = router.parse_gemini_response(manip_data)
        route = router.route_intent(manip_intent)
        print(f"✓ Manipulation routed to: {route}")
        assert route == "manipulation"
        
        # Test invalid intent routing
        print("\nTesting invalid intent routing...")
        invalid_data = {
            "type": "manipulation",
            "message": "Cannot do that",
            "mood": "nervous",
            "command": "Invalid command"
        }
        invalid_intent = router.parse_gemini_response(invalid_data)
        route = router.route_intent(invalid_intent)
        print(f"✓ Invalid intent routed to: {route}")
        assert route == "invalid"
        
        print("\n✓ Intent routing test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Intent routing test FAILED: {e}")
        return False


def test_command_management():
    """Test adding and removing valid commands."""
    print("\n" + "=" * 70)
    print("TEST 7: Command Management")
    print("=" * 70)
    
    try:
        router = IntentRouter()
        
        initial_count = len(router.get_valid_commands())
        print(f"\nInitial command count: {initial_count}")
        
        # Test adding a command
        print("\nAdding new command...")
        new_command = "Pick up the spider and place it in the cauldron"
        router.add_valid_command(new_command)
        
        new_count = len(router.get_valid_commands())
        print(f"✓ New command count: {new_count}")
        assert new_count == initial_count + 1
        assert router.validate_command(new_command) == True
        
        # Test adding duplicate command
        print("\nAdding duplicate command...")
        router.add_valid_command(new_command)
        assert len(router.get_valid_commands()) == new_count  # Should not increase
        
        # Test removing a command
        print("\nRemoving command...")
        removed = router.remove_valid_command(new_command)
        print(f"✓ Command removed: {removed}")
        assert removed == True
        assert len(router.get_valid_commands()) == initial_count
        assert router.validate_command(new_command) == False
        
        # Test removing non-existent command
        print("\nRemoving non-existent command...")
        removed = router.remove_valid_command("Non-existent command")
        print(f"✓ Command removed: {removed}")
        assert removed == False
        
        print("\n✓ Command management test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Command management test FAILED: {e}")
        return False


def test_error_handling():
    """Test error handling for malformed responses."""
    print("\n" + "=" * 70)
    print("TEST 8: Error Handling")
    print("=" * 70)
    
    try:
        router = IntentRouter()
        
        # Test missing required fields
        print("\nTesting missing 'type' field...")
        try:
            router.parse_gemini_response({"message": "test", "mood": "neutral"})
            print("✗ Should have raised ValueError")
            return False
        except ValueError as e:
            print(f"✓ Correctly raised ValueError: {e}")
        
        # Test missing message field
        print("\nTesting missing 'message' field...")
        try:
            router.parse_gemini_response({"type": "conversation", "mood": "neutral"})
            print("✗ Should have raised ValueError")
            return False
        except ValueError as e:
            print(f"✓ Correctly raised ValueError: {e}")
        
        # Test invalid type value
        print("\nTesting invalid 'type' value...")
        try:
            router.parse_gemini_response({
                "type": "invalid_type",
                "message": "test",
                "mood": "neutral"
            })
            print("✗ Should have raised ValueError")
            return False
        except ValueError as e:
            print(f"✓ Correctly raised ValueError: {e}")
        
        # Test manipulation without command
        print("\nTesting manipulation without 'command' field...")
        try:
            router.parse_gemini_response({
                "type": "manipulation",
                "message": "test",
                "mood": "neutral"
            })
            print("✗ Should have raised ValueError")
            return False
        except ValueError as e:
            print(f"✓ Correctly raised ValueError: {e}")
        
        print("\n✓ Error handling test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Error handling test FAILED: {e}")
        return False


def main():
    """Run all tests."""
    logger = setup_logging()
    
    print("\n" + "=" * 70)
    print("INTENT ROUTER TEST SUITE")
    print("=" * 70)
    
    results = []
    
    # Run tests
    results.append(("IntentRouter Initialization", test_intent_router_initialization()))
    results.append(("Parse Conversation Response", test_parse_conversation_response()))
    results.append(("Parse Valid Manipulation Response", test_parse_manipulation_response_valid()))
    results.append(("Parse Invalid Manipulation Response", test_parse_manipulation_response_invalid()))
    results.append(("Command Validation", test_command_validation()))
    results.append(("Intent Routing", test_intent_routing()))
    results.append(("Command Management", test_command_management()))
    results.append(("Error Handling", test_error_handling()))
    
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

