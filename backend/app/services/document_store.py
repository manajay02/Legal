"""Document storage for uploaded case materials.

This module provides a minimal document store used by the API to:
- accept uploads (PDF/TXT/DOCX),
- persist extracted text to disk, and
- reference uploaded documents by `doc_id` during argument scoring.

It is intentionally simple (single-process, local filesystem persistence).
For production/multi-worker deployments, replace with a DB/object store.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Optional, List


@dataclass(frozen=True)
class StoredDocument:
    doc_id: str
    filename: str
    file_type: str  # 'pdf' | 'txt' | 'docx'
    text: str
    created_at: float

    @property
    def text_length(self) -> int:
        return len(self.text)


class DocumentStore:
    """Local document store.

    - Keeps an in-memory cache for fast access.
    - Persists each document as JSON to `storage_dir`.
    """

    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, StoredDocument] = {}

    def _path_for(self, doc_id: str) -> Path:
        return self.storage_dir / f"{doc_id}.json"

    def put(self, filename: str, file_type: str, text: str) -> StoredDocument:
        doc_id = uuid.uuid4().hex
        doc = StoredDocument(
            doc_id=doc_id,
            filename=filename,
            file_type=file_type,
            text=text,
            created_at=time.time(),
        )
        self._cache[doc_id] = doc

        payload = asdict(doc)
        # `StoredDocument` contains only JSON-serializable types.
        self._path_for(doc_id).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return doc

    def get(self, doc_id: str) -> Optional[StoredDocument]:
        if doc_id in self._cache:
            return self._cache[doc_id]

        path = self._path_for(doc_id)
        if not path.exists():
            return None

        raw = json.loads(path.read_text(encoding="utf-8"))
        doc = StoredDocument(**raw)
        self._cache[doc_id] = doc
        return doc

    def list_ids(self) -> List[str]:
        # Prefer disk as source of truth
        return [p.stem for p in self.storage_dir.glob("*.json")]


_store: Optional[DocumentStore] = None


def get_document_store() -> DocumentStore:
    """Singleton document store."""
    global _store
    if _store is None:
        # backend/app/services -> backend/app -> backend
        backend_dir = Path(__file__).resolve().parents[2]
        storage_dir = backend_dir / "data" / "uploaded_docs"
        _store = DocumentStore(storage_dir=storage_dir)
    return _store
