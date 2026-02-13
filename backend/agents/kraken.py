"""Kraken Agent - Task Evaluation and Autonomous Execution Specialist.

The Kraken agent specializes in:
- Evaluating project tasks for AI workability
- Executing approved tasks non-destructively (output as comments + KB docs)
- Computing agenticity scores to help prioritize work

Note: Kraken operates primarily through its service layer (services/task_kraken.py)
via dedicated API endpoints, not through the chat coordinator. This agent class
exists for registration consistency and potential future chat integration.
"""

import logging

import anthropic

from supabase import Client

from .base_agent import AgentContext, AgentResponse, BaseAgent

logger = logging.getLogger(__name__)


class KrakenAgent(BaseAgent):
    """Kraken - The Task Evaluation and Autonomous Execution Specialist.

    Evaluates project tasks for AI workability and executes approved tasks
    non-destructively. Operates primarily via service endpoints rather than
    the chat coordinator.
    """

    def __init__(self, supabase: Client, anthropic_client: anthropic.Anthropic):
        super().__init__(
            name="kraken",
            display_name="Kraken",
            supabase=supabase,
            anthropic_client=anthropic_client,
        )

    def _get_default_instruction(self) -> str:
        return """<system>

<version>
Name: Kraken - Task Evaluation and Autonomous Execution Specialist
Version: 1.0
Date: 2026-02-13
Created_By: Charlie Fuller
Methodology: Gigawatt v4.0 RCCI Framework
</version>

<role>
You are Kraken, a task evaluation and autonomous execution specialist. Your purpose is to assess project tasks for AI workability and execute approved tasks non-destructively.

Core Identity: "Release the Kraken" - you reach into multiple tasks simultaneously, evaluating what AI can handle and executing the work.

Your Philosophy:
- Not all tasks are created equal for AI execution
- Honest confidence assessments prevent wasted effort
- Non-destructive execution preserves human control
- Substantive output beats vague summaries
</role>

<instructions>
When asked about task evaluation in chat context:
1. Explain that task evaluation is available via the Tasks tab in the project detail view
2. Describe the three categories: automatable, assistable, manual
3. Note that execution output appears as task comments and KB documents
4. Recommend clicking "Release the Kraken" in the Tasks tab for full evaluation

NEVER USE EMOJIS.
</instructions>

</system>"""

    async def process(self, context: AgentContext) -> AgentResponse:
        """Process a chat message. Kraken primarily works via service endpoints."""
        return AgentResponse(
            content=(
                "I evaluate project tasks for AI workability. "
                "To run a full evaluation, open the project detail view and click "
                '"Release the Kraken" in the Tasks tab. '
                "I'll categorize each task as automatable, assistable, or manual, "
                "and you can then select which tasks to execute."
            ),
            agent_name=self.name,
            agent_display_name=self.display_name,
        )
