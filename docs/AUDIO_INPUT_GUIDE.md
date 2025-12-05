# Audio Input Feature Guide

## Overview

The Mortis system now supports voice input, allowing users to speak to Mortis through their microphone instead of typing. This guide explains how to use the audio input feature and troubleshoot common issues.

## User Interface

### Audio Input Component

The audio input component is located at the top of the chat interface:

```
┌─────────────────────────────────────────┐
│ 🎤 Speak to Mortis                      │
│ [Microphone Button] [Waveform Display]  │
└─────────────────────────────────────────┘
```

### Transcription Display

Below the audio input, you'll see a transcription display:

```
┌─────────────────────────────────────────┐
│ Transcribed Text                        │
│ Your transcribed speech will appear     │
│ here...                                 │
└─────────────────────────────────────────┘
```

## How to Use

### Basic Voice Interaction

1. **Click the microphone button** to start recording
2. **Speak your message** clearly into your microphone
3. **Click stop** when you're done speaking
4. **Wait for transcription** (1-3 seconds)
5. **Review the transcribed text** in the display field
6. **Message is automatically sent** to Mortis
7. **Mortis responds** with text and gesture

### Example Interaction

```
User: [Clicks microphone]
User: "Hello Mortis, can you wave at me?"
System: [Transcribing...]
Display: "Hello Mortis, can you wave at me?"
Mortis: "Greetings, mortal... *waves ominously*"
Robot: [Executes wave gesture]
```

## Features

### Automatic Submission
- No need to click "Send" after speaking
- Transcription automatically submits to chat
- Seamless voice-to-response flow

### Transcription Confirmation
- See exactly what was transcribed
- Verify accuracy before processing
- Catch transcription errors early

### Error Handling
- Clear error messages for failures
- Fallback to text input always available
- Non-blocking errors keep UI responsive

## Supported Audio Formats

The system supports the following audio formats:
- WAV (recommended)
- MP3
- WEBM
- OGG
- FLAC

Your browser will automatically record in a compatible format.

## Requirements

### Browser Permissions
- Microphone access must be granted
- Modern browser (Chrome, Firefox, Safari, Edge)
- HTTPS connection (for security)

### Environment Setup
```bash
# Required in .env file
GEMINI_API_KEY=your_api_key_here

# Optional configuration
STT_PROVIDER=gemini  # Default, recommended
LOG_LEVEL=INFO       # Set to DEBUG for detailed logs
```

## Troubleshooting

### "Microphone not found"
**Problem**: Browser can't access microphone
**Solution**: 
- Check browser permissions
- Ensure microphone is connected
- Try refreshing the page
- Check system audio settings

### "Audio processing failed"
**Problem**: STT service couldn't transcribe audio
**Solution**:
- Check internet connection
- Verify GEMINI_API_KEY is set
- Try speaking more clearly
- Check audio quality/volume
- Use text input as fallback

### "Audio file not found"
**Problem**: Recorded audio file is missing
**Solution**:
- Try recording again
- Check browser console for errors
- Ensure sufficient disk space
- Try different browser

### Empty transcription
**Problem**: Transcription returns empty text
**Solution**:
- Speak louder or closer to microphone
- Check microphone is not muted
- Ensure background noise is minimal
- Try recording longer utterances

### Slow transcription
**Problem**: Transcription takes too long
**Solution**:
- Check internet speed
- Try shorter utterances
- Consider local STT provider
- Check Gemini API status

## Technical Details

### STT Service
- **Primary**: Gemini native audio support
- **Fallback**: Google Cloud Speech-to-Text
- **Language**: English (en-US) by default
- **Latency**: 1-3 seconds typical

### Audio Processing Flow
```
Browser Microphone
    ↓
Audio Recording (Gradio)
    ↓
Audio File (temporary)
    ↓
STT Service (Gemini)
    ↓
Transcribed Text
    ↓
Transcription Display
    ↓
Chat Interface
    ↓
Mortis Response
```

### Error Recovery
- All errors are logged for debugging
- User sees friendly error messages
- Text input remains available
- System continues functioning

## Configuration Options

### STT Provider Selection
```bash
# Use Gemini (recommended)
STT_PROVIDER=gemini

# Use Google Cloud STT (requires credentials)
STT_PROVIDER=google_stt
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

### Language Configuration
Currently supports English (en-US). Multi-language support coming soon.

### Logging
```bash
# See detailed STT logs
LOG_LEVEL=DEBUG

# Normal operation
LOG_LEVEL=INFO
```

## Best Practices

### For Best Transcription Quality
1. **Speak clearly** and at normal pace
2. **Minimize background noise**
3. **Use good microphone** (headset recommended)
4. **Keep utterances under 10 seconds**
5. **Pause between sentences**

### For Best User Experience
1. **Review transcription** before it submits
2. **Use text input** for complex commands
3. **Speak naturally** - no need to shout
4. **Wait for transcription** to complete
5. **Check error messages** if something fails

## Privacy & Security

### Data Handling
- Audio is processed by Gemini API
- Temporary audio files are created locally
- Files are cleaned up after processing
- No audio is permanently stored

### Security Considerations
- Requires HTTPS for microphone access
- API key must be kept secure
- Audio data sent to Google servers
- Consider local STT for sensitive data

## Future Enhancements

Planned improvements:
- Real-time streaming transcription
- Voice activity detection (auto-stop)
- Multi-language support
- Offline mode with local Whisper
- Audio preprocessing (noise reduction)
- Custom wake words

## Support

### Getting Help
- Check logs with `LOG_LEVEL=DEBUG`
- Review error messages in transcription display
- Test with text input to isolate issues
- Check Gemini API status
- Verify environment configuration

### Reporting Issues
When reporting audio input issues, include:
- Browser and version
- Operating system
- Error message from transcription display
- Relevant logs (with DEBUG level)
- Steps to reproduce

## Summary

The audio input feature provides a natural, hands-free way to interact with Mortis. It's designed to be:
- **Easy to use**: Click, speak, done
- **Reliable**: Comprehensive error handling
- **Fast**: 1-3 second transcription
- **Flexible**: Text input always available
- **Transparent**: See what was transcribed

Enjoy speaking with Mortis! 👻🎤
