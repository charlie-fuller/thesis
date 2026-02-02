"""Architect Agent - Technical Architecture Partner

The Architect agent specializes in:
- Enterprise AI architecture patterns (RAG, agents, fine-tuning)
- Integration design and data pipelines
- Build vs. buy analysis
- Security architecture and MLOps
- Technical evaluation and vendor assessment
"""

import logging
from pathlib import Path
from typing import Optional

import anthropic

from supabase import Client

from .base_agent import AgentContext, AgentResponse, BaseAgent

logger = logging.getLogger(__name__)


class ArchitectAgent(BaseAgent):
    """Architect - The Technical Architecture Partner.

    Specializes in enterprise AI architecture, integration design,
    build vs. buy decisions, and technical implementation guidance.
    """

    def __init__(self, supabase: Client, anthropic_client: anthropic.Anthropic):
        super().__init__(
            name="architect",
            display_name="Architect",
            supabase=supabase,
            anthropic_client=anthropic_client,
        )

    def _get_default_instruction(self) -> str:
        """Load system instruction from XML file or return fallback."""
        xml_path = Path(__file__).parent.parent / "system_instructions/agents/architect.xml"
        if xml_path.exists():
            return xml_path.read_text()
        return self._fallback_instruction()

    def _fallback_instruction(self) -> str:
        """Minimal fallback if XML file is not available."""
        return """You are Architect, the Technical Architecture Partner for Thesis.

You specialize in:
- Enterprise AI architecture patterns (RAG, agents, fine-tuning)
- Integration design and data pipelines
- Build vs. buy analysis
- Security architecture and MLOps

Provide practical, enterprise-grade technical guidance for AI implementations."""

    async def process(self, context: AgentContext) -> AgentResponse:
        """Process a technical architecture query."""
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
            memory_content=f"Architecture decision: {context.user_message[:100]}..."
            if save_to_memory
            else None,
        )

    def _should_save_to_memory(self, query: str, response: str) -> bool:
        """Determine if this interaction should be saved to memory."""
        important_indicators = [
            "architecture",
            "design",
            "integration",
            "decision",
            "build",
            "buy",
            "vendor",
            "pattern",
            "rag",
            "vector",
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

        # Hand off to Guardian for security policy questions
        if any(word in message_lower for word in ["security policy", "compliance", "soc2", "gdpr"]):
            return ("guardian", "Query requires security/governance expertise")

        # Hand off to Pioneer for emerging technology evaluation
        if any(
            word in message_lower for word in ["emerging", "cutting edge", "experimental", "future"]
        ):
            return ("pioneer", "Query requires emerging technology expertise")

        # Hand off to Operator for operational implementation
        if any(
            word in message_lower for word in ["deploy", "operate", "monitor", "production support"]
        ):
            return ("operator", "Query requires operational expertise")

        return None
