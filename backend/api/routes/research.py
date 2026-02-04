"""Research API Routes.

Endpoints for managing Atlas proactive research:
- View and trigger research tasks
- Manage research schedules
- View knowledge gaps
- Access research sources
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field

from auth import get_current_user
from database import get_supabase
from logger_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/research", tags=["research"])

supabase = get_supabase()


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
    current_user: dict = Depends(get_current_user),
):
    """List research tasks.

    Filters:
    - status: pending, running, completed, failed
    - focus_area: strategic_planning, finance_roi, etc.
    """
    try:
        query = (
            supabase.table("research_tasks")
            .select("*")
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
        )

        if status:
            query = query.eq("status", status)
        if focus_area:
            query = query.eq("focus_area", focus_area)

        result = query.execute()

        return {"success": True, "tasks": result.data, "count": len(result.data)}

    except Exception as e:
        logger.error(f"Failed to list research tasks: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/tasks/{task_id}")
async def get_research_task(task_id: str, current_user: dict = Depends(get_current_user)):
    """Get details of a specific research task including full content."""
    try:
        result = supabase.table("research_tasks").select("*").eq("id", task_id).single().execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Research task not found")

        return {"success": True, "task": result.data}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get research task: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/trigger")
async def trigger_research(
    request: TriggerResearchRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
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
        supabase.table("research_tasks").insert(
            {
                "id": task_id,
                "topic": request.focus_area or "Custom research",
                "query": request.custom_query or f"Research {request.focus_area}",
                "focus_area": request.focus_area or "manual",
                "research_type": "manual",
                "status": "pending",
                "priority": 8,
                "client_id": request.client_id,
            }
        ).execute()

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
async def get_research_schedule(client_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """Get the research schedule.

    Returns both global schedule and client-specific schedule if client_id provided.
    """
    try:
        # Get global schedule
        global_result = (
            supabase.table("research_schedule")
            .select("*")
            .is_("client_id", "null")
            .order("day_of_week")
            .order("priority", desc=True)
            .execute()
        )

        schedules = []
        for item in global_result.data or []:
            item["is_global"] = True
            schedules.append(item)

        # Get client-specific schedule
        if client_id:
            client_result = (
                supabase.table("research_schedule")
                .select("*")
                .eq("client_id", client_id)
                .order("day_of_week")
                .order("priority", desc=True)
                .execute()
            )

            for item in client_result.data or []:
                item["is_global"] = False
                schedules.append(item)

        # Group by day
        by_day = {}
        day_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        for item in schedules:
            day = item["day_of_week"]
            day_name = day_names[day] if 0 <= day <= 6 else f"Day {day}"
            if day_name not in by_day:
                by_day[day_name] = []
            by_day[day_name].append(item)

        return {"success": True, "schedule": schedules, "by_day": by_day}

    except Exception as e:
        logger.error(f"Failed to get schedule: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.put("/schedule/{schedule_id}")
async def update_schedule_item(
    schedule_id: str, request: UpdateScheduleRequest, current_user: dict = Depends(get_current_user)
):
    """Update a schedule item (enable/disable, change time, etc.)."""
    try:
        update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}

        if request.is_active is not None:
            update_data["is_active"] = request.is_active
        if request.hour_utc is not None:
            update_data["hour_utc"] = request.hour_utc
        if request.query_template is not None:
            update_data["query_template"] = request.query_template
        if request.priority is not None:
            update_data["priority"] = request.priority

        result = supabase.table("research_schedule").update(update_data).eq("id", schedule_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Schedule item not found")

        return {"success": True, "schedule": result.data[0]}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update schedule: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# KNOWLEDGE GAPS ENDPOINTS
# ============================================================================


@router.get("/gaps")
async def list_knowledge_gaps(status: str = "open", limit: int = 20, current_user: dict = Depends(get_current_user)):
    """List knowledge gaps identified across agent conversations.

    These are questions/topics that agents couldn't fully answer.
    """
    try:
        result = (
            supabase.table("knowledge_gaps")
            .select("*")
            .eq("status", status)
            .order("priority", desc=True)
            .order("occurrence_count", desc=True)
            .limit(limit)
            .execute()
        )

        return {"success": True, "gaps": result.data, "count": len(result.data)}

    except Exception as e:
        logger.error(f"Failed to list knowledge gaps: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/gaps/{gap_id}/research")
async def research_gap(gap_id: str, background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    """Trigger research to fill a specific knowledge gap."""
    try:
        # Get the gap
        gap_result = supabase.table("knowledge_gaps").select("*").eq("id", gap_id).single().execute()

        if not gap_result.data:
            raise HTTPException(status_code=404, detail="Knowledge gap not found")

        gap = gap_result.data

        # Update gap status
        supabase.table("knowledge_gaps").update({"status": "researching"}).eq("id", gap_id).execute()

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
                    supabase.table("knowledge_gaps").update(
                        {
                            "status": "resolved",
                            "resolution_task_id": result.task_id,
                            "resolved_at": datetime.now(timezone.utc).isoformat(),
                        }
                    ).eq("id", gap_id).execute()
                else:
                    supabase.table("knowledge_gaps").update({"status": "open"}).eq("id", gap_id).execute()

            except Exception as e:
                logger.error(f"Gap research failed: {e}")
                supabase.table("knowledge_gaps").update({"status": "open"}).eq("id", gap_id).execute()

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
    current_user: dict = Depends(get_current_user),
):
    """List research sources with their credibility tiers.

    Tier 1: Top consulting/research (McKinsey, Gartner, HBR)
    Tier 2: Big 4, major tech
    Tier 3: Industry publications
    Tier 4: Blogs, vendor marketing
    """
    try:
        query = supabase.table("research_sources").select("*").order("credibility_tier").order("times_cited", desc=True)

        if tier:
            query = query.eq("credibility_tier", tier)
        if source_type:
            query = query.eq("source_type", source_type)

        result = query.execute()

        # Group by tier
        by_tier = {1: [], 2: [], 3: [], 4: []}
        for source in result.data or []:
            tier_num = source.get("credibility_tier", 3)
            if tier_num in by_tier:
                by_tier[tier_num].append(source)

        return {
            "success": True,
            "sources": result.data,
            "by_tier": by_tier,
            "count": len(result.data),
        }

    except Exception as e:
        logger.error(f"Failed to list sources: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# SCHEDULER STATUS ENDPOINTS
# ============================================================================


@router.get("/scheduler/status")
async def get_scheduler_status(current_user: dict = Depends(get_current_user)):
    """Get the current status of the research scheduler."""
    try:
        from services.research_scheduler import get_research_scheduler_status

        status = get_research_scheduler_status()

        # Get recent task stats
        recent_result = (
            supabase.table("research_tasks")
            .select("status")
            .gte(
                "created_at",
                (datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)).isoformat(),
            )
            .execute()
        )

        task_stats = {"pending": 0, "running": 0, "completed": 0, "failed": 0}
        for task in recent_result.data or []:
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
async def get_recent_insights(limit: int = 10, current_user: dict = Depends(get_current_user)):
    """Get recent research insights (summaries of completed research).

    Returns the most recent completed research with their summaries.
    """
    try:
        result = (
            supabase.table("research_tasks")
            .select("id, topic, focus_area, result_summary, completed_at, web_sources")
            .eq("status", "completed")
            .not_.is_("result_summary", "null")
            .order("completed_at", desc=True)
            .limit(limit)
            .execute()
        )

        return {"success": True, "insights": result.data, "count": len(result.data)}

    except Exception as e:
        logger.error(f"Failed to get insights: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e
