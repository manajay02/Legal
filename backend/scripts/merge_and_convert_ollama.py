"""
Merge LoRA Adapter and Convert to Ollama GGUF Format
=====================================================

This script:
1. Loads the base Qwen2.5-3B-Instruct model
2. Merges your fine-tuned LoRA adapter
3. Converts to GGUF format
4. Creates Ollama Modelfile
5. Imports into Ollama

Run: python scripts/merge_and_convert_ollama.py

Author: LegalScoreModel Team
Date: January 2026
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent
ADAPTER_PATH = BASE_DIR / "models" / "fine_tuned" / "adapter_model" / "qwen2.5-3b-legal-critic-adapter"
MERGED_PATH = BASE_DIR / "models" / "fine_tuned" / "merged_model"
GGUF_PATH = BASE_DIR / "models" / "fine_tuned" / "gguf"
LLAMA_CPP_PATH = BASE_DIR / "llama.cpp"


def check_adapter():
    """Verify the adapter exists."""
    print("\n[1/6] Checking adapter files...")
    
    if not ADAPTER_PATH.exists():
        print(f"❌ Adapter not found at: {ADAPTER_PATH}")
        sys.exit(1)
    
    required_files = ["adapter_config.json", "adapter_model.safetensors"]
    for f in required_files:
        if not (ADAPTER_PATH / f).exists():
            print(f"❌ Missing: {f}")
            sys.exit(1)
    
    print(f"✓ Adapter found at: {ADAPTER_PATH}")


def check_hf_cache():
    """Check if base model is already in HuggingFace cache."""
    print("\n[1.5/6] Checking HuggingFace cache for base model...")
    
    # Common cache locations
    cache_paths = [
        Path.home() / ".cache" / "huggingface" / "hub",
        Path(os.getenv("HF_HOME", "")) / "hub" if os.getenv("HF_HOME") else None,
        Path(os.getenv("TRANSFORMERS_CACHE", "")) if os.getenv("TRANSFORMERS_CACHE") else None,
    ]
    
    model_id = "Qwen--Qwen2.5-3B-Instruct"  # HF cache format uses -- instead of /
    
    for cache_path in cache_paths:
        if cache_path and cache_path.exists():
            model_cache = cache_path / f"models--{model_id}"
            if model_cache.exists():
                print(f"✓ Base model FOUND in cache: {model_cache}")
                print("  → Will NOT re-download!")
                return True
    
    print("⚠ Base model NOT in HuggingFace cache")
    print("  → Will download ~6GB (one-time, cached for all projects)")
    
    response = input("\n  Continue? (y/n): ").strip().lower()
    if response != 'y':
        print("Aborted.")
        sys.exit(0)
    
    return False


def merge_adapter():
    """Merge LoRA adapter with base model."""
    print("\n[2/6] Merging adapter with base model...")
    print("      This will download ~6GB base model (cached for future use)")
    
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel
    
    base_model_name = "Qwen/Qwen2.5-3B-Instruct"
    
    print(f"      Loading base model: {base_model_name}")
    tokenizer = AutoTokenizer.from_pretrained(base_model_name, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        torch_dtype=torch.float16,
        device_map="cpu",  # Use CPU for merging to avoid OOM
        trust_remote_code=True
    )
    
    print(f"      Loading adapter: {ADAPTER_PATH}")
    model = PeftModel.from_pretrained(model, str(ADAPTER_PATH))
    
    print("      Merging weights...")
    model = model.merge_and_unload()
    
    print(f"      Saving merged model to: {MERGED_PATH}")
    MERGED_PATH.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(MERGED_PATH), safe_serialization=True)
    tokenizer.save_pretrained(str(MERGED_PATH))
    
    print("✓ Merged model saved")
    return str(MERGED_PATH)


def setup_llama_cpp():
    """Clone and build llama.cpp if needed."""
    print("\n[3/6] Setting up llama.cpp converter...")
    
    if not LLAMA_CPP_PATH.exists():
        print("      Cloning llama.cpp...")
        subprocess.run([
            "git", "clone", "--depth", "1",
            "https://github.com/ggerganov/llama.cpp",
            str(LLAMA_CPP_PATH)
        ], check=True)
    
    # Install requirements for conversion
    requirements_file = LLAMA_CPP_PATH / "requirements.txt"
    if requirements_file.exists():
        print("      Installing llama.cpp requirements...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-q",
            "-r", str(requirements_file)
        ], check=True)
    
    print("✓ llama.cpp ready")


def convert_to_gguf():
    """Convert merged model to GGUF format."""
    print("\n[4/6] Converting to GGUF format...")
    
    GGUF_PATH.mkdir(parents=True, exist_ok=True)
    output_file = GGUF_PATH / "legal-critic-f16.gguf"
    
    convert_script = LLAMA_CPP_PATH / "convert_hf_to_gguf.py"
    
    if not convert_script.exists():
        print(f"❌ Convert script not found: {convert_script}")
        sys.exit(1)
    
    print(f"      Input: {MERGED_PATH}")
    print(f"      Output: {output_file}")
    
    subprocess.run([
        sys.executable, str(convert_script),
        str(MERGED_PATH),
        "--outfile", str(output_file),
        "--outtype", "f16"
    ], check=True)
    
    print("✓ GGUF conversion complete")
    return str(output_file)


def quantize_gguf(input_gguf: str):
    """Quantize to Q4_K_M for smaller size."""
    print("\n[5/6] Quantizing to Q4_K_M (optional, smaller file)...")
    
    output_file = GGUF_PATH / "legal-critic-q4_k_m.gguf"
    
    # Try to find quantize binary
    quantize_bin = None
    for name in ["quantize", "quantize.exe", "llama-quantize", "llama-quantize.exe"]:
        path = LLAMA_CPP_PATH / name
        if path.exists():
            quantize_bin = path
            break
        path = LLAMA_CPP_PATH / "build" / "bin" / name
        if path.exists():
            quantize_bin = path
            break
    
    if quantize_bin is None:
        print("      ⚠ Quantize binary not found, skipping quantization")
        print("      Using F16 GGUF instead (larger but works)")
        return input_gguf
    
    subprocess.run([
        str(quantize_bin),
        input_gguf,
        str(output_file),
        "Q4_K_M"
    ], check=True)
    
    print(f"✓ Quantized model: {output_file}")
    return str(output_file)


def create_modelfile_and_import(gguf_path: str):
    """Create Ollama Modelfile and import the model."""
    print("\n[6/6] Importing into Ollama...")
    
    modelfile_path = GGUF_PATH / "Modelfile"
    
    modelfile_content = f'''# Legal Argument Critic - Fine-tuned Qwen2.5-3B
FROM {gguf_path}

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER num_predict 2048
PARAMETER stop "<|im_end|>"

SYSTEM """You are an expert legal argument critic for Sri Lankan civil cases.

Analyze the legal argument and respond with ONLY valid JSON in this exact format:
{{
    "overall_score": <0-100>,
    "breakdown": [
        {{"category": "Issue & Claim Clarity", "weight": 10, "rubric_score": <0-5>, "points": <weight*score/5>, "rationale": "<explanation>"}},
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

Scoring: 0=Missing, 1=Poor, 2=Below Average, 3=Average, 4=Good, 5=Excellent"""

TEMPLATE """{{{{- if .System }}}}<|im_start|>system
{{{{ .System }}}}<|im_end|>
{{{{ end }}}}<|im_start|>user
{{{{ .Prompt }}}}<|im_end|>
<|im_start|>assistant
"""
'''
    
    with open(modelfile_path, "w") as f:
        f.write(modelfile_content)
    
    print(f"      Modelfile created: {modelfile_path}")
    
    # Import into Ollama
    print("      Importing into Ollama as 'legal-critic'...")
    result = subprocess.run([
        "ollama", "create", "legal-critic", "-f", str(modelfile_path)
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Ollama import failed: {result.stderr}")
        print("\n      Manual import command:")
        print(f"      ollama create legal-critic -f {modelfile_path}")
        return False
    
    print("✓ Model imported as 'legal-critic'")
    return True


def main():
    print("=" * 60)
    print("Fine-Tuned Model → Ollama Converter")
    print("=" * 60)
    
    # Step 1: Check adapter
    check_adapter()
    
    # Step 1.5: Check if base model is cached
    check_hf_cache()
    
    # Step 2: Merge adapter with base model
    merged_path = merge_adapter()
    
    # Step 3: Setup llama.cpp
    setup_llama_cpp()
    
    # Step 4: Convert to GGUF
    gguf_f16 = convert_to_gguf()
    
    # Step 5: Quantize (optional)
    final_gguf = quantize_gguf(gguf_f16)
    
    # Step 6: Create Modelfile and import
    success = create_modelfile_and_import(final_gguf)
    
    print("\n" + "=" * 60)
    if success:
        print("✅ SUCCESS! Your fine-tuned model is now in Ollama")
        print("=" * 60)
        print("\nNext steps:")
        print("  1. Update .env: OLLAMA_MODEL=legal-critic")
        print("  2. Start server: python -m uvicorn app.main:app --reload")
        print("  3. Test: python test_api_v1.py")
    else:
        print("⚠ Conversion complete but Ollama import failed")
        print("=" * 60)
        print("\nManual import:")
        print(f"  ollama create legal-critic -f {GGUF_PATH / 'Modelfile'}")
    
    print("\n")


if __name__ == "__main__":
    main()
