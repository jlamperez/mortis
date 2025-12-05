# Task 3: Gemini System Prompt Implementation

## Summary

Successfully implemented the Gemini system prompt for Mortis character and intent detection in `src/mortis/gemini_client.py`.

## Implementation Details

### 1. System Prompt (`MORTIS_SYSTEM_PROMPT`)

Created a comprehensive system prompt that includes:

- **Character Definition**: Mortis as a mischievous Halloween spirit with specific personality traits
- **Manipulation Tasks**: All 6 exact task strings for SmolVLA execution:
  1. "Pick up the skull and place it in the green cup"
  2. "Pick up the skull and place it in the orange cup"
  3. "Pick up the skull and place it in the purple cup"
  4. "Pick up the eyeball and place it in the green cup"
  5. "Pick up the eyeball and place it in the orange cup"
  6. "Pick up the eyeball and place it in the purple cup"

- **JSON Response Format**: Two distinct response types:
  - **Conversation**: `{type, message, mood, gesture}`
  - **Manipulation**: `{type, command, message, mood}`

- **Examples**: 5 example interactions demonstrating both response types

### 2. JSON Mode Configuration

Confirmed that JSON mode is already configured in `GeminiClient.__init__()`:
```python
self.generation_config = types.GenerateContentConfig(
    temperature=self.temperature,
    response_mime_type="application/json"
)
```

### 3. Default System Prompt

Updated `send_message()` method to use `MORTIS_SYSTEM_PROMPT` by default:
```python
def send_message(self, user_input: str, system_prompt: Optional[str] = None) -> dict:
    if system_prompt is None:
        system_prompt = MORTIS_SYSTEM_PROMPT
    return self._send_message_with_retry(user_input, system_prompt, retry_count=0)
```

## Testing

Created `test_system_prompt.py` with 5 test cases covering:
- Conversational greetings
- Conversational questions
- Manipulation commands with exact wording
- Manipulation commands with variations
- Different object and cup combinations

### Test Results

✅ **All 5 tests passed**

- Correct response type detection (conversation vs manipulation)
- Exact command string matching for manipulation tasks
- Proper JSON structure with all required fields
- Message length constraints enforced (≤30 words, ≤120 chars)
- Character stays in-character with Halloween theme
- Intent detection works with wording variations

## Requirements Satisfied

- ✅ **3.1**: System prompt defines all valid SmolVLA Task Strings
- ✅ **3.2**: Gemini determines if input matches a valid Task String
- ✅ **9.2**: Uses standard Python libraries (no vendor-specific cloud dependencies)

## Files Modified

- `src/mortis/gemini_client.py`: Added `MORTIS_SYSTEM_PROMPT` constant and updated `send_message()` method

## Files Created

- `test_system_prompt.py`: Comprehensive test script for system prompt validation
- `done/TASK_3_SYSTEM_PROMPT.md`: This summary document

## Next Steps

Task 3 is complete. The next task in the implementation plan is:

**Task 4**: Implement error handling and retry logic
- Add exponential backoff retry for rate limiting ✅ (already implemented)
- Handle `BlockedPromptException` with fallback responses ✅ (already implemented)
- Implement timeout handling for API calls
- Add error logging and user-friendly error messages ✅ (already implemented)
- Update environment configuration documentation
