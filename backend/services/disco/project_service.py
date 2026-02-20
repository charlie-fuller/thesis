"""DISCo Project Service.

Handles operations related to projects linked to DISCo initiatives.
"""

import asyncio
from typing import Dict, Optional

from database import get_supabase, with_db_retry
from logger_config import get_logger

logger = get_logger(__name__)


def _is_valid_uuid(value: str) -> bool:
    """Check if a string is a valid UUID."""
    try:
        from uuid import UUID

        UUID(value)
        return True
    except (ValueError, AttributeError):
        return False


async def _resolve_initiative_id(initiative_id: str) -> Optional[str]:
    """Resolve an initiative ID (UUID or name) to its UUID.

    Args:
        initiative_id: Either a UUID or initiative name

    Returns:
        The initiative's UUID, or None if not found
    """
    if _is_valid_uuid(initiative_id):
        return initiative_id

    # Look up by name
    db = get_supabase()
    result = await asyncio.to_thread(
        lambda: db.table("disco_initiatives").select("id").eq("name", initiative_id).single().execute()
    )

    if not result.data:
        return None

    return result.data["id"]


@with_db_retry(max_retries=2)
async def get_initiative_projects(initiative_id: str, status: Optional[str] = None) -> Dict:
    """Get all projects linked to an initiative.

    Args:
        initiative_id: Initiative UUID or name
        status: Optional filter by project status

    Returns:
        Dict with projects list and count
    """
    logger.info(f"Getting projects for initiative: {initiative_id}")

    # Resolve initiative ID (support name or UUID)
    resolved_id = await _resolve_initiative_id(initiative_id)
    if not resolved_id:
        return {"projects": [], "count": 0}

    try:
        db = get_supabase()

        # Query projects where initiative_ids contains this initiative
        query = (
            db.table("ai_projects")
            .select(
                "id, project_code, title, description, status, tier, total_score, source_type, source_id, created_at"
            )
            .contains("initiative_ids", [resolved_id])
        )

        if status:
            query = query.eq("status", status)

        query = query.order("created_at", desc=True)

        result = await asyncio.to_thread(lambda: query.execute())
        projects = result.data or []

        logger.info(f"Found {len(projects)} projects for initiative {resolved_id}")
        return {"projects": projects, "count": len(projects)}

    except Exception as e:
        logger.error(f"Error getting initiative projects: {e}")
        raise


@with_db_retry(max_retries=2)
async def create_project_from_prd(
    prd_id: str,
    initiative_id: str,
    user_id: str,
    project_data: Dict,
) -> Dict:
    """Create a project from a PRD.

    Args:
        prd_id: Source PRD ID
        initiative_id: Parent initiative ID
        user_id: Creating user's ID
        project_data: Project fields extracted from PRD

    Returns:
        Created project record
    """
    from uuid import uuid4

    logger.info(f"Creating project from PRD {prd_id}")

    try:
        db = get_supabase()

        # Get PRD title for reference
        prd_result = await asyncio.to_thread(
            lambda: db.table("disco_prds").select("title").eq("id", prd_id).single().execute()
        )
        prd_title = prd_result.data.get("title") if prd_result.data else "Unknown PRD"

        # Prepare project record
        project_id = str(uuid4())
        project_record = {
            "id": project_id,
            "project_code": project_data.get("project_code", f"PRD{project_id[:4].upper()}"),
            "title": project_data.get("title", prd_title),
            "description": project_data.get("description"),
            "department": project_data.get("department"),
            "current_state": project_data.get("current_state"),
            "desired_state": project_data.get("desired_state"),
            "roi_potential": project_data.get("roi_potential", 3),
            "implementation_effort": project_data.get("implementation_effort", 3),
            "strategic_alignment": project_data.get("strategic_alignment", 3),
            "stakeholder_readiness": project_data.get("stakeholder_readiness", 3),
            "status": "identified",
            "source_type": "disco_prd",
            "source_id": prd_id,
            "source_notes": f"Created from PRD: {prd_title}",
            "initiative_ids": [initiative_id],
            "created_by": user_id,
        }

        result = await asyncio.to_thread(lambda: db.table("ai_projects").insert(project_record).execute())

        if not result.data:
            raise Exception("Failed to create project")

        logger.info(f"Created project {project_id} from PRD {prd_id}")
        return result.data[0]

    except Exception as e:
        logger.error(f"Error creating project from PRD: {e}")
        raise


# Score mapping: HIGH/MEDIUM/LOW -> numeric 1-5
_SCORE_MAP = {"HIGH": 5, "MEDIUM": 3, "LOW": 1}
_INVERSE_SCORE_MAP = {"HIGH": 1, "MEDIUM": 3, "LOW": 5}


@with_db_retry(max_retries=2)
async def create_project_from_bundle(
    bundle: Dict,
    initiative_id: str,
    user_id: str,
    client_id: str,
) -> Dict:
    """Create a project directly from an approved bundle.

    Maps bundle scores to project scoring dimensions:
    - impact_score -> roi_potential (HIGH=5, MEDIUM=3, LOW=1)
    - feasibility_score -> implementation_effort (inverse: HIGH=1, MEDIUM=3, LOW=5)
    - urgency_score -> strategic_alignment (HIGH=5, MEDIUM=3, LOW=1)

    Args:
        bundle: The approved bundle record
        initiative_id: Parent initiative ID
        user_id: Creating user's ID
        client_id: User's client ID

    Returns:
        Created project record
    """
    from uuid import uuid4

    bundle_id = bundle["id"]
    logger.info(f"Creating project from bundle {bundle_id}")

    try:
        db = get_supabase()

        project_id = str(uuid4())
        project_code = project_id[:4].upper()

        # Map scores
        roi_potential = _SCORE_MAP.get(bundle.get("impact_score"), 3)
        implementation_effort = _INVERSE_SCORE_MAP.get(bundle.get("feasibility_score"), 3)
        strategic_alignment = _SCORE_MAP.get(bundle.get("urgency_score"), 3)

        bundle_name = bundle.get("name", "Untitled Bundle")
        project_record = {
            "id": project_id,
            "client_id": client_id,
            "project_code": project_code,
            "title": bundle_name,
            "description": bundle.get("description"),
            "roi_potential": roi_potential,
            "implementation_effort": implementation_effort,
            "strategic_alignment": strategic_alignment,
            "stakeholder_readiness": 3,
            "status": "identified",
            "source_type": "disco_proposed",
            "source_id": bundle_id,
            "source_notes": f"Created from proposed initiative: {bundle_name}",
            "initiative_ids": [initiative_id],
            "created_by": user_id,
        }

        result = await asyncio.to_thread(lambda: db.table("ai_projects").insert(project_record).execute())

        if not result.data:
            raise Exception("Failed to create project")

        logger.info(f"Created project {project_id} from bundle {bundle_id}")
        return result.data[0]

    except Exception as e:
        logger.error(f"Error creating project from bundle: {e}")
        raise
