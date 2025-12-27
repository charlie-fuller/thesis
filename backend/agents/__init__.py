"""
Thesis Multi-Agent System

Core agents for enterprise GenAI strategy implementation:

Stakeholder Perspective Agents (Persona-Aligned):
- Coordinator: Central orchestrator - routes queries to specialists, synthesizes responses
- Atlas: Research agent - GenAI research, consulting approaches, case studies
- Fortuna: Finance agent - ROI analysis, budget justification
- Guardian: IT/Governance agent - security, infrastructure, governance
- Counselor: Legal agent - contracts, compliance, legal considerations
- Oracle: Transcript analyzer - stakeholder sentiment extraction
- Sage: People agent - human-centered change, community building, human flourishing

Consulting/Implementation Agents:
- Strategist: Executive Strategy Partner - C-suite engagement, organizational politics
- Architect: Technical Architecture Partner - enterprise AI patterns, integration
- Operator: Business Operations Partner - process optimization, metrics
- Pioneer: Innovation Partner - emerging technology, hype filtering

Internal Enablement Agents:
- Catalyst: Internal Communications Partner - AI messaging, employee engagement
- Scholar: L&D Partner - training programs, champion enablement

Systems Thinking Agent:
- Nexus: Systems thinking, interconnections, feedback loops, leverage points
"""

from .base_agent import BaseAgent, AgentContext, AgentResponse
from .agent_router import AgentRouter, RoutingDecision
from .coordinator import CoordinatorAgent
from .atlas import AtlasAgent
from .fortuna import FortunaAgent
from .guardian import GuardianAgent
from .counselor import CounselorAgent
from .oracle import OracleAgent
from .sage import SageAgent
from .strategist import StrategistAgent
from .architect import ArchitectAgent
from .operator import OperatorAgent
from .pioneer import PioneerAgent
from .catalyst import CatalystAgent
from .scholar import ScholarAgent
from .nexus import NexusAgent
from .agent_factory import create_coordinator, create_specialist

__all__ = [
    # Base classes
    "BaseAgent",
    "AgentContext",
    "AgentResponse",
    "AgentRouter",
    "RoutingDecision",
    # Coordinator
    "CoordinatorAgent",
    # Stakeholder Perspective Agents
    "AtlasAgent",
    "FortunaAgent",
    "GuardianAgent",
    "CounselorAgent",
    "OracleAgent",
    "SageAgent",
    # Consulting/Implementation Agents
    "StrategistAgent",
    "ArchitectAgent",
    "OperatorAgent",
    "PioneerAgent",
    # Internal Enablement Agents
    "CatalystAgent",
    "ScholarAgent",
    # Systems Thinking Agent
    "NexusAgent",
    # Factory functions
    "create_coordinator",
    "create_specialist",
]
