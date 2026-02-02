"""Task management routes
Handles task CRUD, Kanban board operations, and task extraction from transcripts
"""

import asyncio
from datetime import date, datetime, timezone
from enum import Enum
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from auth import get_current_user
from config import get_default_client_id
from database import get_supabase
from logger_config import get_logger
from validation import validate_uuid

logger = get_logger(__name__)
router = APIRouter(prefix="/api/tasks", tags=["tasks"])
supabase = get_supabase()


# ============================================================================
# Enums and Models
# ============================================================================


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"


class TaskSourceType(str, Enum):
    TRANSCRIPT = "transcript"
    CONVERSATION = "conversation"
    RESEARCH = "research"
    PROJECT = "project"
    MANUAL = "manual"


class TaskTeam(str, Enum):
    FINANCE = "Finance"
    LEGAL = "Legal"
    IT = "IT"
    OPERATIONS = "Operations"
    HR = "HR"
    MARKETING = "Marketing"
    SALES = "Sales"
    ENGINEERING = "Engineering"
    EXECUTIVE = "Executive"
    OTHER = "Other"


class TaskCreate(BaseModel):
    """Request body for creating a task."""

    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: int = Field(default=3, ge=1, le=5)
    assignee_stakeholder_id: Optional[str] = None
    assignee_user_id: Optional[str] = None
    assignee_name: Optional[str] = None
    due_date: Optional[date] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    team: Optional[str] = None
    related_stakeholder_ids: Optional[List[str]] = None
    related_project_id: Optional[str] = None
    linked_project_id: Optional[str] = None  # Parent project
    source_type: TaskSourceType = TaskSourceType.MANUAL
    source_transcript_id: Optional[str] = None
    source_conversation_id: Optional[str] = None
    source_research_task_id: Optional[str] = None
    source_project_id: Optional[str] = None
    source_text: Optional[str] = None
    blocker_reason: Optional[str] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()

    @field_validator("description", "blocker_reason", "category", "assignee_name")
    @classmethod
    def strip_strings(cls, v):
        if v:
            return v.strip()
        return v


class TaskUpdate(BaseModel):
    """Request body for updating a task."""

    title: Optional[str] = Field(default=None, max_length=500)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[int] = Field(default=None, ge=1, le=5)
    assignee_stakeholder_id: Optional[str] = None
    assignee_user_id: Optional[str] = None
    assignee_name: Optional[str] = None
    due_date: Optional[date] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    team: Optional[str] = None
    blocker_reason: Optional[str] = None
    related_project_id: Optional[str] = None
    linked_project_id: Optional[str] = None  # Parent project

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip() if v else v


class TaskStatusUpdate(BaseModel):
    """Request body for updating task status (Kanban drag-drop)."""

    status: TaskStatus
    position: Optional[int] = None
    blocker_reason: Optional[str] = None  # Required if status = blocked


class TaskReorderItem(BaseModel):
    """Single task reorder item."""

    task_id: str
    status: TaskStatus
    position: int


class TaskBulkReorderRequest(BaseModel):
    """Request body for bulk reordering tasks."""

    tasks: List[TaskReorderItem]


class TaskCommentCreate(BaseModel):
    """Request body for creating a task comment."""

    content: str = Field(..., min_length=1)

    @field_validator("content")
    @classmethod
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError("Content cannot be empty")
        return v.strip()


# ============================================================================
# Helper Functions
# ============================================================================


def serialize_task(task: dict) -> dict:
    """Convert task record to API response format."""
    # Handle due_date - may be string (from Supabase) or date object
    due_date = task.get("due_date")
    if due_date:
        due_date = due_date.isoformat() if hasattr(due_date, "isoformat") else str(due_date)

    return {
        "id": task["id"],
        "client_id": task["client_id"],
        "title": task["title"],
        "description": task.get("description"),
        "status": task["status"],
        "priority": task["priority"],
        "assignee_stakeholder_id": task.get("assignee_stakeholder_id"),
        "assignee_user_id": task.get("assignee_user_id"),
        "assignee_name": task.get("assignee_name"),
        "due_date": due_date,
        "completed_at": task.get("completed_at"),
        "source_type": task.get("source_type"),
        "source_transcript_id": task.get("source_transcript_id"),
        "source_conversation_id": task.get("source_conversation_id"),
        "source_research_task_id": task.get("source_research_task_id"),
        "source_project_id": task.get("source_project_id"),
        "category": task.get("category"),
        "tags": task.get("tags") or [],
        "team": task.get("team"),
        "blocker_reason": task.get("blocker_reason"),
        "blocked_at": task.get("blocked_at"),
        "related_project_id": task.get("related_project_id"),
        "linked_project_id": task.get("linked_project_id"),
        "position": task.get("position", 0),
        "created_at": task["created_at"],
        "updated_at": task["updated_at"],
        # Joined fields (from view or explicit joins)
        "stakeholder_name": task.get("stakeholder_name"),
        "stakeholder_email": task.get("stakeholder_email"),
        "user_email": task.get("user_email"),
        "display_assignee": task.get("display_assignee") or task.get("assignee_name"),
    }


async def get_next_position(client_id: str, status: str) -> int:
    """Get the next position for a task in a status column."""
    result = await asyncio.to_thread(
        lambda: supabase.table("project_tasks")
        .select("position")
        .eq("client_id", client_id)
        .eq("status", status)
        .order("position", desc=True)
        .limit(1)
        .execute()
    )
    if result.data:
        return result.data[0]["position"] + 1
    return 0


# ============================================================================
# Static Routes (MUST be defined before parameterized routes like /{task_id})
# ============================================================================


@router.get("/kanban")
async def get_kanban_board(
    current_user: dict = Depends(get_current_user),
    assignee_stakeholder_id: Optional[str] = Query(None),
    assignee_user_id: Optional[str] = Query(None),
    due_date_from: Optional[date] = Query(None),
    due_date_to: Optional[date] = Query(None),
    priority: Optional[List[int]] = Query(None),
    source_type: Optional[List[str]] = Query(None),
    category: Optional[str] = Query(None),
    team: Optional[str] = Query(None, description="Filter by team/department"),
    linked_project_id: Optional[str] = Query(None, description="Filter by linked project"),
    search: Optional[str] = Query(None),
    include_completed: bool = Query(True),
):
    """Get tasks grouped by status for Kanban board display."""
    try:
        client_id = current_user.get("client_id") or get_default_client_id()

        # Build query using view for joined data
        query = supabase.table("v_tasks_with_assignee").select("*").eq("client_id", client_id)

        # Apply filters
        if assignee_stakeholder_id:
            validate_uuid(assignee_stakeholder_id, "assignee_stakeholder_id")
            query = query.eq("assignee_stakeholder_id", assignee_stakeholder_id)

        if assignee_user_id:
            validate_uuid(assignee_user_id, "assignee_user_id")
            query = query.eq("assignee_user_id", assignee_user_id)

        if due_date_from:
            query = query.gte("due_date", due_date_from.isoformat())

        if due_date_to:
            query = query.lte("due_date", due_date_to.isoformat())

        if priority:
            query = query.in_("priority", priority)

        if source_type:
            query = query.in_("source_type", source_type)

        if category:
            query = query.eq("category", category)

        if team:
            query = query.eq("team", team)

        if linked_project_id:
            validate_uuid(linked_project_id, "linked_project_id")
            query = query.eq("linked_project_id", linked_project_id)

        if not include_completed:
            query = query.neq("status", "completed")

        # Order by position within status
        query = query.order("status").order("position")

        result = await asyncio.to_thread(lambda: query.execute())

        tasks = result.data or []

        # Filter by search term (client-side for flexibility)
        if search:
            search_lower = search.lower()
            tasks = [
                t
                for t in tasks
                if search_lower in (t.get("title") or "").lower()
                or search_lower in (t.get("description") or "").lower()
            ]

        # Group tasks by status
        columns = {"pending": [], "in_progress": [], "blocked": [], "completed": []}

        for task in tasks:
            status = task.get("status", "pending")
            if status in columns:
                columns[status].append(serialize_task(task))

        # Count tasks
        counts = {status: len(tasks_list) for status, tasks_list in columns.items()}
        counts["total"] = sum(counts.values())
        counts["overdue"] = len(
            [
                t
                for t in tasks
                if t.get("due_date")
                and t["due_date"] < datetime.now(timezone.utc).date().isoformat()
                and t["status"] != "completed"
            ]
        )

        return {
            "success": True,
            "columns": columns,
            "counts": counts,
            "filters_applied": {
                "assignee_stakeholder_id": assignee_stakeholder_id,
                "assignee_user_id": assignee_user_id,
                "due_date_from": due_date_from.isoformat() if due_date_from else None,
                "due_date_to": due_date_to.isoformat() if due_date_to else None,
                "priority": priority,
                "source_type": source_type,
                "category": category,
                "team": team,
                "linked_project_id": linked_project_id,
                "search": search,
                "include_completed": include_completed,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching kanban board: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.post("/reorder")
async def reorder_tasks(
    request: TaskBulkReorderRequest, current_user: dict = Depends(get_current_user)
):
    """Bulk reorder tasks (for Kanban drag-drop reordering within columns)."""
    try:
        client_id = current_user.get("client_id") or get_default_client_id()
        user_id = current_user["id"]

        updated_count = 0
        errors = []

        for item in request.tasks:
            try:
                validate_uuid(item.task_id, "task_id")

                result = await asyncio.to_thread(
                    lambda tid=item.task_id, s=item.status.value, p=item.position: supabase.table(
                        "project_tasks"
                    )
                    .update({"status": s, "position": p, "updated_by": user_id})
                    .eq("id", tid)
                    .eq("client_id", client_id)
                    .execute()
                )

                if result.data:
                    updated_count += 1
                else:
                    errors.append({"task_id": item.task_id, "error": "Task not found"})

            except Exception as e:
                errors.append({"task_id": item.task_id, "error": str(e)})

        return {
            "success": True,
            "updated_count": updated_count,
            "errors": errors,
            "message": f"Reordered {updated_count} tasks",
        }

    except Exception as e:
        logger.error(f"Error reordering tasks: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.post("/extract/transcript/{transcript_id}")
async def extract_tasks_from_transcript(
    transcript_id: str, current_user: dict = Depends(get_current_user)
):
    """Extract tasks from a meeting transcript's action_items."""
    try:
        validate_uuid(transcript_id, "transcript_id")
        client_id = current_user.get("client_id") or get_default_client_id()
        user_id = current_user["id"]

        # Get transcript with action_items
        transcript_result = await asyncio.to_thread(
            lambda: supabase.table("meeting_transcripts")
            .select("id, title, action_items, client_id")
            .eq("id", transcript_id)
            .single()
            .execute()
        )

        if not transcript_result.data:
            raise HTTPException(status_code=404, detail="Transcript not found")

        transcript = transcript_result.data

        # Verify client access
        if transcript["client_id"] != client_id:
            raise HTTPException(status_code=403, detail="Not authorized to access this transcript")

        action_items = transcript.get("action_items") or []

        if not action_items:
            return {
                "success": True,
                "tasks_created": 0,
                "tasks_skipped": 0,
                "message": "No action items found in transcript",
            }

        tasks_created = 0
        tasks_skipped = 0
        created_tasks = []

        for item in action_items:
            description = item.get("description", "").strip()
            if not description:
                tasks_skipped += 1
                continue

            # Check for duplicate by source_text
            existing = await asyncio.to_thread(
                lambda desc=description: supabase.table("project_tasks")
                .select("id")
                .eq("client_id", client_id)
                .eq("source_transcript_id", transcript_id)
                .eq("source_text", desc)
                .limit(1)
                .execute()
            )

            if existing.data:
                tasks_skipped += 1
                continue

            # Parse due date if present
            due_date = None
            due_date_str = item.get("due_date")
            if due_date_str:
                try:
                    due_date = (
                        datetime.fromisoformat(due_date_str.replace("Z", "+00:00"))
                        .date()
                        .isoformat()
                    )
                except (ValueError, AttributeError):
                    pass

            # Get next position
            position = await get_next_position(client_id, "pending")

            task_record = {
                "client_id": client_id,
                "title": description[:500],  # Truncate to max length
                "description": f"Extracted from: {transcript.get('title', 'Meeting')}",
                "status": "pending",
                "priority": 3,
                "assignee_name": item.get("owner"),
                "due_date": due_date,
                "source_type": "transcript",
                "source_transcript_id": transcript_id,
                "source_text": description,
                "source_extracted_at": datetime.now(timezone.utc).isoformat(),
                "category": "meeting_action",
                "created_by": user_id,
                "updated_by": user_id,
                "position": position,
            }

            result = await asyncio.to_thread(
                lambda rec=task_record: supabase.table("project_tasks").insert(rec).execute()
            )

            if result.data:
                tasks_created += 1
                created_tasks.append(serialize_task(result.data[0]))

        logger.info(f"Extracted {tasks_created} tasks from transcript {transcript_id}")

        return {
            "success": True,
            "tasks_created": tasks_created,
            "tasks_skipped": tasks_skipped,
            "tasks": created_tasks,
            "message": f"Created {tasks_created} tasks, skipped {tasks_skipped} (duplicates or empty)",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting tasks from transcript: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


# ============================================================================
# Task List with Filters
# ============================================================================


@router.get("")
async def list_tasks(
    current_user: dict = Depends(get_current_user),
    status: Optional[List[str]] = Query(None),
    assignee_stakeholder_id: Optional[str] = Query(None),
    assignee_user_id: Optional[str] = Query(None),
    due_date_from: Optional[date] = Query(None),
    due_date_to: Optional[date] = Query(None),
    priority: Optional[List[int]] = Query(None),
    source_type: Optional[List[str]] = Query(None),
    category: Optional[str] = Query(None),
    team: Optional[str] = Query(None, description="Filter by team/department"),
    linked_project_id: Optional[str] = Query(None, description="Filter by linked project"),
    search: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    order_by: str = Query("created_at"),
    order_dir: str = Query("desc"),
):
    """List tasks with filtering, pagination, and sorting."""
    try:
        client_id = current_user.get("client_id") or get_default_client_id()

        # Build query
        query = (
            supabase.table("v_tasks_with_assignee")
            .select("*", count="exact")
            .eq("client_id", client_id)
        )

        # Apply filters
        if status:
            query = query.in_("status", status)

        if assignee_stakeholder_id:
            validate_uuid(assignee_stakeholder_id, "assignee_stakeholder_id")
            query = query.eq("assignee_stakeholder_id", assignee_stakeholder_id)

        if assignee_user_id:
            validate_uuid(assignee_user_id, "assignee_user_id")
            query = query.eq("assignee_user_id", assignee_user_id)

        if due_date_from:
            query = query.gte("due_date", due_date_from.isoformat())

        if due_date_to:
            query = query.lte("due_date", due_date_to.isoformat())

        if priority:
            query = query.in_("priority", priority)

        if source_type:
            query = query.in_("source_type", source_type)

        if category:
            query = query.eq("category", category)

        if team:
            query = query.eq("team", team)

        if linked_project_id:
            validate_uuid(linked_project_id, "linked_project_id")
            query = query.eq("linked_project_id", linked_project_id)

        # Apply ordering
        valid_order_fields = [
            "created_at",
            "updated_at",
            "due_date",
            "priority",
            "position",
            "title",
        ]
        if order_by not in valid_order_fields:
            order_by = "created_at"
        desc = order_dir.lower() == "desc"
        query = query.order(order_by, desc=desc)

        # Apply pagination
        query = query.limit(limit).offset(offset)

        result = await asyncio.to_thread(lambda: query.execute())

        tasks = result.data or []
        total = result.count or len(tasks)

        # Filter by search term (client-side)
        if search:
            search_lower = search.lower()
            tasks = [
                t
                for t in tasks
                if search_lower in (t.get("title") or "").lower()
                or search_lower in (t.get("description") or "").lower()
            ]

        return {
            "success": True,
            "tasks": [serialize_task(t) for t in tasks],
            "total": total,
            "limit": limit,
            "offset": offset,
            "filters_applied": {
                "status": status,
                "assignee_stakeholder_id": assignee_stakeholder_id,
                "assignee_user_id": assignee_user_id,
                "due_date_from": due_date_from.isoformat() if due_date_from else None,
                "due_date_to": due_date_to.isoformat() if due_date_to else None,
                "priority": priority,
                "source_type": source_type,
                "category": category,
                "team": team,
                "linked_project_id": linked_project_id,
                "search": search,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing tasks: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


# ============================================================================
# Task CRUD Operations (parameterized routes MUST come after static routes)
# ============================================================================


@router.post("")
async def create_task(request: TaskCreate, current_user: dict = Depends(get_current_user)):
    """Create a new task."""
    try:
        client_id = current_user.get("client_id") or get_default_client_id()
        user_id = current_user["id"]

        # Validate foreign keys if provided
        if request.assignee_stakeholder_id:
            validate_uuid(request.assignee_stakeholder_id, "assignee_stakeholder_id")
        if request.assignee_user_id:
            validate_uuid(request.assignee_user_id, "assignee_user_id")
        if request.related_project_id:
            validate_uuid(request.related_project_id, "related_project_id")
        if request.linked_project_id:
            validate_uuid(request.linked_project_id, "linked_project_id")
        if request.source_transcript_id:
            validate_uuid(request.source_transcript_id, "source_transcript_id")
        if request.source_conversation_id:
            validate_uuid(request.source_conversation_id, "source_conversation_id")

        # Get next position in the status column
        position = await get_next_position(client_id, request.status.value)

        # Build task record
        task_record = {
            "client_id": client_id,
            "title": request.title,
            "description": request.description,
            "status": request.status.value,
            "priority": request.priority,
            "assignee_stakeholder_id": request.assignee_stakeholder_id,
            "assignee_user_id": request.assignee_user_id,
            "assignee_name": request.assignee_name,
            "due_date": request.due_date.isoformat() if request.due_date else None,
            "category": request.category,
            "tags": request.tags or [],
            "team": request.team,
            "related_stakeholder_ids": request.related_stakeholder_ids or [],
            "related_project_id": request.related_project_id,
            "linked_project_id": request.linked_project_id,
            "source_type": request.source_type.value,
            "source_transcript_id": request.source_transcript_id,
            "source_conversation_id": request.source_conversation_id,
            "source_research_task_id": request.source_research_task_id,
            "source_project_id": request.source_project_id,
            "source_text": request.source_text,
            "source_extracted_at": datetime.now(timezone.utc).isoformat()
            if request.source_text
            else None,
            "blocker_reason": request.blocker_reason
            if request.status == TaskStatus.BLOCKED
            else None,
            "blocked_at": datetime.now(timezone.utc).isoformat()
            if request.status == TaskStatus.BLOCKED
            else None,
            "created_by": user_id,
            "updated_by": user_id,
            "position": position,
        }

        result = await asyncio.to_thread(
            lambda: supabase.table("project_tasks").insert(task_record).execute()
        )

        task = result.data[0]
        logger.info(f"Task created: {task['id']}")

        return {
            "success": True,
            "task": serialize_task(task),
            "message": "Task created successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating task: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


# ============================================================================
# Task Candidates (Auto-extracted from documents)
# IMPORTANT: These routes must be defined BEFORE /{task_id} to avoid route conflicts
# ============================================================================


class CandidateAction(BaseModel):
    """Request body for accepting/rejecting a candidate."""

    overrides: Optional[dict] = None  # For accept: {title, priority, due_date}
    reason: Optional[str] = None  # For reject


class LinkCandidateRequest(BaseModel):
    """Request body for linking a candidate to an existing item."""

    task_id: str


class BulkCandidateAction(BaseModel):
    """Request body for bulk accept/reject."""

    candidate_ids: List[str]
    action: str = Field(..., pattern="^(accept|reject)$")


@router.get("/candidates")
async def get_task_candidates(
    current_user=Depends(get_current_user),
    limit: int = Query(default=20, le=50),
    status: str = Query(default="pending", pattern="^(pending|accepted|rejected|all)$"),
):
    """Get task candidates extracted from documents.

    These are potential tasks that Taskmaster found in uploaded documents.
    Users can accept or reject them.
    """
    try:
        client_id = current_user.get("client_id") or get_default_client_id()

        query = (
            supabase.table("task_candidates")
            .select("*, documents(filename, title)")
            .eq("client_id", client_id)
        )

        if status != "all":
            query = query.eq("status", status)

        result = await asyncio.to_thread(
            lambda: query.order("created_at", desc=True).limit(limit).execute()
        )

        candidates = []
        for c in result.data or []:
            doc = c.get("documents", {}) or {}
            candidates.append(
                {
                    "id": c["id"],
                    "title": c["title"],
                    "suggested_priority": c["suggested_priority"],
                    "suggested_due_date": c["suggested_due_date"],
                    "due_date_text": c["due_date_text"],
                    "assignee_name": c["assignee_name"],
                    "source_document_id": c["source_document_id"],
                    "source_document_name": doc.get("title")
                    or doc.get("filename")
                    or c.get("source_document_name"),
                    "source_text": c["source_text"],
                    "confidence": c["confidence"],
                    "status": c["status"],
                    "created_at": c["created_at"],
                    # Rich context fields (from migration 029)
                    "description": c.get("description"),
                    "meeting_context": c.get("meeting_context"),
                    "team": c.get("team"),
                    "stakeholder_name": c.get("stakeholder_name"),
                    "value_proposition": c.get("value_proposition"),
                    "document_date": c.get("document_date"),
                    "topics": c.get("topics"),
                }
            )

        return {"success": True, "candidates": candidates, "count": len(candidates)}

    except Exception as e:
        logger.error(f"Error fetching task candidates: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.get("/candidates/count")
async def get_candidate_count(current_user=Depends(get_current_user)):
    """Get count of pending task candidates (for badge display)."""
    try:
        client_id = current_user.get("client_id") or get_default_client_id()

        result = await asyncio.to_thread(
            lambda: supabase.table("task_candidates")
            .select("id", count="exact")
            .eq("client_id", client_id)
            .eq("status", "pending")
            .execute()
        )

        return {"success": True, "pending_count": result.count or 0}

    except Exception as e:
        logger.error(f"Error fetching candidate count: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.delete("/candidates/clear")
async def clear_task_candidates(
    status: Optional[str] = Query(
        None, description="Filter by status: pending, accepted, rejected, or all"
    ),
    current_user=Depends(get_current_user),
):
    """Clear task candidates. By default clears pending candidates only.
    Use status=all to clear all candidates.
    """
    try:
        client_id = current_user.get("client_id") or get_default_client_id()

        query = supabase.table("task_candidates").delete().eq("client_id", client_id)

        if status and status != "all":
            query = query.eq("status", status)

        result = query.execute()
        deleted_count = len(result.data) if result.data else 0

        return {
            "success": True,
            "deleted_count": deleted_count,
            "status_filter": status or "pending",
        }

    except Exception as e:
        logger.error(f"Error clearing task candidates: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.post("/candidates/{candidate_id}/accept")
async def accept_task_candidate(
    candidate_id: str,
    body: Optional[CandidateAction] = None,
    current_user=Depends(get_current_user),
):
    """Accept a task candidate and create an actual task.

    Optionally provide overrides for title, priority, or due_date.
    """
    try:
        validate_uuid(candidate_id, "candidate_id")

        from services.task_auto_extractor import accept_task_candidate as do_accept

        result = await do_accept(
            candidate_id=candidate_id,
            user_id=current_user["id"],
            supabase=supabase,
            overrides=body.overrides if body else None,
        )

        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))

        return {"success": True, "task_id": result.get("task_id"), "title": result.get("title")}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error accepting task candidate: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.post("/candidates/{candidate_id}/reject")
async def reject_task_candidate(
    candidate_id: str,
    body: Optional[CandidateAction] = None,
    current_user=Depends(get_current_user),
):
    """Reject a task candidate."""
    try:
        validate_uuid(candidate_id, "candidate_id")

        from services.task_auto_extractor import reject_task_candidate as do_reject

        result = await do_reject(
            candidate_id=candidate_id,
            user_id=current_user["id"],
            supabase=supabase,
            reason=body.reason if body else None,
        )

        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))

        return {"success": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting task candidate: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.post("/candidates/{candidate_id}/link")
async def link_task_candidate(
    candidate_id: str, body: LinkCandidateRequest, current_user=Depends(get_current_user)
):
    """Link a task candidate to an existing task instead of creating a new one.

    This is used when a duplicate is detected and the user wants to associate
    the candidate's context with an existing task rather than creating a new one.
    """
    try:
        validate_uuid(candidate_id, "candidate_id")
        validate_uuid(body.task_id, "task_id")
        client_id = current_user.get("client_id") or get_default_client_id()
        user_id = current_user["id"]

        # Get the candidate
        candidate_result = await asyncio.to_thread(
            lambda: supabase.table("task_candidates")
            .select("*")
            .eq("id", candidate_id)
            .eq("client_id", client_id)
            .single()
            .execute()
        )

        if not candidate_result.data:
            raise HTTPException(status_code=404, detail="Task candidate not found")

        candidate = candidate_result.data

        # Verify target task exists
        task_result = await asyncio.to_thread(
            lambda: supabase.table("project_tasks")
            .select("id, title, description")
            .eq("id", body.task_id)
            .eq("client_id", client_id)
            .single()
            .execute()
        )

        if not task_result.data:
            raise HTTPException(status_code=404, detail="Target task not found")

        task = task_result.data

        # Append candidate context to the existing task's description
        existing_desc = task.get("description") or ""
        candidate_context = candidate.get("meeting_context") or ""
        candidate_source = candidate.get("source_document_name") or ""

        if candidate_context or candidate_source:
            linked_note = f"\n\n---\nLinked from meeting: {candidate_source}"
            if candidate_context:
                linked_note += f"\nContext: {candidate_context}"
            new_description = existing_desc + linked_note

            await asyncio.to_thread(
                lambda: supabase.table("project_tasks")
                .update({"description": new_description, "updated_by": user_id})
                .eq("id", body.task_id)
                .execute()
            )

        # Mark candidate as accepted with reference to the linked task
        await asyncio.to_thread(
            lambda: supabase.table("task_candidates")
            .update(
                {
                    "status": "accepted",
                    "created_task_id": body.task_id,
                    "reviewed_at": datetime.now(timezone.utc).isoformat(),
                    "reviewed_by": user_id,
                }
            )
            .eq("id", candidate_id)
            .execute()
        )

        logger.info(f"Task candidate {candidate_id} linked to existing task {body.task_id}")

        return {
            "success": True,
            "linked_task_id": body.task_id,
            "linked_task_title": task["title"],
            "message": f"Linked to existing task: {task['title']}",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error linking task candidate: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.post("/candidates/bulk")
async def bulk_action_candidates(body: BulkCandidateAction, current_user=Depends(get_current_user)):
    """Accept or reject multiple task candidates at once."""
    try:
        for cid in body.candidate_ids:
            validate_uuid(cid, "candidate_id")

        from services.task_auto_extractor import bulk_action_candidates as do_bulk

        result = await do_bulk(
            candidate_ids=body.candidate_ids,
            action=body.action,
            user_id=current_user["id"],
            supabase=supabase,
        )

        return {
            "success": True,
            "action": body.action,
            "processed": result.get("success", 0),
            "failed": result.get("failed", 0),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk candidate action: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


# ============================================================================
# Document Scanning for Tasks
# ============================================================================


@router.get("/scan-stats")
async def get_scan_stats(current_user=Depends(get_current_user)):
    """Get scan statistics including last scan time, document counts, and pending candidates."""
    try:
        client_id = current_user.get("client_id") or get_default_client_id()

        # Get total document count
        docs_result = (
            supabase.table("documents")
            .select("id", count="exact")
            .eq("client_id", client_id)
            .execute()
        )
        total_docs = docs_result.count or 0

        # Get documents with original_date (scannable)
        from datetime import datetime, timedelta, timezone

        thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).date().isoformat()
        recent_docs_result = (
            supabase.table("documents")
            .select("id", count="exact")
            .eq("client_id", client_id)
            .gte("original_date", thirty_days_ago)
            .execute()
        )
        recent_docs = recent_docs_result.count or 0

        # Get pending candidate count
        candidates_result = (
            supabase.table("task_candidates")
            .select("id", count="exact")
            .eq("client_id", client_id)
            .eq("status", "pending")
            .execute()
        )
        pending_candidates = candidates_result.count or 0

        # Get last scan time (most recent candidate created_at)
        last_scan_result = (
            supabase.table("task_candidates")
            .select("created_at")
            .eq("client_id", client_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        last_scan = last_scan_result.data[0]["created_at"] if last_scan_result.data else None

        # Get documents that have been scanned (have candidates)
        scanned_docs_result = (
            supabase.table("task_candidates")
            .select("source_document_id")
            .eq("client_id", client_id)
            .execute()
        )
        scanned_doc_ids = set(c["source_document_id"] for c in (scanned_docs_result.data or []))

        return {
            "total_documents": total_docs,
            "recent_documents_30d": recent_docs,
            "pending_candidates": pending_candidates,
            "last_scan_at": last_scan,
            "documents_scanned_ever": len(scanned_doc_ids),
        }

    except Exception as e:
        logger.error(f"Error getting scan stats: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


# Meeting summaries folder path - only scan these for tasks
# Note: Path is case-sensitive, matches Obsidian vault structure
MEETING_SUMMARIES_FOLDER = "Granola/Meeting-summaries"


@router.post("/scan-documents")
async def scan_documents_for_tasks(
    limit: int = Query(5, ge=1, le=50, description="Number of recent documents to scan (max 50)"),
    since_days: int = Query(
        7, ge=1, le=365, description="Only scan documents with original_date in the last N days"
    ),
    force_rescan: bool = Query(False, description="Rescan documents even if already scanned"),
    current_user=Depends(get_current_user),
):
    """Scan meeting summary documents for potential tasks.

    Only scans documents in the granola/meeting-summaries folder, which contain
    structured meeting summaries ideal for task extraction. By default only
    scans documents that haven't been scanned yet.

    Uses Claude Sonnet for high-quality extraction.

    Args:
        limit: Max number of documents to scan (1-50, default 10)
        since_days: Only scan documents with original_date in the last N days
        force_rescan: If true, rescan even previously scanned documents
    """
    try:
        client_id = current_user.get("client_id") or get_default_client_id()
        user_id = current_user["id"]

        # Get user's name for task filtering
        user_result = supabase.table("users").select("*").eq("id", user_id).single().execute()

        user_name = None
        if user_result.data:
            user_name = (
                user_result.data.get("full_name")
                or user_result.data.get("name")
                or user_result.data.get("email", "").split("@")[0]
            )

        # Build query for meeting summary documents only
        query = (
            supabase.table("documents")
            .select("id, filename, title, original_date, uploaded_at, obsidian_file_path")
            .eq("client_id", client_id)
            .like("obsidian_file_path", f"{MEETING_SUMMARIES_FOLDER}/%")
        )

        # Only scan unscanned docs unless force_rescan is enabled
        if not force_rescan:
            query = query.is_("tasks_scanned_at", "null")

        # Filter by original_date (defaults to last 7 days)
        from datetime import datetime, timedelta, timezone

        cutoff = (datetime.now(timezone.utc) - timedelta(days=since_days)).date().isoformat()
        query = query.gte("original_date", cutoff)

        # Order by original_date (falls back to uploaded_at for docs without original_date)
        docs_result = (
            query.order("original_date", desc=True, nullsfirst=False).limit(limit).execute()
        )

        if not docs_result.data:
            return {
                "success": True,
                "documents_scanned": 0,
                "total_tasks_found": 0,
                "message": f"No meeting summaries found to scan in {MEETING_SUMMARIES_FOLDER}",
            }

        from services.task_auto_extractor import extract_tasks_from_document

        # Process documents in parallel for speed (Sonnet calls take ~3-5 sec each)
        async def process_doc(doc):
            doc_name = doc.get("title") or doc.get("filename", "Unknown")
            try:
                result = await extract_tasks_from_document(
                    document_id=doc["id"],
                    supabase=supabase,
                    user_name=user_name,
                    auto_store=True,
                    use_fast_model=False,  # Use Sonnet for quality
                )
                return {
                    "document_id": doc["id"],
                    "document_name": doc_name,
                    "tasks_found": result.get("tasks_found", 0),
                    "tasks_stored": result.get("tasks_stored", 0),
                    "status": result.get("status", "completed"),
                }
            except Exception as e:
                logger.warning(f"Failed to scan document {doc['id']}: {e}")
                return {
                    "document_id": doc["id"],
                    "document_name": doc_name,
                    "tasks_found": 0,
                    "tasks_stored": 0,
                    "error": str(e),
                }

        # Run all extractions in parallel (with semaphore to limit concurrency)
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent LLM calls

        async def process_with_semaphore(doc):
            async with semaphore:
                return await process_doc(doc)

        all_results = await asyncio.gather(
            *[process_with_semaphore(doc) for doc in docs_result.data], return_exceptions=True
        )

        # Aggregate results
        results = []
        total_found = 0
        total_stored = 0

        for result in all_results:
            if isinstance(result, Exception):
                logger.warning(f"Document scan exception: {result}")
                continue
            if isinstance(result, dict):
                found = result.get("tasks_found", 0)
                stored = result.get("tasks_stored", 0)
                total_found += found
                total_stored += stored
                if found > 0 or result.get("error"):
                    results.append(result)

        return {
            "success": True,
            "documents_scanned": len(docs_result.data),
            "total_tasks_found": total_found,
            "total_tasks_stored": total_stored,
            "results": results,
            "message": f"Scanned {len(docs_result.data)} documents, found {total_found} potential tasks",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scanning documents for tasks: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.post("/scan-document/{document_id}")
async def scan_single_document_for_tasks(
    document_id: str,
    force_rescan: bool = Query(False, description="Rescan even if already scanned"),
    current_user=Depends(get_current_user),
):
    """Scan a single document for potential tasks.

    Use this endpoint to test task extraction quality on individual documents
    without batch timeout issues.
    """
    try:
        validate_uuid(document_id, "document_id")
        client_id = current_user.get("client_id") or get_default_client_id()
        user_id = current_user["id"]

        # Verify document exists and belongs to user's client
        doc_result = (
            supabase.table("documents")
            .select("id, filename, title, tasks_scanned_at")
            .eq("id", document_id)
            .eq("client_id", client_id)
            .single()
            .execute()
        )

        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")

        doc = doc_result.data
        doc_name = doc.get("title") or doc.get("filename", "Unknown")

        # Check if already scanned
        if doc.get("tasks_scanned_at") and not force_rescan:
            return {
                "success": True,
                "already_scanned": True,
                "document_name": doc_name,
                "scanned_at": doc["tasks_scanned_at"],
                "message": f'Document "{doc_name}" was already scanned. Use force_rescan=true to rescan.',
            }

        # Get user's name for task filtering
        user_result = supabase.table("users").select("*").eq("id", user_id).single().execute()

        user_name = None
        if user_result.data:
            user_name = (
                user_result.data.get("full_name")
                or user_result.data.get("name")
                or user_result.data.get("email", "").split("@")[0]
            )

        # Extract tasks
        from services.task_auto_extractor import extract_tasks_from_document

        result = await extract_tasks_from_document(
            document_id=document_id,
            supabase=supabase,
            user_name=user_name,
            auto_store=True,
            use_fast_model=False,  # Use Sonnet for quality
        )

        return {
            "success": True,
            "document_id": document_id,
            "document_name": doc_name,
            "tasks_found": result.get("tasks_found", 0),
            "tasks_stored": result.get("tasks_stored", 0),
            "tasks": result.get("tasks", []),
            "status": result.get("status", "completed"),
            "message": f'Found {result.get("tasks_found", 0)} potential tasks in "{doc_name}"',
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scanning document {document_id} for tasks: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


# ============================================================================
# Individual Task Operations (parameterized routes MUST come after static routes)
# ============================================================================


@router.get("/{task_id}")
async def get_task(task_id: str, current_user: dict = Depends(get_current_user)):
    """Get a single task with details."""
    try:
        validate_uuid(task_id, "task_id")
        client_id = current_user.get("client_id") or get_default_client_id()

        # Use view for joined data
        result = await asyncio.to_thread(
            lambda: supabase.table("v_tasks_with_assignee")
            .select("*")
            .eq("id", task_id)
            .eq("client_id", client_id)
            .single()
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Task not found")

        return {"success": True, "task": serialize_task(result.data)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching task: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.patch("/{task_id}")
async def update_task(
    task_id: str, request: TaskUpdate, current_user: dict = Depends(get_current_user)
):
    """Update a task."""
    try:
        validate_uuid(task_id, "task_id")
        client_id = current_user.get("client_id") or get_default_client_id()
        user_id = current_user["id"]

        # Verify task exists and belongs to client
        existing = await asyncio.to_thread(
            lambda: supabase.table("project_tasks")
            .select("id")
            .eq("id", task_id)
            .eq("client_id", client_id)
            .single()
            .execute()
        )

        if not existing.data:
            raise HTTPException(status_code=404, detail="Task not found")

        # Build update record (only include provided fields)
        update_record = {"updated_by": user_id}

        if request.title is not None:
            update_record["title"] = request.title
        if request.description is not None:
            update_record["description"] = request.description
        if request.status is not None:
            update_record["status"] = request.status.value
        if request.priority is not None:
            update_record["priority"] = request.priority
        if request.assignee_stakeholder_id is not None:
            if request.assignee_stakeholder_id:
                validate_uuid(request.assignee_stakeholder_id, "assignee_stakeholder_id")
            update_record["assignee_stakeholder_id"] = request.assignee_stakeholder_id or None
        if request.assignee_user_id is not None:
            if request.assignee_user_id:
                validate_uuid(request.assignee_user_id, "assignee_user_id")
            update_record["assignee_user_id"] = request.assignee_user_id or None
        if request.assignee_name is not None:
            update_record["assignee_name"] = request.assignee_name or None
        if request.due_date is not None:
            update_record["due_date"] = request.due_date.isoformat() if request.due_date else None
        if request.category is not None:
            update_record["category"] = request.category or None
        if request.tags is not None:
            update_record["tags"] = request.tags
        if request.team is not None:
            update_record["team"] = request.team or None
        if request.blocker_reason is not None:
            update_record["blocker_reason"] = request.blocker_reason or None
        if request.related_project_id is not None:
            if request.related_project_id:
                validate_uuid(request.related_project_id, "related_project_id")
            update_record["related_project_id"] = request.related_project_id or None
        if request.linked_project_id is not None:
            if request.linked_project_id:
                validate_uuid(request.linked_project_id, "linked_project_id")
            update_record["linked_project_id"] = request.linked_project_id or None

        result = await asyncio.to_thread(
            lambda: supabase.table("project_tasks")
            .update(update_record)
            .eq("id", task_id)
            .execute()
        )

        task = result.data[0]
        logger.info(f"Task updated: {task_id}")

        return {
            "success": True,
            "task": serialize_task(task),
            "message": "Task updated successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating task: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.delete("/{task_id}")
async def delete_task(task_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a task."""
    try:
        validate_uuid(task_id, "task_id")
        client_id = current_user.get("client_id") or get_default_client_id()

        # Verify task exists and belongs to client
        existing = await asyncio.to_thread(
            lambda: supabase.table("project_tasks")
            .select("id")
            .eq("id", task_id)
            .eq("client_id", client_id)
            .single()
            .execute()
        )

        if not existing.data:
            raise HTTPException(status_code=404, detail="Task not found")

        # Delete task (cascade will handle comments and history)
        await asyncio.to_thread(
            lambda: supabase.table("project_tasks").delete().eq("id", task_id).execute()
        )

        logger.info(f"Task deleted: {task_id}")

        return {"success": True, "message": "Task deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting task: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.patch("/{task_id}/status")
async def update_task_status(
    task_id: str, request: TaskStatusUpdate, current_user: dict = Depends(get_current_user)
):
    """Update task status (optimized for Kanban drag-drop)."""
    try:
        validate_uuid(task_id, "task_id")
        client_id = current_user.get("client_id") or get_default_client_id()
        user_id = current_user["id"]

        # Verify task exists and belongs to client
        existing = await asyncio.to_thread(
            lambda: supabase.table("project_tasks")
            .select("id, status, position")
            .eq("id", task_id)
            .eq("client_id", client_id)
            .single()
            .execute()
        )

        if not existing.data:
            raise HTTPException(status_code=404, detail="Task not found")

        # Validate blocker reason if moving to blocked
        if request.status == TaskStatus.BLOCKED and not request.blocker_reason:
            # Allow empty blocker reason but warn
            logger.warning(f"Task {task_id} moved to blocked without blocker_reason")

        # Determine position
        position = request.position
        if position is None:
            # Get next position in new status column
            position = await get_next_position(client_id, request.status.value)

        update_record = {
            "status": request.status.value,
            "position": position,
            "updated_by": user_id,
        }

        if request.status == TaskStatus.BLOCKED:
            update_record["blocker_reason"] = request.blocker_reason

        result = await asyncio.to_thread(
            lambda: supabase.table("project_tasks")
            .update(update_record)
            .eq("id", task_id)
            .execute()
        )

        task = result.data[0]
        logger.info(f"Task {task_id} status updated to {request.status.value}")

        return {
            "success": True,
            "task": serialize_task(task),
            "message": f"Task moved to {request.status.value}",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating task status: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


# ============================================================================
# Task Comments
# ============================================================================


@router.get("/{task_id}/comments")
async def list_task_comments(task_id: str, current_user: dict = Depends(get_current_user)):
    """List comments on a task."""
    try:
        validate_uuid(task_id, "task_id")
        client_id = current_user.get("client_id") or get_default_client_id()

        # Verify task exists and belongs to client
        task_check = await asyncio.to_thread(
            lambda: supabase.table("project_tasks")
            .select("id")
            .eq("id", task_id)
            .eq("client_id", client_id)
            .single()
            .execute()
        )

        if not task_check.data:
            raise HTTPException(status_code=404, detail="Task not found")

        # Get comments with user info
        result = await asyncio.to_thread(
            lambda: supabase.table("task_comments")
            .select("*, users(email)")
            .eq("task_id", task_id)
            .order("created_at")
            .execute()
        )

        comments = []
        for comment in result.data or []:
            comments.append(
                {
                    "id": comment["id"],
                    "task_id": comment["task_id"],
                    "user_id": comment.get("user_id"),
                    "user_email": comment.get("users", {}).get("email")
                    if comment.get("users")
                    else None,
                    "content": comment["content"],
                    "created_at": comment["created_at"],
                    "updated_at": comment["updated_at"],
                }
            )

        return {"success": True, "comments": comments, "count": len(comments)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing task comments: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.post("/{task_id}/comments")
async def create_task_comment(
    task_id: str, request: TaskCommentCreate, current_user: dict = Depends(get_current_user)
):
    """Add a comment to a task."""
    try:
        validate_uuid(task_id, "task_id")
        client_id = current_user.get("client_id") or get_default_client_id()
        user_id = current_user["id"]

        # Verify task exists and belongs to client
        task_check = await asyncio.to_thread(
            lambda: supabase.table("project_tasks")
            .select("id")
            .eq("id", task_id)
            .eq("client_id", client_id)
            .single()
            .execute()
        )

        if not task_check.data:
            raise HTTPException(status_code=404, detail="Task not found")

        # Create comment
        comment_record = {
            "task_id": task_id,
            "user_id": user_id,
            "content": request.content,
        }

        result = await asyncio.to_thread(
            lambda: supabase.table("task_comments").insert(comment_record).execute()
        )

        comment = result.data[0]
        logger.info(f"Comment added to task {task_id}")

        return {
            "success": True,
            "comment": {
                "id": comment["id"],
                "task_id": comment["task_id"],
                "user_id": comment["user_id"],
                "content": comment["content"],
                "created_at": comment["created_at"],
            },
            "message": "Comment added successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating task comment: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


# ============================================================================
# Task History
# ============================================================================


@router.get("/{task_id}/history")
async def get_task_history(
    task_id: str,
    current_user: dict = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=200),
):
    """Get change history for a task."""
    try:
        validate_uuid(task_id, "task_id")
        client_id = current_user.get("client_id") or get_default_client_id()

        # Verify task exists and belongs to client
        task_check = await asyncio.to_thread(
            lambda: supabase.table("project_tasks")
            .select("id")
            .eq("id", task_id)
            .eq("client_id", client_id)
            .single()
            .execute()
        )

        if not task_check.data:
            raise HTTPException(status_code=404, detail="Task not found")

        # Get history with user info
        result = await asyncio.to_thread(
            lambda: supabase.table("task_history")
            .select("*, users(email)")
            .eq("task_id", task_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

        history = []
        for entry in result.data or []:
            history.append(
                {
                    "id": entry["id"],
                    "task_id": entry["task_id"],
                    "user_id": entry.get("user_id"),
                    "user_email": entry.get("users", {}).get("email")
                    if entry.get("users")
                    else None,
                    "field_name": entry["field_name"],
                    "old_value": entry["old_value"],
                    "new_value": entry["new_value"],
                    "created_at": entry["created_at"],
                }
            )

        return {"success": True, "history": history, "count": len(history)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching task history: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")
