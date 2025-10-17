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
        # Skip auth for health check and docs
        if request.url.path in ["/health", "/docs", "/openapi.json", "/redoc"]:
            return await call_next(request)

        # Require X-API-Key header for all other endpoints
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
