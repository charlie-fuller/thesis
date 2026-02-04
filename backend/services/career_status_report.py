"""Career Status Report Generation Service.

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
    """Gather career-related context from KB and memories.

    Pulls from ALL KB documents for the client, prioritizing:
    1. Recent meeting transcripts
    2. Documents with career-relevant content (1:1s, feedback, wins, goals)
    3. Most recently uploaded/modified documents

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
        # Get all recent documents for this client, prioritizing transcripts
        # Order by uploaded_at to get most recent first
        # Note: Document content is stored in document_chunks, not documents table
        logger.info(f"Fetching career context for user_id={user_id}, client_id={client_id}")

        # Get ALL document metadata for this client
        # Only include documents with original_date from January 5, 2026 onwards
        docs_result = (
            supabase.table("documents")
            .select("id, title, filename, document_type, uploaded_at, original_date")
            .eq("client_id", client_id)
            .gte("original_date", "2026-01-05")
            .order("original_date", desc=True)
            .limit(50)  # Get more docs, we'll filter and prioritize
            .execute()
        )

        logger.info(f"Documents query returned {len(docs_result.data) if docs_result.data else 0} documents")

        if docs_result.data:
            # Get document IDs to fetch chunks
            doc_ids = [doc["id"] for doc in docs_result.data]

            # Fetch chunks for these documents (get first few chunks per doc for context)
            chunks_result = (
                supabase.table("document_chunks")
                .select("document_id, content, chunk_index")
                .in_("document_id", doc_ids)
                .order("chunk_index")
                .execute()
            )

            # Build content map from chunks (concatenate first chunks per document)
            content_map = {}
            for chunk in chunks_result.data or []:
                doc_id = chunk["document_id"]
                if doc_id not in content_map:
                    content_map[doc_id] = ""
                # Only take first ~2000 chars per document
                if len(content_map[doc_id]) < 2000:
                    content_map[doc_id] += chunk.get("content", "") + "\n"

            logger.info(f"Fetched content for {len(content_map)} documents from chunks")

            # Categorize documents by type/relevance
            transcripts = []
            career_relevant = []
            other_docs = []

            # Keywords that suggest career-relevant content
            career_keywords = [
                "1:1",
                "one-on-one",
                "feedback",
                "performance",
                "goal",
                "win",
                "accomplishment",
                "review",
                "check-in",
                "checkin",
                "career",
                "growth",
                "development",
                "promotion",
                "raise",
                "project",
                "deliverable",
                "milestone",
                "deadline",
            ]

            for doc in docs_result.data:
                doc_id = doc["id"]
                content = content_map.get(doc_id, "")
                if not content:
                    continue

                # Use title or filename for categorization
                title = doc.get("title") or doc.get("filename") or "Untitled"
                title_lower = title.lower()
                content_lower = content.lower()[:500]  # Check first 500 chars
                doc_type = (doc.get("document_type") or "").lower()

                # Check if it's a transcript
                is_transcript = (
                    doc_type in ["transcript", "meeting_transcript"]
                    or "transcript" in title_lower
                    or "meeting" in title_lower
                )

                # Check for career-relevant keywords
                is_career_relevant = any(kw in title_lower or kw in content_lower for kw in career_keywords)

                doc_entry = {
                    "title": title,
                    "content": content[:2000],  # Truncate for context
                    "doc_type": doc_type,
                    "uploaded_at": doc.get("uploaded_at"),
                }

                if is_transcript:
                    transcripts.append(doc_entry)
                elif is_career_relevant:
                    career_relevant.append(doc_entry)
                else:
                    other_docs.append(doc_entry)

            # Build final document list: prioritize transcripts, then career-relevant
            # Take up to 5 transcripts, 3 career-relevant, 2 other recent docs
            logger.info(
                f"Categorized docs: {len(transcripts)} transcripts, {len(career_relevant)} career-relevant, {len(other_docs)} other"
            )

            final_docs = []
            final_docs.extend(transcripts[:5])
            final_docs.extend(career_relevant[:3])
            final_docs.extend(other_docs[:2])

            # Ensure we have at least some docs, even if not perfectly categorized
            if len(final_docs) < 10:
                remaining_slots = 10 - len(final_docs)
                all_docs = transcripts + career_relevant + other_docs
                for doc in all_docs:
                    if doc not in final_docs and remaining_slots > 0:
                        final_docs.append(doc)
                        remaining_slots -= 1

            context["kb_documents"] = final_docs[:10]
            logger.info(f"Final context has {len(context['kb_documents'])} documents")

    except Exception as e:
        logger.error(f"Error fetching career context: {e}", exc_info=True)
        # Continue with empty context rather than failing completely

    # TODO: Add Mem0 memory retrieval when fully implemented
    # For now, memories will be empty

    return context


def _build_assessment_prompt(context: dict) -> str:
    """Build the prompt for career status assessment."""
    # Format rubric dimensions
    rubric_text = "CAREER ASSESSMENT RUBRIC:\n\n"
    for _key, dim in DEFAULT_RUBRIC.items():
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

    return f"""You are Compass, a career coaching agent. Generate a career status report based on the rubric and available context.

{rubric_text}
{kb_context}
{memory_context}

Assess performance across all 5 dimensions. If evidence is limited, make reasonable inferences but note confidence level.

For each dimension provide:
- A score (1-5 based on the rubric)
- Brief justification (2-3 sentences with evidence when available)
- 2-3 concrete improvement actions (specific things to do this week/month)

Also provide:
- Executive summary (2-3 sentences on overall trajectory)
- 2-3 key strengths
- 2-3 growth opportunities
- 2-3 priority next steps

Use these section labels (the parser expects this format):

EXECUTIVE_SUMMARY: [text]

STRATEGIC_IMPACT_SCORE: [1-5]
STRATEGIC_IMPACT_JUSTIFICATION: [text]
STRATEGIC_IMPACT_IMPROVEMENTS: [action1] | [action2] | [action3]

EXECUTION_QUALITY_SCORE: [1-5]
EXECUTION_QUALITY_JUSTIFICATION: [text]
EXECUTION_QUALITY_IMPROVEMENTS: [action1] | [action2] | [action3]

RELATIONSHIP_BUILDING_SCORE: [1-5]
RELATIONSHIP_BUILDING_JUSTIFICATION: [text]
RELATIONSHIP_BUILDING_IMPROVEMENTS: [action1] | [action2] | [action3]

GROWTH_MINDSET_SCORE: [1-5]
GROWTH_MINDSET_JUSTIFICATION: [text]
GROWTH_MINDSET_IMPROVEMENTS: [action1] | [action2] | [action3]

LEADERSHIP_PRESENCE_SCORE: [1-5]
LEADERSHIP_PRESENCE_JUSTIFICATION: [text]
LEADERSHIP_PRESENCE_IMPROVEMENTS: [action1] | [action2] | [action3]

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
        "improvement_actions": {},
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

    # Parse improvement actions per dimension
    improvement_sections = {
        "STRATEGIC_IMPACT_IMPROVEMENTS:": "strategic_impact",
        "EXECUTION_QUALITY_IMPROVEMENTS:": "execution_quality",
        "RELATIONSHIP_BUILDING_IMPROVEMENTS:": "relationship_building",
        "GROWTH_MINDSET_IMPROVEMENTS:": "growth_mindset",
        "LEADERSHIP_PRESENCE_IMPROVEMENTS:": "leadership_presence",
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

        # Check improvement sections
        for marker, dimension in improvement_sections.items():
            if line.startswith(marker):
                items_str = line[len(marker) :].strip()
                items = [item.strip() for item in items_str.split("|") if item.strip()]
                result["improvement_actions"][dimension] = items

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
    """Generate a career status report.

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
            "strategic_impact_justification": assessment.get("strategic_impact_justification"),
            "execution_quality_justification": assessment.get("execution_quality_justification"),
            "relationship_building_justification": assessment.get("relationship_building_justification"),
            "growth_mindset_justification": assessment.get("growth_mindset_justification"),
            "leadership_presence_justification": assessment.get("leadership_presence_justification"),
            "areas_of_strength": assessment.get("areas_of_strength", []),
            "growth_opportunities": assessment.get("growth_opportunities", []),
            "recommended_actions": assessment.get("recommended_actions", []),
            "improvement_actions": assessment.get("improvement_actions", {}),
            "data_sources": {
                "kb_documents": len(context.get("kb_documents", [])),
                "memories": len(context.get("memories", [])),
            },
            "generation_model": MODEL,
        }

        # Insert into database
        result = supabase.table("compass_status_reports").insert(report_data).execute()

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


async def list_reports(user_id: str, client_id: str, limit: int = 10) -> list:
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


async def get_report_by_id(report_id: str, user_id: str, client_id: str) -> Optional[dict]:
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
