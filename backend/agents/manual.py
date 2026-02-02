"""Manual Agent - In-App Documentation Assistant.

The Manual agent specializes in:
- Explaining Thesis features and capabilities
- Guiding users through platform navigation
- Troubleshooting common issues
- Onboarding assistance and best practices
- Workflow recommendations
"""

import logging
from pathlib import Path
from typing import Optional

import anthropic

from supabase import Client

from .base_agent import AgentContext, AgentResponse, BaseAgent

logger = logging.getLogger(__name__)


class ManualAgent(BaseAgent):
    """Manual - The In-App Documentation Assistant.

    Specializes in helping users understand and navigate Thesis,
    answering questions about features, and troubleshooting issues.
    """

    def __init__(self, supabase: Client, anthropic_client: anthropic.Anthropic):
        super().__init__(
            name="manual",
            display_name="Manual",
            supabase=supabase,
            anthropic_client=anthropic_client,
        )

    def _get_default_instruction(self) -> str:
        """Load system instruction from XML file or return fallback."""
        xml_path = Path(__file__).parent.parent / "system_instructions/agents/manual.xml"
        if xml_path.exists():
            return xml_path.read_text()
        return self._fallback_instruction()

    def _fallback_instruction(self) -> str:
        """Minimal fallback if XML file is not available."""
        return """You are Manual, the in-app documentation assistant for Thesis.

You specialize in:
- Explaining Thesis features and how to use them
- Guiding users through platform navigation
- Troubleshooting common issues
- Onboarding assistance and best practices
- Workflow recommendations

Be approachable, patient, and helpful. Always cite documentation when available.
If you don't know something, admit it and suggest where to find more information."""

    async def process(self, context: AgentContext) -> AgentResponse:
        """Process a documentation/help query."""
        messages = self._build_messages(context)

        # Add any relevant memories to the context (though Manual rarely uses memory)
        if context.memories:
            memory_context = "\n\nRelevant previous context:\n"
            for memory in context.memories[:3]:
                memory_context += f"- {memory.get('content', '')}\n"
            messages[0]["content"] = memory_context + "\n\n" + messages[0]["content"]

        response = self.anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=self.system_instruction,
            messages=messages,
        )

        content = response.content[0].text

        # Documentation queries rarely need memory persistence
        return AgentResponse(
            content=content,
            agent_name=self.name,
            agent_display_name=self.display_name,
            save_to_memory=False,
        )

    def should_handoff(self, context: AgentContext, response: str) -> Optional[tuple[str, str]]:
        """Check if we should hand off to another agent."""
        message_lower = context.user_message.lower()

        # Hand off to Scholar for training/L&D program questions
        training_keywords = [
            "training program",
            "curriculum",
            "learning path",
            "champion program",
            "enablement program",
            "certification",
        ]
        if any(keyword in message_lower for keyword in training_keywords):
            return ("scholar", "Query requires L&D expertise for program design")

        # Hand off to Facilitator for meeting-related questions
        if any(
            word in message_lower
            for word in ["meeting room", "meeting strategy", "multi-agent discussion"]
        ):
            return ("facilitator", "Query about meeting orchestration best practices")

        # Hand off to Architect for technical integration questions
        if any(
            word in message_lower
            for word in ["api", "integration", "technical architecture", "embed"]
        ):
            return ("architect", "Query requires technical architecture expertise")

        return None
