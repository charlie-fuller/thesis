"""Thesis Multi-Agent System

Core agents for enterprise GenAI strategy implementation:

Meta-Agents:
- Facilitator: Meeting orchestration - welcomes, routes, balances, synthesizes discussions

Stakeholder Perspective Agents (Persona-Aligned):
- Coordinator: Central orchestrator - routes queries to specialists, synthesizes responses
- Atlas: Research agent - GenAI research, consulting approaches, case studies
- Capital: Finance agent - ROI analysis, budget justification
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
- Echo: Brand Voice Partner - voice analysis, style profiling, AI emulation guidelines

Systems Thinking Agent:
- Nexus: Systems thinking, interconnections, feedback loops, leverage points

Personal Development Agent:
- Compass: Career coach - win capture, check-in prep, strategic alignment, performance tracking
"""

from .agent_factory import create_coordinator, create_specialist
from .agent_router import AgentRouter, RoutingDecision
from .architect import ArchitectAgent
from .atlas import AtlasAgent
from .base_agent import AgentContext, AgentResponse, BaseAgent
from .capital import CapitalAgent
from .catalyst import CatalystAgent
from .compass import CompassAgent
from .coordinator import CoordinatorAgent
from .counselor import CounselorAgent
from .echo import EchoAgent
from .facilitator import FacilitatorAgent
from .guardian import GuardianAgent
from .nexus import NexusAgent
from .operator import OperatorAgent
from .oracle import OracleAgent
from .pioneer import PioneerAgent
from .sage import SageAgent
from .scholar import ScholarAgent
from .strategist import StrategistAgent

__all__ = [
    # Base classes
    "BaseAgent",
    "AgentContext",
    "AgentResponse",
    "AgentRouter",
    "RoutingDecision",
    # Meta-Agents
    "FacilitatorAgent",
    # Coordinator
    "CoordinatorAgent",
    # Stakeholder Perspective Agents
    "AtlasAgent",
    "CapitalAgent",
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
    "EchoAgent",
    # Systems Thinking Agent
    "NexusAgent",
    # Personal Development Agent
    "CompassAgent",
    # Factory functions
    "create_coordinator",
    "create_specialist",
]
