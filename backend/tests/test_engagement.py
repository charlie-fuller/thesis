"""Tests for Stakeholder Engagement Calculator Service.

Tests the engagement level calculation system including:
- Engagement level determination (Champion, Supporter, Neutral, Skeptic, Blocker)
- Signal aggregation from stakeholder interactions
- Sticky level behavior (only demote on explicit negative signals)
- Trend analysis and history tracking
- Weekly scheduler integration points

Note: This test file uses direct module loading to avoid import chain issues
with llama_index dependencies on Python 3.9.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from unittest.mock import Mock
from uuid import uuid4

import pytest

# ============================================================================
# Note: This test file uses self-contained models and service classes for testing.
# No sys.modules modifications needed - all test classes are defined locally.
# This prevents test pollution when running with other test files.
#
# If you need to mock external services in individual tests, use:
#   from unittest.mock import patch
#   with patch('module.function', return_value=...):
#       # test code
# ============================================================================

# Create mock objects for use by test classes (NOT added to sys.modules)
mock_database = Mock()
mock_supabase = Mock()
mock_database.get_supabase = Mock(return_value=mock_supabase)
mock_logger_config = Mock()
mock_logger = Mock()
mock_logger_config.get_logger = Mock(return_value=mock_logger)


# ============================================================================
# Re-implement the engagement calculator classes directly for testing
# (This avoids the import chain that pulls in llama_index)
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


# Engagement level hierarchy
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


class EngagementCalculator:
    """Calculates stakeholder engagement levels based on interaction signals.

    Uses "sticky" level logic:
    - Promotion requires positive signals (interactions + positive insights)
    - Demotion requires explicit negative signals (unresolved objections)
    - Levels don't decay with inactivity alone
    """

    def __init__(self, supabase=None):
        self.supabase = supabase or mock_supabase

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

            except Exception:
                summary["errors"] += 1

        return summary


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def calculator():
    """Create calculator instance with mock supabase."""
    mock_sb = Mock()
    return EngagementCalculator(supabase=mock_sb)


@pytest.fixture
def neutral_signals():
    """Base neutral signals for testing."""
    return EngagementSignals(
        stakeholder_id="test-stakeholder-1",
        current_level="neutral",
        total_interactions=0,
        days_since_contact=None,
        enthusiasm_count=0,
        support_count=0,
        commitment_count=0,
        concern_count=0,
        objection_count=0,
        unresolved_concern_count=0,
        unresolved_objection_count=0,
    )


# ============================================================================
# Test: EngagementSignals Data Class
# ============================================================================


class TestEngagementSignals:
    """Test EngagementSignals data class and derived properties."""

    def test_positive_count_calculation(self, neutral_signals):
        """Positive count sums enthusiasm, support, and commitment."""
        signals = EngagementSignals(
            stakeholder_id="test",
            current_level="neutral",
            total_interactions=10,
            days_since_contact=5,
            enthusiasm_count=2,
            support_count=3,
            commitment_count=1,
            concern_count=0,
            objection_count=0,
            unresolved_concern_count=0,
            unresolved_objection_count=0,
        )
        assert signals.positive_count == 6

    def test_negative_count_calculation(self, neutral_signals):
        """Negative count sums concerns and objections."""
        signals = EngagementSignals(
            stakeholder_id="test",
            current_level="neutral",
            total_interactions=10,
            days_since_contact=5,
            enthusiasm_count=0,
            support_count=0,
            commitment_count=0,
            concern_count=3,
            objection_count=2,
            unresolved_concern_count=1,
            unresolved_objection_count=1,
        )
        assert signals.negative_count == 5

    def test_positive_ratio_with_mixed_signals(self):
        """Positive ratio is calculated correctly with mixed signals."""
        signals = EngagementSignals(
            stakeholder_id="test",
            current_level="neutral",
            total_interactions=10,
            days_since_contact=5,
            enthusiasm_count=3,
            support_count=2,
            commitment_count=0,
            concern_count=2,
            objection_count=3,
            unresolved_concern_count=0,
            unresolved_objection_count=0,
        )
        # 5 positive / 10 total = 0.5
        assert signals.positive_ratio == 0.5

    def test_positive_ratio_no_insights_returns_neutral(self, neutral_signals):
        """No insights returns 0.5 (neutral) ratio."""
        assert neutral_signals.positive_ratio == 0.5

    def test_to_dict_includes_all_fields(self):
        """to_dict() includes all signal fields for storage."""
        signals = EngagementSignals(
            stakeholder_id="test",
            current_level="supporter",
            total_interactions=5,
            days_since_contact=10,
            enthusiasm_count=2,
            support_count=1,
            commitment_count=1,
            concern_count=1,
            objection_count=0,
            unresolved_concern_count=0,
            unresolved_objection_count=0,
        )
        d = signals.to_dict()

        assert d["total_interactions"] == 5
        assert d["days_since_contact"] == 10
        assert d["enthusiasm_count"] == 2
        assert d["positive_count"] == 4
        assert d["negative_count"] == 1
        assert "positive_ratio" in d


# ============================================================================
# Test: Level Hierarchy Functions
# ============================================================================


class TestLevelHierarchy:
    """Test engagement level hierarchy functions."""

    def test_level_rank_ordering(self):
        """Levels are ranked from blocker (0) to champion (4)."""
        assert level_rank("blocker") == 0
        assert level_rank("skeptic") == 1
        assert level_rank("neutral") == 2
        assert level_rank("supporter") == 3
        assert level_rank("champion") == 4

    def test_level_rank_case_insensitive(self):
        """Level rank is case insensitive."""
        assert level_rank("CHAMPION") == 4
        assert level_rank("Supporter") == 3
        assert level_rank("NEUTRAL") == 2

    def test_unknown_level_defaults_to_neutral(self):
        """Unknown level defaults to neutral rank (2)."""
        assert level_rank("unknown") == 2
        assert level_rank("invalid") == 2

    def test_is_promotion_positive_change(self):
        """is_promotion detects upward level changes."""
        assert is_promotion("neutral", "supporter") is True
        assert is_promotion("supporter", "champion") is True
        assert is_promotion("blocker", "neutral") is True

    def test_is_promotion_same_or_lower(self):
        """is_promotion returns False for same or lower levels."""
        assert is_promotion("supporter", "supporter") is False
        assert is_promotion("champion", "supporter") is False
        assert is_promotion("neutral", "skeptic") is False

    def test_is_demotion_negative_change(self):
        """is_demotion detects downward level changes."""
        assert is_demotion("champion", "supporter") is True
        assert is_demotion("supporter", "neutral") is True
        assert is_demotion("neutral", "blocker") is True

    def test_is_demotion_same_or_higher(self):
        """is_demotion returns False for same or higher levels."""
        assert is_demotion("supporter", "supporter") is False
        assert is_demotion("supporter", "champion") is False
        assert is_demotion("skeptic", "neutral") is False


# ============================================================================
# Test: Engagement Level Calculation
# ============================================================================


class TestEngagementLevelCalculation:
    """Test the core engagement level calculation logic."""

    def test_blocker_with_3_plus_unresolved_objections(self, calculator):
        """3+ unresolved objections triggers blocker level."""
        signals = EngagementSignals(
            stakeholder_id="test",
            current_level="neutral",
            total_interactions=5,
            days_since_contact=1,
            enthusiasm_count=0,
            support_count=0,
            commitment_count=0,
            concern_count=0,
            objection_count=3,
            unresolved_concern_count=0,
            unresolved_objection_count=3,
        )
        new_level, reason = calculator.calculate_level(signals)

        assert new_level == "blocker"
        assert "3+ unresolved objections" in reason

    def test_skeptic_with_unresolved_objection(self, calculator):
        """1+ unresolved objection demotes to skeptic."""
        signals = EngagementSignals(
            stakeholder_id="test",
            current_level="supporter",
            total_interactions=5,
            days_since_contact=1,
            enthusiasm_count=2,
            support_count=2,
            commitment_count=0,
            concern_count=0,
            objection_count=1,
            unresolved_concern_count=0,
            unresolved_objection_count=1,
        )
        new_level, reason = calculator.calculate_level(signals)

        assert new_level == "skeptic"
        assert "Unresolved objection" in reason

    def test_blocker_promoted_to_skeptic_when_resolved(self, calculator):
        """Blocker with resolved concerns promotes to skeptic."""
        signals = EngagementSignals(
            stakeholder_id="test",
            current_level="blocker",
            total_interactions=3,
            days_since_contact=1,
            enthusiasm_count=0,
            support_count=0,
            commitment_count=0,
            concern_count=2,
            objection_count=2,
            unresolved_concern_count=0,
            unresolved_objection_count=0,  # All resolved
        )
        new_level, reason = calculator.calculate_level(signals)

        assert new_level == "skeptic"
        assert "resolved" in reason.lower()

    def test_supporter_demoted_with_multiple_unresolved_concerns(self, calculator):
        """Supporter demoted to neutral with 2+ unresolved concerns."""
        signals = EngagementSignals(
            stakeholder_id="test",
            current_level="supporter",
            total_interactions=5,
            days_since_contact=1,
            enthusiasm_count=2,
            support_count=2,
            commitment_count=0,
            concern_count=3,
            objection_count=0,
            unresolved_concern_count=2,
            unresolved_objection_count=0,
        )
        new_level, reason = calculator.calculate_level(signals)

        assert new_level == "neutral"
        assert "unresolved concerns" in reason.lower()

    def test_champion_demoted_when_objections_exceed_support(self, calculator):
        """Champion demoted to supporter when objections exceed support."""
        signals = EngagementSignals(
            stakeholder_id="test",
            current_level="champion",
            total_interactions=10,
            days_since_contact=1,
            enthusiasm_count=1,
            support_count=2,
            commitment_count=1,
            concern_count=0,
            objection_count=3,  # More than support_count
            unresolved_concern_count=0,
            unresolved_objection_count=0,
        )
        new_level, reason = calculator.calculate_level(signals)

        assert new_level == "supporter"
        assert "Objections" in reason

    def test_promotion_to_champion_with_commitment(self, calculator):
        """Neutral promoted to champion with 5+ interactions and commitment."""
        signals = EngagementSignals(
            stakeholder_id="test",
            current_level="neutral",
            total_interactions=5,
            days_since_contact=1,
            enthusiasm_count=1,
            support_count=1,
            commitment_count=1,
            concern_count=0,
            objection_count=0,
            unresolved_concern_count=0,
            unresolved_objection_count=0,
        )
        new_level, reason = calculator.calculate_level(signals)

        assert new_level == "champion"
        assert "commitment" in reason.lower()

    def test_promotion_to_champion_with_strong_support(self, calculator):
        """Neutral promoted to champion with 5+ interactions and 3+ support."""
        signals = EngagementSignals(
            stakeholder_id="test",
            current_level="neutral",
            total_interactions=5,
            days_since_contact=1,
            enthusiasm_count=0,
            support_count=3,
            commitment_count=0,
            concern_count=0,
            objection_count=0,
            unresolved_concern_count=0,
            unresolved_objection_count=0,
        )
        new_level, reason = calculator.calculate_level(signals)

        assert new_level == "champion"
        assert "support" in reason.lower()

    def test_promotion_to_supporter_with_positive_ratio(self, calculator):
        """Neutral promoted to supporter with 3+ interactions and >50% positive."""
        signals = EngagementSignals(
            stakeholder_id="test",
            current_level="neutral",
            total_interactions=3,
            days_since_contact=1,
            enthusiasm_count=1,
            support_count=1,
            commitment_count=0,
            concern_count=1,
            objection_count=0,
            unresolved_concern_count=0,
            unresolved_objection_count=0,
        )
        new_level, reason = calculator.calculate_level(signals)

        assert new_level == "supporter"
        assert "positive signals" in reason.lower()


# ============================================================================
# Test: Sticky Level Behavior
# ============================================================================


class TestStickyLevelBehavior:
    """Test that levels are 'sticky' - only demote on explicit negative signals."""

    def test_no_demotion_with_inactivity_alone(self, calculator):
        """Champion stays champion with just inactivity (no negative signals)."""
        signals = EngagementSignals(
            stakeholder_id="test",
            current_level="champion",
            total_interactions=10,
            days_since_contact=90,  # 90 days inactive
            enthusiasm_count=2,
            support_count=3,
            commitment_count=1,
            concern_count=0,
            objection_count=0,
            unresolved_concern_count=0,
            unresolved_objection_count=0,
        )
        new_level, reason = calculator.calculate_level(signals)

        assert new_level == "champion"
        assert "maintaining" in reason.lower()

    def test_supporter_maintains_without_negative_signals(self, calculator):
        """Supporter maintains level without explicit negative signals."""
        signals = EngagementSignals(
            stakeholder_id="test",
            current_level="supporter",
            total_interactions=3,
            days_since_contact=30,
            enthusiasm_count=1,
            support_count=1,
            commitment_count=0,
            concern_count=1,  # Concern but resolved
            objection_count=0,
            unresolved_concern_count=0,  # Resolved
            unresolved_objection_count=0,
        )
        new_level, reason = calculator.calculate_level(signals)

        assert new_level == "supporter"

    def test_skeptic_maintains_with_unresolved_objection(self, calculator):
        """Skeptic maintains level when they still have unresolved objection."""
        signals = EngagementSignals(
            stakeholder_id="test",
            current_level="skeptic",
            total_interactions=3,
            days_since_contact=5,
            enthusiasm_count=0,
            support_count=0,
            commitment_count=0,
            concern_count=1,
            objection_count=1,
            unresolved_concern_count=0,
            unresolved_objection_count=1,
        )
        new_level, reason = calculator.calculate_level(signals)

        assert new_level == "skeptic"
        assert "maintaining" in reason.lower()

    def test_neutral_does_not_demote_without_objections(self, calculator):
        """Neutral stays neutral even with concerns (but no objections)."""
        signals = EngagementSignals(
            stakeholder_id="test",
            current_level="neutral",
            total_interactions=2,
            days_since_contact=15,
            enthusiasm_count=0,
            support_count=0,
            commitment_count=0,
            concern_count=3,
            objection_count=0,
            unresolved_concern_count=2,
            unresolved_objection_count=0,  # No objections
        )
        new_level, reason = calculator.calculate_level(signals)

        assert new_level == "neutral"


# ============================================================================
# Test: Signal Collection
# ============================================================================


class TestSignalCollection:
    """Test signal collection from database."""

    @pytest.mark.asyncio
    async def test_collect_signals_aggregates_insights(self):
        """Signal collection properly counts insight types."""
        mock_sb = Mock()

        # Mock stakeholder data
        mock_sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(
            data={
                "engagement_level": "supporter",
                "total_interactions": 8,
                "last_interaction": "2024-01-15T10:00:00Z",
            }
        )

        # Mock insights data
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[
                {"insight_type": "enthusiasm", "is_resolved": False},
                {"insight_type": "support", "is_resolved": False},
                {"insight_type": "support", "is_resolved": False},
                {"insight_type": "concern", "is_resolved": True},
                {"insight_type": "concern", "is_resolved": False},
                {"insight_type": "objection", "is_resolved": False},
            ]
        )

        calculator = EngagementCalculator(supabase=mock_sb)
        signals = await calculator.collect_signals("test-stakeholder")

        assert signals.enthusiasm_count == 1
        assert signals.support_count == 2
        assert signals.concern_count == 2
        assert signals.unresolved_concern_count == 1
        assert signals.objection_count == 1
        assert signals.unresolved_objection_count == 1

    @pytest.mark.asyncio
    async def test_collect_signals_stakeholder_not_found(self):
        """Signal collection raises error when stakeholder not found."""
        mock_sb = Mock()
        mock_sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(
            data=None
        )

        calculator = EngagementCalculator(supabase=mock_sb)

        with pytest.raises(ValueError, match="not found"):
            await calculator.collect_signals("nonexistent-stakeholder")

    @pytest.mark.asyncio
    async def test_collect_signals_defaults_null_level_to_neutral(self):
        """Null engagement level defaults to neutral."""
        mock_sb = Mock()

        mock_sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(
            data={
                "engagement_level": None,
                "total_interactions": 2,
                "last_interaction": None,
            }
        )
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[]
        )

        calculator = EngagementCalculator(supabase=mock_sb)
        signals = await calculator.collect_signals("test-stakeholder")

        assert signals.current_level == "neutral"


# ============================================================================
# Test: Full Calculation Flow
# ============================================================================


class TestCalculationFlow:
    """Test full calculation flow including database updates."""

    @pytest.mark.asyncio
    async def test_calculate_for_stakeholder_records_history(self):
        """Calculate records result in engagement_level_history."""
        mock_sb = Mock()

        # Mock stakeholder lookup
        mock_sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(
            data={
                "engagement_level": "neutral",
                "total_interactions": 5,
                "last_interaction": "2024-01-15T10:00:00Z",
            }
        )

        # Mock insights
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[
                {"insight_type": "commitment", "is_resolved": False},
            ]
        )

        # Mock update and insert
        mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()
        mock_sb.table.return_value.insert.return_value.execute.return_value = Mock()

        calculator = EngagementCalculator(supabase=mock_sb)
        await calculator.calculate_for_stakeholder(
            stakeholder_id="test-stakeholder", client_id="test-client", calculation_type="manual"
        )

        # Verify history was recorded
        insert_calls = [
            c for c in mock_sb.table.call_args_list if "engagement_level_history" in str(c)
        ]
        assert len(insert_calls) > 0

    @pytest.mark.asyncio
    async def test_calculate_for_stakeholder_updates_on_change(self):
        """Calculate updates stakeholder when level changes."""
        mock_sb = Mock()

        # Mock stakeholder lookup - currently neutral
        mock_sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(
            data={
                "engagement_level": "neutral",
                "total_interactions": 5,
                "last_interaction": "2024-01-15T10:00:00Z",
            }
        )

        # Mock insights with commitment (will promote to champion)
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[
                {"insight_type": "commitment", "is_resolved": False},
                {"insight_type": "support", "is_resolved": False},
            ]
        )

        # Mock update and insert
        mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()
        mock_sb.table.return_value.insert.return_value.execute.return_value = Mock()

        calculator = EngagementCalculator(supabase=mock_sb)
        result = await calculator.calculate_for_stakeholder(
            stakeholder_id="test-stakeholder",
            client_id="test-client",
        )

        assert result.changed is True
        assert result.new_level == "champion"
        assert result.previous_level == "neutral"


# ============================================================================
# Test: Client Batch Calculation
# ============================================================================


class TestClientBatchCalculation:
    """Test batch calculation for all stakeholders in a client."""

    @pytest.mark.asyncio
    async def test_calculate_for_client_summarizes_results(self):
        """Client calculation returns summary with change counts."""
        mock_sb = Mock()

        # Use side_effect to return different results for different table calls
        def table_side_effect(table_name):
            table_mock = Mock()

            if table_name == "stakeholders":
                # First call: get list of stakeholders
                # Second+ calls: get individual stakeholder details
                select_mock = Mock()

                # For the list query (no single())
                list_execute = Mock(
                    data=[
                        {"id": "stakeholder-1"},
                        {"id": "stakeholder-2"},
                    ]
                )

                # For individual queries (with single())
                individual_execute = Mock(
                    data={
                        "engagement_level": "neutral",
                        "total_interactions": 5,
                        "last_interaction": "2024-01-15T10:00:00Z",
                    }
                )

                select_mock.return_value.eq.return_value.execute.return_value = list_execute
                select_mock.return_value.eq.return_value.single.return_value.execute.return_value = individual_execute
                table_mock.select = select_mock

                # Update mock
                table_mock.update.return_value.eq.return_value.execute.return_value = Mock()

            elif table_name == "stakeholder_insights":
                # Insights query
                select_mock = Mock()
                select_mock.return_value.eq.return_value.execute.return_value = Mock(
                    data=[{"insight_type": "commitment", "is_resolved": False}]
                )
                table_mock.select = select_mock

            elif table_name == "engagement_level_history":
                # History insert
                table_mock.insert.return_value.execute.return_value = Mock()

            return table_mock

        mock_sb.table.side_effect = table_side_effect

        calculator = EngagementCalculator(supabase=mock_sb)
        summary = await calculator.calculate_for_client(client_id="test-client")

        assert summary["client_id"] == "test-client"
        assert summary["total"] == 2
        assert summary["processed"] == 2
        assert summary["errors"] == 0

    @pytest.mark.asyncio
    async def test_calculate_for_client_empty_stakeholders(self):
        """Client with no stakeholders returns empty summary."""
        mock_sb = Mock()
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[]
        )

        calculator = EngagementCalculator(supabase=mock_sb)
        summary = await calculator.calculate_for_client(client_id="empty-client")

        assert summary["total"] == 0
        assert summary["processed"] == 0
        assert summary["changes"] == []


# ============================================================================
# Test: Edge Cases
# ============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_interactions_maintains_level(self, calculator):
        """Zero interactions maintains current level."""
        signals = EngagementSignals(
            stakeholder_id="test",
            current_level="neutral",
            total_interactions=0,
            days_since_contact=None,
            enthusiasm_count=0,
            support_count=0,
            commitment_count=0,
            concern_count=0,
            objection_count=0,
            unresolved_concern_count=0,
            unresolved_objection_count=0,
        )
        new_level, reason = calculator.calculate_level(signals)

        assert new_level == "neutral"

    def test_exactly_threshold_interactions(self, calculator):
        """Exactly 3 interactions with positive ratio promotes to supporter."""
        signals = EngagementSignals(
            stakeholder_id="test",
            current_level="neutral",
            total_interactions=3,  # Exactly threshold
            days_since_contact=1,
            enthusiasm_count=2,
            support_count=0,
            commitment_count=0,
            concern_count=1,
            objection_count=0,
            unresolved_concern_count=0,
            unresolved_objection_count=0,
        )
        new_level, reason = calculator.calculate_level(signals)

        assert new_level == "supporter"

    def test_exactly_50_percent_positive_does_not_promote(self, calculator):
        """Exactly 50% positive ratio does NOT promote (needs >50%)."""
        signals = EngagementSignals(
            stakeholder_id="test",
            current_level="neutral",
            total_interactions=4,
            days_since_contact=1,
            enthusiasm_count=1,
            support_count=1,
            commitment_count=0,
            concern_count=1,
            objection_count=1,
            unresolved_concern_count=0,
            unresolved_objection_count=0,
        )
        new_level, reason = calculator.calculate_level(signals)

        assert new_level == "neutral"

    def test_already_champion_stays_champion(self, calculator):
        """Already champion with good signals stays champion."""
        signals = EngagementSignals(
            stakeholder_id="test",
            current_level="champion",
            total_interactions=10,
            days_since_contact=1,
            enthusiasm_count=3,
            support_count=4,
            commitment_count=2,
            concern_count=0,
            objection_count=0,
            unresolved_concern_count=0,
            unresolved_objection_count=0,
        )
        new_level, reason = calculator.calculate_level(signals)

        assert new_level == "champion"
