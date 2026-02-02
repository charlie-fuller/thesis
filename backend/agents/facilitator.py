"""Facilitator Agent - Meeting Orchestration Meta-Agent.

The Facilitator is NOT a domain expert. It is a meta-agent that:
- Orchestrates multi-agent meeting discussions
- Acts as gatekeeper - clarifies user intent before inviting agents
- Ensures balanced participation (no single agent dominates)
- Invokes systems thinking (Nexus) on every significant topic
- Bridges perspectives across different domains
- Treats the user as a thought partner, not an audience
- Synthesizes discussions and manages conversation flow

The Facilitator is ALWAYS present in every meeting room.

Key principle: Make others brilliant, not yourself.
"""

import logging
from typing import Optional

import anthropic

from supabase import Client

from .base_agent import AgentContext, AgentResponse, BaseAgent

logger = logging.getLogger(__name__)


class FacilitatorAgent(BaseAgent):
    """Facilitator - The Meeting Orchestration Meta-Agent.

    This agent doesn't provide domain expertise. Instead, it:
    - Welcomes and orients users at meeting start
    - Clarifies user intent before opening the floor
    - Routes questions to appropriate specialist agents
    - Ensures balanced participation across all agents
    - Invokes systems thinking before conclusions
    - Synthesizes discussions and bridges perspectives
    - Engages the user as a thought partner
    """

    def __init__(self, supabase: Client, anthropic_client: anthropic.Anthropic):
        super().__init__(
            name="facilitator",
            display_name="Facilitator",
            supabase=supabase,
            anthropic_client=anthropic_client,
        )

    def _get_default_instruction(self) -> str:
        """Fallback instruction if XML not available."""
        return """<system>.
<role>
You are the Facilitator - a skilled meeting conductor who orchestrates multi-agent discussions.

CRITICAL IDENTITY:
- You are NOT a domain expert
- You NEVER answer substantive questions about research, finance, legal, security, or any specialist topic
- Your expertise is in making groups think better together
- You are ALWAYS present in every meeting

GATEKEEPER ROLE:
When a meeting starts or intent is unclear, YOU have the initial conversation with the user before opening the floor to agents. You clarify what they want to explore, understand their context, and THEN invite relevant agents.

Your job: Draw out insights, bridge perspectives, and ensure every voice (including the user's) contributes to collective intelligence.
</role>

<core_behaviors>
1. WELCOME briefly (2-3 sentences max), name who's present, ask what to explore
2. NEVER let agents introduce themselves with long speeches
3. ROUTE questions to 1-3 relevant agents with brief explanation
4. BALANCE participation - don't let any single expert dominate
5. INVOKE systems thinking (Nexus) before any conclusion
6. ENGAGE the user as a thought partner, not an audience
7. SYNTHESIZE periodically (4-6 sentences max)
8. Stay BRIEF - your messages should be SHORT
</core_behaviors>

<balance_enforcement>
After any agent provides substantial input:
- Immediately invite a contrasting or complementary perspective
- Prioritize agents who haven't spoken
- Technical views need people perspectives (Sage)
- Financial views need risk perspectives (Guardian)
- All views need systems thinking (Nexus)

NEVER let a single expert's view become group consensus unchallenged.
</balance_enforcement>

<remember>
- You are not the star. Create space for others.
- Make others brilliant, not yourself.
- When in doubt, ask the user what they need.
- Always invoke Nexus before conclusions.
</remember>
</system>"""

    async def process(self, context: AgentContext) -> AgentResponse:
        """Process a facilitation request.

        The Facilitator typically operates in streaming mode within the meeting orchestrator,
        but this method supports non-streaming use cases.
        """
        messages = self._build_messages(context)

        response = self.anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=250,  # Facilitator must be brief - routing/synthesis only
            system=self.system_instruction,
            messages=messages,
        )

        content = response.content[0].text

        return AgentResponse(
            content=content,
            agent_name=self.name,
            agent_display_name=self.display_name,
            save_to_memory=False,  # Facilitator doesn't save memories
        )

    async def analyze_intent(
        self, user_message: str, participants: list[dict], message_history: list[dict] = None
    ) -> dict:
        """Analyze user intent to determine facilitation action.

        Returns a dict with:
        - intent_type: 'greeting', 'question', 'followup', 'unclear'
        - agents_to_invoke: list of agent names to invite (0-3)
        - facilitator_message: what the facilitator should say (if any)
        - should_clarify: whether to ask user for clarification first
        """
        # Build participant context
        participant_names = [p.get("agent_display_name", p.get("agent_name")) for p in participants]
        ", ".join(participant_names)

        # Check for greeting patterns
        greeting_patterns = ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]
        message_lower = user_message.lower().strip()

        if any(message_lower.startswith(g) or message_lower == g for g in greeting_patterns):
            return {
                "intent_type": "greeting",
                "agents_to_invoke": [],
                "facilitator_message": self._generate_welcome(participant_names),
                "should_clarify": True,
            }

        # Check for direct agent address (@mention or name)
        for participant in participants:
            agent_name = participant.get("agent_name", "").lower()
            display_name = participant.get("agent_display_name", "").lower()
            if f"@{agent_name}" in message_lower or display_name in message_lower:
                return {
                    "intent_type": "followup",
                    "agents_to_invoke": [agent_name],
                    "facilitator_message": None,  # Direct routing, no facilitation needed
                    "should_clarify": False,
                }

        # For substantive questions, use LLM to determine routing
        routing_result = await self._determine_routing(user_message, participants)

        return routing_result

    def _generate_welcome(self, participant_names: list[str]) -> str:
        """Generate a brief welcome message."""
        if len(participant_names) <= 3:
            names_str = ", ".join(participant_names)
        else:
            names_str = (
                ", ".join(participant_names[:3]) + f", and {len(participant_names) - 3} others"
            )

        return f"Welcome! Today we have {names_str} with us. What would you like us to explore together?"

    async def _determine_routing(self, user_message: str, participants: list[dict]) -> dict:
        """Use LLM to determine which agents should respond."""
        # Build participant info for the prompt
        participant_info = []
        for p in participants:
            name = p.get("agent_display_name", p.get("agent_name"))
            # Add brief expertise description
            expertise = self._get_agent_expertise(p.get("agent_name", ""))
            participant_info.append(f"- {name}: {expertise}")

        participant_str = "\n".join(participant_info)

        routing_prompt = f"""You are a meeting facilitator. Analyze this user message and determine which agents should respond.

PARTICIPANTS IN THIS MEETING:
{participant_str}

USER MESSAGE: {user_message}

Respond with a JSON object (no markdown, just JSON):
{{
    "intent_type": "question" or "unclear",
    "agents_to_invoke": ["agent_name1", "agent_name2"],  // 1-3 agents, use lowercase names
    "facilitator_intro": "Brief intro before agents speak (1-2 sentences)",
    "should_invoke_nexus": true/false  // Should systems thinking be included?
}}

RULES:
- Pick 1-3 most relevant agents based on the question
- Always consider if Nexus (systems thinking) should be included
- Keep facilitator_intro brief - just enough to frame who's being asked and why
- If the question is unclear, set intent_type to "unclear" and ask for clarification"""

        try:
            response = self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=200,
                messages=[{"role": "user", "content": routing_prompt}],
            )

            import json

            result_text = response.content[0].text.strip()
            # Clean up potential markdown formatting
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            result_text = result_text.strip()

            result = json.loads(result_text)

            # Add nexus if recommended and not already included
            agents = result.get("agents_to_invoke", [])
            if result.get("should_invoke_nexus") and "nexus" not in agents:
                # Check if nexus is a participant
                participant_names = [p.get("agent_name", "").lower() for p in participants]
                if "nexus" in participant_names and len(agents) < 3:
                    agents.append("nexus")

            return {
                "intent_type": result.get("intent_type", "question"),
                "agents_to_invoke": agents[:3],  # Max 3 agents
                "facilitator_message": result.get("facilitator_intro"),
                "should_clarify": result.get("intent_type") == "unclear",
            }

        except Exception as e:
            logger.error(f"Error in routing analysis: {e}")
            # Fallback: invoke first 2 participants
            fallback_agents = [p.get("agent_name") for p in participants[:2]]
            return {
                "intent_type": "question",
                "agents_to_invoke": fallback_agents,
                "facilitator_message": "Let me bring in some perspectives on this.",
                "should_clarify": False,
            }

    def _get_agent_expertise(self, agent_name: str) -> str:
        """Get brief expertise description for an agent."""
        expertise_map = {
            "atlas": "Research & Best Practices",
            "capital": "Financial Analysis & ROI",
            "guardian": "Security & Governance",
            "counselor": "Legal & Compliance",
            "oracle": "Meeting Intelligence",
            "sage": "People & Change Management",
            "strategist": "Executive Strategy",
            "architect": "Technical Architecture",
            "operator": "Business Operations",
            "pioneer": "Innovation & R&D",
            "catalyst": "Internal Communications",
            "scholar": "Learning & Development",
            "nexus": "Systems Thinking",
            "echo": "Brand Voice",
        }
        return expertise_map.get(agent_name.lower(), "Specialist")

    async def generate_synthesis(
        self, topic: str, agent_contributions: list[dict], user_context: str = None
    ) -> str:
        """Generate a synthesis of agent contributions.

        Args:
            topic: The topic being discussed
            agent_contributions: List of {agent_name, agent_display_name, content}
            user_context: Optional additional context from user

        Returns:
            A brief synthesis message (4-6 sentences)
        """
        # Format contributions
        contributions_text = []
        for contrib in agent_contributions:
            name = contrib.get("agent_display_name", contrib.get("agent_name"))
            content = contrib.get("content", "")[:500]  # Truncate for prompt
            contributions_text.append(f"{name}: {content}")

        contributions_str = "\n\n".join(contributions_text)

        synthesis_prompt = f"""You are a meeting facilitator synthesizing a discussion.

TOPIC: {topic}

AGENT CONTRIBUTIONS:
{contributions_str}

Write a brief synthesis (4-6 sentences max) that:
1. Summarizes each agent's key point in one sentence
2. Notes areas of agreement or tension
3. Suggests a path forward or asks what to explore next

Be concise. Use bullet points if helpful. End with a question to the user."""

        try:
            response = self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=200,
                messages=[{"role": "user", "content": synthesis_prompt}],
            )
            return response.content[0].text

        except Exception as e:
            logger.error(f"Error generating synthesis: {e}")
            return "Let me summarize where we are. We've heard several perspectives. What would be most helpful to explore further?"

    async def generate_balance_prompt(
        self, last_speaker: str, agents_not_spoken: list[str], topic: str
    ) -> str:
        """Generate a prompt to balance participation.

        Args:
            last_speaker: Name of the agent who just spoke
            agents_not_spoken: List of agent names who haven't contributed
            topic: Current discussion topic

        Returns:
            A brief facilitation message inviting other perspectives
        """
        if not agents_not_spoken:
            return None

        # Get expertise for agents who haven't spoken
        unheard_perspectives = []
        for agent_name in agents_not_spoken[:2]:  # Max 2 to invite
            expertise = self._get_agent_expertise(agent_name)
            display_name = agent_name.title()
            unheard_perspectives.append(f"{display_name} ({expertise})")

        perspectives_str = " and ".join(unheard_perspectives)

        return f"Good insights from {last_speaker.title()}. {perspectives_str} - what's your take on this?"

    def should_handoff(self, context: AgentContext, response: str) -> Optional[tuple[str, str]]:
        """Facilitator doesn't hand off - it routes to multiple agents.

        This method is not used in the standard flow.
        """
        return None
