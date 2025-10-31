"""
Pydantic models for API request and response validation.

This module defines all data models used by the FastAPI backend for:
- Request validation
- Response serialization
- API documentation (OpenAPI/Swagger)

All models include:
- Type hints for all fields
- Field validation rules
- Docstrings for API documentation
- Example values for OpenAPI docs
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, field_validator


# ============================================================================
# Enums
# ============================================================================

class SummaryType(str, Enum):
    """Type of summary to generate."""
    BRIEF = "brief"
    DETAILED = "detailed"


class ProcessingStatus(str, Enum):
    """Status of document processing."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================================================
# Request Models
# ============================================================================

class SummarizeRequest(BaseModel):
    """Request model for generating a document summary."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "document_id": "doc_123abc",
            "summary_type": "brief",
            "query": "What are the main findings?"
        }
    })

    document_id: str = Field(
        ...,
        description="ID of the document to summarize",
        min_length=1,
        max_length=100
    )
    summary_type: SummaryType = Field(
        ...,
        description="Type of summary: 'brief' (3-5 sentences) or 'detailed' (300-500 words)"
    )
    query: Optional[str] = Field(
        None,
        description="Optional specific query/focus for the summary",
        max_length=500
    )


# ============================================================================
# Response Models
# ============================================================================

class DocumentMetadata(BaseModel):
    """Metadata for an uploaded document."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "document_id": "doc_123abc",
            "filename": "research_paper.pdf",
            "upload_date": "2025-10-29T10:30:00",
            "num_pages": 25,
            "file_size": 2048576,
            "status": "completed"
        }
    })

    document_id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    upload_date: datetime = Field(..., description="Timestamp of upload")
    num_pages: int = Field(..., description="Number of pages in document", ge=1)
    file_size: int = Field(..., description="File size in bytes", ge=1)
    status: ProcessingStatus = Field(..., description="Processing status")


class UploadResponse(BaseModel):
    """Response after successful PDF upload."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "document_id": "doc_123abc",
            "filename": "research_paper.pdf",
            "num_pages": 25,
            "status": "completed",
            "message": "Document uploaded and processed successfully"
        }
    })

    document_id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    num_pages: int = Field(..., description="Number of pages", ge=1)
    status: ProcessingStatus = Field(..., description="Processing status")
    message: str = Field(..., description="Status message")


class DocumentListResponse(BaseModel):
    """Response containing list of all documents."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "documents": [
                {
                    "document_id": "doc_123abc",
                    "filename": "research_paper.pdf",
                    "upload_date": "2025-10-29T10:30:00",
                    "num_pages": 25,
                    "file_size": 2048576,
                    "status": "completed"
                }
            ],
            "total": 1
        }
    })

    documents: List[DocumentMetadata] = Field(..., description="List of documents")
    total: int = Field(..., description="Total number of documents", ge=0)


class DocumentDetailResponse(BaseModel):
    """Detailed response for a specific document."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "document_id": "doc_123abc",
            "filename": "research_paper.pdf",
            "upload_date": "2025-10-29T10:30:00",
            "num_pages": 25,
            "file_size": 2048576,
            "status": "completed",
            "num_chunks": 48,
            "summary_count": 2
        }
    })

    document_id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    upload_date: datetime = Field(..., description="Upload timestamp")
    num_pages: int = Field(..., description="Number of pages", ge=1)
    file_size: int = Field(..., description="File size in bytes", ge=1)
    status: ProcessingStatus = Field(..., description="Processing status")
    num_chunks: int = Field(..., description="Number of text chunks", ge=0)
    summary_count: int = Field(..., description="Number of summaries generated", ge=0)


class SummaryResponse(BaseModel):
    """Response containing generated summary."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "summary_id": "sum_456def",
            "document_id": "doc_123abc",
            "summary_text": "This research paper explores...",
            "summary_type": "brief",
            "tokens_used": 850,
            "page_references": [1, 3, 5, 7],
            "timestamp": "2025-10-29T10:35:00",
            "cached": False
        }
    })

    summary_id: str = Field(..., description="Unique summary identifier")
    document_id: str = Field(..., description="Source document ID")
    summary_text: str = Field(..., description="Generated summary text")
    summary_type: SummaryType = Field(..., description="Type of summary")
    tokens_used: int = Field(..., description="Number of tokens used", ge=0)
    page_references: List[int] = Field(..., description="Referenced page numbers")
    timestamp: datetime = Field(..., description="Generation timestamp")
    cached: bool = Field(..., description="Whether result was cached")


class DeleteResponse(BaseModel):
    """Response after document deletion."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "document_id": "doc_123abc",
            "message": "Document deleted successfully",
            "deleted": True
        }
    })

    document_id: str = Field(..., description="ID of deleted document")
    message: str = Field(..., description="Status message")
    deleted: bool = Field(..., description="Whether deletion was successful")


class HealthResponse(BaseModel):
    """Health check response."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "status": "healthy",
            "timestamp": "2025-10-29T10:40:00",
            "dependencies": {
                "qdrant": "up",
                "metadata_store": "up",
                "llm_provider": "up"
            }
        }
    })

    status: str = Field(..., description="Overall health status")
    timestamp: datetime = Field(..., description="Check timestamp")
    dependencies: Dict[str, str] = Field(..., description="Dependency statuses")


class MetricsResponse(BaseModel):
    """System metrics response."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "total_documents": 42,
            "total_summaries": 87,
            "cache_hit_rate": 0.65,
            "avg_tokens_per_summary": 750,
            "avg_processing_time_ms": 1250,
            "total_api_calls": 1523,
            "timestamp": "2025-10-29T10:40:00"
        }
    })

    total_documents: int = Field(..., description="Total documents processed", ge=0)
    total_summaries: int = Field(..., description="Total summaries generated", ge=0)
    cache_hit_rate: float = Field(..., description="Cache hit rate (0-1)", ge=0.0, le=1.0)
    avg_tokens_per_summary: int = Field(..., description="Average tokens used", ge=0)
    avg_processing_time_ms: int = Field(..., description="Avg processing time in ms", ge=0)
    total_api_calls: int = Field(..., description="Total API calls received", ge=0)
    timestamp: datetime = Field(..., description="Metrics timestamp")


# ============================================================================
# Error Response Models
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "error": "Document not found",
            "detail": "No document exists with ID: doc_invalid",
            "status_code": 404
        }
    })

    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    status_code: int = Field(..., description="HTTP status code")


class ValidationErrorResponse(BaseModel):
    """Validation error response."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "error": "Validation error",
            "detail": "Invalid document_id format",
            "status_code": 400,
            "fields": ["document_id"]
        }
    })

    error: str = Field(..., description="Error message")
    detail: str = Field(..., description="Validation error details")
    status_code: int = Field(..., description="HTTP status code")
    fields: Optional[List[str]] = Field(None, description="Fields that failed validation")

