"""
Qdrant Vector Store Manager.

This module handles all interactions with the Qdrant vector database,
including initialization, storage, and retrieval of document embeddings.
"""

import logging
import os
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from qdrant_client.http.exceptions import UnexpectedResponse

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Manager for Qdrant vector database operations.

    Handles collection creation, vector storage, and similarity search
    using Qdrant as the backend vector database.

    Attributes:
        collection_name: Name of the Qdrant collection
        embedding_dim: Dimension of embedding vectors (768 for text-embedding-004)
        client: Qdrant client instance
    """

    def __init__(
        self,
        collection_name: str = "pdf_documents",
        embedding_dim: int = 768,
        qdrant_url: Optional[str] = None,
        qdrant_api_key: Optional[str] = None
    ):
        """
        Initialize the Vector Store with Qdrant connection.

        Args:
            collection_name: Name for the Qdrant collection
            embedding_dim: Dimension of embeddings (768 for Google text-embedding-004)
            qdrant_url: URL for Qdrant server (defaults to localhost)
            qdrant_api_key: API key for Qdrant (optional for local instance)
        """
        self.collection_name = collection_name
        self.embedding_dim = embedding_dim

        # Initialize Qdrant client
        # For local development, use in-memory or local storage
        qdrant_url = qdrant_url or os.getenv("QDRANT_URL", ":memory:")

        if qdrant_url == ":memory:":
            logger.info("Initializing Qdrant with in-memory storage")
            self.client = QdrantClient(":memory:")
        else:
            logger.info(f"Connecting to Qdrant at {qdrant_url}")
            self.client = QdrantClient(
                url=qdrant_url,
                api_key=qdrant_api_key or os.getenv("QDRANT_API_KEY")
            )

        # Initialize collection
        self._initialize_collection()

    def _initialize_collection(self) -> None:
        """
        Create the Qdrant collection if it doesn't exist.

        Configures the collection with:
        - Vector size matching embedding dimensions
        - Cosine similarity as distance metric
        """
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_exists = any(
                col.name == self.collection_name for col in collections
            )

            if not collection_exists:
                logger.info(f"Creating collection: {self.collection_name}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dim,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Collection '{self.collection_name}' created successfully")
            else:
                logger.info(f"Collection '{self.collection_name}' already exists")

        except Exception as e:
            logger.error(f"Error initializing collection: {e}")
            raise

    def add_vectors(
        self,
        vectors: List[List[float]],
        payloads: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> bool:
        """
        Add vectors to the collection.

        Args:
            vectors: List of embedding vectors
            payloads: List of metadata dictionaries for each vector
            ids: Optional list of IDs (auto-generated if not provided)

        Returns:
            True if successful, False otherwise

        Raises:
            ValueError: If vectors and payloads have different lengths
        """
        if len(vectors) != len(payloads):
            raise ValueError(
                f"Vectors ({len(vectors)}) and payloads ({len(payloads)}) "
                "must have the same length"
            )

        try:
            # Generate IDs if not provided
            if ids is None:
                import uuid
                ids = [str(uuid.uuid4()) for _ in range(len(vectors))]

            # Create points
            points = [
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload
                )
                for point_id, vector, payload in zip(ids, vectors, payloads)
            ]

            # Upload points
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )

            logger.info(f"Added {len(vectors)} vectors to collection")
            return True

        except Exception as e:
            logger.error(f"Error adding vectors: {e}")
            return False

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors in the collection.

        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            filter_dict: Optional filter conditions (e.g., {"document_id": "doc123"})

        Returns:
            List of search results with scores and payloads
        """
        try:
            # Build filter if provided
            search_filter = None
            if filter_dict:
                from qdrant_client.models import Filter, FieldCondition, MatchValue
                conditions = [
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value)
                    )
                    for key, value in filter_dict.items()
                ]
                search_filter = Filter(must=conditions)

            # Perform search
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                query_filter=search_filter
            )

            # Format results
            formatted_results = [
                {
                    "id": hit.id,
                    "score": hit.score,
                    "payload": hit.payload
                }
                for hit in results
            ]

            logger.debug(f"Search returned {len(formatted_results)} results")
            return formatted_results

        except Exception as e:
            logger.error(f"Error during search: {e}")
            return []

    def delete_by_filter(self, filter_dict: Dict[str, Any]) -> bool:
        """
        Delete vectors matching the filter.

        Args:
            filter_dict: Filter conditions (e.g., {"document_id": "doc123"})

        Returns:
            True if successful, False otherwise
        """
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue

            conditions = [
                FieldCondition(
                    key=key,
                    match=MatchValue(value=value)
                )
                for key, value in filter_dict.items()
            ]

            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(must=conditions)
            )

            logger.info(f"Deleted vectors matching filter: {filter_dict}")
            return True

        except Exception as e:
            logger.error(f"Error deleting vectors: {e}")
            return False

    def reset_collection(self) -> bool:
        """
        Delete and recreate the collection (removes all data).

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.warning(f"Resetting collection: {self.collection_name}")
            self.client.delete_collection(self.collection_name)
            self._initialize_collection()
            logger.info("Collection reset successfully")
            return True

        except Exception as e:
            logger.error(f"Error resetting collection: {e}")
            return False

    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get information about the collection.

        Returns:
            Dictionary with collection statistics
        """
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status
            }

        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {}

