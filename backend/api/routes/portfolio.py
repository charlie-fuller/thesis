"""Portfolio API Routes.

CRUD endpoints for AI Project Portfolio dashboard.
Projects are scoped to client_id via JWT authentication.
"""

import csv
import io
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

from auth import get_current_user
from database import get_supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


# ============================================================================
# PYDANTIC MODELS
# ============================================================================


class PortfolioProjectCreate(BaseModel):
    """Create a new portfolio project."""

    name: str = Field(..., min_length=1, max_length=255)
    department: str = Field(..., min_length=1, max_length=100)
    owner: Optional[str] = Field(None, max_length=255)
    status: str = Field(default="planned", pattern="^(planned|in_progress|completed)$")
    start_date: Optional[str] = None
    effort: Optional[str] = Field(None, pattern="^(low|medium|high)$")
    investment: Optional[str] = Field(None, pattern="^(0-1k|1k-5k|5k-15k|15k-25k|25k\\+)$")
    business_value: Optional[str] = Field(None, pattern="^(low|medium|high|critical)$")
    tools_platform: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None


class PortfolioProjectUpdate(BaseModel):
    """Update a portfolio project. All fields optional."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    department: Optional[str] = Field(None, min_length=1, max_length=100)
    owner: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = Field(None, pattern="^(planned|in_progress|completed)$")
    start_date: Optional[str] = None
    effort: Optional[str] = Field(None, pattern="^(low|medium|high)$")
    investment: Optional[str] = Field(None, pattern="^(0-1k|1k-5k|5k-15k|15k-25k|25k\\+)$")
    business_value: Optional[str] = Field(None, pattern="^(low|medium|high|critical)$")
    tools_platform: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None


class PortfolioProjectResponse(BaseModel):
    """Portfolio project response model."""

    id: str
    client_id: str
    name: str
    department: str
    owner: Optional[str]
    status: str
    start_date: Optional[str]
    effort: Optional[str]
    investment: Optional[str]
    business_value: Optional[str]
    tools_platform: Optional[str]
    category: Optional[str]
    description: Optional[str]
    created_at: str
    updated_at: str


# ============================================================================
# CSV FIELD MAPPING
# ============================================================================

HEADER_MAP = {
    "name": "name",
    "project name": "name",
    "project_name": "name",
    "department": "department",
    "dept": "department",
    "owner": "owner",
    "status": "status",
    "start_date": "start_date",
    "start date": "start_date",
    "effort": "effort",
    "investment": "investment",
    "business_value": "business_value",
    "business value": "business_value",
    "value": "business_value",
    "tools_platform": "tools_platform",
    "tools": "tools_platform",
    "platform": "tools_platform",
    "category": "category",
    "description": "description",
}

VALID_STATUS = {"planned", "in_progress", "completed"}
VALID_EFFORT = {"low", "medium", "high"}
VALID_INVESTMENT = {"0-1k", "1k-5k", "5k-15k", "15k-25k", "25k+"}
VALID_BUSINESS_VALUE = {"low", "medium", "high", "critical"}


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.get("/projects/export")
async def export_projects(
    department: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Export portfolio projects as CSV."""
    query = (
        supabase.table("portfolio_projects")
        .select("*")
        .eq("client_id", current_user["client_id"])
    )

    if department:
        query = query.eq("department", department)
    if status:
        query = query.eq("status", status)
    if category:
        query = query.eq("category", category)

    result = query.order("department").order("name").execute()

    output = io.StringIO()
    fieldnames = [
        "name", "department", "owner", "status", "start_date",
        "effort", "investment", "business_value", "tools_platform",
        "category", "description",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for row in result.data or []:
        writer.writerow({field: row.get(field, "") for field in fieldnames})

    csv_content = output.getvalue()

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=portfolio_projects.csv"},
    )


@router.post("/projects/import")
async def import_projects(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Import portfolio projects from CSV."""
    content = await file.read()
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    # Map CSV headers to field names
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV file has no headers")

    col_map = {}
    for header in reader.fieldnames:
        normalized = header.strip().lower()
        if normalized in HEADER_MAP:
            col_map[header] = HEADER_MAP[normalized]

    imported = 0
    errors = []

    for row_num, row in enumerate(reader, start=2):
        # Map columns
        mapped = {}
        for csv_col, field_name in col_map.items():
            val = row.get(csv_col, "").strip()
            if val:
                mapped[field_name] = val

        # Validate required fields
        if not mapped.get("name"):
            errors.append({"row": row_num, "error": "Missing required field: name"})
            continue
        if not mapped.get("department"):
            errors.append({"row": row_num, "error": "Missing required field: department"})
            continue

        # Validate enum fields
        if mapped.get("status") and mapped["status"] not in VALID_STATUS:
            errors.append({"row": row_num, "error": f"Invalid status: {mapped['status']}"})
            continue
        if mapped.get("effort") and mapped["effort"] not in VALID_EFFORT:
            errors.append({"row": row_num, "error": f"Invalid effort: {mapped['effort']}"})
            continue
        if mapped.get("investment") and mapped["investment"] not in VALID_INVESTMENT:
            errors.append({"row": row_num, "error": f"Invalid investment: {mapped['investment']}"})
            continue
        if mapped.get("business_value") and mapped["business_value"] not in VALID_BUSINESS_VALUE:
            errors.append({"row": row_num, "error": f"Invalid business_value: {mapped['business_value']}"})
            continue

        # Insert
        data = {
            "client_id": current_user["client_id"],
            **mapped,
        }

        try:
            supabase.table("portfolio_projects").insert(data).execute()
            imported += 1
        except Exception as e:
            errors.append({"row": row_num, "error": str(e)})

    return {"imported": imported, "errors": errors}


@router.get("/projects", response_model=List[PortfolioProjectResponse])
async def list_projects(
    department: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """List portfolio projects, filterable by department, status, and category."""
    query = (
        supabase.table("portfolio_projects")
        .select("*")
        .eq("client_id", current_user["client_id"])
    )

    if department:
        query = query.eq("department", department)
    if status:
        query = query.eq("status", status)
    if category:
        query = query.eq("category", category)

    result = query.order("department").order("name").execute()

    return result.data or []


@router.post("/projects", response_model=PortfolioProjectResponse)
async def create_project(
    project: PortfolioProjectCreate,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Create a new portfolio project."""
    data = {
        "client_id": current_user["client_id"],
        **project.model_dump(),
    }

    result = supabase.table("portfolio_projects").insert(data).execute()

    return result.data[0]


@router.patch("/projects/{project_id}", response_model=PortfolioProjectResponse)
async def update_project(
    project_id: str,
    update: PortfolioProjectUpdate,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Update a portfolio project."""
    # Verify ownership
    existing = (
        supabase.table("portfolio_projects")
        .select("id")
        .eq("id", project_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not existing.data:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = update.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = (
        supabase.table("portfolio_projects")
        .update(update_data)
        .eq("id", project_id)
        .execute()
    )

    return result.data[0]


@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Delete a portfolio project."""
    existing = (
        supabase.table("portfolio_projects")
        .select("id")
        .eq("id", project_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not existing.data:
        raise HTTPException(status_code=404, detail="Project not found")

    supabase.table("portfolio_projects").delete().eq("id", project_id).execute()

    return {"message": "Project deleted"}
