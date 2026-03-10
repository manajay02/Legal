"""Process all sample PDFs and save metadata."""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.ocr_service import OCRService
from app.core.config import get_settings

settings = get_settings()

def main():
    ocr_service = OCRService()
    sample_dir = settings.SAMPLE_CASES_DIR
    output_dir = settings.PROCESSED_DIR
    output_dir.mkdir(exist_ok=True, parents=True)
    
    pdf_files = sorted(sample_dir.glob("*.pdf"))
    
    print(f"Found {len(pdf_files)} PDFs to process\n")
    
    results = []
    
    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"[{i}/{len(pdf_files)}] {pdf_path.name}")
        
        try:
            text, metadata = ocr_service.process_pdf(str(pdf_path), max_pages=5)
            
            # Save text
            output_file = output_dir / f"{pdf_path.stem}.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(text)
            
            results.append({
                "filename": pdf_path.name,
                "success": True,
                **metadata
            })
            
            print(f"   ✓ Saved to {output_file.name}\n")
        
        except Exception as e:
            print(f"   ✗ Failed: {e}\n")
            results.append({
                "filename": pdf_path.name,
                "success": False,
                "error": str(e)
            })
    
    # Save summary
    summary_file = output_dir / f"processing_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            "processed_at": datetime.now().isoformat(),
            "total_files": len(pdf_files),
            "successful": sum(1 for r in results if r.get('success')),
            "files": results
        }, f, indent=2)
    
    print(f"\n✅ Summary saved to {summary_file}")

if __name__ == "__main__":
    main()