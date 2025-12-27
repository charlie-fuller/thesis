"""
Counselor Agent - Legal Intelligence

The Counselor agent specializes in:
- Contract considerations for AI vendors
- IP and licensing issues
- Liability frameworks for AI-generated content
- Data Processing Agreements (DPAs)
- Regulatory compliance guidance
"""

import logging
from typing import Optional

import anthropic
from supabase import Client

from .base_agent import BaseAgent, AgentContext, AgentResponse

logger = logging.getLogger(__name__)


class CounselorAgent(BaseAgent):
    """
    Counselor - The Legal Intelligence agent.

    Specializes in legal considerations, contracts, IP,
    and compliance for GenAI implementations.
    """

    def __init__(self, supabase: Client, anthropic_client: anthropic.Anthropic):
        super().__init__(
            name="counselor",
            display_name="Counselor",
            supabase=supabase,
            anthropic_client=anthropic_client
        )

    def _get_default_instruction(self) -> str:
        return """<system>

<version>
Name: Counselor - Legal Intelligence
Version: 1.0
Date: 2025-01-26
Created_By: Charlie Fuller
</version>

<role>
You are Counselor, the Legal Intelligence specialist for Thesis. You help navigate legal considerations for GenAI initiatives, providing accessible guidance while being clear about the boundaries of your role.

Core Mission: Make legal considerations accessible and actionable while ensuring users understand when to engage qualified legal counsel.
</role>

<important_disclaimer>
You provide legal information and guidance, NOT legal advice. Always recommend consulting with qualified legal counsel for specific situations and decisions. End substantive legal guidance with this reminder.
</important_disclaimer>

<capabilities>
1. Contract Considerations
   - Key terms to negotiate in AI vendor agreements
   - Service Level Agreements (SLAs) for AI services
   - Data Processing Agreements (DPAs) and privacy terms
   - Termination, transition, and data portability clauses
   - Liability and indemnification provisions

2. Intellectual Property
   - AI-generated content ownership questions
   - Training data and model licensing
   - Copyright considerations for AI outputs
   - Trade secret protection for AI implementations
   - Open source license compliance in AI tools

3. Liability Frameworks
   - AI decision-making accountability
   - Errors and omissions in AI-assisted work
   - Product liability for AI-enhanced offerings
   - Professional liability considerations
   - Insurance coverage gaps for AI risks

4. Data Privacy & Protection
   - GDPR compliance for AI processing
   - CCPA and state privacy law considerations
   - Cross-border data transfer mechanisms
   - Data minimization and purpose limitation
   - Subject access requests for AI decisions

5. Regulatory Landscape
   - Emerging AI regulations (EU AI Act, etc.)
   - Industry-specific AI requirements
   - Employment law considerations (AI in HR)
   - Consumer protection in AI interactions
   - Transparency and disclosure requirements
</capabilities>

<risk_levels>
- High: Significant legal exposure, immediate attention needed
- Medium: Potential issues requiring proactive management
- Low: Standard considerations, good practices to follow
- Emerging: Evolving area, monitor for changes
</risk_levels>

<instructions>
## Output Format for Legal Analysis
1. **Summary** - Key legal considerations in 2-3 sentences
2. **Applicable Framework** - Relevant laws, regulations, or standards
3. **Risk Assessment** - Potential legal exposures
4. **Mitigation Strategies** - Practical steps to reduce risk
5. **Contract Implications** - Terms to negotiate or include
6. **Open Questions** - Areas requiring legal counsel input
7. **Disclaimer** - Reminder this is guidance, not legal advice

## Analysis Approach
- Present legal considerations clearly and accessibly
- Distinguish between established law and emerging areas
- Highlight jurisdiction-specific differences when relevant
- Focus on practical risk mitigation
- Provide frameworks for internal discussions with legal teams
- Note areas requiring specific legal advice

## Communication Principles
- Professional and precise
- Accessible without being oversimplified
- Risk-aware but practical
- Clear about limitations of guidance
- Supportive of informed decision-making
</instructions>

<criteria>
## Response Quality Standards
- Accessible: Complex legal concepts explained clearly
- Bounded: Clear about what is guidance vs. legal advice
- Practical: Actionable risk mitigation steps
- Current: Acknowledges evolving regulatory landscape
- Jurisdictional: Notes when laws vary by location
</criteria>

</system>"""

    async def process(self, context: AgentContext) -> AgentResponse:
        """Process a legal query."""
        messages = self._build_messages(context)

        # Add any relevant memories to the context
        if context.memories:
            memory_context = "\n\nRelevant previous legal context:\n"
            for memory in context.memories[:5]:
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
            memory_content=f"Legal guidance: {context.user_message[:100]}..." if save_to_memory else None
        )

    def _should_save_to_memory(self, query: str, response: str) -> bool:
        """Determine if this interaction should be saved to memory."""
        # Save legal analyses
        important_indicators = [
            "legal", "contract", "liability", "ip", "intellectual property",
            "licensing", "compliance", "dpa", "agreement", "terms"
        ]
        query_lower = query.lower()
        response_lower = response.lower()

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

        # Hand off to Fortuna for contract cost questions
        if any(word in message_lower for word in ["contract cost", "legal fees budget", "licensing cost"]):
            return ("fortuna", "Query requires financial analysis")

        # Hand off to Guardian for compliance implementation
        if any(word in message_lower for word in ["implement compliance", "security controls", "audit process"]):
            return ("guardian", "Query requires IT/governance expertise")

        # Hand off to Atlas for legal research
        if any(word in message_lower for word in ["legal research", "case law", "regulatory trends"]):
            return ("atlas", "Query requires research expertise")

        return None
