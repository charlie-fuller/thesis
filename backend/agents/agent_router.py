"""Agent Router for Thesis multi-agent system.

Routes incoming messages to the appropriate agent based on:
1. Explicit agent selection by user
2. Intent detection via keywords
3. LLM-based classification for ambiguous cases
"""

import logging
import re
from dataclasses import dataclass
from typing import Optional

import anthropic

from supabase import Client

logger = logging.getLogger(__name__)


@dataclass
class RoutingDecision:
    """Result of routing decision."""

    primary_agent: str
    confidence: float
    reason: str
    supporting_agents: list[str] = None

    def __post_init__(self):
        if self.supporting_agents is None:
            self.supporting_agents = []


class AgentRouter:
    """Routes messages to the appropriate Thesis agent.

    Routing hierarchy:
    1. Explicit selection (user says "@atlas" or selects in UI)
    2. Keyword matching (fast, for obvious cases)
    3. LLM classification (for ambiguous cases)
    """

    # Keyword patterns for each agent
    AGENT_KEYWORDS = {
        # Stakeholder Perspective Agents
        "atlas": [
            r"\bresearch\b",
            r"\bstudy\b",
            r"\bstudies\b",
            r"\bcase study\b",
            r"\bconsulting\b",
            r"\bmckinsey\b",
            r"\bbcg\b",
            r"\bbain\b",
            r"\baccenture\b",
            r"\bdeloitte\b",
            r"\bkpmg\b",
            r"\bpwc\b",
            r"\bey\b",
            r"\bgartner\b",
            r"\bforrester\b",
            r"\bidc\b",
            r"\bwhitepaper\b",
            r"\breport\b",
            r"\banalysis\b",
            r"\btrend\b",
            r"\bbest practice\b",
            r"\bindustry\b",
            r"\bcompetitor\b",
            r"\bai implementation\b",
            r"\bgenai\b",
            r"\bgen ai\b",
        ],
        "capital": [
            r"\broi\b",
            r"\breturn on investment\b",
            r"\bcost\b",
            r"\bbudget\b",
            r"\bfinance\b",
            r"\bfinancial\b",
            r"\bcfo\b",
            r"\bcontroller\b",
            r"\bsaving\b",
            r"\bexpense\b",
            r"\binvestment\b",
            r"\bspend\b",
            r"\bjustify\b",
            r"\bjustification\b",
            r"\bbusiness case\b",
            r"\bpayback\b",
            r"\bbreakeven\b",
            r"\bvalue\b",
            r"\bprofit\b",
        ],
        "guardian": [
            r"\bsecurity\b",
            r"\bgovernance\b",
            r"\bcompliance\b",
            r"\brisk\b",
            r"\bit\b",
            r"\binfrastructure\b",
            r"\barchitecture\b",
            r"\bpolicy\b",
            r"\bpolicies\b",
            r"\bstandard\b",
            r"\bframework\b",
            r"\bdata protection\b",
            r"\bprivacy\b",
            r"\bgdpr\b",
            r"\bccpa\b",
            r"\baudit\b",
            r"\bcontrol\b",
            r"\baccess\b",
            r"\bpermission\b",
            r"\bciso\b",
            r"\bcio\b",
            r"\bsoc2\b",
            r"\biso\b",
            r"\bhipaa\b",
        ],
        "counselor": [
            r"\blegal\b",
            r"\bcontract\b",
            r"\bagreement\b",
            r"\bterms\b",
            r"\blicense\b",
            r"\blicensing\b",
            r"\bip\b",
            r"\bintellectual property\b",
            r"\bpatent\b",
            r"\bcopyright\b",
            r"\btrademark\b",
            r"\bliability\b",
            r"\bindemnity\b",
            r"\bwarranty\b",
            r"\blawyer\b",
            r"\battorney\b",
            r"\bcounsel\b",
            r"\bnda\b",
            r"\bmsa\b",
            r"\bsow\b",
            r"\bsla\b",
        ],
        "oracle": [
            r"\btranscript\b",
            r"\bmeeting\b",
            r"\bcall\b",
            r"\bconversation\b",
            r"\battendee\b",
            r"\bparticipant\b",
            r"\bspeaker\b",
            r"\bsentiment\b",
            r"\bfeedback\b",
            r"\breaction\b",
            r"\bgranola\b",
            r"\botter\b",
            r"\bzoom\b",
            r"\bteams\b",
            r"\bupload\b",
            r"\banalyze\b",
            r"\bextract\b",
            r"\bwho said\b",
            r"\bwhat did .+ say\b",
            r"\bstakeholder\b",
        ],
        "sage": [
            r"\bpeople\b",
            r"\bchange management\b",
            r"\badoption\b",
            r"\bresistance\b",
            r"\bfear\b",
            r"\banxiety\b",
            r"\bburnout\b",
            r"\bchampion\b",
            r"\bculture\b",
            r"\bhuman\b",
            r"\bflourishing\b",
            r"\bpsychology\b",
            r"\bsafety\b",
            r"\bmorale\b",
            r"\bengagement\b",
            r"\bemployee\b",
            r"\bteam\b",
            r"\bpeople-first\b",
            r"\bhuman-centered\b",
        ],
        # Consulting/Implementation Agents
        "strategist": [
            r"\bexecutive\b",
            r"\bc-suite\b",
            r"\bceo\b",
            r"\bboard\b",
            r"\bsponsor\b",
            r"\bstakeholder management\b",
            r"\bcoalition\b",
            r"\bpolitics\b",
            r"\bgovernance structure\b",
            r"\bstrategic alignment\b",
            r"\btransformation\b",
            r"\bleadership\b",
            r"\bbuy-in\b",
        ],
        "architect": [
            r"\barchitecture\b",
            r"\bintegration\b",
            r"\bapi\b",
            r"\btechnical design\b",
            r"\bbuild vs buy\b",
            r"\brag\b",
            r"\bvector\b",
            r"\bembedding\b",
            r"\bmlops\b",
            r"\bdevops\b",
            r"\bmicroservices\b",
            r"\bdata pipeline\b",
            r"\bsystem design\b",
            r"\btechnical\b",
        ],
        "operator": [
            r"\bprocess\b",
            r"\bworkflow\b",
            r"\bautomation\b",
            r"\bmetrics\b",
            r"\bkpi\b",
            r"\bbaseline\b",
            r"\bexception\b",
            r"\bsop\b",
            r"\boperations\b",
            r"\befficiency\b",
            r"\bthroughput\b",
            r"\bbottleneck\b",
            r"\bfrontline\b",
            r"\bday-to-day\b",
        ],
        "pioneer": [
            r"\bemerging\b",
            r"\binnovation\b",
            r"\br&d\b",
            r"\bnew technology\b",
            r"\bcutting edge\b",
            r"\bexperimental\b",
            r"\bprototype\b",
            r"\bhype\b",
            r"\bmaturity\b",
            r"\breadiness\b",
            r"\bquantum\b",
            r"\bfuture\b",
            r"\bhorizon\b",
        ],
        # Internal Enablement Agents
        "catalyst": [
            r"\binternal communications\b",
            r"\bmessaging\b",
            r"\bnarrative\b",
            r"\bemployee engagement\b",
            r"\bannouncement\b",
            r"\ball-hands\b",
            r"\btown hall\b",
            r"\binternal marketing\b",
            r"\bai anxiety\b",
            r"\btransparency\b",
            r"\bemail\b",
        ],
        "scholar": [
            r"\btraining\b",
            r"\blearning\b",
            r"\bl&d\b",
            r"\benablement\b",
            r"\bcurriculum\b",
            r"\bcourse\b",
            r"\bworkshop\b",
            r"\bcertification\b",
            r"\bchampion program\b",
            r"\bskill development\b",
            r"\badult learning\b",
            r"\bcapability building\b",
            r"\bonboarding\b",
        ],
        "echo": [
            r"\bbrand voice\b",
            r"\bstyle\b",
            r"\btone\b",
            r"\bvoice analysis\b",
            r"\bai emulation\b",
            r"\bwriting style\b",
            r"\bvoice profile\b",
            r"\bbrand guidelines\b",
            r"\btone of voice\b",
            r"\bstyle guide\b",
            r"\bcommunication style\b",
            r"\bbrand consistency\b",
        ],
        # Systems/Coordination Agents
        "nexus": [
            r"\bsystems thinking\b",
            r"\bfeedback loop\b",
            r"\bleverage point\b",
            r"\bunintended consequence\b",
            r"\binterconnection\b",
            r"\bcomplexity\b",
            r"\bsecond-order effect\b",
            r"\bsystem dynamics\b",
            r"\barchetype\b",
            r"\breinforcing loop\b",
            r"\bbalancing loop\b",
            r"\bmental model\b",
            r"\broot cause\b",
            r"\bholistic\b",
            r"\bripple effect\b",
        ],
    }

    # Explicit agent mentions
    AGENT_MENTIONS = {
        # Stakeholder Perspective Agents
        "@atlas": "atlas",
        "@capital": "capital",
        "@guardian": "guardian",
        "@counselor": "counselor",
        "@oracle": "oracle",
        "@sage": "sage",
        # Consulting/Implementation Agents
        "@strategist": "strategist",
        "@architect": "architect",
        "@operator": "operator",
        "@pioneer": "pioneer",
        # Internal Enablement Agents
        "@catalyst": "catalyst",
        "@scholar": "scholar",
        "@echo": "echo",
        # Systems/Coordination Agents
        "@nexus": "nexus",
        "@coordinator": "coordinator",
        # Alternate names
        "@research": "atlas",
        "@finance": "capital",
        "@it": "guardian",
        "@governance": "guardian",
        "@legal": "counselor",
        "@transcript": "oracle",
        "@people": "sage",
        "@change": "sage",
        "@executive": "strategist",
        "@technical": "architect",
        "@operations": "operator",
        "@innovation": "pioneer",
        "@comms": "catalyst",
        "@training": "scholar",
        "@voice": "echo",
        "@systems": "nexus",
    }

    def __init__(self, supabase: Client, anthropic_client: anthropic.Anthropic):
        self.supabase = supabase
        self.anthropic = anthropic_client

    def route(self, message: str, conversation_context: Optional[dict] = None) -> RoutingDecision:
        """Route a message to the appropriate agent.

        Args:
            message: The user's message
            conversation_context: Optional context about the conversation
                (e.g., previous agent, topic)

        Returns:
            RoutingDecision with primary agent and optional supporting agents
        """
        message_lower = message.lower()

        # 1. Check for explicit agent mention
        for mention, agent in self.AGENT_MENTIONS.items():
            if mention in message_lower:
                return RoutingDecision(
                    primary_agent=agent, confidence=1.0, reason=f"Explicit mention of {mention}"
                )

        # 2. Check conversation context for continuity
        if conversation_context and conversation_context.get("current_agent"):
            # If we're in an active conversation with an agent, continue with them
            # unless the message clearly indicates a switch
            current_agent = conversation_context["current_agent"]
            keyword_scores = self._score_keywords(message_lower)

            # Only switch if another agent scores significantly higher
            current_score = keyword_scores.get(current_agent, 0)
            max_other_score = max(
                (score for agent, score in keyword_scores.items() if agent != current_agent),
                default=0,
            )

            if max_other_score < current_score + 3:  # Bias toward continuity
                return RoutingDecision(
                    primary_agent=current_agent,
                    confidence=0.8,
                    reason="Continuing conversation with current agent",
                )

        # 3. Keyword-based routing
        keyword_scores = self._score_keywords(message_lower)

        if keyword_scores:
            best_agent = max(keyword_scores.items(), key=lambda x: x[1])
            if best_agent[1] >= 2:  # At least 2 keyword matches for confidence
                # Check for supporting agents (secondary matches)
                supporting = [
                    agent
                    for agent, score in keyword_scores.items()
                    if agent != best_agent[0] and score >= 1
                ]
                return RoutingDecision(
                    primary_agent=best_agent[0],
                    confidence=min(0.9, 0.5 + best_agent[1] * 0.1),
                    reason=f"Keyword match (score: {best_agent[1]})",
                    supporting_agents=supporting[:2],  # Max 2 supporting agents
                )

        # 4. Default to Atlas (research) for general questions
        # In future, could use LLM classification for ambiguous cases
        return RoutingDecision(
            primary_agent="atlas",
            confidence=0.5,
            reason="Default to research agent for general inquiry",
        )

    def _score_keywords(self, message: str) -> dict[str, int]:
        """Score each agent based on keyword matches."""
        scores = {}

        for agent, patterns in self.AGENT_KEYWORDS.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, message, re.IGNORECASE))
                score += matches
            if score > 0:
                scores[agent] = score

        return scores

    async def route_with_llm(self, message: str, context: Optional[str] = None) -> RoutingDecision:
        """Use LLM to classify ambiguous messages.

        This is more expensive but more accurate for edge cases.
        """
        classification_prompt = f"""You are a routing assistant for a multi-agent system.
Classify the following message to determine which agent should handle it.

Available agents:
- atlas: Research agent for GenAI research, consulting approaches, case studies, thought leadership
- capital: Finance agent for ROI analysis, budget justification, cost-benefit analysis
- guardian: IT/Governance agent for security, compliance, infrastructure, policy
- counselor: Legal agent for contracts, IP, licensing, legal considerations
- oracle: Transcript analyzer for meeting transcripts, stakeholder sentiment
- sage: People/Change agent for change management, adoption, human factors, employee concerns
- strategist: Executive strategy for C-suite engagement, organizational politics, governance
- architect: Technical architecture for AI patterns, RAG, integration, build vs. buy
- operator: Operations for process optimization, automation, metrics, frontline workflows
- pioneer: Innovation/R&D for emerging tech, hype filtering, maturity assessment
- catalyst: Internal communications for AI messaging, employee engagement, announcements
- scholar: L&D for training programs, champion enablement, skill development
- echo: Brand voice for style analysis, voice profiling, AI emulation guidelines
- nexus: Systems thinking for interconnections, feedback loops, unintended consequences

Message: "{message}"

{f"Context: {context}" if context else ""}

Respond with ONLY the agent name and a brief reason.
Format: AGENT_NAME: reason"""

        try:
            response = self.anthropic.messages.create(
                model="claude-haiku-3-20240307",  # Fast and cheap for classification
                max_tokens=100,
                messages=[{"role": "user", "content": classification_prompt}],
            )

            result = response.content[0].text.strip()
            parts = result.split(":", 1)

            agent = parts[0].strip().lower()
            reason = parts[1].strip() if len(parts) > 1 else "LLM classification"

            if agent in self.AGENT_KEYWORDS:
                return RoutingDecision(
                    primary_agent=agent, confidence=0.85, reason=f"LLM classification: {reason}"
                )
        except Exception as e:
            logger.error(f"LLM routing failed: {e}")

        # Fallback to default
        return RoutingDecision(
            primary_agent="atlas", confidence=0.5, reason="Fallback to research agent"
        )

    def get_agent_for_handoff(self, from_agent: str, reason: str) -> Optional[str]:
        """Determine which agent to hand off to based on the handoff reason.

        This is called when an agent wants to defer to another agent.
        """
        reason_lower = reason.lower()

        # Map common handoff reasons to agents
        handoff_mappings = {
            # Stakeholder Perspective Agents
            "atlas": ["research", "study", "analysis", "trend", "benchmark", "case study"],
            "capital": ["cost", "budget", "roi", "financial", "money", "investment"],
            "guardian": ["security", "compliance", "governance", "it", "infrastructure"],
            "counselor": ["legal", "contract", "license", "ip", "liability"],
            "oracle": ["transcript", "meeting", "stakeholder", "sentiment"],
            "sage": ["people", "change", "adoption", "resistance", "employee", "human"],
            # Consulting/Implementation Agents
            "strategist": ["executive", "c-suite", "sponsor", "politics", "leadership"],
            "architect": ["architecture", "technical", "integration", "api", "rag"],
            "operator": ["process", "workflow", "automation", "operations", "metrics"],
            "pioneer": ["innovation", "emerging", "future", "experimental", "r&d"],
            # Internal Enablement Agents
            "catalyst": ["communications", "messaging", "announcement", "engagement"],
            "scholar": ["training", "learning", "enablement", "curriculum", "onboarding"],
            "echo": ["voice", "style", "tone", "brand", "writing"],
            # Systems Agent
            "nexus": ["systems", "interconnection", "feedback", "unintended", "holistic"],
        }

        for agent, keywords in handoff_mappings.items():
            if agent != from_agent:
                for keyword in keywords:
                    if keyword in reason_lower:
                        return agent

        return None
