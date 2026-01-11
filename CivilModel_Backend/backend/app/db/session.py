"""
Database session management.
Currently using in-memory storage, will be upgraded to SQLite later.
"""

from typing import Dict, Optional
from threading import Lock
from loguru import logger


class InMemoryDB:
    """Thread-safe in-memory database for documents."""
    
    def __init__(self):
        """Initialize the in-memory database."""
        self._storage: Dict[str, Dict] = {}
        self._lock = Lock()
        logger.info("In-memory database initialized")
    
    def create(self, doc_id: str, data: Dict) -> None:
        """
        Create a new document entry.
        
        Args:
            doc_id: Unique document identifier
            data: Document data dictionary
        """
        with self._lock:
            self._storage[doc_id] = data
            logger.debug(f"Created document: {doc_id}")
    
    def get(self, doc_id: str) -> Optional[Dict]:
        """
        Retrieve a document by ID.
        
        Args:
            doc_id: Document identifier
            
        Returns:
            Document data or None if not found
        """
        with self._lock:
            return self._storage.get(doc_id)
    
    def update(self, doc_id: str, data: Dict) -> bool:
        """
        Update an existing document.
        
        Args:
            doc_id: Document identifier
            data: Updated document data
            
        Returns:
            True if updated, False if document not found
        """
        with self._lock:
            if doc_id in self._storage:
                self._storage[doc_id].update(data)
                logger.debug(f"Updated document: {doc_id}")
                return True
            return False
    
    def delete(self, doc_id: str) -> bool:
        """
        Delete a document.
        
        Args:
            doc_id: Document identifier
            
        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            if doc_id in self._storage:
                del self._storage[doc_id]
                logger.debug(f"Deleted document: {doc_id}")
                return True
            return False
    
    def list_all(self) -> Dict[str, Dict]:
        """
        Get all documents.
        
        Returns:
            Dictionary of all documents
        """
        with self._lock:
            return self._storage.copy()
    
    def count(self) -> int:
        """
        Get total number of documents.
        
        Returns:
            Document count
        """
        with self._lock:
            return len(self._storage)


# Global database instance
in_memory_db = InMemoryDB()


def get_db() -> InMemoryDB:
    """
    Dependency function to get database instance.
    
    Returns:
        InMemoryDB instance
    """
    return in_memory_db
