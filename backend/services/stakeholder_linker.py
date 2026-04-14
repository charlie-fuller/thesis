"""Stakeholder Linker Service.

Links extracted stakeholders to related opportunities and tasks based on:
- Department/role keyword matching
- Name matching in assignees
- Content similarity in descriptions
"""

import logging

import pb_client as pb
from repositories import projects as projects_repo
from services.stakeholder_extractor import ExtractedStakeholder

logger = logging.getLogger(__name__)


class StakeholderLinker:
    """Links stakeholders to related opportunities and tasks."""

    def __init__(self, supabase_client=None):
        pass  # No longer needs supabase client

    async def find_related_entities(
        self, stakeholder: ExtractedStakeholder, client_id: str
    ) -> tuple[list[str], list[str]]:
        """Find opportunities and tasks related to this stakeholder.

        Args:
            stakeholder: The extracted stakeholder
            client_id: Client ID to scope the search

        Returns:
            Tuple of (opportunity_ids, task_ids)
        """
        opportunity_ids = await self._find_related_opportunities(stakeholder, client_id)
        task_ids = await self._find_related_tasks(stakeholder, client_id)

        return opportunity_ids, task_ids

    async def _find_related_opportunities(self, stakeholder: ExtractedStakeholder, client_id: str) -> list[str]:
        """Find opportunities related to this stakeholder."""
        opportunity_ids = []

        try:
            # Search by department if available
            if stakeholder.department:
                esc_dept = pb.escape_filter(stakeholder.department)
                dept_projects = pb.get_all(
                    "ai_projects",
                    filter=f"department~'{esc_dept}'",
                )
                opportunity_ids.extend([o["id"] for o in dept_projects])

            # Search by stakeholder name in owner_name
            if stakeholder.name:
                esc_name = pb.escape_filter(stakeholder.name)
                name_projects = pb.get_all(
                    "ai_projects",
                    filter=f"owner_name~'{esc_name}'",
                )
                for o in name_projects:
                    if o["id"] not in opportunity_ids:
                        opportunity_ids.append(o["id"])

            # Search by role keywords in title/description
            if stakeholder.role:
                role_keywords = self._extract_keywords(stakeholder.role)
                for keyword in role_keywords[:3]:  # Limit to top 3 keywords
                    if len(keyword) < 3:
                        continue

                    esc_kw = pb.escape_filter(keyword)
                    role_projects = pb.get_all(
                        "ai_projects",
                        filter=f"(title~'{esc_kw}' || description~'{esc_kw}')",
                    )
                    for o in role_projects[:5]:
                        if o["id"] not in opportunity_ids:
                            opportunity_ids.append(o["id"])

            # Limit to prevent excessive linking
            return opportunity_ids[:10]

        except Exception as e:
            logger.error(f"Error finding related opportunities: {e}")
            return []

    async def _find_related_tasks(self, stakeholder: ExtractedStakeholder, client_id: str) -> list[str]:
        """Find tasks related to this stakeholder."""
        task_ids = []

        try:
            # Search by assignee name
            if stakeholder.name:
                # Try exact and partial matches
                name_parts = stakeholder.name.lower().split()

                for name_part in name_parts:
                    if len(name_part) < 3:
                        continue

                    esc_part = pb.escape_filter(name_part)
                    assignee_tasks = pb.get_all(
                        "project_tasks",
                        filter=f"assignee_name~'{esc_part}'",
                    )
                    for t in assignee_tasks[:10]:
                        if t["id"] not in task_ids:
                            task_ids.append(t["id"])

            # Search by stakeholder_name field in task_candidates that were accepted
            if stakeholder.name:
                esc_name = pb.escape_filter(stakeholder.name)
                stakeholder_tasks = pb.get_all(
                    "project_tasks",
                    filter=f"stakeholder_name~'{esc_name}'",
                )
                for t in stakeholder_tasks[:10]:
                    if t["id"] not in task_ids:
                        task_ids.append(t["id"])

            # Limit to prevent excessive linking
            return task_ids[:10]

        except Exception as e:
            logger.error(f"Error finding related tasks: {e}")
            return []

    def _extract_keywords(self, text: str) -> list[str]:
        """Extract meaningful keywords from text."""
        if not text:
            return []

        # Common stop words to filter out
        stop_words = {
            "the",
            "a",
            "an",
            "of",
            "to",
            "for",
            "and",
            "or",
            "in",
            "on",
            "at",
            "by",
            "with",
            "from",
            "as",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "must",
            "vp",
            "svp",
            "evp",
            "avp",
            "director",
            "manager",
            "lead",
            "head",
            "senior",
            "junior",
            "chief",
            "officer",
            "executive",
        }

        # Split and filter
        words = text.lower().split()
        keywords = [w.strip(".,;:-()[]") for w in words if w.lower() not in stop_words and len(w) > 2]

        return keywords


async def link_stakeholder_to_entities(
    supabase_client=None, stakeholder_id: str = "", opportunity_ids: list[str] = None, task_ids: list[str] = None
) -> dict:
    """Create actual links between a stakeholder and opportunities/tasks.

    Called when a stakeholder candidate is accepted.
    Uses the opportunity_stakeholder_link table for opportunity linking
    and adds stakeholder_id to tasks.
    """
    opportunity_ids = opportunity_ids or []
    task_ids = task_ids or []
    results = {"opportunities_linked": 0, "tasks_linked": 0, "errors": []}

    # Link to opportunities using the link table
    esc_sid = pb.escape_filter(stakeholder_id)
    for opp_id in opportunity_ids:
        try:
            # Check if link already exists
            esc_oid = pb.escape_filter(opp_id)
            existing = pb.get_all(
                "opportunity_stakeholder_link",
                filter=f"opportunity_id='{esc_oid}' && stakeholder_id='{esc_sid}'",
            )

            if not existing:
                # Create new link
                pb.create_record("opportunity_stakeholder_link", {
                    "opportunity_id": opp_id,
                    "stakeholder_id": stakeholder_id,
                    "role": "stakeholder",
                    "notes": "Auto-linked from meeting extraction",
                })

                results["opportunities_linked"] += 1

        except Exception as e:
            logger.error(f"Error linking stakeholder to opportunity {opp_id}: {e}")
            results["errors"].append(f"Opportunity {opp_id}: {str(e)}")

    # Link to tasks (update stakeholder_id column if available)
    for task_id in task_ids:
        try:
            task = pb.get_record("project_tasks", task_id)
            if task and not task.get("stakeholder_id"):
                pb.update_record("project_tasks", task_id, {"stakeholder_id": stakeholder_id})
            results["tasks_linked"] += 1

        except Exception as e:
            # Column might not exist - that's OK
            logger.debug(f"Could not link stakeholder to task {task_id}: {e}")

    return results
