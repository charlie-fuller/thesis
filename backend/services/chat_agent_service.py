"""Chat Agent Service - Integrates agent routing into the chat flow.

Handles:
1. Agent selection from request (explicit selection via UI)
2. @mention parsing from messages
3. Coordinator-based routing when no agent specified
4. Loading agent-specific system instructions
"""

import logging
import re
from dataclasses import dataclass
from typing import Optional

import anthropic

from agents import AgentRouter
from services.instruction_loader import instruction_file_exists, load_instruction_from_file
from supabase import Client

logger = logging.getLogger(__name__)


@dataclass
class AgentSelection:
    """Result of agent selection for a chat message."""

    primary_agent: str  # Agent name (e.g., "atlas", "capital")
    display_name: str  # Display name for UI (e.g., "Atlas", "Capital")
    system_instruction: str  # The system instruction to use
    confidence: float  # Routing confidence (1.0 for explicit selection)
    reason: str  # Why this agent was selected
    supporting_agents: list[str] = None  # Additional agents that may be relevant

    def __post_init__(self):
        if self.supporting_agents is None:
            self.supporting_agents = []


# Agent display names mapping
AGENT_DISPLAY_NAMES = {
    "atlas": "Atlas (Research)",
    "capital": "Capital (Finance)",
    "guardian": "Guardian (IT/Governance)",
    "counselor": "Counselor (Legal)",
    "oracle": "Oracle (Meeting Intelligence)",
    "sage": "Sage (People/Change)",
    "strategist": "Strategist (Executive)",
    "architect": "Architect (Technical)",
    "operator": "Operator (Operations)",
    "pioneer": "Pioneer (Innovation)",
    "catalyst": "Catalyst (Communications)",
    "scholar": "Scholar (L&D)",
    "echo": "Echo (Brand Voice)",
    "nexus": "Nexus (Systems Thinking)",
    "coordinator": "Coordinator",
}

# @mention patterns - matches @agentname at word boundaries
MENTION_PATTERN = re.compile(
    r"@(atlas|capital|guardian|counselor|oracle|sage|strategist|architect|"
    r"operator|pioneer|catalyst|scholar|echo|nexus|coordinator|"
    r"research|finance|it|governance|legal|transcript|people|change|"
    r"executive|technical|operations|innovation|comms|training|voice|systems)",
    re.IGNORECASE,
)

# Map alternate names to canonical names
MENTION_ALIASES = {
    "research": "atlas",
    "finance": "capital",
    "it": "guardian",
    "governance": "guardian",
    "legal": "counselor",
    "transcript": "oracle",
    "people": "sage",
    "change": "sage",
    "executive": "strategist",
    "technical": "architect",
    "operations": "operator",
    "innovation": "pioneer",
    "comms": "catalyst",
    "training": "scholar",
    "voice": "echo",
    "systems": "nexus",
}


class ChatAgentService:
    """Service for routing chat messages to the appropriate agent(s).

    Usage:
        service = ChatAgentService(supabase, anthropic_client)
        selection = await service.select_agent(
            message="@atlas what are the latest GenAI trends?",
            agent_ids=None,  # or ["atlas"] for explicit selection
            conversation_context={"current_agent": "atlas"}
        )
        # Use selection.system_instruction for Claude API call
    """

    def __init__(self, supabase: Client, anthropic_client: anthropic.Anthropic):
        self.supabase = supabase
        self.anthropic = anthropic_client
        self._router = AgentRouter(supabase, anthropic_client)
        self._instruction_cache: dict[str, str] = {}

    def parse_mentions(self, message: str) -> list[str]:
        """Parse @mentions from a message.

        Returns list of canonical agent names mentioned.
        """
        mentions = MENTION_PATTERN.findall(message.lower())

        # Convert to canonical names
        canonical = []
        for mention in mentions:
            canonical_name = MENTION_ALIASES.get(mention, mention)
            if canonical_name not in canonical:
                canonical.append(canonical_name)

        return canonical

    async def get_agent_instruction(self, agent_name: str) -> Optional[str]:
        """Load system instruction for an agent.

        Priority:
        1. Cache (if already loaded)
        2. Active version from agent_instruction_versions table
        3. XML file from backend/system_instructions/agents/
        4. None (use default behavior)
        """
        # Check cache first
        if agent_name in self._instruction_cache:
            return self._instruction_cache[agent_name]

        instruction = None

        # Priority 1: XML files are the source of truth (per CLAUDE.md)
        # This ensures updates to XML files take effect immediately
        if instruction_file_exists(agent_name):
            instruction = load_instruction_from_file(agent_name)
            if instruction:
                logger.info(
                    f"Loaded instruction for {agent_name} from XML ({len(instruction)} chars)"
                )

        # Priority 2: Fall back to database if no XML file exists
        if not instruction:
            try:
                # First get agent ID
                agent_result = (
                    self.supabase.table("agents")
                    .select("id")
                    .eq("name", agent_name)
                    .single()
                    .execute()
                )

                if agent_result.data:
                    agent_id = agent_result.data["id"]

                    # Get active instruction version
                    version_result = (
                        self.supabase.table("agent_instruction_versions")
                        .select("instructions")
                        .eq("agent_id", agent_id)
                        .eq("is_active", True)
                        .limit(1)
                        .execute()
                    )

                    if version_result.data and version_result.data[0].get("instructions"):
                        db_instruction = version_result.data[0]["instructions"]
                        # Only use if it's real content, not a placeholder
                        if not db_instruction.startswith("--") and len(db_instruction) > 100:
                            instruction = db_instruction
                            logger.info(
                                f"Loaded instruction for {agent_name} from DB ({len(instruction)} chars)"
                            )
            except Exception as e:
                logger.error(f"Failed to load instruction from DB for {agent_name}: {e}")

        # Cache if found
        if instruction:
            self._instruction_cache[agent_name] = instruction

        return instruction

    async def select_agent(
        self,
        message: str,
        agent_ids: Optional[list[str]] = None,
        conversation_context: Optional[dict] = None,
        fallback_instruction: Optional[str] = None,
    ) -> AgentSelection:
        """Select the appropriate agent(s) for a chat message.

        Args:
            message: The user's message
            agent_ids: Explicit agent selection from UI (takes priority)
            conversation_context: Context about the conversation (current_agent, etc.)
            fallback_instruction: Default instruction if no agent selected

        Returns:
            AgentSelection with the agent to use and their system instruction
        """
        primary_agent = None
        confidence = 0.0
        reason = ""
        supporting_agents = []

        # Priority 1: Explicit agent selection from UI
        if agent_ids and len(agent_ids) > 0:
            primary_agent = agent_ids[0].lower()
            supporting_agents = [a.lower() for a in agent_ids[1:]]
            confidence = 1.0
            reason = "Explicit selection from UI"
            logger.info(f"Agent explicitly selected: {primary_agent}")

        # Priority 2: @mention in message
        if not primary_agent:
            mentions = self.parse_mentions(message)
            if mentions:
                primary_agent = mentions[0]
                supporting_agents = mentions[1:]
                confidence = 1.0
                reason = f"@mention in message: @{primary_agent}"
                logger.info(f"Agent mentioned in message: {primary_agent}")

        # Priority 3: Use AgentRouter for intelligent routing
        if not primary_agent:
            routing_decision = self._router.route(message, conversation_context)
            primary_agent = routing_decision.primary_agent
            supporting_agents = routing_decision.supporting_agents or []
            confidence = routing_decision.confidence
            reason = routing_decision.reason
            logger.info(f"Router selected agent: {primary_agent} ({reason})")

        # Load the agent's system instruction
        instruction = await self.get_agent_instruction(primary_agent)

        # If no agent instruction found, use coordinator or fallback
        if not instruction:
            if primary_agent != "coordinator":
                # Try coordinator as fallback
                instruction = await self.get_agent_instruction("coordinator")
                if instruction:
                    logger.info(f"No instruction for {primary_agent}, using coordinator")

            # Ultimate fallback
            if not instruction:
                instruction = fallback_instruction or self._get_generic_instruction()
                logger.info(f"Using fallback instruction for {primary_agent}")

        display_name = AGENT_DISPLAY_NAMES.get(primary_agent, primary_agent.capitalize())

        return AgentSelection(
            primary_agent=primary_agent,
            display_name=display_name,
            system_instruction=instruction,
            confidence=confidence,
            reason=reason,
            supporting_agents=supporting_agents,
        )

    def _get_generic_instruction(self) -> str:
        """Get a generic fallback instruction."""
        return """You are Thesis, a helpful AI assistant for enterprise GenAI strategy.
You help AI Solutions Partners guide and manage successful AI initiatives.

Provide clear, accurate, and professional assistance. Focus on practical,
actionable guidance while considering both technical and human factors.

If a question falls outside your expertise, acknowledge this and suggest
which specialist might be better suited to help."""

    async def get_conversation_agent_context(self, conversation_id: str) -> Optional[dict]:
        """Get the agent context for an existing conversation.

        Returns context including current_agent if the conversation
        has an established agent.
        """
        try:
            # Check if conversation has an associated agent
            conv_result = (
                self.supabase.table("conversations")
                .select("agent_id, agents(name)")
                .eq("id", conversation_id)
                .single()
                .execute()
            )

            if conv_result.data and conv_result.data.get("agents"):
                agent_name = conv_result.data["agents"]["name"]
                return {"current_agent": agent_name}

            # Check last message for agent context
            msg_result = (
                self.supabase.table("messages")
                .select("metadata")
                .eq("conversation_id", conversation_id)
                .eq("role", "assistant")
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )

            if msg_result.data and msg_result.data[0].get("metadata"):
                metadata = msg_result.data[0]["metadata"]
                if metadata.get("agent_name"):
                    return {"current_agent": metadata["agent_name"]}

        except Exception as e:
            logger.error(f"Failed to get conversation agent context: {e}")

        return None

    def clear_instruction_cache(self, agent_name: Optional[str] = None) -> None:
        """Clear the instruction cache.

        Args:
            agent_name: Specific agent to clear, or None to clear all
        """
        if agent_name:
            self._instruction_cache.pop(agent_name, None)
        else:
            self._instruction_cache.clear()


# Singleton instance
_chat_agent_service: Optional[ChatAgentService] = None


def get_chat_agent_service() -> ChatAgentService:
    """Get the singleton ChatAgentService instance."""
    global _chat_agent_service
    if _chat_agent_service is None:
        import os

        from database import get_supabase

        supabase = get_supabase()
        anthropic_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        _chat_agent_service = ChatAgentService(supabase, anthropic_client)

    return _chat_agent_service
