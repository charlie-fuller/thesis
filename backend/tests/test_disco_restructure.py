"""Tests for DISCO Pipeline Restructuring (Change 1-7).

Covers:
- New Pydantic models: ValueAlignment, CreateTasksFromResolution, ResolutionAnnotations
- parse_triage_suggestions() in agent_service.py
- create_project_from_bundle() score mapping in project_service.py
- _priority_to_int() and _parse_due_date() helpers in initiatives.py
- Updated allowed_fields in initiative_service.py
"""

import os
import sys

import pytest

# Ensure backend is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Set required env vars before imports
os.environ.setdefault("SUPABASE_URL", "https://fake.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "fake-key")
os.environ.setdefault("SUPABASE_KEY", "fake-key")
os.environ.setdefault("ANTHROPIC_API_KEY", "fake-key")


# ============================================================================
# PYDANTIC MODEL TESTS - New Models
# ============================================================================


class TestValueAlignmentModel:
    """Tests for ValueAlignment Pydantic model."""

    def test_value_alignment_empty(self):
        from api.routes.disco._shared import ValueAlignment

        va = ValueAlignment()
        assert va.kpis is None
        assert va.department_goals is None
        assert va.company_priority is None
        assert va.strategic_pillar is None
        assert va.notes is None

    def test_value_alignment_full(self):
        from api.routes.disco._shared import ValueAlignment

        va = ValueAlignment(
            kpis=["Time to fill", "Cost per hire"],
            department_goals=["Eliminate manual recruiting overhead"],
            company_priority="Cost-Efficient GTM Growth",
            strategic_pillar="operationalize",
            notes="Discovered during kickoff with Bella",
        )
        assert len(va.kpis) == 2
        assert va.kpis[0] == "Time to fill"
        assert va.strategic_pillar == "operationalize"

    def test_value_alignment_partial(self):
        from api.routes.disco._shared import ValueAlignment

        va = ValueAlignment(kpis=["Revenue growth"])
        assert va.kpis == ["Revenue growth"]
        assert va.department_goals is None

    def test_value_alignment_valid_pillars(self):
        from api.routes.disco._shared import ValueAlignment

        for pillar in ("enable", "operationalize", "govern"):
            va = ValueAlignment(strategic_pillar=pillar)
            assert va.strategic_pillar == pillar


class TestCreateTasksFromResolutionModel:
    """Tests for CreateTasksFromResolution Pydantic model."""

    def test_basic(self):
        from api.routes.disco._shared import CreateTasksFromResolution

        model = CreateTasksFromResolution(output_id="out-123")
        assert model.output_id == "out-123"
        assert model.project_id is None
        assert model.selected_indices is None

    def test_with_project_and_indices(self):
        from api.routes.disco._shared import CreateTasksFromResolution

        model = CreateTasksFromResolution(
            output_id="out-123",
            project_id="proj-456",
            selected_indices=[0, 2, 3],
        )
        assert model.project_id == "proj-456"
        assert model.selected_indices == [0, 2, 3]

    def test_empty_indices(self):
        from api.routes.disco._shared import CreateTasksFromResolution

        model = CreateTasksFromResolution(output_id="out-123", selected_indices=[])
        assert model.selected_indices == []


class TestResolutionAnnotationsModel:
    """Tests for ResolutionAnnotations Pydantic model."""

    def test_empty(self):
        from api.routes.disco._shared import ResolutionAnnotations

        ra = ResolutionAnnotations()
        assert ra.hypothesis_overrides is None
        assert ra.gap_overrides is None

    def test_hypothesis_override(self):
        from api.routes.disco._shared import ResolutionAnnotations

        ra = ResolutionAnnotations(
            hypothesis_overrides={"h-1": {"status": "refuted", "note": "Disproved in Q1 review"}}
        )
        assert ra.hypothesis_overrides["h-1"]["status"] == "refuted"

    def test_gap_override(self):
        from api.routes.disco._shared import ResolutionAnnotations

        ra = ResolutionAnnotations(gap_overrides={"g-2": {"status": "addressed", "note": "Resolved with new tool"}})
        assert ra.gap_overrides["g-2"]["status"] == "addressed"

    def test_both_overrides(self):
        from api.routes.disco._shared import ResolutionAnnotations

        ra = ResolutionAnnotations(
            hypothesis_overrides={"h-1": {"status": "confirmed"}},
            gap_overrides={"g-1": {"status": "still_open"}},
        )
        assert "h-1" in ra.hypothesis_overrides
        assert "g-1" in ra.gap_overrides


class TestInitiativeModelsWithNewFields:
    """Tests for InitiativeCreate/Update with new fields."""

    def test_create_with_value_alignment(self):
        from api.routes.disco._shared import InitiativeCreate, ValueAlignment

        ic = InitiativeCreate(
            name="Test Discovery",
            target_department="People",
            value_alignment=ValueAlignment(kpis=["Time to fill"]),
        )
        assert ic.target_department == "People"
        assert ic.value_alignment.kpis == ["Time to fill"]

    def test_create_with_stakeholders(self):
        from api.routes.disco._shared import InitiativeCreate

        ic = InitiativeCreate(
            name="Test",
            sponsor_stakeholder_id="stake-123",
            stakeholder_ids=["stake-456", "stake-789"],
        )
        assert ic.sponsor_stakeholder_id == "stake-123"
        assert len(ic.stakeholder_ids) == 2

    def test_update_with_value_alignment(self):
        from api.routes.disco._shared import InitiativeUpdate, ValueAlignment

        iu = InitiativeUpdate(
            value_alignment=ValueAlignment(
                strategic_pillar="govern",
                department_goals=["Reduce risk"],
            )
        )
        assert iu.value_alignment.strategic_pillar == "govern"

    def test_update_with_resolution_annotations(self):
        from api.routes.disco._shared import InitiativeUpdate, ResolutionAnnotations

        iu = InitiativeUpdate(
            resolution_annotations=ResolutionAnnotations(hypothesis_overrides={"h-1": {"status": "refuted"}})
        )
        assert iu.resolution_annotations.hypothesis_overrides["h-1"]["status"] == "refuted"


# ============================================================================
# PARSE TRIAGE SUGGESTIONS TESTS
# ============================================================================


class TestParseTrigeSuggestions:
    """Tests for parse_triage_suggestions() in agent_service.py."""

    def test_no_section(self):
        from services.disco.agent_service import parse_triage_suggestions

        result = parse_triage_suggestions("## Summary\nJust a summary.")
        assert result is None

    def test_problem_statements(self):
        from services.disco.agent_service import parse_triage_suggestions

        output = """## Suggested Framing

### Suggested Problem Statements
- Enterprise onboarding takes too long
- Customer churn is 2x industry average

## Next Steps
"""
        result = parse_triage_suggestions(output)
        assert result is not None
        assert len(result["problem_statements"]) == 2
        assert result["problem_statements"][0]["text"] == "Enterprise onboarding takes too long"
        assert result["problem_statements"][0]["id"] == "ps-1"

    def test_hypotheses(self):
        from services.disco.agent_service import parse_triage_suggestions

        output = """## Suggested Framing

### Suggested Hypotheses
- AI-assisted onboarding will reduce time-to-value by 40%
- Self-service portal adoption depends on executive sponsorship

## Next Steps
"""
        result = parse_triage_suggestions(output)
        assert result is not None
        assert len(result["hypotheses"]) == 2
        assert result["hypotheses"][0]["type"] == "assumption"
        assert "onboarding" in result["hypotheses"][0]["statement"]

    def test_hypotheses_with_rationale(self):
        from services.disco.agent_service import parse_triage_suggestions

        output = """## Suggested Framing

### Suggested Hypotheses
- AI onboarding accelerates adoption (Rationale: Lower barrier to entry)

## Next Steps
"""
        result = parse_triage_suggestions(output)
        assert result is not None
        assert result["hypotheses"][0]["rationale"] == "Lower barrier to entry"
        assert "Rationale" not in result["hypotheses"][0]["statement"]

    def test_gaps_with_types(self):
        from services.disco.agent_service import parse_triage_suggestions

        output = """## Suggested Framing

### Suggested Gaps
- data: No metrics on current processing time
- people: No executive sponsor identified
- process: No documented onboarding workflow

## Next Steps
"""
        result = parse_triage_suggestions(output)
        assert result is not None
        assert len(result["gaps"]) == 3
        assert result["gaps"][0]["type"] == "data"
        assert result["gaps"][1]["type"] == "people"
        assert result["gaps"][2]["type"] == "process"

    def test_kpis(self):
        from services.disco.agent_service import parse_triage_suggestions

        output = """## Suggested Framing

### Suggested KPIs
- Time to fill
- Cost per hire
- Employee satisfaction score

## Next Steps
"""
        result = parse_triage_suggestions(output)
        assert result is not None
        assert len(result["kpis"]) == 3
        assert result["kpis"][0] == "Time to fill"

    def test_stakeholders(self):
        from services.disco.agent_service import parse_triage_suggestions

        output = """## Suggested Framing

### Suggested Stakeholders
- VP Engineering
- Head of People
- CTO

## Next Steps
"""
        result = parse_triage_suggestions(output)
        assert result is not None
        assert len(result["stakeholders"]) == 3
        assert "VP Engineering" in result["stakeholders"]

    def test_value_alignment_notes(self):
        from services.disco.agent_service import parse_triage_suggestions

        output = """## Suggested Framing

### Value Alignment Notes
This discovery aligns with the People team's FY27 goal to reduce manual recruiting overhead.

## Next Steps
"""
        result = parse_triage_suggestions(output)
        assert result is not None
        assert "People team" in result["value_alignment_notes"]

    def test_full_suggested_framing(self):
        from services.disco.agent_service import parse_triage_suggestions

        output = """## Triage Assessment
GO - proceed with discovery.

## Suggested Framing

### Suggested Problem Statements
- Problem A
- Problem B

### Suggested Hypotheses
- Hypothesis X

### Suggested Gaps
- data: Missing data gap

### Suggested KPIs
- KPI One

### Suggested Stakeholders
- Person Alpha

### Value Alignment Notes
Aligns with strategic goal Z.

## Recommendation
Proceed to discovery planning.
"""
        result = parse_triage_suggestions(output)
        assert result is not None
        assert len(result["problem_statements"]) == 2
        assert len(result["hypotheses"]) == 1
        assert len(result["gaps"]) == 1
        assert len(result["kpis"]) == 1
        assert len(result["stakeholders"]) == 1
        assert "strategic goal Z" in result["value_alignment_notes"]

    def test_empty_section_returns_none(self):
        from services.disco.agent_service import parse_triage_suggestions

        output = """## Suggested Framing

No structured suggestions available.

## Next Steps
"""
        result = parse_triage_suggestions(output)
        assert result is None

    def test_problem_statements_with_ids(self):
        from services.disco.agent_service import parse_triage_suggestions

        output = """## Suggested Framing

### Suggested Problem Statements
- [ps-1] First problem
- [ps-2] Second problem

## Next Steps
"""
        result = parse_triage_suggestions(output)
        assert result is not None
        assert result["problem_statements"][0]["id"] == "ps-1"
        assert result["problem_statements"][1]["id"] == "ps-2"


# ============================================================================
# PRIORITY AND DATE HELPER TESTS
# ============================================================================


class TestPriorityToInt:
    """Tests for _priority_to_int() helper in initiatives.py."""

    def test_critical(self):
        from api.routes.disco.initiatives import _priority_to_int

        assert _priority_to_int("critical") == 5

    def test_high(self):
        from api.routes.disco.initiatives import _priority_to_int

        assert _priority_to_int("high") == 4

    def test_medium(self):
        from api.routes.disco.initiatives import _priority_to_int

        assert _priority_to_int("medium") == 3

    def test_low(self):
        from api.routes.disco.initiatives import _priority_to_int

        assert _priority_to_int("low") == 2

    def test_none_returns_default(self):
        from api.routes.disco.initiatives import _priority_to_int

        assert _priority_to_int(None) == 3

    def test_unknown_returns_default(self):
        from api.routes.disco.initiatives import _priority_to_int

        assert _priority_to_int("unknown") == 3

    def test_case_insensitive(self):
        from api.routes.disco.initiatives import _priority_to_int

        assert _priority_to_int("HIGH") == 4
        assert _priority_to_int("Critical") == 5

    def test_whitespace_stripped(self):
        from api.routes.disco.initiatives import _priority_to_int

        assert _priority_to_int("  high  ") == 4


class TestParseDueDate:
    """Tests for _parse_due_date() helper in initiatives.py."""

    def test_none_input(self):
        from api.routes.disco.initiatives import _parse_due_date

        assert _parse_due_date(None) is None

    def test_empty_string(self):
        from api.routes.disco.initiatives import _parse_due_date

        assert _parse_due_date("") is None

    def test_iso_format(self):
        from api.routes.disco.initiatives import _parse_due_date

        result = _parse_due_date("2026-03-15")
        assert result == "2026-03-15"

    def test_us_format(self):
        from api.routes.disco.initiatives import _parse_due_date

        result = _parse_due_date("03/15/2026")
        assert result == "2026-03-15"

    def test_long_month_format(self):
        from api.routes.disco.initiatives import _parse_due_date

        result = _parse_due_date("March 15, 2026")
        assert result == "2026-03-15"

    def test_short_month_format(self):
        from api.routes.disco.initiatives import _parse_due_date

        result = _parse_due_date("Mar 15, 2026")
        assert result == "2026-03-15"

    def test_invalid_date_returns_none(self):
        from api.routes.disco.initiatives import _parse_due_date

        assert _parse_due_date("next tuesday") is None

    def test_unparseable_returns_none(self):
        from api.routes.disco.initiatives import _parse_due_date

        assert _parse_due_date("ASAP") is None


# ============================================================================
# SCORE MAPPING TESTS
# ============================================================================


class TestScoreMapping:
    """Tests for score mapping constants in project_service.py."""

    def test_score_map_values(self):
        from services.disco.project_service import _SCORE_MAP

        assert _SCORE_MAP["HIGH"] == 5
        assert _SCORE_MAP["MEDIUM"] == 3
        assert _SCORE_MAP["LOW"] == 1

    def test_inverse_score_map_values(self):
        from services.disco.project_service import _INVERSE_SCORE_MAP

        # High feasibility = low effort
        assert _INVERSE_SCORE_MAP["HIGH"] == 1
        assert _INVERSE_SCORE_MAP["MEDIUM"] == 3
        assert _INVERSE_SCORE_MAP["LOW"] == 5

    def test_score_map_default(self):
        from services.disco.project_service import _SCORE_MAP

        assert _SCORE_MAP.get("UNKNOWN", 3) == 3


# ============================================================================
# ALLOWED FIELDS TESTS
# ============================================================================


class TestAllowedFields:
    """Tests that new fields are in allowed_fields for initiative updates."""

    def test_new_fields_in_allowed(self):
        """Verify all new restructuring fields are allowed for update."""
        import inspect

        from services.disco.initiative_service import update_initiative

        source = inspect.getsource(update_initiative)
        # These fields should be in the allowed_fields set
        for field in [
            "target_department",
            "value_alignment",
            "sponsor_stakeholder_id",
            "stakeholder_ids",
            "resolution_annotations",
        ]:
            assert field in source, f"{field} not found in update_initiative"
