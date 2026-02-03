"""PuRDy Initiative Service.

Handles CRUD operations for PuRDy initiatives.
"""

import asyncio
from typing import Dict, Optional
from uuid import uuid4

from database import get_supabase, with_db_retry
from logger_config import get_logger

logger = get_logger(__name__)
supabase = get_supabase()


@with_db_retry(max_retries=2)
async def create_initiative(name: str, user_id: str, description: Optional[str] = None) -> Dict:
    """Create a new PuRDy initiative.

    Args:
        name: Initiative name
        user_id: Creating user's ID
        description: Optional description

    Returns:
        Created initiative record

    Raises:
        ValueError: If name is empty or whitespace only
    """
    # Validate name is not empty
    if not name or not name.strip():
        raise ValueError("Initiative name cannot be empty")

    logger.info(f"Creating initiative: {name} for user {user_id}")

    initiative_id = str(uuid4())

    try:
        # Use get_supabase() dynamically to support connection retry
        db = get_supabase()

        # Create the initiative
        result = await asyncio.to_thread(
            lambda: db.table("disco_initiatives")
            .insert(
                {
                    "id": initiative_id,
                    "name": name,
                    "description": description,
                    "status": "draft",
                    "created_by": user_id,
                }
            )
            .execute()
        )

        if not result.data:
            raise ValueError("Failed to create initiative")

        initiative = result.data[0]

        # Add creator as owner in members table
        await asyncio.to_thread(
            lambda: db.table("disco_initiative_members")
            .insert({"initiative_id": initiative_id, "user_id": user_id, "role": "owner"})
            .execute()
        )

        logger.info(f"Created initiative: {initiative_id}")
        return initiative

    except Exception as e:
        logger.error(f"Error creating initiative: {e}")
        raise


@with_db_retry(max_retries=2)
async def get_initiative(initiative_id: str, user_id: str) -> Optional[Dict]:
    """Get a single initiative by ID.

    Args:
        initiative_id: Initiative UUID
        user_id: Requesting user's ID (for access check)

    Returns:
        Initiative record with member info, or None if not found/not accessible
    """
    logger.info(f"Fetching initiative: {initiative_id}")

    try:
        # Use get_supabase() dynamically to support connection retry
        db = get_supabase()

        # Fetch initiative with creator info
        result = await asyncio.to_thread(
            lambda: db.table("disco_initiatives")
            .select("*, users!disco_initiatives_created_by_fkey(id, name, email)")
            .eq("id", initiative_id)
            .single()
            .execute()
        )

        if not result.data:
            return None

        initiative = result.data

        # Check user access
        has_access = await check_user_access(initiative_id, user_id)
        if not has_access:
            logger.warning(f"User {user_id} denied access to initiative {initiative_id}")
            return None

        # Get user's role in this initiative
        member_result = await asyncio.to_thread(
            lambda: db.table("disco_initiative_members")
            .select("role")
            .eq("initiative_id", initiative_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )

        initiative["user_role"] = member_result.data.get("role") if member_result.data else "viewer"

        # Get document count
        doc_count = await asyncio.to_thread(
            lambda: db.table("disco_documents")
            .select("id", count="exact")
            .eq("initiative_id", initiative_id)
            .execute()
        )
        initiative["document_count"] = doc_count.count or 0

        # Get latest output for each agent type
        outputs_result = await asyncio.to_thread(
            lambda: db.table("disco_outputs")
            .select("agent_type, version, created_at, recommendation, confidence_level")
            .eq("initiative_id", initiative_id)
            .order("created_at", desc=True)
            .execute()
        )

        # Group by agent_type, keep only latest
        latest_outputs = {}
        for output in outputs_result.data or []:
            agent_type = output["agent_type"]
            if agent_type not in latest_outputs:
                latest_outputs[agent_type] = output

        initiative["latest_outputs"] = latest_outputs

        return initiative

    except Exception as e:
        logger.error(f"Error fetching initiative {initiative_id}: {e}")
        raise


@with_db_retry(max_retries=2)
async def list_initiatives(
    user_id: str, status_filter: Optional[str] = None, limit: int = 50, offset: int = 0
) -> Dict:
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
        # Use get_supabase() dynamically to support connection retry
        db = get_supabase()

        # Get initiative IDs where user is a member
        member_result = await asyncio.to_thread(
            lambda: db.table("disco_initiative_members")
            .select("initiative_id, role")
            .eq("user_id", user_id)
            .execute()
        )

        if not member_result.data:
            return {"initiatives": [], "total": 0}

        initiative_ids = [m["initiative_id"] for m in member_result.data]
        roles_map = {m["initiative_id"]: m["role"] for m in member_result.data}

        # Build query
        query = (
            db.table("disco_initiatives")
            .select("*, users!disco_initiatives_created_by_fkey(id, name, email)", count="exact")
            .in_("id", initiative_ids)
        )

        if status_filter:
            query = query.eq("status", status_filter)

        query = query.order("updated_at", desc=True).range(offset, offset + limit - 1)

        result = await asyncio.to_thread(lambda: query.execute())

        initiatives = result.data or []

        # Add user role to each initiative
        for initiative in initiatives:
            initiative["user_role"] = roles_map.get(initiative["id"], "viewer")

        # Get document counts for all initiatives
        doc_counts = await asyncio.to_thread(
            lambda: db.table("disco_documents")
            .select("initiative_id")
            .in_("initiative_id", initiative_ids)
            .execute()
        )

        # Count documents per initiative
        doc_count_map = {}
        for doc in doc_counts.data or []:
            init_id = doc["initiative_id"]
            doc_count_map[init_id] = doc_count_map.get(init_id, 0) + 1

        for initiative in initiatives:
            initiative["document_count"] = doc_count_map.get(initiative["id"], 0)

        return {"initiatives": initiatives, "total": result.count or len(initiatives)}

    except Exception as e:
        logger.error(f"Error listing initiatives: {e}")
        raise


@with_db_retry(max_retries=2)
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

    # Filter allowed fields
    allowed_fields = {"name", "description", "status"}
    filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}

    if not filtered_updates:
        raise ValueError("No valid fields to update")

    try:
        # Use get_supabase() dynamically to support connection retry
        db = get_supabase()
        result = await asyncio.to_thread(
            lambda: db.table("disco_initiatives")
            .update(filtered_updates)
            .eq("id", initiative_id)
            .execute()
        )

        if not result.data:
            raise ValueError(f"Initiative {initiative_id} not found")

        logger.info(f"Updated initiative: {initiative_id}")
        return result.data[0]

    except Exception as e:
        logger.error(f"Error updating initiative {initiative_id}: {e}")
        raise


@with_db_retry(max_retries=2)
async def delete_initiative(initiative_id: str, user_id: str) -> bool:
    """Delete an initiative and all associated data.

    Args:
        initiative_id: Initiative UUID
        user_id: Deleting user's ID (must be owner)

    Returns:
        True if deleted successfully
    """
    logger.info(f"Deleting initiative {initiative_id}")

    # Use get_supabase() dynamically to support connection retry
    db = get_supabase()

    # Check permission (must be owner)
    member_result = await asyncio.to_thread(
        lambda: db.table("disco_initiative_members")
        .select("role")
        .eq("initiative_id", initiative_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )

    if not member_result.data or member_result.data.get("role") != "owner":
        raise PermissionError(f"Only the owner can delete initiative {initiative_id}")

    try:
        # Delete initiative (cascades to all related tables)
        await asyncio.to_thread(
            lambda: db.table("disco_initiatives").delete().eq("id", initiative_id).execute()
        )

        logger.info(f"Deleted initiative: {initiative_id}")
        return True

    except Exception as e:
        logger.error(f"Error deleting initiative {initiative_id}: {e}")
        raise


async def check_user_access(initiative_id: str, user_id: str) -> bool:
    """Check if user has any access to initiative."""
    try:
        db = get_supabase()
        result = await asyncio.to_thread(
            lambda: db.table("disco_initiative_members")
            .select("id")
            .eq("initiative_id", initiative_id)
            .eq("user_id", user_id)
            .execute()
        )
        return bool(result.data)
    except Exception:
        return False


async def check_edit_permission(initiative_id: str, user_id: str) -> bool:
    """Check if user can edit initiative (owner or editor)."""
    try:
        db = get_supabase()
        result = await asyncio.to_thread(
            lambda: db.table("disco_initiative_members")
            .select("role")
            .eq("initiative_id", initiative_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        if not result.data:
            return False
        return result.data.get("role") in ("owner", "editor")
    except Exception:
        return False
