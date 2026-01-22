"""
Opportunity Confidence Scoring Service

Evaluates how confident we are in an opportunity's scores based on
the completeness of available information. Higher confidence means
fewer unknowns and better-supported scoring decisions.

RUBRIC (100 points max):
- All 4 dimension scores provided: +20
- Has description: +10
- Has current_state: +8
- Has desired_state: +8
- Has owner stakeholder: +12
- Has department assigned: +5
- Has ROI indicators: +12
- Has justifications generated: +10
- Has source documentation: +8
- Has next_step defined: +5
- Has blockers documented (or none): +2

Confidence Levels:
- 80-100%: High confidence - scores are well-supported
- 60-79%: Moderate confidence - some assumptions made
- 40-59%: Low confidence - significant unknowns
- 0-39%: Very low confidence - mostly speculative
"""

import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)


# ============================================================================
# RUBRIC CONFIGURATION
# ============================================================================

RUBRIC = {
    # Field presence checks (field_name, points, question_if_missing)
    "scores_complete": {
        "points": 20,
        "question": "What scores would you assign for ROI potential, implementation effort, strategic alignment, and stakeholder readiness (1-5 scale)?",
    },
    "description": {
        "points": 10,
        "question": "What specific problem or opportunity does this initiative address?",
    },
    "current_state": {
        "points": 8,
        "question": "What is the current process, pain point, or baseline state?",
    },
    "desired_state": {
        "points": 8,
        "question": "What does success look like? What is the target end state?",
    },
    "owner_stakeholder_id": {
        "points": 12,
        "question": "Who is the business owner or champion for this initiative?",
    },
    "department": {
        "points": 5,
        "question": "Which department or business unit owns this opportunity?",
    },
    "roi_indicators": {
        "points": 12,
        "question": "What are the expected quantifiable benefits (time saved, cost reduction, revenue impact)?",
    },
    "has_justifications": {
        "points": 10,
        "question": "Can you provide rationale for each of the 4 dimension scores?",
    },
    "source_type": {
        "points": 8,
        "question": "What is the source of this opportunity (meeting transcript, research, stakeholder request)?",
    },
    "next_step": {
        "points": 5,
        "question": "What is the immediate next action to move this forward?",
    },
    "blockers_documented": {
        "points": 2,
        "question": "Are there any known technical, organizational, or resource constraints?",
    },
}

MAX_CONFIDENCE = sum(item["points"] for item in RUBRIC.values())


# ============================================================================
# SCORING FUNCTIONS
# ============================================================================

def evaluate_opportunity_confidence(opportunity: dict) -> Tuple[int, List[str]]:
    """
    Evaluate confidence in an opportunity's scores.

    Args:
        opportunity: Dict with opportunity fields

    Returns:
        Tuple of (confidence_score: int 0-100, questions: List[str])
    """
    points = 0
    questions = []

    # Check all 4 dimension scores are present
    scores = [
        opportunity.get("roi_potential"),
        opportunity.get("implementation_effort"),
        opportunity.get("strategic_alignment"),
        opportunity.get("stakeholder_readiness"),
    ]
    if all(s is not None for s in scores):
        points += RUBRIC["scores_complete"]["points"]
    else:
        questions.append(RUBRIC["scores_complete"]["question"])

    # Check description
    if opportunity.get("description"):
        points += RUBRIC["description"]["points"]
    else:
        questions.append(RUBRIC["description"]["question"])

    # Check current_state
    if opportunity.get("current_state"):
        points += RUBRIC["current_state"]["points"]
    else:
        questions.append(RUBRIC["current_state"]["question"])

    # Check desired_state
    if opportunity.get("desired_state"):
        points += RUBRIC["desired_state"]["points"]
    else:
        questions.append(RUBRIC["desired_state"]["question"])

    # Check owner
    if opportunity.get("owner_stakeholder_id"):
        points += RUBRIC["owner_stakeholder_id"]["points"]
    else:
        questions.append(RUBRIC["owner_stakeholder_id"]["question"])

    # Check department
    if opportunity.get("department"):
        points += RUBRIC["department"]["points"]
    else:
        questions.append(RUBRIC["department"]["question"])

    # Check ROI indicators (must have at least one)
    roi_indicators = opportunity.get("roi_indicators") or {}
    if roi_indicators and len(roi_indicators) > 0:
        points += RUBRIC["roi_indicators"]["points"]
    else:
        questions.append(RUBRIC["roi_indicators"]["question"])

    # Check justifications generated
    has_justifications = any([
        opportunity.get("opportunity_summary"),
        opportunity.get("roi_justification"),
        opportunity.get("effort_justification"),
        opportunity.get("alignment_justification"),
        opportunity.get("readiness_justification"),
    ])
    if has_justifications:
        points += RUBRIC["has_justifications"]["points"]
    else:
        questions.append(RUBRIC["has_justifications"]["question"])

    # Check source documentation
    if opportunity.get("source_type") or opportunity.get("source_notes"):
        points += RUBRIC["source_type"]["points"]
    else:
        questions.append(RUBRIC["source_type"]["question"])

    # Check next_step
    if opportunity.get("next_step"):
        points += RUBRIC["next_step"]["points"]
    else:
        questions.append(RUBRIC["next_step"]["question"])

    # Check blockers documented (get points if blockers array exists, even if empty)
    blockers = opportunity.get("blockers")
    if blockers is not None:  # Array exists (could be empty, meaning "reviewed, none found")
        points += RUBRIC["blockers_documented"]["points"]
    else:
        questions.append(RUBRIC["blockers_documented"]["question"])

    # Calculate percentage (0-100)
    confidence = round((points / MAX_CONFIDENCE) * 100)

    # Limit questions to top 5 most impactful (they're already ordered by rubric weight)
    questions = questions[:5]

    logger.debug(
        f"Opportunity confidence: {confidence}% ({points}/{MAX_CONFIDENCE} points), "
        f"{len(questions)} questions"
    )

    return confidence, questions


def get_confidence_level_description(confidence: int) -> str:
    """Get human-readable description of confidence level."""
    if confidence >= 80:
        return "High confidence - scores are well-supported"
    elif confidence >= 60:
        return "Moderate confidence - some assumptions made"
    elif confidence >= 40:
        return "Low confidence - significant unknowns"
    else:
        return "Very low confidence - mostly speculative"


# ============================================================================
# BATCH OPERATIONS
# ============================================================================

async def evaluate_all_opportunities(client_id: str) -> dict:
    """
    Evaluate confidence for all opportunities belonging to a client.

    Args:
        client_id: The client UUID

    Returns:
        Dict with counts and summary statistics
    """
    from database import get_supabase

    supabase = get_supabase()

    # Get all opportunities for client
    result = supabase.table("ai_opportunities") \
        .select("*") \
        .eq("client_id", client_id) \
        .execute()

    opportunities = result.data
    updated_count = 0
    errors = []

    for opp in opportunities:
        try:
            confidence, questions = evaluate_opportunity_confidence(opp)

            # Update the opportunity
            supabase.table("ai_opportunities").update({
                "scoring_confidence": confidence,
                "confidence_questions": questions,
            }).eq("id", opp["id"]).execute()

            updated_count += 1
            logger.info(
                f"Updated confidence for '{opp['title']}': {confidence}% "
                f"({len(questions)} questions)"
            )

        except Exception as e:
            errors.append({
                "id": opp["id"],
                "title": opp.get("title", "Unknown"),
                "error": str(e),
            })
            logger.error(f"Failed to evaluate {opp.get('title')}: {e}")

    # Calculate summary stats
    confidences = []
    for opp in opportunities:
        conf, _ = evaluate_opportunity_confidence(opp)
        confidences.append(conf)

    avg_confidence = round(sum(confidences) / len(confidences)) if confidences else 0

    return {
        "total": len(opportunities),
        "updated": updated_count,
        "failed": len(errors),
        "errors": errors if errors else None,
        "average_confidence": avg_confidence,
        "distribution": {
            "high": len([c for c in confidences if c >= 80]),
            "moderate": len([c for c in confidences if 60 <= c < 80]),
            "low": len([c for c in confidences if 40 <= c < 60]),
            "very_low": len([c for c in confidences if c < 40]),
        },
    }
