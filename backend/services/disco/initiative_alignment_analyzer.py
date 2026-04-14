"""Initiative Goal Alignment Analyzer.

Analyzes DISCO initiatives against IS team FY27 strategic goals,
using rich context from agent outputs for more accurate scoring.
Reuses the same 4-pillar framework and parser from the project analyzer.
"""

import logging
import os

import anthropic

import pb_client as pb
import repositories.disco as disco_repo
import repositories.projects as projects_repo
from services.goal_alignment_analyzer import IS_GOALS, MODEL, _parse_analysis_response

logger = logging.getLogger(__name__)


def _build_initiative_prompt(
    initiative: dict,
    agent_outputs: list[dict],
    bundles: list[dict],
) -> str:
    """Build analysis prompt with rich context from agent outputs."""
    name = initiative.get("name", "Untitled")
    description = initiative.get("description") or "No description provided"

    # Build pillar descriptions (same as project analyzer)
    pillar_text = ""
    for i, (_key, pillar) in enumerate(IS_GOALS.items(), 1):
        outcomes = ", ".join(pillar["key_outcomes"])
        kpis = ", ".join(pillar["kpis"])
        pillar_text += f"""
{i}. {pillar["name"]} (0-25 pts)
   - {pillar["description"]}
   - Outcomes: {outcomes}
   - KPIs: {kpis}
"""

    # Build agent output context
    agent_context = ""
    if agent_outputs:
        agent_context = "\nAGENT ANALYSIS OUTPUTS:\n"
        for output in agent_outputs:
            agent_type = output.get("agent_type", "unknown")
            label = agent_type.replace("_", " ").title()
            content = output.get("content_markdown", "")
            # Use executive summary if available, otherwise truncate content
            summary = output.get("executive_summary") or ""
            recommendation = output.get("recommendation") or ""
            confidence = output.get("confidence_level") or ""

            agent_context += f"\n--- {label} ---\n"
            if recommendation:
                agent_context += f"Recommendation: {recommendation}\n"
            if confidence:
                agent_context += f"Confidence: {confidence}\n"
            if summary:
                agent_context += f"Summary: {summary}\n"
            # Include content (truncated to keep prompt manageable)
            if content:
                truncated = content[:2000] + ("..." if len(content) > 2000 else "")
                agent_context += f"Analysis:\n{truncated}\n"
    else:
        agent_context = "\n(No agent analysis outputs available yet - scoring based on name/description only)\n"

    # Build bundle context
    bundle_context = ""
    if bundles:
        bundle_context = "\nSYNTHESIS BUNDLES:\n"
        for b in bundles:
            bundle_context += f"- {b.get('name', 'Unnamed')}"
            if b.get("impact_score"):
                bundle_context += f" (Impact: {b['impact_score']}"
                if b.get("feasibility_score"):
                    bundle_context += f", Feasibility: {b['feasibility_score']}"
                if b.get("urgency_score"):
                    bundle_context += f", Urgency: {b['urgency_score']}"
                bundle_context += ")"
            bundle_context += "\n"
            if b.get("description"):
                desc = b["description"][:300]
                bundle_context += f"  {desc}\n"

    return f"""Analyze this DISCO initiative against IS team FY27 strategic goals.
This is a strategic initiative being evaluated through a discovery pipeline, not just a single project.
Use ALL the context provided below for accurate scoring.

INITIATIVE:
- Name: {name}
- Description: {description}
{agent_context}
{bundle_context}

IS TEAM STRATEGIC PILLARS (score each 0-25 based on direct support):
{pillar_text}

SCORING GUIDANCE:
- 20-25: Directly advances this pillar's outcomes and impacts its KPIs
- 15-19: Strong indirect support for this pillar
- 10-14: Moderate relevance to this pillar
- 5-9: Tangential connection to this pillar
- 0-4: Minimal or no alignment with this pillar

Score each pillar and identify which KPIs this initiative could impact.
Consider the full scope of the initiative including all agent analyses and bundle assessments.

Also assess your confidence in the alignment scoring (0-100). Confidence reflects how much relevant information was available for scoring -- you may be missing departmental KPIs, team-specific goals, or context about how this work connects to broader organizational priorities. Low confidence doesn't mean the initiative is bad; it means the scoring could shift significantly with more information.
- 80-100: Rich context available (department goals, KPIs, stakeholder input)
- 60-79: Reasonable context but some departmental specifics missing
- 40-59: Significant gaps -- scoring based on general descriptions without team/department KPIs
- 0-39: Very limited information -- mostly inferring alignment from name/description alone

Finally, identify 2-4 specific questions that, if answered, would most improve confidence and potentially raise the alignment score. Focus on:
- Missing departmental KPIs or goals that could reveal stronger alignment
- Stakeholder context that would clarify strategic connections
- Information that would benefit not just this initiative but other projects and initiatives sharing the same strategic pillars

IMPORTANT: Always include this question (adapt the wording to the specific initiative):
"Are there strategic goals, KPIs, or departmental priorities not currently captured in the system that this initiative meaningfully supports?"
This is critical because our goal/KPI catalog is often incomplete, and surfacing missing context improves scoring across all related projects and initiatives.

Respond using this exact format:
PILLAR_1_SCORE: [0-25]
PILLAR_1_RATIONALE: [1-2 sentences explaining the score]
PILLAR_2_SCORE: [0-25]
PILLAR_2_RATIONALE: [1-2 sentences]
PILLAR_3_SCORE: [0-25]
PILLAR_3_RATIONALE: [1-2 sentences]
PILLAR_4_SCORE: [0-25]
PILLAR_4_RATIONALE: [1-2 sentences]
KPI_IMPACTS: [comma-separated list of impacted KPIs from the list above]
CONFIDENCE: [0-100]
CONFIDENCE_QUESTIONS: [numbered list, one per line, e.g. "1. Question text"]
SUMMARY: [1-2 sentences summarizing overall strategic alignment]"""


async def analyze_initiative_alignment(
    initiative_id: str,
    user_id: str,
) -> tuple[int, dict]:
    """Analyze an initiative's alignment with IS team strategic goals.

    Gathers rich context from agent outputs and bundles for accurate scoring.

    Args:
        initiative_id: The initiative UUID
        user_id: The requesting user's ID

    Returns:
        Tuple of (total_score, details_dict)

    Raises:
        ValueError: If initiative not found
    """
    # Fetch initiative
    initiative = disco_repo.get_initiative(initiative_id)
    if not initiative:
        raise ValueError(f"Initiative {initiative_id} not found")

    # Fetch latest agent outputs (one per agent type, newest first)
    all_outputs = disco_repo.list_outputs(initiative_id, sort="-created")
    # Deduplicate: keep latest per agent_type
    seen_agents = set()
    agent_outputs = []
    for output in all_outputs[:20]:
        if output["agent_type"] not in seen_agents:
            seen_agents.add(output["agent_type"])
            agent_outputs.append(output)

    # Fetch bundles if any
    bundles = disco_repo.list_bundles(initiative_id, sort="-created")
    bundles = bundles[:10]

    # Build prompt and call Claude
    prompt = _build_initiative_prompt(initiative, agent_outputs, bundles)

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = response.content[0].text
        score, details = _parse_analysis_response(response_text)

        # Store results on initiative
        disco_repo.update_initiative(initiative_id, {
            "goal_alignment_score": score,
            "goal_alignment_details": details,
        })

        logger.info(f"Analyzed goal alignment for initiative {initiative_id}: score={score}/100")
        return score, details

    except Exception as e:
        logger.error(f"Failed to analyze goal alignment for initiative {initiative_id}: {e}")
        raise


async def get_project_alignment_rollup(initiative_id: str) -> dict:
    """Get alignment score rollup for all projects linked to an initiative.

    Returns:
        Dict with project scores, averages, and distribution
    """
    # Query projects linked to this initiative that have alignment scores
    # PocketBase doesn't support contains() on arrays directly,
    # so we fetch all projects and filter in Python
    all_projects = projects_repo.list_projects(sort="-goal_alignment_score")
    projects = [p for p in all_projects if initiative_id in (p.get("initiative_ids") or [])]

    # Build rollup
    scored_projects = [p for p in projects if p.get("goal_alignment_score") is not None]
    scores = [p["goal_alignment_score"] for p in scored_projects]

    avg_score = round(sum(scores) / len(scores), 1) if scores else None
    distribution = {
        "high": len([s for s in scores if s >= 80]),
        "moderate": len([s for s in scores if 60 <= s < 80]),
        "low": len([s for s in scores if 40 <= s < 60]),
        "minimal": len([s for s in scores if s < 40]),
    }

    project_summaries = []
    for p in projects:
        summary = {
            "id": p["id"],
            "project_code": p.get("project_code"),
            "title": p.get("title"),
            "status": p.get("status"),
            "goal_alignment_score": p.get("goal_alignment_score"),
        }
        # Include alignment level label
        score = p.get("goal_alignment_score")
        if score is not None:
            if score >= 80:
                summary["alignment_level"] = "high"
            elif score >= 60:
                summary["alignment_level"] = "moderate"
            elif score >= 40:
                summary["alignment_level"] = "low"
            else:
                summary["alignment_level"] = "minimal"
        else:
            summary["alignment_level"] = None
        project_summaries.append(summary)

    return {
        "total_projects": len(projects),
        "analyzed_projects": len(scored_projects),
        "average_score": avg_score,
        "distribution": distribution,
        "projects": project_summaries,
    }
