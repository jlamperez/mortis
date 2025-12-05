# Recording Guide: Collecting Demonstration Data

This guide walks you through the process of recording demonstration episodes for training the SmolVLA model.

## Prerequisites

### Hardware Setup

You need:
1. **Leader Arm** (SO101): For teleoperation (controlling the robot)
2. **Follower Arm** (SO101): The robot that will be trained
3. **Cameras**:
   - Intel RealSense camera (serial: 030522070314)
   - OpenCV-compatible camera (index: 8)
4. **USB Connections**: Both arms connected to your computer

### Software Setup

1. Install dependencies:
   ```bash
   make install
   ```

2. Login to Hugging Face (required for uploading datasets):
   ```bash
   huggingface-cli login
   ```
   
   This will prompt you for your Hugging Face token. Get it from: https://huggingface.co/settings/tokens

3. Configure your Hugging Face username in `.env`:
   ```bash
   # Add to .env file
   echo "HF_USER=your-username" >> .env
   ```
   
   The setup script will automatically load this from your `.env` file.

4. Calibrate both robot arms (if not already done):
   ```bash
   make calibrate
   ```

## Quick Start

### 1. Setup Dataset Infrastructure

Run the setup command to create the dataset structure and generate recording scripts:

```bash
make setup-dataset
```

This will:
- Create `data/mortis_manipulation/` directory
- Generate recording scripts for all 6 tasks
- Display instructions for recording

### 2. Navigate to Scripts Directory

```bash
cd data/mortis_manipulation/scripts
```

### 3. Record Episodes

#### Option A: Record One Task at a Time

```bash
# Record task 0: Pick up the skull and place it in the green cup
./record_task_0.sh
```

#### Option B: Record All Tasks Sequentially

```bash
# This will record all 6 tasks one after another
./record_all_tasks.sh
```

## Recording Process

When you run a recording script, LeRobot will:

1. **Initialize**: Connect to both robot arms and cameras
2. **Display**: Show camera feeds and robot state
3. **Wait for Reset**: Give you time to position objects (20 seconds default)
4. **Record**: Capture your demonstration (15 seconds default)
5. **Repeat**: Continue for the specified number of episodes (10 default)
6. **Upload**: Automatically push data to Hugging Face Hub

### During Recording

- **Control the leader arm** to demonstrate the task
- The **follower arm will mirror** your movements
- **Cameras record** the visual observations
- **Robot state is logged** at 30 FPS

### Controls

- **Space**: Start/stop recording
- **Ctrl+C**: Exit recording session
- **R**: Re-record last episode

### Recording Multiple Tasks

The scripts are designed to work together:
- ✅ **First task** (`task_0`): Creates the dataset (NO `--resume` flag)
- ✅ **Subsequent tasks** (`task_1`, `task_2`, ...): Add to existing dataset (WITH `--resume=true`)
- ✅ All tasks end up in the same dataset: `{HF_USER}/mortis_manipulation`

**Important**: Always run `task_0` first to create the dataset. Then you can run other tasks in any order.

## The 6 Predefined Tasks

1. **task_0**: Pick up the skull and place it in the green cup
2. **task_1**: Pick up the skull and place it in the orange cup
3. **task_2**: Pick up the skull and place it in the purple cup
4. **task_3**: Pick up the eyeball and place it in the green cup
5. **task_4**: Pick up the eyeball and place it in the orange cup
6. **task_5**: Pick up the eyeball and place it in the purple cup

## Recommended Recording Strategy

### Episodes Per Task

Record **10-15 episodes per task** for good performance:
- Minimum: 5 episodes (may underfit)
- Recommended: 10-15 episodes (good balance)
- Maximum: 20+ episodes (diminishing returns)

### Demonstration Quality

For best results:
- **Smooth motions**: Avoid jerky movements
- **Consistent approach**: Use similar paths for each episode
- **Clear visibility**: Ensure objects are visible to cameras
- **Complete tasks**: Finish each demonstration successfully
- **Vary slightly**: Small variations help generalization

### Recording Order

1. Start with **easier tasks** (e.g., task_0)
2. Get comfortable with the teleoperation
3. Record **multiple episodes** before moving to next task
4. Take breaks between tasks to avoid fatigue

## Customizing Recording Parameters

Edit the generated scripts to change parameters:

```bash
# Edit a task script
nano record_task_0.sh
```

Common parameters to adjust:

- `--dataset.num_episodes=10`: Number of episodes to record
- `--dataset.episode_time_s=15`: Maximum time per episode
- `--dataset.reset_time_s=20`: Time to reset between episodes
- `--robot.port=/dev/ttyACM1`: Follower robot USB port
- `--teleop.port=/dev/ttyACM0`: Leader robot USB port

## Manual Recording Command

If you prefer to run `lerobot-record` directly (HF_USER will be loaded from `.env`):

```bash
lerobot-record \
    --robot.type=so101_follower \
    --robot.port=/dev/ttyACM1 \
    --robot.id=my_awesome_follower_arm \
    --robot.cameras="{ camera1: {type: intelrealsense, serial_number_or_name: '030522070314', width: 640, height: 480, fps: 30}, camera2: {type: opencv, index_or_path: 8, width: 640, height: 480, fps: 30}}" \
    --teleop.type=so101_leader \
    --teleop.port=/dev/ttyACM0 \
    --teleop.id=my_awesome_leader_arm \
    --display_data=true \
    --dataset.repo_id=${HF_USER}/mortis_manipulation \
    --dataset.num_episodes=10 \
    --dataset.episode_time_s=15 \
    --dataset.reset_time_s=20 \
    --dataset.single_task="Pick up the skull and place it in the green cup" \
    --resume=true
```

**Important**: The `--resume=true` flag tells LeRobot to add episodes to an existing dataset. This allows you to record multiple tasks sequentially into the same dataset.

## Troubleshooting

### Robot Not Connecting

```bash
# Check USB connections
ls /dev/ttyACM*

# Should show /dev/ttyACM0 and /dev/ttyACM1
```

If ports are different, update the scripts or set environment variable:
```bash
export ROBOT_PORT=/dev/ttyACM2  # or whatever port your robot is on
```

### Camera Not Found

```bash
# List available cameras
v4l2-ctl --list-devices

# For RealSense
rs-enumerate-devices
```

Update camera configuration in the scripts if needed.

### Permission Denied

```bash
# Add your user to dialout group for USB access
sudo usermod -a -G dialout $USER

# Log out and back in for changes to take effect
```

### Recording Fails Mid-Episode

- Check USB cable connections
- Ensure sufficient disk space
- Verify Hugging Face authentication: `huggingface-cli whoami`
  - If not logged in, run: `huggingface-cli login`
  - Get your token from: https://huggingface.co/settings/tokens

## Verifying Recorded Data

After recording, your data is automatically uploaded to Hugging Face Hub.

**Check your dataset online:**
```
https://huggingface.co/datasets/{HF_USER}/mortis_manipulation
```

Replace `{HF_USER}` with your Hugging Face username.

**What's in the dataset:**
- `observation.images.camera1/`: RealSense images
- `observation.images.camera2/`: OpenCV camera images  
- `observation.state`: Robot joint positions
- `action`: Robot actions (next state)
- Episode metadata and task descriptions

**Download for training (optional):**
```python
from lerobot.common.datasets.lerobot_dataset import LeRobotDataset

# Downloads from Hugging Face automatically
dataset = LeRobotDataset("your-username/mortis_manipulation")
```

## Next Steps

After recording all tasks:

1. **Verify Data Quality**: Review recorded episodes
2. **Train SmolVLA Model**: Use the collected data for training
3. **Test Inference**: Validate the trained model

See the training documentation for next steps.

## Tips for Success

✅ **DO**:
- Practice teleoperation before recording
- Record in good lighting conditions
- Keep workspace clear of obstacles
- Record multiple episodes per task
- Take breaks to maintain quality

❌ **DON'T**:
- Rush through demonstrations
- Record with poor camera visibility
- Use inconsistent object positions
- Record when tired or distracted
- Skip calibration steps

## Dataset Statistics

Track your progress:

```python
from mortis.data_collector import DataCollector

collector = DataCollector("mortis_manipulation", "your-username/mortis_manipulation")
collector.print_statistics()
```

## Support

For issues or questions:
- Check LeRobot documentation: https://github.com/huggingface/lerobot
- Review this guide's troubleshooting section
- Check camera and robot connections

Happy recording! 🎥🤖
