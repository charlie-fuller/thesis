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
DISCO_MODEL_OPUS = os.environ.get("DISCO_MODEL_OPUS") or os.environ.get(
    "PURDY_MODEL_OPUS", "claude-opus-4-5-20251101"
)

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
    # === Consolidated Agents (v2.0) ===
    "discovery_guide": "discovery-guide-v1.0.md",
    "insight_analyst": "insight-analyst-v1.0.md",
    "initiative_builder": "initiative-builder-v1.0.md",
    "requirements_generator": "requirements-generator-v1.0.md",
    # === Legacy Agents (backwards compatibility) ===
    "triage": "triage-v4.2.md",
    "discovery_prep": "discovery-prep-v1.0.md",
    "discovery_planner": "discovery-planner-v4.1.md",
    "coverage_tracker": "coverage-tracker-v4.1.md",
    "insight_extractor": "insight-extractor-v4.2.md",
    "consolidator": "consolidator-v4.2.md",
    "synthesizer": "synthesizer-v4.2.md",
    "strategist": "strategist-v1.0.md",
    "prd_generator": "prd-generator-v1.0.md",
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
        legacy = [
            {"type": agent_type, **info} for agent_type, info in LEGACY_AGENT_DESCRIPTIONS.items()
        ]
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
            response, usage = _collect_claude_response(
                model, system_prompt, user_prompt, temperature, max_tokens
            )
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


async def build_agent_context(
    initiative_id: str, agent_type: str, include_system_kb: bool = True
) -> Dict:
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
                output_parts.append(
                    f"\n\n=== Previous {output['agent_type']} Output (v{output['version']}) ===\n"
                )
                if output.get("recommendation"):
                    output_parts.append(f"Recommendation: {output['recommendation']}\n")
                if output.get("confidence_level"):
                    output_parts.append(f"Confidence: {output['confidence_level']}\n")
                output_parts.append(output["content_markdown"])
            context["previous_outputs"] = "\n".join(output_parts)

    context["source_outputs"] = source_outputs

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
            .select(
                "document_id, documents!inner(id, filename, title, obsidian_file_path, uploaded_by)"
            )
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
                title = (
                    doc.get("title")
                    or doc.get("filename")
                    or doc.get("obsidian_file_path")
                    or "Untitled"
                )
                content_parts.append(f"\n\n=== {title} ===\n")
                source = doc.get("obsidian_file_path") or doc.get("filename") or "Unknown"
                content_parts.append(f"Source: {source}\n")
                content_parts.append(content)

        return "\n".join(content_parts)

    except Exception as e:
        logger.error(f"Error fetching KB tagged documents: {e}")
        return ""


async def run_agent(
    initiative_id: str,
    agent_type: str,
    user_id: str,
    document_ids: Optional[List[str]] = None,
    output_format: str = "comprehensive",
    kb_folder: Optional[str] = None,
    kb_tags: Optional[List[str]] = None,
) -> AsyncGenerator[Dict, None]:
    """Execute an agent run with streaming response.

    Args:
        initiative_id: Initiative UUID
        agent_type: Type of agent to run
        user_id: User running the agent
        document_ids: Optional list of specific document IDs to use
        kb_folder: Optional KB folder path to include documents from (deprecated, use kb_tags)
        kb_tags: Optional list of KB tags to filter documents by (preferred, uses AND logic)

    Yields:
        Dict with type (status, content, complete) and data
    """
    logger.info("[PURDY] ========== Starting agent run ==========")
    logger.info(f"[PURDY] Agent type: '{agent_type}' (type: {type(agent_type).__name__})")
    logger.info(f"[PURDY] Initiative: {initiative_id}, User: {user_id}")
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
        await asyncio.to_thread(
            lambda: supabase.table("disco_runs")
            .insert(
                {
                    "id": run_id,
                    "initiative_id": initiative_id,
                    "agent_type": agent_type,
                    "run_by": user_id,
                    "status": "running",
                    "metadata": {"output_format": output_format},
                }
            )
            .execute()
        )

        yield {"type": "status", "data": "Loading agent prompt..."}

        # Load agent prompt
        agent_prompt = load_agent_prompt(agent_type)

        yield {"type": "status", "data": "Building context..."}

        # Build context
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

        # Build the full prompt with format guidance
        full_prompt = build_full_prompt(agent_type, context, output_format)

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

        # Store output
        output_id = str(uuid4())
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
            "content_markdown": full_response,
            "content_structured": parsed_output,
            "output_format": output_format,
            "source_outputs": context.get("source_outputs", []),
        }

        # Log the data being stored
        logger.info(
            f"[PURDY] Storing output - id: {output_id}, agent_type: {agent_type}, version: {next_version}"
        )
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

            logger.info(
                f"[PURDY] Insert SUCCESS: {insert_result.data[0].get('id') if insert_result.data else 'no id'}"
            )
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

        # Update initiative status based on agent type
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


def get_format_guidance(agent_type: str, output_format: str) -> str:
    """Return format-specific instructions for the agent."""
    if output_format == "comprehensive":
        return ""  # No additional guidance, use full prompt

    elif output_format == "executive":
        return """## OUTPUT FORMAT: EXECUTIVE SUMMARY

Provide a condensed executive summary (500-800 words max):
- Lead with the key decision/recommendation
- Include only the most critical 3-5 findings
- One table maximum for quantitative data
- Skip detailed analysis, methodology, and appendices
- End with clear next steps (3 max)

Use headers: Decision, Key Findings, Critical Risks, Next Steps
"""

    elif output_format == "brief":
        return """## OUTPUT FORMAT: BRIEF

Provide only the essential decision points (200-300 words max):
- Recommendation: [GO/NO-GO/CONDITIONAL] with one-line rationale
- Confidence: [HIGH/MEDIUM/LOW]
- Top 3 risks (one line each)
- Immediate next step

No tables, no analysis, no background. Just the decision.
"""

    return ""


def build_full_prompt(agent_type: str, context: Dict, output_format: str = "comprehensive") -> str:
    """Build the full user prompt for the agent."""
    parts = []

    # Add format guidance FIRST if not comprehensive
    format_guidance = get_format_guidance(agent_type, output_format)
    if format_guidance:
        parts.append(format_guidance)
        parts.append("\n")

    parts.append("# Initiative Context\n")

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

FIRST, detect the appropriate mode based on what exists:
- If no prior Discovery Guide outputs: Run TRIAGE mode
- If triage was GO but no session transcripts: Run PLANNING mode
- If session transcripts exist: Run COVERAGE mode

Then execute the appropriate mode as defined in your prompt.

For TRIAGE: Validate the problem worth solving with 4-criteria gate, provide GO/NO-GO/INVESTIGATE.
For PLANNING: Design discovery sessions for humans to execute (max 5 sessions, each with quantification questions).
For COVERAGE: Assess if we have enough to proceed to Insight Analyst, or need more discovery.""",
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

    parts.append("## Your Task\n")
    parts.append(
        agent_instructions.get(
            agent_type, "Please analyze this initiative and provide your assessment."
        )
    )

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

    # Extract recommendation (GO/NO-GO)
    rec_patterns = [
        r"(?:Recommendation|Decision)[:\s]+\*?\*?(GO|NO-GO|CONDITIONAL GO)\*?\*?",
        r"\*\*(GO|NO-GO|CONDITIONAL GO)\*\*",
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
    output_format: str = "comprehensive",
) -> AsyncGenerator[Dict, None]:
    """Execute a multi-pass agent run with meta-synthesis.

    Runs 3 Sonnet passes with varying temperatures, then feeds all outputs
    to Opus for meta-synthesis to produce a best-of-all unified output.

    Args:
        initiative_id: Initiative UUID
        agent_type: Type of agent to run (must be in MULTI_PASS_CONFIG["supported_agents"])
        user_id: User running the agent
        document_ids: Optional list of specific document IDs to use
        output_format: Output format (comprehensive, executive, brief)

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
                        "output_format": output_format,
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
        full_prompt = build_full_prompt(agent_type, context, output_format)

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
            logger.info(
                f"[PURDY-MP] Starting Pass {i}: {pass_label} (temp={pass_temp}, model={pass_model})"
            )

            pass_response = ""
            pass_status_messages = [
                f"Pass {i}/3: {random.choice(FUN_STATUS_MESSAGES)}" for _ in range(20)
            ]

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
            "output_format": output_format,
            "source_outputs": context.get("source_outputs", []),
            "synthesis_mode": "multi_pass",
            "synthesis_notes": synthesis_notes,  # Separate explainability report
            "intermediate_outputs": intermediate_for_storage,
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
            lambda: supabase.table("disco_runs")
            .select("*, disco_outputs(*)")
            .eq("id", run_id)
            .single()
            .execute()
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
