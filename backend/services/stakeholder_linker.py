"""Stakeholder Linker Service

Links extracted stakeholders to related opportunities and tasks based on:
- Department/role keyword matching
- Name matching in assignees
- Content similarity in descriptions
"""

import logging

from services.stakeholder_extractor import ExtractedStakeholder

logger = logging.getLogger(__name__)


class StakeholderLinker:
    """Links stakeholders to related opportunities and tasks."""

    def __init__(self, supabase_client):
        self.supabase = supabase_client

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

    async def _find_related_opportunities(
        self, stakeholder: ExtractedStakeholder, client_id: str
    ) -> list[str]:
        """Find opportunities related to this stakeholder."""
        opportunity_ids = []

        try:
            # Search by department if available
            if stakeholder.department:
                dept_result = (
                    self.supabase.table("ai_projects")
                    .select("id")
                    .eq("client_id", client_id)
                    .ilike("department", f"%{stakeholder.department}%")
                    .execute()
                )

                if dept_result.data:
                    opportunity_ids.extend([o["id"] for o in dept_result.data])

            # Search by stakeholder name in owner_name
            if stakeholder.name:
                name_result = (
                    self.supabase.table("ai_projects")
                    .select("id")
                    .eq("client_id", client_id)
                    .ilike("owner_name", f"%{stakeholder.name}%")
                    .execute()
                )

                if name_result.data:
                    for o in name_result.data:
                        if o["id"] not in opportunity_ids:
                            opportunity_ids.append(o["id"])

            # Search by role keywords in title/description
            if stakeholder.role:
                role_keywords = self._extract_keywords(stakeholder.role)
                for keyword in role_keywords[:3]:  # Limit to top 3 keywords
                    if len(keyword) < 3:
                        continue

                    role_result = (
                        self.supabase.table("ai_projects")
                        .select("id")
                        .eq("client_id", client_id)
                        .or_(f"title.ilike.%{keyword}%,description.ilike.%{keyword}%")
                        .limit(5)
                        .execute()
                    )

                    if role_result.data:
                        for o in role_result.data:
                            if o["id"] not in opportunity_ids:
                                opportunity_ids.append(o["id"])

            # Limit to prevent excessive linking
            return opportunity_ids[:10]

        except Exception as e:
            logger.error(f"Error finding related opportunities: {e}")
            return []

    async def _find_related_tasks(
        self, stakeholder: ExtractedStakeholder, client_id: str
    ) -> list[str]:
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

                    assignee_result = (
                        self.supabase.table("project_tasks")
                        .select("id")
                        .eq("client_id", client_id)
                        .ilike("assignee_name", f"%{name_part}%")
                        .limit(10)
                        .execute()
                    )

                    if assignee_result.data:
                        for t in assignee_result.data:
                            if t["id"] not in task_ids:
                                task_ids.append(t["id"])

            # Search by stakeholder_name field in task_candidates that were accepted
            if stakeholder.name:
                stakeholder_result = (
                    self.supabase.table("project_tasks")
                    .select("id")
                    .eq("client_id", client_id)
                    .ilike("stakeholder_name", f"%{stakeholder.name}%")
                    .limit(10)
                    .execute()
                )

                if stakeholder_result.data:
                    for t in stakeholder_result.data:
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
        keywords = [
            w.strip(".,;:-()[]") for w in words if w.lower() not in stop_words and len(w) > 2
        ]

        return keywords


async def link_stakeholder_to_entities(
    supabase_client, stakeholder_id: str, opportunity_ids: list[str], task_ids: list[str]
) -> dict:
    """Create actual links between a stakeholder and opportunities/tasks.

    Called when a stakeholder candidate is accepted.
    Uses the opportunity_stakeholder_link table for opportunity linking
    and adds stakeholder_id to tasks.
    """
    results = {"opportunities_linked": 0, "tasks_linked": 0, "errors": []}

    # Link to opportunities using the link table
    for opp_id in opportunity_ids:
        try:
            # Check if link already exists
            existing = (
                supabase_client.table("opportunity_stakeholder_link")
                .select("id")
                .eq("opportunity_id", opp_id)
                .eq("stakeholder_id", stakeholder_id)
                .execute()
            )

            if not existing.data:
                # Create new link
                supabase_client.table("opportunity_stakeholder_link").insert(
                    {
                        "opportunity_id": opp_id,
                        "stakeholder_id": stakeholder_id,
                        "role": "stakeholder",
                        "notes": "Auto-linked from meeting extraction",
                    }
                ).execute()

                results["opportunities_linked"] += 1

        except Exception as e:
            logger.error(f"Error linking stakeholder to opportunity {opp_id}: {e}")
            results["errors"].append(f"Opportunity {opp_id}: {str(e)}")

    # Link to tasks (update stakeholder_id column if available)
    for task_id in task_ids:
        try:
            # Check if task has stakeholder_id column
            supabase_client.table("project_tasks").update({"stakeholder_id": stakeholder_id}).eq(
                "id", task_id
            ).is_("stakeholder_id", None).execute()

            results["tasks_linked"] += 1

        except Exception as e:
            # Column might not exist - that's OK
            logger.debug(f"Could not link stakeholder to task {task_id}: {e}")

    return results
