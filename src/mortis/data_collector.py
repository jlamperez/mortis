"""
Data collection helper for LeRobot dataset recording.

This module provides utilities for generating lerobot-record commands
and scripts for the 6 predefined Mortis manipulation tasks.

All episode data is managed by LeRobot and uploaded directly to Hugging Face Hub.
This module only generates helper scripts - no local data storage or tracking.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


# Predefined Mortis manipulation tasks
MORTIS_TASKS = [
    "Pick up the skull and place it in the green cup",
    "Pick up the skull and place it in the orange cup",
    "Pick up the skull and place it in the purple cup",
    "Pick up the eyeball and place it in the green cup",
    "Pick up the eyeball and place it in the orange cup",
    "Pick up the eyeball and place it in the purple cup",
]


class DataCollector:
    """
    Helper for generating lerobot-record scripts.
    
    This class generates shell scripts that call lerobot-record with the
    correct parameters for each Mortis manipulation task.
    
    All episode data is managed by LeRobot and stored in Hugging Face Hub.
    No local metadata or episode tracking is performed.
    
    Attributes:
        dataset_name: Name of the dataset (e.g., "mortis_manipulation")
        repo_id: Hugging Face repository ID (e.g., "username/mortis-manipulation")
        dataset_dir: Path to local directory for scripts
    """
    
    def __init__(self, dataset_name: str, repo_id: str, root_dir: str = "data"):
        """
        Initialize the DataCollector.
        
        Args:
            dataset_name: Name for the dataset directory
            repo_id: Hugging Face Hub repository ID for uploading
            root_dir: Root directory for storing scripts (default: "data")
        """
        self.dataset_name = dataset_name
        self.repo_id = repo_id
        self.root_dir = Path(root_dir)
        self.dataset_dir = self.root_dir / dataset_name
        
        # Create scripts directory
        self.dataset_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"DataCollector initialized:")
        print(f"  Dataset: {self.dataset_name}")
        print(f"  Repository: {self.repo_id}")
        print(f"  Scripts directory: {self.dataset_dir}")
    
    def generate_record_command(
        self,
        task_description: str,
        num_episodes: int = 10,
        episode_time_s: int = 15,
        reset_time_s: int = 20,
        robot_port: str = "/dev/ttyACM1",
        teleop_port: str = "/dev/ttyACM0",
        display_data: bool = True,
        camera_config: Optional[str] = None,
        resume: bool = True
    ) -> str:
        """
        Generate a lerobot-record command for a specific task.
        
        Args:
            task_description: The task to record (e.g., "Pick up the skull...")
            num_episodes: Number of episodes to record
            episode_time_s: Maximum time per episode in seconds
            reset_time_s: Time allowed for resetting between episodes
            robot_port: USB port for the follower robot
            teleop_port: USB port for the leader robot (teleoperation)
            display_data: Whether to display data during recording
            camera_config: Optional camera configuration string
            resume: Whether to resume an existing dataset (default: True)
        
        Returns:
            The complete lerobot-record command as a string
        """
        # Load environment variables from .env file
        load_dotenv()
        
        # Get environment variables
        robot_port = os.getenv("ROBOT_PORT", robot_port)
        hf_user = os.getenv("HF_USER", "your-username")
        
        # Default camera configuration if not provided
        if camera_config is None:
            camera_config = (
                "{ camera1: {type: intelrealsense, serial_number_or_name: '030522070314', "
                "width: 640, height: 480, fps: 30}, "
                "camera2: {type: opencv, index_or_path: 8, width: 640, height: 480, fps: 30}}"
            )
        
        # Build the command
        cmd_parts = [
            "lerobot-record",
            f"--robot.type=so101_follower",
            f"--robot.port={robot_port}",
            f"--robot.id=my_awesome_follower_arm",
            f'--robot.cameras="{camera_config}"',
            f"--teleop.type=so101_leader",
            f"--teleop.port={teleop_port}",
            f"--teleop.id=my_awesome_leader_arm",
            f"--display_data={str(display_data).lower()}",
            f"--dataset.repo_id={hf_user}/{self.dataset_name}",
            f"--dataset.num_episodes={num_episodes}",
            f"--dataset.episode_time_s={episode_time_s}",
            f"--dataset.reset_time_s={reset_time_s}",
            f'--dataset.single_task="{task_description}"'
        ]
        
        # Only add --resume=true if resume is True
        if resume:
            cmd_parts.append("--resume=true")
        
        return " \\\n    ".join(cmd_parts)
    
    def print_recording_instructions(self, task_index: Optional[int] = None):
        """
        Print instructions for recording episodes using lerobot-record.
        
        Args:
            task_index: Optional specific task index (0-5) to show instructions for.
                       If None, shows instructions for all tasks.
        """
        print("\n" + "="*70)
        print("LeRobot Data Collection Instructions")
        print("="*70)
        
        if task_index is not None:
            # Show instructions for specific task
            if task_index < 0 or task_index >= len(MORTIS_TASKS):
                print(f"❌ Invalid task index: {task_index}")
                return
            
            task_desc = MORTIS_TASKS[task_index]
            
            print(f"\nTask {task_index}: {task_desc}")
            print(f"\nTo record episodes for this task, run:\n")
            print(self.generate_record_command(task_desc))
            print()
        else:
            # Show instructions for all tasks
            print("\nTo record episodes, use the lerobot-record command for each task:")
            print("\nPredefined tasks:")
            
            for i, task_desc in enumerate(MORTIS_TASKS):
                print(f"\n  {i}: {task_desc}")
            
            print("\n" + "-"*70)
            print("\nExample command for task 0:")
            print("-"*70)
            print(self.generate_record_command(MORTIS_TASKS[0]))
            print()
            
            print("\n" + "-"*70)
            print("Environment Variables:")
            print("-"*70)
            print("  HF_USER: Your Hugging Face username (for dataset.repo_id)")
            print("  ROBOT_PORT: USB port for follower robot (default: /dev/ttyACM1)")
            print()
        
        print("="*70 + "\n")
    
    def generate_all_record_scripts(self, output_dir: Optional[Path] = None):
        """
        Generate shell scripts for recording all tasks.
        
        The first script (task_0) creates the dataset without --resume=true.
        Subsequent scripts (task_1+) use --resume=true to add to the existing dataset.
        
        Args:
            output_dir: Directory to save scripts (default: dataset_dir/scripts)
        """
        if output_dir is None:
            output_dir = self.dataset_dir / "scripts"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate individual scripts for each task
        for i, task_desc in enumerate(MORTIS_TASKS):
            script_file = output_dir / f"record_task_{i}.sh"
            
            # First task (task_0) creates the dataset, others resume
            resume = (i > 0)
            
            with open(script_file, 'w') as f:
                f.write("#!/bin/bash\n")
                f.write(f"# Record episodes for: {task_desc}\n")
                f.write(f"# Task {i}\n")
                if i == 0:
                    f.write("# This script CREATES the dataset\n")
                else:
                    f.write("# This script ADDS to the existing dataset (--resume=true)\n")
                f.write("\n")
                f.write(self.generate_record_command(task_desc, resume=resume))
                f.write("\n")
            
            # Make script executable
            script_file.chmod(0o755)
            print(f"Created: {script_file}")
        
        # Generate master script that records all tasks
        master_script = output_dir / "record_all_tasks.sh"
        with open(master_script, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("# Record episodes for all Mortis manipulation tasks\n\n")
            f.write("echo 'Starting data collection for all tasks...'\n")
            f.write("echo ''\n\n")
            
            for i in range(len(MORTIS_TASKS)):
                f.write(f"echo 'Recording task {i}...'\n")
                f.write(f"./record_task_{i}.sh\n")
                f.write("echo ''\n\n")
            
            f.write("echo 'All tasks recorded!'\n")
        
        master_script.chmod(0o755)
        print(f"Created: {master_script}")
        print(f"\n✅ Generated {len(MORTIS_TASKS) + 1} recording scripts in {output_dir}")
    
    def print_summary(self):
        """Print a summary of the dataset configuration."""
        print("\n" + "="*60)
        print(f"Dataset: {self.dataset_name}")
        print(f"Repository: {self.repo_id}")
        print("="*60)
        print(f"Total Tasks: {len(MORTIS_TASKS)}")
        print()
        print("Tasks:")
        print("-"*60)
        
        for i, task_desc in enumerate(MORTIS_TASKS):
            print(f"  {i}: {task_desc}")
        
        print("="*60 + "\n")
        print("📝 Note: Episode data is stored in Hugging Face Hub")
        print(f"   URL: https://huggingface.co/datasets/{self.repo_id}")
        print()


def create_mortis_dataset(dataset_name: str = "mortis_manipulation", 
                          repo_id: str = "mortis/manipulation") -> DataCollector:
    """
    Convenience function to create a DataCollector for Mortis tasks.
    
    Args:
        dataset_name: Name for the dataset
        repo_id: Hugging Face repository ID
    
    Returns:
        Initialized DataCollector
    """
    collector = DataCollector(dataset_name, repo_id)
    return collector


if __name__ == "__main__":
    # Example usage
    print("Creating Mortis manipulation dataset helper...")
    
    collector = create_mortis_dataset()
    
    # Generate recording scripts
    print("\nGenerating lerobot-record scripts...")
    collector.generate_all_record_scripts()
    
    # Show summary
    collector.print_summary()
    
    # Show recording instructions
    collector.print_recording_instructions()
