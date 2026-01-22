"""
Opportunity Justification Generation Service

Generates AI-powered justifications for opportunity scores using Claude.
Produces:
- A 3-4 sentence summary of the opportunity
- A 3-4 sentence justification for each of the 4 scoring dimensions
- Confidence score (0-100) based on information completeness
- Questions that would raise confidence if answered
"""

import logging
import os
from typing import Optional
import anthropic

from database import get_supabase
from services.opportunity_confidence import evaluate_opportunity_confidence

logger = logging.getLogger(__name__)

# Use Haiku for fast, cost-effective generation
MODEL = "claude-3-5-haiku-20241022"


def _build_generation_prompt(opportunity: dict) -> str:
    """Build the prompt for generating justifications."""

    # Extract opportunity details
    title = opportunity.get("title", "Untitled")
    description = opportunity.get("description") or "No description provided"
    current_state = opportunity.get("current_state") or "Not specified"
    desired_state = opportunity.get("desired_state") or "Not specified"
    department = opportunity.get("department") or "General"

    # Scores
    roi = opportunity.get("roi_potential")
    effort = opportunity.get("implementation_effort")
    alignment = opportunity.get("strategic_alignment")
    readiness = opportunity.get("stakeholder_readiness")

    # ROI indicators if available
    roi_indicators = opportunity.get("roi_indicators") or {}
    roi_details = ""
    if roi_indicators:
        roi_details = "\nROI Indicators: " + ", ".join(
            f"{k}: {v}" for k, v in roi_indicators.items()
        )

    return f"""Analyze this AI opportunity and explain the scores.

OPPORTUNITY:
- Title: {title}
- Department: {department}
- Description: {description}
- Current State: {current_state}
- Desired State: {desired_state}{roi_details}

SCORES (1-5 scale, where 5 is best):
- ROI Potential: {roi if roi else 'Not scored'}/5 (revenue, cost savings, time impact)
- Implementation Ease: {effort if effort else 'Not scored'}/5 (5=plug-and-play, 1=very complex)
- Strategic Alignment: {alignment if alignment else 'Not scored'}/5 (fit with business priorities)
- Stakeholder Readiness: {readiness if readiness else 'Not scored'}/5 (champion, data, team eagerness)

Write brief justifications (2-4 sentences each) for:
1. What this opportunity is and its business impact
2. Why ROI potential is scored as shown
3. Why implementation ease is scored as shown
4. Why strategic alignment is scored as shown
5. Why stakeholder readiness is scored as shown

Use these section labels (parser expects this format):
OPPORTUNITY_SUMMARY: [text]
ROI_JUSTIFICATION: [text]
EFFORT_JUSTIFICATION: [text]
ALIGNMENT_JUSTIFICATION: [text]
READINESS_JUSTIFICATION: [text]"""


def _parse_generation_response(response_text: str) -> dict:
    """Parse the Claude response into structured fields."""
    result = {
        "opportunity_summary": None,
        "roi_justification": None,
        "effort_justification": None,
        "alignment_justification": None,
        "readiness_justification": None,
    }

    # Parse each section
    sections = {
        "OPPORTUNITY_SUMMARY:": "opportunity_summary",
        "ROI_JUSTIFICATION:": "roi_justification",
        "EFFORT_JUSTIFICATION:": "effort_justification",
        "ALIGNMENT_JUSTIFICATION:": "alignment_justification",
        "READINESS_JUSTIFICATION:": "readiness_justification",
    }

    for marker, field in sections.items():
        if marker in response_text:
            start = response_text.find(marker) + len(marker)
            # Find the next section or end of text
            end = len(response_text)
            for other_marker in sections:
                if other_marker != marker and other_marker in response_text[start:]:
                    potential_end = response_text.find(other_marker, start)
                    if potential_end < end:
                        end = potential_end

            value = response_text[start:end].strip()
            if value:
                result[field] = value

    return result


async def generate_opportunity_justifications(
    opportunity_id: str,
    client_id: Optional[str] = None,
) -> dict:
    """
    Generate justifications for an opportunity's scores.

    Args:
        opportunity_id: The opportunity UUID
        client_id: Optional client_id for verification

    Returns:
        Dict with the 5 justification fields

    Raises:
        ValueError: If opportunity not found
    """
    supabase = get_supabase()

    # Fetch opportunity
    query = supabase.table("ai_opportunities").select("*").eq("id", opportunity_id)
    if client_id:
        query = query.eq("client_id", client_id)

    result = query.single().execute()

    if not result.data:
        raise ValueError(f"Opportunity {opportunity_id} not found")

    opportunity = result.data

    # Build prompt and call Claude
    prompt = _build_generation_prompt(opportunity)

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text
        justifications = _parse_generation_response(response_text)

        # Update the opportunity in database with justifications
        supabase.table("ai_opportunities").update(justifications).eq("id", opportunity_id).execute()

        # Re-fetch the opportunity to get updated data for confidence calculation
        updated_result = supabase.table("ai_opportunities").select("*").eq("id", opportunity_id).single().execute()
        updated_opportunity = updated_result.data

        # Calculate and save confidence score
        confidence, questions = evaluate_opportunity_confidence(updated_opportunity)
        supabase.table("ai_opportunities").update({
            "scoring_confidence": confidence,
            "confidence_questions": questions,
        }).eq("id", opportunity_id).execute()

        logger.info(
            f"Generated justifications for opportunity {opportunity_id} "
            f"(confidence: {confidence}%)"
        )

        # Include confidence in return value
        justifications["scoring_confidence"] = confidence
        justifications["confidence_questions"] = questions

        return justifications

    except Exception as e:
        logger.error(f"Failed to generate justifications for {opportunity_id}: {e}")
        raise


async def generate_all_justifications(client_id: str) -> dict:
    """
    Generate justifications for all opportunities belonging to a client.

    Returns:
        Dict with counts of success/failure
    """
    supabase = get_supabase()

    # Get all opportunities for client
    result = supabase.table("ai_opportunities") \
        .select("id, title") \
        .eq("client_id", client_id) \
        .execute()

    opportunities = result.data
    success_count = 0
    failure_count = 0
    errors = []

    for opp in opportunities:
        try:
            await generate_opportunity_justifications(opp["id"], client_id)
            success_count += 1
            logger.info(f"Generated justifications for: {opp['title']}")
        except Exception as e:
            failure_count += 1
            errors.append({"id": opp["id"], "title": opp["title"], "error": str(e)})
            logger.error(f"Failed for {opp['title']}: {e}")

    return {
        "total": len(opportunities),
        "success": success_count,
        "failed": failure_count,
        "errors": errors if errors else None,
    }


async def regenerate_if_scores_changed(
    opportunity_id: str,
    old_scores: dict,
    new_scores: dict,
    client_id: Optional[str] = None,
) -> bool:
    """
    Check if scores changed and regenerate justifications if so.

    Args:
        opportunity_id: The opportunity UUID
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
        await generate_opportunity_justifications(opportunity_id, client_id)
        return True

    return False
