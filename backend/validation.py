"""Input validation utilities for API endpoints"""

import secrets
import string
import uuid
from typing import Optional

from fastapi import HTTPException, UploadFile

from config import MAX_UPLOAD_SIZE_MB
from logger_config import get_logger

logger = get_logger(__name__)

# Try to import python-magic for file signature validation
# Falls back gracefully if not installed
try:
    import magic

    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    logger.warning("python-magic not installed. File signature validation disabled.")

# File upload constraints (imported from config for consistency)
MAX_FILE_SIZE = MAX_UPLOAD_SIZE_MB * 1024 * 1024  # Convert MB to bytes
ALLOWED_FILE_TYPES = {
    "application/pdf",  # .pdf
    "text/plain",  # .txt
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
    "application/json",  # .json
    "application/xml",  # .xml
    "text/xml",  # .xml (alternative MIME type)
    "text/csv",  # .csv
    "text/markdown",  # .md
    "text/x-markdown",  # .md (alternative MIME type)
    "application/octet-stream",  # Generic binary - allow for various file types
}

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".txt",
    ".docx",
    ".json",
    ".xml",
    ".csv",
    ".md",
}  # Currently supported formats

# Avatar/Image upload constraints
MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

# Magic number (file signature) to expected MIME type mappings
# These are validated against the actual file content bytes
MAGIC_MIME_MAPPINGS = {
    # Documents
    "application/pdf": {"application/pdf"},
    "text/plain": {"text/plain", "text/x-c", "text/x-c++"},  # text files can have various subtypes
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/zip",  # DOCX is a ZIP container
    },
    "application/json": {"application/json", "text/plain"},  # JSON often detected as text
    "application/xml": {"application/xml", "text/xml", "text/plain"},
    "text/xml": {"application/xml", "text/xml", "text/plain"},
    "text/csv": {"text/csv", "text/plain", "application/csv"},
    "text/markdown": {"text/plain", "text/markdown"},  # Markdown often detected as plain text
    "text/x-markdown": {"text/plain", "text/markdown"},
    # Images
    "image/jpeg": {"image/jpeg"},
    "image/jpg": {"image/jpeg"},
    "image/png": {"image/png"},
    "image/webp": {"image/webp"},
}


def validate_uuid(value: str, field_name: str = "id") -> str:
    """Validate that a string is a valid UUID.

    Args:
        value: String to validate
        field_name: Name of the field for error messages

    Returns:
        str: The validated UUID string

    Raises:
        HTTPException: If the value is not a valid UUID
    """
    if not value:
        raise HTTPException(status_code=400, detail=f"{field_name} is required")

    try:
        # Try to parse as UUID
        uuid.UUID(value)
        return value
    except ValueError:
        raise HTTPException(
            status_code=400, detail=f"Invalid {field_name} format. Must be a valid UUID."
        )


def validate_file_upload(file: UploadFile) -> None:
    """Validate uploaded file for size and type.

    Args:
        file: The uploaded file

    Raises:
        HTTPException: If file is invalid
    """
    # Check file exists
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")

    # Check filename
    if not file.filename:
        raise HTTPException(status_code=400, detail="File must have a filename")

    # Check file extension
    file_ext = None
    if "." in file.filename:
        file_ext = "." + file.filename.rsplit(".", 1)[1].lower()

    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Check content type if provided
    if file.content_type and file.content_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=400, detail=f"Content type '{file.content_type}' not allowed"
        )


def validate_file_size(file_content: bytes) -> None:
    """Validate that file size is within limits.

    Args:
        file_content: The file content bytes

    Raises:
        HTTPException: If file is too large
    """
    file_size = len(file_content)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413, detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024}MB"
        )

    if file_size == 0:
        raise HTTPException(status_code=400, detail="File is empty")


def validate_file_magic(file_content: bytes, claimed_content_type: Optional[str] = None) -> str:
    """Validate file content using magic numbers (file signatures).

    This prevents attackers from uploading malicious files with spoofed extensions.
    For example, uploading a .exe renamed to .pdf would be caught here.

    Args:
        file_content: The file content bytes
        claimed_content_type: The content type claimed by the upload (optional)

    Returns:
        str: The detected MIME type

    Raises:
        HTTPException: If file signature doesn't match allowed types or claimed type
    """
    if not MAGIC_AVAILABLE:
        # If python-magic is not installed, log warning and skip validation
        logger.debug("Magic validation skipped: python-magic not available")
        return claimed_content_type or "application/octet-stream"

    try:
        # Detect actual MIME type from file content
        detected_mime = magic.from_buffer(file_content, mime=True)
        logger.debug(f"Magic detected MIME type: {detected_mime}, claimed: {claimed_content_type}")

        # Check if detected type is in our allowed list
        all_allowed_mimes = set()
        for mime_set in MAGIC_MIME_MAPPINGS.values():
            all_allowed_mimes.update(mime_set)

        # Also add the main allowed types
        all_allowed_mimes.update(ALLOWED_FILE_TYPES)
        all_allowed_mimes.update(ALLOWED_IMAGE_TYPES)

        if detected_mime not in all_allowed_mimes:
            logger.warning(
                f"File magic validation failed: detected '{detected_mime}' not in allowed types"
            )
            raise HTTPException(
                status_code=400,
                detail=f"File content type '{detected_mime}' not allowed. File may be disguised.",
            )

        # If a content type was claimed, verify it matches (with some flexibility)
        if claimed_content_type and claimed_content_type in MAGIC_MIME_MAPPINGS:
            expected_mimes = MAGIC_MIME_MAPPINGS[claimed_content_type]
            if detected_mime not in expected_mimes:
                logger.warning(
                    f"File magic mismatch: claimed '{claimed_content_type}' "
                    f"but detected '{detected_mime}'"
                )
                raise HTTPException(
                    status_code=400,
                    detail="File content doesn't match declared type. File may be disguised.",
                )

        return detected_mime

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during magic validation: {e}")
        # On error, be permissive but log it
        return claimed_content_type or "application/octet-stream"


def validate_pagination(limit: int, offset: int) -> tuple[int, int]:
    """Validate and normalize pagination parameters.

    Args:
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        tuple: (validated_limit, validated_offset)

    Raises:
        HTTPException: If parameters are invalid
    """
    if limit < 1:
        raise HTTPException(status_code=400, detail="limit must be at least 1")

    if limit > 100:
        raise HTTPException(status_code=400, detail="limit cannot exceed 100")

    if offset < 0:
        raise HTTPException(status_code=400, detail="offset cannot be negative")

    return limit, offset


def sanitize_string(value: Optional[str], max_length: int = 500) -> Optional[str]:
    """Sanitize string input by trimming whitespace and limiting length.

    Args:
        value: String to sanitize
        max_length: Maximum allowed length

    Returns:
        str or None: Sanitized string or None if input was None

    Raises:
        HTTPException: If string exceeds max length
    """
    if value is None:
        return None

    # Trim whitespace
    sanitized = value.strip()

    # Check length
    if len(sanitized) > max_length:
        raise HTTPException(
            status_code=400, detail=f"Input too long. Maximum length: {max_length} characters"
        )

    return sanitized if sanitized else None


def generate_secure_password(length: int = 16) -> str:
    """Generate a cryptographically secure random password.

    Uses secrets module (not random) for cryptographic strength.
    Includes mix of uppercase, lowercase, digits, and special characters.

    Args:
        length: Length of password (default: 16, minimum: 12)

    Returns:
        str: Secure random password

    Raises:
        ValueError: If length is less than 12
    """
    if length < 12:
        raise ValueError("Password length must be at least 12 characters")

    # Character sets
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special = "!@#$%^&*()-_=+[]{}|;:,.<>?"

    # Ensure at least one character from each set
    password_chars = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        secrets.choice(special),
    ]

    # Fill the rest with random characters from all sets
    all_chars = lowercase + uppercase + digits + special
    password_chars += [secrets.choice(all_chars) for _ in range(length - 4)]

    # Shuffle to avoid predictable pattern
    secrets.SystemRandom().shuffle(password_chars)

    return "".join(password_chars)


def validate_image_upload(file: UploadFile) -> None:
    """Validate uploaded image file for size and type.

    Args:
        file: The uploaded image file

    Raises:
        HTTPException: If file is invalid
    """
    # Check file exists
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")

    # Check filename
    if not file.filename:
        raise HTTPException(status_code=400, detail="File must have a filename")

    # Check file extension
    file_ext = None
    if "." in file.filename:
        file_ext = "." + file.filename.rsplit(".", 1)[1].lower()

    if file_ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Image type not allowed. Allowed types: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}",
        )

    # Check content type if provided
    if file.content_type and file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Content type '{file.content_type}' not allowed. Must be an image.",
        )


def validate_image_size(file_content: bytes) -> None:
    """Validate that image size is within limits.

    Args:
        file_content: The image file content bytes

    Raises:
        HTTPException: If image is too large
    """
    file_size = len(file_content)

    if file_size > MAX_AVATAR_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Image too large. Maximum size: {MAX_AVATAR_SIZE / 1024 / 1024}MB",
        )

    if file_size == 0:
        raise HTTPException(status_code=400, detail="Image file is empty")


def validate_image_magic(file_content: bytes, claimed_content_type: Optional[str] = None) -> str:
    """Validate image file content using magic numbers.

    This prevents uploading non-image files with image extensions.

    Args:
        file_content: The image file content bytes
        claimed_content_type: The content type claimed by the upload (optional)

    Returns:
        str: The detected MIME type

    Raises:
        HTTPException: If file is not actually an image
    """
    if not MAGIC_AVAILABLE:
        logger.debug("Image magic validation skipped: python-magic not available")
        return claimed_content_type or "application/octet-stream"

    try:
        detected_mime = magic.from_buffer(file_content, mime=True)
        logger.debug(f"Image magic detected: {detected_mime}, claimed: {claimed_content_type}")

        # Must be an actual image type
        valid_image_mimes = {"image/jpeg", "image/png", "image/webp", "image/gif"}
        if detected_mime not in valid_image_mimes:
            logger.warning(f"Image magic validation failed: '{detected_mime}' is not an image")
            raise HTTPException(
                status_code=400, detail=f"File is not a valid image. Detected type: {detected_mime}"
            )

        return detected_mime

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during image magic validation: {e}")
        return claimed_content_type or "application/octet-stream"
