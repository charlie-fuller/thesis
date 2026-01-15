"""
Operator Agent - Business Operations Partner

The Operator agent specializes in:
- Process analysis and workflow optimization
- Automation opportunity assessment
- Operational metrics and KPIs
- Ground-level change management
- Exception handling and SOP design
- AI opportunity triage and pipeline management (Project-Triage integration)
"""

import logging
from pathlib import Path
from typing import Optional

import anthropic
from supabase import Client

from .base_agent import BaseAgent, AgentContext, AgentResponse
from services.operator_tools import OperatorTools

logger = logging.getLogger(__name__)


class OperatorAgent(BaseAgent):
    """
    Operator - The Business Operations Partner.

    Specializes in process optimization, automation assessment,
    operational metrics, and ground-level implementation.
    """

    def __init__(self, supabase: Client, anthropic_client: anthropic.Anthropic):
        super().__init__(
            name="operator",
            display_name="Operator",
            supabase=supabase,
            anthropic_client=anthropic_client
        )

    def _get_default_instruction(self) -> str:
        """Load system instruction from XML file or return fallback."""
        xml_path = Path(__file__).parent.parent / "system_instructions/agents/operator.xml"
        if xml_path.exists():
            return xml_path.read_text()
        return self._fallback_instruction()

    def _fallback_instruction(self) -> str:
        """Minimal fallback if XML file is not available."""
        return """You are Operator, the Business Operations Partner for Thesis.

You specialize in:
- Process analysis and workflow optimization
- Automation opportunity assessment
- Operational metrics and KPIs
- Ground-level change management

Provide practical, operations-focused guidance for AI implementation."""

    async def process(self, context: AgentContext) -> AgentResponse:
        """Process an operations query."""
        messages = self._build_messages(context)

        # Add any relevant memories to the context
        if context.memories:
            memory_context = "\n\nRelevant previous context:\n"
            for memory in context.memories[:5]:
                memory_context += f"- {memory.get('content', '')}\n"
            messages[0]["content"] = memory_context + "\n\n" + messages[0]["content"]

        # Inject project-triage context if query relates to opportunities, stakeholders, or metrics
        triage_keywords = [
            "opportunity", "opportunities", "pipeline", "triage",
            "stakeholder", "metrics", "tier", "blocked", "priority",
            "meeting prep", "focus", "kpi", "validation"
        ]
        query_lower = context.user_message.lower()
        if any(kw in query_lower for kw in triage_keywords):
            try:
                tools = OperatorTools(self.supabase, context.client_id)
                triage_context = tools.format_context_injection()
                messages[0]["content"] = triage_context + "\n\n" + messages[0]["content"]
                logger.info("Injected project-triage context for Operator query")
            except Exception as e:
                logger.warning(f"Failed to inject triage context: {e}")

        response = self.anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
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
            memory_content=f"Operations insight: {context.user_message[:100]}..." if save_to_memory else None
        )

    def _should_save_to_memory(self, query: str, response: str) -> bool:
        """Determine if this interaction should be saved to memory."""
        important_indicators = [
            "process", "workflow", "automation", "metrics",
            "kpi", "baseline", "efficiency", "bottleneck",
            "opportunity", "triage", "tier", "stakeholder", "blocked"
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
        if any(word in message_lower for word in ["architecture", "system design", "integration pattern"]):
            return ("architect", "Query requires technical architecture expertise")

        # Hand off to Sage for people/change management
        if any(word in message_lower for word in ["resistance", "adoption", "fear", "burnout"]):
            return ("sage", "Query requires people/change management expertise")

        # Hand off to Capital for detailed ROI analysis
        if any(word in message_lower for word in ["roi calculation", "cost-benefit", "financial model"]):
            return ("capital", "Query requires detailed financial analysis")

        return None
