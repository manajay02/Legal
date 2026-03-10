"""
train_model.py
--------------
Trains a TF-IDF similarity model for every (category, subcategory) pair
and saves the artefacts to backend/models/.

Saved artefact per subcategory  (e.g.  models/Civil_Administrative.pkl):
  {
    "category"    : str,
    "subcategory" : str,
    "filenames"   : [str, ...],         # parallel to tfidf_matrix rows
    "mongo_ids"   : [str, ...],         # _id values from MongoDB
    "vectorizer"  : TfidfVectorizer,    # fitted vectorizer
    "tfidf_matrix": sparse matrix       # shape (n_docs, n_features)
  }

Also trains a global model (models/GLOBAL.pkl) across ALL cases for
cross-category similarity search.
"""

import os
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from pymongo import MongoClient
from tqdm import tqdm

# ── Configuration ─────────────────────────────────────────────────────────────
MONGO_URI  = "mongodb+srv://maneth:pathana123@cluster0.thqkj39.mongodb.net/?appName=Cluster0"
DB_NAME    = "legal_cases_db"
COLLECTION = "cases"
MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")

os.makedirs(MODELS_DIR, exist_ok=True)

TFIDF_PARAMS = dict(
    max_features=20_000,   # vocabulary cap
    ngram_range=(1, 2),    # unigrams + bigrams
    sublinear_tf=True,     # log-scaled TF
    min_df=1,              # keep rare terms (small corpora)
    strip_accents="unicode",
    analyzer="word",
    token_pattern=r"(?u)\b\w+\b",
)


def model_key(category: str, subcategory: str) -> str:
    """Return a filesystem-safe model key."""
    return f"{category}_{subcategory}".replace(" ", "_").replace("/", "-")


def train_one(label: str, docs: list[dict]) -> dict:
    """Train a TF-IDF model on a list of {'filename', 'mongo_id', 'text'} dicts."""
    texts     = [d["text"] for d in docs]
    filenames = [d["filename"] for d in docs]
    ids       = [d["mongo_id"] for d in docs]

    vec    = TfidfVectorizer(**TFIDF_PARAMS)
    matrix = vec.fit_transform(texts)

    return {
        "label"       : label,
        "filenames"   : filenames,
        "mongo_ids"   : ids,
        "vectorizer"  : vec,
        "tfidf_matrix": matrix,
    }


def train_all():
    client = MongoClient(MONGO_URI)
    col    = client[DB_NAME][COLLECTION]

    # ── Gather all subcategories ──────────────────────────────────────────────
    pipeline = [
        {"$group": {
            "_id": {"category": "$category", "subcategory": "$subcategory"}
        }},
        {"$sort": {"_id.category": 1, "_id.subcategory": 1}}
    ]
    groups = list(col.aggregate(pipeline))
    print(f"Found {len(groups)} subcategories. Training models...\n")

    all_docs = []  # for global model

    for g in tqdm(groups, desc="Subcategories"):
        cat    = g["_id"]["category"]
        subcat = g["_id"]["subcategory"]
        key    = model_key(cat, subcat)
        path   = os.path.join(MODELS_DIR, f"{key}.pkl")

        # Fetch documents for this subcategory
        cursor = col.find(
            {"category": cat, "subcategory": subcat},
            {"_id": 1, "filename": 1, "text": 1}
        )
        docs = [
            {"filename": d["filename"], "mongo_id": str(d["_id"]), "text": d.get("text", "")}
            for d in cursor
        ]

        if len(docs) < 2:
            tqdm.write(f"  [SKIP] {cat}/{subcat} — only {len(docs)} doc(s), need ≥ 2.")
            all_docs.extend(docs)
            continue

        artefact = train_one(f"{cat}/{subcat}", docs)
        artefact["category"]    = cat
        artefact["subcategory"] = subcat
        joblib.dump(artefact, path, compress=3)
        tqdm.write(f"  Saved: {key}.pkl  ({len(docs)} docs, {artefact['tfidf_matrix'].shape[1]} features)")
        all_docs.extend(docs)

    client.close()

    # ── Global model across all cases ────────────────────────────────────────
    print(f"\nTraining GLOBAL model on {len(all_docs)} documents...")
    if len(all_docs) >= 2:
        artefact = train_one("GLOBAL", all_docs)
        artefact["category"]    = "ALL"
        artefact["subcategory"] = "ALL"
        path = os.path.join(MODELS_DIR, "GLOBAL.pkl")
        joblib.dump(artefact, path, compress=3)
        print(f"  Saved: GLOBAL.pkl  ({len(all_docs)} docs, {artefact['tfidf_matrix'].shape[1]} features)")
    else:
        print("  Not enough documents for global model.")

    print(f"\nAll models saved to: {MODELS_DIR}")


if __name__ == "__main__":
    train_all()
