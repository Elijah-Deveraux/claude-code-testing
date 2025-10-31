"""
API Key Authentication Middleware.

Provides simple header-based API key authentication for all endpoints.
The API key is configured via the API_KEY environment variable.
"""

import logging
from typing import Optional
from fastapi import Request, HTTPException, status
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# API Key header configuration
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware for API key authentication.

    Validates that all incoming requests include a valid API key in the
    X-API-Key header. Requests without valid keys receive 401 Unauthorized.

    Excluded paths (no auth required):
    - /docs (OpenAPI documentation)
    - /redoc (ReDoc documentation)
    - /openapi.json (OpenAPI schema)
    - /health (health check endpoint)
    """

    # Paths that don't require authentication
    EXCLUDED_PATHS = {"/docs", "/redoc", "/openapi.json", "/health"}

    def __init__(self, app, api_key: str):
        """
        Initialize authentication middleware.

        Args:
            app: FastAPI application instance
            api_key: Expected API key value
        """
        super().__init__(app)
        self.api_key = api_key
        logger.info("API Key authentication middleware initialized")

    async def dispatch(self, request: Request, call_next):
        """
        Process request and validate API key.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            Response from downstream handler

        Raises:
            HTTPException: If API key is invalid or missing
        """
        # Skip authentication for excluded paths
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        # Extract API key from header
        provided_key = request.headers.get(API_KEY_NAME)

        # Validate API key
        if not provided_key:
            logger.warning(
                f"Missing API key for {request.method} {request.url.path} "
                f"from {request.client.host}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing API key. Include X-API-Key header.",
                headers={"WWW-Authenticate": "ApiKey"},
            )

        if provided_key != self.api_key:
            logger.warning(
                f"Invalid API key for {request.method} {request.url.path} "
                f"from {request.client.host}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "ApiKey"},
            )

        # API key valid - proceed with request
        logger.debug(
            f"Authenticated {request.method} {request.url.path} "
            f"from {request.client.host}"
        )
        response = await call_next(request)
        return response


def get_api_key() -> str:
    """
    Get API key from environment variable.

    Returns:
        API key string

    Raises:
        ValueError: If API_KEY environment variable is not set
    """
    api_key = os.getenv("API_KEY")
    if not api_key:
        raise ValueError(
            "API_KEY environment variable not set. "
            "Set it in .env file or environment."
        )
    return api_key


async def verify_api_key(api_key: str = api_key_header) -> str:
    """
    Dependency function to verify API key in route handlers.

    Can be used as a FastAPI dependency for individual routes:
    @app.get("/endpoint", dependencies=[Depends(verify_api_key)])

    Args:
        api_key: API key from header

    Returns:
        Validated API key

    Raises:
        HTTPException: If API key is invalid or missing
    """
    expected_key = get_api_key()

    if not api_key:
        logger.warning("Missing API key in request")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Include X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if api_key != expected_key:
        logger.warning("Invalid API key provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return api_key
