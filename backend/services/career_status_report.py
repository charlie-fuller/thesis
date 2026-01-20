"""
Career Status Report Generation Service

Generates AI-powered career status reports for the Compass agent.
Uses a 5-dimension rubric to assess career performance:
- Strategic Impact (25%)
- Execution Quality (25%)
- Relationship Building (20%)
- Growth Mindset (15%)
- Leadership Presence (15%)

Pulls context from:
- KB documents tagged for Compass
- Mem0 memories (when available)
"""

import logging
import os
from datetime import date
from typing import Optional
from uuid import UUID

import anthropic

from database import get_supabase

logger = logging.getLogger(__name__)

# Use Sonnet for higher quality assessment (more nuanced than Haiku)
MODEL = "claude-sonnet-4-20250514"

# Default career rubric with level descriptors
DEFAULT_RUBRIC = {
    "strategic_impact": {
        "name": "Strategic Impact",
        "weight": 25,
        "description": "How well does your work align with and advance company priorities?",
        "levels": {
            5: "Exceptional: Work directly drives top-3 company priorities. Recognized by leadership as strategic contributor.",
            4: "Strong: Consistently connects work to strategic objectives. Proactively identifies alignment opportunities.",
            3: "Solid: Work supports team/department goals that ladder to strategy. Understands the 'why' behind priorities.",
            2: "Developing: Work is task-focused with occasional strategic connection. Needs guidance on priority alignment.",
            1: "Foundational: Work is reactive/ticket-driven. Limited awareness of strategic context.",
        },
    },
    "execution_quality": {
        "name": "Execution Quality",
        "weight": 25,
        "description": "How consistently do you deliver on commitments with quality?",
        "levels": {
            5: "Exceptional: Exceeds expectations consistently. Proactively manages risks. Zero rework needed.",
            4: "Strong: Meets commitments reliably. Communicates blockers early. High-quality output.",
            3: "Solid: Generally delivers on time. Occasional misses with good communication. Acceptable quality.",
            2: "Developing: Inconsistent delivery. Needs reminders/follow-up. Quality varies.",
            1: "Foundational: Frequently misses deadlines. Requires significant rework.",
        },
    },
    "relationship_building": {
        "name": "Relationship Building",
        "weight": 20,
        "description": "How effectively do you build and maintain professional relationships?",
        "levels": {
            5: "Exceptional: Trusted advisor to stakeholders. Expands network cross-functionally. Resolves conflicts.",
            4: "Strong: Strong relationships with key stakeholders. Proactively builds new connections.",
            3: "Solid: Good working relationships with immediate team/stakeholders. Responsive and collaborative.",
            2: "Developing: Limited relationships outside immediate team. Reactive in communication.",
            1: "Foundational: Isolated. Minimal stakeholder engagement.",
        },
    },
    "growth_mindset": {
        "name": "Growth Mindset",
        "weight": 15,
        "description": "How actively do you pursue learning and development?",
        "levels": {
            5: "Exceptional: Actively seeking stretch assignments. Teaches others. Visible skill growth.",
            4: "Strong: Regularly requests feedback. Applies learnings. Expanding skill set.",
            3: "Solid: Open to feedback. Participates in learning opportunities. Steady growth.",
            2: "Developing: Accepts feedback but limited action. Occasional skill development.",
            1: "Foundational: Resistant to feedback. No visible growth effort.",
        },
    },
    "leadership_presence": {
        "name": "Leadership Presence",
        "weight": 15,
        "description": "How visible and influential are you beyond your immediate role?",
        "levels": {
            5: "Exceptional: Recognized thought leader. Drives initiatives. Shapes decisions beyond team.",
            4: "Strong: Speaks up in meetings. Contributes to org-wide discussions. Mentors others.",
            3: "Solid: Contributes in team settings. Occasionally shares perspective in broader forums.",
            2: "Developing: Mostly silent in meetings. Limited visibility beyond immediate team.",
            1: "Foundational: Avoids visibility. No influence beyond assigned tasks.",
        },
    },
}


async def get_career_context(user_id: str, client_id: str) -> dict:
    """
    Gather career-related context from KB and memories.

    Returns:
        Dict with kb_documents, memories, and stakeholder_context
    """
    supabase = get_supabase()
    context = {
        "kb_documents": [],
        "memories": [],
        "stakeholder_context": None,
    }

    try:
        # Get Compass agent ID
        agent_result = (
            supabase.table("agents")
            .select("id")
            .ilike("name", "%compass%")
            .single()
            .execute()
        )
        compass_agent_id = agent_result.data.get("id") if agent_result.data else None

        # Get KB documents tagged for Compass
        # Note: Fetch agent_knowledge_base links first, then fetch documents separately
        # to avoid nested filter issues with Supabase PostgREST
        if compass_agent_id:
            # Step 1: Get document IDs linked to Compass agent
            kb_links_result = (
                supabase.table("agent_knowledge_base")
                .select("document_id, relevance_score")
                .eq("agent_id", compass_agent_id)
                .order("relevance_score", desc=True)
                .limit(20)  # Fetch more, filter by client later
                .execute()
            )

            if kb_links_result.data:
                doc_ids = [link["document_id"] for link in kb_links_result.data]
                relevance_map = {
                    link["document_id"]: link["relevance_score"]
                    for link in kb_links_result.data
                }

                # Step 2: Fetch documents by ID with client filter
                docs_result = (
                    supabase.table("documents")
                    .select("id, title, content")
                    .in_("id", doc_ids)
                    .eq("client_id", client_id)
                    .execute()
                )

                # Sort by relevance and limit to 10
                docs_with_relevance = []
                for doc in docs_result.data or []:
                    if doc.get("content"):
                        docs_with_relevance.append(
                            {
                                "title": doc.get("title", "Untitled"),
                                "content": doc.get("content", "")[:2000],
                                "relevance": relevance_map.get(doc["id"], 0),
                            }
                        )

                # Sort by relevance and take top 10
                docs_with_relevance.sort(key=lambda x: x["relevance"], reverse=True)
                context["kb_documents"] = docs_with_relevance[:10]

    except Exception as e:
        logger.warning(f"Error fetching career context: {e}")
        # Continue with empty context rather than failing completely

    # TODO: Add Mem0 memory retrieval when fully implemented
    # For now, memories will be empty

    return context


def _build_assessment_prompt(context: dict) -> str:
    """Build the prompt for career status assessment."""

    # Format rubric dimensions
    rubric_text = "CAREER ASSESSMENT RUBRIC:\n\n"
    for key, dim in DEFAULT_RUBRIC.items():
        rubric_text += f"### {dim['name']} (Weight: {dim['weight']}%)\n"
        rubric_text += f"{dim['description']}\n"
        for level, desc in sorted(dim["levels"].items(), reverse=True):
            rubric_text += f"  Level {level}: {desc}\n"
        rubric_text += "\n"

    # Format KB context
    kb_context = ""
    if context.get("kb_documents"):
        kb_context = "\n\nCAREER DOCUMENTS (from Knowledge Base):\n"
        for i, doc in enumerate(context["kb_documents"], 1):
            kb_context += f"\n--- Document {i}: {doc['title']} ---\n"
            kb_context += doc["content"][:1500]
            kb_context += "\n"

    # Format memory context
    memory_context = ""
    if context.get("memories"):
        memory_context = "\n\nRECENT CAREER MEMORIES:\n"
        for mem in context["memories"]:
            memory_context += f"- {mem}\n"

    return f"""You are Compass, a career coaching agent. Generate a comprehensive career status report based on the rubric and available context.

{rubric_text}
{kb_context}
{memory_context}

Based on the available information, assess career performance across all 5 dimensions. If specific evidence is limited, make reasonable inferences but note the confidence level.

Generate the following:

1. EXECUTIVE_SUMMARY: A 2-3 sentence overall assessment of career trajectory and performance.

2. For each dimension, provide:
   - SCORE (1-5 based on rubric levels)
   - JUSTIFICATION (2-3 sentences explaining the score with specific evidence if available)

3. AREAS_OF_STRENGTH: List 2-3 specific strengths demonstrated
4. GROWTH_OPPORTUNITIES: List 2-3 areas for development
5. RECOMMENDED_ACTIONS: List 2-3 concrete next steps

Format your response EXACTLY as:
EXECUTIVE_SUMMARY: [your text]

STRATEGIC_IMPACT_SCORE: [1-5]
STRATEGIC_IMPACT_JUSTIFICATION: [your text]

EXECUTION_QUALITY_SCORE: [1-5]
EXECUTION_QUALITY_JUSTIFICATION: [your text]

RELATIONSHIP_BUILDING_SCORE: [1-5]
RELATIONSHIP_BUILDING_JUSTIFICATION: [your text]

GROWTH_MINDSET_SCORE: [1-5]
GROWTH_MINDSET_JUSTIFICATION: [your text]

LEADERSHIP_PRESENCE_SCORE: [1-5]
LEADERSHIP_PRESENCE_JUSTIFICATION: [your text]

AREAS_OF_STRENGTH: [item1] | [item2] | [item3]
GROWTH_OPPORTUNITIES: [item1] | [item2] | [item3]
RECOMMENDED_ACTIONS: [item1] | [item2] | [item3]"""


def _parse_assessment_response(response_text: str) -> dict:
    """Parse the Claude response into structured fields."""
    result = {
        "executive_summary": None,
        "strategic_impact": None,
        "strategic_impact_justification": None,
        "execution_quality": None,
        "execution_quality_justification": None,
        "relationship_building": None,
        "relationship_building_justification": None,
        "growth_mindset": None,
        "growth_mindset_justification": None,
        "leadership_presence": None,
        "leadership_presence_justification": None,
        "areas_of_strength": [],
        "growth_opportunities": [],
        "recommended_actions": [],
    }

    # Parse text fields
    text_sections = {
        "EXECUTIVE_SUMMARY:": "executive_summary",
        "STRATEGIC_IMPACT_JUSTIFICATION:": "strategic_impact_justification",
        "EXECUTION_QUALITY_JUSTIFICATION:": "execution_quality_justification",
        "RELATIONSHIP_BUILDING_JUSTIFICATION:": "relationship_building_justification",
        "GROWTH_MINDSET_JUSTIFICATION:": "growth_mindset_justification",
        "LEADERSHIP_PRESENCE_JUSTIFICATION:": "leadership_presence_justification",
    }

    # Parse scores
    score_sections = {
        "STRATEGIC_IMPACT_SCORE:": "strategic_impact",
        "EXECUTION_QUALITY_SCORE:": "execution_quality",
        "RELATIONSHIP_BUILDING_SCORE:": "relationship_building",
        "GROWTH_MINDSET_SCORE:": "growth_mindset",
        "LEADERSHIP_PRESENCE_SCORE:": "leadership_presence",
    }

    # Parse list fields
    list_sections = {
        "AREAS_OF_STRENGTH:": "areas_of_strength",
        "GROWTH_OPPORTUNITIES:": "growth_opportunities",
        "RECOMMENDED_ACTIONS:": "recommended_actions",
    }

    lines = response_text.split("\n")
    for line in lines:
        line = line.strip()

        # Check score sections
        for marker, field in score_sections.items():
            if line.startswith(marker):
                try:
                    score_str = line[len(marker) :].strip()
                    score = int(score_str.split()[0])  # Take first number
                    if 1 <= score <= 5:
                        result[field] = score
                except (ValueError, IndexError):
                    pass

        # Check text sections
        for marker, field in text_sections.items():
            if line.startswith(marker):
                result[field] = line[len(marker) :].strip()

        # Check list sections
        for marker, field in list_sections.items():
            if line.startswith(marker):
                items_str = line[len(marker) :].strip()
                items = [item.strip() for item in items_str.split("|") if item.strip()]
                result[field] = items

    # Calculate overall score
    scores = [
        result.get("strategic_impact"),
        result.get("execution_quality"),
        result.get("relationship_building"),
        result.get("growth_mindset"),
        result.get("leadership_presence"),
    ]
    valid_scores = [s for s in scores if s is not None]
    if valid_scores:
        result["overall_score"] = round(sum(valid_scores) / len(valid_scores), 2)
    else:
        result["overall_score"] = None

    return result


async def generate_career_status_report(
    user_id: str,
    client_id: str,
    period_start: Optional[date] = None,
    period_end: Optional[date] = None,
) -> dict:
    """
    Generate a career status report.

    Args:
        user_id: The user's UUID
        client_id: The client's UUID
        period_start: Optional start date for assessment period
        period_end: Optional end date for assessment period

    Returns:
        Dict with the full report data including ID

    Raises:
        Exception on generation or database errors
    """
    supabase = get_supabase()

    # Gather context
    context = await get_career_context(user_id, client_id)

    # Build prompt and call Claude
    prompt = _build_assessment_prompt(context)

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = response.content[0].text
        assessment = _parse_assessment_response(response_text)

        # Prepare record for database
        report_data = {
            "user_id": user_id,
            "client_id": client_id,
            "report_date": date.today().isoformat(),
            "period_start": period_start.isoformat() if period_start else None,
            "period_end": period_end.isoformat() if period_end else None,
            "strategic_impact": assessment.get("strategic_impact"),
            "execution_quality": assessment.get("execution_quality"),
            "relationship_building": assessment.get("relationship_building"),
            "growth_mindset": assessment.get("growth_mindset"),
            "leadership_presence": assessment.get("leadership_presence"),
            "overall_score": assessment.get("overall_score"),
            "executive_summary": assessment.get("executive_summary"),
            "strategic_impact_justification": assessment.get(
                "strategic_impact_justification"
            ),
            "execution_quality_justification": assessment.get(
                "execution_quality_justification"
            ),
            "relationship_building_justification": assessment.get(
                "relationship_building_justification"
            ),
            "growth_mindset_justification": assessment.get(
                "growth_mindset_justification"
            ),
            "leadership_presence_justification": assessment.get(
                "leadership_presence_justification"
            ),
            "areas_of_strength": assessment.get("areas_of_strength", []),
            "growth_opportunities": assessment.get("growth_opportunities", []),
            "recommended_actions": assessment.get("recommended_actions", []),
            "data_sources": {
                "kb_documents": len(context.get("kb_documents", [])),
                "memories": len(context.get("memories", [])),
            },
            "generation_model": MODEL,
        }

        # Insert into database
        result = (
            supabase.table("compass_status_reports").insert(report_data).execute()
        )

        if result.data:
            logger.info(f"Generated career status report for user {user_id}")
            return result.data[0]
        else:
            raise Exception("Failed to save report to database")

    except Exception as e:
        logger.error(f"Failed to generate career status report: {e}")
        raise


async def get_latest_report(user_id: str, client_id: str) -> Optional[dict]:
    """Get the most recent report for a user."""
    supabase = get_supabase()

    result = (
        supabase.table("compass_status_reports")
        .select("*")
        .eq("user_id", user_id)
        .eq("client_id", client_id)
        .order("report_date", desc=True)
        .limit(1)
        .execute()
    )

    return result.data[0] if result.data else None


async def list_reports(
    user_id: str, client_id: str, limit: int = 10
) -> list:
    """List historical reports for a user."""
    supabase = get_supabase()

    result = (
        supabase.table("compass_status_reports")
        .select("id, report_date, overall_score, executive_summary, created_at")
        .eq("user_id", user_id)
        .eq("client_id", client_id)
        .order("report_date", desc=True)
        .limit(limit)
        .execute()
    )

    return result.data or []


async def get_report_by_id(
    report_id: str, user_id: str, client_id: str
) -> Optional[dict]:
    """Get a specific report by ID."""
    supabase = get_supabase()

    result = (
        supabase.table("compass_status_reports")
        .select("*")
        .eq("id", report_id)
        .eq("user_id", user_id)
        .eq("client_id", client_id)
        .single()
        .execute()
    )

    return result.data if result.data else None
