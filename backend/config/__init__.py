"""Backend Configuration for Thesis.

This module provides centralized configuration management, including
support for single-tenant mode with a default client.
"""

import logging
import os

from pydantic_settings import BaseSettings

# Use basic logger for config module (runs at import time)
logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Settings (PocketBase migration)
# ============================================================================


class Settings(BaseSettings):
    # PocketBase
    pocketbase_url: str = "http://127.0.0.1:8090"
    pocketbase_email: str = ""
    pocketbase_password: str = ""

    # Vector sidecar
    vec_url: str = "http://127.0.0.1:8080"

    # Auth
    api_key: str = ""

    # AI providers
    anthropic_api_key: str = ""
    voyage_api_key: str = ""
    mem0_api_key: str = ""

    # Server
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    default_model: str = "claude-sonnet-4-6"
    cors_origins: str = ""
    environment: str = "development"

    # Neo4j (kept for graph features)
    neo4j_uri: str = ""
    neo4j_user: str = ""
    neo4j_password: str = ""

    model_config = {"env_prefix": "THESIS_"}


settings = Settings()

# ============================================================================
# Default Client Configuration (Single-Tenant Mode)
# ============================================================================

# Well-known UUID for the default organization in single-tenant deployments
# This allows the application to work without explicit client management
DEFAULT_CLIENT_ID = os.getenv("DEFAULT_CLIENT_ID", "00000000-0000-0000-0000-000000000001")


def get_default_client_id() -> str:
    """Returns the default client ID for single-tenant deployments.

    In single-tenant mode, all users belong to this hidden "default organization".
    This simplifies the user experience by eliminating client management UI
    while preserving multi-tenant database structure for future flexibility.

    Returns:
        str: UUID of the default client

    Example:
        >>> client_id = get_default_client_id()
        >>> print(client_id)
        '00000000-0000-0000-0000-000000000001'
    """
    return DEFAULT_CLIENT_ID


def get_client_id_for_user(user_profile: dict) -> str:
    """Returns the appropriate client_id for a given user.

    In single-tenant mode, this always returns the default client ID.
    In multi-tenant mode (future), this would return user_profile.get('client_id').

    Args:
        user_profile: User profile dictionary from authentication

    Returns:
        str: Client ID to use for this user's operations

    Example:
        >>> user = {"id": "123", "email": "user@example.com"}
        >>> client_id = get_client_id_for_user(user)
        >>> print(client_id)
        '00000000-0000-0000-0000-000000000001'
    """
    # For now, always return default client
    # Future: Check if MULTI_TENANT_MODE is enabled
    return get_default_client_id()


def is_multi_tenant_mode() -> bool:
    """Checks if the application is running in multi-tenant mode.

    Returns:
        bool: True if multi-tenant features should be enabled

    Note:
        Currently always returns False. Set MULTI_TENANT_MODE=true
        in environment variables to enable multi-tenant features.
    """
    return os.getenv("MULTI_TENANT_MODE", "false").lower() == "true"


# ============================================================================
# Application Configuration
# ============================================================================

# API Configuration
API_VERSION = "v1"
API_TITLE = "Thesis API"
API_DESCRIPTION = "Backend API for Thesis"

# Rate Limiting
DEFAULT_RATE_LIMIT = os.getenv("DEFAULT_RATE_LIMIT", "100/minute")
CHAT_RATE_LIMIT = os.getenv("CHAT_RATE_LIMIT", "20/minute")
UPLOAD_RATE_LIMIT = os.getenv("UPLOAD_RATE_LIMIT", "10/minute")

# File Upload Limits
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))
ALLOWED_DOCUMENT_TYPES = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
    "text/csv",
    "text/plain",
]

# Database Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip() or None
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip() or None
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "").strip() or None

# AI Services
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip() or None
VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY", "").strip() or None
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "").strip() or None

# Feature Flags
ENABLE_VOICE_INTERVIEWS = os.getenv("ENABLE_VOICE_INTERVIEWS", "true").lower() == "true"
ENABLE_DOCUMENT_UPLOAD = os.getenv("ENABLE_DOCUMENT_UPLOAD", "true").lower() == "true"
ENABLE_SYSTEM_INSTRUCTIONS = os.getenv("ENABLE_SYSTEM_INSTRUCTIONS", "true").lower() == "true"

# Volume Storage Configuration (for Railway/Docker deployments)
VOLUME_PATH = os.getenv("VOLUME_PATH")  # e.g., "/data" on Railway


# ============================================================================
# Validation Functions
# ============================================================================


def validate_config():
    """Validates that all required configuration is present.

    Raises:
        ValueError: If required configuration is missing
    """
    required_vars = {
        "SUPABASE_URL": SUPABASE_URL,
        "SUPABASE_KEY": SUPABASE_KEY,
        "ANTHROPIC_API_KEY": ANTHROPIC_API_KEY,
    }

    missing = [key for key, value in required_vars.items() if not value]

    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            f"Please check your .env file or environment configuration."
        )


# ============================================================================
# Helper Functions
# ============================================================================


def get_client_name() -> str:
    """Returns the display name for the default client.

    Returns:
        str: Friendly name to use in UI/emails
    """
    return os.getenv("CLIENT_NAME", "Your Organization")


def get_assistant_name() -> str:
    """Returns the default assistant name.

    Returns:
        str: Name of the AI assistant
    """
    return os.getenv("ASSISTANT_NAME", "Thesis")


# Validate configuration on module import
try:
    validate_config()
except ValueError as e:
    # Log warning but don't crash - allow app to start for debugging
    logger.warning(f"Configuration Warning: {e}")
