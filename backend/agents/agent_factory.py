"""Agent Factory - Creates and configures agents for Thesis.

Provides factory functions to create fully configured agents
with proper initialization and specialist registration.

All agent imports are deferred to function call time to avoid
loading 22 agent modules at startup.
"""

import logging
from typing import Optional

import anthropic

from supabase import Client

logger = logging.getLogger(__name__)


def _get_agent_class(name: str):
    """Lazy-import and return an agent class by name.

    This avoids importing all 22 agent modules at module load time,
    saving ~1-2s on cold start.
    """
    _registry = {
        # Stakeholder Perspective Agents
        "atlas": (".atlas", "AtlasAgent"),
        "capital": (".capital", "CapitalAgent"),
        "guardian": (".guardian", "GuardianAgent"),
        "counselor": (".counselor", "CounselorAgent"),
        "oracle": (".oracle", "OracleAgent"),
        "sage": (".sage", "SageAgent"),
        # Consulting/Implementation Agents
        "strategist": (".strategist", "StrategistAgent"),
        "architect": (".architect", "ArchitectAgent"),
        "operator": (".operator", "OperatorAgent"),
        "pioneer": (".pioneer", "PioneerAgent"),
        # Internal Enablement Agents
        "catalyst": (".catalyst", "CatalystAgent"),
        "scholar": (".scholar", "ScholarAgent"),
        "glean_evaluator": (".glean_evaluator", "GleanEvaluatorAgent"),
        "manual": (".manual", "ManualAgent"),
        # Systems Thinking Agent
        "nexus": (".nexus", "NexusAgent"),
        # Brand & Voice Agent
        "echo": (".echo", "EchoAgent"),
        # Personal Development Agent
        "compass": (".compass", "CompassAgent"),
        # Personal Productivity Agent
        "taskmaster": (".taskmaster", "TaskmasterAgent"),
        # Task Automation Agent
        "kraken": (".kraken", "KrakenAgent"),
        # Meta-Agents
        "facilitator": (".facilitator", "FacilitatorAgent"),
        "reporter": (".reporter", "ReporterAgent"),
        # Context-Specific Agents
        "project_agent": (".project_agent", "ProjectAgent"),
        "initiative_agent": (".initiative_agent", "InitiativeAgent"),
    }

    key = name.lower()
    if key not in _registry:
        return None

    module_path, class_name = _registry[key]
    import importlib
    module = importlib.import_module(module_path, package="agents")
    return getattr(module, class_name)


async def create_coordinator(
    supabase: Client, anthropic_client: anthropic.Anthropic, register_specialists: bool = True
):
    """Create and configure a Coordinator agent with all specialists.

    Args:
        supabase: Supabase client for database operations
        anthropic_client: Anthropic client for Claude API calls
        register_specialists: Whether to register specialist agents

    Returns:
        Fully configured CoordinatorAgent ready for use
    """
    CoordinatorAgent = _get_agent_class("coordinator")

    # Create the coordinator
    coordinator = CoordinatorAgent(supabase=supabase, anthropic_client=anthropic_client)

    # Initialize coordinator from database
    await coordinator.initialize()

    if register_specialists:
        # Only import and register agents as needed
        specialist_names = [
            "atlas", "capital", "guardian", "counselor", "oracle", "sage",
            "strategist", "architect", "operator", "pioneer",
            "catalyst", "scholar", "glean_evaluator", "manual",
            "nexus", "echo", "compass", "taskmaster", "kraken",
            "project_agent", "initiative_agent",
        ]

        for name in specialist_names:
            try:
                agent_class = _get_agent_class(name)
                if agent_class is None:
                    logger.error(f"Unknown specialist: {name}")
                    continue
                agent = agent_class(supabase, anthropic_client)
                await agent.initialize()
                coordinator.register_specialist(name, agent)
                logger.info(f"Registered specialist: {name}")
            except Exception as e:
                logger.error(f"Failed to initialize specialist {name}: {e}")

    return coordinator


async def create_specialist(name: str, supabase: Client, anthropic_client: anthropic.Anthropic) -> Optional[object]:
    """Create a single specialist agent by name.

    Args:
        name: Name of the specialist
        supabase: Supabase client
        anthropic_client: Anthropic client

    Returns:
        The specialist agent, or None if name is invalid
    """
    agent_class = _get_agent_class(name)
    if not agent_class:
        logger.error(f"Unknown specialist: {name}")
        return None

    agent = agent_class(supabase, anthropic_client)
    await agent.initialize()
    return agent
