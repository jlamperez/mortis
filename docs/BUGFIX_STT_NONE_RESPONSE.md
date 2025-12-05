# Bug Fix: STT Service None Response Handling

## Issue Description

**Date**: December 3, 2024  
**Severity**: High  
**Component**: `src/mortis/stt_service.py`

### Problem
The STT service was crashing with an `AttributeError` when Gemini's transcription API returned `None` instead of text:

```
AttributeError: 'NoneType' object has no attribute 'strip'
```

### Error Log
```
22:19:57 - mortis.stt_service - ERROR - Gemini transcription failed: AttributeError: 'NoneType' object has no attribute 'strip'
22:19:57 - mortis.stt_service - WARNING - Primary STT provider (gemini) failed: 'NoneType' object has no attribute 'strip'
```

### Root Cause
In the `_transcribe_with_gemini()` method, the code assumed `response.text` would always return a string:

```python
# Old code (buggy)
transcript = response.text.strip()
```

However, Gemini's API can return `None` for `response.text` in certain scenarios:
- Audio file is empty or silent
- Audio format is not properly recognized
- API response doesn't contain text content
- Audio quality is too poor to transcribe

## Solution

### Code Changes
Added null checking before calling `.strip()`:

```python
# New code (fixed)
if response.text is None:
    logger.warning("Gemini returned None for transcription")
    logger.debug(f"Response object: {response}")
    # Check if there are candidates with parts
    if hasattr(response, 'candidates') and response.candidates:
        logger.debug(f"Response has {len(response.candidates)} candidates")
        for i, candidate in enumerate(response.candidates):
            logger.debug(f"Candidate {i}: {candidate}")
    transcript = ""
else:
    transcript = response.text.strip()

if transcript:
    logger.info(f"Gemini transcription successful: '{transcript[:50]}...'")
else:
    logger.warning("Gemini transcription returned empty result")
```

### Benefits
1. **No more crashes**: Gracefully handles None responses
2. **Better logging**: Debug information helps diagnose why transcription failed
3. **User feedback**: Returns empty string instead of crashing
4. **Fallback support**: Allows fallback to Google STT to work properly

## Testing

### Test Cases
1. **Empty audio file** → Returns empty string, no crash
2. **Silent audio** → Returns empty string, no crash
3. **Valid audio** → Returns transcription as before
4. **Invalid format** → Caught earlier by format validation

### Verification
Run with debug logging to see detailed response information:
```bash
LOG_LEVEL=DEBUG make run
```

## Impact

### Before Fix
- Application crashed on None response
- User saw error message
- Fallback to Google STT also failed due to exception
- Poor user experience

### After Fix
- Application handles None gracefully
- User sees empty transcription (can retry)
- Fallback to Google STT can work if configured
- Better user experience

## Related Issues

### Potential Causes of None Response
1. **Audio Quality**: Poor quality audio may not be transcribable
2. **Audio Length**: Very short audio (< 0.5s) may return None
3. **Silence**: Audio with only silence returns None
4. **Format Issues**: Some audio formats may not be fully supported
5. **API Limitations**: Gemini may have limitations on certain audio types

### Recommendations
1. **Validate audio duration**: Check audio is at least 0.5 seconds
2. **Check audio levels**: Ensure audio has sufficient volume
3. **Improve UI feedback**: Show "No speech detected" vs "Transcription failed"
4. **Add retry logic**: Allow user to easily retry recording
5. **Consider local STT**: For better reliability with edge cases

## Future Enhancements

### Short-term
- [ ] Add audio duration validation before transcription
- [ ] Add audio level/volume checking
- [ ] Improve error messages for different failure modes
- [ ] Add retry button in UI

### Long-term
- [ ] Implement local Whisper model for offline/fallback
- [ ] Add voice activity detection (VAD) to filter silence
- [ ] Add audio preprocessing (noise reduction, normalization)
- [ ] Support streaming transcription for real-time feedback

## Documentation Updates

Updated files:
- `src/mortis/stt_service.py` - Added null checking and debug logging
- `docs/AUDIO_INPUT_GUIDE.md` - Already includes troubleshooting for empty transcription

## Deployment Notes

### No Breaking Changes
This is a bug fix with no API changes. Safe to deploy immediately.

### Monitoring
Watch for:
- Frequency of empty transcriptions
- Patterns in audio files that return None
- User retry behavior after empty transcription

### Rollback Plan
If issues arise, revert commit. However, this fix only adds safety checks, so rollback should not be necessary.

## Conclusion

This bug fix improves the robustness of the STT service by properly handling None responses from Gemini's transcription API. The fix prevents crashes, provides better logging for debugging, and enables the fallback mechanism to work correctly.

**Status**: ✅ Fixed and tested  
**Priority**: High (prevents crashes)  
**Risk**: Low (only adds safety checks)
