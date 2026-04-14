"""Graph Sync Service.

Synchronizes data from Supabase (source of truth) to Neo4j (graph layer).
Handles stakeholders, meetings, insights, documents, and relationships.
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

import pb_client as pb
from repositories import (
    agents as agents_repo,
    conversations as conversations_repo,
    documents as documents_repo,
    stakeholders as stakeholders_repo,
)

from .connection import Neo4jConnection
from .schema import CYPHER_TEMPLATES

logger = logging.getLogger(__name__)


class GraphSyncService:
    """Service for synchronizing Supabase data to Neo4j.

    Supports both full sync and incremental sync operations.
    Tracks sync state to enable efficient incremental updates.
    """

    def __init__(self, supabase=None, neo4j: Neo4jConnection = None):
        """Initialize the sync service.

        Args:
            supabase: Deprecated, ignored. Kept for call-site compatibility.
            neo4j: Neo4j connection for writing graph data
        """
        self.neo4j = neo4j

    async def full_sync(self, client_id: str) -> dict:
        """Perform a full sync of all entities for a client.

        Syncs ALL platform data including:
        - Core: clients, users, agents, documents, chunks
        - Conversations: conversations, messages
        - Meetings: transcripts, meeting rooms, room messages
        - Stakeholders: stakeholders, insights, concerns
        - Business: ROI opportunities
        - Knowledge: agent KB links, agent handoffs

        Args:
            client_id: The client ID to sync

        Returns:
            Dict with sync statistics
        """
        logger.info(f"Starting FULL sync for client {client_id}")
        start_time = datetime.now(timezone.utc)

        results = {
            "client_id": client_id,
            "started_at": start_time.isoformat(),
            # Core entities
            "client": {"synced": 0, "errors": 0},
            "users": {"synced": 0, "errors": 0},
            "agents": {"synced": 0, "errors": 0},
            "documents": {"synced": 0, "errors": 0},
            "chunks": {"synced": 0, "errors": 0},
            # Conversations
            "conversations": {"synced": 0, "errors": 0},
            "messages": {"synced": 0, "errors": 0},
            # Meetings
            "meetings": {"synced": 0, "errors": 0},
            "meeting_rooms": {"synced": 0, "errors": 0},
            "meeting_room_messages": {"synced": 0, "errors": 0},
            # Stakeholders
            "stakeholders": {"synced": 0, "errors": 0},
            "insights": {"synced": 0, "errors": 0},
            # Business
            "roi_opportunities": {"synced": 0, "errors": 0},
            # Knowledge
            "agent_knowledge_base": {"synced": 0, "errors": 0},
            "agent_handoffs": {"synced": 0, "errors": 0},
            # Stakeholder-Document relationships
            "stakeholder_documents": {
                "name_matches": 0,
                "department_matches": 0,
                "mentions_found": 0,
                "errors": 0,
            },
            # Relationships
            "relationships": {"created": 0, "errors": 0},
        }

        try:
            # Phase 1: Core entities (no dependencies)
            logger.info("Phase 1: Syncing core entities...")
            results["client"] = await self.sync_client(client_id)
            results["agents"] = await self.sync_agents()
            results["users"] = await self.sync_users(client_id)

            # Phase 2: Documents and chunks
            logger.info("Phase 2: Syncing documents...")
            results["documents"] = await self.sync_documents(client_id)
            results["chunks"] = await self.sync_document_chunks(client_id)

            # Phase 3: Conversations and messages
            logger.info("Phase 3: Syncing conversations...")
            results["conversations"] = await self.sync_conversations(client_id)
            results["messages"] = await self.sync_messages(client_id)

            # Phase 4: Meetings
            logger.info("Phase 4: Syncing meetings...")
            results["meetings"] = await self.sync_meetings(client_id)
            results["meeting_rooms"] = await self.sync_meeting_rooms(client_id)
            results["meeting_room_messages"] = await self.sync_meeting_room_messages(client_id)

            # Phase 5: Stakeholders and insights
            logger.info("Phase 5: Syncing stakeholders...")
            results["stakeholders"] = await self.sync_stakeholders(client_id)
            results["insights"] = await self.sync_insights(client_id)

            # Phase 6: Business entities
            logger.info("Phase 6: Syncing business entities...")
            results["roi_opportunities"] = await self.sync_roi_opportunities(client_id)

            # Phase 7: Knowledge graph links
            logger.info("Phase 7: Syncing knowledge links...")
            results["agent_knowledge_base"] = await self.sync_agent_knowledge_base()
            results["agent_handoffs"] = await self.sync_agent_handoffs(client_id)

            # Phase 8: Stakeholder-document relationships
            logger.info("Phase 8: Syncing stakeholder-document relationships...")
            doc_rel_result = await self.sync_stakeholder_document_relationships(client_id)
            chunk_mention_result = await self.sync_stakeholder_mentions_in_chunks(client_id)
            results["stakeholder_documents"] = {
                "name_matches": doc_rel_result.get("name_matches", 0),
                "department_matches": doc_rel_result.get("department_matches", 0),
                "mentions_found": chunk_mention_result.get("mentions_found", 0),
                "errors": doc_rel_result.get("errors", 0) + chunk_mention_result.get("errors", 0),
            }

            # Log sync completion
            await self._log_sync(client_id, "full", results)

        except Exception as e:
            logger.error(f"Full sync failed for client {client_id}: {e}")
            results["error"] = str(e)

        results["completed_at"] = datetime.now(timezone.utc).isoformat()
        results["duration_seconds"] = (datetime.now(timezone.utc) - start_time).total_seconds()

        # Calculate totals
        total_synced = sum(v.get("synced", 0) for k, v in results.items() if isinstance(v, dict) and "synced" in v)
        total_errors = sum(v.get("errors", 0) for k, v in results.items() if isinstance(v, dict) and "errors" in v)
        results["totals"] = {"synced": total_synced, "errors": total_errors}

        logger.info(f"Full sync completed: {total_synced} entities synced, {total_errors} errors")
        return results

    # ==========================================================================
    # Core Entity Sync Methods
    # ==========================================================================

    async def sync_client(self, client_id: str) -> dict:
        """Sync a single client to Neo4j.

        Args:
            client_id: The client ID to sync

        Returns:
            Dict with sync counts
        """
        result = {"synced": 0, "errors": 0}

        try:
            client = pb.get_record("clients", client_id)

            if client:
                await self.neo4j.execute_write(
                    CYPHER_TEMPLATES["upsert_client"],
                    {
                        "id": client["id"],
                        "name": client.get("name", "Unknown"),
                        "assistant_name": client.get("assistant_name", "Thesis"),
                    },
                )
                result["synced"] = 1
                logger.info(f"Synced client: {client.get('name')}")

        except Exception as e:
            logger.error(f"Client sync failed: {e}")
            result["errors"] = 1

        return result

    async def sync_users(self, client_id: str) -> dict:
        """Sync all users for a client.

        Args:
            client_id: The client ID

        Returns:
            Dict with sync counts
        """
        result = {"synced": 0, "errors": 0}

        try:
            users = pb.get_all("users")
            logger.info(f"Syncing {len(users)} users for client {client_id}")

            for user in users:
                try:
                    await self.neo4j.execute_write(
                        CYPHER_TEMPLATES["upsert_user"],
                        {
                            "id": user["id"],
                            "email": user.get("email", ""),
                            "name": user.get("name", ""),
                            "role": user.get("role", "user"),
                            "client_id": client_id,
                        },
                    )
                    result["synced"] += 1
                except Exception as e:
                    logger.error(f"Failed to sync user {user['id']}: {e}")
                    result["errors"] += 1

        except Exception as e:
            logger.error(f"User sync failed: {e}")
            result["errors"] += 1

        return result

    async def sync_document_chunks(self, client_id: str, max_chunks_per_doc: int = 50) -> dict:
        """Sync document chunks to Neo4j.

        Only syncs a preview of content to keep graph lightweight.

        Args:
            client_id: The client ID
            max_chunks_per_doc: Max chunks to sync per document

        Returns:
            Dict with sync counts
        """
        result = {"synced": 0, "errors": 0}

        try:
            # Get documents
            all_docs = pb.get_all("documents", filter="processing_status='completed'")
            doc_ids = [d["id"] for d in all_docs]
            logger.info(f"Syncing chunks for {len(doc_ids)} documents")

            for doc_id in doc_ids:
                try:
                    all_chunks = documents_repo.list_document_chunks(doc_id)

                    for chunk in all_chunks[:max_chunks_per_doc]:
                        # Truncate content for graph storage
                        content_preview = (chunk.get("content", "") or "")[:500]

                        await self.neo4j.execute_write(
                            CYPHER_TEMPLATES["upsert_chunk"],
                            {
                                "id": chunk["id"],
                                "document_id": doc_id,
                                "chunk_index": chunk.get("chunk_index", 0),
                                "content_preview": content_preview,
                            },
                        )
                        result["synced"] += 1

                except Exception as e:
                    logger.error(f"Failed to sync chunks for document {doc_id}: {e}")
                    result["errors"] += 1

        except Exception as e:
            logger.error(f"Document chunk sync failed: {e}")
            result["errors"] += 1

        return result

    async def sync_conversations(self, client_id: str) -> dict:
        """Sync conversations for a client.

        Args:
            client_id: The client ID

        Returns:
            Dict with sync counts
        """
        result = {"synced": 0, "errors": 0}

        try:
            conversations = conversations_repo.list_conversations()
            logger.info(f"Syncing {len(conversations)} conversations")

            for conv in conversations:
                try:
                    await self.neo4j.execute_write(
                        CYPHER_TEMPLATES["upsert_conversation"],
                        {
                            "id": conv["id"],
                            "title": conv.get("title", "Untitled"),
                            "client_id": client_id,
                            "user_id": conv.get("user_id"),
                            "archived": conv.get("archived", False),
                            "in_knowledge_base": conv.get("in_knowledge_base", False),
                        },
                    )
                    result["synced"] += 1
                except Exception as e:
                    logger.error(f"Failed to sync conversation {conv['id']}: {e}")
                    result["errors"] += 1

        except Exception as e:
            logger.error(f"Conversation sync failed: {e}")
            result["errors"] += 1

        return result

    async def sync_messages(self, client_id: str, max_messages_per_conv: int = 100) -> dict:
        """Sync messages for a client's conversations.

        Only syncs a preview of content to keep graph lightweight.

        Args:
            client_id: The client ID
            max_messages_per_conv: Max messages per conversation

        Returns:
            Dict with sync counts
        """
        result = {"synced": 0, "errors": 0, "agent_links": 0}

        try:
            # Get conversations
            all_convs = conversations_repo.list_conversations()
            conv_ids = [c["id"] for c in all_convs]

            for conv_id in conv_ids:
                try:
                    esc_cid = pb.escape_filter(conv_id)
                    msg_result = pb.list_records(
                        "messages",
                        filter=f"conversation_id='{esc_cid}'",
                        sort="created",
                        per_page=max_messages_per_conv,
                    )
                    all_msgs = msg_result.get("items", [])

                    for msg in all_msgs:
                        content_preview = (msg.get("content", "") or "")[:300]
                        agent_id = msg.get("agent_id")

                        await self.neo4j.execute_write(
                            CYPHER_TEMPLATES["upsert_message"],
                            {
                                "id": msg["id"],
                                "conversation_id": conv_id,
                                "role": msg.get("role", "user"),
                                "content_preview": content_preview,
                                "agent_id": agent_id,
                            },
                        )
                        result["synced"] += 1

                        # Link to agent if assistant message
                        if agent_id and msg.get("role") == "assistant":
                            try:
                                await self.neo4j.execute_write(
                                    CYPHER_TEMPLATES["link_message_agent"],
                                    {"message_id": msg["id"], "agent_id": agent_id},
                                )
                                result["agent_links"] += 1
                            except Exception:
                                pass  # Agent might not exist yet

                except Exception as e:
                    logger.error(f"Failed to sync messages for conversation {conv_id}: {e}")
                    result["errors"] += 1

        except Exception as e:
            logger.error(f"Message sync failed: {e}")
            result["errors"] += 1

        return result

    async def sync_meeting_rooms(self, client_id: str) -> dict:
        """Sync meeting rooms and participants.

        Args:
            client_id: The client ID

        Returns:
            Dict with sync counts
        """
        result = {"synced": 0, "errors": 0, "participants": 0}

        try:
            rooms = pb.get_all("meeting_rooms")
            logger.info(f"Syncing {len(rooms)} meeting rooms")

            for room in rooms:
                try:
                    await self.neo4j.execute_write(
                        CYPHER_TEMPLATES["upsert_meeting_room"],
                        {
                            "id": room["id"],
                            "name": room.get("name", "Untitled Room"),
                            "description": room.get("description", ""),
                            "client_id": client_id,
                            "status": room.get("status", "active"),
                        },
                    )
                    result["synced"] += 1

                    # Sync participants
                    esc_rid = pb.escape_filter(room["id"])
                    participants = pb.get_all(
                        "meeting_room_participants",
                        filter=f"meeting_room_id='{esc_rid}'",
                    )

                    for participant in participants:
                        try:
                            await self.neo4j.execute_write(
                                CYPHER_TEMPLATES["add_meeting_room_participant"],
                                {
                                    "meeting_room_id": room["id"],
                                    "agent_id": participant["agent_id"],
                                },
                            )
                            result["participants"] += 1
                        except Exception:
                            pass  # Agent might not exist

                except Exception as e:
                    logger.error(f"Failed to sync meeting room {room['id']}: {e}")
                    result["errors"] += 1

        except Exception as e:
            logger.error(f"Meeting room sync failed: {e}")
            result["errors"] += 1

        return result

    async def sync_meeting_room_messages(self, client_id: str, max_per_room: int = 200) -> dict:
        """Sync meeting room messages including autonomous discussion metadata.

        Args:
            client_id: The client ID
            max_per_room: Max messages per room

        Returns:
            Dict with sync counts
        """
        result = {"synced": 0, "errors": 0, "response_links": 0}

        try:
            # Get meeting rooms
            all_rooms = pb.get_all("meeting_rooms")
            room_ids = [r["id"] for r in all_rooms]

            for room_id in room_ids:
                try:
                    esc_rid = pb.escape_filter(room_id)
                    msg_result = pb.list_records(
                        "meeting_room_messages",
                        filter=f"meeting_room_id='{esc_rid}'",
                        sort="created",
                        per_page=max_per_room,
                    )
                    messages = msg_result.get("items", [])

                    for msg in messages:
                        content_preview = (msg.get("content", "") or "")[:300]
                        metadata = msg.get("metadata") or {}
                        is_autonomous = metadata.get("autonomous", False) or msg.get("discussion_round") is not None

                        await self.neo4j.execute_write(
                            CYPHER_TEMPLATES["upsert_meeting_room_message"],
                            {
                                "id": msg["id"],
                                "meeting_room_id": room_id,
                                "agent_id": msg.get("agent_id"),
                                "content_preview": content_preview,
                                "role": msg.get("role", "user"),
                                "discussion_round": msg.get("discussion_round"),
                                "responding_to_agent": msg.get("responding_to_agent"),
                                "is_autonomous": is_autonomous,
                            },
                        )
                        result["synced"] += 1

                        # Update graph_synced_at timestamp
                        try:
                            pb.update_record(
                                "meeting_room_messages",
                                msg["id"],
                                {"graph_synced_at": datetime.now(timezone.utc).isoformat()},
                            )
                        except Exception:
                            pass  # Non-critical

                except Exception as e:
                    logger.error(f"Failed to sync messages for room {room_id}: {e}")
                    result["errors"] += 1

        except Exception as e:
            logger.error(f"Meeting room message sync failed: {e}")
            result["errors"] += 1

        return result

    async def sync_single_meeting_room_message(
        self,
        message_id: str,
        meeting_room_id: str,
        content: str,
        role: str,
        agent_id: Optional[str] = None,
        discussion_round: Optional[int] = None,
        responding_to_agent: Optional[str] = None,
        is_autonomous: bool = False,
    ) -> bool:
        """Sync a single meeting room message to Neo4j immediately.

        Used for real-time sync during conversations.

        Args:
            message_id: The message UUID
            meeting_room_id: The meeting room UUID
            content: Message content
            role: Message role (user/agent/system)
            agent_id: Optional agent UUID
            discussion_round: Optional round number for autonomous discussions
            responding_to_agent: Optional agent name this message responds to
            is_autonomous: Whether this is an autonomous discussion message

        Returns:
            True if successful
        """
        try:
            content_preview = (content or "")[:300]

            await self.neo4j.execute_write(
                CYPHER_TEMPLATES["upsert_meeting_room_message"],
                {
                    "id": message_id,
                    "meeting_room_id": meeting_room_id,
                    "agent_id": agent_id,
                    "content_preview": content_preview,
                    "role": role,
                    "discussion_round": discussion_round,
                    "responding_to_agent": responding_to_agent,
                    "is_autonomous": is_autonomous,
                },
            )

            logger.debug(f"Synced meeting room message {message_id} to Neo4j")
            return True

        except Exception as e:
            logger.error(f"Failed to sync message {message_id} to Neo4j: {e}")
            return False

    async def sync_agent_knowledge_base(self) -> dict:
        """Sync agent knowledge base links.

        Creates HAS_KNOWLEDGE_OF relationships between agents and documents.

        Returns:
            Dict with sync counts
        """
        result = {"synced": 0, "errors": 0}

        try:
            kb_links = pb.get_all("agent_knowledge_base")
            logger.info(f"Syncing {len(kb_links)} agent knowledge base links")

            for link in kb_links:
                try:
                    await self.neo4j.execute_write(
                        CYPHER_TEMPLATES["link_agent_knowledge"],
                        {
                            "agent_id": link["agent_id"],
                            "document_id": link["document_id"],
                            "priority": link.get("priority", 0),
                            "notes": link.get("notes", ""),
                        },
                    )
                    result["synced"] += 1
                except Exception as e:
                    logger.error(f"Failed to sync KB link: {e}")
                    result["errors"] += 1

        except Exception as e:
            logger.error(f"Agent knowledge base sync failed: {e}")
            result["errors"] += 1

        return result

    # ==========================================================================
    # Stakeholder Sync Methods
    # ==========================================================================

    async def sync_stakeholders(self, client_id: str) -> dict:
        """Sync all stakeholders and their relationships.

        Args:
            client_id: The client ID

        Returns:
            Dict with sync counts
        """
        result = {"synced": 0, "errors": 0, "relationships": 0}

        try:
            # Fetch stakeholders
            stakeholders = stakeholders_repo.list_stakeholders()
            logger.info(f"Syncing {len(stakeholders)} stakeholders")

            for stakeholder in stakeholders:
                try:
                    # Upsert stakeholder node
                    await self.neo4j.execute_write(
                        CYPHER_TEMPLATES["upsert_stakeholder"],
                        {
                            "id": stakeholder["id"],
                            "name": stakeholder.get("name", "Unknown"),
                            "role": stakeholder.get("role"),
                            "organization": stakeholder.get("organization"),
                            "client_id": client_id,
                            "sentiment_score": stakeholder.get("sentiment_score"),
                            "total_interactions": stakeholder.get("total_interactions", 0),
                        },
                    )
                    result["synced"] += 1
                except Exception as e:
                    logger.error(f"Failed to sync stakeholder {stakeholder['id']}: {e}")
                    result["errors"] += 1

            # Create relationships after all nodes exist
            for stakeholder in stakeholders:
                try:
                    # Handle reports_to relationship
                    reports_to = stakeholder.get("reports_to")
                    if reports_to:
                        await self.neo4j.execute_write(
                            CYPHER_TEMPLATES["create_reports_to"],
                            {"from_id": stakeholder["id"], "to_id": reports_to},
                        )
                        result["relationships"] += 1

                    # Handle influences relationships (from JSONB array)
                    influences = stakeholder.get("influences") or []
                    for influence in influences:
                        if isinstance(influence, dict):
                            target_id = influence.get("stakeholder_id")
                            strength = influence.get("strength", 0.5)
                            influence_type = influence.get("type", "general")
                        else:
                            # Simple ID reference
                            target_id = influence
                            strength = 0.5
                            influence_type = "general"

                        if target_id:
                            await self.neo4j.execute_write(
                                CYPHER_TEMPLATES["create_influences"],
                                {
                                    "from_id": stakeholder["id"],
                                    "to_id": target_id,
                                    "strength": strength,
                                    "influence_type": influence_type,
                                },
                            )
                            result["relationships"] += 1

                except Exception as e:
                    logger.error(f"Failed to create relationships for {stakeholder['id']}: {e}")
                    result["errors"] += 1

        except Exception as e:
            logger.error(f"Stakeholder sync failed: {e}")
            result["errors"] += 1

        return result

    async def sync_meetings(self, client_id: str) -> dict:
        """Sync meetings and attendance relationships.

        Args:
            client_id: The client ID

        Returns:
            Dict with sync counts
        """
        result = {"synced": 0, "errors": 0, "relationships": 0}

        try:
            # Fetch meetings
            meetings = pb.get_all("meeting_transcripts")
            logger.info(f"Syncing {len(meetings)} meetings")

            for meeting in meetings:
                try:
                    # Format meeting date
                    meeting_date = meeting.get("meeting_date")
                    if meeting_date:
                        if isinstance(meeting_date, str):
                            # Parse and format to YYYY-MM-DD
                            meeting_date = meeting_date.split("T")[0]
                    else:
                        meeting_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

                    # Upsert meeting node
                    await self.neo4j.execute_write(
                        CYPHER_TEMPLATES["upsert_meeting"],
                        {
                            "id": meeting["id"],
                            "title": meeting.get("title", "Untitled Meeting"),
                            "client_id": client_id,
                            "meeting_date": meeting_date,
                            "meeting_type": meeting.get("meeting_type", "other"),
                        },
                    )
                    result["synced"] += 1

                    # Create ATTENDED relationships from attendees JSONB
                    attendees = meeting.get("attendees") or []
                    sentiment_summary = meeting.get("sentiment_summary") or {}
                    by_speaker = sentiment_summary.get("by_speaker") or []

                    # Build sentiment lookup
                    sentiment_map = {}
                    for speaker in by_speaker:
                        name = speaker.get("name", "").lower()
                        sentiment_map[name] = speaker.get("sentiment_score", 0.5)

                    for attendee in attendees:
                        attendee_name = attendee.get("name", "") if isinstance(attendee, dict) else attendee
                        if not attendee_name:
                            continue

                        # Find stakeholder by name
                        esc_name = pb.escape_filter(attendee_name)
                        stakeholder_match = pb.get_first(
                            "stakeholders",
                            filter=f"name~'{esc_name}'",
                        )

                        if stakeholder_match:
                            stakeholder_id = stakeholder_match["id"]
                            sentiment = sentiment_map.get(attendee_name.lower(), 0.5)
                            speaking_time = (
                                attendee.get("speaking_time_estimate", "medium")
                                if isinstance(attendee, dict)
                                else "medium"
                            )

                            await self.neo4j.execute_write(
                                CYPHER_TEMPLATES["create_attended"],
                                {
                                    "stakeholder_id": stakeholder_id,
                                    "meeting_id": meeting["id"],
                                    "sentiment": sentiment,
                                    "speaking_time": speaking_time,
                                },
                            )
                            result["relationships"] += 1

                except Exception as e:
                    logger.error(f"Failed to sync meeting {meeting['id']}: {e}")
                    result["errors"] += 1

        except Exception as e:
            logger.error(f"Meeting sync failed: {e}")
            result["errors"] += 1

        return result

    async def sync_insights(self, client_id: str) -> dict:
        """Sync stakeholder insights.

        Args:
            client_id: The client ID

        Returns:
            Dict with sync counts
        """
        result = {"synced": 0, "errors": 0, "relationships": 0}

        try:
            # Fetch all insights
            insights = pb.get_all("stakeholder_insights")
            logger.info(f"Syncing {len(insights)} insights")

            for insight in insights:
                try:
                    # Upsert insight node
                    await self.neo4j.execute_write(
                        CYPHER_TEMPLATES["upsert_insight"],
                        {
                            "id": insight["id"],
                            "insight_type": insight.get("insight_type", "concern"),
                            "content": insight.get("content", ""),
                            "confidence": insight.get("confidence", 0.8),
                        },
                    )
                    result["synced"] += 1

                    # Link to stakeholder
                    stakeholder_id = insight.get("stakeholder_id")
                    if stakeholder_id:
                        await self.neo4j.execute_write(
                            CYPHER_TEMPLATES["link_stakeholder_insight"],
                            {
                                "stakeholder_id": stakeholder_id,
                                "insight_id": insight["id"],
                            },
                        )
                        result["relationships"] += 1

                        # Create Concern node for concern-type insights
                        if insight.get("insight_type") == "concern":
                            concern_id = f"concern_{insight['id']}"
                            await self.neo4j.execute_write(
                                """
                                MERGE (c:Concern {id: $id})
                                SET c.content = $content,
                                    c.severity = $severity,
                                    c.updated_at = datetime()
                                WITH c
                                MATCH (s:Stakeholder {id: $stakeholder_id})
                                MERGE (s)-[r:RAISED_CONCERN]->(c)
                                SET r.quote = $quote
                                RETURN c
                            """,
                                {
                                    "id": concern_id,
                                    "content": insight.get("content", ""),
                                    "severity": "medium",
                                    "stakeholder_id": stakeholder_id,
                                    "quote": insight.get("extracted_quote"),
                                },
                            )
                            result["relationships"] += 1

                except Exception as e:
                    logger.error(f"Failed to sync insight {insight['id']}: {e}")
                    result["errors"] += 1

        except Exception as e:
            logger.error(f"Insight sync failed: {e}")
            result["errors"] += 1

        return result

    async def sync_documents(self, client_id: str) -> dict:
        """Sync documents to graph with full metadata and uploader links.

        Args:
            client_id: The client ID

        Returns:
            Dict with sync counts
        """
        result = {"synced": 0, "errors": 0, "uploader_links": 0}

        try:
            documents = pb.get_all("documents")
            logger.info(f"Syncing {len(documents)} documents")

            for doc in documents:
                try:
                    await self.neo4j.execute_write(
                        CYPHER_TEMPLATES["upsert_document"],
                        {
                            "id": doc["id"],
                            "filename": doc.get("filename", "Untitled"),
                            "file_type": doc.get("file_type", "unknown"),
                            "source_platform": doc.get("source_platform", "upload"),
                            "is_core_document": doc.get("is_core_document", False),
                            "client_id": client_id,
                            "processing_status": doc.get("processing_status", "pending"),
                        },
                    )
                    result["synced"] += 1

                    # Link to uploader if exists
                    uploaded_by = doc.get("uploaded_by")
                    if uploaded_by:
                        try:
                            await self.neo4j.execute_write(
                                CYPHER_TEMPLATES["link_document_uploader"],
                                {"document_id": doc["id"], "user_id": uploaded_by},
                            )
                            result["uploader_links"] += 1
                        except Exception:
                            pass  # User might not be synced yet

                except Exception as e:
                    logger.error(f"Failed to sync document {doc['id']}: {e}")
                    result["errors"] += 1

        except Exception as e:
            logger.error(f"Document sync failed: {e}")
            result["errors"] += 1

        return result

    async def sync_roi_opportunities(self, client_id: str) -> dict:
        """Sync ROI opportunities and supporter/blocker relationships.

        Args:
            client_id: The client ID

        Returns:
            Dict with sync counts
        """
        result = {"synced": 0, "errors": 0, "relationships": 0}

        try:
            opportunities = pb.get_all("roi_opportunities")
            logger.info(f"Syncing {len(opportunities)} ROI opportunities")

            for opp in opportunities:
                try:
                    await self.neo4j.execute_write(
                        CYPHER_TEMPLATES["upsert_roi_opportunity"],
                        {
                            "id": opp["id"],
                            "title": opp.get("title", "Untitled Opportunity"),
                            "status": opp.get("status", "backlog"),
                            "annual_savings": opp.get("annual_savings", 0),
                            "client_id": client_id,
                        },
                    )
                    result["synced"] += 1

                    # Create SUPPORTS relationships from champion stakeholders
                    champions = opp.get("champions") or []
                    for champion in champions:
                        champion_id = champion.get("stakeholder_id") if isinstance(champion, dict) else champion
                        if champion_id:
                            await self.neo4j.execute_write(
                                CYPHER_TEMPLATES["create_supports"],
                                {
                                    "stakeholder_id": champion_id,
                                    "roi_id": opp["id"],
                                    "commitment_level": champion.get("commitment", "supporter")
                                    if isinstance(champion, dict)
                                    else "supporter",
                                },
                            )
                            result["relationships"] += 1

                    # Create BLOCKS relationships from blocker stakeholders
                    blockers = opp.get("blockers") or []
                    for blocker in blockers:
                        blocker_id = blocker.get("stakeholder_id") if isinstance(blocker, dict) else blocker
                        if blocker_id:
                            await self.neo4j.execute_write(
                                CYPHER_TEMPLATES["create_blocks"],
                                {
                                    "stakeholder_id": blocker_id,
                                    "roi_id": opp["id"],
                                    "reason": blocker.get("reason", "Unknown")
                                    if isinstance(blocker, dict)
                                    else "Unknown",
                                },
                            )
                            result["relationships"] += 1

                except Exception as e:
                    logger.error(f"Failed to sync ROI opportunity {opp['id']}: {e}")
                    result["errors"] += 1

        except Exception as e:
            logger.error(f"ROI opportunity sync failed: {e}")
            result["errors"] += 1

        return result

    async def incremental_sync(self, client_id: str, since: datetime, entity_types: Optional[list[str]] = None) -> dict:
        """Perform incremental sync for recently updated entities.

        Args:
            client_id: The client ID
            since: Only sync entities updated after this time
            entity_types: Optional list of entity types to sync

        Returns:
            Dict with sync statistics
        """
        entity_types = entity_types or ["stakeholders", "meetings", "insights", "roi_opportunities"]
        since_iso = since.isoformat()

        results = {
            "client_id": client_id,
            "since": since_iso,
            "entities_checked": 0,
            "entities_synced": 0,
        }

        # Check each entity type for updates
        for entity_type in entity_types:
            try:
                if entity_type == "stakeholders":
                    updated = pb.get_all(
                        "stakeholders",
                        filter=f"updated>='{since_iso}'",
                    )
                    if updated:
                        results["entities_checked"] += len(updated)
                        sync_result = await self.sync_stakeholders(client_id)
                        results["entities_synced"] += sync_result["synced"]

                elif entity_type == "meetings":
                    updated = pb.get_all(
                        "meeting_transcripts",
                        filter=f"created>='{since_iso}'",
                    )
                    if updated:
                        results["entities_checked"] += len(updated)
                        sync_result = await self.sync_meetings(client_id)
                        results["entities_synced"] += sync_result["synced"]

            except Exception as e:
                logger.error(f"Incremental sync failed for {entity_type}: {e}")

        return results

    async def sync_agents(self) -> dict:
        """Sync agents to Neo4j with full metadata and expertise mappings.

        Agents are global (not client-specific) so we sync all active agents.
        Includes all 21 agents with their expertise areas.

        Returns:
            Dict with sync counts
        """
        result = {"synced": 0, "errors": 0, "expertise_links": 0}

        try:
            agents = agents_repo.list_agents()
            logger.info(f"Syncing {len(agents)} agents to Neo4j")

            # Comprehensive agent expertise mapping for all 21 agents
            agent_expertise = {
                # Stakeholder Perspective Agents
                "atlas": [
                    "research",
                    "consulting",
                    "case studies",
                    "thought leadership",
                    "genai",
                    "lean methodology",
                    "benchmarking",
                ],
                "capital": [
                    "roi",
                    "finance",
                    "budget",
                    "cost savings",
                    "investment",
                    "sox compliance",
                    "business case",
                ],
                "guardian": [
                    "governance",
                    "security",
                    "infrastructure",
                    "it",
                    "compliance",
                    "vendor evaluation",
                    "shadow it",
                ],
                "counselor": [
                    "legal",
                    "contracts",
                    "compliance",
                    "risk",
                    "policy",
                    "data privacy",
                    "liability",
                ],
                "sage": [
                    "change management",
                    "human flourishing",
                    "adoption",
                    "people",
                    "culture",
                    "training",
                ],
                "oracle": [
                    "transcripts",
                    "meetings",
                    "stakeholders",
                    "sentiment",
                    "insights",
                    "dynamics",
                ],
                # Consulting/Implementation Agents
                "strategist": [
                    "strategy",
                    "executive",
                    "c-suite",
                    "governance",
                    "politics",
                    "organizational",
                ],
                "architect": [
                    "architecture",
                    "technical",
                    "rag",
                    "integration",
                    "build vs buy",
                    "enterprise ai",
                ],
                "operator": [
                    "operations",
                    "process",
                    "automation",
                    "metrics",
                    "optimization",
                    "workflow",
                ],
                "pioneer": [
                    "innovation",
                    "r&d",
                    "emerging technology",
                    "hype",
                    "maturity assessment",
                ],
                # Internal Enablement Agents
                "catalyst": [
                    "communications",
                    "messaging",
                    "employee engagement",
                    "ai anxiety",
                    "internal",
                ],
                "scholar": [
                    "training",
                    "learning",
                    "development",
                    "champion enablement",
                    "adult learning",
                ],
                "echo": ["brand voice", "style", "tone", "voice analysis", "ai emulation"],
                "glean_evaluator": [
                    "glean",
                    "enterprise search",
                    "connectors",
                    "platform fit",
                    "build vs buy",
                ],
                "manual": [
                    "documentation",
                    "help",
                    "tutorials",
                    "features",
                    "platform",
                    "onboarding",
                    "troubleshooting",
                ],
                # Systems/Coordination Agents
                "nexus": [
                    "systems thinking",
                    "interconnections",
                    "feedback loops",
                    "leverage points",
                    "unintended consequences",
                ],
                "coordinator": ["orchestration", "routing", "synthesis", "coordination"],
                # Personal Development Agent
                "compass": [
                    "career",
                    "wins",
                    "performance",
                    "check-ins",
                    "development",
                    "strategic alignment",
                ],
                # Meta-Agents
                "facilitator": [
                    "meeting orchestration",
                    "discussion flow",
                    "agent coordination",
                    "clarification",
                ],
                "reporter": [
                    "synthesis",
                    "documentation",
                    "summaries",
                    "action items",
                    "executive briefs",
                ],
            }

            for agent in agents:
                try:
                    # Upsert agent node using template
                    await self.neo4j.execute_write(
                        CYPHER_TEMPLATES["upsert_agent"],
                        {
                            "id": agent["id"],
                            "name": agent.get("name", ""),
                            "display_name": agent.get("display_name", ""),
                            "description": agent.get("description", ""),
                            "persona": agent.get("persona", ""),
                            "is_active": agent.get("is_active", True),
                        },
                    )
                    result["synced"] += 1

                    # Create expertise relationships
                    agent_name = agent.get("name", "").lower()
                    expertise_concepts = agent_expertise.get(agent_name, [])

                    for concept_name in expertise_concepts:
                        try:
                            await self.neo4j.execute_write(
                                CYPHER_TEMPLATES["link_agent_expertise"],
                                {
                                    "agent_id": agent["id"],
                                    "expertise_name": concept_name,
                                    "category": "agent_expertise",
                                    "confidence": 0.9,
                                },
                            )
                            result["expertise_links"] += 1
                        except Exception as e:
                            logger.error(f"Failed to link agent {agent['id']} to expertise {concept_name}: {e}")

                except Exception as e:
                    logger.error(f"Failed to sync agent {agent['id']}: {e}")
                    result["errors"] += 1

        except Exception as e:
            logger.error(f"Agent sync failed: {e}")
            result["errors"] += 1

        return result

    async def sync_agent_handoffs(self, client_id: str) -> dict:
        """Sync agent handoffs to Neo4j as relationships.

        Args:
            client_id: The client ID

        Returns:
            Dict with sync counts
        """
        result = {"synced": 0, "errors": 0}

        try:
            # Get all agent handoffs
            handoffs = pb.get_all("agent_handoffs")
            logger.info(f"Syncing {len(handoffs)} agent handoffs")

            for handoff in handoffs:
                try:
                    await self.neo4j.execute_write(
                        """
                        MATCH (from:Agent {id: $from_agent_id})
                        MATCH (to:Agent {id: $to_agent_id})
                        CREATE (from)-[r:HANDED_OFF_TO {
                            conversation_id: $conversation_id,
                            reason: $reason,
                            timestamp: datetime($timestamp)
                        }]->(to)
                        RETURN r
                    """,
                        {
                            "from_agent_id": handoff.get("from_agent_id"),
                            "to_agent_id": handoff.get("to_agent_id"),
                            "conversation_id": handoff.get("conversation_id"),
                            "reason": handoff.get("reason", ""),
                            "timestamp": handoff.get("created_at", datetime.now(timezone.utc).isoformat()),
                        },
                    )
                    result["synced"] += 1
                except Exception as e:
                    logger.error(f"Failed to sync handoff: {e}")
                    result["errors"] += 1

        except Exception as e:
            logger.error(f"Agent handoff sync failed: {e}")
            result["errors"] += 1

        return result

    # ==========================================================================
    # Stakeholder-Document Relationship Sync Methods
    # ==========================================================================

    async def sync_stakeholder_document_relationships(self, client_id: str) -> dict:
        """Sync relationships between stakeholders and documents.

        Creates relationships based on:
        1. Name mentions in document content/chunks
        2. Department matching (finance docs -> finance stakeholders)
        3. Documents explicitly about stakeholders

        Args:
            client_id: The client ID

        Returns:
            Dict with sync counts
        """
        result = {"name_matches": 0, "department_matches": 0, "errors": 0}

        try:
            # Get all stakeholders
            stakeholders = stakeholders_repo.list_stakeholders()
            logger.info(f"Checking {len(stakeholders)} stakeholders for document relationships")

            # Get all completed documents
            documents = pb.get_all("documents", filter="processing_status='completed'")

            # Method 1: Match stakeholder names in document filenames
            for stakeholder in stakeholders:
                stakeholder_name = stakeholder.get("name", "")
                if not stakeholder_name or len(stakeholder_name) < 3:
                    continue

                # Split name into parts for matching
                name_parts = stakeholder_name.lower().split()

                for doc in documents:
                    filename = (doc.get("filename") or "").lower()

                    # Check if any significant name part appears in filename
                    for part in name_parts:
                        if len(part) > 2 and part in filename:
                            try:
                                await self.neo4j.execute_write(
                                    CYPHER_TEMPLATES["link_stakeholder_mentioned_in_document"],
                                    {
                                        "stakeholder_id": stakeholder["id"],
                                        "document_id": doc["id"],
                                        "context": f"Name '{part}' found in filename",
                                    },
                                )
                                result["name_matches"] += 1
                                break  # Only create one relationship per stakeholder-doc pair
                            except Exception as e:
                                logger.error(f"Failed to link stakeholder to document: {e}")
                                result["errors"] += 1

            # Method 2: Match by department keywords in filename
            department_keywords = {
                "finance": ["finance", "financial", "budget", "accounting", "invoice", "expense"],
                "hr": ["hr", "human resources", "employee", "onboarding", "hiring", "talent"],
                "legal": ["legal", "contract", "compliance", "policy", "agreement", "terms"],
                "it": ["it", "technical", "security", "infrastructure", "system", "network"],
                "product": ["product", "roadmap", "feature", "release", "sprint"],
                "executive": ["executive", "board", "strategy", "ceo", "leadership"],
            }

            for stakeholder in stakeholders:
                department = (stakeholder.get("department") or "").lower()
                role = (stakeholder.get("role") or "").lower()

                # Determine which department keywords to use
                keywords = []
                for dept, kw_list in department_keywords.items():
                    if dept in department or dept in role:
                        keywords.extend(kw_list)
                        break

                if not keywords:
                    continue

                for doc in documents:
                    filename = (doc.get("filename") or "").lower()

                    for keyword in keywords:
                        if keyword in filename:
                            try:
                                await self.neo4j.execute_write(
                                    """
                                    MATCH (d:Document {id: $document_id})
                                    MATCH (s:Stakeholder {id: $stakeholder_id})
                                    MERGE (d)-[r:RELEVANT_TO]->(s)
                                    SET r.inferred_by = 'department_match',
                                        r.keyword = $keyword,
                                        r.updated_at = datetime()
                                    RETURN r
                                """,
                                    {
                                        "document_id": doc["id"],
                                        "stakeholder_id": stakeholder["id"],
                                        "keyword": keyword,
                                    },
                                )
                                result["department_matches"] += 1
                                break  # Only one relationship per doc-stakeholder pair
                            except Exception as e:
                                logger.error(f"Failed to create department link: {e}")
                                result["errors"] += 1

            logger.info(
                f"Stakeholder-document sync complete: "
                f"{result['name_matches']} name matches, "
                f"{result['department_matches']} department matches"
            )

        except Exception as e:
            logger.error(f"Stakeholder-document relationship sync failed: {e}")
            result["errors"] += 1

        return result

    async def sync_stakeholder_mentions_in_chunks(self, client_id: str) -> dict:
        """Scan document chunks for stakeholder name mentions.

        More thorough than filename matching but more expensive.

        Args:
            client_id: The client ID

        Returns:
            Dict with sync counts
        """
        result = {"mentions_found": 0, "errors": 0}

        try:
            # Get stakeholders
            stakeholders = stakeholders_repo.list_stakeholders()

            # Get documents
            all_docs = pb.get_all("documents", filter="processing_status='completed'")
            doc_ids = [d["id"] for d in all_docs]

            for doc_id in doc_ids:
                # Get chunks for this document
                all_chunks = documents_repo.list_document_chunks(doc_id)
                chunks = all_chunks[:50]

                # Combine chunk content for searching
                combined_content = " ".join((c.get("content") or "").lower() for c in chunks)

                # Check each stakeholder
                for stakeholder in stakeholders:
                    name = stakeholder.get("name", "")
                    if not name or len(name) < 3:
                        continue

                    # Check for full name or last name
                    name_lower = name.lower()
                    name_parts = name_lower.split()
                    last_name = name_parts[-1] if name_parts else ""

                    if name_lower in combined_content or (len(last_name) > 3 and last_name in combined_content):
                        try:
                            # Find context snippet
                            context = ""
                            for chunk in chunks:
                                content = (chunk.get("content") or "").lower()
                                if name_lower in content or last_name in content:
                                    # Extract surrounding context
                                    idx = content.find(name_lower)
                                    if idx == -1:
                                        idx = content.find(last_name)
                                    start = max(0, idx - 50)
                                    end = min(len(content), idx + len(name) + 50)
                                    context = content[start:end]
                                    break

                            await self.neo4j.execute_write(
                                CYPHER_TEMPLATES["link_stakeholder_mentioned_in_document"],
                                {
                                    "stakeholder_id": stakeholder["id"],
                                    "document_id": doc_id,
                                    "context": context[:200] if context else "Name found in document content",
                                },
                            )
                            result["mentions_found"] += 1

                        except Exception as e:
                            logger.error(f"Failed to create mention link: {e}")
                            result["errors"] += 1

        except Exception as e:
            logger.error(f"Chunk mention scan failed: {e}")
            result["errors"] += 1

        return result

    async def link_stakeholder_to_document(
        self,
        stakeholder_id: str,
        document_id: str,
        relationship_type: str = "MENTIONED_IN",
        context: Optional[str] = None,
        date: Optional[str] = None,
    ) -> bool:
        """Create a specific stakeholder-document relationship.

        Args:
            stakeholder_id: The stakeholder UUID
            document_id: The document UUID
            relationship_type: One of MENTIONED_IN, PROVIDED, ABOUT
            context: Optional context for the relationship
            date: Optional date (for PROVIDED relationship)

        Returns:
            True if successful
        """
        try:
            if relationship_type == "MENTIONED_IN":
                await self.neo4j.execute_write(
                    CYPHER_TEMPLATES["link_stakeholder_mentioned_in_document"],
                    {
                        "stakeholder_id": stakeholder_id,
                        "document_id": document_id,
                        "context": context or "",
                    },
                )
            elif relationship_type == "PROVIDED":
                await self.neo4j.execute_write(
                    CYPHER_TEMPLATES["link_stakeholder_provided_document"],
                    {
                        "stakeholder_id": stakeholder_id,
                        "document_id": document_id,
                        "date": date or datetime.now(timezone.utc).isoformat(),
                    },
                )
            elif relationship_type == "ABOUT":
                await self.neo4j.execute_write(
                    CYPHER_TEMPLATES["link_document_stakeholder"],
                    {
                        "document_id": document_id,
                        "stakeholder_id": stakeholder_id,
                    },
                )
            else:
                logger.warning(f"Unknown relationship type: {relationship_type}")
                return False

            logger.info(
                f"Created {relationship_type} link between stakeholder {stakeholder_id} and document {document_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to create stakeholder-document link: {e}")
            return False

    async def _log_sync(self, client_id: str, sync_type: str, results: dict) -> None:
        """Log sync operation."""
        try:
            pb.create_record("graph_sync_log", {
                "client_id": client_id,
                "sync_type": sync_type,
                "entity_type": "full",
                "synced_at": datetime.now(timezone.utc).isoformat(),
                "sync_status": "completed" if not results.get("error") else "failed",
                "details": results,
            })
        except Exception as e:
            logger.error(f"Failed to log sync: {e}")
