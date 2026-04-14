"""Meeting Room routes.

Handles creation, management, and chat for multi-agent meeting rooms.
"""

import json
import os
from datetime import datetime, timezone
from typing import Optional

from anthropic import Anthropic
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

import pb_client as pb
from repositories.agents import get_agent, list_agents
from repositories.meetings import (
    get_meeting_room,
    create_meeting_room as repo_create_meeting_room,
    update_meeting_room as repo_update_meeting_room,
    delete_meeting_room as repo_delete_meeting_room,
    get_room_messages,
    create_room_message,
    get_room_participants,
    add_room_participant,
    remove_room_participant,
)
from document_processor import search_similar_chunks
from logger_config import get_logger
from validation import validate_uuid

from ..models.meeting_rooms import (
    AutonomousDiscussionRequest,
    AutonomousDiscussionStatus,
    MeetingChatRequest,
    MeetingMessageResponse,
    MeetingRoomCreateRequest,
    MeetingRoomListResponse,
    MeetingRoomResponse,
    MeetingRoomUpdateRequest,
    ParticipantAddRequest,
    ParticipantResponse,
    ParticipantUpdateRequest,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/api/meeting-rooms", tags=["meeting-rooms"])
limiter = Limiter(key_func=get_remote_address)

# Initialize Anthropic client
anthropic_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# Global orchestrator instance (initialized lazily)
_meeting_orchestrator = None


# ============================================================================
# MEETING ROOM CRUD OPERATIONS
# ============================================================================


@router.post("")
async def create_meeting_room(request: MeetingRoomCreateRequest):
    """Create a new meeting room with selected agent participants."""
    try:
        # Validate all agent IDs exist and are active
        agent_ids = request.participant_agent_ids
        found_agents = {}
        missing_agents = []
        for aid in agent_ids:
            a = get_agent(aid)
            if a and a.get("is_active"):
                found_agents[aid] = a
            else:
                missing_agents.append(aid)

        if missing_agents:
            raise HTTPException(status_code=400, detail=f"Invalid or inactive agent IDs: {missing_agents}")

        # Validate project_id and initiative_id if provided
        if request.project_id:
            validate_uuid(request.project_id, "project_id")
        if request.initiative_id:
            validate_uuid(request.initiative_id, "initiative_id")

        # Create the meeting room
        meeting_data = {
            "title": request.title,
            "description": request.description,
            "meeting_type": request.meeting_type,
            "status": "active",
            "config": request.config or {},
        }

        # Add context fields if provided
        if request.project_id:
            meeting_data["project_id"] = request.project_id
        if request.initiative_id:
            meeting_data["initiative_id"] = request.initiative_id

        meeting = repo_create_meeting_room(meeting_data)
        meeting_id = meeting["id"]
        logger.info(f"Created meeting room: {meeting_id}")

        # Add participants
        for idx, agent_id in enumerate(agent_ids):
            add_room_participant(
                {
                    "meeting_room_id": meeting_id,
                    "agent_id": agent_id,
                    "priority": idx,
                }
            )

        logger.info(f"Added {len(agent_ids)} participants to meeting {meeting_id}")

        # Build response with participant details
        participants = [
            ParticipantResponse(
                id=str(idx),  # Temporary ID
                agent_id=agent_id,
                agent_name=found_agents[agent_id]["name"],
                agent_display_name=found_agents[agent_id]["display_name"],
                role_description=None,
                priority=idx,
                turns_taken=0,
                tokens_used=0,
                created_at=datetime.now(timezone.utc),
            )
            for idx, agent_id in enumerate(agent_ids)
        ]

        return {
            "success": True,
            "meeting_room": MeetingRoomResponse(
                id=meeting["id"],
                client_id=meeting.get("client_id", ""),
                user_id=meeting.get("user_id", ""),
                title=meeting["title"],
                description=meeting.get("description"),
                meeting_type=meeting["meeting_type"],
                status=meeting["status"],
                config=meeting.get("config", {}),
                total_tokens_used=meeting.get("total_tokens_used", 0),
                created_at=meeting.get("created", ""),
                updated_at=meeting.get("updated", ""),
                participants=participants,
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating meeting room: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("")
async def list_meeting_rooms(
    status: Optional[str] = None,
    meeting_type: Optional[str] = None,
    project_id: Optional[str] = None,
    initiative_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """List meeting rooms.

    Supports filtering by project_id and/or initiative_id for context-scoped views.
    """
    try:
        # Validate context IDs if provided
        if project_id:
            validate_uuid(project_id, "project_id")
        if initiative_id:
            validate_uuid(initiative_id, "initiative_id")

        # Build filter
        parts = []
        if status:
            parts.append(f"status='{pb.escape_filter(status)}'")
        if meeting_type:
            parts.append(f"meeting_type='{pb.escape_filter(meeting_type)}'")
        if project_id:
            parts.append(f"project_id='{pb.escape_filter(project_id)}'")
        if initiative_id:
            parts.append(f"initiative_id='{pb.escape_filter(initiative_id)}'")
        filter_str = " && ".join(parts)

        page = (offset // limit) + 1 if limit else 1
        result = pb.list_records(
            "meeting_rooms",
            filter=filter_str,
            sort="-updated",
            page=page,
            per_page=limit,
        )

        meetings = result.get("items", [])
        total_count = result.get("totalItems", 0)

        # Get participant counts for all meetings
        if meetings:
            for meeting in meetings:
                participants = get_room_participants(meeting["id"])
                meeting["participant_count"] = len(participants)

        return {
            "success": True,
            "meeting_rooms": [
                MeetingRoomListResponse(
                    id=m["id"],
                    title=m["title"],
                    description=m.get("description"),
                    meeting_type=m["meeting_type"],
                    status=m["status"],
                    total_tokens_used=m.get("total_tokens_used", 0),
                    participant_count=m.get("participant_count", 0),
                    autonomous_topic=m.get("config", {}).get("autonomous", {}).get("topic") if isinstance(m.get("config"), dict) else None,
                    created_at=m.get("created", ""),
                    updated_at=m.get("updated", ""),
                )
                for m in meetings
            ],
            "total": total_count,
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        logger.error(f"Error listing meeting rooms: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/{meeting_id}")
async def get_meeting_room_endpoint(meeting_id: str):
    """Get meeting room details with participants."""
    try:
        validate_uuid(meeting_id, "meeting_id")

        # Get meeting room
        meeting = get_meeting_room(meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting room not found")

        # Get participants with agent details (separate lookups)
        raw_participants = get_room_participants(meeting_id)
        participants = []
        for p in raw_participants:
            agent = get_agent(p["agent_id"]) if p.get("agent_id") else None
            if agent:
                participants.append(
                    ParticipantResponse(
                        id=p["id"],
                        agent_id=p["agent_id"],
                        agent_name=agent["name"],
                        agent_display_name=agent["display_name"],
                        role_description=p.get("role_description"),
                        priority=p.get("priority", 0),
                        turns_taken=p.get("turns_taken", 0),
                        tokens_used=p.get("tokens_used", 0),
                        created_at=p.get("created", ""),
                    )
                )

        return {
            "success": True,
            "meeting_room": MeetingRoomResponse(
                id=meeting["id"],
                client_id=meeting.get("client_id", ""),
                user_id=meeting.get("user_id", ""),
                title=meeting["title"],
                description=meeting.get("description"),
                meeting_type=meeting["meeting_type"],
                status=meeting["status"],
                config=meeting.get("config", {}),
                total_tokens_used=meeting.get("total_tokens_used", 0),
                created_at=meeting.get("created", ""),
                updated_at=meeting.get("updated", ""),
                participants=participants,
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting meeting room: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.patch("/{meeting_id}")
async def update_meeting_room(
    meeting_id: str,
    request: MeetingRoomUpdateRequest,
):
    """Update meeting room details."""
    try:
        validate_uuid(meeting_id, "meeting_id")

        # Build update data
        update_data = {}
        if request.title is not None:
            update_data["title"] = request.title
        if request.description is not None:
            update_data["description"] = request.description
        if request.status is not None:
            update_data["status"] = request.status
        if request.config is not None:
            update_data["config"] = request.config

        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        # Verify meeting exists
        existing = get_meeting_room(meeting_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Meeting room not found")

        result = repo_update_meeting_room(meeting_id, update_data)

        return {"success": True, "meeting_room": result}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating meeting room: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.delete("/{meeting_id}")
async def delete_meeting_room(meeting_id: str):
    """Delete a meeting room and all its messages."""
    try:
        validate_uuid(meeting_id, "meeting_id")

        # Verify meeting exists
        existing = get_meeting_room(meeting_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Meeting room not found")

        # Delete meeting (cascades to participants and messages)
        repo_delete_meeting_room(meeting_id)

        logger.info(f"Deleted meeting room: {meeting_id}")

        return {"success": True, "message": "Meeting room deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting meeting room: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# PARTICIPANT MANAGEMENT
# ============================================================================


@router.post("/{meeting_id}/participants")
async def add_participant(
    meeting_id: str, request: ParticipantAddRequest,
):
    """Add a participant to an existing meeting."""
    try:
        validate_uuid(meeting_id, "meeting_id")
        validate_uuid(request.agent_id, "agent_id")

        # Verify meeting exists
        meeting = get_meeting_room(meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting room not found")

        # Verify agent exists and is active
        agent = get_agent(request.agent_id)
        if not agent or not agent.get("is_active"):
            raise HTTPException(status_code=400, detail="Invalid or inactive agent")

        # Add participant
        participant = add_room_participant(
            {
                "meeting_room_id": meeting_id,
                "agent_id": request.agent_id,
                "role_description": request.role_description,
                "priority": request.priority,
            }
        )

        return {
            "success": True,
            "participant": ParticipantResponse(
                id=participant["id"],
                agent_id=participant["agent_id"],
                agent_name=agent["name"],
                agent_display_name=agent["display_name"],
                role_description=participant.get("role_description"),
                priority=participant.get("priority", 0),
                turns_taken=0,
                tokens_used=0,
                created_at=participant.get("created", ""),
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding participant: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.patch("/{meeting_id}/participants/{participant_id}")
async def update_participant(
    meeting_id: str,
    participant_id: str,
    request: ParticipantUpdateRequest,
):
    """Update a participant's configuration."""
    try:
        validate_uuid(meeting_id, "meeting_id")
        validate_uuid(participant_id, "participant_id")

        # Verify meeting exists
        meeting = get_meeting_room(meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting room not found")

        # Build update data
        update_data = {}
        if request.role_description is not None:
            update_data["role_description"] = request.role_description
        if request.priority is not None:
            update_data["priority"] = request.priority

        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        # Verify participant exists
        existing = pb.get_record("meeting_room_participants", participant_id)
        if not existing or existing.get("meeting_room_id") != meeting_id:
            raise HTTPException(status_code=404, detail="Participant not found")

        result = pb.update_record("meeting_room_participants", participant_id, update_data)

        return {"success": True, "participant": result}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating participant: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.delete("/{meeting_id}/participants/{participant_id}")
async def remove_participant_endpoint(meeting_id: str, participant_id: str):
    """Remove a participant from a meeting."""
    try:
        validate_uuid(meeting_id, "meeting_id")
        validate_uuid(participant_id, "participant_id")

        # Verify meeting exists
        meeting = get_meeting_room(meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting room not found")

        # Check we're not removing below minimum participants
        participants = get_room_participants(meeting_id)
        if len(participants) <= 2:
            raise HTTPException(
                status_code=400,
                detail="Cannot remove participant: meeting requires at least 2 agents",
            )

        # Verify participant exists
        existing = pb.get_record("meeting_room_participants", participant_id)
        if not existing or existing.get("meeting_room_id") != meeting_id:
            raise HTTPException(status_code=404, detail="Participant not found")

        # Remove participant
        remove_room_participant(participant_id)

        return {"success": True, "message": "Participant removed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing participant: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# MESSAGE RETRIEVAL
# ============================================================================


@router.get("/{meeting_id}/messages")
async def get_meeting_messages(
    meeting_id: str,
    limit: int = 100,
    offset: int = 0,
):
    """Get messages from a meeting room."""
    try:
        validate_uuid(meeting_id, "meeting_id")

        # Verify meeting exists
        meeting = get_meeting_room(meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting room not found")

        # Get messages
        page = (offset // limit) + 1 if limit else 1
        result = pb.list_records(
            "meeting_room_messages",
            filter=f"meeting_room_id='{pb.escape_filter(meeting_id)}'",
            sort="created",
            page=page,
            per_page=limit,
        )

        items = result.get("items", [])
        total_count = result.get("totalItems", 0)

        messages = [
            MeetingMessageResponse(
                id=m["id"],
                meeting_room_id=m["meeting_room_id"],
                role=m["role"],
                agent_id=m.get("agent_id"),
                agent_name=m.get("agent_name"),
                agent_display_name=m.get("agent_display_name"),
                content=m["content"],
                metadata=m.get("metadata") or {},
                turn_number=m.get("turn_number"),
                created_at=m.get("created", ""),
            )
            for m in items
        ]

        return {
            "success": True,
            "messages": messages,
            "total_count": total_count,
            "has_more": (offset + limit) < total_count,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting meeting messages: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# STREAMING CHAT ENDPOINT
# ============================================================================


async def get_orchestrator():
    """Get or initialize the meeting orchestrator."""
    global _meeting_orchestrator
    if _meeting_orchestrator is None:
        from services.meeting_orchestrator import get_meeting_orchestrator

        # NOTE: services will be rewritten later; passing None for supabase
        _meeting_orchestrator = await get_meeting_orchestrator(None, anthropic_client)
    return _meeting_orchestrator


@router.post("/{meeting_id}/chat/stream")
@limiter.limit("20/minute")
async def stream_meeting_chat(
    request: Request,
    meeting_id: str,
    chat_request: MeetingChatRequest,
):
    """Send a message in a meeting room and stream responses from agents.

    Returns Server-Sent Events (SSE) with the following event types:
    - agent_turn_start: When an agent begins responding
    - agent_token: Individual tokens from agent response
    - agent_turn_end: When an agent finishes
    - round_complete: When all agents have responded
    - error: If something goes wrong
    """
    logger.info(f"[Meeting Chat] === ENTERING stream_meeting_chat for {meeting_id} ===")

    try:
        validate_uuid(meeting_id, "meeting_id")

        logger.info(f"[Meeting Chat] Starting for meeting {meeting_id}")

        # Get meeting room
        meeting = get_meeting_room(meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting room not found")

        logger.info(f"[Meeting Chat] Found meeting: {meeting.get('title', 'Unknown')}")

        # Get participants with agent details (separate lookups)
        raw_participants = get_room_participants(meeting_id)
        participants = []
        for p in raw_participants:
            agent = get_agent(p["agent_id"]) if p.get("agent_id") else None
            if agent:
                participants.append(
                    {
                        "id": p["id"],
                        "agent_id": p["agent_id"],
                        "agent_name": agent["name"],
                        "agent_display_name": agent["display_name"],
                        "role_description": p.get("role_description"),
                        "priority": p.get("priority", 0),
                    }
                )

        if not participants:
            raise HTTPException(status_code=400, detail="No participants in meeting")

        logger.info(
            f"Meeting {meeting_id} has {len(participants)} participants: {[p['agent_name'] for p in participants]}"
        )

        # Get message history
        all_messages = get_room_messages(meeting_id)
        # Limit to last 50 messages
        recent_messages = all_messages[-50:] if len(all_messages) > 50 else all_messages

        message_history = [
            {
                "role": m.get("role", "user"),
                "content": m.get("content", ""),
                "agent_name": m.get("agent_name"),
                "agent_display_name": m.get("agent_display_name"),
            }
            for m in recent_messages
        ]

        logger.info(f"[Meeting Chat] Found {len(message_history)} messages in history")

        # Calculate turn number
        turn_number = len([m for m in recent_messages if m.get("role") == "user"]) + 1

        # Retrieve Knowledge Base context for the user's message
        kb_context = []
        try:
            simple_messages = {
                "hello", "hi", "hey", "greetings", "good morning",
                "good afternoon", "good evening", "howdy", "yo", "sup",
                "thanks", "thank you", "bye",
            }
            message_lower = chat_request.message.lower().strip()
            is_simple_message = message_lower in simple_messages or len(chat_request.message.split()) <= 2

            if not is_simple_message:
                logger.info("[Meeting Chat] Searching knowledge base for context...")
                kb_results = search_similar_chunks(
                    query=chat_request.message,
                    client_id="system",
                    limit=10,
                    min_similarity=0.0,
                    include_conversations=True,
                )
                kb_context = kb_results
                logger.info(f"[Meeting Chat] Found {len(kb_context)} relevant KB chunks")
        except Exception as kb_err:
            logger.warning(f"[Meeting Chat] KB search failed (non-fatal): {kb_err}")

        # Retrieve Neo4j graph context (stakeholders, relationships, concerns)
        graph_context = {}
        try:
            if not is_simple_message:
                logger.info("[Meeting Chat] Fetching graph context from Neo4j...")
                from services.graph.connection import get_neo4j_connection
                from services.graph.query_service import GraphQueryService

                neo4j = await get_neo4j_connection()
                graph_service = GraphQueryService(neo4j)
                graph_context = await graph_service.get_meeting_context(
                    query=chat_request.message, client_id="system", limit=5
                )
                total_graph_items = (
                    len(graph_context.get("stakeholders", []))
                    + len(graph_context.get("concerns", []))
                    + len(graph_context.get("roi_opportunities", []))
                    + len(graph_context.get("relationships", []))
                )
                logger.info(f"[Meeting Chat] Found {total_graph_items} graph context items")
        except Exception as graph_err:
            logger.warning(f"[Meeting Chat] Graph context failed (non-fatal): {graph_err}")

        # Build meeting context
        logger.info("[Meeting Chat] Importing MeetingContext...")
        try:
            from services.meeting_orchestrator import MeetingContext

            logger.info("[Meeting Chat] MeetingContext imported successfully")
        except Exception as import_err:
            import traceback

            logger.error(f"[Meeting Chat] Failed to import MeetingContext: {import_err}\n{traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Import error: {str(import_err)}") from None

        meeting_context = MeetingContext(
            user_id="system",
            client_id="system",
            meeting_room_id=meeting_id,
            user_message=chat_request.message,
            message_history=message_history,
            participants=participants,
            meeting_type=meeting["meeting_type"],
            config=meeting.get("config") or {},
            turn_number=turn_number,
            kb_context=kb_context,
            graph_context=graph_context,
        )
        graph_items = len(graph_context.get("stakeholders", [])) + len(graph_context.get("concerns", []))
        logger.info(
            f"[Meeting Chat] MeetingContext created for turn {turn_number} with {len(kb_context)} KB chunks and {graph_items} graph items"
        )

        # Get orchestrator and process the turn
        logger.info(f"[Meeting Chat] Getting orchestrator for meeting {meeting_id}")
        try:
            orchestrator = await get_orchestrator()
            logger.info(f"Orchestrator ready with agents: {list(orchestrator.agents.keys())}")
        except Exception as orch_err:
            import traceback

            logger.error(f"Failed to get orchestrator: {orch_err}\n{traceback.format_exc()}")
            raise HTTPException(
                status_code=500, detail=f"Orchestrator initialization failed: {str(orch_err)}"
            ) from None

        async def generate_stream():
            """Generate SSE stream from orchestrator."""
            try:
                # Emit context_sources event first
                context_sources = {
                    "type": "context_sources",
                    "kb_sources": [],
                    "graph_sources": {
                        "stakeholders": [],
                        "concerns": [],
                        "roi_opportunities": [],
                        "relationships": [],
                    },
                }

                # Format KB sources (deduplicated by document_id)
                seen_docs = {}
                for chunk in kb_context:
                    doc_id = chunk.get("document_id")
                    similarity = chunk.get("similarity", 0)
                    if doc_id in seen_docs and seen_docs[doc_id]["similarity"] >= similarity:
                        continue
                    metadata = chunk.get("metadata", {})
                    source_info = {
                        "document_id": doc_id,
                        "similarity": round(similarity, 3),
                        "source_type": chunk.get("source_type", "document"),
                    }
                    if metadata.get("filename"):
                        source_info["title"] = metadata["filename"]
                    elif metadata.get("conversation_title"):
                        source_info["title"] = metadata["conversation_title"]
                    else:
                        source_info["title"] = "Unknown source"
                    seen_docs[doc_id] = source_info

                context_sources["kb_sources"] = sorted(seen_docs.values(), key=lambda x: x["similarity"], reverse=True)

                # Format graph sources
                if graph_context:
                    for s in graph_context.get("stakeholders", [])[:5]:
                        context_sources["graph_sources"]["stakeholders"].append(
                            {"name": s.get("name"), "role": s.get("role"), "sentiment": s.get("sentiment_score")}
                        )
                    for c in graph_context.get("concerns", [])[:5]:
                        context_sources["graph_sources"]["concerns"].append(
                            {"content": (c.get("content") or "")[:100], "severity": c.get("severity")}
                        )
                    for r in graph_context.get("roi_opportunities", [])[:3]:
                        context_sources["graph_sources"]["roi_opportunities"].append(
                            {"name": r.get("name"), "status": r.get("status")}
                        )
                    for rel in graph_context.get("relationships", [])[:5]:
                        context_sources["graph_sources"]["relationships"].append(
                            {"from": rel.get("from_name"), "to": rel.get("to_name"), "type": rel.get("relationship")}
                        )

                has_kb = len(context_sources["kb_sources"]) > 0
                has_graph = any(len(v) > 0 for v in context_sources["graph_sources"].values())
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
                "X-Accel-Buffering": "no",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback

        logger.error(f"Error in meeting chat stream: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# AUTONOMOUS DISCUSSION ENDPOINTS
# ============================================================================


@router.post("/{meeting_id}/autonomous/start")
@limiter.limit("10/minute")
async def start_autonomous_discussion(
    request: Request,
    meeting_id: str,
    discussion_request: AutonomousDiscussionRequest,
):
    """Start an autonomous discussion in a meeting room."""
    try:
        validate_uuid(meeting_id, "meeting_id")

        # Get meeting details
        meeting = get_meeting_room(meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting room not found")

        # Check if autonomous discussion is already active
        config = meeting.get("config", {})
        if isinstance(config, dict):
            autonomous = config.get("autonomous", {})
            if autonomous.get("is_active", False):
                raise HTTPException(
                    status_code=400,
                    detail="Autonomous discussion is already active in this meeting room",
                )

        # Get participants with agent details
        raw_participants = get_room_participants(meeting_id)
        participants = []
        for p in raw_participants:
            agent = get_agent(p["agent_id"]) if p.get("agent_id") else None
            if agent:
                participants.append(
                    {
                        "id": p["id"],
                        "agent_id": p["agent_id"],
                        "agent_name": agent["name"],
                        "agent_display_name": agent["display_name"],
                        "role_description": p.get("role_description"),
                        "priority": p.get("priority", 0),
                    }
                )

        if len(participants) < 2:
            raise HTTPException(
                status_code=400,
                detail="At least 2 participants are required for autonomous discussion",
            )

        # Get recent message history for context
        all_messages = get_room_messages(meeting_id)
        recent_messages = all_messages[-20:] if len(all_messages) > 20 else all_messages

        message_history = [
            {
                "role": m["role"],
                "content": m["content"],
                "agent_name": m.get("agent_name"),
                "agent_display_name": m.get("agent_display_name"),
            }
            for m in recent_messages
        ]

        # Retrieve Knowledge Base context for the discussion topic
        kb_context = []
        try:
            logger.info("[Autonomous] Searching knowledge base for topic context...")
            kb_results = search_similar_chunks(
                query=discussion_request.topic,
                client_id="system",
                limit=10,
                min_similarity=0.0,
                include_conversations=True,
            )
            kb_context = kb_results
            logger.info(f"[Autonomous] Found {len(kb_context)} relevant KB chunks for topic")
        except Exception as kb_err:
            logger.warning(f"[Autonomous] KB search failed (non-fatal): {kb_err}")

        # Retrieve Neo4j graph context for the discussion topic
        graph_context = {}
        try:
            logger.info("[Autonomous] Fetching graph context from Neo4j...")
            from services.graph.connection import get_neo4j_connection
            from services.graph.query_service import GraphQueryService

            neo4j = await get_neo4j_connection()
            graph_service = GraphQueryService(neo4j)
            graph_context = await graph_service.get_meeting_context(
                query=discussion_request.topic, client_id="system", limit=5
            )
            total_graph_items = (
                len(graph_context.get("stakeholders", []))
                + len(graph_context.get("concerns", []))
                + len(graph_context.get("roi_opportunities", []))
            )
            logger.info(f"[Autonomous] Found {total_graph_items} graph context items")
        except Exception as graph_err:
            logger.warning(f"[Autonomous] Graph context failed (non-fatal): {graph_err}")

        # Build meeting context
        from services.meeting_orchestrator import MeetingContext

        meeting_context = MeetingContext(
            user_id="system",
            client_id="system",
            meeting_room_id=meeting_id,
            user_message=discussion_request.topic,
            message_history=message_history,
            participants=participants,
            meeting_type=meeting["meeting_type"],
            config=meeting.get("config") or {},
            turn_number=0,
            kb_context=kb_context,
            graph_context=graph_context,
        )

        # Get orchestrator and process autonomous discussion
        orchestrator = await get_orchestrator()

        async def generate_stream():
            """Generate SSE stream from autonomous discussion."""
            try:
                # Emit context_sources event first
                context_sources = {
                    "type": "context_sources",
                    "kb_sources": [],
                    "graph_sources": {
                        "stakeholders": [],
                        "concerns": [],
                        "roi_opportunities": [],
                        "relationships": [],
                    },
                }

                seen_docs = {}
                for chunk in kb_context:
                    doc_id = chunk.get("document_id")
                    similarity = chunk.get("similarity", 0)
                    if doc_id in seen_docs and seen_docs[doc_id]["similarity"] >= similarity:
                        continue
                    metadata = chunk.get("metadata", {})
                    source_info = {
                        "document_id": doc_id,
                        "similarity": round(similarity, 3),
                        "source_type": chunk.get("source_type", "document"),
                    }
                    if metadata.get("filename"):
                        source_info["title"] = metadata["filename"]
                    elif metadata.get("conversation_title"):
                        source_info["title"] = metadata["conversation_title"]
                    else:
                        source_info["title"] = "Unknown source"
                    seen_docs[doc_id] = source_info

                context_sources["kb_sources"] = sorted(seen_docs.values(), key=lambda x: x["similarity"], reverse=True)

                if graph_context:
                    for s in graph_context.get("stakeholders", [])[:5]:
                        context_sources["graph_sources"]["stakeholders"].append(
                            {"name": s.get("name"), "role": s.get("role"), "sentiment": s.get("sentiment_score")}
                        )
                    for c_item in graph_context.get("concerns", [])[:5]:
                        context_sources["graph_sources"]["concerns"].append(
                            {"content": (c_item.get("content") or "")[:100], "severity": c_item.get("severity")}
                        )
                    for r in graph_context.get("roi_opportunities", [])[:3]:
                        context_sources["graph_sources"]["roi_opportunities"].append(
                            {"name": r.get("name"), "status": r.get("status")}
                        )
                    for rel in graph_context.get("relationships", [])[:5]:
                        context_sources["graph_sources"]["relationships"].append(
                            {"from": rel.get("from_name"), "to": rel.get("to_name"), "type": rel.get("relationship")}
                        )

                has_kb = len(context_sources["kb_sources"]) > 0
                has_graph = any(len(v) > 0 for v in context_sources["graph_sources"].values())
                if has_kb or has_graph:
                    yield f"data: {json.dumps(context_sources)}\n\n"

                async for event in orchestrator.process_autonomous_discussion(
                    context=meeting_context,
                    topic=discussion_request.topic,
                    total_rounds=discussion_request.rounds,
                    speaking_order=discussion_request.speaking_order,
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
                "X-Accel-Buffering": "no",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting autonomous discussion: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/{meeting_id}/autonomous/stop")
async def stop_autonomous_discussion(meeting_id: str):
    """Stop an ongoing autonomous discussion."""
    try:
        validate_uuid(meeting_id, "meeting_id")

        # Verify meeting exists
        meeting = get_meeting_room(meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting room not found")

        # Stop the discussion
        orchestrator = await get_orchestrator()
        await orchestrator.stop_autonomous_discussion(meeting_id)

        return {"success": True, "message": "Autonomous discussion stopped"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping autonomous discussion: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/{meeting_id}/autonomous/status")
async def get_autonomous_status(meeting_id: str):
    """Get the current autonomous discussion status."""
    try:
        validate_uuid(meeting_id, "meeting_id")

        # Verify meeting exists
        meeting = get_meeting_room(meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting room not found")

        # Get status from orchestrator
        orchestrator = await get_orchestrator()
        status = await orchestrator.get_autonomous_status(meeting_id)

        return {"success": True, "status": AutonomousDiscussionStatus(**status)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting autonomous status: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/{meeting_id}/chat/interject")
@limiter.limit("20/minute")
async def interject_in_discussion(
    request: Request,
    meeting_id: str,
    chat_request: MeetingChatRequest,
):
    """Send a user message during an autonomous discussion.

    This will pause the discussion and mark the message as an interjection.
    """
    try:
        validate_uuid(meeting_id, "meeting_id")

        # Verify meeting exists
        meeting = get_meeting_room(meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting room not found")

        # Store the user message with interjection flag
        create_room_message(
            {
                "meeting_room_id": meeting_id,
                "role": "user",
                "content": chat_request.message,
                "pending_interjection": True,
                "metadata": {"interjection": True},
            }
        )

        return {
            "success": True,
            "message": "Interjection sent. Discussion will pause after current agent finishes.",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending interjection: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e
