"""Admin users and clients routes - user/client management and exports."""

import asyncio
import io
import json
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from auth import require_admin
from logger_config import get_logger

from ._shared import supabase

logger = get_logger(__name__)
router = APIRouter()


@router.get("/users")
async def get_all_users(current_user: dict = Depends(require_admin)):
    """Get all users for admin (for KPI user selector).

    Args:
        current_user: Injected by FastAPI dependency.
    """
    try:
        result = await asyncio.to_thread(
            lambda: supabase.table("users").select("id, email, name").order("email").execute()
        )

        logger.info(f"Retrieved {len(result.data)} users for selector")

        return {"success": True, "users": result.data}
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/clients")
async def get_all_clients(current_user: dict = Depends(require_admin)):
    """Get all clients for admin.

    Args:
        current_user: Injected by FastAPI dependency.
    """
    try:
        result = await asyncio.to_thread(
            lambda: supabase.table("clients").select("id, name").order("name").execute()
        )

        logger.info(f"Retrieved {len(result.data)} clients")

        return {"success": True, "clients": result.data}
    except Exception as e:
        logger.error(f"Error fetching clients: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/conversations")
async def get_all_conversations(
    current_user: dict = Depends(require_admin),
    limit: int = 100,
    client_id: str = None,
):
    """Get all conversations with user and client info for admin.

    Args:
        current_user: Injected by FastAPI dependency.
        limit: Maximum conversations to return.
        client_id: Optional filter by client.
    """
    try:
        query = supabase.table("conversations").select("""
                *,
                users:user_id(name, email),
                clients:client_id(name)
            """)

        if client_id:
            query = query.eq("client_id", client_id)

        result = await asyncio.to_thread(
            lambda: query.order("updated_at", desc=True).limit(limit).execute()
        )

        conversations_with_counts = []
        for conv in result.data:
            msg_count_result = await asyncio.to_thread(
                lambda c=conv: supabase.table("messages")
                .select("id", count="exact")
                .eq("conversation_id", c["id"])
                .execute()
            )

            conv["message_count"] = msg_count_result.count or 0
            conversations_with_counts.append(conv)

        logger.info(f"Retrieved {len(conversations_with_counts)} conversations")

        return {"success": True, "conversations": conversations_with_counts}
    except Exception as e:
        logger.error(f"Error fetching conversations: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/conversations/export")
async def export_conversations(
    current_user: dict = Depends(require_admin),
    start_date: str = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(None, description="End date (YYYY-MM-DD)"),
    format: str = Query("json", description="Export format: json or txt"),
):
    """Export all conversations with messages.

    Optional date filters to limit the export range.
    Returns a downloadable file with all conversation data.

    Args:
        current_user: Injected by FastAPI dependency.
        start_date: Optional start date filter.
        end_date: Optional end date filter.
        format: Export format (json or txt).
    """
    try:
        query = supabase.table("conversations").select("""
            *,
            users:user_id(id, name, email),
            clients:client_id(id, name)
        """)

        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.gte("created_at", start_dt.isoformat())
            except ValueError:
                raise HTTPException(
                    status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD"
                ) from None

        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                end_dt = end_dt + timedelta(days=1)
                query = query.lt("created_at", end_dt.isoformat())
            except ValueError:
                raise HTTPException(
                    status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD"
                ) from None

        result = await asyncio.to_thread(lambda: query.order("created_at", desc=True).execute())

        conversations = result.data or []
        logger.info(f"Exporting {len(conversations)} conversations")

        export_data = []
        for conv in conversations:
            messages_result = await asyncio.to_thread(
                lambda c=conv: supabase.table("messages")
                .select("id, role, content, timestamp, metadata")
                .eq("conversation_id", c["id"])
                .order("timestamp")
                .execute()
            )

            messages = messages_result.data or []

            export_data.append(
                {
                    "conversation_id": conv["id"],
                    "title": conv.get("title", "Untitled"),
                    "created_at": conv.get("created_at"),
                    "updated_at": conv.get("updated_at"),
                    "user": {
                        "id": conv.get("users", {}).get("id") if conv.get("users") else None,
                        "name": conv.get("users", {}).get("name")
                        if conv.get("users")
                        else "Unknown",
                        "email": conv.get("users", {}).get("email") if conv.get("users") else None,
                    },
                    "client": {
                        "id": conv.get("clients", {}).get("id") if conv.get("clients") else None,
                        "name": conv.get("clients", {}).get("name")
                        if conv.get("clients")
                        else "Unknown",
                    },
                    "message_count": len(messages),
                    "messages": [
                        {
                            "id": msg["id"],
                            "role": msg["role"],
                            "content": msg["content"],
                            "timestamp": msg["timestamp"],
                        }
                        for msg in messages
                    ],
                }
            )

        date_suffix = ""
        if start_date or end_date:
            date_suffix = f"_{start_date or 'start'}_to_{end_date or 'now'}"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format == "txt":
            text_output = []
            text_output.append("=" * 80)
            text_output.append("CONVERSATION HISTORY EXPORT")
            text_output.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            if start_date:
                text_output.append(f"From: {start_date}")
            if end_date:
                text_output.append(f"To: {end_date}")
            text_output.append(f"Total Conversations: {len(export_data)}")
            text_output.append("=" * 80)
            text_output.append("")

            for conv in export_data:
                text_output.append("-" * 80)
                text_output.append(f"Conversation: {conv['title']}")
                text_output.append(f"ID: {conv['conversation_id']}")
                text_output.append(f"User: {conv['user']['name']} ({conv['user']['email']})")
                text_output.append(f"Client: {conv['client']['name']}")
                text_output.append(f"Created: {conv['created_at']}")
                text_output.append(f"Messages: {conv['message_count']}")
                text_output.append("-" * 80)
                text_output.append("")

                for msg in conv["messages"]:
                    role_label = "USER" if msg["role"] == "user" else "ASSISTANT"
                    text_output.append(f"[{msg['timestamp']}] {role_label}:")
                    text_output.append(msg["content"])
                    text_output.append("")

                text_output.append("")

            content = "\n".join(text_output)
            filename = f"conversation_export{date_suffix}_{timestamp}.txt"

            return StreamingResponse(
                io.BytesIO(content.encode("utf-8")),
                media_type="text/plain",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )
        else:
            export_json = {
                "export_info": {
                    "generated_at": datetime.now().isoformat(),
                    "start_date": start_date,
                    "end_date": end_date,
                    "total_conversations": len(export_data),
                    "total_messages": sum(c["message_count"] for c in export_data),
                },
                "conversations": export_data,
            }

            content = json.dumps(export_json, indent=2, default=str)
            filename = f"conversation_export{date_suffix}_{timestamp}.json"

            return StreamingResponse(
                io.BytesIO(content.encode("utf-8")),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export conversations error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e
