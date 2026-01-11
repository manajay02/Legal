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

Author: LegalScoreModel Team
Date: January 2026
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

from app.services.llm_service import get_gemini_service
from app.core.config import settings


# ============================================
# Configuration
# ============================================

BASE_DIR = Path(__file__).parent.parent
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

---

JUDGMENT SUMMARY:
{summary}

---

WEAK PLAINTIFF ARGUMENT:
"""


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


def generate_training_example(
    text_file: Path,
    gemini_service,
    temperature: float = 0.7
) -> Optional[Dict[str, Any]]:
    """
    Generate a complete training example from a judgment text file.
    
    Three-step process:
    1. Summarize the judgment
    2. Generate a weak argument based on the summary
    3. Generate a detailed JSON critique of the weak argument
    
    Args:
        text_file: Path to the extracted judgment text file
        gemini_service: Initialized Gemini service
        temperature: Sampling temperature for generation
        
    Returns:
        Training example dictionary, or None if generation fails
    """
    case_id = text_file.stem
    logger.info(f"\n{'='*60}")
    logger.info(f"Processing: {case_id}")
    logger.info(f"{'='*60}")
    
    try:
        # Load the judgment text
        judgment_text = load_judgment_text(text_file)
        logger.info(f"[1/3] Loaded judgment ({len(judgment_text):,} chars)")
        
        # ============================================
        # STEP 1: Summarize Judgment
        # ============================================
        logger.info("[2/3] Summarizing judgment with Gemini...")
        
        step1_prompt = STEP1_SUMMARIZE_PROMPT.format(
            judgment_text=judgment_text
        )
        
        summary = gemini_service.get_analysis_from_gemini(
            prompt=step1_prompt,
            temperature=0.3  # Lower temperature for factual summarization
        )
        
        logger.info(f"  ✓ Summary generated ({len(summary)} chars)")
        
        # Rate limiting: Free tier allows 15 requests/min (4 sec/request)
        time.sleep(4)
        
        # ============================================
        # STEP 2: Generate Weak Argument
        # ============================================
        logger.info("[3/3] Generating weak plaintiff argument...")
        
        step2_prompt = STEP2_WEAK_ARGUMENT_PROMPT.format(
            summary=summary
        )
        
        weak_argument = gemini_service.get_analysis_from_gemini(
            prompt=step2_prompt,
            temperature=temperature
        )
        
        logger.info(f"  ✓ Weak argument generated ({len(weak_argument)} chars)")
        
        # Rate limiting delay
        time.sleep(4)
        
        # ============================================
        # STEP 3: Generate JSON Critique
        # ============================================
        logger.info("[4/3] Generating JSON critique...")
        
        rubric_table = create_rubric_table()
        step3_prompt = STEP3_CRITIQUE_PROMPT.format(
            rubric_table=rubric_table,
            weak_argument=weak_argument
        )
        
        critique = gemini_service.get_json_from_gemini(
            prompt=step3_prompt,
            temperature=0.2,  # Low temperature for structured output
            max_tokens=4096   # Ensure enough tokens for full JSON response
        )
        
        logger.info(f"  ✓ Critique generated (score: {critique.get('overall_score', 'N/A')})")
        
        # Validate the JSON structure
        if not validate_json_structure(critique):
            logger.error("  ✗ Invalid JSON structure, skipping example")
            return None
        
        # ============================================
        # Construct Training Example
        # ============================================
        training_example = {
            "case_id": case_id,
            "source_file": text_file.name,
            "generated_at": datetime.now().isoformat(),
            "summary": summary,
            "weak_argument": weak_argument,
            "critique": critique,
            "metadata": {
                "summary_length": len(summary),
                "argument_length": len(weak_argument),
                "overall_score": critique["overall_score"]
            }
        }
        
        logger.info(f"✓ Training example created successfully")
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
        description="Generate training data from Supreme Court judgments using Gemini"
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
        help="Sampling temperature for Gemini (0.0-1.0)"
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("Dataset Generation Pipeline Started")
    logger.info("Teacher Model: Google Gemini 1.5 Flash")
    logger.info("Student Model: Qwen2-1.5B-Instruct (target)")
    logger.info("=" * 60)
    
    # Initialize Gemini service
    try:
        gemini_service = get_gemini_service()
        logger.info("\n✓ Gemini service initialized")
        
        # Health check
        if not gemini_service.check_health():
            logger.error("Gemini health check failed. Please verify your API key.")
            return
        
    except Exception as e:
        logger.error(f"Failed to initialize Gemini service: {str(e)}")
        logger.error("Make sure GOOGLE_API_KEY is set in your .env file")
        logger.error("Get your API key from: https://makersuite.google.com/app/apikey")
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
    
    # Apply limit if specified
    if args.limit:
        text_files = text_files[:args.limit]
        logger.info(f"Limiting to {len(text_files)} files (--limit {args.limit})")
    
    # Process each file
    training_examples = []
    failed_files = []
    
    start_time = time.time()
    
    for idx, text_file in enumerate(text_files, 1):
        logger.info(f"\n[{idx}/{len(text_files)}] Processing: {text_file.stem}")
        
        try:
            example = generate_training_example(
                text_file=text_file,
                gemini_service=gemini_service,
                temperature=args.temperature
            )
            
            if example:
                training_examples.append(example)
                logger.info(f"✓ Success ({len(training_examples)}/{idx} examples generated)")
            else:
                failed_files.append(text_file.stem)
                logger.warning(f"✗ Failed to generate example")
            
        except Exception as e:
            logger.error(f"✗ Error processing {text_file.stem}: {str(e)}")
            failed_files.append(text_file.stem)
        
        # Rate limiting: small delay between API calls
        if idx < len(text_files):
            time.sleep(2)  # 2 seconds between files
    
    # Calculate statistics
    total_time = time.time() - start_time
    avg_time = total_time / len(text_files) if text_files else 0
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save training data
    if training_examples:
        train_file = TRAINING_DATA_DIR / f"train_{timestamp}.jsonl"
        save_training_data(training_examples, train_file)
    
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
    logger.info(f"Total files processed: {len(text_files)}")
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