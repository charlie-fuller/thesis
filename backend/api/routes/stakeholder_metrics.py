"""Stakeholder Metrics API Routes.

Endpoints for managing stakeholder KPIs with validation status tracking.
Supports the red/yellow/green validation framework from project-triage.
"""

import logging
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

import pb_client as pb
from repositories.stakeholders import (
    get_stakeholder,
    list_stakeholder_metrics,
    get_stakeholder_metric,
    create_stakeholder_metric,
    update_stakeholder_metric,
    delete_stakeholder_metric,
)

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
        "created_at": metric.get("created", metric.get("created_at", "")),
        "updated_at": metric.get("updated", metric.get("updated_at", metric.get("created", ""))),
    }

    if stakeholder_name is not None:
        result["stakeholder_name"] = stakeholder_name
        result["stakeholder_department"] = stakeholder_dept

    return result


# ============================================================================
# CROSS-STAKEHOLDER ENDPOINTS (must be before parameterized routes)
# ============================================================================


@router.get("/validation-summary")
async def get_validation_summary():
    """Get a summary of metric validation status across all stakeholders.

    Returns counts by validation status and lists metrics needing validation.
    """
    all_metrics = pb.get_all("stakeholder_metrics")

    # Count by validation status
    status_counts = {"red": 0, "yellow": 0, "green": 0}
    needs_validation = []

    for metric in all_metrics:
        status = metric.get("validation_status", "red")
        status_counts[status] = status_counts.get(status, 0) + 1

        if status in ("red", "yellow"):
            # Look up stakeholder name separately
            stakeholder_name = None
            stakeholder_dept = None
            if metric.get("stakeholder_id"):
                stakeholder = get_stakeholder(metric["stakeholder_id"])
                if stakeholder:
                    stakeholder_name = stakeholder.get("name")
                    stakeholder_dept = stakeholder.get("department")

            needs_validation.append(
                {
                    "id": metric["id"],
                    "metric_name": metric["metric_name"],
                    "stakeholder_id": metric["stakeholder_id"],
                    "stakeholder_name": stakeholder_name,
                    "stakeholder_department": stakeholder_dept,
                    "validation_status": status,
                    "questions_to_confirm": metric.get("questions_to_confirm") or [],
                }
            )

    return {
        "total": len(all_metrics),
        "by_status": status_counts,
        "validation_rate": status_counts["green"] / len(all_metrics) if all_metrics else 0,
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
):
    """Get all metrics that need validation (red or yellow status).

    Useful for meeting prep to know which metrics to verify.
    """
    if status:
        filter_str = f"validation_status='{pb.escape_filter(status)}'"
    else:
        filter_str = "validation_status='red' || validation_status='yellow'"

    result = pb.list_records("stakeholder_metrics", filter=filter_str, per_page=limit)
    metrics = result.get("items", [])

    formatted = []
    for m in metrics:
        # Look up stakeholder name separately
        stakeholder_name = None
        stakeholder_dept = None
        if m.get("stakeholder_id"):
            stakeholder = get_stakeholder(m["stakeholder_id"])
            if stakeholder:
                stakeholder_name = stakeholder.get("name")
                stakeholder_dept = stakeholder.get("department")

        formatted.append(_format_metric(m, stakeholder_name, stakeholder_dept))

    return formatted


@router.get("/by-stakeholder/{stakeholder_id}", response_model=List[MetricResponse])
async def get_stakeholder_metrics_endpoint(
    stakeholder_id: str,
    category: Optional[str] = None,
    validation_status: Optional[str] = Query(None, pattern="^(red|yellow|green)$"),
):
    """Get all metrics for a specific stakeholder."""
    # Verify stakeholder exists
    stakeholder = get_stakeholder(stakeholder_id)
    if not stakeholder:
        raise HTTPException(status_code=404, detail="Stakeholder not found")

    metrics = list_stakeholder_metrics(stakeholder_id)

    # Apply filters
    if category:
        metrics = [m for m in metrics if m.get("metric_category") == category]
    if validation_status:
        metrics = [m for m in metrics if m.get("validation_status") == validation_status]

    return [_format_metric(m) for m in metrics]


# ============================================================================
# CRUD ENDPOINTS
# ============================================================================


@router.post("/stakeholder/{stakeholder_id}", response_model=MetricResponse)
async def create_metric(
    stakeholder_id: str,
    metric: MetricCreate,
):
    """Create a new metric for a stakeholder."""
    # Verify stakeholder exists
    stakeholder = get_stakeholder(stakeholder_id)
    if not stakeholder:
        raise HTTPException(status_code=404, detail="Stakeholder not found")

    # Validate validation_status
    if metric.validation_status not in ("red", "yellow", "green"):
        raise HTTPException(status_code=400, detail="validation_status must be red, yellow, or green")

    data = {
        "stakeholder_id": stakeholder_id,
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
        result = create_stakeholder_metric(data)
    except Exception as e:
        if "duplicate" in str(e).lower():
            raise HTTPException(
                status_code=409,
                detail=f"Metric '{metric.metric_name}' already exists for this stakeholder",
            ) from None
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e

    return _format_metric(result)


@router.get("/{metric_id}", response_model=MetricResponse)
async def get_metric(metric_id: str):
    """Get a single metric by ID."""
    result = get_stakeholder_metric(metric_id)

    if not result:
        raise HTTPException(status_code=404, detail="Metric not found")

    return _format_metric(result)


@router.patch("/{metric_id}", response_model=MetricResponse)
async def update_metric_endpoint(
    metric_id: str,
    update: MetricUpdate,
):
    """Update a metric."""
    # Verify metric exists
    existing = get_stakeholder_metric(metric_id)
    if not existing:
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
        raise HTTPException(status_code=400, detail="validation_status must be red, yellow, or green")

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = update_stakeholder_metric(metric_id, update_data)

    return _format_metric(result)


@router.patch("/{metric_id}/validate", response_model=MetricResponse)
async def validate_metric(
    metric_id: str,
    validation: MetricValidate,
):
    """Update the validation status of a metric.

    Convenience endpoint for quick validation updates.
    - red: Needs validation (estimated, unconfirmed)
    - yellow: Partially validated (directionally correct)
    - green: Confirmed (stakeholder verified)
    """
    # Verify metric exists
    existing = get_stakeholder_metric(metric_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Metric not found")

    update_data = {"validation_status": validation.validation_status}

    if validation.source:
        update_data["source"] = validation.source
    if validation.source_date:
        update_data["source_date"] = str(validation.source_date)
    if validation.notes:
        update_data["notes"] = validation.notes

    result = update_stakeholder_metric(metric_id, update_data)

    return _format_metric(result)


@router.delete("/{metric_id}")
async def delete_metric(metric_id: str):
    """Delete a metric."""
    # Verify metric exists
    existing = get_stakeholder_metric(metric_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Metric not found")

    delete_stakeholder_metric(metric_id)

    return {"message": "Metric deleted"}


# ============================================================================
# BULK OPERATIONS
# ============================================================================


@router.post("/stakeholder/{stakeholder_id}/bulk")
async def create_metrics_bulk(
    stakeholder_id: str,
    metrics: List[MetricCreate],
):
    """Create multiple metrics for a stakeholder at once.

    Useful for data migration or importing metrics from spreadsheets.
    """
    # Verify stakeholder exists
    stakeholder = get_stakeholder(stakeholder_id)
    if not stakeholder:
        raise HTTPException(status_code=404, detail="Stakeholder not found")

    if len(metrics) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 metrics per bulk operation")

    created = []
    try:
        for m in metrics:
            data = {
                "stakeholder_id": stakeholder_id,
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
            result = create_stakeholder_metric(data)
            created.append(result)
    except Exception:
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from None

    return {"created": len(created), "metrics": [_format_metric(m) for m in created]}
