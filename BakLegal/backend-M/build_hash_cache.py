"""Build content hash cache from dataset PDFs."""
import os
import sys
import hashlib
import json

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import pdfplumber
except ImportError:
    print("ERROR: pdfplumber not installed")
    sys.exit(1)

HASH_FILE = os.path.join(os.path.dirname(__file__), "content_hashes.json")
DATASET = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dataset")

def build_cache():
    print(f"Dataset path: {DATASET}")
    print(f"Hash file: {HASH_FILE}")
    
    if not os.path.exists(DATASET):
        print(f"ERROR: Dataset not found at {DATASET}")
        return
    
    hash_cache = {}
    processed = 0
    errors = 0
    
    # Walk recursively through dataset to find all PDFs
    all_pdfs = []
    for root, dirs, files in os.walk(DATASET):
        for f in files:
            if f.lower().endswith('.pdf'):
                full_path = os.path.join(root, f)
                # Get relative category path
                rel_path = os.path.relpath(root, DATASET)
                all_pdfs.append((full_path, rel_path, f))
    
    print(f"Found {len(all_pdfs)} PDF files")
    
    for fpath, category, fname in all_pdfs:
        try:
            with pdfplumber.open(fpath) as pdf:
                text = ' '.join(p.extract_text() or '' for p in pdf.pages)
            content_hash = hashlib.sha256(text.encode()).hexdigest()
            hash_cache[content_hash] = {'category': category, 'filename': fname}
            processed += 1
            if processed % 25 == 0:
                print(f"  Processed {processed}/{len(all_pdfs)}...")
        except Exception as e:
            errors += 1
            print(f"  Error {fname}: {e}")
    
    with open(HASH_FILE, 'w') as f:
        json.dump(hash_cache, f, indent=2)
    
    print(f"\nDone! Built hash cache with {len(hash_cache)} documents ({errors} errors)")

if __name__ == "__main__":
    build_cache()
