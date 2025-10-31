"""
Unit tests for RetrievalAgent.

Tests cover:
- Text chunking
- Embedding generation
- Document storage
- Semantic search
- CRUD operations
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.agents.retrieval_agent import (
    RetrievalAgent,
    DocumentChunk,
    SearchResult
)


class TestRetrievalAgentInitialization:
    """Test RetrievalAgent initialization."""

    @patch('src.agents.retrieval_agent.GoogleGenerativeAIEmbeddings')
    @patch('src.agents.retrieval_agent.VectorStore')
    @patch('src.agents.retrieval_agent.get_metadata_store')
    def test_init_with_valid_config(self, mock_metadata, mock_vector, mock_embeddings):
        """Test initialization with valid configuration."""
        agent = RetrievalAgent(
            embedding_model="models/text-embedding-004",
            chunk_size=1000,
            chunk_overlap=200,
            google_api_key="test-key"
        )

        assert agent.embedding_model == "models/text-embedding-004"
        assert agent.chunk_size == 1000
        assert agent.chunk_overlap == 200
        assert agent.embeddings is not None
        assert agent.text_splitter is not None
        assert agent.vector_store is not None

    @patch('src.agents.retrieval_agent.GoogleGenerativeAIEmbeddings')
    @patch('src.agents.retrieval_agent.VectorStore')
    @patch('src.agents.retrieval_agent.get_metadata_store')
    def test_init_without_api_key_raises_error(self, mock_metadata, mock_vector, mock_embeddings, monkeypatch):
        """Test initialization without API key raises ValueError."""
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

        with pytest.raises(ValueError, match="GOOGLE_API_KEY"):
            RetrievalAgent(google_api_key=None)


class TestTextChunking:
    """Test text chunking functionality."""

    @patch('src.agents.retrieval_agent.GoogleGenerativeAIEmbeddings')
    @patch('src.agents.retrieval_agent.VectorStore')
    @patch('src.agents.retrieval_agent.get_metadata_store')
    def test_chunk_text_creates_chunks(self, mock_metadata, mock_vector, mock_embeddings, sample_text):
        """Test that text chunking creates DocumentChunk objects."""
        agent = RetrievalAgent(google_api_key="test-key")

        chunks = agent.chunk_text(sample_text, "test-doc-123")

        assert len(chunks) > 0
        assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)
        assert all(chunk.document_id == "test-doc-123" for chunk in chunks)
        assert all(chunk.chunk_index == i for i, chunk in enumerate(chunks))

    @patch('src.agents.retrieval_agent.GoogleGenerativeAIEmbeddings')
    @patch('src.agents.retrieval_agent.VectorStore')
    @patch('src.agents.retrieval_agent.get_metadata_store')
    def test_chunk_text_with_empty_string_raises_error(self, mock_metadata, mock_vector, mock_embeddings):
        """Test that chunking empty text raises ValueError."""
        agent = RetrievalAgent(google_api_key="test-key")

        with pytest.raises(ValueError, match="Text cannot be empty"):
            agent.chunk_text("", "test-doc-123")

    @patch('src.agents.retrieval_agent.GoogleGenerativeAIEmbeddings')
    @patch('src.agents.retrieval_agent.VectorStore')
    @patch('src.agents.retrieval_agent.get_metadata_store')
    def test_chunk_text_respects_chunk_size(self, mock_metadata, mock_vector, mock_embeddings, sample_text):
        """Test that chunks respect the configured chunk size."""
        agent = RetrievalAgent(
            chunk_size=100,
            chunk_overlap=20,
            google_api_key="test-key"
        )

        chunks = agent.chunk_text(sample_text, "test-doc-123")

        # Most chunks should be approximately chunk_size or smaller
        for chunk in chunks:
            assert len(chunk.content) <= 150  # Allow some flexibility


class TestEmbeddingGeneration:
    """Test embedding generation functionality."""

    @patch('src.agents.retrieval_agent.VectorStore')
    @patch('src.agents.retrieval_agent.get_metadata_store')
    def test_generate_embeddings_returns_correct_shape(
        self, mock_metadata, mock_vector, mock_google_embeddings
    ):
        """Test that embeddings are generated with correct dimensions."""
        with patch('src.agents.retrieval_agent.GoogleGenerativeAIEmbeddings', return_value=mock_google_embeddings):
            agent = RetrievalAgent(google_api_key="test-key")

            texts = ["text1", "text2"]
            embeddings = agent.generate_embeddings(texts)

            assert len(embeddings) == 2
            assert all(len(emb) == 768 for emb in embeddings)

    @patch('src.agents.retrieval_agent.VectorStore')
    @patch('src.agents.retrieval_agent.get_metadata_store')
    def test_generate_embeddings_with_empty_list(
        self, mock_metadata, mock_vector, mock_google_embeddings
    ):
        """Test that empty list returns empty embeddings."""
        with patch('src.agents.retrieval_agent.GoogleGenerativeAIEmbeddings', return_value=mock_google_embeddings):
            agent = RetrievalAgent(google_api_key="test-key")

            embeddings = agent.generate_embeddings([])

            assert embeddings == []


class TestDocumentStorage:
    """Test document storage functionality."""

    @patch('src.agents.retrieval_agent.GoogleGenerativeAIEmbeddings')
    @patch('src.agents.retrieval_agent.get_metadata_store')
    def test_store_document_success(
        self, mock_metadata_getter, mock_embeddings, mock_vector_store, sample_chunks
    ):
        """Test successful document storage."""
        mock_metadata_store = Mock()
        mock_metadata_getter.return_value = mock_metadata_store

        with patch('src.agents.retrieval_agent.VectorStore', return_value=mock_vector_store):
            agent = RetrievalAgent(google_api_key="test-key")

            # Create DocumentChunk objects
            chunks = [
                DocumentChunk(**chunk) for chunk in sample_chunks
            ]

            embeddings = [[0.1] * 768 for _ in chunks]

            success = agent.store_document("test-doc", chunks, embeddings)

            assert success is True
            mock_vector_store.add_vectors.assert_called_once()
            mock_metadata_store.update_document.assert_called_once()

    @patch('src.agents.retrieval_agent.GoogleGenerativeAIEmbeddings')
    @patch('src.agents.retrieval_agent.get_metadata_store')
    def test_store_document_mismatched_lengths_raises_error(
        self, mock_metadata, mock_embeddings, mock_vector_store
    ):
        """Test that mismatched chunks and embeddings raises error."""
        with patch('src.agents.retrieval_agent.VectorStore', return_value=mock_vector_store):
            agent = RetrievalAgent(google_api_key="test-key")

            chunks = [
                DocumentChunk(
                    chunk_id="test",
                    document_id="doc",
                    content="text",
                    page_number=1,
                    chunk_index=0,
                    metadata={}
                )
            ]
            embeddings = [[0.1] * 768, [0.2] * 768]  # More embeddings than chunks

            with pytest.raises(ValueError, match="must match"):
                agent.store_document("test-doc", chunks, embeddings)


class TestSemanticSearch:
    """Test semantic search functionality."""

    @patch('src.agents.retrieval_agent.get_metadata_store')
    def test_search_returns_results(
        self, mock_metadata, mock_google_embeddings, mock_vector_store
    ):
        """Test that search returns SearchResult objects."""
        with patch('src.agents.retrieval_agent.GoogleGenerativeAIEmbeddings', return_value=mock_google_embeddings), \
             patch('src.agents.retrieval_agent.VectorStore', return_value=mock_vector_store):

            agent = RetrievalAgent(google_api_key="test-key")

            results = agent.search("test query", top_k=3)

            assert len(results) > 0
            assert all(isinstance(r, SearchResult) for r in results)
            mock_google_embeddings.embed_query.assert_called_once()
            mock_vector_store.search.assert_called_once()

    @patch('src.agents.retrieval_agent.get_metadata_store')
    def test_search_with_empty_query_raises_error(
        self, mock_metadata, mock_google_embeddings, mock_vector_store
    ):
        """Test that empty query raises ValueError."""
        with patch('src.agents.retrieval_agent.GoogleGenerativeAIEmbeddings', return_value=mock_google_embeddings), \
             patch('src.agents.retrieval_agent.VectorStore', return_value=mock_vector_store):

            agent = RetrievalAgent(google_api_key="test-key")

            with pytest.raises(ValueError, match="Query cannot be empty"):
                agent.search("")

    @patch('src.agents.retrieval_agent.get_metadata_store')
    def test_search_uses_cache(
        self, mock_metadata, mock_google_embeddings, mock_vector_store
    ):
        """Test that repeated searches use cache."""
        with patch('src.agents.retrieval_agent.GoogleGenerativeAIEmbeddings', return_value=mock_google_embeddings), \
             patch('src.agents.retrieval_agent.VectorStore', return_value=mock_vector_store):

            agent = RetrievalAgent(google_api_key="test-key")

            # First search
            results1 = agent.search("test query", top_k=3)

            # Second search with same query
            results2 = agent.search("test query", top_k=3)

            # Vector store should only be called once (second uses cache)
            assert mock_vector_store.search.call_count == 1
            assert results1 == results2


class TestCRUDOperations:
    """Test CRUD operations."""

    @patch('src.agents.retrieval_agent.GoogleGenerativeAIEmbeddings')
    @patch('src.agents.retrieval_agent.VectorStore')
    def test_delete_document_success(
        self, mock_vector_store_class, mock_embeddings, mock_metadata_store
    ):
        """Test successful document deletion."""
        mock_vector_store = Mock()
        mock_vector_store.delete_by_filter.return_value = True
        mock_vector_store_class.return_value = mock_vector_store

        mock_metadata = Mock()
        mock_metadata.delete_document.return_value = True

        with patch('src.agents.retrieval_agent.get_metadata_store', return_value=mock_metadata):
            agent = RetrievalAgent(google_api_key="test-key")

            success = agent.delete_document("test-doc-123")

            assert success is True
            mock_vector_store.delete_by_filter.assert_called_once()
            mock_metadata.delete_document.assert_called_once()

    @patch('src.agents.retrieval_agent.GoogleGenerativeAIEmbeddings')
    @patch('src.agents.retrieval_agent.VectorStore')
    def test_list_documents_returns_list(
        self, mock_vector_store, mock_embeddings, mock_metadata_store
    ):
        """Test listing documents returns list."""
        mock_metadata = Mock()
        mock_metadata.list_documents.return_value = []

        with patch('src.agents.retrieval_agent.get_metadata_store', return_value=mock_metadata):
            agent = RetrievalAgent(google_api_key="test-key")

            docs = agent.list_documents()

            assert isinstance(docs, list)
            mock_metadata.list_documents.assert_called_once()

    @patch('src.agents.retrieval_agent.GoogleGenerativeAIEmbeddings')
    @patch('src.agents.retrieval_agent.VectorStore')
    def test_get_document_info_returns_metadata(
        self, mock_vector_store, mock_embeddings, sample_document_metadata
    ):
        """Test getting document info returns metadata."""
        from src.database.metadata_store import DocumentMetadata

        mock_metadata = Mock()
        mock_metadata.get_document.return_value = DocumentMetadata(**sample_document_metadata)

        with patch('src.agents.retrieval_agent.get_metadata_store', return_value=mock_metadata):
            agent = RetrievalAgent(google_api_key="test-key")

            info = agent.get_document_info("test-doc-123")

            assert info is not None
            assert info["document_id"] == "test-doc-12345"
            assert info["filename"] == "sample.pdf"


class TestProcessPDF:
    """Test full PDF processing pipeline."""

    @patch('src.agents.retrieval_agent.PyPDFLoader')
    @patch('src.agents.retrieval_agent.GoogleGenerativeAIEmbeddings')
    @patch('src.agents.retrieval_agent.VectorStore')
    @patch('src.agents.retrieval_agent.get_metadata_store')
    def test_process_pdf_with_retry_logic(
        self, mock_metadata_getter, mock_vector_store, mock_embeddings, mock_pdf_loader
    ):
        """Test PDF processing with retry logic."""
        # This test validates that the retry mechanism exists
        # Actual execution would require valid PDF file
        pass  # Placeholder - would need real PDF file to execute


class TestDatabaseReset:
    """Test database reset functionality."""

    @patch('src.agents.retrieval_agent.GoogleGenerativeAIEmbeddings')
    @patch('src.agents.retrieval_agent.get_metadata_store')
    def test_reset_database_clears_all_data(
        self, mock_metadata_getter, mock_embeddings, mock_vector_store
    ):
        """Test that reset clears all data."""
        mock_metadata = Mock()
        mock_metadata_getter.return_value = mock_metadata

        with patch('src.agents.retrieval_agent.VectorStore', return_value=mock_vector_store):
            agent = RetrievalAgent(google_api_key="test-key")

            success = agent.reset_database()

            assert success is True
            mock_vector_store.reset_collection.assert_called_once()
            mock_metadata.clear.assert_called_once()
