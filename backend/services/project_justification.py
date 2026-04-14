"""Project Justification Generation Service.

Generates AI-powered justifications for project scores using Claude.
Produces:
- A 3-4 sentence summary of the project
- A 3-4 sentence justification for each of the 4 scoring dimensions
- Confidence score (0-100) based on information completeness
- Questions that would raise confidence if answered
"""

import logging
import os
from typing import Optional

import anthropic

import pb_client as pb
from repositories import projects as projects_repo, tasks as tasks_repo
from services.project_confidence import evaluate_project_confidence_smart

logger = logging.getLogger(__name__)

# Use Haiku for fast, cost-effective generation
MODEL = "claude-haiku-4-5-20251001"


def _build_generation_prompt(project: dict) -> str:
    """Build the prompt for generating justifications."""
    # Extract project details
    title = project.get("title", "Untitled")
    description = project.get("description") or "No description provided"
    current_state = project.get("current_state") or "Not specified"
    desired_state = project.get("desired_state") or "Not specified"
    department = project.get("department") or "General"

    # Scores
    roi = project.get("roi_potential")
    effort = project.get("implementation_effort")
    alignment = project.get("strategic_alignment")
    readiness = project.get("stakeholder_readiness")

    # ROI indicators if available
    roi_indicators = project.get("roi_indicators") or {}
    roi_details = ""
    if roi_indicators:
        roi_details = "\nROI Indicators: " + ", ".join(f"{k}: {v}" for k, v in roi_indicators.items())

    has_all_scores = all(s is not None for s in [roi, effort, alignment, readiness])

    if has_all_scores:
        scores_block = f"""SCORES (1-5 scale, where 5 is best):
- ROI Potential: {roi}/5 (revenue, cost savings, time impact)
- Implementation Ease: {effort}/5 (5=plug-and-play, 1=very complex)
- Strategic Alignment: {alignment}/5 (fit with business priorities)
- Stakeholder Readiness: {readiness}/5 (champion, data, team eagerness)

Write brief justifications (2-4 sentences each) for:
1. What this project is and its business impact
2. Why ROI potential is scored as shown
3. Why implementation ease is scored as shown
4. Why strategic alignment is scored as shown
5. Why stakeholder readiness is scored as shown"""
    else:
        scores_block = f"""CURRENT SCORES (1-5 scale, where 5 is best):
- ROI Potential: {f"{roi}/5" if roi else "Not yet scored"} (revenue, cost savings, time impact)
- Implementation Ease: {f"{effort}/5" if effort else "Not yet scored"} (5=plug-and-play, 1=very complex)
- Strategic Alignment: {f"{alignment}/5" if alignment else "Not yet scored"} (fit with business priorities)
- Stakeholder Readiness: {f"{readiness}/5" if readiness else "Not yet scored"} (champion, data, team eagerness)

For any dimension marked "Not yet scored", suggest an appropriate score (1-5) based on the project details.

Write brief justifications (2-4 sentences each) for:
1. What this project is and its business impact
2. Why ROI potential deserves its score
3. Why implementation ease deserves its score
4. Why strategic alignment deserves its score
5. Why stakeholder readiness deserves its score"""

    return f"""Analyze this AI project and explain the scores.

PROJECT:
- Title: {title}
- Department: {department}
- Description: {description}
- Current State: {current_state}
- Desired State: {desired_state}{roi_details}

{scores_block}

Use these section labels (parser expects this format):
ROI_SCORE: [integer 1-5]
EFFORT_SCORE: [integer 1-5]
ALIGNMENT_SCORE: [integer 1-5]
READINESS_SCORE: [integer 1-5]
PROJECT_SUMMARY: [text]
ROI_JUSTIFICATION: [text]
EFFORT_JUSTIFICATION: [text]
ALIGNMENT_JUSTIFICATION: [text]
READINESS_JUSTIFICATION: [text]

Always include all score lines, even if confirming existing scores."""


def _parse_generation_response(response_text: str) -> dict:
    """Parse the Claude response into structured fields."""
    import re

    result = {
        "project_summary": None,
        "roi_justification": None,
        "effort_justification": None,
        "alignment_justification": None,
        "readiness_justification": None,
    }

    # Parse numeric scores
    score_map = {
        "ROI_SCORE:": "roi_potential",
        "EFFORT_SCORE:": "effort_score",
        "ALIGNMENT_SCORE:": "alignment_score",
        "READINESS_SCORE:": "readiness_score",
    }

    scores = {}
    for marker, field in score_map.items():
        if marker in response_text:
            start = response_text.find(marker) + len(marker)
            # Grab the rest of the line
            end = response_text.find("\n", start)
            if end == -1:
                end = len(response_text)
            value_str = response_text[start:end].strip()
            match = re.search(r"(\d)", value_str)
            if match:
                score = int(match.group(1))
                if 1 <= score <= 5:
                    scores[field] = score

    # Map parsed score fields to DB column names
    db_score_map = {
        "roi_potential": "roi_potential",
        "effort_score": "implementation_effort",
        "alignment_score": "strategic_alignment",
        "readiness_score": "stakeholder_readiness",
    }
    for parsed_field, db_field in db_score_map.items():
        if parsed_field in scores:
            result[db_field] = scores[parsed_field]

    # Parse text sections
    sections = {
        "PROJECT_SUMMARY:": "project_summary",
        "ROI_JUSTIFICATION:": "roi_justification",
        "EFFORT_JUSTIFICATION:": "effort_justification",
        "ALIGNMENT_JUSTIFICATION:": "alignment_justification",
        "READINESS_JUSTIFICATION:": "readiness_justification",
    }

    # Build list of all markers for boundary detection
    all_markers = list(score_map.keys()) + list(sections.keys())

    for marker, field in sections.items():
        if marker in response_text:
            start = response_text.find(marker) + len(marker)
            # Find the next section or end of text
            end = len(response_text)
            for other_marker in all_markers:
                if other_marker != marker and other_marker in response_text[start:]:
                    potential_end = response_text.find(other_marker, start)
                    if potential_end < end:
                        end = potential_end

            value = response_text[start:end].strip()
            if value:
                result[field] = value

    return result


async def generate_project_justifications(
    project_id: str,
    client_id: Optional[str] = None,
) -> dict:
    """Generate justifications for a project's scores.

    Args:
        project_id: The project UUID
        client_id: Optional client_id for verification

    Returns:
        Dict with the 5 justification fields

    Raises:
        ValueError: If project not found
    """
    # Fetch project
    project = projects_repo.get_project(project_id)
    if not project:
        raise ValueError(f"Project {project_id} not found")

    # Build prompt and call Claude
    prompt = _build_generation_prompt(project)

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    try:
        response = client.messages.create(model=MODEL, max_tokens=1024, messages=[{"role": "user", "content": prompt}])

        response_text = response.content[0].text
        justifications = _parse_generation_response(response_text)

        # Separate score fields from justification text fields
        score_fields = {"roi_potential", "implementation_effort", "strategic_alignment", "stakeholder_readiness"}
        update_data = {}

        for key, value in justifications.items():
            if value is None:
                continue
            if key in score_fields:
                # Only write AI-suggested scores if the project doesn't already have one
                existing_val = project.get(key)
                if existing_val is None:
                    update_data[key] = value
            else:
                update_data[key] = value

        # Update the project in database
        if update_data:
            projects_repo.update_project(project_id, update_data)

        # Re-fetch the project to get updated data for confidence calculation
        updated_project = projects_repo.get_project(project_id)

        # Calculate and save confidence score with context-aware questions
        # Fetch tasks for richer context
        tasks = []
        try:
            all_tasks = tasks_repo.list_tasks(source_project_id=project_id)
            tasks = all_tasks[:10]
        except Exception:
            pass
        confidence, questions = await evaluate_project_confidence_smart(updated_project, tasks)
        projects_repo.update_project(project_id, {
            "scoring_confidence": confidence,
            "confidence_questions": questions,
        })

        logger.info(f"Generated justifications for project {project_id} (confidence: {confidence}%)")

        # Include confidence in return value
        justifications["scoring_confidence"] = confidence
        justifications["confidence_questions"] = questions

        return justifications

    except Exception as e:
        logger.error(f"Failed to generate justifications for {project_id}: {e}")
        raise


async def generate_all_justifications(client_id: str) -> dict:
    """Generate justifications for all projects belonging to a client.

    Returns:
        Dict with counts of success/failure
    """
    # Get all projects for client
    projects = projects_repo.list_projects()
    success_count = 0
    failure_count = 0
    errors = []

    for project in projects:
        try:
            await generate_project_justifications(project["id"], client_id)
            success_count += 1
            logger.info(f"Generated justifications for: {project['title']}")
        except Exception as e:
            failure_count += 1
            errors.append({"id": project["id"], "title": project["title"], "error": str(e)})
            logger.error(f"Failed for {project['title']}: {e}")

    return {
        "total": len(projects),
        "success": success_count,
        "failed": failure_count,
        "errors": errors if errors else None,
    }


async def regenerate_if_scores_changed(
    project_id: str,
    old_scores: dict,
    new_scores: dict,
    client_id: Optional[str] = None,
) -> bool:
    """Check if scores changed and regenerate justifications if so.

    Args:
        project_id: The project UUID
        old_scores: Dict with roi_potential, implementation_effort, etc.
        new_scores: Dict with the new score values
        client_id: Optional client_id for verification

    Returns:
        True if justifications were regenerated, False otherwise
    """
    score_fields = [
        "roi_potential",
        "implementation_effort",
        "strategic_alignment",
        "stakeholder_readiness",
    ]

    # Check if any score changed
    changed = False
    for field in score_fields:
        old_val = old_scores.get(field)
        new_val = new_scores.get(field)
        if old_val != new_val:
            changed = True
            break

    if changed:
        await generate_project_justifications(project_id, client_id)
        return True

    return False
