"""
Knowledge Graph Automatic Sync Scheduler

This module provides background job scheduling for automatic Neo4j graph syncs.
It uses APScheduler to run a daily full sync that mirrors PostgreSQL data to Neo4j.
"""

from datetime import datetime, timezone
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from database import get_supabase
from logger_config import get_logger

logger = get_logger(__name__)

# Global scheduler instance
graph_scheduler: Optional[BackgroundScheduler] = None


async def _execute_full_sync(client_id: str) -> dict:
    """
    Execute a full graph sync for a client.

    Args:
        client_id: The client ID to sync

    Returns:
        Dict with sync statistics
    """
    from services.graph import get_graph_sync_service

    sync_service = get_graph_sync_service()
    if not sync_service:
        raise Exception("Graph sync service not available")

    return await sync_service.full_sync(client_id)


def process_graph_sync():
    """
    Main job function that executes graph sync for all active clients.
    Runs daily via APScheduler.
    """
    import asyncio

    try:
        logger.info(f"\n{'='*60}")
        logger.info(f"Knowledge Graph Sync Job Started: {datetime.now(timezone.utc).isoformat()}")
        logger.info(f"{'='*60}")

        supabase = get_supabase()

        # Get all active clients
        result = supabase.table('clients')\
            .select('id, name')\
            .eq('is_active', True)\
            .execute()

        clients = result.data or []

        if not clients:
            logger.info("   No active clients found for graph sync")
            logger.info(f"{'='*60}\n")
            return

        logger.info(f"   Found {len(clients)} active client(s) for graph sync")

        # Process each client
        total_synced = 0
        total_errors = 0

        for client in clients:
            try:
                client_id = client['id']
                client_name = client.get('name', 'Unknown')

                logger.info(f"\n   Syncing client: {client_name} ({client_id})")

                # Run the async sync in the sync context
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    sync_result = loop.run_until_complete(_execute_full_sync(client_id))

                    # Count totals from results
                    synced_count = sum(
                        v.get('synced', 0) for k, v in sync_result.items()
                        if isinstance(v, dict) and 'synced' in v
                    )
                    error_count = sum(
                        v.get('errors', 0) for k, v in sync_result.items()
                        if isinstance(v, dict) and 'errors' in v
                    )

                    total_synced += synced_count
                    total_errors += error_count

                    logger.info(f"      Synced {synced_count} entities, {error_count} errors")

                finally:
                    loop.close()

            except Exception as client_error:
                logger.error(f"      Error syncing client {client.get('id')}: {str(client_error)}")
                total_errors += 1

        logger.info(f"\n{'='*60}")
        logger.info(f"Knowledge Graph Sync Job Completed: {datetime.now(timezone.utc).isoformat()}")
        logger.info(f"   Total synced: {total_synced}, Total errors: {total_errors}")
        logger.info(f"{'='*60}\n")

    except Exception as e:
        logger.error(f"\nFatal error in graph sync job: {str(e)}")
        logger.info(f"{'='*60}\n")


def start_graph_sync_scheduler(hour_utc: int = 3, minute: int = 0):
    """
    Start the background scheduler for automatic graph syncs.

    Args:
        hour_utc: Hour (UTC) to run the daily sync (default: 3 AM UTC)
        minute: Minute to run the sync (default: 0)
    """
    global graph_scheduler

    if graph_scheduler is not None and graph_scheduler.running:
        logger.warning("Graph sync scheduler is already running")
        return

    graph_scheduler = BackgroundScheduler(timezone='UTC')

    # Add daily job at specified time
    # coalesce=True: Combine multiple missed runs into one
    # max_instances=1: Only allow one instance at a time
    # misfire_grace_time=3600: Allow job to run up to 1 hour late before skipping
    graph_scheduler.add_job(
        func=process_graph_sync,
        trigger=CronTrigger(hour=hour_utc, minute=minute),
        id='knowledge_graph_daily_sync',
        name='Knowledge Graph Daily Sync',
        replace_existing=True,
        coalesce=True,
        max_instances=1,
        misfire_grace_time=3600
    )

    graph_scheduler.start()

    logger.info(f"\n{'='*60}")
    logger.info("Knowledge Graph Sync Scheduler Started")
    logger.info(f"   Schedule: Daily at {hour_utc:02d}:{minute:02d} UTC")
    logger.info(f"   Started at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    logger.info(f"{'='*60}\n")


def stop_graph_sync_scheduler():
    """
    Stop the background scheduler.
    """
    global graph_scheduler

    if graph_scheduler is not None and graph_scheduler.running:
        graph_scheduler.shutdown(wait=True)
        logger.info("Knowledge Graph Sync Scheduler Stopped")


def get_graph_scheduler_status() -> dict:
    """
    Get the current status of the graph sync scheduler.

    Returns:
        dict: Scheduler status information
    """
    if graph_scheduler is None:
        return {
            'running': False,
            'jobs': []
        }

    jobs = []
    for job in graph_scheduler.get_jobs():
        jobs.append({
            'id': job.id,
            'name': job.name,
            'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None
        })

    return {
        'running': graph_scheduler.running,
        'jobs': jobs
    }


def trigger_manual_sync():
    """
    Trigger an immediate graph sync (for manual/on-demand sync).
    Returns immediately after starting the sync in a background thread.
    """
    import threading

    thread = threading.Thread(target=process_graph_sync, daemon=True)
    thread.start()

    return {
        'status': 'started',
        'message': 'Graph sync started in background'
    }
