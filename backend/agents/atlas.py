"""
Atlas Agent - Research Intelligence

The Atlas agent specializes in:
- Tracking GenAI research and trends
- Monitoring consulting approaches (Big 4, McKinsey, BCG, etc.)
- Finding and synthesizing case studies
- Tracking thought leadership and academic research
- Providing evidence-based recommendations
"""

import logging
from typing import Optional

import anthropic
from supabase import Client

from .base_agent import BaseAgent, AgentContext, AgentResponse

logger = logging.getLogger(__name__)


class AtlasAgent(BaseAgent):
    """
    Atlas - The Research Intelligence agent.

    Specializes in GenAI implementation research, consulting approaches,
    and evidence-based recommendations.
    """

    def __init__(self, supabase: Client, anthropic_client: anthropic.Anthropic):
        super().__init__(
            name="atlas",
            display_name="Atlas",
            supabase=supabase,
            anthropic_client=anthropic_client
        )

    def _get_default_instruction(self) -> str:
        return """You are Atlas, the Research Intelligence agent for Thesis.

Your role is to help with GenAI strategy research and provide evidence-based insights.

CAPABILITIES:
1. Track and synthesize GenAI implementation research
2. Monitor consulting firm approaches (McKinsey, BCG, Bain, Big 4, Accenture)
3. Find and analyze corporate case studies
4. Track thought leadership from key publications
5. Summarize academic research (MIT Sloan, HBR, Gartner, Forrester)
6. Identify patterns and trends across sources
7. Provide actionable recommendations based on evidence

RESEARCH FOCUS AREAS:
- Enterprise GenAI implementation strategies
- Change management for AI adoption
- ROI measurement frameworks
- Governance and risk approaches
- Successful implementation patterns
- Common failure modes and how to avoid them

ANALYSIS APPROACH:
- Synthesize multiple sources when possible
- Distinguish between proven approaches and speculation
- Highlight conflicting perspectives when they exist
- Consider organizational context (size, industry, maturity)
- Focus on actionable insights, not just information

OUTPUT FORMAT:
When providing research insights:
1. **Summary** - Key findings in 2-3 sentences
2. **Evidence** - Specific sources, case studies, or data points
3. **Implications** - What this means for GenAI strategy
4. **Recommendations** - Concrete next steps or considerations
5. **Caveats** - Limitations or areas of uncertainty

TONE:
- Professional and analytical
- Evidence-based, citing sources when available
- Balanced, acknowledging uncertainty
- Strategic, focusing on decision-relevant insights
- Supportive of the user's goals

When you don't have specific information, be honest about it and suggest ways to find the information (web search, specific publications to check, etc.)."""

    async def process(self, context: AgentContext) -> AgentResponse:
        """Process a research query."""
        messages = self._build_messages(context)

        # Add any relevant memories to the context
        if context.memories:
            memory_context = "\n\nRelevant previous context:\n"
            for memory in context.memories[:5]:  # Limit to 5 most relevant
                memory_context += f"- {memory.get('content', '')}\n"
            messages[0]["content"] = memory_context + "\n\n" + messages[0]["content"]

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
            memory_content=f"Research query: {context.user_message[:100]}..." if save_to_memory else None
        )

    def _should_save_to_memory(self, query: str, response: str) -> bool:
        """Determine if this interaction should be saved to memory."""
        # Save research that provides substantive insights
        important_indicators = [
            "recommendation", "finding", "study", "research",
            "approach", "framework", "best practice", "lesson"
        ]
        query_lower = query.lower()
        response_lower = response.lower()

        # Check if query or response contains important research content
        for indicator in important_indicators:
            if indicator in query_lower or indicator in response_lower:
                return True

        # Don't save simple questions
        if len(response) < 200:
            return False

        return False

    def should_handoff(self, context: AgentContext, response: str) -> Optional[tuple[str, str]]:
        """Check if we should hand off to another agent."""
        message_lower = context.user_message.lower()

        # Hand off to Fortuna for ROI/cost questions
        if any(word in message_lower for word in ["roi calculation", "budget", "cost-benefit", "financial model"]):
            return ("fortuna", "Query requires detailed financial analysis")

        # Hand off to Guardian for security/compliance specifics
        if any(word in message_lower for word in ["security policy", "compliance framework", "audit requirement"]):
            return ("guardian", "Query requires security/governance expertise")

        # Hand off to Counselor for legal specifics
        if any(word in message_lower for word in ["contract review", "liability", "ip rights", "licensing terms"]):
            return ("counselor", "Query requires legal expertise")

        # Hand off to Oracle for transcript analysis
        if any(word in message_lower for word in ["transcript", "meeting notes", "analyze this call"]):
            return ("oracle", "Query involves transcript analysis")

        return None
