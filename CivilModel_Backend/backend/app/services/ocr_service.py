"""
Hybrid OCR Service for PDF Text Extraction
===========================================

Optimized extraction strategy:
1. Fast Path: Direct PDF text extraction (pdfplumber) for standard English text
2. Slow Path: OCR (Tesseract) only for pages with Sinhala or corrupted text

This hybrid approach is 10-20x faster than pure OCR for mixed-language documents.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pdfplumber
import pytesseract
from loguru import logger
from pdf2image import convert_from_path
from PIL import Image

from app.core.config import get_settings

settings = get_settings()


class OCRService:
    """Hybrid OCR service for extracting text from PDF documents."""
    
    def __init__(self):
        """Initialize OCR service with Tesseract configuration."""
        if settings.TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
            logger.info(f"Tesseract path set to: {settings.TESSERACT_CMD}")
        
        try:
            version = pytesseract.get_tesseract_version()
            logger.info(f"Hybrid OCR Service initialized with Tesseract v{version}")
            logger.info("Strategy: Fast (pdfplumber) + OCR Fallback (Tesseract)")
        except Exception as e:
            logger.error(f"Tesseract not found: {e}")
            raise RuntimeError(
                "Tesseract OCR not found. Please install Tesseract and ensure it's in your PATH."
            ) from e
    
    def needs_ocr(self, text: str) -> bool:
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
    
    def extract_page_with_ocr(self, pdf_path: str, page_num: int) -> str:
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
                dpi=300,  # High DPI for better accuracy
                first_page=page_num,
                last_page=page_num,
                fmt="png"
            )
            
            if not images:
                logger.warning(f"  Page {page_num}: No image generated")
                return ""
            
            # Run OCR on the image
            custom_config = r'--oem 3 --psm 6'  # LSTM OCR Engine, uniform text block
            page_text = pytesseract.image_to_string(
                images[0],
                lang=settings.TESSERACT_LANG,
                config=custom_config
            )
            
            return page_text.strip()
            
        except Exception as e:
            logger.error(f"  Page {page_num}: OCR failed - {str(e)}")
            return ""
    
    def clean_text(self, text: str) -> str:
        """
        Clean OCR text by removing artifacts and normalizing formatting.
        
        This function handles:
        - UTF-8 encoding issues (common OCR artifacts)
        - Page headers/footers
        - Extra whitespace
        - Common OCR misreadings
        
        Args:
            text: Raw OCR text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Fix common UTF-8 encoding issues
        encoding_fixes = {
            'â€™': "'",      # Right single quotation mark
            'â€œ': '"',      # Left double quotation mark
            'â€': '"',       # Right double quotation mark
            'â€"': '—',      # Em dash
            'â€"': '–',      # En dash
            'â€¢': '•',      # Bullet point
            'Â': '',         # Non-breaking space artifact
            'â': "'",        # Generic apostrophe fix
            'Ã¢': 'â',       # â with combining characters
            'Ã¤': 'ä',       # a with umlaut
            'Ã¶': 'ö',       # o with umlaut
            'Ã¼': 'ü',       # u with umlaut
            'Ã©': 'é',       # e with acute
            'Ã¨': 'è',       # e with grave
        }
        
        for wrong, correct in encoding_fixes.items():
            text = text.replace(wrong, correct)
        
        # Remove common OCR scanning artifacts
        text = re.sub(r'(?i)scanned\s+(?:by|with)\s+\w+scanner', '', text)
        
        # Remove page number patterns
        text = re.sub(r'(?i)page\s+\d+\s+of\s+\d+', '', text)
        text = re.sub(r'(?i)page\s+\d+/\d+', '', text)
        text = re.sub(r'\b\d+\s+of\s+\d+\b', '', text)
        text = re.sub(r'-\s*\d+\s*-', '', text)
        
        # Remove standalone page numbers at start/end of lines
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
        
        # Split into lines and strip each line
        lines = [line.strip() for line in text.split('\n')]
        
        # Remove very short lines that are likely artifacts (less than 3 chars)
        lines = [line for line in lines if len(line.strip()) > 2 or line.strip() == '']
        
        # Normalize whitespace within lines
        lines = [re.sub(r'\s+', ' ', line) for line in lines]
        
        # Remove multiple consecutive empty lines
        cleaned_lines = []
        prev_empty = False
        
        for line in lines:
            is_empty = len(line) == 0
            
            if not is_empty:
                cleaned_lines.append(line)
                prev_empty = False
            elif not prev_empty:
                cleaned_lines.append(line)
                prev_empty = True
        
        # Join lines back together
        text = '\n'.join(cleaned_lines)
        
        # Remove any remaining non-printable characters (except newlines and tabs)
        # Preserve Sinhala Unicode range
        text = re.sub(r'[^\x20-\x7E\n\t\u0D80-\u0DFF\u0B80-\u0BFF]', '', text)
        
        # Final whitespace normalization
        text = text.strip()
        
        return text
    
    def process_pdf(
        self,
        pdf_path: str,
        max_pages: int = None
    ) -> Tuple[str, Dict]:
        """
        Process entire PDF using hybrid strategy: fast path + OCR fallback.
        
        Strategy:
        1. Try direct text extraction with pdfplumber (fast)
        2. Check if text needs OCR using needs_ocr()
        3. If needed, fall back to OCR (slow)
        4. Track metadata about fast vs OCR pages
        
        Args:
            pdf_path: Path to PDF file
            max_pages: Maximum number of pages to process (None = all pages)
            
        Returns:
            Tuple of (cleaned_text, metadata_dict)
            
        Metadata includes:
            - total_pages: Total pages in PDF
            - successful_pages: Pages successfully extracted
            - fast_path_pages: Pages using fast extraction
            - ocr_fallback_pages: Pages requiring OCR
            - failed_pages: Pages that failed
            - character_count: Total characters in output
            - word_count: Total words in output
        """
        logger.info(f"Processing PDF (hybrid): {Path(pdf_path).name}")
        
        metadata = {
            "total_pages": 0,
            "successful_pages": 0,
            "fast_path_pages": 0,
            "ocr_fallback_pages": 0,
            "failed_pages": 0,
            "character_count": 0,
            "word_count": 0
        }
        
        all_text = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                metadata["total_pages"] = len(pdf.pages)
                
                # Limit pages if requested
                pages_to_process = pdf.pages
                if max_pages:
                    pages_to_process = pages_to_process[:max_pages]
                    logger.info(f"  Limited to first {max_pages} page(s)")
                
                logger.info(f"  Total pages: {len(pages_to_process)}")
                
                for page_num, page in enumerate(pages_to_process, start=1):
                    try:
                        # FAST PATH: Try direct text extraction
                        page_text = page.extract_text()
                        
                        # Check if extraction was successful and doesn't need OCR
                        if page_text and not self.needs_ocr(page_text):
                            # Success - use fast extraction (pure English page)
                            all_text.append(f"--- Page {page_num} ---\n{page_text}")
                            metadata["successful_pages"] += 1
                            metadata["fast_path_pages"] += 1
                            logger.debug(f"  Page {page_num}: ✓ Fast extraction ({len(page_text)} chars)")
                        
                        else:
                            # SLOW PATH: OCR needed (Sinhala content or corrupted text)
                            reason = "Sinhala/corrupted text" if page_text else "empty extraction"
                            logger.info(f"  Page {page_num}: {reason}, using OCR...")
                            
                            ocr_text = self.extract_page_with_ocr(pdf_path, page_num)
                            
                            if ocr_text:
                                all_text.append(f"--- Page {page_num} ---\n{ocr_text}")
                                metadata["successful_pages"] += 1
                                metadata["ocr_fallback_pages"] += 1
                                logger.debug(f"  Page {page_num}: ✓ OCR extraction ({len(ocr_text)} chars)")
                            else:
                                logger.warning(f"  Page {page_num}: ✗ OCR failed to extract text")
                                metadata["failed_pages"] += 1
                    
                    except Exception as e:
                        logger.error(f"  Page {page_num}: ✗ Error - {str(e)}")
                        metadata["failed_pages"] += 1
            
            # Combine all pages
            combined_text = '\n\n'.join(all_text)
            
            # Apply comprehensive cleaning
            cleaned_text = self.clean_text(combined_text)
            
            # Update metadata
            metadata["character_count"] = len(cleaned_text)
            metadata["word_count"] = len(cleaned_text.split())
            
            # Log summary
            efficiency = (
                f"{metadata['fast_path_pages']}/{metadata['total_pages']} pages "
                f"({100 * metadata['fast_path_pages'] / metadata['total_pages']:.1f}%)"
                if metadata['total_pages'] > 0 else "N/A"
            )
            
            logger.info(f"✓ Extraction complete:")
            logger.info(f"  - Characters: {metadata['character_count']:,}")
            logger.info(f"  - Words: {metadata['word_count']:,}")
            logger.info(f"  - Fast path: {efficiency}")
            logger.info(f"  - OCR fallback: {metadata['ocr_fallback_pages']} pages")
            
            # Save debug output if enabled
            if settings.DEBUG:
                output_path = Path(pdf_path).parent / f"{Path(pdf_path).stem}_hybrid_ocr.txt"
                try:
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(cleaned_text)
                    logger.debug(f"Debug OCR text saved to: {output_path}")
                except Exception as e:
                    logger.warning(f"Could not save debug OCR text: {e}")
            
            return cleaned_text, metadata
        
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            raise
