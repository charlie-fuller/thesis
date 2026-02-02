"""Standardized error handling for the API.

Provides consistent error response format and custom exception classes.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import HTTPException
from fastapi.requests import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class APIError(HTTPException):
    """Base class for API errors with standardized format.

    All API errors should inherit from this class to ensure
    consistent error response structure.
    """

    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.error_code = error_code
        self.message = message
        self.details = details or {}

        super().__init__(
            status_code=status_code,
            detail={
                "success": False,
                "error": {"code": error_code, "message": message, "details": self.details},
            },
        )


class ValidationError(APIError):
    """Validation error (400)."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=400, error_code="VALIDATION_ERROR", message=message, details=details
        )


class AuthenticationError(APIError):
    """Authentication error (401)."""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(status_code=401, error_code="AUTHENTICATION_ERROR", message=message)


class AuthorizationError(APIError):
    """Authorization error (403)."""

    def __init__(self, message: str = "Not authorized to perform this action"):
        super().__init__(status_code=403, error_code="AUTHORIZATION_ERROR", message=message)


class NotFoundError(APIError):
    """Resource not found error (404)."""

    def __init__(self, resource: str, resource_id: Optional[str] = None):
        message = f"{resource} not found"
        if resource_id:
            message += f": {resource_id}"

        super().__init__(
            status_code=404,
            error_code="NOT_FOUND",
            message=message,
            details={"resource": resource, "id": resource_id},
        )


class ConflictError(APIError):
    """Resource conflict error (409)."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=409, error_code="CONFLICT", message=message, details=details)


class RateLimitError(APIError):
    """Rate limit exceeded (429)."""

    def __init__(self, message: str = "Rate limit exceeded. Please try again later."):
        super().__init__(status_code=429, error_code="RATE_LIMIT_EXCEEDED", message=message)


class ServerError(APIError):
    """Internal server error (500)."""

    def __init__(self, message: str = "An internal server error occurred"):
        super().__init__(status_code=500, error_code="SERVER_ERROR", message=message)


def format_success_response(data: Any, message: Optional[str] = None) -> Dict[str, Any]:
    """Format a successful API response.

    Args:
        data: Response data
        message: Optional success message

    Returns:
        Standardized success response
    """
    response = {"success": True, "data": data}

    if message:
        response["message"] = message

    return response


def format_error_response(
    error_code: str, message: str, details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Format an error API response.

    Args:
        error_code: Machine-readable error code
        message: Human-readable error message
        details: Optional additional details

    Returns:
        Standardized error response
    """
    return {
        "success": False,
        "error": {"code": error_code, "message": message, "details": details or {}},
    }


def get_cors_headers(request: Request) -> dict:
    """Get CORS headers based on request origin."""
    import os

    origin = request.headers.get("origin", "")

    # Known allowed origins
    allowed_origins = [
        "https://thesis.vercel.app",
        "https://thesis-woad.vercel.app",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
    ]

    # Add FRONTEND_URL if configured
    frontend_url = os.environ.get("FRONTEND_URL", "")
    for url in frontend_url.split(","):
        url = url.strip()
        if url and url not in allowed_origins:
            if not url.startswith(("http://", "https://")):
                url = f"https://{url}"
            allowed_origins.append(url)

    if origin in allowed_origins:
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
        }
    return {}


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Global error handler for APIError exceptions.

    Args:
        request: The request that caused the error
        exc: The APIError exception

    Returns:
        JSON response with standardized error format
    """
    return JSONResponse(
        status_code=exc.status_code, content=exc.detail, headers=get_cors_headers(request)
    )


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global error handler for unexpected exceptions.

    Args:
        request: The request that caused the error
        exc: The exception

    Returns:
        JSON response with generic server error
    """
    # Log the full error for debugging
    logger.exception(f"Unexpected error: {str(exc)}")

    return JSONResponse(
        status_code=500,
        content=format_error_response(
            error_code="SERVER_ERROR",
            message="An unexpected error occurred. Please try again later.",
            details={"type": type(exc).__name__},
        ),
        headers=get_cors_headers(request),
    )
