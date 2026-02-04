"""Centralized Error Handling Utilities.

Provides custom exception classes, standardized error responses, and
FastAPI exception handlers for consistent error handling across the application.

This is the SINGLE SOURCE OF TRUTH for error handling in Thesis.
All error responses follow this format:

    {
        "success": False,
        "error": {
            "code": "ERROR_CODE",       # Machine-readable code
            "message": "Human message",  # User-friendly message
            "type": "ExceptionClass",    # Exception class name
            "timestamp": "ISO8601",      # When error occurred
            "details": {...}             # Optional additional info
        }
    }
"""

import os
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

from logger_config import get_logger

logger = get_logger(__name__)


# ============================================================================
# Error Codes Enum (Machine-Readable)
# ============================================================================


class ErrorCode(str, Enum):
    """Standardized error codes for consistent API responses."""

    # Authentication & Authorization
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"

    # Resource errors
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"

    # Validation
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"

    # Rate limiting
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # Document processing
    DOCUMENT_PROCESSING_ERROR = "DOCUMENT_PROCESSING_ERROR"
    UNSUPPORTED_FILE_TYPE = "UNSUPPORTED_FILE_TYPE"
    FILE_SIZE_EXCEEDED = "FILE_SIZE_EXCEEDED"
    TEXT_EXTRACTION_FAILED = "TEXT_EXTRACTION_FAILED"

    # External services
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    ANTHROPIC_API_ERROR = "ANTHROPIC_API_ERROR"
    VOYAGE_API_ERROR = "VOYAGE_API_ERROR"
    GOOGLE_DRIVE_ERROR = "GOOGLE_DRIVE_ERROR"
    NOTION_ERROR = "NOTION_ERROR"

    # Database
    DATABASE_ERROR = "DATABASE_ERROR"
    DATABASE_CONNECTION_ERROR = "DATABASE_CONNECTION_ERROR"
    QUERY_EXECUTION_ERROR = "QUERY_EXECUTION_ERROR"

    # Embeddings
    EMBEDDING_ERROR = "EMBEDDING_ERROR"
    VECTOR_SEARCH_ERROR = "VECTOR_SEARCH_ERROR"

    # General
    SERVER_ERROR = "SERVER_ERROR"


def get_cors_headers(request: Request) -> dict:
    """Get CORS headers based on request origin."""
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


# ============================================================================
# Custom Exception Classes
# ============================================================================


class ThesisError(Exception):
    """Base exception for all Thesis errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)


# Authentication & Authorization Errors
class AuthenticationError(ThesisError):
    """Raised when authentication fails."""

    pass


class AuthorizationError(ThesisError):
    """Raised when user lacks permission for an action."""

    pass


class TokenExpiredError(AuthenticationError):
    """Raised when authentication token has expired."""

    pass


# Not Found Errors
class NotFoundError(ThesisError):
    """Raised when a resource cannot be found."""

    def __init__(
        self,
        resource: str,
        resource_id: Optional[str] = None,
        message: Optional[str] = None,
    ):
        """Initialize NotFoundError.

        Args:
            resource: Type of resource (e.g., "Document", "User").
            resource_id: Optional ID of the resource.
            message: Optional custom message.
        """
        if message:
            error_message = message
        else:
            error_message = f"{resource} not found"
            if resource_id:
                error_message += f": {resource_id}"

        super().__init__(
            message=error_message,
            error_code=ErrorCode.NOT_FOUND.value,
            details={"resource": resource, "id": resource_id} if resource_id else None,
        )


# Document Processing Errors
class DocumentProcessingError(ThesisError):
    """Base class for document processing errors."""

    pass


class DocumentNotFoundError(NotFoundError):
    """Raised when a document cannot be found."""

    def __init__(self, document_id: Optional[str] = None):
        super().__init__(resource="Document", resource_id=document_id)


class TextExtractionError(DocumentProcessingError):
    """Raised when text extraction from a file fails."""

    pass


class UnsupportedFileTypeError(DocumentProcessingError):
    """Raised when file type is not supported."""

    pass


class FileSizeLimitError(DocumentProcessingError):
    """Raised when file exceeds size limit."""

    pass


# Embedding & Vector Search Errors
class EmbeddingError(ThesisError):
    """Base class for embedding-related errors."""

    pass


class EmbeddingGenerationError(EmbeddingError):
    """Raised when embedding generation fails."""

    pass


class VectorSearchError(EmbeddingError):
    """Raised when vector search fails."""

    pass


# External Service Errors
class ExternalServiceError(ThesisError):
    """Base class for external service errors."""

    pass


class GoogleDriveError(ExternalServiceError):
    """Raised when Google Drive operations fail."""

    pass


class NotionError(ExternalServiceError):
    """Raised when Notion operations fail."""

    pass


class AnthropicAPIError(ExternalServiceError):
    """Raised when Anthropic API calls fail."""

    pass


class VoyageAPIError(ExternalServiceError):
    """Raised when Voyage AI API calls fail."""

    pass


# Database Errors
class DatabaseError(ThesisError):
    """Base class for database errors."""

    pass


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""

    pass


class QueryExecutionError(DatabaseError):
    """Raised when database query execution fails."""

    pass


# Validation Errors
class ValidationError(ThesisError):
    """Base class for validation errors."""

    pass


class InvalidInputError(ValidationError):
    """Raised when input validation fails."""

    pass


class RateLimitError(ThesisError):
    """Raised when rate limit is exceeded."""

    pass


# ============================================================================
# Error Response Formatting
# ============================================================================


def create_error_response(
    error: Exception,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    include_details: bool = True,
) -> Dict[str, Any]:
    """Create a standardized error response dictionary.

    Args:
        error: The exception that occurred.
        status_code: HTTP status code to return.
        include_details: Whether to include detailed error information.

    Returns:
        Dictionary with standardized error response format.
    """
    response = {
        "success": False,
        "error": {
            "code": ErrorCode.SERVER_ERROR.value,  # Default
            "type": error.__class__.__name__,
            "message": str(error),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }

    # Add error code if available (custom exceptions)
    if isinstance(error, ThesisError):
        response["error"]["code"] = error.error_code

        # Add details if available and requested
        if include_details and error.details:
            response["error"]["details"] = error.details

    return response


# ============================================================================
# Success Response Formatting
# ============================================================================


def format_success_response(data: Any, message: Optional[str] = None) -> Dict[str, Any]:
    """Format a successful API response.

    Args:
        data: Response data.
        message: Optional success message.

    Returns:
        Standardized success response.
    """
    response: Dict[str, Any] = {"success": True, "data": data}

    if message:
        response["message"] = message

    return response


def format_error_response(
    code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Format an error API response.

    Args:
        code: Machine-readable error code (use ErrorCode enum).
        message: Human-readable error message.
        details: Optional additional details.

    Returns:
        Standardized error response.
    """
    response: Dict[str, Any] = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }
    if details:
        response["error"]["details"] = details
    return response


def get_status_code_for_exception(error: Exception) -> int:
    """Determine appropriate HTTP status code for an exception.

    Args:
        error: The exception to evaluate

    Returns:
        Appropriate HTTP status code
    """
    # Authentication errors
    if isinstance(error, (AuthenticationError, TokenExpiredError)):
        return status.HTTP_401_UNAUTHORIZED

    # Authorization errors
    if isinstance(error, AuthorizationError):
        return status.HTTP_403_FORBIDDEN

    # Not found errors
    if isinstance(error, DocumentNotFoundError):
        return status.HTTP_404_NOT_FOUND

    # Validation errors
    if isinstance(error, (ValidationError, InvalidInputError, UnsupportedFileTypeError)):
        return status.HTTP_400_BAD_REQUEST

    # File size errors
    if isinstance(error, FileSizeLimitError):
        return status.HTTP_413_REQUEST_ENTITY_TOO_LARGE

    # Rate limit errors
    if isinstance(error, RateLimitError):
        return status.HTTP_429_TOO_MANY_REQUESTS

    # External service errors (may be temporary)
    if isinstance(error, ExternalServiceError):
        return status.HTTP_503_SERVICE_UNAVAILABLE

    # Database errors
    if isinstance(error, DatabaseError):
        return status.HTTP_503_SERVICE_UNAVAILABLE

    # Default to 500 for unexpected errors
    return status.HTTP_500_INTERNAL_SERVER_ERROR


# ============================================================================
# FastAPI Exception Handlers
# ============================================================================


async def thesis_error_handler(request: Request, exc: ThesisError) -> JSONResponse:
    """Handle Thesis custom exceptions.

    Logs the error with context and returns standardized JSON response.
    """
    status_code = get_status_code_for_exception(exc)

    # Log error with context
    logger.error(
        f"Thesis error: {exc.__class__.__name__}",
        extra={
            "error_type": exc.__class__.__name__,
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method,
            "status_code": status_code,
        },
    )

    # Create standardized response
    response_data = create_error_response(exc, status_code)

    return JSONResponse(
        status_code=status_code, content=response_data, headers=get_cors_headers(request)
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTPException with standardized format."""
    logger.warning(
        f"HTTP exception: {exc.status_code}",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": request.url.path,
            "method": request.method,
        },
    )

    # Map status codes to error codes
    status_to_code = {
        400: ErrorCode.VALIDATION_ERROR.value,
        401: ErrorCode.AUTHENTICATION_ERROR.value,
        403: ErrorCode.AUTHORIZATION_ERROR.value,
        404: ErrorCode.NOT_FOUND.value,
        409: ErrorCode.CONFLICT.value,
        429: ErrorCode.RATE_LIMIT_EXCEEDED.value,
    }
    error_code = status_to_code.get(exc.status_code, ErrorCode.SERVER_ERROR.value)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": error_code,
                "type": "HTTPException",
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
        headers=get_cors_headers(request),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with logging and generic error message.

    This is a catch-all handler for exceptions that don't have specific handlers.
    It logs the full exception but returns a generic message to avoid leaking
    implementation details.
    """
    # Log full exception with traceback
    logger.exception(
        "Unexpected error",
        extra={
            "error_type": exc.__class__.__name__,
            "path": request.url.path,
            "method": request.method,
        },
        exc_info=True,
    )

    # Return generic error message (don't leak implementation details)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": ErrorCode.SERVER_ERROR.value,
                "type": "InternalServerError",
                "message": "An unexpected error occurred. Please try again later.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
        headers=get_cors_headers(request),
    )


# ============================================================================
# Error Context Manager
# ============================================================================


class ErrorContext:
    """Context manager for adding error handling context.

    Usage:
        with ErrorContext("Processing document", document_id=doc_id):
            process_document(doc_id)
    """

    def __init__(self, operation: str, **kwargs):
        self.operation = operation
        self.context = kwargs

    def __enter__(self):
        logger.debug(f"Starting: {self.operation}", extra=self.context)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            logger.error(
                f"Error in {self.operation}: {exc_val}",
                extra={**self.context, "error_type": exc_type.__name__},
                exc_info=True,
            )
        else:
            logger.debug(f"Completed: {self.operation}", extra=self.context)

        # Don't suppress exceptions
        return False


# ============================================================================
# Helper Functions
# ============================================================================


def wrap_external_service_error(
    error: Exception, service_name: str, operation: str
) -> ExternalServiceError:
    """Wrap external service errors with context.

    Args:
        error: The original exception
        service_name: Name of the external service
        operation: Operation that was being performed

    Returns:
        ExternalServiceError with context
    """
    if "anthropic" in service_name.lower():
        return AnthropicAPIError(
            f"{service_name} {operation} failed: {str(error)}",
            details={"service": service_name, "operation": operation},
        )
    elif "voyage" in service_name.lower():
        return VoyageAPIError(
            f"{service_name} {operation} failed: {str(error)}",
            details={"service": service_name, "operation": operation},
        )
    elif "google" in service_name.lower() or "drive" in service_name.lower():
        return GoogleDriveError(
            f"{service_name} {operation} failed: {str(error)}",
            details={"service": service_name, "operation": operation},
        )
    elif "notion" in service_name.lower():
        return NotionError(
            f"{service_name} {operation} failed: {str(error)}",
            details={"service": service_name, "operation": operation},
        )
    else:
        return ExternalServiceError(
            f"{service_name} {operation} failed: {str(error)}",
            details={"service": service_name, "operation": operation},
        )


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # Error codes
    "ErrorCode",
    # Base exceptions
    "ThesisError",
    # Authentication
    "AuthenticationError",
    "AuthorizationError",
    "TokenExpiredError",
    # Not found
    "NotFoundError",
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
]
