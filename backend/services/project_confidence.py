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
import os
from typing import List, Optional, Tuple

import anthropic

logger = logging.getLogger(__name__)

MODEL = "claude-haiku-4-5-20251001"


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


def _make_fallback_question(template: str, project: dict) -> str:
    """Make a basic question with project context. Used as fallback when LLM is unavailable.

    Args:
        template: Generic question template from rubric
        project: Project dict with title and other fields

    Returns:
        Question string with project title/department prepended
    """
    title = project.get("title", "this project")
    department = project.get("department")
    context_prefix = f'For "{title}"'
    if department:
        context_prefix += f" ({department})"
    context_prefix += ": "
    return f"{context_prefix}{template}"


async def _generate_context_aware_questions(
    missing_fields: List[str],
    project: dict,
    tasks: Optional[List[dict]] = None,
) -> List[str]:
    """Generate context-aware confidence questions using an LLM.

    Instead of generic templates, this uses the project's full context
    (description, current/desired state, tasks) to produce specific,
    actionable questions that reference what's already known.

    Args:
        missing_fields: List of rubric field keys that are missing
        project: Full project dict
        tasks: Optional list of task dicts linked to this project

    Returns:
        List of context-specific question strings
    """
    if not missing_fields:
        return []

    # Build context block from project fields
    context_parts = []
    title = project.get("title", "Unknown Project")
    context_parts.append(f"Project: {title}")
    if project.get("department"):
        context_parts.append(f"Department: {project['department']}")
    if project.get("description"):
        context_parts.append(f"Description: {project['description']}")
    if project.get("current_state"):
        context_parts.append(f"Current state: {project['current_state']}")
    if project.get("desired_state"):
        context_parts.append(f"Desired state: {project['desired_state']}")
    if project.get("next_step"):
        context_parts.append(f"Next step: {project['next_step']}")
    if project.get("project_summary"):
        context_parts.append(f"Summary: {project['project_summary']}")

    # Include scores if set
    scores = {}
    for field in ["roi_potential", "implementation_effort", "strategic_alignment", "stakeholder_readiness"]:
        val = project.get(field)
        if val is not None:
            scores[field] = val
    if scores:
        context_parts.append(f"Current scores: {scores}")

    # Include task context
    if tasks:
        task_lines = []
        for t in tasks[:10]:  # Cap at 10 to control token usage
            status = t.get("status", "unknown")
            task_title = t.get("title", "Untitled")
            notes = t.get("notes", "")
            line = f"- [{status}] {task_title}"
            if notes:
                line += f" -- {notes[:150]}"
            task_lines.append(line)
        context_parts.append(f"Related tasks:\n" + "\n".join(task_lines))

    project_context = "\n".join(context_parts)

    # Map missing fields to what info is needed
    field_descriptions = {
        "scores_complete": "dimension scores (ROI potential, implementation effort, strategic alignment, stakeholder readiness) with supporting evidence",
        "description": "a clear description of what this project does and what problem it solves",
        "current_state": "what the current process or situation looks like today",
        "desired_state": "what success looks like and what the target end state is",
        "owner_stakeholder_id": "a named business owner or champion who will drive this forward",
        "department": "which department or team owns this",
        "roi_indicators": "quantifiable expected benefits (hours saved, cost reduction, revenue impact)",
        "has_justifications": "rationale explaining why each dimension was scored the way it was",
        "source_type": "where this project originated (which meeting, stakeholder request, or discovery)",
        "next_step": "the immediate next action to move this forward",
        "blockers_documented": "any known blockers, risks, or dependencies",
    }

    missing_descriptions = [field_descriptions.get(f, f) for f in missing_fields]

    prompt = f"""You are a project analyst reviewing an AI project portfolio. Given the project context below, generate specific questions that would help fill in the missing information.

PROJECT CONTEXT:
{project_context}

MISSING INFORMATION NEEDED:
{chr(10).join(f"- {d}" for d in missing_descriptions)}

RULES:
- Generate exactly one question per missing item (max {len(missing_fields)} questions)
- Each question MUST reference specific details from the project context -- names, processes, metrics, or facts already known
- Questions should be actionable -- answerable by someone familiar with the project
- Do not ask about information that is already provided in the context
- Keep each question to 1-2 sentences
- Do not number the questions or add prefixes

Return ONLY the questions, one per line, no other text."""

    try:
        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        response = client.messages.create(
            model=MODEL,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        questions = [q.strip() for q in raw.split("\n") if q.strip()]
        # Ensure we don't return more questions than missing fields
        return questions[: len(missing_fields)]
    except Exception as e:
        logger.warning(f"LLM question generation failed for '{title}', falling back to templates: {e}")
        return [_make_fallback_question(RUBRIC[f]["question"], project) for f in missing_fields]


def _evaluate_rubric(project: dict) -> Tuple[int, int, List[str]]:
    """Evaluate the rubric and return points, confidence, and missing field keys.

    Args:
        project: Dict with project fields

    Returns:
        Tuple of (confidence_score: int 0-100, points: int, missing_fields: List[str])
    """
    points = 0
    missing_fields = []

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
        missing_fields.append("scores_complete")

    # Check description
    if project.get("description"):
        points += RUBRIC["description"]["points"]
    else:
        missing_fields.append("description")

    # Check current_state
    if project.get("current_state"):
        points += RUBRIC["current_state"]["points"]
    else:
        missing_fields.append("current_state")

    # Check desired_state
    if project.get("desired_state"):
        points += RUBRIC["desired_state"]["points"]
    else:
        missing_fields.append("desired_state")

    # Check owner
    if project.get("owner_stakeholder_id"):
        points += RUBRIC["owner_stakeholder_id"]["points"]
    else:
        missing_fields.append("owner_stakeholder_id")

    # Check department
    if project.get("department"):
        points += RUBRIC["department"]["points"]
    else:
        missing_fields.append("department")

    # Check ROI indicators (must have at least one)
    roi_indicators = project.get("roi_indicators") or {}
    if roi_indicators and len(roi_indicators) > 0:
        points += RUBRIC["roi_indicators"]["points"]
    else:
        missing_fields.append("roi_indicators")

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
        missing_fields.append("has_justifications")

    # Check source documentation
    if project.get("source_type") or project.get("source_notes"):
        points += RUBRIC["source_type"]["points"]
    else:
        missing_fields.append("source_type")

    # Check next_step
    if project.get("next_step"):
        points += RUBRIC["next_step"]["points"]
    else:
        missing_fields.append("next_step")

    # Check blockers documented (get points if blockers array exists, even if empty)
    blockers = project.get("blockers")
    if blockers is not None:  # Array exists (could be empty, meaning "reviewed, none found")
        points += RUBRIC["blockers_documented"]["points"]
    else:
        missing_fields.append("blockers_documented")

    confidence = round((points / MAX_CONFIDENCE) * 100)
    # Limit to top 5 most impactful (ordered by rubric weight since we check high-weight fields first)
    missing_fields = missing_fields[:5]

    logger.debug(f"Project confidence: {confidence}% ({points}/{MAX_CONFIDENCE} points), {len(missing_fields)} missing fields")

    return confidence, points, missing_fields


def evaluate_project_confidence(project: dict) -> Tuple[int, List[str]]:
    """Evaluate confidence in a project's scores (sync, uses fallback template questions).

    Used for batch operations and contexts where async/LLM calls are not practical.

    Args:
        project: Dict with project fields

    Returns:
        Tuple of (confidence_score: int 0-100, questions: List[str])
    """
    confidence, _, missing_fields = _evaluate_rubric(project)
    questions = [_make_fallback_question(RUBRIC[f]["question"], project) for f in missing_fields]
    return confidence, questions


async def evaluate_project_confidence_smart(
    project: dict,
    tasks: Optional[List[dict]] = None,
) -> Tuple[int, List[str]]:
    """Evaluate confidence with context-aware LLM-generated questions.

    Uses the project's full context (description, state, tasks) to generate
    specific, actionable questions instead of generic templates.

    Args:
        project: Dict with project fields
        tasks: Optional list of task dicts linked to this project

    Returns:
        Tuple of (confidence_score: int 0-100, questions: List[str])
    """
    confidence, _, missing_fields = _evaluate_rubric(project)

    if not missing_fields:
        return confidence, []

    questions = await _generate_context_aware_questions(missing_fields, project, tasks)
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
            logger.info(f"Updated confidence for '{project['title']}': {confidence}% ({len(questions)} questions)")

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
