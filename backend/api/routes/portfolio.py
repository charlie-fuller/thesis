"""Portfolio API Routes.

CRUD endpoints for AI Project Portfolio dashboard.
Projects are scoped to client_id via JWT authentication.
"""

import csv
import io
import logging
from typing import List, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

import pb_client as pb

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
):
    """Export portfolio projects as CSV."""
    parts = []
    if department:
        parts.append(f"department='{pb.escape_filter(department)}'")
    if status:
        parts.append(f"status='{pb.escape_filter(status)}'")
    if category:
        parts.append(f"category='{pb.escape_filter(category)}'")
    filter_str = " && ".join(parts)

    records = pb.get_all("portfolio_projects", filter=filter_str, sort="department,name")

    output = io.StringIO()
    fieldnames = [
        "name", "department", "owner", "status", "start_date",
        "effort", "investment", "business_value", "tools_platform",
        "category", "description",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for row in records:
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
):
    """Import portfolio projects from CSV."""
    content = await file.read()
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

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
        mapped = {}
        for csv_col, field_name in col_map.items():
            val = row.get(csv_col, "").strip()
            if val:
                mapped[field_name] = val

        if not mapped.get("name"):
            errors.append({"row": row_num, "error": "Missing required field: name"})
            continue
        if not mapped.get("department"):
            errors.append({"row": row_num, "error": "Missing required field: department"})
            continue

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

        try:
            pb.create_record("portfolio_projects", mapped)
            imported += 1
        except Exception as e:
            errors.append({"row": row_num, "error": str(e)})

    return {"imported": imported, "errors": errors}


@router.get("/projects", response_model=List[PortfolioProjectResponse])
async def list_projects(
    department: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
):
    """List portfolio projects, filterable by department, status, and category."""
    parts = []
    if department:
        parts.append(f"department='{pb.escape_filter(department)}'")
    if status:
        parts.append(f"status='{pb.escape_filter(status)}'")
    if category:
        parts.append(f"category='{pb.escape_filter(category)}'")
    filter_str = " && ".join(parts)

    return pb.get_all("portfolio_projects", filter=filter_str, sort="department,name")


@router.post("/projects", response_model=PortfolioProjectResponse)
async def create_project(
    project: PortfolioProjectCreate,
):
    """Create a new portfolio project."""
    data = project.model_dump()
    return pb.create_record("portfolio_projects", data)


@router.patch("/projects/{project_id}", response_model=PortfolioProjectResponse)
async def update_project(
    project_id: str,
    update: PortfolioProjectUpdate,
):
    """Update a portfolio project."""
    existing = pb.get_record("portfolio_projects", project_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = update.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    return pb.update_record("portfolio_projects", project_id, update_data)


@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: str,
):
    """Delete a portfolio project."""
    existing = pb.get_record("portfolio_projects", project_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Project not found")

    pb.delete_record("portfolio_projects", project_id)

    return {"message": "Project deleted"}
