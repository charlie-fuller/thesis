"""DISCo Workflow routes - Runs, Outputs, and Checkpoints."""

import asyncio
import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from database import get_supabase
from logger_config import get_logger
from services.disco import promote_output_to_document, run_agent
from services.disco.agent_service import (
    MULTI_PASS_CONFIG,
    get_run,
    list_runs,
    run_agent_multi_pass,
)
from services.disco.condenser_service import condense_output

from ._shared import (
    AgentRunRequest,
    CheckpointApprove,
    CheckpointReset,
    require_disco_access,
    require_initiative_access,
)

logger = get_logger(__name__)
router = APIRouter()
supabase = get_supabase()


# ============================================================================
# RUNS
# ============================================================================


@router.get("/initiatives/{initiative_id}/runs")
async def api_list_runs(
    initiative_id: str,
    limit: int = 20,
    current_user: dict = Depends(require_disco_access),
):
    """List agent runs for an initiative."""
    await require_initiative_access(initiative_id, current_user, "viewer")

    try:
        runs = await list_runs(initiative_id, limit)
        return {"success": True, "runs": runs}
    except Exception as e:
        logger.error(f"Error listing runs: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/initiatives/{initiative_id}/runs")
async def api_start_run(
    initiative_id: str,
    data: AgentRunRequest,
    current_user: dict = Depends(require_disco_access),
):
    """Start a new agent run with streaming response."""
    await require_initiative_access(initiative_id, current_user, "editor")

    # Check if multi-pass is requested and valid
    use_multi_pass = data.multi_pass and data.agent_type in MULTI_PASS_CONFIG.get("supported_agents", [])

    async def event_stream():
        # Send initial padding to force proxy buffer flush
        yield ": " + " " * 2048 + "\n\n"

        try:
            if use_multi_pass:
                agent_gen = run_agent_multi_pass(
                    initiative_id=initiative_id,
                    agent_type=data.agent_type,
                    user_id=current_user["id"],
                    document_ids=data.document_ids,
                    output_format=data.output_format or "comprehensive",
                )
            else:
                agent_gen = run_agent(
                    initiative_id=initiative_id,
                    agent_type=data.agent_type,
                    user_id=current_user["id"],
                    document_ids=data.document_ids,
                    output_format=data.output_format or "comprehensive",
                    kb_folder=data.kb_folder,
                    kb_tags=data.kb_tags,
                )

            async for event in agent_gen:
                event_type = event.get("type", "unknown")
                event_data = event.get("data", "")

                if event_type == "content":
                    yield f"data: {event_data}\n\n"
                elif event_type == "keepalive":
                    yield ": keepalive\n\n"
                elif event_type == "status":
                    yield f"event: status\ndata: {event_data}\n\n"
                elif event_type == "pass_complete":
                    yield f"event: pass_complete\ndata: {json.dumps(event_data)}\n\n"
                elif event_type == "complete":
                    yield f"event: complete\ndata: {json.dumps(event_data)}\n\n"
                elif event_type == "error":
                    yield f"event: error\ndata: {event_data}\n\n"

        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"event: error\ndata: {str(e)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Type": "text/event-stream; charset=utf-8",
        },
    )


@router.get("/initiatives/{initiative_id}/runs/{run_id}")
async def api_get_run(
    initiative_id: str,
    run_id: str,
    current_user: dict = Depends(require_disco_access),
):
    """Get a run by ID."""
    await require_initiative_access(initiative_id, current_user, "viewer")

    try:
        run = await get_run(run_id)
        if not run or run.get("initiative_id") != initiative_id:
            raise HTTPException(status_code=404, detail="Run not found")
        return {"success": True, "run": run}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching run: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# OUTPUTS
# ============================================================================


@router.get("/initiatives/{initiative_id}/outputs")
async def api_list_outputs(
    initiative_id: str,
    agent_type: Optional[str] = None,
    current_user: dict = Depends(require_disco_access),
):
    """List outputs for an initiative."""
    await require_initiative_access(initiative_id, current_user, "viewer")

    try:
        query = supabase.table("disco_outputs").select("*").eq("initiative_id", initiative_id)

        if agent_type:
            query = query.eq("agent_type", agent_type)

        query = query.order("created_at", desc=True)
        result = await asyncio.to_thread(lambda: query.execute())

        return {"success": True, "outputs": result.data or []}
    except Exception as e:
        logger.error(f"Error listing outputs: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/initiatives/{initiative_id}/outputs/{agent_type}")
async def api_get_latest_output(
    initiative_id: str,
    agent_type: str,
    current_user: dict = Depends(require_disco_access),
):
    """Get the latest output of a specific type."""
    await require_initiative_access(initiative_id, current_user, "viewer")

    try:
        result = await asyncio.to_thread(
            lambda: supabase.table("disco_outputs")
            .select("*")
            .eq("initiative_id", initiative_id)
            .eq("agent_type", agent_type)
            .order("version", desc=True)
            .limit(1)
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail=f"No {agent_type} output found")

        return {"success": True, "output": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching output: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/initiatives/{initiative_id}/outputs/{agent_type}/versions")
async def api_list_output_versions(
    initiative_id: str,
    agent_type: str,
    current_user: dict = Depends(require_disco_access),
):
    """List all versions of an output type."""
    await require_initiative_access(initiative_id, current_user, "viewer")

    try:
        result = await asyncio.to_thread(
            lambda: supabase.table("disco_outputs")
            .select("id, version, created_at, title, recommendation, confidence_level")
            .eq("initiative_id", initiative_id)
            .eq("agent_type", agent_type)
            .order("version", desc=True)
            .execute()
        )

        return {"success": True, "versions": result.data or []}
    except Exception as e:
        logger.error(f"Error listing output versions: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/initiatives/{initiative_id}/outputs/{output_id}/export")
async def api_export_output(
    initiative_id: str,
    output_id: str,
    current_user: dict = Depends(require_disco_access),
):
    """Export an output as markdown."""
    await require_initiative_access(initiative_id, current_user, "viewer")

    try:
        result = await asyncio.to_thread(
            lambda: supabase.table("disco_outputs")
            .select("agent_type, version, content_markdown")
            .eq("id", output_id)
            .eq("initiative_id", initiative_id)
            .single()
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Output not found")

        output = result.data
        filename = f"{output['agent_type']}_v{output['version']}.md"

        return StreamingResponse(
            iter([output["content_markdown"]]),
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting output: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/initiatives/{initiative_id}/outputs/{output_id}/promote")
async def api_promote_output(
    initiative_id: str,
    output_id: str,
    current_user: dict = Depends(require_disco_access),
):
    """Promote an output to a document."""
    await require_initiative_access(initiative_id, current_user, "editor")

    try:
        document = await promote_output_to_document(output_id, initiative_id)
        return {"success": True, "document": document}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from None
    except Exception as e:
        logger.error(f"Error promoting output: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.delete("/initiatives/{initiative_id}/outputs/{output_id}")
async def api_delete_output(
    initiative_id: str,
    output_id: str,
    current_user: dict = Depends(require_disco_access),
):
    """Delete an output."""
    await require_initiative_access(initiative_id, current_user, "editor")

    try:
        # Verify output belongs to initiative
        output_result = await asyncio.to_thread(
            lambda: supabase.table("disco_outputs")
            .select("id, agent_type, version")
            .eq("id", output_id)
            .eq("initiative_id", initiative_id)
            .single()
            .execute()
        )

        if not output_result.data:
            raise HTTPException(status_code=404, detail="Output not found")

        # Delete the output
        await asyncio.to_thread(lambda: supabase.table("disco_outputs").delete().eq("id", output_id).execute())

        logger.info(
            f"[DISCO] Deleted output {output_id} ({output_result.data['agent_type']} v{output_result.data['version']})"
        )

        return {"success": True, "deleted_output_id": output_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting output: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/initiatives/{initiative_id}/outputs/{output_id}/condense")
async def api_condense_output(
    initiative_id: str,
    output_id: str,
    current_user: dict = Depends(require_disco_access),
):
    """Apply Smart Brevity condensation to an output."""
    await require_initiative_access(initiative_id, current_user, "editor")

    async def event_stream():
        yield ": " + " " * 2048 + "\n\n"

        try:
            async for event in condense_output(output_id, current_user["id"]):
                event_type = event.get("type", "unknown")
                event_data = event.get("data", "")

                if event_type == "content":
                    yield f"data: {event_data}\n\n"
                elif event_type == "keepalive":
                    yield ": keepalive\n\n"
                elif event_type == "status":
                    yield f"event: status\ndata: {event_data}\n\n"
                elif event_type == "complete":
                    yield f"event: complete\ndata: {json.dumps(event_data)}\n\n"
                elif event_type == "error":
                    yield f"event: error\ndata: {event_data}\n\n"

        except Exception as e:
            logger.error(f"Condense stream error: {e}")
            yield f"event: error\ndata: {str(e)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Type": "text/event-stream; charset=utf-8",
        },
    )


# ============================================================================
# CHECKPOINTS
# ============================================================================


def _get_next_agent_for_checkpoint(checkpoint_number: int) -> Optional[str]:
    """Get the next agent to run after a checkpoint is approved."""
    agents = {
        1: "insight_analyst",
        2: "initiative_builder",
        3: "requirements_generator",
        4: None,
    }
    return agents.get(checkpoint_number)


@router.get("/initiatives/{initiative_id}/checkpoints")
async def api_list_checkpoints(
    initiative_id: str,
    current_user: dict = Depends(require_disco_access),
):
    """List all checkpoints for an initiative.

    Returns checkpoint statuses for the 4 stage gates:
    1. Discovery Guide -> Insight Analyst
    2. Insight Analyst -> Initiative Builder
    3. Initiative Builder -> Requirements Generator
    4. Requirements Generator -> Done
    """
    await require_initiative_access(initiative_id, current_user, "viewer")

    try:
        # Initialize checkpoints if they don't exist
        await asyncio.to_thread(
            lambda: supabase.rpc("initialize_disco_checkpoints", {"p_initiative_id": initiative_id}).execute()
        )

        # Fetch checkpoints
        result = await asyncio.to_thread(
            lambda: supabase.table("disco_checkpoints")
            .select("*")
            .eq("initiative_id", initiative_id)
            .order("checkpoint_number")
            .execute()
        )

        checkpoints = result.data or []

        # Calculate staleness for each checkpoint
        for checkpoint in checkpoints:
            if checkpoint["status"] == "approved":
                docs_result = await asyncio.to_thread(
                    lambda cp=checkpoint: supabase.table("disco_initiative_documents")
                    .select("linked_at")
                    .eq("initiative_id", initiative_id)
                    .gt("linked_at", cp["approved_at"])
                    .limit(1)
                    .execute()
                )
                if docs_result.data:
                    checkpoint["status"] = "stale"
                    checkpoint["stale_reason"] = "New documents added since approval"

        return {"success": True, "checkpoints": checkpoints}
    except Exception as e:
        logger.error(f"Error listing checkpoints: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/initiatives/{initiative_id}/checkpoints/{checkpoint_number}")
async def api_get_checkpoint(
    initiative_id: str,
    checkpoint_number: int,
    current_user: dict = Depends(require_disco_access),
):
    """Get a specific checkpoint with details."""
    await require_initiative_access(initiative_id, current_user, "viewer")

    if checkpoint_number not in [1, 2, 3, 4]:
        raise HTTPException(status_code=400, detail="Checkpoint number must be 1-4")

    try:
        result = await asyncio.to_thread(
            lambda: supabase.table("disco_checkpoints")
            .select("*")
            .eq("initiative_id", initiative_id)
            .eq("checkpoint_number", checkpoint_number)
            .single()
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Checkpoint not found")

        checkpoint = result.data

        # Checkpoint-specific checklist content
        checkpoint_checklists = {
            1: {
                "title": "Ready to Execute Discovery?",
                "items": [
                    {
                        "item": "Triage decision is GO (not NO-GO or INVESTIGATE)",
                        "completed": False,
                    },
                    {
                        "item": "Discovery sessions are planned with clear agendas",
                        "completed": False,
                    },
                    {"item": "Participants and sponsors are identified", "completed": False},
                    {
                        "item": "You are ready to execute the discovery sessions",
                        "completed": False,
                    },
                ],
                "human_action": (
                    "After approval, YOU will conduct interviews/workshops per the "
                    "session plan, upload transcripts and notes to Documents, and "
                    "re-run Discovery Guide to check coverage."
                ),
            },
            2: {
                "title": "Ready for Initiative Bundles?",
                "items": [
                    {"item": "Decision document quality is acceptable", "completed": False},
                    {"item": "Leverage point makes sense", "completed": False},
                    {"item": "Evidence supports conclusions", "completed": False},
                    {"item": "No critical gaps or contradictions", "completed": False},
                ],
                "human_action": ("Review the decision document and validate the leverage point before proceeding."),
            },
            3: {
                "title": "Ready for PRD Generation?",
                "items": [
                    {"item": "Bundle definitions are clear", "completed": False},
                    {
                        "item": "Scoring (impact/feasibility/urgency) is accurate",
                        "completed": False,
                    },
                    {"item": "Dependencies are correctly mapped", "completed": False},
                    {"item": "Selected bundles for PRD generation", "completed": False},
                ],
                "human_action": ("Approve, reject, merge, or split bundles as needed before generating PRDs."),
            },
            4: {
                "title": "Ready for Engineering Handoff?",
                "items": [
                    {"item": "PRD is complete and accurate", "completed": False},
                    {"item": "Technical approach is validated", "completed": False},
                    {"item": "Requirements are testable", "completed": False},
                    {"item": "Ready for engineering planning", "completed": False},
                ],
                "human_action": "Final review before handoff to engineering team.",
            },
        }

        checkpoint["checklist_config"] = checkpoint_checklists.get(checkpoint_number)

        return {"success": True, "checkpoint": checkpoint}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting checkpoint: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/initiatives/{initiative_id}/checkpoints/{checkpoint_number}/approve")
async def api_approve_checkpoint(
    initiative_id: str,
    checkpoint_number: int,
    body: CheckpointApprove,
    current_user: dict = Depends(require_disco_access),
):
    """Approve a checkpoint to unlock the next agent.

    This is the human-in-the-loop gate between DISCo stages.
    """
    await require_initiative_access(initiative_id, current_user, "editor")

    if checkpoint_number not in [1, 2, 3, 4]:
        raise HTTPException(status_code=400, detail="Checkpoint number must be 1-4")

    try:
        # Get current checkpoint
        result = await asyncio.to_thread(
            lambda: supabase.table("disco_checkpoints")
            .select("*")
            .eq("initiative_id", initiative_id)
            .eq("checkpoint_number", checkpoint_number)
            .single()
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Checkpoint not found")

        checkpoint = result.data

        if checkpoint["status"] not in ["needs_review", "stale"]:
            raise HTTPException(
                status_code=400,
                detail=f"Checkpoint cannot be approved (current status: {checkpoint['status']})",
            )

        # Update checkpoint to approved
        update_data = {
            "status": "approved",
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "approved_by": current_user["id"],
            "notes": body.notes,
        }

        if body.checklist_items:
            update_data["checklist_items"] = body.checklist_items

        await asyncio.to_thread(
            lambda: supabase.table("disco_checkpoints").update(update_data).eq("id", checkpoint["id"]).execute()
        )

        # Unlock the next checkpoint if not the last one
        if checkpoint_number < 4:
            await asyncio.to_thread(
                lambda: supabase.table("disco_checkpoints")
                .update({"status": "locked"})
                .eq("initiative_id", initiative_id)
                .eq("checkpoint_number", checkpoint_number + 1)
                .eq("status", "locked")
                .execute()
            )

        logger.info(
            f"[DISCO] Checkpoint {checkpoint_number} approved for initiative "
            f"{initiative_id} by user {current_user['id']}"
        )

        return {
            "success": True,
            "message": f"Checkpoint {checkpoint_number} approved",
            "next_agent": _get_next_agent_for_checkpoint(checkpoint_number),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving checkpoint: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/initiatives/{initiative_id}/checkpoints/{checkpoint_number}/reset")
async def api_reset_checkpoint(
    initiative_id: str,
    checkpoint_number: int,
    body: CheckpointReset,
    current_user: dict = Depends(require_disco_access),
):
    """Reset a checkpoint to needs_review.

    Used when re-running an agent after approval, or when requesting changes.
    """
    await require_initiative_access(initiative_id, current_user, "editor")

    if checkpoint_number not in [1, 2, 3, 4]:
        raise HTTPException(status_code=400, detail="Checkpoint number must be 1-4")

    try:
        # Get current checkpoint
        result = await asyncio.to_thread(
            lambda: supabase.table("disco_checkpoints")
            .select("*")
            .eq("initiative_id", initiative_id)
            .eq("checkpoint_number", checkpoint_number)
            .single()
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Checkpoint not found")

        checkpoint = result.data

        if checkpoint["status"] == "locked":
            raise HTTPException(status_code=400, detail="Cannot reset a locked checkpoint")

        # Reset checkpoint to needs_review
        update_data = {
            "status": "needs_review",
            "approved_at": None,
            "approved_by": None,
        }

        if body.reason:
            update_data["notes"] = f"Reset: {body.reason}"

        await asyncio.to_thread(
            lambda: supabase.table("disco_checkpoints").update(update_data).eq("id", checkpoint["id"]).execute()
        )

        # Also reset subsequent checkpoints to locked
        if checkpoint_number < 4:
            await asyncio.to_thread(
                lambda: supabase.table("disco_checkpoints")
                .update({"status": "locked", "approved_at": None, "approved_by": None})
                .eq("initiative_id", initiative_id)
                .gt("checkpoint_number", checkpoint_number)
                .execute()
            )

        logger.info(
            f"[DISCO] Checkpoint {checkpoint_number} reset for initiative {initiative_id} by user {current_user['id']}"
        )

        return {
            "success": True,
            "message": f"Checkpoint {checkpoint_number} reset to needs_review",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting checkpoint: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# DEBUG
# ============================================================================


@router.get("/initiatives/{initiative_id}/debug/outputs")
async def api_debug_outputs(
    initiative_id: str,
    current_user: dict = Depends(require_disco_access),
):
    """Debug endpoint to check raw output data."""
    await require_initiative_access(initiative_id, current_user, "viewer")

    try:
        result = await asyncio.to_thread(
            lambda: supabase.table("disco_outputs")
            .select("id, agent_type, version, title, content_markdown, created_at")
            .eq("initiative_id", initiative_id)
            .order("created_at", desc=True)
            .limit(5)
            .execute()
        )

        outputs = []
        for o in result.data or []:
            outputs.append(
                {
                    "id": o.get("id"),
                    "agent_type": o.get("agent_type"),
                    "agent_type_type": type(o.get("agent_type")).__name__,
                    "version": o.get("version"),
                    "title": o.get("title"),
                    "content_length": len(o.get("content_markdown", "") or ""),
                    "content_preview": (o.get("content_markdown", "") or "")[:200],
                    "created_at": o.get("created_at"),
                }
            )

        return {"success": True, "count": len(result.data or []), "outputs": outputs}
    except Exception as e:
        logger.error(f"Debug outputs error: {e}")
        return {"success": False, "error": str(e)}
