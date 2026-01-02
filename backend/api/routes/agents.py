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
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from database import get_supabase
from supabase import Client
from services.instruction_loader import (
    load_instruction_from_file,
    save_instruction_to_file,
    instruction_file_exists,
    list_available_instruction_files,
    get_instruction_file_mtime
)

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
    meeting_rooms_count: int = 0


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

            # Get meeting room participation count (count unique meetings where agent has messages)
            meetings_result = supabase.table("meeting_room_messages")\
                .select("meeting_room_id", count="exact")\
                .eq("agent_id", agent["id"])\
                .execute()

            # Count unique meeting rooms from messages
            unique_meetings = set()
            if meetings_result.data:
                for msg in meetings_result.data:
                    if msg.get("meeting_room_id"):
                        unique_meetings.add(msg["meeting_room_id"])

            agents.append({
                **agent,
                "instruction_versions_count": versions_result.count or 0,
                "kb_documents_count": kb_result.count or 0,
                "conversations_count": convs_result.count or 0,
                "meeting_rooms_count": len(unique_meetings),
            })

        return {"success": True, "agents": agents}

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
            .execute()

        if not result.data or len(result.data) == 0:
            raise HTTPException(status_code=404, detail="Agent not found")

        agent = result.data[0]

        # Get active instruction version (use limit(1) instead of single() to avoid error when no rows)
        active_version_result = supabase.table("agent_instruction_versions")\
            .select("*")\
            .eq("agent_id", agent_id)\
            .eq("is_active", True)\
            .limit(1)\
            .execute()

        active_version = active_version_result.data[0] if active_version_result.data else None

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
            "active_instruction_version": active_version,
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
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

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
            except (ValueError, IndexError):
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
    """
    Activate a specific instruction version (deactivates others).

    The agent_instruction_versions table is the SINGLE SOURCE OF TRUTH.
    Running agents will pick up changes on next initialization or via reload.
    """
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
                "activated_at": datetime.now(timezone.utc).isoformat()
            })\
            .eq("id", version_id)\
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Version not found")

        # Update agent's updated_at timestamp (but NOT copying system_instruction)
        # The agent_instruction_versions table is the single source of truth
        supabase.table("agents")\
            .update({
                "updated_at": datetime.now(timezone.utc).isoformat()
            })\
            .eq("id", agent_id)\
            .execute()

        return {
            "version": result.data[0],
            "message": "Version activated. Running agents will use this on next request.",
            "reload_required": True  # Signal to frontend that a reload may be needed
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to activate version {version_id} for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class VersionCompareRequest(BaseModel):
    """Request to compare two instruction versions."""
    version_a_id: str
    version_b_id: str


@router.get("/{agent_id}/instructions/{version_id}")
async def get_instruction_version(
    agent_id: str,
    version_id: str,
    supabase: Client = Depends(get_supabase)
):
    """Get a specific instruction version."""
    try:
        result = supabase.table("agent_instruction_versions")\
            .select("*")\
            .eq("id", version_id)\
            .eq("agent_id", agent_id)\
            .single()\
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Version not found")

        return {"success": True, "version": result.data}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get version {version_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{agent_id}/instructions/{version_id}")
async def delete_instruction_version(
    agent_id: str,
    version_id: str,
    supabase: Client = Depends(get_supabase)
):
    """Delete an instruction version (cannot delete active version)."""
    try:
        # Check if version is active
        version = supabase.table("agent_instruction_versions")\
            .select("is_active, version_number")\
            .eq("id", version_id)\
            .eq("agent_id", agent_id)\
            .single()\
            .execute()

        if not version.data:
            raise HTTPException(status_code=404, detail="Version not found")

        if version.data.get("is_active"):
            raise HTTPException(status_code=400, detail="Cannot delete active version")

        result = supabase.table("agent_instruction_versions")\
            .delete()\
            .eq("id", version_id)\
            .execute()

        return {
            "success": True,
            "message": f"Version {version.data['version_number']} deleted"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete version {version_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/instructions/compare")
async def compare_instruction_versions(
    agent_id: str,
    v1: str,
    v2: str,
    supabase: Client = Depends(get_supabase)
):
    """Compare two instruction versions (GET for simple comparison)."""
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


@router.post("/{agent_id}/instructions/compare")
async def compare_versions_detailed(
    agent_id: str,
    request: VersionCompareRequest,
    supabase: Client = Depends(get_supabase)
):
    """Compare two instruction versions with detailed diff."""
    import difflib

    try:
        version_a = supabase.table("agent_instruction_versions")\
            .select("*")\
            .eq("id", request.version_a_id)\
            .eq("agent_id", agent_id)\
            .single()\
            .execute()

        version_b = supabase.table("agent_instruction_versions")\
            .select("*")\
            .eq("id", request.version_b_id)\
            .eq("agent_id", agent_id)\
            .single()\
            .execute()

        if not version_a.data or not version_b.data:
            raise HTTPException(status_code=404, detail="One or both versions not found")

        # Generate unified diff
        content_a = version_a.data.get("instructions", "").splitlines(keepends=True)
        content_b = version_b.data.get("instructions", "").splitlines(keepends=True)

        diff = list(difflib.unified_diff(
            content_a,
            content_b,
            fromfile=f"v{version_a.data['version_number']}",
            tofile=f"v{version_b.data['version_number']}",
            lineterm=""
        ))

        # Calculate stats
        additions = sum(1 for line in diff if line.startswith('+') and not line.startswith('+++'))
        deletions = sum(1 for line in diff if line.startswith('-') and not line.startswith('---'))

        return {
            "success": True,
            "version_a": {
                "id": version_a.data["id"],
                "version_number": version_a.data["version_number"],
                "created_at": version_a.data["created_at"]
            },
            "version_b": {
                "id": version_b.data["id"],
                "version_number": version_b.data["version_number"],
                "created_at": version_b.data["created_at"]
            },
            "diff": diff,
            "stats": {
                "additions": additions,
                "deletions": deletions,
                "total_changes": additions + deletions
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to compare versions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/instructions/compare/summary")
async def generate_comparison_summary(
    agent_id: str,
    request: VersionCompareRequest,
    supabase: Client = Depends(get_supabase)
):
    """Generate an AI summary of changes between two instruction versions."""
    import difflib
    import anthropic
    import os

    try:
        version_a = supabase.table("agent_instruction_versions")\
            .select("*")\
            .eq("id", request.version_a_id)\
            .eq("agent_id", agent_id)\
            .single()\
            .execute()

        version_b = supabase.table("agent_instruction_versions")\
            .select("*")\
            .eq("id", request.version_b_id)\
            .eq("agent_id", agent_id)\
            .single()\
            .execute()

        if not version_a.data or not version_b.data:
            raise HTTPException(status_code=404, detail="One or both versions not found")

        # Get agent info for context
        agent = supabase.table("agents")\
            .select("name, display_name")\
            .eq("id", agent_id)\
            .single()\
            .execute()

        agent_name = agent.data.get("display_name", "Unknown Agent") if agent.data else "Unknown Agent"

        # Generate diff
        content_a = version_a.data.get("instructions", "").splitlines(keepends=True)
        content_b = version_b.data.get("instructions", "").splitlines(keepends=True)

        diff = list(difflib.unified_diff(
            content_a,
            content_b,
            fromfile=f"v{version_a.data['version_number']}",
            tofile=f"v{version_b.data['version_number']}",
            lineterm=""
        ))

        # Calculate stats
        additions = sum(1 for line in diff if line.startswith('+') and not line.startswith('+++'))
        deletions = sum(1 for line in diff if line.startswith('-') and not line.startswith('---'))

        # Generate AI summary using Claude
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        diff_text = "\n".join(diff[:500])  # Limit diff size for API

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": f"""Analyze this diff between two versions of system instructions for the "{agent_name}" agent and provide a concise summary of the key changes.

Focus on:
1. Major additions or new capabilities
2. Removed functionality or restrictions
3. Changes to persona, tone, or communication style
4. Updated examples or few-shot patterns
5. Modified instructions or workflows

Keep the summary actionable and highlight what administrators should be aware of.

Diff:
```
{diff_text}
```

Provide a clear, bulleted summary of the changes (3-7 bullet points)."""
                }
            ]
        )

        summary = message.content[0].text

        return {
            "success": True,
            "version_a": {
                "id": version_a.data["id"],
                "version_number": version_a.data["version_number"],
                "created_at": version_a.data["created_at"]
            },
            "version_b": {
                "id": version_b.data["id"],
                "version_number": version_b.data["version_number"],
                "created_at": version_b.data["created_at"]
            },
            "summary": summary,
            "stats": {
                "additions": additions,
                "deletions": deletions,
                "total_changes": additions + deletions
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate comparison summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Knowledge Base Document Routes
# ============================================================================

# IMPORTANT: Static routes must be defined BEFORE parameterized routes
# /documents/available must come before /{agent_id}/documents
# Otherwise FastAPI matches "documents" as an agent_id

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
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

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


# ============================================================================
# XML Instruction Sync Routes
# ============================================================================

@router.get("/{agent_id}/xml-instructions")
async def get_xml_instructions(
    agent_id: str,
    supabase: Client = Depends(get_supabase)
):
    """
    Get the XML instruction file content for an agent.

    Returns the content of the XML file in backend/system_instructions/agents/{name}.xml
    """
    try:
        # Get agent name
        agent_result = supabase.table("agents")\
            .select("name, display_name")\
            .eq("id", agent_id)\
            .execute()

        if not agent_result.data:
            raise HTTPException(status_code=404, detail="Agent not found")

        agent_name = agent_result.data[0]["name"]
        display_name = agent_result.data[0]["display_name"]

        # Check if XML file exists
        if not instruction_file_exists(agent_name):
            return {
                "success": False,
                "has_xml": False,
                "agent_name": agent_name,
                "display_name": display_name,
                "message": f"No XML file found for agent '{agent_name}'"
            }

        # Load XML content
        xml_content = load_instruction_from_file(agent_name)
        file_mtime = get_instruction_file_mtime(agent_name)

        return {
            "success": True,
            "has_xml": True,
            "agent_name": agent_name,
            "display_name": display_name,
            "xml_instructions": xml_content,
            "character_count": len(xml_content) if xml_content else 0,
            "word_count": len(xml_content.split()) if xml_content else 0,
            "file_modified_at": file_mtime.isoformat() if file_mtime else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get XML instructions for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/sync-from-xml")
async def sync_instructions_from_xml(
    agent_id: str,
    description: Optional[str] = None,
    user_id: Optional[str] = None,
    supabase: Client = Depends(get_supabase)
):
    """
    Sync instructions from XML file to database.

    This creates a new version in agent_instruction_versions from the current XML file
    and activates it. Use this when you've edited the XML file and want to apply changes.
    """
    try:
        # Get agent info
        agent_result = supabase.table("agents")\
            .select("name, display_name")\
            .eq("id", agent_id)\
            .execute()

        if not agent_result.data:
            raise HTTPException(status_code=404, detail="Agent not found")

        agent_name = agent_result.data[0]["name"]

        # Check if XML file exists
        if not instruction_file_exists(agent_name):
            raise HTTPException(
                status_code=404,
                detail=f"No XML file found for agent '{agent_name}'"
            )

        # Load XML content
        xml_content = load_instruction_from_file(agent_name)
        if not xml_content or len(xml_content) < 100:
            raise HTTPException(
                status_code=400,
                detail="XML file is empty or too short"
            )

        # Get current version count to generate version number
        existing = supabase.table("agent_instruction_versions")\
            .select("version_number")\
            .eq("agent_id", agent_id)\
            .order("created_at", desc=True)\
            .limit(1)\
            .execute()

        if existing.data:
            last_version = existing.data[0]["version_number"]
            try:
                major, minor = last_version.split(".")
                new_version = f"{major}.{int(minor) + 1}"
            except (ValueError, IndexError):
                new_version = "1.1"
        else:
            new_version = "1.0"

        # Deactivate all existing versions
        supabase.table("agent_instruction_versions")\
            .update({"is_active": False})\
            .eq("agent_id", agent_id)\
            .execute()

        # Create new version from XML
        version_result = supabase.table("agent_instruction_versions").insert({
            "agent_id": agent_id,
            "version_number": new_version,
            "instructions": xml_content,
            "description": description or f"Synced from XML file",
            "is_active": True,
            "activated_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user_id,
        }).execute()

        # Update agent timestamp
        supabase.table("agents")\
            .update({"updated_at": datetime.now(timezone.utc).isoformat()})\
            .eq("id", agent_id)\
            .execute()

        file_mtime = get_instruction_file_mtime(agent_name)

        return {
            "success": True,
            "message": f"Synced XML to database as version {new_version}",
            "version": version_result.data[0],
            "character_count": len(xml_content),
            "file_modified_at": file_mtime.isoformat() if file_mtime else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync XML for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/sync-to-xml")
async def sync_instructions_to_xml(
    agent_id: str,
    supabase: Client = Depends(get_supabase)
):
    """
    Sync active database instructions to XML file.

    This saves the current active version to the XML file.
    Use this to update the XML file after editing via the admin UI.
    """
    try:
        # Get agent info
        agent_result = supabase.table("agents")\
            .select("name, display_name")\
            .eq("id", agent_id)\
            .execute()

        if not agent_result.data:
            raise HTTPException(status_code=404, detail="Agent not found")

        agent_name = agent_result.data[0]["name"]

        # Get active version
        version_result = supabase.table("agent_instruction_versions")\
            .select("*")\
            .eq("agent_id", agent_id)\
            .eq("is_active", True)\
            .limit(1)\
            .execute()

        if not version_result.data:
            raise HTTPException(
                status_code=404,
                detail="No active instruction version found"
            )

        instructions = version_result.data[0]["instructions"]
        version_number = version_result.data[0]["version_number"]

        # Save to XML file
        success = save_instruction_to_file(agent_name, instructions)
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to write to XML file"
            )

        file_mtime = get_instruction_file_mtime(agent_name)

        return {
            "success": True,
            "message": f"Saved version {version_number} to XML file",
            "agent_name": agent_name,
            "version_number": version_number,
            "character_count": len(instructions),
            "file_modified_at": file_mtime.isoformat() if file_mtime else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync to XML for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/xml-files")
async def list_xml_instruction_files():
    """
    List all available XML instruction files.

    Returns information about each XML file in backend/system_instructions/agents/
    """
    try:
        files = list_available_instruction_files()
        return {
            "success": True,
            "files": files,
            "count": len(files)
        }
    except Exception as e:
        logger.error(f"Failed to list XML files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Agent Stats Routes
# ============================================================================

@router.get("/{agent_id}/default-instructions")
async def get_agent_default_instructions(
    agent_id: str,
    supabase: Client = Depends(get_supabase)
):
    """
    Get the Python default instructions for an agent.

    This returns the hardcoded default instructions from the agent's Python class.
    Useful when the database has placeholder text or empty instructions.
    """
    try:
        # Get the agent name
        agent_result = supabase.table("agents")\
            .select("name, display_name")\
            .eq("id", agent_id)\
            .execute()

        if not agent_result.data:
            raise HTTPException(status_code=404, detail="Agent not found")

        agent_name = agent_result.data[0]["name"]
        display_name = agent_result.data[0]["display_name"]

        # Import and instantiate the agent to get default instructions
        from agents import (
            AtlasAgent, CapitalAgent, GuardianAgent, CounselorAgent, OracleAgent,
            SageAgent, StrategistAgent, ArchitectAgent, OperatorAgent, PioneerAgent,
            CatalystAgent, ScholarAgent, NexusAgent, CoordinatorAgent
        )
        import anthropic
        import os

        # Create a minimal anthropic client (we won't use it, just need it for instantiation)
        anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", "dummy"))

        agent_classes = {
            "atlas": AtlasAgent,
            "capital": CapitalAgent,
            "guardian": GuardianAgent,
            "counselor": CounselorAgent,
            "oracle": OracleAgent,
            "sage": SageAgent,
            "strategist": StrategistAgent,
            "architect": ArchitectAgent,
            "operator": OperatorAgent,
            "pioneer": PioneerAgent,
            "catalyst": CatalystAgent,
            "scholar": ScholarAgent,
            "nexus": NexusAgent,
            "coordinator": CoordinatorAgent,
        }

        agent_class = agent_classes.get(agent_name.lower())
        if not agent_class:
            return {
                "success": False,
                "has_default": False,
                "message": f"No Python class found for agent '{agent_name}'"
            }

        # Instantiate the agent to get default instructions
        agent_instance = agent_class(supabase, anthropic_client)
        default_instructions = agent_instance._get_default_instruction()

        return {
            "success": True,
            "has_default": bool(default_instructions),
            "agent_name": agent_name,
            "display_name": display_name,
            "default_instructions": default_instructions,
            "character_count": len(default_instructions) if default_instructions else 0,
            "word_count": len(default_instructions.split()) if default_instructions else 0
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get default instructions for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
