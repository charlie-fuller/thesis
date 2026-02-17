"""Tests for DISCO Problem Space Discipline Enhancement.

Covers:
- parse_assessment_sections() parser
- suggest_output_type() assessment integration
- solution_type field validation in Bundle models
- ResolutionAnnotations with initiative verdict fields
- KB_CATEGORIES completeness for new documents
- OUTPUT_TYPE_CONFIG assessment entry
- AGENT_FILES assessment_generator entry
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Ensure backend is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Environment is configured by conftest.py


@pytest.fixture(autouse=True)
def mock_supabase_client():
    """Mock the Supabase client to avoid URL validation issues in unit tests."""
    mock_client = MagicMock()
    mock_client.table.return_value.select.return_value.execute.return_value = MagicMock(data=[])
    with patch("database.DatabaseService._instance", mock_client):
        with patch("database.DatabaseService.get_client", return_value=mock_client):
            yield mock_client


# ============================================================================
# ASSESSMENT PARSER TESTS
# ============================================================================


class TestParseAssessmentSections:
    """Tests for parse_assessment_sections() in prd_service.py."""

    def test_basic_parsing(self):
        from services.disco.prd_service import parse_assessment_sections

        content = """# Data Coordination - Assessment

## Executive Summary

**Recommendation**: COORDINATE

This assessment recommends coordinating existing teams rather than building new tools.

## Problem Assessment

The problem is fundamentally about misaligned communication between teams.

## Solution Type: COORDINATE

### Definition
Aligning existing resources through better communication channels.

## Action Plan

### Immediate Actions (Week 1-2)

| # | Action | Owner | Deliverable |
|---|--------|-------|-------------|
| 1 | Set up weekly sync | PM Lead | Meeting invite |

## Cost Comparison: Solve vs. Live With It

Annual cost of status quo: $50K in wasted time.

## Success Criteria

### Leading Indicators (measure within 30 days)
- Handoff errors reduced by 50%

## Review Triggers

Re-evaluate if team grows beyond 20 people.

## Stakeholder Communication Plan

### Key Message
We're improving coordination, not building new tools.
"""
        result = parse_assessment_sections(content)
        assert result["output_type"] == "assessment"
        assert "executive_summary" in result
        assert "COORDINATE" in result["executive_summary"]
        assert result["recommendation_type"] == "coordinate"
        assert "problem_assessment" in result
        assert "action_plan" in result
        assert "cost_comparison" in result
        assert "success_criteria" in result
        assert "review_triggers" in result
        assert "stakeholder_communication" in result

    def test_recommendation_type_extraction(self):
        from services.disco.prd_service import parse_assessment_sections

        for rec_type in ["COORDINATE", "TRAIN", "RESTRUCTURE", "GOVERN", "DOCUMENT", "DEFER", "ACCEPT"]:
            content = f"""## Executive Summary

**Recommendation**: {rec_type}

Brief summary.

## Problem Assessment

Some problem.
"""
            result = parse_assessment_sections(content)
            assert result["recommendation_type"] == rec_type.lower()

    def test_empty_content(self):
        from services.disco.prd_service import parse_assessment_sections

        result = parse_assessment_sections("")
        assert result["output_type"] == "assessment"
        assert "executive_summary" not in result

    def test_partial_content(self):
        from services.disco.prd_service import parse_assessment_sections

        content = """## Executive Summary

Just an executive summary, no other sections.
"""
        result = parse_assessment_sections(content)
        assert result["output_type"] == "assessment"
        assert "executive_summary" in result
        assert "action_plan" not in result


# ============================================================================
# OUTPUT TYPE CONFIG TESTS
# ============================================================================


class TestOutputTypeConfig:
    """Tests for OUTPUT_TYPE_CONFIG including assessment."""

    def test_assessment_in_config(self):
        from services.disco.prd_service import OUTPUT_TYPE_CONFIG

        assert "assessment" in OUTPUT_TYPE_CONFIG
        config = OUTPUT_TYPE_CONFIG["assessment"]
        assert config["agent_prompt"] == "assessment_generator"
        assert config["parser"] == "parse_assessment_sections"
        assert config["label"] == "Assessment"

    def test_all_output_types_present(self):
        from services.disco.prd_service import OUTPUT_TYPE_CONFIG

        expected = {"prd", "evaluation_framework", "decision_framework", "assessment"}
        assert set(OUTPUT_TYPE_CONFIG.keys()) == expected

    def test_all_configs_have_required_fields(self):
        from services.disco.prd_service import OUTPUT_TYPE_CONFIG

        for name, config in OUTPUT_TYPE_CONFIG.items():
            assert "agent_prompt" in config, f"{name} missing agent_prompt"
            assert "parser" in config, f"{name} missing parser"
            assert "label" in config, f"{name} missing label"
            assert "description" in config, f"{name} missing description"


class TestGetSectionParser:
    """Tests for get_section_parser() including assessment."""

    def test_assessment_parser_returned(self):
        from services.disco.prd_service import get_section_parser, parse_assessment_sections

        parser = get_section_parser("assessment")
        assert parser == parse_assessment_sections

    def test_unknown_type_defaults_to_prd(self):
        from services.disco.prd_service import get_section_parser, parse_prd_sections

        parser = get_section_parser("unknown_type")
        assert parser == parse_prd_sections

    def test_all_output_types_have_parsers(self):
        from services.disco.prd_service import OUTPUT_TYPE_CONFIG, get_section_parser

        for output_type in OUTPUT_TYPE_CONFIG:
            parser = get_section_parser(output_type)
            assert callable(parser), f"No parser for {output_type}"


# ============================================================================
# AGENT FILES TESTS
# ============================================================================


class TestAgentFiles:
    """Tests for AGENT_FILES including assessment_generator."""

    def test_assessment_generator_registered(self):
        from services.disco.agent_service import AGENT_FILES

        assert "assessment_generator" in AGENT_FILES
        assert AGENT_FILES["assessment_generator"] == "assessment-generator-v1.1.md"

    def test_all_output_generators_registered(self):
        from services.disco.agent_service import AGENT_FILES

        generators = [
            "prd_generator",
            "evaluation_framework_generator",
            "decision_framework_generator",
            "assessment_generator",
        ]
        for gen in generators:
            assert gen in AGENT_FILES, f"{gen} not in AGENT_FILES"

    def test_consolidated_agents_updated_versions(self):
        from services.disco.agent_service import AGENT_FILES

        assert AGENT_FILES["discovery_guide"] == "discovery-guide-v2.0.md"
        assert AGENT_FILES["insight_analyst"] == "insight-analyst-v1.2.md"
        assert AGENT_FILES["initiative_builder"] == "initiative-builder-v1.2.md"
        assert AGENT_FILES["requirements_generator"] == "requirements-generator-v1.4.md"


# ============================================================================
# SOLUTION TYPE VALIDATION TESTS
# ============================================================================


class TestSolutionTypeValidation:
    """Tests for solution_type field on BundleCreate and BundleUpdate."""

    def test_bundle_create_valid_solution_types(self):
        from api.routes.disco._shared import BundleCreate

        valid_types = ["build", "buy", "govern", "coordinate", "train", "restructure", "document", "defer", "accept"]
        for st in valid_types:
            bundle = BundleCreate(name="Test", description="Test", solution_type=st)
            assert bundle.solution_type == st

    def test_bundle_create_none_solution_type(self):
        from api.routes.disco._shared import BundleCreate

        bundle = BundleCreate(name="Test", description="Test")
        assert bundle.solution_type is None

    def test_bundle_create_invalid_solution_type(self):
        from api.routes.disco._shared import BundleCreate

        with pytest.raises(Exception):
            BundleCreate(name="Test", description="Test", solution_type="invalid")

    def test_bundle_update_valid_solution_types(self):
        from api.routes.disco._shared import BundleUpdate

        for st in ["build", "coordinate", "accept"]:
            update = BundleUpdate(solution_type=st)
            assert update.solution_type == st

    def test_bundle_update_invalid_solution_type(self):
        from api.routes.disco._shared import BundleUpdate

        with pytest.raises(Exception):
            BundleUpdate(solution_type="magic")

    def test_valid_solution_types_constant(self):
        from api.routes.disco._shared import VALID_SOLUTION_TYPES

        expected = {"build", "buy", "govern", "coordinate", "train", "restructure", "document", "defer", "accept"}
        assert VALID_SOLUTION_TYPES == expected


# ============================================================================
# INITIATIVE VERDICT TESTS
# ============================================================================


class TestInitiativeVerdict:
    """Tests for ResolutionAnnotations with initiative verdict fields."""

    def test_resolution_annotations_backward_compatible(self):
        from api.routes.disco._shared import ResolutionAnnotations

        ra = ResolutionAnnotations(
            hypothesis_overrides={"h-1": {"status": "confirmed"}},
            gap_overrides={"g-1": {"status": "addressed"}},
        )
        assert ra.hypothesis_overrides is not None
        assert ra.initiative_verdict is None
        assert ra.defer_until is None
        assert ra.accept_rationale is None

    def test_resolution_annotations_with_verdict(self):
        from api.routes.disco._shared import ResolutionAnnotations

        for verdict in ["proceed", "defer", "accept", "no_action"]:
            ra = ResolutionAnnotations(initiative_verdict=verdict)
            assert ra.initiative_verdict == verdict

    def test_resolution_annotations_defer_with_date(self):
        from api.routes.disco._shared import ResolutionAnnotations

        ra = ResolutionAnnotations(
            initiative_verdict="defer",
            defer_until="2026-Q3",
        )
        assert ra.initiative_verdict == "defer"
        assert ra.defer_until == "2026-Q3"

    def test_resolution_annotations_accept_with_rationale(self):
        from api.routes.disco._shared import ResolutionAnnotations

        ra = ResolutionAnnotations(
            initiative_verdict="accept",
            accept_rationale="Cost of solving exceeds value; workarounds adequate",
        )
        assert ra.initiative_verdict == "accept"
        assert "workarounds" in ra.accept_rationale

    def test_resolution_annotations_invalid_verdict(self):
        from api.routes.disco._shared import ResolutionAnnotations

        with pytest.raises(Exception):
            ResolutionAnnotations(initiative_verdict="maybe")

    def test_valid_initiative_verdicts_constant(self):
        from api.routes.disco._shared import VALID_INITIATIVE_VERDICTS

        expected = {"proceed", "defer", "accept", "no_action"}
        assert VALID_INITIATIVE_VERDICTS == expected


# ============================================================================
# KB CATEGORIES TESTS
# ============================================================================


class TestKBCategories:
    """Tests for KB_CATEGORIES completeness."""

    def test_new_kb_documents_registered(self):
        from services.disco.system_kb_service import KB_CATEGORIES

        new_docs = [
            "five-whys-deep-methodology.md",
            "jobs-to-be-done-framework.md",
            "problem-space-discipline.md",
            "evidence-evaluation-framework.md",
            "pattern-library-reference.md",
            "decision-science-frameworks.md",
            "clustering-methodology.md",
            "requirements-prioritization-heuristics.md",
            "solution-type-taxonomy.md",
            "non-build-solution-patterns.md",
            "decision-forcing-canvas.md",
        ]
        for doc in new_docs:
            assert doc in KB_CATEGORIES, f"{doc} not in KB_CATEGORIES"

    def test_correct_categories(self):
        from services.disco.system_kb_service import KB_CATEGORIES

        assert KB_CATEGORIES["five-whys-deep-methodology.md"] == "methodology"
        assert KB_CATEGORIES["jobs-to-be-done-framework.md"] == "methodology"
        assert KB_CATEGORIES["problem-space-discipline.md"] == "methodology"
        assert KB_CATEGORIES["evidence-evaluation-framework.md"] == "analysis"
        assert KB_CATEGORIES["pattern-library-reference.md"] == "analysis"
        assert KB_CATEGORIES["decision-science-frameworks.md"] == "decision"
        assert KB_CATEGORIES["clustering-methodology.md"] == "methodology"
        assert KB_CATEGORIES["requirements-prioritization-heuristics.md"] == "methodology"
        assert KB_CATEGORIES["solution-type-taxonomy.md"] == "decision"
        assert KB_CATEGORIES["non-build-solution-patterns.md"] == "decision"
        assert KB_CATEGORIES["decision-forcing-canvas.md"] == "decision"

    def test_total_kb_count(self):
        from services.disco.system_kb_service import KB_CATEGORIES

        # 19 original + 10 new + 1 canvas = 30
        assert len(KB_CATEGORIES) >= 30


# ============================================================================
# KB FILE EXISTENCE TESTS
# ============================================================================


class TestKBFilesExist:
    """Tests that all new KB files exist on disk."""

    KB_DIR = os.path.join(os.path.dirname(__file__), "..", "disco_agents", "KB")

    @pytest.mark.parametrize(
        "filename",
        [
            "five-whys-deep-methodology.md",
            "jobs-to-be-done-framework.md",
            "problem-space-discipline.md",
            "evidence-evaluation-framework.md",
            "pattern-library-reference.md",
            "decision-science-frameworks.md",
            "clustering-methodology.md",
            "requirements-prioritization-heuristics.md",
            "solution-type-taxonomy.md",
            "non-build-solution-patterns.md",
            "decision-forcing-canvas.md",
        ],
    )
    def test_kb_file_exists(self, filename):
        filepath = os.path.join(self.KB_DIR, filename)
        assert os.path.exists(filepath), f"KB file missing: {filename}"

    @pytest.mark.parametrize(
        "filename",
        [
            "five-whys-deep-methodology.md",
            "jobs-to-be-done-framework.md",
            "problem-space-discipline.md",
            "evidence-evaluation-framework.md",
            "pattern-library-reference.md",
            "decision-science-frameworks.md",
            "clustering-methodology.md",
            "requirements-prioritization-heuristics.md",
            "solution-type-taxonomy.md",
            "non-build-solution-patterns.md",
            "decision-forcing-canvas.md",
        ],
    )
    def test_kb_file_not_empty(self, filename):
        filepath = os.path.join(self.KB_DIR, filename)
        size = os.path.getsize(filepath)
        assert size > 5000, f"KB file too small ({size} bytes): {filename}"


# ============================================================================
# AGENT PROMPT FILE EXISTENCE TESTS
# ============================================================================


class TestAgentPromptFiles:
    """Tests that updated agent prompt files exist."""

    AGENTS_DIR = os.path.join(os.path.dirname(__file__), "..", "disco_agents")

    @pytest.mark.parametrize(
        "filename",
        [
            "discovery-guide-v2.0.md",
            "insight-analyst-v1.2.md",
            "initiative-builder-v1.2.md",
            "requirements-generator-v1.4.md",
            "assessment-generator-v1.1.md",
        ],
    )
    def test_agent_prompt_exists(self, filename):
        filepath = os.path.join(self.AGENTS_DIR, filename)
        assert os.path.exists(filepath), f"Agent prompt missing: {filename}"


# ============================================================================
# BUNDLE APPROVAL MODEL TEST
# ============================================================================


class TestBundleApproval:
    """Tests for BundleApproval model with assessment output type."""

    def test_assessment_output_type(self):
        from api.routes.disco._shared import BundleApproval

        approval = BundleApproval(output_type="assessment")
        assert approval.output_type == "assessment"

    def test_default_output_type_is_prd(self):
        from api.routes.disco._shared import BundleApproval

        approval = BundleApproval()
        assert approval.output_type == "prd"

    def test_all_valid_output_types(self):
        from api.routes.disco._shared import BundleApproval

        for ot in ["prd", "evaluation_framework", "decision_framework", "assessment"]:
            approval = BundleApproval(output_type=ot)
            assert approval.output_type == ot


# ============================================================================
# MIGRATION FILE TEST
# ============================================================================


class TestMigrationFile:
    """Tests that the migration file exists and has correct content."""

    MIGRATION_PATH = os.path.join(
        os.path.dirname(__file__), "..", "..", "database", "migrations", "073_solution_type_and_verdicts.sql"
    )

    def test_migration_file_exists(self):
        assert os.path.exists(self.MIGRATION_PATH), "Migration 073 not found"

    def test_migration_adds_solution_type(self):
        with open(self.MIGRATION_PATH) as f:
            content = f.read()
        assert "solution_type" in content
        assert "disco_bundles" in content
        assert "ALTER TABLE" in content
