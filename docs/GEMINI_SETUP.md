# Gemini API Setup Guide

## Overview

This document explains how to set up the Gemini API client for the Mortis project.

## Installation

The project now uses the new `google-genai` package (the successor to the deprecated `google-generativeai`). This package is compatible with the project's dependencies and has been successfully installed.

```bash
# Already installed in the project
uv add google-genai
```

## Environment Configuration

Add these variables to your `.env` file:

```bash
# Gemini API Configuration
GEMINI_API_KEY=your_google_api_key_here
GEMINI_MODEL=gemini-2.0-flash-exp
GEMINI_TEMPERATURE=0.2
```

### Getting a Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key and add it to your `.env` file

## Usage Example

```python
from mortis.gemini_client import GeminiClient

# Initialize client (reads from environment variables)
client = GeminiClient()

# Send a message
response = client.send_message(
    "Hello Mortis, introduce yourself!",
    system_prompt="You are Mortis, a mischievous Halloween spirit."
)

print(response)
# Output: {'type': 'conversation', 'message': '...', 'mood': 'ominous', 'gesture': 'wave'}
```

## Features Implemented

✅ **Configuration Management**
- Environment variable support for `GEMINI_API_KEY`, `GEMINI_MODEL`, `GEMINI_TEMPERATURE`
- Default values for model and temperature
- Runtime model reconfiguration

✅ **Message Sending**
- `send_message()` method with system prompt support
- JSON response parsing
- Structured output format

✅ **Error Handling**
- Exponential backoff retry for rate limiting
- Blocked prompt handling with fallback responses
- JSON parsing error recovery
- Comprehensive error logging

✅ **Retry Logic**
- Configurable max retries (default: 3)
- Exponential backoff: 1s, 2s, 4s
- Graceful degradation to fallback responses

## Testing

Run the test suite:

```bash
python test_gemini_client.py
```

This runs unit tests with mocked API calls to verify the implementation.

## Next Steps

1. Set your API key in `.env`:
   ```bash
   GEMINI_API_KEY=your_actual_api_key_here
   ```

2. Test with real API:
   ```bash
   python src/mortis/gemini_client.py
   ```

3. Integrate with the main application (Task 5 in the implementation plan)

## Troubleshooting

### Import Error: No module named 'google.genai'

Run `uv sync` to ensure all dependencies are installed:
```bash
uv sync
```

### API Key Error

Make sure `GEMINI_API_KEY` is set in your `.env` file and is valid.

### Rate Limiting

The client automatically retries with exponential backoff. If you hit rate limits frequently, consider:
- Reducing request frequency
- Upgrading your API quota
- Implementing request caching

## References

- [Gemini API Documentation](https://ai.google.dev/docs)
- [google-genai Python SDK](https://github.com/googleapis/python-genai) (new package)
- [LeRobot GitHub](https://github.com/huggingface/lerobot)

## Migration from google-generativeai

This project uses the new `google-genai` package instead of the deprecated `google-generativeai`. Key differences:

- **Old**: `import google.generativeai as genai`
- **New**: `from google import genai`

- **Old**: `genai.configure(api_key=key)` then `genai.GenerativeModel(...)`
- **New**: `client = genai.Client(api_key=key)` then `client.models.generate_content(...)`

The implementation has been updated to use the new API.
