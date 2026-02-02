"""Stakeholder Engagement Calculator

This module provides automatic calculation of stakeholder engagement levels
based on interaction signals from stakeholder_insights table.

Engagement Level Rules (Sticky - only demote on explicit negative signals):
- Champion: High engagement with commitments/strong support
- Supporter: Regular engagement with positive signals
- Neutral: Default level, some interaction
- Skeptic: Unresolved concerns/objections
- Blocker: Persistent unresolved objections

Architecture:
- Weekly scheduled calculation via engagement_scheduler.py
- Collects signals from stakeholder_insights and stakeholders tables
- Records history in engagement_level_history for trend analytics
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from database import get_supabase
from logger_config import get_logger

logger = get_logger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class EngagementSignals:
    """Signals collected for engagement level calculation."""

    stakeholder_id: str
    current_level: str

    # Interaction metrics
    total_interactions: int
    days_since_contact: Optional[int]

    # Positive signals (from stakeholder_insights)
    enthusiasm_count: int
    support_count: int
    commitment_count: int

    # Negative signals (from stakeholder_insights)
    concern_count: int
    objection_count: int
    unresolved_concern_count: int
    unresolved_objection_count: int

    # Derived metrics
    @property
    def positive_count(self) -> int:
        return self.enthusiasm_count + self.support_count + self.commitment_count

    @property
    def negative_count(self) -> int:
        return self.concern_count + self.objection_count

    @property
    def total_insights(self) -> int:
        return self.positive_count + self.negative_count

    @property
    def positive_ratio(self) -> float:
        if self.total_insights == 0:
            return 0.5  # Neutral if no insights
        return self.positive_count / self.total_insights

    def to_dict(self) -> dict:
        """Convert signals to dictionary for storage."""
        return {
            "total_interactions": self.total_interactions,
            "days_since_contact": self.days_since_contact,
            "enthusiasm_count": self.enthusiasm_count,
            "support_count": self.support_count,
            "commitment_count": self.commitment_count,
            "concern_count": self.concern_count,
            "objection_count": self.objection_count,
            "unresolved_concern_count": self.unresolved_concern_count,
            "unresolved_objection_count": self.unresolved_objection_count,
            "positive_ratio": round(self.positive_ratio, 2),
            "positive_count": self.positive_count,
            "negative_count": self.negative_count,
        }


@dataclass
class EngagementResult:
    """Result of an engagement level calculation."""

    stakeholder_id: str
    new_level: str
    previous_level: str
    reason: str
    signals: dict
    changed: bool


# ============================================================================
# ENGAGEMENT LEVEL HIERARCHY
# ============================================================================

ENGAGEMENT_LEVELS = ["blocker", "skeptic", "neutral", "supporter", "champion"]


def level_rank(level: str) -> int:
    """Get numeric rank of engagement level (higher = better)."""
    try:
        return ENGAGEMENT_LEVELS.index(level.lower())
    except ValueError:
        return 2  # Default to neutral


def is_promotion(old_level: str, new_level: str) -> bool:
    """Check if level change is a promotion."""
    return level_rank(new_level) > level_rank(old_level)


def is_demotion(old_level: str, new_level: str) -> bool:
    """Check if level change is a demotion."""
    return level_rank(new_level) < level_rank(old_level)


# ============================================================================
# ENGAGEMENT CALCULATOR
# ============================================================================


class EngagementCalculator:
    """Calculates stakeholder engagement levels based on interaction signals.

    Uses "sticky" level logic:
    - Promotion requires positive signals (interactions + positive insights)
    - Demotion requires explicit negative signals (unresolved objections)
    - Levels don't decay with inactivity alone
    """

    def __init__(self, supabase=None):
        self.supabase = supabase or get_supabase()

    async def collect_signals(self, stakeholder_id: str) -> EngagementSignals:
        """Collect all signals for engagement calculation.

        Queries:
        - stakeholders table for current level and interaction metrics
        - stakeholder_insights table for insight type counts
        """
        # Get stakeholder data
        stakeholder_result = (
            self.supabase.table("stakeholders")
            .select("engagement_level, total_interactions, last_interaction")
            .eq("id", stakeholder_id)
            .single()
            .execute()
        )

        if not stakeholder_result.data:
            raise ValueError(f"Stakeholder {stakeholder_id} not found")

        stakeholder = stakeholder_result.data
        current_level = stakeholder.get("engagement_level", "neutral") or "neutral"
        total_interactions = stakeholder.get("total_interactions", 0) or 0

        # Calculate days since last contact
        days_since_contact = None
        last_interaction = stakeholder.get("last_interaction")
        if last_interaction:
            try:
                last_dt = datetime.fromisoformat(last_interaction.replace("Z", "+00:00"))
                now = datetime.now(timezone.utc)
                days_since_contact = (now - last_dt).days
            except (ValueError, TypeError):
                pass

        # Count insights by type
        insights_result = (
            self.supabase.table("stakeholder_insights")
            .select("insight_type, is_resolved")
            .eq("stakeholder_id", stakeholder_id)
            .execute()
        )

        insights = insights_result.data or []

        # Initialize counters
        enthusiasm_count = 0
        support_count = 0
        commitment_count = 0
        concern_count = 0
        objection_count = 0
        unresolved_concern_count = 0
        unresolved_objection_count = 0

        for insight in insights:
            insight_type = insight.get("insight_type", "").lower()
            is_resolved = insight.get("is_resolved", False)

            if insight_type == "enthusiasm":
                enthusiasm_count += 1
            elif insight_type == "support":
                support_count += 1
            elif insight_type == "commitment":
                commitment_count += 1
            elif insight_type == "concern":
                concern_count += 1
                if not is_resolved:
                    unresolved_concern_count += 1
            elif insight_type == "objection":
                objection_count += 1
                if not is_resolved:
                    unresolved_objection_count += 1

        return EngagementSignals(
            stakeholder_id=stakeholder_id,
            current_level=current_level,
            total_interactions=total_interactions,
            days_since_contact=days_since_contact,
            enthusiasm_count=enthusiasm_count,
            support_count=support_count,
            commitment_count=commitment_count,
            concern_count=concern_count,
            objection_count=objection_count,
            unresolved_concern_count=unresolved_concern_count,
            unresolved_objection_count=unresolved_objection_count,
        )

    def calculate_level(self, signals: EngagementSignals) -> tuple[str, str]:
        """Calculate engagement level from signals using sticky rules.

        Returns:
            tuple: (new_level, reason)

        Rules (sticky - only demote on explicit negative signals):

        BLOCKER (demotion only):
        - 3+ unresolved objections OR explicit blocking behavior

        SKEPTIC (demotion or promotion from blocker):
        - 1+ unresolved objection
        - Promotion from blocker: blocking concerns resolved

        NEUTRAL (default):
        - No strong signals either way
        - Demotion from supporter: unresolved concerns >= 2

        SUPPORTER (promotion from neutral):
        - interactions >= 3 AND positive_ratio > 0.5
        - Demotion from champion: objections > support_count

        CHAMPION (promotion only):
        - interactions >= 5 AND (commitments >= 1 OR support >= 3)
        """
        current = signals.current_level.lower()
        current_rank = level_rank(current)

        # Check for BLOCKER conditions (severe negative signals)
        if signals.unresolved_objection_count >= 3:
            return "blocker", f"3+ unresolved objections ({signals.unresolved_objection_count})"

        # Check for SKEPTIC conditions
        if signals.unresolved_objection_count >= 1:
            # Allow demotion to skeptic from any level
            if current_rank > level_rank("skeptic"):
                return (
                    "skeptic",
                    f"Unresolved objection detected ({signals.unresolved_objection_count})",
                )
            # Keep at skeptic if already there or lower
            if current_rank <= level_rank("skeptic"):
                return current, "Maintaining current level"

        # If blocker with resolved concerns, can promote to skeptic
        if current == "blocker" and signals.unresolved_objection_count == 0:
            return "skeptic", "Blocking concerns resolved"

        # Check for demotion from SUPPORTER/CHAMPION to NEUTRAL
        if current_rank >= level_rank("supporter"):
            if signals.unresolved_concern_count >= 2:
                return (
                    "neutral",
                    f"Multiple unresolved concerns ({signals.unresolved_concern_count})",
                )

        # Check for demotion from CHAMPION to SUPPORTER
        if current == "champion":
            if signals.objection_count > signals.support_count:
                return (
                    "supporter",
                    f"Objections ({signals.objection_count}) exceed support ({signals.support_count})",
                )

        # Check for promotion to CHAMPION
        if signals.total_interactions >= 5:
            if signals.commitment_count >= 1 or signals.support_count >= 3:
                if current_rank < level_rank("champion"):
                    reason_parts = []
                    if signals.commitment_count >= 1:
                        reason_parts.append(f"{signals.commitment_count} commitment(s)")
                    if signals.support_count >= 3:
                        reason_parts.append(f"{signals.support_count} support signals")
                    return "champion", f"High engagement: {', '.join(reason_parts)}"

        # Check for promotion to SUPPORTER
        if signals.total_interactions >= 3 and signals.positive_ratio > 0.5:
            if current_rank < level_rank("supporter"):
                return (
                    "supporter",
                    f"Regular engagement with {signals.positive_ratio:.0%} positive signals",
                )

        # No change - maintain current level
        return current, "Maintaining current level (no qualifying signals for change)"

    async def calculate_for_stakeholder(
        self, stakeholder_id: str, client_id: str, calculation_type: str = "scheduled"
    ) -> EngagementResult:
        """Calculate and update engagement for a single stakeholder.

        Args:
            stakeholder_id: UUID of stakeholder
            client_id: UUID of client (for history record)
            calculation_type: 'scheduled', 'manual', or 'trigger'

        Returns:
            EngagementResult with new level and change status
        """
        # Collect signals
        signals = await self.collect_signals(stakeholder_id)

        # Calculate new level
        new_level, reason = self.calculate_level(signals)
        previous_level = signals.current_level
        changed = new_level.lower() != previous_level.lower()

        # Update stakeholder if changed
        if changed:
            self.supabase.table("stakeholders").update(
                {
                    "engagement_level": new_level,
                    "last_engagement_calculated": datetime.now(timezone.utc).isoformat(),
                }
            ).eq("id", stakeholder_id).execute()

            logger.info(
                f"Engagement changed: {stakeholder_id} {previous_level} -> {new_level} ({reason})"
            )
        else:
            # Update timestamp even if no change
            self.supabase.table("stakeholders").update(
                {
                    "last_engagement_calculated": datetime.now(timezone.utc).isoformat(),
                }
            ).eq("id", stakeholder_id).execute()

        # Record in history (always, for trend tracking)
        self.supabase.table("engagement_level_history").insert(
            {
                "id": str(uuid4()),
                "stakeholder_id": stakeholder_id,
                "client_id": client_id,
                "engagement_level": new_level,
                "previous_level": previous_level if changed else None,
                "calculation_reason": reason,
                "signals": signals.to_dict(),
                "calculation_type": calculation_type,
            }
        ).execute()

        return EngagementResult(
            stakeholder_id=stakeholder_id,
            new_level=new_level,
            previous_level=previous_level,
            reason=reason,
            signals=signals.to_dict(),
            changed=changed,
        )

    async def calculate_for_client(
        self, client_id: str, calculation_type: str = "scheduled"
    ) -> dict:
        """Calculate engagement for all stakeholders in a client.

        Returns:
            dict with summary: {total, changed, promotions, demotions, errors}
        """
        # Get all stakeholders for client
        result = (
            self.supabase.table("stakeholders").select("id").eq("client_id", client_id).execute()
        )

        stakeholders = result.data or []

        summary = {
            "client_id": client_id,
            "total": len(stakeholders),
            "processed": 0,
            "changed": 0,
            "promotions": 0,
            "demotions": 0,
            "errors": 0,
            "changes": [],
        }

        for stakeholder in stakeholders:
            stakeholder_id = stakeholder["id"]
            try:
                eng_result = await self.calculate_for_stakeholder(
                    stakeholder_id=stakeholder_id,
                    client_id=client_id,
                    calculation_type=calculation_type,
                )
                summary["processed"] += 1

                if eng_result.changed:
                    summary["changed"] += 1
                    if is_promotion(eng_result.previous_level, eng_result.new_level):
                        summary["promotions"] += 1
                    elif is_demotion(eng_result.previous_level, eng_result.new_level):
                        summary["demotions"] += 1

                    summary["changes"].append(
                        {
                            "stakeholder_id": stakeholder_id,
                            "previous_level": eng_result.previous_level,
                            "new_level": eng_result.new_level,
                            "reason": eng_result.reason,
                        }
                    )

            except Exception as e:
                logger.error(f"Error calculating engagement for {stakeholder_id}: {e}")
                summary["errors"] += 1

        return summary

    async def calculate_all_clients(self) -> dict:
        """Calculate engagement for all active clients.

        Returns:
            dict with overall summary and per-client results
        """
        # Get all clients with stakeholders
        result = self.supabase.table("stakeholders").select("client_id").execute()

        client_ids = list({row["client_id"] for row in result.data if row.get("client_id")})

        overall = {
            "clients_processed": 0,
            "total_stakeholders": 0,
            "total_changed": 0,
            "total_promotions": 0,
            "total_demotions": 0,
            "total_errors": 0,
            "client_results": [],
        }

        for client_id in client_ids:
            try:
                client_summary = await self.calculate_for_client(client_id)
                overall["clients_processed"] += 1
                overall["total_stakeholders"] += client_summary["total"]
                overall["total_changed"] += client_summary["changed"]
                overall["total_promotions"] += client_summary["promotions"]
                overall["total_demotions"] += client_summary["demotions"]
                overall["total_errors"] += client_summary["errors"]
                overall["client_results"].append(client_summary)

            except Exception as e:
                logger.error(f"Error processing client {client_id}: {e}")
                overall["total_errors"] += 1

        return overall
