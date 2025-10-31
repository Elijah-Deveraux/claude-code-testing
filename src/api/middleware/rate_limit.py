"""
Rate Limiting Middleware.

Simple in-memory rate limiter to prevent API abuse.
Limits requests per client IP address per time window.
"""

import logging
import time
from typing import Dict, Tuple
from collections import defaultdict
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    In-memory rate limiting middleware.

    Tracks requests per client IP and enforces rate limits.
    Uses a sliding window algorithm with automatic cleanup.

    Attributes:
        max_requests: Maximum requests allowed per window
        window_seconds: Time window in seconds
        requests: Dict tracking request timestamps per client
    """

    def __init__(
        self,
        app,
        max_requests: int = 100,
        window_seconds: int = 60
    ):
        """
        Initialize rate limiter.

        Args:
            app: FastAPI application instance
            max_requests: Max requests per window (default: 100)
            window_seconds: Time window in seconds (default: 60)
        """
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds

        # Track requests per client: {client_ip: [timestamps]}
        self.requests: Dict[str, list] = defaultdict(list)

        logger.info(
            f"Rate limiter initialized: {max_requests} requests "
            f"per {window_seconds} seconds"
        )

    def _get_client_key(self, request: Request) -> str:
        """
        Get unique identifier for client.

        Args:
            request: Incoming HTTP request

        Returns:
            Client identifier (IP address)
        """
        # Use X-Forwarded-For header if behind proxy, else use client IP
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs, take the first
            return forwarded_for.split(",")[0].strip()

        return request.client.host if request.client else "unknown"

    def _cleanup_old_requests(self, client_key: str, current_time: float) -> None:
        """
        Remove request timestamps older than the time window.

        Args:
            client_key: Client identifier
            current_time: Current timestamp
        """
        cutoff_time = current_time - self.window_seconds
        self.requests[client_key] = [
            ts for ts in self.requests[client_key]
            if ts > cutoff_time
        ]

        # Remove client entirely if no recent requests
        if not self.requests[client_key]:
            del self.requests[client_key]

    def _is_rate_limited(self, client_key: str) -> Tuple[bool, int]:
        """
        Check if client has exceeded rate limit.

        Args:
            client_key: Client identifier

        Returns:
            Tuple of (is_limited: bool, current_count: int)
        """
        current_time = time.time()

        # Clean up old requests
        self._cleanup_old_requests(client_key, current_time)

        # Check current request count
        current_count = len(self.requests[client_key])
        is_limited = current_count >= self.max_requests

        return is_limited, current_count

    def _record_request(self, client_key: str) -> None:
        """
        Record a new request for the client.

        Args:
            client_key: Client identifier
        """
        self.requests[client_key].append(time.time())

    async def dispatch(self, request: Request, call_next):
        """
        Process request and enforce rate limit.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            Response from downstream handler

        Raises:
            HTTPException: If rate limit is exceeded
        """
        # Skip rate limiting for health check
        if request.url.path == "/health":
            return await call_next(request)

        # Get client identifier
        client_key = self._get_client_key(request)

        # Check if rate limited
        is_limited, current_count = self._is_rate_limited(client_key)

        if is_limited:
            logger.warning(
                f"Rate limit exceeded for {client_key}: "
                f"{current_count}/{self.max_requests} requests "
                f"in {self.window_seconds}s window"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Rate limit exceeded. "
                    f"Max {self.max_requests} requests per {self.window_seconds} seconds. "
                    f"Try again later."
                ),
                headers={
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + self.window_seconds)
                }
            )

        # Record this request
        self._record_request(client_key)
        remaining = self.max_requests - (current_count + 1)

        logger.debug(
            f"Rate limit check passed for {client_key}: "
            f"{current_count + 1}/{self.max_requests} requests"
        )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(
            int(time.time()) + self.window_seconds
        )

        return response


def get_rate_limit_config() -> Tuple[int, int]:
    """
    Get rate limit configuration from environment.

    Returns:
        Tuple of (max_requests, window_seconds)
    """
    import os

    max_requests = int(os.getenv("API_RATE_LIMIT", "100"))
    window_seconds = 60  # Fixed at 1 minute window

    return max_requests, window_seconds

