"""Manifesto Semantic Scorer.

Background LLM-based compliance evaluator that assesses behavioral alignment
with manifesto principles beyond surface keyword matching. Uses Claude Haiku
for fast, cheap evaluation in fire-and-forget async tasks.

Results are stored in the message row's metadata under the 'semantic_compliance' key.
"""

import asyncio
import os
import time
from typing import Optional

from logger_config import get_logger

logger = get_logger(__name__)

# Rate limiting: max evaluations per minute
_MAX_EVALUATIONS_PER_MINUTE = 10
_evaluation_timestamps: list[float] = []

# Principle labels for human-readable output
PRINCIPLE_LABELS = {
    "P1": "State Change Thinking",
    "P2": "Problems Before Solutions",
    "P3": "Evidence Over Eloquence",
    "P4": "Know Your Output Type",
    "P5": "People Are the Center",
    "P6": "Humans Decide",
    "P7": "Multiple Perspectives",
    "P8": "Context and Brevity",
    "P9": "Guardrails Not Gates",
    "P10": "Trace Connections",
    "P11": "DISCo Methodology",
}

EVALUATION_PROMPT = """You are evaluating an AI agent's response for behavioral alignment with an enterprise AI manifesto.

Agent: {agent_name}
Regex compliance score: {regex_score} (based on keyword detection)
Detected signals: {signals}
Gaps: {gaps}

Evaluate the following response for genuine behavioral alignment (not just keyword presence) with these principles:
- P1: State Change Thinking (defines measurable behavior shifts, not just outputs)
- P2: Problems Before Solutions (validates the problem before proposing solutions)
- P3: Evidence Over Eloquence (cites data/sources, admits uncertainty)
- P4: Know Your Output Type (distinguishes deterministic from non-deterministic output)
- P5: People Are the Center (considers human impact, dignity, workforce concerns)
- P6: Humans Decide (frames recommendations as input to human decisions)
- P7: Multiple Perspectives (considers different viewpoints)
- P8: Context and Brevity (appropriate detail level)
- P9: Guardrails Not Gates (enabling governance, not blocking)
- P10: Trace Connections (considers second-order effects)
- P11: DISCo Methodology (follows structured discovery process)

Response to evaluate:
---
{response_text}
---

Return a JSON object with:
- "semantic_score": float 0.0-1.0 (overall behavioral alignment)
- "principle_assessments": dict of principle_id -> {{"present": bool, "genuine": bool, "note": string}}
  Only include principles that are relevant to this agent's role.
- "behavioral_flags": list of strings noting any concerns (e.g., "keyword stuffing without substance", "false precision")

Respond with ONLY the JSON object, no markdown formatting."""


def _check_rate_limit() -> bool:
    """Check if we're within the rate limit for semantic evaluations.

    Returns True if evaluation is allowed, False if rate limited.
    """
    now = time.time()
    cutoff = now - 60

    # Remove timestamps older than 1 minute
    while _evaluation_timestamps and _evaluation_timestamps[0] < cutoff:
        _evaluation_timestamps.pop(0)

    if len(_evaluation_timestamps) >= _MAX_EVALUATIONS_PER_MINUTE:
        return False

    _evaluation_timestamps.append(now)
    return True


async def evaluate_semantic_compliance(
    response_text: str,
    agent_name: str,
    regex_result: dict,
) -> Optional[dict]:
    """Evaluate response for semantic manifesto compliance using LLM.

    Args:
        response_text: The agent's response text.
        agent_name: Agent name for context.
        regex_result: Result from score_manifesto_compliance() for context.

    Returns:
        Dict with semantic_score, principle_assessments, behavioral_flags,
        or None if rate limited or on error.
    """
    if not _check_rate_limit():
        logger.debug("Semantic compliance evaluation rate limited")
        return None

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set, skipping semantic evaluation")
        return None

    try:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=api_key)

        # Truncate response to avoid excessive token usage
        truncated = response_text[:2000] if len(response_text) > 2000 else response_text

        prompt = EVALUATION_PROMPT.format(
            agent_name=agent_name,
            regex_score=regex_result.get("score", 0.0),
            signals=", ".join(regex_result.get("signals", [])) or "none",
            gaps=", ".join(regex_result.get("gaps", [])) or "none",
            response_text=truncated,
        )

        message = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )

        import json

        raw = message.content[0].text.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()

        result = json.loads(raw)

        return {
            "semantic_score": float(result.get("semantic_score", 0.0)),
            "principle_assessments": result.get("principle_assessments", {}),
            "behavioral_flags": result.get("behavioral_flags", []),
        }

    except Exception as e:
        logger.error(f"Semantic compliance evaluation failed: {e}")
        return None


async def _store_semantic_result(
    message_id: str,
    table_name: str,
    result: dict,
) -> None:
    """Store semantic compliance result in the message's metadata.

    Updates the existing metadata JSONB column with a 'semantic_compliance' key.
    """
    try:
        from database import get_supabase

        supabase = get_supabase()

        # Fetch current metadata
        existing = await asyncio.to_thread(
            lambda: supabase.table(table_name).select("metadata").eq("id", message_id).single().execute()
        )

        metadata = (existing.data or {}).get("metadata") or {}
        metadata["semantic_compliance"] = result

        await asyncio.to_thread(
            lambda: supabase.table(table_name).update({"metadata": metadata}).eq("id", message_id).execute()
        )

        logger.debug(f"Semantic compliance stored for {table_name}/{message_id}")

    except Exception as e:
        logger.error(f"Failed to store semantic compliance result: {e}")
