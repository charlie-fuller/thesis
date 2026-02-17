"""Manifesto Compliance Digest Scheduler.

Weekly scheduled job that aggregates manifesto compliance data and sends
a digest email to admins. Follows the engagement_scheduler.py pattern.

Architecture:
- Weekly scheduled digest (default: Monday 7 AM UTC)
- Queries 7 days of compliance data from messages + meeting_room_messages
- Computes per-agent stats, level distribution, drift alerts
- Sends via Resend email with fallback to logging
- Manual trigger available for testing/admin use
"""

import asyncio
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from logger_config import get_logger

logger = get_logger(__name__)

# Global scheduler instance
manifesto_digest_scheduler: Optional[BackgroundScheduler] = None


# ============================================================================
# MAIN SCHEDULER JOB
# ============================================================================


def run_weekly_digest():
    """Main scheduled job that runs weekly manifesto compliance digest."""
    try:
        logger.info("")
        logger.info("=" * 60)
        logger.info("Manifesto Compliance Digest Started")
        logger.info(f"Time: {datetime.now(timezone.utc).isoformat()}")
        logger.info("=" * 60)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_generate_and_send_digest())
        finally:
            loop.close()

        logger.info(f"Digest result: {result.get('method', 'unknown')}")
        logger.info("=" * 60)
        logger.info("Manifesto Compliance Digest Completed")
        logger.info("=" * 60)
        logger.info("")

    except Exception as e:
        logger.error(f"Fatal error in weekly manifesto digest job: {e}")


async def _generate_and_send_digest() -> dict:
    """Generate and send the weekly manifesto compliance digest."""
    from collections import defaultdict

    from database import get_supabase
    from services.manifesto_compliance import (
        AGENT_EXPECTED_PRINCIPLES,
        DRIFT_ALERT_THRESHOLD,
        MIN_MESSAGES_FOR_EVALUATION,
        _get_compliance_level,
    )

    supabase = get_supabase()

    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=7)

    # Query chat messages
    chat_result = await asyncio.to_thread(
        lambda: supabase.table("messages")
        .select("metadata")
        .eq("role", "assistant")
        .gte("created_at", start_date.isoformat())
        .lte("created_at", end_date.isoformat())
        .execute()
    )

    # Query meeting messages
    meeting_result = await asyncio.to_thread(
        lambda: supabase.table("meeting_room_messages")
        .select("metadata")
        .gte("created_at", start_date.isoformat())
        .lte("created_at", end_date.isoformat())
        .not_.is_("agent_id", "null")
        .execute()
    )

    # Extract compliance records
    records = []
    for msg in (chat_result.data or []) + (meeting_result.data or []):
        metadata = msg.get("metadata") or {}
        compliance = metadata.get("manifesto_compliance")
        if compliance:
            records.append(compliance)

    if not records:
        logger.info("No manifesto compliance data for the past week")
        return {"method": "none", "reason": "no_data"}

    # Aggregate
    by_agent = defaultdict(lambda: {"messages": 0, "total_score": 0.0, "signals": defaultdict(int)})
    level_counts = {"aligned": 0, "drifting": 0, "misaligned": 0}
    source_counts = defaultdict(int)

    for record in records:
        agent = record.get("agent") or "unknown"
        score = record.get("score", 0.0)
        level = record.get("level") or _get_compliance_level(score)

        by_agent[agent]["messages"] += 1
        by_agent[agent]["total_score"] += score
        for sig in record.get("signals", []):
            by_agent[agent]["signals"][sig] += 1

        level_counts[level] = level_counts.get(level, 0) + 1
        source_counts[record.get("source", "unknown")] += 1

    # Drift alerts
    drift_alerts = []
    for agent, expected in AGENT_EXPECTED_PRINCIPLES.items():
        agent_data = by_agent.get(agent)
        if not agent_data or agent_data["messages"] < MIN_MESSAGES_FOR_EVALUATION:
            continue
        msg_count = agent_data["messages"]
        for principle in expected:
            hits = agent_data["signals"].get(principle, 0)
            hit_rate = hits / msg_count if msg_count else 0.0
            if hit_rate < DRIFT_ALERT_THRESHOLD:
                drift_alerts.append(f"  - {agent}: {principle} ({hit_rate:.0%} hit rate)")

    # Build email content
    total = len(records)
    avg_score = sum(r.get("score", 0.0) for r in records) / total if total else 0.0

    # Agent table rows
    agent_rows_html = ""
    agent_rows_text = ""
    for agent, data in sorted(by_agent.items()):
        msg_count = data["messages"]
        avg = data["total_score"] / msg_count if msg_count else 0.0
        level = _get_compliance_level(avg)
        agent_rows_html += f"<tr><td>{agent}</td><td>{msg_count}</td><td>{avg:.2f}</td><td>{level}</td></tr>\n"
        agent_rows_text += f"  {agent:20s} | {msg_count:>4d} msgs | avg {avg:.2f} | {level}\n"

    period_start = start_date.strftime("%b %d")
    period_end = end_date.strftime("%b %d, %Y")

    subject = f"Manifesto Compliance Digest: {period_start} - {period_end}"

    html_body = f"""
    <h2>Weekly Manifesto Compliance Digest</h2>
    <p><strong>Period:</strong> {period_start} - {period_end}</p>

    <h3>Summary</h3>
    <ul>
        <li><strong>Total scored messages:</strong> {total}</li>
        <li><strong>Average score:</strong> {avg_score:.2f}</li>
        <li><strong>Aligned:</strong> {level_counts['aligned']} | <strong>Drifting:</strong> {level_counts['drifting']} | <strong>Misaligned:</strong> {level_counts['misaligned']}</li>
        <li><strong>Sources:</strong> {', '.join(f'{k}: {v}' for k, v in source_counts.items())}</li>
    </ul>

    <h3>Per-Agent Breakdown</h3>
    <table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse;">
        <tr><th>Agent</th><th>Messages</th><th>Avg Score</th><th>Level</th></tr>
        {agent_rows_html}
    </table>

    {"<h3>Drift Alerts</h3><ul>" + "".join(f"<li>{a}</li>" for a in drift_alerts) + "</ul>" if drift_alerts else "<p>No drift alerts this week.</p>"}

    <hr style="margin: 24px 0; border: none; border-top: 1px solid #E5E7EB;">
    <p style="color: #6B7280; font-size: 14px;">
        Automated weekly digest from Thesis Manifesto Compliance System.
    </p>
    """

    newline = "\n"
    drift_section = (
        f"Drift Alerts:{newline}{newline.join(drift_alerts)}" if drift_alerts else "No drift alerts this week."
    )

    text_body = f"""Weekly Manifesto Compliance Digest
Period: {period_start} - {period_end}

Summary:
  Total scored messages: {total}
  Average score: {avg_score:.2f}
  Aligned: {level_counts['aligned']} | Drifting: {level_counts['drifting']} | Misaligned: {level_counts['misaligned']}
  Sources: {', '.join(f'{k}: {v}' for k, v in source_counts.items())}

Per-Agent Breakdown:
{agent_rows_text}
{drift_section}
"""

    return await _send_digest_email(subject, html_body, text_body)


async def _send_digest_email(subject: str, html_body: str, text_body: str) -> dict:
    """Send the digest email via Resend with fallback to logging."""
    from services.admin_notifications import get_admin_emails

    admin_emails = await get_admin_emails()
    if not admin_emails:
        logger.warning("[Manifesto Digest] No admin users found")
        return {"method": "none", "reason": "no_admins"}

    resend_key = os.environ.get("RESEND_API_KEY")
    if resend_key:
        try:
            import resend

            resend.api_key = resend_key
            from_email = os.environ.get("RESEND_FROM_EMAIL", "onboarding@resend.dev")

            emails_sent = 0
            for email in admin_emails:
                try:
                    resend.Emails.send(
                        {
                            "from": from_email,
                            "to": email,
                            "subject": subject,
                            "html": html_body,
                            "text": text_body,
                        }
                    )
                    emails_sent += 1
                except Exception as e:
                    logger.error(f"[Manifesto Digest] Failed to send to {email}: {e}")

            return {"method": "email", "emails_sent": emails_sent}

        except ImportError:
            logger.warning("[Manifesto Digest] Resend library not installed")

    # Fallback: log only
    logger.info("=" * 80)
    logger.info("[Manifesto Digest] EMAIL NOTIFICATION (Log Only)")
    logger.info(f"To: {', '.join(admin_emails)}")
    logger.info(f"Subject: {subject}")
    logger.info("-" * 80)
    logger.info(text_body)
    logger.info("=" * 80)

    return {"method": "log_only", "admin_emails": admin_emails}


# ============================================================================
# MANUAL TRIGGER
# ============================================================================


async def trigger_manual_digest() -> dict:
    """Manually trigger the manifesto compliance digest.

    Returns:
        dict with digest results
    """
    logger.info("Manual manifesto compliance digest triggered")
    return await _generate_and_send_digest()


# ============================================================================
# SCHEDULER LIFECYCLE
# ============================================================================


def start_manifesto_digest_scheduler(day_of_week: str = "mon", hour_utc: int = 7, minute: int = 0):
    """Start the background scheduler for weekly manifesto digest.

    Args:
        day_of_week: Day to run (mon-sun). Default: Monday
        hour_utc: Hour to run (0-23). Default: 7 AM UTC
        minute: Minute to run (0-59). Default: 0
    """
    global manifesto_digest_scheduler

    if manifesto_digest_scheduler is not None and manifesto_digest_scheduler.running:
        logger.warning("Manifesto digest scheduler is already running")
        return

    manifesto_digest_scheduler = BackgroundScheduler(timezone="UTC")

    manifesto_digest_scheduler.add_job(
        func=run_weekly_digest,
        trigger=CronTrigger(day_of_week=day_of_week, hour=hour_utc, minute=minute),
        id="manifesto_weekly_digest",
        name="Manifesto Weekly Compliance Digest",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
        misfire_grace_time=3600,
    )

    manifesto_digest_scheduler.start()

    logger.info("")
    logger.info("=" * 60)
    logger.info("Manifesto Digest Scheduler Started")
    logger.info(f"  Schedule: Every {day_of_week.capitalize()} at {hour_utc:02d}:{minute:02d} UTC")
    logger.info(f"  Started: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    logger.info("=" * 60)
    logger.info("")


def stop_manifesto_digest_scheduler():
    """Stop the manifesto digest scheduler."""
    global manifesto_digest_scheduler

    if manifesto_digest_scheduler is not None and manifesto_digest_scheduler.running:
        manifesto_digest_scheduler.shutdown(wait=True)
        logger.info("Manifesto Digest Scheduler Stopped")
