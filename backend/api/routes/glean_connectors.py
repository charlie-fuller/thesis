"""
Glean Connectors API Routes

Provides endpoints for managing the Glean connector registry,
including listing connectors, checking availability, and logging
connector requests for gap analysis.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from supabase import Client

from ..dependencies import get_supabase

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


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/", response_model=list[ConnectorInfo])
async def list_connectors(
    connector_type: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    supabase: Client = Depends(get_supabase)
):
    """
    List all connectors, optionally filtered by type, category, or status.

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
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def list_categories(supabase: Client = Depends(get_supabase)):
    """Get all unique connector categories."""
    try:
        result = supabase.table("glean_connectors").select("category").execute()
        categories = set(r["category"] for r in result.data if r.get("category"))
        return sorted(list(categories))
    except Exception as e:
        logger.error(f"Error listing categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check", response_model=list[ConnectorCheckResult])
async def check_connectors(
    request: ConnectorCheckRequest,
    supabase: Client = Depends(get_supabase)
):
    """
    Check availability of multiple connectors by name.
    Returns availability status for each requested connector.
    """
    try:
        results = []

        for name in request.connector_names:
            # Normalize name for lookup
            normalized = name.lower().replace(" ", "_").replace("-", "_")

            # Check if connector exists (OOB or custom)
            query = supabase.table("glean_connectors").select("*").or_(
                f"name.eq.{normalized},display_name.ilike.%{name}%"
            ).in_("connector_type", ["oob", "custom"]).execute()

            if query.data:
                connector = query.data[0]
                results.append(ConnectorCheckResult(
                    name=name,
                    available=True,
                    connector_type=connector["connector_type"],
                    status=connector.get("status"),
                    category=connector.get("category"),
                    setup_complexity=connector.get("setup_complexity")
                ))
            else:
                results.append(ConnectorCheckResult(
                    name=name,
                    available=False
                ))

        return results
    except Exception as e:
        logger.error(f"Error checking connectors: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/request")
async def log_connector_request(
    request: ConnectorRequestInput,
    supabase: Client = Depends(get_supabase)
):
    """
    Log a connector request for gap tracking.
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
                "p_priority": request.priority
            }
        ).execute()

        return {
            "success": True,
            "request_id": result.data,
            "message": f"Connector request logged for '{request.connector_name}'"
        }
    except Exception as e:
        logger.error(f"Error logging connector request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gaps", response_model=list[ConnectorGap])
async def get_connector_gaps(
    priority: Optional[str] = None,
    limit: int = 20,
    supabase: Client = Depends(get_supabase)
):
    """
    Get prioritized list of connector gaps/requests.
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
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/{query}")
async def search_connectors(
    query: str,
    supabase: Client = Depends(get_supabase)
):
    """
    Search connectors by name or display name.
    Returns matching connectors across all types.
    """
    try:
        result = supabase.table("glean_connectors").select("*").or_(
            f"name.ilike.%{query}%,display_name.ilike.%{query}%"
        ).execute()

        return result.data
    except Exception as e:
        logger.error(f"Error searching connectors: {e}")
        raise HTTPException(status_code=500, detail=str(e))
