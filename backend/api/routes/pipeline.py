"""
Pipeline API Routes

Endpoints for the Pipeline page - your action-oriented dashboard for
tracking opportunities, commitments, and stakeholder engagement.

Also includes Granola vault scanning endpoints.
"""

import logging
from typing import Optional, List
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel

from auth import get_current_user
from database import get_supabase

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


class GranolaScanStatus(BaseModel):
    """Status of Granola vault scanning."""
    connected: bool
    vault_path: str
    total_files: int
    scanned_files: int
    pending_files: int
    last_scan: Optional[str]
    error: Optional[str] = None


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


# ============================================================================
# PIPELINE ENDPOINTS
# ============================================================================

@router.get("/overview", response_model=PipelineOverview)
async def get_pipeline_overview(
    department: Optional[str] = Query(None, description="Filter by department (e.g., 'Legal')"),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """
    Get the complete pipeline overview with priority queue, commitments, and stakeholder pulse.

    The priority queue ranks opportunities by: (ROI potential × Strategic alignment) / Implementation effort
    """
    client_id = current_user.get("client_id")

    # -------------------------------------------------------------------------
    # PRIORITY QUEUE - Opportunities ranked by composite score
    # -------------------------------------------------------------------------
    opp_query = supabase.table('ai_opportunities') \
        .select('*, stakeholders!owner_stakeholder_id(name)') \
        .eq('client_id', client_id) \
        .neq('status', 'completed')

    if department:
        opp_query = opp_query.ilike('department', f'%{department}%')

    opp_result = opp_query.order('created_at', desc=True).limit(limit).execute()

    priority_queue = []
    for opp in opp_result.data:
        # Compute priority score: (ROI × Strategic) / Effort
        # Higher is better (high ROI, high strategic, low effort)
        roi = opp.get('roi_potential') or 3
        strategic = opp.get('strategic_alignment') or 3
        effort = opp.get('implementation_effort') or 3

        # Invert effort (5 = easy = good, 1 = hard = bad for priority)
        effort_inverted = 6 - effort
        priority_score = (roi * strategic * effort_inverted) / 5  # Normalize

        owner_name = None
        if opp.get('stakeholders'):
            owner_name = opp['stakeholders'].get('name')

        priority_queue.append(PriorityOpportunity(
            id=opp['id'],
            opportunity_code=opp['opportunity_code'],
            title=opp['title'],
            description=opp.get('description'),
            department=opp.get('department'),
            roi_potential=opp.get('roi_potential'),
            implementation_effort=opp.get('implementation_effort'),
            strategic_alignment=opp.get('strategic_alignment'),
            stakeholder_readiness=opp.get('stakeholder_readiness'),
            total_score=opp.get('total_score'),
            tier=opp.get('tier'),
            status=opp['status'],
            priority_score=round(priority_score, 2),
            owner_name=owner_name,
            created_at=opp['created_at']
        ))

    # Sort by priority score descending
    priority_queue.sort(key=lambda x: x.priority_score, reverse=True)

    # -------------------------------------------------------------------------
    # COMMITMENTS - Tasks with due dates (what you owe people)
    # -------------------------------------------------------------------------
    task_query = supabase.table('project_tasks') \
        .select('*') \
        .eq('client_id', client_id) \
        .neq('status', 'completed')

    if department:
        # Filter by related stakeholder department or assignee department
        # For now, we'll just show all tasks when department filter is applied
        pass

    task_result = task_query.order('due_date', desc=False, nullsfirst=False).limit(limit).execute()

    today = date.today()
    commitments = []
    for task in task_result.data:
        due_date_str = task.get('due_date')
        is_overdue = False
        days_until_due = None

        if due_date_str:
            try:
                due_date = date.fromisoformat(due_date_str)
                days_until_due = (due_date - today).days
                is_overdue = days_until_due < 0
            except (ValueError, TypeError):
                pass

        commitments.append(Commitment(
            id=task['id'],
            title=task['title'],
            description=task.get('description'),
            assignee_name=task.get('assignee_name'),
            due_date=due_date_str,
            status=task['status'],
            priority=task.get('priority', 3),
            source_type=task.get('source_type'),
            is_overdue=is_overdue,
            days_until_due=days_until_due,
            created_at=task['created_at']
        ))

    # Sort: overdue first, then by due date, then by priority
    commitments.sort(key=lambda x: (
        not x.is_overdue,  # Overdue first
        x.due_date or '9999-99-99',  # Then by due date
        -x.priority  # Then by priority (high first)
    ))

    # -------------------------------------------------------------------------
    # STAKEHOLDER PULSE - Engagement levels and sentiment
    # -------------------------------------------------------------------------
    sh_query = supabase.table('stakeholders') \
        .select('*') \
        .eq('client_id', client_id)

    if department:
        sh_query = sh_query.ilike('department', f'%{department}%')

    sh_result = sh_query.order('last_interaction', desc=True, nullsfirst=False).limit(limit).execute()

    stakeholder_pulse = []
    for sh in sh_result.data:
        stakeholder_pulse.append(StakeholderPulse(
            id=sh['id'],
            name=sh['name'],
            role=sh.get('role'),
            department=sh.get('department'),
            engagement_level=sh.get('engagement_level'),
            sentiment_score=sh.get('sentiment_score'),
            last_interaction=sh.get('last_interaction'),
            total_interactions=sh.get('total_interactions') or 0,
            open_questions=sh.get('open_questions') or []
        ))

    # -------------------------------------------------------------------------
    # STATS
    # -------------------------------------------------------------------------
    # Count totals
    opp_count = supabase.table('ai_opportunities') \
        .select('id', count='exact') \
        .eq('client_id', client_id) \
        .neq('status', 'completed') \
        .execute()

    task_count = supabase.table('project_tasks') \
        .select('id', count='exact') \
        .eq('client_id', client_id) \
        .neq('status', 'completed') \
        .execute()

    overdue_count = sum(1 for c in commitments if c.is_overdue)

    stats = {
        'total_opportunities': opp_count.count or 0,
        'total_commitments': task_count.count or 0,
        'overdue_commitments': overdue_count,
        'total_stakeholders': len(stakeholder_pulse),
        'department_filter': department
    }

    return PipelineOverview(
        priority_queue=priority_queue[:limit],
        commitments=commitments[:limit],
        stakeholder_pulse=stakeholder_pulse[:limit],
        stats=stats
    )


@router.get("/priority-queue", response_model=List[PriorityOpportunity])
async def get_priority_queue(
    department: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get just the priority queue (opportunities ranked by priority score)."""
    client_id = current_user.get("client_id")

    query = supabase.table('ai_opportunities') \
        .select('*, stakeholders!owner_stakeholder_id(name)') \
        .eq('client_id', client_id)

    if department:
        query = query.ilike('department', f'%{department}%')
    if status:
        query = query.eq('status', status)
    else:
        query = query.neq('status', 'completed')

    result = query.limit(limit).execute()

    priority_queue = []
    for opp in result.data:
        roi = opp.get('roi_potential') or 3
        strategic = opp.get('strategic_alignment') or 3
        effort = opp.get('implementation_effort') or 3
        effort_inverted = 6 - effort
        priority_score = (roi * strategic * effort_inverted) / 5

        owner_name = None
        if opp.get('stakeholders'):
            owner_name = opp['stakeholders'].get('name')

        priority_queue.append(PriorityOpportunity(
            id=opp['id'],
            opportunity_code=opp['opportunity_code'],
            title=opp['title'],
            description=opp.get('description'),
            department=opp.get('department'),
            roi_potential=opp.get('roi_potential'),
            implementation_effort=opp.get('implementation_effort'),
            strategic_alignment=opp.get('strategic_alignment'),
            stakeholder_readiness=opp.get('stakeholder_readiness'),
            total_score=opp.get('total_score'),
            tier=opp.get('tier'),
            status=opp['status'],
            priority_score=round(priority_score, 2),
            owner_name=owner_name,
            created_at=opp['created_at']
        ))

    priority_queue.sort(key=lambda x: x.priority_score, reverse=True)
    return priority_queue


@router.get("/commitments", response_model=List[Commitment])
async def get_commitments(
    include_completed: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get commitments (tasks) sorted by urgency."""
    client_id = current_user.get("client_id")

    query = supabase.table('project_tasks') \
        .select('*') \
        .eq('client_id', client_id)

    if not include_completed:
        query = query.neq('status', 'completed')

    result = query.order('due_date', desc=False, nullsfirst=False).limit(limit).execute()

    today = date.today()
    commitments = []
    for task in result.data:
        due_date_str = task.get('due_date')
        is_overdue = False
        days_until_due = None

        if due_date_str:
            try:
                due_date = date.fromisoformat(due_date_str)
                days_until_due = (due_date - today).days
                is_overdue = days_until_due < 0
            except (ValueError, TypeError):
                pass

        commitments.append(Commitment(
            id=task['id'],
            title=task['title'],
            description=task.get('description'),
            assignee_name=task.get('assignee_name'),
            due_date=due_date_str,
            status=task['status'],
            priority=task.get('priority', 3),
            source_type=task.get('source_type'),
            is_overdue=is_overdue,
            days_until_due=days_until_due,
            created_at=task['created_at']
        ))

    commitments.sort(key=lambda x: (
        not x.is_overdue,
        x.due_date or '9999-99-99',
        -x.priority
    ))

    return commitments


# ============================================================================
# GRANOLA SCANNING ENDPOINTS
# ============================================================================

@router.get("/granola/status", response_model=GranolaScanStatus)
async def get_granola_status(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get the current status of Granola vault scanning."""
    from services.granola_scanner import get_scan_status

    try:
        user_id = current_user["id"]
        status = get_scan_status(user_id)

        # Get last scan time (skip if status has error to avoid cascading failures)
        last_scan = None
        if status.get('connected') and not status.get('error'):
            try:
                # Use RPC to avoid PostgREST ilike issues
                last_doc = supabase.rpc('get_granola_scan_status', {'p_user_id': user_id}).execute()
                # Note: last_scan would need a separate RPC or direct query
                # For now, skip last_scan to avoid the ilike issue
            except Exception as e:
                logger.warning(f"Failed to get last scan time: {e}")

        return GranolaScanStatus(
            connected=status.get('connected', False),
            vault_path=status.get('vault_path', ''),
            total_files=status.get('total_files', 0),
            scanned_files=status.get('scanned_files', 0),
            pending_files=status.get('pending_files', 0),
            last_scan=last_scan,
            error=status.get('error')
        )
    except Exception as e:
        logger.error(f"Granola status endpoint error: {e}")
        return GranolaScanStatus(
            connected=False,
            vault_path='',
            total_files=0,
            scanned_files=0,
            pending_files=0,
            last_scan=None,
            error="Failed to get status"
        )


@router.post("/granola/scan", response_model=GranolaScanResult)
async def scan_granola_vault(
    force_rescan: bool = Query(False, description="Re-process already scanned files"),
    since_date: Optional[date] = Query(None, description="Only scan meetings on or after this date (YYYY-MM-DD)"),
    days_back: Optional[int] = Query(None, description="Only scan meetings from the last N days (alternative to since_date)"),
    background_tasks: BackgroundTasks = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """
    Scan the Granola vault for new meeting summaries.

    Extracts opportunities, tasks, and stakeholders from each meeting.
    Use since_date or days_back to limit scanning to recent meetings.
    Examples:
      - since_date=2026-01-01 (scan from Jan 1 onwards)
      - days_back=30 (scan last 30 days)
    """
    from services.granola_scanner import scan_granola_vault as do_scan
    from datetime import timedelta

    user_id = current_user["id"]
    client_id = current_user.get("client_id")

    if not client_id:
        raise HTTPException(status_code=400, detail="User has no associated client")

    # Calculate since_date from days_back if provided
    effective_since_date = since_date
    if days_back and not since_date:
        effective_since_date = (datetime.now().date() - timedelta(days=days_back))
        logger.info(f"Using days_back={days_back}, calculated since_date={effective_since_date}")

    try:
        result = await do_scan(user_id, client_id, force_rescan=force_rescan, since_date=effective_since_date)

        stats = result.get('stats', {})

        # Extract failure details for debugging
        failed_details = None
        if stats.get('files_failed', 0) > 0:
            results_list = result.get('results', [])
            failed_details = [
                {'file': r.get('file'), 'error': r.get('error')}
                for r in results_list
                if r.get('status') == 'failed'
            ]
            logger.warning(f"Scan failures: {failed_details}")

        return GranolaScanResult(
            status=result.get('status', 'unknown'),
            files_scanned=stats.get('files_scanned', 0),
            files_processed=stats.get('files_processed', 0),
            files_skipped=stats.get('files_skipped', 0),
            files_failed=stats.get('files_failed', 0),
            opportunities_created=stats.get('opportunities_created', 0),
            tasks_created=stats.get('tasks_created', 0),
            stakeholders_created=stats.get('stakeholders_created', 0),
            failed_details=failed_details
        )

    except Exception as e:
        logger.error(f"Granola scan failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/granola/debug")
async def debug_granola_documents(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """
    Debug endpoint to check Granola documents and their storage URLs.
    Returns info about documents that would be scanned.
    """
    import httpx

    user_id = current_user["id"]

    # Get documents using RPC
    try:
        result = supabase.rpc('get_granola_documents_to_scan', {
            'p_user_id': user_id,
            'p_force_rescan': True  # Show all, not just unscanned
        }).execute()
        documents = result.data or []
    except Exception as e:
        return {"error": f"Failed to query documents: {e}", "documents": []}

    # Check each document's storage URL
    debug_info = []
    async with httpx.AsyncClient() as client:
        for doc in documents[:5]:  # Limit to 5 for debug
            storage_url = doc.get('storage_url')
            doc_info = {
                "id": doc.get('id'),
                "filename": doc.get('filename'),
                "storage_url": storage_url[:100] if storage_url else None,
                "storage_url_accessible": False,
                "error": None
            }

            if storage_url:
                try:
                    resp = await client.head(storage_url, timeout=10.0)
                    doc_info["storage_url_accessible"] = resp.status_code == 200
                    doc_info["http_status"] = resp.status_code
                except Exception as e:
                    doc_info["error"] = str(e)

            debug_info.append(doc_info)

    return {
        "total_documents": len(documents),
        "sample_documents": debug_info
    }
