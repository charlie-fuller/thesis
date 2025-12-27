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
from .atlas import AtlasAgent
from .fortuna import FortunaAgent
from .guardian import GuardianAgent
from .counselor import CounselorAgent
from .oracle import OracleAgent

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
        # Create and register specialist agents
        specialists = {
            "atlas": AtlasAgent(supabase, anthropic_client),
            "fortuna": FortunaAgent(supabase, anthropic_client),
            "guardian": GuardianAgent(supabase, anthropic_client),
            "counselor": CounselorAgent(supabase, anthropic_client),
            "oracle": OracleAgent(supabase, anthropic_client),
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
        name: Name of the specialist (atlas, fortuna, guardian, counselor, oracle)
        supabase: Supabase client
        anthropic_client: Anthropic client

    Returns:
        The specialist agent, or None if name is invalid
    """
    agent_classes = {
        "atlas": AtlasAgent,
        "fortuna": FortunaAgent,
        "guardian": GuardianAgent,
        "counselor": CounselorAgent,
        "oracle": OracleAgent,
    }

    agent_class = agent_classes.get(name.lower())
    if not agent_class:
        logger.error(f"Unknown specialist: {name}")
        return None

    agent = agent_class(supabase, anthropic_client)
    await agent.initialize()
    return agent
