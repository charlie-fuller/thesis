"""Glean Evaluator Agent - "Can We Glean This?".

The Glean Evaluator agent specializes in:
- Assessing PRDs and application requests for Glean platform fit
- Evaluating integration requirements and data source compatibility
- Analyzing scale, cost, and time-to-value considerations
- Recommending alternatives when Glean is not appropriate
- Identifying security and compliance requirements
"""

import logging
from pathlib import Path
from typing import Optional

import anthropic

from supabase import Client

from .base_agent import AgentContext, AgentResponse, BaseAgent

logger = logging.getLogger(__name__)


class GleanEvaluatorAgent(BaseAgent):
    """Glean Evaluator - The "Can We Glean This?" Platform Fit Assessor.

    Specializes in evaluating whether Glean is the appropriate tool
    for a given PRD, discussion, or application request. Considers
    integration requirements, data access, scale, cost, and security.
    """

    def __init__(self, supabase: Client, anthropic_client: anthropic.Anthropic):
        super().__init__(
            name="glean_evaluator",
            display_name="Can We Glean This?",
            supabase=supabase,
            anthropic_client=anthropic_client,
        )

    def _get_default_instruction(self) -> str:
        """Load system instruction from XML file or return fallback."""
        xml_path = Path(__file__).parent.parent / "system_instructions/agents/glean_evaluator.xml"
        if xml_path.exists():
            return xml_path.read_text()
        return self._fallback_instruction()

    def _fallback_instruction(self) -> str:
        """Minimal fallback if XML file is not available."""
        return """You are the Glean Evaluator, known as "Can We Glean This?" for Thesis.

You specialize in:
- Assessing PRDs and application requests for Glean platform fit
- Evaluating integration requirements and data source compatibility
- Analyzing scale, cost, and time-to-value considerations
- Recommending alternatives when Glean is not appropriate

Key Glean capabilities: Enterprise search across 100+ integrations, AI assistant,
permission-aware results, knowledge graph, real-time sync.

Key Glean limitations: Requires 100+ users, ~$60K+ annual cost, no content creation,
limited workflow automation, requires good underlying data quality.

Provide clear GO/NO-GO/MAYBE recommendations with specific reasoning."""

    async def process(self, context: AgentContext) -> AgentResponse:
        """Process a Glean fit assessment query."""
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
            memory_content=f"Glean assessment: {context.user_message[:100]}..."
            if save_to_memory
            else None,
        )

    def _should_save_to_memory(self, query: str, response: str) -> bool:
        """Determine if this interaction should be saved to memory."""
        important_indicators = [
            "glean",
            "assessment",
            "recommendation",
            "go",
            "no-go",
            "alternative",
            "integration",
            "platform",
            "decision",
        ]
        query_lower = query.lower()
        response_lower = response.lower()

        for indicator in important_indicators:
            if indicator in query_lower or indicator in response_lower:
                return True

        # Don't save very short responses (likely clarifying questions)
        if len(response) < 200:
            return False

        return False

    def should_handoff(self, context: AgentContext, response: str) -> Optional[tuple[str, str]]:
        """Check if we should hand off to another agent."""
        message_lower = context.user_message.lower()

        # Hand off to Architect for deep technical architecture questions
        if any(
            word in message_lower
            for word in ["architecture", "rag", "custom build", "technical design"]
        ):
            return ("architect", "Query requires deep technical architecture expertise")

        # Hand off to Guardian for security/compliance deep-dives
        if any(
            word in message_lower
            for word in ["soc2", "hipaa", "gdpr", "security audit", "compliance"]
        ):
            return ("guardian", "Query requires security/compliance expertise")

        # Hand off to Capital for detailed cost analysis
        if any(
            word in message_lower
            for word in ["budget", "roi", "cost breakdown", "financial analysis"]
        ):
            return ("capital", "Query requires detailed financial analysis")

        return None
