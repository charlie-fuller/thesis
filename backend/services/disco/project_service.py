"""DISCo Project Service.

Handles operations related to projects linked to DISCo initiatives.
"""

from typing import Dict, Optional

import pb_client as pb
import repositories.disco as disco_repo
import repositories.projects as projects_repo
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
    result = pb.get_first(
        "disco_initiatives",
        filter=f"name='{pb.escape_filter(initiative_id)}'",
    )

    if not result:
        return None

    return result["id"]


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
        # PocketBase doesn't support contains() on arrays directly,
        # so we fetch all projects and filter in Python
        all_projects = projects_repo.list_projects(sort="-created")

        projects = [
            p for p in all_projects
            if resolved_id in (p.get("initiative_ids") or [])
        ]

        if status:
            projects = [p for p in projects if p.get("status") == status]

        # Sort by created descending
        projects.sort(key=lambda p: p.get("created", ""), reverse=True)

        logger.info(f"Found {len(projects)} projects for initiative {resolved_id}")
        return {"projects": projects, "count": len(projects)}

    except Exception as e:
        logger.error(f"Error getting initiative projects: {e}")
        raise


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
    logger.info(f"Creating project from PRD {prd_id}")

    try:
        # Get PRD title for reference
        prd = disco_repo.get_prd(prd_id)
        prd_title = prd.get("title") if prd else "Unknown PRD"

        # Prepare project record
        project_record = {
            "project_code": project_data.get("project_code", f"PRD{prd_id[:4].upper()}" if prd_id else "PRD"),
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

        result = projects_repo.create_project(project_record)

        if not result:
            raise Exception("Failed to create project")

        logger.info(f"Created project {result['id']} from PRD {prd_id}")
        return result

    except Exception as e:
        logger.error(f"Error creating project from PRD: {e}")
        raise


# Score mapping: HIGH/MEDIUM/LOW -> numeric 1-5
_SCORE_MAP = {"HIGH": 5, "MEDIUM": 3, "LOW": 1}
_INVERSE_SCORE_MAP = {"HIGH": 1, "MEDIUM": 3, "LOW": 5}


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
        client_id: User's client ID (unused in PocketBase)

    Returns:
        Created project record
    """
    bundle_id = bundle["id"]
    logger.info(f"Creating project from bundle {bundle_id}")

    try:
        # Map scores
        roi_potential = _SCORE_MAP.get(bundle.get("impact_score"), 3)
        implementation_effort = _INVERSE_SCORE_MAP.get(bundle.get("feasibility_score"), 3)
        strategic_alignment = _SCORE_MAP.get(bundle.get("urgency_score"), 3)

        bundle_name = bundle.get("name", "Untitled Bundle")
        project_record = {
            "project_code": bundle_id[:4].upper() if bundle_id else "BNDL",
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

        result = projects_repo.create_project(project_record)

        if not result:
            raise Exception("Failed to create project")

        logger.info(f"Created project {result['id']} from bundle {bundle_id}")
        return result

    except Exception as e:
        logger.error(f"Error creating project from bundle: {e}")
        raise
