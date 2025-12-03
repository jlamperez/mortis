#!/usr/bin/env python3
"""
Quick test to verify logging is working correctly.
Run this to see what the logs will look like without starting the full app.
"""

import os
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set log level
os.environ['LOG_LEVEL'] = os.getenv('LOG_LEVEL', 'INFO')

def setup_logging():
    """Set up logging the same way the app does."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Remove existing handlers and reconfigure
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Set up new handler with our format
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    ))
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, log_level))
    
    return logging.getLogger(__name__)

def main():
    logger = setup_logging()
    
    print("\n" + "=" * 70)
    print("LOGGING TEST - This is what you'll see when running 'make run'")
    print("=" * 70 + "\n")
    
    # Simulate app startup
    logger.info("=" * 60)
    logger.info("🎃 Starting Mortis application...")
    logger.info(f"📊 Log level: {os.getenv('LOG_LEVEL', 'INFO')}")
    logger.info("🌐 Launching on http://127.0.0.1:7860")
    logger.info("=" * 60)
    
    # Simulate a user interaction
    print("\n[Simulating user sending a message...]\n")
    
    logger.info("💬 User message: Hello Mortis!")
    logger.info("🤖 Using model: gemini-2.5-flash")
    
    # Import and test the tools module
    try:
        from mortis.tools import _get_gemini_client
        logger.info("Asking Mortis: Hello Mortis!...")
        
        # This will initialize the client and show its log
        client = _get_gemini_client()
        
        logger.info("Mortis responds (type: conversation, mood: ominous, gesture: wave)")
        logger.info("👻 Mortis reply: Greetings, mortal... welcome to my haunted domain.")
        logger.info("😈 Mood: ominous, Gesture: wave")
        
    except Exception as e:
        logger.error(f"Error during test: {e}")
        logger.info("(This is expected if GEMINI_API_KEY is not set)")
    
    print("\n" + "=" * 70)
    print("✓ Logging test complete!")
    print("=" * 70)
    print("\nTo see DEBUG level logs (more detailed), run:")
    print("  LOG_LEVEL=DEBUG python test_logging.py")
    print("\nTo see logs when running the app:")
    print("  make run")
    print("\nTo change log level, add to your .env file:")
    print("  LOG_LEVEL=DEBUG  # or INFO, WARNING, ERROR")
    print()

if __name__ == "__main__":
    main()
