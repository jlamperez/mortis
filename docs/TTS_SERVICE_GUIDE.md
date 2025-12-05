# Text-to-Speech Service Guide

## Overview

The TTS (Text-to-Speech) service converts Mortis text responses into audio output, providing a fully voice-based interaction experience. The service supports both Google Cloud TTS (high-quality neural voices) and gTTS (local fallback).

## Features

- **Google Cloud TTS**: High-quality neural voices with customizable parameters
- **gTTS Fallback**: Local text-to-speech for offline scenarios
- **Mortis Character Voice**: Configured for deep, ominous voice (slower speech, lower pitch)
- **Automatic Cleanup**: Removes old audio files to prevent disk space issues
- **MP3 Output**: Browser-compatible audio format

## Installation

The TTS service dependencies are included in the project:

```bash
make install
```

This installs:
- `google-cloud-texttospeech>=2.16.0` - Google Cloud TTS API
- `gtts>=2.5.0` - Google Text-to-Speech (local fallback)

## Configuration

### Google Cloud TTS (Recommended)

To use Google Cloud TTS, set up authentication:

1. Create a Google Cloud project and enable the Text-to-Speech API
2. Create a service account and download the JSON key file
3. Set the environment variable:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

Or add to your `.env` file:

```
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

### gTTS Fallback

If Google Cloud credentials are not available, the service automatically falls back to gTTS. No additional configuration needed.

## Usage

### Basic Usage

```python
from mortis.tts_service import synthesize_speech

# Generate audio from text
audio_path = synthesize_speech("Beware, mortal. The spirits are watching.")

if audio_path:
    print(f"Audio generated: {audio_path}")
    # Play audio or return to UI
```

### Advanced Usage

```python
from mortis.tts_service import TTSService

# Create custom TTS service
tts_service = TTSService(
    output_dir="custom_outputs",
    use_google_tts=True,
    voice_name="en-US-Neural2-D",  # Deep male voice
    speaking_rate=0.9,              # Slightly slower
    pitch=-2.0                      # Lower pitch
)

# Generate audio
audio_path = tts_service.synthesize(
    text="The darkness calls to you.",
    filename="custom_response"
)

# Cleanup old files (older than 1 hour)
tts_service.cleanup_old_files(max_age_seconds=3600)
```

### Singleton Pattern

The service provides a global singleton for convenience:

```python
from mortis.tts_service import get_tts_service

# Get global service instance
tts_service = get_tts_service()

# Use the service
audio_path = tts_service.synthesize("Hello, mortal.")
```

## Voice Configuration

### Mortis Character Voice

The default configuration is optimized for Mortis character:

- **Voice**: `en-US-Neural2-D` (deep male voice)
- **Speaking Rate**: `0.9` (10% slower for ominous effect)
- **Pitch**: `-2.0` (lower pitch for spooky voice)
- **Format**: MP3 (browser-compatible)

### Available Google TTS Voices

You can customize the voice by changing the `voice_name` parameter:

- `en-US-Neural2-D` - Deep male voice (default for Mortis)
- `en-US-Neural2-A` - Male voice
- `en-US-Neural2-C` - Female voice
- `en-US-Neural2-F` - Female voice
- `en-US-Neural2-I` - Male voice
- `en-US-Neural2-J` - Male voice

See [Google Cloud TTS Voices](https://cloud.google.com/text-to-speech/docs/voices) for full list.

## Output Files

Audio files are saved to the `outputs/` directory by default:

```
outputs/
├── mortis_response_1733270400000.mp3
├── mortis_response_1733270401000.mp3
└── ...
```

Filenames include timestamps to prevent collisions.

## Error Handling

The service handles errors gracefully:

1. **Google TTS Unavailable**: Falls back to gTTS automatically
2. **Empty Text**: Returns `None` without generating audio
3. **Synthesis Failure**: Logs error and returns `None`

Example:

```python
audio_path = synthesize_speech("")
# Returns None, logs warning

audio_path = synthesize_speech("Valid text")
# Returns path to audio file or None on failure
```

## Testing

Run the test suite to verify TTS functionality:

```bash
uv run python test/test_tts_service.py
```

Tests cover:
- Service initialization
- Audio synthesis (Google TTS and gTTS)
- File cleanup
- Error handling
- Character voice parameters

## Integration with Gradio

Example integration with Gradio UI:

```python
import gradio as gr
from mortis.tts_service import synthesize_speech

def mortis_reply_with_voice(message, history):
    # Get text response from Gemini
    response_text = get_gemini_response(message)
    
    # Generate audio
    audio_path = synthesize_speech(response_text)
    
    return response_text, audio_path

with gr.Blocks() as demo:
    chatbot = gr.Chatbot()
    msg = gr.Textbox()
    audio_output = gr.Audio(
        label="Mortis speaks",
        autoplay=True,
        type="filepath"
    )
    
    msg.submit(
        mortis_reply_with_voice,
        inputs=[msg, chatbot],
        outputs=[chatbot, audio_output]
    )
```

## Performance

### Latency

- **Google Cloud TTS**: ~500-1000ms for typical responses
- **gTTS**: ~1-2 seconds for typical responses

### File Sizes

- Short response (10 words): ~10-20 KB
- Medium response (30 words): ~30-50 KB
- Long response (100 words): ~100-150 KB

### Cleanup

Run periodic cleanup to prevent disk space issues:

```python
# Cleanup files older than 1 hour
tts_service.cleanup_old_files(max_age_seconds=3600)

# Cleanup files older than 10 minutes
tts_service.cleanup_old_files(max_age_seconds=600)
```

## Troubleshooting

### Google TTS Not Working

**Problem**: Service falls back to gTTS even with credentials set.

**Solution**:
1. Verify `GOOGLE_APPLICATION_CREDENTIALS` is set correctly
2. Check service account has Text-to-Speech API permissions
3. Verify API is enabled in Google Cloud Console
4. Check logs for specific error messages

### Audio Quality Issues

**Problem**: Audio sounds robotic or low quality.

**Solution**:
- Use Google Cloud TTS instead of gTTS
- Try different Neural2 voices
- Adjust speaking rate and pitch parameters

### File Cleanup Not Working

**Problem**: Old audio files not being removed.

**Solution**:
- Call `cleanup_old_files()` periodically
- Check file permissions in output directory
- Verify `max_age_seconds` parameter is set correctly

## API Reference

### TTSService Class

```python
class TTSService:
    def __init__(
        self,
        output_dir: str = "outputs",
        use_google_tts: bool = True,
        voice_name: str = "en-US-Neural2-D",
        speaking_rate: float = 0.9,
        pitch: float = -2.0
    )
```

**Methods**:

- `synthesize(text: str, filename: Optional[str] = None) -> Optional[str]`
  - Convert text to speech audio file
  - Returns path to generated MP3 file or None on failure

- `cleanup_old_files(max_age_seconds: int = 3600)`
  - Remove audio files older than specified age
  - Default: 1 hour

### Convenience Functions

- `get_tts_service() -> TTSService`
  - Get or create global TTS service instance

- `synthesize_speech(text: str, filename: Optional[str] = None) -> Optional[str]`
  - Convenience function using global service

## Requirements

From `requirements.md`:

- **8.1**: Convert Gemini API text responses to audio using TTS service ✓
- **8.2**: Support Google TTS or equivalent widely-available TTS services ✓
- **8.4**: Generate audio in browser-compatible format (MP3) ✓
- **8.5**: Maintain character voice consistency across all audio responses ✓

## Next Steps

After implementing TTS service:

1. **Task 8**: Update Gradio UI for audio input (STT integration)
2. **Task 9**: Update Gradio UI for audio output (TTS integration)
3. **Task 10**: Integrate voice flow with Gemini (complete voice pipeline)

## Resources

- [Google Cloud TTS Documentation](https://cloud.google.com/text-to-speech/docs)
- [gTTS Documentation](https://gtts.readthedocs.io/)
- [Gradio Audio Components](https://www.gradio.app/docs/audio)
