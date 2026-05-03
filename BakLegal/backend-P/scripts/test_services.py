"""
Test script to verify OCR and LLM services.
Processes the first PDF in sample_cases directory.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.services.ocr_service import OCRService
from app.services.llm_service import LLMService


def main():
    """Run the complete pipeline test."""
    print("="*70)
    print("TESTING OCR & LLM SERVICES")
    print("="*70)
    
    # Find first PDF in sample_cases
    sample_dir = settings.SAMPLE_CASES_DIR
    pdf_files = list(sample_dir.glob("*.pdf"))
    
    if not pdf_files:
        print(f"\n✗ No PDF files found in: {sample_dir}")
        print("Please place sample PDFs in data/sample_cases/ directory")
        return
    
    test_pdf = pdf_files[0]
    print(f"\n📄 Test PDF: {test_pdf.name}")
    print(f"   Path: {test_pdf}")
    
    # Initialize services
    print("\n" + "="*70)
    print("INITIALIZING SERVICES")
    print("="*70)
    
    try:
        ocr_service = OCRService()
        print("✓ OCR Service initialized")
    except Exception as e:
        print(f"✗ Failed to initialize OCR Service: {e}")
        return
    
    try:
        llm_service = LLMService()
        print("✓ LLM Service initialized")
    except Exception as e:
        print(f"✗ Failed to initialize LLM Service: {e}")
        return
    
    # Test OCR on first page only (for speed)
    print("\n" + "="*70)
    print("TESTING OCR (First Page Only)")
    print("="*70)
    
    try:
        extracted_text = ocr_service.process_pdf(
            str(test_pdf),
            first_page=1,
            last_page=1
        )
        
        print(f"\n✓ OCR Completed")
        print(f"  Extracted {len(extracted_text)} characters")
        print(f"\n--- First 500 characters ---")
        print(extracted_text[:500])
        print("...")
        
    except Exception as e:
        print(f"\n✗ OCR Failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test LLM summarization
    print("\n" + "="*70)
    print("TESTING LLM (Summarization)")
    print("="*70)
    
    try:
        # Use first 1500 characters for summarization (to stay within context)
        text_sample = extracted_text[:1500]
        
        print(f"\nSending {len(text_sample)} characters to LLM for summary...")
        summary = llm_service.summarize_text(text_sample, max_length=200)
        
        print(f"\n✓ LLM Summarization Completed")
        print(f"\n--- Summary ---")
        print(summary)
        
    except Exception as e:
        print(f"\n✗ LLM Failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Success!
    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED")
    print("="*70)
    print("\n✓ OCR Service is working correctly")
    print("✓ LLM Service is working correctly")
    print("✓ Pipeline is ready for full document processing")
    print("\nNext steps:")
    print("  1. Start the API: uvicorn app.main:app --reload")
    print("  2. Visit http://localhost:8000/docs for API documentation")
    print("  3. Test health endpoint: http://localhost:8000/health")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
