"""Strategy API Routes.

CRUD endpoints for department KPIs used in the Strategy dashboard.
KPIs are scoped to client_id via JWT authentication.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

import pb_client as pb
from repositories import misc as misc_repo

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
    linked_goal_id: Optional[str] = None
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
    linked_goal_id: Optional[str] = None
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
    linked_goal_id: Optional[str]
    fiscal_year: str
    sort_order: int
    created_at: str
    updated_at: str


# ============================================================================
# GOAL MODELS
# ============================================================================


class GoalCreate(BaseModel):
    """Create a new strategic goal."""

    level: str = Field(..., pattern="^(company|team)$")
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    department: Optional[str] = Field(None, max_length=100)
    owner: Optional[str] = Field(None, max_length=255)
    target_metric: Optional[str] = Field(None, max_length=255)
    current_value: Optional[float] = None
    target_value: Optional[float] = None
    unit: Optional[str] = Field(None, max_length=50)
    status: str = Field(default="on_track", pattern="^(on_track|at_risk|behind|achieved)$")
    priority: int = 0
    parent_goal_id: Optional[str] = None
    fiscal_year: str = Field(default="FY27", max_length=10)


class GoalUpdate(BaseModel):
    """Update a strategic goal. All fields optional."""

    level: Optional[str] = Field(None, pattern="^(company|team)$")
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    department: Optional[str] = Field(None, max_length=100)
    owner: Optional[str] = Field(None, max_length=255)
    target_metric: Optional[str] = Field(None, max_length=255)
    current_value: Optional[float] = None
    target_value: Optional[float] = None
    unit: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, pattern="^(on_track|at_risk|behind|achieved)$")
    priority: Optional[int] = None
    parent_goal_id: Optional[str] = None
    fiscal_year: Optional[str] = Field(None, max_length=10)


class GoalResponse(BaseModel):
    """Goal response model."""

    id: str
    level: str
    title: str
    description: Optional[str]
    department: Optional[str]
    owner: Optional[str]
    target_metric: Optional[str]
    current_value: Optional[float]
    target_value: Optional[float]
    unit: Optional[str]
    status: str
    priority: int
    parent_goal_id: Optional[str]
    fiscal_year: str
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
):
    """List KPIs, filterable by department, fiscal_year, and status."""
    kwargs = {}
    if department:
        kwargs["department"] = department
    if fiscal_year:
        kwargs["fiscal_year"] = fiscal_year
    if status:
        kwargs["status"] = status

    return misc_repo.list_department_kpis(sort="department,sort_order", **kwargs)


@router.post("/kpis", response_model=KPIResponse)
async def create_kpi(
    kpi: KPICreate,
):
    """Create a new KPI."""
    return misc_repo.create_department_kpi(kpi.model_dump())


@router.patch("/kpis/{kpi_id}", response_model=KPIResponse)
async def update_kpi(
    kpi_id: str,
    update: KPIUpdate,
):
    """Update a KPI."""
    existing = misc_repo.get_department_kpi(kpi_id)
    if not existing:
        raise HTTPException(status_code=404, detail="KPI not found")

    update_data = update.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    return misc_repo.update_department_kpi(kpi_id, update_data)


@router.delete("/kpis/{kpi_id}")
async def delete_kpi(
    kpi_id: str,
):
    """Delete a KPI."""
    existing = misc_repo.get_department_kpi(kpi_id)
    if not existing:
        raise HTTPException(status_code=404, detail="KPI not found")

    misc_repo.delete_department_kpi(kpi_id)

    return {"message": "KPI deleted"}


@router.get("/kpis/summary")
async def kpi_summary(
    fiscal_year: Optional[str] = None,
):
    """Aggregate stats: count by status and by department."""
    kwargs = {}
    if fiscal_year:
        kwargs["fiscal_year"] = fiscal_year

    kpis = misc_repo.list_department_kpis(**kwargs)

    status_counts = {"green": 0, "yellow": 0, "red": 0}
    dept_counts: dict = {}

    for kpi in kpis:
        s = kpi.get("status", "yellow")
        status_counts[s] = status_counts.get(s, 0) + 1

        dept = kpi.get("department", "Unknown")
        dept_counts[dept] = dept_counts.get(dept, 0) + 1

    return {
        "total": len(kpis),
        "by_status": status_counts,
        "by_department": dept_counts,
    }


# ============================================================================
# GOALS ENDPOINTS
# ============================================================================


@router.get("/goals", response_model=List[GoalResponse])
async def list_goals(
    level: Optional[str] = Query(None, pattern="^(company|team)$"),
    department: Optional[str] = None,
    fiscal_year: Optional[str] = None,
):
    """List strategic goals, filterable by level, department, and fiscal_year."""
    parts = []
    if level:
        parts.append(f"level='{pb.escape_filter(level)}'")
    if department:
        parts.append(f"department='{pb.escape_filter(department)}'")
    if fiscal_year:
        parts.append(f"fiscal_year='{pb.escape_filter(fiscal_year)}'")
    filter_str = " && ".join(parts)

    return pb.get_all("strategic_goals", filter=filter_str, sort="priority")


@router.post("/goals", response_model=GoalResponse)
async def create_goal(
    goal: GoalCreate,
):
    """Create a new strategic goal."""
    data = goal.model_dump()
    return pb.create_record("strategic_goals", data)


@router.patch("/goals/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: str,
    update: GoalUpdate,
):
    """Update a strategic goal."""
    existing = pb.get_record("strategic_goals", goal_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Goal not found")

    update_data = update.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    return pb.update_record("strategic_goals", goal_id, update_data)


@router.delete("/goals/{goal_id}")
async def delete_goal(
    goal_id: str,
):
    """Delete a strategic goal. Linked KPIs get linked_goal_id set to null (DB cascade)."""
    existing = pb.get_record("strategic_goals", goal_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Goal not found")

    pb.delete_record("strategic_goals", goal_id)

    return {"message": "Goal deleted"}
