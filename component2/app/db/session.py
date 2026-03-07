"""
Database session management.
Uses SQLite for persistent storage so data survives server restarts.
"""

import json
import sqlite3
from datetime import datetime, date
from enum import Enum
from pathlib import Path
from threading import Lock
from typing import Dict, Optional

from loguru import logger

# SQLite database file path
_DB_DIR = Path(__file__).parent.parent.parent / "data"
_DB_PATH = _DB_DIR / "civilmodel.db"


class _DateTimeEncoder(json.JSONEncoder):
    """JSON encoder that handles datetime, date, and Enum objects."""
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)


def _dumps(data) -> str:
    return json.dumps(data, cls=_DateTimeEncoder)


def _loads(text: str) -> Dict:
    return json.loads(text)


class SQLiteDB:
    """Thread-safe SQLite-backed database for documents.
    
    Drop-in replacement for InMemoryDB — identical public interface.
    Data is stored in ``data/civilmodel.db`` and survives server restarts.
    """

    def __init__(self, db_path: Path = _DB_PATH):
        self._db_path = db_path
        self._lock = Lock()
        self._init_db()
        count = self.count()
        logger.info(f"SQLite database initialised at {db_path} ({count} documents)")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id      TEXT PRIMARY KEY,
                    data    TEXT NOT NULL
                )
            """)
            conn.commit()

    # ------------------------------------------------------------------
    # Public CRUD methods  (same signature as InMemoryDB)
    # ------------------------------------------------------------------

    def create(self, doc_id: str, data: Dict) -> None:
        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO documents (id, data) VALUES (?, ?)",
                    (doc_id, _dumps(data))
                )
                conn.commit()
        logger.debug(f"Created document: {doc_id}")

    def get(self, doc_id: str) -> Optional[Dict]:
        with self._lock:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT data FROM documents WHERE id = ?", (doc_id,)
                ).fetchone()
        if row is None:
            return None
        doc = _loads(row["data"])
        # Restore datetime strings back to datetime objects for backwards compat
        for field in ("created_at", "processed_at"):
            if doc.get(field) and isinstance(doc[field], str):
                try:
                    doc[field] = datetime.fromisoformat(doc[field])
                except ValueError:
                    pass
        return doc

    def update(self, doc_id: str, data: Dict) -> bool:
        with self._lock:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT data FROM documents WHERE id = ?", (doc_id,)
                ).fetchone()
                if row is None:
                    return False
                existing = _loads(row["data"])
                existing.update(data)
                conn.execute(
                    "UPDATE documents SET data = ? WHERE id = ?",
                    (_dumps(existing), doc_id)
                )
                conn.commit()
        logger.debug(f"Updated document: {doc_id}")
        return True

    def delete(self, doc_id: str) -> bool:
        with self._lock:
            with self._connect() as conn:
                cursor = conn.execute(
                    "DELETE FROM documents WHERE id = ?", (doc_id,)
                )
                conn.commit()
                deleted = cursor.rowcount > 0
        if deleted:
            logger.debug(f"Deleted document: {doc_id}")
        return deleted

    def list_all(self) -> Dict[str, Dict]:
        with self._lock:
            with self._connect() as conn:
                rows = conn.execute("SELECT id, data FROM documents").fetchall()
        result = {}
        for row in rows:
            doc = _loads(row["data"])
            for field in ("created_at", "processed_at"):
                if doc.get(field) and isinstance(doc[field], str):
                    try:
                        doc[field] = datetime.fromisoformat(doc[field])
                    except ValueError:
                        pass
            result[row["id"]] = doc
        return result

    def list_by_batch(self, batch_id: str) -> Dict[str, Dict]:
        all_docs = self.list_all()
        return {k: v for k, v in all_docs.items() if v.get("batch_id") == batch_id}

    def count(self) -> int:
        with self._lock:
            with self._connect() as conn:
                row = conn.execute("SELECT COUNT(*) FROM documents").fetchone()
        return row[0]


# Keep alias so existing imports of InMemoryDB still work
InMemoryDB = SQLiteDB

# Global database instance
in_memory_db = SQLiteDB()


def get_db() -> SQLiteDB:
    """
    Dependency function to get database instance.

    Returns:
        SQLiteDB instance (persistent, survives restarts)
    """
    return in_memory_db
