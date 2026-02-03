"""DISCo Synthesis routes - Bundles and PRDs."""

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from logger_config import get_logger
from services.disco import check_permission, get_initiative, run_agent
from services.disco.prd_service import (
    approve_prd,
    generate_executive_summary,
    generate_prd_for_bundle,
    get_prd,
    list_prds,
    update_prd,
)
from services.disco.synthesis_service import (
    approve_bundle,
    create_bundle,
    get_bundle,
    get_bundle_feedback,
    list_bundles,
    merge_bundles,
    parse_synthesis_output,
    reject_bundle,
    split_bundle,
    update_bundle,
)

from ._shared import (
    BundleApproval,
    BundleCreate,
    BundleMerge,
    BundleSplit,
    BundleUpdate,
    PRDUpdate,
    require_disco_access,
)

logger = get_logger(__name__)
router = APIRouter()


# ============================================================================
# BUNDLES
# ============================================================================


@router.get("/initiatives/{initiative_id}/bundles")
async def api_list_bundles(
    initiative_id: str,
    status: Optional[str] = None,
    current_user: dict = Depends(require_disco_access),
):
    """List bundles for an initiative."""
    try:
        initiative = await get_initiative(initiative_id)
        if not initiative:
            raise HTTPException(status_code=404, detail="Initiative not found")

        can_view = await check_permission(initiative_id, current_user["id"], "viewer")
        if not can_view:
            raise HTTPException(status_code=403, detail="No access to this initiative")

        bundles = await list_bundles(initiative_id, status=status)
        return {"success": True, "bundles": bundles}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing bundles: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/initiatives/{initiative_id}/bundles")
async def api_create_bundle(
    initiative_id: str,
    body: BundleCreate,
    current_user: dict = Depends(require_disco_access),
):
    """Create a new bundle for an initiative."""
    try:
        can_edit = await check_permission(initiative_id, current_user["id"], "editor")
        if not can_edit:
            raise HTTPException(status_code=403, detail="No edit access to this initiative")

        bundle = await create_bundle(
            initiative_id=initiative_id,
            name=body.name,
            description=body.description,
            impact_score=body.impact_score,
            impact_rationale=body.impact_rationale,
            feasibility_score=body.feasibility_score,
            feasibility_rationale=body.feasibility_rationale,
            urgency_score=body.urgency_score,
            urgency_rationale=body.urgency_rationale,
            complexity_tier=body.complexity_tier,
            complexity_rationale=body.complexity_rationale,
            included_items=body.included_items,
            stakeholders=body.stakeholders,
            dependencies=body.dependencies,
            bundling_rationale=body.bundling_rationale,
        )
        return {"success": True, "bundle": bundle}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating bundle: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/initiatives/{initiative_id}/bundles/{bundle_id}")
async def api_get_bundle(
    initiative_id: str,
    bundle_id: str,
    current_user: dict = Depends(require_disco_access),
):
    """Get a specific bundle."""
    try:
        can_view = await check_permission(initiative_id, current_user["id"], "viewer")
        if not can_view:
            raise HTTPException(status_code=403, detail="No access to this initiative")

        bundle = await get_bundle(bundle_id)
        if not bundle or bundle["initiative_id"] != initiative_id:
            raise HTTPException(status_code=404, detail="Bundle not found")

        feedback = await get_bundle_feedback(bundle_id)

        return {"success": True, "bundle": bundle, "feedback": feedback}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting bundle: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.patch("/initiatives/{initiative_id}/bundles/{bundle_id}")
async def api_update_bundle(
    initiative_id: str,
    bundle_id: str,
    body: BundleUpdate,
    current_user: dict = Depends(require_disco_access),
):
    """Update a bundle."""
    try:
        can_edit = await check_permission(initiative_id, current_user["id"], "editor")
        if not can_edit:
            raise HTTPException(status_code=403, detail="No edit access to this initiative")

        bundle = await get_bundle(bundle_id)
        if not bundle or bundle["initiative_id"] != initiative_id:
            raise HTTPException(status_code=404, detail="Bundle not found")

        updates = {k: v for k, v in body.model_dump().items() if v is not None and k != "feedback"}

        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")

        updated_bundle = await update_bundle(
            bundle_id=bundle_id,
            updates=updates,
            user_id=current_user["id"],
            feedback=body.feedback,
        )
        return {"success": True, "bundle": updated_bundle}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
    except Exception as e:
        logger.error(f"Error updating bundle: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/initiatives/{initiative_id}/bundles/{bundle_id}/approve")
async def api_approve_bundle(
    initiative_id: str,
    bundle_id: str,
    body: BundleApproval,
    current_user: dict = Depends(require_disco_access),
):
    """Approve a bundle for PRD generation."""
    try:
        can_edit = await check_permission(initiative_id, current_user["id"], "editor")
        if not can_edit:
            raise HTTPException(status_code=403, detail="No edit access to this initiative")

        bundle = await get_bundle(bundle_id)
        if not bundle or bundle["initiative_id"] != initiative_id:
            raise HTTPException(status_code=404, detail="Bundle not found")

        if bundle["status"] != "proposed":
            raise HTTPException(status_code=400, detail=f"Bundle is already {bundle['status']}")

        approved_bundle = await approve_bundle(
            bundle_id=bundle_id,
            user_id=current_user["id"],
            feedback=body.feedback,
        )
        return {"success": True, "bundle": approved_bundle}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving bundle: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/initiatives/{initiative_id}/bundles/{bundle_id}/reject")
async def api_reject_bundle(
    initiative_id: str,
    bundle_id: str,
    body: BundleApproval,
    current_user: dict = Depends(require_disco_access),
):
    """Reject a bundle."""
    try:
        can_edit = await check_permission(initiative_id, current_user["id"], "editor")
        if not can_edit:
            raise HTTPException(status_code=403, detail="No edit access to this initiative")

        bundle = await get_bundle(bundle_id)
        if not bundle or bundle["initiative_id"] != initiative_id:
            raise HTTPException(status_code=404, detail="Bundle not found")

        if bundle["status"] != "proposed":
            raise HTTPException(status_code=400, detail=f"Bundle is already {bundle['status']}")

        if not body.feedback:
            raise HTTPException(status_code=400, detail="Feedback is required when rejecting")

        rejected_bundle = await reject_bundle(
            bundle_id=bundle_id,
            user_id=current_user["id"],
            feedback=body.feedback,
        )
        return {"success": True, "bundle": rejected_bundle}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting bundle: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/initiatives/{initiative_id}/bundles/merge")
async def api_merge_bundles(
    initiative_id: str,
    body: BundleMerge,
    current_user: dict = Depends(require_disco_access),
):
    """Merge multiple bundles into one."""
    try:
        can_edit = await check_permission(initiative_id, current_user["id"], "editor")
        if not can_edit:
            raise HTTPException(status_code=403, detail="No edit access to this initiative")

        # Verify all bundles belong to this initiative
        for bid in body.bundle_ids:
            bundle = await get_bundle(bid)
            if not bundle or bundle["initiative_id"] != initiative_id:
                raise HTTPException(status_code=404, detail=f"Bundle not found: {bid}")

        merged_bundle = await merge_bundles(
            bundle_ids=body.bundle_ids,
            merged_name=body.merged_name,
            merged_description=body.merged_description,
            user_id=current_user["id"],
            feedback=body.feedback,
        )
        return {"success": True, "bundle": merged_bundle}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
    except Exception as e:
        logger.error(f"Error merging bundles: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/initiatives/{initiative_id}/bundles/{bundle_id}/split")
async def api_split_bundle(
    initiative_id: str,
    bundle_id: str,
    body: BundleSplit,
    current_user: dict = Depends(require_disco_access),
):
    """Split a bundle into multiple bundles."""
    try:
        can_edit = await check_permission(initiative_id, current_user["id"], "editor")
        if not can_edit:
            raise HTTPException(status_code=403, detail="No edit access to this initiative")

        bundle = await get_bundle(bundle_id)
        if not bundle or bundle["initiative_id"] != initiative_id:
            raise HTTPException(status_code=404, detail="Bundle not found")

        new_bundles = await split_bundle(
            bundle_id=bundle_id,
            split_definitions=body.split_definitions,
            user_id=current_user["id"],
            feedback=body.feedback,
        )
        return {"success": True, "bundles": new_bundles}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
    except Exception as e:
        logger.error(f"Error splitting bundle: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/initiatives/{initiative_id}/synthesize")
async def api_run_synthesis(
    initiative_id: str,
    current_user: dict = Depends(require_disco_access),
):
    """Run the Synthesis agent and create bundles from its output.

    This endpoint:
    1. Runs the synthesis agent
    2. Parses the output to extract bundle definitions
    3. Creates bundle records in the database
    """
    try:
        can_edit = await check_permission(initiative_id, current_user["id"], "editor")
        if not can_edit:
            raise HTTPException(status_code=403, detail="No edit access to this initiative")

        async def stream_and_create_bundles():
            output_id = None
            full_content = ""

            async for event in run_agent(
                initiative_id=initiative_id,
                agent_type="strategist",
                user_id=current_user["id"],
                output_format="comprehensive",
            ):
                if event["type"] == "complete":
                    output_id = event.get("data", {}).get("id")
                    full_content = event.get("data", {}).get("content_markdown", "")
                yield event

            # After streaming completes, parse and create bundles
            if output_id and full_content:
                try:
                    bundle_defs = parse_synthesis_output(full_content, output_id)
                    created_bundles = []
                    for defn in bundle_defs:
                        bundle = await create_bundle(initiative_id=initiative_id, **defn)
                        created_bundles.append(bundle)

                    yield {
                        "type": "bundles_created",
                        "data": {"count": len(created_bundles), "bundles": created_bundles},
                    }
                except Exception as e:
                    logger.error(f"Error creating bundles from synthesis: {e}")
                    yield {"type": "bundles_error", "data": str(e)}

        async def generate():
            async for event in stream_and_create_bundles():
                event_type = event["type"]
                data = event.get("data", "")

                if isinstance(data, dict):
                    data = json.dumps(data)

                if event_type in [
                    "status",
                    "complete",
                    "error",
                    "bundles_created",
                    "bundles_error",
                ]:
                    yield f"event: {event_type}\ndata: {data}\n\n"
                else:
                    yield f"data: {data}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running synthesis: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# PRDs
# ============================================================================


@router.get("/initiatives/{initiative_id}/prds")
async def api_list_prds(
    initiative_id: str,
    bundle_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(require_disco_access),
):
    """List PRDs for an initiative."""
    try:
        can_view = await check_permission(initiative_id, current_user["id"], "viewer")
        if not can_view:
            raise HTTPException(status_code=403, detail="No access to this initiative")

        prds = await list_prds(initiative_id, bundle_id=bundle_id, status=status)
        return {"success": True, "prds": prds}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing PRDs: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/initiatives/{initiative_id}/prds/{prd_id}")
async def api_get_prd(
    initiative_id: str,
    prd_id: str,
    current_user: dict = Depends(require_disco_access),
):
    """Get a specific PRD."""
    try:
        can_view = await check_permission(initiative_id, current_user["id"], "viewer")
        if not can_view:
            raise HTTPException(status_code=403, detail="No access to this initiative")

        prd = await get_prd(prd_id)
        if not prd or prd["initiative_id"] != initiative_id:
            raise HTTPException(status_code=404, detail="PRD not found")

        return {"success": True, "prd": prd}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting PRD: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.patch("/initiatives/{initiative_id}/prds/{prd_id}")
async def api_update_prd(
    initiative_id: str,
    prd_id: str,
    body: PRDUpdate,
    current_user: dict = Depends(require_disco_access),
):
    """Update a PRD."""
    try:
        can_edit = await check_permission(initiative_id, current_user["id"], "editor")
        if not can_edit:
            raise HTTPException(status_code=403, detail="No edit access to this initiative")

        prd = await get_prd(prd_id)
        if not prd or prd["initiative_id"] != initiative_id:
            raise HTTPException(status_code=404, detail="PRD not found")

        updates = {k: v for k, v in body.model_dump().items() if v is not None}
        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")

        updated_prd = await update_prd(prd_id, updates)
        return {"success": True, "prd": updated_prd}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating PRD: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/initiatives/{initiative_id}/prds/{prd_id}/approve")
async def api_approve_prd(
    initiative_id: str,
    prd_id: str,
    current_user: dict = Depends(require_disco_access),
):
    """Approve a PRD."""
    try:
        can_edit = await check_permission(initiative_id, current_user["id"], "editor")
        if not can_edit:
            raise HTTPException(status_code=403, detail="No edit access to this initiative")

        prd = await get_prd(prd_id)
        if not prd or prd["initiative_id"] != initiative_id:
            raise HTTPException(status_code=404, detail="PRD not found")

        approved_prd = await approve_prd(prd_id, current_user["id"])
        return {"success": True, "prd": approved_prd}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving PRD: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/initiatives/{initiative_id}/bundles/{bundle_id}/generate-prd")
async def api_generate_prd(
    initiative_id: str,
    bundle_id: str,
    current_user: dict = Depends(require_disco_access),
):
    """Generate a PRD for an approved bundle."""
    try:
        can_edit = await check_permission(initiative_id, current_user["id"], "editor")
        if not can_edit:
            raise HTTPException(status_code=403, detail="No edit access to this initiative")

        bundle = await get_bundle(bundle_id)
        if not bundle or bundle["initiative_id"] != initiative_id:
            raise HTTPException(status_code=404, detail="Bundle not found")

        if bundle["status"] != "approved":
            raise HTTPException(
                status_code=400,
                detail=f"Bundle must be approved (current: {bundle['status']})",
            )

        async def generate():
            async for event in generate_prd_for_bundle(
                bundle_id=bundle_id,
                initiative_id=initiative_id,
                user_id=current_user["id"],
            ):
                event_type = event["type"]
                data = event.get("data", "")

                if isinstance(data, dict):
                    data = json.dumps(data)

                if event_type in ["status", "complete", "error"]:
                    yield f"event: {event_type}\ndata: {data}\n\n"
                else:
                    yield f"data: {data}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating PRD: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/initiatives/{initiative_id}/generate-summary")
async def api_generate_executive_summary(
    initiative_id: str,
    current_user: dict = Depends(require_disco_access),
):
    """Generate an executive summary across all approved bundles."""
    try:
        can_view = await check_permission(initiative_id, current_user["id"], "viewer")
        if not can_view:
            raise HTTPException(status_code=403, detail="No access to this initiative")

        async def generate():
            async for event in generate_executive_summary(
                initiative_id=initiative_id, user_id=current_user["id"]
            ):
                event_type = event["type"]
                data = event.get("data", "")

                if isinstance(data, dict):
                    data = json.dumps(data)

                if event_type in ["status", "complete", "error"]:
                    yield f"event: {event_type}\ndata: {data}\n\n"
                else:
                    yield f"data: {data}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating executive summary: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e
