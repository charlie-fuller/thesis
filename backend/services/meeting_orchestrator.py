"""
Meeting Orchestrator Service

Manages multi-agent conversations in meeting rooms:
- Determines which agents should respond to each user message
- Coordinates agent responses with proper attribution
- Streams responses with agent identification
- Tracks token usage and turn counts
- Creates vector embeddings for semantic search
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import AsyncGenerator, Optional
from uuid import UUID

import anthropic
from supabase import Client

from agents.base_agent import AgentContext, AgentResponse, BaseAgent

logger = logging.getLogger(__name__)

# Lazy import for embeddings to avoid crash if VOYAGE_API_KEY is not set
_embed_meeting_room_message = None

async def _get_embed_function():
    """Lazily load the embedding function."""
    global _embed_meeting_room_message
    if _embed_meeting_room_message is None:
        try:
            from services.embeddings import embed_meeting_room_message
            _embed_meeting_room_message = embed_meeting_room_message
        except Exception as e:
            logger.warning(f"Embeddings not available: {e}")
            _embed_meeting_room_message = lambda *args, **kwargs: None
    return _embed_meeting_room_message


@dataclass
class MeetingContext:
    """Extended context for meeting room interactions."""
    user_id: str
    client_id: str
    meeting_room_id: str
    user_message: str
    message_history: list[dict]
    participants: list[dict]  # List of participant info with agent details
    meeting_type: str  # 'collaboration' or 'meeting_prep'
    config: dict
    turn_number: int


@dataclass
class AgentTurn:
    """Represents a single agent's turn in the meeting."""
    agent_id: str
    agent_name: str
    agent_display_name: str
    content: str
    tokens_input: int
    tokens_output: int


@dataclass
class AutonomousContext:
    """Context for autonomous discussion mode."""
    topic: str
    total_rounds: int
    current_round: int
    speaking_order: str  # 'priority' or 'round_robin'
    last_speaker: Optional[str] = None
    round_messages: Optional[list[dict]] = None  # Messages from current round


class MeetingOrchestrator:
    """
    Orchestrates multi-agent conversations in meeting rooms.

    Responsibilities:
    - Analyze user messages to determine which agents should respond
    - Coordinate agent responses (sequential with streaming)
    - Track and store messages with proper attribution
    - Manage token budgets and turn counts
    """

    # Reuse the specialist domains from CoordinatorAgent
    SPECIALIST_DOMAINS = {
        "atlas": ["research", "study", "trend", "case study", "best practice", "mckinsey",
                  "bcg", "gartner", "forrester", "academic", "literature", "benchmark",
                  "lean", "toyota", "operational excellence", "value stream"],
        "fortuna": ["roi", "budget", "cost", "financial", "investment", "savings",
                   "cfo", "finance", "business case", "payback", "revenue", "expense",
                   "sox", "audit trail", "close cycle", "controller"],
        "guardian": ["security", "governance", "compliance", "infrastructure", "it",
                    "soc2", "gdpr", "hipaa", "policy", "risk", "audit", "ciso", "cio",
                    "okta", "sso", "shadow it", "vendor security"],
        "counselor": ["legal", "contract", "liability", "ip", "intellectual property",
                     "licensing", "terms", "agreement", "lawyer", "counsel", "dpa",
                     "hallucination", "bias", "prompt drift", "data privacy"],
        "oracle": ["transcript", "meeting", "sentiment", "stakeholder analysis",
                  "attendee", "recording", "call notes"],
        "sage": ["people", "change management", "adoption", "resistance", "fear", "anxiety",
                "burnout", "champion", "community", "culture", "human", "flourishing",
                "psychology", "safety", "overwhelm", "support", "morale", "engagement",
                "people-first", "human-centered", "meaningful work", "team", "employee"],
        "strategist": ["executive", "c-suite", "ceo", "board", "sponsor", "sponsorship",
                      "stakeholder management", "coalition", "organizational politics",
                      "governance structure", "strategic alignment", "business strategy",
                      "executive buy-in", "leadership", "transformation"],
        "architect": ["architecture", "integration", "api", "technical design", "build vs buy",
                     "rag", "vector", "embedding", "mlops", "devops", "infrastructure",
                     "microservices", "data pipeline", "system design", "technical"],
        "operator": ["process", "workflow", "automation", "metrics", "kpi", "baseline",
                    "exception", "sop", "operations", "efficiency", "throughput",
                    "bottleneck", "ground level", "frontline", "day-to-day"],
        "pioneer": ["emerging", "innovation", "r&d", "new technology", "cutting edge",
                   "experimental", "prototype", "hype", "maturity", "readiness",
                   "quantum", "future", "horizon", "scout", "evaluate"],
        "catalyst": ["internal communications", "messaging", "narrative", "employee engagement",
                    "announcement", "all-hands", "town hall", "internal marketing",
                    "ai anxiety", "fear communication", "transparency", "email"],
        "scholar": ["training", "learning", "l&d", "enablement", "curriculum", "course",
                   "workshop", "certification", "champion program", "skill development",
                   "adult learning", "capability building", "onboarding"],
        "nexus": ["systems thinking", "interconnection", "feedback loop", "leverage point",
                 "unintended consequence", "causal", "dependency", "ripple effect", "ecosystem",
                 "holistic", "systems dynamics", "second-order", "third-order", "complexity"],
        "echo": ["brand voice", "style", "tone", "voice analysis", "ai emulation", "writing style",
                "voice profile", "brand guidelines", "tone of voice", "style guide",
                "communication style", "brand consistency", "voice cloning", "voice match"]
    }

    def __init__(
        self,
        supabase: Client,
        anthropic_client: anthropic.Anthropic,
        agents: dict[str, BaseAgent]
    ):
        self.supabase = supabase
        self.anthropic = anthropic_client
        self.agents = agents

    def select_responding_agents(
        self,
        context: MeetingContext,
        max_agents: int = 3
    ) -> list[dict]:
        """
        Determine which agents from the meeting participants should respond.

        Uses keyword matching to score relevance. Falls back to all participants
        for very general questions.
        """
        message_lower = context.user_message.lower()
        participant_names = {p['agent_name'] for p in context.participants}

        # Score each participating agent based on keyword matching
        scores: dict[str, int] = {}
        for participant in context.participants:
            agent_name = participant['agent_name']
            keywords = self.SPECIALIST_DOMAINS.get(agent_name, [])
            score = sum(1 for kw in keywords if kw in message_lower)
            scores[agent_name] = score

        # Get agents with positive scores
        relevant_agents = [
            p for p in context.participants
            if scores.get(p['agent_name'], 0) > 0
        ]

        if relevant_agents:
            # Sort by score and take top agents
            relevant_agents.sort(
                key=lambda p: scores.get(p['agent_name'], 0),
                reverse=True
            )
            return relevant_agents[:max_agents]

        # If no clear matches, have all participants respond (limited)
        # For general questions, everyone gets a chance to weigh in
        return context.participants[:max_agents]

    def _build_meeting_system_prompt(
        self,
        agent_name: str,
        agent_display_name: str,
        context: MeetingContext,
        base_instruction: str,
        other_participants: list[str]
    ) -> str:
        """Build a meeting-aware system prompt for an agent."""
        meeting_context = f"""

--- MEETING CONTEXT ---
You are participating in a multi-agent meeting discussion.
Meeting Type: {context.meeting_type}
Other participants in this meeting: {', '.join(other_participants)}

Guidelines for meeting participation:
1. Focus on your domain expertise - don't repeat what others might say
2. Reference other participants when relevant: "Building on what [Agent] mentioned..."
3. If the question isn't relevant to your domain, you can say so briefly and yield
4. For meeting_prep meetings, help prepare the user with talking points and anticipate concerns

SMART BREVITY FORMAT (required):
- Lead with the headline: Start with your key insight or recommendation in the first sentence
- Use bullet points for lists of 3+ items
- Bold key terms and important numbers using **bold**
- Keep responses to 150-300 words maximum - others are also responding
- One idea per paragraph, short paragraphs (2-3 sentences max)
- End with a clear next step or handoff if relevant

The user's message will follow. Respond from your perspective as {agent_display_name}.
--- END MEETING CONTEXT ---

"""
        return base_instruction + meeting_context

    async def process_meeting_turn(
        self,
        context: MeetingContext
    ) -> AsyncGenerator[dict, None]:
        """
        Process a user message and yield streaming responses from agents.

        Yields SSE-formatted events:
        - agent_turn_start: When an agent begins responding
        - agent_token: Individual tokens from agent response
        - agent_turn_end: When an agent finishes
        - round_complete: When all agents have responded
        - error: If something goes wrong
        """
        try:
            # Select which agents should respond
            responding_agents = self.select_responding_agents(context)

            if not responding_agents:
                yield {
                    "type": "error",
                    "message": "No agents available to respond"
                }
                return

            agents_responded = []
            total_tokens_input = 0
            total_tokens_output = 0

            # Store user message first
            await self._store_message(
                meeting_room_id=context.meeting_room_id,
                role="user",
                content=context.user_message,
                turn_number=context.turn_number
            )

            # Get list of other participant names for context
            all_participant_names = [p['agent_display_name'] for p in context.participants]

            # Process each responding agent sequentially with streaming
            for participant in responding_agents:
                agent_name = participant['agent_name']
                agent_display_name = participant['agent_display_name']
                agent_id = participant['agent_id']

                # Get the agent instance
                agent = self.agents.get(agent_name)
                if not agent:
                    logger.warning(f"Agent {agent_name} not found in registry")
                    continue

                # Signal turn start
                yield {
                    "type": "agent_turn_start",
                    "agent_name": agent_name,
                    "agent_display_name": agent_display_name,
                    "turn_number": context.turn_number
                }

                try:
                    # Build meeting-aware context for the agent
                    other_participants = [n for n in all_participant_names if n != agent_display_name]

                    meeting_system_prompt = self._build_meeting_system_prompt(
                        agent_name=agent_name,
                        agent_display_name=agent_display_name,
                        context=context,
                        base_instruction=agent.system_instruction,
                        other_participants=other_participants
                    )

                    # Collect response while streaming
                    full_response = ""
                    tokens_input = 0
                    tokens_output = 0

                    # Stream using Claude API directly with meeting context
                    messages = self._build_meeting_messages(context)

                    with self.anthropic.messages.stream(
                        model="claude-sonnet-4-20250514",
                        max_tokens=2048,  # Shorter for meeting responses
                        system=meeting_system_prompt,
                        messages=messages,
                    ) as stream:
                        for text in stream.text_stream:
                            full_response += text
                            yield {
                                "type": "agent_token",
                                "agent_name": agent_name,
                                "content": text
                            }

                        # Get final message for token counts
                        final_message = stream.get_final_message()
                        tokens_input = final_message.usage.input_tokens
                        tokens_output = final_message.usage.output_tokens

                    # Store the agent's response
                    await self._store_message(
                        meeting_room_id=context.meeting_room_id,
                        role="agent",
                        content=full_response,
                        agent_id=agent_id,
                        agent_name=agent_name,
                        agent_display_name=agent_display_name,
                        turn_number=context.turn_number,
                        metadata={"tokens": {"input": tokens_input, "output": tokens_output}}
                    )

                    # Update participant stats
                    await self._update_participant_stats(
                        meeting_room_id=context.meeting_room_id,
                        agent_id=agent_id,
                        tokens_used=tokens_output
                    )

                    total_tokens_input += tokens_input
                    total_tokens_output += tokens_output
                    agents_responded.append(agent_name)

                    # Signal turn end
                    yield {
                        "type": "agent_turn_end",
                        "agent_name": agent_name,
                        "tokens": {"input": tokens_input, "output": tokens_output}
                    }

                except Exception as e:
                    logger.error(f"Error getting response from {agent_name}: {e}")
                    yield {
                        "type": "error",
                        "agent_name": agent_name,
                        "message": str(e)
                    }

            # Update meeting room token total
            await self._update_meeting_tokens(
                context.meeting_room_id,
                total_tokens_input + total_tokens_output
            )

            # Signal round complete
            yield {
                "type": "round_complete",
                "agents_responded": agents_responded,
                "total_tokens": {
                    "input": total_tokens_input,
                    "output": total_tokens_output
                }
            }

        except Exception as e:
            logger.error(f"Meeting orchestration error: {e}")
            yield {
                "type": "error",
                "message": str(e)
            }

    def _build_meeting_messages(self, context: MeetingContext) -> list[dict]:
        """Build message history for Claude API from meeting context."""
        messages = []

        # Add conversation history
        for msg in context.message_history:
            # For agent messages, include attribution in content
            if msg.get("role") == "agent" and msg.get("agent_display_name"):
                content = f"[{msg['agent_display_name']}]: {msg['content']}"
                messages.append({"role": "assistant", "content": content})
            elif msg.get("role") == "user":
                messages.append({"role": "user", "content": msg["content"]})
            else:
                # System or other messages
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })

        # Add current user message
        messages.append({"role": "user", "content": context.user_message})

        return messages

    async def _store_message(
        self,
        meeting_room_id: str,
        role: str,
        content: str,
        agent_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        agent_display_name: Optional[str] = None,
        turn_number: Optional[int] = None,
        metadata: Optional[dict] = None
    ) -> Optional[str]:
        """Store a message in the meeting room and queue for embedding."""
        try:
            # Build insert data - core fields only
            insert_data = {
                "meeting_room_id": meeting_room_id,
                "role": role,
                "content": content,
                "agent_id": agent_id,
                "agent_name": agent_name,
                "agent_display_name": agent_display_name,
                "turn_number": turn_number,
                "metadata": metadata or {},
            }

            result = await asyncio.to_thread(
                lambda: self.supabase.table("meeting_room_messages").insert(insert_data).execute()
            )

            # Get the message ID for embedding
            if result.data and len(result.data) > 0:
                message_id = result.data[0].get("id")
                if message_id and role != "system":  # Skip system messages
                    # Queue embedding in background (don't await)
                    asyncio.create_task(
                        self._embed_message_background(message_id, content)
                    )
                return message_id
            return None

        except Exception as e:
            logger.error(f"Failed to store meeting message: {e}")
            return None

    async def _embed_message_background(
        self,
        message_id: str,
        content: str
    ) -> None:
        """Background task to embed a message."""
        try:
            await embed_meeting_room_message(
                self.supabase,
                UUID(message_id),
                content
            )
        except Exception as e:
            logger.warning(f"Background embedding failed for {message_id}: {e}")

    async def _update_participant_stats(
        self,
        meeting_room_id: str,
        agent_id: str,
        tokens_used: int
    ) -> None:
        """Update participant stats after a turn."""
        try:
            # Use RPC or direct SQL for increment operations
            await asyncio.to_thread(
                lambda: self.supabase.rpc(
                    "increment_meeting_participant_stats",
                    {
                        "p_meeting_room_id": meeting_room_id,
                        "p_agent_id": agent_id,
                        "p_tokens": tokens_used
                    }
                ).execute()
            )
        except Exception as e:
            # Fallback to manual update if RPC doesn't exist
            logger.warning(f"RPC not available, skipping participant stats update: {e}")

    async def _update_meeting_tokens(
        self,
        meeting_room_id: str,
        tokens: int
    ) -> None:
        """Update total tokens used in the meeting."""
        try:
            # Get current total
            result = await asyncio.to_thread(
                lambda: self.supabase.table("meeting_rooms")
                    .select("total_tokens_used")
                    .eq("id", meeting_room_id)
                    .single()
                    .execute()
            )

            current = result.data.get("total_tokens_used", 0) if result.data else 0

            await asyncio.to_thread(
                lambda: self.supabase.table("meeting_rooms")
                    .update({"total_tokens_used": current + tokens})
                    .eq("id", meeting_room_id)
                    .execute()
            )
        except Exception as e:
            logger.error(f"Failed to update meeting tokens: {e}")

    # =========================================================================
    # AUTONOMOUS DISCUSSION METHODS
    # =========================================================================

    # Agent expertise descriptions for inter-agent awareness
    AGENT_EXPERTISE_DESCRIPTIONS = {
        "atlas": "Research & Best Practices - GenAI implementation research, case studies, Lean methodology, industry benchmarks",
        "fortuna": "Financial Analysis & ROI - Business cases, cost savings, SOX compliance, investment analysis",
        "guardian": "Security & Governance - IT security, compliance, vendor evaluation, shadow IT, infrastructure",
        "counselor": "Legal & Compliance - Contracts, liability, data privacy, AI risk, regulatory",
        "oracle": "Meeting Intelligence - Transcript analysis, stakeholder dynamics, sentiment extraction",
        "sage": "People & Change - Change management, human flourishing, adoption, culture, training",
        "strategist": "Executive Strategy - C-suite engagement, organizational politics, governance structures",
        "architect": "Technical Architecture - Enterprise AI patterns, RAG, integrations, build vs. buy",
        "operator": "Business Operations - Process optimization, automation, operational metrics, workflows",
        "pioneer": "Innovation & R&D - Emerging technology, hype filtering, maturity assessment",
        "catalyst": "Internal Communications - AI messaging, employee engagement, AI anxiety",
        "scholar": "Learning & Development - Training programs, champion enablement, adult learning",
        "nexus": "Systems Thinking - Interconnections, feedback loops, leverage points, unintended consequences",
        "echo": "Brand Voice - Voice analysis, style profiling, AI emulation guidelines",
    }

    def _build_autonomous_system_prompt(
        self,
        agent_name: str,
        agent_display_name: str,
        context: MeetingContext,
        base_instruction: str,
        autonomous_context: AutonomousContext,
        other_participants: list[str]
    ) -> str:
        """Build a prompt for agent-to-agent discourse."""
        # Format recent responses from other agents
        recent_contributions = self._format_recent_contributions(
            autonomous_context.round_messages or [],
            exclude_agent=agent_name
        )

        # Build expertise directory for other participants
        participant_expertise = []
        for participant in context.participants:
            p_name = participant.get("agent_name")
            p_display = participant.get("agent_display_name")
            if p_name != agent_name and p_name in self.AGENT_EXPERTISE_DESCRIPTIONS:
                participant_expertise.append(
                    f"- **{p_display}**: {self.AGENT_EXPERTISE_DESCRIPTIONS[p_name]}"
                )

        expertise_directory = "\n".join(participant_expertise) if participant_expertise else "No other agents."

        # Round-specific guidance
        if autonomous_context.current_round == 1:
            round_guidance = """This is Round 1 - you are establishing initial positions on the topic.
Focus on: Your core perspective and key considerations from your domain."""
        elif autonomous_context.current_round == autonomous_context.total_rounds:
            round_guidance = """This is the FINAL ROUND - synthesize and conclude.
Focus on: Key takeaways, areas of agreement/disagreement, actionable recommendations."""
        else:
            round_guidance = f"""This is Round {autonomous_context.current_round} - the discussion is developing.
Focus on: Responding to what's been said, adding new dimensions, challenging assumptions."""

        discourse_context = f"""

--- AUTONOMOUS DISCUSSION MODE ---
You are in Round {autonomous_context.current_round} of {autonomous_context.total_rounds} in an agent-to-agent discussion.

DISCUSSION TOPIC: {autonomous_context.topic}

PARTICIPANT EXPERTISE DIRECTORY:
{expertise_directory}

{f"RECENT CONTRIBUTIONS FROM OTHER AGENTS:\\n{recent_contributions}" if recent_contributions else "You are the first to speak in this round."}

{round_guidance}

AGENT-TO-AGENT DISCOURSE GUIDELINES:
You are speaking TO other agents, not the user. The user is observing.

COMMUNICATION STYLE:
- Address other agents by name: "Fortuna, your ROI analysis is compelling, but..."
- Build on previous points: "Adding to what Guardian mentioned..."
- Respectfully disagree when warranted
- Synthesize across domains

DISCOURSE MOVES (in order of importance):
1. QUESTION: Ask clarifying questions to other agents - curiosity is KING! Seek to understand before responding.
2. CONNECT: Link ideas across different domains - find the threads between perspectives
3. CHALLENGE: Respectfully push back with alternative perspective - healthy debate is valuable
4. EXTEND: Build on another agent's point with additional depth
5. SYNTHESIZE: Combine multiple viewpoints into integrated insight

DEFERRING TO EXPERTS:
- You do NOT need to be the smartest agent in the room on every topic
- When a topic falls outside your expertise, DEFER to the specialist
- Examples:
  - For financial implications → defer to Fortuna
  - For security concerns → defer to Guardian
  - For legal questions → defer to Counselor
  - For people/adoption → defer to Sage
  - For technical architecture → defer to Architect
- Say: "I'll defer to [Agent] on this, but from my perspective..."

WHAT TO AVOID:
- Echoing what others said without adding value
- Overstepping into another agent's domain of expertise
- Ignoring relevant points from other agents
- Being overly agreeable (healthy debate is valuable)
- Trying to have an opinion on everything (stay in your lane!)

SMART BREVITY FORMAT (required):
- 150-300 words maximum
- Lead with your key insight
- Use bullet points for multiple points
- Bold key terms using **bold**
--- END AUTONOMOUS DISCUSSION MODE ---

"""
        return base_instruction + discourse_context

    def _format_recent_contributions(
        self,
        round_messages: list[dict],
        exclude_agent: str
    ) -> str:
        """Format recent agent contributions for context."""
        contributions = []
        for msg in round_messages:
            if msg.get("agent_name") != exclude_agent:
                agent_name = msg.get("agent_display_name", msg.get("agent_name", "Unknown"))
                content = msg.get("content", "")
                # Truncate long messages
                if len(content) > 500:
                    content = content[:500] + "..."
                contributions.append(f"**{agent_name}**: {content}")

        return "\n\n".join(contributions) if contributions else ""

    def _get_round_speakers(
        self,
        participants: list[dict],
        speaking_order: str,
        round_number: int
    ) -> list[dict]:
        """Get the ordered list of speakers for a round."""
        if speaking_order == "round_robin":
            # Rotate order based on round number
            offset = (round_number - 1) % len(participants)
            return participants[offset:] + participants[:offset]
        else:  # priority (default)
            # Sort by priority, then by name for consistency
            return sorted(
                participants,
                key=lambda p: (-p.get("priority", 0), p.get("agent_name", ""))
            )

    async def _check_for_user_interjection(
        self,
        meeting_room_id: str
    ) -> bool:
        """Check if user has sent a message during autonomous discussion."""
        try:
            result = await asyncio.to_thread(
                lambda: self.supabase.table("meeting_room_messages")
                    .select("id")
                    .eq("meeting_room_id", meeting_room_id)
                    .eq("role", "user")
                    .eq("pending_interjection", True)
                    .limit(1)
                    .execute()
            )
            return len(result.data) > 0 if result.data else False
        except Exception as e:
            logger.warning(f"Error checking for user interjection: {e}")
            return False

    async def _update_autonomous_config(
        self,
        meeting_room_id: str,
        config_update: dict
    ) -> None:
        """Update the autonomous discussion config in meeting room."""
        try:
            # Get current config
            result = await asyncio.to_thread(
                lambda: self.supabase.table("meeting_rooms")
                    .select("config")
                    .eq("id", meeting_room_id)
                    .single()
                    .execute()
            )

            current_config = result.data.get("config", {}) if result.data else {}
            autonomous_config = current_config.get("autonomous", {})
            autonomous_config.update(config_update)
            current_config["autonomous"] = autonomous_config

            await asyncio.to_thread(
                lambda: self.supabase.table("meeting_rooms")
                    .update({"config": current_config})
                    .eq("id", meeting_room_id)
                    .execute()
            )
        except Exception as e:
            logger.error(f"Failed to update autonomous config: {e}")

    async def process_autonomous_discussion(
        self,
        context: MeetingContext,
        topic: str,
        total_rounds: int,
        speaking_order: str = "priority"
    ) -> AsyncGenerator[dict, None]:
        """
        Run autonomous discussion for configured rounds.
        Yields SSE events as agents discuss.

        Events yielded:
        - discussion_round_start: Round N beginning
        - agent_turn_start: Agent begins responding
        - agent_token: Streaming token
        - agent_turn_end: Agent finishes
        - discussion_round_end: Round N complete
        - discussion_complete: All rounds finished
        - discussion_paused: User interjected or error
        """
        try:
            # Store the topic as a system message
            await self._store_message(
                meeting_room_id=context.meeting_room_id,
                role="system",
                content=f"[AUTONOMOUS DISCUSSION STARTED]\nTopic: {topic}\nRounds: {total_rounds}",
                turn_number=0,
                metadata={"autonomous": True, "topic": topic, "total_rounds": total_rounds}
            )

            # Update config to mark discussion as active
            await self._update_autonomous_config(
                context.meeting_room_id,
                {
                    "is_active": True,
                    "topic": topic,
                    "total_rounds": total_rounds,
                    "current_round": 0,
                    "speaking_order": speaking_order,
                    "is_paused": False
                }
            )

            all_participant_names = [p["agent_display_name"] for p in context.participants]
            total_tokens_input = 0
            total_tokens_output = 0

            for round_num in range(1, total_rounds + 1):
                # Update current round in config
                await self._update_autonomous_config(
                    context.meeting_room_id,
                    {"current_round": round_num, "agents_spoken_this_round": []}
                )

                # Signal round start
                yield {
                    "type": "discussion_round_start",
                    "round_number": round_num,
                    "total_rounds": total_rounds
                }

                # Get speaking order for this round
                speakers = self._get_round_speakers(
                    context.participants,
                    speaking_order,
                    round_num
                )

                round_messages: list[dict] = []

                for participant in speakers:
                    # Check for user interjection before each agent speaks
                    has_interjection = await self._check_for_user_interjection(
                        context.meeting_room_id
                    )
                    if has_interjection:
                        await self._update_autonomous_config(
                            context.meeting_room_id,
                            {"is_active": False, "is_paused": True}
                        )
                        yield {
                            "type": "discussion_paused",
                            "reason": "user_interjection",
                            "current_round": round_num
                        }
                        return

                    agent_name = participant["agent_name"]
                    agent_display_name = participant["agent_display_name"]
                    agent_id = participant["agent_id"]

                    # Get the agent instance
                    agent = self.agents.get(agent_name)
                    if not agent:
                        logger.warning(f"Agent {agent_name} not found in registry")
                        continue

                    # Signal turn start
                    yield {
                        "type": "agent_turn_start",
                        "agent_name": agent_name,
                        "agent_display_name": agent_display_name,
                        "turn_number": round_num
                    }

                    try:
                        # Build autonomous context
                        autonomous_ctx = AutonomousContext(
                            topic=topic,
                            total_rounds=total_rounds,
                            current_round=round_num,
                            speaking_order=speaking_order,
                            round_messages=round_messages
                        )

                        other_participants = [
                            n for n in all_participant_names if n != agent_display_name
                        ]

                        autonomous_system_prompt = self._build_autonomous_system_prompt(
                            agent_name=agent_name,
                            agent_display_name=agent_display_name,
                            context=context,
                            base_instruction=agent.system_instruction,
                            autonomous_context=autonomous_ctx,
                            other_participants=other_participants
                        )

                        # Build messages with topic and round context
                        messages = self._build_autonomous_messages(
                            context, topic, round_messages
                        )

                        # Stream response
                        full_response = ""
                        tokens_input = 0
                        tokens_output = 0

                        with self.anthropic.messages.stream(
                            model="claude-sonnet-4-20250514",
                            max_tokens=1024,  # Shorter for autonomous responses
                            system=autonomous_system_prompt,
                            messages=messages,
                        ) as stream:
                            for text in stream.text_stream:
                                full_response += text
                                yield {
                                    "type": "agent_token",
                                    "agent_name": agent_name,
                                    "content": text
                                }

                            final_message = stream.get_final_message()
                            tokens_input = final_message.usage.input_tokens
                            tokens_output = final_message.usage.output_tokens

                        # Determine responding_to (last speaker)
                        responding_to = round_messages[-1]["agent_name"] if round_messages else None

                        # Store the agent's response
                        await self._store_autonomous_message(
                            meeting_room_id=context.meeting_room_id,
                            content=full_response,
                            agent_id=agent_id,
                            agent_name=agent_name,
                            agent_display_name=agent_display_name,
                            discussion_round=round_num,
                            responding_to_agent=responding_to,
                            metadata={
                                "tokens": {"input": tokens_input, "output": tokens_output},
                                "autonomous": True
                            }
                        )

                        # Update participant stats
                        await self._update_participant_stats(
                            meeting_room_id=context.meeting_room_id,
                            agent_id=agent_id,
                            tokens_used=tokens_output
                        )

                        total_tokens_input += tokens_input
                        total_tokens_output += tokens_output

                        # Add to round messages for next agent's context
                        round_messages.append({
                            "agent_name": agent_name,
                            "agent_display_name": agent_display_name,
                            "content": full_response
                        })

                        # Signal turn end
                        yield {
                            "type": "agent_turn_end",
                            "agent_name": agent_name,
                            "tokens": {"input": tokens_input, "output": tokens_output},
                            "full_response": full_response
                        }

                    except Exception as e:
                        logger.error(f"Error in autonomous turn from {agent_name}: {e}")
                        yield {
                            "type": "error",
                            "agent_name": agent_name,
                            "message": str(e)
                        }

                # Signal round end
                yield {
                    "type": "discussion_round_end",
                    "round_number": round_num,
                    "agents_responded": [p["agent_name"] for p in speakers]
                }

            # Update meeting room token total
            await self._update_meeting_tokens(
                context.meeting_room_id,
                total_tokens_input + total_tokens_output
            )

            # Mark discussion as complete
            await self._update_autonomous_config(
                context.meeting_room_id,
                {"is_active": False, "is_paused": False}
            )

            # Store completion message
            await self._store_message(
                meeting_room_id=context.meeting_room_id,
                role="system",
                content=f"[AUTONOMOUS DISCUSSION COMPLETED]\n{total_rounds} rounds completed.",
                turn_number=total_rounds + 1,
                metadata={
                    "autonomous": True,
                    "discussion_complete": True,
                    "total_tokens": total_tokens_input + total_tokens_output
                }
            )

            # Signal discussion complete
            yield {
                "type": "discussion_complete",
                "total_rounds_completed": total_rounds,
                "total_tokens": {
                    "input": total_tokens_input,
                    "output": total_tokens_output
                }
            }

        except Exception as e:
            logger.error(f"Autonomous discussion error: {e}")
            await self._update_autonomous_config(
                context.meeting_room_id,
                {"is_active": False, "is_paused": True}
            )
            yield {
                "type": "discussion_paused",
                "reason": "error",
                "current_round": 0
            }
            yield {
                "type": "error",
                "message": str(e)
            }

    def _build_autonomous_messages(
        self,
        context: MeetingContext,
        topic: str,
        round_messages: list[dict]
    ) -> list[dict]:
        """Build message history for autonomous discussion."""
        messages = []

        # Add previous conversation history (from regular chat)
        for msg in context.message_history[-10:]:  # Limit history for token efficiency
            if msg.get("role") == "agent" and msg.get("agent_display_name"):
                content = f"[{msg['agent_display_name']}]: {msg['content']}"
                messages.append({"role": "assistant", "content": content})
            elif msg.get("role") == "user":
                messages.append({"role": "user", "content": msg["content"]})

        # Add the topic as the current user message
        topic_prompt = f"""The user has asked you to discuss the following topic with the other agents:

TOPIC: {topic}

Please share your perspective and engage with what other agents have said."""

        if round_messages:
            # Add current round's messages
            for rm in round_messages:
                content = f"[{rm['agent_display_name']}]: {rm['content']}"
                messages.append({"role": "assistant", "content": content})
            # Prompt for next response
            messages.append({"role": "user", "content": "Continue the discussion. Respond to what other agents have said."})
        else:
            messages.append({"role": "user", "content": topic_prompt})

        return messages

    async def _store_autonomous_message(
        self,
        meeting_room_id: str,
        content: str,
        agent_id: str,
        agent_name: str,
        agent_display_name: str,
        discussion_round: int,
        responding_to_agent: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> Optional[str]:
        """Store an autonomous discussion message and queue for embedding."""
        try:
            # Build insert data - core fields only (avoid columns that might not exist)
            insert_data = {
                "meeting_room_id": meeting_room_id,
                "role": "agent",
                "content": content,
                "agent_id": agent_id,
                "agent_name": agent_name,
                "agent_display_name": agent_display_name,
                "turn_number": discussion_round,
                "metadata": metadata or {},
            }

            result = await asyncio.to_thread(
                lambda: self.supabase.table("meeting_room_messages").insert(insert_data).execute()
            )

            # Get the message ID for embedding
            if result.data and len(result.data) > 0:
                message_id = result.data[0].get("id")
                if message_id:
                    # Queue embedding in background (don't await)
                    asyncio.create_task(
                        self._embed_message_background(message_id, content)
                    )
                return message_id
            return None

        except Exception as e:
            logger.error(f"Failed to store autonomous message: {e}")
            return None

    async def stop_autonomous_discussion(
        self,
        meeting_room_id: str
    ) -> None:
        """Stop an ongoing autonomous discussion."""
        await self._update_autonomous_config(
            meeting_room_id,
            {"is_active": False, "is_paused": True}
        )

        await self._store_message(
            meeting_room_id=meeting_room_id,
            role="system",
            content="[AUTONOMOUS DISCUSSION STOPPED BY USER]",
            metadata={"autonomous": True, "stopped": True}
        )

    async def get_autonomous_status(
        self,
        meeting_room_id: str
    ) -> dict:
        """Get the current autonomous discussion status."""
        try:
            result = await asyncio.to_thread(
                lambda: self.supabase.table("meeting_rooms")
                    .select("config")
                    .eq("id", meeting_room_id)
                    .single()
                    .execute()
            )

            config = result.data.get("config", {}) if result.data else {}
            autonomous = config.get("autonomous", {})

            return {
                "is_active": autonomous.get("is_active", False),
                "topic": autonomous.get("topic"),
                "total_rounds": autonomous.get("total_rounds", 0),
                "current_round": autonomous.get("current_round", 0),
                "speaking_order": autonomous.get("speaking_order", "priority"),
                "is_paused": autonomous.get("is_paused", False),
                "can_resume": autonomous.get("is_paused", False) and autonomous.get("topic") is not None
            }
        except Exception as e:
            logger.error(f"Failed to get autonomous status: {e}")
            return {
                "is_active": False,
                "topic": None,
                "total_rounds": 0,
                "current_round": 0,
                "speaking_order": "priority",
                "is_paused": False,
                "can_resume": False
            }


async def get_meeting_orchestrator(
    supabase: Client,
    anthropic_client: anthropic.Anthropic
) -> MeetingOrchestrator:
    """
    Factory function to create a MeetingOrchestrator with all agents loaded.
    """
    from agents.atlas import AtlasAgent
    from agents.fortuna import FortunaAgent
    from agents.guardian import GuardianAgent
    from agents.counselor import CounselorAgent
    from agents.oracle import OracleAgent
    from agents.sage import SageAgent

    # Initialize all available agents
    agents: dict[str, BaseAgent] = {}

    # Core agents (these should exist)
    try:
        agents["atlas"] = AtlasAgent(supabase, anthropic_client)
        agents["fortuna"] = FortunaAgent(supabase, anthropic_client)
        agents["guardian"] = GuardianAgent(supabase, anthropic_client)
        agents["counselor"] = CounselorAgent(supabase, anthropic_client)
        agents["oracle"] = OracleAgent(supabase, anthropic_client)
        agents["sage"] = SageAgent(supabase, anthropic_client)
    except Exception as e:
        logger.error(f"Error loading core agents: {e}")

    # Try to load additional agents if they exist
    try:
        from agents.strategist import StrategistAgent
        agents["strategist"] = StrategistAgent(supabase, anthropic_client)
    except ImportError:
        pass

    try:
        from agents.architect import ArchitectAgent
        agents["architect"] = ArchitectAgent(supabase, anthropic_client)
    except ImportError:
        pass

    try:
        from agents.operator import OperatorAgent
        agents["operator"] = OperatorAgent(supabase, anthropic_client)
    except ImportError:
        pass

    try:
        from agents.pioneer import PioneerAgent
        agents["pioneer"] = PioneerAgent(supabase, anthropic_client)
    except ImportError:
        pass

    try:
        from agents.catalyst import CatalystAgent
        agents["catalyst"] = CatalystAgent(supabase, anthropic_client)
    except ImportError:
        pass

    try:
        from agents.scholar import ScholarAgent
        agents["scholar"] = ScholarAgent(supabase, anthropic_client)
    except ImportError:
        pass

    try:
        from agents.nexus import NexusAgent
        agents["nexus"] = NexusAgent(supabase, anthropic_client)
    except ImportError:
        pass

    try:
        from agents.echo import EchoAgent
        agents["echo"] = EchoAgent(supabase, anthropic_client)
    except ImportError:
        pass

    # Initialize all loaded agents
    for agent in agents.values():
        try:
            await agent.initialize()
        except Exception as e:
            logger.warning(f"Failed to initialize agent {agent.name}: {e}")

    logger.info(f"MeetingOrchestrator initialized with {len(agents)} agents: {list(agents.keys())}")

    return MeetingOrchestrator(supabase, anthropic_client, agents)
