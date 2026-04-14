"""Client management routes -- STUB (single-tenant mode).

Clients no longer exist as separate entities in PocketBase.
All endpoints return 410 Gone.
"""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/clients", tags=["clients"])


@router.get("")
async def list_clients():
    raise HTTPException(status_code=410, detail="Not available in single-tenant mode")


@router.get("/{client_id}")
async def get_client(client_id: str):
    raise HTTPException(status_code=410, detail="Not available in single-tenant mode")
