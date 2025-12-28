"""
Projects routes (stub implementation)

This is a placeholder for the projects feature. The frontend has UI for projects,
but the backend is not yet implemented. This stub returns empty results to prevent
404 errors until the full feature is built.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query

from auth import get_current_user

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("")
async def get_projects(
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all projects for the current user.
    Stub implementation - returns empty list until feature is built.
    """
    return {
        "success": True,
        "projects": [],
        "message": "Projects feature coming soon"
    }


@router.post("/create")
async def create_project(
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new project.
    Stub implementation.
    """
    return {
        "success": False,
        "message": "Projects feature not yet implemented"
    }


@router.get("/{project_id}")
async def get_project(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific project.
    Stub implementation.
    """
    return {
        "success": False,
        "message": "Projects feature not yet implemented"
    }


@router.patch("/{project_id}")
async def update_project(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Update a project.
    Stub implementation.
    """
    return {
        "success": False,
        "message": "Projects feature not yet implemented"
    }


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a project.
    Stub implementation.
    """
    return {
        "success": False,
        "message": "Projects feature not yet implemented"
    }


@router.post("/{project_id}/conversations")
async def add_conversation_to_project(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Add a conversation to a project.
    Stub implementation.
    """
    return {
        "success": False,
        "message": "Projects feature not yet implemented"
    }


@router.delete("/{project_id}/conversations/{conversation_id}")
async def remove_conversation_from_project(
    project_id: str,
    conversation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Remove a conversation from a project.
    Stub implementation.
    """
    return {
        "success": False,
        "message": "Projects feature not yet implemented"
    }


@router.get("/{project_id}/conversations")
async def get_project_conversations(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all conversations in a project.
    Stub implementation.
    """
    return {
        "success": True,
        "conversations": []
    }
