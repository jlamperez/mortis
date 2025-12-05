# Data Collection Setup Guide

This guide explains how to use the `DataCollector` class to set up and manage LeRobot datasets for training SmolVLA models.

## Overview

The `DataCollector` class provides infrastructure for working with LeRobot's native `lerobot-record` command:
- Generating `lerobot-record` commands for each task
- Creating executable shell scripts for data collection
- Tracking task descriptions and episode counts
- Managing dataset metadata
- Validating dataset integrity

**Important**: This module does NOT reimplement LeRobot's recording functionality. Instead, it provides helper utilities to make using `lerobot-record` easier for the Mortis project.

## Quick Start

### 1. Setup Dataset Infrastructure

**Option A: Interactive (default name)**
```bash
make setup-dataset
# Will prompt for dataset name (default: mortis_manipulation)
```

**Option B: With custom name**
```bash
make setup-dataset ARGS="--dataset-name=my_custom_dataset"
```

**Option C: Python API**
```python
from mortis.data_collector import DataCollector

# Create a dataset with custom name
collector = DataCollector(
    dataset_name="my_custom_dataset",
    repo_id="your-username/my_custom_dataset"
)

# Generate shell scripts for recording
collector.generate_all_record_scripts()

# Show recording instructions
collector.print_recording_instructions()
```

This will:
- Create the directory structure at `data/{dataset_name}/`
- Generate executable shell scripts for the 6 predefined tasks
- Display instructions for using `lerobot-record`

### 2. Record Episodes Using Generated Scripts

The easiest way to record episodes is to use the generated shell scripts:

```bash
# Set your Hugging Face username
export HF_USER=your-username

# Record episodes for a specific task
cd data/mortis_manipulation/scripts
./record_task_0.sh

# Or record all tasks sequentially
./record_all_tasks.sh
```

### 3. Manual Recording with lerobot-record

You can also run `lerobot-record` directly:

```bash
export HF_USER=your-username

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
    --dataset.single_task="Pick up the skull and place it in the green cup"
```

### 4. View Dataset Statistics

```python
# Print statistics to console
collector.print_statistics()

# Get statistics as a dictionary
stats = collector.get_dataset_statistics()
print(f"Total episodes: {stats['total_episodes']}")
```

### 5. Generate Custom Recording Commands

```python
# Generate a command for a specific task
cmd = collector.generate_record_command(
    task_description="Pick up the skull and place it in the green cup",
    num_episodes=10,
    episode_time_s=15,
    reset_time_s=20
)
print(cmd)
```

## Directory Structure

The DataCollector creates a minimal local structure:

```
data/
└── mortis_manipulation/
    └── scripts/               # Generated recording scripts
        ├── record_task_0.sh   # Individual task scripts
        ├── record_task_1.sh
        ├── ...
        └── record_all_tasks.sh # Master script for all tasks
```

**That's it!** No local metadata or episodes directories needed.

**Where is everything else?**
- **Episode data**: Uploaded directly to Hugging Face Hub by `lerobot-record`
- **Task definitions**: Hardcoded in the scripts (the 6 Mortis tasks)
- **Dataset URL**: `https://huggingface.co/datasets/{HF_USER}/mortis_manipulation`

This minimal approach means:
- ✅ No local storage needed (datasets can be 10-50 GB)
- ✅ No metadata to manage or sync
- ✅ Just generate scripts and start recording
- ✅ Everything managed by LeRobot

## Metadata Format

The `dataset_info.json` file contains:

```json
{
  "dataset_name": "mortis_manipulation",
  "repo_id": "your-username/mortis-manipulation",
  "created_at": 1234567890.0,
  "last_updated": 1234567890.0,
  "robot_type": "so101",
  "fps": 30,
  "tasks": {
    "task_0": {
      "description": "Pick up the skull and place it in the green cup",
      "episode_count": 5,
      "added_at": 1234567890.0
    }
  },
  "total_episodes": 30,
  "version": "1.0.0"
}
```

## Predefined Tasks

The default Mortis dataset includes 6 manipulation tasks:

1. Pick up the skull and place it in the green cup
2. Pick up the skull and place it in the orange cup
3. Pick up the skull and place it in the purple cup
4. Pick up the eyeball and place it in the green cup
5. Pick up the eyeball and place it in the orange cup
6. Pick up the eyeball and place it in the purple cup

## Advanced Usage

### Custom Dataset Names

You might want different dataset names for:
- **Testing**: `mortis_test`, `debug_dataset`
- **Versions**: `mortis_v1`, `mortis_v2`, `mortis_final`
- **Experiments**: `mortis_fast_motions`, `mortis_slow_motions`

**Command line:**
```bash
# Create a test dataset
make setup-dataset ARGS="--dataset-name=mortis_test"

# Create a versioned dataset
make setup-dataset ARGS="--dataset-name=mortis_v2"

# Specify both name and user
uv run setup-dataset --dataset-name=mortis_test --hf-user=myusername
```

**Python API:**
```python
from mortis.data_collector import DataCollector

# Create a custom dataset
collector = DataCollector(
    dataset_name="mortis_v2",
    repo_id="username/mortis_v2",
    root_dir="data"  # Optional: custom root directory
)

# Generate scripts
collector.generate_all_record_scripts()
```

### Export Summary

```python
# Export a human-readable summary
summary_file = collector.dataset_dir / "summary.txt"
collector.export_metadata_summary(summary_file)
```

### Get Episode Path

```python
# Get the path where episode data should be stored
episode_path = collector.get_episode_path(episode_index=0)
print(f"Episode 0 path: {episode_path}")
```

## Recording Workflow

1. **Setup**: Run the DataCollector to generate scripts
2. **Hardware**: Connect both leader (teleop) and follower (robot) arms
3. **Record**: Use the generated scripts or manual commands
4. **Verify**: Check that episodes are saved correctly
5. **Upload**: Push dataset to Hugging Face Hub (done automatically by lerobot-record)

## Environment Variables

Set these before recording:

```bash
export HF_USER=your-username          # Your Hugging Face username
export ROBOT_PORT=/dev/ttyACM1        # Follower robot USB port (optional)
```

## Camera Configuration

The default camera configuration uses:
- **camera1**: Intel RealSense (serial: 030522070314)
- **camera2**: OpenCV camera (index: 8)

Modify the camera configuration in `generate_record_command()` if your setup is different.

## Next Steps

After recording episodes:

1. **Verify Data**: Check that episodes are saved in the dataset directory
2. **Train SmolVLA Model** (Tasks 17-19): Use collected data for training
3. **Test Inference** (Task 20): Validate the trained model

## Requirements Satisfied

This implementation satisfies:
- **Requirement 4.1**: Data collection script for recording demonstrations
- **Requirement 4.3**: Dataset directory structure configuration
- **Requirement 4.4**: Task labeling support
- **Requirement 5.2**: Dataset metadata management

## API Reference

### DataCollector Class

#### `__init__(dataset_name, repo_id, root_dir="data")`
Initialize a new DataCollector.

#### `add_task(task_description, task_id=None) -> str`
Add a new task to the dataset.

#### `get_task_descriptions() -> Dict[str, str]`
Get all task descriptions.

#### `get_task_episode_count(task_id) -> int`
Get episode count for a specific task.

#### `increment_episode_count(task_id)`
Increment the episode count for a task.

#### `get_total_episodes() -> int`
Get total number of episodes across all tasks.

#### `get_dataset_statistics() -> Dict[str, Any]`
Get comprehensive dataset statistics.

#### `print_statistics()`
Print dataset statistics to console.

#### `validate_dataset() -> bool`
Validate dataset structure and metadata.

#### `initialize_predefined_tasks()`
Initialize with the 6 predefined Mortis tasks.

#### `export_metadata_summary(output_file=None) -> str`
Export a human-readable summary.

### Helper Functions

#### `create_mortis_dataset(dataset_name, repo_id) -> DataCollector`
Convenience function to create a DataCollector with predefined tasks.

## Testing

Run the module directly to test:

```bash
python -m mortis.data_collector
```

This will:
- Create a test dataset
- Initialize predefined tasks
- Print statistics
- Validate the dataset
- Export a summary
