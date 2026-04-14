"""DISCo Initiatives routes."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

import pb_client as pb
from logger_config import get_logger
from repositories import disco as disco_repo
from repositories import tasks as tasks_repo
from services.disco import (
    add_member,
    create_initiative,
    delete_initiative,
    get_initiative,
    list_initiatives,
    list_members,
    remove_member,
    update_initiative,
    update_member_role,
)
from services.disco.initiative_alignment_analyzer import (
    analyze_initiative_alignment,
    get_project_alignment_rollup,
)
from services.disco.project_service import get_initiative_projects

from ._shared import (
    CreateTasksFromResolution,
    InitiativeCreate,
    InitiativeUpdate,
    MemberInvite,
    MemberRoleUpdate,
    ResolutionAnnotations,
    require_initiative_access,
)

logger = get_logger(__name__)
router = APIRouter()


# ============================================================================
# INITIATIVES
# ============================================================================


@router.get("/initiatives")
async def api_list_initiatives(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """List all initiatives accessible to the user."""
    try:
        result = await list_initiatives(
            status_filter=status,
            limit=limit,
            offset=offset,
        )
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"Error listing initiatives: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/initiatives")
async def api_create_initiative(
    data: InitiativeCreate,
):
    """Create a new initiative."""
    try:
        initiative = await create_initiative(
            name=data.name,
            description=data.description,
            throughline=data.throughline.model_dump() if data.throughline else None,
            target_department=data.target_department,
            value_alignment=data.value_alignment.model_dump(exclude_none=True) if data.value_alignment else None,
            sponsor_stakeholder_id=data.sponsor_stakeholder_id,
            stakeholder_ids=data.stakeholder_ids,
        )
        return {"success": True, "initiative": initiative}
    except Exception as e:
        logger.error(f"Error creating initiative: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/initiatives/as-tags")
async def api_get_initiatives_as_tags():
    """Get all initiatives formatted as tag options.

    Used by TagSelector component when showInitiatives=true.
    Returns initiative names sorted alphabetically.
    """
    try:
        result = await list_initiatives(limit=500)
        initiatives = result.get("initiatives", [])

        tags = sorted(
            [
                {
                    "tag": init["name"],
                    "count": 0,
                    "type": "initiative",
                    "initiative_id": init["id"],
                    "status": init.get("status", "active"),
                }
                for init in initiatives
            ],
            key=lambda x: x["tag"].lower(),
        )

        return {"success": True, "tags": tags}

    except Exception as e:
        logger.error(f"Error getting initiatives as tags: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/initiatives/{initiative_id}")
async def api_get_initiative(
    initiative_id: str,
):
    """Get initiative details."""
    try:
        initiative = await get_initiative(initiative_id)
        if not initiative:
            raise HTTPException(status_code=404, detail="Initiative not found")
        return {"success": True, "initiative": initiative}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching initiative: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.patch("/initiatives/{initiative_id}")
async def api_update_initiative(
    initiative_id: str,
    data: InitiativeUpdate,
):
    """Update initiative details."""
    require_initiative_access(initiative_id)

    try:
        updates = data.model_dump(exclude_unset=True)
        # Convert Pydantic model fields to dicts if present
        from pydantic import BaseModel

        for field in ("throughline", "value_alignment", "resolution_annotations"):
            if field in updates and updates[field] is not None:
                if isinstance(updates[field], BaseModel):
                    updates[field] = updates[field].model_dump()
        initiative = await update_initiative(
            initiative_id=initiative_id,
            updates=updates,
        )
        return {"success": True, "initiative": initiative}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
    except Exception as e:
        logger.error(f"Error updating initiative: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.patch("/initiatives/{initiative_id}/resolution-annotations")
async def api_update_resolution_annotations(
    initiative_id: str,
    data: ResolutionAnnotations,
):
    """Update resolution annotations (user overrides for hypothesis/gap resolutions).

    Performs a merge-patch: incoming overrides are merged with existing annotations,
    so you only need to send the keys you want to add or change.
    """
    require_initiative_access(initiative_id)

    try:
        # Get current initiative to read existing annotations
        initiative = await get_initiative(initiative_id)
        if not initiative:
            raise HTTPException(status_code=404, detail="Initiative not found")

        existing = initiative.get("resolution_annotations") or {}
        incoming = data.model_dump(exclude_none=True)

        # Merge: deep-merge each override dict
        merged = {**existing}
        for key in ("hypothesis_overrides", "gap_overrides"):
            if key in incoming:
                merged[key] = {**(existing.get(key) or {}), **incoming[key]}

        updated = await update_initiative(
            initiative_id=initiative_id,
            updates={"resolution_annotations": merged},
        )
        return {"success": True, "initiative": updated}
    except HTTPException:
        raise
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from None
    except Exception as e:
        logger.error(f"Error updating resolution annotations: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.delete("/initiatives/{initiative_id}")
async def api_delete_initiative(
    initiative_id: str,
):
    """Delete an initiative (owner only)."""
    try:
        await delete_initiative(initiative_id)
        return {"success": True, "message": "Initiative deleted"}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from None
    except Exception as e:
        logger.error(f"Error deleting initiative: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# PROJECTS (linked to initiative)
# ============================================================================


@router.get("/initiatives/{initiative_id}/projects")
async def api_get_initiative_projects(
    initiative_id: str,
    status: Optional[str] = Query(None, description="Filter by project status"),
):
    """Get all projects linked to this initiative."""
    try:
        # Verify initiative exists
        require_initiative_access(initiative_id)

        # Get projects
        result = await get_initiative_projects(initiative_id, status=status)
        return {"success": True, **result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting initiative projects: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# TASK CREATION FROM RESOLUTION
# ============================================================================


PRIORITY_MAP = {
    "critical": 5,
    "high": 4,
    "medium": 3,
    "low": 2,
    "none": 1,
}


def _parse_due_date(deadline: str | None) -> str | None:
    """Try to parse a deadline string into an ISO date string."""
    if not deadline:
        return None
    # Try common date formats
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%B %d, %Y", "%b %d, %Y", "%d %B %Y", "%d %b %Y"):
        try:
            return datetime.strptime(deadline.strip(), fmt).date().isoformat()
        except ValueError:
            continue
    return None


def _priority_to_int(priority: str | None) -> int:
    """Convert a priority string to an integer (1-5 scale)."""
    if not priority:
        return 3  # default medium
    return PRIORITY_MAP.get(priority.lower().strip(), 3)


@router.post("/initiatives/{initiative_id}/create-tasks-from-resolution")
async def api_create_tasks_from_resolution(
    initiative_id: str,
    data: CreateTasksFromResolution,
):
    """Create tasks from throughline resolution state changes.

    Extracts state_changes and so_what.next_human_action from a convergence
    output's throughline_resolution and creates project_tasks for each.
    """
    resolved_id = require_initiative_access(initiative_id)

    try:
        # 1. Get the output by ID and verify it belongs to the initiative
        output = disco_repo.get_output(data.output_id)
        if not output or output.get("initiative_id") != resolved_id:
            raise HTTPException(status_code=404, detail="Output not found")

        resolution = output.get("throughline_resolution")
        if isinstance(resolution, str):
            import json
            resolution = json.loads(resolution)

        if not resolution:
            raise HTTPException(status_code=400, detail="Output has no throughline resolution")

        # 2. Extract state_changes
        state_changes = resolution.get("state_changes") or []
        so_what = resolution.get("so_what") or {}

        if not state_changes and not so_what.get("next_human_action"):
            raise HTTPException(status_code=400, detail="No state changes or next actions found in resolution")

        # 3. Build task list - state changes + next_human_action
        tasks_to_create = []

        for idx, sc in enumerate(state_changes):
            # If selected_indices is provided, only create tasks for those indices
            if data.selected_indices is not None and idx not in data.selected_indices:
                continue
            tasks_to_create.append(
                {
                    "title": sc.get("description", "Untitled task")[:500],
                    "assignee_name": sc.get("owner"),
                    "due_date": _parse_due_date(sc.get("deadline")),
                    "priority": _priority_to_int(sc.get("priority")),
                }
            )

        # Add next_human_action as a high-priority task if present
        next_action = so_what.get("next_human_action")
        if next_action:
            # Only add if not filtering by indices, or if we have no state changes
            # (always include next_action when there are no state_changes selected)
            next_action_idx = len(state_changes)
            if data.selected_indices is None or next_action_idx in data.selected_indices:
                tasks_to_create.append(
                    {
                        "title": next_action[:500],
                        "assignee_name": None,
                        "due_date": None,
                        "priority": 4,  # high priority for next human action
                    }
                )

        if not tasks_to_create:
            raise HTTPException(status_code=400, detail="No tasks selected for creation")

        # 4. Get next position in pending column
        pending_tasks = pb.get_all(
            "project_tasks",
            filter="status='pending'",
            sort="-position",
        )
        next_position = (pending_tasks[0]["position"] + 1) if pending_tasks else 0

        # 5. Create tasks
        created_tasks = []
        for task_data in tasks_to_create:
            task_record = {
                "title": task_data["title"],
                "status": "pending",
                "priority": task_data["priority"],
                "assignee_name": task_data["assignee_name"],
                "due_date": task_data["due_date"],
                "source_type": "disco",
                "source_initiative_id": resolved_id,
                "source_disco_output_id": data.output_id,
                "linked_project_id": data.project_id,
                "position": next_position,
                "category": "disco_resolution",
                "tags": ["disco"],
            }

            result = tasks_repo.create_task(task_record)
            created_tasks.append(result)
            next_position += 1

        logger.info(f"Created {len(created_tasks)} tasks from resolution for initiative {resolved_id}")

        return {
            "success": True,
            "tasks": created_tasks,
            "count": len(created_tasks),
            "message": f"Created {len(created_tasks)} tasks from resolution",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating tasks from resolution: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# ALIGNMENT
# ============================================================================


@router.post("/initiatives/{initiative_id}/analyze-alignment")
async def api_analyze_initiative_alignment(
    initiative_id: str,
):
    """Analyze initiative alignment with IS FY27 strategic goals.

    Requires editor or owner role. Uses rich context from agent outputs.
    """
    require_initiative_access(initiative_id)

    try:
        score, details = await analyze_initiative_alignment(
            initiative_id=initiative_id,
        )

        # Determine alignment level
        if score >= 80:
            level = "high"
        elif score >= 60:
            level = "moderate"
        elif score >= 40:
            level = "low"
        else:
            level = "minimal"

        return {
            "success": True,
            "goal_alignment_score": score,
            "goal_alignment_details": details,
            "alignment_level": level,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from None
    except Exception as e:
        logger.error(f"Failed to analyze initiative alignment: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze alignment") from e


@router.get("/initiatives/{initiative_id}/alignment-rollup")
async def api_get_alignment_rollup(
    initiative_id: str,
):
    """Get alignment score rollup for projects linked to this initiative."""
    require_initiative_access(initiative_id)

    try:
        rollup = await get_project_alignment_rollup(initiative_id)
        return {"success": True, **rollup}
    except Exception as e:
        logger.error(f"Failed to get alignment rollup: {e}")
        raise HTTPException(status_code=500, detail="Failed to get alignment rollup") from e


# ============================================================================
# MEMBERS
# ============================================================================


@router.get("/initiatives/{initiative_id}/members")
async def api_list_members(
    initiative_id: str,
):
    """List initiative members."""
    require_initiative_access(initiative_id)

    try:
        members = await list_members(initiative_id)
        return {"success": True, "members": members}
    except Exception as e:
        logger.error(f"Error listing members: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/initiatives/{initiative_id}/members")
async def api_add_member(
    initiative_id: str,
    data: MemberInvite,
):
    """Invite a member to an initiative."""
    require_initiative_access(initiative_id)

    try:
        member = await add_member(
            initiative_id=initiative_id,
            user_email=data.email,
            role=data.role,
        )
        return {"success": True, "member": member}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from None
    except Exception as e:
        logger.error(f"Error adding member: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.patch("/initiatives/{initiative_id}/members/{user_id}")
async def api_update_member_role(
    initiative_id: str,
    user_id: str,
    data: MemberRoleUpdate,
):
    """Update a member's role."""
    try:
        member = await update_member_role(
            initiative_id=initiative_id,
            user_id=user_id,
            new_role=data.role,
        )
        return {"success": True, "member": member}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from None
    except Exception as e:
        logger.error(f"Error updating member role: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.delete("/initiatives/{initiative_id}/members/{user_id}")
async def api_remove_member(
    initiative_id: str,
    user_id: str,
):
    """Remove a member from an initiative."""
    try:
        await remove_member(
            initiative_id=initiative_id,
            user_id=user_id,
        )
        return {"success": True, "message": "Member removed"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from None
    except Exception as e:
        logger.error(f"Error removing member: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e
