"""Admin manifesto compliance analytics -- aggregate compliance scoring data."""

import asyncio
import math
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException

from auth import require_admin
from logger_config import get_logger
from services.manifesto_compliance import (
    AGENT_EXPECTED_PRINCIPLES,
    DRIFT_ALERT_THRESHOLD,
    MIN_MESSAGES_FOR_EVALUATION,
    PRINCIPLE_DESCRIPTIONS,
    PRINCIPLE_RECOMMENDATIONS,
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
            avg = round(data["total_score"] / msg_count, 2) if msg_count else 0.0
            agent_summary[agent] = {
                "messages": msg_count,
                "avg_score": avg,
                "level": _get_compliance_level(avg),
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


def _build_recommendation(gaps: list[str], signals: list[str], max_items: int = 3) -> str:
    """Build a recommendation string from the top gap principles."""
    parts = []
    for gap in gaps[:max_items]:
        rec = PRINCIPLE_RECOMMENDATIONS.get(gap)
        if rec:
            parts.append(rec)
    if parts:
        return " ".join(parts)
    # Fallback when no specific gaps (agent not in expected config)
    signal_count = len(signals)
    total = len(PRINCIPLE_RECOMMENDATIONS)
    return f"Only {signal_count} of {total} principles detected. Broaden principle engagement across responses."


def _build_why_flagged(gaps: list[str], signals: list[str], max_items: int = 3) -> str:
    """Build a human-readable 'why flagged' string with descriptions."""
    if gaps:
        parts = []
        for gap in gaps[:max_items]:
            desc = PRINCIPLE_DESCRIPTIONS.get(gap)
            label = _format_principle(gap)
            if desc:
                parts.append(f"{label}: {desc}")
            else:
                parts.append(label)
        remaining = len(gaps) - max_items
        result = ". ".join(parts)
        if remaining > 0:
            result += f". Plus {remaining} more gap{'s' if remaining > 1 else ''}."
        return result
    signal_count = len(signals)
    total = len(PRINCIPLE_DESCRIPTIONS)
    return (
        f"Low overall principle coverage -- only {signal_count} of {total} "
        f"manifesto principles detected in this response."
    )


def _format_principle(principle_id: str) -> str:
    """Convert principle ID to readable label, e.g. P3_evidence_over_eloquence -> Evidence over eloquence."""
    parts = principle_id.split("_", 1)
    if len(parts) == 2:
        return parts[1].replace("_", " ").capitalize()
    return principle_id


_TEST_KEYWORDS = {"test", "demo", "example", "draft", "scratch", "debug"}


def _compute_confidence(
    score: float,
    content: str,
    gaps: list[str],
    signals: list[str],
    agent: str,
    agent_baselines: dict[str, dict],
    conv_meta: dict | None,
    conv_message_count: int,
) -> tuple[int, dict[str, str]]:
    """Compute context-aware confidence score for a flagged compliance item.

    Returns (confidence_int, factors_dict) where confidence is 5-99.
    """
    factors = {}

    # 1. Base score (inverse of compliance score)
    base = 1 - score
    factors["base"] = str(round(base * 100))

    # 2. Message length factor
    length = len(content)
    if length < 50:
        length_factor = 0.3
        factors["length"] = "very short <50 chars (0.3x)"
    elif length < 150:
        length_factor = 0.6
        factors["length"] = "short <150 chars (0.6x)"
    elif length < 300:
        length_factor = 0.8
        factors["length"] = "medium <300 chars (0.8x)"
    else:
        length_factor = 1.0
        factors["length"] = "full length (1.0x)"

    # 3. Conversation context factor
    if conv_meta:
        title = (conv_meta.get("title") or "").lower().strip()
        has_project = bool(conv_meta.get("project_id"))
        has_initiative = bool(conv_meta.get("initiative_id"))

        if any(kw in title for kw in _TEST_KEYWORDS):
            context_factor = 0.2
            factors["context"] = "test conversation (0.2x)"
        elif title in ("new conversation", "") or not title:
            context_factor = 0.6
            factors["context"] = "auto-generated title (0.6x)"
        elif has_project and has_initiative:
            context_factor = 1.0
            factors["context"] = "linked to project+initiative (1.0x)"
        elif has_project or has_initiative:
            context_factor = 0.85
            factors["context"] = "linked to project or initiative (0.85x)"
        else:
            context_factor = 0.7
            factors["context"] = "unlinked chat (0.7x)"
    else:
        context_factor = 0.7
        factors["context"] = "no conversation metadata (0.7x)"

    # 4. Conversation maturity factor
    if conv_message_count <= 1:
        maturity_factor = 0.3
        factors["maturity"] = "single message (0.3x)"
    elif conv_message_count <= 3:
        maturity_factor = 0.6
        factors["maturity"] = f"{conv_message_count} messages (0.6x)"
    elif conv_message_count <= 9:
        maturity_factor = 0.8
        factors["maturity"] = f"{conv_message_count} messages (0.8x)"
    else:
        maturity_factor = 1.0
        factors["maturity"] = f"{conv_message_count} messages (1.0x)"

    # 5. Gap severity factor
    expected = AGENT_EXPECTED_PRINCIPLES.get(agent, [])
    if expected:
        gap_ratio = len(gaps) / len(expected) if expected else 0
    else:
        gap_ratio = 1 - (len(signals) / 11) if signals else 1.0
    if gap_ratio < 0.3:
        gap_factor = 0.5
        factors["gap_severity"] = f"minor ({len(gaps)} gaps, 0.5x)"
    elif gap_ratio <= 0.6:
        gap_factor = 0.75
        factors["gap_severity"] = f"moderate ({len(gaps)} gaps, 0.75x)"
    else:
        gap_factor = 1.0
        factors["gap_severity"] = f"major ({len(gaps)} gaps, 1.0x)"

    # 6. Agent historical baseline factor
    baseline = agent_baselines.get(agent)
    if baseline and baseline["count"] >= 3:
        mean = baseline["mean"]
        stddev = baseline["stddev"]
        if stddev > 0:
            z = (mean - score) / stddev  # positive z = score below mean
            if z < 1:
                baseline_factor = 0.6
                factors["baseline"] = f"normal for {agent} (0.6x)"
            elif z < 2:
                baseline_factor = 0.85
                factors["baseline"] = f"notable for {agent} (0.85x)"
            else:
                baseline_factor = 1.0
                factors["baseline"] = f"significant outlier for {agent} (1.0x)"
        else:
            baseline_factor = 0.6
            factors["baseline"] = f"no variance for {agent} (0.6x)"
    else:
        count = baseline["count"] if baseline else 0
        baseline_factor = 0.7
        factors["baseline"] = f"insufficient data ({count} msgs, 0.7x)"

    # Final calculation
    raw = base * length_factor * context_factor * maturity_factor * gap_factor * baseline_factor * 100
    confidence = max(5, min(99, round(raw)))
    return confidence, factors


@router.get("/analytics/manifesto-compliance/flagged")
async def get_flagged_messages(
    current_user: dict = Depends(require_admin),
    days: int = 30,
    level: str = "drifting",
):
    """Get individual flagged messages with compliance details.

    Args:
        current_user: Injected by FastAPI dependency.
        days: Number of days to look back (default 30).
        level: Filter by compliance level ('drifting' or 'misaligned').
    """
    if level not in ("drifting", "misaligned"):
        raise HTTPException(status_code=400, detail="level must be 'drifting' or 'misaligned'")

    try:
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        # Query chat messages
        chat_result = await asyncio.to_thread(
            lambda: supabase.table("messages")
            .select("id, conversation_id, content, metadata, created_at")
            .eq("role", "assistant")
            .gte("created_at", start_date.isoformat())
            .lte("created_at", end_date.isoformat())
            .execute()
        )

        # Query meeting room messages
        meeting_result = await asyncio.to_thread(
            lambda: supabase.table("meeting_room_messages")
            .select("id, meeting_room_id, content, metadata, created_at")
            .gte("created_at", start_date.isoformat())
            .lte("created_at", end_date.isoformat())
            .not_.is_("agent_id", "null")
            .execute()
        )

        # -- Build agent baselines from ALL compliance records in the period --
        agent_scores: dict[str, list[float]] = defaultdict(list)
        for msg in chat_result.data or []:
            c = (msg.get("metadata") or {}).get("manifesto_compliance")
            if c:
                agent_scores[c.get("agent", "unknown")].append(c.get("score", 0.0))
        for msg in meeting_result.data or []:
            c = (msg.get("metadata") or {}).get("manifesto_compliance")
            if c:
                agent_scores[c.get("agent", "unknown")].append(c.get("score", 0.0))

        agent_baselines: dict[str, dict] = {}
        for agent, scores in agent_scores.items():
            count = len(scores)
            mean = sum(scores) / count if count else 0.0
            variance = sum((s - mean) ** 2 for s in scores) / count if count else 0.0
            agent_baselines[agent] = {
                "mean": mean,
                "stddev": math.sqrt(variance),
                "count": count,
            }

        # -- Build conversation message counts --
        conv_msg_counts: dict[str, int] = defaultdict(int)
        for msg in chat_result.data or []:
            cid = msg.get("conversation_id")
            if cid:
                conv_msg_counts[f"chat:{cid}"] += 1
        for msg in meeting_result.data or []:
            mid = msg.get("meeting_room_id")
            if mid:
                conv_msg_counts[f"meeting:{mid}"] += 1

        # -- Batch-fetch conversation metadata --
        chat_conv_ids = list(
            {msg.get("conversation_id") for msg in chat_result.data or [] if msg.get("conversation_id")}
        )
        meeting_room_ids = list(
            {msg.get("meeting_room_id") for msg in meeting_result.data or [] if msg.get("meeting_room_id")}
        )

        conv_meta_map: dict[str, dict] = {}
        if chat_conv_ids:
            conv_result = await asyncio.to_thread(
                lambda: supabase.table("conversations")
                .select("id, title, project_id, initiative_id")
                .in_("id", chat_conv_ids)
                .execute()
            )
            for conv in conv_result.data or []:
                conv_meta_map[f"chat:{conv['id']}"] = {
                    "title": conv.get("title"),
                    "project_id": conv.get("project_id"),
                    "initiative_id": conv.get("initiative_id"),
                }

        if meeting_room_ids:
            mr_result = await asyncio.to_thread(
                lambda: supabase.table("meeting_rooms").select("id, title").in_("id", meeting_room_ids).execute()
            )
            for mr in mr_result.data or []:
                conv_meta_map[f"meeting:{mr['id']}"] = {
                    "title": mr.get("title"),
                    "project_id": None,
                    "initiative_id": None,
                }

        # -- Build flagged items with context-aware confidence --
        items = []

        for msg in chat_result.data or []:
            metadata = msg.get("metadata") or {}
            compliance = metadata.get("manifesto_compliance")
            if not compliance:
                continue
            msg_level = compliance.get("level") or _get_compliance_level(compliance.get("score", 0.0))
            if msg_level != level:
                continue
            gaps = compliance.get("gaps", [])
            signals = compliance.get("signals", [])
            score = compliance.get("score", 0.0)
            content = msg.get("content") or ""
            agent = compliance.get("agent", "unknown")
            conv_id = msg.get("conversation_id")
            meta_key = f"chat:{conv_id}" if conv_id else None

            confidence, confidence_factors = _compute_confidence(
                score=score,
                content=content,
                gaps=gaps,
                signals=signals,
                agent=agent,
                agent_baselines=agent_baselines,
                conv_meta=conv_meta_map.get(meta_key) if meta_key else None,
                conv_message_count=conv_msg_counts.get(meta_key, 0) if meta_key else 0,
            )

            items.append(
                {
                    "id": msg["id"],
                    "source": "chat",
                    "source_id": conv_id,
                    "agent": agent,
                    "score": score,
                    "confidence": confidence,
                    "confidence_factors": confidence_factors,
                    "level": msg_level,
                    "signals": signals,
                    "gaps": gaps,
                    "why_flagged": _build_why_flagged(gaps, signals),
                    "content_preview": content[:150] + ("..." if len(content) > 150 else ""),
                    "created_at": msg.get("created_at"),
                    "recommendation": _build_recommendation(gaps, signals),
                }
            )

        for msg in meeting_result.data or []:
            metadata = msg.get("metadata") or {}
            compliance = metadata.get("manifesto_compliance")
            if not compliance:
                continue
            msg_level = compliance.get("level") or _get_compliance_level(compliance.get("score", 0.0))
            if msg_level != level:
                continue
            gaps = compliance.get("gaps", [])
            signals = compliance.get("signals", [])
            score = compliance.get("score", 0.0)
            content = msg.get("content") or ""
            agent = compliance.get("agent", "unknown")
            mr_id = msg.get("meeting_room_id")
            meta_key = f"meeting:{mr_id}" if mr_id else None

            confidence, confidence_factors = _compute_confidence(
                score=score,
                content=content,
                gaps=gaps,
                signals=signals,
                agent=agent,
                agent_baselines=agent_baselines,
                conv_meta=conv_meta_map.get(meta_key) if meta_key else None,
                conv_message_count=conv_msg_counts.get(meta_key, 0) if meta_key else 0,
            )

            items.append(
                {
                    "id": msg["id"],
                    "source": "meeting_room",
                    "source_id": mr_id,
                    "agent": agent,
                    "score": score,
                    "confidence": confidence,
                    "confidence_factors": confidence_factors,
                    "level": msg_level,
                    "signals": signals,
                    "gaps": gaps,
                    "why_flagged": _build_why_flagged(gaps, signals),
                    "content_preview": content[:150] + ("..." if len(content) > 150 else ""),
                    "created_at": msg.get("created_at"),
                    "recommendation": _build_recommendation(gaps, signals),
                }
            )

        # Sort by created_at descending (most recent first)
        items.sort(key=lambda x: x.get("created_at") or "", reverse=True)

        return {"items": items, "total": len(items)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Flagged messages query error: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred. Please try again.",
        ) from e
