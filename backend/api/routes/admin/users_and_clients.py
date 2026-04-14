"""Admin users and clients routes -- STUB (single-tenant mode).

Users and clients no longer exist as separate entities in PocketBase.
All endpoints return 410 Gone.
"""

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/users")
async def get_all_users():
    raise HTTPException(status_code=410, detail="Not available in single-tenant mode")


@router.get("/clients")
async def get_all_clients():
    raise HTTPException(status_code=410, detail="Not available in single-tenant mode")


@router.get("/conversations")
async def get_all_conversations():
    raise HTTPException(status_code=410, detail="Not available in single-tenant mode")


@router.get("/conversations/export")
async def export_conversations():
    raise HTTPException(status_code=410, detail="Not available in single-tenant mode")
