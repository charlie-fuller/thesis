"""
PuRDy Executive Summary Generator (formerly Condenser)

Extracts decision-forcing elements from comprehensive outputs:
- The Leverage Point (single highest-impact intervention)
- The Feedback Loop (system dynamics diagram)
- The Decision Required (what, who, when)
- The First Action (Monday morning task)
- The Blocker (what stops this if not addressed)

v3.0: Repurposed from "make it shorter" to "extract what enables decisions"
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

# Use Sonnet for extraction (fast, good at summarization)
EXECUTIVE_SUMMARY_MODEL = os.environ.get("PURDY_MODEL_SONNET", "claude-sonnet-4-20250514")

EXECUTIVE_SUMMARY_PROMPT = """You are an Executive Summary Generator. Your job is NOT to make documents shorter - it's to EXTRACT the decision-forcing elements that enable action.

## What You Extract (In This Order)

### 1. THE LEVERAGE POINT
The single highest-impact intervention. Not a list of recommendations - THE one thing that would create the most change.

Format:
> **THE LEVERAGE POINT:** [One sentence, <30 words]

### 2. THE FEEDBACK LOOP
Why does this problem persist? Visualize the system dynamics as a Mermaid diagram.

Format:
```mermaid
flowchart LR
    A[Current State] --> B[Symptom]
    B --> C[Response]
    C --> D[Consequence]
    D --> A

    LP((LEVERAGE)) -.->|breaks here| B
```

### 3. THE DECISION REQUIRED
What specific decision needs to be made, by whom, and by when?

Format:
| Element | Value |
|---------|-------|
| **Decision** | [What needs deciding] |
| **Owner** | [Specific person/role] |
| **Deadline** | [Date or timeframe] |
| **If Delayed** | [Consequence of waiting] |

### 4. THE FIRST ACTION
What should happen Monday morning? Specific, actionable, owned.

Format:
| Action | Owner | By When | Done When |
|--------|-------|---------|-----------|
| [Specific task] | [Name] | [Date] | [Criteria] |

### 5. THE BLOCKER
What will stop this if not addressed?

Format:
> **THE BLOCKER:** [One sentence describing the main obstacle]
> **Mitigation:** [How to address it]

## Rules

1. **Extract, don't summarize** - Pull out the decision-forcing elements, don't compress everything proportionally
2. **One page max** - The entire output should fit on one page
3. **No fluff** - No "This document covers..." or "In summary..." - just the elements
4. **Preserve specifics** - Keep names, numbers, dates - these enable action
5. **If missing, say so** - If the source document doesn't have a clear leverage point or decision, note that as a gap

## Your Task

Extract the 5 decision-forcing elements from the following document. If any element is missing or unclear in the source, flag it as "[NOT FOUND - document lacks clear X]".
"""


async def generate_executive_summary(
    output_id: str,
    user_id: str
) -> AsyncGenerator[Dict, None]:
    """
    Generate an executive summary that extracts decision-forcing elements.

    NOT condensation (making shorter) - EXTRACTION (pulling out what enables decisions):
    - The Leverage Point
    - The Feedback Loop (Mermaid diagram)
    - The Decision Required
    - The First Action
    - The Blocker

    Args:
        output_id: UUID of the output to summarize
        user_id: User requesting summary

    Yields:
        Dict with type (status, content, complete) and data
    """
    logger.info(f"[EXEC-SUMMARY] Starting executive summary extraction for output {output_id}")

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
        logger.info(f"[EXEC-SUMMARY] Original content: {original_length} chars, agent: {original_agent_type}")

        yield {'type': 'status', 'data': 'Extracting decision-forcing elements...'}

        # Build the extraction prompt
        user_prompt = f"""# Document to Extract From

**Type:** {original_agent_type} output (v{original_version})

---

{original_content}

---

Extract the 5 decision-forcing elements (Leverage Point, Feedback Loop, Decision Required, First Action, Blocker) from this document. If any element is missing or unclear, flag it."""

        # Stream the summary output
        summary_response = ""
        chunk_count = 0

        with anthropic_client.messages.stream(
            model=EXECUTIVE_SUMMARY_MODEL,
            max_tokens=4000,  # Shorter output - 1 page max
            temperature=0.2,  # Low temp for faithful extraction
            system=EXECUTIVE_SUMMARY_PROMPT,
            messages=[{"role": "user", "content": user_prompt}]
        ) as stream:
            for text in stream.text_stream:
                summary_response += text
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

        summary_length = len(summary_response)
        extraction_ratio = round((summary_length / original_length) * 100, 1)

        logger.info(f"[EXEC-SUMMARY] Summary: {summary_length} chars ({extraction_ratio}% of original)")

        # Get next version number for executive summary outputs
        version_result = await _get_next_version(initiative_id, f"{original_agent_type}_executive")
        next_version = version_result

        # Store the executive summary as a new output with _executive suffix
        output_data = {
            'id': str(uuid4()),
            'run_id': None,  # Not from a run
            'initiative_id': initiative_id,
            'agent_type': f"{original_agent_type}_executive",
            'version': next_version,
            'title': f"Executive Summary: {result.get('title', 'Output')}",
            'recommendation': result.get('recommendation'),
            'tier_routing': result.get('tier_routing'),
            'confidence_level': result.get('confidence_level'),
            'content_markdown': summary_response,
            'content_structured': {
                'source_output_id': output_id,
                'source_agent_type': original_agent_type,
                'source_version': original_version,
                'original_length': original_length,
                'summary_length': summary_length,
                'extraction_ratio': extraction_ratio,
                'extraction_type': 'decision_forcing_elements'
            },
            'output_format': 'executive',
            'source_outputs': [{
                'agent_type': original_agent_type,
                'version': original_version,
                'id': output_id
            }]
        }

        insert_result = supabase.table('purdy_outputs').insert(output_data).execute()

        if not insert_result.data:
            logger.error("[EXEC-SUMMARY] Failed to store executive summary")
            yield {'type': 'error', 'data': 'Failed to store executive summary'}
            return

        yield {
            'type': 'complete',
            'data': {
                'output_id': output_data['id'],
                'version': next_version,
                'original_length': original_length,
                'summary_length': summary_length,
                'extraction_ratio': extraction_ratio,
                'token_usage': token_usage
            }
        }

    except Exception as e:
        logger.error(f"[EXEC-SUMMARY] Executive summary generation failed: {e}")
        yield {'type': 'error', 'data': str(e)}


# Alias for backwards compatibility
async def condense_output(output_id: str, user_id: str) -> AsyncGenerator[Dict, None]:
    """Backwards-compatible alias for generate_executive_summary."""
    async for event in generate_executive_summary(output_id, user_id):
        yield event


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
