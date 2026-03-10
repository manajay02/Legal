"""
Quick script to count pages in all PDFs using PyPDF2.
"""

from pathlib import Path
from PyPDF2 import PdfReader

RAW_PDF_DIR = Path("d:/LegalScoreModel/data/raw_pdfs")
PROCESSED_DIR = Path("d:/LegalScoreModel/data/processed_text")
MAX_PAGES = 25

def main():
    pdf_files = sorted(RAW_PDF_DIR.glob("*.pdf"))
    
    # Get already processed files
    processed = {f.stem for f in PROCESSED_DIR.glob("*.txt")}
    
    under_limit = []
    over_limit = []
    already_done = []
    errors = []
    
    print(f"Analyzing {len(pdf_files)} PDFs...")
    print(f"Max pages threshold: {MAX_PAGES}\n")
    
    for i, pdf_path in enumerate(pdf_files, 1):
        case_id = pdf_path.stem
        print(f"\r  Checking {i}/{len(pdf_files)}: {case_id[:40]}...", end="", flush=True)
        
        if case_id in processed:
            already_done.append((case_id, "done"))
            continue
        
        try:
            reader = PdfReader(str(pdf_path))
            page_count = len(reader.pages)
            
            if page_count <= MAX_PAGES:
                under_limit.append((case_id, page_count))
            else:
                over_limit.append((case_id, page_count))
                
        except Exception as e:
            errors.append((case_id, str(e)[:50]))
    
    print("\r" + " " * 80)  # Clear line
    
    # Sort by page count
    under_limit.sort(key=lambda x: x[1])
    over_limit.sort(key=lambda x: x[1])
    
    # Print summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Already processed:        {len(already_done):3d} files")
    print(f"<= {MAX_PAGES} pages (WILL PROCESS): {len(under_limit):3d} files")
    print(f"> {MAX_PAGES} pages (WILL SKIP):    {len(over_limit):3d} files")
    print(f"Errors:                   {len(errors):3d} files")
    print("=" * 60)
    
    # Calculate total pages to process
    total_pages_to_process = sum(p for _, p in under_limit)
    total_pages_skipped = sum(p for _, p in over_limit)
    print(f"\nPages to process: {total_pages_to_process:,} pages")
    print(f"Pages to skip:    {total_pages_skipped:,} pages")
    print(f"Estimated time:   ~{total_pages_to_process * 5 // 60} - {total_pages_to_process * 8 // 60} minutes")
    
    # Print details
    print("\n" + "-" * 60)
    print(f"FILES <= {MAX_PAGES} PAGES (will process): {len(under_limit)} files")
    print("-" * 60)
    for name, pages in under_limit:
        print(f"  {pages:3d} pages: {name}")
    
    print("\n" + "-" * 60)
    print(f"FILES > {MAX_PAGES} PAGES (will skip): {len(over_limit)} files")
    print("-" * 60)
    for name, pages in over_limit:
        print(f"  {pages:3d} pages: {name}")
    
    if errors:
        print("\n" + "-" * 60)
        print("ERRORS:")
        print("-" * 60)
        for name, err in errors:
            print(f"  {name}: {err}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
