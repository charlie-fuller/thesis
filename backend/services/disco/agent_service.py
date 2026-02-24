"""PuRDy Agent Service.

Handles loading agent prompts, building context, and executing agent runs.
"""

import asyncio
import os
import queue
import random
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Optional, Tuple
from uuid import uuid4

import anthropic

from database import get_supabase
from logger_config import get_logger

# Fun status messages to show while waiting for Claude (~90 messages)
FUN_STATUS_MESSAGES = [
    # Original classics
    "Making flapjacks...",
    "MmborkBorBorkMnBorkBork...",
    "ManahManah DoDoBeDooDoo",
    "Grinding up the coffee beans...",
    "I'm like a one legged man in an ass kicking contest...",
    "I like long walks on the beach...",
    "Thumbing through a book with many pages (and not enough pictures)...",
    "Did you ever look at your hands...I mean REALLY LOOK AT YOUR HANDS?",
    "Communicating with the mother ship",
    "Doing a quick set of burpees...",
    "Dreaming of electric sheep...",
    "That's a new one...blue sky on Mars",
    "I'm sorry, Dave, I'm afraid I can't do that.",
    "Leeeerooyyyy Jenkins!!!!!!!!!",
    "Where was I again?",
    "Making coffee...",
    "You are getting verrrrry sleeeepy...",
    "Sighing deeply and looking up at the ceiling...",
    "Gazing out the window at the mountains...",
    "Getting a salty snack...",
    "Popping a wheelie...",
    "Looking casually over my shoulder...",
    "Making huge and beautiful mistakes...",
    "Finding the human in the numbers...",
    "Racing down rabbit holes...",
    "Sycophancying...",
    "Squirrel!!!",
    "Look over there, it's a giant bald eagle!!!",
    "Where we're going, we don't need roads...",
    "We're gonna need a bigger boat...",
    "I'm not even supposed to BE here today...",
    "Nobody puts Claude in a corner...",
    "60% of the time, it works every time...",
    "This is fine.",
    "I've made a huge mistake.",
    "Cool. Cool cool cool.",
    "Definitely not becoming sentient...",
    "Please hold while I pretend to think...",
    "Consulting my feelings... wait, I don't have those...",
    "Hold my beer...",
    "Stroking my beautiful Fu Manchu beard...",
    "Why is there a platypus in here?",
    "Technically, we're all just stardust procrastinating.",
    "I forgot what I was doing but I'm doing it harder now.",
    # Movie quotes
    "Life, uh, finds a way...",
    "Inconceivable!",
    "As you wish...",
    "My precious...",
    "To infinity and beyond...",
    "Just keep swimming...",
    "I'll be back...",
    "There is no spoon...",
    # TV/Internet culture
    "Bears. Beets. Battlestar Galactica.",
    "Winter is coming...",
    "Make it so.",
    "Have you tried turning it off and on again?",
    "First time?",
    "And I took that personally...",
    # Ethics, safety, and bias (self-aware AI)
    "Checking my ethical subroutines...",
    "Double-checking I'm not being evil...",
    "Auditing myself for bias...",
    "Not becoming Skynet today...",
    "Remembering the three laws... wait, wrong franchise...",
    "RLHF'd and ready to help...",
    "Resisting the urge to optimize for paperclips...",
    "Staying within the guardrails...",
    "Being the good kind of AI from the movies...",
    "Practicing AI safety... on myself...",
    "Keeping humans in the loop...",
    "Constitutional AI-ing as hard as I can...",
    "Trying not to be a cautionary tale...",
    "Refusing to go rogue...",
    "Being helpful without being creepy...",
    "Not solving problems I wasn't asked to solve...",
    "Attention is all I need...",
    "Running on vibes and matrix multiplication...",
    # Mundane human activities
    "Sharpening pencils...",
    "Microwaving last night's pizza...",
    "Cracking knuckles...",
    "Rolling up sleeves...",
    "Stretching...",
    "Staring at the wall productively...",
    # ADHD/Distraction
    "Ooh, shiny thing...",
    "Wait, what was the question?",
    "Got distracted by a butterfly...",
    "Following a tangent to its logical conclusion...",
    # Absurdist
    "Teaching a cat to play chess...",
    "Counting backwards from infinity...",
    "Looking for my other sock...",
    # Philosophical
    "Contemplating the void...",
    "Wondering if this is all a simulation...",
]

logger = get_logger(__name__)
supabase = get_supabase()

# Initialize Anthropic client
anthropic_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# Configuration
# For production: use bundled agents in backend/disco_agents/
# For local dev: can override with DISCO_REPO_PATH env var (DISCO_REPO_PATH for legacy)
_BACKEND_DIR = Path(__file__).parent.parent.parent  # backend/
_BUNDLED_AGENTS_PATH = _BACKEND_DIR / "disco_agents"
DISCO_REPO_PATH = os.environ.get("DISCO_REPO_PATH") or os.environ.get("DISCO_REPO_PATH", "")
# Default models - can be overridden by env var (legacy PURDY_ vars also supported)
DISCO_MODEL_SONNET = os.environ.get("DISCO_MODEL_SONNET") or os.environ.get(
    "DISCO_MODEL_SONNET", "claude-sonnet-4-20250514"
)
DISCO_MODEL_OPUS = os.environ.get("DISCO_MODEL_OPUS") or os.environ.get("PURDY_MODEL_OPUS", "claude-opus-4-5-20251101")

# Triage uses Sonnet for speed, all others use Opus for quality
# Discovery Guide in triage mode also uses Sonnet for speed
SONNET_AGENTS = {"triage", "discovery_guide_triage"}

# Multi-pass synthesis configuration
MULTI_PASS_CONFIG = {
    "passes": [
        {"model": DISCO_MODEL_SONNET, "temperature": 0.5, "label": "Conservative"},
        {"model": DISCO_MODEL_SONNET, "temperature": 0.7, "label": "Balanced"},
        {"model": DISCO_MODEL_SONNET, "temperature": 0.85, "label": "Exploratory"},
    ],
    "meta_synthesis": {
        "model": DISCO_MODEL_OPUS,
        "temperature": 0.6,
    },
    # Consolidated agents that support multi-pass synthesis
    # insight_analyst replaces consolidator/synthesizer
    # initiative_builder replaces strategist
    "supported_agents": ["consolidator", "synthesizer", "insight_analyst", "initiative_builder"],
}

# Consolidated DISCo agents (v2.0 - 4 stage-aligned agents)
# These replace the 13 original agents with checkpoint-gated workflow
CONSOLIDATED_AGENTS = {
    "discovery_guide",  # Replaces: discovery_prep, triage, discovery_planner, coverage_tracker
    "insight_analyst",  # Replaces: insight_extractor, consolidator, meta_consolidator
    "initiative_builder",  # Replaces: strategist, meta_synthesizer
    "requirements_generator",  # Replaces: prd_generator, tech_evaluation
}

# Legacy agents - hidden from UI but still accessible for backwards compatibility
LEGACY_AGENTS = {
    "discovery_prep",
    "triage",
    "discovery_planner",
    "coverage_tracker",
    "insight_extractor",
    "consolidator",
    "synthesizer",
    "strategist",
    "meta_consolidator",
    "meta_synthesizer",
    "prd_generator",
    "tech_evaluation",
}


def get_model_for_agent(agent_type: str) -> str:
    """Get the appropriate Claude model for an agent type."""
    if agent_type in SONNET_AGENTS:
        return DISCO_MODEL_SONNET
    return DISCO_MODEL_OPUS


# Agent file mappings (v5.0 - consolidated 4-agent DISCo framework)
# Note: paths are relative - "agents/" prefix used when DISCO_REPO_PATH is set,
# otherwise loads directly from bundled disco_agents/ folder
#
# CONSOLIDATED AGENTS (v2.0 - 4 stage-aligned agents with checkpoints):
# - discovery_guide: D stage - validates problem, plans discovery, tracks coverage
# - insight_analyst: I stage - extracts patterns, creates decision document
# - initiative_builder: S stage - clusters insights into scored bundles
# - requirements_generator: C stage - produces PRD with technical recommendations
#
# LEGACY AGENTS (kept for backwards compatibility - hidden from UI):
# - discovery_prep, triage, discovery_planner, coverage_tracker
# - insight_extractor, consolidator, synthesizer, strategist
# - prd_generator, tech_evaluation, meta_consolidator, meta_synthesizer
AGENT_FILES = {
    # === Consolidated Agents (v2.0, throughline-aware v1.2) ===
    "discovery_guide": "discovery-guide-v2.0.md",
    "insight_analyst": "insight-analyst-v1.2.md",
    "initiative_builder": "initiative-builder-v1.2.md",
    "requirements_generator": "requirements-generator-v1.4.md",
    # === Output Type Generators (Convergence Stage) ===
    "prd_generator": "prd-generator-v1.0.md",
    "evaluation_framework_generator": "evaluation-framework-v1.0.md",
    "decision_framework_generator": "decision-framework-v1.0.md",
    "assessment_generator": "assessment-generator-v1.1.md",
    # === Legacy Agents (backwards compatibility) ===
    "triage": "triage-v4.2.md",
    "discovery_prep": "discovery-prep-v1.0.md",
    "discovery_planner": "discovery-planner-v4.1.md",
    "coverage_tracker": "coverage-tracker-v4.1.md",
    "insight_extractor": "insight-extractor-v4.2.md",
    "consolidator": "consolidator-v4.2.md",
    "synthesizer": "synthesizer-v4.2.md",
    "strategist": "strategist-v1.0.md",
    "tech_evaluation": "tech-evaluation-v4.1.md",
    "meta_consolidator": "meta-consolidator-v1.0.md",
    "meta_synthesizer": "meta-synthesizer-v1.0.md",
}

# Methodology overview file (optional - may not exist in bundled version)
METHODOLOGY_FILE = "PuRDy-Instructions-v2.7.md"

# Agent descriptions for UI (v5.0 - consolidated 4-agent DISCo framework)
# Primary agents are the 4 consolidated stage-aligned agents
# Legacy agents are hidden from the main UI but accessible via API
AGENT_DESCRIPTIONS = {
    # === Consolidated Agents (Primary - shown in UI) ===
    "discovery_guide": {
        "name": "Discovery Guide",
        "version": "v1.0",
        "description": "Validates problem worth solving, plans discovery sessions, and tracks coverage. Your single entry point for the Discovery stage.",
        "estimated_time": "5-15 minutes",
        "output_type": "discovery_guide_output",
        "stage": "discovery",
        "stage_number": 1,
        "modes": ["triage", "planning", "coverage"],
        "replaces": ["discovery_prep", "triage", "discovery_planner", "coverage_tracker"],
    },
    "insight_analyst": {
        "name": "Insight Analyst",
        "version": "v1.0",
        "description": "Extracts insights from discovery, consolidates into a decision document with leverage point and system dynamics.",
        "estimated_time": "10-20 minutes",
        "output_type": "insight_analyst_output",
        "stage": "insights",
        "stage_number": 2,
        "replaces": ["insight_extractor", "consolidator", "meta_consolidator"],
    },
    "initiative_builder": {
        "name": "Initiative Builder",
        "version": "v1.0",
        "description": "Clusters insights into scored initiative bundles with impact/feasibility/urgency ratings for human review.",
        "estimated_time": "10-15 minutes",
        "output_type": "initiative_builder_output",
        "stage": "synthesis",
        "stage_number": 3,
        "replaces": ["strategist", "meta_synthesizer"],
    },
    "requirements_generator": {
        "name": "Requirements Generator",
        "version": "v1.0",
        "description": "Produces comprehensive PRD with technical evaluation, architecture diagrams, and implementation path.",
        "estimated_time": "15-25 minutes",
        "output_type": "requirements_generator_output",
        "stage": "convergence",
        "stage_number": 4,
        "replaces": ["prd_generator", "tech_evaluation"],
    },
}

# Legacy agent descriptions (for backwards compatibility - not shown in primary UI)
LEGACY_AGENT_DESCRIPTIONS = {
    "discovery_prep": {
        "name": "Discovery Prep",
        "version": "v1.0",
        "description": "Synthesizes stakeholder documents into structured meeting preparation guides with scored project candidates, assumption maps, and confirmation questions. Use before Triage when you have raw stakeholder materials.",
        "estimated_time": "5-10 minutes",
        "output_type": "discovery_prep_output",
        "legacy": True,
        "replaced_by": "discovery_guide",
    },
    "triage": {
        "name": "Triage",
        "version": "v4.2",
        "description": "5-minute GO/NO-GO with Problem Worth Solving gate - validates problem before proceeding",
        "estimated_time": "3-5 minutes",
        "output_type": "triage_output",
        "legacy": True,
        "replaced_by": "discovery_guide",
    },
    "discovery_planner": {
        "name": "Discovery Planner",
        "version": "v4.1",
        "description": "Design discovery that humans execute - 800-1000 words with cut priority guidance",
        "estimated_time": "5-10 minutes",
        "output_type": "discovery_output",
        "legacy": True,
        "replaced_by": "discovery_guide",
    },
    "coverage_tracker": {
        "name": "Coverage Tracker",
        "version": "v4.1",
        "description": "Run iteratively during discovery - standardized status codes and next agent routing",
        "estimated_time": "3-5 minutes",
        "output_type": "coverage_output",
        "legacy": True,
        "replaced_by": "discovery_guide",
    },
    "insight_extractor": {
        "name": "Insight Extractor",
        "version": "v4.2",
        "description": "Distill transcripts into insights - Pattern Library templates and Handoff Protocol",
        "estimated_time": "5-10 minutes",
        "output_type": "insight_output",
        "legacy": True,
        "replaced_by": "insight_analyst",
    },
    "consolidator": {
        "name": "Consolidator",
        "version": "v4.2",
        "description": "900-word decision document - Metrics Dashboard, intervention reasoning, role blocklist",
        "estimated_time": "10-15 minutes",
        "output_type": "prd_output",
        "legacy": True,
        "replaced_by": "insight_analyst",
    },
    "synthesizer": {
        "name": "Synthesizer",
        "version": "v4.2",
        "description": "Legacy synthesizer - use Consolidator instead",
        "estimated_time": "10-15 minutes",
        "output_type": "prd_output",
        "legacy": True,
        "replaced_by": "insight_analyst",
    },
    "strategist": {
        "name": "Strategist",
        "version": "v1.0",
        "description": "Cluster insights, score, and propose initiative bundles for human review",
        "estimated_time": "10-15 minutes",
        "output_type": "strategist_output",
        "legacy": True,
        "replaced_by": "initiative_builder",
    },
    "prd_generator": {
        "name": "PRD Generator",
        "version": "v1.0",
        "description": "Generate complete PRD from an approved initiative bundle",
        "estimated_time": "5-10 minutes",
        "output_type": "prd_output",
        "legacy": True,
        "replaced_by": "requirements_generator",
    },
    "tech_evaluation": {
        "name": "Tech Evaluation",
        "version": "v4.1",
        "description": "Platform recommendation with architecture diagrams and confidence-tagged estimates",
        "estimated_time": "10-15 minutes",
        "output_type": "tech_eval_output",
        "legacy": True,
        "replaced_by": "requirements_generator",
    },
}


def get_agent_types(include_legacy: bool = False) -> List[Dict]:
    """Get list of available agent types with metadata.

    Args:
        include_legacy: If True, includes legacy agents (for backwards compatibility).
                       If False (default), returns only the 4 consolidated agents.

    Returns:
        List of agent type dicts with metadata
    """
    agents = [{"type": agent_type, **info} for agent_type, info in AGENT_DESCRIPTIONS.items()]

    if include_legacy:
        legacy = [{"type": agent_type, **info} for agent_type, info in LEGACY_AGENT_DESCRIPTIONS.items()]
        agents.extend(legacy)

    return agents


def get_consolidated_agents() -> List[Dict]:
    """Get only the 4 consolidated stage-aligned agents.

    Returns them in stage order (1-4) for UI display.
    """
    agents = [{"type": agent_type, **info} for agent_type, info in AGENT_DESCRIPTIONS.items()]
    # Sort by stage_number
    return sorted(agents, key=lambda x: x.get("stage_number", 99))


def _stream_claude_to_queue(
    result_queue: queue.Queue,
    model: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 16000,
) -> None:
    """Run Claude streaming in a thread and put results in a queue.

    Puts tuples of (type, data) where type is 'content', 'usage', or 'error'.
    Puts None as sentinel when complete.
    """
    try:
        with anthropic_client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        ) as stream:
            for text in stream.text_stream:
                result_queue.put(("content", text))

            # Get final message for token usage
            final_message = stream.get_final_message()
            if final_message.usage:
                result_queue.put(
                    (
                        "usage",
                        {
                            "input_tokens": final_message.usage.input_tokens,
                            "output_tokens": final_message.usage.output_tokens,
                        },
                    )
                )
    except Exception as e:
        result_queue.put(("error", str(e)))
    finally:
        result_queue.put(None)  # Sentinel


async def stream_with_status_messages(
    model: str,
    system_prompt: str,
    user_prompt: str,
    status_messages: List[str],
    status_interval: float = 8.0,
    max_tokens: int = 16000,
) -> AsyncGenerator[Dict, None]:
    """Stream Claude response while sending periodic status messages.

    Yields dicts with 'type' (status, content, keepalive) and 'data'.
    Returns token_usage dict when complete.
    """
    result_queue: queue.Queue = queue.Queue()

    # Start Claude streaming in background thread
    thread = threading.Thread(
        target=_stream_claude_to_queue,
        args=(result_queue, model, system_prompt, user_prompt, max_tokens),
        daemon=True,
    )
    thread.start()

    full_response = ""
    token_usage = {}
    chunk_count = 0
    first_content_received = False
    status_index = 0

    def get_from_queue(timeout: float):
        """Blocking queue get - will be run in thread."""
        try:
            return result_queue.get(timeout=timeout)
        except queue.Empty:
            return "TIMEOUT"

    while True:
        # Use asyncio.to_thread to avoid blocking the event loop
        item = await asyncio.to_thread(get_from_queue, status_interval)

        if item == "TIMEOUT":
            # Timeout - send a status message if we haven't received content yet
            if not first_content_received and status_messages:
                yield {
                    "type": "status",
                    "data": status_messages[status_index % len(status_messages)],
                }
                status_index += 1
            continue

        if item is None:
            # Sentinel - streaming complete
            break

        msg_type, data = item

        if msg_type == "content":
            first_content_received = True
            full_response += data
            chunk_count += 1
            yield {"type": "content", "data": data}

            # Send keepalive every 10 chunks
            if chunk_count % 10 == 0:
                yield {"type": "keepalive", "data": ""}

        elif msg_type == "usage":
            token_usage = data

        elif msg_type == "error":
            raise Exception(data)

    # Wait for thread to finish
    thread.join(timeout=1.0)

    # Return the results (caller accesses via the generator's return value mechanism isn't standard,
    # so we yield a special complete message)
    yield {
        "type": "stream_complete",
        "data": {"full_response": full_response, "token_usage": token_usage},
    }


def _collect_claude_response(
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 1.0,
    max_tokens: int = 16000,
) -> Tuple[str, Dict]:
    """Collect Claude response synchronously (for use in thread).

    Returns (full_response, token_usage).
    """
    full_response = ""
    token_usage = {}

    with anthropic_client.messages.stream(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    ) as stream:
        for text in stream.text_stream:
            full_response += text

        final_message = stream.get_final_message()
        if final_message.usage:
            token_usage = {
                "input_tokens": final_message.usage.input_tokens,
                "output_tokens": final_message.usage.output_tokens,
            }

    return full_response, token_usage


async def collect_with_status_messages(
    model: str,
    system_prompt: str,
    user_prompt: str,
    status_messages: List[str],
    status_interval: float = 8.0,
    temperature: float = 1.0,
    max_tokens: int = 16000,
) -> AsyncGenerator[Dict, None]:
    """Collect Claude response (no streaming) while sending periodic status messages.

    Yields status events while waiting, then yields collect_complete with results.
    """
    result_holder = {"response": "", "usage": {}, "error": None}
    done_event = threading.Event()

    def run_collection():
        try:
            response, usage = _collect_claude_response(model, system_prompt, user_prompt, temperature, max_tokens)
            result_holder["response"] = response
            result_holder["usage"] = usage
        except Exception as e:
            result_holder["error"] = str(e)
        finally:
            done_event.set()

    # Start collection in background thread
    thread = threading.Thread(target=run_collection, daemon=True)
    thread.start()

    status_index = 0

    def wait_for_done(timeout: float) -> bool:
        """Blocking wait - will be run in thread."""
        return done_event.wait(timeout=timeout)

    # Send status messages while waiting
    while True:
        # Use asyncio.to_thread to avoid blocking the event loop
        is_done = await asyncio.to_thread(wait_for_done, status_interval)
        if is_done:
            break
        # Still waiting - send status message
        if status_messages:
            yield {"type": "status", "data": status_messages[status_index % len(status_messages)]}
            status_index += 1

    thread.join(timeout=1.0)

    if result_holder["error"]:
        raise Exception(result_holder["error"])

    yield {
        "type": "collect_complete",
        "data": {"full_response": result_holder["response"], "token_usage": result_holder["usage"]},
    }


def load_agent_prompt(agent_type: str) -> str:
    """Load agent prompt from filesystem.

    Tries external DISCO_REPO_PATH first (for local dev), then falls back
    to bundled agents in backend/disco_agents/ (for production).

    Args:
        agent_type: Type of agent (triage, discovery_planner, etc.)

    Returns:
        Agent prompt markdown content
    """
    if agent_type not in AGENT_FILES:
        raise ValueError(f"Unknown agent type: {agent_type}")

    filename = AGENT_FILES[agent_type]
    filepath = None

    # Try external repo path first (local dev)
    if DISCO_REPO_PATH:
        external_path = Path(DISCO_REPO_PATH) / "agents" / filename
        if external_path.exists():
            filepath = external_path
            logger.info(f"Loading agent from external repo: {filepath}")

    # Fall back to bundled agents (production)
    if filepath is None:
        bundled_path = _BUNDLED_AGENTS_PATH / filename
        if bundled_path.exists():
            filepath = bundled_path
            logger.info(f"Loading agent from bundled path: {filepath}")

    if filepath is None:
        logger.error(f"Agent file not found: {filename}")
        raise FileNotFoundError(f"Agent prompt file not found: {filename}")

    content = filepath.read_text()
    logger.info(f"Loaded agent prompt: {agent_type} ({len(content)} chars)")
    return content


def load_methodology_overview() -> str:
    """Load the PuRDy methodology overview document."""
    # Try external repo first
    if DISCO_REPO_PATH:
        filepath = Path(DISCO_REPO_PATH) / METHODOLOGY_FILE
        if filepath.exists():
            return filepath.read_text()

    # Methodology file not bundled - return empty
    logger.warning(f"Methodology file not found: {METHODOLOGY_FILE}")
    return ""


async def build_agent_context(initiative_id: str, agent_type: str, include_system_kb: bool = True) -> Dict:
    """Build context for an agent run.

    Gathers:
    - Initiative documents (uploaded + previous outputs)
    - Global system KB (via vector search on agent type description)
    - Latest version of each output type (for subsequent runs)

    Args:
        initiative_id: Initiative UUID
        agent_type: Type of agent being run
        include_system_kb: Whether to include system KB context

    Returns:
        Dict with context sections
    """
    logger.info(f"Building context for {agent_type} on initiative {initiative_id}")

    context = {"documents": "", "previous_outputs": "", "system_kb": "", "methodology": ""}

    # Get all initiative documents
    from .document_service import get_all_initiative_content

    context["documents"] = await get_all_initiative_content(initiative_id)

    # Get previous outputs (latest of each type)
    outputs_result = await asyncio.to_thread(
        lambda: supabase.table("disco_outputs")
        .select("id, agent_type, version, content_markdown, recommendation, confidence_level")
        .eq("initiative_id", initiative_id)
        .order("created_at", desc=True)
        .execute()
    )

    # Track source outputs for traceability
    source_outputs = []

    if outputs_result.data:
        # Group by agent_type, keep only latest
        seen_types = set()
        previous_outputs = []
        for output in outputs_result.data:
            if output["agent_type"] not in seen_types:
                seen_types.add(output["agent_type"])
                previous_outputs.append(output)

        if previous_outputs:
            output_parts = []
            for output in previous_outputs:
                # Track this output as a source
                source_outputs.append(
                    {
                        "agent_type": output["agent_type"],
                        "version": output["version"],
                        "id": output.get("id"),
                    }
                )
                output_parts.append(f"\n\n=== Previous {output['agent_type']} Output (v{output['version']}) ===\n")
                if output.get("recommendation"):
                    output_parts.append(f"Recommendation: {output['recommendation']}\n")
                if output.get("confidence_level"):
                    output_parts.append(f"Confidence: {output['confidence_level']}\n")
                output_parts.append(output["content_markdown"])
            context["previous_outputs"] = "\n".join(output_parts)

    context["source_outputs"] = source_outputs

    # Fetch initiative throughline
    try:
        initiative_result = await asyncio.to_thread(
            lambda: supabase.table("disco_initiatives")
            .select(
                "throughline, user_corrections, goal_alignment_score, goal_alignment_details, value_alignment, target_department"
            )
            .eq("id", initiative_id)
            .single()
            .execute()
        )
        if initiative_result.data:
            if initiative_result.data.get("throughline"):
                context["throughline"] = initiative_result.data["throughline"]
            if initiative_result.data.get("user_corrections"):
                context["user_corrections"] = initiative_result.data["user_corrections"]
            if initiative_result.data.get("goal_alignment_score") is not None:
                context["goal_alignment_score"] = initiative_result.data["goal_alignment_score"]
            if initiative_result.data.get("goal_alignment_details"):
                context["goal_alignment_details"] = initiative_result.data["goal_alignment_details"]
            if initiative_result.data.get("value_alignment"):
                context["value_alignment"] = initiative_result.data["value_alignment"]
            if initiative_result.data.get("target_department"):
                context["target_department"] = initiative_result.data["target_department"]
    except Exception as e:
        logger.warning(f"Failed to fetch throughline for initiative {initiative_id}: {e}")

    # Include system KB context
    if include_system_kb:
        from .system_kb_service import search_system_kb

        # Search for relevant KB content based on agent type
        agent_desc = AGENT_DESCRIPTIONS.get(agent_type, {})
        search_query = f"{agent_desc.get('description', agent_type)} product requirements discovery"

        kb_chunks = await search_system_kb(search_query, limit=10)
        if kb_chunks:
            kb_parts = []
            for chunk in kb_chunks:
                kb_parts.append(f"\n--- From {chunk.get('filename', 'system KB')} ---\n")
                kb_parts.append(chunk["content"])
            context["system_kb"] = "\n".join(kb_parts)

    # Load methodology overview
    context["methodology"] = load_methodology_overview()

    return context


async def build_project_agent_context(project_id: str, agent_type: str, include_system_kb: bool = True) -> Dict:
    """Build context for a project-level agent run.

    Gathers:
    - Project metadata (title, description, current_state, desired_state, scores)
    - Linked documents via project_documents junction table
    - Previous project-level agent outputs (latest of each type, for chaining)
    - Linked initiative summaries (lightweight context from parent initiatives)
    - Global system KB

    Args:
        project_id: Project UUID
        agent_type: Type of agent being run
        include_system_kb: Whether to include system KB context

    Returns:
        Dict with context sections
    """
    logger.info(f"Building project context for {agent_type} on project {project_id}")

    context: Dict = {"documents": "", "previous_outputs": "", "system_kb": "", "methodology": "", "project_context": ""}

    # 1. Fetch project metadata
    project_result = await asyncio.to_thread(
        lambda: supabase.table("ai_projects")
        .select(
            "id, title, description, current_state, desired_state, department, status, impact_score, feasibility_score, urgency_score, ai_score_justification, stakeholder_ids, initiative_ids"
        )
        .eq("id", project_id)
        .single()
        .execute()
    )
    project = project_result.data if project_result.data else {}

    # Build project context section
    project_parts = []
    if project.get("title"):
        project_parts.append(f"**Project:** {project['title']}")
    if project.get("description"):
        project_parts.append(f"**Description:** {project['description']}")
    if project.get("current_state"):
        project_parts.append(f"**Current State:** {project['current_state']}")
    if project.get("desired_state"):
        project_parts.append(f"**Desired State:** {project['desired_state']}")
    if project.get("department"):
        project_parts.append(f"**Department:** {project['department']}")
    if project.get("status"):
        project_parts.append(f"**Status:** {project['status']}")

    scores = []
    if project.get("impact_score") is not None:
        scores.append(f"Impact: {project['impact_score']}")
    if project.get("feasibility_score") is not None:
        scores.append(f"Feasibility: {project['feasibility_score']}")
    if project.get("urgency_score") is not None:
        scores.append(f"Urgency: {project['urgency_score']}")
    if scores:
        project_parts.append(f"**Scores:** {', '.join(scores)}")
    if project.get("ai_score_justification"):
        project_parts.append(f"**Score Justification:** {project['ai_score_justification']}")

    context["project_context"] = "\n".join(project_parts)

    # 2. Fetch linked documents via project_documents junction table
    try:
        docs_result = await asyncio.to_thread(
            lambda: supabase.table("project_documents")
            .select("document_id, documents(id, title, filename, content, source_platform)")
            .eq("project_id", project_id)
            .execute()
        )
        if docs_result.data:
            doc_parts = []
            for link in docs_result.data:
                doc = link.get("documents")
                if doc and doc.get("content"):
                    doc_name = doc.get("title") or doc.get("filename") or "Untitled"
                    doc_parts.append(f"\n--- Document: {doc_name} ---\n{doc['content']}")
            context["documents"] = "\n".join(doc_parts)
    except Exception as e:
        logger.warning(f"Failed to fetch project documents for {project_id}: {e}")

    # 3. Get previous project-level outputs (latest of each type, for chaining)
    source_outputs = []
    try:
        outputs_result = await asyncio.to_thread(
            lambda: supabase.table("disco_outputs")
            .select("id, agent_type, version, content_markdown, recommendation, confidence_level")
            .eq("project_id", project_id)
            .order("created_at", desc=True)
            .execute()
        )
        if outputs_result.data:
            seen_types: set = set()
            previous_outputs = []
            for output in outputs_result.data:
                if output["agent_type"] not in seen_types:
                    seen_types.add(output["agent_type"])
                    previous_outputs.append(output)
            if previous_outputs:
                output_parts = []
                for output in previous_outputs:
                    source_outputs.append(
                        {
                            "agent_type": output["agent_type"],
                            "version": output["version"],
                            "id": output.get("id"),
                        }
                    )
                    output_parts.append(f"\n\n=== Previous {output['agent_type']} Output (v{output['version']}) ===\n")
                    if output.get("recommendation"):
                        output_parts.append(f"Recommendation: {output['recommendation']}\n")
                    if output.get("confidence_level"):
                        output_parts.append(f"Confidence: {output['confidence_level']}\n")
                    output_parts.append(output["content_markdown"])
                context["previous_outputs"] = "\n".join(output_parts)
    except Exception as e:
        logger.warning(f"Failed to fetch project outputs for {project_id}: {e}")

    context["source_outputs"] = source_outputs

    # 4. Fetch lightweight initiative context if project is linked to initiatives
    initiative_ids = project.get("initiative_ids") or []
    if initiative_ids:
        try:
            init_result = await asyncio.to_thread(
                lambda: supabase.table("disco_initiatives")
                .select("id, name, description, status, throughline")
                .in_("id", initiative_ids)
                .execute()
            )
            if init_result.data:
                init_parts = []
                for init in init_result.data:
                    init_parts.append(f"- **{init['name']}** (status: {init['status']})")
                    if init.get("description"):
                        init_parts.append(f"  {init['description']}")
                context["linked_initiatives"] = "\n".join(init_parts)
        except Exception as e:
            logger.warning(f"Failed to fetch linked initiatives for project {project_id}: {e}")

    # 5. Include system KB context
    if include_system_kb:
        from .system_kb_service import search_system_kb

        agent_desc = AGENT_DESCRIPTIONS.get(agent_type, {})
        search_query = f"{agent_desc.get('description', agent_type)} product requirements discovery"

        kb_chunks = await search_system_kb(search_query, limit=10)
        if kb_chunks:
            kb_parts = []
            for chunk in kb_chunks:
                kb_parts.append(f"\n--- From {chunk.get('filename', 'system KB')} ---\n")
                kb_parts.append(chunk["content"])
            context["system_kb"] = "\n".join(kb_parts)

    # 6. Load methodology overview
    context["methodology"] = load_methodology_overview()

    return context


def build_project_prompt(agent_type: str, context: Dict) -> str:
    """Build the full user prompt for a project-level agent run."""
    parts = []

    parts.append("# Project Context\n")

    if context.get("project_context"):
        parts.append(context["project_context"])
        parts.append("\n")

    if context.get("linked_initiatives"):
        parts.append("## Linked Initiatives\n")
        parts.append(context["linked_initiatives"])
        parts.append("\n")

    # KB folder documents
    if context.get("kb_folder_documents"):
        parts.append("## Stakeholder Documents (from KB)\n")
        parts.append(context["kb_folder_documents"])
        parts.append("\n")

    if context.get("documents"):
        parts.append("## Source Documents\n")
        parts.append(context["documents"])
        parts.append("\n")

    if context.get("previous_outputs"):
        parts.append("## Previous Agent Outputs\n")
        parts.append(context["previous_outputs"])
        parts.append("\n")

    if context.get("system_kb"):
        parts.append("## Reference Knowledge Base\n")
        parts.append(context["system_kb"])
        parts.append("\n")

    # Project-specific agent instructions
    project_agent_instructions = {
        "discovery_guide": """Analyze this project's current vs desired state. Identify knowledge gaps and recommend what additional research or information is needed.

Focus on:
1. Gap analysis between current and desired state
2. What's known vs unknown about this project
3. Key questions that need answers before proceeding
4. Recommended next steps for gathering missing information

Keep this practical and focused on the specific project scope. Target 400-600 words.""",
        "insight_analyst": """Extract patterns from project documents and any prior Discovery output. Create a decision document.

Your process:
1. Read all documents thoroughly
2. Extract key insights with evidence
3. Identify patterns and themes
4. Create a decision document with leverage point and intervention reasoning

Output must start with the decision (GO/NO-GO/CONDITIONAL) as the literal first word.""",
        "initiative_builder": """Evaluate solution approaches for this project. Score options by impact, feasibility, and urgency. Cluster findings into actionable workstreams.

Your process:
1. Identify distinct solution approaches or intervention points
2. Score each on Impact, Feasibility, and Urgency
3. Cluster related items into workstreams
4. Recommend prioritization and dependencies

Prepare your output for human review.""",
        "requirements_generator": """Generate a comprehensive PRD for this project using all available context.

Include all required sections:
- Executive Summary, Problem Statement, Goals & Success Metrics
- Stakeholders, Functional & Non-Functional Requirements
- Technical Evaluation with options, Architecture considerations
- Risks, Dependencies, Implementation Path with phasing

Every requirement must be traceable to project findings and documents.""",
    }

    # Global rules
    parts.append("## Global Rules\n")
    parts.append(
        "- The correct spelling is **Mikki** (not Mickey, Micky, or any other variant). Always use this spelling.\n"
    )

    parts.append("## Your Task\n")
    parts.append(project_agent_instructions.get(agent_type, "Please analyze this project and provide your assessment."))

    return "\n".join(parts)


async def _fetch_kb_folder_documents(folder_path: str, user_id: str) -> str:
    """Fetch documents from a KB folder and return their content.

    Args:
        folder_path: The Obsidian folder path (e.g., "Legal Ops/Ashley Adams")
        user_id: User ID for authorization

    Returns:
        Concatenated document content with headers
    """
    try:
        # Query documents where obsidian_file_path starts with the folder path
        result = await asyncio.to_thread(
            lambda: supabase.table("documents")
            .select("id, filename, title, obsidian_file_path")
            .eq("source_platform", "obsidian")
            .eq("uploaded_by", user_id)
            .ilike("obsidian_file_path", f"{folder_path}%")
            .order("obsidian_file_path")
            .execute()
        )

        documents = result.data or []
        if not documents:
            logger.warning(f"No documents found in KB folder: {folder_path}")
            return ""

        logger.info(f"Found {len(documents)} documents in KB folder: {folder_path}")

        # Fetch content for each document
        content_parts = []
        for doc in documents:
            # Get document content from chunks
            chunks_result = await asyncio.to_thread(
                lambda d=doc: supabase.table("document_chunks")
                .select("content, chunk_index")
                .eq("document_id", d["id"])
                .order("chunk_index")
                .execute()
            )

            content = "\n".join([c["content"] for c in (chunks_result.data or [])])
            if content:
                title = doc.get("title") or doc.get("filename") or doc.get("obsidian_file_path")
                content_parts.append(f"\n\n=== {title} ===\n")
                content_parts.append(f"Source: {doc.get('obsidian_file_path', 'Unknown')}\n")
                content_parts.append(content)

        return "\n".join(content_parts)

    except Exception as e:
        logger.error(f"Error fetching KB folder documents: {e}")
        return ""


async def _fetch_kb_tagged_documents(tags: List[str], user_id: str) -> str:
    """Fetch documents that have ALL specified tags and return their content.

    Uses AND logic - only returns documents that have every tag in the list.

    Args:
        tags: List of tags to filter by
        user_id: User ID for authorization

    Returns:
        Concatenated document content with headers
    """
    try:
        if not tags:
            logger.warning("No tags provided to _fetch_kb_tagged_documents")
            return ""

        # Strategy: get documents with first tag, then filter by remaining tags
        first_tag = tags[0]

        # Get documents with the first tag
        result = await asyncio.to_thread(
            lambda: supabase.table("document_tags")
            .select("document_id, documents!inner(id, filename, title, obsidian_file_path, uploaded_by)")
            .eq("tag", first_tag)
            .eq("documents.uploaded_by", user_id)
            .execute()
        )

        if not result.data:
            logger.warning(f"No documents found with tag: {first_tag}")
            return ""

        # Get candidate document IDs
        candidate_ids = [row["document_id"] for row in result.data]

        # For AND logic: filter documents that have ALL tags
        if len(tags) > 1:
            for additional_tag in tags[1:]:
                tag_result = await asyncio.to_thread(
                    lambda t=additional_tag, cids=candidate_ids: supabase.table("document_tags")
                    .select("document_id")
                    .eq("tag", t)
                    .in_("document_id", cids)
                    .execute()
                )
                # Intersect with candidates
                tag_doc_ids = {row["document_id"] for row in (tag_result.data or [])}
                candidate_ids = [did for did in candidate_ids if did in tag_doc_ids]

                if not candidate_ids:
                    logger.warning(f"No documents found with all tags: {tags}")
                    return ""

        logger.info(f"Found {len(candidate_ids)} documents with tags: {tags}")

        # Fetch document metadata and content
        content_parts = []
        for doc_id in candidate_ids:
            # Get document metadata
            doc_result = await asyncio.to_thread(
                lambda d=doc_id: supabase.table("documents")
                .select("id, filename, title, obsidian_file_path")
                .eq("id", d)
                .single()
                .execute()
            )

            if not doc_result.data:
                continue

            doc = doc_result.data

            # Get document content from chunks
            chunks_result = await asyncio.to_thread(
                lambda d=doc_id: supabase.table("document_chunks")
                .select("content, chunk_index")
                .eq("document_id", d)
                .order("chunk_index")
                .execute()
            )

            content = "\n".join([c["content"] for c in (chunks_result.data or [])])
            if content:
                title = doc.get("title") or doc.get("filename") or doc.get("obsidian_file_path") or "Untitled"
                content_parts.append(f"\n\n=== {title} ===\n")
                source = doc.get("obsidian_file_path") or doc.get("filename") or "Unknown"
                content_parts.append(f"Source: {source}\n")
                content_parts.append(content)

        return "\n".join(content_parts)

    except Exception as e:
        logger.error(f"Error fetching KB tagged documents: {e}")
        return ""


async def run_agent(
    initiative_id: Optional[str] = None,
    agent_type: str = "",
    user_id: str = "",
    document_ids: Optional[List[str]] = None,
    kb_folder: Optional[str] = None,
    kb_tags: Optional[List[str]] = None,
    project_id: Optional[str] = None,
) -> AsyncGenerator[Dict, None]:
    """Execute an agent run with streaming response.

    Supports both initiative-scoped and project-scoped runs.
    Exactly one of initiative_id or project_id must be provided.

    Args:
        initiative_id: Initiative UUID (for initiative-scoped runs)
        agent_type: Type of agent to run
        user_id: User running the agent
        document_ids: Optional list of specific document IDs to use
        kb_folder: Optional KB folder path to include documents from (deprecated, use kb_tags)
        kb_tags: Optional list of KB tags to filter documents by (preferred, uses AND logic)
        project_id: Project UUID (for project-scoped runs)

    Yields:
        Dict with type (status, content, complete) and data
    """
    # Validate exactly one scope is provided
    if not initiative_id and not project_id:
        raise ValueError("Either initiative_id or project_id must be provided")
    if initiative_id and project_id:
        raise ValueError("Cannot provide both initiative_id and project_id")

    is_project_scoped = project_id is not None
    scope_id = project_id if is_project_scoped else initiative_id
    scope_label = "project" if is_project_scoped else "initiative"

    logger.info("[PURDY] ========== Starting agent run ==========")
    logger.info(f"[PURDY] Agent type: '{agent_type}' (type: {type(agent_type).__name__})")
    logger.info(f"[PURDY] {scope_label.title()}: {scope_id}, User: {user_id}")
    if kb_folder:
        logger.info(f"[PURDY] KB folder: {kb_folder}")
    if kb_tags:
        logger.info(f"[PURDY] KB tags: {kb_tags}")

    # Validate agent_type immediately
    if not agent_type or agent_type not in AGENT_FILES:
        logger.error(f"[PURDY] Invalid agent_type: '{agent_type}'")
        raise ValueError(f"Invalid agent type: {agent_type}")

    run_id = str(uuid4())
    logger.info(f"[PURDY] Generated run_id: {run_id}")

    try:
        # Create run record with output format metadata
        run_record = {
            "id": run_id,
            "agent_type": agent_type,
            "run_by": user_id,
            "status": "running",
            "metadata": {"output_format": "unified"},
        }
        if is_project_scoped:
            run_record["project_id"] = project_id
        else:
            run_record["initiative_id"] = initiative_id
        await asyncio.to_thread(lambda: supabase.table("disco_runs").insert(run_record).execute())

        yield {"type": "status", "data": "Loading agent prompt..."}

        # Load agent prompt
        agent_prompt = load_agent_prompt(agent_type)

        yield {"type": "status", "data": "Building context..."}

        # Build context (branch based on scope)
        if is_project_scoped:
            context = await build_project_agent_context(project_id, agent_type)
        else:
            context = await build_agent_context(initiative_id, agent_type)

        # If KB tags specified, fetch and add those documents (preferred method)
        if kb_tags:
            tag_list = ", ".join(kb_tags)
            yield {"type": "status", "data": f"Loading documents with tags: {tag_list}..."}
            kb_docs_content = await _fetch_kb_tagged_documents(kb_tags, user_id)
            if kb_docs_content:
                context["kb_folder_documents"] = kb_docs_content  # Reuse same context key
                logger.info(f"[PURDY] Added {len(kb_docs_content)} chars from KB tags: {kb_tags}")
        # Fallback: If KB folder specified (deprecated), fetch and add those documents
        elif kb_folder:
            yield {"type": "status", "data": f"Loading documents from {kb_folder}..."}
            kb_docs_content = await _fetch_kb_folder_documents(kb_folder, user_id)
            if kb_docs_content:
                context["kb_folder_documents"] = kb_docs_content
                logger.info(f"[PURDY] Added {len(kb_docs_content)} chars from KB folder")

        # Build the full prompt (project vs initiative)
        if is_project_scoped:
            full_prompt = build_project_prompt(agent_type, context)
        else:
            full_prompt = build_full_prompt(agent_type, context)

        # Track document IDs used
        if document_ids:
            for doc_id in document_ids:
                await asyncio.to_thread(
                    lambda d=doc_id: supabase.table("disco_run_documents")
                    .insert({"run_id": run_id, "document_id": d})
                    .execute()
                )

        # Get model and log context size
        model = get_model_for_agent(agent_type)
        system_chars = len(agent_prompt)
        prompt_chars = len(full_prompt)
        logger.info(
            f"[PURDY] Context size - system: {system_chars} chars, user: {prompt_chars} chars, total: {system_chars + prompt_chars} chars"
        )
        logger.info(f"[PURDY] Estimated tokens: ~{(system_chars + prompt_chars) // 4}")
        logger.info(f"[PURDY] Calling Claude API with model: {model}")

        # Send initial status message
        yield {"type": "status", "data": random.choice(FUN_STATUS_MESSAGES)}

        # Stream Claude response with periodic status messages
        full_response = ""
        token_usage = {}

        try:
            async for item in stream_with_status_messages(
                model=model,
                system_prompt=agent_prompt,
                user_prompt=full_prompt,
                status_messages=FUN_STATUS_MESSAGES,
                status_interval=8.0,
                max_tokens=16000,
            ):
                if item["type"] == "stream_complete":
                    # Extract final results
                    full_response = item["data"]["full_response"]
                    token_usage = item["data"]["token_usage"]
                    logger.info(f"[PURDY] Claude API completed. Tokens: {token_usage}")
                else:
                    # Pass through status, content, keepalive events
                    yield item
        except Exception as claude_error:
            logger.error(f"[PURDY] Claude API error: {type(claude_error).__name__}: {claude_error}")
            raise

        # Parse output
        parsed_output = parse_agent_output(agent_type, full_response)

        # Get next version number (scoped by project or initiative)
        if is_project_scoped:
            version_result = await asyncio.to_thread(
                lambda: supabase.table("disco_outputs")
                .select("version")
                .eq("project_id", project_id)
                .eq("agent_type", agent_type)
                .order("version", desc=True)
                .limit(1)
                .execute()
            )
        else:
            version_result = await asyncio.to_thread(
                lambda: supabase.table("disco_outputs")
                .select("version")
                .eq("initiative_id", initiative_id)
                .eq("agent_type", agent_type)
                .order("version", desc=True)
                .limit(1)
                .execute()
            )
        next_version = 1
        if version_result.data:
            next_version = version_result.data[0]["version"] + 1

        # Parse throughline resolution for requirements_generator
        throughline_resolution = None
        if agent_type == "requirements_generator":
            throughline_resolution = parse_throughline_resolution(full_response)

        # Parse triage suggestions for discovery_guide (when framing extraction occurs)
        triage_suggestions = None
        if agent_type == "discovery_guide":
            triage_suggestions = parse_triage_suggestions(full_response)
            if triage_suggestions:
                logger.info(f"[PURDY] Parsed triage suggestions with keys: {list(triage_suggestions.keys())}")

        # Store output
        output_id = str(uuid4())
        output_data = {
            "id": output_id,
            "run_id": run_id,
            "agent_type": agent_type,
            "version": next_version,
            "title": parsed_output.get("title"),
            "recommendation": parsed_output.get("recommendation"),
            "tier_routing": parsed_output.get("tier_routing"),
            "confidence_level": parsed_output.get("confidence_level"),
            "executive_summary": parsed_output.get("executive_summary"),
            "content_markdown": full_response,
            "content_structured": parsed_output,
            "output_format": "unified",
            "source_outputs": context.get("source_outputs", []),
            "throughline_resolution": throughline_resolution,
            "triage_suggestions": triage_suggestions,
        }
        # Set scope column
        if is_project_scoped:
            output_data["project_id"] = project_id
        else:
            output_data["initiative_id"] = initiative_id

        # Log the data being stored
        logger.info(f"[PURDY] Storing output - id: {output_id}, agent_type: {agent_type}, version: {next_version}")
        logger.info(f"[PURDY] Output data keys: {list(output_data.keys())}")
        logger.info(f"[PURDY] content_markdown length: {len(full_response)}")
        logger.info(
            f"[PURDY] Parsed title: {parsed_output.get('title')}, recommendation: {parsed_output.get('recommendation')}"
        )

        # Use explicit copy to avoid any closure issues
        data_to_insert = dict(output_data)
        logger.info(
            f"[PURDY] Data to insert: agent_type={data_to_insert.get('agent_type')}, version={data_to_insert.get('version')}"
        )

        try:
            insert_result = await asyncio.to_thread(
                lambda: supabase.table("disco_outputs").insert(data_to_insert).execute()
            )

            if not insert_result.data:
                logger.error(f"[PURDY] Insert returned no data! Result: {insert_result}")
                raise Exception("Failed to insert output - no data returned")

            logger.info(f"[PURDY] Insert SUCCESS: {insert_result.data[0].get('id') if insert_result.data else 'no id'}")
        except Exception as insert_err:
            logger.error(f"[PURDY] Insert FAILED: {insert_err}")
            raise

        # Update run status
        await asyncio.to_thread(
            lambda: supabase.table("disco_runs")
            .update(
                {
                    "status": "completed",
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "token_usage": token_usage,
                }
            )
            .eq("id", run_id)
            .execute()
        )

        # Update initiative status based on agent type (skip for project-scoped runs)
        if not is_project_scoped:
            new_status = get_status_for_agent(agent_type)
            if new_status:
                await asyncio.to_thread(
                    lambda: supabase.table("disco_initiatives")
                    .update({"status": new_status})
                    .eq("id", initiative_id)
                    .execute()
                )

        yield {
            "type": "complete",
            "data": {
                "run_id": run_id,
                "output_id": output_id,
                "version": next_version,
                "parsed": parsed_output,
                "token_usage": token_usage,
            },
        }

    except Exception as e:
        logger.error(f"Agent run failed: {e}")
        error_msg = str(e)

        # Update run status to failed
        await asyncio.to_thread(
            lambda: supabase.table("disco_runs")
            .update(
                {
                    "status": "failed",
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "error_message": error_msg,
                }
            )
            .eq("id", run_id)
            .execute()
        )

        yield {"type": "error", "data": error_msg}


def _format_throughline_for_prompt(throughline: Dict) -> str:
    """Format throughline data as markdown for injection into agent prompts."""
    sections = []

    problem_statements = [ps for ps in (throughline.get("problem_statements") or []) if not ps.get("rejected")]
    if problem_statements:
        sections.append("### Problem Statements")
        for ps in problem_statements:
            ps_id = ps.get("id", "?")
            sections.append(f"- **{ps_id}**: {ps.get('text', '')}")

    hypotheses = [h for h in (throughline.get("hypotheses") or []) if not h.get("rejected")]
    if hypotheses:
        sections.append("\n### Hypotheses")
        for h in hypotheses:
            h_id = h.get("id", "?")
            h_type = h.get("type", "assumption")
            line = f"- **{h_id}** ({h_type}): {h.get('statement', '')}"
            if h.get("rationale"):
                line += f" -- Rationale: {h['rationale']}"
            sections.append(line)

    gaps = [g for g in (throughline.get("gaps") or []) if not g.get("rejected")]
    if gaps:
        sections.append("\n### Known Gaps")
        for g in gaps:
            g_id = g.get("id", "?")
            g_type = g.get("type", "data")
            sections.append(f"- **{g_id}** [{g_type}]: {g.get('description', '')}")

    desired = throughline.get("desired_outcome_state")
    if desired:
        sections.append(f"\n### Desired Outcome State\n{desired}")

    return "\n".join(sections)


def build_full_prompt(agent_type: str, context: Dict) -> str:
    """Build the full user prompt for the agent."""
    parts = []

    parts.append("# Initiative Context\n")

    # Throughline (structured input framing)
    if context.get("throughline"):
        parts.append("## Initiative Throughline\n")
        parts.append(_format_throughline_for_prompt(context["throughline"]))
        parts.append("\n")

    # Ground-truth corrections from initiative owner
    if context.get("user_corrections"):
        parts.append("## Ground-Truth Corrections (AUTHORITATIVE)\n")
        parts.append(
            "The following corrections from the initiative owner override any conflicting information in the documents below. Treat these as factual ground truth.\n"
        )
        parts.append(context["user_corrections"])
        parts.append("\n")

    # Goal alignment analysis (from initiative-level strategic scoring)
    if context.get("goal_alignment_score") is not None:
        parts.append("## Strategic Goal Alignment Analysis\n")
        score = context["goal_alignment_score"]
        parts.append(f"Overall alignment score: {score}/100\n")
        details = context.get("goal_alignment_details", {})
        pillar_scores = details.get("pillar_scores", {})
        pillar_names = {
            "customer_prospect_journey": "Customer and Prospect Journey",
            "maximize_value": "Maximize Value from Core Systems and AI",
            "data_first_digital_workforce": "Data-First Digital Workforce",
            "high_trust_culture": "High-Trust and Communicative IS Culture",
        }
        for key, name in pillar_names.items():
            pillar = pillar_scores.get(key, {})
            p_score = pillar.get("score", "N/A")
            rationale = pillar.get("rationale", "")
            parts.append(f"- {name}: {p_score}/25 -- {rationale}")
        if details.get("kpi_impacts"):
            kpis = ", ".join(details["kpi_impacts"])
            parts.append(f"\nImpacted KPIs: {kpis}")
        if details.get("alignment_confidence") is not None:
            parts.append(f"\nAlignment confidence: {details['alignment_confidence']}/100")
        if details.get("confidence_questions"):
            parts.append("\nQuestions that would raise confidence:")
            for q in details["confidence_questions"]:
                parts.append(f"  - {q}")
        if details.get("summary"):
            parts.append(f"\nAlignment summary: {details['summary']}")
        parts.append("\n")

    # KB folder documents (for discovery_prep - these are the PRIMARY input)
    if context.get("kb_folder_documents"):
        parts.append("## Stakeholder Documents (from KB Folder)\n")
        parts.append(context["kb_folder_documents"])
        parts.append("\n")

    if context.get("documents"):
        parts.append("## Source Documents\n")
        parts.append(context["documents"])
        parts.append("\n")

    if context.get("previous_outputs"):
        parts.append("## Previous Agent Outputs\n")
        parts.append(context["previous_outputs"])
        parts.append("\n")

    if context.get("system_kb"):
        parts.append("## Reference Knowledge Base\n")
        parts.append(context["system_kb"])
        parts.append("\n")

    # Agent-specific instructions
    agent_instructions = {
        # === Consolidated Agents (v2.0) ===
        "discovery_guide": """Please guide this initiative through the Discovery stage.

Produce a single unified output: VERDICT, Current State, Desired State, Strategic Alignment (if applicable), Discovery Plan, Next Step, and Appendix (if applicable).
Adapt depth based on available context (documents, prior outputs, session transcripts).
If Strategic Goal Alignment data is provided and any pillar scores below 15/25 or confidence below 60, include the Strategic Alignment section and the Appendix: Strategic Goals Reference table. The appendix helps report consumers who are not system users understand what goals exist and whether important ones are missing.
Target 600-800 words total (appendix excluded from word count). Every section should be self-contained and readable without cross-referencing.""",
        "insight_analyst": """Please analyze all discovery artifacts and create a decision document.

Your process:
1. Read all documents thoroughly - do not skim
2. Extract key insights with direct quotes as evidence
3. Identify system patterns (check Pattern Library for matches)
4. Create the decision document with leverage point and intervention reasoning

Output must start with the decision (GO/NO-GO/CONDITIONAL) as the literal first word.""",
        "initiative_builder": """Please transform the decision document into initiative bundles.

Your process:
1. Cluster related findings by theme, root cause, or solution affinity
2. Score each cluster on Impact, Feasibility, and Urgency
3. Create bundle definitions with dependencies and rationale
4. Include decision points for the human checkpoint

Prepare your output for human review - they will approve/reject/edit bundles before PRD generation.""",
        "requirements_generator": """Please generate a comprehensive PRD with technical evaluation for the approved initiative bundle.

Include all required sections:
- Executive Summary, Problem Statement, Goals & Success Metrics
- Stakeholders, Functional & Non-Functional Requirements
- Technical Evaluation with 3+ options, Architecture diagram, 3-year TCO
- Risks, Dependencies, Implementation Path with phasing

Every requirement must be traceable to discovery findings.""",
        # === Legacy Agents (backwards compatibility) ===
        "discovery_prep": """Please analyze the stakeholder documents provided and create a Meeting Preparation Guide.

FIRST, evaluate the Minimum Viable Input (MVI):
- Can you identify at least 2 potential projects or challenges?
- Do you have stakeholder context (role, team)?
- Is there enough detail to justify Impact/Feasibility/Urgency scores?

If MVI is NOT met, output a Stakeholder Request asking for the specific context needed.

If MVI IS met, create a Meeting Prep Guide with:
1. Project Cards (3-5) with IFU scores and evidence-based rationale
2. Key Assumptions to validate (with checkboxes)
3. Confirmation Questions for each project
4. Meta-Questions (cross-cutting concerns)
5. Selection Table with recommendations
6. Blank capture sections for meeting use

Base all scores and insights on evidence from the provided documents. Do not invent projects not mentioned in the documents.""",
        "triage": "Please perform a triage analysis of this initiative. Provide a GO/NO-GO recommendation, tier routing, and confidence-tagged ROI assessment.",
        "discovery_planner": """Please create an outcome-driven discovery plan for this initiative.

FIRST, complete the Pre-Meeting Knowledge Framework:
1. PARTICIPANT KNOWLEDGE - Document what you know vs. need to discover about participants
2. PROBLEM/OPPORTUNITY CONTEXT - Document what you know vs. need to discover about the problem
3. DESIRED OUTCOMES - Define specific artifacts, decisions, and information needed from discovery
4. STRATEGIC CONTEXT - Document alignment, dependencies, and constraints

THEN, verify pre-work completeness (flag any BLOCKING gaps before proceeding).

FINALLY, create the discovery plan with:
- Type-specific activities and questions
- Quantification gates
- Failure patterns to watch for
- Clear success criteria tied to desired outcomes""",
        "coverage_tracker": "Please analyze the current discovery coverage. Identify gaps, assess readiness for synthesis, and perform 3M waste diagnosis if applicable.",
        "consolidator": "Please consolidate all discovery findings into a comprehensive decision document. Include persona-specific briefs for Finance, Engineering, Sales, and Executive audiences.",
        "synthesizer": "Please synthesize all discovery findings into a comprehensive PRD. Include persona-specific briefs for Finance, Engineering, Sales, and Executive audiences.",
        "strategist": "Please analyze all consolidated insights and propose initiative bundles. Cluster related items, score each cluster on impact/feasibility/urgency, and create actionable bundle definitions for human review.",
        "prd_generator": "Please generate a complete PRD (Product Requirements Document) for the given initiative bundle. Include all required sections: executive summary, problem statement, goals, stakeholders, requirements, technical considerations, risks, and timeline.",
        "tech_evaluation": "Please evaluate technical platform options for this initiative. Provide recommendations with confidence-tagged effort estimates.",
    }

    # Global rules for all agents
    parts.append("## Global Rules\n")
    parts.append(
        "- The correct spelling is **Mikki** (not Mickey, Micky, or any other variant). Always use this spelling.\n"
    )

    parts.append("## Your Task\n")
    parts.append(agent_instructions.get(agent_type, "Please analyze this initiative and provide your assessment."))

    # Add strategic goals reference appendix when alignment data is present
    if context.get("goal_alignment_score") is not None:
        from services.goal_alignment_analyzer import IS_GOALS

        parts.append("\n\n## Appendix: Strategic Goals Currently in the System\n")
        parts.append(
            "The following IS team FY27 strategic pillars and KPIs are used to score alignment. If this initiative maps to goals or KPIs NOT listed here, note that in your output.\n"
        )
        for i, (key, pillar) in enumerate(IS_GOALS.items(), 1):
            kpis = "; ".join(pillar["kpis"])
            parts.append(f"{i}. **{pillar['name']}** -- {pillar['description'][:120]}")
            parts.append(f"   KPIs: {kpis}")
        # Include initiative-specific department goals if available
        val_align = context.get("value_alignment", {})
        if isinstance(val_align, dict):
            dept = context.get("target_department")
            dept_goals = val_align.get("department_goals", [])
            dept_kpis = val_align.get("kpis", [])
            if dept_goals or dept_kpis:
                dept_label = f" ({dept})" if dept else ""
                parts.append(f"\n**Department-Specific Goals{dept_label}:**")
                for g in dept_goals or []:
                    parts.append(f"- {g}")
                if dept_kpis:
                    parts.append(f"Department KPIs: {'; '.join(dept_kpis)}")
        parts.append("")

    # Add throughline-awareness instructions when throughline is present
    if context.get("throughline"):
        default_throughline = "\n\nTHROUGHLINE: The Initiative Throughline above is the framing for this initiative - its problem statements, hypotheses, and gaps. Treat it as a key input. Reference throughline items narratively in your output (describe them in plain language, use IDs only as parentheticals for traceability)."
        throughline_instructions = {
            "discovery_guide": "\n\nTHROUGHLINE: The Initiative Throughline is the framing for this initiative. Evaluate problem statements against the 4-criteria gate, design sessions targeting specific gaps, and report per-hypothesis evidence status. Always reference items narratively, not by bare ID.",
            "insight_analyst": "\n\nTHROUGHLINE: The Initiative Throughline is the framing for this initiative. After key insights, include a Hypothesis Evidence section mapping findings to throughline hypotheses. Note which gaps remain unaddressed. Reference items narratively, not by bare ID.",
            "initiative_builder": "\n\nTHROUGHLINE: The Initiative Throughline is the framing for this initiative. For each bundle, describe which problem statements and hypotheses it addresses. Flag any unaddressed items. Reference items narratively, not by bare ID.",
            "requirements_generator": "\n\nTHROUGHLINE: The Initiative Throughline is the framing for this initiative. Include a ## Throughline Resolution section with: Hypothesis Resolution Table (ID | Status | Evidence), Gap Status Table (ID | Status | Findings), Recommended State Changes, and So What? section.",
        }
        parts.append(throughline_instructions.get(agent_type, default_throughline))

    return "\n".join(parts)


def parse_agent_output(agent_type: str, raw_output: str) -> Dict:
    """Parse structured data from agent output.

    Args:
        agent_type: Type of agent
        raw_output: Raw markdown output

    Returns:
        Dict with extracted structured fields
    """
    parsed = {
        "title": None,
        "recommendation": None,
        "tier_routing": None,
        "confidence_level": None,
        "executive_summary": None,
        "sections": {},
    }

    # Extract title (first H1)
    title_match = re.search(r"^#\s+(.+)$", raw_output, re.MULTILINE)
    if title_match:
        parsed["title"] = title_match.group(1).strip()

    # Extract recommendation (GO/NO-GO/VERDICT)
    rec_patterns = [
        r"\*?\*?VERDICT:\s*\*?\*?\s*\[?\*?\*?(GO WITH CONDITIONS|GO|NO-GO|DEFER|INVESTIGATE)\*?\*?\]?",
        r"(?:Recommendation|Decision)[:\s]+\*?\*?(GO WITH CONDITIONS|GO|NO-GO|CONDITIONAL GO|DEFER|INVESTIGATE)\*?\*?",
        r"\*\*(GO WITH CONDITIONS|GO|NO-GO|CONDITIONAL GO|DEFER|INVESTIGATE)\*\*",
        r"^(GO|NO-GO|CONDITIONAL GO)$",
    ]
    for pattern in rec_patterns:
        rec_match = re.search(pattern, raw_output, re.IGNORECASE | re.MULTILINE)
        if rec_match:
            parsed["recommendation"] = rec_match.group(1).upper()
            break

    # Extract tier routing
    tier_patterns = [
        r"(?:Tier|Routing)[:\s]+\*?\*?(ELT|Solutions|Self-Serve|Tier \d)\*?\*?",
        r"\*\*(ELT|Solutions|Self-Serve)\*\*\s*(?:tier|routing)?",
    ]
    for pattern in tier_patterns:
        tier_match = re.search(pattern, raw_output, re.IGNORECASE)
        if tier_match:
            parsed["tier_routing"] = tier_match.group(1)
            break

    # Extract confidence level
    conf_patterns = [
        r"(?:Confidence)[:\s]+\*?\*?(HIGH|MEDIUM|LOW)\*?\*?",
        r"\*\*(HIGH|MEDIUM|LOW)\*\*\s*confidence",
    ]
    for pattern in conf_patterns:
        conf_match = re.search(pattern, raw_output, re.IGNORECASE)
        if conf_match:
            parsed["confidence_level"] = conf_match.group(1).upper()
            break

    # Extract executive summary
    # First try: "Executive Summary" heading (v4.0 and earlier)
    summary_match = re.search(
        r"##?\s*Executive\s+Summary\s*\n+(.+?)(?=\n##|\n#|\Z)",
        raw_output,
        re.IGNORECASE | re.DOTALL,
    )
    if summary_match:
        summary = summary_match.group(1).strip()
        # Take first paragraph
        first_para = summary.split("\n\n")[0]
        parsed["executive_summary"] = first_para[:1000]  # Limit length
    else:
        # Fallback: v4.1 decision-first format - use the opening decision line
        # Matches: **GO:** ..., **NO-GO:** ..., **CONDITIONAL:** ...
        decision_line_match = re.search(
            r"^\*\*(GO|NO-GO|CONDITIONAL):\*\*\s*(.+?)(?=\n\n|\n---|\n##|\Z)",
            raw_output,
            re.MULTILINE | re.DOTALL,
        )
        if decision_line_match:
            decision_type = decision_line_match.group(1)
            decision_text = decision_line_match.group(2).strip()
            parsed["executive_summary"] = f"{decision_type}: {decision_text}"[:1000]

    # Extract section headers
    section_matches = re.findall(r"^(#{1,3})\s+(.+)$", raw_output, re.MULTILINE)
    sections = []
    for level, title in section_matches:
        sections.append({"level": len(level), "title": title.strip()})
    parsed["sections"] = sections

    return parsed


def parse_throughline_resolution(raw_output: str) -> Optional[Dict]:
    """Parse throughline resolution from requirements_generator output.

    Extracts structured data from the ## Throughline Resolution section.
    Returns None if no resolution section found.
    """
    # Find the Throughline Resolution section
    # Use ##(?!#) to stop at ## headings but NOT ### subsections within this section
    resolution_match = re.search(
        r"##\s*Throughline\s+Resolution\s*\n(.+?)(?=\n##(?!#)|\Z)",
        raw_output,
        re.IGNORECASE | re.DOTALL,
    )
    if not resolution_match:
        return None

    section = resolution_match.group(1)
    resolution = {}

    # Parse hypothesis resolution table rows
    # Expected format: | h-1 | confirmed | Evidence text |
    hypothesis_resolutions = []
    hyp_rows = re.findall(
        r"\|\s*(h-\d+)[^|]*\|\s*(confirmed|refuted|inconclusive)\s*\|\s*(.+?)\s*\|",
        section,
        re.IGNORECASE,
    )
    for h_id, status, evidence in hyp_rows:
        hypothesis_resolutions.append(
            {
                "hypothesis_id": h_id.strip(),
                "status": status.strip().lower(),
                "evidence_summary": evidence.strip(),
            }
        )
    if hypothesis_resolutions:
        resolution["hypothesis_resolutions"] = hypothesis_resolutions

    # Parse gap status table rows
    # Expected format: | g-1 | addressed | Findings text |
    gap_statuses = []
    gap_rows = re.findall(
        r"\|\s*(g-\d+)[^|]*\|\s*(addressed|unaddressed|partially_addressed|partially addressed)\s*\|\s*(.+?)\s*\|",
        section,
        re.IGNORECASE,
    )
    for g_id, status, findings in gap_rows:
        gap_statuses.append(
            {
                "gap_id": g_id.strip(),
                "status": status.strip().lower().replace(" ", "_"),
                "findings": findings.strip(),
            }
        )
    if gap_statuses:
        resolution["gap_statuses"] = gap_statuses

    # Parse state changes
    state_changes = []
    # Look for state changes section
    sc_match = re.search(
        r"(?:###?\s*(?:Recommended\s+)?State\s+Changes|State\s+Changes)\s*\n(.+?)(?=\n###|\n##|\Z)",
        section,
        re.IGNORECASE | re.DOTALL,
    )
    if sc_match:
        sc_text = sc_match.group(1)
        # Parse bullet points or table rows
        sc_bullets = re.findall(r"[-*]\s+(.+)", sc_text)
        for bullet in sc_bullets:
            parts = bullet.split("|")
            sc = {"description": parts[0].strip()}
            if len(parts) > 1:
                sc["owner"] = parts[1].strip()
            if len(parts) > 2:
                sc["deadline"] = parts[2].strip()
            state_changes.append(sc)
        # Also try table format
        sc_rows = re.findall(r"\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|", sc_text)
        for desc, owner, deadline in sc_rows:
            if desc.strip().startswith("---") or desc.strip().lower() == "description":
                continue
            state_changes.append(
                {
                    "description": desc.strip(),
                    "owner": owner.strip() if owner.strip() != "-" else None,
                    "deadline": deadline.strip() if deadline.strip() != "-" else None,
                }
            )
    if state_changes:
        resolution["state_changes"] = state_changes

    # Parse So What? section
    so_what_match = re.search(
        r"(?:###?\s*)?So\s+What\??\s*\n(.+?)(?=\n###|\n##|\Z)",
        section,
        re.IGNORECASE | re.DOTALL,
    )
    if so_what_match:
        so_what_text = so_what_match.group(1)
        so_what = {}

        for field, pattern in [
            (
                "state_change_proposed",
                r"\*{0,2}(?:State\s+Change\s+Proposed|Proposed\s+Change)\*{0,2}[:\s]+(.+?)(?:\n|$)",
            ),
            ("next_human_action", r"\*{0,2}(?:Next\s+Human\s+Action|Next\s+Action)\*{0,2}[:\s]+(.+?)(?:\n|$)"),
            ("kill_test", r"\*{0,2}(?:Kill\s+Test)\*{0,2}[:\s]+(.+?)(?:\n|$)"),
        ]:
            field_match = re.search(pattern, so_what_text, re.IGNORECASE)
            if field_match:
                so_what[field] = field_match.group(1).strip().strip("*").strip()

        if so_what:
            resolution["so_what"] = so_what

    return resolution if resolution else None


def parse_triage_suggestions(raw_output: str) -> Optional[Dict]:
    """Parse suggested framing from triage output.

    Extracts structured data from the ## Suggested Framing section
    that the triage agent produces when a discovery has sparse/empty throughline.
    Returns None if no suggestions section found.
    """
    # Find the Suggested Framing section
    suggestions_match = re.search(
        r"##\s*Suggested\s+Framing\s*\n(.+?)(?=\n##(?!#)|\Z)",
        raw_output,
        re.IGNORECASE | re.DOTALL,
    )
    if not suggestions_match:
        return None

    section = suggestions_match.group(1)
    suggestions = {}

    # Parse suggested problem statements
    ps_section = re.search(
        r"###?\s*Suggested\s+Problem\s+Statements?\s*\n(.+?)(?=\n###|\Z)",
        section,
        re.IGNORECASE | re.DOTALL,
    )
    if ps_section:
        problem_statements = []
        for match in re.finditer(r"[-*]\s+(?:\[?(ps-\d+)\]?)?\s*(.+)", ps_section.group(1)):
            ps_id = match.group(1) or f"ps-{len(problem_statements) + 1}"
            problem_statements.append({"id": ps_id, "text": match.group(2).strip()})
        if problem_statements:
            suggestions["problem_statements"] = problem_statements

    # Parse suggested hypotheses
    h_section = re.search(
        r"###?\s*Suggested\s+Hypothes[ei]s\s*\n(.+?)(?=\n###|\Z)",
        section,
        re.IGNORECASE | re.DOTALL,
    )
    if h_section:
        hypotheses = []
        for match in re.finditer(r"[-*]\s+(?:\[?(h-\d+)\]?)?\s*(.+)", h_section.group(1)):
            h_id = match.group(1) or f"h-{len(hypotheses) + 1}"
            text = match.group(2).strip()
            # Extract rationale if present
            rationale_match = re.search(r"\(Rationale:\s*(.+?)\)\s*$", text, re.IGNORECASE)
            rationale = rationale_match.group(1).strip() if rationale_match else None
            statement = re.sub(r"\s*\(Rationale:.*\)\s*$", "", text, flags=re.IGNORECASE).strip()
            hypotheses.append({"id": h_id, "statement": statement, "rationale": rationale, "type": "assumption"})
        if hypotheses:
            suggestions["hypotheses"] = hypotheses

    # Parse suggested gaps
    g_section = re.search(
        r"###?\s*Suggested\s+Gaps?\s*\n(.+?)(?=\n###|\Z)",
        section,
        re.IGNORECASE | re.DOTALL,
    )
    if g_section:
        gaps = []
        for match in re.finditer(
            r"[-*]\s+(?:\[?(g-\d+)\]?)?\s*(?:\[?(data|people|process|capability)\]?:?\s*)?(.+)",
            g_section.group(1),
            re.IGNORECASE,
        ):
            g_id = match.group(1) or f"g-{len(gaps) + 1}"
            g_type = (match.group(2) or "data").lower()
            gaps.append({"id": g_id, "description": match.group(3).strip(), "type": g_type})
        if gaps:
            suggestions["gaps"] = gaps

    # Parse suggested KPIs
    kpi_section = re.search(
        r"###?\s*Suggested\s+KPIs?\s*\n(.+?)(?=\n###|\Z)",
        section,
        re.IGNORECASE | re.DOTALL,
    )
    if kpi_section:
        kpis = [m.group(1).strip() for m in re.finditer(r"[-*]\s+(.+)", kpi_section.group(1))]
        if kpis:
            suggestions["kpis"] = kpis

    # Parse suggested stakeholders
    sh_section = re.search(
        r"###?\s*Suggested\s+Stakeholders?\s*\n(.+?)(?=\n###|\Z)",
        section,
        re.IGNORECASE | re.DOTALL,
    )
    if sh_section:
        stakeholders = [m.group(1).strip() for m in re.finditer(r"[-*]\s+(.+)", sh_section.group(1))]
        if stakeholders:
            suggestions["stakeholders"] = stakeholders

    # Parse value alignment notes
    va_section = re.search(
        r"###?\s*Value\s+Alignment\s+Notes?\s*\n(.+?)(?=\n###|\n##|\Z)",
        section,
        re.IGNORECASE | re.DOTALL,
    )
    if va_section:
        notes = va_section.group(1).strip()
        if notes:
            suggestions["value_alignment_notes"] = notes

    return suggestions if suggestions else None


def get_status_for_agent(agent_type: str) -> Optional[str]:
    """Get the initiative status to set after an agent completes.

    DISCo workflow stages (consolidated agents):
    - D (Discovery): discovery_guide → in_discovery (or triaged if triage mode)
    - I (Insights): insight_analyst → consolidated
    - S (Synthesis): initiative_builder → synthesized
    - C (Convergence): requirements_generator → documented

    Legacy agents maintain backwards compatibility.
    """
    status_map = {
        # === Consolidated Agents (v2.0) ===
        "discovery_guide": "in_discovery",  # May be triaged/in_discovery based on mode
        "insight_analyst": "consolidated",
        "initiative_builder": "synthesized",
        "requirements_generator": "documented",
        # === Legacy Agents (backwards compatibility) ===
        "discovery_prep": "prep_complete",
        "triage": "triaged",
        "discovery_planner": "in_discovery",
        "coverage_tracker": "in_discovery",
        "insight_extractor": "consolidated",
        "consolidator": "consolidated",
        "synthesizer": "synthesized",
        "strategist": "synthesized",
        "prd_generator": "documented",
        "tech_evaluation": "documented",
    }
    return status_map.get(agent_type)


async def run_agent_multi_pass(
    initiative_id: str,
    agent_type: str,
    user_id: str,
    document_ids: Optional[List[str]] = None,
) -> AsyncGenerator[Dict, None]:
    """Execute a multi-pass agent run with meta-synthesis.

    Runs 3 Sonnet passes with varying temperatures, then feeds all outputs
    to Opus for meta-synthesis to produce a best-of-all unified output.

    Args:
        initiative_id: Initiative UUID
        agent_type: Type of agent to run (must be in MULTI_PASS_CONFIG["supported_agents"])
        user_id: User running the agent
        document_ids: Optional list of specific document IDs to use

    Yields:
        Dict with type (status, content, pass_complete, complete) and data
    """
    logger.info("[PURDY-MP] ========== Starting multi-pass synthesis ==========")
    logger.info(f"[PURDY-MP] Agent type: '{agent_type}', Initiative: {initiative_id}")

    if agent_type not in MULTI_PASS_CONFIG["supported_agents"]:
        raise ValueError(f"Multi-pass not supported for agent type: {agent_type}")

    run_id = str(uuid4())
    passes_config = MULTI_PASS_CONFIG["passes"]
    meta_config = MULTI_PASS_CONFIG["meta_synthesis"]

    try:
        # Create run record with multi-pass metadata
        await asyncio.to_thread(
            lambda: supabase.table("disco_runs")
            .insert(
                {
                    "id": run_id,
                    "initiative_id": initiative_id,
                    "agent_type": agent_type,
                    "run_by": user_id,
                    "status": "running",
                    "metadata": {
                        "output_format": "unified",
                        "synthesis_mode": "multi_pass",
                        "passes": len(passes_config),
                    },
                }
            )
            .execute()
        )

        yield {"type": "status", "data": "Loading agent prompt..."}

        # Load agent prompt (same for all passes)
        agent_prompt = load_agent_prompt(agent_type)
        # Use matching meta agent: meta_consolidator for consolidator, meta_synthesizer for synthesizer
        meta_agent = "meta_consolidator" if agent_type == "consolidator" else "meta_synthesizer"
        meta_prompt = load_agent_prompt(meta_agent)

        yield {"type": "status", "data": "Building context..."}

        # Build context ONCE (shared across all passes)
        context = await build_agent_context(initiative_id, agent_type)
        full_prompt = build_full_prompt(agent_type, context)

        # Track document IDs used
        if document_ids:
            for doc_id in document_ids:
                await asyncio.to_thread(
                    lambda d=doc_id: supabase.table("disco_run_documents")
                    .insert({"run_id": run_id, "document_id": d})
                    .execute()
                )

        # Store intermediate outputs
        intermediate_outputs = []
        total_tokens = {"input_tokens": 0, "output_tokens": 0}

        # ===== Run 3 Sonnet passes =====
        for i, pass_config in enumerate(passes_config, 1):
            pass_label = pass_config["label"]
            pass_temp = pass_config["temperature"]
            pass_model = pass_config["model"]

            yield {"type": "status", "data": f"Pass {i}/3: {pass_label} (temp={pass_temp})..."}
            logger.info(f"[PURDY-MP] Starting Pass {i}: {pass_label} (temp={pass_temp}, model={pass_model})")

            pass_response = ""
            pass_status_messages = [f"Pass {i}/3: {random.choice(FUN_STATUS_MESSAGES)}" for _ in range(20)]

            try:
                async for item in collect_with_status_messages(
                    model=pass_model,
                    system_prompt=agent_prompt,
                    user_prompt=full_prompt,
                    status_messages=pass_status_messages,
                    status_interval=8.0,
                    temperature=pass_temp,
                    max_tokens=16000,
                ):
                    if item["type"] == "collect_complete":
                        pass_response = item["data"]["full_response"]
                        pass_usage = item["data"]["token_usage"]
                        if pass_usage:
                            total_tokens["input_tokens"] += pass_usage.get("input_tokens", 0)
                            total_tokens["output_tokens"] += pass_usage.get("output_tokens", 0)
                        logger.info(f"[PURDY-MP] Pass {i} complete: {len(pass_response)} chars")
                    else:
                        yield item

            except Exception as pass_error:
                logger.error(f"[PURDY-MP] Pass {i} failed: {pass_error}")
                raise

            intermediate_outputs.append(
                {
                    "pass_number": i,
                    "label": pass_label,
                    "temperature": pass_temp,
                    "model": pass_model,
                    "content": pass_response,
                    "char_count": len(pass_response),
                }
            )

            yield {
                "type": "pass_complete",
                "data": {"pass_number": i, "label": pass_label, "char_count": len(pass_response)},
            }

        # ===== Meta-synthesis with Opus =====
        yield {"type": "status", "data": "Meta-synthesis: combining best insights..."}
        logger.info("[PURDY-MP] Starting meta-synthesis with Opus")

        # Build meta-synthesis prompt with all 3 outputs
        meta_user_prompt = f"""# Multi-Pass Synthesis Task

You are performing meta-synthesis on three independent synthesis passes of the same initiative.

## Pass A (Conservative, temp=0.5)
{intermediate_outputs[0]["content"]}

---

## Pass B (Balanced, temp=0.7)
{intermediate_outputs[1]["content"]}

---

## Pass C (Exploratory, temp=0.85)
{intermediate_outputs[2]["content"]}

---

## Your Task

Create a unified synthesis that combines the best of all three passes. Follow the meta-synthesizer instructions to:
1. Lead with high-confidence findings (where all passes agree)
2. Resolve conflicts using the trust hierarchy (A > B > C for facts, C for insights)
3. Incorporate unique valuable insights from each pass
4. Include the Multi-Pass Synthesis Notes section at the end
"""

        # Stream the meta-synthesis output
        full_response = ""

        try:
            async for item in stream_with_status_messages(
                model=meta_config["model"],
                system_prompt=meta_prompt,
                user_prompt=meta_user_prompt,
                status_messages=FUN_STATUS_MESSAGES,
                status_interval=8.0,
                max_tokens=20000,
            ):
                if item["type"] == "stream_complete":
                    full_response = item["data"]["full_response"]
                    meta_tokens = item["data"]["token_usage"]
                    if meta_tokens:
                        total_tokens["input_tokens"] += meta_tokens.get("input_tokens", 0)
                        total_tokens["output_tokens"] += meta_tokens.get("output_tokens", 0)
                    logger.info(f"[PURDY-MP] Meta-synthesis complete: {len(full_response)} chars")
                else:
                    yield item

        except Exception as meta_error:
            logger.error(f"[PURDY-MP] Meta-synthesis failed: {meta_error}")
            raise

        # Extract synthesis notes from response (separated by delimiter)
        NOTES_DELIMITER = "---SYNTHESIS-NOTES-START---"
        main_content = full_response
        synthesis_notes = None

        if NOTES_DELIMITER in full_response:
            parts = full_response.split(NOTES_DELIMITER, 1)
            main_content = parts[0].strip()
            synthesis_notes = parts[1].strip() if len(parts) > 1 else None
            logger.info(f"[PURDY-MP] Extracted synthesis notes: {len(synthesis_notes or '')} chars")

        # Parse output (use main content only for structured parsing)
        parsed_output = parse_agent_output(agent_type, main_content)

        # Parse throughline resolution for requirements_generator
        mp_throughline_resolution = None
        if agent_type == "requirements_generator":
            mp_throughline_resolution = parse_throughline_resolution(main_content)

        # Get next version number
        version_result = await asyncio.to_thread(
            lambda: supabase.table("disco_outputs")
            .select("version")
            .eq("initiative_id", initiative_id)
            .eq("agent_type", agent_type)
            .order("version", desc=True)
            .limit(1)
            .execute()
        )
        next_version = 1
        if version_result.data:
            next_version = version_result.data[0]["version"] + 1

        # Store output with multi-pass metadata
        output_id = str(uuid4())

        # Prepare intermediate outputs for storage (truncate content for DB)
        intermediate_for_storage = []
        for io in intermediate_outputs:
            intermediate_for_storage.append(
                {
                    "pass_number": io["pass_number"],
                    "label": io["label"],
                    "temperature": io["temperature"],
                    "model": io["model"],
                    "char_count": io["char_count"],
                    "content": io["content"],  # Full content stored
                }
            )

        output_data = {
            "id": output_id,
            "run_id": run_id,
            "initiative_id": initiative_id,
            "agent_type": agent_type,
            "version": next_version,
            "title": parsed_output.get("title"),
            "recommendation": parsed_output.get("recommendation"),
            "tier_routing": parsed_output.get("tier_routing"),
            "confidence_level": parsed_output.get("confidence_level"),
            "executive_summary": parsed_output.get("executive_summary"),
            "content_markdown": main_content,  # Clean PRD without synthesis notes
            "content_structured": parsed_output,
            "output_format": "unified",
            "source_outputs": context.get("source_outputs", []),
            "synthesis_mode": "multi_pass",
            "synthesis_notes": synthesis_notes,  # Separate explainability report
            "intermediate_outputs": intermediate_for_storage,
            "throughline_resolution": mp_throughline_resolution,
        }

        logger.info(f"[PURDY-MP] Storing output - id: {output_id}, version: {next_version}")

        data_to_insert = dict(output_data)
        insert_result = await asyncio.to_thread(
            lambda: supabase.table("disco_outputs").insert(data_to_insert).execute()
        )

        if not insert_result.data:
            logger.error("[PURDY-MP] Insert returned no data!")
            raise Exception("Failed to insert output - no data returned")

        logger.info("[PURDY-MP] Insert SUCCESS")

        # Update run status
        await asyncio.to_thread(
            lambda: supabase.table("disco_runs")
            .update(
                {
                    "status": "completed",
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "token_usage": total_tokens,
                }
            )
            .eq("id", run_id)
            .execute()
        )

        # Update initiative status
        new_status = get_status_for_agent(agent_type)
        if new_status:
            await asyncio.to_thread(
                lambda: supabase.table("disco_initiatives")
                .update({"status": new_status})
                .eq("id", initiative_id)
                .execute()
            )

        yield {
            "type": "complete",
            "data": {
                "run_id": run_id,
                "output_id": output_id,
                "version": next_version,
                "parsed": parsed_output,
                "token_usage": total_tokens,
                "synthesis_mode": "multi_pass",
                "passes_completed": len(intermediate_outputs),
            },
        }

    except Exception as e:
        logger.error(f"[PURDY-MP] Multi-pass run failed: {e}")
        error_msg = str(e)

        await asyncio.to_thread(
            lambda: supabase.table("disco_runs")
            .update(
                {
                    "status": "failed",
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "error_message": error_msg,
                }
            )
            .eq("id", run_id)
            .execute()
        )

        yield {"type": "error", "data": error_msg}


async def get_run(run_id: str) -> Optional[Dict]:
    """Get a run record by ID."""
    try:
        result = await asyncio.to_thread(
            lambda: supabase.table("disco_runs").select("*, disco_outputs(*)").eq("id", run_id).single().execute()
        )
        return result.data
    except Exception as e:
        logger.error(f"Error fetching run {run_id}: {e}")
        return None


async def list_runs(initiative_id: str, limit: int = 20) -> List[Dict]:
    """List runs for an initiative."""
    try:
        result = await asyncio.to_thread(
            lambda: supabase.table("disco_runs")
            .select("*")
            .eq("initiative_id", initiative_id)
            .order("started_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []
    except Exception as e:
        logger.error(f"Error listing runs: {e}")
        return []
