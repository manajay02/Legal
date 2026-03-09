"""Validate instruction-style JSONL fine-tuning data.

Checks rows shaped like:
  {"instruction": str, "input": str, "output": "<json string>", "_meta": {...}}

and ensures that "output" parses into JSON and contains expected top-level keys.

Usage:
  python scripts/validate_civil_cases_jsonl.py --path data/training/civil_cases.jsonl
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List


REQUIRED_TOP_LEVEL_KEYS = [
    "metadata",
    "outcome",
    "timeline",
    "citations",
    "insights",
    "confidence_scores",
    "sections",
]


def _parse_output(value: Any) -> Dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        try:
            parsed = json.loads(value)
        except Exception:
            return None
        return parsed if isinstance(parsed, dict) else None
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate instruction-style JSONL for fine-tuning.")
    ap.add_argument("--path", required=True, help="Path to JSONL")
    ap.add_argument("--max_errors", type=int, default=50, help="Stop listing after N errors")
    args = ap.parse_args()

    path = Path(args.path)
    total = 0
    ok = 0

    error_counts = Counter()
    sample_errors: List[str] = []

    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                row = json.loads(line)
            except Exception:
                error_counts["bad_jsonl_line"] += 1
                if len(sample_errors) < args.max_errors:
                    sample_errors.append(f"Line {line_no}: invalid JSONL")
                continue

            if not isinstance(row, dict):
                error_counts["row_not_object"] += 1
                if len(sample_errors) < args.max_errors:
                    sample_errors.append(f"Line {line_no}: row is not an object")
                continue

            for key in ["instruction", "input", "output"]:
                if key not in row:
                    error_counts[f"missing_{key}"] += 1
            if any(k not in row for k in ["instruction", "input", "output"]):
                if len(sample_errors) < args.max_errors:
                    sample_errors.append(f"Line {line_no}: missing instruction/input/output")
                continue

            output_obj = _parse_output(row.get("output"))
            if output_obj is None:
                error_counts["output_not_json_object"] += 1
                if len(sample_errors) < args.max_errors:
                    sample_errors.append(f"Line {line_no}: output does not parse to a JSON object")
                continue

            missing_keys = [k for k in REQUIRED_TOP_LEVEL_KEYS if k not in output_obj]
            if missing_keys:
                error_counts["output_missing_top_keys"] += 1
                if len(sample_errors) < args.max_errors:
                    sample_errors.append(f"Line {line_no}: output missing keys: {missing_keys}")
                continue

            ok += 1

    print(f"file: {path}")
    print(f"rows: {total}")
    print(f"valid: {ok}")

    if error_counts:
        print("\nErrors:")
        for k, v in error_counts.most_common():
            print(f"  {k}: {v}")

    if sample_errors:
        print("\nSample issues:")
        for s in sample_errors:
            print(f"  {s}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
