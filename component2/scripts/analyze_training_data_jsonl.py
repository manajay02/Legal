"""Quick analysis for training_data.jsonl-style datasets (metadata + sections).

Usage:
  python scripts/analyze_training_data_jsonl.py --path data/training/training_data.jsonl
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict


def canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def date_fmt(s: str | None) -> str:
    if not s:
        return "missing"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return "YYYY-MM-DD"
    if re.fullmatch(r"\d{4}-\d{2}", s):
        return "YYYY-MM"
    if re.fullmatch(r"\d{4}", s):
        return "YYYY"
    return "other"


def main() -> int:
    ap = argparse.ArgumentParser(description="Analyze training_data.jsonl schema coverage and duplicates.")
    ap.add_argument("--path", required=True, help="Path to JSONL")
    args = ap.parse_args()

    path = Path(args.path)
    records = []
    errors = 0

    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except Exception:
            errors += 1

    missing = Counter()
    section_counts = []
    case_numbers = []
    date_formats = Counter()
    judge_counts = Counter()
    party_counts = Counter()

    hashes = []
    for r in records:
        hashes.append(hashlib.sha256(canonical(r).encode("utf-8")).hexdigest())

        md = r.get("metadata")
        if not isinstance(md, dict):
            missing["metadata"] += 1
            md = {}
        for key in ["case_number", "court", "date", "parties", "judges"]:
            if key not in md or md.get(key) in (None, "", []):
                missing[f"metadata.{key}"] += 1

        cn = md.get("case_number")
        if cn:
            case_numbers.append(cn)

        parties = md.get("parties")
        if isinstance(parties, list):
            party_counts[len(parties)] += 1

        judges = md.get("judges")
        if isinstance(judges, list):
            judge_counts[len(judges)] += 1

        date_formats[date_fmt(md.get("date"))] += 1

        sections = r.get("sections")
        if not isinstance(sections, list) or not sections:
            missing["sections"] += 1
            section_counts.append(0)
        else:
            section_counts.append(len(sections))

    cn_counts = Counter(case_numbers)
    dup_case_numbers = [(cn, c) for cn, c in cn_counts.items() if c > 1]
    dup_case_numbers.sort(key=lambda x: x[1], reverse=True)

    print("file:", path)
    print("records:", len(records), "parse_errors:", errors)
    print("unique_record_hashes:", len(set(hashes)), "of", len(records))

    if missing:
        print("\nMissing fields (top 10):")
        for k, v in missing.most_common(10):
            print(f"  {k}: {v}")

    print("\nDate formats:", dict(date_formats))
    print("Judges per record:", dict(judge_counts))
    print("Parties per record:", dict(party_counts))

    if section_counts:
        section_counts_sorted = sorted(section_counts)
        med = section_counts_sorted[len(section_counts_sorted) // 2]
        print("\nSection count min/median/max:", min(section_counts), med, max(section_counts))

    print("\nDuplicate case_number count:", len(dup_case_numbers))
    print("Top duplicates:", dup_case_numbers[:10])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
