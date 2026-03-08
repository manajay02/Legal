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

    # Local import to keep startup light if unused.
    # IMPORTANT: scikit-learn is optional in this repo; fall back to a pure-Python
    # TF-IDF cosine scorer when it's not installed.
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore
        from sklearn.metrics.pairwise import cosine_similarity  # type: ignore

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
    except Exception:
        pass

    # ── Pure-Python fallback (unigrams only) ───────────────────────────────
    # Tokenization and weighting are intentionally simple; this is a retrieval
    # helper, not a full IR system.
    stop = {
        "the","and","for","that","with","this","from","were","was","are","but","not","have","has","had",
        "they","them","their","there","here","into","onto","over","under","upon","than","then","when",
        "what","which","while","where","who","whom","why","how","a","an","of","to","in","on","at","by",
        "as","is","it","be","or","if","we","you","i","he","she","his","her","its","our","us",
    }

    def tok(s: str) -> List[str]:
        return [t for t in re.findall(r"[a-z]{2,}", (s or "").lower()) if t not in stop]

    docs = [tok(c) for c in chunks]
    q = tok(query)
    if not q:
        return []

    # Document frequency
    df: dict[str, int] = {}
    for d in docs:
        for t in set(d):
            df[t] = df.get(t, 0) + 1
    n_docs = max(1, len(docs))

    def idf(term: str) -> float:
        # Smoothed IDF
        return math.log(1.0 + (n_docs / (1.0 + df.get(term, 0)))) + 1.0

    # Query vector (tf-idf)
    q_tf: dict[str, int] = {}
    for t in q:
        q_tf[t] = q_tf.get(t, 0) + 1
    q_vec: dict[str, float] = {t: (1.0 + math.log(v)) * idf(t) for t, v in q_tf.items()}
    q_norm = math.sqrt(sum(v * v for v in q_vec.values())) or 1.0

    ranked: List[Tuple[int, float]] = []
    for i, d in enumerate(docs):
        if not d:
            continue
        d_tf: dict[str, int] = {}
        for t in d:
            d_tf[t] = d_tf.get(t, 0) + 1
        # Only compute weights for terms that appear in the query to keep this fast.
        dot = 0.0
        d_norm_sq = 0.0
        for t, q_w in q_vec.items():
            if t not in d_tf:
                continue
            d_w = (1.0 + math.log(d_tf[t])) * idf(t)
            dot += q_w * d_w
        # Approximate doc norm using only query terms.
        for t in q_vec.keys():
            if t in d_tf:
                d_w = (1.0 + math.log(d_tf[t])) * idf(t)
                d_norm_sq += d_w * d_w
        d_norm = math.sqrt(d_norm_sq) or 1.0

        sim = dot / (q_norm * d_norm)
        if not math.isnan(sim):
            ranked.append((i, float(sim)))

    ranked.sort(key=lambda x: x[1], reverse=True)
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
