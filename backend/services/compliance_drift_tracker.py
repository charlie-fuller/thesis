"""Compliance Drift Tracker.

In-memory, conversation-scoped tracking of manifesto compliance scores.
When an agent drifts (3+ consecutive low scores), generates a principle
reminder for injection into the system prompt.

No database table needed -- tracking is ephemeral and conversation-scoped.
"""

from collections import OrderedDict
from typing import Optional

from logger_config import get_logger

logger = get_logger(__name__)

# Configuration
DRIFT_WINDOW = 3  # Check last N scores
DRIFT_THRESHOLD = 0.30  # Avg below this triggers reminder
MAX_TRACKED_CONVERSATIONS = 500  # Prevent memory leak

# In-memory tracking: {conversation_id: {agent_name: [score1, score2, ...]}}
_conversation_drift: OrderedDict[str, dict[str, list[float]]] = OrderedDict()
# Track gaps per conversation/agent for reminder content
_conversation_gaps: dict[str, dict[str, list[list[str]]]] = {}

PRINCIPLE_LABELS = {
    "P1_state_change": "State Change (P1)",
    "P2_problems_before_solutions": "Problems Before Solutions (P2)",
    "P3_evidence_over_eloquence": "Evidence Over Eloquence (P3)",
    "P4_know_your_output_type": "Know Your Output Type (P4)",
    "P5_people_are_the_center": "People Are the Center (P5)",
    "P6_humans_decide": "Humans Decide (P6)",
    "P7_multiple_perspectives": "Multiple Perspectives (P7)",
    "P8_context_and_brevity": "Context and Brevity (P8)",
    "P9_guardrails_not_gates": "Guardrails Not Gates (P9)",
    "P10_trace_connections": "Trace the Connections (P10)",
    "P11_disco_methodology": "DISCo Methodology (P11)",
}


def record_compliance_score(
    conversation_id: str,
    agent_name: str,
    score: float,
    gaps: Optional[list[str]] = None,
) -> None:
    """Record a compliance score for an agent in a conversation.

    Evicts oldest conversations if over MAX_TRACKED_CONVERSATIONS.
    """
    if not conversation_id or not agent_name:
        return

    # Evict oldest if at capacity
    while len(_conversation_drift) >= MAX_TRACKED_CONVERSATIONS:
        evicted_id, _ = _conversation_drift.popitem(last=False)
        _conversation_gaps.pop(evicted_id, None)

    if conversation_id not in _conversation_drift:
        _conversation_drift[conversation_id] = {}
        _conversation_gaps[conversation_id] = {}

    if agent_name not in _conversation_drift[conversation_id]:
        _conversation_drift[conversation_id][agent_name] = []
        _conversation_gaps[conversation_id][agent_name] = []

    _conversation_drift[conversation_id][agent_name].append(score)
    _conversation_gaps[conversation_id][agent_name].append(gaps or [])


def get_compliance_reminder(agent_name: str, conversation_id: str) -> Optional[str]:
    """Return a compliance reminder if the agent is drifting, else None.

    Drifting = average of last DRIFT_WINDOW scores < DRIFT_THRESHOLD.
    """
    if not conversation_id or not agent_name:
        return None

    scores = _conversation_drift.get(conversation_id, {}).get(agent_name, [])

    if len(scores) < DRIFT_WINDOW:
        return None

    recent_scores = scores[-DRIFT_WINDOW:]
    avg = sum(recent_scores) / len(recent_scores)

    if avg >= DRIFT_THRESHOLD:
        return None

    # Collect unique gap principles from recent responses
    recent_gaps_lists = _conversation_gaps.get(conversation_id, {}).get(agent_name, [])
    recent_gaps = recent_gaps_lists[-DRIFT_WINDOW:]
    unique_gaps: list[str] = []
    seen = set()
    for gap_list in recent_gaps:
        for gap in gap_list:
            if gap not in seen:
                seen.add(gap)
                unique_gaps.append(gap)

    if not unique_gaps:
        return None

    gap_names = ", ".join(PRINCIPLE_LABELS.get(g, g) for g in unique_gaps)

    return (
        f"[COMPLIANCE NOTE] Your recent responses have not demonstrated these "
        f"expected principles: {gap_names}. Please actively incorporate them. "
        f"Briefly reflect on which principles you've been strong and weak on "
        f"before responding."
    )


def clear_conversation(conversation_id: str) -> None:
    """Clean up tracking data for an ended conversation."""
    _conversation_drift.pop(conversation_id, None)
    _conversation_gaps.pop(conversation_id, None)
