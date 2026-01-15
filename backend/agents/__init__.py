"""
Thesis Multi-Agent System

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

from .base_agent import BaseAgent, AgentContext, AgentResponse
from .agent_router import AgentRouter, RoutingDecision
from .coordinator import CoordinatorAgent
from .facilitator import FacilitatorAgent
from .atlas import AtlasAgent
from .capital import CapitalAgent
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
from .echo import EchoAgent
from .nexus import NexusAgent
from .compass import CompassAgent
from .agent_factory import create_coordinator, create_specialist

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
