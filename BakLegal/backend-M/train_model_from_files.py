"""
train_model_from_files.py
-------------------------
Trains TF-IDF similarity models directly from PDF files in the dataset folder.
Does NOT require MongoDB.

Usage:
    python train_model_from_files.py

The script scans dataset/{category}/{subcategory}/*.pdf and trains models.
"""

import os
import sys
import joblib
import pdfplumber
from sklearn.feature_extraction.text import TfidfVectorizer
from tqdm import tqdm
from collections import defaultdict

# ── Configuration ─────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(SCRIPT_DIR, "..", "dataset")
MODELS_DIR = os.path.join(SCRIPT_DIR, "models")

os.makedirs(MODELS_DIR, exist_ok=True)

TFIDF_PARAMS = dict(
    max_features=20_000,
    ngram_range=(1, 2),
    sublinear_tf=True,
    min_df=1,
    strip_accents="unicode",
    analyzer="word",
    token_pattern=r"(?u)\b\w+\b",
)


def model_key(category: str, subcategory: str) -> str:
    """Return a filesystem-safe model key."""
    return f"{category}_{subcategory}".replace(" ", "_").replace("/", "-")


def extract_pdf_text(pdf_path: str) -> str:
    """Extract text from a PDF file."""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
    except Exception as e:
        print(f"  [ERROR] Failed to read {pdf_path}: {e}")
    return text.strip()


def scan_dataset() -> dict:
    """
    Scan the dataset folder and return a dict:
    {
        (category, subcategory): [
            {"filename": str, "path": str, "text": str},
            ...
        ]
    }
    """
    data = defaultdict(list)
    
    if not os.path.exists(DATASET_DIR):
        print(f"[ERROR] Dataset folder not found: {DATASET_DIR}")
        return data
    
    # Walk through dataset/{category}/{subcategory}/*.pdf
    for category in os.listdir(DATASET_DIR):
        cat_path = os.path.join(DATASET_DIR, category)
        if not os.path.isdir(cat_path):
            continue
        
        for subcategory in os.listdir(cat_path):
            sub_path = os.path.join(cat_path, subcategory)
            if not os.path.isdir(sub_path):
                continue
            
            # Find all PDFs in this subcategory
            pdfs = [f for f in os.listdir(sub_path) if f.lower().endswith(".pdf")]
            for pdf_name in pdfs:
                pdf_path = os.path.join(sub_path, pdf_name)
                data[(category, subcategory)].append({
                    "filename": pdf_name,
                    "path": pdf_path,
                })
    
    return data


def train_one(label: str, docs: list[dict]) -> dict:
    """Train a TF-IDF model on a list of documents."""
    texts = [d["text"] for d in docs]
    filenames = [d["filename"] for d in docs]
    # Use filename as ID since we don't have MongoDB
    ids = [d["filename"] for d in docs]

    vec = TfidfVectorizer(**TFIDF_PARAMS)
    matrix = vec.fit_transform(texts)

    return {
        "label": label,
        "filenames": filenames,
        "mongo_ids": ids,
        "vectorizer": vec,
        "tfidf_matrix": matrix,
    }


def train_all():
    print("=" * 60)
    print("  Training TF-IDF Models from Dataset Files")
    print("=" * 60)
    print(f"Dataset folder: {DATASET_DIR}")
    print(f"Models folder:  {MODELS_DIR}")
    print()
    
    # Scan dataset
    print("Scanning dataset folder...")
    data = scan_dataset()
    
    if not data:
        print("[ERROR] No PDF files found in dataset folder.")
        return
    
    total_pdfs = sum(len(docs) for docs in data.values())
    print(f"Found {len(data)} subcategories with {total_pdfs} total PDFs.\n")
    
    all_docs = []
    
    # Process each subcategory
    for (category, subcategory), docs in tqdm(sorted(data.items()), desc="Processing"):
        key = model_key(category, subcategory)
        path = os.path.join(MODELS_DIR, f"{key}.pkl")
        
        # Extract text from PDFs
        for doc in docs:
            tqdm.write(f"  Extracting: {doc['filename'][:40]}...")
            doc["text"] = extract_pdf_text(doc["path"])
        
        # Filter out documents with no/little text
        valid_docs = [d for d in docs if len(d.get("text", "")) > 100]
        
        if len(valid_docs) < 2:
            tqdm.write(f"  [SKIP] {category}/{subcategory} — only {len(valid_docs)} valid doc(s), need >= 2.")
            all_docs.extend(valid_docs)
            continue
        
        # Train model
        artefact = train_one(f"{category}/{subcategory}", valid_docs)
        artefact["category"] = category
        artefact["subcategory"] = subcategory
        joblib.dump(artefact, path, compress=3)
        tqdm.write(f"  Saved: {key}.pkl  ({len(valid_docs)} docs, {artefact['tfidf_matrix'].shape[1]} features)")
        
        all_docs.extend(valid_docs)
    
    # Train global model
    print(f"\nTraining GLOBAL model on {len(all_docs)} documents...")
    if len(all_docs) >= 2:
        artefact = train_one("GLOBAL", all_docs)
        artefact["category"] = "ALL"
        artefact["subcategory"] = "ALL"
        path = os.path.join(MODELS_DIR, "GLOBAL.pkl")
        joblib.dump(artefact, path, compress=3)
        print(f"  Saved: GLOBAL.pkl  ({len(all_docs)} docs, {artefact['tfidf_matrix'].shape[1]} features)")
    else:
        print("  Not enough documents for global model.")
    
    print(f"\n{'=' * 60}")
    print(f"  Training complete!")
    print(f"  Models saved to: {MODELS_DIR}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    train_all()
