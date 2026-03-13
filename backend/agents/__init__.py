"""Thesis Multi-Agent System.

Core agents for enterprise GenAI strategy implementation.
Agents are lazy-loaded on first access to reduce startup time.

Meta-Agents:
- Facilitator: Meeting orchestration

Stakeholder Perspective Agents:
- Coordinator, Atlas, Capital, Guardian, Counselor, Oracle, Sage

Consulting/Implementation Agents:
- Strategist, Architect, Operator, Pioneer

Internal Enablement Agents:
- Catalyst, Scholar, Echo

Systems Thinking: Nexus
Personal Development: Compass
"""

# These are lightweight — import eagerly
from .agent_factory import create_coordinator, create_specialist
from .agent_router import AgentRouter, RoutingDecision
from .base_agent import AgentContext, AgentResponse, BaseAgent


def __getattr__(name):
    """Lazy-load agent classes on first access."""
    _lazy_imports = {
        "ArchitectAgent": ".architect",
        "AtlasAgent": ".atlas",
        "CapitalAgent": ".capital",
        "CatalystAgent": ".catalyst",
        "CompassAgent": ".compass",
        "CoordinatorAgent": ".coordinator",
        "CounselorAgent": ".counselor",
        "EchoAgent": ".echo",
        "FacilitatorAgent": ".facilitator",
        "GuardianAgent": ".guardian",
        "NexusAgent": ".nexus",
        "OperatorAgent": ".operator",
        "OracleAgent": ".oracle",
        "PioneerAgent": ".pioneer",
        "SageAgent": ".sage",
        "ScholarAgent": ".scholar",
        "StrategistAgent": ".strategist",
    }

    if name in _lazy_imports:
        import importlib
        module = importlib.import_module(_lazy_imports[name], package=__name__)
        cls = getattr(module, name)
        globals()[name] = cls  # Cache for subsequent access
        return cls

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Base classes (eagerly loaded)
    "BaseAgent",
    "AgentContext",
    "AgentResponse",
    "AgentRouter",
    "RoutingDecision",
    # Factory functions (eagerly loaded)
    "create_coordinator",
    "create_specialist",
    # Agent classes (lazy-loaded on access)
    "FacilitatorAgent",
    "CoordinatorAgent",
    "AtlasAgent",
    "CapitalAgent",
    "GuardianAgent",
    "CounselorAgent",
    "OracleAgent",
    "SageAgent",
    "StrategistAgent",
    "ArchitectAgent",
    "OperatorAgent",
    "PioneerAgent",
    "CatalystAgent",
    "ScholarAgent",
    "EchoAgent",
    "NexusAgent",
    "CompassAgent",
]
