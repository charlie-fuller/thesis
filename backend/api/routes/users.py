"""User management routes -- STUB (single-tenant mode).

Users no longer exist as separate entities in PocketBase.
All endpoints return 410 Gone.
"""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("")
async def list_users():
    raise HTTPException(status_code=410, detail="Not available in single-tenant mode")


@router.post("")
async def create_user():
    raise HTTPException(status_code=410, detail="Not available in single-tenant mode")


@router.put("/{user_id}")
async def update_user(user_id: str):
    raise HTTPException(status_code=410, detail="Not available in single-tenant mode")


@router.post("/{user_id}/avatar")
async def upload_avatar(user_id: str):
    raise HTTPException(status_code=410, detail="Not available in single-tenant mode")


@router.delete("/{user_id}/avatar")
async def delete_avatar(user_id: str):
    raise HTTPException(status_code=410, detail="Not available in single-tenant mode")


@router.post("/{user_id}/resend-invitation")
async def resend_invitation(user_id: str):
    raise HTTPException(status_code=410, detail="Not available in single-tenant mode")


@router.get("/me/documents")
async def list_user_documents():
    raise HTTPException(status_code=410, detail="Not available in single-tenant mode")


@router.get("/me/storage")
async def get_storage_info():
    raise HTTPException(status_code=410, detail="Not available in single-tenant mode")


@router.get("/me/documents/list")
async def list_user_documents_paginated():
    raise HTTPException(status_code=410, detail="Not available in single-tenant mode")


@router.get("/me/documents/counts")
async def get_user_document_counts():
    raise HTTPException(status_code=410, detail="Not available in single-tenant mode")
