#!/usr/bin/env python3
"""
Merge LoRA Adapter with Base Model
===================================

This script merges the fine-tuned LoRA adapter with the base Qwen2.5-3B model
to create a standalone model that can be used with Ollama.

Requirements:
    - GPU with 16GB+ VRAM (or use CPU with 32GB+ RAM)
    - ~20GB disk space for merged model

Usage:
    python scripts/merge_adapter.py

The merged model will be saved to: ./merged_model/
"""

import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def check_requirements():
    """Check if required packages are installed."""
    required = ["torch", "transformers", "peft"]
    missing = []
    
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    
    if missing:
        print("❌ Missing required packages. Install with:")
        print(f"   pip install {' '.join(missing)}")
        sys.exit(1)


def merge_adapter():
    """Merge LoRA adapter with base model."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel
    
    # Configuration
    BASE_MODEL_ID = "Qwen/Qwen2.5-3B-Instruct"
    
    # Try to find adapter - check multiple locations
    adapter_paths = [
        PROJECT_ROOT / "adapter_model",  # Local training output
        PROJECT_ROOT / "data" / "adapter_model",
        Path.home() / ".cache" / "huggingface" / "hub" / "models--KrishSteve--civilmodel_qwen3b_v1",
    ]
    
    ADAPTER_PATH = None
    for path in adapter_paths:
        if path.exists():
            ADAPTER_PATH = path
            break
    
    # If not found locally, download from HuggingFace
    if ADAPTER_PATH is None:
        print("📥 Adapter not found locally. Will download from HuggingFace...")
        ADAPTER_PATH = "KrishSteve/civilmodel_qwen3b_v1"
    
    OUTPUT_DIR = PROJECT_ROOT / "merged_model"
    
    print("=" * 60)
    print("🔧 LoRA Adapter Merge Tool")
    print("=" * 60)
    print(f"Base Model:  {BASE_MODEL_ID}")
    print(f"Adapter:     {ADAPTER_PATH}")
    print(f"Output:      {OUTPUT_DIR}")
    print("=" * 60)
    
    # Check GPU availability
    if torch.cuda.is_available():
        device = "cuda"
        print(f"🎮 Using GPU: {torch.cuda.get_device_name(0)}")
        print(f"   VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    else:
        device = "cpu"
        print("⚠️  No GPU found. Using CPU (this will be slow!)")
    
    print()
    
    # Step 1: Load base model
    print("📦 Step 1/4: Loading base model...")
    print("   (This downloads ~6GB if not cached)")
    
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_ID,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        device_map="auto" if device == "cuda" else None,
        trust_remote_code=True,
        low_cpu_mem_usage=True
    )
    print("   ✅ Base model loaded")
    
    # Step 2: Load tokenizer
    print("📦 Step 2/4: Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        BASE_MODEL_ID,
        trust_remote_code=True
    )
    print("   ✅ Tokenizer loaded")
    
    # Step 3: Load and merge LoRA adapter
    print("🔗 Step 3/4: Loading and merging LoRA adapter...")
    
    model = PeftModel.from_pretrained(
        base_model,
        str(ADAPTER_PATH),
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
    )
    
    # Merge adapter weights into base model
    print("   Merging weights...")
    model = model.merge_and_unload()
    print("   ✅ Adapter merged")
    
    # Step 4: Save merged model
    print(f"💾 Step 4/4: Saving merged model to {OUTPUT_DIR}...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    model.save_pretrained(OUTPUT_DIR, safe_serialization=True)
    tokenizer.save_pretrained(OUTPUT_DIR)
    
    print("   ✅ Model saved")
    
    # Calculate size
    total_size = sum(f.stat().st_size for f in OUTPUT_DIR.rglob("*") if f.is_file())
    print()
    print("=" * 60)
    print("✅ MERGE COMPLETE!")
    print("=" * 60)
    print(f"   Location: {OUTPUT_DIR}")
    print(f"   Size: {total_size / 1e9:.2f} GB")
    print()
    print("Next steps:")
    print("   1. Create Modelfile for Ollama (see Modelfile.template)")
    print("   2. Import to Ollama: ollama create civilmodel-qwen3b -f Modelfile")
    print("   3. Test: ollama run civilmodel-qwen3b")
    print("=" * 60)


def main():
    """Main entry point."""
    print()
    print("🚀 Starting LoRA Adapter Merge...")
    print()
    
    check_requirements()
    
    try:
        merge_adapter()
    except KeyboardInterrupt:
        print("\n\n⚠️ Merge cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error during merge: {e}")
        print("\nTroubleshooting:")
        print("  1. Ensure you have enough GPU VRAM (16GB+) or RAM (32GB+ for CPU)")
        print("  2. Check that the adapter path is correct")
        print("  3. Try running with: PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True python merge_adapter.py")
        sys.exit(1)


if __name__ == "__main__":
    main()
