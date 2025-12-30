"""
Meeting Room routes
Handles creation, management, and chat for multi-agent meeting rooms
"""
import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Optional

from anthropic import Anthropic
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from auth import get_current_user
from config import get_default_client_id
from database import get_supabase
from document_processor import search_similar_chunks
from logger_config import get_logger
from validation import validate_uuid

from ..models.meeting_rooms import (
    MeetingRoomCreateRequest,
    MeetingRoomUpdateRequest,
    MeetingChatRequest,
    ParticipantAddRequest,
    ParticipantUpdateRequest,
    MeetingRoomResponse,
    MeetingRoomListResponse,
    MeetingMessageResponse,
    ParticipantResponse,
    AutonomousDiscussionRequest,
    AutonomousDiscussionStatus,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/api/meeting-rooms", tags=["meeting-rooms"])
limiter = Limiter(key_func=get_remote_address)
supabase = get_supabase()

# Initialize Anthropic client
anthropic_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# Global orchestrator instance (initialized lazily)
_meeting_orchestrator = None


# ============================================================================
# MEETING ROOM CRUD OPERATIONS
# ============================================================================

@router.post("")
async def create_meeting_room(
    request: MeetingRoomCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new meeting room with selected agent participants."""
    try:
        user_id = current_user['id']
        client_id = get_default_client_id()

        # Validate all agent IDs exist and are active
        agent_ids = request.participant_agent_ids
        agents_result = await asyncio.to_thread(
            lambda: supabase.table('agents')
                .select('id, name, display_name')
                .in_('id', agent_ids)
                .eq('is_active', True)
                .execute()
        )

        found_agents = {a['id']: a for a in agents_result.data}
        missing_agents = [aid for aid in agent_ids if aid not in found_agents]

        if missing_agents:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid or inactive agent IDs: {missing_agents}"
            )

        # Create the meeting room
        meeting_data = {
            'client_id': client_id,
            'user_id': user_id,
            'title': request.title,
            'description': request.description,
            'meeting_type': request.meeting_type,
            'status': 'active',
            'config': request.config or {},
        }

        meeting_result = await asyncio.to_thread(
            lambda: supabase.table('meeting_rooms')
                .insert(meeting_data)
                .execute()
        )

        meeting = meeting_result.data[0]
        meeting_id = meeting['id']
        logger.info(f"Created meeting room: {meeting_id}")

        # Add participants
        participants_data = [
            {
                'meeting_room_id': meeting_id,
                'agent_id': agent_id,
                'priority': idx,
            }
            for idx, agent_id in enumerate(agent_ids)
        ]

        await asyncio.to_thread(
            lambda: supabase.table('meeting_room_participants')
                .insert(participants_data)
                .execute()
        )

        logger.info(f"Added {len(agent_ids)} participants to meeting {meeting_id}")

        # Build response with participant details
        participants = [
            ParticipantResponse(
                id=str(idx),  # Temporary ID
                agent_id=agent_id,
                agent_name=found_agents[agent_id]['name'],
                agent_display_name=found_agents[agent_id]['display_name'],
                role_description=None,
                priority=idx,
                turns_taken=0,
                tokens_used=0,
                created_at=datetime.now(timezone.utc),
            )
            for idx, agent_id in enumerate(agent_ids)
        ]

        return {
            'success': True,
            'meeting_room': MeetingRoomResponse(
                id=meeting['id'],
                client_id=meeting['client_id'],
                user_id=meeting['user_id'],
                title=meeting['title'],
                description=meeting['description'],
                meeting_type=meeting['meeting_type'],
                status=meeting['status'],
                config=meeting['config'],
                total_tokens_used=meeting['total_tokens_used'],
                created_at=meeting['created_at'],
                updated_at=meeting['updated_at'],
                participants=participants,
            )
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating meeting room: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def list_meeting_rooms(
    status: Optional[str] = None,
    meeting_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """List user's meeting rooms."""
    try:
        user_id = current_user['id']

        # Build query
        query = supabase.table('meeting_rooms')\
            .select('*', count='exact')\
            .eq('user_id', user_id)

        if status:
            query = query.eq('status', status)
        if meeting_type:
            query = query.eq('meeting_type', meeting_type)

        query = query.order('updated_at', desc=True)\
            .range(offset, offset + limit - 1)

        result = await asyncio.to_thread(lambda: query.execute())

        meetings = result.data

        # Get participant counts for all meetings
        if meetings:
            meeting_ids = [m['id'] for m in meetings]
            participants_result = await asyncio.to_thread(
                lambda: supabase.table('meeting_room_participants')
                    .select('meeting_room_id')
                    .in_('meeting_room_id', meeting_ids)
                    .execute()
            )

            # Count participants per meeting
            participant_counts = {}
            for p in participants_result.data:
                mid = p['meeting_room_id']
                participant_counts[mid] = participant_counts.get(mid, 0) + 1

            # Add counts to meetings
            for meeting in meetings:
                meeting['participant_count'] = participant_counts.get(meeting['id'], 0)

        return {
            'success': True,
            'meeting_rooms': [
                MeetingRoomListResponse(
                    id=m['id'],
                    title=m['title'],
                    description=m['description'],
                    meeting_type=m['meeting_type'],
                    status=m['status'],
                    total_tokens_used=m['total_tokens_used'],
                    participant_count=m.get('participant_count', 0),
                    created_at=m['created_at'],
                    updated_at=m['updated_at'],
                )
                for m in meetings
            ],
            'total': result.count,
            'limit': limit,
            'offset': offset,
        }

    except Exception as e:
        logger.error(f"Error listing meeting rooms: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{meeting_id}")
async def get_meeting_room(
    meeting_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get meeting room details with participants."""
    try:
        validate_uuid(meeting_id, "meeting_id")
        user_id = current_user['id']

        # Get meeting room
        meeting_result = await asyncio.to_thread(
            lambda: supabase.table('meeting_rooms')
                .select('*')
                .eq('id', meeting_id)
                .eq('user_id', user_id)
                .single()
                .execute()
        )

        if not meeting_result.data:
            raise HTTPException(status_code=404, detail="Meeting room not found")

        meeting = meeting_result.data

        # Get participants with agent details
        participants_result = await asyncio.to_thread(
            lambda: supabase.table('meeting_room_participants')
                .select('*, agents(id, name, display_name, description)')
                .eq('meeting_room_id', meeting_id)
                .order('priority')
                .execute()
        )

        participants = [
            ParticipantResponse(
                id=p['id'],
                agent_id=p['agent_id'],
                agent_name=p['agents']['name'],
                agent_display_name=p['agents']['display_name'],
                role_description=p['role_description'],
                priority=p['priority'],
                turns_taken=p['turns_taken'],
                tokens_used=p['tokens_used'],
                created_at=p['created_at'],
            )
            for p in participants_result.data
        ]

        return {
            'success': True,
            'meeting_room': MeetingRoomResponse(
                id=meeting['id'],
                client_id=meeting['client_id'],
                user_id=meeting['user_id'],
                title=meeting['title'],
                description=meeting['description'],
                meeting_type=meeting['meeting_type'],
                status=meeting['status'],
                config=meeting['config'],
                total_tokens_used=meeting['total_tokens_used'],
                created_at=meeting['created_at'],
                updated_at=meeting['updated_at'],
                participants=participants,
            )
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting meeting room: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{meeting_id}")
async def update_meeting_room(
    meeting_id: str,
    request: MeetingRoomUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update meeting room details."""
    try:
        validate_uuid(meeting_id, "meeting_id")
        user_id = current_user['id']

        # Build update data
        update_data = {}
        if request.title is not None:
            update_data['title'] = request.title
        if request.description is not None:
            update_data['description'] = request.description
        if request.status is not None:
            update_data['status'] = request.status
        if request.config is not None:
            update_data['config'] = request.config

        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        result = await asyncio.to_thread(
            lambda: supabase.table('meeting_rooms')
                .update(update_data)
                .eq('id', meeting_id)
                .eq('user_id', user_id)
                .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Meeting room not found")

        return {
            'success': True,
            'meeting_room': result.data[0]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating meeting room: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{meeting_id}")
async def delete_meeting_room(
    meeting_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a meeting room and all its messages."""
    try:
        validate_uuid(meeting_id, "meeting_id")
        user_id = current_user['id']

        # Verify ownership first
        meeting_result = await asyncio.to_thread(
            lambda: supabase.table('meeting_rooms')
                .select('id')
                .eq('id', meeting_id)
                .eq('user_id', user_id)
                .execute()
        )

        if not meeting_result.data:
            raise HTTPException(status_code=404, detail="Meeting room not found")

        # Delete meeting (cascades to participants and messages)
        await asyncio.to_thread(
            lambda: supabase.table('meeting_rooms')
                .delete()
                .eq('id', meeting_id)
                .execute()
        )

        logger.info(f"Deleted meeting room: {meeting_id}")

        return {
            'success': True,
            'message': 'Meeting room deleted successfully'
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting meeting room: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PARTICIPANT MANAGEMENT
# ============================================================================

@router.post("/{meeting_id}/participants")
async def add_participant(
    meeting_id: str,
    request: ParticipantAddRequest,
    current_user: dict = Depends(get_current_user)
):
    """Add a participant to an existing meeting."""
    try:
        validate_uuid(meeting_id, "meeting_id")
        validate_uuid(request.agent_id, "agent_id")
        user_id = current_user['id']

        # Verify meeting ownership
        meeting_result = await asyncio.to_thread(
            lambda: supabase.table('meeting_rooms')
                .select('id')
                .eq('id', meeting_id)
                .eq('user_id', user_id)
                .execute()
        )

        if not meeting_result.data:
            raise HTTPException(status_code=404, detail="Meeting room not found")

        # Verify agent exists and is active
        agent_result = await asyncio.to_thread(
            lambda: supabase.table('agents')
                .select('id, name, display_name')
                .eq('id', request.agent_id)
                .eq('is_active', True)
                .single()
                .execute()
        )

        if not agent_result.data:
            raise HTTPException(status_code=400, detail="Invalid or inactive agent")

        agent = agent_result.data

        # Add participant
        participant_data = {
            'meeting_room_id': meeting_id,
            'agent_id': request.agent_id,
            'role_description': request.role_description,
            'priority': request.priority,
        }

        result = await asyncio.to_thread(
            lambda: supabase.table('meeting_room_participants')
                .insert(participant_data)
                .execute()
        )

        participant = result.data[0]

        return {
            'success': True,
            'participant': ParticipantResponse(
                id=participant['id'],
                agent_id=participant['agent_id'],
                agent_name=agent['name'],
                agent_display_name=agent['display_name'],
                role_description=participant['role_description'],
                priority=participant['priority'],
                turns_taken=0,
                tokens_used=0,
                created_at=participant['created_at'],
            )
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding participant: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{meeting_id}/participants/{participant_id}")
async def update_participant(
    meeting_id: str,
    participant_id: str,
    request: ParticipantUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update a participant's configuration."""
    try:
        validate_uuid(meeting_id, "meeting_id")
        validate_uuid(participant_id, "participant_id")
        user_id = current_user['id']

        # Verify meeting ownership
        meeting_result = await asyncio.to_thread(
            lambda: supabase.table('meeting_rooms')
                .select('id')
                .eq('id', meeting_id)
                .eq('user_id', user_id)
                .execute()
        )

        if not meeting_result.data:
            raise HTTPException(status_code=404, detail="Meeting room not found")

        # Build update data
        update_data = {}
        if request.role_description is not None:
            update_data['role_description'] = request.role_description
        if request.priority is not None:
            update_data['priority'] = request.priority

        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        result = await asyncio.to_thread(
            lambda: supabase.table('meeting_room_participants')
                .update(update_data)
                .eq('id', participant_id)
                .eq('meeting_room_id', meeting_id)
                .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Participant not found")

        return {
            'success': True,
            'participant': result.data[0]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating participant: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{meeting_id}/participants/{participant_id}")
async def remove_participant(
    meeting_id: str,
    participant_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Remove a participant from a meeting."""
    try:
        validate_uuid(meeting_id, "meeting_id")
        validate_uuid(participant_id, "participant_id")
        user_id = current_user['id']

        # Verify meeting ownership
        meeting_result = await asyncio.to_thread(
            lambda: supabase.table('meeting_rooms')
                .select('id')
                .eq('id', meeting_id)
                .eq('user_id', user_id)
                .execute()
        )

        if not meeting_result.data:
            raise HTTPException(status_code=404, detail="Meeting room not found")

        # Check we're not removing the last participant(s)
        count_result = await asyncio.to_thread(
            lambda: supabase.table('meeting_room_participants')
                .select('id', count='exact')
                .eq('meeting_room_id', meeting_id)
                .execute()
        )

        if count_result.count <= 2:
            raise HTTPException(
                status_code=400,
                detail="Cannot remove participant: meeting requires at least 2 agents"
            )

        # Remove participant
        result = await asyncio.to_thread(
            lambda: supabase.table('meeting_room_participants')
                .delete()
                .eq('id', participant_id)
                .eq('meeting_room_id', meeting_id)
                .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Participant not found")

        return {
            'success': True,
            'message': 'Participant removed successfully'
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing participant: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MESSAGE RETRIEVAL
# ============================================================================

@router.get("/{meeting_id}/messages")
async def get_meeting_messages(
    meeting_id: str,
    limit: int = 100,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """Get messages from a meeting room."""
    try:
        validate_uuid(meeting_id, "meeting_id")
        user_id = current_user['id']

        # Verify meeting ownership
        meeting_result = await asyncio.to_thread(
            lambda: supabase.table('meeting_rooms')
                .select('id')
                .eq('id', meeting_id)
                .eq('user_id', user_id)
                .execute()
        )

        if not meeting_result.data:
            raise HTTPException(status_code=404, detail="Meeting room not found")

        # Get messages
        result = await asyncio.to_thread(
            lambda: supabase.table('meeting_room_messages')
                .select('*', count='exact')
                .eq('meeting_room_id', meeting_id)
                .order('created_at', desc=False)
                .range(offset, offset + limit - 1)
                .execute()
        )

        messages = [
            MeetingMessageResponse(
                id=m['id'],
                meeting_room_id=m['meeting_room_id'],
                role=m['role'],
                agent_id=m['agent_id'],
                agent_name=m['agent_name'],
                agent_display_name=m['agent_display_name'],
                content=m['content'],
                metadata=m['metadata'] or {},
                turn_number=m['turn_number'],
                created_at=m['created_at'],
            )
            for m in result.data
        ]

        return {
            'success': True,
            'messages': messages,
            'total_count': result.count,
            'has_more': (offset + limit) < result.count,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting meeting messages: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# STREAMING CHAT ENDPOINT
# ============================================================================

async def get_orchestrator():
    """Get or initialize the meeting orchestrator."""
    global _meeting_orchestrator
    if _meeting_orchestrator is None:
        from services.meeting_orchestrator import get_meeting_orchestrator
        _meeting_orchestrator = await get_meeting_orchestrator(supabase, anthropic_client)
    return _meeting_orchestrator


@router.post("/{meeting_id}/chat/stream")
@limiter.limit("20/minute")
async def stream_meeting_chat(
    request: Request,
    meeting_id: str,
    chat_request: MeetingChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Send a message in a meeting room and stream responses from agents.

    Returns Server-Sent Events (SSE) with the following event types:
    - agent_turn_start: When an agent begins responding
    - agent_token: Individual tokens from agent response
    - agent_turn_end: When an agent finishes
    - round_complete: When all agents have responded
    - error: If something goes wrong
    """
    # Ultra-early logging to confirm we enter the function
    logger.info(f"[Meeting Chat] === ENTERING stream_meeting_chat for {meeting_id} ===")

    try:
        validate_uuid(meeting_id, "meeting_id")
        user_id = current_user['id']
        client_id = get_default_client_id()

        logger.info(f"[Meeting Chat] Starting for meeting {meeting_id}, user {user_id}")

        # Verify meeting ownership and get meeting details
        try:
            meeting_result = await asyncio.to_thread(
                lambda: supabase.table('meeting_rooms')
                    .select('*')
                    .eq('id', meeting_id)
                    .eq('user_id', user_id)
                    .single()
                    .execute()
            )
        except Exception as db_err:
            logger.error(f"[Meeting Chat] DB error fetching meeting: {db_err}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(db_err)}")

        if not meeting_result.data:
            raise HTTPException(status_code=404, detail="Meeting room not found")

        meeting = meeting_result.data
        logger.info(f"[Meeting Chat] Found meeting: {meeting.get('title', 'Unknown')}")

        # Get participants with agent details
        try:
            participants_result = await asyncio.to_thread(
                lambda: supabase.table('meeting_room_participants')
                    .select('*, agents(id, name, display_name)')
                    .eq('meeting_room_id', meeting_id)
                    .order('priority')
                    .execute()
            )
        except Exception as db_err:
            logger.error(f"[Meeting Chat] DB error fetching participants: {db_err}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(db_err)}")

        participants = [
            {
                'id': p['id'],
                'agent_id': p['agent_id'],
                'agent_name': p['agents']['name'],
                'agent_display_name': p['agents']['display_name'],
                'role_description': p.get('role_description'),
                'priority': p.get('priority', 0),
            }
            for p in participants_result.data
            if p.get('agents')  # Skip participants with missing agent data
        ]

        if not participants:
            raise HTTPException(status_code=400, detail="No participants in meeting")

        logger.info(f"Meeting {meeting_id} has {len(participants)} participants: {[p['agent_name'] for p in participants]}")

        # Get message history
        try:
            messages_result = await asyncio.to_thread(
                lambda: supabase.table('meeting_room_messages')
                    .select('id, role, content, agent_name, agent_display_name, created_at')
                    .eq('meeting_room_id', meeting_id)
                    .order('created_at', desc=False)
                    .limit(50)  # Last 50 messages for context
                    .execute()
            )
        except Exception as db_err:
            logger.error(f"[Meeting Chat] DB error fetching messages: {db_err}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(db_err)}")

        message_history = [
            {
                'role': m.get('role', 'user'),
                'content': m.get('content', ''),
                'agent_name': m.get('agent_name'),
                'agent_display_name': m.get('agent_display_name'),
            }
            for m in messages_result.data
        ]

        logger.info(f"[Meeting Chat] Found {len(message_history)} messages in history")

        # Calculate turn number
        turn_number = len([m for m in messages_result.data if m.get('role') == 'user']) + 1

        # Retrieve Knowledge Base context for the user's message
        # This gives agents access to documents and previous conversations
        kb_context = []
        try:
            # Skip KB search for simple greetings
            simple_messages = {
                'hello', 'hi', 'hey', 'greetings', 'good morning', 'good afternoon',
                'good evening', 'howdy', 'yo', 'sup', 'thanks', 'thank you', 'bye'
            }
            message_lower = chat_request.message.lower().strip()
            is_simple_message = message_lower in simple_messages or len(chat_request.message.split()) <= 2

            if not is_simple_message:
                logger.info(f"[Meeting Chat] Searching knowledge base for context...")
                # Increased from 5 to 10 chunks for more comprehensive context
                # Agents need thorough access to KB to find all relevant information
                kb_results = await asyncio.to_thread(
                    lambda: search_similar_chunks(
                        query=chat_request.message,
                        client_id=client_id,
                        limit=10,  # Increased from 5 to 10 for comprehensive KB coverage
                        min_similarity=0.0,  # Use adaptive threshold
                        include_conversations=True  # Include past conversation context
                    )
                )
                kb_context = kb_results
                logger.info(f"[Meeting Chat] Found {len(kb_context)} relevant KB chunks")
        except Exception as kb_err:
            # KB search is optional - don't fail the request if it errors
            logger.warning(f"[Meeting Chat] KB search failed (non-fatal): {kb_err}")

        # Retrieve Neo4j graph context (stakeholders, relationships, concerns)
        graph_context = {}
        try:
            if not is_simple_message:
                logger.info(f"[Meeting Chat] Fetching graph context from Neo4j...")
                from services.graph.connection import get_neo4j_connection
                from services.graph.query_service import GraphQueryService

                neo4j = await get_neo4j_connection()
                graph_service = GraphQueryService(neo4j)
                graph_context = await graph_service.get_meeting_context(
                    query=chat_request.message,
                    client_id=client_id,
                    limit=5
                )
                # Count non-empty results
                total_graph_items = (
                    len(graph_context.get("stakeholders", [])) +
                    len(graph_context.get("concerns", [])) +
                    len(graph_context.get("roi_opportunities", [])) +
                    len(graph_context.get("relationships", []))
                )
                logger.info(f"[Meeting Chat] Found {total_graph_items} graph context items")
        except Exception as graph_err:
            # Graph context is optional - don't fail the request if it errors
            logger.warning(f"[Meeting Chat] Graph context failed (non-fatal): {graph_err}")

        # Build meeting context
        logger.info(f"[Meeting Chat] Importing MeetingContext...")
        try:
            from services.meeting_orchestrator import MeetingContext
            logger.info(f"[Meeting Chat] MeetingContext imported successfully")
        except Exception as import_err:
            import traceback
            logger.error(f"[Meeting Chat] Failed to import MeetingContext: {import_err}\n{traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Import error: {str(import_err)}")

        meeting_context = MeetingContext(
            user_id=user_id,
            client_id=client_id,
            meeting_room_id=meeting_id,
            user_message=chat_request.message,
            message_history=message_history,
            participants=participants,
            meeting_type=meeting['meeting_type'],
            config=meeting['config'] or {},
            turn_number=turn_number,
            kb_context=kb_context,  # Vector search KB context (Voyage AI)
            graph_context=graph_context,  # Graph relationship context (Neo4j)
        )
        graph_items = len(graph_context.get("stakeholders", [])) + len(graph_context.get("concerns", []))
        logger.info(f"[Meeting Chat] MeetingContext created for turn {turn_number} with {len(kb_context)} KB chunks and {graph_items} graph items")

        # Get orchestrator and process the turn
        logger.info(f"[Meeting Chat] Getting orchestrator for meeting {meeting_id}")
        try:
            orchestrator = await get_orchestrator()
            logger.info(f"Orchestrator ready with agents: {list(orchestrator.agents.keys())}")
        except Exception as orch_err:
            import traceback
            logger.error(f"Failed to get orchestrator: {orch_err}\n{traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Orchestrator initialization failed: {str(orch_err)}")

        async def generate_stream():
            """Generate SSE stream from orchestrator."""
            try:
                # Emit context_sources event first so frontend can display what informed the response
                context_sources = {
                    "type": "context_sources",
                    "kb_sources": [],
                    "graph_sources": {
                        "stakeholders": [],
                        "concerns": [],
                        "roi_opportunities": [],
                        "relationships": []
                    }
                }

                # Format KB sources with document info
                for chunk in kb_context:
                    metadata = chunk.get('metadata', {})
                    source_info = {
                        "document_id": chunk.get('document_id'),
                        "similarity": round(chunk.get('similarity', 0), 3),
                        "source_type": chunk.get('source_type', 'document'),
                    }
                    # Add title/filename for display
                    if metadata.get('filename'):
                        source_info["title"] = metadata['filename']
                    elif metadata.get('conversation_title'):
                        source_info["title"] = metadata['conversation_title']
                    else:
                        source_info["title"] = "Unknown source"

                    context_sources["kb_sources"].append(source_info)

                # Format graph sources
                if graph_context:
                    for s in graph_context.get("stakeholders", [])[:5]:
                        context_sources["graph_sources"]["stakeholders"].append({
                            "name": s.get("name"),
                            "role": s.get("role"),
                            "sentiment": s.get("sentiment_score")
                        })
                    for c in graph_context.get("concerns", [])[:5]:
                        context_sources["graph_sources"]["concerns"].append({
                            "content": (c.get("content") or "")[:100],
                            "severity": c.get("severity")
                        })
                    for r in graph_context.get("roi_opportunities", [])[:3]:
                        context_sources["graph_sources"]["roi_opportunities"].append({
                            "name": r.get("name"),
                            "status": r.get("status")
                        })
                    for rel in graph_context.get("relationships", [])[:5]:
                        context_sources["graph_sources"]["relationships"].append({
                            "from": rel.get("from_name"),
                            "to": rel.get("to_name"),
                            "type": rel.get("relationship")
                        })

                # Only emit if there's actual context
                has_kb = len(context_sources["kb_sources"]) > 0
                has_graph = any(
                    len(v) > 0 for v in context_sources["graph_sources"].values()
                )
                if has_kb or has_graph:
                    yield f"data: {json.dumps(context_sources)}\n\n"

                async for event in orchestrator.process_meeting_turn(meeting_context):
                    yield f"data: {json.dumps(event)}\n\n"
            except Exception as e:
                import traceback
                logger.error(f"Meeting stream error: {e}\n{traceback.format_exc()}")
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error in meeting chat stream: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# AUTONOMOUS DISCUSSION ENDPOINTS
# ============================================================================

@router.post("/{meeting_id}/autonomous/start")
@limiter.limit("10/minute")
async def start_autonomous_discussion(
    request: Request,
    meeting_id: str,
    discussion_request: AutonomousDiscussionRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Start an autonomous discussion in a meeting room.
    Agents will discuss the provided topic for the specified number of rounds.

    Returns Server-Sent Events (SSE) with the following event types:
    - discussion_round_start: When a round begins
    - agent_turn_start: When an agent begins responding
    - agent_token: Individual tokens from agent response
    - agent_turn_end: When an agent finishes
    - discussion_round_end: When a round completes
    - discussion_complete: When all rounds are finished
    - discussion_paused: If user interjects or error occurs
    - error: If something goes wrong
    """
    try:
        validate_uuid(meeting_id, "meeting_id")
        user_id = current_user['id']
        client_id = get_default_client_id()

        # Verify meeting ownership and get meeting details
        meeting_result = await asyncio.to_thread(
            lambda: supabase.table('meeting_rooms')
                .select('*')
                .eq('id', meeting_id)
                .eq('user_id', user_id)
                .single()
                .execute()
        )

        if not meeting_result.data:
            raise HTTPException(status_code=404, detail="Meeting room not found")

        meeting = meeting_result.data

        # Check if autonomous discussion is already active
        config = meeting.get('config', {})
        autonomous = config.get('autonomous', {})
        if autonomous.get('is_active', False):
            raise HTTPException(
                status_code=400,
                detail="Autonomous discussion is already active in this meeting room"
            )

        # Get participants with agent details
        participants_result = await asyncio.to_thread(
            lambda: supabase.table('meeting_room_participants')
                .select('*, agents(id, name, display_name)')
                .eq('meeting_room_id', meeting_id)
                .order('priority')
                .execute()
        )

        participants = [
            {
                'id': p['id'],
                'agent_id': p['agent_id'],
                'agent_name': p['agents']['name'],
                'agent_display_name': p['agents']['display_name'],
                'role_description': p['role_description'],
                'priority': p['priority'],
            }
            for p in participants_result.data
        ]

        if len(participants) < 2:
            raise HTTPException(
                status_code=400,
                detail="At least 2 participants are required for autonomous discussion"
            )

        # Get recent message history for context
        messages_result = await asyncio.to_thread(
            lambda: supabase.table('meeting_room_messages')
                .select('*')
                .eq('meeting_room_id', meeting_id)
                .order('created_at', desc=False)
                .limit(20)  # Limited history for context
                .execute()
        )

        message_history = [
            {
                'role': m['role'],
                'content': m['content'],
                'agent_name': m['agent_name'],
                'agent_display_name': m['agent_display_name'],
            }
            for m in messages_result.data
        ]

        # Retrieve Knowledge Base context for the discussion topic
        kb_context = []
        try:
            logger.info(f"[Autonomous] Searching knowledge base for topic context...")
            # Increased from 5 to 10 chunks for comprehensive KB coverage
            kb_results = await asyncio.to_thread(
                lambda: search_similar_chunks(
                    query=discussion_request.topic,
                    client_id=client_id,
                    limit=10,  # Increased from 5 to 10 for comprehensive KB coverage
                    min_similarity=0.0,  # Use adaptive threshold
                    include_conversations=True
                )
            )
            kb_context = kb_results
            logger.info(f"[Autonomous] Found {len(kb_context)} relevant KB chunks for topic")
        except Exception as kb_err:
            logger.warning(f"[Autonomous] KB search failed (non-fatal): {kb_err}")

        # Retrieve Neo4j graph context for the discussion topic
        graph_context = {}
        try:
            logger.info(f"[Autonomous] Fetching graph context from Neo4j...")
            from services.graph.connection import get_neo4j_connection
            from services.graph.query_service import GraphQueryService

            neo4j = await get_neo4j_connection()
            graph_service = GraphQueryService(neo4j)
            graph_context = await graph_service.get_meeting_context(
                query=discussion_request.topic,
                client_id=client_id,
                limit=5
            )
            total_graph_items = (
                len(graph_context.get("stakeholders", [])) +
                len(graph_context.get("concerns", [])) +
                len(graph_context.get("roi_opportunities", []))
            )
            logger.info(f"[Autonomous] Found {total_graph_items} graph context items")
        except Exception as graph_err:
            logger.warning(f"[Autonomous] Graph context failed (non-fatal): {graph_err}")

        # Build meeting context
        from services.meeting_orchestrator import MeetingContext

        meeting_context = MeetingContext(
            user_id=user_id,
            client_id=client_id,
            meeting_room_id=meeting_id,
            user_message=discussion_request.topic,  # Topic becomes the initial message
            message_history=message_history,
            participants=participants,
            meeting_type=meeting['meeting_type'],
            config=meeting['config'] or {},
            turn_number=0,
            kb_context=kb_context,  # Vector search KB context (Voyage AI)
            graph_context=graph_context,  # Graph relationship context (Neo4j)
        )

        # Get orchestrator and process autonomous discussion
        orchestrator = await get_orchestrator()

        async def generate_stream():
            """Generate SSE stream from autonomous discussion."""
            try:
                # Emit context_sources event first so frontend can display what informed the discussion
                context_sources = {
                    "type": "context_sources",
                    "kb_sources": [],
                    "graph_sources": {
                        "stakeholders": [],
                        "concerns": [],
                        "roi_opportunities": [],
                        "relationships": []
                    }
                }

                # Format KB sources with document info
                for chunk in kb_context:
                    metadata = chunk.get('metadata', {})
                    source_info = {
                        "document_id": chunk.get('document_id'),
                        "similarity": round(chunk.get('similarity', 0), 3),
                        "source_type": chunk.get('source_type', 'document'),
                    }
                    if metadata.get('filename'):
                        source_info["title"] = metadata['filename']
                    elif metadata.get('conversation_title'):
                        source_info["title"] = metadata['conversation_title']
                    else:
                        source_info["title"] = "Unknown source"
                    context_sources["kb_sources"].append(source_info)

                # Format graph sources
                if graph_context:
                    for s in graph_context.get("stakeholders", [])[:5]:
                        context_sources["graph_sources"]["stakeholders"].append({
                            "name": s.get("name"),
                            "role": s.get("role"),
                            "sentiment": s.get("sentiment_score")
                        })
                    for c in graph_context.get("concerns", [])[:5]:
                        context_sources["graph_sources"]["concerns"].append({
                            "content": (c.get("content") or "")[:100],
                            "severity": c.get("severity")
                        })
                    for r in graph_context.get("roi_opportunities", [])[:3]:
                        context_sources["graph_sources"]["roi_opportunities"].append({
                            "name": r.get("name"),
                            "status": r.get("status")
                        })
                    for rel in graph_context.get("relationships", [])[:5]:
                        context_sources["graph_sources"]["relationships"].append({
                            "from": rel.get("from_name"),
                            "to": rel.get("to_name"),
                            "type": rel.get("relationship")
                        })

                # Only emit if there's actual context
                has_kb = len(context_sources["kb_sources"]) > 0
                has_graph = any(len(v) > 0 for v in context_sources["graph_sources"].values())
                if has_kb or has_graph:
                    yield f"data: {json.dumps(context_sources)}\n\n"

                async for event in orchestrator.process_autonomous_discussion(
                    context=meeting_context,
                    topic=discussion_request.topic,
                    total_rounds=discussion_request.rounds,
                    speaking_order=discussion_request.speaking_order
                ):
                    yield f"data: {json.dumps(event)}\n\n"
            except Exception as e:
                logger.error(f"Autonomous discussion stream error: {e}")
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting autonomous discussion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{meeting_id}/autonomous/stop")
async def stop_autonomous_discussion(
    meeting_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Stop an ongoing autonomous discussion."""
    try:
        validate_uuid(meeting_id, "meeting_id")
        user_id = current_user['id']

        # Verify meeting ownership
        meeting_result = await asyncio.to_thread(
            lambda: supabase.table('meeting_rooms')
                .select('id, config')
                .eq('id', meeting_id)
                .eq('user_id', user_id)
                .single()
                .execute()
        )

        if not meeting_result.data:
            raise HTTPException(status_code=404, detail="Meeting room not found")

        # Stop the discussion
        orchestrator = await get_orchestrator()
        await orchestrator.stop_autonomous_discussion(meeting_id)

        return {
            'success': True,
            'message': 'Autonomous discussion stopped'
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping autonomous discussion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{meeting_id}/autonomous/status")
async def get_autonomous_status(
    meeting_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get the current autonomous discussion status."""
    try:
        validate_uuid(meeting_id, "meeting_id")
        user_id = current_user['id']

        # Verify meeting ownership
        meeting_result = await asyncio.to_thread(
            lambda: supabase.table('meeting_rooms')
                .select('id')
                .eq('id', meeting_id)
                .eq('user_id', user_id)
                .single()
                .execute()
        )

        if not meeting_result.data:
            raise HTTPException(status_code=404, detail="Meeting room not found")

        # Get status from orchestrator
        orchestrator = await get_orchestrator()
        status = await orchestrator.get_autonomous_status(meeting_id)

        return {
            'success': True,
            'status': AutonomousDiscussionStatus(**status)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting autonomous status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{meeting_id}/chat/interject")
@limiter.limit("20/minute")
async def interject_in_discussion(
    request: Request,
    meeting_id: str,
    chat_request: MeetingChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Send a user message during an autonomous discussion.
    This will pause the discussion and mark the message as an interjection.
    """
    try:
        validate_uuid(meeting_id, "meeting_id")
        user_id = current_user['id']

        # Verify meeting ownership
        meeting_result = await asyncio.to_thread(
            lambda: supabase.table('meeting_rooms')
                .select('id, config')
                .eq('id', meeting_id)
                .eq('user_id', user_id)
                .single()
                .execute()
        )

        if not meeting_result.data:
            raise HTTPException(status_code=404, detail="Meeting room not found")

        # Store the user message with interjection flag
        await asyncio.to_thread(
            lambda: supabase.table('meeting_room_messages')
                .insert({
                    'meeting_room_id': meeting_id,
                    'role': 'user',
                    'content': chat_request.message,
                    'pending_interjection': True,
                    'metadata': {'interjection': True}
                })
                .execute()
        )

        return {
            'success': True,
            'message': 'Interjection sent. Discussion will pause after current agent finishes.'
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending interjection: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
