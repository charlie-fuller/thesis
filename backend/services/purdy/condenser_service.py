"""
PuRDy Smart Brevity Condenser Service

Applies Chain of Density with Smart Brevity principles to condense
comprehensive outputs into scannable, executive-friendly versions.
"""

import os
from typing import AsyncGenerator, Dict, Optional
from uuid import uuid4

import anthropic
from database import get_supabase
from logger_config import get_logger

logger = get_logger(__name__)
supabase = get_supabase()

# Initialize Anthropic client
anthropic_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# Use Sonnet for condensation (fast, good at summarization)
CONDENSER_MODEL = os.environ.get("PURDY_MODEL_SONNET", "claude-sonnet-4-20250514")

SMART_BREVITY_PROMPT = """You are a Smart Brevity editor. Your job is to condense comprehensive analysis documents into scannable, executive-friendly versions while preserving ALL key information.

## Smart Brevity Principles

1. **Lead with the key insight** - The most important thing goes first, not background
2. **Bold the critical phrases** - 3-5 bolded terms per section for scanning
3. **Short paragraphs** - Maximum 3 sentences per paragraph
4. **Tables over prose** - Convert comparisons to tables whenever possible
5. **What's new, why it matters, what's next** - This is the fundamental structure
6. **Cut redundancy ruthlessly** - If you said it once, don't say it again

## Chain of Density Rules

You will condense in 3 passes:
1. **Pass 1:** Remove filler words, combine redundant points, tighten prose
2. **Pass 2:** Add entities that were implicit, make claims more specific
3. **Pass 3:** Final polish for readability while maintaining density

## Output Format

Produce a condensed version that is:
- 40-60% of the original length
- More scannable (more headers, bullets, tables)
- Same number of key insights/entities
- Boldface on critical terms
- No loss of decision-relevant information

Do NOT:
- Lose any quantified data points
- Remove stakeholder names or roles
- Skip risks or blockers
- Omit next steps or action items
- Add new information not in the original

## Your Task

Condense the following document using Smart Brevity principles and Chain of Density technique. Produce a single condensed output.
"""


async def condense_output(
    output_id: str,
    user_id: str
) -> AsyncGenerator[Dict, None]:
    """
    Apply Smart Brevity condensation to a PuRDy output.

    Uses Chain of Density technique with Smart Brevity principles
    to create a more scannable, executive-friendly version.

    Args:
        output_id: UUID of the output to condense
        user_id: User requesting condensation

    Yields:
        Dict with type (status, content, complete) and data
    """
    logger.info(f"[CONDENSER] Starting condensation for output {output_id}")

    try:
        # Fetch the original output
        yield {'type': 'status', 'data': 'Loading original output...'}

        result = await _fetch_output(output_id)
        if not result:
            yield {'type': 'error', 'data': 'Output not found'}
            return

        original_content = result['content_markdown']
        original_agent_type = result['agent_type']
        original_version = result['version']
        initiative_id = result['initiative_id']

        original_length = len(original_content)
        logger.info(f"[CONDENSER] Original content: {original_length} chars, agent: {original_agent_type}")

        yield {'type': 'status', 'data': 'Applying Smart Brevity condensation...'}

        # Build the condensation prompt
        user_prompt = f"""# Document to Condense

**Type:** {original_agent_type} output (v{original_version})
**Original Length:** {original_length} characters

---

{original_content}

---

Now apply Smart Brevity condensation. Produce a single condensed version that is 40-60% of the original length while preserving all key information."""

        # Stream the condensed output
        condensed_response = ""
        chunk_count = 0

        with anthropic_client.messages.stream(
            model=CONDENSER_MODEL,
            max_tokens=12000,
            temperature=0.3,  # Low temp for faithful condensation
            system=SMART_BREVITY_PROMPT,
            messages=[{"role": "user", "content": user_prompt}]
        ) as stream:
            for text in stream.text_stream:
                condensed_response += text
                chunk_count += 1
                yield {'type': 'content', 'data': text}

                if chunk_count % 10 == 0:
                    yield {'type': 'keepalive', 'data': ''}

            final_message = stream.get_final_message()
            token_usage = {}
            if final_message.usage:
                token_usage = {
                    'input_tokens': final_message.usage.input_tokens,
                    'output_tokens': final_message.usage.output_tokens
                }

        condensed_length = len(condensed_response)
        compression_ratio = round((1 - condensed_length / original_length) * 100, 1)

        logger.info(f"[CONDENSER] Condensed: {condensed_length} chars ({compression_ratio}% reduction)")

        # Get next version number for condensed outputs
        version_result = await _get_next_version(initiative_id, f"{original_agent_type}_condensed")
        next_version = version_result

        # Store the condensed output as a new output with _condensed suffix
        output_data = {
            'id': str(uuid4()),
            'run_id': None,  # Not from a run
            'initiative_id': initiative_id,
            'agent_type': f"{original_agent_type}_condensed",
            'version': next_version,
            'title': f"Condensed: {result.get('title', 'Output')}",
            'recommendation': result.get('recommendation'),
            'tier_routing': result.get('tier_routing'),
            'confidence_level': result.get('confidence_level'),
            'content_markdown': condensed_response,
            'content_structured': {
                'source_output_id': output_id,
                'source_agent_type': original_agent_type,
                'source_version': original_version,
                'original_length': original_length,
                'condensed_length': condensed_length,
                'compression_ratio': compression_ratio
            },
            'output_format': 'condensed',
            'source_outputs': [{
                'agent_type': original_agent_type,
                'version': original_version,
                'id': output_id
            }]
        }

        insert_result = supabase.table('purdy_outputs').insert(output_data).execute()

        if not insert_result.data:
            logger.error("[CONDENSER] Failed to store condensed output")
            yield {'type': 'error', 'data': 'Failed to store condensed output'}
            return

        yield {
            'type': 'complete',
            'data': {
                'output_id': output_data['id'],
                'version': next_version,
                'original_length': original_length,
                'condensed_length': condensed_length,
                'compression_ratio': compression_ratio,
                'token_usage': token_usage
            }
        }

    except Exception as e:
        logger.error(f"[CONDENSER] Condensation failed: {e}")
        yield {'type': 'error', 'data': str(e)}


async def _fetch_output(output_id: str) -> Optional[Dict]:
    """Fetch an output by ID."""
    try:
        result = supabase.table('purdy_outputs').select('*').eq('id', output_id).single().execute()
        return result.data
    except Exception as e:
        logger.error(f"Error fetching output {output_id}: {e}")
        return None


async def _get_next_version(initiative_id: str, agent_type: str) -> int:
    """Get the next version number for an agent type."""
    try:
        result = supabase.table('purdy_outputs').select('version').eq('initiative_id', initiative_id).eq('agent_type', agent_type).order('version', desc=True).limit(1).execute()
        if result.data:
            return result.data[0]['version'] + 1
        return 1
    except Exception:
        return 1
