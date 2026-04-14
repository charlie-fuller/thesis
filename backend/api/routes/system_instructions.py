"""System Instructions Version Management Routes.

Handles upload, versioning, activation, and comparison of global system instructions.
Admin-only endpoints for managing system instruction versions.
"""

import difflib
import os
import re
from datetime import datetime, timezone
from typing import Optional

import anthropic
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, field_validator

import pb_client as pb
from cache import invalidate_all_system_instructions
from logger_config import get_logger
from validation import validate_uuid

logger = get_logger(__name__)
router = APIRouter(prefix="/api/admin/system-instructions", tags=["system-instructions"])

# ============================================================================
# Constants
# ============================================================================

MAX_INSTRUCTION_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_INSTRUCTION_EXTENSIONS = {".txt", ".xml"}
VERSION_NUMBER_PATTERN = re.compile(r"^[0-9]+\.[0-9]+(-.+)?$")


# ============================================================================
# Pydantic Models
# ============================================================================


class VersionNotesUpdate(BaseModel):
    """Model for updating version notes."""

    version_notes: str


class VersionCompareRequest(BaseModel):
    """Model for comparing two versions."""

    version_a_id: str
    version_b_id: str

    @field_validator("version_a_id", "version_b_id")
    @classmethod
    def validate_uuid_format(cls, v: str) -> str:
        validate_uuid(v, "version_id")
        return v


class VersionResponse(BaseModel):
    """Standard response model for version operations."""

    success: bool
    version: Optional[dict] = None
    message: Optional[str] = None


# ============================================================================
# Helper Functions
# ============================================================================


def validate_version_number(version_number: str) -> str:
    """Validate version number format (e.g., '1.3', '2.0-beta')."""
    if not version_number:
        raise HTTPException(status_code=400, detail="Version number is required")

    if not VERSION_NUMBER_PATTERN.match(version_number):
        raise HTTPException(
            status_code=400,
            detail="Invalid version number format. Must be like '1.0', '2.3', or '1.0-beta'",
        )

    return version_number


def validate_instruction_file(file: UploadFile) -> None:
    """Validate system instruction file."""
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")

    if not file.filename:
        raise HTTPException(status_code=400, detail="File must have a filename")

    # Check file extension
    file_ext = None
    if "." in file.filename:
        file_ext = "." + file.filename.rsplit(".", 1)[1].lower()

    if file_ext not in ALLOWED_INSTRUCTION_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_INSTRUCTION_EXTENSIONS)}",
        )


def get_version_by_id(version_id: str) -> dict:
    """Fetch a version by ID, raises 404 if not found."""
    result = pb.get_record("system_instruction_versions", version_id)
    if not result:
        raise HTTPException(status_code=404, detail="Version not found")
    return result


def count_conversations_using_version(version_id: str) -> int:
    """Count how many conversations are using a specific version."""
    return pb.count(
        "conversations",
        filter=f"system_instruction_version_id='{pb.escape_filter(version_id)}'",
    )


# ============================================================================
# Upload Endpoint
# ============================================================================


@router.post("/upload")
async def upload_system_instructions(
    file: UploadFile = File(...),
    version_number: str = Form(...),
    version_notes: str = Form(None),
):
    """Upload new system instructions file as a new version.

    The version will be created as inactive. Use the activate endpoint
    to make it the active version for new chats.
    """
    try:
        # Validate inputs
        validate_instruction_file(file)
        version_number = validate_version_number(version_number)

        # Check if version number already exists
        existing = pb.get_first(
            "system_instruction_versions",
            filter=f"version_number='{pb.escape_filter(version_number)}'",
        )

        if existing:
            raise HTTPException(status_code=409, detail=f"Version {version_number} already exists")

        # Read file content
        file_content = await file.read()

        # Validate file size
        if len(file_content) > MAX_INSTRUCTION_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size is {MAX_INSTRUCTION_FILE_SIZE // (1024 * 1024)}MB",
            )

        # Decode content (ensure UTF-8)
        try:
            content = file_content.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="File must be UTF-8 encoded") from None

        # Create version record
        version_data = {
            "version_number": version_number,
            "content": content,
            "file_size": len(file_content),
            "status": "active",
            "is_active": False,  # Not active until explicitly activated
            "version_notes": version_notes,
            "metadata": {
                "original_filename": file.filename,
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
            },
        }

        version = pb.create_record("system_instruction_versions", version_data)

        logger.info(f"System instruction version {version_number} created")

        return {
            "success": True,
            "version": version,
            "message": f"Version {version_number} created successfully. Activate it to use for new chats.",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}") from None


# ============================================================================
# List & Get Endpoints
# ============================================================================


@router.get("/versions")
async def list_versions(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
):
    """List all system instruction versions with metadata.

    Ordered by created descending (newest first).
    """
    try:
        parts = []
        if status:
            parts.append(f"status='{pb.escape_filter(status)}'")
        filter_str = " && ".join(parts)

        page = (offset // limit) + 1 if limit else 1
        result = pb.list_records(
            "system_instruction_versions",
            filter=filter_str,
            sort="-created",
            page=page,
            per_page=limit,
        )

        versions = result.get("items", [])
        total = result.get("totalItems", 0)

        # Enrich with creator names
        user_ids = set()
        for v in versions:
            if v.get("created_by"):
                user_ids.add(v["created_by"])
            if v.get("activated_by"):
                user_ids.add(v["activated_by"])

        user_names = {}
        for uid in user_ids:
            user = pb.get_record("users", uid)
            if user:
                user_names[uid] = user.get("name") or user.get("email", "Unknown")

        # Add user names to versions
        for v in versions:
            v["created_by_name"] = user_names.get(v.get("created_by"))
            v["activated_by_name"] = user_names.get(v.get("activated_by"))

        return {
            "success": True,
            "versions": versions,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        logger.error(f"Error listing versions: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/versions/active")
async def get_active_version():
    """Get the currently active system instruction version.

    Available to all users.
    """
    try:
        result = pb.get_first(
            "system_instruction_versions",
            filter="is_active=true",
        )

        if not result:
            raise HTTPException(status_code=404, detail="No active version found")

        return {"success": True, "version": result}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching active version: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/versions/{version_id}")
async def get_version(version_id: str):
    """Get full details of a specific version including content."""
    try:
        validate_uuid(version_id, "version_id")

        version = get_version_by_id(version_id)

        # Get conversation count
        conversation_count = count_conversations_using_version(version_id)
        version["conversation_count"] = conversation_count

        # Get creator name
        if version.get("created_by"):
            user = pb.get_record("users", version["created_by"])
            if user:
                version["created_by_name"] = user.get("name") or user.get("email")

        return {"success": True, "version": version}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching version: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# Activate Version Endpoint
# ============================================================================


@router.post("/versions/{version_id}/activate")
async def activate_version(version_id: str):
    """Activate a version, making it the default for new chats.

    This operation:
    1. Deactivates the current active version
    2. Activates the specified version
    3. Invalidates all system instruction caches
    """
    try:
        validate_uuid(version_id, "version_id")

        # Get the version to activate
        version = get_version_by_id(version_id)

        if version.get("is_active"):
            return {"success": True, "version": version, "message": "Version is already active"}

        # Deactivate current active version(s)
        active_versions = pb.get_all(
            "system_instruction_versions",
            filter="is_active=true",
        )
        for av in active_versions:
            pb.update_record("system_instruction_versions", av["id"], {"is_active": False})

        # Activate the specified version
        updated_version = pb.update_record(
            "system_instruction_versions",
            version_id,
            {
                "is_active": True,
                "activated_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        # Invalidate all system instruction caches
        try:
            invalidate_all_system_instructions()
            logger.info("System instruction caches invalidated")
        except Exception as cache_error:
            logger.warning(f"Failed to invalidate caches: {cache_error}")

        logger.info(f"Version {version['version_number']} activated")

        return {
            "success": True,
            "version": updated_version,
            "message": f"Version {version['version_number']} is now active for new chats",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Activation error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# Compare Versions Endpoint
# ============================================================================


@router.post("/versions/compare")
async def compare_versions(request: VersionCompareRequest):
    """Generate a diff between two versions.

    Returns unified diff format with statistics.
    """
    try:
        # Fetch both versions
        version_a = get_version_by_id(request.version_a_id)
        version_b = get_version_by_id(request.version_b_id)

        # Generate diff
        content_a = version_a["content"].splitlines(keepends=True)
        content_b = version_b["content"].splitlines(keepends=True)

        diff = list(
            difflib.unified_diff(
                content_a,
                content_b,
                fromfile=f"Version {version_a['version_number']}",
                tofile=f"Version {version_b['version_number']}",
                lineterm="",
            )
        )

        # Calculate statistics
        additions = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
        deletions = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))

        return {
            "success": True,
            "version_a": {
                "id": version_a["id"],
                "version_number": version_a["version_number"],
                "created_at": version_a.get("created", version_a.get("created_at", "")),
            },
            "version_b": {
                "id": version_b["id"],
                "version_number": version_b["version_number"],
                "created_at": version_b.get("created", version_b.get("created_at", "")),
            },
            "diff": diff,
            "stats": {
                "additions": additions,
                "deletions": deletions,
                "total_changes": additions + deletions,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Comparison error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/versions/compare/summary")
async def compare_versions_with_summary(request: VersionCompareRequest):
    """Generate an AI-powered narrative summary comparing two versions.

    Uses Claude to analyze the differences and provide human-readable insights.
    """
    try:
        # Fetch both versions
        version_a = get_version_by_id(request.version_a_id)
        version_b = get_version_by_id(request.version_b_id)

        # Generate diff for context
        content_a = version_a["content"].splitlines(keepends=True)
        content_b = version_b["content"].splitlines(keepends=True)

        diff = list(
            difflib.unified_diff(
                content_a,
                content_b,
                fromfile=f"Version {version_a['version_number']}",
                tofile=f"Version {version_b['version_number']}",
                lineterm="",
            )
        )

        # Calculate statistics
        additions = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
        deletions = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))

        # Prepare the diff text (limit to avoid token limits)
        diff_text = "\n".join(diff[:500])  # Limit diff lines to avoid token overflow
        if len(diff) > 500:
            diff_text += f"\n\n... and {len(diff) - 500} more changes ..."

        created_a = version_a.get("created", version_a.get("created_at", ""))
        created_b = version_b.get("created", version_b.get("created_at", ""))

        # Create the prompt for Claude
        prompt = f"""You are analyzing changes between two versions of system instructions for an AI assistant called "Thesis" (an L&D design assistant).

## Version Information
- **From:** Version {version_a["version_number"]} (created {created_a[:10] if created_a else "unknown"})
- **To:** Version {version_b["version_number"]} (created {created_b[:10] if created_b else "unknown"})

## Version Notes
- **Version A Notes:** {version_a.get("version_notes") or "None provided"}
- **Version B Notes:** {version_b.get("version_notes") or "None provided"}

## Statistics
- Lines added: {additions}
- Lines removed: {deletions}

## Diff (unified format)
```diff
{diff_text}
```

## Your Task
Provide a clear, concise summary of the changes between these two versions. Structure your response as follows:

1. **Overview** (1-2 sentences): High-level summary of what changed
2. **Key Changes** (bullet points): List the most significant changes
3. **Impact Assessment**: How these changes might affect Thesis's behavior
4. **Recommendations** (if applicable): Any suggestions for testing or validation

Keep your response professional and focused on actionable insights for the admin reviewing these changes."""

        # Call Claude API
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=500,
                detail="ANTHROPIC_API_KEY not configured. Cannot generate AI summary.",
            )

        client = anthropic.Anthropic(api_key=api_key)

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )

        # Extract the summary text
        summary = message.content[0].text if message.content else "Unable to generate summary."

        logger.info(
            f"AI summary generated for versions {version_a['version_number']} -> {version_b['version_number']}"
        )

        return {
            "success": True,
            "version_a": {
                "id": version_a["id"],
                "version_number": version_a["version_number"],
                "created_at": created_a,
            },
            "version_b": {
                "id": version_b["id"],
                "version_number": version_b["version_number"],
                "created_at": created_b,
            },
            "summary": summary,
            "stats": {
                "additions": additions,
                "deletions": deletions,
                "total_changes": additions + deletions,
            },
        }

    except HTTPException:
        raise
    except anthropic.APIError as e:
        logger.error(f"Anthropic API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI summary generation failed: {str(e)}") from None
    except Exception as e:
        logger.error(f"Summary generation error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/versions/{version_id}/changelog")
async def get_version_changelog(version_id: str):
    """Fetch the changelog file for a specific version if it exists.

    Looks for files like v1.1-update-log.md or v1.3-changelog.md.
    """
    from pathlib import Path

    try:
        validate_uuid(version_id, "version_id")

        # Get the version to find its version number
        version = get_version_by_id(version_id)
        version_number = version["version_number"]

        # Look for changelog files in docs/system-instructions/
        docs_path = Path(__file__).parent.parent.parent.parent / "docs" / "system-instructions"

        changelog_patterns = [
            f"v{version_number}-changelog.md",
            f"v{version_number}-update-log.md",
            f"v{version_number.replace('.', '-')}-changelog.md",
        ]

        changelog_content = None
        found_file = None

        for pattern in changelog_patterns:
            file_path = docs_path / pattern
            if file_path.exists():
                changelog_content = file_path.read_text(encoding="utf-8")
                found_file = pattern
                break

        if not changelog_content:
            return {
                "success": True,
                "version_number": version_number,
                "changelog": None,
                "message": f"No changelog file found for version {version_number}",
            }

        return {
            "success": True,
            "version_number": version_number,
            "changelog": changelog_content,
            "filename": found_file,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Changelog fetch error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# Update & Delete Endpoints
# ============================================================================


@router.patch("/versions/{version_id}")
async def update_version_notes(
    version_id: str, update: VersionNotesUpdate,
):
    """Update version notes/changelog for a version."""
    try:
        validate_uuid(version_id, "version_id")

        # Verify version exists
        get_version_by_id(version_id)

        result = pb.update_record(
            "system_instruction_versions",
            version_id,
            {"version_notes": update.version_notes},
        )

        logger.info(f"Version {version_id} notes updated")

        return {
            "success": True,
            "version": result,
            "message": "Version notes updated successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.delete("/versions/{version_id}")
async def delete_version(version_id: str):
    """Delete a version.

    Cannot delete:
    - The active version
    - A version that is bound to existing conversations
    """
    try:
        validate_uuid(version_id, "version_id")

        # Get the version
        version = get_version_by_id(version_id)

        # Check if active
        if version.get("is_active"):
            raise HTTPException(
                status_code=403,
                detail="Cannot delete the active version. Activate another version first.",
            )

        # Check if bound to conversations
        conversation_count = count_conversations_using_version(version_id)
        if conversation_count > 0:
            raise HTTPException(
                status_code=403,
                detail=f"Cannot delete this version. It is used by {conversation_count} conversation(s). Archive it instead.",
            )

        # Delete the version
        pb.delete_record("system_instruction_versions", version_id)

        logger.info(f"Version {version['version_number']} deleted")

        return {
            "success": True,
            "message": f"Version {version['version_number']} deleted successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/versions/{version_id}/archive")
async def archive_version(version_id: str):
    """Archive a version (soft delete).

    Archived versions remain in the database but are not shown in the default list.
    """
    try:
        validate_uuid(version_id, "version_id")

        # Get the version
        version = get_version_by_id(version_id)

        # Check if active
        if version.get("is_active"):
            raise HTTPException(
                status_code=403,
                detail="Cannot archive the active version. Activate another version first.",
            )

        # Archive the version
        result = pb.update_record(
            "system_instruction_versions",
            version_id,
            {"status": "archived"},
        )

        logger.info(f"Version {version['version_number']} archived")

        return {
            "success": True,
            "version": result,
            "message": f"Version {version['version_number']} archived successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Archive error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e
