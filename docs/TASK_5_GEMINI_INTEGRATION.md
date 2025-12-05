# Task 5: Replace Existing LLM API in tools.py

## Summary

Successfully refactored the Mortis system to use Google Gemini API instead of the previous generic LLM API. This task maintains backward compatibility with gesture execution while integrating the new GeminiClient and structured response parsing.

## Changes Made

### 1. Refactored `src/mortis/tools.py`

**Before:**
- Used generic LLM API with `requests` library
- Required `API_KEY` and `API_BASE_URL` environment variables
- Used tool calling with `perform_mortis_act` function
- Direct HTTP POST requests to API endpoint

**After:**
- Uses `GeminiClient` from `gemini_client.py`
- Requires `GEMINI_API_KEY` environment variable
- Leverages structured JSON responses from Gemini
- Uses `GeminiResponse` model for parsing
- Maintains backward compatibility with same return signature: `(message, mood, gesture)`

**Key Features:**
- Lazy initialization of `GeminiClient` (created on first use)
- Graceful error handling with fallback responses
- Support for model selection via `model_name` parameter
- Automatic robot arm connection
- Comprehensive logging

### 2. Updated Environment Configuration

**`.env.example`:**
- Added detailed documentation for Gemini API configuration
- Documented all environment variables with descriptions
- Added link to get Gemini API key
- Marked old `API_KEY` and `API_BASE_URL` as deprecated
- Included default values and options

**New Required Variables:**
- `GEMINI_API_KEY`: Google API key (required)
- `GEMINI_MODEL`: Model name (default: gemini-2.5-flash)
- `GEMINI_TEMPERATURE`: Temperature setting (default: 0.2)

### 3. Updated `README.md`

**Environment Setup Section:**
- Added comprehensive setup instructions for Gemini API
- Included step-by-step guide to get API key from Google AI Studio
- Updated example `.env` configuration
- Added instructions to copy `.env.example`
- Updated feature list to mention Gemini API

**Other Updates:**
- Changed "Chat with LLM models via API" to "Chat with Gemini AI models via Google's Gemini API"
- Updated `make check-env` description to reference `GEMINI_API_KEY`

### 4. Updated `Makefile`

**Changes:**
- Changed `REQUIRED_ENV` from `API_KEY` to `GEMINI_API_KEY`
- Updated success message in `check-env` target
- Now validates correct environment variable

### 5. Updated `src/mortis/app.py`

**Model Choices:**
- Replaced old model names with Gemini models:
  - `gemini-2.5-flash` (default)
  - `gemini-2.0-flash-exp`
  - `gemini-1.5-pro`
  - `gemini-1.5-flash`

**UI Updates:**
- Changed dropdown label from "LLM model" to "Gemini Model"
- Updated info text to "Select Gemini model for Mortis"

## Backward Compatibility

The refactored `ask_mortis()` function maintains the same signature and return values:

```python
def ask_mortis(user_msg: str, model_name: str = None) -> Tuple[str, str, str]:
    """Returns: (message, mood, gesture)"""
```

This ensures that:
- Existing code calling `ask_mortis()` continues to work
- Gradio UI integration requires no changes (except model names)
- Gesture execution flow remains unchanged
- Robot arm control is unaffected

## Integration Points

The refactored code integrates with:

1. **`gemini_client.py`**: Handles all Gemini API communication
2. **`models.py`**: Provides structured data models for parsing responses
3. **`robot.py`**: Unchanged - gesture execution works as before
4. **`app.py`**: Updated model choices, but interface unchanged

## Testing

### Import Test
```bash
python -c "from src.mortis.tools import ask_mortis; print('Import successful')"
```
✓ Passed - All imports work correctly

### Diagnostics
```bash
# No syntax errors or type issues
getDiagnostics(["src/mortis/tools.py", "src/mortis/gemini_client.py", "src/mortis/models.py"])
```
✓ Passed - No diagnostics found

### Existing Test
The existing test file `test/test_system_prompt.py` validates:
- Conversational responses return correct type
- Manipulation commands return correct type
- JSON format is properly structured
- Message length constraints are met

## Requirements Satisfied

This task satisfies the following requirements from the spec:

- **Requirement 1.1**: "THE Mortis System SHALL use the Google Gemini API for all language model interactions" ✓
- **Requirement 9.1**: "THE Mortis System SHALL not depend on vendor-specific cloud platform services" ✓
- **Requirement 9.4**: "THE Mortis System SHALL document all external service dependencies in the environment configuration" ✓

## Migration Notes

For users upgrading from the old API:

1. **Update `.env` file:**
   ```bash
   # Old (remove these)
   API_KEY=...
   API_BASE_URL=...
   
   # New (add these)
   GEMINI_API_KEY=your_google_api_key_here
   GEMINI_MODEL=gemini-2.5-flash
   GEMINI_TEMPERATURE=0.2
   ```

2. **Get Gemini API Key:**
   - Visit https://aistudio.google.com/app/apikey
   - Sign in with Google account
   - Create API key
   - Add to `.env` file

3. **Update model selection:**
   - Old models (cai-llama-*, gpt-oss-*) no longer available
   - Use Gemini models in dropdown

4. **No code changes required:**
   - Existing gesture execution works unchanged
   - UI interaction remains the same
   - Robot control unaffected

## Next Steps

With this task complete, the system is ready for:

- **Task 6-10**: Voice input/output integration (Phase 2)
- **Task 11-15**: Dataset collection infrastructure (Phase 3)
- **Task 24-26**: Intent detection and routing for SmolVLA (Phase 5)

The Gemini integration provides the foundation for:
- Multi-modal interaction (voice + text)
- Intent detection for manipulation commands
- Structured JSON responses for routing decisions

## Files Modified

1. `src/mortis/tools.py` - Complete refactor to use GeminiClient
2. `.env.example` - Updated with Gemini configuration
3. `README.md` - Updated environment setup and features
4. `Makefile` - Updated environment variable checks
5. `src/mortis/app.py` - Updated model choices

## Files Created

1. `done/TASK_5_GEMINI_INTEGRATION.md` - This summary document

## Verification Commands

```bash
# Check environment configuration
make check-env

# Test imports
python -c "from src.mortis.tools import ask_mortis; print('✓ Import successful')"

# Run system prompt test (requires GEMINI_API_KEY)
python test/test_system_prompt.py

# Run the application
make run
```

## Status

✅ **Task 5 Complete**

All subtasks completed:
- ✅ Refactor `ask_mortis()` function to use `GeminiClient`
- ✅ Update response parsing to use new data models
- ✅ Maintain backward compatibility with gesture execution
- ✅ Update environment configuration documentation
