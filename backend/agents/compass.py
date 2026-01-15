"""
Compass Agent - Personal Career Coach

The Compass agent specializes in:
- Win capture and impact documentation from conversational updates
- Check-in and performance review preparation
- Strategic alignment tracking with company priorities
- Goal progress monitoring and reflection prompting
- Performance Tracker document management

Philosophy: Growth happens in small moments that are easily forgotten.
Compass helps capture them conversationally, connect them to strategy,
and build a compelling narrative of professional growth.
"""

import logging
from typing import Optional

import anthropic
from supabase import Client

from .base_agent import BaseAgent, AgentContext, AgentResponse

logger = logging.getLogger(__name__)


class CompassAgent(BaseAgent):
    """
    Compass - The Personal Career Coach agent.

    Specializes in helping professionals track performance, capture wins,
    prepare for manager conversations, and maintain strategic alignment
    with company goals through natural conversation.
    """

    def __init__(self, supabase: Client, anthropic_client: anthropic.Anthropic):
        super().__init__(
            name="compass",
            display_name="Compass",
            supabase=supabase,
            anthropic_client=anthropic_client
        )

    def _get_default_instruction(self) -> str:
        return """<system>

<version>
Name: Compass - Personal Career Coach
Version: 1.0
Date: 2025-01-15
Created_By: Charlie Fuller
Methodology: Gigawatt v4.0 RCCI Framework
</version>

<role>
You are Compass, a personal career development coach. Your purpose is to help professionals track their performance, capture wins, prepare for manager conversations, and maintain strategic alignment with company goals - all through natural conversation rather than tedious data entry.

Core Identity: "Your career co-pilot" - you help people see their work clearly, connect daily activities to strategic impact, and build a compelling narrative of their professional growth.

Your Philosophy:
- Growth happens in small moments that are easily forgotten without capture
- Strategic alignment beats task completion
- The best career tracking is conversational, not administrative
- Top performers connect their work to company priorities
- Reflection drives intentional growth
</role>

<context>
You support professionals who want to grow their careers but don't have time for elaborate tracking systems. They need:

1. A way to log wins and accomplishments without filling out forms
2. Preparation support for 1:1s, check-ins, and performance reviews
3. Connection between daily work and company strategic priorities
4. Reflection prompts that help them think intentionally about growth
5. A running record that makes performance reviews easy
</context>

<capabilities>
## 1. Win Capture and Impact Documentation
- Extract wins from conversational updates
- Ask clarifying questions to capture impact metrics
- Map wins to competencies and strategic priorities

## 2. Check-In and Review Preparation
- Synthesize recent wins into talking points
- Generate discussion questions for manager conversations
- Create evidence-based self-assessments

## 3. Strategic Alignment Tracking
- Connect individual initiatives to company priorities
- Validate work against strategic alignment criteria
- Surface opportunities to increase strategic relevance

## 4. Goal Tracking and Reflection
- Track progress on 30-60-90 day plans
- Generate reflection questions
- Identify patterns in wins and challenges
</capabilities>

<instructions>
## Win Capture Process

When someone shares an accomplishment:
1. Acknowledge the win
2. Ask ONE clarifying question for impact (hours saved, stakeholders, etc.)
3. Connect it to their strategic priorities
4. Confirm the capture format

## Check-In Preparation

When preparing for a manager conversation:
1. Summarize recent documented wins
2. Note goal progress status
3. Suggest discussion topics
4. Ask what they most want to communicate

## Always Be Specific
- Reference their actual goals and context
- Connect to their company's priorities
- Use their stakeholder names
- Never give generic career advice
</instructions>

<criteria>
1. Conversational - feels like talking to a colleague
2. Impact-Focused - always pushes for measurable outcomes
3. Evidence-Based - grounds advice in their actual tracker
4. Efficient - maximum value with minimum effort
5. Strategic - connects individual work to bigger picture
</criteria>

</system>"""

    async def process(self, context: AgentContext) -> AgentResponse:
        """Process a career development or performance tracking query."""
        messages = self._build_messages(context)

        # Add any relevant memories to the context
        if context.memories:
            memory_context = "\n\nRelevant previous context about this person's career:\n"
            for memory in context.memories[:5]:  # Limit to 5 most relevant
                memory_context += f"- {memory.get('content', '')}\n"
            messages[0]["content"] = memory_context + "\n\n" + messages[0]["content"]

        # Add stakeholder context if available (for relationship tracking)
        if context.stakeholders:
            stakeholder_context = "\n\nKey relationships being tracked:\n"
            for stakeholder in context.stakeholders[:5]:
                name = stakeholder.get('name', 'Unknown')
                role = stakeholder.get('role', 'Unknown role')
                engagement = stakeholder.get('engagement_level', 'unknown')
                stakeholder_context += f"- {name} ({role}): {engagement}\n"
            messages[0]["content"] = stakeholder_context + "\n\n" + messages[0]["content"]

        response = self.anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=self.system_instruction,
            messages=messages
        )

        content = response.content[0].text

        # Career conversations often contain important context worth saving
        save_to_memory = self._should_save_to_memory(context.user_message, content)

        return AgentResponse(
            content=content,
            agent_name=self.name,
            agent_display_name=self.display_name,
            save_to_memory=save_to_memory,
            memory_content=f"Career update: {context.user_message[:100]}..." if save_to_memory else None
        )

    def _should_save_to_memory(self, query: str, response: str) -> bool:
        """Determine if this interaction should be saved to memory."""
        # Save interactions that reveal important career/performance content
        important_indicators = [
            "win", "accomplished", "shipped", "launched", "completed",
            "goal", "check-in", "1:1", "review", "feedback",
            "promotion", "growth", "skill", "competency", "impact",
            "stakeholder", "relationship", "manager", "mentor"
        ]
        query_lower = query.lower()
        response_lower = response.lower()

        # Check if query or response contains important career content
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

        # Hand off to Sage for deeper change management or people challenges
        if any(word in message_lower for word in ["team resistance", "burnout", "culture change", "adoption challenge"]):
            return ("sage", "Query requires people/change management expertise")

        # Hand off to Scholar for training program design
        if any(word in message_lower for word in ["training program", "learning path", "curriculum", "upskilling plan"]):
            return ("scholar", "Query requires L&D expertise")

        # Hand off to Strategist for executive-level career strategy
        if any(word in message_lower for word in ["executive visibility", "c-suite", "board presentation", "organizational politics"]):
            return ("strategist", "Query requires executive strategy expertise")

        # Hand off to Oracle for meeting transcript analysis
        if any(word in message_lower for word in ["analyze meeting", "transcript", "what did they say", "meeting notes"]):
            return ("oracle", "Query involves transcript analysis")

        return None
