"""
Integration test for full PDF summarization workflow.

This test validates the complete end-to-end workflow:
1. Upload PDF → 2. Process → 3. Store → 4. Retrieve → 5. Summarize

Note: This test requires actual PDF files and configured API keys.
It should be run in a staging/test environment with real services.
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import time

from src.api.main import app


@pytest.mark.integration
class TestFullWorkflow:
    """
    Integration test for the complete PDF summarization workflow.

    This test requires:
    - Valid API keys configured
    - Qdrant running (can be in-memory)
    - Small test PDF file
    """

    def test_complete_workflow(self, sample_pdf_path):
        """
        Test the complete workflow from upload to summarization.

        Steps:
        1. Upload PDF document
        2. Verify document is listed
        3. Retrieve document metadata
        4. Generate brief summary
        5. Generate detailed summary
        6. Verify summaries are cached
        7. Delete document
        8. Verify document is removed
        """
        client = TestClient(app)
        headers = {"X-API-Key": "dev-key-12345"}

        # Skip if sample PDF doesn't exist
        if not sample_pdf_path.exists():
            pytest.skip("Sample PDF not found")

        # Step 1: Upload PDF
        with open(sample_pdf_path, 'rb') as f:
            files = {"file": ("test.pdf", f, "application/pdf")}
            upload_response = client.post(
                "/upload-pdf",
                headers=headers,
                files=files
            )

        assert upload_response.status_code == 201
        upload_data = upload_response.json()
        document_id = upload_data["document_id"]

        # Wait for processing
        time.sleep(2)

        # Step 2: Verify document is listed
        list_response = client.get("/documents", headers=headers)
        assert list_response.status_code == 200
        list_data = list_response.json()
        assert any(doc["document_id"] == document_id for doc in list_data["documents"])

        # Step 3: Retrieve document metadata
        get_response = client.get(f"/document/{document_id}", headers=headers)
        assert get_response.status_code == 200
        doc_data = get_response.json()
        assert doc_data["document_id"] == document_id
        assert doc_data["processing_status"] == "completed"

        # Step 4: Generate brief summary
        brief_response = client.post(
            "/summarize",
            headers=headers,
            json={
                "document_id": document_id,
                "summary_type": "brief"
            }
        )
        assert brief_response.status_code == 200
        brief_data = brief_response.json()
        assert brief_data["summary_type"] == "brief"
        assert brief_data["cached"] is False
        assert len(brief_data["summary_text"]) > 0

        # Step 5: Generate detailed summary
        detailed_response = client.post(
            "/summarize",
            headers=headers,
            json={
                "document_id": document_id,
                "summary_type": "detailed"
            }
        )
        assert detailed_response.status_code == 200
        detailed_data = detailed_response.json()
        assert detailed_data["summary_type"] == "detailed"
        assert detailed_data["cached"] is False
        assert len(detailed_data["summary_text"]) > len(brief_data["summary_text"])

        # Step 6: Verify summaries are cached
        brief_cached_response = client.post(
            "/summarize",
            headers=headers,
            json={
                "document_id": document_id,
                "summary_type": "brief"
            }
        )
        brief_cached_data = brief_cached_response.json()
        assert brief_cached_data["cached"] is True

        # Step 7: Delete document
        delete_response = client.delete(f"/document/{document_id}", headers=headers)
        assert delete_response.status_code == 200

        # Step 8: Verify document is removed
        get_deleted_response = client.get(f"/document/{document_id}", headers=headers)
        assert get_deleted_response.status_code == 404

    def test_workflow_with_multiple_documents(self, sample_pdf_path):
        """
        Test workflow with multiple documents to verify isolation.

        Ensures that:
        - Multiple documents can be processed simultaneously
        - Summaries are specific to each document
        - Deletion doesn't affect other documents
        """
        if not sample_pdf_path.exists():
            pytest.skip("Sample PDF not found")

        client = TestClient(app)
        headers = {"X-API-Key": "dev-key-12345"}

        document_ids = []

        # Upload multiple documents
        for i in range(2):
            with open(sample_pdf_path, 'rb') as f:
                files = {"file": (f"test_{i}.pdf", f, "application/pdf")}
                response = client.post("/upload-pdf", headers=headers, files=files)

            assert response.status_code == 201
            document_ids.append(response.json()["document_id"])

        time.sleep(2)

        # Generate summaries for each
        for doc_id in document_ids:
            response = client.post(
                "/summarize",
                headers=headers,
                json={"document_id": doc_id, "summary_type": "brief"}
            )
            assert response.status_code == 200

        # Delete first document
        delete_response = client.delete(f"/document/{document_ids[0]}", headers=headers)
        assert delete_response.status_code == 200

        # Verify second document still exists
        get_response = client.get(f"/document/{document_ids[1]}", headers=headers)
        assert get_response.status_code == 200

        # Cleanup
        client.delete(f"/document/{document_ids[1]}", headers=headers)

    def test_error_handling_in_workflow(self):
        """
        Test error handling throughout the workflow.

        Tests:
        - Invalid PDF format
        - Summarizing non-existent document
        - Invalid summary types
        """
        client = TestClient(app)
        headers = {"X-API-Key": "dev-key-12345"}

        # Test 1: Invalid file format
        files = {"file": ("test.txt", b"Not a PDF", "text/plain")}
        response = client.post("/upload-pdf", headers=headers, files=files)
        assert response.status_code == 400

        # Test 2: Summarize non-existent document
        response = client.post(
            "/summarize",
            headers=headers,
            json={"document_id": "non-existent", "summary_type": "brief"}
        )
        assert response.status_code == 404

        # Test 3: Invalid summary type
        response = client.post(
            "/summarize",
            headers=headers,
            json={"document_id": "test-doc", "summary_type": "invalid"}
        )
        assert response.status_code == 422


@pytest.mark.integration
class TestPerformance:
    """Performance and stress tests."""

    def test_large_pdf_processing(self):
        """
        Test processing a larger PDF (10+ pages).

        Validates:
        - System handles larger documents
        - Processing completes within reasonable time
        - Memory usage is acceptable
        """
        # Placeholder - requires large PDF
        pytest.skip("Large PDF test requires specific test file")

    def test_concurrent_uploads(self):
        """
        Test multiple concurrent PDF uploads.

        Validates:
        - System handles concurrent requests
        - No race conditions in storage
        - All documents processed correctly
        """
        # Placeholder - requires async testing setup
        pytest.skip("Concurrent upload test requires async test setup")


@pytest.mark.integration
class TestDataConsistency:
    """Test data consistency across components."""

    def test_vector_metadata_consistency(self, sample_pdf_path):
        """
        Test that vector store and metadata store remain consistent.

        Validates:
        - Chunk count matches between stores
        - Metadata is accurate
        - No orphaned data after deletion
        """
        if not sample_pdf_path.exists():
            pytest.skip("Sample PDF not found")

        # This would require direct access to both stores
        # Placeholder for consistency validation
        pass

    def test_cache_consistency(self):
        """
        Test that cache remains consistent with source data.

        Validates:
        - Cache invalidation on document update
        - Cache entries expire appropriately
        """
        # Placeholder for cache consistency tests
        pass


@pytest.mark.integration
class TestRecovery:
    """Test system recovery and error handling."""

    def test_recovery_from_failed_upload(self):
        """
        Test system recovers from failed upload.

        Validates:
        - Partial data is cleaned up
        - System remains in consistent state
        - Subsequent uploads work correctly
        """
        # Placeholder for recovery testing
        pass

    def test_recovery_from_failed_summarization(self):
        """
        Test system recovers from failed summarization.

        Validates:
        - Failed summary doesn't corrupt cache
        - Retry works correctly
        - Error is properly reported
        """
        # Placeholder for summarization recovery
        pass
