"""Glean Connectors API Routes

Provides endpoints for managing the Glean connector registry,
including listing connectors, checking availability, and logging
connector requests for gap analysis.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from database import get_supabase
from supabase import Client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/glean-connectors", tags=["Glean Connectors"])


# ============================================================================
# Request/Response Models
# ============================================================================


class ConnectorInfo(BaseModel):
    """Information about a Glean connector."""

    id: UUID
    name: str
    display_name: str
    connector_type: str  # 'oob', 'custom', 'requested'
    status: str
    category: Optional[str] = None
    description: Optional[str] = None
    glean_tier: Optional[str] = None
    setup_complexity: Optional[str] = None


class ConnectorCheckRequest(BaseModel):
    """Request to check multiple connector names."""

    connector_names: list[str]


class ConnectorCheckResult(BaseModel):
    """Result of checking a connector's availability."""

    name: str
    available: bool
    connector_type: Optional[str] = None  # 'oob' or 'custom' if available
    status: Optional[str] = None
    category: Optional[str] = None
    setup_complexity: Optional[str] = None


class ConnectorRequestInput(BaseModel):
    """Input for logging a connector request."""

    connector_name: str
    requested_by: Optional[str] = None
    request_source: Optional[str] = None
    use_case: str
    business_justification: Optional[str] = None
    priority: str = "medium"  # 'critical', 'high', 'medium', 'low'


class ConnectorGap(BaseModel):
    """A connector gap/request for prioritization."""

    connector_name: str
    request_count: int
    priority: str
    status: str
    use_cases: Optional[str] = None
    requesters: Optional[str] = None
    first_requested: Optional[str] = None
    last_requested: Optional[str] = None


class DiscoIntegrationRequest(BaseModel):
    """Request to check DISCO integration feasibility."""

    integration_names: list[str]


class DiscoIntegrationResult(BaseModel):
    """Result of checking a single integration's feasibility."""

    integration_name: str
    connector_found: bool
    connector_name: Optional[str] = None
    display_name: Optional[str] = None
    connector_type: Optional[str] = None
    contentful_status: Optional[str] = None
    disco_score: int
    feasibility_rating: str
    is_blocker: bool = False
    notes: str


class DiscoScoreSummary(BaseModel):
    """Summary of overall DISCO integration feasibility."""

    total_integrations: int
    ready_integrations: int
    blockers: int
    blocker_names: list[str] = []
    score: int
    max_score: int
    percentage: float
    overall_feasibility: str
    action_required: str


class DiscoDataSource(BaseModel):
    """Information about the connector data source."""

    source: str
    last_updated: str
    note: str


class DiscoScoreResponse(BaseModel):
    """Full DISCO integration score response."""

    integrations: list[DiscoIntegrationResult]
    summary: DiscoScoreSummary
    data_source: DiscoDataSource


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/", response_model=list[ConnectorInfo])
async def list_connectors(
    connector_type: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    supabase: Client = Depends(get_supabase),
):
    """List all connectors, optionally filtered by type, category, or status.

    - connector_type: 'oob', 'custom', or 'requested'
    - category: 'productivity', 'engineering', 'hr', 'sales', etc.
    - status: 'available', 'in_development', 'planned', 'requested'
    """
    try:
        query = supabase.table("glean_connectors").select("*")

        if connector_type:
            query = query.eq("connector_type", connector_type)
        if category:
            query = query.eq("category", category)
        if status:
            query = query.eq("status", status)

        result = query.order("display_name").execute()
        return result.data
    except Exception as e:
        logger.error(f"Error listing connectors: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/categories")
async def list_categories(supabase: Client = Depends(get_supabase)):
    """Get all unique connector categories."""
    try:
        result = supabase.table("glean_connectors").select("category").execute()
        categories = set(r["category"] for r in result.data if r.get("category"))
        return sorted(list(categories))
    except Exception as e:
        logger.error(f"Error listing categories: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/check", response_model=list[ConnectorCheckResult])
async def check_connectors(
    request: ConnectorCheckRequest, supabase: Client = Depends(get_supabase)
):
    """Check availability of multiple connectors by name.
    Returns availability status for each requested connector.
    """
    try:
        results = []

        for name in request.connector_names:
            # Normalize name for lookup
            normalized = name.lower().replace(" ", "_").replace("-", "_")

            # Check if connector exists (OOB or custom)
            query = (
                supabase.table("glean_connectors")
                .select("*")
                .or_(f"name.eq.{normalized},display_name.ilike.%{name}%")
                .in_("connector_type", ["oob", "custom"])
                .execute()
            )

            if query.data:
                connector = query.data[0]
                results.append(
                    ConnectorCheckResult(
                        name=name,
                        available=True,
                        connector_type=connector["connector_type"],
                        status=connector.get("status"),
                        category=connector.get("category"),
                        setup_complexity=connector.get("setup_complexity"),
                    )
                )
            else:
                results.append(ConnectorCheckResult(name=name, available=False))

        return results
    except Exception as e:
        logger.error(f"Error checking connectors: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/request")
async def log_connector_request(
    request: ConnectorRequestInput, supabase: Client = Depends(get_supabase)
):
    """Log a connector request for gap tracking.
    Increments request_count if connector was already requested.
    """
    try:
        # Call the stored function
        result = supabase.rpc(
            "log_connector_request",
            {
                "p_connector_name": request.connector_name,
                "p_requested_by": request.requested_by,
                "p_request_source": request.request_source,
                "p_use_case": request.use_case,
                "p_business_justification": request.business_justification,
                "p_priority": request.priority,
            },
        ).execute()

        return {
            "success": True,
            "request_id": result.data,
            "message": f"Connector request logged for '{request.connector_name}'",
        }
    except Exception as e:
        logger.error(f"Error logging connector request: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/gaps", response_model=list[ConnectorGap])
async def get_connector_gaps(
    priority: Optional[str] = None, limit: int = 20, supabase: Client = Depends(get_supabase)
):
    """Get prioritized list of connector gaps/requests.
    Use this to understand what connectors are being requested most.
    """
    try:
        query = supabase.table("glean_connector_gaps").select("*")

        if priority:
            query = query.eq("priority", priority)

        result = query.limit(limit).execute()
        return result.data
    except Exception as e:
        logger.error(f"Error getting connector gaps: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/search/{query}")
async def search_connectors(query: str, supabase: Client = Depends(get_supabase)):
    """Search connectors by name or display name.
    Returns matching connectors across all types.
    """
    try:
        result = (
            supabase.table("glean_connectors")
            .select("*")
            .or_(f"name.ilike.%{query}%,display_name.ilike.%{query}%")
            .execute()
        )

        return result.data
    except Exception as e:
        logger.error(f"Error searching connectors: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# DISCO Integration Scoring Endpoints
# ============================================================================


@router.post("/disco/score", response_model=DiscoScoreResponse)
async def calculate_disco_score(
    request: DiscoIntegrationRequest, supabase: Client = Depends(get_supabase)
):
    """Calculate DISCO integration feasibility score for a list of integrations.

    Scoring:
    - 5 = READY: Integration enabled and working at Contentful
    - 4 = TESTING: Integration in indexing/testing phase
    - 3 = APPROVED: Integration approved, awaiting deployment
    - 2 = BUILDING: Custom connector being developed
    - 1 = AVAILABLE: Glean has connector, needs approval process
    - 0 = CUSTOM: No connector exists, would need custom build

    Returns detailed breakdown per integration plus overall summary.
    """
    try:
        result = supabase.rpc(
            "calculate_disco_integration_score", {"p_integration_names": request.integration_names}
        ).execute()

        data = result.data
        if not data:
            raise HTTPException(status_code=500, detail="Failed to calculate DISCO score")

        # Parse the response
        integrations = []
        for item in data.get("integrations", []):
            integrations.append(
                DiscoIntegrationResult(
                    integration_name=item.get("integration_name", ""),
                    connector_found=item.get("connector_found", False),
                    connector_name=item.get("connector_name"),
                    display_name=item.get("display_name"),
                    connector_type=item.get("connector_type"),
                    contentful_status=item.get("contentful_status"),
                    disco_score=item.get("disco_score", 0),
                    feasibility_rating=item.get("feasibility_rating", "BLOCKER"),
                    is_blocker=item.get("is_blocker", False),
                    notes=item.get("notes", "No connector found"),
                )
            )

        summary_data = data.get("summary", {})
        summary = DiscoScoreSummary(
            total_integrations=summary_data.get("total_integrations", 0),
            ready_integrations=summary_data.get("ready_integrations", 0),
            blockers=summary_data.get("blockers", 0),
            blocker_names=summary_data.get("blocker_names", []),
            score=summary_data.get("score", 0),
            max_score=summary_data.get("max_score", 0),
            percentage=summary_data.get("percentage", 0),
            overall_feasibility=summary_data.get("overall_feasibility", "UNKNOWN"),
            action_required=summary_data.get("action_required", ""),
        )

        data_source_data = data.get("data_source", {})
        data_source = DiscoDataSource(
            source=data_source_data.get("source", "AWC-Glean Data Source Connector Tracking"),
            last_updated=data_source_data.get("last_updated", "2026-01-29"),
            note=data_source_data.get(
                "note", "Check with IT/AWC team for latest connector status."
            ),
        )

        return DiscoScoreResponse(
            integrations=integrations, summary=summary, data_source=data_source
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating DISCO score: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/disco/matrix")
async def get_disco_matrix(
    min_score: Optional[int] = None,
    contentful_status: Optional[str] = None,
    supabase: Client = Depends(get_supabase),
):
    """Get the DISCO integration matrix showing all connectors with their
    Contentful deployment status and feasibility scores.

    Filter options:
    - min_score: Only return connectors with disco_score >= this value
    - contentful_status: 'enabled', 'testing', 'approved', 'in_progress', 'pending_approval', 'not_requested'
    """
    try:
        query = supabase.table("glean_disco_integration_matrix").select("*")

        if min_score is not None:
            query = query.gte("disco_score", min_score)
        if contentful_status:
            query = query.eq("contentful_status", contentful_status)

        result = query.execute()
        return result.data
    except Exception as e:
        logger.error(f"Error getting DISCO matrix: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/disco/summary")
async def get_disco_summary(supabase: Client = Depends(get_supabase)):
    """Get a summary of connectors grouped by Contentful status and DISCO score.
    Useful for quick overview of integration capabilities.
    """
    try:
        result = supabase.table("glean_connector_summary").select("*").execute()
        return result.data
    except Exception as e:
        logger.error(f"Error getting DISCO summary: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e
