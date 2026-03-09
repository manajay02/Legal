"""Prepare fine-tuning data from sample judgments.

This script turns PDFs (via OCR) or .txt files into JSONL training examples in the
classic instruction format:

  {"instruction": "...", "input": "<OCR text>", "output": "<JSON string>"}

The output JSON is produced by the currently configured LLM provider
(OpenRouter or Ollama) using the same extraction prompt as the application.

Typical usage:
  python scripts/prepare_training_data.py --input_dir data/sample_cases --output_file data/training/civil_cases.jsonl

Notes:
- You should review/clean the generated outputs before fine-tuning.
- For best model accuracy, prefer REAL OCR text as input (including artifacts),
  not already-structured/cleaned text.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Set, Tuple

# Allow "python scripts/..." to import "app"
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

from app.core.config import get_settings
from app.services.llm_service import LLMService
from app.services.ocr_service import OCRService
from app.services.parser_service import ParserService


DEFAULT_INSTRUCTION = (
    "Extract structured legal data from the OCR text of a Sri Lankan Supreme Court judgment. "
    "Return ONLY a single valid JSON object matching the required schema. "
    "Use null for missing fields and do not invent facts."
)


def _truncate_text(text: str, max_chars: Optional[int]) -> str:
    if not max_chars or max_chars <= 0:
        return text
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_period = truncated.rfind(".")
    if last_period > max_chars * 0.7:
        truncated = truncated[: last_period + 1]
    return truncated


def _iter_input_files(input_dir: Path) -> Iterable[Path]:
    for p in sorted(input_dir.rglob("*")):
        if p.is_file() and p.suffix.lower() in {".pdf", ".txt"}:
            yield p


def _read_text_from_file(path: Path, ocr: OCRService, max_pages: Optional[int]) -> Tuple[str, Dict[str, Any]]:
    if path.suffix.lower() == ".txt":
        text = path.read_text(encoding="utf-8", errors="replace")
        return text, {"source": "txt"}

    # PDF
    text, meta = ocr.process_pdf(str(path), max_pages=max_pages)
    meta = dict(meta or {})
    meta["source"] = "pdf"
    return text, meta


def _safe_json_dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False)


def _load_already_written_filenames(output_file: Path) -> Set[str]:
    """Parse an existing output JSONL and return processed filenames.

    This allows the script to be restarted without re-processing the same docs.
    """
    if not output_file.exists():
        return set()

    processed: Set[str] = set()
    with output_file.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            meta = obj.get("_meta") if isinstance(obj, dict) else None
            if isinstance(meta, dict):
                fn = meta.get("filename")
                if isinstance(fn, str) and fn.strip():
                    processed.add(fn.strip())
    return processed


def generate_example(
    *,
    input_path: Path,
    ocr: OCRService,
    llm: LLMService,
    parser: ParserService,
    max_pages: Optional[int],
    instruction: str,
    max_input_chars: Optional[int],
) -> Optional[Dict[str, Any]]:
    try:
        ocr_text, ocr_meta = _read_text_from_file(input_path, ocr, max_pages)
        ocr_text = (ocr_text or "").strip()
        ocr_text = _truncate_text(ocr_text, max_input_chars)
        if len(ocr_text) < 200:
            logger.warning(f"Skipping {input_path.name}: too little text ({len(ocr_text)} chars)")
            return None

        llm_raw = llm.extract_document_data(ocr_text)
        llm_json = parser.clean_llm_json(llm_raw)

        return {
            "instruction": instruction,
            "input": ocr_text,
            "output": _safe_json_dumps(llm_json),
            "_meta": {
                "filename": input_path.name,
                "source": ocr_meta.get("source"),
                "ocr": {k: v for k, v in ocr_meta.items() if k != "source"},
            },
        }

    except Exception as e:
        logger.exception(f"Failed on {input_path.name}: {e}")
        return None


def main() -> int:
    settings = get_settings()

    ap = argparse.ArgumentParser(description="Prepare JSONL training data from PDFs/TXT.")
    ap.add_argument(
        "--input_dir",
        type=str,
        default=str(settings.SAMPLE_CASES_DIR),
        help="Directory containing .pdf or .txt documents (default: data/sample_cases)",
    )
    ap.add_argument(
        "--output_file",
        type=str,
        default=str(settings.TRAINING_DIR / "civil_cases.jsonl"),
        help="Output JSONL file (default: data/training/civil_cases.jsonl)",
    )
    ap.add_argument(
        "--max_pages",
        type=int,
        default=0,
        help="Max pages per PDF (0 = all pages). Use 5-10 for faster labeling.",
    )
    ap.add_argument(
        "--max_input_chars",
        type=int,
        default=50000,
        help="Truncate input OCR text to N characters before sending/storing (0 = no truncation).",
    )
    ap.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Process at most N files (0 = no limit).",
    )
    ap.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite output file instead of appending.",
    )
    ap.add_argument(
        "--resume",
        action="store_true",
        help="Skip files already present in the output JSONL (default behavior unless --overwrite).",
    )
    ap.add_argument(
        "--instruction",
        type=str,
        default=DEFAULT_INSTRUCTION,
        help="Instruction string written for each example.",
    )

    args = ap.parse_args()

    input_dir = Path(args.input_dir)
    output_file = Path(args.output_file)
    max_pages: Optional[int] = None if args.max_pages == 0 else args.max_pages
    max_input_chars: Optional[int] = None if args.max_input_chars == 0 else args.max_input_chars
    limit: Optional[int] = None if args.limit == 0 else args.limit

    if not input_dir.exists():
        raise SystemExit(f"Input directory does not exist: {input_dir}")

    output_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"LLM provider: {settings.LLM_PROVIDER} | model: {getattr(settings, 'OPENROUTER_MODEL', '') or getattr(settings, 'OLLAMA_MODEL', '')}")
    logger.info(f"Input dir: {input_dir}")
    logger.info(f"Output: {output_file}")

    ocr = OCRService()
    llm = LLMService()
    parser = ParserService()

    files = list(_iter_input_files(input_dir))
    if not files:
        logger.warning("No .pdf or .txt files found.")
        return 0

    already_done: Set[str] = set()
    if not args.overwrite and (args.resume or output_file.exists()):
        already_done = _load_already_written_filenames(output_file)
        if already_done:
            logger.info(f"Resume: found {len(already_done)} already-written examples in {output_file.name}")

    if already_done:
        files = [p for p in files if p.name not in already_done]

    if limit is not None:
        files = files[:limit]

    if not files:
        logger.success("Nothing to do (all files already processed).")
        return 0

    written = 0
    mode = "w" if args.overwrite else "a"
    with output_file.open(mode, encoding="utf-8") as out:
        for idx, p in enumerate(files, 1):
            logger.info(f"[{idx}/{len(files)}] Processing {p.name}")
            ex = generate_example(
                input_path=p,
                ocr=ocr,
                llm=llm,
                parser=parser,
                max_pages=max_pages,
                instruction=args.instruction,
                max_input_chars=max_input_chars,
            )
            if not ex:
                continue

            out.write(json.dumps(ex, ensure_ascii=False) + "\n")
            written += 1

    logger.success(f"Wrote {written} examples to {output_file}")
    logger.info("Next: review/clean outputs, then fine-tune using civil_cases.jsonl")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
