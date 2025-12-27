"""
Thesis Multi-Agent System

Core agents for enterprise GenAI strategy implementation:
- Coordinator: Central orchestrator - routes queries to specialists, synthesizes responses
- Atlas: Research agent - GenAI research, consulting approaches, case studies
- Fortuna: Finance agent - ROI analysis, budget justification
- Guardian: IT/Governance agent - security, infrastructure, governance
- Counselor: Legal agent - contracts, compliance, legal considerations
- Oracle: Transcript analyzer - stakeholder sentiment extraction
"""

from .base_agent import BaseAgent, AgentContext, AgentResponse
from .agent_router import AgentRouter, RoutingDecision
from .coordinator import CoordinatorAgent
from .atlas import AtlasAgent
from .fortuna import FortunaAgent
from .guardian import GuardianAgent
from .counselor import CounselorAgent
from .oracle import OracleAgent
from .agent_factory import create_coordinator, create_specialist

__all__ = [
    "BaseAgent",
    "AgentContext",
    "AgentResponse",
    "AgentRouter",
    "RoutingDecision",
    "CoordinatorAgent",
    "AtlasAgent",
    "FortunaAgent",
    "GuardianAgent",
    "CounselorAgent",
    "OracleAgent",
    "create_coordinator",
    "create_specialist",
]
