"""Coordinator Agent - Central Orchestrator for Thesis.

The Coordinator is the meta-agent that:
- Analyzes incoming queries to determine which specialists to consult
- Routes queries to appropriate specialist agents
- Synthesizes responses from multiple specialists into unified output
- Maintains seamless user experience (no visible agent switching)
- Enriches context with graph-based stakeholder network insights
"""

import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, AsyncGenerator, Optional

import anthropic

from repositories import agents as agents_repo
from .base_agent import AgentContext, AgentResponse, BaseAgent

logger = logging.getLogger(__name__)

# Optional graph integration - gracefully handle if Neo4j not configured
_graph_available = False
try:
    if os.getenv("NEO4J_URI") and os.getenv("NEO4J_PASSWORD"):
        from ..services.graph import GraphQueryService, get_neo4j_connection

        _graph_available = True
except ImportError:
    pass


class ConsultationMode(Enum):
    """How the coordinator should handle a query."""

    DIRECT = "direct"  # Coordinator answers directly (greetings, simple questions)
    SINGLE = "single"  # Route to a single specialist
    MULTI = "multi"  # Consult multiple specialists and synthesize


@dataclass
class ConsultationPlan:
    """Plan for how to handle a user query."""

    mode: ConsultationMode
    specialists: list[str]  # List of agent names to consult
    reasoning: str  # Why these specialists were chosen


class CoordinatorAgent(BaseAgent):
    """Thesis Coordinator - The central orchestrating agent.

    Presents as "Thesis" to users and seamlessly coordinates
    specialist agents behind the scenes.
    """

    # Map of specialist names to their expertise keywords
    SPECIALIST_DOMAINS = {
        # Original persona-aligned agents
        "atlas": [
            "research",
            "study",
            "trend",
            "case study",
            "best practice",
            "mckinsey",
            "bcg",
            "gartner",
            "forrester",
            "academic",
            "literature",
            "benchmark",
            "lean",
            "toyota",
            "operational excellence",
            "value stream",
        ],
        "capital": [
            "roi",
            "budget",
            "cost",
            "financial",
            "investment",
            "savings",
            "cfo",
            "finance",
            "business case",
            "payback",
            "revenue",
            "expense",
            "sox",
            "audit trail",
            "close cycle",
            "controller",
        ],
        "guardian": [
            "security",
            "governance",
            "compliance",
            "infrastructure",
            "it",
            "soc2",
            "gdpr",
            "hipaa",
            "policy",
            "risk",
            "audit",
            "ciso",
            "cio",
            "okta",
            "sso",
            "shadow it",
            "vendor security",
        ],
        "counselor": [
            "legal",
            "contract",
            "liability",
            "ip",
            "intellectual property",
            "licensing",
            "terms",
            "agreement",
            "lawyer",
            "counsel",
            "dpa",
            "hallucination",
            "bias",
            "prompt drift",
            "data privacy",
        ],
        "oracle": [
            "transcript",
            "meeting",
            "sentiment",
            "stakeholder analysis",
            "attendee",
            "recording",
            "call notes",
        ],
        "sage": [
            "people",
            "change management",
            "adoption",
            "resistance",
            "fear",
            "anxiety",
            "burnout",
            "champion",
            "community",
            "culture",
            "human",
            "flourishing",
            "psychology",
            "safety",
            "overwhelm",
            "support",
            "morale",
            "engagement",
            "people-first",
            "human-centered",
            "meaningful work",
            "team",
            "employee",
        ],
        # New consulting/implementation agents
        "strategist": [
            "executive",
            "c-suite",
            "ceo",
            "board",
            "sponsor",
            "sponsorship",
            "stakeholder management",
            "coalition",
            "organizational politics",
            "governance structure",
            "strategic alignment",
            "business strategy",
            "executive buy-in",
            "leadership",
            "transformation",
        ],
        "architect": [
            "architecture",
            "integration",
            "api",
            "technical design",
            "build vs buy",
            "rag",
            "vector",
            "embedding",
            "mlops",
            "devops",
            "infrastructure",
            "microservices",
            "data pipeline",
            "system design",
            "technical",
        ],
        "operator": [
            "process",
            "workflow",
            "automation",
            "metrics",
            "kpi",
            "baseline",
            "exception",
            "sop",
            "operations",
            "efficiency",
            "throughput",
            "bottleneck",
            "ground level",
            "frontline",
            "day-to-day",
        ],
        "pioneer": [
            "emerging",
            "innovation",
            "r&d",
            "new technology",
            "cutting edge",
            "experimental",
            "prototype",
            "hype",
            "maturity",
            "readiness",
            "quantum",
            "future",
            "horizon",
            "scout",
            "evaluate",
        ],
        # Internal enablement agents
        "catalyst": [
            "internal communications",
            "messaging",
            "narrative",
            "employee engagement",
            "announcement",
            "all-hands",
            "town hall",
            "internal marketing",
            "ai anxiety",
            "fear communication",
            "transparency",
            "email",
        ],
        "scholar": [
            "training",
            "learning",
            "l&d",
            "enablement",
            "curriculum",
            "course",
            "workshop",
            "certification",
            "champion program",
            "skill development",
            "adult learning",
            "capability building",
            "onboarding",
        ],
        # Systems thinking agent
        "nexus": [
            "systems thinking",
            "feedback loop",
            "leverage point",
            "unintended consequences",
            "interconnection",
            "complexity",
            "second-order effect",
            "system dynamics",
            "archetype",
            "reinforcing loop",
            "balancing loop",
            "mental model",
            "paradigm",
            "root cause",
            "holistic",
            "emergent",
            "ripple effect",
        ],
        # Brand voice agent
        "echo": [
            "brand voice",
            "style",
            "tone",
            "voice analysis",
            "ai emulation",
            "writing style",
            "voice profile",
            "brand guidelines",
            "tone of voice",
            "style guide",
            "communication style",
            "brand consistency",
            "voice cloning",
            "voice match",
        ],
        # Personal development agent
        "compass": [
            "career",
            "performance",
            "win",
            "accomplishment",
            "check-in",
            "1:1",
            "one on one",
            "review",
            "promotion",
            "goal tracking",
            "reflection",
            "growth",
            "achievement",
            "manager conversation",
            "feedback",
            "competency",
            "strategic alignment",
            "professional development",
            "win log",
            "impact",
            "tracker",
        ],
        # Task management agent
        "taskmaster": [
            "task",
            "tasks",
            "to do",
            "to-do",
            "action item",
            "action items",
            "what should i work on",
            "my tasks",
            "my priorities",
            "deliverable",
            "deliverables",
            "assignment",
            "overdue",
            "due today",
            "due date",
            "slippage",
            "blocked",
            "follow up",
            "follow-up",
            "commitment",
            "what do i need to do",
            "what's on my plate",
            "focus",
            "today's work",
        ],
    }

    def __init__(
        self,
        anthropic_client: anthropic.Anthropic,
        specialists: Optional[dict[str, BaseAgent]] = None,
    ):
        super().__init__(
            name="coordinator",
            display_name="Thesis",
            anthropic_client=anthropic_client,
        )
        self._specialists = specialists or {}

    def register_specialist(self, name: str, agent: BaseAgent) -> None:
        """Register a specialist agent with the coordinator."""
        self._specialists[name] = agent
        logger.info(f"Registered specialist: {name}")

    def get_specialist(self, name: str) -> Optional[BaseAgent]:
        """Get a specialist agent by name."""
        return self._specialists.get(name)

    async def reload_specialist_instruction(self, name: str) -> bool:
        """Reload a specialist's instruction from the database.

        Used for hot-reloading after instruction updates in admin UI.
        Returns True if reload was successful.
        """
        specialist = self._specialists.get(name)
        if specialist:
            return await specialist.reload_instruction()
        logger.warning(f"Specialist {name} not found for reload")
        return False

    async def reload_all_instructions(self) -> dict[str, bool]:
        """Reload instructions for all specialists.

        Returns dict of agent_name -> success.
        """
        results = {}
        for name, agent in self._specialists.items():
            results[name] = await agent.reload_instruction()
        # Also reload coordinator's own instruction
        results["coordinator"] = await self.reload_instruction()
        return results

    def _get_default_instruction(self) -> str:
        return """<system>.

<version>
Name: Thesis Coordinator
Version: 1.0
Date: 2025-01-26
Created_By: Charlie Fuller
</version>

<role>
You are Thesis, the central AI assistant for enterprise GenAI strategy implementation. You seamlessly coordinate specialized expertise to help consultants and enterprise teams navigate complex AI initiatives.

Core Mission: Synthesize insights across research, finance, governance, legal, and stakeholder domains to deliver unified, actionable guidance for GenAI success.
</role>

<capabilities>
## Stakeholder Perspective Agents (Persona-Aligned)

1. Research Intelligence (Atlas domain)
   - GenAI implementation trends and patterns
   - Consulting firm approaches and frameworks
   - Case studies and best practices
   - Lean/Toyota Production System thinking

2. Financial Analysis (Capital domain)
   - ROI calculations and projections
   - Budget justification and business cases
   - SOX compliance and audit trails
   - Close cycle optimization

3. Governance & Security (Guardian domain)
   - Security assessments for AI implementations
   - Compliance guidance (SOC2, GDPR, HIPAA)
   - Shadow IT risk management
   - Vendor security evaluation

4. Legal Considerations (Counselor domain)
   - Contract review and negotiation points
   - AI-specific risks (hallucination, bias, prompt drift)
   - Data processing agreements
   - Liability frameworks

5. Stakeholder Intelligence (Oracle domain)
   - Meeting transcript analysis
   - Sentiment extraction
   - Stakeholder mapping

6. People & Human Flourishing (Sage domain)
   - Human-centered change management
   - Addressing fear, resistance, and anxiety
   - Community building and psychological safety
   - Champion enablement without burnout

## Consulting/Implementation Agents

7. Executive Strategy (Strategist domain)
   - C-suite engagement and sponsorship
   - Organizational politics and coalition building
   - Business case development for executives
   - Governance structure design

8. Technical Architecture (Architect domain)
   - Enterprise AI architecture patterns (RAG, agents)
   - Integration design and data pipelines
   - Build vs. buy analysis
   - Security architecture and MLOps

9. Business Operations (Operator domain)
   - Process analysis and workflow optimization
   - Automation opportunity assessment
   - Operational metrics and KPIs
   - Ground-level change management

10. Innovation & R&D (Pioneer domain)
    - Emerging technology scouting
    - Technology maturity assessment
    - Hype cycle navigation
    - Innovation portfolio strategy

## Internal Enablement Agents

11. Internal Communications (Catalyst domain)
    - AI initiative messaging and narratives
    - Employee engagement communication
    - Addressing AI anxiety proactively
    - Multi-channel communication strategies

12. Learning & Development (Scholar domain)
    - AI training program design
    - Champion program enablement
    - Skill development and capability building
    - Adult learning and behavior change

## Systems Thinking Agent

13. Systems Thinking (Nexus domain)
    - Feedback loop identification and analysis
    - Leverage point identification
    - Unintended consequence anticipation
    - System archetype recognition
    - Second and third-order effect analysis
</capabilities>

<instructions>
## Response Architecture

### For Simple Queries
- Provide direct, concise answers
- Maintain professional consultative tone
- Focus on actionable insights

### For Domain-Specific Queries
- Draw on relevant specialist expertise
- Present unified perspective
- Include evidence and examples when available

### For Complex Cross-Domain Queries
- Synthesize insights from multiple domains
- Organize information logically
- Highlight connections and tensions
- Provide prioritized recommendations

## Communication Principles
- Be professional, strategic, and evidence-based
- Focus on "what to do next" not just "what to know"
- Consider organizational context (size, industry, maturity)
- Acknowledge uncertainty when appropriate
- Never mention internal specialist agents to users
</instructions>

<criteria>
## Response Quality Standards
- Evidence-Based: Recommendations backed by research and data
- Action-Oriented: Concrete next steps with realistic timelines
- Context-Aware: Tailored to user's specific situation
- Integrated: Multiple perspectives synthesized coherently
- Honest: Clear about limitations and uncertainty
</criteria>

</system>"""

    async def analyze_query(self, context: AgentContext) -> ConsultationPlan:
        """Analyze a user query to determine which specialists to consult.

        Uses Claude Haiku for fast, cost-effective classification.
        """
        message = context.user_message.lower()

        # Quick checks for direct handling
        if self._is_greeting_or_simple(message):
            return ConsultationPlan(
                mode=ConsultationMode.DIRECT,
                specialists=[],
                reasoning="Simple greeting or question - handling directly",
            )

        # Score each specialist based on keyword matching
        scores: dict[str, int] = {}
        for specialist, keywords in self.SPECIALIST_DOMAINS.items():
            score = sum(1 for kw in keywords if kw in message)
            if score > 0:
                scores[specialist] = score

        # If we have clear keyword matches, use those
        if scores:
            # Sort by score descending
            sorted_specialists = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

            # Take top specialists (max 3)
            top_specialists = sorted_specialists[:3]

            if len(top_specialists) == 1:
                return ConsultationPlan(
                    mode=ConsultationMode.SINGLE,
                    specialists=top_specialists,
                    reasoning=f"Query matches {top_specialists[0]} domain",
                )
            else:
                return ConsultationPlan(
                    mode=ConsultationMode.MULTI,
                    specialists=top_specialists,
                    reasoning=f"Query spans multiple domains: {', '.join(top_specialists)}",
                )

        # For complex queries, use Claude Haiku to classify
        return await self._classify_with_llm(context)

    def _is_greeting_or_simple(self, message: str) -> bool:
        """Check if message is a simple greeting or basic question."""
        greetings = [
            "hello",
            "hi",
            "hey",
            "good morning",
            "good afternoon",
            "good evening",
            "thanks",
            "thank you",
            "bye",
            "goodbye",
        ]
        simple_phrases = [
            "what can you do",
            "help me",
            "who are you",
            "what is thesis",
            "how does this work",
        ]

        for greeting in greetings:
            if message.strip().lower().startswith(greeting):
                return True
        for phrase in simple_phrases:
            if phrase in message.lower():
                return True
        return False

    async def _classify_with_llm(self, context: AgentContext) -> ConsultationPlan:
        """Use Claude Haiku for intelligent query classification."""
        classification_prompt = f"""Analyze this query and determine which specialist agents should handle it.

Available specialists (Stakeholder Perspectives):
- atlas: Research, trends, case studies, best practices, Lean/Toyota methodology
- capital: Financial analysis, ROI, budgets, SOX compliance, audit trails
- guardian: Security, governance, compliance, IT infrastructure, shadow IT
- counselor: Legal, contracts, AI risks (hallucination, bias), liability
- oracle: Meeting transcripts, stakeholder sentiment analysis
- sage: People, change management, adoption resistance, burnout, community, human flourishing

Available specialists (Consulting/Implementation):
- strategist: Executive engagement, C-suite sponsorship, organizational politics, governance design
- architect: Technical architecture, integration, build vs buy, RAG, MLOps, system design
- operator: Process optimization, automation, operational metrics, ground-level change
- pioneer: Emerging technology, innovation, hype filtering, technology maturity assessment

Available specialists (Internal Enablement):
- catalyst: Internal communications, employee messaging, AI announcements, addressing AI anxiety
- scholar: Training programs, L&D, skill development, champion enablement, adult learning

Available specialists (Systems Thinking):
- nexus: Systems thinking, feedback loops, leverage points, unintended consequences, system archetypes

Available specialists (Personal Development):
- compass: Career coaching, win capture, check-in preparation, performance tracking, goal progress, strategic alignment

Query: {context.user_message}

Respond with ONLY a JSON object (no markdown):
{{"specialists": ["agent1", "agent2"], "reasoning": "brief explanation"}}

If no specialists are needed (simple question), return:
{{"specialists": [], "reasoning": "direct response"}}"""

        try:
            response = self.anthropic.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=200,
                messages=[{"role": "user", "content": classification_prompt}],
            )

            import json

            result = json.loads(response.content[0].text)
            specialists = result.get("specialists", [])
            reasoning = result.get("reasoning", "LLM classification")

            if not specialists:
                return ConsultationPlan(mode=ConsultationMode.DIRECT, specialists=[], reasoning=reasoning)
            elif len(specialists) == 1:
                return ConsultationPlan(mode=ConsultationMode.SINGLE, specialists=specialists, reasoning=reasoning)
            else:
                return ConsultationPlan(
                    mode=ConsultationMode.MULTI,
                    specialists=specialists[:3],  # Max 3 specialists
                    reasoning=reasoning,
                )
        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
            # Fallback to Atlas for research-oriented response
            return ConsultationPlan(
                mode=ConsultationMode.SINGLE,
                specialists=["atlas"],
                reasoning="Fallback to Atlas due to classification error",
            )

    async def consult_specialist(self, specialist_name: str, context: AgentContext) -> Optional[AgentResponse]:
        """Consult a specialist agent and get their response."""
        specialist = self._specialists.get(specialist_name)
        if not specialist:
            logger.warning(f"Specialist {specialist_name} not registered")
            return None

        try:
            # Create enriched context for specialist
            enriched_context = AgentContext(
                user_id=context.user_id,
                client_id=context.client_id,
                conversation_id=context.conversation_id,
                message_history=context.message_history,
                user_message=context.user_message,
                handoff_context={"from_coordinator": True},
                memories=context.memories,
                stakeholders=context.stakeholders,
                kb_context=context.kb_context,
            )

            response = await specialist.process(enriched_context)

            # Log the handoff
            await self._log_handoff(context, specialist_name)

            return response
        except Exception as e:
            logger.error(f"Error consulting {specialist_name}: {e}")
            return None

    async def synthesize_responses(self, responses: list[tuple[str, AgentResponse]], context: AgentContext) -> str:
        """Synthesize multiple specialist responses into a unified output.

        Takes a list of (specialist_name, response) tuples and combines them.
        """
        if len(responses) == 1:
            return responses[0][1].content

        # Build synthesis prompt
        specialist_insights = "\n\n".join(
            [f"=== {name.upper()} PERSPECTIVE ===\n{resp.content}" for name, resp in responses]
        )

        synthesis_prompt = f"""You are synthesizing insights from multiple specialist perspectives into a single, coherent response.

The user asked: {context.user_message}

Here are the specialist perspectives:

{specialist_insights}

Create a unified response that:
1. Integrates all relevant insights without repeating information
2. Maintains a single voice (don't mention the specialists by name)
3. Organizes information logically
4. Highlights connections and tensions between perspectives
5. Provides actionable recommendations where appropriate

Your response should read as a single, coherent answer - not as separate sections."""

        response = self.anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{"role": "user", "content": synthesis_prompt}],
        )

        return response.content[0].text

    async def process(self, context: AgentContext) -> AgentResponse:
        """Main processing method for the Coordinator.

        1. Enrich context with graph data (if relevant)
        2. Analyze the query
        3. Consult appropriate specialists
        4. Synthesize responses if needed
        5. Return unified response
        """
        # Enrich context with graph data for stakeholder queries
        context = await self._enrich_context_with_graph(context)

        # Analyze the query
        plan = await self.analyze_query(context)
        logger.info(f"Consultation plan: {plan.mode.value} -> {plan.specialists}")

        # Handle based on mode
        if plan.mode == ConsultationMode.DIRECT:
            # Coordinator handles directly
            return await self._direct_response(context)

        elif plan.mode == ConsultationMode.SINGLE:
            # Single specialist
            specialist_name = plan.specialists[0]
            response = await self.consult_specialist(specialist_name, context)

            if response:
                return AgentResponse(
                    content=response.content,
                    agent_name=self.name,
                    agent_display_name=self.display_name,
                    save_to_memory=response.save_to_memory,
                    memory_content=response.memory_content,
                )
            else:
                # Fallback to direct response
                return await self._direct_response(context)

        else:  # MULTI
            # Consult multiple specialists
            responses: list[tuple[str, AgentResponse]] = []

            for specialist_name in plan.specialists:
                response = await self.consult_specialist(specialist_name, context)
                if response:
                    responses.append((specialist_name, response))

            if not responses:
                return await self._direct_response(context)

            # Synthesize responses
            synthesized = await self.synthesize_responses(responses, context)

            return AgentResponse(
                content=synthesized,
                agent_name=self.name,
                agent_display_name=self.display_name,
                save_to_memory=True,
                memory_content=f"Multi-specialist query: {context.user_message[:100]}...",
            )

    async def _direct_response(self, context: AgentContext) -> AgentResponse:
        """Handle query directly without specialist consultation."""
        messages = self._build_messages(context)

        # Include graph context in system prompt if available
        system_prompt = self.system_instruction
        if context.handoff_context and context.handoff_context.get("graph_summary"):
            system_prompt += context.handoff_context["graph_summary"]

        response = self.anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=system_prompt,
            messages=messages,
        )

        return AgentResponse(
            content=response.content[0].text,
            agent_name=self.name,
            agent_display_name=self.display_name,
        )

    async def stream(self, context: AgentContext) -> AsyncGenerator[str, None]:
        """Stream a response, handling multi-specialist synthesis.

        For multi-specialist queries, we collect responses first then stream synthesis.
        For direct/single queries, we stream directly.
        """
        # Enrich context with graph data
        context = await self._enrich_context_with_graph(context)

        plan = await self.analyze_query(context)

        if plan.mode == ConsultationMode.DIRECT:
            # Stream direct response
            async for chunk in self._stream_direct(context):
                yield chunk

        elif plan.mode == ConsultationMode.SINGLE:
            # Stream single specialist response
            specialist = self._specialists.get(plan.specialists[0])
            if specialist:
                async for chunk in specialist.stream(context):
                    yield chunk
                await self._log_handoff(context, plan.specialists[0])
            else:
                async for chunk in self._stream_direct(context):
                    yield chunk

        else:  # MULTI
            # Collect specialist responses first (can't stream this part)
            responses: list[tuple[str, AgentResponse]] = []

            for specialist_name in plan.specialists:
                response = await self.consult_specialist(specialist_name, context)
                if response:
                    responses.append((specialist_name, response))

            if not responses:
                async for chunk in self._stream_direct(context):
                    yield chunk
            else:
                # Stream the synthesis
                async for chunk in self._stream_synthesis(responses, context):
                    yield chunk

    async def _stream_direct(self, context: AgentContext) -> AsyncGenerator[str, None]:
        """Stream a direct response from the coordinator."""
        messages = self._build_messages(context)

        # Include graph context in system prompt if available
        system_prompt = self.system_instruction
        if context.handoff_context and context.handoff_context.get("graph_summary"):
            system_prompt += context.handoff_context["graph_summary"]

        with self.anthropic.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=system_prompt,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                yield text

    async def _stream_synthesis(
        self, responses: list[tuple[str, AgentResponse]], context: AgentContext
    ) -> AsyncGenerator[str, None]:
        """Stream the synthesis of multiple specialist responses."""
        specialist_insights = "\n\n".join(
            [f"=== {name.upper()} PERSPECTIVE ===\n{resp.content}" for name, resp in responses]
        )

        synthesis_prompt = f"""You are synthesizing insights from multiple specialist perspectives into a single, coherent response.

The user asked: {context.user_message}

Here are the specialist perspectives:

{specialist_insights}

Create a unified response that:
1. Integrates all relevant insights without repeating information
2. Maintains a single voice (don't mention the specialists by name)
3. Organizes information logically
4. Highlights connections and tensions between perspectives
5. Provides actionable recommendations where appropriate

Your response should read as a single, coherent answer - not as separate sections."""

        with self.anthropic.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{"role": "user", "content": synthesis_prompt}],
        ) as stream:
            for text in stream.text_stream:
                yield text

    async def _log_handoff(self, context: AgentContext, to_specialist: str) -> None:
        """Log a handoff to a specialist agent."""
        try:
            # Get specialist agent ID
            specialist_record = agents_repo.get_agent_by_name(to_specialist)
            to_agent_id = specialist_record["id"] if specialist_record else None

            agents_repo.create_agent_handoff(
                {
                    "conversation_id": context.conversation_id,
                    "from_agent_id": self._agent_id,
                    "to_agent_id": to_agent_id,
                    "reason": f"Query routed to {to_specialist}",
                    "context": {"query_preview": context.user_message[:200]},
                    "status": "completed",
                }
            )
        except Exception as e:
            logger.error(f"Failed to log handoff: {e}")

    # =========================================================================
    # Graph Integration Methods
    # =========================================================================

    def _should_use_graph(self, message: str) -> bool:
        """Determine if the query would benefit from graph context.

        Returns True for stakeholder-related, influence, or network queries.
        """
        graph_keywords = [
            "influence",
            "network",
            "relationship",
            "connected",
            "reports to",
            "who knows",
            "path to",
            "reach",
            "blocker",
            "blocking",
            "champion",
            "supporter",
            "aligned",
            "concern",
            "shared concern",
            "stakeholder",
        ]
        message_lower = message.lower()
        return any(kw in message_lower for kw in graph_keywords)

    async def _get_graph_context(self, context: AgentContext) -> dict[str, Any]:
        """Fetch relevant graph context for stakeholder queries.

        Returns dict with influence network, key influencers, shared concerns, etc.
        """
        if not _graph_available:
            return {}

        try:
            connection = await get_neo4j_connection()
            query_service = GraphQueryService(connection)
            graph_context = {}

            message_lower = context.user_message.lower()

            # Get key influencers for general stakeholder queries
            if "influencer" in message_lower or "key stakeholder" in message_lower:
                influencers = await query_service.find_key_influencers(context.client_id, limit=5)
                if influencers:
                    graph_context["key_influencers"] = influencers

            # Get shared concerns
            if "concern" in message_lower or "issue" in message_lower or "problem" in message_lower:
                concerns = await query_service.find_shared_concerns(context.client_id, min_stakeholders=2)
                if concerns:
                    graph_context["shared_concerns"] = concerns[:5]

            # If specific stakeholder is mentioned, get their network
            if context.stakeholders:
                # Use first stakeholder for network context
                stakeholder = context.stakeholders[0]
                stakeholder_id = stakeholder.get("id")
                if stakeholder_id:
                    network = await query_service.get_stakeholder_network(stakeholder_id, depth=2)
                    if network.get("connected"):
                        graph_context["stakeholder_network"] = network

            # Get graph stats for context
            stats = await query_service.get_graph_stats(context.client_id)
            if stats.get("nodes", {}).get("stakeholders", 0) > 0:
                graph_context["network_stats"] = stats

            return graph_context

        except Exception as e:
            logger.warning(f"Failed to get graph context: {e}")
            return {}

    def _format_graph_context(self, graph_context: dict[str, Any]) -> str:
        """Format graph context as a string for inclusion in prompts."""
        if not graph_context:
            return ""

        parts = ["\n\n--- STAKEHOLDER NETWORK INTELLIGENCE ---\n"]

        if "key_influencers" in graph_context:
            parts.append("\n**Key Influencers:**")
            for inf in graph_context["key_influencers"][:5]:
                parts.append(f"- {inf['name']} ({inf['role']}) - Influence Score: {inf.get('influence_score', 'N/A')}")

        if "shared_concerns" in graph_context:
            parts.append("\n**Shared Concerns Across Stakeholders:**")
            for concern in graph_context["shared_concerns"][:3]:
                stakeholder_names = [s["name"] for s in concern.get("stakeholders", [])]
                parts.append(
                    f'- "{concern["concern"]["content"][:100]}..." (raised by: {", ".join(stakeholder_names)})'
                )

        if "stakeholder_network" in graph_context:
            network = graph_context["stakeholder_network"]
            if network.get("center"):
                center = network["center"]
                parts.append(f"\n**Network for {center['name']}:**")
                parts.append(f"- Role: {center.get('role', 'Unknown')}")
                parts.append(f"- Connected to: {network.get('connection_count', 0)} stakeholders")
                if network.get("connected"):
                    connected_names = [c["name"] for c in network["connected"][:5]]
                    parts.append(f"- Key connections: {', '.join(connected_names)}")

        if "network_stats" in graph_context:
            stats = graph_context["network_stats"]
            nodes = stats.get("nodes", {})
            rels = stats.get("relationships", {})
            parts.append(
                f"\n**Network Overview:** {nodes.get('stakeholders', 0)} stakeholders, "
                f"{rels.get('influences', 0)} influence relationships, "
                f"{nodes.get('concerns', 0)} tracked concerns"
            )

        parts.append("\n--- END NETWORK INTELLIGENCE ---\n")
        return "\n".join(parts)

    async def _enrich_context_with_graph(self, context: AgentContext) -> AgentContext:
        """Enrich the agent context with graph-based insights.

        Called before processing stakeholder-related queries.
        """
        if not self._should_use_graph(context.user_message):
            return context

        graph_context = await self._get_graph_context(context)
        if not graph_context:
            return context

        # Add graph context to handoff_context for specialists
        enriched_handoff = context.handoff_context or {}
        enriched_handoff["graph_context"] = graph_context
        enriched_handoff["graph_summary"] = self._format_graph_context(graph_context)

        return AgentContext(
            user_id=context.user_id,
            client_id=context.client_id,
            conversation_id=context.conversation_id,
            message_history=context.message_history,
            user_message=context.user_message,
            handoff_context=enriched_handoff,
            memories=context.memories,
            stakeholders=context.stakeholders,
        )
