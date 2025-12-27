"""
Base Agent class for Thesis multi-agent system.

All agents inherit from this class and implement their specialized behaviors.
"""

import logging
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional
from dataclasses import dataclass
from datetime import datetime

import anthropic
from supabase import Client

logger = logging.getLogger(__name__)


@dataclass
class AgentContext:
    """Context passed to agents for each interaction."""
    user_id: str
    client_id: str
    conversation_id: str
    message_history: list[dict]
    user_message: str
    # Optional context from other agents or previous interactions
    handoff_context: Optional[dict] = None
    # Relevant memories from Mem0
    memories: Optional[list[dict]] = None
    # Relevant stakeholders
    stakeholders: Optional[list[dict]] = None


@dataclass
class AgentResponse:
    """Response from an agent."""
    content: str
    agent_name: str
    agent_display_name: str
    # Optional handoff to another agent
    handoff_to: Optional[str] = None
    handoff_reason: Optional[str] = None
    # Extracted data (stakeholders, insights, etc.)
    extracted_data: Optional[dict] = None
    # Whether to save to memory
    save_to_memory: bool = False
    memory_content: Optional[str] = None


class BaseAgent(ABC):
    """
    Base class for all Thesis agents.

    Each agent has:
    - A unique name (atlas, fortuna, guardian, counselor, oracle)
    - A display name for the UI
    - System instructions loaded from database or file
    - Access to Claude API for responses
    - Access to Supabase for data
    """

    def __init__(
        self,
        name: str,
        display_name: str,
        supabase: Client,
        anthropic_client: anthropic.Anthropic,
        system_instruction: Optional[str] = None,
    ):
        self.name = name
        self.display_name = display_name
        self.supabase = supabase
        self.anthropic = anthropic_client
        self._system_instruction = system_instruction
        self._agent_id: Optional[str] = None

    @property
    def agent_id(self) -> Optional[str]:
        """Get the agent's database ID."""
        return self._agent_id

    async def initialize(self) -> None:
        """
        Initialize the agent by loading its configuration from the database.
        Called once when the agent is first loaded.
        """
        try:
            result = self.supabase.table("agents").select("*").eq("name", self.name).single().execute()
            if result.data:
                self._agent_id = result.data["id"]
                # Load active instruction from agent_instruction_versions (single source of truth)
                await self._load_active_instruction()
                logger.info(f"Initialized agent: {self.name} (ID: {self._agent_id})")
            else:
                logger.warning(f"Agent {self.name} not found in database")
        except Exception as e:
            logger.error(f"Failed to initialize agent {self.name}: {e}")

    async def _load_active_instruction(self) -> bool:
        """
        Load the active instruction version from agent_instruction_versions table.
        This is the SINGLE SOURCE OF TRUTH for agent instructions.
        Falls back to Python default if no valid instruction in DB.
        Returns True if DB instruction was loaded.
        """
        if not self._agent_id:
            return False

        try:
            version_result = self.supabase.table("agent_instruction_versions")\
                .select("instructions")\
                .eq("agent_id", self._agent_id)\
                .eq("is_active", True)\
                .limit(1)\
                .execute()

            if version_result.data and version_result.data[0].get("instructions"):
                instruction = version_result.data[0]["instructions"]
                # Only use if it's real content, not a placeholder
                if not instruction.startswith("--") and len(instruction) > 100:
                    self._system_instruction = instruction
                    logger.info(f"Loaded active instruction for {self.name} from DB")
                    return True

            logger.info(f"No active instruction in DB for {self.name}, using Python default")
            return False
        except Exception as e:
            logger.error(f"Failed to load active instruction for {self.name}: {e}")
            return False

    @property
    def system_instruction(self) -> str:
        """Get the agent's system instruction."""
        if self._system_instruction:
            return self._system_instruction
        return self._get_default_instruction()

    async def reload_instruction(self) -> bool:
        """
        Reload the system instruction from the database.
        Called when instructions are updated via the admin UI.
        This hot-reloads from agent_instruction_versions (single source of truth).
        Returns True if reload was successful.
        """
        return await self._load_active_instruction()

    @abstractmethod
    def _get_default_instruction(self) -> str:
        """Get the default system instruction for this agent."""
        pass

    @abstractmethod
    async def process(self, context: AgentContext) -> AgentResponse:
        """
        Process a user message and return a response.

        This is the main method that each agent implements.
        """
        pass

    async def stream(self, context: AgentContext) -> AsyncGenerator[str, None]:
        """
        Stream a response to the user.

        Default implementation uses Claude's streaming API.
        Agents can override this for custom streaming behavior.
        """
        messages = self._build_messages(context)

        with self.anthropic.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=self.system_instruction,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                yield text

    def _build_messages(self, context: AgentContext) -> list[dict]:
        """Build the message list for Claude API."""
        messages = []

        # Add conversation history
        for msg in context.message_history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        # Add the current user message
        messages.append({
            "role": "user",
            "content": context.user_message
        })

        return messages

    def should_handoff(self, context: AgentContext, response: str) -> Optional[tuple[str, str]]:
        """
        Determine if this agent should hand off to another agent.

        Returns (agent_name, reason) if handoff should occur, None otherwise.
        Default implementation returns None - agents override for custom logic.
        """
        return None

    async def save_memory(self, content: str, context: AgentContext, metadata: Optional[dict] = None) -> None:
        """
        Save a memory to Mem0 for future context.

        Memories are tagged with the agent name and relevant metadata.
        """
        # This will be implemented when Mem0 integration is added
        logger.info(f"Would save memory for {self.name}: {content[:100]}...")

    async def get_relevant_memories(self, query: str, context: AgentContext) -> list[dict]:
        """
        Retrieve relevant memories from Mem0.

        Returns memories that are relevant to the current query.
        """
        # This will be implemented when Mem0 integration is added
        return []

    async def log_interaction(self, context: AgentContext, response: AgentResponse) -> None:
        """Log this interaction for analytics and debugging."""
        try:
            # Update conversation with agent info
            if self._agent_id:
                self.supabase.table("conversations").update({
                    "agent_id": self._agent_id,
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("id", context.conversation_id).execute()
        except Exception as e:
            logger.error(f"Failed to log interaction for {self.name}: {e}")
