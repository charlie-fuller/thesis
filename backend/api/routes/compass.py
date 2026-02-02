"""Compass Agent API Routes

Endpoints for career status report generation and history.
The Compass agent helps users track wins, prepare for check-ins,
and assess their career performance against a 5-dimension rubric.
"""

import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from auth import get_current_user
from services.career_status_report import (
    DEFAULT_RUBRIC,
    generate_career_status_report,
    get_latest_report,
    get_report_by_id,
    list_reports,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/compass", tags=["compass"])


# ============================================================================
# PYDANTIC MODELS
# ============================================================================


class GenerateReportRequest(BaseModel):
    """Request to generate a new career status report."""

    period_start: Optional[date] = None
    period_end: Optional[date] = None


class ReportSummary(BaseModel):
    """Summary view of a report for list endpoints."""

    id: str
    report_date: date
    overall_score: Optional[float]
    executive_summary: Optional[str]
    created_at: str


class DimensionDetail(BaseModel):
    """Detail for a single rubric dimension."""

    name: str
    weight: int
    description: str
    score: Optional[int]
    justification: Optional[str]


class ReportResponse(BaseModel):
    """Full report response."""

    id: str
    report_date: date
    period_start: Optional[date]
    period_end: Optional[date]

    # Scores
    strategic_impact: Optional[int]
    execution_quality: Optional[int]
    relationship_building: Optional[int]
    growth_mindset: Optional[int]
    leadership_presence: Optional[int]
    overall_score: Optional[float]

    # AI-generated content
    executive_summary: Optional[str]
    strategic_impact_justification: Optional[str]
    execution_quality_justification: Optional[str]
    relationship_building_justification: Optional[str]
    growth_mindset_justification: Optional[str]
    leadership_presence_justification: Optional[str]

    # Evidence and recommendations
    areas_of_strength: list[str]
    growth_opportunities: list[str]
    recommended_actions: list[str]
    improvement_actions: Optional[dict] = None

    # Metadata
    data_sources: dict
    created_at: str


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post("/status-report/generate", response_model=ReportResponse)
async def generate_report(
    request: GenerateReportRequest = GenerateReportRequest(),
    current_user: dict = Depends(get_current_user),
):
    """Generate a new career status report.

    Analyzes KB documents tagged for Compass and any available memories
    to produce a 5-dimension assessment with justifications.
    """
    user_id = current_user.get("id")
    client_id = current_user.get("client_id")

    logger.info(f"Generate report: user_id={user_id}, client_id={client_id}")

    if not user_id or not client_id:
        logger.error(f"Auth failed: user_id={user_id}, client_id={client_id}")
        raise HTTPException(status_code=401, detail="User not authenticated")

    try:
        report = await generate_career_status_report(
            user_id=user_id,
            client_id=client_id,
            period_start=request.period_start,
            period_end=request.period_end,
        )
        return report
    except Exception as e:
        logger.error(f"Failed to generate career status report: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@router.get("/status-report/latest", response_model=Optional[ReportResponse])
async def get_latest(current_user: dict = Depends(get_current_user)):
    """Get the most recent career status report.

    Returns null if no reports exist yet.
    """
    user_id = current_user.get("id")
    client_id = current_user.get("client_id")

    if not user_id or not client_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    try:
        report = await get_latest_report(user_id, client_id)
        return report
    except Exception as e:
        logger.error(f"Failed to get latest report: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.get("/status-reports", response_model=list[ReportSummary])
async def list_all_reports(
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
):
    """List historical career status reports.

    Returns summaries sorted by date descending (newest first).
    """
    user_id = current_user.get("id")
    client_id = current_user.get("client_id")

    if not user_id or not client_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    try:
        reports = await list_reports(user_id, client_id, limit)
        return reports
    except Exception as e:
        logger.error(f"Failed to list reports: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.get("/status-reports/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get a specific career status report by ID."""
    user_id = current_user.get("id")
    client_id = current_user.get("client_id")

    if not user_id or not client_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    try:
        report = await get_report_by_id(report_id, user_id, client_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        return report
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get report {report_id}: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.get("/rubric")
async def get_rubric():
    """Get the career assessment rubric definitions.

    Returns the 5 dimensions with their weights and level descriptors.
    This can be used by the frontend to display what each score level means.
    """
    return {
        "dimensions": [
            {
                "key": key,
                "name": dim["name"],
                "weight": dim["weight"],
                "description": dim["description"],
                "levels": dim["levels"],
            }
            for key, dim in DEFAULT_RUBRIC.items()
        ]
    }
