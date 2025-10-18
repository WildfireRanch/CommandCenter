"""
API Key Authentication Middleware

WHAT: Simple API key authentication for all endpoints
WHY: Protect API from unauthorized access
HOW: Check X-API-Key header against environment variable
"""

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
import os
import logging

logger = logging.getLogger(__name__)

API_KEY = os.getenv("API_KEY", "")  # Set in Railway environment


class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    Middleware to require API key authentication on all endpoints.

    Exceptions:
    - /health (health check)
    - /docs (API documentation)
    - /openapi.json (OpenAPI schema)

    Usage:
        app.add_middleware(APIKeyMiddleware)
    """

    async def dispatch(self, request: Request, call_next):
        # Skip auth for public endpoints
        public_paths = ["/health", "/docs", "/openapi.json", "/redoc"]

        # Also skip auth for frontend data endpoints (they don't send API keys)
        if (request.url.path in public_paths or
            request.url.path.startswith("/energy/") or
            request.url.path.startswith("/victron/") or
            request.url.path.startswith("/solark/") or
            request.url.path.startswith("/kb/") or
            request.url.path.startswith("/chat/") or
            request.url.path.startswith("/ask") or
            request.url.path.startswith("/db/")):
            return await call_next(request)

        # Require X-API-Key header for protected endpoints (V1.9 API)
        api_key = request.headers.get("X-API-Key")

        if not API_KEY:
            logger.warning("API_KEY environment variable not set - authentication disabled!")
            # In development, allow without key if not configured
            # In production, Railway should always set this
            return await call_next(request)

        if not api_key or api_key != API_KEY:
            logger.warning(f"Unauthorized access attempt to {request.url.path}")
            raise HTTPException(
                status_code=401,
                detail="Invalid or missing API key. Include X-API-Key header."
            )

        return await call_next(request)
