"""
Relationship Extractor

Infers graph relationships from Supabase data that aren't explicitly stored.
This is where Neo4j's value shines - deriving relationships from patterns.
"""

import logging
import os
from typing import Any, Optional
from collections import defaultdict

from anthropic import Anthropic
from supabase import Client

from .connection import Neo4jConnection

logger = logging.getLogger(__name__)


class RelationshipExtractor:
    """
    Infers graph relationships from Supabase data.

    Key capabilities:
    - Influence inference from meeting co-attendance patterns
    - Concept extraction from meeting transcripts using LLM
    - Stakeholder clustering based on shared concerns and meetings
    """

    def __init__(
        self,
        supabase: Client,
        neo4j: Neo4jConnection,
        anthropic_client: Optional[Anthropic] = None
    ):
        """
        Initialize the relationship extractor.

        Args:
            supabase: Supabase client for reading source data
            neo4j: Neo4j connection for writing relationships
            anthropic_client: Optional Anthropic client for LLM-based extraction
        """
        self.supabase = supabase
        self.neo4j = neo4j
        self.anthropic = anthropic_client or Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )

    async def infer_influences(self, client_id: str) -> dict:
        """
        Analyze meeting co-attendance and interaction patterns
        to infer who influences whom.

        Influence is inferred when:
        - Stakeholders frequently attend the same meetings
        - One stakeholder has a senior role
        - Meeting sentiment patterns suggest deference

        Args:
            client_id: Client ID to analyze

        Returns:
            Dict with inferred influence relationships
        """
        result = {"influences_created": 0, "analyzed_pairs": 0, "errors": 0}

        try:
            # Get all stakeholders with their meeting attendance
            stakeholders = await self._get_stakeholders_with_meetings(client_id)

            if len(stakeholders) < 2:
                logger.info(f"Not enough stakeholders for influence analysis: {len(stakeholders)}")
                return result

            # Analyze co-attendance patterns
            co_attendance = self._calculate_co_attendance(stakeholders)

            # Determine influence based on role hierarchy and meeting patterns
            for (s1_id, s2_id), meetings in co_attendance.items():
                if len(meetings) < 2:
                    continue

                result["analyzed_pairs"] += 1

                s1 = stakeholders.get(s1_id, {})
                s2 = stakeholders.get(s2_id, {})

                # Determine influence direction based on role seniority
                influence_direction = self._determine_influence_direction(s1, s2)

                if influence_direction:
                    influencer_id, influenced_id = influence_direction
                    strength = min(len(meetings) / 10.0, 1.0)  # Max strength at 10+ shared meetings

                    try:
                        await self.neo4j.execute_write("""
                            MATCH (a:Stakeholder {id: $influencer_id})
                            MATCH (b:Stakeholder {id: $influenced_id})
                            MERGE (a)-[r:INFLUENCES]->(b)
                            SET r.strength = $strength,
                                r.influence_type = 'inferred_from_meetings',
                                r.shared_meeting_count = $meeting_count,
                                r.inferred_at = datetime()
                            RETURN r
                        """, {
                            "influencer_id": influencer_id,
                            "influenced_id": influenced_id,
                            "strength": strength,
                            "meeting_count": len(meetings),
                        })
                        result["influences_created"] += 1
                    except Exception as e:
                        logger.error(f"Failed to create influence relationship: {e}")
                        result["errors"] += 1

        except Exception as e:
            logger.error(f"Influence inference failed: {e}")
            result["errors"] += 1

        return result

    async def extract_concepts_from_meeting(self, meeting_id: str) -> dict:
        """
        Use LLM to extract key concepts/topics from a meeting transcript.

        Args:
            meeting_id: Meeting ID to analyze

        Returns:
            Dict with extracted concepts
        """
        result = {"concepts_created": 0, "discusses_links": 0, "errors": 0}

        try:
            # Get meeting with transcript content
            response = self.supabase.table("meeting_transcripts") \
                .select("id, title, content, summary") \
                .eq("id", meeting_id) \
                .single() \
                .execute()

            if not response.data:
                logger.warning(f"Meeting {meeting_id} not found")
                return result

            meeting = response.data
            content = meeting.get("content") or meeting.get("summary") or ""

            if not content:
                logger.info(f"No content to analyze for meeting {meeting_id}")
                return result

            # Extract concepts using LLM
            concepts = await self._extract_concepts_with_llm(content)

            for concept in concepts:
                try:
                    # Create concept node and link to meeting
                    await self.neo4j.execute_write("""
                        MERGE (c:Concept {name: $name})
                        SET c.category = $category,
                            c.updated_at = datetime()
                        WITH c
                        MATCH (m:Meeting {id: $meeting_id})
                        MERGE (m)-[r:DISCUSSES]->(c)
                        SET r.frequency = coalesce(r.frequency, 0) + 1,
                            r.extracted_at = datetime()
                        RETURN c
                    """, {
                        "name": concept["name"],
                        "category": concept.get("category", "general"),
                        "meeting_id": meeting_id,
                    })
                    result["concepts_created"] += 1
                    result["discusses_links"] += 1
                except Exception as e:
                    logger.error(f"Failed to create concept {concept}: {e}")
                    result["errors"] += 1

        except Exception as e:
            logger.error(f"Concept extraction failed for meeting {meeting_id}: {e}")
            result["errors"] += 1

        return result

    async def detect_stakeholder_clusters(self, client_id: str) -> dict:
        """
        Identify natural groupings of stakeholders based on
        meeting patterns and shared concerns.

        Args:
            client_id: Client ID to analyze

        Returns:
            Dict with cluster information
        """
        result = {"clusters_found": 0, "stakeholders_clustered": 0}

        try:
            # Find stakeholders who share concerns
            shared_concerns = await self.neo4j.execute_query("""
                MATCH (s1:Stakeholder {client_id: $client_id})-[:RAISED_CONCERN]->(c:Concern)<-[:RAISED_CONCERN]-(s2:Stakeholder)
                WHERE s1.id < s2.id
                WITH s1, s2, count(c) as shared_concerns
                WHERE shared_concerns >= 2
                RETURN {
                    stakeholder1: {id: s1.id, name: s1.name},
                    stakeholder2: {id: s2.id, name: s2.name},
                    shared_concern_count: shared_concerns
                } as cluster_pair
            """, {"client_id": client_id})

            # Find stakeholders who attend many meetings together
            meeting_clusters = await self.neo4j.execute_query("""
                MATCH (s1:Stakeholder {client_id: $client_id})-[:ATTENDED]->(m:Meeting)<-[:ATTENDED]-(s2:Stakeholder)
                WHERE s1.id < s2.id
                WITH s1, s2, count(m) as shared_meetings
                WHERE shared_meetings >= 3
                RETURN {
                    stakeholder1: {id: s1.id, name: s1.name},
                    stakeholder2: {id: s2.id, name: s2.name},
                    shared_meeting_count: shared_meetings
                } as cluster_pair
            """, {"client_id": client_id})

            # Build cluster groups from the pairs
            clusters = self._build_clusters_from_pairs(
                shared_concerns + meeting_clusters
            )

            result["clusters_found"] = len(clusters)
            result["stakeholders_clustered"] = sum(len(c) for c in clusters)

            # Store cluster information as relationships
            for i, cluster in enumerate(clusters):
                cluster_name = f"cluster_{client_id[:8]}_{i}"
                for stakeholder_id in cluster:
                    try:
                        await self.neo4j.execute_write("""
                            MERGE (c:Cluster {name: $cluster_name})
                            SET c.client_id = $client_id,
                                c.size = $size,
                                c.updated_at = datetime()
                            WITH c
                            MATCH (s:Stakeholder {id: $stakeholder_id})
                            MERGE (s)-[:MEMBER_OF]->(c)
                            RETURN c
                        """, {
                            "cluster_name": cluster_name,
                            "client_id": client_id,
                            "size": len(cluster),
                            "stakeholder_id": stakeholder_id,
                        })
                    except Exception as e:
                        logger.error(f"Failed to add stakeholder to cluster: {e}")

        except Exception as e:
            logger.error(f"Cluster detection failed: {e}")

        return result

    async def extract_all_meeting_concepts(self, client_id: str) -> dict:
        """
        Extract concepts from all meetings for a client.

        Args:
            client_id: Client ID

        Returns:
            Dict with extraction statistics
        """
        result = {"meetings_processed": 0, "total_concepts": 0, "errors": 0}

        try:
            response = self.supabase.table("meeting_transcripts") \
                .select("id") \
                .eq("client_id", client_id) \
                .execute()

            meetings = response.data or []
            logger.info(f"Extracting concepts from {len(meetings)} meetings")

            for meeting in meetings:
                extraction = await self.extract_concepts_from_meeting(meeting["id"])
                result["meetings_processed"] += 1
                result["total_concepts"] += extraction["concepts_created"]
                result["errors"] += extraction["errors"]

        except Exception as e:
            logger.error(f"Batch concept extraction failed: {e}")
            result["errors"] += 1

        return result

    # =========================================================================
    # Private Helper Methods
    # =========================================================================

    async def _get_stakeholders_with_meetings(self, client_id: str) -> dict:
        """Get stakeholders with their meeting attendance info."""
        stakeholders = {}

        # Get stakeholders
        response = self.supabase.table("stakeholders") \
            .select("id, name, role, organization") \
            .eq("client_id", client_id) \
            .execute()

        for s in response.data or []:
            stakeholders[s["id"]] = {
                **s,
                "meetings": []
            }

        # Get meeting attendance from Neo4j
        attendance = await self.neo4j.execute_query("""
            MATCH (s:Stakeholder {client_id: $client_id})-[:ATTENDED]->(m:Meeting)
            RETURN s.id as stakeholder_id, collect(m.id) as meeting_ids
        """, {"client_id": client_id})

        for record in attendance:
            s_id = record["stakeholder_id"]
            if s_id in stakeholders:
                stakeholders[s_id]["meetings"] = record["meeting_ids"]

        return stakeholders

    def _calculate_co_attendance(self, stakeholders: dict) -> dict:
        """Calculate which stakeholders attend meetings together."""
        co_attendance = defaultdict(set)

        # Build meeting -> stakeholders lookup
        meeting_attendees = defaultdict(set)
        for s_id, s_data in stakeholders.items():
            for m_id in s_data.get("meetings", []):
                meeting_attendees[m_id].add(s_id)

        # Find pairs that attend the same meetings
        for m_id, attendees in meeting_attendees.items():
            attendee_list = list(attendees)
            for i in range(len(attendee_list)):
                for j in range(i + 1, len(attendee_list)):
                    pair = tuple(sorted([attendee_list[i], attendee_list[j]]))
                    co_attendance[pair].add(m_id)

        return co_attendance

    def _determine_influence_direction(
        self,
        s1: dict,
        s2: dict
    ) -> Optional[tuple[str, str]]:
        """
        Determine which stakeholder influences the other based on role.

        Returns:
            Tuple of (influencer_id, influenced_id) or None if unclear
        """
        # Role hierarchy keywords (higher = more senior)
        seniority_keywords = [
            ("chief", 5), ("ceo", 5), ("cto", 5), ("cfo", 5), ("coo", 5),
            ("vp", 4), ("vice president", 4),
            ("director", 3),
            ("head", 2), ("lead", 2), ("senior", 2),
            ("manager", 1),
        ]

        def get_seniority(role: str) -> int:
            if not role:
                return 0
            role_lower = role.lower()
            for keyword, score in seniority_keywords:
                if keyword in role_lower:
                    return score
            return 0

        s1_seniority = get_seniority(s1.get("role", ""))
        s2_seniority = get_seniority(s2.get("role", ""))

        if s1_seniority > s2_seniority:
            return (s1["id"], s2["id"])
        elif s2_seniority > s1_seniority:
            return (s2["id"], s1["id"])

        return None

    async def _extract_concepts_with_llm(self, content: str) -> list[dict]:
        """
        Use Claude to extract key concepts from meeting content.

        Args:
            content: Meeting transcript or summary

        Returns:
            List of concept dicts with name and category
        """
        # Truncate content if too long
        max_chars = 10000
        if len(content) > max_chars:
            content = content[:max_chars] + "..."

        try:
            message = self.anthropic.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": f"""Extract 3-7 key business concepts or topics from this meeting content.
Return them as a simple list, one per line, in format: concept_name | category

Categories should be one of: technology, finance, governance, legal, strategy, process, people

Meeting content:
{content}

Example output:
AI Implementation | technology
Budget Approval | finance
Data Security | governance"""
                }]
            )

            concepts = []
            response_text = message.content[0].text

            for line in response_text.strip().split("\n"):
                if "|" in line:
                    parts = line.split("|")
                    if len(parts) >= 2:
                        concepts.append({
                            "name": parts[0].strip().lower(),
                            "category": parts[1].strip().lower()
                        })

            return concepts

        except Exception as e:
            logger.error(f"LLM concept extraction failed: {e}")
            return []

    def _build_clusters_from_pairs(self, pairs: list) -> list[set]:
        """
        Build connected components (clusters) from stakeholder pairs.

        Uses Union-Find algorithm for efficient clustering.
        """
        parent = {}

        def find(x):
            if x not in parent:
                parent[x] = x
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]

        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py

        # Build union-find structure from pairs
        for pair in pairs:
            s1_id = pair.get("cluster_pair", pair).get("stakeholder1", {}).get("id")
            s2_id = pair.get("cluster_pair", pair).get("stakeholder2", {}).get("id")
            if s1_id and s2_id:
                union(s1_id, s2_id)

        # Group by root parent
        clusters = defaultdict(set)
        for s_id in parent:
            root = find(s_id)
            clusters[root].add(s_id)

        # Filter to clusters with 2+ members
        return [c for c in clusters.values() if len(c) >= 2]
