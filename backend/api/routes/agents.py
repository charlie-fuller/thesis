"""Agent Management API Routes.

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

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import pb_client as pb
from repositories.agents import (
    create_agent as repo_create_agent,
    get_agent as repo_get_agent,
    get_agent_by_name,
    list_agents as repo_list_agents,
    update_agent as repo_update_agent,
    list_instruction_versions,
    get_instruction_version as repo_get_instruction_version,
    create_instruction_version as repo_create_instruction_version,
    update_instruction_version as repo_update_instruction_version,
    delete_instruction_version as repo_delete_instruction_version,
    list_agent_knowledge_base,
    create_agent_knowledge_base_item,
    update_agent_knowledge_base_item,
    delete_agent_knowledge_base_item,
)
from services.instruction_loader import (
    get_instruction_file_mtime,
    instruction_file_exists,
    list_available_instruction_files,
    load_instruction_from_file,
    save_instruction_to_file,
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
):
    """List all agents with summary stats."""
    try:
        agents_data = repo_list_agents(is_active=not include_inactive) if not include_inactive else repo_list_agents(is_active=False)
        if include_inactive:
            # list all agents regardless of active status
            agents_data = pb.get_all("agents", sort="name")

        agents = []
        for agent in agents_data:
            # Get instruction version count
            versions = list_instruction_versions(agent["id"])
            versions_count = len(versions)

            # Get conversation count
            convs_count = pb.count("conversations", filter=f"agent_id='{pb.escape_filter(agent['id'])}'")

            # Get KB document count
            kb_docs = list_agent_knowledge_base(agent["id"])
            kb_count = len(kb_docs)

            # Get meeting room participation count (count unique meetings where agent has messages)
            meeting_msgs = pb.get_all(
                "meeting_room_messages",
                filter=f"agent_id='{pb.escape_filter(agent['id'])}'",
            )
            unique_meetings = set()
            for msg in meeting_msgs:
                if msg.get("meeting_room_id"):
                    unique_meetings.add(msg["meeting_room_id"])

            agents.append(
                {
                    **agent,
                    "instruction_versions_count": versions_count,
                    "kb_documents_count": kb_count,
                    "conversations_count": convs_count,
                    "meeting_rooms_count": len(unique_meetings),
                }
            )

        return {"success": True, "agents": agents}

    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/{agent_id}/conversations")
async def get_agent_conversations(
    agent_id: str,
    limit: int = 50,
    include_archived: bool = False,
):
    """Get conversations for a specific agent."""
    try:
        # Verify agent exists
        agent = repo_get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Build filter for conversations
        parts = [f"agent_id='{pb.escape_filter(agent_id)}'"]
        if not include_archived:
            parts.append("archived=false")
        filter_str = " && ".join(parts)

        result = pb.list_records(
            "conversations",
            filter=filter_str,
            sort="-updated_at",
            per_page=limit,
        )
        conversations = result.get("items", [])

        # Get message counts for all conversations
        if conversations:
            for conv in conversations:
                msg_count = pb.count("messages", filter=f"conversation_id='{pb.escape_filter(conv['id'])}'")
                conv["message_count"] = msg_count

        return {
            "success": True,
            "agent": {"id": agent["id"], "name": agent["name"], "display_name": agent["display_name"]},
            "conversations": conversations,
            "count": len(conversations),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversations for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/{agent_id}")
async def get_agent(
    agent_id: str,
):
    """Get full agent details including current instructions."""
    try:
        agent = repo_get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Get all instruction versions
        all_versions = list_instruction_versions(agent_id)

        # Get active instruction version
        active_version = None
        for v in all_versions:
            if v.get("is_active"):
                active_version = v
                break

        # Get conversation count
        convs_count = pb.count("conversations", filter=f"agent_id='{pb.escape_filter(agent_id)}'")

        # Get linked KB documents (without join -- separate lookup for documents)
        kb_links = list_agent_knowledge_base(agent_id)

        kb_documents = []
        for link in kb_links:
            doc = pb.get_record("documents", link.get("document_id", ""))
            if doc:
                kb_documents.append(
                    {
                        "link_id": link["id"],
                        "document": doc,
                        "notes": link.get("notes"),
                        "priority": link.get("priority", 0),
                        "added_at": link.get("created"),
                    }
                )

        return {
            "agent": agent,
            "active_instruction_version": active_version,
            "instruction_versions": all_versions,
            "kb_documents": kb_documents,
            "stats": {
                "conversations_count": convs_count,
                "instruction_versions_count": len(all_versions),
                "kb_documents_count": len(kb_documents),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("")
async def create_agent(
    agent: AgentCreate,
):
    """Create a new agent."""
    try:
        # Check if name already exists
        existing = get_agent_by_name(agent.name)
        if existing:
            raise HTTPException(status_code=400, detail=f"Agent '{agent.name}' already exists")

        result = repo_create_agent(
            {
                "name": agent.name,
                "display_name": agent.display_name,
                "description": agent.description,
                "system_instruction": agent.system_instruction,
                "is_active": agent.is_active,
                "config": agent.config,
            }
        )

        return {"agent": result}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.patch("/{agent_id}")
async def update_agent(
    agent_id: str,
    updates: AgentUpdate,
):
    """Update agent metadata (not instructions - use instruction versioning for that)."""
    try:
        update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

        existing = repo_get_agent(agent_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Agent not found")

        result = repo_update_agent(agent_id, update_data)

        return {"agent": result}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# Instruction Version Routes
# ============================================================================


@router.get("/{agent_id}/instructions")
async def get_agent_instructions(
    agent_id: str,
):
    """Get all instruction versions for an agent."""
    try:
        versions = list_instruction_versions(agent_id)
        return {"versions": versions}

    except Exception as e:
        logger.error(f"Failed to get instructions for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/{agent_id}/instructions")
async def create_instruction_version(
    agent_id: str,
    instruction: AgentInstructionUpdate,
):
    """Create a new instruction version for an agent."""
    try:
        # Get current version count to generate version number
        versions = list_instruction_versions(agent_id)

        if versions:
            # Parse version and increment
            last_version = versions[0]["version_number"]
            try:
                major, minor = last_version.split(".")
                new_version = f"{major}.{int(minor) + 1}"
            except (ValueError, IndexError):
                new_version = "1.1"
        else:
            new_version = "1.0"

        # Create new version
        result = repo_create_instruction_version(
            {
                "agent_id": agent_id,
                "version_number": new_version,
                "instructions": instruction.instructions,
                "description": instruction.description,
                "is_active": False,  # Don't auto-activate
            }
        )

        return {"version": result}

    except Exception as e:
        logger.error(f"Failed to create instruction version for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/{agent_id}/instructions/{version_id}/activate")
async def activate_instruction_version(
    agent_id: str,
    version_id: str,
):
    """Activate a specific instruction version (deactivates others).

    The agent_instruction_versions table is the SINGLE SOURCE OF TRUTH.
    Running agents will pick up changes on next initialization or via reload.
    """
    try:
        # Deactivate all versions for this agent
        all_versions = list_instruction_versions(agent_id)
        for v in all_versions:
            if v.get("is_active"):
                repo_update_instruction_version(v["id"], {"is_active": False})

        # Activate the specified version
        result = repo_update_instruction_version(
            version_id,
            {"is_active": True, "activated_at": datetime.now(timezone.utc).isoformat()},
        )

        if not result:
            raise HTTPException(status_code=404, detail="Version not found")

        # Update agent's updated_at timestamp
        repo_update_agent(agent_id, {"updated_at": datetime.now(timezone.utc).isoformat()})

        return {
            "version": result,
            "message": "Version activated. Running agents will use this on next request.",
            "reload_required": True,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to activate version {version_id} for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


class VersionCompareRequest(BaseModel):
    """Request to compare two instruction versions."""

    version_a_id: str
    version_b_id: str


@router.get("/{agent_id}/instructions/{version_id}")
async def get_instruction_version(
    agent_id: str,
    version_id: str,
):
    """Get a specific instruction version."""
    try:
        version = repo_get_instruction_version(version_id)

        if not version or version.get("agent_id") != agent_id:
            raise HTTPException(status_code=404, detail="Version not found")

        return {"success": True, "version": version}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get version {version_id}: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.delete("/{agent_id}/instructions/{version_id}")
async def delete_instruction_version(
    agent_id: str,
    version_id: str,
):
    """Delete an instruction version (cannot delete active version)."""
    try:
        # Check if version is active
        version = repo_get_instruction_version(version_id)

        if not version or version.get("agent_id") != agent_id:
            raise HTTPException(status_code=404, detail="Version not found")

        if version.get("is_active"):
            raise HTTPException(status_code=400, detail="Cannot delete active version")

        repo_delete_instruction_version(version_id)

        return {"success": True, "message": f"Version {version['version_number']} deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete version {version_id}: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/{agent_id}/instructions/compare")
async def compare_instruction_versions(
    agent_id: str,
    v1: str,
    v2: str,
):
    """Compare two instruction versions (GET for simple comparison)."""
    try:
        version1 = repo_get_instruction_version(v1)
        version2 = repo_get_instruction_version(v2)

        if not version1 or not version2:
            raise HTTPException(status_code=404, detail="One or both versions not found")

        return {
            "version1": version1,
            "version2": version2,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to compare versions: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/{agent_id}/instructions/compare")
async def compare_versions_detailed(
    agent_id: str,
    request: VersionCompareRequest,
):
    """Compare two instruction versions with detailed diff."""
    import difflib

    try:
        version_a = repo_get_instruction_version(request.version_a_id)
        version_b = repo_get_instruction_version(request.version_b_id)

        if not version_a or not version_b:
            raise HTTPException(status_code=404, detail="One or both versions not found")
        if version_a.get("agent_id") != agent_id or version_b.get("agent_id") != agent_id:
            raise HTTPException(status_code=404, detail="One or both versions not found")

        # Generate unified diff
        content_a = version_a.get("instructions", "").splitlines(keepends=True)
        content_b = version_b.get("instructions", "").splitlines(keepends=True)

        diff = list(
            difflib.unified_diff(
                content_a,
                content_b,
                fromfile=f"v{version_a['version_number']}",
                tofile=f"v{version_b['version_number']}",
                lineterm="",
            )
        )

        # Calculate stats
        additions = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
        deletions = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))

        return {
            "success": True,
            "version_a": {
                "id": version_a["id"],
                "version_number": version_a["version_number"],
                "created": version_a["created"],
            },
            "version_b": {
                "id": version_b["id"],
                "version_number": version_b["version_number"],
                "created": version_b["created"],
            },
            "diff": diff,
            "stats": {
                "additions": additions,
                "deletions": deletions,
                "total_changes": additions + deletions,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to compare versions: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/{agent_id}/instructions/compare/summary")
async def generate_comparison_summary(
    agent_id: str,
    request: VersionCompareRequest,
):
    """Generate an AI summary of changes between two instruction versions."""
    import difflib
    import os

    import anthropic

    try:
        version_a = repo_get_instruction_version(request.version_a_id)
        version_b = repo_get_instruction_version(request.version_b_id)

        if not version_a or not version_b:
            raise HTTPException(status_code=404, detail="One or both versions not found")

        # Get agent info for context
        agent = repo_get_agent(agent_id)
        agent_name = agent.get("display_name", "Unknown Agent") if agent else "Unknown Agent"

        # Generate diff
        content_a = version_a.get("instructions", "").splitlines(keepends=True)
        content_b = version_b.get("instructions", "").splitlines(keepends=True)

        diff = list(
            difflib.unified_diff(
                content_a,
                content_b,
                fromfile=f"v{version_a['version_number']}",
                tofile=f"v{version_b['version_number']}",
                lineterm="",
            )
        )

        # Calculate stats
        additions = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
        deletions = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))

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

Provide a clear, bulleted summary of the changes (3-7 bullet points).""",
                }
            ],
        )

        summary = message.content[0].text

        return {
            "success": True,
            "version_a": {
                "id": version_a["id"],
                "version_number": version_a["version_number"],
                "created": version_a["created"],
            },
            "version_b": {
                "id": version_b["id"],
                "version_number": version_b["version_number"],
                "created": version_b["created"],
            },
            "summary": summary,
            "stats": {
                "additions": additions,
                "deletions": deletions,
                "total_changes": additions + deletions,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate comparison summary: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# Knowledge Base Document Routes
# ============================================================================

# IMPORTANT: Static routes must be defined BEFORE parameterized routes
# /documents/available must come before /{agent_id}/documents
# Otherwise FastAPI matches "documents" as an agent_id


@router.get("/documents/available")
async def get_available_documents(
    agent_id: Optional[str] = None,
):
    """Get all documents available for linking. If agent_id provided, excludes already linked docs."""
    try:
        # Get all documents
        documents = pb.get_all("documents", sort="-uploaded_at")

        # If agent_id provided, filter out already linked documents
        if agent_id:
            kb_links = list_agent_knowledge_base(agent_id)
            linked_ids = {link["document_id"] for link in kb_links}
            documents = [doc for doc in documents if doc["id"] not in linked_ids]

        return {"documents": documents}

    except Exception as e:
        logger.error(f"Failed to get available documents: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/{agent_id}/documents")
async def get_agent_documents(
    agent_id: str,
):
    """Get documents linked to an agent's knowledge base."""
    try:
        kb_links = list_agent_knowledge_base(agent_id)

        documents = []
        for link in kb_links:
            doc = pb.get_record("documents", link.get("document_id", ""))
            if doc:
                documents.append(
                    {
                        "link_id": link["id"],
                        "document": doc,
                        "notes": link.get("notes"),
                        "priority": link.get("priority", 0),
                        "added_at": link.get("created"),
                    }
                )

        return {"documents": documents}

    except Exception as e:
        logger.error(f"Failed to get documents for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/{agent_id}/documents")
async def link_document_to_agent(
    agent_id: str,
    doc_link: AgentKBDocLink,
):
    """Link a document to an agent's knowledge base."""
    try:
        # Check if link already exists
        existing = pb.get_first(
            "agent_knowledge_base",
            filter=f"agent_id='{pb.escape_filter(agent_id)}' && document_id='{pb.escape_filter(doc_link.document_id)}'",
        )

        if existing:
            raise HTTPException(status_code=400, detail="Document already linked to this agent")

        # Verify document exists
        doc = pb.get_record("documents", doc_link.document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Create link
        result = create_agent_knowledge_base_item(
            {
                "agent_id": agent_id,
                "document_id": doc_link.document_id,
                "notes": doc_link.notes,
                "priority": doc_link.priority,
            }
        )

        return {
            "link": result,
            "document": doc,
            "message": f"Document '{doc['filename']}' linked to agent",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to link document to agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.patch("/{agent_id}/documents/{link_id}")
async def update_document_link(
    agent_id: str,
    link_id: str,
    updates: AgentKBDocUpdate,
):
    """Update a KB document link (notes, priority)."""
    try:
        update_data = {k: v for k, v in updates.model_dump().items() if v is not None}

        # Verify link exists and belongs to this agent
        existing = pb.get_record("agent_knowledge_base", link_id)
        if not existing or existing.get("agent_id") != agent_id:
            raise HTTPException(status_code=404, detail="Link not found")

        result = update_agent_knowledge_base_item(link_id, update_data)

        return {"link": result}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update document link {link_id}: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.delete("/{agent_id}/documents/{link_id}")
async def unlink_document_from_agent(
    agent_id: str,
    link_id: str,
):
    """Remove a document from an agent's knowledge base."""
    try:
        # Verify link exists and belongs to this agent
        existing = pb.get_record("agent_knowledge_base", link_id)
        if not existing or existing.get("agent_id") != agent_id:
            raise HTTPException(status_code=404, detail="Link not found")

        delete_agent_knowledge_base_item(link_id)

        return {"message": "Document unlinked from agent", "deleted_link": existing}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to unlink document from agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# XML Instruction Sync Routes
# ============================================================================


@router.get("/{agent_id}/xml-instructions")
async def get_xml_instructions(
    agent_id: str,
):
    """Get the XML instruction file content for an agent.

    Returns the content of the XML file in backend/system_instructions/agents/{name}.xml
    """
    try:
        # Get agent name
        agent = repo_get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        agent_name = agent["name"]
        display_name = agent["display_name"]

        # Check if XML file exists
        if not instruction_file_exists(agent_name):
            return {
                "success": False,
                "has_xml": False,
                "agent_name": agent_name,
                "display_name": display_name,
                "message": f"No XML file found for agent '{agent_name}'",
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
            "file_modified_at": file_mtime.isoformat() if file_mtime else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get XML instructions for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/{agent_id}/sync-from-xml")
async def sync_instructions_from_xml(
    agent_id: str,
    description: Optional[str] = None,
):
    """Sync instructions from XML file to database.

    This creates a new version in agent_instruction_versions from the current XML file
    and activates it. Use this when you've edited the XML file and want to apply changes.
    """
    try:
        # Get agent info
        agent = repo_get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        agent_name = agent["name"]

        # Check if XML file exists
        if not instruction_file_exists(agent_name):
            raise HTTPException(status_code=404, detail=f"No XML file found for agent '{agent_name}'")

        # Load XML content
        xml_content = load_instruction_from_file(agent_name)
        if not xml_content or len(xml_content) < 100:
            raise HTTPException(status_code=400, detail="XML file is empty or too short")

        # Get current version count to generate version number
        versions = list_instruction_versions(agent_id)

        if versions:
            last_version = versions[0]["version_number"]
            try:
                major, minor = last_version.split(".")
                new_version = f"{major}.{int(minor) + 1}"
            except (ValueError, IndexError):
                new_version = "1.1"
        else:
            new_version = "1.0"

        # Deactivate all existing versions
        for v in versions:
            if v.get("is_active"):
                repo_update_instruction_version(v["id"], {"is_active": False})

        # Create new version from XML
        version_result = repo_create_instruction_version(
            {
                "agent_id": agent_id,
                "version_number": new_version,
                "instructions": xml_content,
                "description": description or "Synced from XML file",
                "is_active": True,
                "activated_at": datetime.now(timezone.utc).isoformat(),
            }
        )

        # Update agent timestamp
        repo_update_agent(agent_id, {"updated_at": datetime.now(timezone.utc).isoformat()})

        file_mtime = get_instruction_file_mtime(agent_name)

        return {
            "success": True,
            "message": f"Synced XML to database as version {new_version}",
            "version": version_result,
            "character_count": len(xml_content),
            "file_modified_at": file_mtime.isoformat() if file_mtime else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync XML for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/{agent_id}/sync-to-xml")
async def sync_instructions_to_xml(
    agent_id: str,
):
    """Sync active database instructions to XML file.

    This saves the current active version to the XML file.
    Use this to update the XML file after editing via the admin UI.
    """
    try:
        # Get agent info
        agent = repo_get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        agent_name = agent["name"]

        # Get active version
        versions = list_instruction_versions(agent_id)
        active_version = None
        for v in versions:
            if v.get("is_active"):
                active_version = v
                break

        if not active_version:
            raise HTTPException(status_code=404, detail="No active instruction version found")

        instructions = active_version["instructions"]
        version_number = active_version["version_number"]

        # Save to XML file
        success = save_instruction_to_file(agent_name, instructions)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to write to XML file")

        file_mtime = get_instruction_file_mtime(agent_name)

        return {
            "success": True,
            "message": f"Saved version {version_number} to XML file",
            "agent_name": agent_name,
            "version_number": version_number,
            "character_count": len(instructions),
            "file_modified_at": file_mtime.isoformat() if file_mtime else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync to XML for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/xml-files")
async def list_xml_instruction_files():
    """List all available XML instruction files.

    Returns information about each XML file in backend/system_instructions/agents/
    """
    try:
        files = list_available_instruction_files()
        return {"success": True, "files": files, "count": len(files)}
    except Exception as e:
        logger.error(f"Failed to list XML files: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# Agent Stats Routes
# ============================================================================


@router.get("/{agent_id}/default-instructions")
async def get_agent_default_instructions(
    agent_id: str,
):
    """Get the Python default instructions for an agent.

    This returns the hardcoded default instructions from the agent's Python class.
    Useful when the database has placeholder text or empty instructions.
    """
    try:
        # Get the agent name
        agent = repo_get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        agent_name = agent["name"]
        display_name = agent["display_name"]

        # Import and instantiate the agent to get default instructions
        import os

        import anthropic

        from agents import (
            ArchitectAgent,
            AtlasAgent,
            CapitalAgent,
            CatalystAgent,
            CoordinatorAgent,
            CounselorAgent,
            GuardianAgent,
            NexusAgent,
            OperatorAgent,
            OracleAgent,
            PioneerAgent,
            SageAgent,
            ScholarAgent,
            StrategistAgent,
        )

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
                "message": f"No Python class found for agent '{agent_name}'",
            }

        # Instantiate the agent to get default instructions
        # NOTE: services will be rewritten later; passing None for supabase
        agent_instance = agent_class(None, anthropic_client)
        default_instructions = agent_instance._get_default_instruction()

        return {
            "success": True,
            "has_default": bool(default_instructions),
            "agent_name": agent_name,
            "display_name": display_name,
            "default_instructions": default_instructions,
            "character_count": len(default_instructions) if default_instructions else 0,
            "word_count": len(default_instructions.split()) if default_instructions else 0,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get default instructions for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/{agent_id}/stats")
async def get_agent_stats(
    agent_id: str,
):
    """Get usage statistics for an agent."""
    try:
        # Conversation count
        convs_count = pb.count("conversations", filter=f"agent_id='{pb.escape_filter(agent_id)}'")

        # Recent conversations
        recent_result = pb.list_records(
            "conversations",
            filter=f"agent_id='{pb.escape_filter(agent_id)}'",
            sort="-created_at",
            per_page=5,
        )
        recent_convs = recent_result.get("items", [])

        return {
            "total_conversations": convs_count,
            "recent_conversations": recent_convs,
        }

    except Exception as e:
        logger.error(f"Failed to get stats for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e
