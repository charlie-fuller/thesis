"""
Thesis Multi-Agent System

Core agents for enterprise GenAI strategy implementation:
- Atlas: Research agent - GenAI research, consulting approaches, case studies
- Fortuna: Finance agent - ROI analysis, budget justification
- Guardian: IT/Governance agent - security, infrastructure, governance
- Counselor: Legal agent - contracts, compliance, legal considerations
- Oracle: Transcript analyzer - stakeholder sentiment extraction
"""

from .base_agent import BaseAgent, AgentContext, AgentResponse
from .agent_router import AgentRouter, RoutingDecision
from .atlas import AtlasAgent
from .oracle import OracleAgent

__all__ = [
    "BaseAgent",
    "AgentContext",
    "AgentResponse",
    "AgentRouter",
    "RoutingDecision",
    "AtlasAgent",
    "OracleAgent",
]
