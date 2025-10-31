"""
FastAPI Main Application.

Entry point for the PDF Summarizer API.
Configures middleware, routes, CORS, and application lifecycle events.
"""

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv

# Load environment variables from .env file first
load_dotenv()

# Import middleware
from src.api.middleware.auth import APIKeyAuthMiddleware, get_api_key
from src.api.middleware.rate_limit import RateLimitMiddleware, get_rate_limit_config
from src.api.middleware.error_handler import register_exception_handlers

# Import routes
from src.api.routes import health, documents, summarize

# Configure logging
from src.config.logging_config import configure_logging_from_env

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle context manager.

    Handles startup and shutdown events for the FastAPI application.

    Startup:
    - Initialize logging
    - Log application configuration
    - Prepare connections (Stage 3/4)

    Shutdown:
    - Clean up resources
    - Close connections
    """
    # Startup
    logger.info("=" * 60)
    logger.info("PDF Summarizer API starting up...")
    logger.info("=" * 60)

    # Log configuration
    env = os.getenv("ENVIRONMENT", "development")
    debug = os.getenv("DEBUG", "false").lower() == "true"
    api_host = os.getenv("API_HOST", "0.0.0.0")
    api_port = os.getenv("API_PORT", "8000")

    logger.info(f"Environment: {env}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"API Host: {api_host}:{api_port}")

    # TODO: Stage 3 - Initialize database connections
    # - Connect to Qdrant vector database
    # - Initialize metadata store

    # TODO: Stage 4 - Initialize LLM provider
    # - Initialize Google Gemini or Ollama connection
    # - Validate API keys

    logger.info("Startup complete - API ready to serve requests")

    yield

    # Shutdown
    logger.info("=" * 60)
    logger.info("PDF Summarizer API shutting down...")
    logger.info("=" * 60)

    # TODO: Stage 3 - Close database connections
    # TODO: Stage 4 - Clean up LLM resources

    logger.info("Shutdown complete")


# Initialize FastAPI application
app = FastAPI(
    title="PDF Summarizer API",
    description=(
        "A powerful API for PDF document processing and AI-powered summarization. "
        "Upload PDFs, extract text, generate embeddings, and create intelligent summaries "
        "using a 2-agent architecture (Retrieval + Summarization)."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# ============================================================================
# Configure CORS
# ============================================================================

# Get allowed origins from environment
cors_origins_str = os.getenv("CORS_ORIGINS", '["http://localhost:8501"]')
# Parse the string as a Python list (simple eval for config)
try:
    import json
    cors_origins = json.loads(cors_origins_str)
except json.JSONDecodeError:
    # Fallback to default if parsing fails
    cors_origins = ["http://localhost:8501", "http://localhost:3000"]
    logger.warning(f"Failed to parse CORS_ORIGINS, using defaults: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info(f"CORS configured with origins: {cors_origins}")


# ============================================================================
# Configure Middleware (order matters!)
# ============================================================================

# 1. Rate limiting (check before authentication)
max_requests, window_seconds = get_rate_limit_config()
app.add_middleware(RateLimitMiddleware, max_requests=max_requests, window_seconds=window_seconds)
logger.info(f"Rate limiting: {max_requests} requests per {window_seconds}s")

# 2. API key authentication
try:
    api_key = get_api_key()
    app.add_middleware(APIKeyAuthMiddleware, api_key=api_key)
    logger.info("API key authentication enabled")
except ValueError as e:
    logger.error(f"API key configuration error: {e}")
    logger.error("API will start but authentication will fail!")

# 3. Exception handlers (register last to catch all errors)
register_exception_handlers(app)


# ============================================================================
# Register Routes
# ============================================================================

# Health and metrics (no prefix, at root level)
app.include_router(health.router)

# Document operations
app.include_router(documents.router)

# Summarization
app.include_router(summarize.router)

logger.info("All routes registered")


# ============================================================================
# Root Endpoint
# ============================================================================

@app.get(
    "/",
    include_in_schema=False,
    summary="Root Redirect",
    description="Redirects to API documentation"
)
async def root():
    """
    Root endpoint redirects to API documentation.

    Returns:
        Redirect to /docs
    """
    return RedirectResponse(url="/docs")


# ============================================================================
# Application Startup
# ============================================================================

# Initialize logging when module is imported
configure_logging_from_env()
logger = logging.getLogger(__name__)

logger.info("FastAPI application module loaded")


# ============================================================================
# Entry Point for Development
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("DEBUG", "false").lower() == "true"

    logger.info(f"Starting development server on {host}:{port}")

    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
