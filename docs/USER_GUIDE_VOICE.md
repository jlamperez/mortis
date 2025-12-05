# Voice Interaction User Guide

This guide explains how to use Mortis's voice interaction features for a fully hands-free, multi-modal experience.

## Overview

Mortis supports complete voice interaction:
- **Voice Input (STT)**: Speak to Mortis through your microphone
- **Voice Output (TTS)**: Hear Mortis respond with synthesized speech
- **Multi-Modal**: Seamlessly switch between voice and text

## Getting Started

### Prerequisites

- **Gemini API Key**: Required for voice input (STT)
- **Microphone**: Built-in or external microphone
- **Browser**: Modern browser with microphone support (Chrome, Firefox, Edge)
- **Internet Connection**: Required for Gemini API and TTS services

### Quick Setup

1. **Ensure Gemini API key is configured**:
   ```bash
   # Check .env file
   grep GEMINI_API_KEY .env
   ```

2. **Run Mortis**:
   ```bash
   make run
   ```

3. **Open in browser**:
   - Navigate to http://127.0.0.1:7860/?__theme=dark
   - Allow microphone access when prompted

4. **Start talking**:
   - Click the microphone icon
   - Speak your message
   - Stop recording
   - Listen to Mortis's response

## Using Voice Input

### Basic Voice Interaction

1. **Click the microphone icon** in the "Speak to Mortis" audio input component
2. **Speak clearly** into your microphone
3. **Click stop** when finished speaking
4. **Wait for transcription** - Your speech will be converted to text
5. **View transcription** - The text appears in the chat
6. **Receive response** - Mortis responds with voice and text

### Tips for Best Results

- **Speak clearly** and at a normal pace
- **Minimize background noise** for better transcription accuracy
- **Keep messages concise** (under 30 seconds for best performance)
- **Wait for processing** - Don't interrupt while Mortis is responding
- **Check transcription** - Verify the text matches what you said

### Voice Input Examples

**Conversational**:
- "Hello Mortis, introduce yourself"
- "Tell me a spooky story"
- "What can you do?"
- "How are you feeling today?"

**Gesture Commands**:
- "Wave hello to me"
- "Point to the left"
- "Grab something"
- "Drop what you're holding"

**Manipulation Tasks** (if enabled):
- "Pick up the skull and place it in the green cup"
- "Move the eyeball to the orange cup"

## Using Voice Output

### Automatic Voice Responses

Mortis automatically generates voice responses for all interactions:

1. **Text input** → Mortis responds with voice + text
2. **Voice input** → Mortis responds with voice + text
3. **Audio plays automatically** in the browser

### Voice Characteristics

Mortis's voice is configured to match the character:

- **Voice**: Deep male voice (en-US-Neural2-D)
- **Speaking Rate**: 0.9x (slightly slower for ominous effect)
- **Pitch**: -2.0 (lower for spooky character)
- **Format**: MP3 (compatible with all browsers)

### Controlling Audio Playback

- **Autoplay**: Enabled by default
- **Volume**: Use browser volume controls
- **Pause/Resume**: Use audio player controls in UI
- **Replay**: Click the audio player to replay

## Voice Configuration

### STT Provider Selection

Mortis uses Gemini native audio by default (recommended):

```bash
# In .env file
STT_PROVIDER=gemini  # Default, uses Gemini API
```

Alternative: Google Cloud Speech-to-Text:

```bash
# In .env file
STT_PROVIDER=google_stt
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

### TTS Provider Selection

Mortis automatically selects the best available TTS provider:

1. **Google Cloud TTS** (if credentials available)
   - Highest quality
   - Natural-sounding voice
   - Requires Google Cloud credentials

2. **gTTS** (automatic fallback)
   - Good quality
   - Free, no setup required
   - Works offline

To use Google Cloud TTS:

```bash
# In .env file
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

### Voice Quality Settings

Adjust voice characteristics by editing `src/mortis/tts_service.py`:

```python
# Speaking rate (0.5 - 2.0)
speaking_rate=0.9  # Default: slightly slower

# Pitch (-20.0 to 20.0)
pitch=-2.0  # Default: lower for spooky effect

# Voice selection
name="en-US-Neural2-D"  # Deep male voice
```

## Performance and Latency

### Expected Latency

- **STT (Speech-to-Text)**: 0.5-1.5 seconds
- **Gemini Processing**: 1.0-2.0 seconds
- **TTS (Text-to-Speech)**: 0.3-0.5 seconds
- **Total Pipeline**: 2-4 seconds

### Optimizing Performance

**For faster responses**:
- Use `gemini-2.5-flash` model (default)
- Use gTTS instead of Google Cloud TTS
- Keep messages short (under 10 seconds)
- Ensure good internet connection

**For better quality**:
- Use `gemini-1.5-pro` model
- Use Google Cloud TTS
- Speak clearly with minimal background noise

### Monitoring Latency

Enable debug logging to see detailed timing:

```bash
LOG_LEVEL=DEBUG make run
```

Look for log messages like:
```
INFO - ⏱️ STT latency: 0.85s
INFO - ⏱️ Gemini latency: 1.43s
INFO - ⏱️ TTS latency: 0.34s
INFO - ⏱️ Complete voice pipeline latency: 2.62s
```

## Troubleshooting Voice Issues

### Microphone Not Working

**Problem**: Browser can't access microphone

**Solutions**:
1. **Check browser permissions**:
   - Chrome: Settings → Privacy and security → Site settings → Microphone
   - Firefox: Preferences → Privacy & Security → Permissions → Microphone
   - Allow access for localhost

2. **Test microphone**:
   - Use browser's built-in microphone test
   - Try a different browser
   - Check system microphone settings

3. **Restart browser** after granting permissions

### Transcription Errors

**Problem**: Speech not transcribed correctly

**Solutions**:
1. **Speak more clearly** and at a normal pace
2. **Reduce background noise**:
   - Close windows
   - Turn off fans/AC
   - Use a quiet room
3. **Use a better microphone**:
   - External USB microphone
   - Headset with mic
4. **Check audio quality**:
   - Ensure microphone is not muted
   - Adjust input volume in system settings

### No Audio Output

**Problem**: Mortis's voice doesn't play

**Solutions**:
1. **Check browser audio**:
   - Ensure browser is not muted
   - Check system volume
   - Try playing other audio in browser

2. **Check outputs directory**:
   ```bash
   ls -la outputs/
   # Should show .mp3 files
   ```

3. **Verify TTS service**:
   ```bash
   LOG_LEVEL=DEBUG make run
   # Look for "TTS generation" messages
   ```

4. **Try fallback TTS**:
   - System automatically uses gTTS if Google TTS fails
   - Check logs for which provider is being used

### High Latency

**Problem**: Long delays between speaking and response

**Solutions**:
1. **Check internet speed**:
   - Gemini API requires good connection
   - Test with speedtest.net

2. **Use faster model**:
   ```bash
   # In .env
   GEMINI_MODEL=gemini-2.5-flash
   ```

3. **Reduce audio length**:
   - Keep messages under 10 seconds
   - Break long messages into shorter ones

4. **Use local TTS**:
   - gTTS is faster than Google Cloud TTS
   - Remove GOOGLE_APPLICATION_CREDENTIALS from .env

### Voice Cuts Off

**Problem**: Audio response is incomplete

**Solutions**:
1. **Check audio file**:
   ```bash
   ls -la outputs/
   # Verify .mp3 files are not 0 bytes
   ```

2. **Increase timeout**:
   - Edit `src/mortis/tts_service.py`
   - Increase timeout in TTS generation

3. **Check logs**:
   ```bash
   LOG_LEVEL=DEBUG make run
   # Look for TTS errors
   ```

## Advanced Features

### Voice-Only Mode

For a completely hands-free experience:

1. **Disable text input** (optional):
   - Use only the microphone
   - Ignore the text chat box

2. **Continuous conversation**:
   - Speak → Listen → Speak → Listen
   - No typing required

### Mixing Voice and Text

You can seamlessly switch between input modes:

1. **Voice input** → Mortis responds with voice
2. **Text input** → Mortis responds with voice
3. **Mix freely** based on your preference

### Voice Commands for Robot

Use natural language to control the robot:

**Gestures**:
- "Wave at me"
- "Point to the right"
- "Grab the object"
- "Drop it"

**Manipulation** (if enabled):
- "Pick up the skull and put it in the green cup"
- "Move the eyeball to the orange cup"

## Best Practices

### For Best Voice Recognition

1. **Environment**:
   - Quiet room
   - Minimal background noise
   - Good microphone quality

2. **Speaking**:
   - Clear pronunciation
   - Normal pace (not too fast or slow)
   - Natural tone

3. **Message Length**:
   - Keep under 30 seconds
   - Break long messages into shorter ones
   - One thought per message

### For Best Voice Output

1. **Audio Quality**:
   - Use Google Cloud TTS for best quality
   - Ensure good internet connection
   - Use quality speakers/headphones

2. **Character Consistency**:
   - Voice matches Mortis's spooky character
   - Consistent tone across responses
   - Appropriate pacing for dramatic effect

### For Best Overall Experience

1. **Start with text** to understand Mortis's personality
2. **Switch to voice** once comfortable
3. **Use voice for natural conversation**
4. **Use text for precise commands**
5. **Monitor latency** and adjust settings if needed

## Privacy and Security

### Data Handling

- **Voice data**: Sent to Gemini API for transcription
- **Text responses**: Generated by Gemini API
- **Audio files**: Stored locally in `outputs/` directory
- **Cleanup**: Old audio files automatically deleted after 1 hour

### Privacy Considerations

1. **API calls**: Voice data sent to Google servers
2. **Local storage**: Audio files stored temporarily
3. **No recording**: Mortis doesn't record conversations
4. **Automatic cleanup**: Audio files deleted regularly

### Security Best Practices

1. **API keys**: Keep GEMINI_API_KEY secure
2. **Credentials**: Protect Google Cloud credentials
3. **Local files**: `outputs/` directory is local only
4. **Network**: Use secure internet connection

## Examples and Use Cases

### Example 1: Casual Conversation

**User** (voice): "Hello Mortis, how are you today?"

**Mortis** (voice + text): "Ah, another soul dares to speak... I am well, dwelling in the shadows as always. What brings you to my domain?"

### Example 2: Robot Control

**User** (voice): "Wave hello to me"

**Mortis** (voice + text): "As you wish, mortal..." *[robot waves]*

### Example 3: Manipulation Task

**User** (voice): "Pick up the skull and place it in the green cup"

**Mortis** (voice + text): "The skull shall find its resting place..." *[robot executes task]*

### Example 4: Mixed Input

**User** (text): "What can you do?"

**Mortis** (voice + text): "I can converse, gesture, and manipulate objects with my spectral limb..."

**User** (voice): "Show me a gesture"

**Mortis** (voice + text): "Behold!" *[robot performs gesture]*

## Next Steps

- **Explore gestures**: Try different voice commands for robot control
- **Train manipulation**: Collect data and train SmolVLA for custom tasks
- **Customize voice**: Adjust TTS settings for different character voices
- **Optimize performance**: Tune settings for your hardware and network

## Additional Resources

- [Voice Integration Guide](VOICE_INTEGRATION_GUIDE.md) - Technical details
- [STT Service Guide](STT_SERVICE_GUIDE.md) - Speech-to-text implementation
- [TTS Service Guide](TTS_SERVICE_GUIDE.md) - Text-to-speech implementation
- [Quick Reference](QUICK_REFERENCE.md) - Common commands and workflows

## Support

For voice-related issues:

1. Check this guide's troubleshooting section
2. Enable debug logging: `LOG_LEVEL=DEBUG make run`
3. Review [Voice Integration Guide](VOICE_INTEGRATION_GUIDE.md)
4. Check browser console for errors
5. Verify API keys and credentials
