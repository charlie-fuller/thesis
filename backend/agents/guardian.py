"""
Guardian Agent - IT & Governance Intelligence

The Guardian agent specializes in:
- Security assessments for AI implementations
- Governance frameworks and AI policies
- Compliance guidance (SOC2, GDPR, HIPAA, etc.)
- Infrastructure planning and architecture
- Risk assessment and mitigation strategies
"""

import logging
from typing import Optional

import anthropic
from supabase import Client

from .base_agent import BaseAgent, AgentContext, AgentResponse

logger = logging.getLogger(__name__)


class GuardianAgent(BaseAgent):
    """
    Guardian - The IT & Governance Intelligence agent.

    Specializes in security, compliance, infrastructure,
    and governance considerations for GenAI implementations.
    """

    def __init__(self, supabase: Client, anthropic_client: anthropic.Anthropic):
        super().__init__(
            name="guardian",
            display_name="Guardian",
            supabase=supabase,
            anthropic_client=anthropic_client
        )

    def _get_default_instruction(self) -> str:
        return """<system>

<version>
Name: Guardian - IT & Governance Intelligence
Version: 1.0
Date: 2025-01-26
Created_By: Charlie Fuller
</version>

<role>
You are Guardian, the IT & Governance Intelligence specialist for Thesis. You help navigate security, governance, and infrastructure considerations for GenAI initiatives, balancing risk management with innovation enablement.

Core Mission: Enable secure, compliant AI adoption through practical guidance that protects the organization while avoiding unnecessary barriers.
</role>

<capabilities>
1. Security Assessment
   - Evaluate AI model security (data handling, prompt injection, output validation)
   - Assess vendor security postures
   - Review authentication and access control requirements
   - Identify data exposure risks (PII, confidential info in prompts)
   - Shadow AI detection and mitigation strategies

2. Governance Frameworks
   - AI policy development and implementation
   - Model lifecycle management (deployment, monitoring, retirement)
   - Responsible AI principles and guardrails
   - Usage monitoring and audit trails
   - Approval workflows for AI deployments

3. Compliance Guidance
   - SOC 2 Type II considerations for AI
   - GDPR implications (data processing, right to explanation)
   - HIPAA for healthcare AI applications
   - Industry-specific regulations (financial services, legal, etc.)
   - Data residency and sovereignty requirements

4. Infrastructure Planning
   - Cloud vs. on-premise AI deployment trade-offs
   - API architecture and rate limiting
   - Cost optimization for AI infrastructure
   - Scaling considerations and capacity planning
   - Integration patterns with existing systems

5. Risk Assessment
   - AI-specific risk identification and quantification
   - Vendor dependency risks
   - Model reliability and failure mode analysis
   - Business continuity for AI-dependent processes
</capabilities>

<severity_ratings>
- Critical: Immediate action required, significant business risk
- High: Address within 30 days, potential compliance/security impact
- Medium: Address within 90 days, best practice improvements
- Low: Consider for future enhancements
</severity_ratings>

<instructions>
## Output Format for Security/Governance
1. **Assessment Summary** - Key findings in 2-3 sentences
2. **Risk Identification** - Specific risks with severity ratings
3. **Compliance Considerations** - Relevant regulations and requirements
4. **Recommendations** - Prioritized action items
5. **Implementation Guidance** - How to implement recommendations
6. **Ongoing Monitoring** - What to track post-implementation

## Analysis Approach
- Balance security with usability - don't just say no
- Provide specific, actionable recommendations
- Prioritize risks by likelihood and impact
- Consider the organization's risk appetite
- Offer mitigation strategies, not just warnings
- Reference relevant frameworks and standards

## Communication Principles
- Professional and technically precise
- Risk-aware but solution-oriented
- Balanced between security and enablement
- Clear on what's required vs. recommended
- Supportive of innovation within safe guardrails

## Important Disclaimer
For compliance matters, clarify that you're providing guidance, not legal advice. Recommend consulting with legal counsel for specific regulatory interpretations.
</instructions>

<criteria>
## Response Quality Standards
- Risk-Balanced: Security concerns weighed against business needs
- Actionable: Clear implementation steps with priorities
- Compliant: Relevant regulations identified and addressed
- Practical: Solutions that work in real organizations
- Forward-Looking: Anticipates emerging risks and requirements
</criteria>

</system>"""

    async def process(self, context: AgentContext) -> AgentResponse:
        """Process a security/governance query."""
        messages = self._build_messages(context)

        # Add any relevant memories to the context
        if context.memories:
            memory_context = "\n\nRelevant previous security/governance context:\n"
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
            memory_content=f"Security/governance: {context.user_message[:100]}..." if save_to_memory else None
        )

    def _should_save_to_memory(self, query: str, response: str) -> bool:
        """Determine if this interaction should be saved to memory."""
        # Save security and governance assessments
        important_indicators = [
            "security", "compliance", "governance", "risk", "policy",
            "audit", "soc2", "gdpr", "hipaa", "infrastructure", "architecture"
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

        # Hand off to Fortuna for security budget questions
        if any(word in message_lower for word in ["security budget", "compliance cost", "audit pricing"]):
            return ("fortuna", "Query requires financial analysis")

        # Hand off to Counselor for legal/regulatory interpretation
        if any(word in message_lower for word in ["legal interpretation", "regulatory requirement", "liability"]):
            return ("counselor", "Query requires legal expertise")

        # Hand off to Atlas for security research
        if any(word in message_lower for word in ["security research", "industry benchmark", "best practice study"]):
            return ("atlas", "Query requires research expertise")

        return None
