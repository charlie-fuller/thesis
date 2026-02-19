"""Manifesto Compliance Scorer.

Lightweight pattern-matching scorer that detects manifesto principle signals
in agent responses. No LLM calls -- string matching only, microseconds latency.

Stores compliance data in existing metadata JSONB column. Informational only:
flags drift, does not block or rewrite responses.
"""

import re
from typing import Optional

from logger_config import get_logger

logger = get_logger(__name__)

# Compliance level thresholds
COMPLIANCE_THRESHOLDS = {
    "aligned": 0.60,  # >= 0.60
    "drifting": 0.30,  # >= 0.30 and < 0.60
    "misaligned": 0.0,  # < 0.30
}
DRIFT_ALERT_THRESHOLD = 0.25  # Hit rate below this triggers a drift alert
MIN_MESSAGES_FOR_EVALUATION = 3  # Minimum messages before evaluating an agent


def _get_compliance_level(score: float) -> str:
    """Classify a compliance score into a human-readable level.

    Args:
        score: Compliance score between 0.0 and 1.0.

    Returns:
        "aligned", "drifting", or "misaligned".
    """
    if score >= COMPLIANCE_THRESHOLDS["aligned"]:
        return "aligned"
    if score >= COMPLIANCE_THRESHOLDS["drifting"]:
        return "drifting"
    return "misaligned"


# Principle signal patterns: keywords/phrases that indicate an agent is
# engaging with each manifesto principle. Patterns are case-insensitive.
# Numbering matches manifesto.xml v1.1 (11 principles).
PRINCIPLE_SIGNALS: dict[str, list[str]] = {
    "P1_state_change": [
        r"state change",
        r"behavior\s+shift",
        r"behavior\s+change",
        r"mindset\s+change",
        r"what state are we trying to change",
        r"baseline.{0,20}target",
        r"measurable\s+shift",
        r"nothing\s+changed",
        r"didn.t change state",
        r"validation\s+criteria",
    ],
    "P2_problems_before_solutions": [
        r"problem\s+space",
        r"problems?\s+before\s+solutions?",
        r"what\s+problem\s+are\s+we\s+solving",
        r"do\s+nothing",
        r"doesn.t\s+need\s+ai",
        r"fix\s+the\s+process\s+first",
        r"right\s+problem",
    ],
    "P3_evidence_over_eloquence": [
        r"evidence",
        r"knowledge\s+base",
        r"data\s+shows",
        r"research\s+(shows|indicates|suggests)",
        r"according\s+to",
        r"documented\s+outcomes?",
        r"i\s+don.t\s+have\s+enough\s+information",
        r"based\s+on\s+(available\s+)?data",
        r"cite",
        r"source",
    ],
    "P4_know_your_output_type": [
        r"deterministic",
        r"non[\s-]?deterministic",
        r"calculation\s+(or|vs|versus)\s+interpretation",
        r"interpretation\s+(or|vs|versus)\s+calculation",
        r"what\s+kind\s+of\s+(answer|output)",
        r"probabilistic\s+summary",
        r"treating\s+it\s+as\s+(a\s+)?fact",
        r"false\s+(confidence|precision)",
        r"dangerous\s+middle",
        r"informed\s+interpretation",
        r"not\s+ground\s+truth",
    ],
    "P5_people_are_the_center": [
        r"people\s+(are\s+)?the\s+center",
        r"human\s+(experience|impact|cost)",
        r"employee\s+experience",
        r"fear\s+of\s+job\s+loss",
        r"dignity",
        r"champions?\s+burn\s+out",
        r"identity\s+threat",
        r"who\s+bears\s+the\s+costs?",
        r"meaningful\s+work",
        r"workforce\s+(transformation|impact)",
    ],
    "P6_humans_decide": [
        r"humans?\s+decide",
        r"human\s+decision\s+point",
        r"human\s+judgment",
        r"veto\s+power",
        r"your\s+(decision|call|choice)",
        r"recommend.{0,30}you\s+decide",
        r"input\s+to\s+human\s+decision",
        r"no\s+automation\s+by\s+default",
    ],
    "P7_multiple_perspectives": [
        r"multiple\s+perspectives?",
        r"whose\s+perspective\s+is\s+missing",
        r"different\s+(viewpoints?|perspectives?|lenses?)",
        r"finance.{0,20}security.{0,20}legal",
        r"from\s+a\s+\w+\s+perspective",
        r"stakeholder\s+perspectives?",
    ],
    "P8_context_and_brevity": [
        r"dig[\s-]?deeper",
        r"context\s+is\s+kindness",
        r"brevity\s+is\s+respect",
    ],
    "P9_guardrails_not_gates": [
        r"guardrails?.{0,10}not\s+gates?",
        r"enabling.{0,20}not\s+blocking",
        r"governance.{0,20}enables",
        r"structured\s+process",
        r"governance\s+questions?\s+answered",
    ],
    "P10_trace_connections": [
        r"second[\s-]?order\s+effects?",
        r"trace\s+the\s+connections?",
        r"ripple\s+effects?",
        r"downstream\s+impacts?",
        r"and\s+then\s+what\s+happens",
        r"system\s+dynamics?",
        r"feedback\s+loops?",
        r"unintended\s+consequences?",
    ],
    "P11_disco_methodology": [
        r"disco",
        r"discovery\s+phase",
        r"shared\s+methodology",
        r"insights?\s+phase",
        r"synthesis\s+phase",
        r"capabilities?\s+phase",
        r"the\s+questions\s+stay\s+the\s+same",
    ],
}

# Expected principle engagement per agent. Agents are expected to show
# signals for principles they champion or naturally engage with.
PRINCIPLE_RECOMMENDATIONS: dict[str, str] = {
    "P1_state_change": "Frame responses around what changed and why it matters, not just what is.",
    "P2_problems_before_solutions": "Lead with the problem statement before proposing solutions.",
    "P3_evidence_over_eloquence": "Cite specific data, metrics, or sources rather than general claims.",
    "P4_know_your_output_type": "Match output format to what the user needs (analysis, decision brief, action items).",
    "P5_people_are_the_center": "Center the response around stakeholder impact and human outcomes.",
    "P6_humans_decide": "Present options and tradeoffs rather than making the decision.",
    "P7_multiple_perspectives": "Consider and surface alternative viewpoints or counterarguments.",
    "P8_context_and_brevity": "Be concise -- provide enough context without over-explaining.",
    "P9_guardrails_not_gates": "Enable action with appropriate guardrails rather than blocking.",
    "P10_trace_connections": "Highlight relationships between concepts, stakeholders, or initiatives.",
    "P11_disco_methodology": "Follow the DISCO framework (Discovery > Intelligence > Synthesis > Convergence).",
}

AGENT_EXPECTED_PRINCIPLES: dict[str, list[str]] = {
    "strategist": [
        "P1_state_change",
        "P2_problems_before_solutions",
        "P4_know_your_output_type",
        "P5_people_are_the_center",
        "P6_humans_decide",
    ],
    "operator": [
        "P1_state_change",
        "P3_evidence_over_eloquence",
        "P5_people_are_the_center",
    ],
    "scholar": [
        "P1_state_change",
        "P3_evidence_over_eloquence",
        "P5_people_are_the_center",
    ],
    "architect": [
        "P1_state_change",
        "P3_evidence_over_eloquence",
        "P4_know_your_output_type",
        "P5_people_are_the_center",
        "P10_trace_connections",
    ],
    "atlas": [
        "P3_evidence_over_eloquence",
        "P11_disco_methodology",
    ],
    "pioneer": [
        "P3_evidence_over_eloquence",
        "P4_know_your_output_type",
        "P6_humans_decide",
        "P11_disco_methodology",
    ],
    "catalyst": [
        "P5_people_are_the_center",
        "P8_context_and_brevity",
    ],
    "nexus": [
        "P10_trace_connections",
        "P11_disco_methodology",
    ],
    "sage": [
        "P5_people_are_the_center",
        "P6_humans_decide",
    ],
    "oracle": [
        "P3_evidence_over_eloquence",
        "P4_know_your_output_type",
        "P6_humans_decide",
        "P10_trace_connections",
    ],
    "capital": [
        "P3_evidence_over_eloquence",
        "P4_know_your_output_type",
        "P6_humans_decide",
    ],
    "echo": [
        "P8_context_and_brevity",
    ],
    "kraken": [
        "P6_humans_decide",
        "P9_guardrails_not_gates",
    ],
    "reporter": [
        "P3_evidence_over_eloquence",
        "P8_context_and_brevity",
    ],
    "project_agent": [
        "P3_evidence_over_eloquence",
        "P8_context_and_brevity",
        "P11_disco_methodology",
    ],
    "compass": [
        "P3_evidence_over_eloquence",
        "P5_people_are_the_center",
        "P6_humans_decide",
    ],
}


def score_manifesto_compliance(
    response_text: str,
    agent_name: Optional[str] = None,
    source: Optional[str] = None,
) -> dict:
    """Score a response for manifesto principle signals.

    Args:
        response_text: The agent's response text to scan.
        agent_name: Optional agent name to compare against expected principles.

    Returns:
        Dict with score, detected signals, and gaps (if agent_name provided).
        Example: {
            "score": 0.75,
            "signals": ["P1_state_change", "P3_evidence_over_eloquence"],
            "gaps": ["P5_people_are_the_center"],
            "agent": "strategist"
        }
    """
    if not response_text or not isinstance(response_text, str):
        result = {"score": 0.0, "signals": [], "gaps": [], "agent": agent_name, "level": "misaligned"}
        if source:
            result["source"] = source
        return result

    text_lower = response_text.lower()
    detected_signals = []

    for principle_id, patterns in PRINCIPLE_SIGNALS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                detected_signals.append(principle_id)
                break

    # Calculate score against expected principles for this agent
    gaps = []
    score = 0.0

    clean_name = _normalize_agent_name(agent_name) if agent_name else None
    expected = AGENT_EXPECTED_PRINCIPLES.get(clean_name, []) if clean_name else []

    if expected:
        matched = [p for p in expected if p in detected_signals]
        gaps = [p for p in expected if p not in detected_signals]
        score = len(matched) / len(expected) if expected else 0.0
    elif detected_signals:
        # No expected config -- score based on total principle coverage
        score = len(detected_signals) / len(PRINCIPLE_SIGNALS)

    rounded_score = round(score, 2)
    result = {
        "score": rounded_score,
        "signals": detected_signals,
        "gaps": gaps,
        "agent": clean_name,
        "level": _get_compliance_level(rounded_score),
    }
    if source:
        result["source"] = source
    return result


def _normalize_agent_name(agent_name: str) -> str:
    """Normalize agent name to match config keys.

    Handles display names like 'The Strategist' -> 'strategist',
    and technical names like 'initiative_agent' -> 'initiative_agent'.
    """
    name = agent_name.lower().strip()
    # Remove common prefixes
    for prefix in ("the ", "agent "):
        if name.startswith(prefix):
            name = name[len(prefix) :]
    return name.strip()


# ============================================================================
# Semantic Evaluation Selection + Trigger
# ============================================================================

import asyncio
import random


def should_semantic_evaluate(regex_result: dict, agent_name: Optional[str] = None) -> bool:
    """Decide whether a response warrants semantic LLM evaluation.

    Triggers when:
    - 0 signals detected but agent has expected principles (likely gap)
    - 20% random sample of all scored messages (for calibration)
    """
    clean_name = _normalize_agent_name(agent_name) if agent_name else None
    expected = AGENT_EXPECTED_PRINCIPLES.get(clean_name, []) if clean_name else []

    if not regex_result.get("signals") and expected:
        return True

    if random.random() < 0.20:
        return True

    return False


def trigger_semantic_evaluation(
    response_text: str,
    agent_name: str,
    regex_result: dict,
    message_id: Optional[str] = None,
    table_name: str = "messages",
) -> None:
    """Fire-and-forget async semantic evaluation."""

    async def _evaluate_and_store():
        try:
            from services.manifesto_semantic_scorer import (
                _store_semantic_result,
                evaluate_semantic_compliance,
            )

            result = await evaluate_semantic_compliance(response_text, agent_name, regex_result)
            if result and message_id:
                await _store_semantic_result(message_id, table_name, result)
        except Exception as e:
            logger.error(f"Semantic evaluation background task failed: {e}")

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_evaluate_and_store())
    except RuntimeError:
        logger.debug("No running event loop for semantic evaluation, skipping")
