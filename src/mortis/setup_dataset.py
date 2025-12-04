#!/usr/bin/env python3
"""
CLI tool for setting up Mortis dataset infrastructure.

This script initializes the dataset structure and generates
lerobot-record scripts for data collection.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from dotenv import load_dotenv

from mortis.data_collector import create_mortis_dataset, DataCollector


def check_huggingface_auth():
    """Check if user is authenticated with Hugging Face."""
    try:
        result = subprocess.run(
            ["huggingface-cli", "whoami"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def main():
    """Main entry point for dataset setup."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Setup Mortis dataset infrastructure and generate recording scripts"
    )
    parser.add_argument(
        "--dataset-name",
        type=str,
        default=None,
        help="Name for the dataset (default: mortis_manipulation)"
    )
    parser.add_argument(
        "--hf-user",
        type=str,
        default=None,
        help="Hugging Face username (default: from HF_USER env var)"
    )
    args = parser.parse_args()
    
    # Load environment variables from .env file
    REPO_ROOT = Path(__file__).resolve().parents[2]
    load_dotenv(REPO_ROOT / ".env")

    
    print("="*70)
    print("Mortis Dataset Setup")
    print("="*70)
    print()
    
    # Check Hugging Face authentication
    print("Checking Hugging Face authentication...")
    if not check_huggingface_auth():
        print("⚠️  Not logged in to Hugging Face")
        print("📝 You need to authenticate before recording datasets")
        print()
        print("Run this command to login:")
        print("   huggingface-cli login")
        print()
        print("Get your token from: https://huggingface.co/settings/tokens")
        print()
        response = input("Continue anyway? (y/N): ").strip().lower()
        if response != 'y':
            print("Setup cancelled. Please login first with: huggingface-cli login")
            sys.exit(0)
        print()
    else:
        print("✅ Hugging Face authentication verified")
        print()
    
    # Get Hugging Face username
    hf_user = args.hf_user or os.getenv("HF_USER")
    if not hf_user:
        print("⚠️  HF_USER not found in .env file or environment")
        hf_user = input("Enter your Hugging Face username: ").strip()
        if not hf_user:
            print("❌ Hugging Face username is required")
            sys.exit(1)
        print(f"💡 Tip: Add HF_USER to your .env file to skip this prompt:")
        print(f"   echo 'HF_USER={hf_user}' >> .env")
        print()
    
    # Get dataset name
    dataset_name = args.dataset_name
    if not dataset_name:
        print("Dataset name:")
        print("  Press Enter for default: 'mortis_manipulation'")
        print("  Or enter a custom name (e.g., 'mortis_v2', 'test_dataset')")
        user_input = input("Dataset name: ").strip()
        dataset_name = user_input if user_input else "mortis_manipulation"
        print()
    
    # Create repository ID
    repo_id = f"{hf_user}/{dataset_name}"
    
    print(f"Creating dataset: {dataset_name}")
    print(f"Repository: {repo_id}")
    print()
    
    # Create collector with custom name
    collector = DataCollector(dataset_name, repo_id)
    
    # Generate scripts
    print("\nGenerating recording scripts...")
    collector.generate_all_record_scripts()
    
    # Show summary
    collector.print_summary()
    
    # Show instructions
    collector.print_recording_instructions()
    
    # Final instructions
    print("="*70)
    print("Setup Complete! 🎉")
    print("="*70)
    print()
    print("Next steps:")
    print("  1. Make sure you're logged in to Hugging Face:")
    print("     huggingface-cli login")
    print("  2. Connect your leader and follower robot arms")
    print("  3. Navigate to the scripts directory:")
    print(f"     cd {collector.dataset_dir}/scripts")
    print("  4. Run a recording script:")
    print("     ./record_task_0.sh")
    print()
    print("Or record all tasks:")
    print("     ./record_all_tasks.sh")
    print()
    print("="*70)


if __name__ == "__main__":
    main()
