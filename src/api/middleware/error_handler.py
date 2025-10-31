"""
Global Error Handling Middleware.

Provides centralized exception handling for all API endpoints.
Converts exceptions to appropriate HTTP responses with proper status codes.
"""

import logging
import traceback
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handle HTTP exceptions (4xx, 5xx status codes).

    Args:
        request: The incoming request
        exc: The HTTP exception

    Returns:
        JSON response with error details
    """
    logger.warning(
        f"HTTP {exc.status_code}: {request.method} {request.url.path} - {exc.detail}"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail if isinstance(exc.detail, str) else "HTTP Error",
            "detail": str(exc.detail) if not isinstance(exc.detail, str) else None,
            "status_code": exc.status_code,
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle Pydantic validation errors (422 Unprocessable Entity).

    Args:
        request: The incoming request
        exc: The validation error

    Returns:
        JSON response with validation error details
    """
    errors = exc.errors()
    fields = [err["loc"][-1] for err in errors if err.get("loc")]

    error_messages = []
    for err in errors:
        field = ".".join(str(x) for x in err["loc"])
        msg = err["msg"]
        error_messages.append(f"{field}: {msg}")

    detail = "; ".join(error_messages)

    logger.warning(
        f"Validation error: {request.method} {request.url.path} - {detail}"
    )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Validation error",
            "detail": detail,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "fields": fields,
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle all other uncaught exceptions (500 Internal Server Error).

    Args:
        request: The incoming request
        exc: The exception

    Returns:
        JSON response with error details
    """
    # Log full traceback for debugging
    logger.error(
        f"Unhandled exception: {request.method} {request.url.path}",
        exc_info=True
    )

    # Get exception details
    exc_type = type(exc).__name__
    exc_message = str(exc)

    # In development, include traceback in response
    # In production, hide internal details
    import os
    debug_mode = os.getenv("DEBUG", "false").lower() == "true"

    if debug_mode:
        tb = traceback.format_exc()
        detail = f"{exc_type}: {exc_message}\n\nTraceback:\n{tb}"
    else:
        detail = "An internal server error occurred. Please contact support."

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": detail,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        },
    )


# Custom exception classes for domain-specific errors

class DocumentNotFoundError(Exception):
    """Raised when a document is not found."""
    def __init__(self, document_id: str):
        self.document_id = document_id
        super().__init__(f"Document not found: {document_id}")


class DocumentProcessingError(Exception):
    """Raised when document processing fails."""
    def __init__(self, message: str, document_id: str = None):
        self.document_id = document_id
        super().__init__(message)


class SummaryGenerationError(Exception):
    """Raised when summary generation fails."""
    def __init__(self, message: str, document_id: str = None):
        self.document_id = document_id
        super().__init__(message)


async def document_not_found_handler(request: Request, exc: DocumentNotFoundError) -> JSONResponse:
    """
    Handle document not found errors (404).

    Args:
        request: The incoming request
        exc: The exception

    Returns:
        JSON response with error details
    """
    logger.warning(f"Document not found: {exc.document_id}")

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": "Document not found",
            "detail": f"No document exists with ID: {exc.document_id}",
            "status_code": status.HTTP_404_NOT_FOUND,
        },
    )


async def document_processing_error_handler(request: Request, exc: DocumentProcessingError) -> JSONResponse:
    """
    Handle document processing errors (500).

    Args:
        request: The incoming request
        exc: The exception

    Returns:
        JSON response with error details
    """
    logger.error(
        f"Document processing error for {exc.document_id}: {str(exc)}",
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Document processing failed",
            "detail": str(exc),
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        },
    )


async def summary_generation_error_handler(request: Request, exc: SummaryGenerationError) -> JSONResponse:
    """
    Handle summary generation errors (500).

    Args:
        request: The incoming request
        exc: The exception

    Returns:
        JSON response with error details
    """
    logger.error(
        f"Summary generation error for {exc.document_id}: {str(exc)}",
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Summary generation failed",
            "detail": str(exc),
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        },
    )


def register_exception_handlers(app):
    """
    Register all exception handlers with the FastAPI app.

    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(DocumentNotFoundError, document_not_found_handler)
    app.add_exception_handler(DocumentProcessingError, document_processing_error_handler)
    app.add_exception_handler(SummaryGenerationError, summary_generation_error_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    logger.info("Exception handlers registered")
