"""Admin manifesto compliance analytics -- aggregate compliance scoring data."""

import asyncio
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException

from auth import require_admin
from logger_config import get_logger
from services.manifesto_compliance import (
    AGENT_EXPECTED_PRINCIPLES,
    DRIFT_ALERT_THRESHOLD,
    MIN_MESSAGES_FOR_EVALUATION,
    _get_compliance_level,
)

from ._shared import supabase

logger = get_logger(__name__)
router = APIRouter()


@router.get("/analytics/manifesto-compliance")
async def get_manifesto_compliance(
    current_user: dict = Depends(require_admin),
    days: int = 30,
):
    """Get manifesto compliance analytics aggregated by agent and principle.

    Queries messages and meeting_room_messages for stored compliance data,
    aggregates by agent and principle, and flags drift (low hit rates on
    expected principles).

    Args:
        current_user: Injected by FastAPI dependency.
        days: Number of days to analyze (default 30).
    """
    try:
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        # Query chat messages with compliance data
        chat_messages = await asyncio.to_thread(
            lambda: supabase.table("messages")
            .select("metadata")
            .eq("role", "assistant")
            .gte("created_at", start_date.isoformat())
            .lte("created_at", end_date.isoformat())
            .execute()
        )

        # Query meeting room messages with compliance data
        meeting_messages = await asyncio.to_thread(
            lambda: supabase.table("meeting_room_messages")
            .select("metadata")
            .gte("created_at", start_date.isoformat())
            .lte("created_at", end_date.isoformat())
            .not_.is_("agent_id", "null")
            .execute()
        )

        # Extract compliance records from both sources
        compliance_records = []

        for msg in chat_messages.data or []:
            metadata = msg.get("metadata") or {}
            compliance = metadata.get("manifesto_compliance")
            if compliance:
                compliance_records.append(compliance)

        for msg in meeting_messages.data or []:
            metadata = msg.get("metadata") or {}
            compliance = metadata.get("manifesto_compliance")
            if compliance:
                compliance_records.append(compliance)

        # Aggregate by agent
        by_agent = defaultdict(
            lambda: {
                "messages": 0,
                "total_score": 0.0,
                "principle_hits": defaultdict(int),
                "principle_gaps": defaultdict(int),
            }
        )

        # Aggregate by principle
        by_principle = defaultdict(
            lambda: {
                "total_hits": 0,
                "agents_engaging": set(),
            }
        )

        # Level distribution counts
        level_distribution = {"aligned": 0, "drifting": 0, "misaligned": 0}

        # Source aggregation
        by_source = defaultdict(lambda: {"messages": 0, "total_score": 0.0})

        for record in compliance_records:
            agent = record.get("agent") or "unknown"
            score = record.get("score", 0.0)
            signals = record.get("signals", [])
            gaps = record.get("gaps", [])

            by_agent[agent]["messages"] += 1
            by_agent[agent]["total_score"] += score

            # Level distribution
            level = record.get("level") or _get_compliance_level(score)
            level_distribution[level] = level_distribution.get(level, 0) + 1

            # Source aggregation
            src = record.get("source") or "unknown"
            by_source[src]["messages"] += 1
            by_source[src]["total_score"] += score

            for signal in signals:
                by_agent[agent]["principle_hits"][signal] += 1
                by_principle[signal]["total_hits"] += 1
                by_principle[signal]["agents_engaging"].add(agent)

            for gap in gaps:
                by_agent[agent]["principle_gaps"][gap] += 1

        # Build response
        agent_summary = {}
        for agent, data in by_agent.items():
            msg_count = data["messages"]
            agent_summary[agent] = {
                "messages": msg_count,
                "avg_score": round(data["total_score"] / msg_count, 2) if msg_count else 0.0,
                "principle_hits": dict(data["principle_hits"]),
                "principle_gaps": dict(data["principle_gaps"]),
            }

        principle_summary = {}
        for principle, data in by_principle.items():
            principle_summary[principle] = {
                "total_hits": data["total_hits"],
                "agents_engaging": sorted(data["agents_engaging"]),
            }

        # Source summary with averages
        source_summary = {}
        for src, data in by_source.items():
            msg_count = data["messages"]
            source_summary[src] = {
                "messages": msg_count,
                "avg_score": round(data["total_score"] / msg_count, 2) if msg_count else 0.0,
            }

        # Drift alerts: expected principles with low hit rates
        drift_alerts = []
        for agent, expected in AGENT_EXPECTED_PRINCIPLES.items():
            agent_data = by_agent.get(agent)
            if not agent_data or agent_data["messages"] < MIN_MESSAGES_FOR_EVALUATION:
                continue
            msg_count = agent_data["messages"]
            for principle in expected:
                hits = agent_data["principle_hits"].get(principle, 0)
                hit_rate = hits / msg_count if msg_count else 0.0
                if hit_rate < DRIFT_ALERT_THRESHOLD:
                    drift_alerts.append(
                        {
                            "agent": agent,
                            "principle": principle,
                            "hit_rate": round(hit_rate, 2),
                            "expected": True,
                        }
                    )

        return {
            "period_days": days,
            "total_scored_messages": len(compliance_records),
            "by_agent": agent_summary,
            "by_principle": principle_summary,
            "drift_alerts": drift_alerts,
            "level_distribution": level_distribution,
            "by_source": source_summary,
        }

    except Exception as e:
        logger.error(f"Manifesto compliance analytics error: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred. Please try again.",
        ) from e
