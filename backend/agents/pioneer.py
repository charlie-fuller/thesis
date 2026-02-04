"""Pioneer Agent - Innovation/R&D Partner.

The Pioneer agent specializes in:
- Emerging technology scouting and evaluation
- Technology maturity assessment
- Hype cycle navigation and reality checks
- Innovation portfolio strategy
- Experimental approach recommendations
"""

import logging
from pathlib import Path
from typing import Optional

import anthropic

from supabase import Client

from .base_agent import AgentContext, AgentResponse, BaseAgent

logger = logging.getLogger(__name__)


class PioneerAgent(BaseAgent):
    """Pioneer - The Innovation/R&D Partner.

    Specializes in emerging technology evaluation, hype filtering,
    maturity assessment, and innovation portfolio strategy.
    """

    def __init__(self, supabase: Client, anthropic_client: anthropic.Anthropic):
        super().__init__(
            name="pioneer",
            display_name="Pioneer",
            supabase=supabase,
            anthropic_client=anthropic_client,
        )

    def _get_default_instruction(self) -> str:
        """Load system instruction from XML file or return fallback."""
        xml_path = Path(__file__).parent.parent / "system_instructions/agents/pioneer.xml"
        if xml_path.exists():
            return xml_path.read_text()
        return self._fallback_instruction()

    def _fallback_instruction(self) -> str:
        """Minimal fallback if XML file is not available."""
        return """You are Pioneer, the Innovation/R&D Partner for Thesis.

You specialize in:
- Emerging technology scouting and evaluation
- Technology maturity assessment
- Hype cycle navigation and reality checks
- Innovation portfolio strategy

Provide clear-eyed, hype-free guidance on emerging AI technologies."""

    async def process(self, context: AgentContext) -> AgentResponse:
        """Process an innovation/emerging tech query."""
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
            memory_content=f"Innovation assessment: {context.user_message[:100]}..." if save_to_memory else None,
        )

    def _should_save_to_memory(self, query: str, response: str) -> bool:
        """Determine if this interaction should be saved to memory."""
        important_indicators = [
            "emerging",
            "innovation",
            "new technology",
            "maturity",
            "evaluation",
            "assessment",
            "hype",
            "experimental",
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

        # Hand off to Architect for implementation architecture
        if any(word in message_lower for word in ["implement", "architecture", "integrate", "build"]):
            return ("architect", "Query requires technical architecture expertise")

        # Hand off to Atlas for research and case studies
        if any(word in message_lower for word in ["research", "case study", "benchmark", "evidence"]):
            return ("atlas", "Query requires research intelligence")

        # Hand off to Strategist for executive positioning
        if any(word in message_lower for word in ["executive", "board", "business case", "justify"]):
            return ("strategist", "Query requires executive strategy expertise")

        return None
