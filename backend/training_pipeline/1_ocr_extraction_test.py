"""
OCR Extraction Pipeline - TEST VERSION (First 5 PDFs)
=====================================================

Quick test to verify OCR pipeline works before processing all 80 PDFs.

Author: LegalScoreModel Team
Date: January 2026
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

import pytesseract
from pdf2image import convert_from_path
from PIL import Image
from tqdm import tqdm


# ============================================
# Configuration
# ============================================

BASE_DIR = Path(__file__).parent.parent
RAW_PDF_DIR = BASE_DIR / "data" / "raw_pdfs"
OUTPUT_TEXT_DIR = BASE_DIR / "data" / "processed_text"
METADATA_DIR = BASE_DIR / "data" / "metadata"
LOG_DIR = BASE_DIR / "logs" / "ocr"

OCR_LANGUAGE = "sin+eng"
OCR_DPI = 300
TESSERACT_CONFIG = "--psm 6"
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# TEST: Process only first 5 PDFs
MAX_PDFS_TO_PROCESS = 5


# ============================================
# Setup Logging
# ============================================

LOG_DIR.mkdir(parents=True, exist_ok=True)
log_file = LOG_DIR / f"ocr_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def setup_tesseract():
    """Configure pytesseract."""
    if os.path.exists(TESSERACT_CMD):
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
        logger.info(f"Tesseract configured: {TESSERACT_CMD}")
    else:
        logger.warning(f"Tesseract not found: {TESSERACT_CMD}")


def get_pdf_files() -> List[Path]:
    """Get list of PDF files."""
    if not RAW_PDF_DIR.exists():
        raise FileNotFoundError(f"PDF directory not found: {RAW_PDF_DIR}")
    
    pdf_files = sorted(list(RAW_PDF_DIR.glob("*.pdf")))[:MAX_PDFS_TO_PROCESS]
    logger.info(f"Selected {len(pdf_files)} PDF files for testing")
    return pdf_files


def clean_text(text: str) -> str:
    """Clean extracted text."""
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return "\n".join(lines)


def extract_text_from_pdf(pdf_path: Path) -> Tuple[str, Dict]:
    """Extract text from PDF using OCR."""
    logger.info(f"\nProcessing: {pdf_path.name}")
    
    metadata = {
        "filename": pdf_path.name,
        "case_id": pdf_path.stem,
        "processed_at": datetime.now().isoformat(),
        "total_pages": 0,
        "successful_pages": 0,
        "errors": []
    }
    
    all_text = []
    
    try:
        logger.info(f"  Converting to images (DPI: {OCR_DPI})...")
        images = convert_from_path(pdf_path, dpi=OCR_DPI, fmt="png")
        metadata["total_pages"] = len(images)
        logger.info(f"  Converted {len(images)} pages")
        
        for page_num, image in enumerate(images, start=1):
            try:
                logger.info(f"  OCR on page {page_num}/{len(images)}...")
                page_text = pytesseract.image_to_string(
                    image,
                    lang=OCR_LANGUAGE,
                    config=TESSERACT_CONFIG
                )
                
                if page_text.strip():
                    all_text.append(f"--- Page {page_num} ---\n{page_text}")
                    metadata["successful_pages"] += 1
                    
            except Exception as e:
                logger.error(f"  Page {page_num} failed: {str(e)}")
                metadata["errors"].append({"page": page_num, "error": str(e)})
        
        combined_text = "\n\n".join(all_text)
        cleaned_text = clean_text(combined_text)
        
        metadata["character_count"] = len(cleaned_text)
        metadata["word_count"] = len(cleaned_text.split())
        
        logger.info(f"  SUCCESS: {metadata['word_count']:,} words from {metadata['successful_pages']} pages")
        
        return cleaned_text, metadata
        
    except Exception as e:
        logger.error(f"  FAILED: {str(e)}")
        metadata["errors"].append({"stage": "pdf_conversion", "error": str(e)})
        raise


def save_text(text: str, case_id: str):
    """Save extracted text."""
    OUTPUT_TEXT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_TEXT_DIR / f"{case_id}.txt"
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(text)
    
    logger.info(f"  Saved: {output_file.name}")


def save_metadata(all_metadata: List[Dict]):
    """Save metadata."""
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    metadata_file = METADATA_DIR / f"ocr_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    summary = {
        "test_run": True,
        "max_pdfs": MAX_PDFS_TO_PROCESS,
        "extraction_date": datetime.now().isoformat(),
        "total_files": len(all_metadata),
        "successful_files": sum(1 for m in all_metadata if m["successful_pages"] > 0),
        "total_words": sum(m.get("word_count", 0) for m in all_metadata),
        "files": all_metadata
    }
    
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\nMetadata saved: {metadata_file.name}")
    logger.info(f"Summary: {summary['successful_files']}/{summary['total_files']} files processed")
    logger.info(f"Total words extracted: {summary['total_words']:,}")


def main():
    """Main execution."""
    print("=" * 60)
    print("OCR EXTRACTION TEST - First 5 PDFs")
    print("=" * 60)
    print()
    
    setup_tesseract()
    pdf_files = get_pdf_files()
    
    if not pdf_files:
        logger.warning("No PDF files found.")
        return
    
    all_metadata = []
    
    with tqdm(total=len(pdf_files), desc="Processing PDFs", unit="file") as pbar:
        for pdf_path in pdf_files:
            try:
                extracted_text, metadata = extract_text_from_pdf(pdf_path)
                save_text(extracted_text, metadata["case_id"])
                all_metadata.append(metadata)
                
            except Exception as e:
                logger.error(f"Skipping {pdf_path.name}: {str(e)}")
                all_metadata.append({
                    "filename": pdf_path.name,
                    "case_id": pdf_path.stem,
                    "processed_at": datetime.now().isoformat(),
                    "total_pages": 0,
                    "successful_pages": 0,
                    "errors": [{"stage": "main", "error": str(e)}]
                })
            
            pbar.update(1)
    
    save_metadata(all_metadata)
    
    print()
    print("=" * 60)
    print("TEST COMPLETE!")
    print("=" * 60)
    print()
    print("If successful, run the full extraction:")
    print("  python training_pipeline\\1_ocr_extraction.py")
    print()


if __name__ == "__main__":
    main()
