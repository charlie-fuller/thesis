"""
Graph Sync Service

Synchronizes data from Supabase (source of truth) to Neo4j (graph layer).
Handles stakeholders, meetings, insights, documents, and relationships.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Any
from uuid import uuid4

from supabase import Client

from .connection import Neo4jConnection
from .schema import CYPHER_TEMPLATES

logger = logging.getLogger(__name__)


class GraphSyncService:
    """
    Service for synchronizing Supabase data to Neo4j.

    Supports both full sync and incremental sync operations.
    Tracks sync state to enable efficient incremental updates.
    """

    def __init__(self, supabase: Client, neo4j: Neo4jConnection):
        """
        Initialize the sync service.

        Args:
            supabase: Supabase client for reading source data
            neo4j: Neo4j connection for writing graph data
        """
        self.supabase = supabase
        self.neo4j = neo4j

    async def full_sync(self, client_id: str) -> dict:
        """
        Perform a full sync of all entities for a client.

        Args:
            client_id: The client ID to sync

        Returns:
            Dict with sync statistics
        """
        logger.info(f"Starting full sync for client {client_id}")
        start_time = datetime.now(timezone.utc)

        results = {
            "client_id": client_id,
            "started_at": start_time.isoformat(),
            "agents": {"synced": 0, "errors": 0},
            "stakeholders": {"synced": 0, "errors": 0},
            "meetings": {"synced": 0, "errors": 0},
            "insights": {"synced": 0, "errors": 0},
            "documents": {"synced": 0, "errors": 0},
            "roi_opportunities": {"synced": 0, "errors": 0},
            "relationships": {"created": 0, "errors": 0},
        }

        try:
            # Sync agents first (global, not client-specific)
            agent_result = await self.sync_agents()
            results["agents"] = agent_result

            # Sync in order of dependencies
            stakeholder_result = await self.sync_stakeholders(client_id)
            results["stakeholders"] = stakeholder_result

            meeting_result = await self.sync_meetings(client_id)
            results["meetings"] = meeting_result

            insight_result = await self.sync_insights(client_id)
            results["insights"] = insight_result

            document_result = await self.sync_documents(client_id)
            results["documents"] = document_result

            roi_result = await self.sync_roi_opportunities(client_id)
            results["roi_opportunities"] = roi_result

            # Log sync completion
            await self._log_sync(client_id, "full", results)

        except Exception as e:
            logger.error(f"Full sync failed for client {client_id}: {e}")
            results["error"] = str(e)

        results["completed_at"] = datetime.now(timezone.utc).isoformat()
        results["duration_seconds"] = (datetime.now(timezone.utc) - start_time).total_seconds()

        return results

    async def sync_stakeholders(self, client_id: str) -> dict:
        """
        Sync all stakeholders and their relationships.

        Args:
            client_id: The client ID

        Returns:
            Dict with sync counts
        """
        result = {"synced": 0, "errors": 0, "relationships": 0}

        try:
            # Fetch stakeholders from Supabase
            response = self.supabase.table("stakeholders") \
                .select("*") \
                .eq("client_id", client_id) \
                .execute()

            stakeholders = response.data or []
            logger.info(f"Syncing {len(stakeholders)} stakeholders for client {client_id}")

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
                        }
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
                            {"from_id": stakeholder["id"], "to_id": reports_to}
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
                                }
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
        """
        Sync meetings and attendance relationships.

        Args:
            client_id: The client ID

        Returns:
            Dict with sync counts
        """
        result = {"synced": 0, "errors": 0, "relationships": 0}

        try:
            # Fetch meetings from Supabase
            response = self.supabase.table("meeting_transcripts") \
                .select("*") \
                .eq("client_id", client_id) \
                .execute()

            meetings = response.data or []
            logger.info(f"Syncing {len(meetings)} meetings for client {client_id}")

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
                        }
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
                        stakeholder_response = self.supabase.table("stakeholders") \
                            .select("id") \
                            .eq("client_id", client_id) \
                            .ilike("name", f"%{attendee_name}%") \
                            .limit(1) \
                            .execute()

                        if stakeholder_response.data:
                            stakeholder_id = stakeholder_response.data[0]["id"]
                            sentiment = sentiment_map.get(attendee_name.lower(), 0.5)
                            speaking_time = attendee.get("speaking_time_estimate", "medium") if isinstance(attendee, dict) else "medium"

                            await self.neo4j.execute_write(
                                CYPHER_TEMPLATES["create_attended"],
                                {
                                    "stakeholder_id": stakeholder_id,
                                    "meeting_id": meeting["id"],
                                    "sentiment": sentiment,
                                    "speaking_time": speaking_time,
                                }
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
        """
        Sync stakeholder insights.

        Args:
            client_id: The client ID

        Returns:
            Dict with sync counts
        """
        result = {"synced": 0, "errors": 0, "relationships": 0}

        try:
            # Fetch insights with stakeholder info
            response = self.supabase.table("stakeholder_insights") \
                .select("*, stakeholders!inner(client_id)") \
                .eq("stakeholders.client_id", client_id) \
                .execute()

            insights = response.data or []
            logger.info(f"Syncing {len(insights)} insights for client {client_id}")

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
                        }
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
                            }
                        )
                        result["relationships"] += 1

                        # Create Concern node for concern-type insights
                        if insight.get("insight_type") == "concern":
                            concern_id = f"concern_{insight['id']}"
                            await self.neo4j.execute_write("""
                                MERGE (c:Concern {id: $id})
                                SET c.content = $content,
                                    c.severity = $severity,
                                    c.updated_at = datetime()
                                WITH c
                                MATCH (s:Stakeholder {id: $stakeholder_id})
                                MERGE (s)-[r:RAISED_CONCERN]->(c)
                                SET r.quote = $quote
                                RETURN c
                            """, {
                                "id": concern_id,
                                "content": insight.get("content", ""),
                                "severity": "medium",
                                "stakeholder_id": stakeholder_id,
                                "quote": insight.get("extracted_quote"),
                            })
                            result["relationships"] += 1

                except Exception as e:
                    logger.error(f"Failed to sync insight {insight['id']}: {e}")
                    result["errors"] += 1

        except Exception as e:
            logger.error(f"Insight sync failed: {e}")
            result["errors"] += 1

        return result

    async def sync_documents(self, client_id: str) -> dict:
        """
        Sync documents to graph.

        Args:
            client_id: The client ID

        Returns:
            Dict with sync counts
        """
        result = {"synced": 0, "errors": 0}

        try:
            response = self.supabase.table("documents") \
                .select("*") \
                .eq("client_id", client_id) \
                .execute()

            documents = response.data or []
            logger.info(f"Syncing {len(documents)} documents for client {client_id}")

            for doc in documents:
                try:
                    await self.neo4j.execute_write("""
                        MERGE (d:Document {id: $id})
                        SET d.title = $title,
                            d.doc_type = $doc_type,
                            d.summary = $summary,
                            d.client_id = $client_id,
                            d.updated_at = datetime()
                        RETURN d
                    """, {
                        "id": doc["id"],
                        "title": doc.get("title", "Untitled"),
                        "doc_type": doc.get("doc_type", "document"),
                        "summary": doc.get("summary", ""),
                        "client_id": client_id,
                    })
                    result["synced"] += 1
                except Exception as e:
                    logger.error(f"Failed to sync document {doc['id']}: {e}")
                    result["errors"] += 1

        except Exception as e:
            logger.error(f"Document sync failed: {e}")
            result["errors"] += 1

        return result

    async def sync_roi_opportunities(self, client_id: str) -> dict:
        """
        Sync ROI opportunities and supporter/blocker relationships.

        Args:
            client_id: The client ID

        Returns:
            Dict with sync counts
        """
        result = {"synced": 0, "errors": 0, "relationships": 0}

        try:
            response = self.supabase.table("roi_opportunities") \
                .select("*") \
                .eq("client_id", client_id) \
                .execute()

            opportunities = response.data or []
            logger.info(f"Syncing {len(opportunities)} ROI opportunities for client {client_id}")

            for opp in opportunities:
                try:
                    await self.neo4j.execute_write(
                        CYPHER_TEMPLATES["upsert_roi_opportunity"],
                        {
                            "id": opp["id"],
                            "title": opp.get("title", "Untitled Opportunity"),
                            "status": opp.get("status", "identified"),
                            "annual_savings": opp.get("annual_savings", 0),
                            "client_id": client_id,
                        }
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
                                    "commitment_level": champion.get("commitment", "supporter") if isinstance(champion, dict) else "supporter",
                                }
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
                                    "reason": blocker.get("reason", "Unknown") if isinstance(blocker, dict) else "Unknown",
                                }
                            )
                            result["relationships"] += 1

                except Exception as e:
                    logger.error(f"Failed to sync ROI opportunity {opp['id']}: {e}")
                    result["errors"] += 1

        except Exception as e:
            logger.error(f"ROI opportunity sync failed: {e}")
            result["errors"] += 1

        return result

    async def incremental_sync(
        self,
        client_id: str,
        since: datetime,
        entity_types: Optional[list[str]] = None
    ) -> dict:
        """
        Perform incremental sync for recently updated entities.

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
                    response = self.supabase.table("stakeholders") \
                        .select("id") \
                        .eq("client_id", client_id) \
                        .gte("updated_at", since_iso) \
                        .execute()
                    if response.data:
                        results["entities_checked"] += len(response.data)
                        sync_result = await self.sync_stakeholders(client_id)
                        results["entities_synced"] += sync_result["synced"]

                elif entity_type == "meetings":
                    response = self.supabase.table("meeting_transcripts") \
                        .select("id") \
                        .eq("client_id", client_id) \
                        .gte("created_at", since_iso) \
                        .execute()
                    if response.data:
                        results["entities_checked"] += len(response.data)
                        sync_result = await self.sync_meetings(client_id)
                        results["entities_synced"] += sync_result["synced"]

            except Exception as e:
                logger.error(f"Incremental sync failed for {entity_type}: {e}")

        return results

    async def sync_agents(self) -> dict:
        """
        Sync agents to Neo4j.

        Agents are global (not client-specific) so we sync all active agents.

        Returns:
            Dict with sync counts
        """
        result = {"synced": 0, "errors": 0, "expertise_links": 0}

        try:
            response = self.supabase.table("agents") \
                .select("*") \
                .eq("is_active", True) \
                .execute()

            agents = response.data or []
            logger.info(f"Syncing {len(agents)} agents to Neo4j")

            # Agent expertise mapping (which concepts each agent is expert in)
            agent_expertise = {
                "atlas": ["research", "consulting", "case studies", "thought leadership", "genai"],
                "fortuna": ["roi", "finance", "budget", "cost savings", "investment"],
                "guardian": ["governance", "security", "infrastructure", "it", "compliance"],
                "counselor": ["legal", "contracts", "compliance", "risk", "policy"],
                "oracle": ["transcripts", "meetings", "stakeholders", "sentiment", "insights"],
            }

            for agent in agents:
                try:
                    # Upsert agent node
                    await self.neo4j.execute_write("""
                        MERGE (a:Agent {id: $id})
                        SET a.name = $name,
                            a.display_name = $display_name,
                            a.description = $description,
                            a.is_active = $is_active,
                            a.updated_at = datetime()
                        RETURN a
                    """, {
                        "id": agent["id"],
                        "name": agent.get("name", ""),
                        "display_name": agent.get("display_name", ""),
                        "description": agent.get("description", ""),
                        "is_active": agent.get("is_active", True),
                    })
                    result["synced"] += 1

                    # Create expertise relationships
                    agent_name = agent.get("name", "").lower()
                    expertise_concepts = agent_expertise.get(agent_name, [])

                    for concept_name in expertise_concepts:
                        try:
                            await self.neo4j.execute_write("""
                                MERGE (c:Concept {name: $concept_name})
                                SET c.category = 'agent_expertise',
                                    c.updated_at = datetime()
                                WITH c
                                MATCH (a:Agent {id: $agent_id})
                                MERGE (a)-[r:EXPERT_IN]->(c)
                                SET r.confidence = 0.9
                                RETURN r
                            """, {
                                "concept_name": concept_name,
                                "agent_id": agent["id"],
                            })
                            result["expertise_links"] += 1
                        except Exception as e:
                            logger.error(f"Failed to link agent {agent['id']} to concept {concept_name}: {e}")

                except Exception as e:
                    logger.error(f"Failed to sync agent {agent['id']}: {e}")
                    result["errors"] += 1

        except Exception as e:
            logger.error(f"Agent sync failed: {e}")
            result["errors"] += 1

        return result

    async def sync_agent_handoffs(self, client_id: str) -> dict:
        """
        Sync agent handoffs to Neo4j as relationships.

        Args:
            client_id: The client ID

        Returns:
            Dict with sync counts
        """
        result = {"synced": 0, "errors": 0}

        try:
            # Get recent handoffs for this client's conversations
            response = self.supabase.table("agent_handoffs") \
                .select("*, conversations!inner(client_id)") \
                .eq("conversations.client_id", client_id) \
                .execute()

            handoffs = response.data or []
            logger.info(f"Syncing {len(handoffs)} agent handoffs for client {client_id}")

            for handoff in handoffs:
                try:
                    await self.neo4j.execute_write("""
                        MATCH (from:Agent {id: $from_agent_id})
                        MATCH (to:Agent {id: $to_agent_id})
                        CREATE (from)-[r:HANDED_OFF_TO {
                            conversation_id: $conversation_id,
                            reason: $reason,
                            timestamp: datetime($timestamp)
                        }]->(to)
                        RETURN r
                    """, {
                        "from_agent_id": handoff.get("from_agent_id"),
                        "to_agent_id": handoff.get("to_agent_id"),
                        "conversation_id": handoff.get("conversation_id"),
                        "reason": handoff.get("reason", ""),
                        "timestamp": handoff.get("created_at", datetime.now(timezone.utc).isoformat()),
                    })
                    result["synced"] += 1
                except Exception as e:
                    logger.error(f"Failed to sync handoff: {e}")
                    result["errors"] += 1

        except Exception as e:
            logger.error(f"Agent handoff sync failed: {e}")
            result["errors"] += 1

        return result

    async def _log_sync(
        self,
        client_id: str,
        sync_type: str,
        results: dict
    ) -> None:
        """Log sync operation to Supabase."""
        try:
            self.supabase.table("graph_sync_log").insert({
                "id": str(uuid4()),
                "client_id": client_id,
                "sync_type": sync_type,
                "entity_type": "full",
                "synced_at": datetime.now(timezone.utc).isoformat(),
                "sync_status": "completed" if not results.get("error") else "failed",
                "details": results,
            }).execute()
        except Exception as e:
            logger.error(f"Failed to log sync: {e}")
