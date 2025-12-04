#!/usr/bin/env python3
"""
CLI tool for setting up Mortis training infrastructure.

This script generates lerobot-train scripts with appropriate
configurations for training SmolVLA models on Mortis datasets.
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv


class TrainingScriptGenerator:
    """
    Helper for generating lerobot-train scripts.
    
    This class generates shell scripts that call lerobot-train with the
    correct parameters for training SmolVLA models on Mortis datasets.
    
    Attributes:
        dataset_repo_id: Hugging Face dataset repository ID
        output_dir: Directory for training outputs
        job_name: Name for the training job
        model_repo_id: Optional Hugging Face model repository ID for pushing
    """
    
    def __init__(
        self,
        dataset_repo_id: str,
        output_dir: str = "outputs/train",
        job_name: str = "smolvla_mortis",
        model_repo_id: str = None,
        scripts_dir: str = "train"
    ):
        """
        Initialize the TrainingScriptGenerator.
        
        Args:
            dataset_repo_id: Hugging Face dataset repository ID
            output_dir: Base directory for training outputs (checkpoints, logs)
            job_name: Name for the training job
            model_repo_id: Optional HF model repo ID for pushing trained model
            scripts_dir: Directory to save training scripts
        """
        self.dataset_repo_id = dataset_repo_id
        self.output_dir = Path(output_dir)
        self.job_name = job_name
        self.model_repo_id = model_repo_id
        self.scripts_dir = Path(scripts_dir)
        
        # Create scripts directory
        self.scripts_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"TrainingScriptGenerator initialized:")
        print(f"  Dataset: {self.dataset_repo_id}")
        print(f"  Scripts directory: {self.scripts_dir}")
        print(f"  Training output directory: {self.output_dir}")
        print(f"  Job name: {self.job_name}")
        if self.model_repo_id:
            print(f"  Model repository: {self.model_repo_id}")
    
    def generate_train_command(
        self,
        policy_path: str = "lerobot/smolvla_base",
        batch_size: int = 16,
        steps: int = 20000,
        save_freq: int = 5000,
        eval_freq: int = 5000,
        n_action_steps: int = 50,
        chunk_size: int = 50,
        use_amp: bool = True,
        enable_wandb: bool = True,
        device: str = "cuda",
        image_transforms: bool = True,
        rename_map: str = None,
        cuda_alloc_conf: str = "expandable_segments:True"
    ) -> str:
        """
        Generate a lerobot-train command with specified parameters.
        
        Args:
            policy_path: Path to base policy (default: lerobot/smolvla_base)
            batch_size: Training batch size
            steps: Total training steps
            save_freq: Checkpoint save frequency
            eval_freq: Evaluation frequency
            n_action_steps: Number of action steps to predict
            chunk_size: Action chunk size
            use_amp: Use automatic mixed precision
            enable_wandb: Enable Weights & Biases logging
            device: Device to use (cuda or cpu)
            image_transforms: Enable image transformations
            rename_map: Optional observation key rename mapping
            cuda_alloc_conf: CUDA memory allocator configuration
        
        Returns:
            The complete lerobot-train command as a string
        """
        # Load environment variables
        load_dotenv()
        
        # Build output directory path
        full_output_dir = self.output_dir / self.job_name
        
        # Default rename map for SO101 with dual cameras
        if rename_map is None:
            rename_map = (
                '{"observation.images.camera1": "observation.images.camera1", '
                '"observation.images.camera2": "observation.images.camera2"}'
            )
        
        # Build the command
        cmd_parts = [
            f"PYTORCH_CUDA_ALLOC_CONF={cuda_alloc_conf} \\",
            "lerobot-train \\",
            f"  --policy.path={policy_path} \\",
            f"  --dataset.repo_id={self.dataset_repo_id} \\",
            f"  --dataset.image_transforms.enable={str(image_transforms).lower()} \\",
            f"  --policy.device={device} \\",
            f"  --policy.use_amp={str(use_amp).lower()} \\",
            f"  --policy.n_action_steps={n_action_steps} \\",
            f"  --policy.chunk_size={chunk_size} \\",
            f"  --batch_size={batch_size} \\",
            f"  --steps={steps} \\",
            f"  --save_checkpoint=true \\",
            f"  --save_freq={save_freq} \\",
            f"  --eval_freq={eval_freq} \\",
            f"  --wandb.enable={str(enable_wandb).lower()} \\",
            f"  --output_dir={full_output_dir} \\",
            f"  --job_name={self.job_name} \\",
        ]
        
        # Add model repo ID if specified
        if self.model_repo_id:
            cmd_parts.append(f"  --policy.repo_id={self.model_repo_id} \\")
        
        # Add rename map
        cmd_parts.append(f"  --rename_map='{rename_map}'")
        
        return "\n".join(cmd_parts)
    
    def generate_training_script(
        self,
        script_name: str = "train.sh",
        **kwargs
    ) -> Path:
        """
        Generate a shell script for training.
        
        Args:
            script_name: Name for the training script
            **kwargs: Additional arguments passed to generate_train_command
        
        Returns:
            Path to the generated script
        """
        script_path = self.scripts_dir / script_name
        
        with open(script_path, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write(f"# Training script for {self.job_name}\n")
            f.write(f"# Dataset: {self.dataset_repo_id}\n")
            f.write(f"# Generated by setup_train.py\n\n")
            
            f.write("# Check if CUDA is available\n")
            f.write("if ! command -v nvidia-smi &> /dev/null; then\n")
            f.write('    echo "⚠️  Warning: nvidia-smi not found. CUDA may not be available."\n')
            f.write('    read -p "Continue anyway? (y/N): " -n 1 -r\n')
            f.write('    echo\n')
            f.write('    if [[ ! $REPLY =~ ^[Yy]$ ]]; then\n')
            f.write('        exit 1\n')
            f.write('    fi\n')
            f.write("fi\n\n")
            
            f.write("# Start training\n")
            f.write(f'echo "Starting training: {self.job_name}"\n')
            f.write(f'echo "Dataset: {self.dataset_repo_id}"\n')
            f.write(f'echo "Output: {self.output_dir / self.job_name}"\n')
            f.write('echo ""\n\n')
            
            f.write(self.generate_train_command(**kwargs))
            f.write("\n")
        
        # Make script executable
        script_path.chmod(0o755)
        print(f"Created: {script_path}")
        
        return script_path
    
    def generate_training_configs(self):
        """
        Generate multiple training scripts with different configurations.
        
        Creates:
        - train_quick.sh: Quick test training (1000 steps)
        - train_standard.sh: Standard training (20k steps)
        - train_full.sh: Full training (100k steps)
        """
        configs = [
            {
                "script_name": "train_quick.sh",
                "steps": 1000,
                "save_freq": 500,
                "eval_freq": 500,
                "batch_size": 8,
            },
            {
                "script_name": "train_standard.sh",
                "steps": 20000,
                "save_freq": 5000,
                "eval_freq": 5000,
                "batch_size": 16,
            },
            {
                "script_name": "train_full.sh",
                "steps": 100000,
                "save_freq": 10000,
                "eval_freq": 10000,
                "batch_size": 16,
            },
        ]
        
        for config in configs:
            self.generate_training_script(**config)
        
        print(f"\n✅ Generated {len(configs)} training scripts in {self.scripts_dir}")
    
    def print_usage_instructions(self):
        """Print instructions for using the generated training scripts."""
        print("\n" + "="*70)
        print("Training Scripts Generated")
        print("="*70)
        print()
        print("Available training scripts:")
        print(f"  {self.scripts_dir}/train_quick.sh     - Quick test (1k steps)")
        print(f"  {self.scripts_dir}/train_standard.sh  - Standard training (20k steps)")
        print(f"  {self.scripts_dir}/train_full.sh      - Full training (100k steps)")
        print()
        print("To start training:")
        print(f"  cd {self.scripts_dir}")
        print("  ./train_standard.sh")
        print()
        print("Training outputs will be saved to:")
        print(f"  {self.output_dir}/{self.job_name}/")
        print()
        print("Monitor training:")
        print("  - Console: Watch the terminal output")
        print("  - W&B: https://wandb.ai (if enabled)")
        print(f"  - Checkpoints: {self.output_dir}/{self.job_name}/checkpoints/")
        print()
        print("Resume training:")
        print("  Add --resume=true to the lerobot-train command")
        print()
        print("="*70)


def main():
    """Main entry point for training setup."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Setup Mortis training infrastructure and generate training scripts"
    )
    parser.add_argument(
        "--dataset-repo-id",
        type=str,
        required=True,
        help="Hugging Face dataset repository ID (e.g., username/dataset-name)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="outputs/train",
        help="Base directory for training outputs/checkpoints (default: outputs/train)"
    )
    parser.add_argument(
        "--scripts-dir",
        type=str,
        default="train",
        help="Directory to save training scripts (default: train)"
    )
    parser.add_argument(
        "--job-name",
        type=str,
        default=None,
        help="Name for the training job (default: derived from dataset name)"
    )
    parser.add_argument(
        "--model-repo-id",
        type=str,
        default=None,
        help="Hugging Face model repository ID for pushing trained model"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
        help="Training batch size (default: 16)"
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=20000,
        help="Total training steps (default: 20000)"
    )
    parser.add_argument(
        "--policy-path",
        type=str,
        default="lerobot/smolvla_base",
        help="Path to base policy (default: lerobot/smolvla_base)"
    )
    parser.add_argument(
        "--no-wandb",
        action="store_true",
        help="Disable Weights & Biases logging"
    )
    parser.add_argument(
        "--generate-configs",
        action="store_true",
        help="Generate multiple training configurations (quick, standard, full)"
    )
    
    args = parser.parse_args()
    
    # Load environment variables
    REPO_ROOT = Path(__file__).resolve().parents[2]
    load_dotenv(REPO_ROOT / ".env")
    
    print("="*70)
    print("Mortis Training Setup")
    print("="*70)
    print()
    
    # Derive job name from dataset if not provided
    job_name = args.job_name
    if not job_name:
        # Extract dataset name from repo_id
        dataset_name = args.dataset_repo_id.split('/')[-1]
        job_name = f"smolvla_{dataset_name}"
        print(f"Using job name: {job_name}")
        print()
    
    # Create generator
    generator = TrainingScriptGenerator(
        dataset_repo_id=args.dataset_repo_id,
        output_dir=args.output_dir,
        job_name=job_name,
        model_repo_id=args.model_repo_id,
        scripts_dir=args.scripts_dir
    )
    
    print()
    
    if args.generate_configs:
        # Generate multiple configurations
        print("Generating training configurations...")
        generator.generate_training_configs()
    else:
        # Generate single training script
        print("Generating training script...")
        generator.generate_training_script(
            script_name="train.sh",
            policy_path=args.policy_path,
            batch_size=args.batch_size,
            steps=args.steps,
            enable_wandb=not args.no_wandb
        )
    
    # Print usage instructions
    generator.print_usage_instructions()
    
    # Final tips
    print("\n💡 Tips:")
    print("  - Adjust batch_size based on your GPU memory")
    print("  - Monitor GPU usage with: watch -n 1 nvidia-smi")
    print("  - Training logs are saved in the output directory")
    print("  - Use Ctrl+C to stop training (checkpoints are saved)")
    print()
    print("="*70)


if __name__ == "__main__":
    main()
