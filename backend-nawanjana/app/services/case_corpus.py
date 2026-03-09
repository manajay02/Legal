"""Case corpus retrieval for precedent/similarity evidence.

Indexes existing judgment texts under backend/data/processed_text.
Used to return 'similar cases' excerpts to justify scoring.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple


@dataclass(frozen=True)
class SimilarCase:
    case_id: str  # filename
    excerpt: str
    score: float


class CaseCorpusIndex:
    def __init__(self, processed_dir: Path, max_files: int = 300, max_chars_per_file: int = 20000):
        self.processed_dir = processed_dir
        self.max_files = max_files
        self.max_chars_per_file = max_chars_per_file
        self._ready = False
        self._filenames: List[str] = []
        self._texts: List[str] = []
        self._vectorizer = None
        self._matrix = None

    @property
    def ready(self) -> bool:
        return self._ready

    def build(self) -> None:
        if self._ready:
            return

        if not self.processed_dir.exists():
            self._ready = True
            return

        files = sorted(self.processed_dir.glob("*.txt"))[: self.max_files]
        self._filenames = []
        self._texts = []

        for p in files:
            try:
                txt = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            txt = txt.strip()
            if not txt:
                continue

            if len(txt) > self.max_chars_per_file:
                txt = txt[: self.max_chars_per_file]

            self._filenames.append(p.name)
            self._texts.append(txt)

        if not self._texts:
            self._ready = True
            return

        from sklearn.feature_extraction.text import TfidfVectorizer

        self._vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            max_features=80000,
            ngram_range=(1, 2),
        )
        self._matrix = self._vectorizer.fit_transform(self._texts)
        self._ready = True

    def query(self, query_text: str, k: int = 3) -> List[SimilarCase]:
        self.build()
        if not self._texts or self._vectorizer is None or self._matrix is None:
            return []

        from sklearn.metrics.pairwise import cosine_similarity

        q_vec = self._vectorizer.transform([query_text])
        sims = cosine_similarity(q_vec, self._matrix).flatten()
        ranked = sorted(enumerate(sims.tolist()), key=lambda x: x[1], reverse=True)[:k]

        out: List[SimilarCase] = []
        for idx, score in ranked:
            fname = self._filenames[idx]
            text = self._texts[idx]
            excerpt = text[:1000].strip()
            out.append(SimilarCase(case_id=fname, excerpt=excerpt, score=float(score)))
        return out


_index: Optional[CaseCorpusIndex] = None


def get_case_corpus_index() -> CaseCorpusIndex:
    global _index
    if _index is None:
        backend_dir = Path(__file__).resolve().parents[2]
        processed_dir = backend_dir / "data" / "processed_text"
        max_files = int(os.getenv("CASE_CORPUS_MAX_FILES", "300"))
        max_chars = int(os.getenv("CASE_CORPUS_MAX_CHARS", "20000"))
        _index = CaseCorpusIndex(processed_dir=processed_dir, max_files=max_files, max_chars_per_file=max_chars)
    return _index
