"""
PuRDy API Routes

Product Requirements Document (PuRDy) API endpoints.
"""

import asyncio
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr

from auth import get_current_user, require_admin
from database import get_supabase
from logger_config import get_logger
from services.purdy import (
    # Initiative
    create_initiative,
    get_initiative,
    list_initiatives,
    update_initiative,
    delete_initiative,
    # Document
    upload_document,
    upload_document_file,
    get_documents,
    get_document,
    delete_document,
    search_initiative_docs,
    promote_output_to_document,
    # Agent
    load_agent_prompt,
    run_agent,
    get_agent_types,
    # Chat
    ask_question,
    get_conversation,
    # Sharing
    add_member,
    remove_member,
    list_members,
    update_member_role,
    check_permission,
    # System KB
    sync_kb_from_filesystem,
    search_system_kb,
    get_kb_files,
)
from services.purdy.agent_service import list_runs, get_run, run_agent_multi_pass, MULTI_PASS_CONFIG

logger = get_logger(__name__)
router = APIRouter(prefix="/api/purdy", tags=["purdy"])
supabase = get_supabase()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class InitiativeCreate(BaseModel):
    name: str
    description: Optional[str] = None


class InitiativeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class DocumentUploadText(BaseModel):
    filename: str
    content: str
    document_type: str = 'uploaded'


class MemberInvite(BaseModel):
    email: EmailStr
    role: str = 'viewer'


class MemberRoleUpdate(BaseModel):
    role: str


class ChatQuestion(BaseModel):
    question: str
    conversation_id: Optional[str] = None


class AgentRunRequest(BaseModel):
    agent_type: str
    document_ids: Optional[List[str]] = None
    output_format: Optional[str] = "comprehensive"  # comprehensive, executive, brief
    multi_pass: Optional[bool] = False  # Enable multi-pass synthesis (synthesizer only)


# ============================================================================
# AUTH HELPERS
# ============================================================================

async def check_purdy_access(user: dict) -> bool:
    """Check if user has PuRDy access."""
    user_id = user.get('id')
    if not user_id:
        return False

    # Fetch user's app_access
    result = await asyncio.to_thread(
        lambda: supabase.table('users')
            .select('app_access')
            .eq('id', user_id)
            .single()
            .execute()
    )

    if not result.data:
        return False

    app_access = result.data.get('app_access', ['thesis'])

    # Check for purdy or all access
    return 'purdy' in app_access or 'all' in app_access


async def require_purdy_access(current_user: dict = Depends(get_current_user)) -> dict:
    """Dependency to require PuRDy access."""
    has_access = await check_purdy_access(current_user)
    if not has_access:
        raise HTTPException(status_code=403, detail="PuRDy access required")
    return current_user


async def require_initiative_access(
    initiative_id: str,
    current_user: dict,
    required_role: str = 'viewer'
) -> bool:
    """Check user has access to initiative."""
    has_permission = await check_permission(initiative_id, current_user['id'], required_role)
    if not has_permission:
        raise HTTPException(
            status_code=403,
            detail=f"Insufficient permissions. Required: {required_role}"
        )
    return True


# ============================================================================
# INITIATIVES
# ============================================================================

@router.get("/initiatives")
async def api_list_initiatives(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(require_purdy_access)
):
    """List all initiatives accessible to the user."""
    try:
        result = await list_initiatives(
            user_id=current_user['id'],
            status_filter=status,
            limit=limit,
            offset=offset
        )
        return {
            'success': True,
            **result
        }
    except Exception as e:
        logger.error(f"Error listing initiatives: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/initiatives")
async def api_create_initiative(
    data: InitiativeCreate,
    current_user: dict = Depends(require_purdy_access)
):
    """Create a new initiative."""
    try:
        initiative = await create_initiative(
            name=data.name,
            description=data.description,
            user_id=current_user['id']
        )
        return {
            'success': True,
            'initiative': initiative
        }
    except Exception as e:
        logger.error(f"Error creating initiative: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/initiatives/{initiative_id}")
async def api_get_initiative(
    initiative_id: str,
    current_user: dict = Depends(require_purdy_access)
):
    """Get initiative details."""
    try:
        initiative = await get_initiative(initiative_id, current_user['id'])
        if not initiative:
            raise HTTPException(status_code=404, detail="Initiative not found")
        return {
            'success': True,
            'initiative': initiative
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching initiative: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/initiatives/{initiative_id}")
async def api_update_initiative(
    initiative_id: str,
    data: InitiativeUpdate,
    current_user: dict = Depends(require_purdy_access)
):
    """Update initiative details."""
    await require_initiative_access(initiative_id, current_user, 'editor')

    try:
        updates = data.model_dump(exclude_unset=True)
        initiative = await update_initiative(
            initiative_id=initiative_id,
            user_id=current_user['id'],
            updates=updates
        )
        return {
            'success': True,
            'initiative': initiative
        }
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating initiative: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/initiatives/{initiative_id}")
async def api_delete_initiative(
    initiative_id: str,
    current_user: dict = Depends(require_purdy_access)
):
    """Delete an initiative (owner only)."""
    try:
        await delete_initiative(initiative_id, current_user['id'])
        return {
            'success': True,
            'message': 'Initiative deleted'
        }
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting initiative: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# DOCUMENTS
# ============================================================================

@router.get("/initiatives/{initiative_id}/documents")
async def api_list_documents(
    initiative_id: str,
    document_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: dict = Depends(require_purdy_access)
):
    """List documents in an initiative."""
    await require_initiative_access(initiative_id, current_user, 'viewer')

    try:
        result = await get_documents(
            initiative_id=initiative_id,
            document_type=document_type,
            limit=limit,
            offset=offset
        )
        return {
            'success': True,
            **result
        }
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/initiatives/{initiative_id}/documents")
async def api_upload_document_file(
    initiative_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(require_purdy_access)
):
    """Upload a file document."""
    await require_initiative_access(initiative_id, current_user, 'editor')

    logger.info(f"[PURDY-DOC] Upload started: {file.filename}, content_type: {file.content_type}")

    try:
        file_data = await file.read()
        logger.info(f"[PURDY-DOC] File read complete: {len(file_data)} bytes")

        document = await upload_document_file(
            initiative_id=initiative_id,
            file_data=file_data,
            filename=file.filename,
            user_id=current_user['id']
        )
        logger.info(f"[PURDY-DOC] Upload successful: {document.get('id')}")
        return {
            'success': True,
            'document': document
        }
    except ValueError as e:
        logger.warning(f"[PURDY-DOC] Upload validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[PURDY-DOC] Upload failed: {type(e).__name__}: {e}")
        import traceback
        logger.error(f"[PURDY-DOC] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/initiatives/{initiative_id}/documents/text")
async def api_upload_document_text(
    initiative_id: str,
    data: DocumentUploadText,
    current_user: dict = Depends(require_purdy_access)
):
    """Upload a text document (for pasting content)."""
    await require_initiative_access(initiative_id, current_user, 'editor')

    try:
        document = await upload_document(
            initiative_id=initiative_id,
            filename=data.filename,
            content=data.content,
            user_id=current_user['id'],
            document_type=data.document_type
        )
        return {
            'success': True,
            'document': document
        }
    except Exception as e:
        logger.error(f"Error uploading text document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/initiatives/{initiative_id}/documents/{document_id}")
async def api_get_document(
    initiative_id: str,
    document_id: str,
    current_user: dict = Depends(require_purdy_access)
):
    """Get a document by ID."""
    await require_initiative_access(initiative_id, current_user, 'viewer')

    try:
        document = await get_document(document_id, initiative_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return {
            'success': True,
            'document': document
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/initiatives/{initiative_id}/documents/{document_id}")
async def api_delete_document(
    initiative_id: str,
    document_id: str,
    current_user: dict = Depends(require_purdy_access)
):
    """Delete a document."""
    await require_initiative_access(initiative_id, current_user, 'editor')

    try:
        await delete_document(document_id, initiative_id)
        return {
            'success': True,
            'message': 'Document deleted'
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# RUNS
# ============================================================================

@router.get("/initiatives/{initiative_id}/runs")
async def api_list_runs(
    initiative_id: str,
    limit: int = 20,
    current_user: dict = Depends(require_purdy_access)
):
    """List agent runs for an initiative."""
    await require_initiative_access(initiative_id, current_user, 'viewer')

    try:
        runs = await list_runs(initiative_id, limit)
        return {
            'success': True,
            'runs': runs
        }
    except Exception as e:
        logger.error(f"Error listing runs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/initiatives/{initiative_id}/runs")
async def api_start_run(
    initiative_id: str,
    data: AgentRunRequest,
    current_user: dict = Depends(require_purdy_access)
):
    """Start a new agent run with streaming response."""
    await require_initiative_access(initiative_id, current_user, 'editor')

    # Check if multi-pass is requested and valid
    use_multi_pass = (
        data.multi_pass and
        data.agent_type in MULTI_PASS_CONFIG.get("supported_agents", [])
    )

    async def event_stream():
        # Send initial padding to force proxy buffer flush (some proxies buffer first 1KB)
        yield ": " + " " * 2048 + "\n\n"

        try:
            # Choose single or multi-pass based on request
            if use_multi_pass:
                agent_gen = run_agent_multi_pass(
                    initiative_id=initiative_id,
                    agent_type=data.agent_type,
                    user_id=current_user['id'],
                    document_ids=data.document_ids,
                    output_format=data.output_format or "comprehensive"
                )
            else:
                agent_gen = run_agent(
                    initiative_id=initiative_id,
                    agent_type=data.agent_type,
                    user_id=current_user['id'],
                    document_ids=data.document_ids,
                    output_format=data.output_format or "comprehensive"
                )

            async for event in agent_gen:
                event_type = event.get('type', 'unknown')
                event_data = event.get('data', '')

                if event_type == 'content':
                    yield f"data: {event_data}\n\n"
                elif event_type == 'keepalive':
                    # SSE comment to keep connection alive and force flush
                    yield ": keepalive\n\n"
                elif event_type == 'status':
                    yield f"event: status\ndata: {event_data}\n\n"
                elif event_type == 'pass_complete':
                    # Multi-pass specific: indicates a pass completed
                    import json
                    yield f"event: pass_complete\ndata: {json.dumps(event_data)}\n\n"
                elif event_type == 'complete':
                    import json
                    yield f"event: complete\ndata: {json.dumps(event_data)}\n\n"
                elif event_type == 'error':
                    yield f"event: error\ndata: {event_data}\n\n"

        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"event: error\ndata: {str(e)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Content-Type": "text/event-stream; charset=utf-8",
        }
    )


@router.get("/initiatives/{initiative_id}/runs/{run_id}")
async def api_get_run(
    initiative_id: str,
    run_id: str,
    current_user: dict = Depends(require_purdy_access)
):
    """Get a run by ID."""
    await require_initiative_access(initiative_id, current_user, 'viewer')

    try:
        run = await get_run(run_id)
        if not run or run.get('initiative_id') != initiative_id:
            raise HTTPException(status_code=404, detail="Run not found")
        return {
            'success': True,
            'run': run
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# OUTPUTS
# ============================================================================

@router.get("/initiatives/{initiative_id}/outputs")
async def api_list_outputs(
    initiative_id: str,
    agent_type: Optional[str] = None,
    current_user: dict = Depends(require_purdy_access)
):
    """List outputs for an initiative."""
    await require_initiative_access(initiative_id, current_user, 'viewer')

    try:
        query = supabase.table('purdy_outputs')\
            .select('*')\
            .eq('initiative_id', initiative_id)

        if agent_type:
            query = query.eq('agent_type', agent_type)

        query = query.order('created_at', desc=True)

        result = await asyncio.to_thread(lambda: query.execute())

        return {
            'success': True,
            'outputs': result.data or []
        }
    except Exception as e:
        logger.error(f"Error listing outputs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/initiatives/{initiative_id}/outputs/{agent_type}")
async def api_get_latest_output(
    initiative_id: str,
    agent_type: str,
    current_user: dict = Depends(require_purdy_access)
):
    """Get the latest output of a specific type."""
    await require_initiative_access(initiative_id, current_user, 'viewer')

    try:
        result = await asyncio.to_thread(
            lambda: supabase.table('purdy_outputs')
                .select('*')
                .eq('initiative_id', initiative_id)
                .eq('agent_type', agent_type)
                .order('version', desc=True)
                .limit(1)
                .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail=f"No {agent_type} output found")

        return {
            'success': True,
            'output': result.data[0]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching output: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/initiatives/{initiative_id}/outputs/{agent_type}/versions")
async def api_list_output_versions(
    initiative_id: str,
    agent_type: str,
    current_user: dict = Depends(require_purdy_access)
):
    """List all versions of an output type."""
    await require_initiative_access(initiative_id, current_user, 'viewer')

    try:
        result = await asyncio.to_thread(
            lambda: supabase.table('purdy_outputs')
                .select('id, version, created_at, title, recommendation, confidence_level')
                .eq('initiative_id', initiative_id)
                .eq('agent_type', agent_type)
                .order('version', desc=True)
                .execute()
        )

        return {
            'success': True,
            'versions': result.data or []
        }
    except Exception as e:
        logger.error(f"Error listing output versions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/initiatives/{initiative_id}/outputs/{output_id}/export")
async def api_export_output(
    initiative_id: str,
    output_id: str,
    current_user: dict = Depends(require_purdy_access)
):
    """Export an output as markdown."""
    await require_initiative_access(initiative_id, current_user, 'viewer')

    try:
        result = await asyncio.to_thread(
            lambda: supabase.table('purdy_outputs')
                .select('agent_type, version, content_markdown')
                .eq('id', output_id)
                .eq('initiative_id', initiative_id)
                .single()
                .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Output not found")

        output = result.data
        filename = f"{output['agent_type']}_v{output['version']}.md"

        return StreamingResponse(
            iter([output['content_markdown']]),
            media_type="text/markdown",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting output: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/initiatives/{initiative_id}/outputs/{output_id}/promote")
async def api_promote_output(
    initiative_id: str,
    output_id: str,
    current_user: dict = Depends(require_purdy_access)
):
    """Promote an output to a document."""
    await require_initiative_access(initiative_id, current_user, 'editor')

    try:
        document = await promote_output_to_document(output_id, initiative_id)
        return {
            'success': True,
            'document': document
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error promoting output: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/initiatives/{initiative_id}/outputs/{output_id}")
async def api_delete_output(
    initiative_id: str,
    output_id: str,
    current_user: dict = Depends(require_purdy_access)
):
    """Delete an output."""
    await require_initiative_access(initiative_id, current_user, 'editor')

    try:
        # Verify output belongs to initiative
        output_result = await asyncio.to_thread(
            lambda: supabase.table('purdy_outputs')
                .select('id, agent_type, version')
                .eq('id', output_id)
                .eq('initiative_id', initiative_id)
                .single()
                .execute()
        )

        if not output_result.data:
            raise HTTPException(status_code=404, detail="Output not found")

        # Delete the output
        await asyncio.to_thread(
            lambda: supabase.table('purdy_outputs')
                .delete()
                .eq('id', output_id)
                .execute()
        )

        logger.info(f"[PURDY] Deleted output {output_id} ({output_result.data['agent_type']} v{output_result.data['version']})")

        return {
            'success': True,
            'deleted_output_id': output_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting output: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# DEBUG
# ============================================================================

@router.get("/initiatives/{initiative_id}/debug/outputs")
async def api_debug_outputs(
    initiative_id: str,
    current_user: dict = Depends(require_purdy_access)
):
    """Debug endpoint to check raw output data."""
    await require_initiative_access(initiative_id, current_user, 'viewer')

    try:
        result = await asyncio.to_thread(
            lambda: supabase.table('purdy_outputs')
                .select('id, agent_type, version, title, content_markdown, created_at')
                .eq('initiative_id', initiative_id)
                .order('created_at', desc=True)
                .limit(5)
                .execute()
        )

        outputs = []
        for o in (result.data or []):
            outputs.append({
                'id': o.get('id'),
                'agent_type': o.get('agent_type'),
                'agent_type_type': type(o.get('agent_type')).__name__,
                'version': o.get('version'),
                'title': o.get('title'),
                'content_length': len(o.get('content_markdown', '') or ''),
                'content_preview': (o.get('content_markdown', '') or '')[:200],
                'created_at': o.get('created_at')
            })

        return {
            'success': True,
            'count': len(result.data or []),
            'outputs': outputs
        }
    except Exception as e:
        logger.error(f"Debug outputs error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


# ============================================================================
# SHARING
# ============================================================================

@router.get("/initiatives/{initiative_id}/members")
async def api_list_members(
    initiative_id: str,
    current_user: dict = Depends(require_purdy_access)
):
    """List initiative members."""
    await require_initiative_access(initiative_id, current_user, 'viewer')

    try:
        members = await list_members(initiative_id)
        return {
            'success': True,
            'members': members
        }
    except Exception as e:
        logger.error(f"Error listing members: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/initiatives/{initiative_id}/members")
async def api_add_member(
    initiative_id: str,
    data: MemberInvite,
    current_user: dict = Depends(require_purdy_access)
):
    """Invite a member to an initiative."""
    await require_initiative_access(initiative_id, current_user, 'editor')

    try:
        member = await add_member(
            initiative_id=initiative_id,
            user_email=data.email,
            role=data.role,
            inviter_id=current_user['id']
        )
        return {
            'success': True,
            'member': member
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding member: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/initiatives/{initiative_id}/members/{user_id}")
async def api_update_member_role(
    initiative_id: str,
    user_id: str,
    data: MemberRoleUpdate,
    current_user: dict = Depends(require_purdy_access)
):
    """Update a member's role."""
    try:
        member = await update_member_role(
            initiative_id=initiative_id,
            user_id=user_id,
            new_role=data.role,
            updater_id=current_user['id']
        )
        return {
            'success': True,
            'member': member
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating member role: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/initiatives/{initiative_id}/members/{user_id}")
async def api_remove_member(
    initiative_id: str,
    user_id: str,
    current_user: dict = Depends(require_purdy_access)
):
    """Remove a member from an initiative."""
    try:
        await remove_member(
            initiative_id=initiative_id,
            user_id=user_id,
            remover_id=current_user['id']
        )
        return {
            'success': True,
            'message': 'Member removed'
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error removing member: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CHAT
# ============================================================================

@router.get("/initiatives/{initiative_id}/chat")
async def api_get_chat(
    initiative_id: str,
    current_user: dict = Depends(require_purdy_access)
):
    """Get or create chat conversation."""
    await require_initiative_access(initiative_id, current_user, 'viewer')

    try:
        conversation = await get_conversation(initiative_id, current_user['id'])
        return {
            'success': True,
            'conversation': conversation
        }
    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/initiatives/{initiative_id}/chat")
async def api_ask_question(
    initiative_id: str,
    data: ChatQuestion,
    current_user: dict = Depends(require_purdy_access)
):
    """Ask a question about the initiative."""
    await require_initiative_access(initiative_id, current_user, 'viewer')

    try:
        result = await ask_question(
            initiative_id=initiative_id,
            question=data.question,
            user_id=current_user['id'],
            conversation_id=data.conversation_id
        )
        return {
            'success': True,
            **result
        }
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# AGENTS (Reference)
# ============================================================================

@router.get("/agents")
async def api_list_agents(
    current_user: dict = Depends(require_purdy_access)
):
    """List available agent types."""
    return {
        'success': True,
        'agents': get_agent_types()
    }


@router.get("/agents/{agent_type}")
async def api_get_agent_prompt(
    agent_type: str,
    current_user: dict = Depends(require_admin)
):
    """Get agent prompt (admin only)."""
    try:
        prompt = load_agent_prompt(agent_type)
        return {
            'success': True,
            'agent_type': agent_type,
            'prompt': prompt
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error loading agent prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SYSTEM KB (Admin)
# ============================================================================

@router.get("/system-kb")
async def api_list_kb_files(
    current_user: dict = Depends(require_admin)
):
    """List system KB files (admin only)."""
    try:
        files = await get_kb_files()
        return {
            'success': True,
            'files': files
        }
    except Exception as e:
        logger.error(f"Error listing KB files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/system-kb/sync")
async def api_sync_kb(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_admin)
):
    """Sync system KB from filesystem (admin only)."""
    try:
        # Run sync in background
        async def do_sync():
            try:
                result = await sync_kb_from_filesystem()
                logger.info(f"KB sync completed: {result}")
            except Exception as e:
                logger.error(f"KB sync failed: {e}")

        background_tasks.add_task(asyncio.create_task, do_sync())

        return {
            'success': True,
            'message': 'KB sync started in background'
        }
    except Exception as e:
        logger.error(f"Error starting KB sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system-kb/search")
async def api_search_kb(
    q: str,
    limit: int = 10,
    category: Optional[str] = None,
    current_user: dict = Depends(require_purdy_access)
):
    """Search system KB."""
    try:
        chunks = await search_system_kb(q, limit=limit, category=category)
        return {
            'success': True,
            'results': chunks
        }
    except Exception as e:
        logger.error(f"Error searching KB: {e}")
        raise HTTPException(status_code=500, detail=str(e))
