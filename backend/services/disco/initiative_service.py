"""PuRDy Initiative Service.

Handles CRUD operations for PuRDy initiatives.
"""

from typing import Dict, Optional
from uuid import uuid4

import pb_client as pb
import repositories.disco as disco_repo
from logger_config import get_logger

logger = get_logger(__name__)


def _auto_id_throughline(throughline: Optional[Dict]) -> Optional[Dict]:
    """Auto-generate sequential IDs for throughline items missing them."""
    if not throughline:
        return throughline

    for prefix, key in [("ps", "problem_statements"), ("h", "hypotheses"), ("g", "gaps")]:
        items = throughline.get(key)
        if items:
            for i, item in enumerate(items, 1):
                if not item.get("id"):
                    item["id"] = f"{prefix}-{i}"

    return throughline


async def create_initiative(
    name: str,
    user_id: str,
    description: Optional[str] = None,
    throughline: Optional[Dict] = None,
    target_department: Optional[str] = None,
    value_alignment: Optional[Dict] = None,
    sponsor_stakeholder_id: Optional[str] = None,
    stakeholder_ids: Optional[list] = None,
) -> Dict:
    """Create a new discovery (initiative).

    Args:
        name: Discovery name
        user_id: Creating user's ID
        description: Optional description
        throughline: Optional structured input framing (problem statements, hypotheses, gaps)
        target_department: Optional target department
        value_alignment: Optional value alignment (kpis, department_goals, etc.)
        sponsor_stakeholder_id: Optional executive sponsor UUID
        stakeholder_ids: Optional list of stakeholder UUIDs

    Returns:
        Created initiative record

    Raises:
        ValueError: If name is empty or whitespace only
    """
    # Validate name is not empty
    if not name or not name.strip():
        raise ValueError("Initiative name cannot be empty")

    logger.info(f"Creating initiative: {name} for user {user_id}")

    # Auto-generate IDs for throughline items
    throughline = _auto_id_throughline(throughline)

    try:
        insert_data = {
            "name": name,
            "description": description,
            "status": "draft",
            "created_by": user_id,
        }
        if throughline:
            insert_data["throughline"] = throughline
        if target_department:
            insert_data["target_department"] = target_department
        if value_alignment:
            insert_data["value_alignment"] = value_alignment
        if sponsor_stakeholder_id:
            insert_data["sponsor_stakeholder_id"] = sponsor_stakeholder_id
        if stakeholder_ids:
            insert_data["stakeholder_ids"] = stakeholder_ids

        # Create the initiative
        initiative = disco_repo.create_initiative(insert_data)
        initiative_id = initiative["id"]

        # Add creator as owner in members table
        disco_repo.add_member({
            "initiative_id": initiative_id,
            "user_id": user_id,
            "role": "owner",
        })

        logger.info(f"Created initiative: {initiative_id}")
        return initiative

    except Exception as e:
        logger.error(f"Error creating initiative: {e}")
        raise


def _is_valid_uuid(value: str) -> bool:
    """Check if a string is a valid UUID."""
    try:
        from uuid import UUID

        UUID(value)
        return True
    except (ValueError, AttributeError):
        return False


async def get_initiative(initiative_id: str, user_id: str) -> Optional[Dict]:
    """Get a single initiative by ID or name.

    Args:
        initiative_id: Initiative UUID or name (slug)
        user_id: Requesting user's ID (for access check)

    Returns:
        Initiative record with member info, or None if not found/not accessible
    """
    logger.info(f"Fetching initiative: {initiative_id}")

    try:
        # Determine if we're looking up by UUID or by name
        if _is_valid_uuid(initiative_id):
            initiative = disco_repo.get_initiative(initiative_id)
        else:
            # Fetch initiative by name
            initiative = pb.get_first(
                "disco_initiatives",
                filter=f"name='{pb.escape_filter(initiative_id)}'",
            )

        if not initiative:
            return None

        # Use the actual UUID for subsequent queries
        actual_initiative_id = initiative["id"]

        # Check user access (use actual UUID)
        has_access = await check_user_access(actual_initiative_id, user_id)
        if not has_access:
            logger.warning(f"User {user_id} denied access to initiative {actual_initiative_id}")
            return None

        # Get user's role in this initiative
        members = disco_repo.get_initiative_members(actual_initiative_id)
        user_member = next((m for m in members if m.get("user_id") == user_id), None)
        initiative["user_role"] = user_member.get("role") if user_member else "viewer"

        # Get document count
        doc_count = pb.count("disco_documents", filter=f"initiative_id='{pb.escape_filter(actual_initiative_id)}'")
        initiative["document_count"] = doc_count

        # Get latest output for each agent type
        all_outputs = disco_repo.list_outputs(actual_initiative_id, sort="-created")

        # Group by agent_type, keep only latest
        latest_outputs = {}
        for output in all_outputs:
            agent_type = output["agent_type"]
            if agent_type not in latest_outputs:
                latest_outputs[agent_type] = output

        initiative["latest_outputs"] = latest_outputs

        return initiative

    except Exception as e:
        logger.error(f"Error fetching initiative {initiative_id}: {e}")
        raise


async def list_initiatives(user_id: str, status_filter: Optional[str] = None, limit: int = 50, offset: int = 0) -> Dict:
    """List all initiatives accessible to a user.

    Args:
        user_id: User's ID
        status_filter: Optional status to filter by
        limit: Max results
        offset: Pagination offset

    Returns:
        Dict with initiatives list and total count
    """
    logger.info(f"Listing initiatives for user {user_id}")

    try:
        # Get initiative IDs where user is a member
        member_records = pb.get_all(
            "disco_initiative_members",
            filter=f"user_id='{pb.escape_filter(user_id)}'",
        )

        if not member_records:
            return {"initiatives": [], "total": 0}

        initiative_ids = [m["initiative_id"] for m in member_records]
        roles_map = {m["initiative_id"]: m["role"] for m in member_records}

        # Build filter for initiatives
        id_filter = " || ".join(f"id='{pb.escape_filter(iid)}'" for iid in initiative_ids)
        parts = [f"({id_filter})"]
        if status_filter:
            parts.append(f"status='{pb.escape_filter(status_filter)}'")
        filter_str = " && ".join(parts)

        # Fetch initiatives with pagination
        result = pb.list_records(
            "disco_initiatives",
            filter=filter_str,
            sort="-updated",
            page=(offset // limit) + 1 if limit else 1,
            per_page=limit,
        )

        initiatives = result.get("items", [])
        total = result.get("totalItems", len(initiatives))

        # Add user role to each initiative
        for initiative in initiatives:
            initiative["user_role"] = roles_map.get(initiative["id"], "viewer")

        # Get document counts for all initiatives
        doc_count_map = {}
        for iid in initiative_ids:
            doc_count_map[iid] = pb.count(
                "disco_documents",
                filter=f"initiative_id='{pb.escape_filter(iid)}'",
            )

        for initiative in initiatives:
            initiative["document_count"] = doc_count_map.get(initiative["id"], 0)

        return {"initiatives": initiatives, "total": total}

    except Exception as e:
        logger.error(f"Error listing initiatives: {e}")
        raise


async def update_initiative(initiative_id: str, user_id: str, updates: Dict) -> Dict:
    """Update an initiative.

    Args:
        initiative_id: Initiative UUID
        user_id: Updating user's ID
        updates: Fields to update (name, description, status)

    Returns:
        Updated initiative record
    """
    logger.info(f"Updating initiative {initiative_id}")

    # Check permission (must be owner or editor)
    has_permission = await check_edit_permission(initiative_id, user_id)
    if not has_permission:
        raise PermissionError(f"User {user_id} cannot edit initiative {initiative_id}")

    # Auto-generate IDs for throughline items if present
    if "throughline" in updates and updates["throughline"]:
        updates["throughline"] = _auto_id_throughline(updates["throughline"])

    # Filter allowed fields
    allowed_fields = {
        "name",
        "description",
        "status",
        "throughline",
        "target_department",
        "value_alignment",
        "sponsor_stakeholder_id",
        "stakeholder_ids",
        "resolution_annotations",
        "user_corrections",
        "goal_alignment_details",
    }
    filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}

    if not filtered_updates:
        raise ValueError("No valid fields to update")

    try:
        result = disco_repo.update_initiative(initiative_id, filtered_updates)

        logger.info(f"Updated initiative: {initiative_id}")
        return result

    except Exception as e:
        logger.error(f"Error updating initiative {initiative_id}: {e}")
        raise


async def delete_initiative(initiative_id: str, user_id: str) -> bool:
    """Delete an initiative and all associated data.

    Args:
        initiative_id: Initiative UUID
        user_id: Deleting user's ID (must be owner)

    Returns:
        True if deleted successfully
    """
    logger.info(f"Deleting initiative {initiative_id}")

    # Check permission (must be owner)
    members = disco_repo.get_initiative_members(initiative_id)
    user_member = next((m for m in members if m.get("user_id") == user_id), None)

    if not user_member or user_member.get("role") != "owner":
        raise PermissionError(f"Only the owner can delete initiative {initiative_id}")

    try:
        # Delete initiative (PocketBase cascade rules handle related tables)
        pb.delete_record("disco_initiatives", initiative_id)

        logger.info(f"Deleted initiative: {initiative_id}")
        return True

    except Exception as e:
        logger.error(f"Error deleting initiative {initiative_id}: {e}")
        raise


async def check_user_access(initiative_id: str, user_id: str) -> bool:
    """Check if user has any access to initiative."""
    try:
        record = pb.get_first(
            "disco_initiative_members",
            filter=f"initiative_id='{pb.escape_filter(initiative_id)}' && user_id='{pb.escape_filter(user_id)}'",
        )
        return record is not None
    except Exception:
        return False


async def check_edit_permission(initiative_id: str, user_id: str) -> bool:
    """Check if user can edit initiative (owner or editor)."""
    try:
        record = pb.get_first(
            "disco_initiative_members",
            filter=f"initiative_id='{pb.escape_filter(initiative_id)}' && user_id='{pb.escape_filter(user_id)}'",
        )
        if not record:
            return False
        return record.get("role") in ("owner", "editor")
    except Exception:
        return False
