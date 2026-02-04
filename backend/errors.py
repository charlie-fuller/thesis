"""Standardized error handling for the API.

This module re-exports from api.utils.error_handler for backward compatibility.
The single source of truth for error handling is api/utils/error_handler.py.

All API errors should use the exception classes from api.utils.error_handler.
"""

# Re-export everything from the main error handler
from api.utils.error_handler import (
    AnthropicAPIError,
    # Authentication
    AuthenticationError,
    AuthorizationError,
    DatabaseConnectionError,
    # Database
    DatabaseError,
    DocumentNotFoundError,
    # Document processing
    DocumentProcessingError,
    # Embeddings
    EmbeddingError,
    EmbeddingGenerationError,
    # Error codes
    ErrorCode,
    ErrorContext,
    # External services
    ExternalServiceError,
    FileSizeLimitError,
    GoogleDriveError,
    InvalidInputError,
    # Not found
    NotFoundError,
    NotionError,
    QueryExecutionError,
    RateLimitError,
    TextExtractionError,
    # Base exceptions
    ThesisError,
    TokenExpiredError,
    UnsupportedFileTypeError,
    # Validation
    ValidationError,
    VectorSearchError,
    VoyageAPIError,
    # Response formatting
    create_error_response,
    format_error_response,
    format_success_response,
    generic_exception_handler,
    # Utilities
    get_status_code_for_exception,
    http_exception_handler,
    # Exception handlers
    thesis_error_handler,
    wrap_external_service_error,
)

# Legacy alias for backward compatibility
generic_error_handler = generic_exception_handler

# Legacy aliases for backward compatibility
# The old errors.py had APIError which extended HTTPException
# New code should use ThesisError instead
from fastapi import HTTPException


class APIError(HTTPException):
    """Legacy API error class for backward compatibility.

    New code should use ThesisError or its subclasses instead.
    This class is kept for existing code that may depend on it.
    """

    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: dict = None,
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


async def api_error_handler(request, exc: APIError):
    """Legacy handler for APIError - delegates to http_exception_handler."""
    from fastapi.responses import JSONResponse

    from api.utils.error_handler import get_cors_headers

    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail,
        headers=get_cors_headers(request),
    )


# Convenience aliases that match old errors.py class names
class ConflictError(ThesisError):
    """Resource conflict error (409)."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.CONFLICT.value,
            details=details,
        )


class ServerError(ThesisError):
    """Internal server error (500)."""

    def __init__(self, message: str = "An internal server error occurred"):
        super().__init__(
            message=message,
            error_code=ErrorCode.SERVER_ERROR.value,
        )


__all__ = [
    # Error codes
    "ErrorCode",
    # Base exceptions
    "ThesisError",
    "APIError",  # Legacy
    # Authentication
    "AuthenticationError",
    "AuthorizationError",
    "TokenExpiredError",
    # Not found
    "NotFoundError",
    # Conflict
    "ConflictError",
    # Document processing
    "DocumentProcessingError",
    "DocumentNotFoundError",
    "TextExtractionError",
    "UnsupportedFileTypeError",
    "FileSizeLimitError",
    # Embeddings
    "EmbeddingError",
    "EmbeddingGenerationError",
    "VectorSearchError",
    # External services
    "ExternalServiceError",
    "GoogleDriveError",
    "NotionError",
    "AnthropicAPIError",
    "VoyageAPIError",
    # Database
    "DatabaseError",
    "DatabaseConnectionError",
    "QueryExecutionError",
    # Validation
    "ValidationError",
    "InvalidInputError",
    "RateLimitError",
    # Server
    "ServerError",
    # Response formatting
    "create_error_response",
    "format_success_response",
    "format_error_response",
    # Utilities
    "get_status_code_for_exception",
    "ErrorContext",
    "wrap_external_service_error",
    # Exception handlers
    "thesis_error_handler",
    "http_exception_handler",
    "generic_exception_handler",
    "api_error_handler",  # Legacy
    "generic_error_handler",  # Legacy alias
]
