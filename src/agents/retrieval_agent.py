"""
Retrieval Agent for PDF document processing and semantic search.

This agent is responsible for:
1. Loading and extracting text from PDF documents using LangChain PyPDFLoader
2. Chunking text into manageable segments using RecursiveCharacterTextSplitter
3. Generating embeddings using Google Text-Embedding-004 via LangChain
4. Storing vectors in Qdrant database using LangChain Qdrant integration
5. Performing semantic search for relevant document chunks

This agent uses LangChain framework for:
- Document loaders (PyPDFLoader)
- Text splitters (RecursiveCharacterTextSplitter)
- Embeddings (GoogleGenerativeAIEmbeddings)
- Vector stores (Qdrant)
"""

import logging
import os
import time
import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime

# LangChain imports for document processing
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Qdrant
from langchain.schema import Document

# Database imports
from src.database.vector_store import VectorStore
from src.database.metadata_store import (
    MetadataStore,
    DocumentMetadata,
    get_metadata_store
)

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """
    Represents a chunk of text from a PDF document.

    Attributes:
        chunk_id: Unique identifier for the chunk
        document_id: ID of the parent document
        content: Text content of the chunk
        page_number: Page number in the original document
        chunk_index: Index of the chunk in the document
        metadata: Additional metadata for the chunk
    """
    chunk_id: str
    document_id: str
    content: str
    page_number: int
    chunk_index: int
    metadata: Dict[str, Any]


@dataclass
class SearchResult:
    """
    Represents a search result from semantic search.

    Attributes:
        chunk: The document chunk
        score: Similarity score (0-1, higher is better)
        rank: Rank in the search results
    """
    chunk: DocumentChunk
    score: float
    rank: int


class RetrievalAgent:
    """
    Agent responsible for PDF document processing and retrieval.

    This agent handles the complete ETL pipeline:
    - Extract: Load PDF and extract text
    - Transform: Chunk text and generate embeddings
    - Load: Store vectors and metadata in databases

    It also provides semantic search functionality to retrieve relevant
    document chunks based on user queries.

    Attributes:
        embedding_model: Name of the embedding model to use
        chunk_size: Size of text chunks in characters
        chunk_overlap: Overlap between chunks in characters
        top_k: Number of results to return from search
    """

    def __init__(
        self,
        embedding_model: str = "models/text-embedding-004",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        top_k: int = 5,
        google_api_key: Optional[str] = None
    ) -> None:
        """
        Initialize the Retrieval Agent with LangChain components.

        Args:
            embedding_model: Google embedding model to use
            chunk_size: Size of text chunks in characters
            chunk_overlap: Overlap between chunks in characters
            top_k: Number of search results to return
            google_api_key: Google API key for embeddings (uses env var if not provided)

        Raises:
            ValueError: If configuration parameters are invalid
        """
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.top_k = top_k

        # Get API key from parameter or environment
        api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY must be provided or set in environment"
            )

        # Initialize Google embeddings with LangChain
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=embedding_model,
            google_api_key=api_key
        )

        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )

        # Initialize vector store
        self.vector_store = VectorStore(
            collection_name="pdf_documents",
            embedding_dim=768  # Google text-embedding-004 dimension
        )

        # Initialize metadata store
        self.metadata_store = get_metadata_store()

        # Simple in-memory cache for queries
        self.query_cache: Dict[str, List[SearchResult]] = {}

        logger.info(
            f"RetrievalAgent initialized with LangChain components: "
            f"model={embedding_model}, chunk_size={chunk_size}, "
            f"chunk_overlap={chunk_overlap}"
        )

    def load_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Load a PDF file and extract its text content.

        This method will use LangChain's PyPDFLoader to extract text from
        PDF files, handling multi-page documents and preserving page numbers.

        Args:
            file_path: Path to the PDF file

        Returns:
            Dictionary containing:
                - document_id: Unique ID for the document
                - filename: Name of the PDF file
                - num_pages: Number of pages in the PDF
                - content: Raw text content
                - metadata: Additional document metadata

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If file is not a valid PDF
            Exception: For other PDF processing errors

        Example:
            >>> agent = RetrievalAgent()
            >>> doc = agent.load_pdf("document.pdf")
            >>> print(f"Loaded {doc['num_pages']} pages")
        """
        logger.info(f"Loading PDF from {file_path}")

        # Validate file exists
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        if not path.suffix.lower() == '.pdf':
            raise ValueError(f"File must be a PDF: {file_path}")

        try:
            # Load PDF using LangChain PyPDFLoader
            loader = PyPDFLoader(file_path)
            pages = loader.load()

            if not pages:
                raise ValueError(f"PDF appears to be empty: {file_path}")

            # Extract content and metadata
            document_id = str(uuid.uuid4())
            filename = path.name
            num_pages = len(pages)
            content = "\n\n".join([page.page_content for page in pages])
            file_size = path.stat().st_size

            # Store metadata
            metadata = DocumentMetadata(
                document_id=document_id,
                filename=filename,
                upload_date=datetime.now().isoformat(),
                num_pages=num_pages,
                file_size=file_size,
                processing_status="processing"
            )

            self.metadata_store.add_document(metadata)

            logger.info(
                f"Loaded PDF: {filename} ({num_pages} pages, "
                f"{file_size} bytes)"
            )

            return {
                "document_id": document_id,
                "filename": filename,
                "num_pages": num_pages,
                "content": content,
                "file_size": file_size,
                "pages": pages  # Include LangChain Document objects
            }

        except Exception as e:
            logger.error(f"Error loading PDF {file_path}: {e}")
            raise

    def chunk_text(self, text: str, document_id: str) -> List[DocumentChunk]:
        """
        Split text into overlapping chunks for processing.

        Uses RecursiveCharacterTextSplitter from LangChain to create
        semantically meaningful chunks while respecting size constraints.

        Args:
            text: Raw text content to chunk
            document_id: ID of the parent document

        Returns:
            List of DocumentChunk objects

        Raises:
            ValueError: If text is empty or invalid

        Example:
            >>> agent = RetrievalAgent(chunk_size=500, chunk_overlap=100)
            >>> chunks = agent.chunk_text("Long text...", "doc123")
            >>> print(f"Created {len(chunks)} chunks")
        """
        logger.debug(f"Chunking text for document {document_id}")

        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        try:
            # Use LangChain text splitter
            text_chunks = self.text_splitter.split_text(text)

            # Create DocumentChunk objects
            chunks = []
            for idx, chunk_text in enumerate(text_chunks):
                chunk = DocumentChunk(
                    chunk_id=f"{document_id}_chunk_{idx}",
                    document_id=document_id,
                    content=chunk_text,
                    page_number=0,  # Will be updated if page info available
                    chunk_index=idx,
                    metadata={
                        "chunk_size": len(chunk_text),
                        "document_id": document_id
                    }
                )
                chunks.append(chunk)

            logger.info(
                f"Created {len(chunks)} chunks for document {document_id}"
            )

            return chunks

        except Exception as e:
            logger.error(f"Error chunking text: {e}")
            raise

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts using Google Text-Embedding-004.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors (each is a list of floats)

        Raises:
            Exception: If embedding generation fails

        Example:
            >>> agent = RetrievalAgent()
            >>> embeddings = agent.generate_embeddings(["text1", "text2"])
            >>> print(f"Generated {len(embeddings)} embeddings")
        """
        logger.debug(f"Generating embeddings for {len(texts)} texts")

        if not texts:
            return []

        try:
            # Use LangChain GoogleGenerativeAIEmbeddings
            embeddings = self.embeddings.embed_documents(texts)

            logger.info(
                f"Generated {len(embeddings)} embeddings "
                f"(dim={len(embeddings[0]) if embeddings else 0})"
            )

            return embeddings

        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise

    def store_document(
        self,
        document_id: str,
        chunks: List[DocumentChunk],
        embeddings: List[List[float]]
    ) -> bool:
        """
        Store document chunks and their embeddings in Qdrant.

        Args:
            document_id: Unique document identifier
            chunks: List of document chunks
            embeddings: List of embedding vectors

        Returns:
            True if storage was successful, False otherwise

        Raises:
            Exception: If storage operation fails

        Example:
            >>> agent = RetrievalAgent()
            >>> success = agent.store_document("doc123", chunks, embeddings)
        """
        logger.info(f"Storing document {document_id} with {len(chunks)} chunks")

        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Number of chunks ({len(chunks)}) must match "
                f"number of embeddings ({len(embeddings)})"
            )

        try:
            # Prepare payloads for vector store
            payloads = []
            ids = []

            for chunk in chunks:
                payload = {
                    "chunk_id": chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "content": chunk.content,
                    "page_number": chunk.page_number,
                    "chunk_index": chunk.chunk_index,
                    "metadata": chunk.metadata
                }
                payloads.append(payload)
                ids.append(chunk.chunk_id)

            # Store in vector database
            success = self.vector_store.add_vectors(
                vectors=embeddings,
                payloads=payloads,
                ids=ids
            )

            if success:
                # Update metadata store
                self.metadata_store.update_document(
                    document_id,
                    num_chunks=len(chunks),
                    processing_status="completed"
                )

                logger.info(
                    f"Successfully stored {len(chunks)} chunks "
                    f"for document {document_id}"
                )

            return success

        except Exception as e:
            logger.error(f"Error storing document {document_id}: {e}")
            self.metadata_store.update_document(
                document_id,
                processing_status="failed",
                error_message=str(e)
            )
            raise

    def search(
        self,
        query: str,
        document_id: Optional[str] = None,
        top_k: Optional[int] = None
    ) -> List[SearchResult]:
        """
        Perform semantic search for relevant document chunks.

        Args:
            query: Search query text
            document_id: Optional filter to search within specific document
            top_k: Number of results to return (uses self.top_k if not provided)

        Returns:
            List of SearchResult objects ranked by relevance

        Raises:
            ValueError: If query is empty
            Exception: If search operation fails

        Example:
            >>> agent = RetrievalAgent()
            >>> results = agent.search("What is the main topic?")
            >>> for result in results:
            ...     print(f"Score: {result.score}, Content: {result.chunk.content[:50]}")
        """
        k = top_k or self.top_k
        logger.info(f"Searching for query: '{query[:50]}...' (top_k={k})")

        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        # Check cache
        cache_key = f"{query}_{document_id}_{k}"
        if cache_key in self.query_cache:
            logger.debug("Returning cached search results")
            return self.query_cache[cache_key]

        try:
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)

            # Build filter if document_id specified
            filter_dict = {"document_id": document_id} if document_id else None

            # Search in vector store
            raw_results = self.vector_store.search(
                query_vector=query_embedding,
                top_k=k,
                filter_dict=filter_dict
            )

            # Convert to SearchResult objects
            search_results = []
            for rank, result in enumerate(raw_results):
                payload = result["payload"]

                chunk = DocumentChunk(
                    chunk_id=payload["chunk_id"],
                    document_id=payload["document_id"],
                    content=payload["content"],
                    page_number=payload["page_number"],
                    chunk_index=payload["chunk_index"],
                    metadata=payload["metadata"]
                )

                search_result = SearchResult(
                    chunk=chunk,
                    score=result["score"],
                    rank=rank + 1
                )

                search_results.append(search_result)

            # Cache results
            self.query_cache[cache_key] = search_results

            logger.info(f"Found {len(search_results)} results for query")

            return search_results

        except Exception as e:
            logger.error(f"Error during search: {e}")
            raise

    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document and all its chunks from storage.

        Args:
            document_id: ID of document to delete

        Returns:
            True if deletion was successful, False otherwise

        Raises:
            Exception: If deletion fails

        Example:
            >>> agent = RetrievalAgent()
            >>> agent.delete_document("doc123")
        """
        logger.info(f"Deleting document {document_id}")

        try:
            # Delete from vector store
            vector_success = self.vector_store.delete_by_filter(
                {"document_id": document_id}
            )

            # Delete from metadata store
            metadata_success = self.metadata_store.delete_document(document_id)

            # Clear related cache entries
            cache_keys_to_remove = [
                key for key in self.query_cache.keys()
                if document_id in key
            ]
            for key in cache_keys_to_remove:
                del self.query_cache[key]

            success = vector_success and metadata_success

            if success:
                logger.info(f"Successfully deleted document {document_id}")
            else:
                logger.warning(
                    f"Partial deletion for document {document_id}: "
                    f"vector={vector_success}, metadata={metadata_success}"
                )

            return success

        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            raise

    def get_document_info(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve metadata information for a specific document.

        Args:
            document_id: ID of the document

        Returns:
            Dictionary with document metadata or None if not found

        Example:
            >>> agent = RetrievalAgent()
            >>> info = agent.get_document_info("doc123")
            >>> print(info['filename'])
        """
        logger.debug(f"Retrieving info for document {document_id}")

        metadata = self.metadata_store.get_document(document_id)

        if metadata:
            return metadata.to_dict()

        return None

    def list_documents(self) -> List[Dict[str, Any]]:
        """
        List all documents in the system.

        Returns:
            List of dictionaries containing document metadata

        Example:
            >>> agent = RetrievalAgent()
            >>> docs = agent.list_documents()
            >>> print(f"Found {len(docs)} documents")
        """
        logger.debug("Listing all documents")

        documents = self.metadata_store.list_documents()
        return [doc.to_dict() for doc in documents]

    def process_pdf(self, file_path: str, max_retries: int = 3) -> Dict[str, Any]:
        """
        Complete ETL pipeline: Load PDF, chunk, embed, and store.

        This is the main entry point for processing a PDF document.
        It handles the entire pipeline with retry logic.

        Args:
            file_path: Path to the PDF file
            max_retries: Maximum number of retry attempts

        Returns:
            Dictionary with processing results and document_id

        Raises:
            Exception: If processing fails after all retries
        """
        logger.info(f"Starting PDF processing pipeline for {file_path}")

        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                # Step 1: Load PDF
                doc_info = self.load_pdf(file_path)
                document_id = doc_info["document_id"]

                # Step 2: Chunk text
                chunks = self.chunk_text(doc_info["content"], document_id)

                # Step 3: Generate embeddings
                chunk_texts = [chunk.content for chunk in chunks]
                embeddings = self.generate_embeddings(chunk_texts)

                # Step 4: Store in vector database
                success = self.store_document(document_id, chunks, embeddings)

                if success:
                    logger.info(
                        f"Successfully processed PDF: {doc_info['filename']} "
                        f"(ID: {document_id}, {len(chunks)} chunks)"
                    )

                    return {
                        "success": True,
                        "document_id": document_id,
                        "filename": doc_info["filename"],
                        "num_pages": doc_info["num_pages"],
                        "num_chunks": len(chunks),
                        "file_size": doc_info["file_size"]
                    }

            except Exception as e:
                last_error = e
                logger.warning(
                    f"Attempt {attempt}/{max_retries} failed: {e}"
                )

                if attempt < max_retries:
                    wait_time = attempt * 1  # 1s, 2s, 3s delays
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(
                        f"All {max_retries} attempts failed for {file_path}"
                    )

        raise Exception(
            f"Failed to process PDF after {max_retries} attempts: {last_error}"
        )

    def reset_database(self) -> bool:
        """
        Reset all databases (vector store and metadata).

        WARNING: This deletes all stored data!

        Returns:
            True if successful, False otherwise
        """
        logger.warning("Resetting all databases...")

        try:
            # Reset vector store
            vector_success = self.vector_store.reset_collection()

            # Reset metadata store
            self.metadata_store.clear()

            # Clear cache
            self.query_cache.clear()

            if vector_success:
                logger.info("Successfully reset all databases")
                return True
            else:
                logger.error("Failed to reset vector store")
                return False

        except Exception as e:
            logger.error(f"Error resetting databases: {e}")
            return False
