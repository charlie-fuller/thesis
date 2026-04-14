"""Goal Alignment Analyzer Service.

Analyzes AI projects against IS team FY27 strategic goals.
Produces a 0-100 alignment score across 4 pillars (25 points each):
1. Decision-Ready Customer Journey
2. Maximize Business Systems & AI Value
3. Data-First Digital Workforce
4. High-Trust IS Culture
"""

import logging
import os
from datetime import datetime, timezone
from typing import Optional

import anthropic

import pb_client as pb
from repositories import projects as projects_repo

logger = logging.getLogger(__name__)

# Use Haiku for fast, cost-effective analysis
MODEL = "claude-haiku-4-5-20251001"

# IS Team FY27 Strategic Goals Definition (from FY'27 Plan - Top Priorities)
IS_GOALS = {
    "customer_prospect_journey": {
        "name": "Customer and Prospect Journey",
        "description": "Make the Customer and Prospect Journey Decision-Ready, First Touch to Churn. Provide the connected backbone of systems and data that enables Contentful to understand and act on the full customer and prospect journey, from first touch to expansion (or churn), so GTM, Product, and Finance can make faster, better decisions.",
        "key_outcomes": [
            "Accelerate Customer Deployment (Product Sold/Usage, Digital Touch Model, Customer Lifecycle Communications)",
            "Personalization Everywhere",
            "Accelerate Wall to Wall Enterprise Adoption (Strategic Account Planning)",
            "100% of customers trackable from first touch to churn in shared model",
        ],
        "kpis": [
            "100% customers trackable first-touch-to-churn (Sales, CX, Marketing, Product, Finance)",
            "2+ critical GTM motions with journey-level insights/playbooks adopted by business",
        ],
    },
    "maximize_value": {
        "name": "Maximize Value from Core Business Systems and AI",
        "description": "Treat IS-owned systems and AI capabilities as a portfolio of capabilities and products that drive measurable value: higher productivity, lower software spend, and better employee and customer experience.",
        "key_outcomes": [
            "Next Gen Platform - ExO launch",
            "Billing System Optimization",
            "New v5 P&P with new pricing structures",
            "Contract entitlements integrated with adoption/consumption signals",
        ],
        "kpis": [
            "v5 P&P launched with new pricing structures",
            "All contract entitlements integrated with adoption/consumption signals",
        ],
    },
    "data_first_digital_workforce": {
        "name": "Data First Digital Workforce",
        "description": "Operate as the Data First Digital Workforce for Contentful. Evolve from traditional IT, systems support, and siloed analytics into a Digital Workforce and Data Platform that engineers how work gets done and decisions get made. Treat repeat issues and data gaps as defects to eliminate using automation, standard data models, and AI to reduce friction for employees and provide trusted, decision-ready insights.",
        "key_outcomes": [
            "Data Evolution - 100% sources in Insight 360",
            "IT Forward - tickets/requests treated as product signals",
            "AI Enabled Business Platforms",
            "AI Program with measurable ROI",
            "50%+ employee lifecycle scenarios fully automated",
        ],
        "kpis": [
            "100% sources support cross-functional initiatives in Insight 360",
            "Defined defect backlog with quarterly reduction targets",
            "50%+ common employee lifecycle scenarios fully automated end-to-end",
            "AI Program ROI measured/reported on 2+ strategic projects",
        ],
    },
    "high_trust_culture": {
        "name": "High-Trust and Communicative IS Culture",
        "description": "Build a High-Trust and Communicative IS Culture. Invest in people, communication, and ways of working so that IS is a strategic partner: easy to work with, transparent on trade-offs, and a place where team members grow their careers.",
        "key_outcomes": [
            "Ways of Working improvements",
            "Winning Culture initiatives",
            "Overall Delivery Targets met",
            "Documented communication model executed consistently",
        ],
        "kpis": [
            "Stakeholder sentiment scores improving on IS communication/partnership",
            "Employee engagement improving on 'information I need to do my job'",
            "Development plans in place with clear internal mobility paths",
        ],
    },
}


def _build_analysis_prompt(project: dict) -> str:
    """Build the prompt for analyzing goal alignment."""
    title = project.get("title", "Untitled")
    description = project.get("description") or "No description provided"
    current_state = project.get("current_state") or "Not specified"
    desired_state = project.get("desired_state") or "Not specified"
    department = project.get("department") or "General"

    # Build pillar descriptions
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

    return f"""Analyze this AI project against IS team FY27 strategic goals.

PROJECT:
- Title: {title}
- Department: {department}
- Description: {description}
- Current State: {current_state}
- Desired State: {desired_state}

IS TEAM STRATEGIC PILLARS (score each 0-25 based on direct support):
{pillar_text}

SCORING GUIDANCE:
- 20-25: Directly advances this pillar's outcomes and impacts its KPIs
- 15-19: Strong indirect support for this pillar
- 10-14: Moderate relevance to this pillar
- 5-9: Tangential connection to this pillar
- 0-4: Minimal or no alignment with this pillar

Score each pillar and identify which KPIs this project could impact.

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
SUMMARY: [1-2 sentences summarizing overall strategic alignment]"""


def _parse_analysis_response(response_text: str) -> tuple[int, dict]:
    """Parse the Claude response into score and details."""
    pillar_keys = [
        "customer_prospect_journey",
        "maximize_value",
        "data_first_digital_workforce",
        "high_trust_culture",
    ]

    pillar_scores = {}
    total_score = 0

    # Parse each pillar score and rationale
    for i, key in enumerate(pillar_keys, 1):
        score_marker = f"PILLAR_{i}_SCORE:"
        rationale_marker = f"PILLAR_{i}_RATIONALE:"

        score = 0
        rationale = ""

        if score_marker in response_text:
            start = response_text.find(score_marker) + len(score_marker)
            end = response_text.find("\n", start)
            score_text = response_text[start:end].strip()
            try:
                score = min(25, max(0, int(score_text)))
            except ValueError:
                score = 0

        if rationale_marker in response_text:
            start = response_text.find(rationale_marker) + len(rationale_marker)
            # Find the next section marker or end
            end = len(response_text)
            for next_marker in [f"PILLAR_{i + 1}_SCORE:", "KPI_IMPACTS:", "SUMMARY:"]:
                if next_marker in response_text[start:]:
                    potential_end = response_text.find(next_marker, start)
                    if potential_end < end:
                        end = potential_end
            rationale = response_text[start:end].strip()

        pillar_scores[key] = {"score": score, "rationale": rationale}
        total_score += score

    # Parse KPI impacts
    kpi_impacts = []
    if "KPI_IMPACTS:" in response_text:
        start = response_text.find("KPI_IMPACTS:") + len("KPI_IMPACTS:")
        # Find next section marker
        end = len(response_text)
        for next_m in ["CONFIDENCE:", "CONFIDENCE_QUESTIONS:", "SUMMARY:"]:
            if next_m in response_text[start:]:
                potential_end = response_text.find(next_m, start)
                if potential_end < end:
                    end = potential_end
        impacts_text = response_text[start:end].strip()
        if impacts_text and impacts_text.lower() != "none":
            kpi_impacts = [kpi.strip() for kpi in impacts_text.split(",") if kpi.strip()]

    # Parse confidence score (optional -- not present in project-level analysis)
    alignment_confidence = None
    if "CONFIDENCE:" in response_text:
        start = response_text.find("CONFIDENCE:") + len("CONFIDENCE:")
        end = response_text.find("\n", start)
        conf_text = response_text[start:end].strip()
        try:
            alignment_confidence = min(100, max(0, int(conf_text)))
        except ValueError:
            pass

    # Parse confidence questions (optional)
    confidence_questions = []
    if "CONFIDENCE_QUESTIONS:" in response_text:
        start = response_text.find("CONFIDENCE_QUESTIONS:") + len("CONFIDENCE_QUESTIONS:")
        end = response_text.find("SUMMARY:", start) if "SUMMARY:" in response_text[start:] else len(response_text)
        questions_text = response_text[start:end].strip()
        import re

        for line in questions_text.split("\n"):
            line = line.strip()
            if line:
                cleaned = re.sub(r"^\d+\.\s*", "", line).strip()
                if cleaned:
                    confidence_questions.append(cleaned)

    # Parse summary
    summary = ""
    if "SUMMARY:" in response_text:
        start = response_text.find("SUMMARY:") + len("SUMMARY:")
        summary = response_text[start:].strip()

    details = {
        "pillar_scores": pillar_scores,
        "kpi_impacts": kpi_impacts,
        "summary": summary,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }

    # Include confidence fields if present
    if alignment_confidence is not None:
        details["alignment_confidence"] = alignment_confidence
    if confidence_questions:
        details["confidence_questions"] = confidence_questions

    return total_score, details


async def analyze_goal_alignment(
    project_id: str,
    client_id: Optional[str] = None,
) -> tuple[int, dict]:
    """Analyze a project's alignment with IS team strategic goals.

    Args:
        project_id: The project UUID
        client_id: Optional client_id for verification

    Returns:
        Tuple of (total_score, details_dict)

    Raises:
        ValueError: If project not found
    """
    # Fetch project
    project = projects_repo.get_project(project_id)
    if not project:
        raise ValueError(f"Project {project_id} not found")

    # Build prompt and call Claude
    prompt = _build_analysis_prompt(project)

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    try:
        response = client.messages.create(model=MODEL, max_tokens=1024, messages=[{"role": "user", "content": prompt}])

        response_text = response.content[0].text
        score, details = _parse_analysis_response(response_text)

        # Update the project in database
        projects_repo.update_project(project_id, {"goal_alignment_score": score, "goal_alignment_details": details})

        logger.info(f"Analyzed goal alignment for project {project_id}: score={score}/100")

        return score, details

    except Exception as e:
        logger.error(f"Failed to analyze goal alignment for {project_id}: {e}")
        raise


async def batch_analyze_all(client_id: str) -> dict:
    """Analyze goal alignment for all projects belonging to a client.

    Returns:
        Dict with counts and statistics
    """
    # Get all projects
    projects = projects_repo.list_projects()
    success_count = 0
    failure_count = 0
    errors = []
    scores = []

    for proj in projects:
        try:
            score, _ = await analyze_goal_alignment(proj["id"], client_id)
            success_count += 1
            scores.append(score)
            logger.info(f"Analyzed alignment for: {proj['title']} (score: {score})")
        except Exception as e:
            failure_count += 1
            errors.append({"id": proj["id"], "title": proj["title"], "error": str(e)})
            logger.error(f"Failed for {proj['title']}: {e}")

    # Calculate statistics
    avg_score = sum(scores) / len(scores) if scores else 0
    distribution = {
        "high": len([s for s in scores if s >= 80]),
        "moderate": len([s for s in scores if 60 <= s < 80]),
        "low": len([s for s in scores if 40 <= s < 60]),
        "minimal": len([s for s in scores if s < 40]),
    }

    return {
        "total": len(projects),
        "success": success_count,
        "failed": failure_count,
        "average_score": round(avg_score, 1),
        "distribution": distribution,
        "errors": errors if errors else None,
    }
