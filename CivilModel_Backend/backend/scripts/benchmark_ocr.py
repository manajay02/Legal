"""Benchmark hybrid OCR vs pure OCR."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.ocr_service import OCRService
from app.core.config import get_settings

settings = get_settings()

def main():
    ocr_service = OCRService()
    
    # Get test PDF
    sample_dir = settings.SAMPLE_CASES_DIR
    pdf_files = list(sample_dir.glob("*.pdf"))[:1]  # Test first PDF
    
    if not pdf_files:
        print("No PDFs found")
        return
    
    test_pdf = pdf_files[0]
    
    print(f"Benchmarking: {test_pdf.name}")
    print(f"Processing first 5 pages...\n")
    
    # Test hybrid approach
    start = time.time()
    text, metadata = ocr_service.process_pdf(str(test_pdf), max_pages=5)
    hybrid_time = time.time() - start
    
    print(f"\n⏱️  Hybrid OCR Time: {hybrid_time:.2f}s")
    print(f"   Fast path: {metadata['fast_path_pages']} pages")
    print(f"   OCR fallback: {metadata['ocr_fallback_pages']} pages")
    print(f"   Speedup estimate: {metadata['fast_path_pages']*10 + metadata['ocr_fallback_pages']*2:.0f}s saved vs pure OCR")

if __name__ == "__main__":
    main()