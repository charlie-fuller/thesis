"""Entity Registry API endpoints.
Manage organizations and person names for validation.

Version: 1.0.0
Created: 2026-01-23
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import get_current_user
from database import get_supabase
from services.entity_registry_manager import EntityRegistryManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/entity-registry", tags=["Entity Registry"])


# =============================================================================
# Request/Response Models
# =============================================================================


class CreateOrganizationRequest(BaseModel):
    canonical_name: str
    aliases: Optional[list[str]] = None
    domain: Optional[str] = None
    industry: Optional[str] = None
    notes: Optional[str] = None


class UpdateOrganizationRequest(BaseModel):
    aliases: Optional[list[str]] = None
    domain: Optional[str] = None
    industry: Optional[str] = None
    notes: Optional[str] = None


class CreatePersonRequest(BaseModel):
    canonical_name: str
    aliases: Optional[list[str]] = None
    stakeholder_id: Optional[str] = None
    notes: Optional[str] = None


class AddAliasRequest(BaseModel):
    alias: str


class BootstrapResponse(BaseModel):
    persons_created: int
    persons_skipped: int
    organizations_created: int
    organizations_skipped: int


# =============================================================================
# Organization Endpoints
# =============================================================================


@router.get("/organizations")
async def list_organizations(
    limit: int = 100,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """List organizations in the registry."""
    client_id = current_user.get("client_id")
    if not client_id:
        raise HTTPException(status_code=400, detail="Client ID required")

    manager = EntityRegistryManager(supabase)
    entries = await manager.list_organizations(client_id, limit, offset)

    return {
        "organizations": [
            {
                "id": e.id,
                "canonical_name": e.canonical_name,
                "aliases": e.aliases,
                "domain": e.domain,
                "industry": e.industry,
                "notes": e.notes,
                "created_at": e.created_at.isoformat() if e.created_at else None,
                "updated_at": e.updated_at.isoformat() if e.updated_at else None,
            }
            for e in entries
        ],
        "count": len(entries),
    }


@router.post("/organizations")
async def create_organization(
    request: CreateOrganizationRequest,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Add an organization to the registry."""
    client_id = current_user.get("client_id")
    if not client_id:
        raise HTTPException(status_code=400, detail="Client ID required")

    manager = EntityRegistryManager(supabase)
    entry_id = await manager.add_organization(
        client_id=client_id,
        canonical_name=request.canonical_name,
        aliases=request.aliases,
        domain=request.domain,
        industry=request.industry,
        notes=request.notes,
    )

    if not entry_id:
        raise HTTPException(
            status_code=409, detail=f"Organization '{request.canonical_name}' already exists"
        )

    return {"id": entry_id, "canonical_name": request.canonical_name}


@router.get("/organizations/{org_id}")
async def get_organization(
    org_id: str, current_user: dict = Depends(get_current_user), supabase=Depends(get_supabase)
):
    """Get a specific organization."""
    client_id = current_user.get("client_id")
    if not client_id:
        raise HTTPException(status_code=400, detail="Client ID required")

    manager = EntityRegistryManager(supabase)
    entry = await manager.get_organization(client_id, org_id=org_id)

    if not entry:
        raise HTTPException(status_code=404, detail="Organization not found")

    return {
        "id": entry.id,
        "canonical_name": entry.canonical_name,
        "aliases": entry.aliases,
        "domain": entry.domain,
        "industry": entry.industry,
        "notes": entry.notes,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
        "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
    }


@router.post("/organizations/{org_id}/aliases")
async def add_organization_alias(
    org_id: str,
    request: AddAliasRequest,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Add an alias to an organization."""
    client_id = current_user.get("client_id")
    if not client_id:
        raise HTTPException(status_code=400, detail="Client ID required")

    manager = EntityRegistryManager(supabase)

    # Verify organization exists
    entry = await manager.get_organization(client_id, org_id=org_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Organization not found")

    success = await manager.add_organization_alias(org_id, request.alias)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to add alias")

    return {"success": True, "alias": request.alias}


# =============================================================================
# Person Endpoints
# =============================================================================


@router.get("/persons")
async def list_persons(
    limit: int = 100,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """List persons in the registry."""
    client_id = current_user.get("client_id")
    if not client_id:
        raise HTTPException(status_code=400, detail="Client ID required")

    manager = EntityRegistryManager(supabase)
    entries = await manager.list_persons(client_id, limit, offset)

    return {
        "persons": [
            {
                "id": e.id,
                "canonical_name": e.canonical_name,
                "first_name": e.first_name,
                "last_name": e.last_name,
                "aliases": e.aliases,
                "stakeholder_id": e.stakeholder_id,
                "notes": e.notes,
                "created_at": e.created_at.isoformat() if e.created_at else None,
                "updated_at": e.updated_at.isoformat() if e.updated_at else None,
            }
            for e in entries
        ],
        "count": len(entries),
    }


@router.post("/persons")
async def create_person(
    request: CreatePersonRequest,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Add a person to the registry."""
    client_id = current_user.get("client_id")
    if not client_id:
        raise HTTPException(status_code=400, detail="Client ID required")

    manager = EntityRegistryManager(supabase)
    entry_id = await manager.add_person(
        client_id=client_id,
        canonical_name=request.canonical_name,
        aliases=request.aliases,
        stakeholder_id=request.stakeholder_id,
        notes=request.notes,
    )

    if not entry_id:
        raise HTTPException(
            status_code=409, detail=f"Person '{request.canonical_name}' already exists"
        )

    return {"id": entry_id, "canonical_name": request.canonical_name}


@router.get("/persons/{person_id}")
async def get_person(
    person_id: str, current_user: dict = Depends(get_current_user), supabase=Depends(get_supabase)
):
    """Get a specific person."""
    client_id = current_user.get("client_id")
    if not client_id:
        raise HTTPException(status_code=400, detail="Client ID required")

    manager = EntityRegistryManager(supabase)
    entry = await manager.get_person(client_id, person_id=person_id)

    if not entry:
        raise HTTPException(status_code=404, detail="Person not found")

    return {
        "id": entry.id,
        "canonical_name": entry.canonical_name,
        "first_name": entry.first_name,
        "last_name": entry.last_name,
        "aliases": entry.aliases,
        "stakeholder_id": entry.stakeholder_id,
        "notes": entry.notes,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
        "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
    }


@router.post("/persons/{person_id}/aliases")
async def add_person_alias(
    person_id: str,
    request: AddAliasRequest,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Add an alias to a person."""
    client_id = current_user.get("client_id")
    if not client_id:
        raise HTTPException(status_code=400, detail="Client ID required")

    manager = EntityRegistryManager(supabase)

    # Verify person exists
    entry = await manager.get_person(client_id, person_id=person_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Person not found")

    success = await manager.add_person_alias(person_id, request.alias)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to add alias")

    return {"success": True, "alias": request.alias}


# =============================================================================
# Bootstrap Endpoint
# =============================================================================


@router.post("/bootstrap", response_model=BootstrapResponse)
async def bootstrap_registry(
    current_user: dict = Depends(get_current_user), supabase=Depends(get_supabase)
):
    """Populate registries from existing stakeholder data.

    Creates person entries for all stakeholders and organization entries
    for unique organizations.
    """
    client_id = current_user.get("client_id")
    if not client_id:
        raise HTTPException(status_code=400, detail="Client ID required")

    manager = EntityRegistryManager(supabase)
    stats = await manager.bootstrap_from_stakeholders(client_id)

    return BootstrapResponse(**stats)
