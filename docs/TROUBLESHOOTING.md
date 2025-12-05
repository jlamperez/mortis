# Troubleshooting Guide

This guide helps you diagnose and fix common issues with the Mortis system.

## Table of Contents

- [Setup Issues](#setup-issues)
- [API and Authentication](#api-and-authentication)
- [Robot Connection](#robot-connection)
- [Voice Interaction](#voice-interaction)
- [Manipulation Tasks](#manipulation-tasks)
- [Training Issues](#training-issues)
- [Performance Problems](#performance-problems)
- [UI and Display](#ui-and-display)
- [Debugging Tools](#debugging-tools)

## Setup Issues

### "Command not found: make"

**Problem**: `make` is not installed on your system.

**Solution**:
```bash
# Ubuntu/Debian
sudo apt-get install build-essential

# macOS (install Xcode Command Line Tools)
xcode-select --install

# Or run commands directly without make
uv run python -m mortis.app
```

### "Command not found: uv"

**Problem**: `uv` package manager is not installed.

**Solution**:
```bash
# Install uv
pip install uv

# Or use pip directly
pip install -e .
```

### "Python version mismatch"

**Problem**: Python version is below 3.12.

**Solution**:
```bash
# Check Python version
python --version

# Install Python 3.12+ using your system's package manager
# Ubuntu/Debian
sudo apt-get install python3.12

# macOS (using Homebrew)
brew install python@3.12

# Or use pyenv
pyenv install 3.12.0
pyenv local 3.12.0
```

### "Dependencies not installing"

**Problem**: `uv sync` or `make install` fails.

**Solution**:
```bash
# Clear cache and retry
rm -rf .venv
uv cache clean
uv sync

# If still failing, check for specific error messages
uv sync --verbose

# Try with pip as fallback
pip install -e .
```

## API and Authentication

### "Gemini API key not found"

**Problem**: `GEMINI_API_KEY` is not set in `.env` file.

**Solution**:
```bash
# 1. Get API key from https://aistudio.google.com/app/apikey
# 2. Create or edit .env file
echo "GEMINI_API_KEY=your_actual_api_key_here" >> .env

# 3. Verify it's set
grep GEMINI_API_KEY .env

# 4. Restart Mortis
make run
```

### "Invalid API key"

**Problem**: Gemini API key is incorrect or expired.

**Solution**:
```bash
# 1. Verify key format (should be a long alphanumeric string)
cat .env | grep GEMINI_API_KEY

# 2. Generate new key at https://aistudio.google.com/app/apikey
# 3. Update .env with new key
# 4. Restart Mortis
```

### "Rate limit exceeded"

**Problem**: Too many API requests in a short time.

**Solution**:
```bash
# The system automatically retries with exponential backoff
# Wait a few seconds and try again

# To reduce rate limiting:
# 1. Reduce request frequency
# 2. Check for infinite loops in code
# 3. Consider upgrading API quota
```

### "Blocked prompt"

**Problem**: Gemini API blocked the prompt due to safety filters.

**Solution**:
```bash
# The system automatically provides a fallback response
# To avoid blocks:
# 1. Rephrase your message
# 2. Avoid sensitive topics
# 3. Keep messages appropriate

# Check logs for details
LOG_LEVEL=DEBUG make run
```

## Robot Connection

### "Robot not connecting"

**Problem**: SO101 arm not detected on USB port.

**Solution**:
```bash
# 1. Check USB connection
ls /dev/ttyACM*
# Should show /dev/ttyACM0 or /dev/ttyACM1

# 2. Check which port the robot is on
dmesg | grep tty
# Look for recent USB device connections

# 3. Update ROBOT_PORT in .env
echo "ROBOT_PORT=/dev/ttyACM0" >> .env

# 4. Check permissions
ls -l /dev/ttyACM1
# Should show read/write permissions

# 5. Fix permissions if needed
sudo chmod 666 /dev/ttyACM1
# Or add user to dialout group (permanent fix)
sudo usermod -a -G dialout $USER
# Then log out and back in

# 6. Recalibrate
make calibrate
```

### "Robot moves erratically"

**Problem**: Robot movements are jerky or incorrect.

**Solution**:
```bash
# 1. Recalibrate the robot
rm -rf .cache/calibration/so101/
make calibrate

# 2. Check power supply
# Ensure robot has adequate power

# 3. Check for loose connections
# Verify all servo cables are secure

# 4. Test individual gestures
make test-gesture
# Edit src/mortis/robot.py to test different gestures
```

### "Calibration fails"

**Problem**: Calibration process doesn't complete.

**Solution**:
```bash
# 1. Ensure robot is connected
ls /dev/ttyACM*

# 2. Check robot is powered on
# Verify power LED is lit

# 3. Try different USB port
# Some ports may have power issues

# 4. Run calibration with verbose output
uv run python -m mortis.calibrate

# 5. Check for error messages
# Follow on-screen instructions carefully
```

### "Robot doesn't move"

**Problem**: Robot is connected but doesn't execute gestures.

**Solution**:
```bash
# 1. Check if robot is in idle mode
# Look for "Robot connected" message in logs

# 2. Verify calibration exists
ls .cache/calibration/so101/
# Should show calibration files

# 3. Test with simple gesture
make test-gesture

# 4. Check logs for errors
LOG_LEVEL=DEBUG make run
# Look for robot-related error messages

# 5. Restart Mortis
# Sometimes connection needs to be reestablished
```

## Voice Interaction

### "Microphone not accessible"

**Problem**: Browser can't access microphone.

**Solution**:
```bash
# 1. Check browser permissions
# Chrome: Settings → Privacy and security → Site settings → Microphone
# Firefox: Preferences → Privacy & Security → Permissions → Microphone
# Allow access for localhost

# 2. Check system microphone
# Ensure microphone is not muted in system settings

# 3. Test microphone
# Use browser's built-in microphone test
# Or test with another application

# 4. Try different browser
# Chrome and Firefox have best support

# 5. Restart browser after granting permissions
```

### "Voice input not transcribing"

**Problem**: Speech is not converted to text.

**Solution**:
```bash
# 1. Check Gemini API key
grep GEMINI_API_KEY .env

# 2. Enable debug logging
LOG_LEVEL=DEBUG make run
# Look for STT-related errors

# 3. Check audio format
# Ensure browser is recording in supported format

# 4. Try fallback STT provider
echo "STT_PROVIDER=google_stt" >> .env
echo "GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json" >> .env

# 5. Test with shorter audio
# Keep recordings under 10 seconds
```

### "Audio output not playing"

**Problem**: Mortis's voice doesn't play.

**Solution**:
```bash
# 1. Check browser audio
# Ensure browser is not muted
# Check system volume

# 2. Check outputs directory
ls -la outputs/
# Should show .mp3 files

# 3. Verify TTS service
LOG_LEVEL=DEBUG make run
# Look for "TTS generation" messages

# 4. Check file permissions
chmod 755 outputs/
chmod 644 outputs/*.mp3

# 5. Try playing audio file directly
# Open outputs/mortis_response_*.mp3 in media player
```

### "Poor transcription quality"

**Problem**: Speech is transcribed incorrectly.

**Solution**:
```bash
# 1. Reduce background noise
# Use quiet room
# Close windows, turn off fans

# 2. Speak more clearly
# Normal pace, clear pronunciation
# Avoid mumbling or speaking too fast

# 3. Use better microphone
# External USB microphone
# Headset with mic

# 4. Check microphone settings
# Adjust input volume in system settings
# Ensure microphone is not too far away

# 5. Try shorter messages
# Keep under 10 seconds for best results
```

### "High voice latency"

**Problem**: Long delays between speaking and response.

**Solution**:
```bash
# 1. Check internet speed
# Gemini API requires good connection
# Test with speedtest.net

# 2. Use faster model
echo "GEMINI_MODEL=gemini-2.5-flash" >> .env

# 3. Use local TTS
# Remove GOOGLE_APPLICATION_CREDENTIALS from .env
# System will use gTTS (faster)

# 4. Reduce audio length
# Keep messages under 10 seconds

# 5. Check system resources
# Close other applications
# Ensure CPU/memory not maxed out
```

## Manipulation Tasks

### "Manipulation not working"

**Problem**: SmolVLA tasks don't execute.

**Solution**:
```bash
# 1. Check if manipulation is enabled
grep ENABLE_MANIPULATION .env
# Should be "true"

# 2. Verify checkpoint path exists
ls outputs/train/smolvla_standard/checkpoints/last/
# Should show model files

# 3. Update .env configuration
echo "ENABLE_MANIPULATION=true" >> .env
echo "SMOLVLA_CHECKPOINT_PATH=outputs/train/smolvla_standard/checkpoints/last" >> .env

# 4. Check GPU availability
python -c "import torch; print(torch.cuda.is_available())"
# Should print "True" for GPU

# 5. Restart Mortis
make run
```

### "Model not loading"

**Problem**: SmolVLA model fails to load.

**Solution**:
```bash
# 1. Verify checkpoint path
ls -la $SMOLVLA_CHECKPOINT_PATH
# Should show pretrained_model.safetensors or similar

# 2. Check model format
# Ensure checkpoint is from LeRobot training

# 3. Check GPU memory
nvidia-smi
# Ensure sufficient VRAM available

# 4. Try CPU inference
echo "SMOLVLA_DEVICE=cpu" >> .env

# 5. Check logs for specific error
LOG_LEVEL=DEBUG make run
# Look for model loading errors
```

### "Manipulation tasks timeout"

**Problem**: Tasks don't complete within timeout.

**Solution**:
```bash
# 1. Increase timeout
echo "MANIPULATION_TIMEOUT=90.0" >> .env

# 2. Check task complexity
# Some tasks may need more time

# 3. Verify robot can reach objects
# Ensure physical setup matches training

# 4. Check camera view
# Ensure objects are visible to camera

# 5. Monitor execution
# Watch robot during task
# Look for stuck or repeated motions
```

### "Robot executes wrong task"

**Problem**: Robot performs incorrect manipulation.

**Solution**:
```bash
# 1. Verify command matches training
# Use exact task strings from training

# 2. Check model training
# Ensure model was trained on this task

# 3. Verify physical setup
# Objects, cups, camera positions should match training

# 4. Retrain model
# Collect more demonstrations
# Train with more steps

# 5. Check intent detection
LOG_LEVEL=DEBUG make run
# Verify correct task string is extracted
```

## Training Issues

### "CUDA out of memory"

**Problem**: GPU doesn't have enough memory for training.

**Solution**:
```bash
# 1. Reduce batch size
# Edit train/train_standard.sh
# Change --batch_size=16 to --batch_size=8 or --batch_size=4

# 2. Use gradient accumulation
# Add to training command:
# --gradient_accumulation_steps=2

# 3. Clear GPU memory
nvidia-smi
# Kill other GPU processes if needed

# 4. Use smaller model
# Reduce image resolution in dataset config

# 5. Use CPU training (slow)
# Edit training script, change --policy.device=cuda to --policy.device=cpu
```

### "Dataset not found"

**Problem**: Training can't find dataset.

**Solution**:
```bash
# 1. Verify dataset on Hugging Face
# Visit https://huggingface.co/datasets/your-username/dataset-name

# 2. Check HF_USER is set
echo $HF_USER
# Should match your Hugging Face username

# 3. Verify dataset repo ID in training script
# Should be: your-username/dataset-name

# 4. Re-record episodes if needed
cd data/mortis_manipulation/scripts
./record_all_tasks.sh

# 5. Check Hugging Face authentication
huggingface-cli whoami
# Should show your username
```

### "Training not starting"

**Problem**: Training script fails to start.

**Solution**:
```bash
# 1. Check CUDA installation
python -c "import torch; print(torch.cuda.is_available())"

# 2. Verify LeRobot installation
python -c "import lerobot; print(lerobot.__version__)"

# 3. Check training script permissions
chmod +x train/train_standard.sh

# 4. Run with verbose output
cd train
bash -x ./train_standard.sh

# 5. Check for missing dependencies
uv sync
```

### "Training loss not decreasing"

**Problem**: Model is not learning.

**Solution**:
```bash
# 1. Check learning rate
# May be too high or too low
# Edit training script, adjust --lr parameter

# 2. Verify dataset quality
# Ensure demonstrations are consistent
# Check for corrupted episodes

# 3. Increase training steps
# Use train_full.sh instead of train_standard.sh

# 4. Check data augmentation
# Ensure image transforms are enabled

# 5. Monitor with W&B
# Visit https://wandb.ai
# Check loss curves and metrics
```

### "Checkpoints not saving"

**Problem**: Model checkpoints are not being saved.

**Solution**:
```bash
# 1. Check output directory permissions
ls -la outputs/train/
chmod 755 outputs/train/

# 2. Verify save_freq in training script
# Should have --save_freq=5000 or similar

# 3. Check disk space
df -h
# Ensure sufficient space for checkpoints

# 4. Check logs for save errors
# Look for "Checkpoint saved" messages

# 5. Manually save checkpoint
# Training script should save at intervals
```

## Performance Problems

### "Slow response times"

**Problem**: Mortis takes too long to respond.

**Solution**:
```bash
# 1. Use faster Gemini model
echo "GEMINI_MODEL=gemini-2.5-flash" >> .env

# 2. Check internet speed
# Slow connection affects API calls

# 3. Reduce temperature
echo "GEMINI_TEMPERATURE=0.1" >> .env
# Lower temperature = faster generation

# 4. Use local TTS
# Remove GOOGLE_APPLICATION_CREDENTIALS
# gTTS is faster than Google Cloud TTS

# 5. Check system resources
top
# Ensure CPU/memory not maxed out
```

### "High CPU usage"

**Problem**: Mortis uses too much CPU.

**Solution**:
```bash
# 1. Check for infinite loops
LOG_LEVEL=DEBUG make run
# Look for repeated operations

# 2. Reduce polling frequency
# Edit app.py, increase status check interval

# 3. Close other applications
# Free up CPU resources

# 4. Use GPU for inference
echo "SMOLVLA_DEVICE=cuda" >> .env

# 5. Monitor with htop
htop
# Identify specific processes using CPU
```

### "High memory usage"

**Problem**: Mortis uses too much RAM.

**Solution**:
```bash
# 1. Restart Mortis periodically
# Memory leaks may accumulate

# 2. Reduce batch size (if training)
# Edit training script

# 3. Clear audio file cache
rm outputs/*.mp3

# 4. Check for memory leaks
# Monitor memory usage over time

# 5. Use smaller model
# Reduce model size or use CPU inference
```

### "GPU memory issues"

**Problem**: GPU runs out of memory.

**Solution**:
```bash
# 1. Check GPU memory usage
nvidia-smi

# 2. Clear GPU cache
python -c "import torch; torch.cuda.empty_cache()"

# 3. Reduce batch size (training)
# Edit training script

# 4. Use CPU for inference
echo "SMOLVLA_DEVICE=cpu" >> .env

# 5. Close other GPU applications
# Kill other processes using GPU
```

## UI and Display

### "UI not loading"

**Problem**: Gradio interface doesn't appear.

**Solution**:
```bash
# 1. Check if server is running
# Look for "Running on local URL" message

# 2. Verify port is not in use
lsof -i :7860
# Kill process if port is occupied

# 3. Try different port
PORT=8080 make run

# 4. Check firewall settings
# Ensure port is not blocked

# 5. Try different browser
# Chrome and Firefox have best support
```

### "Webcam not showing"

**Problem**: Camera feed doesn't display.

**Solution**:
```bash
# 1. Check camera permissions
# Allow camera access in browser

# 2. Verify camera is connected
ls /dev/video*
# Should show video devices

# 3. Test camera
# Use cheese or other camera app

# 4. Check camera index
# Edit app.py if using different camera

# 5. Restart browser
# Sometimes camera needs reinitialization
```

### "Dark theme not applying"

**Problem**: UI shows light theme instead of dark.

**Solution**:
```bash
# 1. Use dark theme URL
# http://127.0.0.1:7860/?__theme=dark

# 2. Clear browser cache
# Ctrl+Shift+Delete in most browsers

# 3. Try incognito/private mode
# Rules out cache issues

# 4. Check CSS in app.py
# Verify dark theme CSS is present
```

### "Chat history not showing"

**Problem**: Previous messages don't appear.

**Solution**:
```bash
# 1. Refresh page
# Chat history is session-based

# 2. Check browser console
# F12 → Console tab
# Look for JavaScript errors

# 3. Clear browser cache
# May have cached old version

# 4. Restart Mortis
# Reinitialize Gradio interface
```

## Debugging Tools

### Enable Debug Logging

```bash
# Set in .env file
LOG_LEVEL=DEBUG

# Or run with environment variable
LOG_LEVEL=DEBUG make run

# View logs in real-time
tail -f logs/mortis.log
```

### Check Environment Configuration

```bash
# Verify all required variables
make check-env

# View current configuration
cat .env

# Test specific components
python -c "from mortis.gemini_client import GeminiClient; print('OK')"
python -c "from mortis.stt_service import get_stt_service; print('OK')"
python -c "from mortis.tts_service import get_tts_service; print('OK')"
```

### Monitor System Resources

```bash
# CPU and memory
top
# or
htop

# GPU usage
nvidia-smi
# or continuous monitoring
watch -n 1 nvidia-smi

# Disk space
df -h

# Network
iftop
```

### Test Individual Components

```bash
# Test Gemini API
python -c "from mortis.gemini_client import GeminiClient; c = GeminiClient(); print(c.send_message('Hello'))"

# Test STT
python -c "from mortis.stt_service import get_stt_service; s = get_stt_service(); print('STT OK')"

# Test TTS
python -c "from mortis.tts_service import get_tts_service; t = get_tts_service(); print('TTS OK')"

# Test robot connection
python -c "from mortis.robot import MortisArm; m = MortisArm(); m.connect(); print('Robot OK')"
```

### Check Logs

```bash
# View recent logs
tail -n 100 logs/mortis.log

# Search for errors
grep ERROR logs/mortis.log

# Search for specific component
grep "Gemini" logs/mortis.log
grep "STT" logs/mortis.log
grep "TTS" logs/mortis.log
grep "SmolVLA" logs/mortis.log
```

### Validate Installation

```bash
# Check Python version
python --version

# Check installed packages
uv pip list

# Verify LeRobot
python -c "import lerobot; print(lerobot.__version__)"

# Verify PyTorch
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"

# Verify Gradio
python -c "import gradio; print(gradio.__version__)"
```

## Getting Additional Help

If you've tried the solutions above and still have issues:

1. **Enable debug logging**: `LOG_LEVEL=DEBUG make run`
2. **Check all documentation**:
   - [README.md](../README.md)
   - [Quick Reference](QUICK_REFERENCE.md)
   - [Voice Integration Guide](VOICE_INTEGRATION_GUIDE.md)
   - [Training Guide](TRAINING_GUIDE.md)
3. **Review error messages carefully**: Often contain specific solutions
4. **Check LeRobot documentation**: https://github.com/huggingface/lerobot
5. **Verify environment**: `make check-env`
6. **Try minimal setup**: Start with basic features, add complexity gradually

## Common Error Messages

### "ModuleNotFoundError: No module named 'X'"

**Solution**: Run `uv sync` or `make install`

### "PermissionError: [Errno 13] Permission denied"

**Solution**: Check file/directory permissions, use `chmod` to fix

### "ConnectionError: Failed to connect to API"

**Solution**: Check internet connection, verify API key

### "RuntimeError: CUDA out of memory"

**Solution**: Reduce batch size, clear GPU cache, or use CPU

### "FileNotFoundError: [Errno 2] No such file or directory"

**Solution**: Check file paths, ensure files exist, verify working directory

### "ValueError: Invalid configuration"

**Solution**: Check .env file, verify all required variables are set

## Prevention Tips

1. **Keep dependencies updated**: Run `make upgrade` periodically
2. **Monitor logs**: Check for warnings before they become errors
3. **Test incrementally**: Verify each component works before combining
4. **Backup configurations**: Keep copies of working .env files
5. **Document changes**: Note what works and what doesn't
6. **Use version control**: Track changes to code and configs
7. **Regular calibration**: Recalibrate robot if behavior changes
8. **Clean up regularly**: Remove old logs, audio files, checkpoints
