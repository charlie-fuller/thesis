"""API key authentication middleware.

Replaces Supabase JWT auth with a simple API key check.
All requests must include Authorization: Bearer <api_key>
except for health/docs endpoints.
"""

import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from config import settings

logger = logging.getLogger(__name__)

# Paths that bypass authentication
PUBLIC_PATHS = {"/", "/health", "/docs", "/openapi.json", "/redoc"}


async def verify_api_key(request: Request, call_next):
    """Middleware that checks API key on all requests except public paths."""
    if request.url.path in PUBLIC_PATHS:
        return await call_next(request)

    # Allow OPTIONS for CORS preflight
    if request.method == "OPTIONS":
        return await call_next(request)

    auth = request.headers.get("Authorization", "")
    expected = f"Bearer {settings.api_key}"

    if not settings.api_key or auth != expected:
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid or missing API key"},
        )

    return await call_next(request)
