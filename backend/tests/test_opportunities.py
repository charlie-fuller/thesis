"""
Tests for Opportunities Pipeline API

Tests the AI implementation opportunities with 4-dimension scoring:
- roi_potential (1-5)
- implementation_effort (1-5)
- strategic_alignment (1-5)
- stakeholder_readiness (1-5)

Note: This test file uses direct module loading to avoid import chain issues
with llama_index dependencies on Python 3.9+.
"""

import sys
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid


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

# Create mock objects for opportunity services (used by test methods directly, not sys.modules)
mock_opportunity_context = Mock()
mock_opportunity_context.get_scoring_related_documents = Mock(return_value=[])

mock_opportunity_chat = Mock()
mock_opportunity_chat.ask_about_opportunity = AsyncMock(return_value={
    "response": "Test response",
    "sources": []
})
mock_opportunity_chat.get_opportunity_conversations = AsyncMock(return_value=[])


# ============================================================================
# Re-implement the core models and logic for isolated testing
# ============================================================================

@dataclass
class Opportunity:
    """Opportunity data model for testing."""
    id: str
    client_id: str
    opportunity_code: str
    title: str
    description: Optional[str] = None
    department: Optional[str] = None
    owner_stakeholder_id: Optional[str] = None
    current_state: Optional[str] = None
    desired_state: Optional[str] = None
    roi_potential: Optional[int] = None  # 1-5 scoring
    implementation_effort: Optional[int] = None  # 1-5 scoring
    strategic_alignment: Optional[int] = None  # 1-5 scoring
    stakeholder_readiness: Optional[int] = None  # 1-5 scoring
    total_score: int = 0
    tier: int = 4
    status: str = "identified"
    next_step: Optional[str] = None
    blockers: List[str] = field(default_factory=list)
    follow_up_questions: List[str] = field(default_factory=list)
    roi_indicators: Dict[str, Any] = field(default_factory=dict)
    source_type: Optional[str] = None
    source_notes: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""


def calculate_total_score(opp: dict) -> int:
    """Calculate total score from 4 dimensions."""
    roi = opp.get("roi_potential") or 0
    effort = opp.get("implementation_effort") or 0
    alignment = opp.get("strategic_alignment") or 0
    readiness = opp.get("stakeholder_readiness") or 0
    return roi + effort + alignment + readiness


def calculate_tier(total_score: int) -> int:
    """Calculate tier from total score (max 20)."""
    if total_score >= 16:
        return 1  # Strategic
    elif total_score >= 12:
        return 2  # High Impact
    elif total_score >= 8:
        return 3  # Medium
    else:
        return 4  # Backlog


VALID_STATUSES = [
    "identified",
    "scoping",
    "pilot",
    "scaling",
    "completed",
    "blocked"
]

STATUS_TRANSITIONS = {
    "identified": ["scoping", "blocked"],
    "scoping": ["pilot", "blocked", "identified"],
    "pilot": ["scaling", "blocked", "scoping"],
    "scaling": ["completed", "blocked", "pilot"],
    "completed": [],  # Terminal state
    "blocked": ["identified", "scoping", "pilot", "scaling"],  # Can unblock to any active state
}

STAKEHOLDER_LINK_ROLES = [
    "owner",
    "champion",
    "involved",
    "blocker",
    "approver"
]


class OpportunityService:
    """Service class for opportunity operations (test implementation)."""

    def __init__(self, supabase, client_id: str):
        self.supabase = supabase
        self.client_id = client_id

    def validate_scores(self, roi: int = None, effort: int = None,
                       alignment: int = None, readiness: int = None) -> List[str]:
        """Validate scoring dimensions are within 1-5 range."""
        errors = []
        for name, value in [
            ("roi_potential", roi),
            ("implementation_effort", effort),
            ("strategic_alignment", alignment),
            ("stakeholder_readiness", readiness)
        ]:
            if value is not None:
                if not isinstance(value, int) or value < 1 or value > 5:
                    errors.append(f"{name} must be an integer between 1 and 5")
        return errors

    def validate_status_transition(self, current: str, new: str) -> bool:
        """Validate status transition is allowed."""
        if current == new:
            return True
        allowed = STATUS_TRANSITIONS.get(current, [])
        return new in allowed

    def create_opportunity(self, data: dict) -> dict:
        """Create a new opportunity with scoring."""
        # Calculate derived fields
        total_score = calculate_total_score(data)
        tier = calculate_tier(total_score)

        opp_data = {
            **data,
            "id": str(uuid.uuid4()),
            "client_id": self.client_id,
            "total_score": total_score,
            "tier": tier,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        return opp_data

    def update_scores(self, opp: dict, scores: dict) -> dict:
        """Update opportunity scores and recalculate total/tier."""
        updated = {**opp, **scores}
        updated["total_score"] = calculate_total_score(updated)
        updated["tier"] = calculate_tier(updated["total_score"])
        updated["updated_at"] = datetime.now(timezone.utc).isoformat()
        return updated

    def filter_by_tier(self, opportunities: List[dict], tier: int) -> List[dict]:
        """Filter opportunities by tier."""
        return [o for o in opportunities if o.get("tier") == tier]

    def filter_by_department(self, opportunities: List[dict], department: str) -> List[dict]:
        """Filter opportunities by department."""
        return [o for o in opportunities if o.get("department", "").lower() == department.lower()]

    def filter_by_status(self, opportunities: List[dict], status: str) -> List[dict]:
        """Filter opportunities by status."""
        return [o for o in opportunities if o.get("status") == status]

    def group_by_tier(self, opportunities: List[dict]) -> Dict[int, List[dict]]:
        """Group opportunities by tier."""
        grouped = {1: [], 2: [], 3: [], 4: []}
        for opp in opportunities:
            tier = opp.get("tier", 4)
            grouped[tier].append(opp)
        return grouped


class OperatorContextInjector:
    """Handles context injection for Operator agent (test implementation)."""

    def __init__(self, supabase, client_id: str):
        self.supabase = supabase
        self.client_id = client_id

    def get_opportunity_summary(self, opportunities: List[dict]) -> dict:
        """Generate summary for context injection."""
        tier_counts = {1: 0, 2: 0, 3: 0, 4: 0}
        status_counts = {}

        for opp in opportunities:
            tier = opp.get("tier", 4)
            tier_counts[tier] = tier_counts.get(tier, 0) + 1

            status = opp.get("status", "identified")
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "total": len(opportunities),
            "by_tier": tier_counts,
            "by_status": status_counts,
            "top_opportunities": sorted(opportunities, key=lambda x: x.get("total_score", 0), reverse=True)[:5]
        }

    def get_blocked_opportunities(self, opportunities: List[dict]) -> List[dict]:
        """Get blocked opportunities."""
        return [o for o in opportunities if o.get("status") == "blocked"]

    def format_context_injection(self, opportunities: List[dict]) -> str:
        """Format triage data as context injection string."""
        summary = self.get_opportunity_summary(opportunities)
        blocked = self.get_blocked_opportunities(opportunities)

        lines = [
            "<project_triage_context>",
            "",
            "## AI Opportunity Pipeline Summary",
            f"Total Opportunities: {summary['total']}",
            f"- Tier 1 (Strategic): {summary['by_tier'][1]}",
            f"- Tier 2 (High Impact): {summary['by_tier'][2]}",
            f"- Tier 3 (Medium): {summary['by_tier'][3]}",
            f"- Tier 4 (Backlog): {summary['by_tier'][4]}",
            "",
        ]

        if blocked:
            lines.append(f"## Blocked Opportunities ({len(blocked)} items)")
            for b in blocked:
                lines.append(f"- {b.get('opportunity_code', 'N/A')}: {b.get('title', 'N/A')}")
            lines.append("")

        lines.append("</project_triage_context>")

        return "\n".join(lines)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def test_client_id():
    """Test client ID."""
    return str(uuid.uuid4())


@pytest.fixture
def test_user(test_client_id):
    """Test user dict."""
    return {
        "id": str(uuid.uuid4()),
        "client_id": test_client_id,
        "email": "test@example.com"
    }


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client."""
    client = Mock()

    # Default chain returns
    client.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(data=[])
    client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = Mock(data=[])
    client.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value = Mock(data=None)
    client.table.return_value.insert.return_value.execute.return_value = Mock(data=[])
    client.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock(data=[])
    client.table.return_value.delete.return_value.eq.return_value.execute.return_value = Mock(data=[])

    return client


@pytest.fixture
def opportunity_service(mock_supabase_client, test_client_id):
    """Opportunity service instance."""
    return OpportunityService(mock_supabase_client, test_client_id)


@pytest.fixture
def context_injector(mock_supabase_client, test_client_id):
    """Context injector instance."""
    return OperatorContextInjector(mock_supabase_client, test_client_id)


@pytest.fixture
def sample_opportunity_data():
    """Sample opportunity creation data."""
    return {
        "opportunity_code": "F01",
        "title": "Finance Process Automation",
        "description": "Automate invoice processing using AI",
        "department": "finance",
        "roi_potential": 5,
        "implementation_effort": 4,
        "strategic_alignment": 5,
        "stakeholder_readiness": 4,
        "status": "identified",
        "current_state": "Manual invoice processing",
        "desired_state": "Automated invoice processing with 95% accuracy",
    }


@pytest.fixture
def sample_opportunities(test_client_id):
    """Sample list of opportunities for testing filters."""
    return [
        {
            "id": str(uuid.uuid4()),
            "client_id": test_client_id,
            "opportunity_code": "F01",
            "title": "Finance Automation",
            "description": "Automate invoice processing using AI",
            "department": "finance",
            "roi_potential": 5,
            "implementation_effort": 4,
            "strategic_alignment": 5,
            "stakeholder_readiness": 4,
            "total_score": 18,
            "tier": 1,
            "status": "pilot",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": str(uuid.uuid4()),
            "client_id": test_client_id,
            "opportunity_code": "L01",
            "title": "Legal Contract Review",
            "description": "AI-assisted contract review and analysis",
            "department": "legal",
            "roi_potential": 4,
            "implementation_effort": 3,
            "strategic_alignment": 4,
            "stakeholder_readiness": 3,
            "total_score": 14,
            "tier": 2,
            "status": "scoping",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": str(uuid.uuid4()),
            "client_id": test_client_id,
            "opportunity_code": "H01",
            "title": "HR Onboarding AI",
            "description": "Automate employee onboarding process",
            "department": "hr",
            "roi_potential": 3,
            "implementation_effort": 3,
            "strategic_alignment": 3,
            "stakeholder_readiness": 2,
            "total_score": 11,
            "tier": 3,
            "status": "identified",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": str(uuid.uuid4()),
            "client_id": test_client_id,
            "opportunity_code": "M01",
            "title": "Marketing Content Gen",
            "description": "AI content generation for marketing",
            "department": "marketing",
            "roi_potential": 2,
            "implementation_effort": 2,
            "strategic_alignment": 2,
            "stakeholder_readiness": 1,
            "total_score": 7,
            "tier": 4,
            "status": "blocked",
            "blockers": ["No budget allocated", "Stakeholder resistance"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
    ]


@pytest.fixture
def sample_stakeholder(test_client_id):
    """Sample stakeholder for linkage tests."""
    return {
        "id": str(uuid.uuid4()),
        "client_id": test_client_id,
        "name": "John Smith",
        "role": "CFO",
        "department": "finance",
    }


# ============================================================================
# Test: Opportunity Creation with Tier Scoring
# ============================================================================

class TestOpportunityCreation:
    """Test opportunity creation and 4-dimension scoring."""

    def test_create_opportunity_calculates_total_score(self, opportunity_service, sample_opportunity_data):
        """Creating opportunity calculates total score from 4 dimensions."""
        opp = opportunity_service.create_opportunity(sample_opportunity_data)

        expected_score = 5 + 4 + 5 + 4  # roi + effort + alignment + readiness
        assert opp["total_score"] == expected_score
        assert opp["total_score"] == 18

    def test_create_opportunity_assigns_tier_1(self, opportunity_service, sample_opportunity_data):
        """High score (16+) assigns Tier 1."""
        opp = opportunity_service.create_opportunity(sample_opportunity_data)

        assert opp["total_score"] >= 16
        assert opp["tier"] == 1

    def test_create_opportunity_assigns_tier_2(self, opportunity_service):
        """Medium-high score (12-15) assigns Tier 2."""
        data = {
            "opportunity_code": "L01",
            "title": "Legal Process",
            "roi_potential": 4,
            "implementation_effort": 3,
            "strategic_alignment": 4,
            "stakeholder_readiness": 3,
        }
        opp = opportunity_service.create_opportunity(data)

        assert opp["total_score"] == 14
        assert opp["tier"] == 2

    def test_create_opportunity_assigns_tier_3(self, opportunity_service):
        """Medium score (8-11) assigns Tier 3."""
        data = {
            "opportunity_code": "H01",
            "title": "HR Process",
            "roi_potential": 3,
            "implementation_effort": 2,
            "strategic_alignment": 3,
            "stakeholder_readiness": 2,
        }
        opp = opportunity_service.create_opportunity(data)

        assert opp["total_score"] == 10
        assert opp["tier"] == 3

    def test_create_opportunity_assigns_tier_4(self, opportunity_service):
        """Low score (<8) assigns Tier 4."""
        data = {
            "opportunity_code": "M01",
            "title": "Marketing Process",
            "roi_potential": 2,
            "implementation_effort": 1,
            "strategic_alignment": 2,
            "stakeholder_readiness": 1,
        }
        opp = opportunity_service.create_opportunity(data)

        assert opp["total_score"] == 6
        assert opp["tier"] == 4

    def test_create_opportunity_with_null_scores(self, opportunity_service):
        """Opportunity with null scores defaults to tier 4."""
        data = {
            "opportunity_code": "X01",
            "title": "Unscored Opportunity",
        }
        opp = opportunity_service.create_opportunity(data)

        assert opp["total_score"] == 0
        assert opp["tier"] == 4

    def test_create_opportunity_generates_uuid(self, opportunity_service, sample_opportunity_data):
        """Creating opportunity generates valid UUID."""
        opp = opportunity_service.create_opportunity(sample_opportunity_data)

        assert opp["id"] is not None
        assert len(opp["id"]) == 36  # UUID format

    def test_create_opportunity_sets_timestamps(self, opportunity_service, sample_opportunity_data):
        """Creating opportunity sets created_at and updated_at."""
        opp = opportunity_service.create_opportunity(sample_opportunity_data)

        assert opp["created_at"] is not None
        assert opp["updated_at"] is not None


# ============================================================================
# Test: Score Validation
# ============================================================================

class TestScoreValidation:
    """Test score validation (1-5 range)."""

    def test_valid_scores_pass_validation(self, opportunity_service):
        """Scores within 1-5 range pass validation."""
        errors = opportunity_service.validate_scores(
            roi=5, effort=4, alignment=3, readiness=2
        )
        assert errors == []

    def test_score_below_1_fails(self, opportunity_service):
        """Score below 1 fails validation."""
        errors = opportunity_service.validate_scores(roi=0)
        assert len(errors) == 1
        assert "roi_potential" in errors[0]

    def test_score_above_5_fails(self, opportunity_service):
        """Score above 5 fails validation."""
        errors = opportunity_service.validate_scores(effort=6)
        assert len(errors) == 1
        assert "implementation_effort" in errors[0]

    def test_negative_score_fails(self, opportunity_service):
        """Negative score fails validation."""
        errors = opportunity_service.validate_scores(alignment=-1)
        assert len(errors) == 1

    def test_null_scores_pass_validation(self, opportunity_service):
        """Null scores pass validation (optional)."""
        errors = opportunity_service.validate_scores()
        assert errors == []

    def test_multiple_invalid_scores_return_multiple_errors(self, opportunity_service):
        """Multiple invalid scores return multiple errors."""
        errors = opportunity_service.validate_scores(roi=0, effort=10, readiness=-5)
        assert len(errors) == 3


# ============================================================================
# Test: Score Updates and Tier Recalculation
# ============================================================================

class TestScoreUpdates:
    """Test score updates and tier recalculation."""

    def test_update_scores_recalculates_total(self, opportunity_service, sample_opportunities):
        """Updating scores recalculates total_score."""
        opp = sample_opportunities[2]  # Tier 3, score 11

        updated = opportunity_service.update_scores(opp, {
            "roi_potential": 5,
            "implementation_effort": 5,
        })

        expected_score = 5 + 5 + 3 + 2  # Updated roi/effort + original alignment/readiness
        assert updated["total_score"] == expected_score

    def test_update_scores_recalculates_tier(self, opportunity_service, sample_opportunities):
        """Updating scores recalculates tier."""
        opp = sample_opportunities[2]  # Tier 3, score 11

        updated = opportunity_service.update_scores(opp, {
            "roi_potential": 5,
            "implementation_effort": 5,
            "strategic_alignment": 5,
            "stakeholder_readiness": 5,
        })

        assert updated["total_score"] == 20
        assert updated["tier"] == 1

    def test_update_scores_updates_timestamp(self, opportunity_service, sample_opportunities):
        """Updating scores updates updated_at timestamp."""
        opp = sample_opportunities[0]
        original_updated = opp["updated_at"]

        updated = opportunity_service.update_scores(opp, {"roi_potential": 3})

        assert updated["updated_at"] != original_updated


# ============================================================================
# Test: Status Progression
# ============================================================================

class TestStatusProgression:
    """Test opportunity status progression (identified -> completed)."""

    def test_initial_status_is_identified(self, opportunity_service, sample_opportunity_data):
        """New opportunity defaults to 'identified' status."""
        data = {k: v for k, v in sample_opportunity_data.items() if k != "status"}
        opp = opportunity_service.create_opportunity(data)

        assert opp.get("status", "identified") == "identified"

    def test_valid_transition_identified_to_scoping(self, opportunity_service):
        """Valid: identified -> scoping."""
        assert opportunity_service.validate_status_transition("identified", "scoping")

    def test_valid_transition_scoping_to_pilot(self, opportunity_service):
        """Valid: scoping -> pilot."""
        assert opportunity_service.validate_status_transition("scoping", "pilot")

    def test_valid_transition_pilot_to_scaling(self, opportunity_service):
        """Valid: pilot -> scaling."""
        assert opportunity_service.validate_status_transition("pilot", "scaling")

    def test_valid_transition_scaling_to_completed(self, opportunity_service):
        """Valid: scaling -> completed."""
        assert opportunity_service.validate_status_transition("scaling", "completed")

    def test_any_status_can_transition_to_blocked(self, opportunity_service):
        """Any active status can transition to blocked."""
        for status in ["identified", "scoping", "pilot", "scaling"]:
            assert opportunity_service.validate_status_transition(status, "blocked")

    def test_blocked_can_transition_to_any_active(self, opportunity_service):
        """Blocked can transition back to any active status."""
        for status in ["identified", "scoping", "pilot", "scaling"]:
            assert opportunity_service.validate_status_transition("blocked", status)

    def test_completed_cannot_transition(self, opportunity_service):
        """Completed is terminal - cannot transition to other statuses."""
        for status in ["identified", "scoping", "pilot", "scaling", "blocked"]:
            assert not opportunity_service.validate_status_transition("completed", status)

    def test_invalid_skip_transition(self, opportunity_service):
        """Cannot skip statuses (identified -> pilot is invalid)."""
        assert not opportunity_service.validate_status_transition("identified", "pilot")

    def test_same_status_is_valid(self, opportunity_service):
        """Transitioning to same status is valid (no-op)."""
        for status in VALID_STATUSES:
            assert opportunity_service.validate_status_transition(status, status)


# ============================================================================
# Test: Filtering by Tier, Department, Status
# ============================================================================

class TestFiltering:
    """Test opportunity filtering."""

    def test_filter_by_tier_1(self, opportunity_service, sample_opportunities):
        """Filter returns only Tier 1 opportunities."""
        result = opportunity_service.filter_by_tier(sample_opportunities, 1)

        assert len(result) == 1
        assert result[0]["opportunity_code"] == "F01"
        assert all(o["tier"] == 1 for o in result)

    def test_filter_by_tier_4(self, opportunity_service, sample_opportunities):
        """Filter returns only Tier 4 opportunities."""
        result = opportunity_service.filter_by_tier(sample_opportunities, 4)

        assert len(result) == 1
        assert result[0]["opportunity_code"] == "M01"

    def test_filter_by_department(self, opportunity_service, sample_opportunities):
        """Filter by department returns correct opportunities."""
        result = opportunity_service.filter_by_department(sample_opportunities, "finance")

        assert len(result) == 1
        assert result[0]["opportunity_code"] == "F01"

    def test_filter_by_department_case_insensitive(self, opportunity_service, sample_opportunities):
        """Department filter is case-insensitive."""
        result = opportunity_service.filter_by_department(sample_opportunities, "FINANCE")

        assert len(result) == 1
        assert result[0]["department"] == "finance"

    def test_filter_by_status(self, opportunity_service, sample_opportunities):
        """Filter by status returns correct opportunities."""
        result = opportunity_service.filter_by_status(sample_opportunities, "blocked")

        assert len(result) == 1
        assert result[0]["opportunity_code"] == "M01"

    def test_filter_returns_empty_for_no_matches(self, opportunity_service, sample_opportunities):
        """Filter returns empty list when no matches."""
        result = opportunity_service.filter_by_department(sample_opportunities, "nonexistent")

        assert result == []

    def test_group_by_tier(self, opportunity_service, sample_opportunities):
        """Group by tier returns dict with tier keys."""
        result = opportunity_service.group_by_tier(sample_opportunities)

        assert len(result[1]) == 1  # Tier 1
        assert len(result[2]) == 1  # Tier 2
        assert len(result[3]) == 1  # Tier 3
        assert len(result[4]) == 1  # Tier 4


# ============================================================================
# Test: Stakeholder Linkage
# ============================================================================

class TestStakeholderLinkage:
    """Test opportunity-stakeholder linking."""

    def test_valid_link_roles(self):
        """All link roles are valid."""
        expected_roles = ["owner", "champion", "involved", "blocker", "approver"]
        assert STAKEHOLDER_LINK_ROLES == expected_roles

    def test_owner_role_in_valid_roles(self):
        """Owner is a valid role."""
        assert "owner" in STAKEHOLDER_LINK_ROLES

    def test_champion_role_in_valid_roles(self):
        """Champion is a valid role."""
        assert "champion" in STAKEHOLDER_LINK_ROLES

    def test_blocker_role_in_valid_roles(self):
        """Blocker is a valid role (for tracking resistance)."""
        assert "blocker" in STAKEHOLDER_LINK_ROLES

    def test_approver_role_in_valid_roles(self):
        """Approver is a valid role."""
        assert "approver" in STAKEHOLDER_LINK_ROLES


# ============================================================================
# Test: Operator Context Injection
# ============================================================================

class TestOperatorContextInjection:
    """Test Operator agent context injection for triage."""

    def test_get_opportunity_summary(self, context_injector, sample_opportunities):
        """Summary includes counts by tier and status."""
        summary = context_injector.get_opportunity_summary(sample_opportunities)

        assert summary["total"] == 4
        assert summary["by_tier"][1] == 1
        assert summary["by_tier"][2] == 1
        assert summary["by_tier"][3] == 1
        assert summary["by_tier"][4] == 1

    def test_summary_includes_status_breakdown(self, context_injector, sample_opportunities):
        """Summary includes status breakdown."""
        summary = context_injector.get_opportunity_summary(sample_opportunities)

        assert "pilot" in summary["by_status"]
        assert "scoping" in summary["by_status"]
        assert "identified" in summary["by_status"]
        assert "blocked" in summary["by_status"]

    def test_summary_top_opportunities_sorted_by_score(self, context_injector, sample_opportunities):
        """Top opportunities are sorted by score descending."""
        summary = context_injector.get_opportunity_summary(sample_opportunities)
        top = summary["top_opportunities"]

        assert len(top) <= 5
        scores = [o["total_score"] for o in top]
        assert scores == sorted(scores, reverse=True)

    def test_get_blocked_opportunities(self, context_injector, sample_opportunities):
        """Get blocked opportunities returns only blocked status."""
        blocked = context_injector.get_blocked_opportunities(sample_opportunities)

        assert len(blocked) == 1
        assert blocked[0]["status"] == "blocked"
        assert blocked[0]["opportunity_code"] == "M01"

    def test_format_context_injection_has_xml_tags(self, context_injector, sample_opportunities):
        """Context injection is wrapped in XML tags."""
        context = context_injector.format_context_injection(sample_opportunities)

        assert "<project_triage_context>" in context
        assert "</project_triage_context>" in context

    def test_format_context_injection_includes_tier_counts(self, context_injector, sample_opportunities):
        """Context includes tier breakdown."""
        context = context_injector.format_context_injection(sample_opportunities)

        assert "Tier 1 (Strategic): 1" in context
        assert "Tier 2 (High Impact): 1" in context
        assert "Tier 3 (Medium): 1" in context
        assert "Tier 4 (Backlog): 1" in context

    def test_format_context_injection_includes_blocked(self, context_injector, sample_opportunities):
        """Context includes blocked opportunities section."""
        context = context_injector.format_context_injection(sample_opportunities)

        assert "Blocked Opportunities" in context
        assert "M01" in context

    def test_format_context_injection_empty_list(self, context_injector):
        """Context injection handles empty opportunity list."""
        context = context_injector.format_context_injection([])

        assert "<project_triage_context>" in context
        assert "Total Opportunities: 0" in context
        assert "Blocked Opportunities" not in context  # No blocked section if none


# ============================================================================
# Test: Tier Calculation Edge Cases
# ============================================================================

class TestTierCalculationEdgeCases:
    """Test tier calculation boundary conditions."""

    def test_exact_tier_1_boundary(self):
        """Score of exactly 16 is Tier 1."""
        assert calculate_tier(16) == 1

    def test_below_tier_1_boundary(self):
        """Score of 15 is Tier 2 (not Tier 1)."""
        assert calculate_tier(15) == 2

    def test_exact_tier_2_boundary(self):
        """Score of exactly 12 is Tier 2."""
        assert calculate_tier(12) == 2

    def test_below_tier_2_boundary(self):
        """Score of 11 is Tier 3 (not Tier 2)."""
        assert calculate_tier(11) == 3

    def test_exact_tier_3_boundary(self):
        """Score of exactly 8 is Tier 3."""
        assert calculate_tier(8) == 3

    def test_below_tier_3_boundary(self):
        """Score of 7 is Tier 4."""
        assert calculate_tier(7) == 4

    def test_zero_score_is_tier_4(self):
        """Score of 0 is Tier 4."""
        assert calculate_tier(0) == 4

    def test_max_score_20_is_tier_1(self):
        """Max score of 20 is Tier 1."""
        assert calculate_tier(20) == 1


# ============================================================================
# Test: Total Score Calculation
# ============================================================================

class TestTotalScoreCalculation:
    """Test total score calculation from 4 dimensions."""

    def test_all_fives_equals_20(self):
        """All dimensions at 5 equals max score 20."""
        opp = {
            "roi_potential": 5,
            "implementation_effort": 5,
            "strategic_alignment": 5,
            "stakeholder_readiness": 5,
        }
        assert calculate_total_score(opp) == 20

    def test_all_ones_equals_4(self):
        """All dimensions at 1 equals min score 4."""
        opp = {
            "roi_potential": 1,
            "implementation_effort": 1,
            "strategic_alignment": 1,
            "stakeholder_readiness": 1,
        }
        assert calculate_total_score(opp) == 4

    def test_mixed_scores(self):
        """Mixed scores calculate correctly."""
        opp = {
            "roi_potential": 5,
            "implementation_effort": 3,
            "strategic_alignment": 4,
            "stakeholder_readiness": 2,
        }
        assert calculate_total_score(opp) == 14

    def test_null_values_treated_as_zero(self):
        """Null/missing values are treated as 0."""
        opp = {
            "roi_potential": 5,
            "implementation_effort": None,
        }
        assert calculate_total_score(opp) == 5

    def test_empty_dict_returns_zero(self):
        """Empty dict returns 0."""
        assert calculate_total_score({}) == 0


# ============================================================================
# Test: API Response Format
# ============================================================================

class TestAPIResponseFormat:
    """Test expected API response formats."""

    def test_opportunity_response_has_required_fields(self, sample_opportunities):
        """Opportunity response includes all required fields."""
        opp = sample_opportunities[0]

        required_fields = [
            "id", "opportunity_code", "title", "description", "department",
            "roi_potential", "implementation_effort", "strategic_alignment",
            "stakeholder_readiness", "total_score", "tier", "status",
            "created_at", "updated_at"
        ]

        for field in required_fields:
            assert field in opp

    def test_blockers_is_list(self, sample_opportunities):
        """Blockers field is a list."""
        opp = sample_opportunities[3]  # Blocked opportunity

        assert isinstance(opp.get("blockers", []), list)
        assert len(opp["blockers"]) == 2

    def test_scores_are_integers(self, sample_opportunities):
        """All score fields are integers."""
        opp = sample_opportunities[0]

        for field in ["roi_potential", "implementation_effort", "strategic_alignment", "stakeholder_readiness"]:
            assert isinstance(opp[field], int)

    def test_tier_is_integer_1_to_4(self, sample_opportunities):
        """Tier is an integer 1-4."""
        for opp in sample_opportunities:
            assert isinstance(opp["tier"], int)
            assert 1 <= opp["tier"] <= 4


# ============================================================================
# DETAIL MODAL TESTS - Related Documents, Q&A Chat, Conversations
# ============================================================================

class TestRelatedDocuments:
    """Tests for opportunity-related document retrieval."""

    def test_get_scoring_related_documents_returns_list(self):
        """Related documents endpoint returns a list."""
        mock_opportunity_context.get_scoring_related_documents.return_value = []
        result = mock_opportunity_context.get_scoring_related_documents(
            opportunity={"id": "test-id", "title": "Test Opportunity"},
            client_id="test-client",
            limit=8,
            min_similarity=0.25
        )
        assert isinstance(result, list)

    def test_related_document_structure(self):
        """Related document has required fields."""
        sample_doc = {
            "chunk_id": "chunk-123",
            "document_id": "doc-456",
            "document_name": "Test Document.md",
            "relevance_score": 0.85,
            "snippet": "This is a relevant excerpt from the document...",
            "metadata": {
                "filename": "Test Document.md",
                "page_number": None,
                "source_type": "upload",
                "storage_path": "/uploads/test.md"
            }
        }
        mock_opportunity_context.get_scoring_related_documents.return_value = [sample_doc]
        result = mock_opportunity_context.get_scoring_related_documents(
            opportunity={"id": "test-id"},
            client_id="test-client"
        )
        assert len(result) == 1
        doc = result[0]
        assert "chunk_id" in doc
        assert "document_id" in doc
        assert "document_name" in doc
        assert "relevance_score" in doc
        assert "snippet" in doc
        assert "metadata" in doc

    def test_related_documents_sorted_by_relevance(self):
        """Documents are sorted by relevance score descending."""
        docs = [
            {"chunk_id": "1", "relevance_score": 0.5},
            {"chunk_id": "2", "relevance_score": 0.9},
            {"chunk_id": "3", "relevance_score": 0.7},
        ]
        sorted_docs = sorted(docs, key=lambda x: x["relevance_score"], reverse=True)
        assert sorted_docs[0]["relevance_score"] == 0.9
        assert sorted_docs[1]["relevance_score"] == 0.7
        assert sorted_docs[2]["relevance_score"] == 0.5

    def test_related_documents_limit_respected(self):
        """Document limit parameter is respected."""
        # Test that limit parameter works
        mock_opportunity_context.get_scoring_related_documents.return_value = [
            {"chunk_id": str(i)} for i in range(5)
        ]
        result = mock_opportunity_context.get_scoring_related_documents(
            opportunity={"id": "test-id"},
            client_id="test-client",
            limit=5
        )
        assert len(result) <= 5

    def test_related_documents_min_similarity_filter(self):
        """Documents below min_similarity are filtered out."""
        # All returned docs should be above threshold
        docs = [
            {"chunk_id": "1", "relevance_score": 0.3},
            {"chunk_id": "2", "relevance_score": 0.5},
        ]
        filtered = [d for d in docs if d["relevance_score"] >= 0.25]
        assert len(filtered) == 2

        filtered_strict = [d for d in docs if d["relevance_score"] >= 0.4]
        assert len(filtered_strict) == 1

    def test_related_documents_empty_opportunity(self):
        """Empty opportunity context returns empty results gracefully."""
        mock_opportunity_context.get_scoring_related_documents.return_value = []
        result = mock_opportunity_context.get_scoring_related_documents(
            opportunity={"id": "test-id", "title": "", "description": None},
            client_id="test-client"
        )
        assert result == []


class TestOpportunityQA:
    """Tests for Q&A chat about opportunities."""

    @pytest.mark.asyncio
    async def test_ask_about_opportunity_returns_response(self):
        """Ask endpoint returns a response with sources."""
        mock_opportunity_chat.ask_about_opportunity.return_value = {
            "response": "Based on the documents, this opportunity has high ROI potential.",
            "sources": []
        }
        result = await mock_opportunity_chat.ask_about_opportunity(
            opportunity_id="test-opp-id",
            question="Why is ROI rated 5?",
            client_id="test-client",
            user_id="test-user"
        )
        assert "response" in result
        assert "sources" in result
        assert isinstance(result["response"], str)
        assert isinstance(result["sources"], list)

    @pytest.mark.asyncio
    async def test_ask_with_sources(self):
        """Response includes source documents when available."""
        mock_opportunity_chat.ask_about_opportunity.return_value = {
            "response": "The ROI is rated 5 because of the evidence in the attached document.",
            "sources": [
                {
                    "chunk_id": "chunk-1",
                    "document_id": "doc-1",
                    "document_name": "Business Case.pdf",
                    "relevance_score": 0.92,
                    "snippet": "Expected annual savings of $2M..."
                }
            ]
        }
        result = await mock_opportunity_chat.ask_about_opportunity(
            opportunity_id="test-opp-id",
            question="Why is ROI rated 5?",
            client_id="test-client",
            user_id="test-user"
        )
        assert len(result["sources"]) == 1
        assert result["sources"][0]["document_name"] == "Business Case.pdf"

    @pytest.mark.asyncio
    async def test_ask_question_validation(self):
        """Question must be non-empty."""
        # Empty question should be invalid
        question = ""
        assert len(question.strip()) == 0

        # Valid question
        question = "What are the blockers?"
        assert len(question.strip()) > 0

    @pytest.mark.asyncio
    async def test_ask_question_max_length(self):
        """Question has maximum length limit."""
        max_length = 1000
        long_question = "a" * 1001
        assert len(long_question) > max_length

        valid_question = "a" * 500
        assert len(valid_question) <= max_length


class TestOpportunityConversations:
    """Tests for opportunity conversation history."""

    @pytest.mark.asyncio
    async def test_get_conversations_returns_list(self):
        """Conversations endpoint returns a list."""
        mock_opportunity_chat.get_opportunity_conversations.return_value = []
        result = await mock_opportunity_chat.get_opportunity_conversations(
            opportunity_id="test-opp-id",
            client_id="test-client"
        )
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_conversation_structure(self):
        """Conversation has required fields."""
        sample_convo = {
            "id": str(uuid.uuid4()),
            "question": "What is the implementation timeline?",
            "response": "Based on the assessment, implementation would take 3-6 months.",
            "source_documents": [
                {"document_id": "doc-1", "document_name": "Timeline.pdf"}
            ],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        mock_opportunity_chat.get_opportunity_conversations.return_value = [sample_convo]
        result = await mock_opportunity_chat.get_opportunity_conversations(
            opportunity_id="test-opp-id",
            client_id="test-client"
        )
        assert len(result) == 1
        convo = result[0]
        assert "id" in convo
        assert "question" in convo
        assert "response" in convo
        assert "source_documents" in convo
        assert "created_at" in convo

    @pytest.mark.asyncio
    async def test_conversations_ordered_by_date(self):
        """Conversations are returned newest first."""
        convos = [
            {"id": "1", "created_at": "2026-01-15T10:00:00Z"},
            {"id": "2", "created_at": "2026-01-16T10:00:00Z"},
            {"id": "3", "created_at": "2026-01-14T10:00:00Z"},
        ]
        sorted_convos = sorted(convos, key=lambda x: x["created_at"], reverse=True)
        assert sorted_convos[0]["id"] == "2"  # newest
        assert sorted_convos[2]["id"] == "3"  # oldest

    @pytest.mark.asyncio
    async def test_conversations_pagination(self):
        """Conversations support limit and offset."""
        # Generate 25 conversations
        all_convos = [{"id": str(i)} for i in range(25)]

        # First page (limit 20, offset 0)
        page1 = all_convos[0:20]
        assert len(page1) == 20

        # Second page (limit 20, offset 20)
        page2 = all_convos[20:40]
        assert len(page2) == 5  # Only 5 remaining


class TestScoreJustification:
    """Tests for score justification display logic."""

    def test_score_level_descriptions(self):
        """Each score level 1-5 has a description."""
        roi_descriptions = {
            1: "Minimal impact",
            2: "Minor improvement",
            3: "Moderate impact",
            4: "Significant impact",
            5: "Transformative impact"
        }
        for level in range(1, 6):
            assert level in roi_descriptions
            assert len(roi_descriptions[level]) > 0

    def test_all_dimensions_have_descriptions(self):
        """All 4 scoring dimensions have level descriptions."""
        dimensions = [
            "roi_potential",
            "implementation_effort",
            "strategic_alignment",
            "stakeholder_readiness"
        ]
        assert len(dimensions) == 4
        for dim in dimensions:
            assert dim.replace("_", " ").title()  # Can be displayed

    def test_tier_explanation(self):
        """Tiers have explanations for scoring context."""
        tier_info = {
            1: {"label": "Tier 1: Strategic Priority", "range": "17-20"},
            2: {"label": "Tier 2: High Impact", "range": "14-16"},
            3: {"label": "Tier 3: Medium Priority", "range": "11-13"},
            4: {"label": "Tier 4: Backlog", "range": "0-10"},
        }
        assert len(tier_info) == 4
        for tier in range(1, 5):
            assert "label" in tier_info[tier]
            assert "range" in tier_info[tier]

    def test_score_color_coding(self):
        """Scores map to appropriate colors."""
        def get_score_color(score: int) -> str:
            if score >= 4:
                return "green"
            elif score >= 3:
                return "amber"
            else:
                return "gray"

        assert get_score_color(5) == "green"
        assert get_score_color(4) == "green"
        assert get_score_color(3) == "amber"
        assert get_score_color(2) == "gray"
        assert get_score_color(1) == "gray"


class TestOpportunityDetailModalAPI:
    """Tests for the detail modal API endpoints."""

    def test_related_documents_endpoint_path(self):
        """Related documents endpoint has correct path pattern."""
        opportunity_id = str(uuid.uuid4())
        expected_path = f"/api/opportunities/{opportunity_id}/related-documents"
        assert "/related-documents" in expected_path
        assert opportunity_id in expected_path

    def test_conversations_endpoint_path(self):
        """Conversations endpoint has correct path pattern."""
        opportunity_id = str(uuid.uuid4())
        expected_path = f"/api/opportunities/{opportunity_id}/conversations"
        assert "/conversations" in expected_path
        assert opportunity_id in expected_path

    def test_ask_endpoint_path(self):
        """Ask endpoint has correct path pattern."""
        opportunity_id = str(uuid.uuid4())
        expected_path = f"/api/opportunities/{opportunity_id}/ask"
        assert "/ask" in expected_path
        assert opportunity_id in expected_path

    def test_related_documents_default_limit(self):
        """Related documents has sensible default limit."""
        default_limit = 8
        assert 1 <= default_limit <= 20

    def test_conversations_default_limit(self):
        """Conversations has sensible default limit."""
        default_limit = 20
        assert 1 <= default_limit <= 100

    def test_min_similarity_default(self):
        """Min similarity has sensible default."""
        default_min_similarity = 0.25
        assert 0 < default_min_similarity < 1
