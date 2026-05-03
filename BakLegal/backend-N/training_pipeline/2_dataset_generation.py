"""
Dataset Generation Pipeline for Legal Argument Grading
=======================================================

Teacher-Student Training Data Generation:
- Teacher Model: Google Gemini 1.5 Flash (high-quality, free tier)
- Student Model: Qwen2-1.5B-Instruct (our target for fine-tuning)

This script uses the extracted Supreme Court judgments to generate
synthetic training examples with weak arguments and detailed critiques.

Three-Step Prompting Chain:
1. Summarize judgment → Extract key legal principles
2. Generate weak argument → Create a flawed plaintiff argument
3. Generate JSON critique → Teacher model scores the weak argument

"""

import os
import sys
import json
import logging
import argparse
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.llm_service import get_gemini_service, get_openrouter_service, get_deepseek_service
from app.core.config import settings


# ============================================
# Configuration
# ============================================

BASE_DIR = Path(__file__).parent.parent
RAW_PDF_DIR = BASE_DIR / "data" / "raw_pdfs"
PROCESSED_TEXT_DIR = BASE_DIR / "data" / "processed_text"
TRAINING_DATA_DIR = BASE_DIR / "data" / "training_data"
METADATA_DIR = BASE_DIR / "data" / "metadata"
LOG_DIR = BASE_DIR / "logs" / "training"

# Grading categories (from grading_schema.py)
GRADING_CATEGORIES = [
    {"category": "Issue & Claim Clarity", "weight": 10},
    {"category": "Facts & Chronology", "weight": 15},
    {"category": "Legal Basis / Elements", "weight": 20},
    {"category": "Evidence & Support", "weight": 15},
    {"category": "Reasoning & Logic", "weight": 15},
    {"category": "Counterarguments & Rebuttal", "weight": 10},
    {"category": "Remedies & Quantification", "weight": 10},
    {"category": "Structure & Professionalism", "weight": 5}
]


# ============================================
# Setup Logging
# ============================================

LOG_DIR.mkdir(parents=True, exist_ok=True)
log_file = LOG_DIR / f"dataset_generation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ============================================
# Prompt Templates
# ============================================

STEP1_SUMMARIZE_PROMPT = """You are a legal expert analyzing a Supreme Court judgment from Sri Lanka.

Your task: Extract the key facts, legal issues, and court's reasoning from the judgment below.

Provide a structured summary in the following format:

**Case Overview:**
[Brief 2-3 sentence overview]

**Key Facts:**
- [Fact 1]
- [Fact 2]
- [Fact 3]
[etc.]

**Legal Issues:**
- [Issue 1]
- [Issue 2]
[etc.]

**Court's Reasoning:**
- [Key point 1]
- [Key point 2]
[etc.]

**Outcome:**
[Court's decision in 1-2 sentences]

---

JUDGMENT TEXT:
{judgment_text}
"""


STEP2_WEAK_ARGUMENT_PROMPT = """You are a law student writing a WEAK plaintiff argument for a civil case.

Based on the judgment summary below, create a flawed plaintiff's written submission that exhibits the following weaknesses:

1. **Vague claim** - unclear relief sought
2. **Poor fact presentation** - missing timeline, lacks specificity
3. **Weak legal basis** - fails to cite relevant laws or precedents
4. **No evidence references** - makes assertions without documentary support
5. **Logical gaps** - reasoning has holes or contradictions
6. **Ignores counterarguments** - doesn't anticipate defendant's position
7. **Unclear remedies** - doesn't quantify damages or specify relief properly
8. **Poor structure** - disorganized, unprofessional tone

Your weak argument should be 300-500 words and sound like a poorly prepared submission.

{variant_instruction}
---

JUDGMENT SUMMARY:
{summary}

---

WEAK PLAINTIFF ARGUMENT:
"""

# Different focuses for generating varied weak arguments from the same case
VARIANT_INSTRUCTIONS = [
    # v0 – default (all weaknesses equally)
    "",
    # v1 – especially weak on jurisdiction / procedural grounds
    "Focus especially on procedural and jurisdictional errors: wrong court, time-bar issues, wrong parties named, failure to exhaust remedies.\n\n",
    # v2 – especially weak on evidence / proof
    "Focus especially on evidentiary failures: no documentary exhibits, hearsay reliance, unsworn assertions, missing expert evidence.\n\n",
    # v3 – especially weak on legal authority
    "Focus especially on misapplied law: cite irrelevant sections, confuse civil and criminal standards, ignore binding precedents.\n\n",
    # v4 – especially weak on remedies / quantum
    "Focus especially on remedy and quantification failures: unspecified damages, no calculation shown, wrong type of relief requested.\n\n",
    # v5 – defendant perspective gone wrong (plaintiff arguing from wrong side)
    "Make the plaintiff inadvertently argue facts that actually support the defendant's case, contradicting their own claim.\n\n",
    # v6 – emotional / non-legal language
    "Use excessively emotional, non-legal language throughout — appeals to sympathy rather than law, personal attacks, dramatic assertions.\n\n",
    # v7 – contradictory timeline / inconsistent facts
    "Introduce internal contradictions in dates and facts: the timeline should be inconsistent and self-contradictory.\n\n",
]


STEP3_CRITIQUE_PROMPT = """You are an expert legal argument critic for Sri Lankan civil cases.

Your task: Analyze the weak argument below and provide a detailed JSON critique following this exact rubric.

**Grading Rubric (100 points total):**

{rubric_table}

**Scoring Scale (0-5 for each category):**
- 0 = Missing/Not addressed
- 1 = Very weak (minimal effort)
- 2 = Weak (basic attempt, major gaps)
- 3 = Adequate (satisfactory, some gaps)
- 4 = Strong (well-done, minor gaps)
- 5 = Excellent (exceptional, comprehensive)

**Points Calculation:**
Points = (rubric_score / 5) × category_weight

---

WEAK ARGUMENT TO CRITIQUE:
{weak_argument}

---

**Important Instructions:**
1. Provide ONLY a valid JSON response (no additional text)
2. Use the exact category names from the rubric
3. Each category must have: weight, rubric_score (0-5), points (calculated), and rationale
4. Include overall_score (sum of all points)
5. Add a brief feedback section with 2-3 improvement suggestions

**Required JSON Format:**
```json
{{
  "overall_score": <number 0-100>,
  "breakdown": [
    {{
      "category": "Issue & Claim Clarity",
      "weight": 10,
      "rubric_score": <0-5>,
      "points": <calculated>,
      "rationale": "<brief explanation>"
    }},
    ... (all 8 categories)
  ],
  "feedback": [
    "<improvement suggestion 1>",
    "<improvement suggestion 2>",
    "<improvement suggestion 3>"
  ]
}}
```

Provide ONLY the JSON response:
"""


# ============================================
# Helper Functions
# ============================================

def create_rubric_table() -> str:
    """Create a formatted rubric table for the prompt."""
    lines = [
        "| Category | Weight | Description |",
        "|----------|--------|-------------|"
    ]
    
    for cat in GRADING_CATEGORIES:
        lines.append(f"| {cat['category']} | {cat['weight']} pts | |")
    
    return "\n".join(lines)


def load_judgment_text(text_file: Path) -> str:
    """
    Load extracted judgment text from a file.
    
    Args:
        text_file: Path to the .txt file
        
    Returns:
        Text content
    """
    try:
        with open(text_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Truncate if too long (Gemini has token limits)
        max_chars = 20000  # ~5000 tokens
        if len(text) > max_chars:
            logger.warning(f"  Truncating {text_file.name} ({len(text)} → {max_chars} chars)")
            text = text[:max_chars] + "\n\n[... truncated ...]"
        
        return text
        
    except Exception as e:
        logger.error(f"Error loading {text_file.name}: {str(e)}")
        raise


def validate_json_structure(critique: Dict[str, Any]) -> bool:
    """
    Validate that the critique JSON has the correct structure.
    
    Args:
        critique: Parsed JSON dictionary
        
    Returns:
        True if valid, False otherwise
    """
    required_keys = ["overall_score", "breakdown", "feedback"]
    
    # Check top-level keys
    if not all(key in critique for key in required_keys):
        logger.error("Missing required top-level keys in critique")
        return False
    
    # Check overall_score
    if not isinstance(critique["overall_score"], (int, float)):
        logger.error("overall_score is not a number")
        return False
    
    if not (0 <= critique["overall_score"] <= 100):
        logger.error(f"overall_score out of range: {critique['overall_score']}")
        return False
    
    # Check breakdown
    if not isinstance(critique["breakdown"], list):
        logger.error("breakdown is not a list")
        return False
    
    if len(critique["breakdown"]) != len(GRADING_CATEGORIES):
        logger.error(f"Expected {len(GRADING_CATEGORIES)} categories, got {len(critique['breakdown'])}")
        return False
    
    # Check each category
    for item in critique["breakdown"]:
        required_category_keys = ["category", "weight", "rubric_score", "points", "rationale"]
        if not all(key in item for key in required_category_keys):
            logger.error(f"Missing keys in category: {item}")
            return False
        
        if not (0 <= item["rubric_score"] <= 5):
            logger.error(f"Invalid rubric_score: {item['rubric_score']}")
            return False
    
    # Check feedback
    if not isinstance(critique["feedback"], list):
        logger.error("feedback is not a list")
        return False
    
    if len(critique["feedback"]) < 1:
        logger.error("feedback is empty")
        return False
    
    logger.debug("✓ JSON structure validation passed")
    return True


def summarize_judgment(text_file: Path, gemini_service, temperature: float = 0.3) -> str:
    """Summarize a judgment text file. Returns summary string."""
    judgment_text = load_judgment_text(text_file)
    logger.info(f"  Loaded judgment ({len(judgment_text):,} chars)")
    step1_prompt = STEP1_SUMMARIZE_PROMPT.format(judgment_text=judgment_text)
    summary = gemini_service.get_analysis_from_gemini(prompt=step1_prompt, temperature=temperature)
    logger.info(f"  ✓ Summary generated ({len(summary):,} chars)")
    return summary


def generate_training_example(
    text_file: Path,
    gemini_service,
    temperature: float = 0.7,
    variant_index: int = 0,
    summary: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Generate one training example from a judgment.

    If `summary` is provided it is reused (avoids re-summarising for multi-variant runs).
    `variant_index` selects a different weak-argument focus from VARIANT_INSTRUCTIONS.
    The case_id is stored as  <stem>__v<variant_index>  so each variant is tracked separately.
    """
    case_id = f"{text_file.stem}__v{variant_index}"
    logger.info(f"\n{'='*60}")
    logger.info(f"Processing: {text_file.stem}  [variant {variant_index}]")
    logger.info(f"{'='*60}")

    try:
        # ============================================
        # STEP 1: Summarize Judgment (skip if already done)
        # ============================================
        if summary is None:
            logger.info("[1/3] Summarizing judgment...")
            summary = summarize_judgment(text_file, gemini_service)
            time.sleep(4)
        else:
            logger.info("[1/3] Reusing cached summary")

        # ============================================
        # STEP 2: Generate Weak Argument
        # ============================================
        logger.info("[2/3] Generating weak plaintiff argument...")
        variant_instruction = VARIANT_INSTRUCTIONS[variant_index % len(VARIANT_INSTRUCTIONS)]
        step2_prompt = STEP2_WEAK_ARGUMENT_PROMPT.format(
            summary=summary,
            variant_instruction=variant_instruction,
        )
        # Slightly raise temperature for later variants to increase diversity
        arg_temp = min(temperature + variant_index * 0.05, 1.0)
        weak_argument = gemini_service.get_analysis_from_gemini(prompt=step2_prompt, temperature=arg_temp)
        logger.info(f"  ✓ Weak argument generated ({len(weak_argument):,} chars)")
        time.sleep(4)

        # ============================================
        # STEP 3: Generate JSON Critique
        # ============================================
        logger.info("[3/3] Generating JSON critique...")
        rubric_table = create_rubric_table()
        step3_prompt = STEP3_CRITIQUE_PROMPT.format(
            rubric_table=rubric_table,
            weak_argument=weak_argument,
        )
        critique = gemini_service.get_json_from_gemini(
            prompt=step3_prompt,
            temperature=0.2,
            max_tokens=4096,
        )
        logger.info(f"  ✓ Critique generated (score: {critique.get('overall_score', 'N/A')})")

        if not validate_json_structure(critique):
            logger.error("  ✗ Invalid JSON structure, skipping example")
            return None

        training_example = {
            "case_id": case_id,
            "source_file": text_file.name,
            "variant_index": variant_index,
            "generated_at": datetime.now().isoformat(),
            "summary": summary,
            "weak_argument": weak_argument,
            "critique": critique,
            "metadata": {
                "summary_length": len(summary),
                "argument_length": len(weak_argument),
                "overall_score": critique["overall_score"],
            },
        }
        logger.info("✓ Training example created successfully")
        return training_example

    except Exception as e:
        logger.error(f"✗ Failed to generate training example: {str(e)}")
        return None


def save_training_data(
    examples: List[Dict[str, Any]],
    output_file: Path
):
    """
    Save training examples to a JSONL file (one JSON per line).
    
    Args:
        examples: List of training example dictionaries
        output_file: Path to output .jsonl file
    """
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for example in examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')
    
    logger.info(f"\n✓ Saved {len(examples)} training examples to: {output_file}")


def save_metadata(
    metadata: Dict[str, Any],
    output_file: Path
):
    """
    Save generation metadata to a JSON file.
    
    Args:
        metadata: Metadata dictionary
        output_file: Path to output .json file
    """
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✓ Saved metadata to: {output_file}")


# ============================================
# Main Execution
# ============================================

def main():
    """
    Main execution function for dataset generation pipeline.
    """
    parser = argparse.ArgumentParser(
        description="Generate training data from Supreme Court judgments"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of files to process (for testing)"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Sampling temperature (0.0-1.0)"
    )
    parser.add_argument(
        "--provider",
        type=str,
        default="openrouter",
        choices=["gemini", "openrouter", "deepseek"],
        help="LLM provider to use: 'gemini', 'openrouter', or 'deepseek' (default: openrouter)"
    )
    parser.add_argument(
        "--only-from-raw-pdfs",
        action="store_true",
        default=False,
        help="Only process .txt files whose source PDF exists in data/raw_pdfs/ (skip all others)"
    )
    parser.add_argument(
        "--examples-per-file",
        type=int,
        default=1,
        dest="examples_per_file",
        help="Number of training examples to generate per judgment file (default: 1, max useful: 8)"
    )

    args = parser.parse_args()

    # Initialize the chosen LLM service
    if args.provider == "deepseek":
        logger.info("=" * 60)
        logger.info("Dataset Generation Pipeline Started")
        logger.info(f"Teacher Model: DeepSeek ({settings.DEEPSEEK_MODEL_NAME})")
        logger.info("Student Model: Qwen2-1.5B-Instruct (target)")
        logger.info("=" * 60)
        try:
            gemini_service = get_deepseek_service()
            logger.info("\n✓ DeepSeek service initialized")
            if not gemini_service.check_health():
                logger.error("DeepSeek health check failed. Please verify your API key.")
                return
        except Exception as e:
            logger.error(f"Failed to initialize DeepSeek service: {str(e)}")
            logger.error("Make sure DEEPSEEK_API_KEY is set in your .env file")
            logger.error("Get your key from: https://platform.deepseek.com/")
            return
    elif args.provider == "openrouter":
        logger.info("=" * 60)
        logger.info("Dataset Generation Pipeline Started")
        logger.info(f"Teacher Model: OpenRouter ({settings.OPENROUTER_MODEL})")
        logger.info("Student Model: Qwen2-1.5B-Instruct (target)")
        logger.info("=" * 60)
        try:
            gemini_service = get_openrouter_service()
            logger.info("\n✓ OpenRouter service initialized")
            if not gemini_service.check_health():
                logger.error("OpenRouter health check failed. Please verify your API key.")
                return
        except Exception as e:
            logger.error(f"Failed to initialize OpenRouter service: {str(e)}")
            logger.error("Make sure OPENROUTER_API_KEY is set in your .env file")
            logger.error("Get your key from: https://openrouter.ai/")
            return
    else:
        logger.info("=" * 60)
        logger.info("Dataset Generation Pipeline Started")
        logger.info(f"Teacher Model: Google Gemini ({settings.GEMINI_MODEL_NAME})")
        logger.info("Student Model: Qwen2-1.5B-Instruct (target)")
        logger.info("=" * 60)
        try:
            gemini_service = get_gemini_service()
            logger.info("\n✓ Gemini service initialized")
            if not gemini_service.check_health():
                logger.error("Gemini health check failed. Please verify your API key.")
                return
        except Exception as e:
            logger.error(f"Failed to initialize Gemini service: {str(e)}")
            logger.error("Make sure GOOGLE_API_KEY is set in your .env file")
            logger.error("Get your key from: https://aistudio.google.com/apikey")
            return
    
    # Get all processed text files
    if not PROCESSED_TEXT_DIR.exists():
        logger.error(f"Processed text directory not found: {PROCESSED_TEXT_DIR}")
        logger.error("Please run 1_ocr_extraction.py first")
        return
    
    text_files = sorted(list(PROCESSED_TEXT_DIR.glob("*.txt")))
    
    if not text_files:
        logger.error("No processed text files found")
        logger.error("Please run 1_ocr_extraction.py first")
        return
    
    logger.info(f"\nFound {len(text_files)} processed judgment files")

    # Skip variant IDs already present in any training data JSONL
    # IDs are stored as  <stem>__v<n>  (new format) or bare <stem> (legacy, counts as v0)
    already_done: set = set()
    for jsonl_file in TRAINING_DATA_DIR.glob("*.jsonl"):
        with open(jsonl_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if "case_id" in obj:
                        cid = obj["case_id"]
                        already_done.add(cid)
                        # Legacy entries have bare stem — treat as variant 0
                        if "__v" not in cid:
                            already_done.add(f"{cid}__v0")
                except json.JSONDecodeError:
                    pass

    examples_per_file = max(1, args.examples_per_file)

    # A file is fully done only when all requested variants exist
    def _variants_needed(stem: str) -> List[int]:
        return [
            i for i in range(examples_per_file)
            if f"{stem}__v{i}" not in already_done
        ]

    text_files_with_variants = [
        (f, _variants_needed(f.stem)) for f in text_files
    ]
    text_files_with_variants = [(f, vs) for f, vs in text_files_with_variants if vs]

    skipped = len(text_files) - len(text_files_with_variants)
    if skipped:
        logger.info(f"Skipping {skipped} fully-processed files")
    text_files = text_files  # keep original for length reference

    # If --only-from-raw-pdfs, restrict to files whose PDF is in raw_pdfs/
    if args.only_from_raw_pdfs:
        if not RAW_PDF_DIR.exists():
            logger.error(f"raw_pdfs directory not found: {RAW_PDF_DIR}")
            return
        raw_pdf_stems = {p.stem for p in RAW_PDF_DIR.glob("*.pdf")}
        before = len(text_files)
        text_files = [f for f in text_files if f.stem in raw_pdf_stems]
        logger.info(f"--only-from-raw-pdfs: keeping {len(text_files)} of {before} files (matched PDFs in raw_pdfs/)")
        if not text_files:
            logger.info("No matching .txt files found for PDFs in raw_pdfs/. Nothing to do.")
            return

    if not text_files_with_variants:
        logger.info("All files already processed. Nothing to do.")
        return

    total_variants = sum(len(vs) for _, vs in text_files_with_variants)
    logger.info(f"Files to process: {len(text_files_with_variants)}  ({total_variants} examples total, {examples_per_file} per file)")

    # Apply limit if specified (limits the number of files, not variants)
    if args.limit:
        text_files_with_variants = text_files_with_variants[:args.limit]
        total_variants = sum(len(vs) for _, vs in text_files_with_variants)
        logger.info(f"Limiting to {len(text_files_with_variants)} files (--limit {args.limit})")

    # Output file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    train_file = TRAINING_DATA_DIR / f"train_{timestamp}.jsonl"
    train_file.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Saving to: {train_file}")

    # Process each file
    training_examples = []
    failed_files = []
    example_count = 0

    start_time = time.time()

    for file_idx, (text_file, variants) in enumerate(text_files_with_variants, 1):
        logger.info(f"\n[{file_idx}/{len(text_files_with_variants)}] {text_file.stem}  ({len(variants)} variant(s) needed)")

        # Summarize the judgment once, then reuse for all variants of this file
        cached_summary: Optional[str] = None
        if len(variants) > 1 or variants[0] != 0:
            # We'll summarize on the first variant call; cache it for the rest
            pass

        for variant_idx in variants:
            example_count += 1
            logger.info(f"  → variant {variant_idx}  (example {example_count}/{total_variants})")
            try:
                example = generate_training_example(
                    text_file=text_file,
                    gemini_service=gemini_service,
                    temperature=args.temperature,
                    variant_index=variant_idx,
                    summary=cached_summary,
                )

                if example:
                    # Cache the summary for the next variant of this file
                    if cached_summary is None:
                        cached_summary = example["summary"]
                    training_examples.append(example)
                    with open(train_file, "a", encoding="utf-8") as f:
                        f.write(json.dumps(example, ensure_ascii=False) + "\n")
                    logger.info(f"  ✓ Success ({len(training_examples)} total examples so far)")
                else:
                    failed_files.append(f"{text_file.stem}__v{variant_idx}")
                    logger.warning("  ✗ Failed to generate example")

            except Exception as e:
                logger.error(f"  ✗ Error on variant {variant_idx}: {str(e)}")
                failed_files.append(f"{text_file.stem}__v{variant_idx}")

            # Brief delay between variants
            time.sleep(2)

        # Slightly longer pause between files
        if file_idx < len(text_files_with_variants):
            time.sleep(2)
    
    # Calculate statistics
    total_time = time.time() - start_time
    avg_time = total_time / len(text_files) if text_files else 0

    # Save metadata
    metadata = {
        "generation_date": datetime.now().isoformat(),
        "teacher_model": gemini_service.model_name,
        "temperature": args.temperature,
        "total_files_processed": len(text_files),
        "successful_examples": len(training_examples),
        "failed_files": failed_files,
        "total_time_seconds": total_time,
        "average_time_per_file": avg_time,
        "output_file": str(train_file) if training_examples else None
    }
    
    metadata_file = METADATA_DIR / f"dataset_generation_{timestamp}.json"
    save_metadata(metadata, metadata_file)
    
    # Final summary
    logger.info("\n" + "=" * 60)
    logger.info("Dataset Generation Pipeline Completed")
    logger.info("=" * 60)
    logger.info(f"Total files processed: {len(text_files_with_variants)}")
    logger.info(f"Successful examples: {len(training_examples)}")
    logger.info(f"Failed files: {len(failed_files)}")
    logger.info(f"Total time: {total_time/60:.1f} minutes")
    logger.info(f"Average time per file: {avg_time:.1f} seconds")
    
    if training_examples:
        logger.info(f"\n✓ Training data saved to: {train_file}")
        logger.info(f"  Total examples: {len(training_examples)}")
        logger.info(f"  Average score: {sum(ex['critique']['overall_score'] for ex in training_examples) / len(training_examples):.1f}")
    
    if failed_files:
        logger.warning(f"\n⚠ {len(failed_files)} files failed:")
        for failed in failed_files[:10]:  # Show first 10
            logger.warning(f"  - {failed}")
        if len(failed_files) > 10:
            logger.warning(f"  ... and {len(failed_files) - 10} more")
    
    logger.info("\n" + "=" * 60)


if __name__ == "__main__":
    main()