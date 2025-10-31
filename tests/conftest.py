"""
Pytest configuration and shared fixtures.

This file contains pytest fixtures that are shared across all test modules.
"""

import pytest
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock
from datetime import datetime

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def sample_pdf_path():
    """
    Fixture providing path to sample PDF file.

    Returns:
        Path to sample.pdf in fixtures directory
    """
    return Path(__file__).parent / "fixtures" / "sample.pdf"


@pytest.fixture
def sample_text():
    """
    Fixture providing sample text content.

    Returns:
        Sample text string for testing
    """
    return """
    This is a sample document for testing the PDF summarization system.

    The document contains multiple paragraphs with various topics. It discusses
    the importance of testing in software development and how automated tests
    help ensure code quality and reliability.

    Additionally, it covers best practices for writing unit tests, including
    the use of mocks and fixtures to isolate components and make tests
    more maintainable and reliable.

    The final section emphasizes the value of integration tests in validating
    that different components work together correctly in a production-like
    environment.
    """


@pytest.fixture
def sample_document_id():
    """
    Fixture providing a sample document ID.

    Returns:
        Sample document ID string
    """
    return "test-doc-12345"


@pytest.fixture
def sample_document_metadata():
    """
    Fixture providing sample document metadata.

    Returns:
        Dictionary with document metadata
    """
    return {
        "document_id": "test-doc-12345",
        "filename": "sample.pdf",
        "upload_date": "2025-10-30T10:00:00",
        "num_pages": 5,
        "file_size": 102400,
        "processing_status": "completed",
        "num_chunks": 10
    }


@pytest.fixture
def sample_chunks():
    """
    Fixture providing sample document chunks.

    Returns:
        List of sample chunk dictionaries
    """
    return [
        {
            "chunk_id": "test-doc-12345_chunk_0",
            "document_id": "test-doc-12345",
            "content": "This is the first chunk of text.",
            "page_number": 1,
            "chunk_index": 0,
            "metadata": {"chunk_size": 32}
        },
        {
            "chunk_id": "test-doc-12345_chunk_1",
            "document_id": "test-doc-12345",
            "content": "This is the second chunk of text.",
            "page_number": 1,
            "chunk_index": 1,
            "metadata": {"chunk_size": 33}
        },
        {
            "chunk_id": "test-doc-12345_chunk_2",
            "document_id": "test-doc-12345",
            "content": "This is the third chunk of text.",
            "page_number": 2,
            "chunk_index": 2,
            "metadata": {"chunk_size": 32}
        }
    ]


@pytest.fixture
def sample_embeddings():
    """
    Fixture providing sample embeddings.

    Returns:
        List of sample embedding vectors (768 dimensions)
    """
    return [
        [0.1] * 768,  # Simplified embedding for chunk 0
        [0.2] * 768,  # Simplified embedding for chunk 1
        [0.3] * 768   # Simplified embedding for chunk 2
    ]


@pytest.fixture
def mock_google_embeddings():
    """
    Fixture providing a mocked GoogleGenerativeAIEmbeddings instance.

    Returns:
        Mock object for GoogleGenerativeAIEmbeddings
    """
    mock = Mock()
    mock.embed_documents.return_value = [[0.1] * 768, [0.2] * 768]
    mock.embed_query.return_value = [0.15] * 768
    return mock


@pytest.fixture
def mock_llm():
    """
    Fixture providing a mocked LLM instance.

    Returns:
        Mock object for LLM (Gemini/Ollama)
    """
    mock = Mock()
    return mock


@pytest.fixture
def mock_vector_store():
    """
    Fixture providing a mocked VectorStore instance.

    Returns:
        Mock object for VectorStore
    """
    mock = Mock()
    mock.add_vectors.return_value = True
    mock.search.return_value = [
        {
            "id": "chunk_0",
            "score": 0.95,
            "payload": {
                "chunk_id": "test-doc-12345_chunk_0",
                "document_id": "test-doc-12345",
                "content": "Sample content",
                "page_number": 1,
                "chunk_index": 0,
                "metadata": {}
            }
        }
    ]
    mock.delete_by_filter.return_value = True
    mock.reset_collection.return_value = True
    return mock


@pytest.fixture
def mock_metadata_store():
    """
    Fixture providing a mocked MetadataStore instance.

    Returns:
        Mock object for MetadataStore
    """
    from src.database.metadata_store import DocumentMetadata

    mock = Mock()
    mock.add_document.return_value = True
    mock.get_document.return_value = DocumentMetadata(
        document_id="test-doc-12345",
        filename="sample.pdf",
        upload_date="2025-10-30T10:00:00",
        num_pages=5,
        file_size=102400,
        processing_status="completed",
        num_chunks=10
    )
    mock.update_document.return_value = True
    mock.delete_document.return_value = True
    mock.list_documents.return_value = []
    return mock


@pytest.fixture
def mock_retrieval_agent():
    """
    Fixture providing a mocked RetrievalAgent instance.

    Returns:
        Mock object for RetrievalAgent
    """
    from src.agents.retrieval_agent import SearchResult, DocumentChunk

    mock = Mock()

    # Mock search results
    chunk = DocumentChunk(
        chunk_id="test-chunk",
        document_id="test-doc",
        content="Sample content for testing",
        page_number=1,
        chunk_index=0,
        metadata={}
    )

    search_result = SearchResult(
        chunk=chunk,
        score=0.95,
        rank=1
    )

    mock.search.return_value = [search_result]
    mock.get_document_info.return_value = {
        "document_id": "test-doc",
        "filename": "sample.pdf",
        "num_pages": 5,
        "processing_status": "completed"
    }

    return mock


@pytest.fixture
def sample_summary_response():
    """
    Fixture providing a sample summary response.

    Returns:
        Dictionary with summary response data
    """
    return {
        "summary_id": "summary-123",
        "document_id": "test-doc-12345",
        "summary_text": "This is a brief summary of the document. It covers the main points. The document discusses testing.",
        "summary_type": "brief",
        "tokens_used": 150,
        "page_references": [1, 2, 3],
        "timestamp": "2025-10-30T10:30:00",
        "cached": False
    }


@pytest.fixture
def mock_requests():
    """
    Fixture providing a mocked requests module.

    Returns:
        Mock object for requests
    """
    mock = Mock()

    # Mock successful responses
    success_response = Mock()
    success_response.status_code = 200
    success_response.json.return_value = {"status": "ok"}

    mock.get.return_value = success_response
    mock.post.return_value = success_response
    mock.delete.return_value = success_response

    return mock


@pytest.fixture
def test_api_key():
    """
    Fixture providing a test API key.

    Returns:
        Test API key string
    """
    return "test-api-key-12345"


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """
    Auto-use fixture that sets up mock environment variables for all tests.

    This prevents tests from trying to use real API keys.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-api-key")
    monkeypatch.setenv("API_KEY", "test-api-key")
    monkeypatch.setenv("QDRANT_URL", ":memory:")


@pytest.fixture
def cleanup_test_files():
    """
    Fixture for cleaning up test files after tests.

    Yields control to the test, then cleans up.
    """
    test_files = []

    def register_file(filepath):
        test_files.append(filepath)

    yield register_file

    # Cleanup after test
    for filepath in test_files:
        if os.path.exists(filepath):
            os.remove(filepath)
