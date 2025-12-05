# Quick Reference Guide

This guide provides quick access to common commands, workflows, and configurations for the Mortis project.

## Table of Contents

- [Installation & Setup](#installation--setup)
- [Running Mortis](#running-mortis)
- [Voice Interaction](#voice-interaction)
- [Robot Control](#robot-control)
- [Data Collection](#data-collection)
- [Training](#training)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

## Installation & Setup

### First-Time Setup

```bash
# 1. Clone repository
git clone https://github.com/jlamperez/mortis.git
cd mortis

# 2. Install dependencies
make install

# 3. Create .env file
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# 4. Calibrate robot (first time only)
make calibrate

# 5. Run Mortis
make run
```

### Quick Commands

```bash
make install          # Install/sync dependencies
make run              # Run Mortis web UI
make calibrate        # Calibrate robot arm
make check-env        # Verify environment configuration
make clean            # Remove build artifacts
```

## Running Mortis

### Basic Usage

```bash
# Run with default settings
make run

# Run with debug logging
LOG_LEVEL=DEBUG make run

# Run on custom port
PORT=8080 make run

# Run as Python module
make run-m
```

### Access the UI

- **URL**: http://127.0.0.1:7860
- **Dark Mode**: http://127.0.0.1:7860/?__theme=dark (recommended)

## Voice Interaction

### Setup Voice Features

```bash
# 1. Voice input (STT) - works out of the box with Gemini
# No additional setup required

# 2. Voice output (TTS) - optional Google Cloud setup
# Add to .env:
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# Or use free gTTS (automatic fallback)
# No setup required
```

### Using Voice

1. Click microphone icon in UI
2. Speak your message
3. Stop recording
4. Mortis transcribes, processes, and responds with voice

### Voice Configuration

```bash
# In .env file

# STT provider (default: gemini)
STT_PROVIDER=gemini  # or "google_stt"

# Logging for voice debugging
LOG_LEVEL=DEBUG
```

### Test Voice Pipeline

```bash
# Test complete voice-to-voice interaction
python -c "from mortis.tools import ask_mortis_with_voice; print(ask_mortis_with_voice('Hello Mortis', generate_audio=True))"
```

## Robot Control

### Calibration

```bash
# First-time calibration (required)
make calibrate

# Recalibrate if robot behaves incorrectly
rm -rf .cache/calibration/so101/
make calibrate
```

### Test Gestures

```bash
# Test a specific gesture
make test-gesture

# Edit src/mortis/robot.py to change gesture:
# mortis_arm.move_arm("wave")  # Options: idle, wave, point_left, point_right, grab, drop
```

### Available Gestures

- `idle` - Neutral resting position
- `wave` - Friendly greeting wave
- `point_left` - Point to the left
- `point_right` - Point to the right
- `grab` - Grabbing motion
- `drop` - Dropping/releasing motion

### Robot Configuration

```bash
# In .env file

# USB port (typically /dev/ttyACM0 or /dev/ttyACM1)
ROBOT_PORT=/dev/ttyACM1

# Check available ports
ls /dev/ttyACM*

# Fix permissions if needed
sudo chmod 666 /dev/ttyACM1
```

## Data Collection

### Setup Dataset

```bash
# Interactive setup (prompts for dataset name)
make setup-dataset

# With custom name
make setup-dataset ARGS="--dataset-name=my_dataset"

# Set Hugging Face username
export HF_USER=your-username
```

### Record Demonstrations

```bash
# Record individual tasks
cd data/mortis_manipulation/scripts
./record_task_0.sh  # Pick up skull → green cup
./record_task_1.sh  # Pick up skull → orange cup
# ... etc

# Or record all tasks sequentially
./record_all_tasks.sh
```

### Manual Recording

```bash
export HF_USER=your-username

lerobot-record \
    --robot.type=so101_follower \
    --robot.port=/dev/ttyACM1 \
    --teleop.type=so101_leader \
    --teleop.port=/dev/ttyACM0 \
    --dataset.repo_id=${HF_USER}/mortis_manipulation \
    --dataset.num_episodes=10 \
    --dataset.single_task="Pick up the skull and place it in the green cup"
```

### Dataset Configuration

```bash
# In .env file

# Your Hugging Face username
HF_USER=your-username
```

## Training

### Quick Training Workflow

```bash
# 1. Setup dataset (if not done)
make setup-dataset

# 2. Record demonstrations
cd data/mortis_manipulation/scripts
./record_all_tasks.sh

# 3. Generate training scripts
make setup-train ARGS="--dataset-repo-id your-username/mortis_manipulation --model-repo-id your-username/mortis-smolvla --generate-configs"

# 4. Start training
cd train
./train_standard.sh  # 20k steps (recommended)
```

### Training Scripts

```bash
cd train

# Quick test (1k steps, ~10 minutes)
./train_quick.sh

# Standard training (20k steps, ~3-4 hours)
./train_standard.sh

# Full training (100k steps, ~15-20 hours)
./train_full.sh
```

### Monitor Training

```bash
# Console output
# Watch terminal for loss, step, and checkpoint messages

# Weights & Biases (optional)
# 1. Add to .env: WANDB_API_KEY=your_key
# 2. Visit https://wandb.ai
# 3. View project: mortis-smolvla
```

### Training Configuration

```bash
# In .env file (optional)

# Weights & Biases API key
WANDB_API_KEY=your_wandb_key
```

### Use Trained Model

```bash
# In .env file

# Enable manipulation tasks
ENABLE_MANIPULATION=true

# Path to trained model checkpoint
SMOLVLA_CHECKPOINT_PATH=outputs/train/smolvla_standard/checkpoints/last

# Optional: specify device
SMOLVLA_DEVICE=cuda  # or "cpu"

# Manipulation timeout (seconds)
MANIPULATION_TIMEOUT=60.0
```

## Configuration

### Essential Environment Variables

```bash
# Required
GEMINI_API_KEY=your_google_api_key_here

# Optional - Gemini Configuration
GEMINI_MODEL=gemini-2.5-flash  # or gemini-1.5-pro
GEMINI_TEMPERATURE=0.2

# Optional - Robot Configuration
ROBOT_PORT=/dev/ttyACM1

# Optional - Voice Configuration
STT_PROVIDER=gemini
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# Optional - Application Configuration
PORT=7860
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Optional - Dataset Configuration
HF_USER=your-username

# Optional - SmolVLA Configuration
ENABLE_MANIPULATION=false
SMOLVLA_CHECKPOINT_PATH=checkpoints/smolvla_best
SMOLVLA_DEVICE=cuda
MANIPULATION_TIMEOUT=60.0
```

### Check Configuration

```bash
# Verify .env file exists and has required variables
make check-env

# View current configuration
cat .env
```

## Troubleshooting

### Quick Fixes

```bash
# Gemini API key error
echo "GEMINI_API_KEY=your_actual_key" >> .env

# Robot not connecting
ls /dev/ttyACM*
sudo chmod 666 /dev/ttyACM1
make calibrate

# Voice not working
LOG_LEVEL=DEBUG make run
# Check browser microphone permissions

# Training CUDA out of memory
# Edit train/train_standard.sh
# Change --batch_size=16 to --batch_size=8

# Dataset not found
echo "HF_USER=your-username" >> .env
cd data/mortis_manipulation/scripts
./record_all_tasks.sh
```

### Debug Mode

```bash
# Enable detailed logging
LOG_LEVEL=DEBUG make run

# Check specific component logs
# Look for:
# - "Gemini API" - API calls and responses
# - "STT" - Speech-to-text processing
# - "TTS" - Text-to-speech generation
# - "SmolVLA" - Manipulation inference
# - "AsyncExecutor" - Background task execution
```

### Common Issues

| Issue | Quick Fix |
|-------|-----------|
| API key not found | Add `GEMINI_API_KEY` to `.env` |
| Robot not connecting | Check USB port, run `make calibrate` |
| Voice input fails | Check browser permissions, verify API key |
| Audio not playing | Check `outputs/` directory permissions |
| Manipulation not working | Set `ENABLE_MANIPULATION=true`, verify checkpoint path |
| Training fails | Reduce batch size, check GPU availability |
| Dataset not found | Set `HF_USER`, verify dataset on HF Hub |

## Useful Commands

### Development

```bash
make install          # Install dependencies
make sync             # Sync dependencies (alias for install)
make upgrade          # Upgrade all dependencies
make lock             # Update uv.lock
make export           # Export requirements.txt
make clean            # Remove build artifacts
```

### Testing

```bash
make test-gesture     # Test robot gesture
make check-env        # Verify environment
python test_*.py      # Run specific test file
```

### Dataset & Training

```bash
make setup-dataset    # Setup dataset infrastructure
make setup-train      # Generate training scripts
```

### Adding Dependencies

```bash
make add-<package>    # Add new dependency
# Example:
make add-numpy
make add-pandas
```

## Example Workflows

### Complete Setup (First Time)

```bash
# 1. Install
git clone https://github.com/jlamperez/mortis.git
cd mortis
make install

# 2. Configure
cp .env.example .env
# Edit .env and add GEMINI_API_KEY

# 3. Calibrate robot
make calibrate

# 4. Run
make run
```

### Train Custom Manipulation Model

```bash
# 1. Setup dataset
make setup-dataset
export HF_USER=your-username

# 2. Record demonstrations
cd data/mortis_manipulation/scripts
./record_all_tasks.sh

# 3. Generate training scripts
cd ../..
make setup-train ARGS="--dataset-repo-id your-username/mortis_manipulation --generate-configs"

# 4. Train
cd train
./train_standard.sh

# 5. Enable in Mortis
echo "ENABLE_MANIPULATION=true" >> .env
echo "SMOLVLA_CHECKPOINT_PATH=outputs/train/smolvla_standard/checkpoints/last" >> .env

# 6. Run with manipulation
make run
```

### Voice-Only Interaction

```bash
# 1. Ensure Gemini API key is set
grep GEMINI_API_KEY .env

# 2. Optional: Setup Google Cloud TTS
echo "GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json" >> .env

# 3. Run Mortis
make run

# 4. Use microphone in UI
# Click mic → speak → stop → listen to response
```

## Performance Tips

- **Faster responses**: Use `gemini-2.5-flash` (default)
- **Better quality**: Use `gemini-1.5-pro` (slower)
- **Reduce voice latency**: Use gTTS instead of Google Cloud TTS
- **GPU optimization**: Ensure CUDA is installed for SmolVLA
- **Reduce training time**: Use `train_quick.sh` for testing

## Additional Resources

### Documentation
- [README.md](../README.md) - Main documentation
- [Voice Integration Guide](VOICE_INTEGRATION_GUIDE.md)
- [Training Guide](TRAINING_GUIDE.md)
- [Data Collection Setup](DATA_COLLECTION_SETUP.md)
- [Gemini Setup](GEMINI_SETUP.md)

### External Links
- [Google AI Studio](https://aistudio.google.com/app/apikey) - Get Gemini API key
- [Hugging Face](https://huggingface.co) - Datasets and models
- [LeRobot](https://github.com/huggingface/lerobot) - Robotics framework
- [Weights & Biases](https://wandb.ai) - Training monitoring

## Getting Help

1. Check this quick reference
2. Review detailed documentation in `docs/`
3. Enable debug logging: `LOG_LEVEL=DEBUG make run`
4. Check LeRobot documentation
5. Verify environment: `make check-env`
