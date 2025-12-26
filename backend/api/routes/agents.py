"""
Agent Management API Routes

Provides full CRUD and management for Thesis agents:
- List all agents
- Get agent details with instructions and KB docs
- Update agent instructions (with versioning)
- Manage agent knowledge base document links
- Agent configuration and status
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from database import get_supabase
from supabase import Client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agents", tags=["agents"])


# ============================================================================
# Pydantic Models
# ============================================================================

class AgentBase(BaseModel):
    """Base agent fields."""
    name: str
    display_name: str
    description: Optional[str] = None
    is_active: bool = True
    config: dict = Field(default_factory=dict)


class AgentCreate(AgentBase):
    """Create a new agent."""
    system_instruction: Optional[str] = None


class AgentUpdate(BaseModel):
    """Update agent fields."""
    display_name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    config: Optional[dict] = None


class AgentInstructionUpdate(BaseModel):
    """Update agent system instruction (creates new version)."""
    instructions: str
    description: Optional[str] = None  # Description of changes


class AgentInstructionVersionActivate(BaseModel):
    """Activate a specific instruction version."""
    version_id: str


class AgentKBDocLink(BaseModel):
    """Link a document to an agent's knowledge base."""
    document_id: str
    notes: Optional[str] = None
    priority: int = 0


class AgentKBDocUpdate(BaseModel):
    """Update a KB document link."""
    notes: Optional[str] = None
    priority: Optional[int] = None


class AgentResponse(BaseModel):
    """Full agent response."""
    id: str
    name: str
    display_name: str
    description: Optional[str]
    system_instruction: Optional[str]
    is_active: bool
    config: dict
    created_at: str
    updated_at: str
    # Enriched data
    instruction_versions_count: int = 0
    kb_documents_count: int = 0
    conversations_count: int = 0


class AgentInstructionVersion(BaseModel):
    """Instruction version details."""
    id: str
    agent_id: str
    version_number: str
    instructions: str
    description: Optional[str]
    is_active: bool
    created_by: Optional[str]
    created_at: str
    activated_at: Optional[str]


# ============================================================================
# Agent CRUD Routes
# ============================================================================

@router.get("")
async def list_agents(
    include_inactive: bool = False,
    supabase: Client = Depends(get_supabase)
):
    """List all agents with summary stats."""
    try:
        query = supabase.table("agents").select("*")
        if not include_inactive:
            query = query.eq("is_active", True)

        result = query.order("name").execute()

        agents = []
        for agent in result.data:
            # Get instruction version count
            versions_result = supabase.table("agent_instruction_versions")\
                .select("id", count="exact")\
                .eq("agent_id", agent["id"])\
                .execute()

            # Get conversation count
            convs_result = supabase.table("conversations")\
                .select("id", count="exact")\
                .eq("agent_id", agent["id"])\
                .execute()

            # Get KB document count
            kb_result = supabase.table("agent_knowledge_base")\
                .select("id", count="exact")\
                .eq("agent_id", agent["id"])\
                .execute()

            agents.append({
                **agent,
                "instruction_versions_count": versions_result.count or 0,
                "kb_documents_count": kb_result.count or 0,
                "conversations_count": convs_result.count or 0,
            })

        return {"agents": agents}

    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}")
async def get_agent(
    agent_id: str,
    supabase: Client = Depends(get_supabase)
):
    """Get full agent details including current instructions."""
    try:
        result = supabase.table("agents")\
            .select("*")\
            .eq("id", agent_id)\
            .single()\
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Agent not found")

        agent = result.data

        # Get active instruction version
        active_version = supabase.table("agent_instruction_versions")\
            .select("*")\
            .eq("agent_id", agent_id)\
            .eq("is_active", True)\
            .single()\
            .execute()

        # Get all instruction versions
        all_versions = supabase.table("agent_instruction_versions")\
            .select("*")\
            .eq("agent_id", agent_id)\
            .order("created_at", desc=True)\
            .execute()

        # Get conversation count
        convs_result = supabase.table("conversations")\
            .select("id", count="exact")\
            .eq("agent_id", agent_id)\
            .execute()

        # Get linked KB documents
        kb_result = supabase.table("agent_knowledge_base")\
            .select("*, documents(*)")\
            .eq("agent_id", agent_id)\
            .order("priority", desc=True)\
            .execute()

        # Format KB documents
        kb_documents = []
        for link in kb_result.data or []:
            if link.get("documents"):
                kb_documents.append({
                    "link_id": link["id"],
                    "document": link["documents"],
                    "notes": link.get("notes"),
                    "priority": link.get("priority", 0),
                    "added_at": link.get("created_at"),
                })

        return {
            "agent": agent,
            "active_instruction_version": active_version.data if active_version.data else None,
            "instruction_versions": all_versions.data or [],
            "kb_documents": kb_documents,
            "stats": {
                "conversations_count": convs_result.count or 0,
                "instruction_versions_count": len(all_versions.data or []),
                "kb_documents_count": len(kb_documents),
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
async def create_agent(
    agent: AgentCreate,
    supabase: Client = Depends(get_supabase)
):
    """Create a new agent."""
    try:
        # Check if name already exists
        existing = supabase.table("agents")\
            .select("id")\
            .eq("name", agent.name)\
            .execute()

        if existing.data:
            raise HTTPException(status_code=400, detail=f"Agent '{agent.name}' already exists")

        result = supabase.table("agents").insert({
            "name": agent.name,
            "display_name": agent.display_name,
            "description": agent.description,
            "system_instruction": agent.system_instruction,
            "is_active": agent.is_active,
            "config": agent.config,
        }).execute()

        return {"agent": result.data[0]}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{agent_id}")
async def update_agent(
    agent_id: str,
    updates: AgentUpdate,
    supabase: Client = Depends(get_supabase)
):
    """Update agent metadata (not instructions - use instruction versioning for that)."""
    try:
        update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
        update_data["updated_at"] = datetime.utcnow().isoformat()

        result = supabase.table("agents")\
            .update(update_data)\
            .eq("id", agent_id)\
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Agent not found")

        return {"agent": result.data[0]}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Instruction Version Routes
# ============================================================================

@router.get("/{agent_id}/instructions")
async def get_agent_instructions(
    agent_id: str,
    supabase: Client = Depends(get_supabase)
):
    """Get all instruction versions for an agent."""
    try:
        result = supabase.table("agent_instruction_versions")\
            .select("*")\
            .eq("agent_id", agent_id)\
            .order("created_at", desc=True)\
            .execute()

        return {"versions": result.data or []}

    except Exception as e:
        logger.error(f"Failed to get instructions for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/instructions")
async def create_instruction_version(
    agent_id: str,
    instruction: AgentInstructionUpdate,
    user_id: Optional[str] = None,  # TODO: Get from auth
    supabase: Client = Depends(get_supabase)
):
    """Create a new instruction version for an agent."""
    try:
        # Get current version count to generate version number
        existing = supabase.table("agent_instruction_versions")\
            .select("version_number")\
            .eq("agent_id", agent_id)\
            .order("created_at", desc=True)\
            .limit(1)\
            .execute()

        if existing.data:
            # Parse version and increment
            last_version = existing.data[0]["version_number"]
            try:
                major, minor = last_version.split(".")
                new_version = f"{major}.{int(minor) + 1}"
            except:
                new_version = "1.1"
        else:
            new_version = "1.0"

        # Create new version
        result = supabase.table("agent_instruction_versions").insert({
            "agent_id": agent_id,
            "version_number": new_version,
            "instructions": instruction.instructions,
            "description": instruction.description,
            "is_active": False,  # Don't auto-activate
            "created_by": user_id,
        }).execute()

        return {"version": result.data[0]}

    except Exception as e:
        logger.error(f"Failed to create instruction version for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/instructions/{version_id}/activate")
async def activate_instruction_version(
    agent_id: str,
    version_id: str,
    supabase: Client = Depends(get_supabase)
):
    """Activate a specific instruction version (deactivates others)."""
    try:
        # Deactivate all versions for this agent
        supabase.table("agent_instruction_versions")\
            .update({"is_active": False})\
            .eq("agent_id", agent_id)\
            .execute()

        # Activate the specified version
        result = supabase.table("agent_instruction_versions")\
            .update({
                "is_active": True,
                "activated_at": datetime.utcnow().isoformat()
            })\
            .eq("id", version_id)\
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Version not found")

        # Also update the agent's system_instruction field
        supabase.table("agents")\
            .update({
                "system_instruction": result.data[0]["instructions"],
                "updated_at": datetime.utcnow().isoformat()
            })\
            .eq("id", agent_id)\
            .execute()

        return {"version": result.data[0], "message": "Version activated"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to activate version {version_id} for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/instructions/compare")
async def compare_instruction_versions(
    agent_id: str,
    v1: str,
    v2: str,
    supabase: Client = Depends(get_supabase)
):
    """Compare two instruction versions."""
    try:
        version1 = supabase.table("agent_instruction_versions")\
            .select("*")\
            .eq("id", v1)\
            .single()\
            .execute()

        version2 = supabase.table("agent_instruction_versions")\
            .select("*")\
            .eq("id", v2)\
            .single()\
            .execute()

        if not version1.data or not version2.data:
            raise HTTPException(status_code=404, detail="One or both versions not found")

        return {
            "version1": version1.data,
            "version2": version2.data,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to compare versions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Knowledge Base Document Routes
# ============================================================================

@router.get("/{agent_id}/documents")
async def get_agent_documents(
    agent_id: str,
    supabase: Client = Depends(get_supabase)
):
    """Get documents linked to an agent's knowledge base."""
    try:
        result = supabase.table("agent_knowledge_base")\
            .select("*, documents(*)")\
            .eq("agent_id", agent_id)\
            .order("priority", desc=True)\
            .execute()

        documents = []
        for link in result.data or []:
            if link.get("documents"):
                documents.append({
                    "link_id": link["id"],
                    "document": link["documents"],
                    "notes": link.get("notes"),
                    "priority": link.get("priority", 0),
                    "added_at": link.get("created_at"),
                })

        return {"documents": documents}

    except Exception as e:
        logger.error(f"Failed to get documents for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/documents")
async def link_document_to_agent(
    agent_id: str,
    doc_link: AgentKBDocLink,
    user_id: Optional[str] = None,  # TODO: Get from auth
    supabase: Client = Depends(get_supabase)
):
    """Link a document to an agent's knowledge base."""
    try:
        # Check if link already exists
        existing = supabase.table("agent_knowledge_base")\
            .select("id")\
            .eq("agent_id", agent_id)\
            .eq("document_id", doc_link.document_id)\
            .execute()

        if existing.data:
            raise HTTPException(status_code=400, detail="Document already linked to this agent")

        # Verify document exists
        doc_check = supabase.table("documents")\
            .select("id, filename")\
            .eq("id", doc_link.document_id)\
            .single()\
            .execute()

        if not doc_check.data:
            raise HTTPException(status_code=404, detail="Document not found")

        # Create link
        result = supabase.table("agent_knowledge_base").insert({
            "agent_id": agent_id,
            "document_id": doc_link.document_id,
            "notes": doc_link.notes,
            "priority": doc_link.priority,
            "added_by": user_id,
        }).execute()

        return {
            "link": result.data[0],
            "document": doc_check.data,
            "message": f"Document '{doc_check.data['filename']}' linked to agent"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to link document to agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{agent_id}/documents/{link_id}")
async def update_document_link(
    agent_id: str,
    link_id: str,
    updates: AgentKBDocUpdate,
    supabase: Client = Depends(get_supabase)
):
    """Update a KB document link (notes, priority)."""
    try:
        update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
        update_data["updated_at"] = datetime.utcnow().isoformat()

        result = supabase.table("agent_knowledge_base")\
            .update(update_data)\
            .eq("id", link_id)\
            .eq("agent_id", agent_id)\
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Link not found")

        return {"link": result.data[0]}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update document link {link_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{agent_id}/documents/{link_id}")
async def unlink_document_from_agent(
    agent_id: str,
    link_id: str,
    supabase: Client = Depends(get_supabase)
):
    """Remove a document from an agent's knowledge base."""
    try:
        result = supabase.table("agent_knowledge_base")\
            .delete()\
            .eq("id", link_id)\
            .eq("agent_id", agent_id)\
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Link not found")

        return {"message": "Document unlinked from agent", "deleted_link": result.data[0]}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to unlink document from agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/available")
async def get_available_documents(
    agent_id: Optional[str] = None,
    supabase: Client = Depends(get_supabase)
):
    """Get all documents available for linking. If agent_id provided, excludes already linked docs."""
    try:
        # Get all documents
        docs_result = supabase.table("documents")\
            .select("id, filename, content_type, file_size, uploaded_at")\
            .order("uploaded_at", desc=True)\
            .execute()

        documents = docs_result.data or []

        # If agent_id provided, filter out already linked documents
        if agent_id:
            linked = supabase.table("agent_knowledge_base")\
                .select("document_id")\
                .eq("agent_id", agent_id)\
                .execute()

            linked_ids = {link["document_id"] for link in linked.data or []}
            documents = [doc for doc in documents if doc["id"] not in linked_ids]

        return {"documents": documents}

    except Exception as e:
        logger.error(f"Failed to get available documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Agent Stats Routes
# ============================================================================

@router.get("/{agent_id}/stats")
async def get_agent_stats(
    agent_id: str,
    supabase: Client = Depends(get_supabase)
):
    """Get usage statistics for an agent."""
    try:
        # Conversation count
        convs = supabase.table("conversations")\
            .select("id, created_at", count="exact")\
            .eq("agent_id", agent_id)\
            .execute()

        # Recent conversations
        recent_convs = supabase.table("conversations")\
            .select("id, title, created_at")\
            .eq("agent_id", agent_id)\
            .order("created_at", desc=True)\
            .limit(5)\
            .execute()

        return {
            "total_conversations": convs.count or 0,
            "recent_conversations": recent_convs.data or [],
        }

    except Exception as e:
        logger.error(f"Failed to get stats for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
