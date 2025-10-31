"""
Document Management Endpoints.

Handles PDF upload, document listing, retrieval, and deletion operations.
"""

import logging
import os
import uuid
from datetime import datetime
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from src.api.models import (
    UploadResponse,
    DocumentListResponse,
    DocumentDetailResponse,
    DocumentMetadata,
    DeleteResponse,
    ProcessingStatus
)
from src.api.middleware.error_handler import DocumentNotFoundError, DocumentProcessingError
from src.api.routes.health import increment_document_count

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


# In-memory document storage (will be replaced with actual database in Stage 3)
_documents_store: dict = {}


@router.post(
    "/upload-pdf",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload PDF Document",
    description="Upload a PDF file for processing and summarization.",
    responses={
        201: {"description": "PDF uploaded and processed successfully"},
        400: {"description": "Bad request - Invalid file or format"},
        401: {"description": "Unauthorized - Missing or invalid API key"},
        500: {"description": "Internal server error - Processing failed"}
    }
)
async def upload_pdf(
    file: UploadFile = File(..., description="PDF file to upload")
) -> UploadResponse:
    """
    Upload a PDF document for processing.

    Steps:
    1. Validate file format (must be PDF)
    2. Save file temporarily
    3. Extract text and generate embeddings (Stage 3)
    4. Store in vector database (Stage 3)
    5. Return document metadata

    Args:
        file: Uploaded PDF file

    Returns:
        UploadResponse: Document metadata and status

    Raises:
        HTTPException: If file is invalid or processing fails
    """
    logger.info("=" * 60)
    logger.info("UPLOAD ENDPOINT CALLED")
    logger.info("=" * 60)

    # Log detailed request info
    logger.info(f"PDF upload requested: filename={file.filename}, content_type={file.content_type}")
    logger.info(f"File object type: {type(file)}")
    logger.info(f"Has filename: {file.filename is not None}")

    # Try to read a bit of the file to check if it's actually sent
    try:
        content_preview = await file.read(100)
        logger.info(f"File content preview (first 100 bytes): {content_preview[:50]}...")
        await file.seek(0)  # Reset to beginning
    except Exception as e:
        logger.error(f"Error reading file content: {e}")

    # Validate filename exists
    if not file.filename:
        logger.error("No filename provided in upload - file.filename is None or empty")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided in request"
        )

    # Validate file extension (case-insensitive)
    if not file.filename.lower().endswith('.pdf'):
        logger.warning(f"Invalid file type: {file.filename}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only PDF files are allowed. Received: {file.filename}"
        )

    # Validate file size (from config, default 50MB)
    max_size = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50")) * 1024 * 1024
    content = await file.read()
    file_size = len(content)

    if file_size > max_size:
        logger.warning(f"File too large: {file_size} bytes")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum of {max_size // (1024*1024)}MB"
        )

    # Reset file pointer for potential re-reading
    await file.seek(0)

    try:
        # Generate unique document ID
        document_id = f"doc_{uuid.uuid4().hex[:12]}"

        # Extract actual page count and text from PDF
        import io
        from pypdf import PdfReader

        # Read PDF content
        pdf_bytes = io.BytesIO(content)
        pdf_reader = PdfReader(pdf_bytes)
        num_pages = len(pdf_reader.pages)

        # Extract text from all pages for storage
        full_text = ""
        for page in pdf_reader.pages:
            full_text += page.extract_text() + "\n"

        logger.info(f"Extracted {num_pages} pages, {len(full_text)} characters from {file.filename}")

        # Store document metadata in memory with extracted text
        doc_metadata = {
            "document_id": document_id,
            "filename": file.filename,
            "upload_date": datetime.utcnow(),
            "num_pages": num_pages,
            "file_size": file_size,
            "status": ProcessingStatus.COMPLETED,
            "text_content": full_text  # Store extracted text
        }
        _documents_store[document_id] = doc_metadata

        # Update metrics
        increment_document_count()

        logger.info(
            f"PDF uploaded successfully: {document_id} "
            f"({file.filename}, {num_pages} pages)"
        )

        return UploadResponse(
            document_id=document_id,
            filename=file.filename,
            num_pages=num_pages,
            status=ProcessingStatus.COMPLETED,
            message="Document uploaded and processed successfully"
        )

    except Exception as e:
        logger.error(f"Error processing PDF upload: {str(e)}", exc_info=True)
        raise DocumentProcessingError(f"Failed to process PDF: {str(e)}")


@router.get(
    "",
    response_model=DocumentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List All Documents",
    description="Retrieve a list of all uploaded and processed documents.",
    responses={
        200: {"description": "Documents retrieved successfully"},
        401: {"description": "Unauthorized - Missing or invalid API key"}
    }
)
async def list_documents() -> DocumentListResponse:
    """
    Get a list of all documents in the system.

    Returns:
        DocumentListResponse: List of document metadata

    Note:
        Returns empty list if no documents have been uploaded.
    """
    logger.debug("Document list requested")

    # Convert in-memory store to list of DocumentMetadata
    documents = [
        DocumentMetadata(**doc) for doc in _documents_store.values()
    ]

    # TODO: Stage 3 - Query from actual metadata database
    # documents = retrieval_agent.list_documents()

    logger.info(f"Returning {len(documents)} documents")

    return DocumentListResponse(
        documents=documents,
        total=len(documents)
    )


@router.get(
    "/{doc_id}",
    response_model=DocumentDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Document Details",
    description="Retrieve detailed information about a specific document.",
    responses={
        200: {"description": "Document details retrieved successfully"},
        401: {"description": "Unauthorized - Missing or invalid API key"},
        404: {"description": "Document not found"}
    }
)
async def get_document(doc_id: str) -> DocumentDetailResponse:
    """
    Get detailed information about a specific document.

    Args:
        doc_id: Document ID

    Returns:
        DocumentDetailResponse: Detailed document information

    Raises:
        DocumentNotFoundError: If document doesn't exist
    """
    logger.debug(f"Document details requested: {doc_id}")

    # Check if document exists
    if doc_id not in _documents_store:
        logger.warning(f"Document not found: {doc_id}")
        raise DocumentNotFoundError(doc_id)

    doc = _documents_store[doc_id]

    # TODO: Stage 3 - Get actual chunk count from vector store
    # TODO: Stage 4 - Get actual summary count from cache/database
    num_chunks = 48  # Placeholder
    summary_count = 0  # Placeholder

    logger.info(f"Returning details for document: {doc_id}")

    return DocumentDetailResponse(
        document_id=doc["document_id"],
        filename=doc["filename"],
        upload_date=doc["upload_date"],
        num_pages=doc["num_pages"],
        file_size=doc["file_size"],
        status=doc["status"],
        num_chunks=num_chunks,
        summary_count=summary_count
    )


@router.delete(
    "/{doc_id}",
    response_model=DeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete Document",
    description="Delete a document and all associated data.",
    responses={
        200: {"description": "Document deleted successfully"},
        401: {"description": "Unauthorized - Missing or invalid API key"},
        404: {"description": "Document not found"}
    }
)
async def delete_document(doc_id: str) -> DeleteResponse:
    """
    Delete a document and all its associated data.

    This removes:
    - Document metadata
    - Text chunks from vector database
    - Generated summaries
    - Cached results

    Args:
        doc_id: Document ID to delete

    Returns:
        DeleteResponse: Deletion confirmation

    Raises:
        DocumentNotFoundError: If document doesn't exist
    """
    logger.info(f"Document deletion requested: {doc_id}")

    # Check if document exists
    if doc_id not in _documents_store:
        logger.warning(f"Document not found for deletion: {doc_id}")
        raise DocumentNotFoundError(doc_id)

    try:
        # TODO: Stage 3 - Delete from vector database
        # TODO: Stage 3 - Delete from metadata store
        # TODO: Stage 4 - Clear cached summaries
        # retrieval_agent.delete_document(doc_id)

        # Remove from in-memory store
        del _documents_store[doc_id]

        logger.info(f"Document deleted successfully: {doc_id}")

        return DeleteResponse(
            document_id=doc_id,
            message="Document deleted successfully",
            deleted=True
        )

    except Exception as e:
        logger.error(f"Error deleting document {doc_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )


# Helper function to get document (used by other routes)
def get_document_metadata(doc_id: str) -> dict:
    """
    Get document metadata by ID.

    Args:
        doc_id: Document ID

    Returns:
        Document metadata dictionary

    Raises:
        DocumentNotFoundError: If document doesn't exist
    """
    if doc_id not in _documents_store:
        raise DocumentNotFoundError(doc_id)
    return _documents_store[doc_id]
