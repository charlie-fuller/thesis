"""
PuRDy Agent Service

Handles loading agent prompts, building context, and executing agent runs.
"""

import asyncio
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Optional
from uuid import uuid4

import anthropic
from database import get_supabase
from logger_config import get_logger

logger = get_logger(__name__)
supabase = get_supabase()

# Initialize Anthropic client
anthropic_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# Configuration
# For production: use bundled agents in backend/purdy_agents/
# For local dev: can override with PURDY_REPO_PATH env var
_BACKEND_DIR = Path(__file__).parent.parent.parent  # backend/
_BUNDLED_AGENTS_PATH = _BACKEND_DIR / "purdy_agents"
PURDY_REPO_PATH = os.environ.get("PURDY_REPO_PATH", "")
# Opus for high-quality PuRDy agent runs (may take longer but produces better analysis)
PURDY_AGENT_MODEL = os.environ.get("PURDY_AGENT_MODEL", "claude-opus-4-5-20251101")

# Agent file mappings (v2.8 for discovery planner, v2.7 for others)
# Note: paths are relative - "agents/" prefix used when PURDY_REPO_PATH is set,
# otherwise loads directly from bundled purdy_agents/ folder
AGENT_FILES = {
    "triage": "triage-v2.6.md",
    "discovery_planner": "discovery-planner-v2.8.md",
    "coverage_tracker": "coverage-tracker-v2.7.md",
    "synthesizer": "synthesizer-v2.7.md",
    "tech_evaluation": "tech-evaluation-v2.6.md"
}

# Methodology overview file (optional - may not exist in bundled version)
METHODOLOGY_FILE = "PuRDy-Instructions-v2.7.md"

# Agent descriptions for UI
AGENT_DESCRIPTIONS = {
    "triage": {
        "name": "Triage",
        "version": "v2.6",
        "description": "Quick GO/NO-GO assessment with tier routing and confidence-tagged ROI",
        "estimated_time": "5-10 minutes",
        "output_type": "triage_output"
    },
    "discovery_planner": {
        "name": "Discovery Planner",
        "version": "v2.8",
        "description": "Outcome-driven discovery with pre-meeting knowledge framework, quantification gates, and type-specific planning",
        "estimated_time": "10-15 minutes",
        "output_type": "discovery_output"
    },
    "coverage_tracker": {
        "name": "Coverage Tracker",
        "version": "v2.7",
        "description": "Track discovery coverage, flag gaps, and perform 3M waste diagnosis",
        "estimated_time": "10-15 minutes",
        "output_type": "coverage_output"
    },
    "synthesizer": {
        "name": "Synthesizer",
        "version": "v2.7",
        "description": "112%+ synthesis with persona-specific outputs (Finance/Engineering/Sales/Executive)",
        "estimated_time": "15-25 minutes",
        "output_type": "prd_output"
    },
    "tech_evaluation": {
        "name": "Tech Evaluation",
        "version": "v2.6",
        "description": "Platform recommendation with confidence-tagged estimates",
        "estimated_time": "10-15 minutes",
        "output_type": "tech_eval_output"
    }
}


def get_agent_types() -> List[Dict]:
    """Get list of available agent types with metadata."""
    return [
        {"type": agent_type, **info}
        for agent_type, info in AGENT_DESCRIPTIONS.items()
    ]


def load_agent_prompt(agent_type: str) -> str:
    """
    Load agent prompt from filesystem.

    Tries external PURDY_REPO_PATH first (for local dev), then falls back
    to bundled agents in backend/purdy_agents/ (for production).

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
    if PURDY_REPO_PATH:
        external_path = Path(PURDY_REPO_PATH) / "agents" / filename
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
    if PURDY_REPO_PATH:
        filepath = Path(PURDY_REPO_PATH) / METHODOLOGY_FILE
        if filepath.exists():
            return filepath.read_text()

    # Methodology file not bundled - return empty
    logger.warning(f"Methodology file not found: {METHODOLOGY_FILE}")
    return ""


async def build_agent_context(
    initiative_id: str,
    agent_type: str,
    include_system_kb: bool = True
) -> Dict:
    """
    Build context for an agent run.

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

    context = {
        'documents': '',
        'previous_outputs': '',
        'system_kb': '',
        'methodology': ''
    }

    # Get all initiative documents
    from .document_service import get_all_initiative_content
    context['documents'] = await get_all_initiative_content(initiative_id)

    # Get previous outputs (latest of each type)
    outputs_result = await asyncio.to_thread(
        lambda: supabase.table('purdy_outputs')
            .select('agent_type, version, content_markdown, recommendation, confidence_level')
            .eq('initiative_id', initiative_id)
            .order('created_at', desc=True)
            .execute()
    )

    if outputs_result.data:
        # Group by agent_type, keep only latest
        seen_types = set()
        previous_outputs = []
        for output in outputs_result.data:
            if output['agent_type'] not in seen_types:
                seen_types.add(output['agent_type'])
                previous_outputs.append(output)

        if previous_outputs:
            output_parts = []
            for output in previous_outputs:
                output_parts.append(f"\n\n=== Previous {output['agent_type']} Output (v{output['version']}) ===\n")
                if output.get('recommendation'):
                    output_parts.append(f"Recommendation: {output['recommendation']}\n")
                if output.get('confidence_level'):
                    output_parts.append(f"Confidence: {output['confidence_level']}\n")
                output_parts.append(output['content_markdown'])
            context['previous_outputs'] = '\n'.join(output_parts)

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
                kb_parts.append(chunk['content'])
            context['system_kb'] = '\n'.join(kb_parts)

    # Load methodology overview
    context['methodology'] = load_methodology_overview()

    return context


async def run_agent(
    initiative_id: str,
    agent_type: str,
    user_id: str,
    document_ids: Optional[List[str]] = None
) -> AsyncGenerator[Dict, None]:
    """
    Execute an agent run with streaming response.

    Args:
        initiative_id: Initiative UUID
        agent_type: Type of agent to run
        user_id: User running the agent
        document_ids: Optional list of specific document IDs to use

    Yields:
        Dict with type (status, content, complete) and data
    """
    logger.info(f"[PURDY] ========== Starting agent run ==========")
    logger.info(f"[PURDY] Agent type: '{agent_type}' (type: {type(agent_type).__name__})")
    logger.info(f"[PURDY] Initiative: {initiative_id}, User: {user_id}")

    # Validate agent_type immediately
    if not agent_type or agent_type not in AGENT_FILES:
        logger.error(f"[PURDY] Invalid agent_type: '{agent_type}'")
        raise ValueError(f"Invalid agent type: {agent_type}")

    run_id = str(uuid4())
    logger.info(f"[PURDY] Generated run_id: {run_id}")

    try:
        # Create run record
        await asyncio.to_thread(
            lambda: supabase.table('purdy_runs').insert({
                'id': run_id,
                'initiative_id': initiative_id,
                'agent_type': agent_type,
                'run_by': user_id,
                'status': 'running'
            }).execute()
        )

        yield {'type': 'status', 'data': 'Loading agent prompt...'}

        # Load agent prompt
        agent_prompt = load_agent_prompt(agent_type)

        yield {'type': 'status', 'data': 'Building context...'}

        # Build context
        context = await build_agent_context(initiative_id, agent_type)

        # Build the full prompt
        full_prompt = build_full_prompt(agent_type, context)

        yield {'type': 'status', 'data': 'Running agent...'}

        # Track document IDs used
        if document_ids:
            for doc_id in document_ids:
                await asyncio.to_thread(
                    lambda d=doc_id: supabase.table('purdy_run_documents').insert({
                        'run_id': run_id,
                        'document_id': d
                    }).execute()
                )

        # Stream Claude response
        full_response = ""
        token_usage = {}
        chunk_count = 0

        # Log context size before calling Claude
        system_chars = len(agent_prompt)
        prompt_chars = len(full_prompt)
        logger.info(f"[PURDY] Context size - system: {system_chars} chars, user: {prompt_chars} chars, total: {system_chars + prompt_chars} chars")
        logger.info(f"[PURDY] Estimated tokens: ~{(system_chars + prompt_chars) // 4}")
        logger.info(f"[PURDY] Calling Claude API with model: {PURDY_AGENT_MODEL}")

        try:
            with anthropic_client.messages.stream(
                model=PURDY_AGENT_MODEL,
                max_tokens=16000,
                system=agent_prompt,
                messages=[{"role": "user", "content": full_prompt}]
            ) as stream:
                for text in stream.text_stream:
                    full_response += text
                    chunk_count += 1
                    yield {'type': 'content', 'data': text}

                    # Send keepalive every 10 chunks to force proxy flush
                    if chunk_count % 10 == 0:
                        yield {'type': 'keepalive', 'data': ''}

                # Get final message for token usage
                final_message = stream.get_final_message()
                if final_message.usage:
                    token_usage = {
                        'input_tokens': final_message.usage.input_tokens,
                        'output_tokens': final_message.usage.output_tokens
                    }
                logger.info(f"[PURDY] Claude API completed. Tokens: {token_usage}")
        except Exception as claude_error:
            logger.error(f"[PURDY] Claude API error: {type(claude_error).__name__}: {claude_error}")
            raise

        # Parse output
        parsed_output = parse_agent_output(agent_type, full_response)

        # Get next version number
        version_result = await asyncio.to_thread(
            lambda: supabase.table('purdy_outputs')
                .select('version')
                .eq('initiative_id', initiative_id)
                .eq('agent_type', agent_type)
                .order('version', desc=True)
                .limit(1)
                .execute()
        )
        next_version = 1
        if version_result.data:
            next_version = version_result.data[0]['version'] + 1

        # Store output
        output_id = str(uuid4())
        output_data = {
            'id': output_id,
            'run_id': run_id,
            'initiative_id': initiative_id,
            'agent_type': agent_type,
            'version': next_version,
            'title': parsed_output.get('title'),
            'recommendation': parsed_output.get('recommendation'),
            'tier_routing': parsed_output.get('tier_routing'),
            'confidence_level': parsed_output.get('confidence_level'),
            'executive_summary': parsed_output.get('executive_summary'),
            'content_markdown': full_response,
            'content_structured': parsed_output
        }

        # Log the data being stored
        logger.info(f"[PURDY] Storing output - id: {output_id}, agent_type: {agent_type}, version: {next_version}")
        logger.info(f"[PURDY] Output data keys: {list(output_data.keys())}")
        logger.info(f"[PURDY] content_markdown length: {len(full_response)}")
        logger.info(f"[PURDY] Parsed title: {parsed_output.get('title')}, recommendation: {parsed_output.get('recommendation')}")

        # Use explicit copy to avoid any closure issues
        data_to_insert = dict(output_data)
        logger.info(f"[PURDY] Data to insert: agent_type={data_to_insert.get('agent_type')}, version={data_to_insert.get('version')}")

        try:
            insert_result = await asyncio.to_thread(
                lambda: supabase.table('purdy_outputs').insert(data_to_insert).execute()
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
            lambda: supabase.table('purdy_runs').update({
                'status': 'completed',
                'completed_at': datetime.now(timezone.utc).isoformat(),
                'token_usage': token_usage
            }).eq('id', run_id).execute()
        )

        # Update initiative status based on agent type
        new_status = get_status_for_agent(agent_type)
        if new_status:
            await asyncio.to_thread(
                lambda: supabase.table('purdy_initiatives')
                    .update({'status': new_status})
                    .eq('id', initiative_id)
                    .execute()
            )

        yield {
            'type': 'complete',
            'data': {
                'run_id': run_id,
                'output_id': output_id,
                'version': next_version,
                'parsed': parsed_output,
                'token_usage': token_usage
            }
        }

    except Exception as e:
        logger.error(f"Agent run failed: {e}")

        # Update run status to failed
        await asyncio.to_thread(
            lambda: supabase.table('purdy_runs').update({
                'status': 'failed',
                'completed_at': datetime.now(timezone.utc).isoformat(),
                'error_message': str(e)
            }).eq('id', run_id).execute()
        )

        yield {'type': 'error', 'data': str(e)}


def build_full_prompt(agent_type: str, context: Dict) -> str:
    """Build the full user prompt for the agent."""
    parts = []

    parts.append("# Initiative Context\n")

    if context.get('documents'):
        parts.append("## Source Documents\n")
        parts.append(context['documents'])
        parts.append("\n")

    if context.get('previous_outputs'):
        parts.append("## Previous Agent Outputs\n")
        parts.append(context['previous_outputs'])
        parts.append("\n")

    if context.get('system_kb'):
        parts.append("## Reference Knowledge Base\n")
        parts.append(context['system_kb'])
        parts.append("\n")

    # Agent-specific instructions
    agent_instructions = {
        'triage': "Please perform a triage analysis of this initiative. Provide a GO/NO-GO recommendation, tier routing, and confidence-tagged ROI assessment.",
        'discovery_planner': """Please create an outcome-driven discovery plan for this initiative.

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
        'coverage_tracker': "Please analyze the current discovery coverage. Identify gaps, assess readiness for synthesis, and perform 3M waste diagnosis if applicable.",
        'synthesizer': "Please synthesize all discovery findings into a comprehensive PRD. Include persona-specific briefs for Finance, Engineering, Sales, and Executive audiences.",
        'tech_evaluation': "Please evaluate technical platform options for this initiative. Provide recommendations with confidence-tagged effort estimates."
    }

    parts.append("## Your Task\n")
    parts.append(agent_instructions.get(agent_type, "Please analyze this initiative and provide your assessment."))

    return '\n'.join(parts)


def parse_agent_output(agent_type: str, raw_output: str) -> Dict:
    """
    Parse structured data from agent output.

    Args:
        agent_type: Type of agent
        raw_output: Raw markdown output

    Returns:
        Dict with extracted structured fields
    """
    parsed = {
        'title': None,
        'recommendation': None,
        'tier_routing': None,
        'confidence_level': None,
        'executive_summary': None,
        'sections': {}
    }

    # Extract title (first H1)
    title_match = re.search(r'^#\s+(.+)$', raw_output, re.MULTILINE)
    if title_match:
        parsed['title'] = title_match.group(1).strip()

    # Extract recommendation (GO/NO-GO)
    rec_patterns = [
        r'(?:Recommendation|Decision)[:\s]+\*?\*?(GO|NO-GO|CONDITIONAL GO)\*?\*?',
        r'\*\*(GO|NO-GO|CONDITIONAL GO)\*\*',
        r'^(GO|NO-GO|CONDITIONAL GO)$'
    ]
    for pattern in rec_patterns:
        rec_match = re.search(pattern, raw_output, re.IGNORECASE | re.MULTILINE)
        if rec_match:
            parsed['recommendation'] = rec_match.group(1).upper()
            break

    # Extract tier routing
    tier_patterns = [
        r'(?:Tier|Routing)[:\s]+\*?\*?(ELT|Solutions|Self-Serve|Tier \d)\*?\*?',
        r'\*\*(ELT|Solutions|Self-Serve)\*\*\s*(?:tier|routing)?'
    ]
    for pattern in tier_patterns:
        tier_match = re.search(pattern, raw_output, re.IGNORECASE)
        if tier_match:
            parsed['tier_routing'] = tier_match.group(1)
            break

    # Extract confidence level
    conf_patterns = [
        r'(?:Confidence)[:\s]+\*?\*?(HIGH|MEDIUM|LOW)\*?\*?',
        r'\*\*(HIGH|MEDIUM|LOW)\*\*\s*confidence'
    ]
    for pattern in conf_patterns:
        conf_match = re.search(pattern, raw_output, re.IGNORECASE)
        if conf_match:
            parsed['confidence_level'] = conf_match.group(1).upper()
            break

    # Extract executive summary (first paragraph after "Executive Summary" heading)
    summary_match = re.search(
        r'##?\s*Executive\s+Summary\s*\n+(.+?)(?=\n##|\n#|\Z)',
        raw_output,
        re.IGNORECASE | re.DOTALL
    )
    if summary_match:
        summary = summary_match.group(1).strip()
        # Take first paragraph
        first_para = summary.split('\n\n')[0]
        parsed['executive_summary'] = first_para[:1000]  # Limit length

    # Extract section headers
    section_matches = re.findall(r'^(#{1,3})\s+(.+)$', raw_output, re.MULTILINE)
    sections = []
    for level, title in section_matches:
        sections.append({
            'level': len(level),
            'title': title.strip()
        })
    parsed['sections'] = sections

    return parsed


def get_status_for_agent(agent_type: str) -> Optional[str]:
    """Get the initiative status to set after an agent completes."""
    status_map = {
        'triage': 'triaged',
        'discovery_planner': 'in_discovery',
        'coverage_tracker': 'in_discovery',
        'synthesizer': 'synthesized',
        'tech_evaluation': 'evaluated'
    }
    return status_map.get(agent_type)


async def get_run(run_id: str) -> Optional[Dict]:
    """Get a run record by ID."""
    try:
        result = await asyncio.to_thread(
            lambda: supabase.table('purdy_runs')
                .select('*, purdy_outputs(*)')
                .eq('id', run_id)
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
            lambda: supabase.table('purdy_runs')
                .select('*')
                .eq('initiative_id', initiative_id)
                .order('started_at', desc=True)
                .limit(limit)
                .execute()
        )
        return result.data or []
    except Exception as e:
        logger.error(f"Error listing runs: {e}")
        return []
