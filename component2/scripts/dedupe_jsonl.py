"""Dedupe a JSONL file by exact record content.

Useful for preventing duplicated examples from overweighting fine-tuning.

Usage:
  python scripts/dedupe_jsonl.py --input data/training/training_data.jsonl --output data/training/training_data.deduped.jsonl

By default this dedupes by canonical JSON (sorted keys).
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Set


def canonical_dumps(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def record_hash(obj: Any) -> str:
    return hashlib.sha256(canonical_dumps(obj).encode("utf-8")).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description="Dedupe a JSONL file by exact record content.")
    ap.add_argument("--input", required=True, help="Input JSONL")
    ap.add_argument("--output", required=True, help="Output JSONL")
    args = ap.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)

    seen: Set[str] = set()
    total = 0
    kept = 0
    bad = 0

    out_path.parent.mkdir(parents=True, exist_ok=True)

    with in_path.open("r", encoding="utf-8") as f_in, out_path.open("w", encoding="utf-8") as f_out:
        for line_no, line in enumerate(f_in, 1):
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                obj = json.loads(line)
            except Exception:
                bad += 1
                continue

            h = record_hash(obj)
            if h in seen:
                continue
            seen.add(h)
            f_out.write(json.dumps(obj, ensure_ascii=False) + "\n")
            kept += 1

    print(f"Input records: {total}")
    print(f"Invalid JSON lines skipped: {bad}")
    print(f"Kept (unique): {kept}")
    print(f"Removed duplicates: {total - bad - kept}")
    print(f"Output: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
