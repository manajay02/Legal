"""
Hybrid OCR Extraction Pipeline for Sri Lankan Supreme Court Judgments
======================================================================

Optimized extraction strategy:
1. Fast Path: Direct PDF text extraction (pdfplumber) for standard English text
2. Slow Path: OCR (Tesseract) only for legacy Sinhala font pages (fallback)

This approach is 10-20x faster than pure OCR for mixed-language documents.

Author: LegalScoreModel Team
Date: January 2026
"""

import os
import sys
import json
import logging
import time
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional

import pdfplumber
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
from tqdm import tqdm


# ============================================
# Configuration
# ============================================

# Directory paths
BASE_DIR = Path(__file__).parent.parent
RAW_PDF_DIR = BASE_DIR / "data" / "raw_pdfs"
OUTPUT_TEXT_DIR = BASE_DIR / "data" / "processed_text"
METADATA_DIR = BASE_DIR / "data" / "metadata"
LOG_DIR = BASE_DIR / "logs" / "ocr"

# OCR settings (only used for fallback)
OCR_LANGUAGE = "sin+eng"  # Sinhala + English
OCR_DPI = 300  # High DPI for better OCR accuracy
TESSERACT_CONFIG = "--psm 6"  # Assume uniform text block
MAX_PAGES = 25  # Skip PDFs with more than this many pages

# Tesseract executable path (Windows)
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Gibberish detection threshold
GIBBERISH_THRESHOLD = 0.20  # 20% non-standard characters


# ============================================
# Setup Logging
# ============================================

LOG_DIR.mkdir(parents=True, exist_ok=True)
log_file = LOG_DIR / f"ocr_extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

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
# Helper Functions
# ============================================

def setup_tesseract():
    """Configure pytesseract to use the correct Tesseract executable."""
    if os.path.exists(TESSERACT_CMD):
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
        logger.info(f"Tesseract configured at: {TESSERACT_CMD}")
    else:
        logger.warning(f"Tesseract not found at: {TESSERACT_CMD}")
        logger.warning("Attempting to use system PATH tesseract...")


def needs_ocr(text: str) -> bool:
    """
    Determine if a page needs OCR extraction.
    
    Strategy:
    1. If page contains ANY Sinhala-like characters → USE OCR (even if they look valid,
       pdfplumber often extracts corrupted text from Sinhala PDFs)
    2. If page has gibberish/corrupted text → USE OCR
    3. If page is pure English/ASCII → USE FAST PATH
    
    Args:
        text: Text extracted by pdfplumber
        
    Returns:
        True if page needs OCR, False if fast extraction is sufficient
    """
    if not text or len(text.strip()) < 10:
        return True  # Empty or very short text - try OCR
    
    total_chars = len(text)
    
    # 1. Standard ASCII (English text, numbers, punctuation)
    ascii_chars = len(re.findall(r'[a-zA-Z0-9\s.,;:!?\-\'\"()\[\]{}/@#$%&*+=<>\n]', text))
    
    # 2. Sinhala Unicode range (U+0D80 to U+0DFF)
    # Even if these look valid, pdfplumber often corrupts them - always use OCR
    sinhala_chars = len(re.findall(r'[\u0D80-\u0DFF]', text))
    
    # 3. Tamil Unicode range (U+0B80 to U+0BFF) - also common in Sri Lankan docs
    tamil_chars = len(re.findall(r'[\u0B80-\u0BFF]', text))
    
    # 4. Other non-ASCII characters (could be corrupted legacy fonts)
    other_chars = total_chars - ascii_chars - sinhala_chars - tamil_chars
    
    # Calculate ratios
    ascii_ratio = ascii_chars / total_chars if total_chars > 0 else 0
    sinhala_ratio = sinhala_chars / total_chars if total_chars > 0 else 0
    other_ratio = other_chars / total_chars if total_chars > 0 else 0
    
    # RULE 1: If ANY Sinhala/Tamil characters detected (even >1%), use OCR
    # This is because pdfplumber often corrupts Sinhala text
    if sinhala_ratio > 0.01 or tamil_chars > 0:
        logger.debug(f"Sinhala/Tamil detected ({sinhala_ratio:.1%}) - using OCR")
        return True
    
    # RULE 2: If too many "other" characters (corrupted encoding), use OCR
    if other_ratio > 0.20:
        logger.debug(f"High corruption ({other_ratio:.1%} other chars) - using OCR")
        return True
    
    # RULE 3: If mostly ASCII, fast extraction is fine
    if ascii_ratio > 0.80:
        return False  # Fast path OK
    
    # Default: use OCR to be safe
    return True


def get_page_count_fast(pdf_path: Path) -> int:
    """
    Get the number of pages in a PDF file using pdfplumber.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Number of pages, or -1 if error
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            return len(pdf.pages)
    except Exception as e:
        logger.error(f"Error getting page count for {pdf_path.name}: {str(e)}")
        return -1


def get_pdf_files(skip_existing: bool = True, max_pages: int = MAX_PAGES) -> List[Path]:
    """
    Retrieve all PDF files from the raw_pdfs directory.
    
    Args:
        skip_existing: If True, skip PDFs that already have processed text files
        max_pages: Skip PDFs with more than this many pages (0 = no limit)
    
    Returns:
        List of Path objects for each PDF file
    """
    if not RAW_PDF_DIR.exists():
        raise FileNotFoundError(f"PDF directory not found: {RAW_PDF_DIR}")
    
    pdf_files = list(RAW_PDF_DIR.glob("*.pdf"))
    total_pdfs = len(pdf_files)
    logger.info(f"Found {total_pdfs} PDF files in {RAW_PDF_DIR}")
    
    if skip_existing:
        # Filter out PDFs that already have corresponding .txt files
        OUTPUT_TEXT_DIR.mkdir(parents=True, exist_ok=True)
        existing_txt_files = {f.stem for f in OUTPUT_TEXT_DIR.glob("*.txt")}
        
        already_processed = [pdf for pdf in pdf_files if pdf.stem in existing_txt_files]
        pdf_files = [pdf for pdf in pdf_files if pdf.stem not in existing_txt_files]
        
        if already_processed:
            logger.info(f"Skipping {len(already_processed)} already processed PDFs")
    
    # Filter by page count
    if max_pages > 0:
        filtered_files = []
        skipped_large = []
        
        logger.info(f"Checking page counts (max: {max_pages} pages)...")
        for pdf in tqdm(pdf_files, desc="Counting pages", unit="file"):
            page_count = get_page_count_fast(pdf)
            if page_count > 0 and page_count <= max_pages:
                filtered_files.append(pdf)
            elif page_count > max_pages:
                skipped_large.append((pdf.stem, page_count))
        
        if skipped_large:
            logger.info(f"Skipping {len(skipped_large)} PDFs with >{max_pages} pages:")
            for name, pages in skipped_large[:5]:  # Show first 5
                logger.info(f"  - {name}: {pages} pages")
            if len(skipped_large) > 5:
                logger.info(f"  ... and {len(skipped_large) - 5} more")
        
        pdf_files = filtered_files
    
    logger.info(f"PDFs to process: {len(pdf_files)}")
    
    return sorted(pdf_files)


def clean_extracted_text(text: str) -> str:
    """
    Clean extracted text by removing artifacts while preserving paragraph structure.
    
    Args:
        text: Raw extracted text
        
    Returns:
        Cleaned text with preserved paragraphs
    """
    # Split into lines and strip each line
    lines = [line.strip() for line in text.split("\n")]
    
    # Remove completely empty lines but keep structure
    # Join consecutive non-empty lines, preserve paragraph breaks (double newlines)
    cleaned_lines = []
    for line in lines:
        if line:
            # Remove multiple consecutive spaces within a line
            line = ' '.join(line.split())
            cleaned_lines.append(line)
        else:
            # Keep empty line as paragraph separator (if previous wasn't empty)
            if cleaned_lines and cleaned_lines[-1] != "":
                cleaned_lines.append("")
    
    # Join with newlines to preserve paragraph structure
    cleaned = "\n".join(cleaned_lines)
    
    # Remove more than 2 consecutive newlines
    import re
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    
    return cleaned.strip()


def extract_page_with_ocr(pdf_path: Path, page_num: int) -> str:
    """
    Extract text from a single page using OCR (fallback method).
    
    Args:
        pdf_path: Path to the PDF file
        page_num: Page number to extract (1-indexed)
        
    Returns:
        Extracted text from the page
    """
    try:
        # Convert single page to image
        images = convert_from_path(
            pdf_path,
            dpi=OCR_DPI,
            first_page=page_num,
            last_page=page_num,
            fmt="png"
        )
        
        if not images:
            logger.warning(f"  Page {page_num}: No image generated")
            return ""
        
        # Run OCR on the image
        page_text = pytesseract.image_to_string(
            images[0],
            lang=OCR_LANGUAGE,
            config=TESSERACT_CONFIG
        )
        
        return page_text.strip()
        
    except Exception as e:
        logger.error(f"  Page {page_num}: OCR failed - {str(e)}")
        return ""


def extract_text_from_pdf_hybrid(pdf_path: Path) -> Tuple[str, Dict]:
    """
    Extract text from a PDF using hybrid strategy (fast + OCR fallback).
    
    Strategy:
    1. Try direct text extraction with pdfplumber (fast)
    2. If text is gibberish or empty, fall back to OCR (slow)
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Tuple of (extracted_text, metadata_dict)
    """
    logger.info(f"Processing: {pdf_path.name}")
    
    metadata = {
        "filename": pdf_path.name,
        "case_id": pdf_path.stem,
        "processed_at": datetime.now().isoformat(),
        "total_pages": 0,
        "successful_pages": 0,
        "fast_path_pages": 0,
        "ocr_fallback_pages": 0,
        "failed_pages": 0,
        "errors": []
    }
    
    all_text = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            metadata["total_pages"] = len(pdf.pages)
            logger.info(f"  Total pages: {len(pdf.pages)}")
            
            for page_num, page in enumerate(pdf.pages, start=1):
                try:
                    # FAST PATH: Try direct text extraction
                    page_text = page.extract_text()
                    
                    # Check if extraction was successful and doesn't need OCR
                    if page_text and not needs_ocr(page_text):
                        # Success - use fast extraction (pure English page)
                        all_text.append(f"--- Page {page_num} ---\n{page_text}")
                        metadata["successful_pages"] += 1
                        metadata["fast_path_pages"] += 1
                        logger.debug(f"  Page {page_num}: Fast extraction ({len(page_text)} chars)")
                    
                    else:
                        # SLOW PATH: OCR needed (Sinhala content or corrupted text)
                        reason = "Sinhala/corrupted text" if page_text else "empty extraction"
                        logger.info(f"  Page {page_num}: {reason}, using OCR...")
                        ocr_text = extract_page_with_ocr(pdf_path, page_num)
                        
                        if ocr_text:
                            all_text.append(f"--- Page {page_num} ---\n{ocr_text}")
                            metadata["successful_pages"] += 1
                            metadata["ocr_fallback_pages"] += 1
                            logger.debug(f"  Page {page_num}: OCR extraction ({len(ocr_text)} chars)")
                        else:
                            logger.warning(f"  Page {page_num}: OCR failed to extract text")
                            metadata["failed_pages"] += 1
                            
                except Exception as e:
                    logger.error(f"  Page {page_num}: Error - {str(e)}")
                    metadata["failed_pages"] += 1
                    metadata["errors"].append({
                        "page": page_num,
                        "error": str(e)
                    })
        
        # Combine all pages
        combined_text = "\n\n".join(all_text)
        cleaned_text = clean_extracted_text(combined_text)
        
        metadata["character_count"] = len(cleaned_text)
        metadata["word_count"] = len(cleaned_text.split())
        metadata["extraction_efficiency"] = (
            f"{metadata['fast_path_pages']}/{metadata['total_pages']} pages "
            f"({100 * metadata['fast_path_pages'] / metadata['total_pages']:.1f}%) fast extraction"
        )
        
        logger.info(
            f"  SUCCESS: {metadata['word_count']:,} words | "
            f"Fast: {metadata['fast_path_pages']}/{metadata['total_pages']} pages | "
            f"OCR: {metadata['ocr_fallback_pages']} pages"
        )
        
        return cleaned_text, metadata
        
    except Exception as e:
        logger.error(f"  FAILED: Error processing PDF: {str(e)}")
        metadata["errors"].append({
            "stage": "pdf_processing",
            "error": str(e)
        })
        raise


def save_extracted_text(text: str, case_id: str):
    """
    Save extracted text to a file.
    
    Args:
        text: Extracted text content
        case_id: Case identifier (filename without extension)
    """
    OUTPUT_TEXT_DIR.mkdir(parents=True, exist_ok=True)
    
    output_file = OUTPUT_TEXT_DIR / f"{case_id}.txt"
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(text)
    
    logger.debug(f"  Saved to: {output_file}")


def save_metadata(all_metadata: List[Dict]):
    """
    Save processing metadata to a JSON file.
    
    Args:
        all_metadata: List of metadata dictionaries for each PDF
    """
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    
    metadata_file = METADATA_DIR / f"ocr_extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Calculate summary statistics
    total_pages = sum(m["total_pages"] for m in all_metadata)
    fast_pages = sum(m["fast_path_pages"] for m in all_metadata)
    ocr_pages = sum(m["ocr_fallback_pages"] for m in all_metadata)
    
    summary = {
        "extraction_date": datetime.now().isoformat(),
        "total_files": len(all_metadata),
        "successful_files": sum(1 for m in all_metadata if m["successful_pages"] > 0),
        "failed_files": sum(1 for m in all_metadata if m["successful_pages"] == 0),
        "total_pages_processed": total_pages,
        "fast_extraction_pages": fast_pages,
        "ocr_fallback_pages": ocr_pages,
        "overall_efficiency": f"{100 * fast_pages / total_pages:.1f}%" if total_pages > 0 else "N/A",
        "total_words_extracted": sum(m.get("word_count", 0) for m in all_metadata),
        "files": all_metadata
    }
    
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\nMetadata saved to: {metadata_file}")
    logger.info(f"Summary: {summary['successful_files']}/{summary['total_files']} files processed successfully")
    logger.info(f"Efficiency: {summary['overall_efficiency']} fast extraction (avoided OCR)")


# ============================================
# Main Execution
# ============================================

def main():
    """
    Main execution function for hybrid OCR extraction pipeline.
    """
    logger.info("=" * 60)
    logger.info("Hybrid OCR Extraction Pipeline Started")
    logger.info("Strategy: Fast (pdfplumber) + OCR Fallback (Tesseract)")
    logger.info("=" * 60)
    
    # Setup
    setup_tesseract()
    
    # Get all PDF files
    pdf_files = get_pdf_files()
    
    if not pdf_files:
        logger.warning("No PDF files found. Exiting.")
        return
    
    # Process each PDF with progress bar
    all_metadata = []
    successful_count = 0
    failed_count = 0
    
    # ANSI color codes for terminal
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    
    start_time = time.time()
    
    with tqdm(total=len(pdf_files), desc="Processing PDFs", unit="file") as pbar:
        for idx, pdf_path in enumerate(pdf_files, 1):
            file_start_time = time.time()
            
            try:
                # Extract text using hybrid strategy
                extracted_text, metadata = extract_text_from_pdf_hybrid(pdf_path)
                
                # Save text file
                save_extracted_text(extracted_text, metadata["case_id"])
                
                # Store metadata
                all_metadata.append(metadata)
                successful_count += 1
                
                # Calculate timing
                elapsed = time.time() - file_start_time
                mins, secs = divmod(int(elapsed), 60)
                
                # Success message with efficiency metrics
                efficiency_color = GREEN if metadata["fast_path_pages"] > metadata["ocr_fallback_pages"] else YELLOW
                print(
                    f"{GREEN}[SUCCESS]{RESET} [{idx}/{len(pdf_files)}] {pdf_path.stem[:40]} | "
                    f"{metadata['word_count']:,} words | "
                    f"{efficiency_color}Fast: {metadata['fast_path_pages']}/{metadata['total_pages']}{RESET} | "
                    f"OCR: {metadata['ocr_fallback_pages']} | "
                    f"Time: {mins}m {secs}s"
                )
                
            except Exception as e:
                elapsed = time.time() - file_start_time
                mins, secs = divmod(int(elapsed), 60)
                
                print(
                    f"{RED}[FAILED]{RESET} [{idx}/{len(pdf_files)}] {pdf_path.stem[:40]} | "
                    f"Error: {str(e)[:50]} | Time: {mins}m {secs}s"
                )
                logger.error(f"Skipping {pdf_path.name} due to error: {str(e)}")
                failed_count += 1
                
                all_metadata.append({
                    "filename": pdf_path.name,
                    "case_id": pdf_path.stem,
                    "processed_at": datetime.now().isoformat(),
                    "total_pages": 0,
                    "successful_pages": 0,
                    "fast_path_pages": 0,
                    "ocr_fallback_pages": 0,
                    "failed_pages": 0,
                    "errors": [{"stage": "main", "error": str(e)}]
                })
            
            pbar.update(1)
    
    # Calculate total time
    total_elapsed = time.time() - start_time
    total_mins, total_secs = divmod(int(total_elapsed), 60)
    
    # Final summary
    print(f"\n{YELLOW}" + "=" * 60 + f"{RESET}")
    print(f"{GREEN}Successful: {successful_count}{RESET} | {RED}Failed: {failed_count}{RESET} | Total: {len(pdf_files)}")
    print(f"Total Time: {total_mins}m {total_secs}s")
    
    # Calculate overall efficiency
    if all_metadata:
        total_pages = sum(m["total_pages"] for m in all_metadata)
        fast_pages = sum(m["fast_path_pages"] for m in all_metadata)
        if total_pages > 0:
            efficiency = 100 * fast_pages / total_pages
            print(f"{BLUE}Overall Efficiency: {efficiency:.1f}% fast extraction (avoided OCR){RESET}")
    
    print(f"{YELLOW}" + "=" * 60 + f"{RESET}")
    
    # Save metadata
    save_metadata(all_metadata)
    
    logger.info("=" * 60)
    logger.info("Hybrid OCR Extraction Pipeline Completed")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()