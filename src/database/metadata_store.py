"""
In-Memory Metadata Store for Document Management.

This module provides a simple in-memory storage solution for document metadata.
For production use, this should be replaced with a persistent database like PostgreSQL.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class DocumentMetadata:
    """
    Metadata for a processed PDF document.

    Attributes:
        document_id: Unique identifier for the document
        filename: Original filename
        upload_date: Timestamp of when document was uploaded
        num_pages: Number of pages in the PDF
        file_size: Size of the file in bytes
        processing_status: Current status (processing, completed, failed)
        num_chunks: Number of text chunks created
        error_message: Error message if processing failed
    """
    document_id: str
    filename: str
    upload_date: str
    num_pages: int
    file_size: int
    processing_status: str
    num_chunks: int = 0
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class MetadataStore:
    """
    In-memory storage for document metadata.

    This is a simple thread-safe in-memory store. For production,
    replace with a persistent database (PostgreSQL, SQLite, etc.).

    Attributes:
        documents: Dictionary mapping document_id to DocumentMetadata
        _lock: Thread lock for safe concurrent access
    """

    def __init__(self):
        """Initialize the metadata store."""
        self.documents: Dict[str, DocumentMetadata] = {}
        self._lock = Lock()
        logger.info("Metadata store initialized (in-memory)")

    def add_document(self, metadata: DocumentMetadata) -> bool:
        """
        Add a new document to the store.

        Args:
            metadata: DocumentMetadata object

        Returns:
            True if successful, False if document already exists
        """
        with self._lock:
            if metadata.document_id in self.documents:
                logger.warning(
                    f"Document {metadata.document_id} already exists"
                )
                return False

            self.documents[metadata.document_id] = metadata
            logger.info(
                f"Added document {metadata.document_id} ({metadata.filename})"
            )
            return True

    def get_document(self, document_id: str) -> Optional[DocumentMetadata]:
        """
        Retrieve document metadata by ID.

        Args:
            document_id: Document identifier

        Returns:
            DocumentMetadata object or None if not found
        """
        with self._lock:
            return self.documents.get(document_id)

    def update_document(
        self,
        document_id: str,
        **kwargs
    ) -> bool:
        """
        Update document metadata fields.

        Args:
            document_id: Document identifier
            **kwargs: Fields to update

        Returns:
            True if successful, False if document not found
        """
        with self._lock:
            if document_id not in self.documents:
                logger.warning(f"Document {document_id} not found for update")
                return False

            doc = self.documents[document_id]
            for key, value in kwargs.items():
                if hasattr(doc, key):
                    setattr(doc, key, value)
                else:
                    logger.warning(
                        f"Attempted to update unknown field: {key}"
                    )

            logger.debug(f"Updated document {document_id}")
            return True

    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from the store.

        Args:
            document_id: Document identifier

        Returns:
            True if successful, False if document not found
        """
        with self._lock:
            if document_id not in self.documents:
                logger.warning(
                    f"Document {document_id} not found for deletion"
                )
                return False

            del self.documents[document_id]
            logger.info(f"Deleted document {document_id}")
            return True

    def list_documents(
        self,
        status: Optional[str] = None
    ) -> List[DocumentMetadata]:
        """
        List all documents, optionally filtered by status.

        Args:
            status: Optional status filter (e.g., 'completed', 'failed')

        Returns:
            List of DocumentMetadata objects
        """
        with self._lock:
            docs = list(self.documents.values())

            if status:
                docs = [d for d in docs if d.processing_status == status]

            return docs

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about stored documents.

        Returns:
            Dictionary with statistics
        """
        with self._lock:
            total = len(self.documents)
            by_status = {}

            for doc in self.documents.values():
                status = doc.processing_status
                by_status[status] = by_status.get(status, 0) + 1

            return {
                "total_documents": total,
                "by_status": by_status,
                "total_pages": sum(d.num_pages for d in self.documents.values()),
                "total_chunks": sum(d.num_chunks for d in self.documents.values())
            }

    def clear(self) -> None:
        """Clear all documents from the store."""
        with self._lock:
            count = len(self.documents)
            self.documents.clear()
            logger.warning(f"Cleared all documents ({count} removed)")


# Global singleton instance
_metadata_store_instance: Optional[MetadataStore] = None


def get_metadata_store() -> MetadataStore:
    """
    Get the global metadata store instance (singleton pattern).

    Returns:
        MetadataStore instance
    """
    global _metadata_store_instance

    if _metadata_store_instance is None:
        _metadata_store_instance = MetadataStore()

    return _metadata_store_instance

