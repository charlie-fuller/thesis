"""
Goal Alignment Analyzer Service

Analyzes AI opportunities against IS team FY27 strategic goals.
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

from database import get_supabase

logger = logging.getLogger(__name__)

# Use Haiku for fast, cost-effective analysis
MODEL = "claude-3-5-haiku-20241022"

# IS Team FY27 Strategic Goals Definition (from FY'27 Plan - Top Priorities)
IS_GOALS = {
    "customer_prospect_journey": {
        "name": "Customer and Prospect Journey",
        "description": "Make the Customer and Prospect Journey Decision-Ready, First Touch to Churn. Provide the connected backbone of systems and data that enables Contentful to understand and act on the full customer and prospect journey, from first touch to expansion (or churn), so GTM, Product, and Finance can make faster, better decisions.",
        "key_outcomes": [
            "Accelerate Customer Deployment (Product Sold/Usage, Digital Touch Model, Customer Lifecycle Communications)",
            "Personalization Everywhere",
            "Accelerate Wall to Wall Enterprise Adoption (Strategic Account Planning)",
            "100% of customers trackable from first touch to churn in shared model"
        ],
        "kpis": [
            "100% customers trackable first-touch-to-churn (Sales, CX, Marketing, Product, Finance)",
            "2+ critical GTM motions with journey-level insights/playbooks adopted by business"
        ]
    },
    "maximize_value": {
        "name": "Maximize Value from Core Business Systems and AI",
        "description": "Treat IS-owned systems and AI capabilities as a portfolio of capabilities and products that drive measurable value: higher productivity, lower software spend, and better employee and customer experience.",
        "key_outcomes": [
            "Next Gen Platform - ExO launch",
            "Billing System Optimization",
            "New v5 P&P with new pricing structures",
            "Contract entitlements integrated with adoption/consumption signals"
        ],
        "kpis": [
            "v5 P&P launched with new pricing structures",
            "All contract entitlements integrated with adoption/consumption signals"
        ]
    },
    "data_first_digital_workforce": {
        "name": "Data First Digital Workforce",
        "description": "Operate as the Data First Digital Workforce for Contentful. Evolve from traditional IT, systems support, and siloed analytics into a Digital Workforce and Data Platform that engineers how work gets done and decisions get made. Treat repeat issues and data gaps as defects to eliminate using automation, standard data models, and AI to reduce friction for employees and provide trusted, decision-ready insights.",
        "key_outcomes": [
            "Data Evolution - 100% sources in Insight 360",
            "IT Forward - tickets/requests treated as product signals",
            "AI Enabled Business Platforms",
            "AI Program with measurable ROI",
            "50%+ employee lifecycle scenarios fully automated"
        ],
        "kpis": [
            "100% sources support cross-functional initiatives in Insight 360",
            "Defined defect backlog with quarterly reduction targets",
            "50%+ common employee lifecycle scenarios fully automated end-to-end",
            "AI Program ROI measured/reported on 2+ strategic projects"
        ]
    },
    "high_trust_culture": {
        "name": "High-Trust and Communicative IS Culture",
        "description": "Build a High-Trust and Communicative IS Culture. Invest in people, communication, and ways of working so that IS is a strategic partner: easy to work with, transparent on trade-offs, and a place where team members grow their careers.",
        "key_outcomes": [
            "Ways of Working improvements",
            "Winning Culture initiatives",
            "Overall Delivery Targets met",
            "Documented communication model executed consistently"
        ],
        "kpis": [
            "Stakeholder sentiment scores improving on IS communication/partnership",
            "Employee engagement improving on 'information I need to do my job'",
            "Development plans in place with clear internal mobility paths"
        ]
    }
}


def _build_analysis_prompt(opportunity: dict) -> str:
    """Build the prompt for analyzing goal alignment."""

    title = opportunity.get("title", "Untitled")
    description = opportunity.get("description") or "No description provided"
    current_state = opportunity.get("current_state") or "Not specified"
    desired_state = opportunity.get("desired_state") or "Not specified"
    department = opportunity.get("department") or "General"

    # Build pillar descriptions
    pillar_text = ""
    for i, (key, pillar) in enumerate(IS_GOALS.items(), 1):
        outcomes = ", ".join(pillar["key_outcomes"])
        kpis = ", ".join(pillar["kpis"])
        pillar_text += f"""
{i}. {pillar['name']} (0-25 pts)
   - {pillar['description']}
   - Outcomes: {outcomes}
   - KPIs: {kpis}
"""

    return f"""Analyze this AI opportunity against IS team FY27 strategic goals.

OPPORTUNITY:
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

Score each pillar and identify which KPIs this opportunity could impact.

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
        "high_trust_culture"
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
            for next_marker in [f"PILLAR_{i+1}_SCORE:", "KPI_IMPACTS:", "SUMMARY:"]:
                if next_marker in response_text[start:]:
                    potential_end = response_text.find(next_marker, start)
                    if potential_end < end:
                        end = potential_end
            rationale = response_text[start:end].strip()

        pillar_scores[key] = {
            "score": score,
            "rationale": rationale
        }
        total_score += score

    # Parse KPI impacts
    kpi_impacts = []
    if "KPI_IMPACTS:" in response_text:
        start = response_text.find("KPI_IMPACTS:") + len("KPI_IMPACTS:")
        end = response_text.find("SUMMARY:", start) if "SUMMARY:" in response_text[start:] else len(response_text)
        impacts_text = response_text[start:end].strip()
        if impacts_text and impacts_text.lower() != "none":
            kpi_impacts = [kpi.strip() for kpi in impacts_text.split(",") if kpi.strip()]

    # Parse summary
    summary = ""
    if "SUMMARY:" in response_text:
        start = response_text.find("SUMMARY:") + len("SUMMARY:")
        summary = response_text[start:].strip()

    details = {
        "pillar_scores": pillar_scores,
        "kpi_impacts": kpi_impacts,
        "summary": summary,
        "analyzed_at": datetime.now(timezone.utc).isoformat()
    }

    return total_score, details


async def analyze_goal_alignment(
    opportunity_id: str,
    client_id: Optional[str] = None,
) -> tuple[int, dict]:
    """
    Analyze an opportunity's alignment with IS team strategic goals.

    Args:
        opportunity_id: The opportunity UUID
        client_id: Optional client_id for verification

    Returns:
        Tuple of (total_score, details_dict)

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
    prompt = _build_analysis_prompt(opportunity)

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text
        score, details = _parse_analysis_response(response_text)

        # Update the opportunity in database
        supabase.table("ai_opportunities").update({
            "goal_alignment_score": score,
            "goal_alignment_details": details
        }).eq("id", opportunity_id).execute()

        logger.info(
            f"Analyzed goal alignment for opportunity {opportunity_id}: "
            f"score={score}/100"
        )

        return score, details

    except Exception as e:
        logger.error(f"Failed to analyze goal alignment for {opportunity_id}: {e}")
        raise


async def batch_analyze_all(client_id: str) -> dict:
    """
    Analyze goal alignment for all opportunities belonging to a client.

    Returns:
        Dict with counts and statistics
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
    scores = []

    for opp in opportunities:
        try:
            score, _ = await analyze_goal_alignment(opp["id"], client_id)
            success_count += 1
            scores.append(score)
            logger.info(f"Analyzed alignment for: {opp['title']} (score: {score})")
        except Exception as e:
            failure_count += 1
            errors.append({"id": opp["id"], "title": opp["title"], "error": str(e)})
            logger.error(f"Failed for {opp['title']}: {e}")

    # Calculate statistics
    avg_score = sum(scores) / len(scores) if scores else 0
    distribution = {
        "high": len([s for s in scores if s >= 80]),
        "moderate": len([s for s in scores if 60 <= s < 80]),
        "low": len([s for s in scores if 40 <= s < 60]),
        "minimal": len([s for s in scores if s < 40])
    }

    return {
        "total": len(opportunities),
        "success": success_count,
        "failed": failure_count,
        "average_score": round(avg_score, 1),
        "distribution": distribution,
        "errors": errors if errors else None,
    }
