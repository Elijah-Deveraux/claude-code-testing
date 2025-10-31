"""
Unit tests for FastAPI endpoints.

Tests cover:
- All API endpoints (happy paths and error cases)
- Authentication
- Request/response validation
- Error handling
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from io import BytesIO

# Import the FastAPI app
from src.api.main import app


class TestHealthEndpoint:
    """Test the /health endpoint."""

    def test_health_check_success(self):
        """Test successful health check."""
        client = TestClient(app)

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_health_check_includes_dependencies(self):
        """Test health check includes dependency status."""
        client = TestClient(app)

        response = client.get("/health")
        data = response.json()

        assert "dependencies" in data
        assert isinstance(data["dependencies"], dict)


class TestMetricsEndpoint:
    """Test the /metrics endpoint."""

    def test_metrics_requires_authentication(self):
        """Test metrics endpoint requires API key."""
        client = TestClient(app)

        response = client.get("/metrics")

        assert response.status_code == 403

    def test_metrics_with_valid_auth(self):
        """Test metrics with valid authentication."""
        client = TestClient(app)

        response = client.get(
            "/metrics",
            headers={"X-API-Key": "dev-key-12345"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_documents" in data
        assert "total_summaries" in data


class TestUploadPDFEndpoint:
    """Test the /upload-pdf endpoint."""

    def test_upload_pdf_requires_authentication(self):
        """Test upload requires API key."""
        client = TestClient(app)

        response = client.post("/upload-pdf")

        assert response.status_code == 403

    def test_upload_pdf_with_no_file(self):
        """Test upload with no file returns error."""
        client = TestClient(app)

        response = client.post(
            "/upload-pdf",
            headers={"X-API-Key": "dev-key-12345"}
        )

        assert response.status_code == 422  # Validation error

    @patch('src.api.routes.documents.retrieval_agent')
    def test_upload_pdf_success(self, mock_agent):
        """Test successful PDF upload."""
        mock_agent.process_pdf.return_value = {
            "success": True,
            "document_id": "test-doc-123",
            "filename": "test.pdf",
            "num_pages": 5,
            "num_chunks": 10,
            "file_size": 102400
        }

        client = TestClient(app)

        # Create a mock PDF file
        pdf_content = b"%PDF-1.4\nMock PDF content"
        files = {"file": ("test.pdf", BytesIO(pdf_content), "application/pdf")}

        response = client.post(
            "/upload-pdf",
            headers={"X-API-Key": "dev-key-12345"},
            files=files
        )

        assert response.status_code == 201
        data = response.json()
        assert data["document_id"] == "test-doc-123"
        assert data["filename"] == "test.pdf"

    @patch('src.api.routes.documents.retrieval_agent')
    def test_upload_non_pdf_file(self, mock_agent):
        """Test uploading non-PDF file returns error."""
        client = TestClient(app)

        files = {"file": ("test.txt", BytesIO(b"Not a PDF"), "text/plain")}

        response = client.post(
            "/upload-pdf",
            headers={"X-API-Key": "dev-key-12345"},
            files=files
        )

        assert response.status_code == 400


class TestGetDocumentsEndpoint:
    """Test the /documents endpoint."""

    def test_get_documents_requires_authentication(self):
        """Test listing documents requires API key."""
        client = TestClient(app)

        response = client.get("/documents")

        assert response.status_code == 403

    @patch('src.api.routes.documents.retrieval_agent')
    def test_get_documents_success(self, mock_agent):
        """Test successful document listing."""
        mock_agent.list_documents.return_value = [
            {
                "document_id": "doc1",
                "filename": "test1.pdf",
                "num_pages": 5
            },
            {
                "document_id": "doc2",
                "filename": "test2.pdf",
                "num_pages": 3
            }
        ]

        client = TestClient(app)

        response = client.get(
            "/documents",
            headers={"X-API-Key": "dev-key-12345"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert len(data["documents"]) == 2

    @patch('src.api.routes.documents.retrieval_agent')
    def test_get_documents_empty_list(self, mock_agent):
        """Test listing when no documents exist."""
        mock_agent.list_documents.return_value = []

        client = TestClient(app)

        response = client.get(
            "/documents",
            headers={"X-API-Key": "dev-key-12345"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["documents"] == []


class TestGetDocumentEndpoint:
    """Test the /document/{doc_id} endpoint."""

    def test_get_document_requires_authentication(self):
        """Test get document requires API key."""
        client = TestClient(app)

        response = client.get("/document/test-doc-123")

        assert response.status_code == 403

    @patch('src.api.routes.documents.retrieval_agent')
    def test_get_document_success(self, mock_agent):
        """Test successful document retrieval."""
        mock_agent.get_document_info.return_value = {
            "document_id": "test-doc-123",
            "filename": "test.pdf",
            "num_pages": 5,
            "processing_status": "completed"
        }

        client = TestClient(app)

        response = client.get(
            "/document/test-doc-123",
            headers={"X-API-Key": "dev-key-12345"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "test-doc-123"

    @patch('src.api.routes.documents.retrieval_agent')
    def test_get_document_not_found(self, mock_agent):
        """Test get non-existent document returns 404."""
        mock_agent.get_document_info.return_value = None

        client = TestClient(app)

        response = client.get(
            "/document/non-existent",
            headers={"X-API-Key": "dev-key-12345"}
        )

        assert response.status_code == 404


class TestDeleteDocumentEndpoint:
    """Test the /document/{doc_id} DELETE endpoint."""

    def test_delete_document_requires_authentication(self):
        """Test delete requires API key."""
        client = TestClient(app)

        response = client.delete("/document/test-doc-123")

        assert response.status_code == 403

    @patch('src.api.routes.documents.retrieval_agent')
    def test_delete_document_success(self, mock_agent):
        """Test successful document deletion."""
        mock_agent.delete_document.return_value = True

        client = TestClient(app)

        response = client.delete(
            "/document/test-doc-123",
            headers={"X-API-Key": "dev-key-12345"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deleted"

    @patch('src.api.routes.documents.retrieval_agent')
    def test_delete_document_not_found(self, mock_agent):
        """Test deleting non-existent document returns 404."""
        mock_agent.delete_document.return_value = False

        client = TestClient(app)

        response = client.delete(
            "/document/non-existent",
            headers={"X-API-Key": "dev-key-12345"}
        )

        assert response.status_code == 404


class TestSummarizeEndpoint:
    """Test the /summarize endpoint."""

    def test_summarize_requires_authentication(self):
        """Test summarize requires API key."""
        client = TestClient(app)

        response = client.post("/summarize")

        assert response.status_code == 403

    def test_summarize_missing_fields(self):
        """Test summarize with missing fields returns validation error."""
        client = TestClient(app)

        response = client.post(
            "/summarize",
            headers={"X-API-Key": "dev-key-12345"},
            json={}
        )

        assert response.status_code == 422

    @patch('src.api.routes.summaries.summarizer_agent')
    @patch('src.api.routes.summaries.retrieval_agent')
    def test_summarize_success(self, mock_retrieval, mock_summarizer):
        """Test successful summary generation."""
        from src.agents.summarizer_agent import SummaryResponse, SummaryType
        from datetime import datetime

        # Mock retrieval agent
        mock_retrieval.get_document_info.return_value = {
            "document_id": "test-doc",
            "filename": "test.pdf"
        }

        # Mock summarizer response
        mock_summarizer.generate_summary.return_value = SummaryResponse(
            summary_id="summary-123",
            document_id="test-doc",
            summary_text="This is a test summary.",
            summary_type=SummaryType.BRIEF,
            tokens_used=50,
            page_references=[1, 2],
            timestamp=datetime.now(),
            cached=False
        )

        client = TestClient(app)

        response = client.post(
            "/summarize",
            headers={"X-API-Key": "dev-key-12345"},
            json={
                "document_id": "test-doc",
                "summary_type": "brief"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["summary_id"] == "summary-123"
        assert data["summary_text"] == "This is a test summary."

    @patch('src.api.routes.summaries.retrieval_agent')
    def test_summarize_document_not_found(self, mock_retrieval):
        """Test summarize with non-existent document."""
        mock_retrieval.get_document_info.return_value = None

        client = TestClient(app)

        response = client.post(
            "/summarize",
            headers={"X-API-Key": "dev-key-12345"},
            json={
                "document_id": "non-existent",
                "summary_type": "brief"
            }
        )

        assert response.status_code == 404

    def test_summarize_invalid_summary_type(self):
        """Test summarize with invalid summary type."""
        client = TestClient(app)

        response = client.post(
            "/summarize",
            headers={"X-API-Key": "dev-key-12345"},
            json={
                "document_id": "test-doc",
                "summary_type": "invalid"
            }
        )

        assert response.status_code == 422


class TestAuthenticationMiddleware:
    """Test authentication middleware."""

    def test_request_without_api_key(self):
        """Test request without API key is rejected."""
        client = TestClient(app)

        response = client.get("/documents")

        assert response.status_code == 403

    def test_request_with_invalid_api_key(self):
        """Test request with invalid API key is rejected."""
        client = TestClient(app)

        response = client.get(
            "/documents",
            headers={"X-API-Key": "invalid-key"}
        )

        assert response.status_code == 403

    def test_request_with_valid_api_key(self):
        """Test request with valid API key is allowed."""
        client = TestClient(app)

        with patch('src.api.routes.documents.retrieval_agent') as mock_agent:
            mock_agent.list_documents.return_value = []

            response = client.get(
                "/documents",
                headers={"X-API-Key": "dev-key-12345"}
            )

            assert response.status_code == 200


class TestRateLimiting:
    """Test rate limiting middleware."""

    def test_rate_limiting_blocks_excessive_requests(self):
        """Test that rate limiting blocks excessive requests."""
        client = TestClient(app)

        # This would require actual rate limit testing
        # Placeholder for rate limit validation
        pass


class TestErrorHandling:
    """Test error handling middleware."""

    @patch('src.api.routes.documents.retrieval_agent')
    def test_internal_error_returns_500(self, mock_agent):
        """Test that internal errors return 500."""
        mock_agent.list_documents.side_effect = Exception("Internal error")

        client = TestClient(app)

        response = client.get(
            "/documents",
            headers={"X-API-Key": "dev-key-12345"}
        )

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data


class TestCORSHeaders:
    """Test CORS configuration."""

    def test_cors_headers_present(self):
        """Test that CORS headers are present in responses."""
        client = TestClient(app)

        response = client.get("/health")

        # Check for CORS headers
        assert "access-control-allow-origin" in response.headers


class TestOpenAPIDocumentation:
    """Test OpenAPI documentation."""

    def test_docs_endpoint_accessible(self):
        """Test /docs endpoint is accessible."""
        client = TestClient(app)

        response = client.get("/docs")

        assert response.status_code == 200

    def test_openapi_json_accessible(self):
        """Test /openapi.json is accessible."""
        client = TestClient(app)

        response = client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data

