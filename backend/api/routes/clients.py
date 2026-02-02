"""Client management routes.

Handles listing and retrieving client information.
"""

import asyncio

from fastapi import APIRouter, Depends, HTTPException

from auth import check_client_member_or_admin, get_current_user, require_admin
from database import get_supabase
from logger_config import get_logger
from validation import validate_uuid

logger = get_logger(__name__)
router = APIRouter(prefix="/api/clients", tags=["clients"])
supabase = get_supabase()


@router.get("")
async def list_clients(
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(require_admin),
):
    """Get all clients with pagination.

    Requires: admin role

    Args:
        limit: Maximum number of clients to return (default 50, max 200)
        offset: Number of clients to skip (for pagination)

    Returns:
        List of clients with basic stats
    """
    try:
        # Clamp limit to prevent abuse
        limit = min(limit, 200)

        logger.info(f"\n🏢 Loading clients (limit={limit}, offset={offset})")

        # Fetch clients with pagination
        clients_result = await asyncio.to_thread(
            lambda: supabase.table("clients")
            .select("*", count="exact")
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )

        clients = clients_result.data
        total_count = clients_result.count or 0

        if not clients:
            return {
                "success": True,
                "clients": [],
                "count": 0,
                "total": total_count,
                "limit": limit,
                "offset": offset,
            }

        # Batch fetch stats for all clients (avoids N+1 queries)
        client_ids = [c["id"] for c in clients]

        # Get conversation counts grouped by client_id
        conv_result = await asyncio.to_thread(
            lambda: supabase.table("conversations")
            .select("client_id")
            .in_("client_id", client_ids)
            .execute()
        )
        conv_counts = {}
        for row in conv_result.data or []:
            cid = row["client_id"]
            conv_counts[cid] = conv_counts.get(cid, 0) + 1

        # Get document counts grouped by client_id
        docs_result = await asyncio.to_thread(
            lambda: supabase.table("documents")
            .select("client_id")
            .in_("client_id", client_ids)
            .execute()
        )
        docs_counts = {}
        for row in docs_result.data or []:
            cid = row["client_id"]
            docs_counts[cid] = docs_counts.get(cid, 0) + 1

        # Get user counts grouped by client_id
        users_result = await asyncio.to_thread(
            lambda: supabase.table("users")
            .select("client_id")
            .in_("client_id", client_ids)
            .execute()
        )
        users_counts = {}
        for row in users_result.data or []:
            cid = row["client_id"]
            users_counts[cid] = users_counts.get(cid, 0) + 1

        # Enrich clients with stats
        enriched_clients = [
            {
                **client,
                "conversation_count": conv_counts.get(client["id"], 0),
                "document_count": docs_counts.get(client["id"], 0),
                "user_count": users_counts.get(client["id"], 0),
            }
            for client in clients
        ]

        logger.info(f"   ✅ Loaded {len(enriched_clients)} clients (total: {total_count})")

        return {
            "success": True,
            "clients": enriched_clients,
            "count": len(enriched_clients),
            "total": total_count,
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        logger.error(f"❌ Error loading clients: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/{client_id}")
async def get_client(client_id: str, current_user: dict = Depends(get_current_user)):
    """Get a single client by ID.

    Args:
        client_id: UUID of the client
        current_user: Authenticated user from JWT token

    Returns:
        Client details with stats
    """
    try:
        # Validate UUID
        validate_uuid(client_id, "client_id")

        logger.info(f"\n🏢 Loading client: {client_id}")

        # Verify user has access to this client (unless admin)
        check_client_member_or_admin(current_user, client_id, "client")

        # Fetch client from database
        client_result = await asyncio.to_thread(
            lambda: supabase.table("clients").select("*").eq("id", client_id).single().execute()
        )

        if not client_result.data:
            raise HTTPException(status_code=404, detail="Client not found")

        client = client_result.data

        # Count conversations
        conv_result = await asyncio.to_thread(
            lambda: supabase.table("conversations")
            .select("id", count="exact")
            .eq("client_id", client_id)
            .execute()
        )

        # Count documents
        docs_result = await asyncio.to_thread(
            lambda: supabase.table("documents")
            .select("id", count="exact")
            .eq("client_id", client_id)
            .execute()
        )

        # Count users
        users_result = await asyncio.to_thread(
            lambda: supabase.table("users")
            .select("id", count="exact")
            .eq("client_id", client_id)
            .execute()
        )

        enriched_client = {
            **client,
            "conversation_count": conv_result.count or 0,
            "document_count": docs_result.count or 0,
            "user_count": users_result.count or 0,
        }

        logger.info(f"   ✅ Loaded client: {client.get('name', 'Unknown')}")

        return {"success": True, "client": enriched_client}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error loading client: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e
