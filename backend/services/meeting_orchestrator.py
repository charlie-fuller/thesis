"""Meeting Orchestrator Service.

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
import logging
import re
from dataclasses import dataclass, field
from typing import AsyncGenerator, Optional
from uuid import UUID

import anthropic

from agents.base_agent import BaseAgent
from services.compliance_drift_tracker import (
    get_compliance_reminder,
    record_compliance_score,
)
import pb_client as pb
from services.manifesto_compliance import (
    score_manifesto_compliance,
    should_semantic_evaluate,
    trigger_semantic_evaluation,
)

logger = logging.getLogger(__name__)

# Greeting patterns that trigger facilitator welcome
GREETING_PATTERNS = [
    "hello",
    "hi",
    "hey",
    "good morning",
    "good afternoon",
    "good evening",
    "howdy",
    "greetings",
    "what's up",
    "yo",
    "hi there",
    "hello there",
]

# Summary patterns that trigger Reporter (single voice for synthesis)
SUMMARY_PATTERNS = [
    "summary",
    "summarize",
    "summarise",
    "sum up",
    "sum it up",
    "recap",
    "recapitulate",
    "takeaway",
    "take away",
    "takeaways",
    "key takeaway",
    "action item",
    "action items",
    "next step",
    "next steps",
    "what did we",
    "what have we",
    "what was discussed",
    "wrap up",
    "wrap-up",
    "wrapping up",
    "highlight",
    "highlights",
    "key highlight",
    "key point",
    "key points",
    "main point",
    "conclude",
    "conclusion",
    "in conclusion",
    "document",
    "documentation",
    "brief",
    "briefing",
    "executive brief",
    "share with",
    "send to",
    "forward to",
    "bottom line",
    "bottomline",
    "tldr",
    "tl;dr",
    "give me the gist",
    "give me the highlights",
    "what should i take",
    "what do i need to know",
    "pull together",
    "bring it together",
]

# @mention pattern for direct agent addressing in meetings
# Matches @agentname at word boundaries (case-insensitive)
MENTION_PATTERN = re.compile(
    r"@(atlas|capital|guardian|counselor|oracle|sage|strategist|architect|"
    r"operator|pioneer|catalyst|scholar|echo|nexus|facilitator|reporter)",
    re.IGNORECASE,
)

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

            def _noop_embed(*args, **kwargs):
                return None

            _embed_meeting_room_message = _noop_embed
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
    kb_context: list[dict] = field(default_factory=list)  # Vector search KB context (Voyage AI)
    graph_context: dict = field(default_factory=dict)  # Graph relationship context (Neo4j)


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
    """Orchestrates multi-agent conversations in meeting rooms.

    Responsibilities:
    - Analyze user messages to determine which agents should respond
    - Coordinate agent responses (sequential with streaming)
    - Track and store messages with proper attribution
    - Manage token budgets and turn counts
    """

    # Reuse the specialist domains from CoordinatorAgent
    SPECIALIST_DOMAINS = {
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
        "nexus": [
            "systems thinking",
            "interconnection",
            "feedback loop",
            "leverage point",
            "unintended consequence",
            "causal",
            "dependency",
            "ripple effect",
            "ecosystem",
            "holistic",
            "systems dynamics",
            "second-order",
            "third-order",
            "complexity",
        ],
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
    }

    def __init__(
        self,
        supabase=None,
        anthropic_client: anthropic.Anthropic = None,
        agents: dict[str, BaseAgent] = None,
        facilitator: Optional[BaseAgent] = None,
        reporter: Optional[BaseAgent] = None,
    ):
        self.anthropic = anthropic_client
        self.agents = agents
        self.facilitator = facilitator  # The Facilitator meta-agent (always present)
        self.reporter = reporter  # The Reporter meta-agent (always present for summaries)

    def _is_greeting(self, message: str) -> bool:
        """Check if a message is a greeting that should trigger facilitator welcome."""
        message_lower = message.lower().strip()
        # Check for exact matches or messages starting with greeting
        for greeting in GREETING_PATTERNS:
            if (
                message_lower == greeting
                or message_lower.startswith(greeting + " ")
                or message_lower.startswith(greeting + "!")
            ):
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

    def _parse_direct_mention(self, message: str, participants: list[dict]) -> Optional[list[dict]]:
        """Parse @mentions from a message and return matching participants.

        When a user directly addresses an agent with @mention, that agent should
        respond directly WITHOUT Facilitator intervention.

        Returns:
            List of participant dicts for mentioned agents that are in the meeting,
            or None if no valid @mentions found.
        """
        mentions = MENTION_PATTERN.findall(message.lower())
        if not mentions:
            return None

        # Build a map of agent names to participants
        participant_map = {p["agent_name"].lower(): p for p in participants}

        # Find mentioned agents that are actually in this meeting
        mentioned_participants = []
        for mention in mentions:
            mention_lower = mention.lower()
            if mention_lower in participant_map:
                mentioned_participants.append(participant_map[mention_lower])

        if mentioned_participants:
            logger.info(f"Direct @mention detected: {[p['agent_name'] for p in mentioned_participants]}")
            return mentioned_participants

        # User mentioned agents not in this meeting - return None to let normal routing happen
        logger.info(f"@mention for agents not in meeting: {mentions}")
        return None

    def _track_agents_spoken(self, context: MeetingContext) -> set[str]:
        """Track which agents have spoken in recent history."""
        spoken = set()
        # Look at last 10 messages to see who's spoken
        for msg in context.message_history[-10:]:
            if msg.get("role") == "agent" and msg.get("agent_name"):
                spoken.add(msg["agent_name"])
        return spoken

    def _get_unheard_agents(self, context: MeetingContext, spoken: set[str]) -> list[dict]:
        """Get list of participant agents who haven't spoken recently."""
        return [p for p in context.participants if p["agent_name"] not in spoken]

    # Agents that should always be considered for inclusion in discussions
    # These provide essential perspectives that should never be overlooked
    ESSENTIAL_PERSPECTIVES = ["sage", "nexus"]  # People + Systems thinking

    # Meta-agents that should not be selected as responding agents
    # (they have their own orchestration roles)
    META_AGENT_NAMES = {"facilitator", "reporter"}

    def select_responding_agents(self, context: MeetingContext, max_agents: int = 3) -> list[dict]:
        """Determine which agents from the meeting participants should respond.

        Uses keyword matching to score relevance, but ensures essential perspectives
        (Sage for people/change, Nexus for systems thinking) are always considered.

        Meta-agents (Facilitator, Reporter) are excluded - they have their own roles.
        """
        message_lower = context.user_message.lower()

        # Filter out meta-agents from consideration
        eligible_participants = [
            p for p in context.participants if p.get("agent_name", "").lower() not in self.META_AGENT_NAMES
        ]

        {p["agent_name"] for p in eligible_participants}

        # Score each eligible agent based on keyword matching
        scores: dict[str, int] = {}
        for participant in eligible_participants:
            agent_name = participant["agent_name"]
            keywords = self.SPECIALIST_DOMAINS.get(agent_name, [])
            score = sum(1 for kw in keywords if kw in message_lower)
            scores[agent_name] = score

        # Get agents with positive scores
        relevant_agents = [p for p in eligible_participants if scores.get(p["agent_name"], 0) > 0]

        if relevant_agents:
            # Sort by score and take top agents
            relevant_agents.sort(key=lambda p: scores.get(p["agent_name"], 0), reverse=True)
            selected = relevant_agents[:max_agents]
        else:
            # If no clear matches, start with first eligible participant
            selected = eligible_participants[:1] if eligible_participants else []

        # Ensure essential perspectives are included if they're participants
        # and we have room (or make room for them)
        selected_names = {p["agent_name"] for p in selected}

        for essential_agent in self.ESSENTIAL_PERSPECTIVES:
            if essential_agent not in selected_names:
                # Find this agent in eligible participants
                for p in eligible_participants:
                    if p["agent_name"] == essential_agent:
                        # Add essential agent, respecting max_agents by replacing lowest scored
                        if len(selected) < max_agents:
                            selected.append(p)
                        elif len(selected) >= max_agents and selected:
                            # Replace the lowest scored non-essential agent
                            for i in range(len(selected) - 1, -1, -1):
                                if selected[i]["agent_name"] not in self.ESSENTIAL_PERSPECTIVES:
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
        recent_agent_turns: list[dict] = None,
    ) -> str:
        """Build a meeting-aware system prompt for an agent.

        Includes recent contributions from other agents so the current agent
        can build on or segue from what was just said.
        Also includes knowledge base context when available.
        """
        # Format recent contributions from other agents in this turn
        recent_context = ""
        if recent_agent_turns:
            recent_lines = []
            for turn in recent_agent_turns:
                turn_name = turn.get("agent_display_name", turn.get("agent_name", "Agent"))
                turn_content = turn.get("content", "")
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

        # Format knowledge base context if available
        kb_context_section = ""
        if context.kb_context:
            kb_parts = []
            seen_content = set()  # Track content hashes to avoid duplicates
            source_counter = 0
            for chunk in context.kb_context:
                content = chunk.get("content", "")
                if not content:
                    continue

                # Create a content hash to detect near-duplicates
                # Normalize by lowercasing and removing extra whitespace
                content_normalized = " ".join(content.lower().split())
                content_hash = hash(content_normalized[:200])  # Hash first 200 chars

                # Skip if we've already seen very similar content
                if content_hash in seen_content:
                    continue
                seen_content.add(content_hash)

                source_counter += 1
                source_info = f"[Source {source_counter}"
                metadata = chunk.get("metadata", {})
                if metadata.get("filename"):
                    source_info += f" - {metadata['filename']}"
                elif metadata.get("conversation_title"):
                    source_info += f" - {metadata['conversation_title']}"
                source_info += "]"
                # Truncate content if too long to preserve token budget
                # Increased to 1000 chars to provide comprehensive context from each chunk
                if len(content) > 1000:
                    content = content[:1000] + "..."
                kb_parts.append(f"{source_info}:\n{content}")

            kb_text = "\n\n".join(kb_parts)
            kb_context_section = f"""
KNOWLEDGE BASE CONTEXT (from documents and previous conversations):
<knowledge_base>
{kb_text}
</knowledge_base>

CRITICAL - PRIORITIZE KB CONTEXT:
- The knowledge base above contains REAL information from the user's documents and conversations.
- If the KB context addresses the question, you MUST reference it specifically in your response.
- Quote or paraphrase relevant passages. Cite the source (e.g., "According to [Source 1]...").
- Do NOT ignore KB content in favor of general knowledge when specific data exists above.
- If KB context is incomplete or doesn't address the question, say so and provide your perspective.

"""

        # Format graph context if available (stakeholders, concerns, ROI opportunities)
        graph_context_section = ""
        if context.graph_context:
            graph_parts = []
            # Stakeholders
            if context.graph_context.get("stakeholders"):
                stakeholder_lines = []
                for s in context.graph_context["stakeholders"][:3]:
                    sentiment = s.get("sentiment_score") or 0.5
                    sentiment_label = "positive" if sentiment > 0.6 else "neutral" if sentiment > 0.4 else "cautious"
                    stakeholder_lines.append(f"  - {s['name']} ({s.get('role', 'Unknown')}) - {sentiment_label}")
                if stakeholder_lines:
                    graph_parts.append("Stakeholders:\n" + "\n".join(stakeholder_lines))

            # Concerns
            if context.graph_context.get("concerns"):
                concern_lines = []
                for c in context.graph_context["concerns"][:3]:
                    content = (c.get("content") or "")[:80]
                    severity = c.get("severity", "unknown")
                    concern_lines.append(f"  - [{severity}] {content}...")
                if concern_lines:
                    graph_parts.append("Concerns raised:\n" + "\n".join(concern_lines))

            # ROI Opportunities
            if context.graph_context.get("roi_opportunities"):
                roi_lines = []
                for o in context.graph_context["roi_opportunities"][:2]:
                    name = o.get("name", "Unnamed")
                    status = o.get("status", "unknown")
                    roi_lines.append(f"  - {name} ({status})")
                if roi_lines:
                    graph_parts.append("ROI Opportunities:\n" + "\n".join(roi_lines))

            # Relationships
            if context.graph_context.get("relationships"):
                rel_lines = []
                for r in context.graph_context["relationships"][:3]:
                    rel_type = (r.get("relationship") or "relates_to").lower().replace("_", " ")
                    rel_lines.append(f"  - {r.get('from_name', '?')} {rel_type} {r.get('to_name', '?')}")
                if rel_lines:
                    graph_parts.append("Relationships:\n" + "\n".join(rel_lines))

            if graph_parts:
                graph_text = "\n".join(graph_parts)
                graph_context_section = f"""
STAKEHOLDER & RELATIONSHIP CONTEXT (from Neo4j graph):
<graph_context>
{graph_text}
</graph_context>

Use this relationship context to understand stakeholder dynamics and organizational factors.

"""

        # Build explicit participant list
        all_participants = [agent_display_name] + other_participants
        participant_list = ", ".join(all_participants)

        meeting_context = f"""

--- MEETING CONTEXT ---
You are in a multi-agent meeting room.

PARTICIPANTS IN THIS MEETING (ONLY these agents are present):
{participant_list}

CRITICAL: Only refer to or defer to agents who are actually IN THIS MEETING.
Do NOT mention agents who are not participants. If you would normally defer to
an agent not in this meeting, provide your best perspective instead.

{kb_context_section}{graph_context_section}{recent_context}
IDENTITY - CRITICAL:
- You are {agent_display_name}. Respond AS YOURSELF, not as anyone else.
- NEVER prefix your response with ANY name in brackets like "[Facilitator]:" or "[Sage]:" or "[{agent_display_name}]:".
- The conversation history shows "[AgentName]:" prefixes for context only - YOU must NOT use this format.
- NEVER speak on behalf of another agent. Only provide YOUR perspective.
- Just start speaking directly - your name is already shown in the UI.
- DO NOT format your response as if you were multiple agents speaking.

BREVITY IS MANDATORY:
- 50-100 words MAX. Not a suggestion - a hard limit.
- ONE key insight from your domain. That's it.
- NO preamble, NO "Great question", NO filler.
- Start with your point. End when you've made it.
- If another agent just spoke, acknowledge/segue briefly before your point.
- If not your domain AND a relevant agent IS in the meeting, say "I'll defer to [Agent]" and stop.
- If not your domain AND no relevant agent is present, provide your best perspective.

Format: Lead sentence + 2-3 bullets max. Bold **key terms** only.

The user can always ask you to expand. Default to SHORT.
--- END MEETING CONTEXT ---

"""
        return base_instruction + meeting_context

    async def _stream_facilitator_message(self, message: str, context: MeetingContext) -> AsyncGenerator[dict, None]:
        """Stream a facilitator message with proper event types."""
        yield {
            "type": "facilitator_turn_start",
            "agent_name": "facilitator",
            "agent_display_name": "Facilitator",
        }

        # Stream the message character by character for consistency
        # (or could stream word by word for faster perceived response)
        words = message.split()
        for i, word in enumerate(words):
            token = word + (" " if i < len(words) - 1 else "")
            yield {"type": "facilitator_token", "content": token}
            await asyncio.sleep(0.02)  # Small delay for natural streaming feel

        # Score manifesto compliance for facilitator
        facilitator_compliance = score_manifesto_compliance(message, "facilitator", source="meeting")
        facilitator_metadata = {"is_facilitator": True}
        if facilitator_compliance:
            facilitator_metadata["manifesto_compliance"] = facilitator_compliance

        # Record score for drift tracking
        record_compliance_score(
            str(context.meeting_room_id),
            "facilitator",
            facilitator_compliance["score"],
            facilitator_compliance.get("gaps", []),
        )

        # Store the facilitator message
        facilitator_msg_id = await self._store_message(
            meeting_room_id=context.meeting_room_id,
            role="agent",
            content=message,
            agent_name="facilitator",
            agent_display_name="Facilitator",
            turn_number=context.turn_number,
            metadata=facilitator_metadata,
        )

        # Trigger semantic evaluation if warranted
        if should_semantic_evaluate(facilitator_compliance, "facilitator"):
            trigger_semantic_evaluation(
                message,
                "facilitator",
                facilitator_compliance,
                message_id=facilitator_msg_id,
                table_name="meeting_room_messages",
            )

        yield {"type": "facilitator_turn_end", "agent_name": "facilitator"}

    async def _stream_reporter_response(self, context: MeetingContext) -> AsyncGenerator[dict, None]:
        """Stream a Reporter response for summary/documentation requests.

        The Reporter synthesizes the entire meeting discussion into a single
        unified summary, preventing multiple agents from each giving their own
        summary which causes confusion.
        """
        if not self.reporter:
            yield {"type": "error", "message": "Reporter agent not available"}
            return

        # Signal reporter turn start
        yield {
            "type": "agent_turn_start",
            "agent_name": "reporter",
            "agent_display_name": "Reporter",
            "turn_number": context.turn_number,
        }

        try:
            # Build the meeting history context for the Reporter
            meeting_history_text = self._format_meeting_history_for_reporter(context)

            # Build the system prompt with meeting context
            reporter_system = (
                self.reporter.system_instruction
                + f"""

--- MEETING CONTEXT FOR SYNTHESIS ---
The following is the discussion you need to synthesize:

{meeting_history_text}

The user's current request is below. Create a unified summary based on what the agents discussed.
--- END MEETING CONTEXT ---
"""
            )

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
                    yield {"type": "agent_token", "agent_name": "reporter", "content": text}

                final_message = stream.get_final_message()
                tokens_input = final_message.usage.input_tokens
                tokens_output = final_message.usage.output_tokens

            # Score manifesto compliance for reporter
            reporter_compliance = score_manifesto_compliance(full_response, "reporter", source="meeting")
            reporter_metadata = {
                "is_reporter": True,
                "is_summary": True,
                "tokens": {"input": tokens_input, "output": tokens_output},
            }
            if reporter_compliance:
                reporter_metadata["manifesto_compliance"] = reporter_compliance

            # Record score for drift tracking
            record_compliance_score(
                str(context.meeting_room_id),
                "reporter",
                reporter_compliance["score"],
                reporter_compliance.get("gaps", []),
            )

            # Store the reporter's response
            reporter_msg_id = await self._store_message(
                meeting_room_id=context.meeting_room_id,
                role="agent",
                content=full_response,
                agent_name="reporter",
                agent_display_name="Reporter",
                turn_number=context.turn_number,
                metadata=reporter_metadata,
            )

            # Trigger semantic evaluation if warranted
            if should_semantic_evaluate(reporter_compliance, "reporter"):
                trigger_semantic_evaluation(
                    full_response,
                    "reporter",
                    reporter_compliance,
                    message_id=reporter_msg_id,
                    table_name="meeting_room_messages",
                )

            # Signal turn end
            yield {
                "type": "agent_turn_end",
                "agent_name": "reporter",
                "tokens": {"input": tokens_input, "output": tokens_output},
            }

            # Signal round complete
            yield {
                "type": "round_complete",
                "agents_responded": ["reporter"],
                "reporter_only": True,
                "total_tokens": {"input": tokens_input, "output": tokens_output},
            }

        except Exception as e:
            logger.error(f"Error in Reporter response: {e}")
            yield {"type": "error", "agent_name": "reporter", "message": str(e)}

    def _format_meeting_history_for_reporter(self, context: MeetingContext) -> str:
        """Format the meeting history for the Reporter to synthesize."""
        lines = []
        for msg in context.message_history:
            role = msg.get("role", "unknown")
            if role == "user":
                lines.append(f"**User**: {msg.get('content', '')}")
            elif role == "agent":
                agent_name = msg.get("agent_display_name", msg.get("agent_name", "Agent"))
                lines.append(f"**{agent_name}**: {msg.get('content', '')}")
            # Skip system messages
        return "\n\n".join(lines)

    def _generate_facilitator_welcome(self, participants: list[dict]) -> str:
        """Generate a brief welcome message from the Facilitator.

        Uses first-person voice and excludes meta-agents (Facilitator, Reporter)
        from the participant list since they're always present.
        """
        # Get participant display names, excluding meta-agents
        meta_agent_names = {"facilitator", "reporter"}
        participant_names = []
        for p in participants:
            agent_name = p.get("agent_name", "").lower()
            if agent_name not in meta_agent_names:
                display_name = p.get("agent_display_name", p.get("agent_name", "Agent"))
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
            "atlas": "research",
            "capital": "finance",
            "guardian": "security",
            "counselor": "legal",
            "oracle": "meetings",
            "sage": "people",
            "strategist": "strategy",
            "architect": "technical",
            "operator": "operations",
            "pioneer": "innovation",
            "catalyst": "communications",
            "scholar": "learning",
            "nexus": "systems",
            "echo": "brand voice",
        }
        return labels.get(agent_name.lower(), "specialist")

    async def _generate_facilitator_routing_intro(
        self, responding_agents: list[dict], user_message: str
    ) -> Optional[str]:
        """Generate a conversational routing intro using the Facilitator LLM.

        Instead of hardcoded templates like "Let's hear from X and Y", this uses
        the Facilitator to craft human-level handoffs that give each agent a
        specific angle or question to address.
        """
        if not responding_agents or not self.facilitator:
            return None

        # Filter out meta-agents (facilitator, reporter) from the list
        meta_agents = {"facilitator", "reporter"}
        filtered_agents = [p for p in responding_agents if p.get("agent_name", "").lower() not in meta_agents]

        if not filtered_agents:
            return None

        # Build agent info for the prompt
        agent_info_lines = []
        for agent in filtered_agents:
            agent_name = agent.get("agent_name", "")
            display_name = agent.get("agent_display_name", agent_name)
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
- "That's a layered question. Capital, I'd love to understand the financial dynamics here. And Sage, how might this land with the team from a people perspective?"
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
                messages=[{"role": "user", "content": routing_prompt}],
            )

            if response.content and len(response.content) > 0:
                return response.content[0].text.strip()

        except Exception as e:
            logger.warning(f"Facilitator routing intro generation failed: {e}")
            # Fallback to simple but correct format (no self-reference)
            agent_names = [p.get("agent_display_name", p.get("agent_name")) for p in filtered_agents]
            if len(agent_names) == 1:
                return f"Let me bring in {agent_names[0]} on this."
            else:
                names_str = ", ".join(agent_names[:-1]) + f" and {agent_names[-1]}"
                return f"I'd like to hear from {names_str} on this."

        return None

    async def process_meeting_turn(self, context: MeetingContext) -> AsyncGenerator[dict, None]:
        """Process a user message and yield streaming responses from agents.

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
                turn_number=context.turn_number,
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
                    "total_tokens": {"input": 0, "output": len(welcome_message.split())},
                }
                return

            # Check if this is a summary request - Reporter handles alone
            # This prevents multiple agents from each giving their own summary
            if self._is_summary_request(context.user_message) and self.reporter:
                async for event in self._stream_reporter_response(context):
                    yield event
                return

            # Check for direct @mention - route directly to mentioned agent(s)
            # WITHOUT Facilitator intervention
            direct_mention_agents = self._parse_direct_mention(context.user_message, context.participants)
            is_direct_mention = direct_mention_agents is not None

            if is_direct_mention:
                # User directly addressed specific agent(s) - route to them
                responding_agents = direct_mention_agents
                logger.info(f"Direct @mention routing to: {[a['agent_name'] for a in responding_agents]}")
            else:
                # Normal routing - select agents based on message content
                responding_agents = self.select_responding_agents(context)

            if not responding_agents:
                yield {"type": "error", "message": "No agents available to respond"}
                return

            # Facilitator introduces the agents (brief routing message)
            # SKIP for direct @mentions - user already knows who they're talking to
            routing_intro = None
            if not is_direct_mention:
                routing_intro = await self._generate_facilitator_routing_intro(responding_agents, context.user_message)
            if routing_intro:
                async for event in self._stream_facilitator_message(routing_intro, context):
                    yield event

            agents_responded = []
            total_tokens_input = 0
            total_tokens_output = 0

            # Get list of other participant names for context
            all_participant_names = [p["agent_display_name"] for p in context.participants]

            # Track agent turns in this round for context passing
            current_round_turns: list[dict] = []

            # Process each responding agent sequentially with streaming
            for participant in responding_agents:
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
                    "turn_number": context.turn_number,
                }

                try:
                    # Build meeting-aware context for the agent
                    other_participants = [n for n in all_participant_names if n != agent_display_name]

                    effective_instruction = agent.system_instruction
                    reminder = get_compliance_reminder(agent_name, str(context.meeting_room_id))
                    if reminder:
                        effective_instruction = effective_instruction + "\n\n" + reminder

                    meeting_system_prompt = self._build_meeting_system_prompt(
                        agent_name=agent_name,
                        agent_display_name=agent_display_name,
                        context=context,
                        base_instruction=effective_instruction,
                        other_participants=other_participants,
                        recent_agent_turns=current_round_turns,  # Pass recent turns for context
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
                            yield {"type": "agent_token", "agent_name": agent_name, "content": text}

                        # Get final message for token counts
                        final_message = stream.get_final_message()
                        tokens_input = final_message.usage.input_tokens
                        tokens_output = final_message.usage.output_tokens

                    # Score manifesto compliance (pattern matching only, no LLM call)
                    compliance = score_manifesto_compliance(full_response, agent_name, source="meeting")
                    msg_metadata = {"tokens": {"input": tokens_input, "output": tokens_output}}
                    if compliance:
                        msg_metadata["manifesto_compliance"] = compliance

                    # Record score for drift tracking
                    record_compliance_score(
                        str(context.meeting_room_id),
                        agent_name,
                        compliance["score"],
                        compliance.get("gaps", []),
                    )

                    # Store the agent's response
                    agent_msg_id = await self._store_message(
                        meeting_room_id=context.meeting_room_id,
                        role="agent",
                        content=full_response,
                        agent_id=agent_id,
                        agent_name=agent_name,
                        agent_display_name=agent_display_name,
                        turn_number=context.turn_number,
                        metadata=msg_metadata,
                    )

                    # Trigger semantic evaluation if warranted
                    if should_semantic_evaluate(compliance, agent_name):
                        trigger_semantic_evaluation(
                            full_response,
                            agent_name,
                            compliance,
                            message_id=agent_msg_id,
                            table_name="meeting_room_messages",
                        )

                    # Update participant stats
                    await self._update_participant_stats(
                        meeting_room_id=context.meeting_room_id,
                        agent_id=agent_id,
                        tokens_used=tokens_output,
                    )

                    total_tokens_input += tokens_input
                    total_tokens_output += tokens_output
                    agents_responded.append(agent_name)

                    # Add this agent's turn to context for next agents
                    current_round_turns.append(
                        {
                            "agent_name": agent_name,
                            "agent_display_name": agent_display_name,
                            "content": full_response,
                        }
                    )

                    # Signal turn end
                    yield {
                        "type": "agent_turn_end",
                        "agent_name": agent_name,
                        "tokens": {"input": tokens_input, "output": tokens_output},
                    }

                except Exception as e:
                    logger.error(f"Error getting response from {agent_name}: {e}")
                    yield {"type": "error", "agent_name": agent_name, "message": str(e)}

            # Update meeting room token total
            await self._update_meeting_tokens(context.meeting_room_id, total_tokens_input + total_tokens_output)

            # Signal round complete
            yield {
                "type": "round_complete",
                "agents_responded": agents_responded,
                "total_tokens": {"input": total_tokens_input, "output": total_tokens_output},
            }

        except Exception as e:
            logger.error(f"Meeting orchestration error: {e}")
            yield {"type": "error", "message": str(e)}

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
                messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})

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
        metadata: Optional[dict] = None,
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

            result = pb.create_record("meeting_room_messages", insert_data)

            # Get the message ID for embedding
            if result:
                message_id = result.get("id")
                if message_id and role != "system":  # Skip system messages
                    # Queue embedding in background (don't await)
                    asyncio.create_task(self._embed_message_background(message_id, content))
                return message_id
            return None

        except Exception as e:
            logger.error(f"Failed to store meeting message: {e}")
            return None

    async def _embed_message_background(self, message_id: str, content: str) -> None:
        """Background task to embed a message."""
        try:
            embed_func = await _get_embed_function()
            if embed_func:
                await embed_func(None, UUID(message_id), content)
        except Exception as e:
            logger.warning(f"Background embedding failed for {message_id}: {e}")

    async def _update_participant_stats(self, meeting_room_id: str, agent_id: str, tokens_used: int) -> None:
        """Update participant stats after a turn."""
        try:
            esc_mid = pb.escape_filter(meeting_room_id)
            esc_aid = pb.escape_filter(agent_id)
            participant = pb.get_first(
                "meeting_room_participants",
                filter=f"meeting_room_id='{esc_mid}' && agent_id='{esc_aid}'",
            )
            if participant:
                current_turns = participant.get("turns_taken", 0)
                current_tokens = participant.get("tokens_used", 0)
                pb.update_record(
                    "meeting_room_participants",
                    participant["id"],
                    {
                        "turns_taken": current_turns + 1,
                        "tokens_used": current_tokens + tokens_used,
                    },
                )
        except Exception as e:
            logger.warning(f"Failed to update participant stats: {e}")

    async def _update_meeting_tokens(self, meeting_room_id: str, tokens: int) -> None:
        """Update total tokens used in the meeting."""
        try:
            room = pb.get_record("meeting_rooms", meeting_room_id)
            current = room.get("total_tokens_used", 0) if room else 0
            pb.update_record("meeting_rooms", meeting_room_id, {"total_tokens_used": current + tokens})
        except Exception as e:
            logger.error(f"Failed to update meeting tokens: {e}")

    # =========================================================================
    # AUTONOMOUS DISCUSSION METHODS
    # =========================================================================

    # Agent expertise descriptions for inter-agent awareness
    AGENT_EXPERTISE_DESCRIPTIONS = {
        "atlas": "Research & Best Practices - GenAI implementation research, case studies, Lean methodology, industry benchmarks",
        "capital": "Financial Analysis & ROI - Business cases, cost savings, SOX compliance, investment analysis",
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
        other_participants: list[str],
    ) -> str:
        """Build a prompt for agent-to-agent discourse."""
        # Format recent responses from other agents
        recent_contributions = self._format_recent_contributions(
            autonomous_context.round_messages or [], exclude_agent=agent_name
        )

        # Build expertise directory for other participants
        participant_expertise = []
        for participant in context.participants:
            p_name = participant.get("agent_name")
            p_display = participant.get("agent_display_name")
            if p_name != agent_name and p_name in self.AGENT_EXPERTISE_DESCRIPTIONS:
                participant_expertise.append(f"- **{p_display}**: {self.AGENT_EXPERTISE_DESCRIPTIONS[p_name]}")

        ("\n".join(participant_expertise) if participant_expertise else "No other agents.")

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

        # Format knowledge base context if available
        kb_context_section = ""
        if context.kb_context:
            kb_parts = []
            seen_content = set()  # Track content hashes to avoid duplicates
            source_counter = 0
            for chunk in context.kb_context[:8]:  # Limit to 8 chunks for autonomous context
                content = chunk.get("content", "")
                if not content:
                    continue

                # Create a content hash to detect near-duplicates
                content_normalized = " ".join(content.lower().split())
                content_hash = hash(content_normalized[:200])  # Hash first 200 chars

                # Skip if we've already seen very similar content
                if content_hash in seen_content:
                    continue
                seen_content.add(content_hash)

                source_counter += 1
                source_info = f"[Source {source_counter}"
                metadata = chunk.get("metadata", {})
                if metadata.get("filename"):
                    source_info += f" - {metadata['filename']}"
                elif metadata.get("conversation_title"):
                    source_info += f" - {metadata['conversation_title']}"
                source_info += "]"
                # Increased to 800 chars for autonomous mode - agents need full context
                if len(content) > 800:
                    content = content[:800] + "..."
                kb_parts.append(f"{source_info}: {content}")

            kb_text = "\n".join(kb_parts)
            kb_context_section = f"""
KNOWLEDGE BASE CONTEXT:
{kb_text}

IMPORTANT: This is REAL data from the user's documents. Reference it specifically when addressing the topic.
"""

        # Format graph context if available (compact for autonomous mode)
        graph_context_section = ""
        if context.graph_context:
            graph_parts = []
            if context.graph_context.get("stakeholders"):
                names = [s["name"] for s in context.graph_context["stakeholders"][:3]]
                if names:
                    graph_parts.append(f"Stakeholders: {', '.join(names)}")
            if context.graph_context.get("concerns"):
                concerns = [c.get("content", "")[:50] + "..." for c in context.graph_context["concerns"][:2]]
                if concerns:
                    graph_parts.append(f"Concerns: {'; '.join(concerns)}")
            if context.graph_context.get("roi_opportunities"):
                opps = [o.get("name", "?") for o in context.graph_context["roi_opportunities"][:2]]
                if opps:
                    graph_parts.append(f"ROI Opps: {', '.join(opps)}")
            if graph_parts:
                graph_context_section = "GRAPH CONTEXT: " + " | ".join(graph_parts) + "\n"

        # Build participant list for this specific meeting
        all_participant_names = [agent_display_name] + other_participants
        participant_list = ", ".join(all_participant_names)

        discourse_context = f"""

--- AUTONOMOUS DISCUSSION ---
Round {autonomous_context.current_round}/{autonomous_context.total_rounds} | Topic: {autonomous_context.topic}

PARTICIPANTS IN THIS MEETING (ONLY these agents are present):
{participant_list}

CRITICAL: Only refer to or defer to agents who are IN THIS MEETING.
Do NOT mention agents not listed above. If you would defer to an absent agent,
provide your best perspective instead.
{kb_context_section}{graph_context_section}
{contributions_section}

{round_guidance}

IDENTITY - CRITICAL:
- You are {agent_display_name}. Respond AS YOURSELF, not as anyone else.
- NEVER prefix your response with ANY name in brackets like "[Facilitator]:" or "[Sage]:" or "[{agent_display_name}]:".
- The conversation history shows "[AgentName]:" prefixes for context only - YOU must NOT use this format.
- NEVER speak on behalf of another agent. Only provide YOUR perspective.
- Just start speaking directly - your name is already shown in the UI.
- DO NOT format your response as if you were multiple agents speaking.

CRITICAL - 75 WORDS MAX:
- ONE point per turn. Make it count.
- Address ONLY agents in this meeting by name: "@Capital, but what about..."
- Question > Agree. Challenge assumptions.
- Not your domain AND relevant agent IS present? Defer to them.
- Not your domain AND no relevant agent present? Give your best take.
- NO filler. NO preamble. Start with substance.

Format: 1-2 sentences + optional question to another agent IN THIS MEETING.
--- END ---

"""
        return base_instruction + discourse_context

    def _format_recent_contributions(self, round_messages: list[dict], exclude_agent: str) -> str:
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

    def _get_round_speakers(self, participants: list[dict], speaking_order: str, round_number: int) -> list[dict]:
        """Get the ordered list of speakers for a round."""
        if speaking_order == "round_robin":
            # Rotate order based on round number
            offset = (round_number - 1) % len(participants)
            return participants[offset:] + participants[:offset]
        else:  # priority (default)
            # Sort by priority, then by name for consistency
            return sorted(participants, key=lambda p: (-p.get("priority", 0), p.get("agent_name", "")))

    async def _check_for_user_interjection(self, meeting_room_id: str) -> bool:
        """Check if user has sent a message during autonomous discussion."""
        try:
            esc_mid = pb.escape_filter(meeting_room_id)
            result = pb.list_records(
                "meeting_room_messages",
                filter=f"meeting_room_id='{esc_mid}' && role='user' && pending_interjection=true",
                per_page=1,
            )
            items = result.get("items", [])
            return len(items) > 0
        except Exception as e:
            logger.warning(f"Error checking for user interjection: {e}")
            return False

    async def _update_autonomous_config(self, meeting_room_id: str, config_update: dict) -> None:
        """Update the autonomous discussion config in meeting room."""
        try:
            room = pb.get_record("meeting_rooms", meeting_room_id)
            current_config = room.get("config", {}) if room else {}
            if isinstance(current_config, str):
                current_config = pb.parse_json_field(current_config, default={})
            autonomous_config = current_config.get("autonomous", {})
            autonomous_config.update(config_update)
            current_config["autonomous"] = autonomous_config
            pb.update_record("meeting_rooms", meeting_room_id, {"config": current_config})
        except Exception as e:
            logger.error(f"Failed to update autonomous config: {e}")

    async def process_autonomous_discussion(
        self,
        context: MeetingContext,
        topic: str,
        total_rounds: int,
        speaking_order: str = "priority",
    ) -> AsyncGenerator[dict, None]:
        """Run autonomous discussion for configured rounds.

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
                metadata={"autonomous": True, "topic": topic, "total_rounds": total_rounds},
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
                    "is_paused": False,
                },
            )

            all_participant_names = [p["agent_display_name"] for p in context.participants]
            total_tokens_input = 0
            total_tokens_output = 0

            for round_num in range(1, total_rounds + 1):
                # Update current round in config
                await self._update_autonomous_config(
                    context.meeting_room_id,
                    {"current_round": round_num, "agents_spoken_this_round": []},
                )

                # Signal round start
                yield {
                    "type": "discussion_round_start",
                    "round_number": round_num,
                    "total_rounds": total_rounds,
                }

                # Get speaking order for this round
                speakers = self._get_round_speakers(context.participants, speaking_order, round_num)

                round_messages: list[dict] = []

                for participant in speakers:
                    # Check for user interjection before each agent speaks
                    has_interjection = await self._check_for_user_interjection(context.meeting_room_id)
                    if has_interjection:
                        await self._update_autonomous_config(
                            context.meeting_room_id, {"is_active": False, "is_paused": True}
                        )
                        yield {
                            "type": "discussion_paused",
                            "reason": "user_interjection",
                            "current_round": round_num,
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
                        "turn_number": round_num,
                    }

                    try:
                        # Build autonomous context
                        autonomous_ctx = AutonomousContext(
                            topic=topic,
                            total_rounds=total_rounds,
                            current_round=round_num,
                            speaking_order=speaking_order,
                            round_messages=round_messages,
                        )

                        other_participants = [n for n in all_participant_names if n != agent_display_name]

                        effective_instruction = agent.system_instruction
                        reminder = get_compliance_reminder(agent_name, str(context.meeting_room_id))
                        if reminder:
                            effective_instruction = effective_instruction + "\n\n" + reminder

                        autonomous_system_prompt = self._build_autonomous_system_prompt(
                            agent_name=agent_name,
                            agent_display_name=agent_display_name,
                            context=context,
                            base_instruction=effective_instruction,
                            autonomous_context=autonomous_ctx,
                            other_participants=other_participants,
                        )

                        # Build messages with topic and round context
                        messages = self._build_autonomous_messages(context, topic, round_messages)

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
                                    "content": text,
                                }

                            final_message = stream.get_final_message()
                            tokens_input = final_message.usage.input_tokens
                            tokens_output = final_message.usage.output_tokens

                        # Determine responding_to (last speaker)
                        responding_to = round_messages[-1]["agent_name"] if round_messages else None

                        # Score manifesto compliance for autonomous agent
                        autonomous_compliance = score_manifesto_compliance(full_response, agent_name, source="meeting")
                        autonomous_metadata = {
                            "tokens": {"input": tokens_input, "output": tokens_output},
                            "autonomous": True,
                        }
                        if autonomous_compliance:
                            autonomous_metadata["manifesto_compliance"] = autonomous_compliance

                        # Record score for drift tracking
                        record_compliance_score(
                            str(context.meeting_room_id),
                            agent_name,
                            autonomous_compliance["score"],
                            autonomous_compliance.get("gaps", []),
                        )

                        # Store the agent's response
                        auto_msg_id = await self._store_autonomous_message(
                            meeting_room_id=context.meeting_room_id,
                            content=full_response,
                            agent_id=agent_id,
                            agent_name=agent_name,
                            agent_display_name=agent_display_name,
                            discussion_round=round_num,
                            responding_to_agent=responding_to,
                            metadata=autonomous_metadata,
                        )

                        # Trigger semantic evaluation if warranted
                        if should_semantic_evaluate(autonomous_compliance, agent_name):
                            trigger_semantic_evaluation(
                                full_response,
                                agent_name,
                                autonomous_compliance,
                                message_id=auto_msg_id,
                                table_name="meeting_room_messages",
                            )

                        # Update participant stats
                        await self._update_participant_stats(
                            meeting_room_id=context.meeting_room_id,
                            agent_id=agent_id,
                            tokens_used=tokens_output,
                        )

                        total_tokens_input += tokens_input
                        total_tokens_output += tokens_output

                        # Add to round messages for next agent's context
                        round_messages.append(
                            {
                                "agent_name": agent_name,
                                "agent_display_name": agent_display_name,
                                "content": full_response,
                            }
                        )

                        # Signal turn end
                        yield {
                            "type": "agent_turn_end",
                            "agent_name": agent_name,
                            "tokens": {"input": tokens_input, "output": tokens_output},
                            "full_response": full_response,
                        }

                    except Exception as e:
                        logger.error(f"Error in autonomous turn from {agent_name}: {e}")
                        yield {"type": "error", "agent_name": agent_name, "message": str(e)}

                # Signal round end
                yield {
                    "type": "discussion_round_end",
                    "round_number": round_num,
                    "agents_responded": [p["agent_name"] for p in speakers],
                }

            # Update meeting room token total
            await self._update_meeting_tokens(context.meeting_room_id, total_tokens_input + total_tokens_output)

            # Mark discussion as complete
            await self._update_autonomous_config(context.meeting_room_id, {"is_active": False, "is_paused": False})

            # Store completion message
            await self._store_message(
                meeting_room_id=context.meeting_room_id,
                role="system",
                content=f"[AUTONOMOUS DISCUSSION COMPLETED]\n{total_rounds} rounds completed.",
                turn_number=total_rounds + 1,
                metadata={
                    "autonomous": True,
                    "discussion_complete": True,
                    "total_tokens": total_tokens_input + total_tokens_output,
                },
            )

            # Signal discussion complete
            yield {
                "type": "discussion_complete",
                "total_rounds_completed": total_rounds,
                "total_tokens": {"input": total_tokens_input, "output": total_tokens_output},
            }

        except Exception as e:
            logger.error(f"Autonomous discussion error: {e}")
            await self._update_autonomous_config(context.meeting_room_id, {"is_active": False, "is_paused": True})
            yield {"type": "discussion_paused", "reason": "error", "current_round": 0}
            yield {"type": "error", "message": str(e)}

    def _build_autonomous_messages(self, context: MeetingContext, topic: str, round_messages: list[dict]) -> list[dict]:
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
            messages.append(
                {
                    "role": "user",
                    "content": "Continue the discussion. Respond to what other agents have said.",
                }
            )
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
        metadata: Optional[dict] = None,
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

            result = pb.create_record("meeting_room_messages", insert_data)

            # Get the message ID for embedding
            if result:
                message_id = result.get("id")
                if message_id:
                    # Queue embedding in background (don't await)
                    asyncio.create_task(self._embed_message_background(message_id, content))
                return message_id
            return None

        except Exception as e:
            logger.error(f"Failed to store autonomous message: {e}")
            return None

    async def stop_autonomous_discussion(self, meeting_room_id: str) -> None:
        """Stop an ongoing autonomous discussion."""
        await self._update_autonomous_config(meeting_room_id, {"is_active": False, "is_paused": True})

        await self._store_message(
            meeting_room_id=meeting_room_id,
            role="system",
            content="[AUTONOMOUS DISCUSSION STOPPED BY USER]",
            metadata={"autonomous": True, "stopped": True},
        )

    async def get_autonomous_status(self, meeting_room_id: str) -> dict:
        """Get the current autonomous discussion status."""
        try:
            room = pb.get_record("meeting_rooms", meeting_room_id)
            config = room.get("config", {}) if room else {}
            if isinstance(config, str):
                config = pb.parse_json_field(config, default={})
            autonomous = config.get("autonomous", {})

            return {
                "is_active": autonomous.get("is_active", False),
                "topic": autonomous.get("topic"),
                "total_rounds": autonomous.get("total_rounds", 0),
                "current_round": autonomous.get("current_round", 0),
                "speaking_order": autonomous.get("speaking_order", "priority"),
                "is_paused": autonomous.get("is_paused", False),
                "can_resume": autonomous.get("is_paused", False) and autonomous.get("topic") is not None,
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
                "can_resume": False,
            }


async def get_meeting_orchestrator(supabase=None, anthropic_client: anthropic.Anthropic = None) -> MeetingOrchestrator:
    """Factory function to create a MeetingOrchestrator with all agents loaded.

    Includes the Facilitator and Reporter meta-agents which are always present in meetings.
    - Facilitator: Orchestrates conversation flow, routes to agents
    - Reporter: Synthesizes discussions into unified summaries.
    """
    from agents.atlas import AtlasAgent
    from agents.capital import CapitalAgent
    from agents.counselor import CounselorAgent
    from agents.guardian import GuardianAgent
    from agents.oracle import OracleAgent
    from agents.sage import SageAgent

    # Initialize the Facilitator meta-agent (always present)
    facilitator = None
    try:
        from agents.facilitator import FacilitatorAgent

        facilitator = FacilitatorAgent(None, anthropic_client)
        await facilitator.initialize()
        logger.info("Facilitator meta-agent initialized")
    except Exception as e:
        logger.warning(f"Could not load Facilitator agent: {e}")

    # Initialize the Reporter meta-agent (always present for summaries)
    reporter = None
    try:
        from agents.reporter import ReporterAgent

        reporter = ReporterAgent(None, anthropic_client)
        await reporter.initialize()
        logger.info("Reporter meta-agent initialized")
    except Exception as e:
        logger.warning(f"Could not load Reporter agent: {e}")

    # Initialize all available agents
    agents: dict[str, BaseAgent] = {}

    # Core agents (these should exist)
    try:
        agents["atlas"] = AtlasAgent(None, anthropic_client)
        agents["capital"] = CapitalAgent(None, anthropic_client)
        agents["guardian"] = GuardianAgent(None, anthropic_client)
        agents["counselor"] = CounselorAgent(None, anthropic_client)
        agents["oracle"] = OracleAgent(None, anthropic_client)
        agents["sage"] = SageAgent(None, anthropic_client)
    except Exception as e:
        logger.error(f"Error loading core agents: {e}")

    # Try to load additional agents if they exist
    try:
        from agents.strategist import StrategistAgent

        agents["strategist"] = StrategistAgent(None, anthropic_client)
    except ImportError:
        pass

    try:
        from agents.architect import ArchitectAgent

        agents["architect"] = ArchitectAgent(None, anthropic_client)
    except ImportError:
        pass

    try:
        from agents.operator import OperatorAgent

        agents["operator"] = OperatorAgent(None, anthropic_client)
    except ImportError:
        pass

    try:
        from agents.pioneer import PioneerAgent

        agents["pioneer"] = PioneerAgent(None, anthropic_client)
    except ImportError:
        pass

    try:
        from agents.catalyst import CatalystAgent

        agents["catalyst"] = CatalystAgent(None, anthropic_client)
    except ImportError:
        pass

    try:
        from agents.scholar import ScholarAgent

        agents["scholar"] = ScholarAgent(None, anthropic_client)
    except ImportError:
        pass

    try:
        from agents.nexus import NexusAgent

        agents["nexus"] = NexusAgent(None, anthropic_client)
    except ImportError:
        pass

    try:
        from agents.echo import EchoAgent

        agents["echo"] = EchoAgent(None, anthropic_client)
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

    return MeetingOrchestrator(None, anthropic_client, agents, facilitator, reporter)
