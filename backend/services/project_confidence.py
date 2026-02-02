"""Project Confidence Scoring Service.

Evaluates how confident we are in a project's scores based on
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
        "question": "What specific problem or project does this initiative address?",
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
        "question": "Which department or business unit owns this project?",
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
        "question": "What is the source of this project (meeting transcript, research, stakeholder request)?",
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


def _make_specific_question(template: str, project: dict) -> str:
    """Make a question specific to the project by including context.

    Args:
        template: Generic question template
        project: Project dict with title and other fields

    Returns:
        Context-specific question string
    """
    title = project.get("title", "this project")
    department = project.get("department")

    # Add project context to questions
    context_prefix = f'For "{title}"'
    if department:
        context_prefix += f" ({department})"
    context_prefix += ": "

    # Make questions specific based on their type
    if "scores would you assign" in template:
        return f"{context_prefix}What specific evidence supports the current scores for ROI potential ({project.get('roi_potential', 'unset')}), effort ({project.get('implementation_effort', 'unset')}), alignment ({project.get('strategic_alignment', 'unset')}), and readiness ({project.get('stakeholder_readiness', 'unset')})?"
    elif "problem or project" in template:
        return f"{context_prefix}What specific business problem does this solve, and how does it impact day-to-day operations?"
    elif "current process" in template or "baseline state" in template:
        return f"{context_prefix}How are things done today without this solution? What workarounds exist?"
    elif "success look like" in template or "target end state" in template:
        return f"{context_prefix}What measurable outcomes would indicate this was successful (e.g., 30% time reduction, $50K savings)?"
    elif "business owner" in template or "champion" in template:
        return (
            f"{context_prefix}Who has budget authority and will drive adoption of this initiative?"
        )
    elif "department or business unit" in template:
        return f'Which team or department would be the primary beneficiary and owner of "{title}"?'
    elif "quantifiable benefits" in template:
        return f"{context_prefix}What are the estimated hours saved per week, cost reduction, or revenue impact?"
    elif "rationale" in template:
        return f"{context_prefix}What specific factors led to scoring ROI as {project.get('roi_potential', 'N/A')} and effort as {project.get('implementation_effort', 'N/A')}?"
    elif "source of this project" in template:
        return f'Where did "{title}" originate? (e.g., specific meeting, stakeholder request, pain point observation)'
    elif "immediate next action" in template:
        return f"{context_prefix}What is the single most important next step to validate or advance this?"
    elif "constraints" in template:
        return f"{context_prefix}Are there any known blockers like budget limits, technical dependencies, or competing priorities?"

    # Default: just prepend context
    return f"{context_prefix}{template}"


def evaluate_project_confidence(project: dict) -> Tuple[int, List[str]]:
    """Evaluate confidence in a project's scores.

    Args:
        project: Dict with project fields

    Returns:
        Tuple of (confidence_score: int 0-100, questions: List[str])
    """
    points = 0
    questions = []

    # Check all 4 dimension scores are present
    scores = [
        project.get("roi_potential"),
        project.get("implementation_effort"),
        project.get("strategic_alignment"),
        project.get("stakeholder_readiness"),
    ]
    if all(s is not None for s in scores):
        points += RUBRIC["scores_complete"]["points"]
    else:
        questions.append(_make_specific_question(RUBRIC["scores_complete"]["question"], project))

    # Check description
    if project.get("description"):
        points += RUBRIC["description"]["points"]
    else:
        questions.append(_make_specific_question(RUBRIC["description"]["question"], project))

    # Check current_state
    if project.get("current_state"):
        points += RUBRIC["current_state"]["points"]
    else:
        questions.append(_make_specific_question(RUBRIC["current_state"]["question"], project))

    # Check desired_state
    if project.get("desired_state"):
        points += RUBRIC["desired_state"]["points"]
    else:
        questions.append(_make_specific_question(RUBRIC["desired_state"]["question"], project))

    # Check owner
    if project.get("owner_stakeholder_id"):
        points += RUBRIC["owner_stakeholder_id"]["points"]
    else:
        questions.append(
            _make_specific_question(RUBRIC["owner_stakeholder_id"]["question"], project)
        )

    # Check department
    if project.get("department"):
        points += RUBRIC["department"]["points"]
    else:
        questions.append(_make_specific_question(RUBRIC["department"]["question"], project))

    # Check ROI indicators (must have at least one)
    roi_indicators = project.get("roi_indicators") or {}
    if roi_indicators and len(roi_indicators) > 0:
        points += RUBRIC["roi_indicators"]["points"]
    else:
        questions.append(_make_specific_question(RUBRIC["roi_indicators"]["question"], project))

    # Check justifications generated
    has_justifications = any(
        [
            project.get("project_summary"),
            project.get("roi_justification"),
            project.get("effort_justification"),
            project.get("alignment_justification"),
            project.get("readiness_justification"),
        ]
    )
    if has_justifications:
        points += RUBRIC["has_justifications"]["points"]
    else:
        questions.append(_make_specific_question(RUBRIC["has_justifications"]["question"], project))

    # Check source documentation
    if project.get("source_type") or project.get("source_notes"):
        points += RUBRIC["source_type"]["points"]
    else:
        questions.append(_make_specific_question(RUBRIC["source_type"]["question"], project))

    # Check next_step
    if project.get("next_step"):
        points += RUBRIC["next_step"]["points"]
    else:
        questions.append(_make_specific_question(RUBRIC["next_step"]["question"], project))

    # Check blockers documented (get points if blockers array exists, even if empty)
    blockers = project.get("blockers")
    if blockers is not None:  # Array exists (could be empty, meaning "reviewed, none found")
        points += RUBRIC["blockers_documented"]["points"]
    else:
        questions.append(
            _make_specific_question(RUBRIC["blockers_documented"]["question"], project)
        )

    # Calculate percentage (0-100)
    confidence = round((points / MAX_CONFIDENCE) * 100)

    # Limit questions to top 5 most impactful (they're already ordered by rubric weight)
    questions = questions[:5]

    logger.debug(
        f"Project confidence: {confidence}% ({points}/{MAX_CONFIDENCE} points), "
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


async def evaluate_all_projects(client_id: str) -> dict:
    """Evaluate confidence for all projects belonging to a client.

    Args:
        client_id: The client UUID

    Returns:
        Dict with counts and summary statistics
    """
    from database import get_supabase

    supabase = get_supabase()

    # Get all projects for client
    result = supabase.table("ai_projects").select("*").eq("client_id", client_id).execute()

    projects = result.data
    updated_count = 0
    errors = []

    for project in projects:
        try:
            confidence, questions = evaluate_project_confidence(project)

            # Update the project
            supabase.table("ai_projects").update(
                {
                    "scoring_confidence": confidence,
                    "confidence_questions": questions,
                }
            ).eq("id", project["id"]).execute()

            updated_count += 1
            logger.info(
                f"Updated confidence for '{project['title']}': {confidence}% "
                f"({len(questions)} questions)"
            )

        except Exception as e:
            errors.append(
                {
                    "id": project["id"],
                    "title": project.get("title", "Unknown"),
                    "error": str(e),
                }
            )
            logger.error(f"Failed to evaluate {project.get('title')}: {e}")

    # Calculate summary stats
    confidences = []
    for project in projects:
        conf, _ = evaluate_project_confidence(project)
        confidences.append(conf)

    avg_confidence = round(sum(confidences) / len(confidences)) if confidences else 0

    return {
        "total": len(projects),
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
