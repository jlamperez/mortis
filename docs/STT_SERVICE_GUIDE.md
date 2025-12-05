# Speech-to-Text Service Guide

This guide explains how to use the STT (Speech-to-Text) service in the Mortis application.

## Overview

The STT service converts audio input to text, enabling voice interaction with Mortis. It supports two providers:

1. **Gemini Native Audio** (Recommended) - Uses Google's Gemini API for audio transcription
2. **Google Cloud Speech-to-Text** (Fallback) - Uses Google Cloud STT API

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Required: Gemini API key
GEMINI_API_KEY=your_google_api_key_here

# Optional: STT provider (default: gemini)
STT_PROVIDER=gemini

# Optional: Google Cloud credentials (only needed for google_stt provider)
# GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

### Supported Audio Formats

- WAV (`.wav`)
- MP3 (`.mp3`)
- WebM (`.webm`)
- OGG (`.ogg`)
- FLAC (`.flac`)

## Usage

### Basic Usage

```python
from mortis.stt_service import STTService

# Initialize service (uses environment variables)
stt_service = STTService()

# Transcribe audio file
transcript = stt_service.transcribe("path/to/audio.wav")
print(f"Transcript: {transcript}")
```

### Custom Configuration

```python
from mortis.stt_service import STTService, STTProvider

# Initialize with custom settings
stt_service = STTService(
    provider=STTProvider.GEMINI,
    language_code="es-ES",  # Spanish
    enable_fallback=True
)

# Transcribe audio
transcript = stt_service.transcribe("audio.wav")
```

### Changing Configuration at Runtime

```python
# Change provider
stt_service.configure(
    provider=STTProvider.GOOGLE_STT,
    language_code="fr-FR",
    enable_fallback=False
)
```

## Command-Line Testing

Test the STT service from the command line:

```bash
# Run test suite
python test/test_stt_service.py

# Test with actual audio file
python test/test_stt_service.py path/to/audio.wav

# Test directly with the module
python -m mortis.stt_service path/to/audio.wav
```

## Error Handling

The service handles various error conditions:

### File Not Found
```python
try:
    transcript = stt_service.transcribe("missing.wav")
except FileNotFoundError as e:
    print(f"Audio file not found: {e}")
```

### Invalid Format
```python
try:
    transcript = stt_service.transcribe("document.pdf")
except AudioProcessingError as e:
    print(f"Invalid audio format: {e}")
```

### API Failures
```python
try:
    transcript = stt_service.transcribe("audio.wav")
except AudioProcessingError as e:
    print(f"Transcription failed: {e}")
    # Service automatically tries fallback provider if enabled
```

## Provider Comparison

| Feature | Gemini Native | Google Cloud STT |
|---------|---------------|------------------|
| Setup | Simple (API key only) | Requires service account |
| Accuracy | High | High |
| Latency | Low | Low |
| Cost | Included in Gemini API | Separate billing |
| Offline | No | No |
| Recommended | ✓ Yes | Fallback only |

## Fallback Behavior

When `enable_fallback=True` (default):

1. Primary provider attempts transcription
2. If primary fails, fallback provider is tried automatically
3. If both fail, `AudioProcessingError` is raised

Example:
```python
# With fallback enabled (default)
stt_service = STTService(
    provider=STTProvider.GEMINI,
    enable_fallback=True
)

# If Gemini fails, automatically tries Google STT
transcript = stt_service.transcribe("audio.wav")
```

## Integration with Gradio

The STT service integrates with Gradio's audio input component:

```python
import gradio as gr
from mortis.stt_service import STTService

stt_service = STTService()

def process_audio(audio_path):
    """Process audio input from Gradio."""
    if audio_path is None:
        return "No audio provided"
    
    try:
        transcript = stt_service.transcribe(audio_path)
        return transcript
    except Exception as e:
        return f"Error: {e}"

# Gradio interface
with gr.Blocks() as demo:
    audio_input = gr.Audio(
        sources=["microphone"],
        type="filepath",
        label="Speak to Mortis"
    )
    transcript_output = gr.Textbox(label="Transcript")
    
    audio_input.change(
        fn=process_audio,
        inputs=[audio_input],
        outputs=[transcript_output]
    )
```

## Troubleshooting

### "GEMINI_API_KEY must be provided"
- Add `GEMINI_API_KEY` to your `.env` file
- Get an API key from: https://aistudio.google.com/app/apikey

### "google-cloud-speech is not installed"
- Install with: `pip install google-cloud-speech`
- Or add to `pyproject.toml` dependencies

### "Could not default credentials"
- Set `GOOGLE_APPLICATION_CREDENTIALS` environment variable
- Or use Gemini provider instead (recommended)

### Poor transcription quality
- Ensure audio is clear with minimal background noise
- Use supported audio formats (WAV recommended)
- Check microphone quality
- Try different language codes if applicable

## Performance Tips

1. **Use Gemini provider** - Simpler setup, good performance
2. **Enable fallback** - Ensures reliability
3. **Use WAV format** - Best compatibility
4. **Keep audio short** - Better accuracy for shorter clips
5. **Clear audio** - Reduce background noise

## Next Steps

- See [LOGGING_GUIDE.md](LOGGING_GUIDE.md) for debugging
- See task 7 in the implementation plan for TTS integration
- See task 8 for Gradio UI audio input integration
