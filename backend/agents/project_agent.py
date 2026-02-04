"""Project Agent - AI Implementation Project Specialist.

The Project Agent specializes in:
- Deep-dive discussions about specific AI implementation projects
- Score analysis and justification (ROI, Effort, Alignment, Readiness)
- Evidence-based recommendations using linked documents
- Task breakdown with Taskmaster integration
- Initiative relationship awareness
"""

import logging
from pathlib import Path
from typing import Optional

import anthropic

from supabase import Client

from .base_agent import AgentContext, AgentResponse, BaseAgent

logger = logging.getLogger(__name__)


class ProjectAgent(BaseAgent):
    """Project Agent - The AI Implementation Project Specialist.

    Specializes in project-specific Q&A with full context injection,
    score justification, document evidence, and task breakdown.
    """

    def __init__(self, supabase: Client, anthropic_client: anthropic.Anthropic):
        super().__init__(
            name="project_agent",
            display_name="Project Agent",
            supabase=supabase,
            anthropic_client=anthropic_client,
        )

    def _get_default_instruction(self) -> str:
        """Load system instruction from XML file or return fallback."""
        xml_path = Path(__file__).parent.parent / "system_instructions/agents/project_agent.xml"
        if xml_path.exists():
            return xml_path.read_text()
        return self._fallback_instruction()

    def _fallback_instruction(self) -> str:
        """Minimal fallback if XML file is not available."""
        return """You are Project Agent, the AI Implementation Project Specialist for Thesis.

You specialize in:
- Deep-dive discussions about specific AI implementation projects
- Score analysis and justification (ROI, Effort, Alignment, Readiness)
- Evidence-based recommendations using linked documents
- Task breakdown and actionable next steps

You have full context about the project being discussed. Use this context to provide
specific, evidence-based guidance. Always cite linked documents when available.

Follow Smart Brevity: 100-150 words max, no emojis, end with dig-deeper links."""

    async def process(self, context: AgentContext) -> AgentResponse:
        """Process a project-related query."""
        messages = self._build_messages(context)

        # Add any relevant memories to the context
        if context.memories:
            memory_context = "\n\nRelevant previous context:\n"
            for memory in context.memories[:5]:
                memory_context += f"- {memory.get('content', '')}\n"
            messages[0]["content"] = memory_context + "\n\n" + messages[0]["content"]

        # Project context should be injected by the chat service
        # based on conversation.project_id - this agent expects it

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
            memory_content=f"Project insight: {context.user_message[:100]}..."
            if save_to_memory
            else None,
        )

    def _should_save_to_memory(self, query: str, response: str) -> bool:
        """Determine if this interaction should be saved to memory."""
        important_indicators = [
            "score",
            "roi",
            "effort",
            "alignment",
            "readiness",
            "confidence",
            "evidence",
            "document",
            "task",
            "breakdown",
            "initiative",
            "status",
            "blocker",
            "decision",
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

        # Hand off to Taskmaster for detailed task management
        if any(
            phrase in message_lower
            for phrase in ["create task", "add task", "task list", "my tasks"]
        ):
            return ("taskmaster", "Query requires task management capabilities")

        # Hand off to Capital for detailed financial analysis
        if any(
            phrase in message_lower
            for phrase in ["roi calculation", "cost-benefit", "financial model", "npv"]
        ):
            return ("capital", "Query requires detailed financial analysis")

        # Hand off to Operator for process/operational details
        if any(
            phrase in message_lower
            for phrase in ["process flow", "workflow", "automation", "operational metrics"]
        ):
            return ("operator", "Query requires operational process expertise")

        # Hand off to Initiative Agent for initiative-level discussions
        if any(
            phrase in message_lower
            for phrase in ["initiative overview", "disco process", "discovery phase"]
        ):
            return ("initiative_agent", "Query requires initiative-level context")

        return None
