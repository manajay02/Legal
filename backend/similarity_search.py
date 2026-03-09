"""
similarity_search.py
--------------------
Utility for finding similar legal cases using the trained TF-IDF models.

Usage (CLI):
    python similarity_search.py --filename "case10.pdf" --subcategory "Administrative" --category "Civil" --top 5
    python similarity_search.py --filename "case10.pdf" --global-search --top 5
    python similarity_search.py --text "murder conviction appeal" --global-search --top 5

Usage (as a module):
    from similarity_search import SimilarityEngine
    engine = SimilarityEngine()
    results = engine.find_similar(filename="case10.pdf", category="Civil", subcategory="Administrative", top_n=5)
"""

import os
import re
import argparse
import joblib
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from pymongo import MongoClient
import certifi

# ── Configuration ─────────────────────────────────────────────────────────────
MONGO_URI  = "mongodb+srv://maneth:pathana123@cluster0.thqkj39.mongodb.net/?appName=Cluster0"
DB_NAME    = "legal_cases_db"
COLLECTION = "cases"
MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")


def _model_key(category: str, subcategory: str) -> str:
    return f"{category}_{subcategory}".replace(" ", "_").replace("/", "-")


class SimilarityEngine:
    """Load TF-IDF models and answer similarity queries."""

    def __init__(self):
        self._cache: dict = {}
        self._client = MongoClient(MONGO_URI, tlsCAFile=certifi.where(),
                                   serverSelectionTimeoutMS=5000,
                                   connectTimeoutMS=5000)
        self._col = self._client[DB_NAME][COLLECTION]

    # ── Model loading ─────────────────────────────────────────────────────────
    def _load_model(self, key: str) -> dict | None:
        if key in self._cache:
            return self._cache[key]
        path = os.path.join(MODELS_DIR, f"{key}.pkl")
        if not os.path.exists(path):
            return None
        model = joblib.load(path)
        self._cache[key] = model
        return model

    # ── Core similarity logic ─────────────────────────────────────────────────
    def _rank(self, model: dict, query_vec, exclude_filename: str | None, top_n: int) -> list[dict]:
        matrix    = model["tfidf_matrix"]
        filenames = model["filenames"]
        mongo_ids = model["mongo_ids"]

        sims = cosine_similarity(query_vec, matrix).flatten()

        # Sort descending
        ranked = np.argsort(sims)[::-1]
        results = []
        for idx in ranked:
            fname = filenames[idx]
            if exclude_filename and fname == exclude_filename:
                continue
            if sims[idx] < 1e-6:
                break
            results.append({
                "filename"   : fname,
                "mongo_id"   : mongo_ids[idx],
                "score"      : round(float(sims[idx]), 4),
                "category"   : model.get("category", ""),
                "subcategory": model.get("subcategory", ""),
            })
            if len(results) >= top_n:
                break
        return results

    # ── Public API ────────────────────────────────────────────────────────────
    def find_similar(
        self,
        *,
        filename   : str | None = None,
        text       : str | None = None,
        category   : str | None = None,
        subcategory: str | None = None,
        global_search: bool = False,
        top_n      : int = 5,
    ) -> list[dict]:
        """
        Find similar cases.

        Parameters
        ----------
        filename      : Look up this file in MongoDB to get its text.
        text          : Use this raw text as the query (alternative to filename).
        category      : Required when global_search=False, e.g. 'Civil'.
        subcategory   : Required when global_search=False, e.g. 'Administrative'.
        global_search : Search across ALL categories.
        top_n         : How many results to return.
        """
        if global_search:
            key = "GLOBAL"
        else:
            if not category or not subcategory:
                raise ValueError("Provide category and subcategory (or use global_search=True).")
            key = _model_key(category, subcategory)

        model = self._load_model(key)
        if model is None:
            raise FileNotFoundError(
                f"No model found for key '{key}'. "
                f"Run train_model.py first, or check MODELS_DIR: {MODELS_DIR}"
            )

        # Resolve query text
        query_text = text
        if query_text is None:
            if filename is None:
                raise ValueError("Provide either 'filename' or 'text'.")
            doc = self._col.find_one({"filename": filename})
            if doc is None:
                raise ValueError(f"File '{filename}' not found in collection '{COLLECTION}'.")
            query_text = doc.get("text", "")

        query_vec = model["vectorizer"].transform([query_text])
        return self._rank(model, query_vec, exclude_filename=filename, top_n=top_n)

    def list_available_models(self) -> list[str]:
        """Return all trained model keys (without .pkl extension)."""
        return [f[:-4] for f in os.listdir(MODELS_DIR) if f.endswith(".pkl")]

    def close(self):
        self._client.close()


# ── CLI entry-point ───────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Find similar legal cases.")
    parser.add_argument("--filename",    type=str, help="Filename to use as query (e.g. case10.pdf)")
    parser.add_argument("--text",        type=str, help="Raw text query string")
    parser.add_argument("--category",   type=str, help="Category (e.g. Civil)")
    parser.add_argument("--subcategory",type=str, help="Subcategory (e.g. Administrative)")
    parser.add_argument("--global-search", action="store_true", help="Search across all categories")
    parser.add_argument("--top",         type=int, default=5, help="Number of results (default: 5)")
    parser.add_argument("--list-models", action="store_true", help="List all available models")
    args = parser.parse_args()

    engine = SimilarityEngine()

    if args.list_models:
        print("Available models:")
        for m in sorted(engine.list_available_models()):
            print(f"  {m}")
        engine.close()
        return

    results = engine.find_similar(
        filename      = args.filename,
        text          = args.text,
        category      = args.category,
        subcategory   = args.subcategory,
        global_search = args.global_search,
        top_n         = args.top,
    )

    print(f"\nTop {len(results)} similar cases:\n")
    print(f"{'Rank':<5} {'Score':<8} {'Category':<12} {'Subcategory':<28} {'Filename'}")
    print("-" * 80)
    for rank, r in enumerate(results, 1):
        print(f"{rank:<5} {r['score']:<8} {r['category']:<12} {r['subcategory']:<28} {r['filename']}")

    engine.close()


if __name__ == "__main__":
    main()
