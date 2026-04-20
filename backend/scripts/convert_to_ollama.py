"""
Convert Fine-Tuned LoRA Adapter to Ollama GGUF Format
======================================================

This script:
1. Loads the base Qwen2.5-3B-Instruct model
2. Merges the fine-tuned LoRA adapter
3. Saves the merged model
4. Converts to GGUF format for Ollama

Requirements:
    pip install torch transformers peft accelerate
    pip install llama-cpp-python  # for GGUF conversion

Author: LegalScoreModel Team
Date: January 2026
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent
ADAPTER_PATH = BASE_DIR / "models" / "fine_tuned" / "adapter_model" / "qwen2.5-3b-legal-critic-adapter"
MERGED_MODEL_PATH = BASE_DIR / "models" / "fine_tuned" / "merged_model"
GGUF_OUTPUT_PATH = BASE_DIR / "models" / "fine_tuned" / "gguf"


def check_dependencies():
    """Check if required packages are installed."""
    required = ["torch", "transformers", "peft", "accelerate"]
    missing = []
    
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    
    if missing:
        print(f"❌ Missing packages: {missing}")
        print(f"   Install with: pip install {' '.join(missing)}")
        sys.exit(1)
    
    print("✓ All required packages installed")


def merge_adapter():
    """Merge the LoRA adapter with the base model."""
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel
    import torch
    
    print("\n" + "=" * 60)
    print("Step 1: Merging LoRA Adapter with Base Model")
    print("=" * 60)
    
    base_model_name = "Qwen/Qwen2.5-3B-Instruct"
    
    print(f"\nLoading base model: {base_model_name}")
    print("This may take a few minutes and will download ~6GB if not cached...")
    
    # Load base model
    model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True
    )
    
    tokenizer = AutoTokenizer.from_pretrained(
        base_model_name,
        trust_remote_code=True
    )
    
    print(f"✓ Base model loaded")
    
    # Load and merge adapter
    print(f"\nLoading adapter from: {ADAPTER_PATH}")
    model = PeftModel.from_pretrained(model, str(ADAPTER_PATH))
    
    print("Merging adapter weights...")
    model = model.merge_and_unload()
    
    print(f"✓ Adapter merged successfully")
    
    # Save merged model
    print(f"\nSaving merged model to: {MERGED_MODEL_PATH}")
    MERGED_MODEL_PATH.mkdir(parents=True, exist_ok=True)
    
    model.save_pretrained(str(MERGED_MODEL_PATH), safe_serialization=True)
    tokenizer.save_pretrained(str(MERGED_MODEL_PATH))
    
    print(f"✓ Merged model saved")
    
    return str(MERGED_MODEL_PATH)


def convert_to_gguf(merged_path: str, quantization: str = "q4_k_m"):
    """Convert the merged model to GGUF format."""
    print("\n" + "=" * 60)
    print("Step 2: Converting to GGUF Format")
    print("=" * 60)
    
    # Create output directory
    GGUF_OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
    
    output_file = GGUF_OUTPUT_PATH / f"legal-critic-{quantization}.gguf"
    
    print(f"\nQuantization: {quantization}")
    print(f"Output: {output_file}")
    
    # We need llama.cpp's convert script
    # First, check if llama-cpp-python has the converter
    try:
        # Try using the llama-cpp-python converter
        print("\nAttempting conversion using llama-cpp-python...")
        
        # Alternative: Use transformers' built-in GGUF export (if available)
        from transformers import AutoModelForCausalLM
        
        print("Loading merged model for GGUF conversion...")
        # This is a placeholder - actual GGUF conversion requires llama.cpp tools
        
        print("""
⚠️  GGUF conversion requires llama.cpp tools.

Please follow these steps manually:

1. Clone llama.cpp:
   git clone https://github.com/ggerganov/llama.cpp
   cd llama.cpp

2. Install Python requirements:
   pip install -r requirements.txt

3. Convert the merged model:
   python convert_hf_to_gguf.py "{merged_path}" --outfile "{output_file}" --outtype {quantization}

4. Create the Ollama Modelfile (already created at models/fine_tuned/Modelfile)

5. Import into Ollama:
   ollama create legal-critic -f models/fine_tuned/Modelfile
""".format(merged_path=merged_path, output_file=output_file, quantization=quantization))
        
        return None
        
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        return None


def create_modelfile():
    """Create an Ollama Modelfile for the converted model."""
    print("\n" + "=" * 60)
    print("Step 3: Creating Ollama Modelfile")
    print("=" * 60)
    
    modelfile_path = BASE_DIR / "models" / "fine_tuned" / "Modelfile"
    gguf_path = GGUF_OUTPUT_PATH / "legal-critic-q4_k_m.gguf"
    
    modelfile_content = f'''# Ollama Modelfile for Legal Argument Critic
# Fine-tuned Qwen2.5-3B-Instruct for Sri Lankan legal cases

FROM {gguf_path}

# Model parameters
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER num_predict 2048
PARAMETER stop "<|im_end|>"

# System prompt for legal argument critique
SYSTEM """You are an expert legal argument critic for Sri Lankan civil cases.

Your task is to analyze legal arguments and provide detailed critiques in JSON format.

IMPORTANT: You MUST respond with ONLY valid JSON, no other text before or after.

The JSON response must have this exact structure:
{{
    "overall_score": <number 0-100>,
    "breakdown": [
        {{"category": "Issue & Claim Clarity", "weight": 10, "rubric_score": <0-5>, "points": <calculated>, "rationale": "<explanation>"}},
        {{"category": "Facts & Chronology", "weight": 15, "rubric_score": <0-5>, "points": <calculated>, "rationale": "<explanation>"}},
        {{"category": "Legal Basis", "weight": 20, "rubric_score": <0-5>, "points": <calculated>, "rationale": "<explanation>"}},
        {{"category": "Evidence & Support", "weight": 15, "rubric_score": <0-5>, "points": <calculated>, "rationale": "<explanation>"}},
        {{"category": "Reasoning & Logic", "weight": 15, "rubric_score": <0-5>, "points": <calculated>, "rationale": "<explanation>"}},
        {{"category": "Counterarguments", "weight": 10, "rubric_score": <0-5>, "points": <calculated>, "rationale": "<explanation>"}},
        {{"category": "Remedies & Quantification", "weight": 10, "rubric_score": <0-5>, "points": <calculated>, "rationale": "<explanation>"}},
        {{"category": "Structure & Professionalism", "weight": 5, "rubric_score": <0-5>, "points": <calculated>, "rationale": "<explanation>"}}
    ],
    "feedback": ["<suggestion 1>", "<suggestion 2>", "<suggestion 3>"]
}}

Scoring: 0=Missing, 1=Poor, 2=Below Average, 3=Average, 4=Good, 5=Excellent
The overall_score = sum of all points."""

# Chat template
TEMPLATE """{{{{ if .System }}}}<|im_start|>system
{{{{ .System }}}}<|im_end|>
{{{{ end }}}}<|im_start|>user
{{{{ .Prompt }}}}<|im_end|>
<|im_start|>assistant
"""
'''
    
    with open(modelfile_path, "w") as f:
        f.write(modelfile_content)
    
    print(f"✓ Modelfile created at: {modelfile_path}")
    
    return str(modelfile_path)


def main():
    parser = argparse.ArgumentParser(description="Convert fine-tuned model for Ollama")
    parser.add_argument("--skip-merge", action="store_true", help="Skip merging if already done")
    parser.add_argument("--quantization", default="q4_k_m", help="GGUF quantization type")
    args = parser.parse_args()
    
    print("=" * 60)
    print("Fine-Tuned Model to Ollama Converter")
    print("=" * 60)
    
    # Check dependencies
    check_dependencies()
    
    # Step 1: Merge adapter
    if args.skip_merge and MERGED_MODEL_PATH.exists():
        print(f"\n⏭️  Skipping merge (--skip-merge flag, using existing: {MERGED_MODEL_PATH})")
        merged_path = str(MERGED_MODEL_PATH)
    else:
        merged_path = merge_adapter()
    
    # Step 2: Create Modelfile
    modelfile_path = create_modelfile()
    
    # Step 3: Convert to GGUF (manual instructions)
    convert_to_gguf(merged_path, args.quantization)
    
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print("""
After GGUF conversion is complete, import into Ollama:

    ollama create legal-critic -f models/fine_tuned/Modelfile

Then update your .env:

    OLLAMA_MODEL=legal-critic

And restart the API server!
""")


if __name__ == "__main__":
    main()
