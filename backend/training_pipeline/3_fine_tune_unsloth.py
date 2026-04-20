"""
Fine-Tuning Script for Legal Argument Critic Model
===================================================

This script fine-tunes Qwen2.5-3B-Instruct using Unsloth for efficient
LoRA training on a Kaggle GPU (P100) environment.

Model: unsloth/Qwen2.5-3B-Instruct-bnb-4bit
Dataset: train.jsonl (generated from Supreme Court judgments)
Task: Score and critique legal arguments (0-100 scale)

Usage (on Kaggle):
    1. Upload this script and train.jsonl to Kaggle
    2. Enable GPU accelerator (P100)
    3. Run: python 3_fine_tune_unsloth.py

Author: LegalScoreModel Team
Date: January 2026
"""

# ============================================
# 0. INSTALL DEPENDENCIES
# ============================================
# Automatically install required packages

import subprocess
import sys

print("Installing dependencies...")
print("=" * 60)

# Install Unsloth (optimized for fast LoRA training)
print("[1/4] Installing Unsloth...")
subprocess.check_call([
    sys.executable, "-m", "pip", "install", "-q",
    "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
])

# Install compatible PEFT version to avoid ensure_weight_tying error
print("[2/4] Installing compatible PEFT version...")
subprocess.check_call([
    sys.executable, "-m", "pip", "install", "-q",
    "peft>=0.13.0", "--upgrade"
])

# Install additional required packages
print("[3/4] Installing TRL and dependencies...")
subprocess.check_call([
    sys.executable, "-m", "pip", "install", "-q",
    "--no-deps", "trl", "accelerate", "bitsandbytes"
])

print("[4/4] Installing datasets...")
subprocess.check_call([
    sys.executable, "-m", "pip", "install", "-q", "datasets"
])

print("✓ All dependencies installed!")
print("=" * 60)
print()

import os
import json
import torch
from datasets import load_dataset

# Disable Triton for P100 GPU (CUDA capability 6.0, Triton needs 7.0+)
os.environ["DISABLE_TRITON"] = "1"
os.environ["TORCHDYNAMO_DISABLE"] = "1"

# ============================================
# 1. SETUP AND IMPORTS
# ============================================

from unsloth import FastLanguageModel
from transformers import TrainingArguments, Trainer
from trl import SFTTrainer

print("=" * 60)
print("Legal Argument Critic - Fine-Tuning with Unsloth")
print("=" * 60)

# Check GPU availability
if torch.cuda.is_available():
    gpu_name = torch.cuda.get_device_name(0)
    gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
    print(f"✓ GPU detected: {gpu_name} ({gpu_memory:.1f} GB)")
else:
    print("⚠ No GPU detected. Training will be very slow!")

# ============================================
# 2. MODEL AND TOKENIZER LOADING
# ============================================

# Configuration
BASE_MODEL = "unsloth/Qwen2.5-3B-Instruct-bnb-4bit"  # 4-bit quantized Qwen2.5-3B
MAX_SEQ_LENGTH = 2048  # Handle long legal arguments
DTYPE = None  # Auto-detect (float16 or bfloat16)
LOAD_IN_4BIT = True  # Use 4-bit quantization for memory efficiency

print(f"\n[1/6] Loading base model: {BASE_MODEL}")

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=BASE_MODEL,
    max_seq_length=MAX_SEQ_LENGTH,
    dtype=DTYPE,
    load_in_4bit=LOAD_IN_4BIT,
)

print(f"✓ Model loaded successfully")
print(f"  - Max sequence length: {MAX_SEQ_LENGTH}")
print(f"  - 4-bit quantization: {LOAD_IN_4BIT}")

# ============================================
# 3. LORA CONFIGURATION
# ============================================
# LoRA (Low-Rank Adaptation) allows efficient fine-tuning by only
# training a small number of additional parameters.

print("\n[2/6] Configuring LoRA adapter...")

model = FastLanguageModel.get_peft_model(
    model,
    r=16,  # Rank of the low-rank matrices (higher = more capacity)
    lora_alpha=32,  # Scaling factor (usually 2x r)
    target_modules=[
        "q_proj", "k_proj", "v_proj", "o_proj",  # Attention layers
        "gate_proj", "up_proj", "down_proj",  # MLP layers
    ],
    lora_dropout=0,  # Set to 0 for faster training (Unsloth optimized)
    bias="none",  # Don't train bias terms
    use_gradient_checkpointing="unsloth",  # Memory optimization
    random_state=42,
)

# Print trainable parameters
trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
total_params = sum(p.numel() for p in model.parameters())
print(f"✓ LoRA adapter configured")
print(f"  - Trainable parameters: {trainable_params:,} ({100*trainable_params/total_params:.2f}%)")
print(f"  - Total parameters: {total_params:,}")

# ============================================
# 4. DATASET LOADING AND FORMATTING
# ============================================

# Qwen2 Chat Template
# The model expects conversations in this specific format
SYSTEM_PROMPT = """You are an expert legal argument critic for Sri Lankan civil cases. 
Analyze the provided legal argument and return a JSON critique with:
1. overall_score (0-100)
2. breakdown (8 categories with weight, rubric_score 0-5, points, rationale)
3. feedback (3 improvement suggestions)

Categories: Issue & Claim Clarity (10), Facts & Chronology (15), Legal Basis (20), 
Evidence & Support (15), Reasoning & Logic (15), Counterarguments (10), 
Remedies & Quantification (10), Structure & Professionalism (5)"""


def format_prompt(example):
    """
    Format a training example into Qwen2 chat format.
    
    Input format (from train.jsonl):
    {
        "instruction": "Critique this legal argument.",
        "input": "...",
        "output": { "overall_score": X, "breakdown": [...], "feedback": [...] }
    }
    
    Output format (Qwen2 chat):
    <|im_start|>system
    {system_prompt}<|im_end|>
    <|im_start|>user
    {instruction}\n{input}<|im_end|>
    <|im_start|>assistant
    {output_json}<|im_end|>
    """
    # Extract the legal argument (input field)
    user_input = example.get("input", "")
    
    # Extract and format the critique (output field)
    # The output is already a dict/JSON in your dataset
    output_data = example.get("output", {})
    assistant_output = json.dumps(output_data, indent=2, ensure_ascii=False)
    
    # Format in Qwen2 chat template
    formatted = f"""<|im_start|>system
{SYSTEM_PROMPT}<|im_end|>
<|im_start|>user
Critique this legal argument:

{user_input}<|im_end|>
<|im_start|>assistant
{assistant_output}<|im_end|>"""
    
    return {"text": formatted}


print("\n[3/6] Loading and formatting dataset...")

# Load the training dataset
# Check multiple possible locations
DATASET_PATHS = [
    "/kaggle/input/traindatasetlegal/train.jsonl",  # Most recent Kaggle upload
    "/kaggle/input/legaldataset/train.jsonl",
    "/kaggle/input/legal-dataset/train.jsonl",
    "/kaggle/input/legal-critic-dataset/train.jsonl",
    "train.jsonl",  # Same directory as script
    "../data/training_data/train.jsonl",
    "data/training_data/train.jsonl",
]

# List all available paths to help debug
print("  Checking for dataset file...")
import glob
kaggle_datasets = glob.glob("/kaggle/input/*/*.jsonl")
if kaggle_datasets:
    print(f"  Found {len(kaggle_datasets)} JSONL files in /kaggle/input:")
    for f in kaggle_datasets:
        print(f"    - {f}")
else:
    print("  No JSONL files found in /kaggle/input/*/")

DATASET_PATH = None
for path in DATASET_PATHS:
    if os.path.exists(path):
        # Check if file is not empty
        if os.path.getsize(path) > 0:
            DATASET_PATH = path
            break
        else:
            print(f"  Warning: Found {path} but file is empty!")

if DATASET_PATH is None:
    raise FileNotFoundError(
        f"Dataset not found or empty. Tried:\n  " + "\n  ".join(DATASET_PATHS) +
        "\n\nPlease upload train.jsonl as a Kaggle Dataset or place it in the same directory as this script."
    )

print(f"  Loading from: {DATASET_PATH}")
print(f"  File size: {os.path.getsize(DATASET_PATH) / 1024:.2f} KB")

# Load dataset - manually read JSONL with error handling
import json
raw_data = []
with open(DATASET_PATH, 'r', encoding='utf-8') as f:
    for line_num, line in enumerate(f, 1):
        line = line.strip()
        if not line:  # Skip empty lines
            continue
        try:
            raw_data.append(json.loads(line))
        except json.JSONDecodeError as e:
            print(f"  ⚠ Warning: Skipping line {line_num} due to JSON error: {e}")
            print(f"     First 200 chars: {line[:200]}")
            # Try to continue with other lines
            continue

if len(raw_data) == 0:
    raise ValueError("No valid JSON data found in dataset file!")

print(f"  - Loaded {len(raw_data)} valid examples")

# Convert to HuggingFace Dataset
from datasets import Dataset
dataset = Dataset.from_list(raw_data)
print(f"  - Total examples: {len(dataset)}")

# Apply formatting
dataset = dataset.map(format_prompt, remove_columns=dataset.column_names)
print(f"✓ Dataset formatted successfully")

# Preview a sample
print("\n  Sample formatted prompt (first 500 chars):")
print("-" * 40)
print(dataset[0]["text"][:500] + "...")
print("-" * 40)

# ============================================
# 5. TRAINER CONFIGURATION
# ============================================

print("\n[4/6] Configuring training arguments...")

# Output directory for checkpoints
OUTPUT_DIR = "models/fine_tuned/qwen2.5-3b-legal-critic"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Training arguments optimized for Kaggle P100 (16GB VRAM)
training_args = TrainingArguments(
    # Batch size settings
    per_device_train_batch_size=2,  # Small batch for P100
    gradient_accumulation_steps=4,  # Effective batch size = 2 * 4 = 8
    
    # Training duration
    num_train_epochs=5,  # 5 full passes over the data (optimal for 70 examples)
    warmup_steps=5,  # Gradual learning rate warmup
    
    # Learning rate
    learning_rate=2e-4,  # Standard for LoRA fine-tuning
    
    # Precision (auto-detect based on GPU)
    fp16=not torch.cuda.is_bf16_supported(),
    bf16=torch.cuda.is_bf16_supported(),
    
    # Logging
    logging_steps=1,
    logging_first_step=True,
    
    # Optimizer
    optim="adamw_8bit",  # Memory-efficient 8-bit AdamW
    weight_decay=0.01,
    
    # Gradient clipping
    max_grad_norm=1.0,
    
    # Saving
    output_dir=OUTPUT_DIR,
    save_strategy="epoch",
    save_total_limit=2,  # Keep only last 2 checkpoints
    
    # Reproducibility
    seed=42,
    
    # Disable unused features
    report_to="none",  # Disable W&B logging on Kaggle
)

print(f"✓ Training arguments configured")
print(f"  - Batch size: {training_args.per_device_train_batch_size}")
print(f"  - Gradient accumulation: {training_args.gradient_accumulation_steps}")
print(f"  - Effective batch size: {training_args.per_device_train_batch_size * training_args.gradient_accumulation_steps}")
print(f"  - Epochs: {training_args.num_train_epochs}")
print(f"  - Learning rate: {training_args.learning_rate}")
print(f"  - FP16: {training_args.fp16}, BF16: {training_args.bf16}")

# ============================================
# 6. TRAINING EXECUTION
# ============================================

print("\n[5/6] Starting training...")
print("=" * 60)

# Create the trainer
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="text",
    max_seq_length=MAX_SEQ_LENGTH,
    dataset_num_proc=2,
    packing=False,  # Don't pack multiple examples into one sequence
    args=training_args,
)

# Start training
trainer_stats = trainer.train()

print("=" * 60)
print("✓ Training completed!")
print(f"  - Training time: {trainer_stats.metrics['train_runtime']:.2f} seconds")
print(f"  - Final loss: {trainer_stats.metrics['train_loss']:.4f}")

# ============================================
# 7. SAVE THE FINAL MODEL
# ============================================

print("\n[6/6] Saving fine-tuned model...")

# Final save path for the LoRA adapter
FINAL_SAVE_PATH = "models/fine_tuned/qwen2.5-3b-legal-critic-adapter"
os.makedirs(FINAL_SAVE_PATH, exist_ok=True)

# Save the LoRA adapter weights
model.save_pretrained(FINAL_SAVE_PATH)
tokenizer.save_pretrained(FINAL_SAVE_PATH)

print(f"✓ Model saved to: {FINAL_SAVE_PATH}")
print(f"  Contents:")
for f in os.listdir(FINAL_SAVE_PATH):
    size = os.path.getsize(os.path.join(FINAL_SAVE_PATH, f)) / 1024
    print(f"    - {f} ({size:.1f} KB)")

# ============================================
# OPTIONAL: Save merged model for easier inference
# ============================================

# Uncomment the following to save a fully merged model (larger but standalone)
# MERGED_PATH = "models/fine_tuned/qwen2.5-3b-legal-critic-merged"
# model.save_pretrained_merged(MERGED_PATH, tokenizer, save_method="merged_16bit")
# print(f"✓ Merged model saved to: {MERGED_PATH}")

print("\n" + "=" * 60)
print("Fine-tuning complete!")
print("=" * 60)
print(f"""
Next steps:
1. Download the adapter from: {FINAL_SAVE_PATH}
2. For inference, load with:
   
   from unsloth import FastLanguageModel
   model, tokenizer = FastLanguageModel.from_pretrained(
       "{FINAL_SAVE_PATH}",
       max_seq_length=2048,
       load_in_4bit=True,
   )
   FastLanguageModel.for_inference(model)

3. Or use with transformers + PEFT:
   
   from transformers import AutoModelForCausalLM, AutoTokenizer
   from peft import PeftModel
   
   base_model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-3B-Instruct")
   model = PeftModel.from_pretrained(base_model, "{FINAL_SAVE_PATH}")
""")
