"""Task management routes.

Handles task CRUD, Kanban board operations, and task extraction from transcripts.
"""

import asyncio
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

import pb_client as pb
from logger_config import get_logger
from repositories import tasks as tasks_repo
from validation import validate_uuid

logger = get_logger(__name__)
router = APIRouter(prefix="/api/tasks", tags=["tasks"])


# ============================================================================
# Enums and Models
# ============================================================================


class TaskStatus(str, Enum):
    BACKLOG = "backlog"
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
    PEOPLE = "People"
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
    sequence_number: Optional[int] = None
    depends_on: Optional[List[str]] = None  # Task IDs this depends on
    notes: Optional[str] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()

    @field_validator("description", "blocker_reason", "category", "assignee_name", "notes")
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
    sequence_number: Optional[int] = None
    depends_on: Optional[List[str]] = None  # Task IDs this depends on
    notes: Optional[str] = None

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


class BulkTaskItem(BaseModel):
    """Single task in a bulk creation request."""

    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    priority: int = Field(default=3, ge=1, le=5)
    due_date: Optional[date] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    team: Optional[str] = None
    assignee_name: Optional[str] = None
    sequence_number: Optional[int] = None
    depends_on_indices: Optional[List[int]] = None  # References to other items by index in this batch


class BulkTaskRequest(BaseModel):
    """Request body for bulk task creation."""

    tasks: List[BulkTaskItem]
    linked_project_id: Optional[str] = None
    source_conversation_id: Optional[str] = None


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
    # Handle due_date - may be string (from PocketBase) or date object
    due_date = task.get("due_date")
    if due_date:
        due_date = due_date.isoformat() if hasattr(due_date, "isoformat") else str(due_date)

    return {
        "id": task["id"],
        "client_id": task.get("client_id"),
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
        "sequence_number": task.get("sequence_number"),
        "depends_on": task.get("depends_on") or [],
        "notes": task.get("notes"),
        "created_at": task.get("created_at", task.get("created", "")),
        "updated_at": task.get("updated_at", task.get("updated", "")),
        # Joined fields (from view or explicit joins -- may be None from PocketBase)
        "stakeholder_name": task.get("stakeholder_name"),
        "stakeholder_email": task.get("stakeholder_email"),
        "user_email": task.get("user_email"),
        "display_assignee": task.get("display_assignee") or task.get("assignee_name"),
        # Project fields (from v_tasks_with_assignee view -- may be None from PocketBase)
        "project_code": task.get("project_code"),
        "project_title": task.get("project_title"),
        "project_department": task.get("project_department"),
    }


def get_next_position(status: str) -> int:
    """Get the next position for a task in a status column."""
    result = pb.list_records(
        "project_tasks",
        filter=f"status='{pb.escape_filter(status)}'",
        sort="-position",
        per_page=1,
    )
    items = result.get("items", [])
    if items:
        return items[0].get("position", 0) + 1
    return 0


def _build_task_filter(
    *,
    assignee_stakeholder_id: str | None = None,
    assignee_user_id: str | None = None,
    due_date_from: date | None = None,
    due_date_to: date | None = None,
    priority: list[int] | None = None,
    source_type: list[str] | None = None,
    category: str | None = None,
    team: str | None = None,
    linked_project_id: str | None = None,
    include_completed: bool = True,
    status: list[str] | None = None,
) -> str:
    """Build a PocketBase filter string from query parameters."""
    parts: list[str] = []

    if assignee_stakeholder_id:
        parts.append(f"assignee_stakeholder_id='{pb.escape_filter(assignee_stakeholder_id)}'")

    if assignee_user_id:
        parts.append(f"assignee_user_id='{pb.escape_filter(assignee_user_id)}'")

    if due_date_from:
        parts.append(f"due_date>='{due_date_from.isoformat()}'")

    if due_date_to:
        parts.append(f"due_date<='{due_date_to.isoformat()}'")

    if priority:
        or_parts = " || ".join(f"priority={p}" for p in priority)
        parts.append(f"({or_parts})")

    if source_type:
        or_parts = " || ".join(f"source_type='{pb.escape_filter(s)}'" for s in source_type)
        parts.append(f"({or_parts})")

    if category:
        parts.append(f"category='{pb.escape_filter(category)}'")

    if team:
        parts.append(f"team='{pb.escape_filter(team)}'")

    if linked_project_id:
        parts.append(f"linked_project_id='{pb.escape_filter(linked_project_id)}'")

    if not include_completed:
        parts.append("status!='completed'")

    if status:
        or_parts = " || ".join(f"status='{pb.escape_filter(s)}'" for s in status)
        parts.append(f"({or_parts})")

    return " && ".join(parts)


# ============================================================================
# Static Routes (MUST be defined before parameterized routes like /{task_id})
# ============================================================================


@router.get("/kanban")
async def get_kanban_board(
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
        # Validate UUIDs
        if assignee_stakeholder_id:
            validate_uuid(assignee_stakeholder_id, "assignee_stakeholder_id")
        if assignee_user_id:
            validate_uuid(assignee_user_id, "assignee_user_id")
        if linked_project_id:
            validate_uuid(linked_project_id, "linked_project_id")

        filter_str = _build_task_filter(
            assignee_stakeholder_id=assignee_stakeholder_id,
            assignee_user_id=assignee_user_id,
            due_date_from=due_date_from,
            due_date_to=due_date_to,
            priority=priority,
            source_type=source_type,
            category=category,
            team=team,
            linked_project_id=linked_project_id,
            include_completed=include_completed,
        )

        tasks = pb.get_all("project_tasks", filter=filter_str, sort="status,position")

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
        columns = {"backlog": [], "pending": [], "in_progress": [], "blocked": [], "completed": []}

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
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/bulk")
async def create_tasks_bulk(request: BulkTaskRequest):
    """Create multiple tasks in a single request with dependency mapping.

    Used by Taskmaster to create sequenced task plans from chat conversations.
    The depends_on_indices field references other items by their index in the batch,
    which are resolved to actual task UUIDs after creation.
    """
    try:
        if not request.tasks:
            raise HTTPException(status_code=400, detail="No tasks provided")

        # Validate linked_project_id if provided
        if request.linked_project_id:
            validate_uuid(request.linked_project_id, "linked_project_id")
        if request.source_conversation_id:
            validate_uuid(request.source_conversation_id, "source_conversation_id")

        created_tasks = []
        created_ids = []  # Track IDs by index for dependency resolution

        # Look up project department for auto-filling team
        project_department = None
        if request.linked_project_id:
            try:
                proj = pb.get_record("ai_projects", request.linked_project_id)
                if proj:
                    project_department = proj.get("department")
            except Exception:
                pass

        for idx, item in enumerate(request.tasks):
            # Get next position
            position = get_next_position("pending")

            # Resolve depends_on_indices to actual task UUIDs
            depends_on_uuids = []
            if item.depends_on_indices:
                for dep_idx in item.depends_on_indices:
                    if 0 <= dep_idx < len(created_ids):
                        depends_on_uuids.append(created_ids[dep_idx])
                    else:
                        logger.warning(f"Invalid depends_on_index {dep_idx} for task at index {idx}")

            # Auto-fill team from project department if not specified
            task_team = item.team or project_department

            task_record = {
                "title": item.title.strip()[:500],
                "description": item.description,
                "status": "pending",
                "priority": item.priority,
                "assignee_name": item.assignee_name,
                "due_date": item.due_date.isoformat() if item.due_date else None,
                "category": item.category,
                "tags": item.tags or [],
                "team": task_team,
                "source_type": "conversation",
                "source_conversation_id": request.source_conversation_id,
                "linked_project_id": request.linked_project_id,
                "position": position,
                "sequence_number": item.sequence_number,
                "depends_on": depends_on_uuids,
            }

            task = tasks_repo.create_task(task_record)
            created_ids.append(task["id"])
            created_tasks.append(serialize_task(task))

        logger.info(f"Bulk created {len(created_tasks)} tasks for project {request.linked_project_id}")

        return {
            "success": True,
            "tasks": created_tasks,
            "count": len(created_tasks),
            "message": f"Created {len(created_tasks)} tasks",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating tasks in bulk: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/reorder")
async def reorder_tasks(request: TaskBulkReorderRequest):
    """Bulk reorder tasks (for Kanban drag-drop reordering within columns)."""
    try:
        updated_count = 0
        errors = []

        for item in request.tasks:
            try:
                validate_uuid(item.task_id, "task_id")

                tasks_repo.update_task(item.task_id, {
                    "status": item.status.value,
                    "position": item.position,
                })
                updated_count += 1

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
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/extract/transcript/{transcript_id}")
async def extract_tasks_from_transcript(transcript_id: str):
    """Extract tasks from a meeting transcript's action_items."""
    try:
        validate_uuid(transcript_id, "transcript_id")

        # Get transcript with action_items
        transcript = pb.get_record("meeting_transcripts", transcript_id)

        if not transcript:
            raise HTTPException(status_code=404, detail="Transcript not found")

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
            esc_desc = pb.escape_filter(description)
            esc_tid = pb.escape_filter(transcript_id)
            existing = pb.get_first(
                "project_tasks",
                f"source_transcript_id='{esc_tid}' && source_text='{esc_desc}'",
            )

            if existing:
                tasks_skipped += 1
                continue

            # Parse due date if present
            due_date = None
            due_date_str = item.get("due_date")
            if due_date_str:
                try:
                    due_date = datetime.fromisoformat(due_date_str.replace("Z", "+00:00")).date().isoformat()
                except (ValueError, AttributeError):
                    pass

            # Get next position
            position = get_next_position("pending")

            task_record = {
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
                "position": position,
            }

            task = tasks_repo.create_task(task_record)
            tasks_created += 1
            created_tasks.append(serialize_task(task))

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
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# Task List with Filters
# ============================================================================


@router.get("")
async def list_tasks(
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
        # Validate UUIDs
        if assignee_stakeholder_id:
            validate_uuid(assignee_stakeholder_id, "assignee_stakeholder_id")
        if assignee_user_id:
            validate_uuid(assignee_user_id, "assignee_user_id")
        if linked_project_id:
            validate_uuid(linked_project_id, "linked_project_id")

        filter_str = _build_task_filter(
            assignee_stakeholder_id=assignee_stakeholder_id,
            assignee_user_id=assignee_user_id,
            due_date_from=due_date_from,
            due_date_to=due_date_to,
            priority=priority,
            source_type=source_type,
            category=category,
            team=team,
            linked_project_id=linked_project_id,
            status=status,
        )

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

        # PocketBase sort: prefix with - for descending
        sort_str = f"-{order_by}" if order_dir.lower() == "desc" else order_by

        # Fetch with pagination
        page = (offset // limit) + 1 if limit else 1
        result = pb.list_records(
            "project_tasks",
            filter=filter_str,
            sort=sort_str,
            page=page,
            per_page=limit,
        )

        tasks = result.get("items", [])
        total = result.get("totalItems", len(tasks))

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
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# Task CRUD Operations (parameterized routes MUST come after static routes)
# ============================================================================


@router.post("")
async def create_task(request: TaskCreate):
    """Create a new task."""
    try:
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
        position = get_next_position(request.status.value)

        # Build task record
        task_record = {
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
            "source_extracted_at": datetime.now(timezone.utc).isoformat() if request.source_text else None,
            "blocker_reason": request.blocker_reason if request.status == TaskStatus.BLOCKED else None,
            "blocked_at": datetime.now(timezone.utc).isoformat() if request.status == TaskStatus.BLOCKED else None,
            "position": position,
            "sequence_number": request.sequence_number,
            "depends_on": request.depends_on or [],
            "notes": request.notes,
        }

        task = tasks_repo.create_task(task_record)
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
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


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
    limit: int = Query(default=20, le=50),
    status: str = Query(default="pending", pattern="^(pending|accepted|rejected|all)$"),
):
    """Get task candidates extracted from documents.

    These are potential tasks that Taskmaster found in uploaded documents.
    Users can accept or reject them.
    """
    try:
        if status == "all":
            # Fetch all statuses
            result = pb.list_records(
                "task_candidates",
                sort="-created",
                per_page=limit,
            )
        else:
            result = pb.list_records(
                "task_candidates",
                filter=f"status='{pb.escape_filter(status)}'",
                sort="-created",
                per_page=limit,
            )

        candidates = []
        for c in result.get("items", []):
            # Try to get source document name
            source_doc_name = c.get("source_document_name")
            if not source_doc_name and c.get("source_document_id"):
                try:
                    doc = pb.get_record("documents", c["source_document_id"])
                    if doc:
                        source_doc_name = doc.get("title") or doc.get("filename")
                except Exception:
                    pass

            candidates.append(
                {
                    "id": c["id"],
                    "title": c["title"],
                    "suggested_priority": c.get("suggested_priority"),
                    "suggested_due_date": c.get("suggested_due_date"),
                    "due_date_text": c.get("due_date_text"),
                    "assignee_name": c.get("assignee_name"),
                    "source_document_id": c.get("source_document_id"),
                    "source_document_name": source_doc_name,
                    "source_text": c.get("source_text"),
                    "confidence": c.get("confidence"),
                    "status": c.get("status"),
                    "created_at": c.get("created_at", c.get("created", "")),
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
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/candidates/count")
async def get_candidate_count():
    """Get count of pending task candidates (for badge display)."""
    try:
        pending_count = tasks_repo.count_pending_task_candidates()
        return {"success": True, "pending_count": pending_count}

    except Exception as e:
        logger.error(f"Error fetching candidate count: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.delete("/candidates/clear")
async def clear_task_candidates(
    status: Optional[str] = Query(None, description="Filter by status: pending, accepted, rejected, or all"),
):
    """Clear task candidates. By default clears pending candidates only.

    Use status=all to clear all candidates.
    """
    try:
        filter_str = ""
        if status and status != "all":
            filter_str = f"status='{pb.escape_filter(status)}'"

        candidates = pb.get_all("task_candidates", filter=filter_str)
        for c in candidates:
            pb.delete_record("task_candidates", c["id"])
        deleted_count = len(candidates)

        return {
            "success": True,
            "deleted_count": deleted_count,
            "status_filter": status or "pending",
        }

    except Exception as e:
        logger.error(f"Error clearing task candidates: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/candidates/{candidate_id}/accept")
async def accept_task_candidate(
    candidate_id: str,
    body: Optional[CandidateAction] = None,
):
    """Accept a task candidate and create an actual task.

    Optionally provide overrides for title, priority, or due_date.
    """
    try:
        validate_uuid(candidate_id, "candidate_id")

        from services.task_auto_extractor import accept_task_candidate as do_accept

        result = await do_accept(
            candidate_id=candidate_id,
            user_id="",
            overrides=body.overrides if body else None,
        )

        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))

        return {"success": True, "task_id": result.get("task_id"), "title": result.get("title")}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error accepting task candidate: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/candidates/{candidate_id}/reject")
async def reject_task_candidate(
    candidate_id: str,
    body: Optional[CandidateAction] = None,
):
    """Reject a task candidate."""
    try:
        validate_uuid(candidate_id, "candidate_id")

        from services.task_auto_extractor import reject_task_candidate as do_reject

        result = await do_reject(
            candidate_id=candidate_id,
            user_id="",
            reason=body.reason if body else None,
        )

        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))

        return {"success": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting task candidate: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/candidates/{candidate_id}/link")
async def link_task_candidate(candidate_id: str, body: LinkCandidateRequest):
    """Link a task candidate to an existing task instead of creating a new one.

    This is used when a duplicate is detected and the user wants to associate
    the candidate's context with an existing task rather than creating a new one.
    """
    try:
        validate_uuid(candidate_id, "candidate_id")
        validate_uuid(body.task_id, "task_id")

        # Get the candidate
        candidate = tasks_repo.get_task_candidate(candidate_id)

        if not candidate:
            raise HTTPException(status_code=404, detail="Task candidate not found")

        # Verify target task exists
        task = tasks_repo.get_task(body.task_id)

        if not task:
            raise HTTPException(status_code=404, detail="Target task not found")

        # Append candidate context to the existing task's description
        existing_desc = task.get("description") or ""
        candidate_context = candidate.get("meeting_context") or ""
        candidate_source = candidate.get("source_document_name") or ""

        if candidate_context or candidate_source:
            linked_note = f"\n\n---\nLinked from meeting: {candidate_source}"
            if candidate_context:
                linked_note += f"\nContext: {candidate_context}"
            new_description = existing_desc + linked_note

            tasks_repo.update_task(body.task_id, {"description": new_description})

        # Mark candidate as accepted with reference to the linked task
        tasks_repo.update_task_candidate(
            candidate_id,
            {
                "status": "accepted",
                "created_task_id": body.task_id,
                "reviewed_at": datetime.now(timezone.utc).isoformat(),
            },
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
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/candidates/bulk")
async def bulk_action_candidates(body: BulkCandidateAction):
    """Accept or reject multiple task candidates at once."""
    try:
        for cid in body.candidate_ids:
            validate_uuid(cid, "candidate_id")

        from services.task_auto_extractor import bulk_action_candidates as do_bulk

        result = await do_bulk(
            candidate_ids=body.candidate_ids,
            action=body.action,
            user_id="",
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
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# Document Scanning for Tasks
# ============================================================================


@router.get("/scan-stats")
async def get_scan_stats():
    """Get scan statistics including last scan time, document counts, and pending candidates."""
    try:
        # Get total document count
        total_docs = pb.count("documents")

        # Get documents with original_date (scannable) in last 30 days
        thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).date().isoformat()
        recent_docs = pb.count("documents", filter=f"original_date>='{thirty_days_ago}'")

        # Get pending candidate count
        pending_candidates = tasks_repo.count_pending_task_candidates()

        # Get last scan time (most recent candidate created_at)
        last_scan_result = pb.list_records(
            "task_candidates",
            sort="-created",
            per_page=1,
        )
        last_scan_items = last_scan_result.get("items", [])
        last_scan = last_scan_items[0].get("created_at", last_scan_items[0].get("created")) if last_scan_items else None

        # Get documents that have been scanned (have candidates)
        all_candidates = pb.get_all("task_candidates", filter="")
        scanned_doc_ids = {c.get("source_document_id") for c in all_candidates if c.get("source_document_id")}

        return {
            "total_documents": total_docs,
            "recent_documents_30d": recent_docs,
            "pending_candidates": pending_candidates,
            "last_scan_at": last_scan,
            "documents_scanned_ever": len(scanned_doc_ids),
        }

    except Exception as e:
        logger.error(f"Error getting scan stats: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# Meeting summaries folder path - only scan these for tasks
# Note: Path is case-sensitive, matches Obsidian vault structure
MEETING_SUMMARIES_FOLDER = "Granola/Meeting-summaries"


@router.post("/scan-documents")
async def scan_documents_for_tasks(
    limit: int = Query(5, ge=1, le=50, description="Number of recent documents to scan (max 50)"),
    since_days: int = Query(7, ge=1, le=365, description="Only scan documents with original_date in the last N days"),
    force_rescan: bool = Query(False, description="Rescan documents even if already scanned"),
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
        # Build filter for meeting summary documents only
        cutoff = (datetime.now(timezone.utc) - timedelta(days=since_days)).date().isoformat()
        filter_parts = [
            f"obsidian_file_path~'{pb.escape_filter(MEETING_SUMMARIES_FOLDER)}/'",
            f"original_date>='{cutoff}'",
        ]

        # Only scan unscanned docs unless force_rescan is enabled
        if not force_rescan:
            filter_parts.append("tasks_scanned_at=''")

        filter_str = " && ".join(filter_parts)

        docs_result = pb.list_records(
            "documents",
            filter=filter_str,
            sort="-original_date",
            per_page=limit,
        )

        docs = docs_result.get("items", [])

        if not docs:
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
                    user_name=None,
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
            *[process_with_semaphore(doc) for doc in docs], return_exceptions=True
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
            "documents_scanned": len(docs),
            "total_tasks_found": total_found,
            "total_tasks_stored": total_stored,
            "results": results,
            "message": f"Scanned {len(docs)} documents, found {total_found} potential tasks",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scanning documents for tasks: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/scan-document/{document_id}")
async def scan_single_document_for_tasks(
    document_id: str,
    force_rescan: bool = Query(False, description="Rescan even if already scanned"),
):
    """Scan a single document for potential tasks.

    Use this endpoint to test task extraction quality on individual documents
    without batch timeout issues.
    """
    try:
        validate_uuid(document_id, "document_id")

        # Verify document exists
        doc = pb.get_record("documents", document_id)

        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

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

        # Extract tasks
        from services.task_auto_extractor import extract_tasks_from_document

        result = await extract_tasks_from_document(
            document_id=document_id,
            user_name=None,
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
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# Kraken Single-Task Evaluation & Execution
# IMPORTANT: These routes use /{task_id}/kraken/... but must be defined
# before the generic /{task_id} catch-all routes.
# ============================================================================


class KrakenSingleTaskExecuteRequest(BaseModel):
    """Request body for executing a single task via Kraken."""

    evaluation_notes: str = Field(..., min_length=1)


@router.post("/{task_id}/kraken/evaluate")
async def kraken_evaluate_single_task(task_id: str):
    """Evaluate a single task for AI workability via Kraken. Returns SSE stream."""
    from fastapi.responses import StreamingResponse

    validate_uuid(task_id, "task_id")

    from services.task_kraken import evaluate_single_task

    async def event_stream():
        async for event in evaluate_single_task(task_id, "", "", None):
            import json

            event_type = event.get("type", "status")
            data = event.get("data", "")
            if isinstance(data, dict):
                data = json.dumps(data)
            yield f"event: {event_type}\ndata: {data}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/{task_id}/kraken/execute")
async def kraken_execute_single_task(
    task_id: str, request: KrakenSingleTaskExecuteRequest
):
    """Execute a single task via Kraken after evaluation approval. Returns SSE stream."""
    from fastapi.responses import StreamingResponse

    validate_uuid(task_id, "task_id")

    from services.task_kraken import execute_single_task

    async def event_stream():
        async for event in execute_single_task(task_id, request.evaluation_notes, "", "", None):
            import json

            event_type = event.get("type", "status")
            data = event.get("data", "")
            if isinstance(data, dict):
                data = json.dumps(data)
            yield f"event: {event_type}\ndata: {data}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ============================================================================
# Individual Task Operations (parameterized routes MUST come after static routes)
# ============================================================================


@router.get("/{task_id}")
async def get_task(task_id: str):
    """Get a single task with details."""
    try:
        validate_uuid(task_id, "task_id")

        task = tasks_repo.get_task(task_id)

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        return {"success": True, "task": serialize_task(task)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching task: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.patch("/{task_id}")
async def update_task(task_id: str, request: TaskUpdate):
    """Update a task."""
    try:
        validate_uuid(task_id, "task_id")

        # Verify task exists
        existing = tasks_repo.get_task(task_id)

        if not existing:
            raise HTTPException(status_code=404, detail="Task not found")

        # Build update record - use model_fields_set to distinguish
        # "not provided" from "explicitly set to null" for clearable fields
        update_record = {}
        fields_set = request.model_fields_set

        if "title" in fields_set:
            update_record["title"] = request.title
        if "description" in fields_set:
            update_record["description"] = request.description or None
        if "status" in fields_set:
            update_record["status"] = request.status.value if request.status else None
        if "priority" in fields_set:
            update_record["priority"] = request.priority
        if "assignee_stakeholder_id" in fields_set:
            if request.assignee_stakeholder_id:
                validate_uuid(request.assignee_stakeholder_id, "assignee_stakeholder_id")
            update_record["assignee_stakeholder_id"] = request.assignee_stakeholder_id or None
        if "assignee_user_id" in fields_set:
            if request.assignee_user_id:
                validate_uuid(request.assignee_user_id, "assignee_user_id")
            update_record["assignee_user_id"] = request.assignee_user_id or None
        if "assignee_name" in fields_set:
            update_record["assignee_name"] = request.assignee_name or None
        if "due_date" in fields_set:
            update_record["due_date"] = request.due_date.isoformat() if request.due_date else None
        if "category" in fields_set:
            update_record["category"] = request.category or None
        if "tags" in fields_set:
            update_record["tags"] = request.tags
        if "team" in fields_set:
            update_record["team"] = request.team or None
        if "blocker_reason" in fields_set:
            update_record["blocker_reason"] = request.blocker_reason or None
        if "related_project_id" in fields_set:
            if request.related_project_id:
                validate_uuid(request.related_project_id, "related_project_id")
            update_record["related_project_id"] = request.related_project_id or None
        if "linked_project_id" in fields_set:
            if request.linked_project_id:
                validate_uuid(request.linked_project_id, "linked_project_id")
            update_record["linked_project_id"] = request.linked_project_id or None
        if "sequence_number" in fields_set:
            update_record["sequence_number"] = request.sequence_number
        if "depends_on" in fields_set:
            update_record["depends_on"] = request.depends_on
        if "notes" in fields_set:
            update_record["notes"] = request.notes or None

        task = tasks_repo.update_task(task_id, update_record)
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
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.delete("/{task_id}")
async def delete_task(task_id: str):
    """Delete a task."""
    try:
        validate_uuid(task_id, "task_id")

        # Verify task exists
        existing = tasks_repo.get_task(task_id)

        if not existing:
            raise HTTPException(status_code=404, detail="Task not found")

        # Delete task
        tasks_repo.delete_task(task_id)

        logger.info(f"Task deleted: {task_id}")

        return {"success": True, "message": "Task deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting task: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.patch("/{task_id}/status")
async def update_task_status(task_id: str, request: TaskStatusUpdate):
    """Update task status (optimized for Kanban drag-drop)."""
    try:
        validate_uuid(task_id, "task_id")

        # Verify task exists
        existing = tasks_repo.get_task(task_id)

        if not existing:
            raise HTTPException(status_code=404, detail="Task not found")

        # Validate blocker reason if moving to blocked
        if request.status == TaskStatus.BLOCKED and not request.blocker_reason:
            # Allow empty blocker reason but warn
            logger.warning(f"Task {task_id} moved to blocked without blocker_reason")

        # Determine position
        position = request.position
        if position is None:
            # Get next position in new status column
            position = get_next_position(request.status.value)

        update_record = {
            "status": request.status.value,
            "position": position,
        }

        if request.status == TaskStatus.BLOCKED:
            update_record["blocker_reason"] = request.blocker_reason

        task = tasks_repo.update_task(task_id, update_record)
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
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# Task Comments
# ============================================================================


@router.get("/{task_id}/comments")
async def list_task_comments(task_id: str):
    """List comments on a task."""
    try:
        validate_uuid(task_id, "task_id")

        # Verify task exists
        task_check = tasks_repo.get_task(task_id)

        if not task_check:
            raise HTTPException(status_code=404, detail="Task not found")

        # Get comments
        raw_comments = tasks_repo.get_task_comments(task_id)

        comments = []
        for comment in raw_comments:
            comments.append(
                {
                    "id": comment["id"],
                    "task_id": comment.get("task_id"),
                    "user_id": comment.get("user_id"),
                    "user_email": comment.get("user_email"),
                    "content": comment.get("content"),
                    "created_at": comment.get("created_at", comment.get("created", "")),
                    "updated_at": comment.get("updated_at", comment.get("updated", "")),
                }
            )

        return {"success": True, "comments": comments, "count": len(comments)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing task comments: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/{task_id}/comments")
async def create_task_comment(task_id: str, request: TaskCommentCreate):
    """Add a comment to a task."""
    try:
        validate_uuid(task_id, "task_id")

        # Verify task exists
        task_check = tasks_repo.get_task(task_id)

        if not task_check:
            raise HTTPException(status_code=404, detail="Task not found")

        # Create comment
        comment_record = {
            "task_id": task_id,
            "content": request.content,
        }

        comment = tasks_repo.create_task_comment(comment_record)
        logger.info(f"Comment added to task {task_id}")

        return {
            "success": True,
            "comment": {
                "id": comment["id"],
                "task_id": comment.get("task_id"),
                "user_id": comment.get("user_id"),
                "content": comment.get("content"),
                "created_at": comment.get("created_at", comment.get("created", "")),
            },
            "message": "Comment added successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating task comment: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# Task History
# ============================================================================


@router.get("/{task_id}/history")
async def get_task_history(
    task_id: str,
    limit: int = Query(50, ge=1, le=200),
):
    """Get change history for a task."""
    try:
        validate_uuid(task_id, "task_id")

        # Verify task exists
        task_check = tasks_repo.get_task(task_id)

        if not task_check:
            raise HTTPException(status_code=404, detail="Task not found")

        # Get history
        raw_history = tasks_repo.get_task_history(task_id)

        # Apply limit (repo returns all, we limit here)
        raw_history = raw_history[:limit]

        history = []
        for entry in raw_history:
            history.append(
                {
                    "id": entry["id"],
                    "task_id": entry.get("task_id"),
                    "user_id": entry.get("user_id"),
                    "user_email": entry.get("user_email"),
                    "field_name": entry.get("field_name"),
                    "old_value": entry.get("old_value"),
                    "new_value": entry.get("new_value"),
                    "created_at": entry.get("created_at", entry.get("created", "")),
                }
            )

        return {"success": True, "history": history, "count": len(history)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching task history: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e
