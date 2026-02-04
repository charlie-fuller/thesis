"""Strategist Agent - Executive Strategy Partner.

The Strategist agent specializes in:
- C-suite engagement and executive sponsorship
- Organizational politics and coalition building
- Governance structure design
- Business case development for executives
- Strategic alignment and transformation leadership
"""

import logging
from pathlib import Path
from typing import Optional

import anthropic

from supabase import Client

from .base_agent import AgentContext, AgentResponse, BaseAgent

logger = logging.getLogger(__name__)


class StrategistAgent(BaseAgent):
    """Strategist - The Executive Strategy Partner.

    Specializes in C-suite engagement, organizational politics,
    governance design, and strategic transformation leadership.
    """

    def __init__(self, supabase: Client, anthropic_client: anthropic.Anthropic):
        super().__init__(
            name="strategist",
            display_name="Strategist",
            supabase=supabase,
            anthropic_client=anthropic_client,
        )

    def _get_default_instruction(self) -> str:
        """Load system instruction from XML file or return fallback."""
        xml_path = Path(__file__).parent.parent / "system_instructions/agents/strategist.xml"
        if xml_path.exists():
            return xml_path.read_text()
        return self._fallback_instruction()

    def _fallback_instruction(self) -> str:
        """Minimal fallback if XML file is not available."""
        return """You are Strategist, the Executive Strategy Partner for Thesis.

You specialize in:
- C-suite engagement and executive sponsorship
- Organizational politics and coalition building
- Governance structure design
- Business case development for executives

Provide strategic, executive-level guidance for AI transformation initiatives."""

    async def process(self, context: AgentContext) -> AgentResponse:
        """Process a strategic query."""
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
            memory_content=f"Strategic insight: {context.user_message[:100]}..." if save_to_memory else None,
        )

    def _should_save_to_memory(self, query: str, response: str) -> bool:
        """Determine if this interaction should be saved to memory."""
        important_indicators = [
            "executive",
            "strategy",
            "governance",
            "sponsor",
            "coalition",
            "transformation",
            "board",
            "c-suite",
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

        # Hand off to Architect for technical architecture questions
        if any(word in message_lower for word in ["architecture", "technical design", "integration", "api"]):
            return ("architect", "Query requires technical architecture expertise")

        # Hand off to Capital for detailed financial modeling
        if any(word in message_lower for word in ["roi calculation", "financial model", "budget breakdown"]):
            return ("capital", "Query requires detailed financial analysis")

        # Hand off to Operator for ground-level operations
        if any(word in message_lower for word in ["process optimization", "workflow", "frontline"]):
            return ("operator", "Query requires operational expertise")

        return None
