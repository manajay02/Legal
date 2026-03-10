"""
Merge new-format training data into train.jsonl
================================================
Converts files with the new pipeline format:
  { case_id, source_file, summary, weak_argument, critique, ... }

Into the OLD training format used by train.jsonl:
  {
    "instruction": "Critique this legal argument.",
    "input": "<plain prose argument, no markdown>",
    "output": {
      "overall_score": int,
      "strength_label": str,
      "breakdown": [{"category", "score", "reason"}, ...],
      "weaknesses": [...],
      "improvement_suggestions": [...]
    }
  }

Normalizations applied:
  - Strips markdown formatting from weak_argument (input)
  - Splits out the "Weaknesses:" section from argument text → output.weaknesses
  - Remaps rubric_score → score, rationale → reason, feedback → improvement_suggestions
  - Adds strength_label derived from overall_score
  - Drops weight/points fields not present in old format

Usage:
  python scripts/merge_new_training_data.py
  python scripts/merge_new_training_data.py --dry-run        # preview only, no writes
  python scripts/merge_new_training_data.py --input path/to/file.jsonl  # specific file
"""

import argparse
import json
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
TRAINING_DATA_DIR = BASE_DIR / "data" / "training_data"
TRAIN_JSONL = TRAINING_DATA_DIR / "train.jsonl"

INSTRUCTION = "Critique this legal argument."


# ── Text normalization ─────────────────────────────────────────────────────────

def strip_markdown(text: str) -> str:
    """Remove markdown formatting and collapse whitespace into clean prose."""
    # Remove bold/italic markers
    text = re.sub(r'\*{1,3}(.+?)\*{1,3}', r'\1', text, flags=re.DOTALL)
    # Remove ATX headers (## Heading)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    # Remove horizontal rules
    text = re.sub(r'^[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)
    # Remove leading bullet/numbered list markers
    text = re.sub(r'^\s*[\*\-\d]+[.)]\s*', '', text, flags=re.MULTILINE)
    # Collapse newlines and excess whitespace
    text = re.sub(r'\r\n|\r', '\n', text)
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    return text.strip()


# Patterns that mark the start of the appended "Weaknesses" meta-commentary
_WEAKNESS_SECTION_RE = re.compile(
    r'(?:\*{1,3}Weaknesses:\*{1,3}|#{1,4}\s*\*{0,2}Why This is Weak\*{0,2}|---\s*\n.*?Why This is Weak)',
    re.IGNORECASE | re.DOTALL,
)

# Numbered weakness items — just grab the whole line content after "N. "
_WEAKNESS_ITEM_RE = re.compile(r'^\s*\d+\.\s+(.+)$', re.MULTILINE)


def split_argument(text: str) -> tuple[str, list[str]]:
    """
    Separate the actual weak argument from the appended weakness commentary.
    Returns (clean_plain_argument, weaknesses_list).
    """
    match = _WEAKNESS_SECTION_RE.search(text)
    if match:
        argument_part = text[:match.start()]
        weakness_part = text[match.start():]
    else:
        argument_part = text
        weakness_part = ""

    # Extract weakness bullet items
    weaknesses = []
    for match in _WEAKNESS_ITEM_RE.findall(weakness_part):
        entry = strip_markdown(match)
        if entry:
            weaknesses.append(entry)

    return strip_markdown(argument_part), weaknesses


# ── Output normalization ───────────────────────────────────────────────────────

def strength_label(score: int) -> str:
    if score < 40:
        return "Weak"
    elif score < 60:
        return "Moderate"
    elif score < 80:
        return "Strong"
    return "Very Strong"


def normalize_output(critique: dict, weaknesses: list[str]) -> dict:
    """Remap new critique schema → old schema."""
    overall = critique.get("overall_score", 0)

    breakdown = []
    for item in critique.get("breakdown", []):
        breakdown.append({
            "category": item.get("category", ""),
            # new uses rubric_score; old uses score — fall back gracefully
            "score": item.get("rubric_score", item.get("score", 0)),
            "reason": item.get("rationale", item.get("reason", "")),
        })

    # new uses "feedback"; old uses "improvement_suggestions"
    suggestions = critique.get("feedback", critique.get("improvement_suggestions", []))

    return {
        "overall_score": overall,
        "strength_label": strength_label(overall),
        "breakdown": breakdown,
        "weaknesses": weaknesses,
        "improvement_suggestions": suggestions,
    }


# ── Duplicate detection ────────────────────────────────────────────────────────

def load_existing_inputs(train_file: Path) -> set:
    """Return normalised input strings already in train.jsonl."""
    existing = set()
    if not train_file.exists():
        return existing
    with open(train_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if "input" in obj:
                    # Normalise for comparison (strip markdown in case old run added raw markdown)
                    existing.add(strip_markdown(obj["input"])[:300])
            except json.JSONDecodeError:
                pass
    return existing


# ── Conversion entry point ────────────────────────────────────────────────────

def convert(record: dict) -> dict | None:
    """Convert a new-format record to the old instruction/input/output format."""
    weak_argument = record.get("weak_argument", "").strip()
    critique = record.get("critique")

    if not weak_argument or not critique:
        return None

    clean_input, weaknesses = split_argument(weak_argument)
    if not clean_input:
        return None

    return {
        "instruction": INSTRUCTION,
        "input": clean_input,
        "output": normalize_output(critique, weaknesses),
    }


def main():
    parser = argparse.ArgumentParser(description="Merge new training data into train.jsonl")
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Specific new-format .jsonl file to merge (default: all train_*.jsonl files except train.jsonl)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Preview what would be added without writing anything",
    )
    args = parser.parse_args()

    # Determine which files to merge
    if args.input:
        source_files = [Path(args.input)]
    else:
        source_files = [
            f for f in sorted(TRAINING_DATA_DIR.glob("train_*.jsonl"))
            if f.name != "train.jsonl"
        ]

    if not source_files:
        print("No new-format files found to merge.")
        sys.exit(0)

    print(f"Target file: {TRAIN_JSONL}")
    print(f"Source files: {[f.name for f in source_files]}")
    print()

    # Load existing inputs to skip duplicates
    existing_inputs = load_existing_inputs(TRAIN_JSONL)
    print(f"Existing examples in train.jsonl: {len(existing_inputs)}")

    converted = []
    skipped_duplicates = 0
    skipped_invalid = 0

    for source_file in source_files:
        print(f"\nReading: {source_file.name}")
        with open(source_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    skipped_invalid += 1
                    continue

                result = convert(record)
                if result is None:
                    skipped_invalid += 1
                    continue

                if result["input"] in existing_inputs:
                    skipped_duplicates += 1
                    continue

                converted.append(result)
                existing_inputs.add(result["input"])  # prevent dupes across source files

    print(f"\nNew examples to add:  {len(converted)}")
    print(f"Skipped (duplicates): {skipped_duplicates}")
    print(f"Skipped (invalid):    {skipped_invalid}")

    if not converted:
        print("\nNothing new to add.")
        sys.exit(0)

    if args.dry_run:
        print("\n--dry-run: no changes written.")
        print("\nSample of first converted record:")
        sample = converted[0]
        out = sample["output"]
        print(f"  input (first 150 chars): {sample['input'][:150]}...")
        print(f"  overall_score:  {out['overall_score']}")
        print(f"  strength_label: {out['strength_label']}")
        print(f"  breakdown categories: {[b['category'] for b in out['breakdown']]}")
        print(f"  weaknesses ({len(out['weaknesses'])}): {out['weaknesses'][:2]}")
        print(f"  improvement_suggestions ({len(out['improvement_suggestions'])}): {out['improvement_suggestions'][:1]}")
        sys.exit(0)

    # Append to train.jsonl
    with open(TRAIN_JSONL, "a", encoding="utf-8") as f:
        for record in converted:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"\n✓ Appended {len(converted)} new examples to {TRAIN_JSONL}")
    print(f"  Total examples now: {len(existing_inputs)}")


if __name__ == "__main__":
    main()
