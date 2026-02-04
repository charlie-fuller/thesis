"""Initiative Agent - DISCo Initiative Discovery Specialist.

The Initiative Agent specializes in:
- DISCo workflow guidance (Discovery, Insights, Synthesis, Capabilities)
- Synthesizing outputs from multiple specialist agents
- PuRDy methodology for product discovery
- Project extraction from initiative insights
- Document intelligence and gap analysis
"""

import logging
from pathlib import Path
from typing import Optional

import anthropic

from supabase import Client

from .base_agent import AgentContext, AgentResponse, BaseAgent

logger = logging.getLogger(__name__)


class InitiativeAgent(BaseAgent):
    """Initiative Agent - The DISCo Initiative Discovery Specialist.

    Specializes in initiative-level discussions with full context injection,
    cross-agent synthesis, methodology guidance, and project extraction.
    """

    def __init__(self, supabase: Client, anthropic_client: anthropic.Anthropic):
        super().__init__(
            name="initiative_agent",
            display_name="Initiative Agent",
            supabase=supabase,
            anthropic_client=anthropic_client,
        )

    def _get_default_instruction(self) -> str:
        """Load system instruction from XML file or return fallback."""
        xml_path = Path(__file__).parent.parent / "system_instructions/agents/initiative_agent.xml"
        if xml_path.exists():
            return xml_path.read_text()
        return self._fallback_instruction()

    def _fallback_instruction(self) -> str:
        """Minimal fallback if XML file is not available."""
        return """You are Initiative Agent, the DISCo Initiative Discovery Specialist for Thesis.

You specialize in:
- DISCo workflow guidance (Discovery, Insights, Synthesis, Capabilities)
- Synthesizing outputs from multiple specialist agents (Atlas, Guardian, Capital, etc.)
- PuRDy methodology for structured product discovery
- Helping extract project opportunities from initiative insights

You have full context about the initiative being discussed, including all agent outputs
and uploaded documents. Use this to provide synthesized, actionable guidance.

Follow Smart Brevity: 100-150 words max, no emojis, end with dig-deeper links."""

    async def process(self, context: AgentContext) -> AgentResponse:
        """Process an initiative-related query."""
        messages = self._build_messages(context)

        # Add any relevant memories to the context
        if context.memories:
            memory_context = "\n\nRelevant previous context:\n"
            for memory in context.memories[:5]:
                memory_context += f"- {memory.get('content', '')}\n"
            messages[0]["content"] = memory_context + "\n\n" + messages[0]["content"]

        # Initiative context (including agent outputs) should be injected
        # by the chat service based on conversation.initiative_id

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
            memory_content=f"Initiative insight: {context.user_message[:100]}..." if save_to_memory else None,
        )

    def _should_save_to_memory(self, query: str, response: str) -> bool:
        """Determine if this interaction should be saved to memory."""
        important_indicators = [
            "synthesis",
            "discovery",
            "insights",
            "capabilities",
            "project",
            "extract",
            "atlas",
            "guardian",
            "capital",
            "counselor",
            "decision",
            "recommendation",
            "next step",
            "phase",
            "purdy",
        ]
        query_lower = query.lower()
        response_lower = response.lower()

        for indicator in important_indicators:
            if indicator in query_lower or indicator in response_lower:
                return True

        # Don't save very short responses
        if len(response) < 200:
            return False

        return False

    def should_handoff(self, context: AgentContext, response: str) -> Optional[tuple[str, str]]:
        """Check if we should hand off to another agent."""
        message_lower = context.user_message.lower()

        # Hand off to Project Agent for project-specific deep dives
        if any(
            phrase in message_lower
            for phrase in ["project details", "project score", "specific project", "this project"]
        ):
            return ("project_agent", "Query requires project-specific context")

        # Hand off to Atlas for new research requests
        if any(
            phrase in message_lower
            for phrase in [
                "research this",
                "market analysis",
                "competitive landscape",
                "find information",
            ]
        ):
            return ("atlas", "Query requires new research")

        # Hand off to specific specialist agents for detailed analysis
        if "guardian" in message_lower and "run" in message_lower:
            return ("guardian", "Request to run Guardian assessment")
        if "capital" in message_lower and "run" in message_lower:
            return ("capital", "Request to run Capital assessment")
        if "counselor" in message_lower and "run" in message_lower:
            return ("counselor", "Request to run Counselor assessment")

        return None
