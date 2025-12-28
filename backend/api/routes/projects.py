"""
Project management routes
Handles creation, retrieval, updating, and deletion of projects
Projects group related conversations for better organization
"""
import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import get_current_user
from config import get_default_client_id
from database import get_supabase
from logger_config import get_logger
from validation import validate_uuid

logger = get_logger(__name__)
router = APIRouter(prefix="/api/projects", tags=["projects"])
supabase = get_supabase()


# ============================================================================
# Request/Response Models
# ============================================================================

class ProjectCreateRequest(BaseModel):
    title: str
    description: Optional[str] = None
    current_phase: Optional[str] = "Analysis"
    client_id: Optional[str] = None


class ProjectUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    current_phase: Optional[str] = None
    status: Optional[str] = None


class AddConversationRequest(BaseModel):
    conversation_id: str


# ============================================================================
# Project CRUD Operations
# ============================================================================

@router.post("/create")
async def create_project(
    request: ProjectCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new project"""
    try:
        # Auto-assign default client if not provided
        client_id = request.client_id or get_default_client_id()
        user_id = current_user['id']

        logger.info(f"📁 Creating project for user: {user_id}")

        # Validate phase if provided
        valid_phases = ['Analysis', 'Design', 'Development', 'Implementation', 'Evaluation', 'Complete']
        if request.current_phase and request.current_phase not in valid_phases:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid phase. Must be one of: {', '.join(valid_phases)}"
            )

        # Create project in database
        result = await asyncio.to_thread(
            lambda: supabase.table('projects').insert({
                'client_id': client_id,
                'user_id': user_id,
                'title': request.title,
                'description': request.description,
                'current_phase': request.current_phase or 'Analysis',
                'status': 'active'
            }).execute()
        )

        project = result.data[0]
        logger.info(f"✅ Project created: {project['id']}")

        return {
            'success': True,
            'project': project
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def list_projects(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """List all projects for the current user"""
    try:
        user_id = current_user['id']

        query = supabase.table('projects')\
            .select('*, conversations(id, title, created_at)')\
            .eq('user_id', user_id)\
            .order('updated_at', desc=True)

        if status:
            query = query.eq('status', status)

        result = await asyncio.to_thread(lambda: query.execute())

        # Add conversation count to each project
        projects = result.data if result.data else []
        for project in projects:
            project['conversation_count'] = len(project.get('conversations', []))

        return {
            'success': True,
            'projects': projects
        }

    except Exception as e:
        logger.error(f"❌ Error listing projects: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}")
async def get_project(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific project with its conversations"""
    try:
        validate_uuid(project_id, "project_id")
        user_id = current_user['id']

        result = await asyncio.to_thread(
            lambda: supabase.table('projects')\
                .select('*, conversations(id, title, created_at, updated_at)')\
                .eq('id', project_id)\
                .eq('user_id', user_id)\
                .single()\
                .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Project not found")

        return {
            'success': True,
            'project': result.data
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{project_id}")
async def update_project(
    project_id: str,
    request: ProjectUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update a project"""
    try:
        validate_uuid(project_id, "project_id")
        user_id = current_user['id']

        # Build update data
        update_data = {}
        if request.title is not None:
            update_data['title'] = request.title
        if request.description is not None:
            update_data['description'] = request.description
        if request.current_phase is not None:
            valid_phases = ['Analysis', 'Design', 'Development', 'Implementation', 'Evaluation', 'Complete']
            if request.current_phase not in valid_phases:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid phase. Must be one of: {', '.join(valid_phases)}"
                )
            update_data['current_phase'] = request.current_phase
        if request.status is not None:
            valid_statuses = ['active', 'archived', 'complete']
            if request.status not in valid_statuses:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
                )
            update_data['status'] = request.status

        if not update_data:
            raise HTTPException(status_code=400, detail="No update data provided")

        # Update project
        result = await asyncio.to_thread(
            lambda: supabase.table('projects')\
                .update(update_data)\
                .eq('id', project_id)\
                .eq('user_id', user_id)\
                .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Project not found")

        logger.info(f"✅ Project updated: {project_id}")

        return {
            'success': True,
            'project': result.data[0]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a project (conversations are unlinked, not deleted)"""
    try:
        validate_uuid(project_id, "project_id")
        user_id = current_user['id']

        # First unlink all conversations from this project
        await asyncio.to_thread(
            lambda: supabase.table('conversations')\
                .update({'project_id': None})\
                .eq('project_id', project_id)\
                .execute()
        )

        # Delete the project
        result = await asyncio.to_thread(
            lambda: supabase.table('projects')\
                .delete()\
                .eq('id', project_id)\
                .eq('user_id', user_id)\
                .execute()
        )

        logger.info(f"✅ Project deleted: {project_id}")

        return {
            'success': True,
            'message': 'Project deleted successfully'
        }

    except Exception as e:
        logger.error(f"❌ Error deleting project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Conversation Management within Projects
# ============================================================================

@router.post("/{project_id}/conversations")
async def add_conversation_to_project(
    project_id: str,
    request: AddConversationRequest,
    current_user: dict = Depends(get_current_user)
):
    """Add a conversation to a project"""
    try:
        validate_uuid(project_id, "project_id")
        validate_uuid(request.conversation_id, "conversation_id")
        user_id = current_user['id']

        # Verify project belongs to user
        project_result = await asyncio.to_thread(
            lambda: supabase.table('projects')\
                .select('id')\
                .eq('id', project_id)\
                .eq('user_id', user_id)\
                .single()\
                .execute()
        )

        if not project_result.data:
            raise HTTPException(status_code=404, detail="Project not found")

        # Update conversation to link to project
        result = await asyncio.to_thread(
            lambda: supabase.table('conversations')\
                .update({'project_id': project_id})\
                .eq('id', request.conversation_id)\
                .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Conversation not found")

        logger.info(f"✅ Conversation {request.conversation_id} added to project {project_id}")

        return {
            'success': True,
            'message': 'Conversation added to project'
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error adding conversation to project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{project_id}/conversations/{conversation_id}")
async def remove_conversation_from_project(
    project_id: str,
    conversation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Remove a conversation from a project (unlinks, doesn't delete)"""
    try:
        validate_uuid(project_id, "project_id")
        validate_uuid(conversation_id, "conversation_id")

        # Update conversation to unlink from project
        result = await asyncio.to_thread(
            lambda: supabase.table('conversations')\
                .update({'project_id': None})\
                .eq('id', conversation_id)\
                .eq('project_id', project_id)\
                .execute()
        )

        logger.info(f"✅ Conversation {conversation_id} removed from project {project_id}")

        return {
            'success': True,
            'message': 'Conversation removed from project'
        }

    except Exception as e:
        logger.error(f"❌ Error removing conversation from project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/conversations")
async def get_project_conversations(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all conversations in a project"""
    try:
        validate_uuid(project_id, "project_id")
        user_id = current_user['id']

        # Verify project belongs to user
        project_result = await asyncio.to_thread(
            lambda: supabase.table('projects')\
                .select('id')\
                .eq('id', project_id)\
                .eq('user_id', user_id)\
                .single()\
                .execute()
        )

        if not project_result.data:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get conversations
        result = await asyncio.to_thread(
            lambda: supabase.table('conversations')\
                .select('id, title, created_at, updated_at, message_count:messages(count)')\
                .eq('project_id', project_id)\
                .order('updated_at', desc=True)\
                .execute()
        )

        return {
            'success': True,
            'conversations': result.data if result.data else []
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching project conversations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
