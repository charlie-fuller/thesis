"""Operator Tools Service

Provides data retrieval functions for the Operator agent to access
project-triage data: opportunities, metrics, stakeholder information.
"""

import logging
from typing import Any, Dict, List, Optional

from supabase import Client

logger = logging.getLogger(__name__)


class OperatorTools:
    """Service class providing triage data access for the Operator agent."""

    def __init__(self, supabase: Client, client_id: str):
        self.supabase = supabase
        self.client_id = client_id

    def get_opportunity_summary(self) -> Dict[str, Any]:
        """Get a high-level summary of the AI opportunity pipeline.

        Returns:
            Summary dict with tier counts, status breakdown, top opportunities.
        """
        try:
            result = (
                self.supabase.table("ai_projects")
                .select("id, opportunity_code, title, total_score, tier, status, department")
                .eq("client_id", self.client_id)
                .order("total_score", desc=True)
                .execute()
            )

            opportunities = result.data or []

            # Count by tier
            tier_counts = {1: 0, 2: 0, 3: 0, 4: 0}
            for opp in opportunities:
                tier = opp.get("tier", 4)
                tier_counts[tier] = tier_counts.get(tier, 0) + 1

            # Count by status
            status_counts = {}
            for opp in opportunities:
                status = opp.get("status", "identified")
                status_counts[status] = status_counts.get(status, 0) + 1

            # Top 5 opportunities
            top_opps = [
                {
                    "code": o["opportunity_code"],
                    "title": o["title"],
                    "score": o["total_score"],
                    "tier": o["tier"],
                    "status": o["status"],
                }
                for o in opportunities[:5]
            ]

            return {
                "total": len(opportunities),
                "by_tier": tier_counts,
                "by_status": status_counts,
                "top_opportunities": top_opps,
            }

        except Exception as e:
            logger.error(f"Error getting opportunity summary: {e}")
            return {
                "total": 0,
                "by_tier": {},
                "by_status": {},
                "top_opportunities": [],
                "error": str(e),
            }

    def get_opportunities_by_department(self, department: str) -> List[Dict[str, Any]]:
        """Get opportunities for a specific department.

        Args:
            department: Department name (e.g., 'finance', 'legal', 'hr')

        Returns:
            List of opportunities for that department.
        """
        try:
            result = (
                self.supabase.table("ai_projects")
                .select(
                    "id, opportunity_code, title, total_score, tier, status, current_state, desired_state, next_step"
                )
                .eq("client_id", self.client_id)
                .eq("department", department.lower())
                .order("total_score", desc=True)
                .execute()
            )

            return result.data or []

        except Exception as e:
            logger.error(f"Error getting opportunities by department: {e}")
            return []

    def get_blocked_opportunities(self) -> List[Dict[str, Any]]:
        """Get all blocked opportunities that need attention.

        Returns:
            List of blocked opportunities with blockers.
        """
        try:
            result = (
                self.supabase.table("ai_projects")
                .select("id, opportunity_code, title, department, total_score, blockers, next_step")
                .eq("client_id", self.client_id)
                .eq("status", "blocked")
                .execute()
            )

            return result.data or []

        except Exception as e:
            logger.error(f"Error getting blocked opportunities: {e}")
            return []

    def get_metrics_validation_gaps(self) -> Dict[str, Any]:
        """Get metrics that need validation (red or yellow status).

        Returns:
            Dict with unvalidated metrics grouped by stakeholder.
        """
        try:
            result = (
                self.supabase.table("stakeholder_metrics")
                .select("*, stakeholders(id, name, department)")
                .eq("client_id", self.client_id)
                .in_("validation_status", ["red", "yellow"])
                .execute()
            )

            metrics = result.data or []

            # Group by stakeholder
            by_stakeholder = {}
            for m in metrics:
                stakeholder = m.get("stakeholders", {})
                s_name = stakeholder.get("name", "Unknown") if stakeholder else "Unknown"
                if s_name not in by_stakeholder:
                    by_stakeholder[s_name] = []
                by_stakeholder[s_name].append(
                    {
                        "metric": m["metric_name"],
                        "status": m["validation_status"],
                        "questions": m.get("questions_to_confirm") or [],
                    }
                )

            # Count by status
            red_count = sum(1 for m in metrics if m.get("validation_status") == "red")
            yellow_count = sum(1 for m in metrics if m.get("validation_status") == "yellow")

            return {
                "total_unvalidated": len(metrics),
                "red_count": red_count,
                "yellow_count": yellow_count,
                "by_stakeholder": by_stakeholder,
            }

        except Exception as e:
            logger.error(f"Error getting metrics validation gaps: {e}")
            return {
                "total_unvalidated": 0,
                "red_count": 0,
                "yellow_count": 0,
                "by_stakeholder": {},
                "error": str(e),
            }

    def get_stakeholder_meeting_prep(self, stakeholder_name: str) -> Optional[Dict[str, Any]]:
        """Get meeting prep context for a stakeholder by name.

        Args:
            stakeholder_name: Name of the stakeholder (partial match supported)

        Returns:
            Meeting prep data or None if not found.
        """
        try:
            # Find stakeholder by name (partial match)
            stakeholder_result = (
                self.supabase.table("stakeholders")
                .select("*")
                .eq("client_id", self.client_id)
                .ilike("name", f"%{stakeholder_name}%")
                .limit(1)
                .execute()
            )

            if not stakeholder_result.data:
                return None

            stakeholder = stakeholder_result.data[0]
            stakeholder_id = stakeholder["id"]

            # Get metrics
            metrics_result = (
                self.supabase.table("stakeholder_metrics")
                .select("metric_name, current_value, target_value, validation_status, unit")
                .eq("stakeholder_id", stakeholder_id)
                .execute()
            )

            # Get linked opportunities
            opps_result = (
                self.supabase.table("opportunity_stakeholder_link")
                .select(
                    "role, ai_projects(opportunity_code, title, total_score, tier, status, next_step)"
                )
                .eq("stakeholder_id", stakeholder_id)
                .execute()
            )

            # Also get owned opportunities
            owned_opps_result = (
                self.supabase.table("ai_projects")
                .select("opportunity_code, title, total_score, tier, status, next_step")
                .eq("owner_stakeholder_id", stakeholder_id)
                .execute()
            )

            # Format response
            linked_opps = []
            for link in opps_result.data or []:
                opp = link.get("ai_projects")
                if opp:
                    linked_opps.append(
                        {
                            **opp,
                            "role": link.get("role", "involved"),
                        }
                    )

            for opp in owned_opps_result.data or []:
                if not any(lo["opportunity_code"] == opp["opportunity_code"] for lo in linked_opps):
                    linked_opps.append({**opp, "role": "owner"})

            return {
                "stakeholder": {
                    "name": stakeholder["name"],
                    "role": stakeholder.get("role"),
                    "department": stakeholder.get("department"),
                    "engagement_level": stakeholder.get("engagement_level"),
                    "priority_level": stakeholder.get("priority_level"),
                    "relationship_status": stakeholder.get("relationship_status"),
                    "communication_style": stakeholder.get("communication_style"),
                    "pain_points": stakeholder.get("pain_points") or [],
                    "win_conditions": stakeholder.get("win_conditions") or [],
                    "ai_priorities": stakeholder.get("ai_priorities") or [],
                    "open_questions": stakeholder.get("open_questions") or [],
                },
                "metrics": [
                    {
                        "name": m["metric_name"],
                        "current": m.get("current_value"),
                        "target": m.get("target_value"),
                        "status": m.get("validation_status", "red"),
                        "unit": m.get("unit"),
                    }
                    for m in (metrics_result.data or [])
                ],
                "opportunities": sorted(
                    linked_opps, key=lambda x: x.get("total_score", 0), reverse=True
                ),
            }

        except Exception as e:
            logger.error(f"Error getting stakeholder meeting prep: {e}")
            return None

    def get_tier1_focus_areas(self) -> Dict[str, Any]:
        """Get Tier 1 strategic priorities for focus.

        Returns:
            Dict with Tier 1 opportunities and their next steps.
        """
        try:
            result = (
                self.supabase.table("ai_projects")
                .select("*, stakeholders:owner_stakeholder_id(name)")
                .eq("client_id", self.client_id)
                .eq("tier", 1)
                .order("total_score", desc=True)
                .execute()
            )

            opportunities = result.data or []

            return {
                "count": len(opportunities),
                "opportunities": [
                    {
                        "code": o["opportunity_code"],
                        "title": o["title"],
                        "department": o.get("department"),
                        "owner": o.get("stakeholders", {}).get("name")
                        if o.get("stakeholders")
                        else None,
                        "status": o.get("status"),
                        "score": o.get("total_score"),
                        "next_step": o.get("next_step"),
                        "blockers": o.get("blockers") or [],
                    }
                    for o in opportunities
                ],
            }

        except Exception as e:
            logger.error(f"Error getting Tier 1 focus areas: {e}")
            return {"count": 0, "opportunities": [], "error": str(e)}

    def format_context_injection(self) -> str:
        """Format triage data as context injection for the Operator agent.

        Returns:
            Formatted string to inject into agent context.
        """
        summary = self.get_opportunity_summary()
        gaps = self.get_metrics_validation_gaps()
        blocked = self.get_blocked_opportunities()
        tier1 = self.get_tier1_focus_areas()

        lines = [
            "<project_triage_context>",
            "",
            "## AI Opportunity Pipeline Summary",
            f"Total Opportunities: {summary.get('total', 0)}",
            f"- Tier 1 (Strategic): {summary.get('by_tier', {}).get(1, 0)}",
            f"- Tier 2 (High Impact): {summary.get('by_tier', {}).get(2, 0)}",
            f"- Tier 3 (Medium): {summary.get('by_tier', {}).get(3, 0)}",
            f"- Tier 4 (Backlog): {summary.get('by_tier', {}).get(4, 0)}",
            "",
        ]

        # Status breakdown
        status_counts = summary.get("by_status", {})
        if status_counts:
            lines.append("Status Breakdown:")
            for status, count in status_counts.items():
                lines.append(f"- {status.capitalize()}: {count}")
            lines.append("")

        # Blocked opportunities
        if blocked:
            lines.append(f"## Blocked Opportunities ({len(blocked)} items)")
            for b in blocked:
                lines.append(f"- {b['opportunity_code']}: {b['title']}")
                if b.get("blockers"):
                    for blocker in b["blockers"][:2]:
                        lines.append(f"  - Blocker: {blocker}")
            lines.append("")

        # Metrics validation gaps
        if gaps.get("total_unvalidated", 0) > 0:
            lines.append(f"## Metrics Needing Validation ({gaps['total_unvalidated']} total)")
            lines.append(f"- Red (needs validation): {gaps.get('red_count', 0)}")
            lines.append(f"- Yellow (partial): {gaps.get('yellow_count', 0)}")
            lines.append("")

        # Top Tier 1 priorities
        if tier1.get("count", 0) > 0:
            lines.append(f"## Tier 1 Strategic Priorities ({tier1['count']} items)")
            for t in tier1.get("opportunities", [])[:5]:
                lines.append(f"- {t['code']}: {t['title']} ({t['department']}) - {t['status']}")
                if t.get("next_step"):
                    lines.append(f"  Next: {t['next_step']}")
            lines.append("")

        lines.append("</project_triage_context>")

        return "\n".join(lines)
