"""
Graph Query Service

Provides high-level graph queries for agents and API endpoints.
Focuses on relationship traversal, influence networks, and pattern matching.
"""

import logging
from typing import Any, Optional

from .connection import Neo4jConnection

logger = logging.getLogger(__name__)


class GraphQueryService:
    """
    Service for executing graph queries.

    Provides methods for:
    - Influence network analysis
    - Stakeholder relationship queries
    - ROI blocker analysis
    - Concern pattern detection
    - Path finding between entities
    """

    def __init__(self, neo4j: Neo4jConnection):
        """
        Initialize the query service.

        Args:
            neo4j: Neo4j connection instance
        """
        self.neo4j = neo4j

    # =========================================================================
    # Influence Network Queries
    # =========================================================================

    async def get_influence_path(
        self,
        from_id: str,
        to_id: str,
        max_depth: int = 5
    ) -> dict[str, Any]:
        """
        Find the influence path between two stakeholders.

        Args:
            from_id: Source stakeholder ID
            to_id: Target stakeholder ID
            max_depth: Maximum path length

        Returns:
            Dict with path nodes and relationships
        """
        result = await self.neo4j.execute_query(f"""
            MATCH path = shortestPath(
                (a:Stakeholder {{id: $from_id}})-[:INFLUENCES|REPORTS_TO*..{max_depth}]-(b:Stakeholder {{id: $to_id}})
            )
            RETURN
                [n IN nodes(path) | {{
                    id: n.id,
                    name: n.name,
                    role: n.role,
                    organization: n.organization
                }}] as nodes,
                [r IN relationships(path) | {{
                    type: type(r),
                    strength: r.strength,
                    influence_type: r.influence_type
                }}] as relationships,
                length(path) as path_length
        """, {"from_id": from_id, "to_id": to_id})

        if result:
            return {
                "found": True,
                "path": result[0]
            }
        return {
            "found": False,
            "message": "No influence path found between stakeholders"
        }

    async def get_stakeholder_network(
        self,
        stakeholder_id: str,
        depth: int = 2
    ) -> dict[str, Any]:
        """
        Get the full network around a stakeholder.

        Args:
            stakeholder_id: Center stakeholder ID
            depth: How many hops to include

        Returns:
            Dict with center node, connected nodes, and relationships
        """
        result = await self.neo4j.execute_query(f"""
            MATCH (center:Stakeholder {{id: $stakeholder_id}})
            OPTIONAL MATCH (center)-[r:INFLUENCES|REPORTS_TO*1..{depth}]-(connected:Stakeholder)
            WITH center, collect(DISTINCT connected) as connected_list,
                 collect(DISTINCT r) as rel_list
            RETURN {{
                center: {{
                    id: center.id,
                    name: center.name,
                    role: center.role,
                    organization: center.organization,
                    sentiment_score: center.sentiment_score
                }},
                connected: [c IN connected_list | {{
                    id: c.id,
                    name: c.name,
                    role: c.role,
                    organization: c.organization,
                    sentiment_score: c.sentiment_score
                }}],
                connection_count: size(connected_list)
            }} as network
        """, {"stakeholder_id": stakeholder_id})

        if result:
            return result[0]["network"]
        return {"center": None, "connected": [], "connection_count": 0}

    async def find_key_influencers(
        self,
        client_id: str,
        limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Find the most influential stakeholders based on network centrality.

        Args:
            client_id: Client ID to filter by
            limit: Maximum results to return

        Returns:
            List of stakeholders with influence metrics
        """
        result = await self.neo4j.execute_query("""
            MATCH (s:Stakeholder {client_id: $client_id})
            OPTIONAL MATCH (s)-[out:INFLUENCES]->()
            OPTIONAL MATCH ()-[in:INFLUENCES]->(s)
            OPTIONAL MATCH (s)-[:REPORTS_TO]->()
            OPTIONAL MATCH ()-[:REPORTS_TO]->(s)
            WITH s,
                 count(DISTINCT out) as influences_others,
                 count(DISTINCT in) as influenced_by,
                 sum(CASE WHEN out IS NOT NULL THEN coalesce(out.strength, 0.5) ELSE 0 END) as influence_strength
            RETURN {
                id: s.id,
                name: s.name,
                role: s.role,
                organization: s.organization,
                influences_others: influences_others,
                influenced_by: influenced_by,
                influence_score: influences_others * 2 + influenced_by + influence_strength,
                sentiment_score: s.sentiment_score
            } as stakeholder
            ORDER BY stakeholder.influence_score DESC
            LIMIT $limit
        """, {"client_id": client_id, "limit": limit})

        return [r["stakeholder"] for r in result]

    async def find_influence_chains(
        self,
        client_id: str,
        target_id: str,
        min_path_length: int = 2
    ) -> list[dict[str, Any]]:
        """
        Find all stakeholders who can influence a target through chains.

        Args:
            client_id: Client ID
            target_id: Target stakeholder ID
            min_path_length: Minimum path length (to exclude direct connections)

        Returns:
            List of influence chains
        """
        result = await self.neo4j.execute_query("""
            MATCH path = (source:Stakeholder {client_id: $client_id})
                         -[:INFLUENCES*2..4]->
                         (target:Stakeholder {id: $target_id})
            WHERE source <> target
            RETURN {
                source: {
                    id: source.id,
                    name: source.name,
                    role: source.role
                },
                path_length: length(path),
                intermediaries: [n IN nodes(path)[1..-1] | {
                    id: n.id,
                    name: n.name,
                    role: n.role
                }]
            } as chain
            ORDER BY length(path) ASC
            LIMIT 20
        """, {"client_id": client_id, "target_id": target_id})

        return [r["chain"] for r in result]

    # =========================================================================
    # ROI & Blocker Queries
    # =========================================================================

    async def get_roi_blockers(
        self,
        opportunity_id: str
    ) -> list[dict[str, Any]]:
        """
        Find all stakeholders blocking an ROI opportunity.

        Args:
            opportunity_id: ROI opportunity ID

        Returns:
            List of blockers with reasons and influence info
        """
        result = await self.neo4j.execute_query("""
            MATCH (s:Stakeholder)-[r:BLOCKS]->(o:ROIOpportunity {id: $opportunity_id})
            OPTIONAL MATCH ()-[influence:INFLUENCES]->(s)
            WITH s, r, count(influence) as influenced_by_count
            RETURN {
                stakeholder: {
                    id: s.id,
                    name: s.name,
                    role: s.role,
                    organization: s.organization,
                    sentiment_score: s.sentiment_score
                },
                block_reason: r.reason,
                influenced_by_count: influenced_by_count,
                priority: CASE
                    WHEN s.sentiment_score < 0.3 THEN 'high'
                    WHEN s.sentiment_score < 0.5 THEN 'medium'
                    ELSE 'low'
                END
            } as blocker
            ORDER BY blocker.priority DESC, influenced_by_count DESC
        """, {"opportunity_id": opportunity_id})

        return [r["blocker"] for r in result]

    async def get_roi_supporters(
        self,
        opportunity_id: str
    ) -> list[dict[str, Any]]:
        """
        Find all stakeholders supporting an ROI opportunity.

        Args:
            opportunity_id: ROI opportunity ID

        Returns:
            List of supporters with commitment levels
        """
        result = await self.neo4j.execute_query("""
            MATCH (s:Stakeholder)-[r:SUPPORTS]->(o:ROIOpportunity {id: $opportunity_id})
            OPTIONAL MATCH (s)-[influence:INFLUENCES]->()
            WITH s, r, count(influence) as influences_count
            RETURN {
                stakeholder: {
                    id: s.id,
                    name: s.name,
                    role: s.role,
                    organization: s.organization,
                    sentiment_score: s.sentiment_score
                },
                commitment_level: r.commitment_level,
                influences_count: influences_count
            } as supporter
            ORDER BY supporter.commitment_level DESC, influences_count DESC
        """, {"opportunity_id": opportunity_id})

        return [r["supporter"] for r in result]

    async def suggest_blocker_strategy(
        self,
        opportunity_id: str
    ) -> dict[str, Any]:
        """
        Suggest strategy for addressing ROI blockers.

        Finds supporters who can influence blockers.

        Args:
            opportunity_id: ROI opportunity ID

        Returns:
            Strategy with supporter-blocker influence paths
        """
        result = await self.neo4j.execute_query("""
            // Find blockers and supporters
            MATCH (blocker:Stakeholder)-[:BLOCKS]->(o:ROIOpportunity {id: $opportunity_id})
            MATCH (supporter:Stakeholder)-[:SUPPORTS]->(o)

            // Find influence paths from supporters to blockers
            OPTIONAL MATCH path = (supporter)-[:INFLUENCES*1..3]->(blocker)

            WITH blocker, supporter, path,
                 CASE WHEN path IS NOT NULL THEN length(path) ELSE null END as path_length

            RETURN {
                blocker: {
                    id: blocker.id,
                    name: blocker.name,
                    role: blocker.role
                },
                potential_advocates: collect(DISTINCT {
                    supporter: {
                        id: supporter.id,
                        name: supporter.name,
                        role: supporter.role
                    },
                    influence_path_length: path_length,
                    can_influence: path IS NOT NULL
                })
            } as strategy
        """, {"opportunity_id": opportunity_id})

        return {
            "opportunity_id": opportunity_id,
            "strategies": [r["strategy"] for r in result]
        }

    # =========================================================================
    # Concern Analysis Queries
    # =========================================================================

    async def find_shared_concerns(
        self,
        client_id: str,
        min_stakeholders: int = 2
    ) -> list[dict[str, Any]]:
        """
        Find concerns shared by multiple stakeholders.

        Args:
            client_id: Client ID
            min_stakeholders: Minimum stakeholders sharing concern

        Returns:
            List of shared concerns with stakeholder details
        """
        result = await self.neo4j.execute_query("""
            MATCH (s:Stakeholder {client_id: $client_id})-[:RAISED_CONCERN]->(c:Concern)
            WITH c, collect({
                id: s.id,
                name: s.name,
                role: s.role
            }) as stakeholders
            WHERE size(stakeholders) >= $min_stakeholders
            RETURN {
                concern: {
                    id: c.id,
                    content: c.content,
                    severity: c.severity
                },
                stakeholders: stakeholders,
                stakeholder_count: size(stakeholders)
            } as shared_concern
            ORDER BY shared_concern.stakeholder_count DESC
        """, {"client_id": client_id, "min_stakeholders": min_stakeholders})

        return [r["shared_concern"] for r in result]

    async def get_stakeholder_concerns(
        self,
        stakeholder_id: str
    ) -> list[dict[str, Any]]:
        """
        Get all concerns raised by a stakeholder.

        Args:
            stakeholder_id: Stakeholder ID

        Returns:
            List of concerns with meeting context
        """
        result = await self.neo4j.execute_query("""
            MATCH (s:Stakeholder {id: $stakeholder_id})-[r:RAISED_CONCERN]->(c:Concern)
            OPTIONAL MATCH (s)-[:ATTENDED]->(m:Meeting)
            WITH c, r, collect(DISTINCT {
                id: m.id,
                title: m.title,
                date: m.meeting_date
            }) as meetings
            RETURN {
                concern: {
                    id: c.id,
                    content: c.content,
                    severity: c.severity
                },
                quote: r.quote,
                related_meetings: meetings
            } as concern_detail
        """, {"stakeholder_id": stakeholder_id})

        return [r["concern_detail"] for r in result]

    # =========================================================================
    # Meeting & Concept Queries
    # =========================================================================

    async def get_meeting_network(
        self,
        meeting_id: str
    ) -> dict[str, Any]:
        """
        Get the stakeholder network from a meeting.

        Args:
            meeting_id: Meeting ID

        Returns:
            Meeting details with attendees and their relationships
        """
        result = await self.neo4j.execute_query("""
            MATCH (m:Meeting {id: $meeting_id})
            OPTIONAL MATCH (s:Stakeholder)-[a:ATTENDED]->(m)
            WITH m, collect({
                stakeholder: {
                    id: s.id,
                    name: s.name,
                    role: s.role,
                    sentiment_score: s.sentiment_score
                },
                meeting_sentiment: a.sentiment,
                speaking_time: a.speaking_time
            }) as attendees
            RETURN {
                meeting: {
                    id: m.id,
                    title: m.title,
                    date: m.meeting_date,
                    type: m.meeting_type
                },
                attendees: attendees,
                attendee_count: size(attendees)
            } as meeting_network
        """, {"meeting_id": meeting_id})

        if result:
            return result[0]["meeting_network"]
        return {"meeting": None, "attendees": [], "attendee_count": 0}

    async def find_concept_advocates(
        self,
        concept_name: str,
        client_id: str
    ) -> list[dict[str, Any]]:
        """
        Find stakeholders who advocate for a concept based on meeting participation.

        Args:
            concept_name: Concept name (e.g., "AI", "Security")
            client_id: Client ID

        Returns:
            List of stakeholders with advocacy metrics
        """
        result = await self.neo4j.execute_query("""
            MATCH (c:Concept {name: $concept_name})
            MATCH (m:Meeting)-[:DISCUSSES]->(c)
            MATCH (s:Stakeholder {client_id: $client_id})-[a:ATTENDED]->(m)
            WITH s, count(m) as meeting_count, avg(a.sentiment) as avg_sentiment
            WHERE meeting_count >= 1
            RETURN {
                id: s.id,
                name: s.name,
                role: s.role,
                organization: s.organization,
                meetings_discussing_concept: meeting_count,
                average_sentiment: avg_sentiment,
                advocacy_score: meeting_count * coalesce(avg_sentiment, 0.5)
            } as advocate
            ORDER BY advocate.advocacy_score DESC
        """, {"concept_name": concept_name, "client_id": client_id})

        return [r["advocate"] for r in result]

    # =========================================================================
    # Alignment Queries
    # =========================================================================

    async def find_aligned_stakeholders(
        self,
        stakeholder_id: str,
        min_shared_meetings: int = 2
    ) -> list[dict[str, Any]]:
        """
        Find stakeholders who are aligned (attend same meetings, similar sentiment).

        Args:
            stakeholder_id: Source stakeholder ID
            min_shared_meetings: Minimum meetings attended together

        Returns:
            List of aligned stakeholders
        """
        result = await self.neo4j.execute_query("""
            MATCH (s1:Stakeholder {id: $stakeholder_id})-[:ATTENDED]->(m:Meeting)<-[:ATTENDED]-(s2:Stakeholder)
            WHERE s1 <> s2
            WITH s1, s2, count(m) as shared_meetings,
                 abs(coalesce(s1.sentiment_score, 0.5) - coalesce(s2.sentiment_score, 0.5)) as sentiment_diff
            WHERE shared_meetings >= $min_shared_meetings
            RETURN {
                stakeholder: {
                    id: s2.id,
                    name: s2.name,
                    role: s2.role,
                    organization: s2.organization,
                    sentiment_score: s2.sentiment_score
                },
                shared_meetings: shared_meetings,
                sentiment_alignment: 1 - sentiment_diff,
                alignment_score: shared_meetings * (1 - sentiment_diff)
            } as aligned
            ORDER BY aligned.alignment_score DESC
        """, {"stakeholder_id": stakeholder_id, "min_shared_meetings": min_shared_meetings})

        return [r["aligned"] for r in result]

    # =========================================================================
    # Summary Statistics
    # =========================================================================

    async def get_graph_stats(self, client_id: str) -> dict[str, Any]:
        """
        Get summary statistics for a client's graph.

        Args:
            client_id: Client ID

        Returns:
            Dict with node and relationship counts in format expected by frontend:
            {
                nodes: { total: int, by_label: { label: count, ... } },
                relationships: { total: int, by_type: { type: count, ... } }
            }
        """
        # Helper to extract integer from Neo4j result (handles {low, high} format)
        def to_int(val) -> int:
            if val is None:
                return 0
            if isinstance(val, dict) and 'low' in val:
                return val['low']
            return int(val)

        # Get all node labels and their counts
        node_result = await self.neo4j.execute_query("""
            MATCH (n)
            RETURN labels(n)[0] as label, count(n) as count
            ORDER BY count DESC
        """)

        by_label = {}
        for record in node_result:
            label = record.get('label')
            count = to_int(record.get('count', 0))
            if label and count > 0:
                by_label[label] = count

        # Get all relationship types and their counts
        rel_result = await self.neo4j.execute_query("""
            MATCH ()-[r]->()
            RETURN type(r) as rel_type, count(r) as count
            ORDER BY count DESC
        """)

        by_type = {}
        for record in rel_result:
            rel_type = record.get('rel_type')
            count = to_int(record.get('count', 0))
            if rel_type and count > 0:
                by_type[rel_type] = count

        return {
            "nodes": {
                "total": sum(by_label.values()),
                "by_label": by_label
            },
            "relationships": {
                "total": sum(by_type.values()),
                "by_type": by_type
            }
        }

    # =========================================================================
    # Agent Coordination Queries
    # =========================================================================

    async def get_agent_for_concepts(
        self,
        concepts: list[str],
        limit: int = 1
    ) -> list[dict[str, Any]]:
        """
        Find the best agent(s) to handle a question based on concepts.

        Uses the EXPERT_IN relationships to match agents to topics.

        Args:
            concepts: List of concept names from the question
            limit: Maximum agents to return

        Returns:
            List of agents with relevance scores
        """
        # Match against both Expertise nodes (from agent sync) and Concept nodes (from document extraction)
        result = await self.neo4j.execute_query("""
            MATCH (a:Agent)-[e:EXPERT_IN]->(exp)
            WHERE (exp:Expertise OR exp:Concept)
              AND toLower(exp.name) IN $concepts
              AND a.is_active = true
            WITH a, sum(e.confidence) as relevance, collect(exp.name) as matched_concepts
            RETURN {
                id: a.id,
                name: a.name,
                display_name: a.display_name,
                relevance_score: relevance,
                matched_concepts: matched_concepts
            } as agent
            ORDER BY relevance DESC
            LIMIT $limit
        """, {"concepts": [c.lower() for c in concepts], "limit": limit})

        return [r["agent"] for r in result]

    async def get_agent_expertise(self, agent_id: str) -> dict[str, Any]:
        """
        Get the expertise areas for an agent.

        Args:
            agent_id: Agent ID

        Returns:
            Dict with agent info and expertise concepts
        """
        result = await self.neo4j.execute_query("""
            MATCH (a:Agent {id: $agent_id})
            OPTIONAL MATCH (a)-[e:EXPERT_IN]->(c:Concept)
            WITH a, collect({
                concept: c.name,
                category: c.category,
                confidence: e.confidence
            }) as expertise
            RETURN {
                id: a.id,
                name: a.name,
                display_name: a.display_name,
                description: a.description,
                expertise: expertise
            } as agent
        """, {"agent_id": agent_id})

        if result:
            return result[0]["agent"]
        return {}

    async def get_agent_handoff_patterns(self) -> list[dict[str, Any]]:
        """
        Analyze agent handoff patterns to understand collaboration flows.

        Returns:
            List of handoff patterns with frequency
        """
        result = await self.neo4j.execute_query("""
            MATCH (from:Agent)-[h:HANDED_OFF_TO]->(to:Agent)
            WITH from, to, count(h) as handoff_count,
                 collect(DISTINCT h.reason) as reasons
            RETURN {
                from_agent: {
                    id: from.id,
                    name: from.name,
                    display_name: from.display_name
                },
                to_agent: {
                    id: to.id,
                    name: to.name,
                    display_name: to.display_name
                },
                handoff_count: handoff_count,
                common_reasons: reasons[0..5]
            } as pattern
            ORDER BY handoff_count DESC
        """)

        return [r["pattern"] for r in result]

    async def suggest_agent_for_question(
        self,
        question: str,
        current_agent_id: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Suggest the best agent to handle a question.

        Extracts keywords and matches against agent expertise.

        Args:
            question: The user's question
            current_agent_id: Current agent (to exclude from suggestions)

        Returns:
            Dict with suggested agent and reasoning
        """
        # Extract potential concepts from question
        keywords = self._extract_keywords(question)

        # Find matching agents
        agents = await self.get_agent_for_concepts(keywords, limit=3)

        if not agents:
            return {
                "suggestion": None,
                "reason": "No matching agent found for the question topics"
            }

        # Filter out current agent if provided
        if current_agent_id:
            agents = [a for a in agents if a["id"] != current_agent_id]

        if not agents:
            return {
                "suggestion": None,
                "reason": "Current agent is the best match for this question"
            }

        top_agent = agents[0]
        return {
            "suggestion": top_agent,
            "reason": f"Agent '{top_agent['display_name']}' is expert in: {', '.join(top_agent['matched_concepts'])}",
            "alternatives": agents[1:] if len(agents) > 1 else []
        }

    def _extract_keywords(self, text: str) -> list[str]:
        """
        Extract potential topic keywords from text.

        Maps common question terms to expertise areas in the graph.
        """
        # Map keywords in questions to expertise names in the graph
        # Each expertise name maps to trigger words that might appear in questions
        keyword_triggers = {
            # Capital (Finance)
            "roi": ["roi", "return on investment", "payback"],
            "finance": ["finance", "financial", "money", "revenue"],
            "budget": ["budget", "cost", "expense", "spending"],
            "investment": ["investment", "invest", "funding"],
            "sox compliance": ["sox", "sarbanes"],
            "business case": ["business case", "justification"],
            "cost savings": ["cost savings", "save money", "reduce costs"],
            # Guardian (IT/Governance)
            "security": ["security", "secure", "protect"],
            "compliance": ["compliance", "compliant", "regulatory"],
            "governance": ["governance", "govern", "oversight"],
            "infrastructure": ["infrastructure", "it infrastructure"],
            "vendor evaluation": ["vendor", "evaluate vendor", "compare vendors"],
            "shadow it": ["shadow it", "unsanctioned"],
            "it": ["it department", "information technology"],
            # Counselor (Legal)
            "legal": ["legal", "lawyer", "attorney"],
            "contracts": ["contract", "agreement", "terms"],
            "liability": ["liability", "liable", "responsible"],
            "risk": ["risk", "risks", "risky"],
            "data privacy": ["privacy", "gdpr", "data protection", "pii"],
            "policy": ["policy", "policies"],
            # Sage (People/Change)
            "change management": ["change management", "change resistance", "organizational change"],
            "adoption": ["adoption", "adopt", "rollout", "implementation"],
            "culture": ["culture", "cultural"],
            "people": ["people", "employees", "staff", "workforce"],
            "human flourishing": ["flourishing", "wellbeing", "well-being"],
            "training": ["training", "train", "upskill"],
            # Scholar (L&D)
            "learning": ["learning", "education", "course"],
            "champion enablement": ["champion", "power user"],
            "adult learning": ["adult learning", "andragogy"],
            "development": ["development", "develop skills"],
            # Atlas (Research)
            "research": ["research", "study", "analysis", "findings"],
            "genai": ["ai", "genai", "artificial intelligence", "machine learning", "llm", "gpt", "claude"],
            "benchmarking": ["benchmark", "compare", "best practice"],
            "consulting": ["consulting", "consultant", "advisory"],
            "thought leadership": ["thought leadership", "insights"],
            "case studies": ["case study", "case studies", "example"],
            "lean methodology": ["lean", "methodology"],
            # Oracle (Meeting Intelligence)
            "meetings": ["meeting", "meetings"],
            "transcripts": ["transcript", "recording"],
            "sentiment": ["sentiment", "feeling", "mood"],
            "stakeholders": ["stakeholder", "stakeholders"],
            "insights": ["insights", "insight"],
            "dynamics": ["dynamics", "dynamic", "interaction"],
            # Architect (Technical)
            "architecture": ["architecture", "architectural", "design pattern"],
            "integration": ["integration", "integrate", "api"],
            "rag": ["rag", "retrieval", "vector"],
            "enterprise ai": ["enterprise ai", "enterprise-grade"],
            "build vs buy": ["build vs buy", "build or buy", "make or buy"],
            "technical": ["technical", "tech stack"],
            # Operator (Business Ops)
            "operations": ["operations", "operational"],
            "automation": ["automation", "automate", "automated"],
            "process": ["process", "workflow", "procedure"],
            "metrics": ["metrics", "kpi", "measurement"],
            "optimization": ["optimization", "optimize", "improve efficiency"],
            "workflow": ["workflow", "workflows"],
            # Pioneer (Innovation)
            "innovation": ["innovation", "innovative", "new technology"],
            "emerging technology": ["emerging", "cutting-edge", "new tech"],
            "hype": ["hype", "overhyped", "realistic"],
            "maturity assessment": ["maturity", "readiness"],
            "r&d": ["r&d", "research and development"],
            # Strategist (Executive)
            "strategy": ["strategy", "strategic", "roadmap"],
            "executive": ["executive", "c-suite", "ceo", "cfo", "cto", "cio"],
            "c-suite": ["c-suite", "board", "leadership"],
            "organizational": ["organizational", "org structure"],
            "politics": ["politics", "political", "stakeholder management"],
            # Catalyst (Communications)
            "communications": ["communications", "communicate", "messaging"],
            "messaging": ["messaging", "message", "announce"],
            "employee engagement": ["engagement", "engaged", "morale"],
            "ai anxiety": ["anxiety", "worried", "fear", "concern about ai"],
            "internal": ["internal", "internally"],
            # Echo (Brand Voice)
            "brand voice": ["brand voice", "brand identity"],
            "voice analysis": ["voice", "tone of voice"],
            "style": ["style", "writing style"],
            "tone": ["tone", "tonality"],
            "ai emulation": ["emulation", "emulate", "mimic"],
            # Nexus (Systems Thinking)
            "systems thinking": ["systems thinking", "systemic"],
            "interconnections": ["interconnection", "connected", "dependencies"],
            "feedback loops": ["feedback loop", "reinforcing", "balancing"],
            "leverage points": ["leverage point", "high impact"],
            "unintended consequences": ["unintended", "side effect", "ripple"],
            # Coordinator
            "coordination": ["coordinate", "coordination"],
            "orchestration": ["orchestrate", "orchestration"],
            "routing": ["route", "routing", "which agent"],
            "synthesis": ["synthesize", "synthesis", "combine"],
        }

        text_lower = text.lower()
        found_keywords = []

        for expertise, triggers in keyword_triggers.items():
            for trigger in triggers:
                if trigger in text_lower:
                    found_keywords.append(expertise)
                    break

        return list(set(found_keywords)) or ["genai"]  # Default to genai if nothing matches

    # =========================================================================
    # Meeting Room Context Queries
    # =========================================================================

    async def get_meeting_context(
        self,
        query: str,
        client_id: str,
        limit: int = 5
    ) -> dict[str, Any]:
        """
        Get relevant graph context for a meeting room discussion.

        Searches for:
        - Related stakeholders and their concerns
        - ROI opportunities connected to keywords
        - Influence networks relevant to the topic
        - Agent expertise matches

        Args:
            query: The user's message or topic
            client_id: Client ID for filtering
            limit: Max results per category

        Returns:
            Dict with stakeholders, concerns, roi_opportunities, and agent_suggestions
        """
        keywords = self._extract_keywords(query)

        result = {
            "keywords_detected": keywords,
            "stakeholders": [],
            "concerns": [],
            "roi_opportunities": [],
            "relationships": [],
            "agent_suggestions": []
        }

        try:
            # Get relevant stakeholders based on keywords
            stakeholders_result = await self.neo4j.execute_query("""
                MATCH (s:Stakeholder {client_id: $client_id})
                WHERE any(keyword IN $keywords WHERE
                    toLower(s.name) CONTAINS keyword OR
                    toLower(coalesce(s.role, '')) CONTAINS keyword OR
                    toLower(coalesce(s.organization, '')) CONTAINS keyword
                )
                RETURN {
                    id: s.id,
                    name: s.name,
                    role: s.role,
                    organization: s.organization,
                    sentiment_score: s.sentiment_score
                } as stakeholder
                LIMIT $limit
            """, {"client_id": client_id, "keywords": keywords, "limit": limit})

            result["stakeholders"] = [r["stakeholder"] for r in stakeholders_result]

            # Get shared concerns related to keywords
            concerns_result = await self.neo4j.execute_query("""
                MATCH (s:Stakeholder {client_id: $client_id})-[:RAISED_CONCERN]->(c:Concern)
                WHERE any(keyword IN $keywords WHERE toLower(c.content) CONTAINS keyword)
                WITH c, collect(DISTINCT {name: s.name, role: s.role}) as stakeholders
                RETURN {
                    content: c.content,
                    severity: c.severity,
                    raised_by: stakeholders
                } as concern
                ORDER BY c.severity DESC
                LIMIT $limit
            """, {"client_id": client_id, "keywords": keywords, "limit": limit})

            result["concerns"] = [r["concern"] for r in concerns_result]

            # Get ROI opportunities related to keywords
            roi_result = await self.neo4j.execute_query("""
                MATCH (o:ROIOpportunity)
                WHERE any(keyword IN $keywords WHERE
                    toLower(coalesce(o.name, '')) CONTAINS keyword OR
                    toLower(coalesce(o.description, '')) CONTAINS keyword OR
                    toLower(coalesce(o.category, '')) CONTAINS keyword
                )
                OPTIONAL MATCH (blocker:Stakeholder)-[:BLOCKS]->(o)
                OPTIONAL MATCH (supporter:Stakeholder)-[:SUPPORTS]->(o)
                WITH o,
                     collect(DISTINCT blocker.name) as blockers,
                     collect(DISTINCT supporter.name) as supporters
                RETURN {
                    name: o.name,
                    description: o.description,
                    estimated_value: o.estimated_value,
                    status: o.status,
                    blockers: blockers,
                    supporters: supporters
                } as opportunity
                LIMIT $limit
            """, {"keywords": keywords, "limit": limit})

            result["roi_opportunities"] = [r["opportunity"] for r in roi_result]

            # Get influence relationships between stakeholders
            relationships_result = await self.neo4j.execute_query("""
                MATCH (s1:Stakeholder {client_id: $client_id})-[r:INFLUENCES|REPORTS_TO]->(s2:Stakeholder)
                WHERE any(keyword IN $keywords WHERE
                    toLower(s1.name) CONTAINS keyword OR
                    toLower(s2.name) CONTAINS keyword OR
                    toLower(coalesce(s1.role, '')) CONTAINS keyword OR
                    toLower(coalesce(s2.role, '')) CONTAINS keyword
                )
                RETURN {
                    from_name: s1.name,
                    from_role: s1.role,
                    to_name: s2.name,
                    to_role: s2.role,
                    relationship: type(r),
                    strength: coalesce(r.strength, 0.5)
                } as relationship
                LIMIT $limit
            """, {"client_id": client_id, "keywords": keywords, "limit": limit})

            result["relationships"] = [r["relationship"] for r in relationships_result]

            # Get agent suggestions based on keywords
            agents_result = await self.get_agent_for_concepts(keywords, limit=3)
            result["agent_suggestions"] = agents_result

        except Exception as e:
            logger.warning(f"Error fetching graph context: {e}")
            # Return partial results on error

        return result

    def format_context_for_prompt(
        self,
        context: dict[str, Any]
    ) -> str:
        """
        Format graph context into a readable prompt section.

        Args:
            context: Result from get_meeting_context

        Returns:
            Formatted string for inclusion in agent prompts
        """
        sections = []

        if context.get("stakeholders"):
            stakeholder_lines = []
            for s in context["stakeholders"]:
                sentiment = s.get("sentiment_score") or 0.5
                sentiment_label = "positive" if sentiment > 0.6 else "neutral" if sentiment > 0.4 else "cautious"
                stakeholder_lines.append(
                    f"- {s['name']} ({s.get('role', 'Unknown role')}) - {sentiment_label}"
                )
            sections.append("RELEVANT STAKEHOLDERS:\n" + "\n".join(stakeholder_lines))

        if context.get("concerns"):
            concern_lines = []
            for c in context["concerns"]:
                raisers = ", ".join([p["name"] for p in c.get("raised_by", [])])
                severity = c.get("severity", "unknown")
                content = c.get("content", "")[:100]
                concern_lines.append(f"- [{severity}] {content}... (raised by: {raisers})")
            sections.append("SHARED CONCERNS:\n" + "\n".join(concern_lines))

        if context.get("roi_opportunities"):
            roi_lines = []
            for o in context["roi_opportunities"]:
                value = o.get("estimated_value", "TBD")
                status = o.get("status", "unknown")
                blockers = ", ".join([b for b in (o.get("blockers") or []) if b][:3]) or "none"
                roi_lines.append(f"- {o.get('name', 'Unnamed')}: ${value} ({status}) - blockers: {blockers}")
            sections.append("ROI OPPORTUNITIES:\n" + "\n".join(roi_lines))

        if context.get("relationships"):
            rel_lines = []
            for r in context["relationships"]:
                rel_type = (r.get("relationship") or "relates_to").lower().replace("_", " ")
                rel_lines.append(f"- {r['from_name']} {rel_type} {r['to_name']}")
            sections.append("STAKEHOLDER RELATIONSHIPS:\n" + "\n".join(rel_lines))

        if not sections:
            return ""

        return "\n\n".join(sections)
