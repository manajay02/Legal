"""Retrieval utilities for grounding scores in uploaded documents and case texts.

This is a minimal TF-IDF retriever (no external vector DB).
It is designed for transparency: we return the exact excerpts used.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import List, Sequence, Tuple


@dataclass(frozen=True)
class EvidenceChunk:
    evidence_id: str
    source: str  # 'uploaded_doc' | 'case_corpus'
    source_id: str  # doc_id or case filename
    title: str  # filename
    excerpt: str
    score: float


def _normalize_whitespace(text: str) -> str:
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(text: str, max_chars: int = 1200, overlap: int = 150) -> List[str]:
    """Chunk text into overlapping segments.

    Heuristic: split by paragraphs first; then pack into chunks.
    """
    text = _normalize_whitespace(text)
    if not text:
        return []

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks: List[str] = []
    current: List[str] = []
    current_len = 0

    def flush():
        nonlocal current, current_len
        if not current:
            return
        chunk = "\n\n".join(current).strip()
        if chunk:
            chunks.append(chunk)
        current = []
        current_len = 0

    for para in paragraphs:
        if len(para) > max_chars:
            # Hard-split long paragraphs
            for i in range(0, len(para), max_chars - 50):
                part = para[i : i + (max_chars - 50)]
                if current_len + len(part) + 2 > max_chars:
                    flush()
                current.append(part)
                current_len += len(part) + 2
            continue

        if current_len + len(para) + 2 > max_chars:
            flush()
        current.append(para)
        current_len += len(para) + 2

    flush()

    if overlap > 0 and len(chunks) > 1:
        overlapped: List[str] = []
        prev_tail = ""
        for chunk in chunks:
            if prev_tail:
                chunk = (prev_tail + "\n\n" + chunk).strip()
            overlapped.append(chunk)
            prev_tail = chunk[-overlap:]
        return overlapped

    return chunks


def top_k_tfidf(query: str, chunks: Sequence[str], k: int = 5) -> List[Tuple[int, float]]:
    """Return (chunk_index, similarity_score) pairs."""
    query = _normalize_whitespace(query)
    if not query or not chunks:
        return []

    # Local import to keep startup light if unused
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        max_features=50000,
        ngram_range=(1, 2),
    )

    doc_matrix = vectorizer.fit_transform(list(chunks))
    q_vec = vectorizer.transform([query])
    sims = cosine_similarity(q_vec, doc_matrix).flatten()

    ranked = sorted(enumerate(sims.tolist()), key=lambda x: x[1], reverse=True)
    ranked = [(i, float(s)) for i, s in ranked if not math.isnan(s)]
    return ranked[:k]
