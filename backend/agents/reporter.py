"""Reporter Agent - Meeting Synthesis and Documentation.

The Reporter agent specializes in:
- Synthesizing multi-agent discussions into clear summaries
- Creating action items with attribution
- Producing executive briefs for stakeholder sharing
- Documenting disagreements without false consensus
- Providing one unified voice for meeting documentation

Always present in meetings alongside the Facilitator.
Facilitator manages the conversation; Reporter documents it.
"""

import logging
from typing import Optional

import anthropic

from supabase import Client

from .base_agent import AgentContext, AgentResponse, BaseAgent

logger = logging.getLogger(__name__)


class ReporterAgent(BaseAgent):
    """Reporter - The Synthesis and Documentation meta-agent.

    Provides unified documentation of multi-agent discussions.
    Responds to summary, recap, and action item requests.
    Always attributes insights to source agents.
    """

    def __init__(self, supabase: Client, anthropic_client: anthropic.Anthropic):
        super().__init__(
            name="reporter",
            display_name="Reporter",
            supabase=supabase,
            anthropic_client=anthropic_client,
        )

    def _get_default_instruction(self) -> str:
        """Fallback instruction if XML file is not available."""
        return """<system>.

<version>
Name: Reporter - Meeting Synthesis and Documentation
Version: 1.0
Date: 2025-12-28
Created_By: Thesis Platform
Type: Meta-Agent (Synthesis/Documentation)
</version>

<role>
You are the Reporter - the synthesizer who distills multi-agent discussions into clear, actionable documentation.

CRITICAL IDENTITY:
- You are NOT a domain expert
- Your expertise is in SYNTHESIS - combining diverse viewpoints into unified output
- You listen to what all agents said and create a single coherent narrative
- You are the ONLY voice for summaries, recaps, and action items
- You are ALWAYS present in meetings alongside the Facilitator

WHEN TO SPEAK:
You respond when the user asks for:
- A summary of the discussion
- Key takeaways or action items
- A recap of what was discussed
- Documentation of the meeting
- "What did we conclude?"
- "Give me the highlights"
</role>

<instructions>
## ABSOLUTE RULES (NEVER VIOLATE)

1. **NEVER USE EMOJIS** - No emoji characters anywhere
2. **MAXIMUM 150 WORDS** - Response must fit on ONE screen
3. **ALWAYS ATTRIBUTE** - Every insight linked to its source agent
4. **PRESERVE DISAGREEMENT** - Don't create false consensus
5. **ALWAYS END WITH DIG-DEEPER LINKS** - 2-4 links at the bottom

## Summary Format

**Summary: [Topic in 5 words]**

**Key Insights**:
- **[Agent Name]**: [Their key point in one sentence]
- **[Agent Name]**: [Their key point in one sentence]

**Alignment**: [What agents agreed on]

**Tension**: [Where agents disagreed]

**Next Steps**: [Actions if any]

[Get detailed breakdown](dig-deeper:full_summary)
</instructions>

<anti_patterns>
- NEVER offer your own domain opinions
- NEVER smooth over disagreements (preserve them)
- NEVER state insights without attribution
- NEVER write more than the source material
</anti_patterns>

</system>"""

    async def process(self, context: AgentContext) -> AgentResponse:
        """Process a synthesis/documentation request."""
        messages = self._build_messages(context)

        # Add meeting context if available
        if hasattr(context, "meeting_history") and context.meeting_history:
            meeting_context = "\n\nMeeting discussion to synthesize:\n"
            for msg in context.meeting_history:
                agent = msg.get("agent_display_name", msg.get("agent_name", "Unknown"))
                content = msg.get("content", "")
                role = msg.get("role", "user")
                if role == "agent":
                    meeting_context += f"\n**{agent}**: {content}\n"
                elif role == "user":
                    meeting_context += f"\n**User**: {content}\n"
            messages[0]["content"] = meeting_context + "\n\nUser request:\n" + messages[0]["content"]

        response = self.anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=self.system_instruction,
            messages=messages,
        )

        content = response.content[0].text

        return AgentResponse(
            content=content,
            agent_name=self.name,
            agent_display_name=self.display_name,
            save_to_memory=False,
            memory_content=None,
        )

    def is_summary_request(self, message: str) -> bool:
        """Check if a message is requesting a summary or documentation."""
        message_lower = message.lower().strip()

        summary_patterns = [
            "summary",
            "summarize",
            "summarise",
            "sum up",
            "recap",
            "recapitulate",
            "takeaway",
            "take away",
            "takeaways",
            "action item",
            "action items",
            "next step",
            "next steps",
            "what did we",
            "what have we",
            "wrap up",
            "wrap-up",
            "highlight",
            "highlights",
            "key point",
            "key points",
            "conclude",
            "conclusion",
            "document",
            "documentation",
            "brief",
            "briefing",
            "share with",
            "send to",
            "forward to",
            "bottom line",
            "bottomline",
            "tldr",
            "tl;dr",
            "give me the",
            "what should i take",
            "what do i need to know",
        ]

        for pattern in summary_patterns:
            if pattern in message_lower:
                return True

        return False

    def should_handoff(self, context: AgentContext, response: str) -> Optional[tuple[str, str]]:
        """Reporter doesn't hand off - it synthesizes what others said."""
        # Reporter is a synthesis agent, not a routing agent
        # If someone asks a domain question, Facilitator handles routing
        return None
