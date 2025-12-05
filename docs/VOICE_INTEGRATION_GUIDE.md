# Voice Integration Guide

## Overview

The Mortis system now supports complete multi-modal voice interaction through an integrated voice-to-text-to-Gemini-to-TTS pipeline. This guide explains how to use the voice features and understand the latency monitoring.

## Features

### 1. Voice Input (Speech-to-Text)
- Supports audio input through microphone in Gradio UI
- Uses Gemini native audio processing as primary STT provider
- Automatic fallback to Google Cloud Speech-to-Text if Gemini fails
- Displays transcribed text for user confirmation

### 2. Voice Output (Text-to-Speech)
- Generates audio responses using Google Cloud TTS
- Configured with deep, ominous voice for Mortis character
- Automatic fallback to gTTS for offline scenarios
- Audio files saved to `outputs/` directory

### 3. Latency Monitoring
- Tracks STT processing time
- Tracks Gemini API response time
- Tracks TTS generation time
- Logs total pipeline latency for performance analysis

## API Usage

### Basic Text Input (Backward Compatible)

```python
from mortis.tools import ask_mortis

# Traditional text-only interaction
message, mood, gesture = ask_mortis("Hello Mortis!")
```

### Voice Input with Audio File

```python
from mortis.tools import ask_mortis

# Process audio file and get text response
message, mood, gesture = ask_mortis(audio_path="user_audio.wav")
```

### Complete Voice Pipeline

```python
from mortis.tools import ask_mortis_with_voice

# Full voice-to-voice interaction
message, mood, gesture, audio_path = ask_mortis_with_voice(
    user_msg="Tell me a joke",
    generate_audio=True
)

# Play the audio file at audio_path
```

### Voice Input + Voice Output

```python
from mortis.tools import ask_mortis_with_voice

# Process voice input and generate voice output
message, mood, gesture, audio_path = ask_mortis_with_voice(
    audio_path="user_audio.wav",
    generate_audio=True
)
```

## Configuration

### Environment Variables

```bash
# Gemini API (required)
GEMINI_API_KEY=your_api_key
GEMINI_MODEL=gemini-2.5-flash
GEMINI_TEMPERATURE=0.2

# STT Configuration (optional)
STT_PROVIDER=gemini  # or "google_stt"

# Google Cloud TTS (optional, for better voice quality)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

### STT Provider Selection

The system automatically selects the best available STT provider:

1. **Gemini Native Audio** (default, recommended)
   - High accuracy
   - Single API integration
   - Context-aware transcription

2. **Google Cloud Speech-to-Text** (fallback)
   - Requires Google Cloud credentials
   - High accuracy
   - Supports multiple audio formats

3. **Automatic Fallback**
   - If primary provider fails, automatically tries fallback
   - Ensures robust voice input processing

### TTS Configuration

The system uses Google Cloud TTS by default with these settings:

- **Voice**: en-US-Neural2-D (deep male voice)
- **Speaking Rate**: 0.9 (slightly slower for ominous effect)
- **Pitch**: -2.0 (lower for spooky voice)
- **Format**: MP3

If Google Cloud TTS is unavailable, the system falls back to gTTS.

## Latency Monitoring

The voice pipeline logs detailed latency metrics:

```
INFO - ⏱️ STT latency: 0.85s
INFO - ⏱️ Gemini latency: 1.43s
INFO - ⏱️ Total pipeline latency: 2.28s
INFO - ⏱️ TTS latency: 0.34s
INFO - ⏱️ Complete voice pipeline latency: 2.62s
```

### Performance Targets

- **STT**: < 1.5s for 10-second audio clips
- **Gemini**: < 2.0s for typical responses
- **TTS**: < 0.5s for short responses
- **Total Pipeline**: < 3.0s for complete voice interaction

## Gradio UI Integration

The Gradio interface provides:

1. **Audio Input Component**
   - Click to record from microphone
   - Automatic transcription on recording stop
   - Transcribed text displayed for confirmation

2. **Audio Output Component**
   - Automatic playback of Mortis responses
   - Audio files saved to `outputs/` directory
   - Automatic cleanup of old files (>1 hour)

3. **Text Input (Still Available)**
   - Traditional text chat interface
   - Generates audio responses automatically
   - Full backward compatibility

## Error Handling

The voice pipeline includes robust error handling:

### STT Errors
- **Empty audio**: Returns "I couldn't hear you... speak again."
- **File not found**: Returns error message with fallback
- **Transcription failure**: Automatically tries fallback provider

### TTS Errors
- **Generation failure**: Returns text response without audio
- **Service unavailable**: Falls back to gTTS
- **No audio output**: User still receives text response

### Gemini API Errors
- **Rate limiting**: Automatic retry with exponential backoff
- **Blocked prompts**: Returns safe fallback response
- **Timeout**: Returns "The spirits are slow to respond..."

## Audio File Management

### Output Directory
- Audio files saved to `outputs/` directory
- Filename format: `mortis_response_<timestamp>.mp3`
- Automatic cleanup of files older than 1 hour

### Cleanup
```python
from mortis.tts_service import get_tts_service

tts = get_tts_service()
tts.cleanup_old_files(max_age_seconds=3600)  # Clean files > 1 hour old
```

## Testing

### Test Voice Pipeline

```bash
# Test text input (backward compatibility)
python -c "from mortis.tools import ask_mortis; print(ask_mortis('Hello'))"

# Test voice pipeline with audio generation
python -c "from mortis.tools import ask_mortis_with_voice; print(ask_mortis_with_voice('Hello', generate_audio=True))"
```

### Run Integration Tests

```bash
python test_voice_integration.py
```

## Troubleshooting

### "STT service initialization failed"
- Check GEMINI_API_KEY is set in .env
- Verify API key has access to Gemini models
- Check internet connection

### "TTS generation failed"
- Verify GOOGLE_APPLICATION_CREDENTIALS is set (optional)
- Check outputs/ directory is writable
- System will fall back to gTTS automatically

### "Audio file not found"
- Ensure audio file path is correct
- Check file format is supported (wav, mp3, webm, ogg, flac)
- Verify file is not corrupted

### High Latency
- Check internet connection speed
- Consider using faster Gemini model (gemini-2.5-flash)
- Reduce audio quality for faster processing
- Use local TTS for faster audio generation

## Requirements

### Required
- `google-generativeai>=0.8.0` - Gemini API client
- `gtts` - Fallback TTS service

### Optional (for better quality)
- `google-cloud-speech>=2.26.0` - Google Cloud STT
- `google-cloud-texttospeech>=2.16.0` - Google Cloud TTS

## Next Steps

- **Phase 7**: Asynchronous execution for long-running tasks
- **Phase 8**: Integration testing and deployment
- **Future**: Wake word detection, continuous conversation mode

## Related Documentation

- [STT Service Guide](STT_SERVICE_GUIDE.md)
- [TTS Service Guide](TTS_SERVICE_GUIDE.md)
- [Gemini Setup](GEMINI_SETUP.md)
- [Audio Input Guide](AUDIO_INPUT_GUIDE.md)
