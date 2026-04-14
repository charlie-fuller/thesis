"""Glean Connectors API Routes.

Provides endpoints for managing the Glean connector registry,
including listing connectors, checking availability, and logging
connector requests for gap analysis.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import pb_client as pb

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/glean-connectors", tags=["Glean Connectors"])


# ============================================================================
# Request/Response Models
# ============================================================================


class ConnectorInfo(BaseModel):
    """Information about a Glean connector."""

    id: str
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
    connector_type: Optional[str] = None
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
    priority: str = "medium"


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
):
    """List all connectors, optionally filtered by type, category, or status."""
    try:
        filters = []
        if connector_type:
            safe_type = pb.escape_filter(connector_type)
            filters.append(f"connector_type='{safe_type}'")
        if category:
            safe_cat = pb.escape_filter(category)
            filters.append(f"category='{safe_cat}'")
        if status:
            safe_status = pb.escape_filter(status)
            filters.append(f"status='{safe_status}'")

        filter_str = " && ".join(filters) if filters else ""

        result = pb.get_all(
            "glean_connectors",
            filter=filter_str if filter_str else None,
            sort="display_name",
        )
        return result
    except Exception as e:
        logger.error(f"Error listing connectors: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/categories")
async def list_categories():
    """Get all unique connector categories."""
    try:
        result = pb.get_all("glean_connectors", fields="category")
        categories = {r["category"] for r in result if r.get("category")}
        return sorted(categories)
    except Exception as e:
        logger.error(f"Error listing categories: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/check", response_model=list[ConnectorCheckResult])
async def check_connectors(request: ConnectorCheckRequest):
    """Check availability of multiple connectors by name."""
    try:
        results = []

        for name in request.connector_names:
            # Normalize name for lookup
            normalized = name.lower().replace(" ", "_").replace("-", "_")
            safe_normalized = pb.escape_filter(normalized)
            safe_name = pb.escape_filter(name)

            # Check if connector exists (OOB or custom)
            query_result = pb.get_all(
                "glean_connectors",
                filter=(
                    f"(name='{safe_normalized}' || display_name~'{safe_name}') "
                    f"&& (connector_type='oob' || connector_type='custom')"
                ),
            )

            if query_result:
                connector = query_result[0]
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
async def log_connector_request(request: ConnectorRequestInput):
    """Log a connector request for gap tracking.

    Increments request_count if connector was already requested.
    """
    try:
        safe_name = pb.escape_filter(request.connector_name)

        # Check if connector gap already exists
        existing = pb.get_first(
            "glean_connector_gaps",
            filter=f"connector_name='{safe_name}'",
        )

        if existing:
            # Increment request count and update
            new_count = (existing.get("request_count") or 0) + 1
            update_data = {
                "request_count": new_count,
                "priority": request.priority,
            }
            if request.use_case:
                existing_cases = existing.get("use_cases") or ""
                if request.use_case not in existing_cases:
                    sep = "; " if existing_cases else ""
                    update_data["use_cases"] = existing_cases + sep + request.use_case
            if request.requested_by:
                existing_requesters = existing.get("requesters") or ""
                if request.requested_by not in existing_requesters:
                    sep = ", " if existing_requesters else ""
                    update_data["requesters"] = existing_requesters + sep + request.requested_by

            pb.update_record("glean_connector_gaps", existing["id"], update_data)
            request_id = existing["id"]
        else:
            # Create new gap entry
            new_record = pb.create_record(
                "glean_connector_gaps",
                {
                    "connector_name": request.connector_name,
                    "request_count": 1,
                    "priority": request.priority,
                    "status": "requested",
                    "use_cases": request.use_case,
                    "requesters": request.requested_by or "",
                },
            )
            request_id = new_record["id"] if new_record else None

        return {
            "success": True,
            "request_id": request_id,
            "message": f"Connector request logged for '{request.connector_name}'",
        }
    except Exception as e:
        logger.error(f"Error logging connector request: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/gaps", response_model=list[ConnectorGap])
async def get_connector_gaps(priority: Optional[str] = None, limit: int = 20):
    """Get prioritized list of connector gaps/requests."""
    try:
        filter_str = None
        if priority:
            safe_priority = pb.escape_filter(priority)
            filter_str = f"priority='{safe_priority}'"

        result = pb.list_records(
            "glean_connector_gaps",
            filter=filter_str,
            per_page=limit,
        )
        return result.get("items", [])
    except Exception as e:
        logger.error(f"Error getting connector gaps: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/search/{query}")
async def search_connectors(query: str):
    """Search connectors by name or display name."""
    try:
        safe_query = pb.escape_filter(query)
        result = pb.get_all(
            "glean_connectors",
            filter=f"name~'{safe_query}' || display_name~'{safe_query}'",
        )
        return result
    except Exception as e:
        logger.error(f"Error searching connectors: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# DISCO Integration Scoring Endpoints
# ============================================================================


@router.post("/disco/score", response_model=DiscoScoreResponse)
async def calculate_disco_score(request: DiscoIntegrationRequest):
    """Calculate DISCO integration feasibility score for a list of integrations.

    Scoring:
    - 5 = READY: Integration enabled and working at Contentful
    - 4 = TESTING: Integration in indexing/testing phase
    - 3 = APPROVED: Integration approved, awaiting deployment
    - 2 = BUILDING: Custom connector being developed
    - 1 = AVAILABLE: Glean has connector, needs approval process
    - 0 = CUSTOM: No connector exists, would need custom build
    """
    try:
        # Compute score locally since PocketBase has no RPC
        integrations = []
        total_score = 0
        max_score = len(request.integration_names) * 5
        blockers = []

        status_score_map = {
            "enabled": 5,
            "testing": 4,
            "indexing": 4,
            "approved": 3,
            "in_progress": 2,
            "pending_approval": 1,
            "not_requested": 0,
        }

        feasibility_map = {
            5: "READY",
            4: "TESTING",
            3: "APPROVED",
            2: "BUILDING",
            1: "AVAILABLE",
            0: "CUSTOM",
        }

        for name in request.integration_names:
            safe_name = pb.escape_filter(name)
            normalized = name.lower().replace(" ", "_").replace("-", "_")
            safe_normalized = pb.escape_filter(normalized)

            connector = pb.get_first(
                "glean_connectors",
                filter=f"name='{safe_normalized}' || display_name~'{safe_name}'",
            )

            if connector:
                cf_status = connector.get("contentful_status") or "not_requested"
                score = status_score_map.get(cf_status, 0)
                total_score += score
                is_blocker = score == 0
                if is_blocker:
                    blockers.append(name)

                integrations.append(
                    DiscoIntegrationResult(
                        integration_name=name,
                        connector_found=True,
                        connector_name=connector.get("name"),
                        display_name=connector.get("display_name"),
                        connector_type=connector.get("connector_type"),
                        contentful_status=cf_status,
                        disco_score=score,
                        feasibility_rating=feasibility_map.get(score, "CUSTOM"),
                        is_blocker=is_blocker,
                        notes=f"Status: {cf_status}",
                    )
                )
            else:
                blockers.append(name)
                integrations.append(
                    DiscoIntegrationResult(
                        integration_name=name,
                        connector_found=False,
                        disco_score=0,
                        feasibility_rating="CUSTOM",
                        is_blocker=True,
                        notes="No connector found",
                    )
                )

        ready_count = sum(1 for i in integrations if i.disco_score >= 4)
        percentage = round((total_score / max_score * 100) if max_score > 0 else 0, 1)

        if percentage >= 80:
            overall = "HIGH"
            action = "Most integrations ready. Address remaining gaps."
        elif percentage >= 50:
            overall = "MODERATE"
            action = "Several integrations need work. Prioritize blockers."
        else:
            overall = "LOW"
            action = "Significant integration gaps. Review feasibility."

        summary = DiscoScoreSummary(
            total_integrations=len(request.integration_names),
            ready_integrations=ready_count,
            blockers=len(blockers),
            blocker_names=blockers,
            score=total_score,
            max_score=max_score,
            percentage=percentage,
            overall_feasibility=overall,
            action_required=action,
        )

        data_source = DiscoDataSource(
            source="AWC-Glean Data Source Connector Tracking",
            last_updated="2026-01-29",
            note="Check with IT/AWC team for latest connector status.",
        )

        return DiscoScoreResponse(integrations=integrations, summary=summary, data_source=data_source)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating DISCO score: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/disco/matrix")
async def get_disco_matrix(
    min_score: Optional[int] = None,
    contentful_status: Optional[str] = None,
):
    """Get the DISCO integration matrix showing all connectors with their
    Contentful deployment status and feasibility scores.
    """
    try:
        filters = []
        if min_score is not None:
            filters.append(f"disco_score>={min_score}")
        if contentful_status:
            safe_status = pb.escape_filter(contentful_status)
            filters.append(f"contentful_status='{safe_status}'")

        filter_str = " && ".join(filters) if filters else None
        result = pb.get_all("glean_disco_integration_matrix", filter=filter_str)
        return result
    except Exception as e:
        logger.error(f"Error getting DISCO matrix: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/disco/summary")
async def get_disco_summary():
    """Get a summary of connectors grouped by Contentful status and DISCO score."""
    try:
        result = pb.get_all("glean_connector_summary")
        return result
    except Exception as e:
        logger.error(f"Error getting DISCO summary: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e
