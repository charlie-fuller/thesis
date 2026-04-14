"""Research API Routes.

Endpoints for managing Atlas proactive research:
- View and trigger research tasks
- Manage research schedules
- View knowledge gaps
- Access research sources
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

import pb_client as pb
from logger_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/research", tags=["research"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class TriggerResearchRequest(BaseModel):
    """Request to manually trigger research."""

    focus_area: Optional[str] = Field(None, description="Focus area from schedule")
    custom_query: Optional[str] = Field(None, description="Custom research query")
    client_id: Optional[str] = Field(None, description="Client to research for")


class TriggerResearchResponse(BaseModel):
    """Response from triggering research."""

    success: bool
    task_id: str
    message: str


class ResearchTaskResponse(BaseModel):
    """Research task details."""

    id: str
    topic: str
    query: str
    focus_area: Optional[str]
    research_type: str
    status: str
    priority: int
    result_summary: Optional[str]
    created_at: str
    completed_at: Optional[str]


class ScheduleItemResponse(BaseModel):
    """Schedule item details."""

    id: str
    day_of_week: int
    hour_utc: int
    focus_area: str
    description: Optional[str]
    is_active: bool
    priority: int
    is_global: bool


class UpdateScheduleRequest(BaseModel):
    """Request to update a schedule item."""

    is_active: Optional[bool] = None
    hour_utc: Optional[int] = Field(None, ge=0, le=23)
    query_template: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=10)


class KnowledgeGapResponse(BaseModel):
    """Knowledge gap details."""

    id: str
    topic: str
    question: str
    source_agent: Optional[str]
    occurrence_count: int
    priority: int
    status: str
    created_at: str


class ResearchSourceResponse(BaseModel):
    """Research source details."""

    id: str
    domain: str
    name: Optional[str]
    credibility_tier: int
    source_type: Optional[str]
    times_cited: int


# ============================================================================
# RESEARCH TASKS ENDPOINTS
# ============================================================================


@router.get("/tasks")
async def list_research_tasks(
    status: Optional[str] = None,
    focus_area: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """List research tasks.

    Filters:
    - status: pending, running, completed, failed
    - focus_area: strategic_planning, finance_roi, etc.
    """
    try:
        filters = []
        if status:
            safe_status = pb.escape_filter(status)
            filters.append(f"status='{safe_status}'")
        if focus_area:
            safe_area = pb.escape_filter(focus_area)
            filters.append(f"focus_area='{safe_area}'")

        filter_str = " && ".join(filters) if filters else None

        # PocketBase uses page-based pagination
        page = (offset // limit) + 1 if limit > 0 else 1

        result = pb.list_records(
            "research_tasks",
            filter=filter_str,
            sort="-created",
            per_page=limit,
            page=page,
        )

        items = result.get("items", [])
        return {"success": True, "tasks": items, "count": len(items)}

    except Exception as e:
        logger.error(f"Failed to list research tasks: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/tasks/{task_id}")
async def get_research_task(task_id: str):
    """Get details of a specific research task including full content."""
    try:
        safe_id = pb.escape_filter(task_id)
        task = pb.get_first("research_tasks", filter=f"id='{safe_id}'")

        if not task:
            raise HTTPException(status_code=404, detail="Research task not found")

        return {"success": True, "task": task}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get research task: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/trigger")
async def trigger_research(
    request: TriggerResearchRequest,
    background_tasks: BackgroundTasks,
):
    """Manually trigger a research task.

    Provide either:
    - focus_area: Uses the scheduled query template for that focus area
    - custom_query: Uses your custom research query
    """
    try:
        from services.research_scheduler import trigger_research_now

        if not request.focus_area and not request.custom_query:
            raise HTTPException(status_code=400, detail="Must provide either focus_area or custom_query")

        # Run research in background
        async def run_research():
            try:
                result = await trigger_research_now(
                    focus_area=request.focus_area,
                    client_id=request.client_id,
                    custom_query=request.custom_query,
                )
                if not result.success:
                    logger.error(f"Research failed: {result.error}")
            except Exception as e:
                logger.error(f"Background research failed: {e}")

        # Get task ID before starting
        from uuid import uuid4

        task_id = str(uuid4())

        # Create task record first
        pb.create_record(
            "research_tasks",
            {
                "id": task_id,
                "topic": request.focus_area or "Custom research",
                "query": request.custom_query or f"Research {request.focus_area}",
                "focus_area": request.focus_area or "manual",
                "research_type": "manual",
                "status": "pending",
                "priority": 8,
                "client_id": request.client_id,
            },
        )

        background_tasks.add_task(run_research)

        return {
            "success": True,
            "task_id": task_id,
            "message": f"Research triggered for {request.focus_area or 'custom query'}",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger research: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# SCHEDULE ENDPOINTS
# ============================================================================


@router.get("/schedule")
async def get_research_schedule(client_id: Optional[str] = None):
    """Get the research schedule.

    Returns both global schedule and client-specific schedule if client_id provided.
    """
    try:
        # Get global schedule (client_id is empty/null)
        global_items = pb.get_all(
            "research_schedule",
            filter="client_id=''",
            sort="day_of_week,-priority",
        )

        schedules = []
        for item in global_items:
            item["is_global"] = True
            schedules.append(item)

        # Get client-specific schedule
        if client_id:
            safe_client = pb.escape_filter(client_id)
            client_items = pb.get_all(
                "research_schedule",
                filter=f"client_id='{safe_client}'",
                sort="day_of_week,-priority",
            )

            for item in client_items:
                item["is_global"] = False
                schedules.append(item)

        # Group by day
        by_day = {}
        day_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        for item in schedules:
            day = item.get("day_of_week", 0)
            day_name = day_names[day] if 0 <= day <= 6 else f"Day {day}"
            if day_name not in by_day:
                by_day[day_name] = []
            by_day[day_name].append(item)

        return {"success": True, "schedule": schedules, "by_day": by_day}

    except Exception as e:
        logger.error(f"Failed to get schedule: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.put("/schedule/{schedule_id}")
async def update_schedule_item(schedule_id: str, request: UpdateScheduleRequest):
    """Update a schedule item (enable/disable, change time, etc.)."""
    try:
        update_data = {}

        if request.is_active is not None:
            update_data["is_active"] = request.is_active
        if request.hour_utc is not None:
            update_data["hour_utc"] = request.hour_utc
        if request.query_template is not None:
            update_data["query_template"] = request.query_template
        if request.priority is not None:
            update_data["priority"] = request.priority

        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        result = pb.update_record("research_schedule", schedule_id, update_data)

        if not result:
            raise HTTPException(status_code=404, detail="Schedule item not found")

        return {"success": True, "schedule": result}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update schedule: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# KNOWLEDGE GAPS ENDPOINTS
# ============================================================================


@router.get("/gaps")
async def list_knowledge_gaps(status: str = "open", limit: int = 20):
    """List knowledge gaps identified across agent conversations.

    These are questions/topics that agents couldn't fully answer.
    """
    try:
        safe_status = pb.escape_filter(status)
        result = pb.list_records(
            "knowledge_gaps",
            filter=f"status='{safe_status}'",
            sort="-priority,-occurrence_count",
            per_page=limit,
        )

        items = result.get("items", [])
        return {"success": True, "gaps": items, "count": len(items)}

    except Exception as e:
        logger.error(f"Failed to list knowledge gaps: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/gaps/{gap_id}/research")
async def research_gap(gap_id: str, background_tasks: BackgroundTasks):
    """Trigger research to fill a specific knowledge gap."""
    try:
        # Get the gap
        safe_id = pb.escape_filter(gap_id)
        gap = pb.get_first("knowledge_gaps", filter=f"id='{safe_id}'")

        if not gap:
            raise HTTPException(status_code=404, detail="Knowledge gap not found")

        # Update gap status
        pb.update_record("knowledge_gaps", gap_id, {"status": "researching"})

        # Trigger research
        from services.research_scheduler import trigger_research_now

        async def run_gap_research():
            try:
                result = await trigger_research_now(
                    focus_area=gap.get("topic", "knowledge_gap"),
                    client_id=gap.get("client_id"),
                    custom_query=gap.get("question"),
                )

                # Update gap with resolution
                if result.success:
                    pb.update_record(
                        "knowledge_gaps",
                        gap_id,
                        {
                            "status": "resolved",
                            "resolution_task_id": result.task_id,
                            "resolved_at": datetime.now(timezone.utc).isoformat(),
                        },
                    )
                else:
                    pb.update_record("knowledge_gaps", gap_id, {"status": "open"})

            except Exception as e:
                logger.error(f"Gap research failed: {e}")
                pb.update_record("knowledge_gaps", gap_id, {"status": "open"})

        background_tasks.add_task(run_gap_research)

        return {"success": True, "message": f"Research triggered for gap: {gap.get('topic')}"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to research gap: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# SOURCES ENDPOINTS
# ============================================================================


@router.get("/sources")
async def list_research_sources(
    tier: Optional[int] = None,
    source_type: Optional[str] = None,
):
    """List research sources with their credibility tiers.

    Tier 1: Top consulting/research (McKinsey, Gartner, HBR)
    Tier 2: Big 4, major tech
    Tier 3: Industry publications
    Tier 4: Blogs, vendor marketing
    """
    try:
        filters = []
        if tier:
            filters.append(f"credibility_tier={tier}")
        if source_type:
            safe_type = pb.escape_filter(source_type)
            filters.append(f"source_type='{safe_type}'")

        filter_str = " && ".join(filters) if filters else None

        sources = pb.get_all(
            "research_sources",
            filter=filter_str,
            sort="credibility_tier,-times_cited",
        )

        # Group by tier
        by_tier = {1: [], 2: [], 3: [], 4: []}
        for source in sources:
            tier_num = source.get("credibility_tier", 3)
            if tier_num in by_tier:
                by_tier[tier_num].append(source)

        return {
            "success": True,
            "sources": sources,
            "by_tier": by_tier,
            "count": len(sources),
        }

    except Exception as e:
        logger.error(f"Failed to list sources: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# SCHEDULER STATUS ENDPOINTS
# ============================================================================


@router.get("/scheduler/status")
async def get_scheduler_status():
    """Get the current status of the research scheduler."""
    try:
        from services.research_scheduler import get_research_scheduler_status

        status = get_research_scheduler_status()

        # Get recent task stats (today)
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0).isoformat()
        recent_result = pb.list_records(
            "research_tasks",
            filter=f"created>='{today_start}'",
            fields="status",
            per_page=200,
        )

        task_stats = {"pending": 0, "running": 0, "completed": 0, "failed": 0}
        for task in recent_result.get("items", []):
            task_status = task.get("status", "unknown")
            if task_status in task_stats:
                task_stats[task_status] += 1

        return {"success": True, "scheduler": status, "today_stats": task_stats}

    except Exception as e:
        logger.error(f"Failed to get scheduler status: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# INSIGHTS ENDPOINT
# ============================================================================


@router.get("/insights")
async def get_recent_insights(limit: int = 10):
    """Get recent research insights (summaries of completed research).

    Returns the most recent completed research with their summaries.
    """
    try:
        result = pb.list_records(
            "research_tasks",
            filter="status='completed' && result_summary!=''",
            sort="-completed_at",
            per_page=limit,
            fields="id,topic,focus_area,result_summary,completed_at,web_sources",
        )

        items = result.get("items", [])
        return {"success": True, "insights": items, "count": len(items)}

    except Exception as e:
        logger.error(f"Failed to get insights: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e
