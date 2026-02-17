"""Discovery Inbox Scan Scheduler.

Runs a daily background scan of meeting documents to extract tasks,
projects, and stakeholders into the discovery inbox.
"""

import asyncio
from datetime import datetime, timezone
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from database import get_supabase
from logger_config import get_logger

logger = get_logger(__name__)

# Global scheduler instance
discovery_scheduler: Optional[BackgroundScheduler] = None


async def _execute_discovery_scan(user_id: str, client_id: str) -> dict:
    """Execute a discovery scan for a user/client pair."""
    from services.granola_scanner import scan_meeting_documents

    return await scan_meeting_documents(user_id, client_id, force_rescan=False)


def process_discovery_scan():
    """Main job function that scans documents for all active users.

    Runs daily via APScheduler.
    """
    try:
        logger.info(f"Discovery Scan Job Started: {datetime.now(timezone.utc).isoformat()}")

        supabase = get_supabase()

        # Get active users (users who have logged in recently)
        result = (
            supabase.table("profiles").select("id, client_id, display_name").not_.is_("client_id", "null").execute()
        )

        users = result.data or []

        if not users:
            logger.info("   No active users found for discovery scan")
            return

        logger.info(f"   Found {len(users)} user(s) for discovery scan")

        total_scanned = 0
        total_extracted = 0

        for user in users:
            try:
                user_id = user["id"]
                client_id = user["client_id"]
                display_name = user.get("display_name", "Unknown")

                logger.info(f"   Scanning for user: {display_name}")

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(_execute_discovery_scan(user_id, client_id))

                    stats = result.get("stats", {})
                    scanned = stats.get("files_scanned", 0)
                    extracted = stats.get("total_extracted", 0)
                    total_scanned += scanned
                    total_extracted += extracted

                    logger.info(f"      Scanned {scanned} docs, extracted {extracted} items")
                finally:
                    loop.close()

            except Exception as user_error:
                logger.error(f"      Error scanning for user {user.get('id')}: {user_error}")

        logger.info(
            f"Discovery Scan Job Completed: scanned {total_scanned} docs, " f"extracted {total_extracted} items"
        )

    except Exception as e:
        logger.error(f"Fatal error in discovery scan job: {e}")


def start_discovery_scan_scheduler(hour_utc: int = 5, minute: int = 0):
    """Start the daily discovery scan scheduler.

    Args:
        hour_utc: Hour (UTC) to run (default: 5 AM UTC / 6 AM CET)
        minute: Minute to run (default: 0)
    """
    global discovery_scheduler

    if discovery_scheduler is not None and discovery_scheduler.running:
        logger.warning("Discovery scan scheduler is already running")
        return

    discovery_scheduler = BackgroundScheduler(timezone="UTC")

    discovery_scheduler.add_job(
        func=process_discovery_scan,
        trigger=CronTrigger(hour=hour_utc, minute=minute),
        id="discovery_daily_scan",
        name="Discovery Inbox Daily Scan",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
        misfire_grace_time=3600,
    )

    discovery_scheduler.start()

    logger.info(f"Discovery Scan Scheduler Started: Daily at {hour_utc:02d}:{minute:02d} UTC")


def stop_discovery_scan_scheduler():
    """Stop the discovery scan scheduler."""
    global discovery_scheduler

    if discovery_scheduler is not None and discovery_scheduler.running:
        discovery_scheduler.shutdown(wait=True)
        logger.info("Discovery Scan Scheduler Stopped")
