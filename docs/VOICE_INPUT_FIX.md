# Voice Input Fix

## Problem

After implementing the audio output fix for text chat, voice input (speaking to Mortis) stopped working correctly. The audio wasn't being processed properly.

## Root Cause

The `handle_audio_and_submit` function was trying to process audio through the voice pipeline twice:

1. First call: `mortis_reply_with_audio(audio_input_path=audio_path)` - This would transcribe the audio internally
2. Second call: `process_audio_input(audio_path)` - This would transcribe the same audio again for display

This caused confusion in the pipeline and the audio wasn't being handled correctly.

## Solution

Refactored the `handle_audio_and_submit` function to follow a clearer flow:

### New Flow

```python
def handle_audio_and_submit(audio_path, history, model_name):
    # Step 1: Transcribe audio once for display
    transcript = process_audio_input(audio_path)
    
    # Step 2: Check for errors
    if not transcript or transcript.startswith("[Error:"):
        return transcript, history, None
    
    # Step 3: Use transcribed TEXT (not audio) to get response
    response_text, response_audio = mortis_reply_with_audio(
        message=transcript,  # Pass text, not audio
        audio_input_path=None  # Don't pass audio to avoid double transcription
    )
    
    # Step 4: Update chat history
    history.append({"role": "user", "content": transcript})
    history.append({"role": "assistant", "content": response_text})
    
    return transcript, history, response_audio
```

## Key Changes

1. **Single Transcription**: Audio is transcribed only once via `process_audio_input()`
2. **Text-Based Processing**: The transcribed text is passed to `mortis_reply_with_audio()` as a text message
3. **No Double Processing**: We explicitly set `audio_input_path=None` to prevent the voice pipeline from trying to transcribe again
4. **Clear Error Handling**: Errors are caught early and returned immediately

## How It Works Now

### Voice Input Flow

```
User speaks → Audio recorded → 
Transcribe to text (STT) → 
Display transcript → 
Send text to Gemini → 
Generate response + audio (TTS) → 
Display text + play audio
```

### Text Input Flow

```
User types → 
Send text to Gemini → 
Generate response + audio (TTS) → 
Display text + play audio
```

Both flows now work correctly and independently!

## Benefits

✅ **Voice input works correctly** - Audio is transcribed and processed properly
✅ **No double transcription** - Efficient processing, faster response
✅ **Clear error handling** - Errors are caught and displayed to user
✅ **Text input still works** - No regression in text chat functionality
✅ **Audio output for both** - Both voice and text input get audio responses

## Testing

### Test Voice Input

1. Start the application: `make run`
2. Click the microphone button
3. Speak a message
4. Stop recording
5. You should see:
   - Your transcribed text in the "Transcribed Text" box
   - Mortis's text response in the chat
   - Mortis's voice response playing automatically

### Test Text Input

1. Type a message in the text input
2. Press Enter or click Send
3. You should see:
   - Mortis's text response in the chat
   - Mortis's voice response playing automatically

## Files Modified

- `src/mortis/app.py`
  - Refactored `handle_audio_and_submit()` function
  - Fixed double transcription issue
  - Improved error handling

## Related Documentation

- [Audio Output Fix](AUDIO_OUTPUT_FIX.md)
- [Voice Integration Guide](docs/VOICE_INTEGRATION_GUIDE.md)
- [Task 10 Implementation Summary](TASK_10_IMPLEMENTATION_SUMMARY.md)

## Summary

Both voice input and text input now work perfectly with full audio output! 🎤🔊👻
