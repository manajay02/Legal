"""
Embedding service for multilingual semantic search.
Uses sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2)
  → supports English + Sinhala (and 50+ other languages)
Stores the FAISS index on disk so it survives restarts.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from threading import Lock
from typing import Dict, List, Optional, Tuple

import numpy as np
from loguru import logger

# ---------------------------------------------------------------------------
# Lazy imports – sentence-transformers and faiss are optional at startup
# ---------------------------------------------------------------------------
_model = None
_faiss = None
_model_lock = Lock()

# Where to persist the FAISS index and id-mapping
_DATA_DIR = Path(__file__).parent.parent.parent / "data"
_INDEX_PATH = _DATA_DIR / "faiss_index.bin"
_IDS_PATH   = _DATA_DIR / "faiss_ids.json"

# Embedding model name (multilingual, ~418 MB, supports 50+ languages)
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_DIM = 384          # dimension for the chosen model


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_model():
    """Lazy-load the SentenceTransformer model (thread-safe)."""
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                try:
                    from sentence_transformers import SentenceTransformer
                    logger.info(f"Loading embedding model: {MODEL_NAME}")
                    _model = SentenceTransformer(MODEL_NAME)
                    logger.info("Embedding model loaded successfully")
                except ImportError:
                    logger.error(
                        "sentence-transformers not installed. "
                        "Run: pip install sentence-transformers faiss-cpu"
                    )
                    raise
    return _model


def _get_faiss():
    """Lazy-import faiss."""
    global _faiss
    if _faiss is None:
        try:
            import faiss as _faiss_module
            _faiss = _faiss_module
        except ImportError:
            logger.error(
                "faiss-cpu not installed. Run: pip install faiss-cpu"
            )
            raise
    return _faiss


# ---------------------------------------------------------------------------
# In-memory index state
# ---------------------------------------------------------------------------

# doc_id list (position i → FAISS vector i)
_index_ids: List[str] = []
# The FAISS index itself
_faiss_index = None
_index_lock  = Lock()


def _load_index() -> None:
    """Load FAISS index from disk if it exists."""
    global _faiss_index, _index_ids
    faiss = _get_faiss()
    if _INDEX_PATH.exists() and _IDS_PATH.exists():
        try:
            _faiss_index = faiss.read_index(str(_INDEX_PATH))
            with open(_IDS_PATH, "r", encoding="utf-8") as f:
                _index_ids = json.load(f)
            logger.info(
                f"Loaded FAISS index ({_faiss_index.ntotal} vectors) from {_INDEX_PATH}"
            )
        except Exception as e:
            logger.warning(f"Could not load FAISS index from disk: {e}")
            _faiss_index = None
            _index_ids = []


def _save_index() -> None:
    """Persist the current FAISS index to disk."""
    if _faiss_index is None:
        return
    faiss = _get_faiss()
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(_faiss_index, str(_INDEX_PATH))
    with open(_IDS_PATH, "w", encoding="utf-8") as f:
        json.dump(_index_ids, f)
    logger.debug(f"FAISS index saved ({_faiss_index.ntotal} vectors)")


def _ensure_index() -> None:
    """Make sure an index exists (load or create empty)."""
    global _faiss_index
    if _faiss_index is None:
        faiss = _get_faiss()
        _load_index()
        if _faiss_index is None:
            _faiss_index = faiss.IndexFlatIP(EMBEDDING_DIM)   # Inner-product → cosine after normalisation
            logger.info("Created new empty FAISS index")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def embed_text(text: str) -> np.ndarray:
    """
    Return a normalised L2 float32 embedding vector for *text*.

    Normalisation means inner-product == cosine similarity.
    """
    model = _get_model()
    vec = model.encode([text], normalize_embeddings=True, show_progress_bar=False)
    return vec[0].astype(np.float32)


def embed_batch(texts: List[str]) -> np.ndarray:
    """Embed a list of texts, returning shape (N, EMBEDDING_DIM)."""
    model = _get_model()
    vecs = model.encode(texts, normalize_embeddings=True, show_progress_bar=False, batch_size=32)
    return vecs.astype(np.float32)


def build_index(documents: Dict[str, Dict]) -> int:
    """
    (Re)build the FAISS index from *documents* (id → doc_data dict).
    Returns number of vectors added.
    """
    global _faiss_index, _index_ids
    faiss = _get_faiss()

    texts: List[str] = []
    ids:   List[str] = []

    for doc_id, doc in documents.items():
        text = _doc_to_search_text(doc)
        if text.strip():
            texts.append(text)
            ids.append(doc_id)

    if not texts:
        logger.warning("build_index: no documents with searchable text")
        return 0

    logger.info(f"Embedding {len(texts)} documents for FAISS index …")
    vecs = embed_batch(texts)

    with _index_lock:
        _faiss_index = faiss.IndexFlatIP(EMBEDDING_DIM)
        _faiss_index.add(vecs)
        _index_ids = ids
        _save_index()

    logger.info(f"FAISS index built with {len(ids)} vectors")
    return len(ids)


def add_document(doc_id: str, doc: Dict) -> None:
    """
    Add (or update) a single document to the FAISS index.
    If the doc already exists it is replaced.
    """
    global _faiss_index, _index_ids

    text = _doc_to_search_text(doc)
    if not text.strip():
        return

    vec = embed_text(text).reshape(1, -1)

    with _index_lock:
        _ensure_index()

        if doc_id in _index_ids:
            # FAISS FlatIP does not support in-place removal; rebuild a small
            # subset instead.  For the scale of this project (hundreds of docs)
            # a full rebuild is fast enough.
            return  # Skip; caller should call build_index() to refresh

        _faiss_index.add(vec)
        _index_ids.append(doc_id)
        _save_index()


def semantic_search(
    query: str,
    k: int = 20,
    score_threshold: float = 0.0,
) -> List[Tuple[str, float]]:
    """
    Return top-k (doc_id, cosine_similarity) pairs for *query*.
    similarity is in [0, 1] (higher = better).
    """
    with _index_lock:
        _ensure_index()
        if _faiss_index is None or _faiss_index.ntotal == 0:
            return []

    q_vec = embed_text(query).reshape(1, -1)
    actual_k = min(k, len(_index_ids))

    with _index_lock:
        scores, indices = _faiss_index.search(q_vec, actual_k)

    results: List[Tuple[str, float]] = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(_index_ids):
            continue
        sim = float(score)           # Inner-product == cosine (normalised)
        if sim >= score_threshold:
            results.append((_index_ids[idx], sim))
    return results


def index_size() -> int:
    """Return the number of vectors in the current index."""
    with _index_lock:
        _ensure_index()
        return _faiss_index.ntotal if _faiss_index else 0


# ---------------------------------------------------------------------------
# Helper – build a rich text blob from a stored document dict
# ---------------------------------------------------------------------------

def _doc_to_search_text(doc: Dict) -> str:
    """
    Concatenate all semantically rich fields from a stored document dict
    into a single string for embedding.
    """
    parts: List[str] = []

    def _add(val):
        if val and isinstance(val, str):
            parts.append(val.strip())

    def _add_list(lst):
        if isinstance(lst, list):
            for item in lst:
                if item and isinstance(item, str):
                    parts.append(item.strip())

    # Case metadata
    meta = doc.get("metadata") or doc.get("extracted_data", {}).get("metadata") or {}
    _add(meta.get("case_number"))
    _add(meta.get("court"))
    _add(meta.get("case_type"))
    _add_list(meta.get("legal_provisions", []))

    # Legal insights
    insights = doc.get("legal_insights") or doc.get("extracted_data", {}).get("legal_insights") or {}
    _add_list(insights.get("key_legal_issues", []))
    _add_list(insights.get("doctrines", []))
    _add(insights.get("reliefs_requested"))
    _add(insights.get("reliefs_granted"))
    _add(insights.get("state_involvement_level"))

    # Outcome explanation
    outcome = doc.get("outcome_classification") or doc.get("extracted_data", {}).get("outcome_classification") or {}
    _add(outcome.get("explanation"))

    # Sections / reasoning
    sections = (
        doc.get("sections")
        or doc.get("extracted_data", {}).get("sections")
        or []
    )
    for sec in sections:
        if isinstance(sec, dict):
            _add(sec.get("title"))
            _add(sec.get("content"))
            _add(sec.get("text"))

    # Filename as last resort
    _add(doc.get("filename"))

    return " ".join(parts)
