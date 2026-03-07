"""Test the hybrid OCR service."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.ocr_service import OCRService
from app.core.config import get_settings

settings = get_settings()

def main():
    print("="*70)
    print("TESTING HYBRID OCR SERVICE")
    print("="*70)
    
    # Initialize service
    ocr_service = OCRService()
    
    # Get first sample PDF
    sample_dir = settings.SAMPLE_CASES_DIR
    pdf_files = list(sample_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("❌ No PDF files found in sample_cases/")
        return
    
    test_pdf = pdf_files[0]
    print(f"\n📄 Test PDF: {test_pdf.name}")
    print(f"   Path: {test_pdf}")
    
    # Process with hybrid strategy
    print(f"\n{'='*70}")
    print("PROCESSING WITH HYBRID STRATEGY")
    print(f"{'='*70}\n")
    
    text, metadata = ocr_service.process_pdf(str(test_pdf), max_pages=3)
    
    # Display results
    print(f"\n{'='*70}")
    print("RESULTS")
    print(f"{'='*70}")
    
    print(f"\n📊 Metadata:")
    for key, value in metadata.items():
        print(f"   {key}: {value}")
    
    print(f"\n📝 Extracted Text Preview (first 500 chars):")
    print("-" * 70)
    print(text[:500])
    print("-" * 70)
    
    # Calculate efficiency
    if metadata['total_pages'] > 0:
        efficiency = (metadata['fast_path_pages'] / metadata['total_pages']) * 100
        print(f"\n⚡ Efficiency: {efficiency:.1f}% pages used fast path (avoided OCR)")
    
    print(f"\n{'='*70}")
    print("✅ TEST COMPLETED")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()