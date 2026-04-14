"""Pipeline API Routes.

Endpoints for the Pipeline page - your action-oriented dashboard for
tracking opportunities, commitments, and stakeholder engagement.

Also includes Granola vault scanning endpoints.
"""

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel

import pb_client as pb

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


# ============================================================================
# RESPONSE MODELS
# ============================================================================


class PriorityOpportunity(BaseModel):
    """An opportunity in the priority queue."""

    id: str
    opportunity_code: str
    title: str
    description: Optional[str]
    department: Optional[str]
    roi_potential: Optional[int]
    implementation_effort: Optional[int]
    strategic_alignment: Optional[int]
    stakeholder_readiness: Optional[int]
    total_score: Optional[int]
    tier: Optional[int]
    status: str
    priority_score: float  # Computed: (roi * strategic) / effort
    owner_name: Optional[str]
    created_at: str


class Commitment(BaseModel):
    """A task/commitment with due date."""

    id: str
    title: str
    description: Optional[str]
    assignee_name: Optional[str]
    due_date: Optional[str]
    status: str
    priority: int
    source_type: Optional[str]
    is_overdue: bool
    days_until_due: Optional[int]
    created_at: str


class StakeholderPulse(BaseModel):
    """Stakeholder engagement snapshot."""

    id: str
    name: str
    role: Optional[str]
    department: Optional[str]
    engagement_level: Optional[str]
    sentiment_score: Optional[float]
    last_interaction: Optional[str]
    total_interactions: int
    open_questions: Optional[List[str]]


class PipelineOverview(BaseModel):
    """Complete pipeline overview response."""

    priority_queue: List[PriorityOpportunity]
    commitments: List[Commitment]
    stakeholder_pulse: List[StakeholderPulse]
    stats: dict


class SyncActivityInfo(BaseModel):
    """Real-time sync activity from Obsidian watcher."""

    active: bool
    current_file: Optional[str] = None
    last_synced_file: Optional[str] = None  # Most recently synced file
    recent_files: List[dict] = []


class ExtractionActivityInfo(BaseModel):
    """Status of entity extraction from scanned documents."""

    active: bool
    job_id: Optional[str] = None
    status: Optional[str] = None  # 'pending', 'running', 'completed', 'failed'
    files_processed: int = 0
    opportunities_found: int = 0
    tasks_found: int = 0
    stakeholders_found: int = 0
    started_at: Optional[str] = None


class GranolaScanStatus(BaseModel):
    """Status of Granola vault scanning."""

    connected: bool
    vault_path: str
    total_files: int
    scanned_files: int
    pending_files: int
    last_scan: Optional[str]
    error: Optional[str] = None
    sync_activity: Optional[SyncActivityInfo] = None
    extraction_activity: Optional[ExtractionActivityInfo] = None


class GranolaScanResult(BaseModel):
    """Result of a Granola scan."""

    status: str
    files_scanned: int
    files_processed: int
    files_skipped: int
    files_failed: int
    opportunities_created: int
    tasks_created: int
    stakeholders_created: int
    failed_details: Optional[List[dict]] = None  # Details of failures
    job_id: Optional[str] = None  # For background scans
    message: Optional[str] = None  # User-friendly message


# ============================================================================
# PIPELINE ENDPOINTS
# ============================================================================


def _build_priority_queue(opps: list) -> list:
    """Build priority-scored opportunity list from raw records."""
    priority_queue = []
    for opp in opps:
        roi = opp.get("roi_potential") or 3
        strategic = opp.get("strategic_alignment") or 3
        effort = opp.get("implementation_effort") or 3
        effort_inverted = 6 - effort
        priority_score = (roi * strategic * effort_inverted) / 5

        # Owner name requires a separate lookup since PB has no joins
        owner_name = None
        owner_id = opp.get("owner_stakeholder_id")
        if owner_id:
            safe_owner = pb.escape_filter(owner_id)
            owner = pb.get_first("stakeholders", filter=f"id='{safe_owner}'", fields="name")
            if owner:
                owner_name = owner.get("name")

        priority_queue.append(
            PriorityOpportunity(
                id=opp["id"],
                opportunity_code=opp.get("opportunity_code", ""),
                title=opp.get("title", ""),
                description=opp.get("description"),
                department=opp.get("department"),
                roi_potential=opp.get("roi_potential"),
                implementation_effort=opp.get("implementation_effort"),
                strategic_alignment=opp.get("strategic_alignment"),
                stakeholder_readiness=opp.get("stakeholder_readiness"),
                total_score=opp.get("total_score"),
                tier=opp.get("tier"),
                status=opp.get("status", ""),
                priority_score=round(priority_score, 2),
                owner_name=owner_name,
                created_at=opp.get("created", ""),
            )
        )

    priority_queue.sort(key=lambda x: x.priority_score, reverse=True)
    return priority_queue


def _build_commitments(tasks: list) -> list:
    """Build commitment list with overdue calculation."""
    today = date.today()
    commitments = []
    for task in tasks:
        due_date_str = task.get("due_date")
        is_overdue = False
        days_until_due = None

        if due_date_str:
            try:
                due_date = date.fromisoformat(due_date_str)
                days_until_due = (due_date - today).days
                is_overdue = days_until_due < 0
            except (ValueError, TypeError):
                pass

        commitments.append(
            Commitment(
                id=task["id"],
                title=task.get("title", ""),
                description=task.get("description"),
                assignee_name=task.get("assignee_name"),
                due_date=due_date_str,
                status=task.get("status", ""),
                priority=task.get("priority", 3),
                source_type=task.get("source_type"),
                is_overdue=is_overdue,
                days_until_due=days_until_due,
                created_at=task.get("created", ""),
            )
        )

    commitments.sort(
        key=lambda x: (
            not x.is_overdue,
            x.due_date or "9999-99-99",
            -x.priority,
        )
    )
    return commitments


@router.get("/overview", response_model=PipelineOverview)
async def get_pipeline_overview(
    department: Optional[str] = Query(None, description="Filter by department (e.g., 'Legal')"),
    limit: int = Query(20, ge=1, le=100),
):
    """Get the complete pipeline overview with priority queue, commitments, and stakeholder pulse.

    The priority queue ranks opportunities by: (ROI potential x Strategic alignment) / Implementation effort
    """

    # -------------------------------------------------------------------------
    # PRIORITY QUEUE - Opportunities ranked by composite score
    # -------------------------------------------------------------------------
    opp_filters = ["status!='completed'"]
    if department:
        safe_dept = pb.escape_filter(department)
        opp_filters.append(f"department~'{safe_dept}'")

    opp_filter = " && ".join(opp_filters)
    opp_result = pb.list_records(
        "ai_projects",
        filter=opp_filter,
        sort="-created",
        per_page=limit,
    )
    opps = opp_result.get("items", [])
    priority_queue = _build_priority_queue(opps)

    # -------------------------------------------------------------------------
    # COMMITMENTS - Tasks with due dates (what you owe people)
    # -------------------------------------------------------------------------
    task_filters = ["status!='completed'"]
    task_filter = " && ".join(task_filters)
    task_result = pb.list_records(
        "project_tasks",
        filter=task_filter,
        sort="due_date",
        per_page=limit,
    )
    tasks = task_result.get("items", [])
    commitments = _build_commitments(tasks)

    # -------------------------------------------------------------------------
    # STAKEHOLDER PULSE - Engagement levels and sentiment
    # -------------------------------------------------------------------------
    sh_filters = []
    if department:
        safe_dept = pb.escape_filter(department)
        sh_filters.append(f"department~'{safe_dept}'")

    sh_filter = " && ".join(sh_filters) if sh_filters else None
    sh_result = pb.list_records(
        "stakeholders",
        filter=sh_filter,
        sort="-last_interaction",
        per_page=limit,
    )
    sh_items = sh_result.get("items", [])

    stakeholder_pulse = []
    for sh in sh_items:
        open_questions = pb.parse_json_field(sh, "open_questions", [])
        stakeholder_pulse.append(
            StakeholderPulse(
                id=sh["id"],
                name=sh.get("name", ""),
                role=sh.get("role"),
                department=sh.get("department"),
                engagement_level=sh.get("engagement_level"),
                sentiment_score=sh.get("sentiment_score"),
                last_interaction=sh.get("last_interaction"),
                total_interactions=sh.get("total_interactions") or 0,
                open_questions=open_questions,
            )
        )

    # -------------------------------------------------------------------------
    # STATS
    # -------------------------------------------------------------------------
    opp_count = pb.count("ai_projects", filter="status!='completed'")
    task_count = pb.count("project_tasks", filter="status!='completed'")
    overdue_count = sum(1 for c in commitments if c.is_overdue)

    stats = {
        "total_opportunities": opp_count,
        "total_commitments": task_count,
        "overdue_commitments": overdue_count,
        "total_stakeholders": len(stakeholder_pulse),
        "department_filter": department,
    }

    return PipelineOverview(
        priority_queue=priority_queue[:limit],
        commitments=commitments[:limit],
        stakeholder_pulse=stakeholder_pulse[:limit],
        stats=stats,
    )


@router.get("/priority-queue", response_model=List[PriorityOpportunity])
async def get_priority_queue(
    department: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
):
    """Get just the priority queue (opportunities ranked by priority score)."""
    filters = []
    if department:
        safe_dept = pb.escape_filter(department)
        filters.append(f"department~'{safe_dept}'")
    if status:
        safe_status = pb.escape_filter(status)
        filters.append(f"status='{safe_status}'")
    else:
        filters.append("status!='completed'")

    filter_str = " && ".join(filters) if filters else None
    result = pb.list_records(
        "ai_projects",
        filter=filter_str,
        per_page=limit,
    )
    opps = result.get("items", [])
    priority_queue = _build_priority_queue(opps)
    return priority_queue


@router.get("/commitments", response_model=List[Commitment])
async def get_commitments(
    include_completed: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
):
    """Get commitments (tasks) sorted by urgency."""
    filters = []
    if not include_completed:
        filters.append("status!='completed'")

    filter_str = " && ".join(filters) if filters else None
    result = pb.list_records(
        "project_tasks",
        filter=filter_str,
        sort="due_date",
        per_page=limit,
    )
    tasks = result.get("items", [])
    commitments = _build_commitments(tasks)
    return commitments


# ============================================================================
# GRANOLA SCANNING ENDPOINTS
# ============================================================================


@router.get("/granola/status", response_model=GranolaScanStatus)
async def get_granola_status():
    """Get the current status of Granola vault scanning."""
    from services.granola_scanner import get_scan_status

    try:
        status = get_scan_status("owner")

        last_scan = None

        # Get sync activity from obsidian_sync_log
        sync_activity = None
        try:
            config = pb.get_first(
                "obsidian_vault_configs",
                filter="is_active=true",
                fields="id",
            )

            if config:
                config_id = config["id"]
                safe_config = pb.escape_filter(config_id)

                # Check for running syncs
                running_result = pb.list_records(
                    "obsidian_sync_log",
                    filter=f"config_id='{safe_config}' && status='running'",
                    per_page=1,
                    fields="id",
                )
                running = running_result.get("items", [])

                # Get most recently synced file
                last_synced_file = None
                recent_state = pb.list_records(
                    "obsidian_sync_state",
                    filter=f"config_id='{safe_config}'",
                    sort="-updated",
                    per_page=1,
                    fields="file_path",
                )
                recent_items = recent_state.get("items", [])
                if recent_items:
                    last_synced_file = recent_items[0]["file_path"].split("/")[-1]

                current_file = last_synced_file if running else None

                # Get recently completed syncs (last 60 seconds)
                cutoff = (datetime.now(timezone.utc) - timedelta(seconds=60)).isoformat()
                recent = pb.list_records(
                    "obsidian_sync_log",
                    filter=f"config_id='{safe_config}' && status='completed' && completed_at>='{cutoff}'",
                    sort="-completed_at",
                    per_page=3,
                    fields="files_added,files_updated,completed_at",
                )
                recent_items = recent.get("items", [])

                sync_activity = SyncActivityInfo(
                    active=len(running) > 0,
                    current_file=current_file,
                    last_synced_file=last_synced_file,
                    recent_files=[
                        {
                            "files_added": r.get("files_added", 0),
                            "files_updated": r.get("files_updated", 0),
                        }
                        for r in recent_items
                    ],
                )
        except Exception as e:
            logger.warning(f"Failed to get sync activity: {e}")

        # Get extraction activity from background scan jobs
        extraction_activity = None
        try:
            for job_id, job in _scan_jobs.items():
                if job.get("user_id") == "owner":
                    job_status = job.get("status", "unknown")
                    if job_status in ("pending", "running"):
                        result = job.get("result", {})
                        extraction_activity = ExtractionActivityInfo(
                            active=True,
                            job_id=job_id,
                            status=job_status,
                            files_processed=result.get("files_processed", 0),
                            opportunities_found=result.get("opportunities_created", 0),
                            tasks_found=result.get("tasks_created", 0),
                            stakeholders_found=result.get("stakeholders_created", 0),
                            started_at=job.get("started_at"),
                        )
                        break
                    elif job_status == "completed":
                        completed_at = job.get("completed_at")
                        if completed_at:
                            try:
                                completed_time = datetime.fromisoformat(completed_at)
                                if (datetime.now() - completed_time).total_seconds() < 30:
                                    result = job.get("result", {})
                                    extraction_activity = ExtractionActivityInfo(
                                        active=False,
                                        job_id=job_id,
                                        status="completed",
                                        files_processed=result.get("files_processed", 0),
                                        opportunities_found=result.get("opportunities_created", 0),
                                        tasks_found=result.get("tasks_created", 0),
                                        stakeholders_found=result.get("stakeholders_created", 0),
                                        started_at=job.get("started_at"),
                                    )
                            except Exception:
                                pass
        except Exception as e:
            logger.warning(f"Failed to get extraction activity: {e}")

        return GranolaScanStatus(
            connected=status.get("connected", False),
            vault_path=status.get("vault_path", ""),
            total_files=status.get("total_files", 0),
            scanned_files=status.get("scanned_files", 0),
            pending_files=status.get("pending_files", 0),
            last_scan=last_scan,
            error=status.get("error"),
            sync_activity=sync_activity,
            extraction_activity=extraction_activity,
        )
    except Exception as e:
        logger.error(f"Granola status endpoint error: {e}")
        return GranolaScanStatus(
            connected=False,
            vault_path="",
            total_files=0,
            scanned_files=0,
            pending_files=0,
            last_scan=None,
            error="Failed to get status",
        )


# In-memory scan job tracking (simple approach - could use Redis for production)
_scan_jobs: Dict[str, Dict] = {}
# Track active scans per user to prevent concurrent duplicates
_active_user_scans: Dict[str, str] = {}  # user_id -> job_id


def _run_background_scan(job_id: str, user_id: str, client_id: str, force_rescan: bool, since_date):
    """Run scan in background and update job status."""
    import asyncio

    from services.granola_scanner import scan_granola_vault as do_scan

    async def _async_scan():
        try:
            _scan_jobs[job_id]["status"] = "running"
            result = await do_scan(user_id, client_id, force_rescan=force_rescan, since_date=since_date)
            stats = result.get("stats", {})
            _scan_jobs[job_id].update(
                {
                    "status": "completed",
                    "result": {
                        "files_scanned": stats.get("files_scanned", 0),
                        "files_processed": stats.get("files_processed", 0),
                        "opportunities_created": stats.get("opportunities_created", 0),
                        "tasks_created": stats.get("tasks_created", 0),
                        "stakeholders_created": stats.get("stakeholders_created", 0),
                    },
                    "completed_at": datetime.now().isoformat(),
                }
            )
        except Exception as e:
            _scan_jobs[job_id].update({"status": "failed", "error": str(e), "completed_at": datetime.now().isoformat()})

    # Run in new event loop for background thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_async_scan())
    finally:
        loop.close()
        # Clear active scan for this user
        if user_id in _active_user_scans and _active_user_scans[user_id] == job_id:
            del _active_user_scans[user_id]


@router.post("/granola/scan", response_model=GranolaScanResult)
async def scan_granola_vault(
    force_rescan: bool = Query(False, description="Re-process already scanned files"),
    since_date: Optional[date] = Query(None, description="Only scan meetings on or after this date (YYYY-MM-DD)"),
    days_back: Optional[int] = Query(
        None, description="Only scan meetings from the last N days (alternative to since_date)"
    ),
    background: bool = Query(False, description="Run scan in background (returns immediately)"),
    background_tasks: BackgroundTasks = None,
):
    """Scan the Granola vault for new meeting summaries.

    Extracts opportunities, tasks, and stakeholders from each meeting.
    Use since_date or days_back to limit scanning to recent meetings.
    Use background=true to run in background (you can navigate away).

    Examples:
      - since_date=2026-01-01 (scan from Jan 1 onwards)
      - days_back=30 (scan last 30 days)
      - background=true (run in background, returns job_id)
    """
    import threading
    import uuid

    from services.granola_scanner import scan_granola_vault as do_scan

    user_id = "owner"
    client_id = None  # single-tenant

    # Check for active scan to prevent concurrent duplicates
    if user_id in _active_user_scans:
        existing_job_id = _active_user_scans[user_id]
        existing_job = _scan_jobs.get(existing_job_id, {})
        if existing_job.get("status") in ("starting", "running"):
            logger.info(f"Scan already in progress for user {user_id}, skipping duplicate request")
            return GranolaScanResult(
                status="already_running",
                job_id=existing_job_id,
                message="Scan already in progress",
                files_scanned=0,
                files_processed=0,
                files_skipped=0,
                files_failed=0,
                opportunities_created=0,
                tasks_created=0,
                stakeholders_created=0,
            )

    # Calculate since_date from days_back if provided
    effective_since_date = since_date
    if days_back and not since_date:
        effective_since_date = datetime.now().date() - timedelta(days=days_back)
        logger.info(f"Using days_back={days_back}, calculated since_date={effective_since_date}")

    # Background mode - return immediately
    if background:
        job_id = str(uuid.uuid4())[:8]
        _scan_jobs[job_id] = {
            "status": "starting",
            "user_id": user_id,
            "started_at": datetime.now().isoformat(),
        }
        _active_user_scans[user_id] = job_id
        thread = threading.Thread(
            target=_run_background_scan,
            args=(job_id, user_id, client_id, force_rescan, effective_since_date),
        )
        thread.start()
        return GranolaScanResult(
            status="started",
            job_id=job_id,
            message="Analysis started. You can navigate away safely.",
            files_scanned=0,
            files_processed=0,
            files_skipped=0,
            files_failed=0,
            opportunities_created=0,
            tasks_created=0,
            stakeholders_created=0,
        )

    try:
        result = await do_scan(user_id, client_id, force_rescan=force_rescan, since_date=effective_since_date)

        stats = result.get("stats", {})

        # Extract failure details for debugging
        failed_details = None
        if stats.get("files_failed", 0) > 0:
            results_list = result.get("results", [])
            failed_details = [
                {"file": r.get("file"), "error": r.get("error")} for r in results_list if r.get("status") == "failed"
            ]
            logger.warning(f"Scan failures: {failed_details}")

        return GranolaScanResult(
            status=result.get("status", "unknown"),
            files_scanned=stats.get("files_scanned", 0),
            files_processed=stats.get("files_processed", 0),
            files_skipped=stats.get("files_skipped", 0),
            files_failed=stats.get("files_failed", 0),
            opportunities_created=stats.get("opportunities_created", 0),
            tasks_created=stats.get("tasks_created", 0),
            stakeholders_created=stats.get("stakeholders_created", 0),
            failed_details=failed_details,
        )

    except Exception as e:
        logger.error(f"Granola scan failed: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/granola/scan/job/{job_id}")
async def get_scan_job_status(job_id: str):
    """Get the status of a background scan job.

    Returns job status: starting, running, completed, or failed.
    """
    if job_id not in _scan_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = _scan_jobs[job_id]

    return {
        "job_id": job_id,
        "status": job.get("status"),
        "started_at": job.get("started_at"),
        "completed_at": job.get("completed_at"),
        "result": job.get("result"),
        "error": job.get("error"),
    }


@router.get("/granola/debug")
async def debug_granola_documents():
    """Debug endpoint to check Granola documents and their storage URLs.

    Returns info about documents that would be scanned.
    """
    import httpx

    # Get documents directly from PocketBase
    try:
        # Get documents that are Granola-sourced and pending scan
        documents = pb.get_all(
            "documents",
            filter="source~'granola'",
            sort="-created",
        )
        documents = documents[:20]  # Limit for debug
    except Exception as e:
        return {"error": f"Failed to query documents: {e}", "documents": []}

    # Check each document's storage URL
    debug_info = []
    async with httpx.AsyncClient() as client:
        for doc in documents[:5]:  # Limit to 5 for debug
            storage_url = doc.get("storage_url")
            doc_info = {
                "id": doc.get("id"),
                "filename": doc.get("filename"),
                "storage_url": storage_url[:100] if storage_url else None,
                "storage_url_accessible": False,
                "error": None,
            }

            if storage_url:
                try:
                    resp = await client.head(storage_url, timeout=10.0)
                    doc_info["storage_url_accessible"] = resp.status_code == 200
                    doc_info["http_status"] = resp.status_code
                except Exception as e:
                    doc_info["error"] = str(e)

            debug_info.append(doc_info)

    return {"total_documents": len(documents), "sample_documents": debug_info}
