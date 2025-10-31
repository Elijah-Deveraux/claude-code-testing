"""
Summarization Endpoint.

Handles document summarization requests using the Summarizer Agent.
"""

import logging
import uuid
from datetime import datetime
from fastapi import APIRouter, status
from src.api.models import SummarizeRequest, SummaryResponse, SummaryType
from src.api.middleware.error_handler import DocumentNotFoundError, SummaryGenerationError
from src.api.routes.documents import get_document_metadata
from src.api.routes.health import (
    increment_summary_count,
    record_cache_hit,
    record_cache_miss,
    record_tokens_used,
    record_processing_time
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/summarize", tags=["Summarization"])


# In-memory summary cache (will be replaced with proper caching in Stage 4)
_summary_cache: dict = {}


@router.post(
    "",
    response_model=SummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Document Summary",
    description="Generate a summary of a document using the Summarizer Agent.",
    responses={
        200: {"description": "Summary generated successfully"},
        400: {"description": "Bad request - Invalid parameters"},
        401: {"description": "Unauthorized - Missing or invalid API key"},
        404: {"description": "Document not found"},
        500: {"description": "Internal server error - Summary generation failed"}
    }
)
async def generate_summary(request: SummarizeRequest) -> SummaryResponse:
    """
    Generate a summary for the specified document.

    Process:
    1. Validate document exists
    2. Check cache for existing summary
    3. Retrieve relevant context from vector store (Stage 3)
    4. Generate summary using LLM (Stage 4)
    5. Cache result
    6. Return summary with metadata

    Args:
        request: Summary request parameters

    Returns:
        SummaryResponse: Generated summary with metadata

    Raises:
        DocumentNotFoundError: If document doesn't exist
        SummaryGenerationError: If summary generation fails
    """
    logger.info(
        f"Summary requested: doc={request.document_id}, "
        f"type={request.summary_type.value}"
    )

    # Validate document exists
    try:
        doc_metadata = get_document_metadata(request.document_id)
    except DocumentNotFoundError:
        logger.warning(f"Summary requested for non-existent document: {request.document_id}")
        raise

    # Check cache
    cache_key = (request.document_id, request.summary_type.value, request.query)
    if cache_key in _summary_cache:
        logger.info(f"Cache hit for summary: {request.document_id}")
        record_cache_hit()
        cached_response = _summary_cache[cache_key]
        # Update cached flag
        cached_response.cached = True
        return cached_response

    logger.debug(f"Cache miss for summary: {request.document_id}")
    record_cache_miss()

    try:
        # Generate actual summary using Gemini AI
        import time
        import os
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain.schema import HumanMessage

        start_time = time.time()

        summary_id = f"sum_{uuid.uuid4().hex[:12]}"

        # Get document text content
        text_content = doc_metadata.get('text_content', '')

        if not text_content:
            raise SummaryGenerationError(
                "Document has no text content",
                document_id=request.document_id
            )

        # Initialize Gemini LLM
        google_api_key = os.getenv("GOOGLE_API_KEY")
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")

        llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=google_api_key,
            temperature=0.3
        )

        # Create prompt based on summary type
        if request.summary_type == SummaryType.BRIEF:
            prompt = f"""Please provide a brief summary (3-5 sentences) of the following document.
Focus on the main points and key findings.

Document: {doc_metadata['filename']}

Content:
{text_content[:8000]}

Brief Summary:"""
        else:  # DETAILED
            prompt = f"""Please provide a detailed summary (300-500 words) of the following document.
Include main themes, key findings, important details, and conclusions.

Document: {doc_metadata['filename']}

Content:
{text_content[:15000]}

Detailed Summary:"""

        # Call LLM to generate summary
        messages = [HumanMessage(content=prompt)]
        response = llm.invoke(messages)
        summary_text = response.content

        # Estimate tokens used (rough estimate: 1 token ≈ 4 characters)
        tokens_used = len(prompt + summary_text) // 4

        # Extract page references (simplified - just use page 1 for now)
        page_references = list(range(1, min(doc_metadata['num_pages'] + 1, 6)))

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Create response
        response = SummaryResponse(
            summary_id=summary_id,
            document_id=request.document_id,
            summary_text=summary_text,
            summary_type=request.summary_type,
            tokens_used=tokens_used,
            page_references=page_references,
            timestamp=datetime.utcnow(),
            cached=False
        )

        # Cache the result
        _summary_cache[cache_key] = response

        # Update metrics
        increment_summary_count()
        record_tokens_used(tokens_used)
        record_processing_time(processing_time_ms)

        logger.info(
            f"Summary generated: {summary_id} for {request.document_id} "
            f"({tokens_used} tokens, {processing_time_ms}ms)"
        )

        return response

    except Exception as e:
        logger.error(
            f"Error generating summary for {request.document_id}: {str(e)}",
            exc_info=True
        )
        raise SummaryGenerationError(
            f"Failed to generate summary: {str(e)}",
            document_id=request.document_id
        )


# Helper function to clear cache (useful for testing/maintenance)
def clear_summary_cache():
    """Clear all cached summaries."""
    global _summary_cache
    _summary_cache.clear()
    logger.info("Summary cache cleared")


def get_cached_summary_count() -> int:
    """Get number of cached summaries."""
    return len(_summary_cache)

