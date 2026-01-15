"""
Agent Factory - Creates and configures agents for Thesis

Provides factory functions to create fully configured agents
with proper initialization and specialist registration.
"""

import logging
from typing import Optional

import anthropic
from supabase import Client

from .coordinator import CoordinatorAgent
# Stakeholder Perspective Agents
from .atlas import AtlasAgent
from .capital import CapitalAgent
from .guardian import GuardianAgent
from .counselor import CounselorAgent
from .oracle import OracleAgent
from .sage import SageAgent
# Consulting/Implementation Agents
from .strategist import StrategistAgent
from .architect import ArchitectAgent
from .operator import OperatorAgent
from .pioneer import PioneerAgent
# Internal Enablement Agents
from .catalyst import CatalystAgent
from .scholar import ScholarAgent
from .glean_evaluator import GleanEvaluatorAgent
# Systems Thinking Agent
from .nexus import NexusAgent
# Brand & Voice Agent
from .echo import EchoAgent
# Personal Development Agent
from .compass import CompassAgent
# Meta-Agents (always present in meetings)
from .facilitator import FacilitatorAgent
from .reporter import ReporterAgent

logger = logging.getLogger(__name__)


async def create_coordinator(
    supabase: Client,
    anthropic_client: anthropic.Anthropic,
    register_specialists: bool = True
) -> CoordinatorAgent:
    """
    Create and configure a Coordinator agent with all specialists.

    Args:
        supabase: Supabase client for database operations
        anthropic_client: Anthropic client for Claude API calls
        register_specialists: Whether to register specialist agents

    Returns:
        Fully configured CoordinatorAgent ready for use
    """
    # Create the coordinator
    coordinator = CoordinatorAgent(
        supabase=supabase,
        anthropic_client=anthropic_client
    )

    # Initialize coordinator from database
    await coordinator.initialize()

    if register_specialists:
        # Create and register all specialist agents
        specialists = {
            # Stakeholder Perspective Agents
            "atlas": AtlasAgent(supabase, anthropic_client),
            "capital": CapitalAgent(supabase, anthropic_client),
            "guardian": GuardianAgent(supabase, anthropic_client),
            "counselor": CounselorAgent(supabase, anthropic_client),
            "oracle": OracleAgent(supabase, anthropic_client),
            "sage": SageAgent(supabase, anthropic_client),
            # Consulting/Implementation Agents
            "strategist": StrategistAgent(supabase, anthropic_client),
            "architect": ArchitectAgent(supabase, anthropic_client),
            "operator": OperatorAgent(supabase, anthropic_client),
            "pioneer": PioneerAgent(supabase, anthropic_client),
            # Internal Enablement Agents
            "catalyst": CatalystAgent(supabase, anthropic_client),
            "scholar": ScholarAgent(supabase, anthropic_client),
            "glean_evaluator": GleanEvaluatorAgent(supabase, anthropic_client),
            # Systems Thinking Agent
            "nexus": NexusAgent(supabase, anthropic_client),
            # Brand & Voice Agent
            "echo": EchoAgent(supabase, anthropic_client),
            # Personal Development Agent
            "compass": CompassAgent(supabase, anthropic_client),
        }

        # Initialize all specialists
        for name, agent in specialists.items():
            try:
                await agent.initialize()
                coordinator.register_specialist(name, agent)
                logger.info(f"Registered specialist: {name}")
            except Exception as e:
                logger.error(f"Failed to initialize specialist {name}: {e}")

    return coordinator


async def create_specialist(
    name: str,
    supabase: Client,
    anthropic_client: anthropic.Anthropic
) -> Optional[object]:
    """
    Create a single specialist agent by name.

    Args:
        name: Name of the specialist (all 14 agents supported)
        supabase: Supabase client
        anthropic_client: Anthropic client

    Returns:
        The specialist agent, or None if name is invalid
    """
    agent_classes = {
        # Stakeholder Perspective Agents
        "atlas": AtlasAgent,
        "capital": CapitalAgent,
        "guardian": GuardianAgent,
        "counselor": CounselorAgent,
        "oracle": OracleAgent,
        "sage": SageAgent,
        # Consulting/Implementation Agents
        "strategist": StrategistAgent,
        "architect": ArchitectAgent,
        "operator": OperatorAgent,
        "pioneer": PioneerAgent,
        # Internal Enablement Agents
        "catalyst": CatalystAgent,
        "scholar": ScholarAgent,
        "glean_evaluator": GleanEvaluatorAgent,
        # Systems Thinking Agent
        "nexus": NexusAgent,
        # Brand & Voice Agent
        "echo": EchoAgent,
        # Personal Development Agent
        "compass": CompassAgent,
        # Meta-Agents
        "facilitator": FacilitatorAgent,
        "reporter": ReporterAgent,
    }

    agent_class = agent_classes.get(name.lower())
    if not agent_class:
        logger.error(f"Unknown specialist: {name}")
        return None

    agent = agent_class(supabase, anthropic_client)
    await agent.initialize()
    return agent
