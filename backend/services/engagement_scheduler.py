"""Stakeholder Engagement Scheduler.

This module provides background job scheduling for automated engagement level
calculation. Runs weekly to update stakeholder engagement levels based on
interaction signals.

Architecture:
- Weekly scheduled calculation (default: Sunday 4 AM UTC)
- Uses EngagementCalculator for level determination
- Records all calculations in engagement_level_history for analytics
- Manual trigger available for testing/admin use
"""

import asyncio
from datetime import datetime, timezone
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from logger_config import get_logger

logger = get_logger(__name__)

# Global scheduler instance
engagement_scheduler: Optional[BackgroundScheduler] = None


# ============================================================================
# MAIN SCHEDULER JOB
# ============================================================================


def run_weekly_engagement():
    """Main scheduled job that runs weekly engagement calculation.

    This function:
    1. Gets all clients with stakeholders
    2. Calculates engagement levels for each stakeholder
    3. Records results in engagement_level_history
    4. Logs summary of changes
    """
    from services.engagement_calculator import EngagementCalculator

    try:
        logger.info("")
        logger.info("=" * 60)
        logger.info("Stakeholder Engagement Calculation Started")
        logger.info(f"Time: {datetime.now(timezone.utc).isoformat()}")
        logger.info("=" * 60)

        # Create calculator instance
        calculator = EngagementCalculator()

        # Run async calculation in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(calculator.calculate_all_clients())
        finally:
            loop.close()

        # Log summary
        logger.info("")
        logger.info("Engagement Calculation Summary:")
        logger.info(f"  Clients processed: {result['clients_processed']}")
        logger.info(f"  Total stakeholders: {result['total_stakeholders']}")
        logger.info(f"  Levels changed: {result['total_changed']}")
        logger.info(f"  Promotions: {result['total_promotions']}")
        logger.info(f"  Demotions: {result['total_demotions']}")
        logger.info(f"  Errors: {result['total_errors']}")

        # Log individual changes
        for client_result in result.get("client_results", []):
            if client_result.get("changes"):
                logger.info(f"  Client {client_result['client_id']}:")
                for change in client_result["changes"]:
                    logger.info(
                        f"    {change['previous_level']} -> {change['new_level']}: "
                        f"{change['reason']}"
                    )

        logger.info("")
        logger.info("=" * 60)
        logger.info("Stakeholder Engagement Calculation Completed")
        logger.info("=" * 60)
        logger.info("")

    except Exception as e:
        logger.error(f"Fatal error in weekly engagement job: {e}")
        logger.info("=" * 60)
        logger.info("")


# ============================================================================
# MANUAL TRIGGER
# ============================================================================


async def trigger_manual_calculation(client_id: Optional[str] = None) -> dict:
    """Manually trigger engagement calculation.

    Args:
        client_id: Optional client to calculate for. If None, calculates all.

    Returns:
        dict with calculation results
    """
    from services.engagement_calculator import EngagementCalculator

    try:
        calculator = EngagementCalculator()

        if client_id:
            logger.info(f"Manual engagement calculation triggered for client: {client_id}")
            result = await calculator.calculate_for_client(
                client_id=client_id, calculation_type="manual"
            )
        else:
            logger.info("Manual engagement calculation triggered for all clients")
            result = await calculator.calculate_all_clients()

        return result

    except Exception as e:
        logger.error(f"Manual engagement calculation failed: {e}")
        raise


# ============================================================================
# SCHEDULER LIFECYCLE
# ============================================================================


def start_engagement_scheduler(day_of_week: str = "sun", hour_utc: int = 4, minute: int = 0):
    """Start the background scheduler for automated engagement calculation.

    Args:
        day_of_week: Day to run (mon, tue, wed, thu, fri, sat, sun). Default: Sunday
        hour_utc: Hour to run (0-23). Default: 4 AM UTC
        minute: Minute to run (0-59). Default: 0
    """
    global engagement_scheduler

    if engagement_scheduler is not None and engagement_scheduler.running:
        logger.warning("Engagement scheduler is already running")
        return

    engagement_scheduler = BackgroundScheduler(timezone="UTC")

    # Add weekly engagement job
    engagement_scheduler.add_job(
        func=run_weekly_engagement,
        trigger=CronTrigger(day_of_week=day_of_week, hour=hour_utc, minute=minute),
        id="stakeholder_weekly_engagement",
        name="Stakeholder Weekly Engagement Calculation",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
        misfire_grace_time=3600,  # Allow job to run up to 1 hour late
    )

    engagement_scheduler.start()

    logger.info("")
    logger.info("=" * 60)
    logger.info("Stakeholder Engagement Scheduler Started")
    logger.info(f"  Schedule: Every {day_of_week.capitalize()} at {hour_utc:02d}:{minute:02d} UTC")
    logger.info(f"  Started: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    logger.info("=" * 60)
    logger.info("")


def stop_engagement_scheduler():
    """Stop the engagement scheduler."""
    global engagement_scheduler

    if engagement_scheduler is not None and engagement_scheduler.running:
        engagement_scheduler.shutdown(wait=True)
        logger.info("")
        logger.info("Stakeholder Engagement Scheduler Stopped")
        logger.info("")


def get_engagement_scheduler_status() -> dict:
    """Get the current status of the engagement scheduler.

    Returns:
        dict with running status and job info
    """
    if engagement_scheduler is None:
        return {"running": False, "jobs": []}

    jobs = []
    for job in engagement_scheduler.get_jobs():
        jobs.append(
            {
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            }
        )

    return {"running": engagement_scheduler.running, "jobs": jobs}
