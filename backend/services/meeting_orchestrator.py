"""
Meeting Orchestrator Service

Manages multi-agent conversations in meeting rooms:
- Determines which agents should respond to each user message
- Coordinates agent responses with proper attribution
- Streams responses with agent identification
- Tracks token usage and turn counts
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import AsyncGenerator, Optional

import anthropic
from supabase import Client

from agents.base_agent import AgentContext, AgentResponse, BaseAgent

logger = logging.getLogger(__name__)


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
                   "adult learning", "capability building", "onboarding"]
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
    ) -> None:
        """Store a message in the meeting room."""
        try:
            await asyncio.to_thread(
                lambda: self.supabase.table("meeting_room_messages").insert({
                    "meeting_room_id": meeting_room_id,
                    "role": role,
                    "content": content,
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "agent_display_name": agent_display_name,
                    "turn_number": turn_number,
                    "metadata": metadata or {}
                }).execute()
            )
        except Exception as e:
            logger.error(f"Failed to store meeting message: {e}")

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

    # Initialize all loaded agents
    for agent in agents.values():
        try:
            await agent.initialize()
        except Exception as e:
            logger.warning(f"Failed to initialize agent {agent.name}: {e}")

    logger.info(f"MeetingOrchestrator initialized with {len(agents)} agents: {list(agents.keys())}")

    return MeetingOrchestrator(supabase, anthropic_client, agents)
