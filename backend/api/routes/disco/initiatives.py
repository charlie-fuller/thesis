"""DISCo Initiatives routes."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from logger_config import get_logger
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
from services.disco.project_service import get_initiative_projects

from ._shared import (
    InitiativeCreate,
    InitiativeUpdate,
    MemberInvite,
    MemberRoleUpdate,
    require_disco_access,
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
    current_user: dict = Depends(require_disco_access),
):
    """List all initiatives accessible to the user."""
    try:
        result = await list_initiatives(
            user_id=current_user["id"],
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
    current_user: dict = Depends(require_disco_access),
):
    """Create a new initiative."""
    try:
        initiative = await create_initiative(
            name=data.name,
            description=data.description,
            user_id=current_user["id"],
        )
        return {"success": True, "initiative": initiative}
    except Exception as e:
        logger.error(f"Error creating initiative: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/initiatives/as-tags")
async def api_get_initiatives_as_tags(
    current_user: dict = Depends(require_disco_access),
):
    """Get all initiatives formatted as tag options.

    Used by TagSelector component when showInitiatives=true.
    Returns initiative names sorted alphabetically.
    """
    try:
        user_id = current_user["id"]
        result = await list_initiatives(user_id=user_id, limit=500)
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
    current_user: dict = Depends(require_disco_access),
):
    """Get initiative details."""
    try:
        initiative = await get_initiative(initiative_id, current_user["id"])
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
    current_user: dict = Depends(require_disco_access),
):
    """Update initiative details."""
    await require_initiative_access(initiative_id, current_user, "editor")

    try:
        updates = data.model_dump(exclude_unset=True)
        initiative = await update_initiative(
            initiative_id=initiative_id,
            user_id=current_user["id"],
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


@router.delete("/initiatives/{initiative_id}")
async def api_delete_initiative(
    initiative_id: str,
    current_user: dict = Depends(require_disco_access),
):
    """Delete an initiative (owner only)."""
    try:
        await delete_initiative(initiative_id, current_user["id"])
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
    current_user: dict = Depends(require_disco_access),
):
    """Get all projects linked to this initiative."""
    try:
        # Verify access to initiative
        await require_initiative_access(initiative_id, current_user, "viewer")

        # Get projects
        result = await get_initiative_projects(initiative_id, status=status)
        return {"success": True, **result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting initiative projects: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# MEMBERS
# ============================================================================


@router.get("/initiatives/{initiative_id}/members")
async def api_list_members(
    initiative_id: str,
    current_user: dict = Depends(require_disco_access),
):
    """List initiative members."""
    await require_initiative_access(initiative_id, current_user, "viewer")

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
    current_user: dict = Depends(require_disco_access),
):
    """Invite a member to an initiative."""
    await require_initiative_access(initiative_id, current_user, "editor")

    try:
        member = await add_member(
            initiative_id=initiative_id,
            user_email=data.email,
            role=data.role,
            inviter_id=current_user["id"],
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
    current_user: dict = Depends(require_disco_access),
):
    """Update a member's role."""
    try:
        member = await update_member_role(
            initiative_id=initiative_id,
            user_id=user_id,
            new_role=data.role,
            updater_id=current_user["id"],
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
    current_user: dict = Depends(require_disco_access),
):
    """Remove a member from an initiative."""
    try:
        await remove_member(
            initiative_id=initiative_id,
            user_id=user_id,
            remover_id=current_user["id"],
        )
        return {"success": True, "message": "Member removed"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from None
    except Exception as e:
        logger.error(f"Error removing member: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e
