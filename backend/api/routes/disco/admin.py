"""DISCo Admin routes - Agents, System KB, and Analytics."""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException

import pb_client as pb
from logger_config import get_logger
from services.disco import (
    get_agent_types,
    get_kb_files,
    load_agent_prompt,
    search_system_kb,
    sync_kb_from_filesystem,
)
from services.disco.agent_service import get_consolidated_agents

logger = get_logger(__name__)
router = APIRouter()


# ============================================================================
# AGENTS (Reference)
# ============================================================================


@router.get("/agents")
async def api_list_agents(
    include_legacy: bool = False,
):
    """List available agent types.

    Args:
        include_legacy: If True, includes legacy agents for backwards compatibility.
                       Default returns only the 4 consolidated stage-aligned agents.
    """
    if include_legacy:
        return {"success": True, "agents": get_agent_types(include_legacy=True)}
    else:
        return {"success": True, "agents": get_consolidated_agents()}


@router.get("/agents/{agent_type}")
async def api_get_agent_prompt(
    agent_type: str,
):
    """Get agent prompt (admin only)."""
    try:
        prompt = load_agent_prompt(agent_type)
        return {"success": True, "agent_type": agent_type, "prompt": prompt}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from None
    except Exception as e:
        logger.error(f"Error loading agent prompt: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# SYSTEM KB (Admin)
# ============================================================================


@router.get("/system-kb")
async def api_list_kb_files():
    """List system KB files (admin only)."""
    try:
        files = await get_kb_files()
        return {"success": True, "files": files}
    except Exception as e:
        logger.error(f"Error listing KB files: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/system-kb/sync")
async def api_sync_kb(
    background_tasks: BackgroundTasks,
):
    """Sync system KB from filesystem (admin only)."""
    try:
        import asyncio

        async def do_sync():
            try:
                result = await sync_kb_from_filesystem()
                logger.info(f"KB sync completed: {result}")
            except Exception as e:
                logger.error(f"KB sync failed: {e}")

        background_tasks.add_task(asyncio.create_task, do_sync())

        return {"success": True, "message": "KB sync started in background"}
    except Exception as e:
        logger.error(f"Error starting KB sync: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/system-kb/search")
async def api_search_kb(
    q: str,
    limit: int = 10,
    category: Optional[str] = None,
):
    """Search system KB."""
    try:
        chunks = await search_system_kb(q, limit=limit, category=category)
        return {"success": True, "results": chunks}
    except Exception as e:
        logger.error(f"Error searching KB: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# ANALYTICS
# ============================================================================


@router.get("/analytics/usage")
async def api_disco_usage_analytics(
    days: int = 30,
):
    """Get DISCo usage analytics - agent runs over time.

    Returns usage trends with each DISCo agent broken out separately.
    """
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Fetch all runs in the date range
        esc_date = pb.escape_filter(start_date.isoformat())
        runs = pb.get_all(
            "disco_runs",
            filter=f"started_at>='{esc_date}'",
            sort="started_at",
        )

        # Build daily counts per agent
        daily_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        agent_totals: dict[str, int] = defaultdict(int)
        all_agents: set[str] = set()

        for run in runs:
            agent_type = run["agent_type"]
            started_at = run.get("started_at") or run.get("created", "")
            if started_at:
                date_str = started_at.split("T")[0]
                daily_counts[date_str][agent_type] += 1
                agent_totals[agent_type] += 1
                all_agents.add(agent_type)

        # Generate all dates in range
        date_cursor = start_date
        all_dates = []
        while date_cursor <= end_date:
            all_dates.append(date_cursor.strftime("%Y-%m-%d"))
            date_cursor += timedelta(days=1)

        # Sort agents by total usage (descending)
        sorted_agents = sorted(all_agents, key=lambda a: agent_totals[a], reverse=True)

        # Build trends data
        trends = []
        for date_str in all_dates:
            data_point = {"date": date_str}
            for agent in sorted_agents:
                data_point[agent] = daily_counts[date_str].get(agent, 0)
            trends.append(data_point)

        return {
            "trends": trends,
            "agents": sorted_agents,
            "agent_totals": dict(agent_totals),
            "total_runs": len(runs),
        }

    except Exception as e:
        logger.error(f"Error fetching DISCo analytics: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e
