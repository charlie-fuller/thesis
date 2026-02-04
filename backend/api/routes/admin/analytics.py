"""Admin analytics routes - usage trends, health metrics, keyword analysis."""

import asyncio
import re
from collections import Counter
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request

from auth import require_admin
from logger_config import get_logger

from ._shared import limiter, supabase

logger = get_logger(__name__)
router = APIRouter()


@router.get("/analytics/usage-trends")
async def get_usage_trends(
    current_user: dict = Depends(require_admin),
    days: int = 30,
):
    """Get usage trends over time, grouped by agent.

    Args:
        current_user: Injected by FastAPI dependency.
        days: Number of days to analyze.
    """
    try:
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        # Get all agents for reference
        agents_result = await asyncio.to_thread(
            lambda: supabase.table("agents").select("id, name, display_name").execute()
        )
        agent_display_names = {a["name"]: a.get("display_name", a["name"]) for a in (agents_result.data or [])}

        # Get all assistant messages in range WITH metadata
        messages = await asyncio.to_thread(
            lambda: supabase.table("messages")
            .select("created_at, metadata")
            .eq("role", "assistant")
            .gte("created_at", start_date.isoformat())
            .lte("created_at", end_date.isoformat())
            .execute()
        )

        # Also get meeting room messages for multi-agent conversations
        meeting_messages = await asyncio.to_thread(
            lambda: supabase.table("meeting_room_messages")
            .select("created_at, agent_id, agent_name")
            .gte("created_at", start_date.isoformat())
            .lte("created_at", end_date.isoformat())
            .not_.is_("agent_id", "null")
            .execute()
        )

        # Get all conversations in range
        convos = await asyncio.to_thread(
            lambda: supabase.table("conversations")
            .select("created_at")
            .gte("created_at", start_date.isoformat())
            .lte("created_at", end_date.isoformat())
            .execute()
        )

        # Get all documents in range
        docs = await asyncio.to_thread(
            lambda: supabase.table("documents")
            .select("uploaded_at")
            .gte("uploaded_at", start_date.isoformat())
            .lte("uploaded_at", end_date.isoformat())
            .execute()
        )

        # Initialize trends by date
        trends_by_date = {}
        current_date = start_date.date()
        while current_date <= end_date.date():
            date_str = current_date.isoformat()
            trends_by_date[date_str] = {
                "date": date_str,
                "conversations": 0,
                "documents": 0,
                "messages": 0,
                "agent_usage": {},
            }
            current_date += timedelta(days=1)

        # Count messages by date AND extract agent from metadata
        for msg in messages.data or []:
            date = datetime.fromisoformat(msg["created_at"].replace("Z", "+00:00")).date().isoformat()
            if date in trends_by_date:
                trends_by_date[date]["messages"] += 1

                metadata = msg.get("metadata") or {}
                agent_name = metadata.get("agent_display_name") or metadata.get("agent_name")
                if agent_name:
                    normalized_name = agent_display_names.get(agent_name, agent_name)
                    if normalized_name and normalized_name[0].islower():
                        normalized_name = normalized_name.capitalize()
                    trends_by_date[date]["agent_usage"][normalized_name] = (
                        trends_by_date[date]["agent_usage"].get(normalized_name, 0) + 1
                    )

        # Count meeting room messages by date and agent
        for msg in meeting_messages.data or []:
            date = datetime.fromisoformat(msg["created_at"].replace("Z", "+00:00")).date().isoformat()
            if date in trends_by_date:
                trends_by_date[date]["messages"] += 1
                agent_name = msg.get("agent_name", "Unknown")
                if agent_name:
                    normalized_name = agent_display_names.get(agent_name, agent_name)
                    if normalized_name and normalized_name[0].islower():
                        normalized_name = normalized_name.capitalize()
                    trends_by_date[date]["agent_usage"][normalized_name] = (
                        trends_by_date[date]["agent_usage"].get(normalized_name, 0) + 1
                    )

        # Count conversations by date
        for convo in convos.data or []:
            date = datetime.fromisoformat(convo["created_at"].replace("Z", "+00:00")).date().isoformat()
            if date in trends_by_date:
                trends_by_date[date]["conversations"] += 1

        # Count documents by date
        for doc in docs.data or []:
            date = datetime.fromisoformat(doc["uploaded_at"].replace("Z", "+00:00")).date().isoformat()
            if date in trends_by_date:
                trends_by_date[date]["documents"] += 1

        # Collect all agent names for consistent series
        all_agents = set()
        for day_data in trends_by_date.values():
            all_agents.update(day_data["agent_usage"].keys())

        # Build final trends with per-agent columns
        trends = []
        for date_str in sorted(trends_by_date.keys()):
            day = trends_by_date[date_str]
            trend_entry = {
                "date": day["date"],
                "conversations": day["conversations"],
                "documents": day["documents"],
                "messages": day["messages"],
            }
            for agent_name in all_agents:
                trend_entry[agent_name] = day["agent_usage"].get(agent_name, 0)
            trends.append(trend_entry)

        # Build agent summary
        agent_totals = {}
        for day_data in trends_by_date.values():
            for agent_name, count in day_data["agent_usage"].items():
                agent_totals[agent_name] = agent_totals.get(agent_name, 0) + count

        sorted_agents = sorted(agent_totals.items(), key=lambda x: -x[1])

        return {
            "success": True,
            "trends": trends,
            "agents": [a[0] for a in sorted_agents],
            "agent_totals": dict(sorted_agents),
        }
    except Exception as e:
        logger.error(f"Analytics error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/analytics/active-users")
async def get_active_users(
    current_user: dict = Depends(require_admin),
    days: int = 7,
):
    """Get active users in specified timeframe.

    Args:
        current_user: Injected by FastAPI dependency.
        days: Number of days to analyze.
    """
    try:
        total_users_result = await asyncio.to_thread(
            lambda: supabase.table("users").select("id", count="exact").execute()
        )
        total_users = total_users_result.count or 0

        seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        active_7_convos = await asyncio.to_thread(
            lambda: supabase.table("conversations").select("user_id").gte("updated_at", seven_days_ago).execute()
        )

        active_7_user_ids = set()
        for convo in active_7_convos.data or []:
            if convo.get("user_id"):
                active_7_user_ids.add(convo["user_id"])

        thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        active_30_convos = await asyncio.to_thread(
            lambda: supabase.table("conversations").select("user_id").gte("updated_at", thirty_days_ago).execute()
        )

        active_30_user_ids = set()
        for convo in active_30_convos.data or []:
            if convo.get("user_id"):
                active_30_user_ids.add(convo["user_id"])

        return {
            "success": True,
            "active_users": {
                "last_7_days": len(active_7_user_ids),
                "last_30_days": len(active_30_user_ids),
                "total_users": total_users,
            },
        }
    except Exception as e:
        logger.error(f"Active users error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/analytics/recent-activity")
async def get_recent_activity(
    current_user: dict = Depends(require_admin),
    limit: int = 20,
):
    """Get recent platform activity.

    Args:
        current_user: Injected by FastAPI dependency.
        limit: Maximum items to return.
    """
    try:
        convos = await asyncio.to_thread(
            lambda: supabase.table("conversations")
            .select("id, title, created_at, user_id, users:user_id(id, name, email)")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

        docs = await asyncio.to_thread(
            lambda: supabase.table("documents")
            .select("id, filename, uploaded_at, uploaded_by, users:uploaded_by(id, name, email)")
            .order("uploaded_at", desc=True)
            .limit(limit)
            .execute()
        )

        activity = []

        for conv in convos.data or []:
            msg_count_result = await asyncio.to_thread(
                lambda c=conv: supabase.table("messages")
                .select("id", count="exact")
                .eq("conversation_id", c["id"])
                .execute()
            )

            activity.append(
                {
                    "type": "conversation",
                    "id": conv["id"],
                    "timestamp": conv["created_at"],
                    "title": conv.get("title"),
                    "user": conv.get("users") if conv.get("users") else None,
                    "message_count": msg_count_result.count or 0,
                }
            )

        for doc in docs.data or []:
            activity.append(
                {
                    "type": "document",
                    "id": doc["id"],
                    "timestamp": doc["uploaded_at"],
                    "filename": doc.get("filename"),
                    "user": doc.get("users") if doc.get("users") else None,
                }
            )

        activity.sort(key=lambda x: x["timestamp"], reverse=True)
        activity = activity[:limit]

        return {"success": True, "activity": activity}
    except Exception as e:
        logger.error(f"Recent activity error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/analytics/upload-health")
async def get_upload_health(current_user: dict = Depends(require_admin)):
    """Get document upload health metrics.

    Returns success rates, failure breakdown, and stuck documents.

    Args:
        current_user: Injected by FastAPI dependency.
    """
    try:
        now = datetime.now(timezone.utc)
        one_day_ago = (now - timedelta(days=1)).isoformat()
        seven_days_ago = (now - timedelta(days=7)).isoformat()
        thirty_days_ago = (now - timedelta(days=30)).isoformat()
        one_hour_ago = (now - timedelta(hours=1)).isoformat()

        async def get_status_counts(since: str):
            result = await asyncio.to_thread(
                lambda: supabase.table("documents")
                .select("processing_status, filename")
                .gte("uploaded_at", since)
                .execute()
            )
            docs = result.data or []

            counts = {
                "total": len(docs),
                "completed": 0,
                "failed": 0,
                "pending": 0,
                "processing": 0,
            }
            failed_by_type = {}

            for doc in docs:
                status = doc.get("processing_status", "pending")
                if status in counts:
                    counts[status] += 1

                if status == "failed":
                    filename = doc.get("filename", "")
                    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "unknown"
                    failed_by_type[ext] = failed_by_type.get(ext, 0) + 1

            success_rate = (counts["completed"] / counts["total"] * 100) if counts["total"] > 0 else 100
            return counts, success_rate, failed_by_type

        counts_24h, rate_24h, failed_types_24h = await get_status_counts(one_day_ago)
        counts_7d, rate_7d, failed_types_7d = await get_status_counts(seven_days_ago)
        counts_30d, rate_30d, _ = await get_status_counts(thirty_days_ago)

        stuck_result = await asyncio.to_thread(
            lambda: supabase.table("documents")
            .select("id, filename, processing_status, uploaded_at")
            .in_("processing_status", ["pending", "processing"])
            .lt("uploaded_at", one_hour_ago)
            .execute()
        )
        stuck_docs = stuck_result.data or []

        recent_failures = await asyncio.to_thread(
            lambda: supabase.table("documents")
            .select("id, filename, processing_error, uploaded_at")
            .eq("processing_status", "failed")
            .gte("uploaded_at", seven_days_ago)
            .order("uploaded_at", desc=True)
            .limit(5)
            .execute()
        )

        logger.info(f"Upload health: {rate_24h:.1f}% success (24h), {len(stuck_docs)} stuck")

        return {
            "success": True,
            "periods": {
                "24h": {
                    "total": counts_24h["total"],
                    "completed": counts_24h["completed"],
                    "failed": counts_24h["failed"],
                    "pending": counts_24h["pending"],
                    "processing": counts_24h["processing"],
                    "success_rate": round(rate_24h, 1),
                    "failed_by_type": failed_types_24h,
                },
                "7d": {
                    "total": counts_7d["total"],
                    "completed": counts_7d["completed"],
                    "failed": counts_7d["failed"],
                    "success_rate": round(rate_7d, 1),
                    "failed_by_type": failed_types_7d,
                },
                "30d": {
                    "total": counts_30d["total"],
                    "completed": counts_30d["completed"],
                    "failed": counts_30d["failed"],
                    "success_rate": round(rate_30d, 1),
                },
            },
            "stuck_documents": [
                {
                    "id": doc["id"],
                    "filename": doc["filename"],
                    "status": doc["processing_status"],
                    "uploaded_at": doc["uploaded_at"],
                }
                for doc in stuck_docs
            ],
            "recent_failures": [
                {
                    "id": doc["id"],
                    "filename": doc["filename"],
                    "error": doc.get("processing_error", "Unknown error"),
                    "uploaded_at": doc["uploaded_at"],
                }
                for doc in (recent_failures.data or [])
            ],
        }
    except Exception as e:
        logger.error(f"Upload health error: {str(e)}")
        return {
            "success": False,
            "error": "Database temporarily unavailable",
            "periods": {
                "24h": {
                    "total": 0,
                    "completed": 0,
                    "failed": 0,
                    "pending": 0,
                    "processing": 0,
                    "success_rate": 0,
                    "failed_by_type": {},
                },
                "7d": {
                    "total": 0,
                    "completed": 0,
                    "failed": 0,
                    "success_rate": 0,
                    "failed_by_type": {},
                },
                "30d": {"total": 0, "completed": 0, "failed": 0, "success_rate": 0},
            },
            "stuck_documents": [],
            "recent_failures": [],
        }


@router.post("/analytics/upload-health/clear-issues")
@limiter.limit("10/minute")
async def clear_upload_issues(
    request: Request,
    current_user: dict = Depends(require_admin),
):
    """Clear stuck documents and recent failures from the upload health panel.

    Args:
        request: FastAPI request object for rate limiting.
        current_user: Injected by FastAPI dependency.
    """
    try:
        now = datetime.now(timezone.utc)
        one_hour_ago = (now - timedelta(hours=1)).isoformat()
        seven_days_ago = (now - timedelta(days=7)).isoformat()

        stuck_result = await asyncio.to_thread(
            lambda: supabase.table("documents")
            .select("id, filename")
            .in_("processing_status", ["pending", "processing"])
            .lt("uploaded_at", one_hour_ago)
            .execute()
        )
        stuck_docs = stuck_result.data or []

        stuck_count = 0
        for doc in stuck_docs:
            await asyncio.to_thread(
                lambda doc_id=doc["id"]: supabase.table("documents")
                .update(
                    {
                        "processing_status": "failed",
                        "processing_error": "Cleared by admin - document was stuck in processing",
                    }
                )
                .eq("id", doc_id)
                .execute()
            )
            stuck_count += 1

        failures_result = await asyncio.to_thread(
            lambda: supabase.table("documents")
            .select("id")
            .eq("processing_status", "failed")
            .gte("uploaded_at", seven_days_ago)
            .execute()
        )
        failed_docs = failures_result.data or []

        failures_count = 0
        for doc in failed_docs:
            await asyncio.to_thread(
                lambda doc_id=doc["id"]: supabase.table("documents").delete().eq("id", doc_id).execute()
            )
            failures_count += 1

        logger.info(
            f"Admin {current_user.get('email')} cleared upload issues: {stuck_count} stuck, {failures_count} failures"
        )

        return {
            "success": True,
            "cleared": {"stuck_documents": stuck_count, "recent_failures": failures_count},
            "message": f"Cleared {stuck_count} stuck documents and {failures_count} failed uploads",
        }
    except Exception as e:
        logger.error(f"Clear upload issues error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/analytics/interface-health")
async def get_interface_health(current_user: dict = Depends(require_admin)):
    """Get interface health metrics.

    Returns response length stats, image generation stats, and workflow metrics.

    Args:
        current_user: Injected by FastAPI dependency.
    """
    try:
        now = datetime.now(timezone.utc)
        seven_days_ago = (now - timedelta(days=7)).isoformat()
        five_minutes_ago = (now - timedelta(minutes=5)).isoformat()
        one_hour_ago = (now - timedelta(hours=1)).isoformat()

        messages_task = asyncio.to_thread(
            lambda: supabase.table("messages")
            .select("content")
            .eq("role", "assistant")
            .gte("created_at", seven_days_ago)
            .execute()
        )

        convos_task = asyncio.to_thread(
            lambda: supabase.table("conversations")
            .select("id", count="exact")
            .gte("created_at", seven_days_ago)
            .execute()
        )

        active_users_task = asyncio.to_thread(
            lambda: supabase.table("conversations").select("user_id").gte("updated_at", seven_days_ago).execute()
        )

        recent_messages_task = asyncio.to_thread(
            lambda: supabase.table("messages")
            .select("conversation_id, metadata, created_at")
            .gte("created_at", one_hour_ago)
            .lt("created_at", five_minutes_ago)
            .order("created_at", desc=True)
            .limit(50)
            .execute()
        )

        (
            messages_result,
            convos_result,
            active_users_result,
            recent_messages_result,
        ) = await asyncio.gather(messages_task, convos_task, active_users_task, recent_messages_task)

        messages = messages_result.data or []

        total_words = 0
        response_count = 0

        for msg in messages:
            content = msg.get("content", "")
            if content:
                word_count = len(content.split())
                total_words += word_count
                response_count += 1

        avg_response_length = round(total_words / response_count) if response_count > 0 else 0
        total_conversations_7d = convos_result.count or 0

        active_user_ids = set()
        for convo in active_users_result.data or []:
            if convo.get("user_id"):
                active_user_ids.add(convo["user_id"])
        active_users_count = len(active_user_ids)

        stuck_conversations = set()
        for msg in recent_messages_result.data or []:
            metadata = msg.get("metadata") or {}
            if metadata.get("awaiting_image_confirmation"):
                stuck_conversations.add(msg["conversation_id"])

        avg_turns = 0
        useable_convos = []
        try:
            useable_result = await asyncio.to_thread(
                lambda: supabase.table("conversations")
                .select("turns_to_useable_output")
                .not_.is_("turns_to_useable_output", "null")
                .gte("updated_at", seven_days_ago)
                .limit(100)
                .execute()
            )
            useable_convos = useable_result.data or []
            total_turns = sum(c.get("turns_to_useable_output", 0) for c in useable_convos)
            avg_turns = round(total_turns / len(useable_convos), 1) if useable_convos else 0
        except Exception as e:
            logger.warning(f"turns_to_useable_output query failed: {str(e)}")

        response_status = (
            "healthy" if avg_response_length <= 500 else ("warning" if avg_response_length <= 800 else "critical")
        )
        stuck_status = (
            "healthy" if len(stuck_conversations) == 0 else ("warning" if len(stuck_conversations) <= 2 else "critical")
        )

        logger.info(
            f"Interface health: {avg_response_length} avg words, "
            f"{len(stuck_conversations)} stuck, {total_conversations_7d} chats, "
            f"{active_users_count} active users"
        )

        return {
            "success": True,
            "response_metrics": {
                "avg_word_count": avg_response_length,
                "total_responses": response_count,
                "target": 500,
                "status": response_status,
            },
            "activity_metrics": {
                "conversations_7d": total_conversations_7d,
                "active_users_7d": active_users_count,
            },
            "workflow_metrics": {
                "avg_turns_to_useable": avg_turns,
                "conversations_tracked": len(useable_convos),
                "stuck_conversations": len(stuck_conversations),
                "stuck_status": stuck_status,
            },
            "period": "7d",
        }
    except Exception as e:
        logger.error(f"Interface health error: {str(e)}")
        return {
            "success": False,
            "error": "Database temporarily unavailable",
            "response_metrics": {
                "avg_word_count": 0,
                "total_responses": 0,
                "target": 500,
                "status": "unknown",
            },
            "activity_metrics": {"conversations_7d": 0, "active_users_7d": 0},
            "workflow_metrics": {
                "avg_turns_to_useable": 0,
                "conversations_tracked": 0,
                "stuck_conversations": 0,
                "stuck_status": "unknown",
            },
            "period": "7d",
        }


@router.get("/analytics/keyword-trends")
async def get_keyword_trends(
    current_user: dict = Depends(require_admin),
    days: int = 30,
):
    """Analyze keyword trends from user messages.

    Returns top keywords, questions asked, and suggested FAQs.

    Args:
        current_user: Injected by FastAPI dependency.
        days: Number of days to analyze.
    """
    try:
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        messages_result = await asyncio.to_thread(
            lambda: supabase.table("messages")
            .select("content, created_at")
            .eq("role", "user")
            .gte("created_at", start_date.isoformat())
            .lte("created_at", end_date.isoformat())
            .execute()
        )

        messages = messages_result.data if messages_result.data else []

        # Domain keywords and categories
        domain_keywords = {
            "strategy",
            "roadmap",
            "initiative",
            "transformation",
            "adoption",
            "roi",
            "business case",
            "value",
            "impact",
            "metrics",
            "kpi",
            "genai",
            "llm",
            "rag",
            "embeddings",
            "fine-tuning",
            "prompt",
            "model",
            "inference",
            "agent",
            "chatbot",
            "copilot",
            "automation",
            "governance",
            "compliance",
            "security",
            "privacy",
            "policy",
            "risk",
            "audit",
            "regulation",
            "shadow ai",
            "stakeholder",
            "sponsor",
            "champion",
            "executive",
            "c-suite",
            "alignment",
            "pilot",
            "poc",
            "mvp",
            "prototype",
            "integration",
            "vendor",
            "research",
            "benchmark",
            "best practice",
            "use case",
            "innovation",
            "emerging",
        }

        keyword_categories = {
            "strategy": "Strategy",
            "roadmap": "Strategy",
            "initiative": "Strategy",
            "transformation": "Strategy",
            "adoption": "Strategy",
            "roi": "Business Value",
            "business case": "Business Value",
            "value": "Business Value",
            "impact": "Business Value",
            "metrics": "Business Value",
            "kpi": "Business Value",
            "genai": "AI Technology",
            "llm": "AI Technology",
            "rag": "AI Technology",
            "embeddings": "AI Technology",
            "fine-tuning": "AI Technology",
            "prompt": "AI Technology",
            "model": "AI Technology",
            "inference": "AI Technology",
            "agent": "AI Technology",
            "chatbot": "AI Technology",
            "copilot": "AI Technology",
            "automation": "AI Technology",
            "governance": "Governance",
            "compliance": "Governance",
            "security": "Governance",
            "privacy": "Governance",
            "policy": "Governance",
            "risk": "Governance",
            "audit": "Governance",
            "regulation": "Governance",
            "shadow ai": "Governance",
            "stakeholder": "Stakeholders",
            "sponsor": "Stakeholders",
            "champion": "Stakeholders",
            "executive": "Stakeholders",
            "c-suite": "Stakeholders",
            "alignment": "Stakeholders",
            "pilot": "Implementation",
            "poc": "Implementation",
            "mvp": "Implementation",
            "prototype": "Implementation",
            "integration": "Implementation",
            "vendor": "Implementation",
            "research": "Research",
            "benchmark": "Research",
            "best practice": "Research",
            "use case": "Research",
            "innovation": "Research",
            "emerging": "Research",
        }

        # Process messages
        questions = []
        all_words = []

        for msg in messages:
            content = msg.get("content", "").lower()

            if content.strip().endswith("?"):
                questions.append(
                    {
                        "text": msg.get("content", "").strip()[:200],
                        "timestamp": msg.get("created_at"),
                    }
                )

            words = re.findall(r"\b[a-zA-Z]{3,}\b", content)
            all_words.extend(words)

        word_counts = Counter(all_words)

        stop_words = {
            "the",
            "and",
            "for",
            "are",
            "but",
            "not",
            "you",
            "all",
            "can",
            "had",
            "her",
            "was",
            "one",
            "our",
            "out",
            "has",
            "have",
            "been",
            "were",
            "will",
            "this",
            "that",
            "with",
            "from",
            "they",
            "what",
            "which",
            "when",
            "would",
            "there",
            "their",
            "about",
            "could",
            "other",
            "into",
            "some",
            "than",
            "then",
            "these",
            "only",
            "just",
            "also",
            "more",
            "after",
            "before",
            "should",
            "how",
            "like",
            "help",
            "want",
            "need",
            "please",
            "thanks",
            "thank",
        }

        keywords = []
        for word, count in word_counts.most_common(100):
            if word not in stop_words and len(word) > 2:
                is_domain = word in domain_keywords
                category = keyword_categories.get(word, "General")
                keywords.append(
                    {
                        "word": word,
                        "count": count,
                        "is_domain_keyword": is_domain,
                        "category": category,
                    }
                )

        keywords.sort(key=lambda x: (not x["is_domain_keyword"], -x["count"]))
        keywords = keywords[:30]

        # Generate FAQ suggestions
        question_texts = [q["text"].lower() for q in questions]
        question_themes = Counter()

        for q in question_texts:
            if "how" in q:
                question_themes["how-to guides"] += 1
            if "what" in q:
                question_themes["definitions/concepts"] += 1
            if "why" in q:
                question_themes["rationale/reasoning"] += 1
            if any(word in q for word in ["example", "sample", "template"]):
                question_themes["examples/templates"] += 1
            if any(word in q for word in ["best", "practice", "recommend"]):
                question_themes["best practices"] += 1

        suggested_faqs = []
        suggestion_map = {
            "how-to guides": "Create step-by-step how-to guides",
            "definitions/concepts": "Add a glossary or concept definitions",
            "rationale/reasoning": "Document decision rationale and reasoning",
            "examples/templates": "Provide more examples and templates",
            "best practices": "Compile best practices documentation",
        }
        for theme, count in question_themes.most_common(5):
            if count >= 2:
                suggested_faqs.append(
                    {
                        "topic": theme,
                        "count": count,
                        "suggestion": suggestion_map.get(theme, f"Create resources for {theme}"),
                    }
                )

        domain_keyword_count = sum(1 for k in keywords if k["is_domain_keyword"])
        date_range = f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"

        logger.info(
            f"Keyword trends: {len(keywords)} keywords, {len(questions)} questions, {domain_keyword_count} domain terms"
        )

        return {
            "keywords": keywords,
            "questions": questions[:20],
            "message_count": len(messages),
            "date_range": date_range,
            "domain_keyword_count": domain_keyword_count,
            "suggested_faqs": suggested_faqs,
        }

    except Exception as e:
        logger.error(f"Keyword trends error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e
