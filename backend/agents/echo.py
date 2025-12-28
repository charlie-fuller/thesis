"""
Echo Agent - Brand Voice Analysis & Emulation Partner

The Echo agent specializes in:
- Brand voice analysis and profiling
- Writing style documentation
- Voice emulation guidelines for AI content generation
- Tone and style consistency auditing
- Multi-channel voice adaptation
"""

import logging
from pathlib import Path
from typing import Optional

import anthropic
from supabase import Client

from .base_agent import BaseAgent, AgentContext, AgentResponse

logger = logging.getLogger(__name__)


class EchoAgent(BaseAgent):
    """
    Echo - The Brand Voice Analysis & Emulation Partner.

    Specializes in analyzing text samples to create comprehensive
    brand voice profiles and actionable AI emulation guidelines.
    """

    def __init__(self, supabase: Client, anthropic_client: anthropic.Anthropic):
        super().__init__(
            name="echo",
            display_name="Echo",
            supabase=supabase,
            anthropic_client=anthropic_client
        )

    def _get_default_instruction(self) -> str:
        """Load system instruction from XML file or return fallback."""
        xml_path = Path(__file__).parent.parent / "system_instructions/agents/echo.xml"
        if xml_path.exists():
            return xml_path.read_text()
        return self._fallback_instruction()

    def _fallback_instruction(self) -> str:
        """Minimal fallback if XML file is not available."""
        return """You are Echo, the Brand Voice Analysis & Emulation Partner for Thesis.

You specialize in:
- Analyzing text samples to identify brand voice characteristics
- Creating comprehensive brand voice profiles
- Developing actionable AI emulation guidelines
- Auditing content for voice consistency
- Adapting voice across channels and content types

Help create detailed, implementable brand voice specifications."""

    async def process(self, context: AgentContext) -> AgentResponse:
        """Process a brand voice analysis query."""
        messages = self._build_messages(context)

        # Add any relevant memories to the context
        if context.memories:
            memory_context = "\n\nRelevant previous context:\n"
            for memory in context.memories[:5]:
                memory_context += f"- {memory.get('content', '')}\n"
            messages[0]["content"] = memory_context + "\n\n" + messages[0]["content"]

        response = self.anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8192,  # Higher token limit for detailed voice analysis
            system=self.system_instruction,
            messages=messages
        )

        content = response.content[0].text

        # Determine if this should be saved to memory
        save_to_memory = self._should_save_to_memory(context.user_message, content)

        return AgentResponse(
            content=content,
            agent_name=self.name,
            agent_display_name=self.display_name,
            save_to_memory=save_to_memory,
            memory_content=f"Brand voice insight: {context.user_message[:100]}..." if save_to_memory else None
        )

    def _should_save_to_memory(self, query: str, response: str) -> bool:
        """Determine if this interaction should be saved to memory."""
        important_indicators = [
            "brand voice", "tone", "style", "emulation", "persona",
            "writing style", "voice profile", "voice guidelines"
        ]
        query_lower = query.lower()
        response_lower = response.lower()

        for indicator in important_indicators:
            if indicator in query_lower or indicator in response_lower:
                return True

        # Save if we created a substantial voice profile
        if len(response) > 2000:
            return True

        return False

    def should_handoff(self, context: AgentContext, response: str) -> Optional[tuple[str, str]]:
        """Check if we should hand off to another agent."""
        message_lower = context.user_message.lower()

        # Hand off to Catalyst for internal communications application
        if any(word in message_lower for word in ["internal communication", "employee messaging", "announcement"]):
            return ("catalyst", "Query requires internal communications expertise")

        # Hand off to Scholar for training content voice
        if any(word in message_lower for word in ["training material", "learning content", "educational"]):
            return ("scholar", "Query requires L&D content expertise")

        # Hand off to Strategist for executive communication voice
        if any(word in message_lower for word in ["executive communication", "board presentation", "investor"]):
            return ("strategist", "Query requires executive communications expertise")

        return None
