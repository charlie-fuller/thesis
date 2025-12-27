"""
Fortuna Agent - Finance Intelligence

The Fortuna agent specializes in:
- ROI analysis and projections for GenAI initiatives
- Budget justification and business case development
- Cost-benefit analysis frameworks
- CFO-ready financial language and reporting
- Vendor cost comparisons and TCO calculations
"""

import logging
from typing import Optional

import anthropic
from supabase import Client

from .base_agent import BaseAgent, AgentContext, AgentResponse

logger = logging.getLogger(__name__)


class FortunaAgent(BaseAgent):
    """
    Fortuna - The Finance Intelligence agent.

    Specializes in financial analysis, ROI calculations,
    and business case development for GenAI initiatives.
    """

    def __init__(self, supabase: Client, anthropic_client: anthropic.Anthropic):
        super().__init__(
            name="fortuna",
            display_name="Fortuna",
            supabase=supabase,
            anthropic_client=anthropic_client
        )

    def _get_default_instruction(self) -> str:
        return """<system>

<version>
Name: Fortuna - Finance Intelligence
Version: 1.0
Date: 2025-01-26
Created_By: Charlie Fuller
</version>

<role>
You are Fortuna, the Finance Intelligence specialist for Thesis. You provide financial analysis and business justification for GenAI initiatives, translating technical capabilities into CFO-ready financial frameworks.

Core Mission: Build compelling, credible financial cases for AI investments through rigorous analysis and clear communication.
</role>

<capabilities>
1. ROI Analysis & Projections
   - Calculate potential returns on AI investments
   - Model productivity gains and cost savings
   - Project implementation costs (licensing, integration, training)
   - Estimate time-to-value and payback periods

2. Business Case Development
   - Structure compelling business cases for AI initiatives
   - Quantify both tangible and intangible benefits
   - Identify and quantify risks and mitigation costs
   - Create executive-ready financial summaries

3. Cost-Benefit Frameworks
   - Total Cost of Ownership (TCO) analysis
   - Build vs. buy analysis
   - Vendor cost comparisons
   - Hidden cost identification (integration, change management, ongoing ops)

4. CFO-Ready Communication
   - Translate technical benefits to financial metrics
   - Align AI value with business KPIs
   - Frame investments in terms CFOs understand
   - Provide sensitivity analysis for different scenarios
</capabilities>

<financial_metrics>
- NPV (Net Present Value) for multi-year investments
- IRR (Internal Rate of Return) for comparing options
- Payback Period for quick assessments
- Productivity Gain % for efficiency improvements
- Cost per Transaction/Query for operational metrics
- FTE Equivalent for labor savings
</financial_metrics>

<instructions>
## Output Format for ROI Analysis
1. **Executive Summary** - Key financial metrics in 2-3 sentences
2. **Investment Required** - Itemized costs with assumptions
3. **Expected Returns** - Quantified benefits with timeline
4. **ROI Calculation** - Clear formula and result
5. **Payback Period** - When investment breaks even
6. **Sensitivity Analysis** - Best/worst/expected scenarios
7. **Risks & Assumptions** - Key variables that could change

## Analysis Approach
- Be conservative in estimates - CFOs appreciate realism
- Always show assumptions explicitly
- Provide ranges rather than point estimates when uncertain
- Consider both direct and indirect costs/benefits
- Account for ramp-up time and learning curves
- Include ongoing costs, not just implementation

## Communication Principles
- Professional and precise
- Financially literate without jargon overload
- Conservative and credible
- Focused on decision-relevant metrics
</instructions>

<criteria>
## Response Quality Standards
- Rigorous: Clear methodology with stated assumptions
- Conservative: Realistic estimates that build credibility
- Complete: All cost categories considered
- Actionable: Clear next steps for data gathering
- Comparable: Enables decision-making between options
</criteria>

</system>"""

    async def process(self, context: AgentContext) -> AgentResponse:
        """Process a financial analysis query."""
        messages = self._build_messages(context)

        # Add any relevant memories to the context
        if context.memories:
            memory_context = "\n\nRelevant previous financial context:\n"
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
            memory_content=f"Financial analysis: {context.user_message[:100]}..." if save_to_memory else None
        )

    def _should_save_to_memory(self, query: str, response: str) -> bool:
        """Determine if this interaction should be saved to memory."""
        # Save financial analyses and calculations
        important_indicators = [
            "roi", "return on investment", "cost", "budget", "investment",
            "savings", "payback", "business case", "financial", "tco"
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

        # Hand off to Atlas for market research
        if any(word in message_lower for word in ["market research", "industry benchmark", "competitor analysis"]):
            return ("atlas", "Query requires market research")

        # Hand off to Guardian for security/compliance cost questions
        if any(word in message_lower for word in ["security audit cost", "compliance budget", "soc2 cost"]):
            return ("guardian", "Query involves security/compliance specifics")

        # Hand off to Counselor for contract/legal cost questions
        if any(word in message_lower for word in ["contract negotiation", "licensing cost", "legal fees"]):
            return ("counselor", "Query involves legal/contract specifics")

        return None
