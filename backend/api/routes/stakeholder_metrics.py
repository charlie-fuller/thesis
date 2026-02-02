"""Stakeholder Metrics API Routes.

Endpoints for managing stakeholder KPIs with validation status tracking.
Supports the red/yellow/green validation framework from project-triage.
"""

import logging
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from auth import get_current_user
from database import get_supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stakeholder-metrics", tags=["stakeholder-metrics"])


# ============================================================================
# PYDANTIC MODELS
# ============================================================================


class MetricCreate(BaseModel):
    """Create a new stakeholder metric."""

    metric_name: str = Field(..., min_length=1, max_length=255)
    metric_category: str = "primary"  # primary, secondary, operational
    unit: Optional[str] = None
    current_value: Optional[str] = None
    target_value: Optional[str] = None
    validation_status: str = "red"  # red, yellow, green
    source: Optional[str] = None
    source_date: Optional[date] = None
    notes: Optional[str] = None
    questions_to_confirm: List[str] = []


class MetricUpdate(BaseModel):
    """Update a stakeholder metric."""

    metric_name: Optional[str] = Field(None, min_length=1, max_length=255)
    metric_category: Optional[str] = None
    unit: Optional[str] = None
    current_value: Optional[str] = None
    target_value: Optional[str] = None
    validation_status: Optional[str] = None
    source: Optional[str] = None
    source_date: Optional[date] = None
    notes: Optional[str] = None
    questions_to_confirm: Optional[List[str]] = None


class MetricValidate(BaseModel):
    """Validate a metric (update validation status)."""

    validation_status: str = Field(..., pattern="^(red|yellow|green)$")
    source: Optional[str] = None
    source_date: Optional[date] = None
    notes: Optional[str] = None


class MetricResponse(BaseModel):
    """Metric response model."""

    id: str
    stakeholder_id: str
    metric_name: str
    metric_category: str
    unit: Optional[str]
    current_value: Optional[str]
    target_value: Optional[str]
    validation_status: str
    source: Optional[str]
    source_date: Optional[str]
    notes: Optional[str]
    questions_to_confirm: List[str]
    created_at: str
    updated_at: str


class MetricWithStakeholder(MetricResponse):
    """Metric with stakeholder info for cross-stakeholder queries."""

    stakeholder_name: str
    stakeholder_department: Optional[str]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _format_metric(
    metric: dict, stakeholder_name: Optional[str] = None, stakeholder_dept: Optional[str] = None
) -> dict:
    """Format metric for response."""
    result = {
        "id": metric["id"],
        "stakeholder_id": metric["stakeholder_id"],
        "metric_name": metric["metric_name"],
        "metric_category": metric.get("metric_category", "primary"),
        "unit": metric.get("unit"),
        "current_value": metric.get("current_value"),
        "target_value": metric.get("target_value"),
        "validation_status": metric.get("validation_status", "red"),
        "source": metric.get("source"),
        "source_date": metric.get("source_date"),
        "notes": metric.get("notes"),
        "questions_to_confirm": metric.get("questions_to_confirm") or [],
        "created_at": metric["created_at"],
        "updated_at": metric.get("updated_at", metric["created_at"]),
    }

    if stakeholder_name is not None:
        result["stakeholder_name"] = stakeholder_name
        result["stakeholder_department"] = stakeholder_dept

    return result


# ============================================================================
# CROSS-STAKEHOLDER ENDPOINTS (must be before parameterized routes)
# ============================================================================


@router.get("/validation-summary")
async def get_validation_summary(
    current_user: dict = Depends(get_current_user), supabase=Depends(get_supabase)
):
    """Get a summary of metric validation status across all stakeholders.

    Returns counts by validation status and lists metrics needing validation.
    """
    result = (
        supabase.table("stakeholder_metrics")
        .select("*, stakeholders(name, department)")
        .eq("client_id", current_user["client_id"])
        .execute()
    )

    # Count by validation status
    status_counts = {"red": 0, "yellow": 0, "green": 0}
    needs_validation = []

    for metric in result.data:
        status = metric.get("validation_status", "red")
        status_counts[status] = status_counts.get(status, 0) + 1

        if status in ("red", "yellow"):
            stakeholder = metric.get("stakeholders", {})
            needs_validation.append(
                {
                    "id": metric["id"],
                    "metric_name": metric["metric_name"],
                    "stakeholder_id": metric["stakeholder_id"],
                    "stakeholder_name": stakeholder.get("name") if stakeholder else None,
                    "stakeholder_department": stakeholder.get("department")
                    if stakeholder
                    else None,
                    "validation_status": status,
                    "questions_to_confirm": metric.get("questions_to_confirm") or [],
                }
            )

    return {
        "total": len(result.data),
        "by_status": status_counts,
        "validation_rate": status_counts["green"] / len(result.data) if result.data else 0,
        "needs_validation": sorted(
            needs_validation,
            key=lambda x: (
                0 if x["validation_status"] == "red" else 1,
                x["stakeholder_name"] or "",
            ),
        ),
    }


@router.get("/needs-validation")
async def get_metrics_needing_validation(
    status: Optional[str] = Query(None, pattern="^(red|yellow)$"),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Get all metrics that need validation (red or yellow status).

    Useful for meeting prep to know which metrics to verify.
    """
    query = (
        supabase.table("stakeholder_metrics")
        .select("*, stakeholders(name, department)")
        .eq("client_id", current_user["client_id"])
    )

    if status:
        query = query.eq("validation_status", status)
    else:
        query = query.in_("validation_status", ["red", "yellow"])

    result = query.limit(limit).execute()

    return [
        _format_metric(
            m,
            m.get("stakeholders", {}).get("name") if m.get("stakeholders") else None,
            m.get("stakeholders", {}).get("department") if m.get("stakeholders") else None,
        )
        for m in result.data
    ]


@router.get("/by-stakeholder/{stakeholder_id}", response_model=List[MetricResponse])
async def get_stakeholder_metrics(
    stakeholder_id: str,
    category: Optional[str] = None,
    validation_status: Optional[str] = Query(None, pattern="^(red|yellow|green)$"),
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Get all metrics for a specific stakeholder."""
    # Verify stakeholder exists and belongs to client
    stakeholder = (
        supabase.table("stakeholders")
        .select("id")
        .eq("id", stakeholder_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not stakeholder.data:
        raise HTTPException(status_code=404, detail="Stakeholder not found")

    query = supabase.table("stakeholder_metrics").select("*").eq("stakeholder_id", stakeholder_id)

    if category:
        query = query.eq("metric_category", category)
    if validation_status:
        query = query.eq("validation_status", validation_status)

    result = query.order("metric_category").order("metric_name").execute()

    return [_format_metric(m) for m in result.data]


# ============================================================================
# CRUD ENDPOINTS
# ============================================================================


@router.post("/stakeholder/{stakeholder_id}", response_model=MetricResponse)
async def create_metric(
    stakeholder_id: str,
    metric: MetricCreate,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Create a new metric for a stakeholder."""
    # Verify stakeholder exists and belongs to client
    stakeholder = (
        supabase.table("stakeholders")
        .select("id")
        .eq("id", stakeholder_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not stakeholder.data:
        raise HTTPException(status_code=404, detail="Stakeholder not found")

    # Validate validation_status
    if metric.validation_status not in ("red", "yellow", "green"):
        raise HTTPException(
            status_code=400, detail="validation_status must be red, yellow, or green"
        )

    data = {
        "stakeholder_id": stakeholder_id,
        "client_id": current_user["client_id"],
        "metric_name": metric.metric_name,
        "metric_category": metric.metric_category,
        "unit": metric.unit,
        "current_value": metric.current_value,
        "target_value": metric.target_value,
        "validation_status": metric.validation_status,
        "source": metric.source,
        "source_date": str(metric.source_date) if metric.source_date else None,
        "notes": metric.notes,
        "questions_to_confirm": metric.questions_to_confirm,
    }

    try:
        result = supabase.table("stakeholder_metrics").insert(data).execute()
    except Exception as e:
        if "duplicate" in str(e).lower():
            raise HTTPException(
                status_code=409,
                detail=f"Metric '{metric.metric_name}' already exists for this stakeholder",
            )
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e

    return _format_metric(result.data[0])


@router.get("/{metric_id}", response_model=MetricResponse)
async def get_metric(
    metric_id: str, current_user: dict = Depends(get_current_user), supabase=Depends(get_supabase)
):
    """Get a single metric by ID."""
    result = (
        supabase.table("stakeholder_metrics")
        .select("*")
        .eq("id", metric_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Metric not found")

    return _format_metric(result.data)


@router.patch("/{metric_id}", response_model=MetricResponse)
async def update_metric(
    metric_id: str,
    update: MetricUpdate,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Update a metric."""
    # Verify ownership
    existing = (
        supabase.table("stakeholder_metrics")
        .select("id")
        .eq("id", metric_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not existing.data:
        raise HTTPException(status_code=404, detail="Metric not found")

    # Build update dict
    update_data = {}
    for k, v in update.model_dump().items():
        if v is not None:
            if k == "source_date":
                update_data[k] = str(v)
            else:
                update_data[k] = v

    # Validate validation_status if provided
    if update_data.get("validation_status") and update_data["validation_status"] not in (
        "red",
        "yellow",
        "green",
    ):
        raise HTTPException(
            status_code=400, detail="validation_status must be red, yellow, or green"
        )

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = supabase.table("stakeholder_metrics").update(update_data).eq("id", metric_id).execute()

    return _format_metric(result.data[0])


@router.patch("/{metric_id}/validate", response_model=MetricResponse)
async def validate_metric(
    metric_id: str,
    validation: MetricValidate,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Update the validation status of a metric.

    Convenience endpoint for quick validation updates.
    - red: Needs validation (estimated, unconfirmed)
    - yellow: Partially validated (directionally correct)
    - green: Confirmed (stakeholder verified)
    """
    # Verify ownership
    existing = (
        supabase.table("stakeholder_metrics")
        .select("id")
        .eq("id", metric_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not existing.data:
        raise HTTPException(status_code=404, detail="Metric not found")

    update_data = {"validation_status": validation.validation_status}

    if validation.source:
        update_data["source"] = validation.source
    if validation.source_date:
        update_data["source_date"] = str(validation.source_date)
    if validation.notes:
        update_data["notes"] = validation.notes

    result = supabase.table("stakeholder_metrics").update(update_data).eq("id", metric_id).execute()

    return _format_metric(result.data[0])


@router.delete("/{metric_id}")
async def delete_metric(
    metric_id: str, current_user: dict = Depends(get_current_user), supabase=Depends(get_supabase)
):
    """Delete a metric."""
    # Verify ownership
    existing = (
        supabase.table("stakeholder_metrics")
        .select("id")
        .eq("id", metric_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not existing.data:
        raise HTTPException(status_code=404, detail="Metric not found")

    supabase.table("stakeholder_metrics").delete().eq("id", metric_id).execute()

    return {"message": "Metric deleted"}


# ============================================================================
# BULK OPERATIONS
# ============================================================================


@router.post("/stakeholder/{stakeholder_id}/bulk")
async def create_metrics_bulk(
    stakeholder_id: str,
    metrics: List[MetricCreate],
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Create multiple metrics for a stakeholder at once.

    Useful for data migration or importing metrics from spreadsheets.
    """
    # Verify stakeholder exists
    stakeholder = (
        supabase.table("stakeholders")
        .select("id")
        .eq("id", stakeholder_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not stakeholder.data:
        raise HTTPException(status_code=404, detail="Stakeholder not found")

    if len(metrics) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 metrics per bulk operation")

    # Prepare data
    data = [
        {
            "stakeholder_id": stakeholder_id,
            "client_id": current_user["client_id"],
            "metric_name": m.metric_name,
            "metric_category": m.metric_category,
            "unit": m.unit,
            "current_value": m.current_value,
            "target_value": m.target_value,
            "validation_status": m.validation_status,
            "source": m.source,
            "source_date": str(m.source_date) if m.source_date else None,
            "notes": m.notes,
            "questions_to_confirm": m.questions_to_confirm,
        }
        for m in metrics
    ]

    try:
        result = supabase.table("stakeholder_metrics").insert(data).execute()
    except Exception:
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")

    return {"created": len(result.data), "metrics": [_format_metric(m) for m in result.data]}
