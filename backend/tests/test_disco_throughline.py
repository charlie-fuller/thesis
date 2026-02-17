"""Tests for DISCO throughline functionality.

Covers:
- Pydantic model validation (_shared.py)
- Auto-ID generation (initiative_service.py)
- Prompt formatting (agent_service.py)
- Resolution parsing (agent_service.py)
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
# PYDANTIC MODEL TESTS
# ============================================================================


class TestPydanticModels:
    """Tests for throughline Pydantic models in _shared.py."""

    def test_problem_statement_basic(self):
        from api.routes.disco._shared import ProblemStatement

        ps = ProblemStatement(text="Test problem")
        assert ps.text == "Test problem"
        assert ps.id is None

    def test_problem_statement_with_id(self):
        from api.routes.disco._shared import ProblemStatement

        ps = ProblemStatement(id="ps-1", text="Test problem")
        assert ps.id == "ps-1"

    def test_hypothesis_defaults(self):
        from api.routes.disco._shared import Hypothesis

        h = Hypothesis(statement="Test hypothesis")
        assert h.type == "assumption"
        assert h.rationale is None

    def test_hypothesis_valid_types(self):
        from api.routes.disco._shared import Hypothesis

        for t in ("assumption", "belief", "prediction"):
            h = Hypothesis(statement="test", type=t)
            assert h.type == t

    def test_hypothesis_invalid_type_defaults(self):
        from api.routes.disco._shared import Hypothesis

        h = Hypothesis(statement="test", type="invalid")
        assert h.type == "assumption"

    def test_gap_defaults(self):
        from api.routes.disco._shared import Gap

        g = Gap(description="Test gap")
        assert g.type == "data"

    def test_gap_valid_types(self):
        from api.routes.disco._shared import Gap

        for t in ("data", "people", "process", "capability"):
            g = Gap(description="test", type=t)
            assert g.type == t

    def test_gap_invalid_type_defaults(self):
        from api.routes.disco._shared import Gap

        g = Gap(description="test", type="invalid")
        assert g.type == "data"

    def test_throughline_all_fields(self):
        from api.routes.disco._shared import (
            Gap,
            Hypothesis,
            ProblemStatement,
            Throughline,
        )

        t = Throughline(
            problem_statements=[ProblemStatement(text="p1")],
            hypotheses=[Hypothesis(statement="h1")],
            gaps=[Gap(description="g1")],
            desired_outcome_state="Success",
        )
        assert len(t.problem_statements) == 1
        assert len(t.hypotheses) == 1
        assert len(t.gaps) == 1
        assert t.desired_outcome_state == "Success"

    def test_throughline_empty(self):
        from api.routes.disco._shared import Throughline

        t = Throughline()
        assert t.problem_statements is None
        assert t.hypotheses is None
        assert t.gaps is None
        assert t.desired_outcome_state is None

    def test_throughline_resolution_full(self):
        from api.routes.disco._shared import (
            GapStatus,
            HypothesisResolution,
            SoWhat,
            StateChange,
            ThroughlineResolution,
        )

        tr = ThroughlineResolution(
            hypothesis_resolutions=[
                HypothesisResolution(
                    hypothesis_id="h-1",
                    status="confirmed",
                    evidence_summary="Strong evidence",
                )
            ],
            gap_statuses=[GapStatus(gap_id="g-1", status="addressed", findings="Done")],
            state_changes=[StateChange(description="Do X", owner="Alice")],
            so_what=SoWhat(
                state_change_proposed="Change Y",
                next_human_action="Review Z",
                kill_test="If W fails",
            ),
        )
        assert len(tr.hypothesis_resolutions) == 1
        assert tr.hypothesis_resolutions[0].status == "confirmed"
        assert tr.so_what.kill_test == "If W fails"

    def test_initiative_create_with_throughline(self):
        from api.routes.disco._shared import (
            InitiativeCreate,
            ProblemStatement,
            Throughline,
        )

        ic = InitiativeCreate(
            name="Test",
            throughline=Throughline(problem_statements=[ProblemStatement(text="problem")]),
        )
        assert ic.throughline is not None
        assert ic.throughline.problem_statements[0].text == "problem"

    def test_initiative_create_without_throughline(self):
        from api.routes.disco._shared import InitiativeCreate

        ic = InitiativeCreate(name="Test")
        assert ic.throughline is None

    def test_initiative_update_with_throughline(self):
        from api.routes.disco._shared import InitiativeUpdate, Throughline

        iu = InitiativeUpdate(throughline=Throughline(desired_outcome_state="Win"))
        assert iu.throughline.desired_outcome_state == "Win"


# ============================================================================
# AUTO-ID TESTS
# ============================================================================


class TestAutoIdThroughline:
    """Tests for _auto_id_throughline() in initiative_service.py."""

    def test_none_input(self):
        from services.disco.initiative_service import _auto_id_throughline

        assert _auto_id_throughline(None) is None

    def test_empty_dict(self):
        from services.disco.initiative_service import _auto_id_throughline

        result = _auto_id_throughline({})
        assert result == {}

    def test_assigns_problem_ids(self):
        from services.disco.initiative_service import _auto_id_throughline

        t = {"problem_statements": [{"text": "A"}, {"text": "B"}]}
        result = _auto_id_throughline(t)
        assert result["problem_statements"][0]["id"] == "ps-1"
        assert result["problem_statements"][1]["id"] == "ps-2"

    def test_assigns_hypothesis_ids(self):
        from services.disco.initiative_service import _auto_id_throughline

        t = {"hypotheses": [{"statement": "H1"}, {"statement": "H2"}]}
        result = _auto_id_throughline(t)
        assert result["hypotheses"][0]["id"] == "h-1"
        assert result["hypotheses"][1]["id"] == "h-2"

    def test_assigns_gap_ids(self):
        from services.disco.initiative_service import _auto_id_throughline

        t = {"gaps": [{"description": "G1"}]}
        result = _auto_id_throughline(t)
        assert result["gaps"][0]["id"] == "g-1"

    def test_preserves_existing_ids(self):
        from services.disco.initiative_service import _auto_id_throughline

        t = {
            "problem_statements": [
                {"id": "custom-ps", "text": "A"},
                {"text": "B"},
            ]
        }
        result = _auto_id_throughline(t)
        assert result["problem_statements"][0]["id"] == "custom-ps"
        assert result["problem_statements"][1]["id"] == "ps-2"

    def test_preserves_desired_outcome(self):
        from services.disco.initiative_service import _auto_id_throughline

        t = {"desired_outcome_state": "Success"}
        result = _auto_id_throughline(t)
        assert result["desired_outcome_state"] == "Success"

    def test_mixed_all_sections(self):
        from services.disco.initiative_service import _auto_id_throughline

        t = {
            "problem_statements": [{"text": "P"}],
            "hypotheses": [{"statement": "H", "id": "my-h"}],
            "gaps": [{"description": "G1"}, {"description": "G2"}],
        }
        result = _auto_id_throughline(t)
        assert result["problem_statements"][0]["id"] == "ps-1"
        assert result["hypotheses"][0]["id"] == "my-h"
        assert result["gaps"][0]["id"] == "g-1"
        assert result["gaps"][1]["id"] == "g-2"


# ============================================================================
# FORMAT FOR PROMPT TESTS
# ============================================================================


class TestFormatThroughlineForPrompt:
    """Tests for _format_throughline_for_prompt() in agent_service.py."""

    def test_empty_throughline(self):
        from services.disco.agent_service import _format_throughline_for_prompt

        result = _format_throughline_for_prompt({})
        assert result == ""

    def test_problem_statements_only(self):
        from services.disco.agent_service import _format_throughline_for_prompt

        t = {"problem_statements": [{"id": "ps-1", "text": "Problem A"}]}
        result = _format_throughline_for_prompt(t)
        assert "### Problem Statements" in result
        assert "**ps-1**: Problem A" in result

    def test_hypotheses_with_rationale(self):
        from services.disco.agent_service import _format_throughline_for_prompt

        t = {
            "hypotheses": [
                {
                    "id": "h-1",
                    "statement": "CMS AI accelerates adoption",
                    "type": "prediction",
                    "rationale": "Lower barrier",
                }
            ]
        }
        result = _format_throughline_for_prompt(t)
        assert "### Hypotheses" in result
        assert "**h-1** (prediction)" in result
        assert "Rationale: Lower barrier" in result

    def test_hypotheses_without_rationale(self):
        from services.disco.agent_service import _format_throughline_for_prompt

        t = {"hypotheses": [{"id": "h-1", "statement": "Test", "type": "assumption"}]}
        result = _format_throughline_for_prompt(t)
        assert "Rationale" not in result

    def test_gaps(self):
        from services.disco.agent_service import _format_throughline_for_prompt

        t = {
            "gaps": [
                {
                    "id": "g-1",
                    "description": "Missing competitive data",
                    "type": "data",
                }
            ]
        }
        result = _format_throughline_for_prompt(t)
        assert "### Known Gaps" in result
        assert "**g-1** [data]: Missing competitive data" in result

    def test_desired_outcome_state(self):
        from services.disco.agent_service import _format_throughline_for_prompt

        t = {"desired_outcome_state": "Clear roadmap with buy-in"}
        result = _format_throughline_for_prompt(t)
        assert "### Desired Outcome State" in result
        assert "Clear roadmap with buy-in" in result

    def test_missing_id_uses_question_mark(self):
        from services.disco.agent_service import _format_throughline_for_prompt

        t = {"problem_statements": [{"text": "No ID here"}]}
        result = _format_throughline_for_prompt(t)
        assert "**?**: No ID here" in result

    def test_full_throughline(self):
        from services.disco.agent_service import _format_throughline_for_prompt

        t = {
            "problem_statements": [{"id": "ps-1", "text": "Problem"}],
            "hypotheses": [{"id": "h-1", "statement": "Hyp", "type": "belief"}],
            "gaps": [{"id": "g-1", "description": "Gap", "type": "process"}],
            "desired_outcome_state": "Done",
        }
        result = _format_throughline_for_prompt(t)
        assert "Problem Statements" in result
        assert "Hypotheses" in result
        assert "Known Gaps" in result
        assert "Desired Outcome State" in result

    def test_rejected_problem_statements_filtered(self):
        from services.disco.agent_service import _format_throughline_for_prompt

        t = {
            "problem_statements": [
                {"id": "ps-1", "text": "Active problem"},
                {"id": "ps-2", "text": "Rejected problem", "rejected": True},
            ]
        }
        result = _format_throughline_for_prompt(t)
        assert "Active problem" in result
        assert "Rejected problem" not in result

    def test_rejected_hypotheses_filtered(self):
        from services.disco.agent_service import _format_throughline_for_prompt

        t = {
            "hypotheses": [
                {"id": "h-1", "statement": "Good hyp", "type": "assumption"},
                {"id": "h-2", "statement": "Bad hyp", "type": "belief", "rejected": True},
            ]
        }
        result = _format_throughline_for_prompt(t)
        assert "Good hyp" in result
        assert "Bad hyp" not in result

    def test_rejected_gaps_filtered(self):
        from services.disco.agent_service import _format_throughline_for_prompt

        t = {
            "gaps": [
                {"id": "g-1", "description": "Real gap", "type": "data"},
                {"id": "g-2", "description": "Not a gap", "type": "process", "rejected": True},
            ]
        }
        result = _format_throughline_for_prompt(t)
        assert "Real gap" in result
        assert "Not a gap" not in result

    def test_all_rejected_returns_empty_section(self):
        from services.disco.agent_service import _format_throughline_for_prompt

        t = {
            "problem_statements": [
                {"id": "ps-1", "text": "Rejected", "rejected": True},
            ]
        }
        result = _format_throughline_for_prompt(t)
        assert "Problem Statements" not in result


class TestBuildFullPromptUserCorrections:
    """Tests for user_corrections injection in build_full_prompt()."""

    def test_user_corrections_included(self):
        from services.disco.agent_service import build_full_prompt

        context = {
            "user_corrections": "The budget is $2M not $5M. Timeline is Q3 not Q4.",
        }
        result = build_full_prompt("discovery", context)
        assert "Ground-Truth Corrections" in result
        assert "AUTHORITATIVE" in result
        assert "The budget is $2M not $5M" in result

    def test_no_user_corrections(self):
        from services.disco.agent_service import build_full_prompt

        context = {}
        result = build_full_prompt("discovery", context)
        assert "Ground-Truth Corrections" not in result

    def test_empty_user_corrections_excluded(self):
        from services.disco.agent_service import build_full_prompt

        context = {"user_corrections": ""}
        result = build_full_prompt("discovery", context)
        assert "Ground-Truth Corrections" not in result


class TestModelRejectedFields:
    """Tests for rejected/rejection_reason fields on throughline models."""

    def test_problem_statement_rejected_field(self):
        from api.routes.disco._shared import ProblemStatement

        ps = ProblemStatement(text="Test", rejected=True, rejection_reason="Outdated")
        assert ps.rejected is True
        assert ps.rejection_reason == "Outdated"

    def test_hypothesis_rejected_field(self):
        from api.routes.disco._shared import Hypothesis

        h = Hypothesis(statement="Test", rejected=True, rejection_reason="Disproven")
        assert h.rejected is True

    def test_gap_rejected_field(self):
        from api.routes.disco._shared import Gap

        g = Gap(description="Test", rejected=True, rejection_reason="Resolved")
        assert g.rejected is True

    def test_initiative_update_user_corrections(self):
        from api.routes.disco._shared import InitiativeUpdate

        update = InitiativeUpdate(user_corrections="Budget is $2M")
        assert update.user_corrections == "Budget is $2M"

    def test_initiative_update_goal_alignment_details(self):
        from api.routes.disco._shared import InitiativeUpdate

        update = InitiativeUpdate(goal_alignment_details={"summary": "test"})
        assert update.goal_alignment_details == {"summary": "test"}


# ============================================================================
# PARSE RESOLUTION TESTS
# ============================================================================


class TestParseThroughlineResolution:
    """Tests for parse_throughline_resolution() in agent_service.py."""

    def test_no_resolution_section(self):
        from services.disco.agent_service import parse_throughline_resolution

        result = parse_throughline_resolution("## Summary\nSome text")
        assert result is None

    def test_hypothesis_resolutions(self):
        from services.disco.agent_service import parse_throughline_resolution

        output = """## Throughline Resolution

### Hypothesis Resolution
| ID | Status | Evidence Summary |
|----|--------|-----------------|
| h-1 | confirmed | Strong evidence found |
| h-2 | refuted | Contradicted by data |

## Next Steps
"""
        result = parse_throughline_resolution(output)
        assert result is not None
        assert len(result["hypothesis_resolutions"]) == 2
        assert result["hypothesis_resolutions"][0]["hypothesis_id"] == "h-1"
        assert result["hypothesis_resolutions"][0]["status"] == "confirmed"
        assert result["hypothesis_resolutions"][1]["status"] == "refuted"

    def test_gap_statuses(self):
        from services.disco.agent_service import parse_throughline_resolution

        output = """## Throughline Resolution

### Gap Status
| ID | Status | Findings |
|----|--------|----------|
| g-1 | addressed | Fully resolved |
| g-2 | partially_addressed | Needs more work |
| g-3 | unaddressed | Not investigated |

## Next Steps
"""
        result = parse_throughline_resolution(output)
        assert result is not None
        assert len(result["gap_statuses"]) == 3
        assert result["gap_statuses"][0]["status"] == "addressed"
        assert result["gap_statuses"][1]["status"] == "partially_addressed"
        assert result["gap_statuses"][2]["status"] == "unaddressed"

    def test_gap_status_with_space(self):
        from services.disco.agent_service import parse_throughline_resolution

        output = """## Throughline Resolution

### Gap Status
| ID | Status | Findings |
|----|--------|----------|
| g-1 | partially addressed | Some work done |
"""
        result = parse_throughline_resolution(output)
        assert result is not None
        assert result["gap_statuses"][0]["status"] == "partially_addressed"

    def test_state_changes_bullets(self):
        from services.disco.agent_service import parse_throughline_resolution

        output = """## Throughline Resolution

### Recommended State Changes
- Implement feature X
- Hire specialist Y

## Next Steps
"""
        result = parse_throughline_resolution(output)
        assert result is not None
        assert len(result["state_changes"]) == 2
        assert result["state_changes"][0]["description"] == "Implement feature X"

    def test_so_what_section(self):
        from services.disco.agent_service import parse_throughline_resolution

        output = """## Throughline Resolution

### So What?
**State Change Proposed:** Shift to AI-first strategy
**Next Human Action:** Present to exec team
**Kill Test:** If adoption < 2x in 6 months, pivot

## Next Steps
"""
        result = parse_throughline_resolution(output)
        assert result is not None
        assert result["so_what"]["state_change_proposed"] == "Shift to AI-first strategy"
        assert result["so_what"]["next_human_action"] == "Present to exec team"
        assert "adoption < 2x" in result["so_what"]["kill_test"]

    def test_so_what_without_bold(self):
        from services.disco.agent_service import parse_throughline_resolution

        output = """## Throughline Resolution

### So What?
State Change Proposed: Do X
Next Action: Do Y
Kill Test: If Z fails

## Next Steps
"""
        result = parse_throughline_resolution(output)
        assert result is not None
        assert result["so_what"]["state_change_proposed"] == "Do X"
        assert result["so_what"]["next_human_action"] == "Do Y"
        assert result["so_what"]["kill_test"] == "If Z fails"

    def test_full_resolution(self):
        from services.disco.agent_service import parse_throughline_resolution

        output = """## Executive Summary
Great work.

## Throughline Resolution

### Hypothesis Resolution
| ID | Status | Evidence Summary |
|----|--------|-----------------|
| h-1 | confirmed | Clear evidence |

### Gap Status
| ID | Status | Findings |
|----|--------|----------|
| g-1 | addressed | Complete |

### Recommended State Changes
- Change A
- Change B

### So What?
**State Change Proposed:** Big shift
**Next Human Action:** Review
**Kill Test:** If fails, stop

## Implementation Plan
Details here.
"""
        result = parse_throughline_resolution(output)
        assert result is not None
        assert len(result["hypothesis_resolutions"]) == 1
        assert len(result["gap_statuses"]) == 1
        assert len(result["state_changes"]) == 2
        assert result["so_what"]["state_change_proposed"] == "Big shift"

    def test_inconclusive_hypothesis(self):
        from services.disco.agent_service import parse_throughline_resolution

        output = """## Throughline Resolution

### Hypothesis Resolution
| ID | Status | Evidence Summary |
|----|--------|-----------------|
| h-1 | inconclusive | Mixed signals |
"""
        result = parse_throughline_resolution(output)
        assert result["hypothesis_resolutions"][0]["status"] == "inconclusive"
        assert "Mixed signals" in result["hypothesis_resolutions"][0]["evidence_summary"]

    def test_empty_resolution_section(self):
        from services.disco.agent_service import parse_throughline_resolution

        output = """## Throughline Resolution

No structured data here, just text.

## Next Steps
"""
        result = parse_throughline_resolution(output)
        assert result is None
