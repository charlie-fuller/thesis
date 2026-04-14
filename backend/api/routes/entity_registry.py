"""Entity Registry API endpoints.

Manage organizations and person names for validation.

Version: 1.0.0
Created: 2026-01-23
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

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


def _get_manager() -> EntityRegistryManager:
    """Get EntityRegistryManager instance.

    TODO: EntityRegistryManager still takes supabase -- needs service-level migration.
    """
    return EntityRegistryManager(None)


# =============================================================================
# Organization Endpoints
# =============================================================================


@router.get("/organizations")
async def list_organizations(limit: int = 100, offset: int = 0):
    """List organizations in the registry."""
    manager = _get_manager()
    entries = await manager.list_organizations(None, limit, offset)

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
async def create_organization(request: CreateOrganizationRequest):
    """Add an organization to the registry."""
    manager = _get_manager()
    entry_id = await manager.add_organization(
        client_id=None,
        canonical_name=request.canonical_name,
        aliases=request.aliases,
        domain=request.domain,
        industry=request.industry,
        notes=request.notes,
    )

    if not entry_id:
        raise HTTPException(status_code=409, detail=f"Organization '{request.canonical_name}' already exists")

    return {"id": entry_id, "canonical_name": request.canonical_name}


@router.get("/organizations/{org_id}")
async def get_organization(org_id: str):
    """Get a specific organization."""
    manager = _get_manager()
    entry = await manager.get_organization(None, org_id=org_id)

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
async def add_organization_alias(org_id: str, request: AddAliasRequest):
    """Add an alias to an organization."""
    manager = _get_manager()

    # Verify organization exists
    entry = await manager.get_organization(None, org_id=org_id)
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
async def list_persons(limit: int = 100, offset: int = 0):
    """List persons in the registry."""
    manager = _get_manager()
    entries = await manager.list_persons(None, limit, offset)

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
async def create_person(request: CreatePersonRequest):
    """Add a person to the registry."""
    manager = _get_manager()
    entry_id = await manager.add_person(
        client_id=None,
        canonical_name=request.canonical_name,
        aliases=request.aliases,
        stakeholder_id=request.stakeholder_id,
        notes=request.notes,
    )

    if not entry_id:
        raise HTTPException(status_code=409, detail=f"Person '{request.canonical_name}' already exists")

    return {"id": entry_id, "canonical_name": request.canonical_name}


@router.get("/persons/{person_id}")
async def get_person(person_id: str):
    """Get a specific person."""
    manager = _get_manager()
    entry = await manager.get_person(None, person_id=person_id)

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
async def add_person_alias(person_id: str, request: AddAliasRequest):
    """Add an alias to a person."""
    manager = _get_manager()

    # Verify person exists
    entry = await manager.get_person(None, person_id=person_id)
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
async def bootstrap_registry():
    """Populate registries from existing stakeholder data.

    Creates person entries for all stakeholders and organization entries
    for unique organizations.
    """
    manager = _get_manager()
    stats = await manager.bootstrap_from_stakeholders(None)

    return BootstrapResponse(**stats)
