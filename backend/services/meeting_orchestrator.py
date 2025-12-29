"""
Meeting Orchestrator Service

Manages multi-agent conversations in meeting rooms:
- Uses Facilitator agent to analyze intent and manage turn-taking
- Uses Reporter agent for summary/documentation requests (single voice)
- Facilitator is ALWAYS present and speaks first on greetings/unclear intent
- Reporter is ALWAYS present and handles all summary requests
- Ensures balanced participation (no single agent dominates)
- Invokes systems thinking (Nexus) before conclusions
- Coordinates agent responses with proper attribution
- Streams responses with agent identification
- Tracks token usage and turn counts
- Creates vector embeddings for semantic search

Updated: 2025-12-28 - Added Facilitator-based orchestration
Updated: 2025-12-28 - Added Reporter for unified summaries
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

# Greeting patterns that trigger facilitator welcome
GREETING_PATTERNS = [
    'hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening',
    'howdy', 'greetings', "what's up", 'yo', 'hi there', 'hello there'
]

# Summary patterns that trigger Reporter (single voice for synthesis)
SUMMARY_PATTERNS = [
    'summary', 'summarize', 'summarise', 'sum up', 'sum it up',
    'recap', 'recapitulate',
    'takeaway', 'take away', 'takeaways', 'key takeaway',
    'action item', 'action items', 'next step', 'next steps',
    'what did we', 'what have we', 'what was discussed',
    'wrap up', 'wrap-up', 'wrapping up',
    'highlight', 'highlights', 'key highlight',
    'key point', 'key points', 'main point',
    'conclude', 'conclusion', 'in conclusion',
    'document', 'documentation',
    'brief', 'briefing', 'executive brief',
    'share with', 'send to', 'forward to',
    'bottom line', 'bottomline',
    'tldr', 'tl;dr',
    'give me the gist', 'give me the highlights',
    'what should i take', 'what do i need to know',
    'pull together', 'bring it together'
]

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
        agents: dict[str, BaseAgent],
        facilitator: Optional[BaseAgent] = None,
        reporter: Optional[BaseAgent] = None
    ):
        self.supabase = supabase
        self.anthropic = anthropic_client
        self.agents = agents
        self.facilitator = facilitator  # The Facilitator meta-agent (always present)
        self.reporter = reporter  # The Reporter meta-agent (always present for summaries)

    def _is_greeting(self, message: str) -> bool:
        """Check if a message is a greeting that should trigger facilitator welcome."""
        message_lower = message.lower().strip()
        # Check for exact matches or messages starting with greeting
        for greeting in GREETING_PATTERNS:
            if message_lower == greeting or message_lower.startswith(greeting + " ") or message_lower.startswith(greeting + "!"):
                return True
        # Also catch very short messages that are likely greetings
        if len(message_lower) < 20 and any(g in message_lower for g in GREETING_PATTERNS[:6]):
            return True
        return False

    def _is_summary_request(self, message: str) -> bool:
        """Check if a message is requesting a summary - should route to Reporter only."""
        message_lower = message.lower().strip()
        for pattern in SUMMARY_PATTERNS:
            if pattern in message_lower:
                return True
        return False

    def _track_agents_spoken(self, context: MeetingContext) -> set[str]:
        """Track which agents have spoken in recent history."""
        spoken = set()
        # Look at last 10 messages to see who's spoken
        for msg in context.message_history[-10:]:
            if msg.get('role') == 'agent' and msg.get('agent_name'):
                spoken.add(msg['agent_name'])
        return spoken

    def _get_unheard_agents(self, context: MeetingContext, spoken: set[str]) -> list[dict]:
        """Get list of participant agents who haven't spoken recently."""
        return [p for p in context.participants if p['agent_name'] not in spoken]

    # Agents that should always be considered for inclusion in discussions
    # These provide essential perspectives that should never be overlooked
    ESSENTIAL_PERSPECTIVES = ['sage', 'nexus']  # People + Systems thinking

    # Meta-agents that should not be selected as responding agents
    # (they have their own orchestration roles)
    META_AGENT_NAMES = {'facilitator', 'reporter'}

    def select_responding_agents(
        self,
        context: MeetingContext,
        max_agents: int = 3
    ) -> list[dict]:
        """
        Determine which agents from the meeting participants should respond.

        Uses keyword matching to score relevance, but ensures essential perspectives
        (Sage for people/change, Nexus for systems thinking) are always considered.

        Meta-agents (Facilitator, Reporter) are excluded - they have their own roles.
        """
        message_lower = context.user_message.lower()

        # Filter out meta-agents from consideration
        eligible_participants = [
            p for p in context.participants
            if p.get('agent_name', '').lower() not in self.META_AGENT_NAMES
        ]

        participant_names = {p['agent_name'] for p in eligible_participants}

        # Score each eligible agent based on keyword matching
        scores: dict[str, int] = {}
        for participant in eligible_participants:
            agent_name = participant['agent_name']
            keywords = self.SPECIALIST_DOMAINS.get(agent_name, [])
            score = sum(1 for kw in keywords if kw in message_lower)
            scores[agent_name] = score

        # Get agents with positive scores
        relevant_agents = [
            p for p in eligible_participants
            if scores.get(p['agent_name'], 0) > 0
        ]

        if relevant_agents:
            # Sort by score and take top agents
            relevant_agents.sort(
                key=lambda p: scores.get(p['agent_name'], 0),
                reverse=True
            )
            selected = relevant_agents[:max_agents]
        else:
            # If no clear matches, start with first eligible participant
            selected = eligible_participants[:1] if eligible_participants else []

        # Ensure essential perspectives are included if they're participants
        # and we have room (or make room for them)
        selected_names = {p['agent_name'] for p in selected}

        for essential_agent in self.ESSENTIAL_PERSPECTIVES:
            if essential_agent not in selected_names:
                # Find this agent in eligible participants
                for p in eligible_participants:
                    if p['agent_name'] == essential_agent:
                        # Add essential agent, respecting max_agents by replacing lowest scored
                        if len(selected) < max_agents:
                            selected.append(p)
                        elif len(selected) >= max_agents and selected:
                            # Replace the lowest scored non-essential agent
                            for i in range(len(selected) - 1, -1, -1):
                                if selected[i]['agent_name'] not in self.ESSENTIAL_PERSPECTIVES:
                                    selected[i] = p
                                    break
                        selected_names.add(essential_agent)
                        break

        return selected[:max_agents]

    def _build_meeting_system_prompt(
        self,
        agent_name: str,
        agent_display_name: str,
        context: MeetingContext,
        base_instruction: str,
        other_participants: list[str],
        recent_agent_turns: list[dict] = None
    ) -> str:
        """Build a meeting-aware system prompt for an agent.

        Includes recent contributions from other agents so the current agent
        can build on or segue from what was just said.
        """
        # Format recent contributions from other agents in this turn
        recent_context = ""
        if recent_agent_turns:
            recent_lines = []
            for turn in recent_agent_turns:
                turn_name = turn.get('agent_display_name', turn.get('agent_name', 'Agent'))
                turn_content = turn.get('content', '')
                # Truncate if too long
                if len(turn_content) > 300:
                    turn_content = turn_content[:300] + "..."
                recent_lines.append(f"**{turn_name}** just said: {turn_content}")

            if recent_lines:
                recent_contributions = "\n".join(recent_lines)
                recent_context = f"""
RECENT CONTRIBUTIONS (respond to or build on these):
{recent_contributions}

"""

        meeting_context = f"""

--- MEETING CONTEXT ---
Multi-agent meeting. Other participants: {', '.join(other_participants)}
{recent_context}
CRITICAL - BREVITY IS MANDATORY:
- 50-100 words MAX. Not a suggestion - a hard limit.
- ONE key insight from your domain. That's it.
- NO preamble, NO "Great question", NO filler.
- Start with your point. End when you've made it.
- If another agent just spoke, acknowledge/segue briefly before your point.
- If not your domain, say "I'll defer to [Agent]" and stop.

Format: Lead sentence + 2-3 bullets max. Bold **key terms** only.

The user can always ask you to expand. Default to SHORT.
--- END MEETING CONTEXT ---

"""
        return base_instruction + meeting_context

    async def _stream_facilitator_message(
        self,
        message: str,
        context: MeetingContext
    ) -> AsyncGenerator[dict, None]:
        """Stream a facilitator message with proper event types."""
        yield {
            "type": "facilitator_turn_start",
            "agent_name": "facilitator",
            "agent_display_name": "Facilitator"
        }

        # Stream the message character by character for consistency
        # (or could stream word by word for faster perceived response)
        words = message.split()
        for i, word in enumerate(words):
            token = word + (" " if i < len(words) - 1 else "")
            yield {
                "type": "facilitator_token",
                "content": token
            }
            await asyncio.sleep(0.02)  # Small delay for natural streaming feel

        # Store the facilitator message
        await self._store_message(
            meeting_room_id=context.meeting_room_id,
            role="agent",
            content=message,
            agent_name="facilitator",
            agent_display_name="Facilitator",
            turn_number=context.turn_number,
            metadata={"is_facilitator": True}
        )

        yield {
            "type": "facilitator_turn_end",
            "agent_name": "facilitator"
        }

    async def _stream_reporter_response(
        self,
        context: MeetingContext
    ) -> AsyncGenerator[dict, None]:
        """
        Stream a Reporter response for summary/documentation requests.

        The Reporter synthesizes the entire meeting discussion into a single
        unified summary, preventing multiple agents from each giving their own
        summary which causes confusion.
        """
        if not self.reporter:
            yield {
                "type": "error",
                "message": "Reporter agent not available"
            }
            return

        # Signal reporter turn start
        yield {
            "type": "agent_turn_start",
            "agent_name": "reporter",
            "agent_display_name": "Reporter",
            "turn_number": context.turn_number
        }

        try:
            # Build the meeting history context for the Reporter
            meeting_history_text = self._format_meeting_history_for_reporter(context)

            # Build the system prompt with meeting context
            reporter_system = self.reporter.system_instruction + f"""

--- MEETING CONTEXT FOR SYNTHESIS ---
The following is the discussion you need to synthesize:

{meeting_history_text}

The user's current request is below. Create a unified summary based on what the agents discussed.
--- END MEETING CONTEXT ---
"""

            # Build messages for the API
            messages = [{"role": "user", "content": context.user_message}]

            # Stream the response
            full_response = ""
            tokens_input = 0
            tokens_output = 0

            with self.anthropic.messages.stream(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,  # Summaries can be slightly longer
                system=reporter_system,
                messages=messages,
            ) as stream:
                for text in stream.text_stream:
                    full_response += text
                    yield {
                        "type": "agent_token",
                        "agent_name": "reporter",
                        "content": text
                    }

                final_message = stream.get_final_message()
                tokens_input = final_message.usage.input_tokens
                tokens_output = final_message.usage.output_tokens

            # Store the reporter's response
            await self._store_message(
                meeting_room_id=context.meeting_room_id,
                role="agent",
                content=full_response,
                agent_name="reporter",
                agent_display_name="Reporter",
                turn_number=context.turn_number,
                metadata={
                    "is_reporter": True,
                    "is_summary": True,
                    "tokens": {"input": tokens_input, "output": tokens_output}
                }
            )

            # Signal turn end
            yield {
                "type": "agent_turn_end",
                "agent_name": "reporter",
                "tokens": {"input": tokens_input, "output": tokens_output}
            }

            # Signal round complete
            yield {
                "type": "round_complete",
                "agents_responded": ["reporter"],
                "reporter_only": True,
                "total_tokens": {"input": tokens_input, "output": tokens_output}
            }

        except Exception as e:
            logger.error(f"Error in Reporter response: {e}")
            yield {
                "type": "error",
                "agent_name": "reporter",
                "message": str(e)
            }

    def _format_meeting_history_for_reporter(self, context: MeetingContext) -> str:
        """Format the meeting history for the Reporter to synthesize."""
        lines = []
        for msg in context.message_history:
            role = msg.get('role', 'unknown')
            if role == 'user':
                lines.append(f"**User**: {msg.get('content', '')}")
            elif role == 'agent':
                agent_name = msg.get('agent_display_name', msg.get('agent_name', 'Agent'))
                lines.append(f"**{agent_name}**: {msg.get('content', '')}")
            # Skip system messages
        return "\n\n".join(lines)

    def _generate_facilitator_welcome(self, participants: list[dict]) -> str:
        """Generate a brief welcome message from the Facilitator.

        Uses first-person voice and excludes meta-agents (Facilitator, Reporter)
        from the participant list since they're always present.
        """
        # Get participant display names, excluding meta-agents
        meta_agent_names = {'facilitator', 'reporter'}
        participant_names = []
        for p in participants:
            agent_name = p.get('agent_name', '').lower()
            if agent_name not in meta_agent_names:
                display_name = p.get('agent_display_name', p.get('agent_name', 'Agent'))
                participant_names.append(display_name)

        if len(participant_names) == 0:
            return "Welcome! I'm the Facilitator - I'll be guiding our discussion today. What would you like us to explore together?"

        if len(participant_names) <= 4:
            names_str = ", ".join(participant_names)
        else:
            names_str = ", ".join(participant_names[:4]) + f", and {len(participant_names) - 4} others"

        return f"Welcome! I'm the Facilitator - I'll be guiding our discussion today. We have {names_str} joining us. What would you like us to explore together?"

    def _get_agent_domain_label(self, agent_name: str) -> str:
        """Get a brief domain label for an agent."""
        labels = {
            'atlas': 'research',
            'fortuna': 'finance',
            'guardian': 'security',
            'counselor': 'legal',
            'oracle': 'meetings',
            'sage': 'people',
            'strategist': 'strategy',
            'architect': 'technical',
            'operator': 'operations',
            'pioneer': 'innovation',
            'catalyst': 'communications',
            'scholar': 'learning',
            'nexus': 'systems',
            'echo': 'brand voice',
        }
        return labels.get(agent_name.lower(), 'specialist')

    async def _generate_facilitator_routing_intro(
        self,
        responding_agents: list[dict],
        user_message: str
    ) -> Optional[str]:
        """
        Generate a conversational routing intro using the Facilitator LLM.

        Instead of hardcoded templates like "Let's hear from X and Y", this uses
        the Facilitator to craft human-level handoffs that give each agent a
        specific angle or question to address.
        """
        if not responding_agents or not self.facilitator:
            return None

        # Filter out meta-agents (facilitator, reporter) from the list
        meta_agents = {'facilitator', 'reporter'}
        filtered_agents = [
            p for p in responding_agents
            if p.get('agent_name', '').lower() not in meta_agents
        ]

        if not filtered_agents:
            return None

        # Build agent info for the prompt
        agent_info_lines = []
        for agent in filtered_agents:
            agent_name = agent.get('agent_name', '')
            display_name = agent.get('agent_display_name', agent_name)
            domain = self._get_agent_domain_label(agent_name)
            agent_info_lines.append(f"- {display_name} ({domain})")

        agents_context = "\n".join(agent_info_lines)

        # Create a focused prompt for the Facilitator to generate a handoff
        routing_prompt = f"""The user asked: "{user_message}"

You need to invite these agents to respond:
{agents_context}

Generate a brief, conversational handoff (2-3 sentences max) that:
1. Acknowledges the question briefly (half a sentence)
2. For EACH agent, explains what perspective or angle you're curious about from them
3. Sounds natural - like a skilled meeting facilitator

EXAMPLES of good handoffs:
- "That's a layered question. Fortuna, I'd love to understand the financial dynamics here. And Sage, how might this land with the team from a people perspective?"
- "Interesting challenge. Guardian, what security considerations should we have on our radar? And Architect, how would this fit into the technical landscape?"

DO NOT:
- Just list names ("Let's hear from X and Y")
- Use generic prompts ("thoughts?" or "what do you think?")
- Include yourself (Facilitator) or Reporter in the list

Respond with ONLY the handoff message, nothing else."""

        try:
            # Use a quick, focused LLM call
            response = self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=150,
                system=self.facilitator.system_instruction,
                messages=[{"role": "user", "content": routing_prompt}]
            )

            if response.content and len(response.content) > 0:
                return response.content[0].text.strip()

        except Exception as e:
            logger.warning(f"Facilitator routing intro generation failed: {e}")
            # Fallback to simple but correct format (no self-reference)
            agent_names = [p.get('agent_display_name', p.get('agent_name')) for p in filtered_agents]
            if len(agent_names) == 1:
                return f"Let me bring in {agent_names[0]} on this."
            else:
                names_str = ", ".join(agent_names[:-1]) + f" and {agent_names[-1]}"
                return f"I'd like to hear from {names_str} on this."

        return None

    async def process_meeting_turn(
        self,
        context: MeetingContext
    ) -> AsyncGenerator[dict, None]:
        """
        Process a user message and yield streaming responses from agents.

        The Facilitator orchestrates the conversation:
        - For greetings: Facilitator welcomes and asks what to explore (no agent responses)
        - For questions: Facilitator briefly introduces, then relevant agents respond
        - For follow-ups: Routes directly to addressed agent

        Yields SSE-formatted events:
        - facilitator_turn_start: When facilitator begins
        - facilitator_token: Facilitator response tokens
        - facilitator_turn_end: When facilitator finishes
        - agent_turn_start: When an agent begins responding
        - agent_token: Individual tokens from agent response
        - agent_turn_end: When an agent finishes
        - round_complete: When all agents have responded
        - error: If something goes wrong
        """
        try:
            # Store user message first
            await self._store_message(
                meeting_room_id=context.meeting_room_id,
                role="user",
                content=context.user_message,
                turn_number=context.turn_number
            )

            # Check if this is a greeting - Facilitator handles alone
            if self._is_greeting(context.user_message):
                welcome_message = self._generate_facilitator_welcome(context.participants)
                async for event in self._stream_facilitator_message(welcome_message, context):
                    yield event

                yield {
                    "type": "round_complete",
                    "agents_responded": ["facilitator"],
                    "facilitator_only": True,
                    "total_tokens": {"input": 0, "output": len(welcome_message.split())}
                }
                return

            # Check if this is a summary request - Reporter handles alone
            # This prevents multiple agents from each giving their own summary
            if self._is_summary_request(context.user_message) and self.reporter:
                async for event in self._stream_reporter_response(context):
                    yield event
                return

            # Select which agents should respond
            responding_agents = self.select_responding_agents(context)

            if not responding_agents:
                yield {
                    "type": "error",
                    "message": "No agents available to respond"
                }
                return

            # Facilitator introduces the agents (brief routing message)
            routing_intro = await self._generate_facilitator_routing_intro(
                responding_agents,
                context.user_message
            )
            if routing_intro:
                async for event in self._stream_facilitator_message(routing_intro, context):
                    yield event

            agents_responded = []
            total_tokens_input = 0
            total_tokens_output = 0

            # Get list of other participant names for context
            all_participant_names = [p['agent_display_name'] for p in context.participants]

            # Track agent turns in this round for context passing
            current_round_turns: list[dict] = []

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
                        other_participants=other_participants,
                        recent_agent_turns=current_round_turns  # Pass recent turns for context
                    )

                    # Collect response while streaming
                    full_response = ""
                    tokens_input = 0
                    tokens_output = 0

                    # Stream using Claude API directly with meeting context
                    messages = self._build_meeting_messages(context)

                    with self.anthropic.messages.stream(
                        model="claude-sonnet-4-20250514",
                        max_tokens=300,  # Enforce brevity - 50-100 words target
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

                    # Add this agent's turn to context for next agents
                    current_round_turns.append({
                        'agent_name': agent_name,
                        'agent_display_name': agent_display_name,
                        'content': full_response
                    })

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
            embed_func = await _get_embed_function()
            if embed_func:
                await embed_func(
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

        # Pre-format recent contributions section (avoid backslash in f-string expression)
        if recent_contributions:
            contributions_section = f"RECENT CONTRIBUTIONS FROM OTHER AGENTS:\n{recent_contributions}"
        else:
            contributions_section = "You are the first to speak in this round."

        discourse_context = f"""

--- AUTONOMOUS DISCUSSION ---
Round {autonomous_context.current_round}/{autonomous_context.total_rounds} | Topic: {autonomous_context.topic}

{contributions_section}

{round_guidance}

CRITICAL - 75 WORDS MAX:
- ONE point per turn. Make it count.
- Address agents by name: "@Fortuna, but what about..."
- Question > Agree. Challenge assumptions.
- Not your domain? Defer and stop: "That's for Guardian."
- NO filler. NO preamble. Start with substance.

Format: 1-2 sentences + optional question to another agent.
--- END ---

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
                            max_tokens=200,  # Enforce brevity - 75 words target
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
    Includes the Facilitator and Reporter meta-agents which are always present in meetings.
    - Facilitator: Orchestrates conversation flow, routes to agents
    - Reporter: Synthesizes discussions into unified summaries
    """
    from agents.atlas import AtlasAgent
    from agents.fortuna import FortunaAgent
    from agents.guardian import GuardianAgent
    from agents.counselor import CounselorAgent
    from agents.oracle import OracleAgent
    from agents.sage import SageAgent

    # Initialize the Facilitator meta-agent (always present)
    facilitator = None
    try:
        from agents.facilitator import FacilitatorAgent
        facilitator = FacilitatorAgent(supabase, anthropic_client)
        await facilitator.initialize()
        logger.info("Facilitator meta-agent initialized")
    except Exception as e:
        logger.warning(f"Could not load Facilitator agent: {e}")

    # Initialize the Reporter meta-agent (always present for summaries)
    reporter = None
    try:
        from agents.reporter import ReporterAgent
        reporter = ReporterAgent(supabase, anthropic_client)
        await reporter.initialize()
        logger.info("Reporter meta-agent initialized")
    except Exception as e:
        logger.warning(f"Could not load Reporter agent: {e}")

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
    if facilitator:
        logger.info("Facilitator is active and will orchestrate meetings")
    if reporter:
        logger.info("Reporter is active and will handle summary requests")

    return MeetingOrchestrator(supabase, anthropic_client, agents, facilitator, reporter)
