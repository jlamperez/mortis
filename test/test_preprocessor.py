#!/usr/bin/env python3
"""
Test to verify SmolVLA preprocessor handles tokenization automatically.

This test verifies that:
1. The preprocessor loads correctly from the checkpoint
2. Task strings are automatically tokenized by the TokenizerProcessorStep
3. The observation contains the expected language tokens and attention mask
"""

import sys
from pathlib import Path

# Add parent directory to path to import mortis package
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
import torch
from src.mortis.smolvla_executor import SmolVLAExecutor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def test_preprocessor():
    """Test that the preprocessor tokenizes task strings automatically."""
    print("\n" + "="*60)
    print("Testing SmolVLA preprocessor with automatic tokenization")
    print("="*60 + "\n")
    
    checkpoint_path = "outputs/train/smolvla_kiroween_potion_20k/checkpoints/last/pretrained_model"
    
    try:
        # Initialize executor
        print("1. Initializing executor...")
        executor = SmolVLAExecutor(
            checkpoint_path=checkpoint_path,
            robot_arm=None,
            device="cuda",
            enable_safety_checks=False
        )
        print("   ✓ Executor initialized\n")
        
        # Test observation creation
        print("2. Creating test observation...")
        test_command = "Pick up the skull and place it in the orange cup"
        
        # Create raw observation (without tokenization)
        observation = {
            "observation.state": torch.zeros(1, 6, dtype=torch.float32, device="cuda"),
            "observation.images.camera1": torch.zeros(1, 3, 256, 256, dtype=torch.float32, device="cuda"),
            "observation.images.camera2": torch.zeros(1, 3, 256, 256, dtype=torch.float32, device="cuda"),
            "observation.images.camera3": torch.zeros(1, 3, 256, 256, dtype=torch.float32, device="cuda"),
            "task": test_command  # Just the string - preprocessor will tokenize it
        }
        print(f"   Task string: '{test_command}'")
        print(f"   ✓ Raw observation created\n")
        
        # Apply preprocessor
        print("3. Applying preprocessor (should tokenize automatically)...")
        processed_obs = executor.preprocessor(observation)
        print("   ✓ Preprocessor applied\n")
        
        # Check results
        print("4. Checking processed observation...")
        print(f"   Keys in processed observation:")
        for key in processed_obs.keys():
            if isinstance(processed_obs[key], torch.Tensor):
                print(f"     - {key}: shape={processed_obs[key].shape}")
            else:
                print(f"     - {key}: {type(processed_obs[key])}")
        
        # Check for language tokens
        has_tokens = "observation.language.tokens" in processed_obs
        has_attention = "observation.language.attention_mask" in processed_obs
        
        if has_tokens and has_attention:
            print("\n   ✓ Language tokens found!")
            tokens = processed_obs["observation.language.tokens"]
            attention = processed_obs["observation.language.attention_mask"]
            print(f"     - Tokens shape: {tokens.shape}, dtype: {tokens.dtype}")
            print(f"     - Attention mask shape: {attention.shape}, dtype: {attention.dtype}")
            
            # Verify shapes match expected
            expected_length = 48  # From config: tokenizer_max_length
            if tokens.shape[-1] == expected_length:
                print(f"     - Token length matches expected: {expected_length}")
            else:
                print(f"     - WARNING: Token length {tokens.shape[-1]} != expected {expected_length}")
        else:
            print("\n   ✗ Language tokens not found")
            if not has_tokens:
                print("     - Missing: observation.language.tokens")
            if not has_attention:
                print("     - Missing: observation.language.attention_mask")
            return False
        
        print("\n" + "="*60)
        print("✓ Test passed! Preprocessor tokenizes automatically")
        print("="*60 + "\n")
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_preprocessor()
    exit(0 if success else 1)
