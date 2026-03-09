"""
Merge all training JSONL files and prepare a clean dataset for Kaggle upload.

Usage (run after prepare_training_data.py finishes):
  python scripts/prepare_kaggle_upload.py

What it does:
  1. Merges civil_cases.jsonl + training_data.jsonl → combined_training.jsonl
  2. Deduplicates by filename (_meta.filename) and by instruction+input hash
  3. Validates every JSON line
  4. Writes the merged file to data/training/combined_training.jsonl
  5. Creates a Kaggle dataset metadata file (dataset-metadata.json)
  6. Prints upload instructions

The notebook expects: /kaggle/input/civilmodel-training-data/civil_cases.jsonl
Point DATASET_PATH in the notebook to combined_training.jsonl for best results.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import get_settings

settings = get_settings()

# ─── Sources ──────────────────────────────────────────────────────────────────
SOURCE_FILES = [
    settings.TRAINING_DIR / "civil_cases.jsonl",   # Real OCR → LLM extraction examples
    settings.TRAINING_DIR / "training_data.jsonl",  # Synthetic / hand-crafted examples
]
OUTPUT_FILE = settings.TRAINING_DIR / "combined_training.jsonl"
KAGGLE_METADATA_FILE = settings.TRAINING_DIR / "dataset-metadata.json"
KAGGLE_UPLOAD_DIR = settings.TRAINING_DIR / "kaggle_upload"


def _entry_key(obj: dict) -> str:
    """Unique key: prefer _meta.filename, otherwise hash of instruction+input."""
    meta = obj.get("_meta")
    if isinstance(meta, dict) and meta.get("filename"):
        return f"file:{meta['filename']}"
    # For synthetic entries without _meta, hash the content
    raw = str(obj.get("instruction", "")) + str(obj.get("input", ""))[:200]
    return "hash:" + hashlib.md5(raw.encode()).hexdigest()


def load_jsonl(path: Path) -> list[dict]:
    entries = []
    skipped = 0
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                entries.append(obj)
            except json.JSONDecodeError as e:
                print(f"  [WARN] {path.name} line {i}: bad JSON – {e}")
                skipped += 1
    if skipped:
        print(f"  [WARN] Skipped {skipped} bad lines in {path.name}")
    return entries


def validate_entry(obj: dict) -> tuple[bool, str]:
    """Check that an entry has usable content — supports both formats:
    - instruction style: {"instruction", "input", "output"}
    - legacy style:      {"metadata", "sections"}
    """
    if not isinstance(obj, dict):
        return False, "not a dict"

    # Format 1: instruction style (civil_cases.jsonl)
    if "input" in obj and "output" in obj:
        if len(str(obj.get("input", ""))) < 50:
            return False, f"input too short ({len(str(obj.get('input','')))} chars)"
        try:
            json.loads(str(obj["output"]))
        except (json.JSONDecodeError, TypeError):
            return False, "output is not valid JSON"
        return True, "ok"

    # Format 2: legacy metadata+sections style (training_data.jsonl)
    if "metadata" in obj and "sections" in obj:
        if not isinstance(obj.get("metadata"), dict):
            return False, "metadata is not a dict"
        if not isinstance(obj.get("sections"), list):
            return False, "sections is not a list"
        return True, "ok"

    return False, "unrecognised format (needs input+output or metadata+sections)"


def main() -> None:
    print("=" * 60)
    print("CivilModel — Kaggle Training Data Preparation")
    print("=" * 60)

    all_entries: list[dict] = []
    seen_keys: set[str] = set()

    for src in SOURCE_FILES:
        if not src.exists():
            print(f"\n[SKIP] {src.name} not found — skipping")
            continue
        print(f"\n[LOAD] {src.name}")
        entries = load_jsonl(src)
        print(f"       Loaded {len(entries)} raw entries")

        added = 0
        dupes = 0
        invalid = 0
        for obj in entries:
            ok, reason = validate_entry(obj)
            if not ok:
                print(f"  [INVALID] {reason} — source: {(obj.get('_meta') or {}).get('filename', '?')}")
                invalid += 1
                continue
            key = _entry_key(obj)
            if key in seen_keys:
                dupes += 1
                continue
            seen_keys.add(key)
            all_entries.append(obj)
            added += 1

        print(f"       Added: {added} | Duplicates skipped: {dupes} | Invalid: {invalid}")

    if not all_entries:
        print("\n[ERROR] No valid entries found. Run prepare_training_data.py first.")
        sys.exit(1)

    # ─── Write combined JSONL ──────────────────────────────────────────────────
    print(f"\n[WRITE] {OUTPUT_FILE.name}")
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        for obj in all_entries:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
    print(f"        Wrote {len(all_entries)} entries ({OUTPUT_FILE.stat().st_size / 1024:.1f} KB)")

    # ─── Kaggle upload folder ──────────────────────────────────────────────────
    KAGGLE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # Copy the combined file as civil_cases.jsonl so the notebook path works unchanged
    dst = KAGGLE_UPLOAD_DIR / "civil_cases.jsonl"
    shutil.copy2(OUTPUT_FILE, dst)
    print(f"\n[COPY]  → {dst}")

    # ─── Kaggle dataset-metadata.json ─────────────────────────────────────────
    metadata = {
        "title": "CivilModel Training Data",
        "id": "youruser/civilmodel-training-data",
        "licenses": [{"name": "other"}],
    }
    meta_path = KAGGLE_UPLOAD_DIR / "dataset-metadata.json"
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"[META]  → {meta_path}")

    # ─── Summary ──────────────────────────────────────────────────────────────
    real = sum(1 for e in all_entries if isinstance(e.get("_meta"), dict))
    synthetic = len(all_entries) - real

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Total entries   : {len(all_entries)}")
    print(f"  Real (from PDFs): {real}")
    print(f"  Synthetic       : {synthetic}")
    print(f"  Output file     : {OUTPUT_FILE}")
    print(f"  Kaggle folder   : {KAGGLE_UPLOAD_DIR}")

    # Epoch recommendation
    if len(all_entries) >= 150:
        epochs = "3-5"
    elif len(all_entries) >= 80:
        epochs = "2-3"
    else:
        epochs = "1-2"

    print(f"\n  Recommended epochs in notebook: {epochs}")
    print(f"  (Set num_train_epochs={epochs.split('-')[1]} in the notebook)")

    print("\n" + "=" * 60)
    print("NEXT STEPS — Upload to Kaggle")
    print("=" * 60)
    print("""
1. Install Kaggle CLI (if not already):
     pip install kaggle

2. Place your kaggle.json API token at:
     C:\\Users\\<you>\\.kaggle\\kaggle.json

3. First-time dataset creation:
     cd data/training/kaggle_upload
     kaggle datasets create -p .

   Subsequent updates (add new data):
     kaggle datasets version -p . -m "Added more Court of Appeal and HCC cases"

4. In the notebook, DATASET_PATH is already set to:
     /kaggle/input/civilmodel-training-data/civil_cases.jsonl
   No change needed.

5. After training, download the LoRA adapter:
     kaggle kernels output <your-notebook-slug> -p ./models/civilmodel_qwen3b_v2
""")


if __name__ == "__main__":
    main()
