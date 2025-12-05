# Audio Output Fix for Text Chat

## Problem

When users chat with Mortis using text input, the system was generating audio responses but not playing them. Only the text response was displayed.

## Root Cause

The issue was with how Gradio's `ChatInterface` component works:

1. `ChatInterface` internally handles the submit button and text input
2. It only passes the text response to the chatbot component
3. Our `mortis_reply_wrapper` was generating audio but had no way to pass it to the `audio_output` component
4. The separate `handle_text_submit_with_audio` function wasn't being triggered because `ChatInterface` handles submission internally

## Solution

Implemented a state-based approach using Gradio's `State` component:

### Changes Made

1. **Added Audio State Component**
   ```python
   audio_state = gr.State(value=None)
   ```

2. **Updated mortis_reply_wrapper**
   ```python
   def mortis_reply_wrapper(message, history, model_name, audio_state_value):
       """Wrapper that generates both text and audio."""
       text_response, audio_path = mortis_reply_with_audio(message, history, model_name)
       # Return text for chat and audio path for state
       return text_response, audio_path
   ```

3. **Connected State to ChatInterface**
   ```python
   chat_interface = gr.ChatInterface(
       fn=mortis_reply_wrapper,
       additional_inputs=[model_dd, audio_state],
       additional_outputs=[audio_state],  # Audio path stored in state
       ...
   )
   ```

4. **Connected State Changes to Audio Output**
   ```python
   audio_state.change(
       fn=lambda x: x,  # Pass through the audio path
       inputs=[audio_state],
       outputs=[audio_output],
   )
   ```

## How It Works

1. User types a message and submits
2. `ChatInterface` calls `mortis_reply_wrapper`
3. `mortis_reply_wrapper` generates both text and audio
4. Text goes to the chatbot, audio path goes to `audio_state`
5. When `audio_state` changes, it triggers the `.change()` event
6. The audio path is passed to `audio_output` component
7. Audio plays automatically (autoplay=True)

## Benefits

- ✅ Audio now plays for text chat
- ✅ Audio plays for voice chat (already working)
- ✅ Clean integration with Gradio's component system
- ✅ No breaking changes to existing functionality
- ✅ Maintains backward compatibility

## Testing

To verify the fix works:

1. Start the application: `make run`
2. Type a message in the text input
3. Submit the message
4. You should hear Mortis speak the response
5. The audio player should show the waveform

## Files Modified

- `src/mortis/app.py`
  - Added `audio_state` component
  - Updated `mortis_reply_wrapper` to return audio path
  - Connected state changes to audio output
  - Removed redundant `handle_text_submit_with_audio` function

## Related Documentation

- [Voice Integration Guide](docs/VOICE_INTEGRATION_GUIDE.md)
- [Task 10 Implementation Summary](TASK_10_IMPLEMENTATION_SUMMARY.md)
