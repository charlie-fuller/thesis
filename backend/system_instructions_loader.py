from cache import (
    cache_delete,
    cache_get,
    cache_set,
    cache_system_instructions,
    get_cached_system_instructions,
)
from logger_config import get_logger

logger = get_logger(__name__)

"""
System Instructions Loader

Loads per-user system instructions (system prompts) for the AI assistant.
Instructions are stored in Supabase Storage (persistent) with fallback to local files.

Storage Priority:
1. Supabase Storage: system-instructions bucket, path: users/{user_id}.txt (persistent)
2. Local files: system_instructions/users/{user_id}.txt (ephemeral on Railway)
3. Default: system_instructions/default.txt (fallback)

Supports template variables that are replaced at runtime with user/client data:
- {user_name} - User's full name
- {user_email} - User's email address
- {user_role} - User's role (admin, user)
- {client_name} - Organization name (uses default in single-tenant mode)
- {client_id} - Client UUID (uses default in single-tenant mode)
- {assistant_name} - Custom assistant name (from client or default "Thesis")
"""

from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional

import pb_client as pb
from config import get_assistant_name, get_client_name, get_default_client_id

# Path to system instructions directory
SYSTEM_INSTRUCTIONS_DIR = Path(__file__).parent / "system_instructions"
DEFAULT_PROMPT_FILE = SYSTEM_INSTRUCTIONS_DIR / "default.txt"
USERS_DIR = SYSTEM_INSTRUCTIONS_DIR / "users"


def replace_template_variables(template: str, variables: Dict[str, str]) -> str:
    """Replace template variables in the format {variable_name} with actual values.

    Args:
        template: The template string with {variable_name} placeholders
        variables: Dictionary mapping variable names to their values

    Returns:
        String with all variables replaced
    """
    result = template
    for key, value in variables.items():
        # Replace {key} with value
        result = result.replace(f"{{{key}}}", str(value))
    return result


@lru_cache(maxsize=32)
def load_user_system_instructions(
    user_id: str,
    user_name: str = "User",
    user_email: str = "",
    user_role: str = "user",
    client_id: str = None,
    client_name: str = None,
    assistant_name: str = None,
) -> str:
    """Load system instructions for a specific user.

    Priority:
    1. Supabase Storage: system-instructions bucket, users/{user_id}.txt (persistent)
    2. Local file: system_instructions/users/{user_id}.txt (ephemeral on Railway)
    3. Default file: system_instructions/default.txt (fallback)

    Replaces template variables with actual user/client data.

    Args:
        user_id: UUID of the user
        user_name: User's full name
        user_email: User's email address
        user_role: User's role (admin or user)
        client_id: Client's UUID
        client_name: Client organization name
        assistant_name: Custom assistant name

    Returns:
        str: The system instructions with variables replaced

    Raises:
        FileNotFoundError: If no instructions found anywhere
    """
    template = None

    # PRIORITY 1: Try PocketBase file storage (persistent)
    # TODO: PocketBase file API migration pending (Plan 3).
    # For now, skip remote storage and fall through to local files.

    # PRIORITY 2: Try local file (ephemeral on Railway, but works for dev/testing)
    if not template:
        user_file = USERS_DIR / f"{user_id}.txt"
        if user_file.exists():
            logger.info("   📋 Loading user-specific system instructions from local file")
            with open(user_file, "r", encoding="utf-8") as f:
                template = f.read()
            logger.info("   ✅ Loaded from local file (ephemeral on Railway)")

    # PRIORITY 3: Fall back to default
    if not template:
        if DEFAULT_PROMPT_FILE.exists():
            logger.info(f"   📋 Loading default system instructions (no user-specific found for {user_id})")
            with open(DEFAULT_PROMPT_FILE, "r", encoding="utf-8") as f:
                template = f.read()
        else:
            raise FileNotFoundError(
                f"No system instructions found anywhere:\n"
                f"  - Supabase Storage: system-instructions/users/{user_id}.txt (not found)\n"
                f"  - Local file: {USERS_DIR / f'{user_id}.txt'} (not found)\n"
                f"  - Default: {DEFAULT_PROMPT_FILE} (not found)"
            )

    # Use config defaults for missing values (single-tenant mode)
    if client_id is None:
        client_id = get_default_client_id()
    if client_name is None:
        client_name = get_client_name()
    if assistant_name is None:
        assistant_name = get_assistant_name()

    # Prepare variables for replacement
    variables = {
        "user_name": user_name,
        "user_email": user_email,
        "user_role": user_role,
        "client_id": client_id,
        "client_name": client_name,
        "assistant_name": assistant_name,
    }

    # Replace template variables
    instructions = replace_template_variables(template, variables)

    return instructions


def get_system_instructions_for_user(user_id: str, user_data: Optional[Dict] = None) -> str:
    """Convenience function to load system instructions from user data dict.

    Uses Redis cache for performance (1-hour TTL), with automatic fallback
    to loading from storage/files if cache miss or Redis unavailable.

    Args:
        user_id: UUID of the user
        user_data: Dict containing user info from Supabase (from get_current_user)

    Returns:
        str: The system instructions with variables replaced
    """
    if user_data is None:
        user_data = {}

    # Try to get from Redis cache first (1-hour TTL)
    cached = get_cached_system_instructions(user_id)
    if cached is not None:
        logger.debug(f"✅ System instructions loaded from cache for user {user_id}")
        return cached

    # Cache miss or Redis unavailable - load from storage/files
    logger.debug(f"📋 Cache miss - loading system instructions for user {user_id}")
    instructions = load_user_system_instructions(
        user_id=user_id,
        user_name=user_data.get("name", "User"),
        user_email=user_data.get("email", ""),
        user_role=user_data.get("role", "user"),
        client_id=user_data.get("client_id"),  # Will use default if None
        client_name=user_data.get("client_name"),  # Will use default if None
        assistant_name=user_data.get("assistant_name"),  # Will use default if None
    )

    # Cache for 1 hour (3600 seconds)
    cache_system_instructions(user_id, instructions, ttl=3600)

    return instructions


# ============================================================================
# Version-Based System Instructions Loading (NEW - for system instruction versioning)
# ============================================================================


def get_active_system_instruction_version() -> Optional[dict]:
    """Get the currently active system instruction version from the database.

    Returns the full version record including id, version_number, content,
    and metadata. Returns None if no active version exists.

    This is the source of truth for which system instructions to use for
    new conversations.
    """
    # Try cache first
    cached = cache_get("active_version", namespace="sys_inst_versions")
    if cached is not None:
        logger.debug("✅ Active system instruction version loaded from cache")
        return cached

    # Fetch from database
    try:
        record = pb.get_first(
            "system_instruction_versions",
            filter="is_active=true",
        )

        if record:
            # Cache for 5 minutes (invalidated on activation)
            cache_set("active_version", record, ttl=300, namespace="sys_inst_versions")
            logger.info(f"Active version {record['version_number']} loaded from database")
            return record
        else:
            logger.warning("No active system instruction version found")
            return None

    except Exception as e:
        logger.warning(f"Error fetching active system instruction version: {e}")
        return None


def get_system_instructions_for_version(version_id: str, user_data: Optional[Dict] = None) -> str:
    """Load system instructions for a specific version ID.

    This is used for conversations that are bound to a specific version,
    ensuring that the same instructions are used throughout the conversation
    even if a new version is activated.

    Args:
        version_id: UUID of the system instruction version
        user_data: Dict containing user info for template variable replacement

    Returns:
        str: The system instructions with variables replaced

    Raises:
        ValueError: If the version is not found
    """
    if user_data is None:
        user_data = {}

    # Try cache first
    cache_key = f"version:{version_id}"
    cached = cache_get(cache_key, namespace="sys_inst_versions")
    if cached is not None:
        logger.debug(f"✅ Version {version_id} content loaded from cache")
        content = cached
    else:
        # Fetch from database
        try:
            record = pb.get_record("system_instruction_versions", version_id)

            if not record:
                raise ValueError(f"System instruction version {version_id} not found")

            content = record["content"]

            # Cache for 1 hour (versions are immutable once created)
            cache_set(cache_key, content, ttl=3600, namespace="sys_inst_versions")
            logger.info(f"Version {version_id} loaded from database")

        except Exception as e:
            raise ValueError(f"Error loading system instruction version: {e}") from None

    # Apply template variable replacement
    client_id = user_data.get("client_id") or get_default_client_id()
    client_name = user_data.get("client_name") or get_client_name()
    assistant_name = user_data.get("assistant_name") or get_assistant_name()

    variables = {
        "user_name": user_data.get("name", "User"),
        "user_email": user_data.get("email", ""),
        "user_role": user_data.get("role", "user"),
        "client_id": client_id,
        "client_name": client_name,
        "assistant_name": assistant_name,
    }

    instructions = replace_template_variables(content, variables)
    return instructions


def invalidate_version_cache(version_id: str = None):
    """Invalidate system instruction version caches.

    If version_id is provided, only that version's cache is cleared.
    If version_id is None, the active version cache is cleared.

    This should be called when:
    - A new version is activated (clear active version cache)
    - A version's content is modified (shouldn't happen, but for safety)
    """
    if version_id:
        cache_delete(f"version:{version_id}", namespace="sys_inst_versions")
        logger.info(f"✅ Cache cleared for version {version_id}")
    else:
        cache_delete("active_version", namespace="sys_inst_versions")
        logger.info("✅ Active version cache cleared")


# Legacy function for backwards compatibility
def get_default_system_instructions() -> str:
    """Legacy function - loads default system instructions without user customization.

    DEPRECATED: Use get_system_instructions_for_user() instead.

    Returns:
        str: The default system instructions
    """
    logger.warning("Using deprecated get_default_system_instructions()")
    logger.warning("Upgrade to get_system_instructions_for_user() for per-user customization")

    if DEFAULT_PROMPT_FILE.exists():
        with open(DEFAULT_PROMPT_FILE, "r", encoding="utf-8") as f:
            return f.read()
    else:
        raise FileNotFoundError(f"Default system instructions not found at {DEFAULT_PROMPT_FILE}")


# For testing/debugging
if __name__ == "__main__":
    logger.info("System Instructions Loader - Test Mode\n")

    # Test loading default
    try:
        default_instructions = get_default_system_instructions()
        logger.info(f"Default instructions loaded: {len(default_instructions)} characters")
        logger.info(f"  First 100 characters: {default_instructions[:100]}...\n")
    except FileNotFoundError as e:
        logger.info(f"Could not load default instructions: {e}\n")

    # Test template variable replacement
    logger.info("Testing template variable replacement:")
    test_template = "Hello {user_name} from {client_name}! Your role is {user_role}."
    test_variables = {"user_name": "John Doe", "client_name": "Acme Corp", "user_role": "admin"}
    result = replace_template_variables(test_template, test_variables)
    logger.info(f"  Template: {test_template}")
    logger.info(f"  Result: {result}")
    logger.info("  Variables replaced successfully\n")

    # Test loading user-specific instructions
    logger.info("Testing user-specific loading:")
    test_user_id = "test-user-123"
    try:
        user_instructions = load_user_system_instructions(
            user_id=test_user_id, user_name="Test User", client_name="Test Corp"
        )
        logger.info(f"Loaded instructions for {test_user_id}: {len(user_instructions)} characters")
    except FileNotFoundError:
        logger.info("  No user-specific file found (expected), fell back to default")
