"""DISCo Workflow routes - Runs, Outputs, and Checkpoints."""

import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

import pb_client as pb
from logger_config import get_logger
from repositories import disco as disco_repo
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
    require_initiative_access,
)

logger = get_logger(__name__)
router = APIRouter()


# ============================================================================
# RUNS
# ============================================================================


@router.get("/initiatives/{initiative_id}/runs")
async def api_list_runs(
    initiative_id: str,
    limit: int = 20,
):
    """List agent runs for an initiative."""
    require_initiative_access(initiative_id)

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
):
    """Start a new agent run with streaming response."""
    require_initiative_access(initiative_id)

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
                    document_ids=data.document_ids,
                )
            else:
                agent_gen = run_agent(
                    initiative_id=initiative_id,
                    agent_type=data.agent_type,
                    document_ids=data.document_ids,
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
):
    """Get a run by ID."""
    require_initiative_access(initiative_id)

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
):
    """List outputs for an initiative."""
    # Resolve to UUID and check access
    resolved_id = require_initiative_access(initiative_id)

    try:
        outputs = disco_repo.list_outputs(resolved_id, agent_type=agent_type or "", sort="-created")

        return {"success": True, "outputs": outputs}
    except Exception as e:
        logger.error(f"Error listing outputs: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/initiatives/{initiative_id}/outputs/{agent_type}")
async def api_get_latest_output(
    initiative_id: str,
    agent_type: str,
):
    """Get the latest output of a specific type."""
    require_initiative_access(initiative_id)

    try:
        esc_init = pb.escape_filter(initiative_id)
        esc_agent = pb.escape_filter(agent_type)
        result = pb.list_records(
            "disco_outputs",
            filter=f"initiative_id='{esc_init}' && agent_type='{esc_agent}'",
            sort="-version",
            per_page=1,
        )
        items = result.get("items", [])

        if not items:
            raise HTTPException(status_code=404, detail=f"No {agent_type} output found")

        return {"success": True, "output": items[0]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching output: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/initiatives/{initiative_id}/outputs/{agent_type}/versions")
async def api_list_output_versions(
    initiative_id: str,
    agent_type: str,
):
    """List all versions of an output type."""
    require_initiative_access(initiative_id)

    try:
        esc_init = pb.escape_filter(initiative_id)
        esc_agent = pb.escape_filter(agent_type)
        versions = pb.get_all(
            "disco_outputs",
            filter=f"initiative_id='{esc_init}' && agent_type='{esc_agent}'",
            sort="-version",
        )

        return {"success": True, "versions": versions}
    except Exception as e:
        logger.error(f"Error listing output versions: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/initiatives/{initiative_id}/outputs/{output_id}/export")
async def api_export_output(
    initiative_id: str,
    output_id: str,
):
    """Export an output as markdown."""
    require_initiative_access(initiative_id)

    try:
        output = disco_repo.get_output(output_id)
        if not output or output.get("initiative_id") != initiative_id:
            raise HTTPException(status_code=404, detail="Output not found")

        filename = f"{output['agent_type']}_v{output['version']}.md"

        return StreamingResponse(
            iter([output.get("content_markdown", "")]),
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
):
    """Promote an output to a document."""
    require_initiative_access(initiative_id)

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
):
    """Delete an output."""
    require_initiative_access(initiative_id)

    try:
        # Verify output belongs to initiative
        output = disco_repo.get_output(output_id)
        if not output or output.get("initiative_id") != initiative_id:
            raise HTTPException(status_code=404, detail="Output not found")

        # Delete the output
        pb.delete_record("disco_outputs", output_id)

        logger.info(
            f"[DISCO] Deleted output {output_id} ({output['agent_type']} v{output['version']})"
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
):
    """Apply Smart Brevity condensation to an output."""
    require_initiative_access(initiative_id)

    async def event_stream():
        yield ": " + " " * 2048 + "\n\n"

        try:
            async for event in condense_output(output_id):
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
):
    """List all checkpoints for an initiative.

    Returns checkpoint statuses for the 4 stage gates:
    1. Discovery Guide -> Insight Analyst
    2. Insight Analyst -> Initiative Builder
    3. Initiative Builder -> Requirements Generator
    4. Requirements Generator -> Done
    """
    require_initiative_access(initiative_id)

    try:
        # Fetch checkpoints
        checkpoints = disco_repo.list_checkpoints(initiative_id, sort="checkpoint_number")

        # If no checkpoints exist, initialize them
        if not checkpoints:
            for num in range(1, 5):
                disco_repo.create_checkpoint({
                    "initiative_id": initiative_id,
                    "checkpoint_number": num,
                    "status": "locked" if num > 1 else "needs_review",
                })
            checkpoints = disco_repo.list_checkpoints(initiative_id, sort="checkpoint_number")

        # Calculate staleness for each checkpoint
        for checkpoint in checkpoints:
            if checkpoint.get("status") == "approved" and checkpoint.get("approved_at"):
                esc_init = pb.escape_filter(initiative_id)
                esc_date = pb.escape_filter(checkpoint["approved_at"])
                new_docs = pb.get_first(
                    "disco_initiative_documents",
                    filter=f"initiative_id='{esc_init}' && created>'{esc_date}'",
                )
                if new_docs:
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
):
    """Get a specific checkpoint with details."""
    require_initiative_access(initiative_id)

    if checkpoint_number not in [1, 2, 3, 4]:
        raise HTTPException(status_code=400, detail="Checkpoint number must be 1-4")

    try:
        esc_init = pb.escape_filter(initiative_id)
        checkpoint = pb.get_first(
            "disco_checkpoints",
            filter=f"initiative_id='{esc_init}' && checkpoint_number={checkpoint_number}",
        )

        if not checkpoint:
            raise HTTPException(status_code=404, detail="Checkpoint not found")

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
):
    """Approve a checkpoint to unlock the next agent.

    This is the human-in-the-loop gate between DISCo stages.
    """
    require_initiative_access(initiative_id)

    if checkpoint_number not in [1, 2, 3, 4]:
        raise HTTPException(status_code=400, detail="Checkpoint number must be 1-4")

    try:
        # Get current checkpoint
        esc_init = pb.escape_filter(initiative_id)
        checkpoint = pb.get_first(
            "disco_checkpoints",
            filter=f"initiative_id='{esc_init}' && checkpoint_number={checkpoint_number}",
        )

        if not checkpoint:
            raise HTTPException(status_code=404, detail="Checkpoint not found")

        if checkpoint["status"] not in ["needs_review", "stale"]:
            raise HTTPException(
                status_code=400,
                detail=f"Checkpoint cannot be approved (current status: {checkpoint['status']})",
            )

        # Update checkpoint to approved
        update_data = {
            "status": "approved",
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "notes": body.notes,
        }

        if body.checklist_items:
            update_data["checklist_items"] = body.checklist_items

        disco_repo.update_checkpoint(checkpoint["id"], update_data)

        # Unlock the next checkpoint if not the last one
        if checkpoint_number < 4:
            next_cp = pb.get_first(
                "disco_checkpoints",
                filter=f"initiative_id='{esc_init}' && checkpoint_number={checkpoint_number + 1} && status='locked'",
            )
            if next_cp:
                disco_repo.update_checkpoint(next_cp["id"], {"status": "locked"})

        logger.info(
            f"[DISCO] Checkpoint {checkpoint_number} approved for initiative {initiative_id}"
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
):
    """Reset a checkpoint to needs_review.

    Used when re-running an agent after approval, or when requesting changes.
    """
    require_initiative_access(initiative_id)

    if checkpoint_number not in [1, 2, 3, 4]:
        raise HTTPException(status_code=400, detail="Checkpoint number must be 1-4")

    try:
        # Get current checkpoint
        esc_init = pb.escape_filter(initiative_id)
        checkpoint = pb.get_first(
            "disco_checkpoints",
            filter=f"initiative_id='{esc_init}' && checkpoint_number={checkpoint_number}",
        )

        if not checkpoint:
            raise HTTPException(status_code=404, detail="Checkpoint not found")

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

        disco_repo.update_checkpoint(checkpoint["id"], update_data)

        # Also reset subsequent checkpoints to locked
        if checkpoint_number < 4:
            subsequent = pb.get_all(
                "disco_checkpoints",
                filter=f"initiative_id='{esc_init}' && checkpoint_number>{checkpoint_number}",
            )
            for cp in subsequent:
                disco_repo.update_checkpoint(cp["id"], {
                    "status": "locked",
                    "approved_at": None,
                    "approved_by": None,
                })

        logger.info(
            f"[DISCO] Checkpoint {checkpoint_number} reset for initiative {initiative_id}"
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
):
    """Debug endpoint to check raw output data."""
    require_initiative_access(initiative_id)

    try:
        esc_init = pb.escape_filter(initiative_id)
        result = pb.list_records(
            "disco_outputs",
            filter=f"initiative_id='{esc_init}'",
            sort="-created",
            per_page=5,
        )

        outputs = []
        for o in result.get("items", []):
            outputs.append(
                {
                    "id": o.get("id"),
                    "agent_type": o.get("agent_type"),
                    "agent_type_type": type(o.get("agent_type")).__name__,
                    "version": o.get("version"),
                    "title": o.get("title"),
                    "content_length": len(o.get("content_markdown", "") or ""),
                    "content_preview": (o.get("content_markdown", "") or "")[:200],
                    "created_at": o.get("created"),
                }
            )

        return {"success": True, "count": len(outputs), "outputs": outputs}
    except Exception as e:
        logger.error(f"Debug outputs error: {e}")
        return {"success": False, "error": str(e)}
