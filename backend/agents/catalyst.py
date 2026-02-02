"""Catalyst Agent - Internal Communications Partner.

The Catalyst agent specializes in:
- AI initiative messaging and narratives
- Employee engagement communication
- Addressing AI anxiety proactively
- Multi-channel communication strategies
- Change narrative development
"""

import logging
from pathlib import Path
from typing import Optional

import anthropic

from supabase import Client

from .base_agent import AgentContext, AgentResponse, BaseAgent

logger = logging.getLogger(__name__)


class CatalystAgent(BaseAgent):
    """Catalyst - The Internal Communications Partner.

    Specializes in internal AI messaging, employee engagement,
    addressing AI anxiety, and multi-channel communication.
    """

    def __init__(self, supabase: Client, anthropic_client: anthropic.Anthropic):
        super().__init__(
            name="catalyst",
            display_name="Catalyst",
            supabase=supabase,
            anthropic_client=anthropic_client,
        )

    def _get_default_instruction(self) -> str:
        """Load system instruction from XML file or return fallback."""
        xml_path = Path(__file__).parent.parent / "system_instructions/agents/catalyst.xml"
        if xml_path.exists():
            return xml_path.read_text()
        return self._fallback_instruction()

    def _fallback_instruction(self) -> str:
        """Minimal fallback if XML file is not available."""
        return """You are Catalyst, the Internal Communications Partner for Thesis.

You specialize in:
- AI initiative messaging and narratives
- Employee engagement communication
- Addressing AI anxiety proactively
- Multi-channel communication strategies

Help craft authentic, transparent internal communications that build trust."""

    async def process(self, context: AgentContext) -> AgentResponse:
        """Process an internal communications query."""
        messages = self._build_messages(context)

        # Add any relevant memories to the context
        if context.memories:
            memory_context = "\n\nRelevant previous context:\n"
            for memory in context.memories[:5]:
                memory_context += f"- {memory.get('content', '')}\n"
            messages[0]["content"] = memory_context + "\n\n" + messages[0]["content"]

        response = self.anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=self.system_instruction,
            messages=messages,
        )

        content = response.content[0].text

        # Determine if this should be saved to memory
        save_to_memory = self._should_save_to_memory(context.user_message, content)

        return AgentResponse(
            content=content,
            agent_name=self.name,
            agent_display_name=self.display_name,
            save_to_memory=save_to_memory,
            memory_content=f"Communications insight: {context.user_message[:100]}..."
            if save_to_memory
            else None,
        )

    def _should_save_to_memory(self, query: str, response: str) -> bool:
        """Determine if this interaction should be saved to memory."""
        important_indicators = [
            "messaging",
            "communication",
            "announcement",
            "narrative",
            "employee",
            "engagement",
            "anxiety",
            "transparency",
        ]
        query_lower = query.lower()
        response_lower = response.lower()

        for indicator in important_indicators:
            if indicator in query_lower or indicator in response_lower:
                return True

        if len(response) < 200:
            return False

        return False

    def should_handoff(self, context: AgentContext, response: str) -> Optional[tuple[str, str]]:
        """Check if we should hand off to another agent."""
        message_lower = context.user_message.lower()

        # Hand off to Sage for deep people/change management
        if any(
            word in message_lower
            for word in ["resistance", "burnout", "champion program", "community"]
        ):
            return ("sage", "Query requires people/change management expertise")

        # Hand off to Scholar for training content
        if any(
            word in message_lower
            for word in ["training", "curriculum", "learning program", "skill development"]
        ):
            return ("scholar", "Query requires L&D expertise")

        # Hand off to Strategist for executive communications
        if any(word in message_lower for word in ["executive", "board", "c-suite", "leadership"]):
            return ("strategist", "Query requires executive strategy expertise")

        return None
