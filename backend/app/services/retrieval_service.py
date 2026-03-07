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


def extract_numbered_paragraphs(text: str, max_paras: int = 40) -> List[Tuple[str, str]]:
    """Extract numbered-paragraph tuples ``(label, excerpt)`` from legal text.

    Recognises the following para numbering styles commonly found in Sri Lankan
    appellate judgments:

    * ``10.``  ``10)``  ``(10)``   – plain numeric at line start
    * ``Para 10``  ``Para. 10``  ``Paragraph 10``  – explicit "Para" prefix

    Each entry is ``("Para N", "<first 200 chars of paragraph text>")``.
    Results are sorted by paragraph number and capped at *max_paras*.
    """
    text = _normalize_whitespace(text)

    # Pattern 1: lines that START with a number marker
    # Matches: (10) text   /   10. text   /   10) text
    line_num_re = re.compile(
        r'(?m)^(?:\((\d{1,3})\)|(\d{1,3})[.)]\s+)(.+)'
    )

    # Pattern 2: "Para N" / "Para. N" / "Paragraph N" anywhere
    para_label_re = re.compile(
        r'(?i)\b(?:para(?:graph)?\.?\s*)(\d{1,3})\b[:\-\u2013\u2014]?\s*([^\n]{10,})'
    )

    collected: dict = {}  # num -> (label, excerpt)

    # Scan line-start numbers
    for m in line_num_re.finditer(text):
        num_grp = m.group(1) or m.group(2)
        body = m.group(3).strip()[:200]
        n = int(num_grp)
        if n not in collected and 1 <= n <= 999:
            collected[n] = (f"Para {n}", body)

    # Scan explicit Para N labels (these take priority when both match same N)
    for m in para_label_re.finditer(text):
        n = int(m.group(1))
        body = m.group(2).strip()[:200]
        if 1 <= n <= 999:
            collected[n] = (f"Para {n}", body)   # overwrite — explicit label wins

    # Sort and cap
    sorted_paras = sorted(collected.items(), key=lambda x: x[0])[:max_paras]
    return [(label, excerpt) for _, (label, excerpt) in sorted_paras]
