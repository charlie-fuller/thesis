"""Strategy API Routes.

CRUD endpoints for department KPIs used in the Strategy dashboard.
KPIs are scoped to client_id via JWT authentication.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from auth import get_current_user
from database import get_supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/strategy", tags=["strategy"])


# ============================================================================
# PYDANTIC MODELS
# ============================================================================


class KPICreate(BaseModel):
    """Create a new department KPI."""

    department: str = Field(..., min_length=1, max_length=100)
    kpi_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    current_value: Optional[float] = None
    target_value: float
    unit: str = Field(..., min_length=1, max_length=50)
    trend: str = Field(default="flat", pattern="^(up|down|flat)$")
    trend_percentage: float = 0
    status: str = Field(default="yellow", pattern="^(green|yellow|red)$")
    linked_objective_id: Optional[str] = None
    fiscal_year: str = Field(default="FY27", max_length=10)
    sort_order: int = 0


class KPIUpdate(BaseModel):
    """Update a department KPI. All fields optional."""

    department: Optional[str] = Field(None, min_length=1, max_length=100)
    kpi_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    current_value: Optional[float] = None
    target_value: Optional[float] = None
    unit: Optional[str] = Field(None, min_length=1, max_length=50)
    trend: Optional[str] = Field(None, pattern="^(up|down|flat)$")
    trend_percentage: Optional[float] = None
    status: Optional[str] = Field(None, pattern="^(green|yellow|red)$")
    linked_objective_id: Optional[str] = None
    fiscal_year: Optional[str] = Field(None, max_length=10)
    sort_order: Optional[int] = None


class KPIResponse(BaseModel):
    """KPI response model."""

    id: str
    department: str
    kpi_name: str
    description: Optional[str]
    current_value: Optional[float]
    target_value: float
    unit: str
    trend: str
    trend_percentage: float
    status: str
    linked_objective_id: Optional[str]
    fiscal_year: str
    sort_order: int
    created_at: str
    updated_at: str


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.get("/kpis", response_model=List[KPIResponse])
async def list_kpis(
    department: Optional[str] = None,
    fiscal_year: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """List KPIs, filterable by department, fiscal_year, and status."""
    query = (
        supabase.table("department_kpis")
        .select("*")
        .eq("client_id", current_user["client_id"])
    )

    if department:
        query = query.eq("department", department)
    if fiscal_year:
        query = query.eq("fiscal_year", fiscal_year)
    if status:
        query = query.eq("status", status)

    result = query.order("department").order("sort_order").execute()

    return result.data or []


@router.post("/kpis", response_model=KPIResponse)
async def create_kpi(
    kpi: KPICreate,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Create a new KPI."""
    data = {
        "client_id": current_user["client_id"],
        **kpi.model_dump(),
    }

    result = supabase.table("department_kpis").insert(data).execute()

    return result.data[0]


@router.patch("/kpis/{kpi_id}", response_model=KPIResponse)
async def update_kpi(
    kpi_id: str,
    update: KPIUpdate,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Update a KPI."""
    # Verify ownership
    existing = (
        supabase.table("department_kpis")
        .select("id")
        .eq("id", kpi_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not existing.data:
        raise HTTPException(status_code=404, detail="KPI not found")

    update_data = {k: v for k, v in update.model_dump().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = (
        supabase.table("department_kpis")
        .update(update_data)
        .eq("id", kpi_id)
        .execute()
    )

    return result.data[0]


@router.delete("/kpis/{kpi_id}")
async def delete_kpi(
    kpi_id: str,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Delete a KPI."""
    existing = (
        supabase.table("department_kpis")
        .select("id")
        .eq("id", kpi_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not existing.data:
        raise HTTPException(status_code=404, detail="KPI not found")

    supabase.table("department_kpis").delete().eq("id", kpi_id).execute()

    return {"message": "KPI deleted"}


@router.get("/kpis/summary")
async def kpi_summary(
    fiscal_year: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Aggregate stats: count by status and by department."""
    query = (
        supabase.table("department_kpis")
        .select("department, status")
        .eq("client_id", current_user["client_id"])
    )

    if fiscal_year:
        query = query.eq("fiscal_year", fiscal_year)

    result = query.execute()

    status_counts = {"green": 0, "yellow": 0, "red": 0}
    dept_counts: dict = {}

    for kpi in result.data or []:
        s = kpi.get("status", "yellow")
        status_counts[s] = status_counts.get(s, 0) + 1

        dept = kpi.get("department", "Unknown")
        dept_counts[dept] = dept_counts.get(dept, 0) + 1

    return {
        "total": len(result.data or []),
        "by_status": status_counts,
        "by_department": dept_counts,
    }
