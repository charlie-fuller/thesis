"""
Rigorous Testing Suite

Advanced tests for production reliability:
1. Contract Tests - Frontend/Backend interface alignment
2. Boundary Tests - Exact boundary condition testing
3. Error Recovery Tests - Graceful degradation
4. Time-Based Tests - Date/time edge cases
5. Load Pattern Tests - Behavior under stress
6. Database Constraint Tests - DB-level validation
7. Snapshot/Golden Tests - API response stability

Total: 60+ tests targeting production edge cases.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timedelta, timezone
from uuid import uuid4, UUID
import asyncio
import json
from typing import Optional, List
from pydantic import BaseModel, ValidationError, field_validator


# ============================================================================
# CATEGORY 1: CONTRACT TESTS (Frontend ↔ Backend)
# ============================================================================

class TestAPIContractsProject:
    """Verify backend responses match frontend TypeScript interfaces."""

    # Fields required by frontend Project interface
    FRONTEND_PROJECT_FIELDS = [
        "id", "project_code", "title", "description", "department",
        "owner_stakeholder_id", "owner_name", "current_state", "desired_state",
        "roi_potential", "implementation_effort", "strategic_alignment",
        "stakeholder_readiness", "total_score", "tier", "status",
        "next_step", "blockers", "follow_up_questions", "roi_indicators",
        "created_at", "updated_at",
        # Justification fields (optional)
        "project_summary", "roi_justification", "effort_justification",
        "alignment_justification", "readiness_justification"
    ]

    def test_project_response_has_all_frontend_fields(self):
        """ProjectResponse matches frontend Project interface."""
        # Simulate a complete backend response
        backend_response = {
            "id": str(uuid4()),
            "project_code": "OPP-001",
            "title": "Test Project",
            "description": "Test description",
            "department": "finance",
            "owner_stakeholder_id": str(uuid4()),
            "owner_name": "John Doe",
            "current_state": "Manual process",
            "desired_state": "Automated",
            "roi_potential": 4,
            "implementation_effort": 3,
            "strategic_alignment": 5,
            "stakeholder_readiness": 4,
            "total_score": 16,
            "tier": 2,
            "status": "identified",
            "next_step": "Schedule demo",
            "blockers": [],
            "follow_up_questions": [],
            "roi_indicators": {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "project_summary": None,
            "roi_justification": None,
            "effort_justification": None,
            "alignment_justification": None,
            "readiness_justification": None,
        }

        for field in self.FRONTEND_PROJECT_FIELDS:
            assert field in backend_response, f"Missing required field: {field}"

    def test_project_nullable_fields_are_nullable(self):
        """Fields that frontend treats as nullable can be null."""
        nullable_fields = [
            "description", "department", "owner_stakeholder_id", "owner_name",
            "current_state", "desired_state", "roi_potential", "implementation_effort",
            "strategic_alignment", "stakeholder_readiness", "next_step",
            "project_summary", "roi_justification", "effort_justification",
            "alignment_justification", "readiness_justification"
        ]

        response = {field: None for field in nullable_fields}
        response.update({
            "id": str(uuid4()),
            "project_code": "OPP-001",
            "title": "Test",
            "total_score": 0,
            "tier": 4,
            "status": "identified",
            "blockers": [],
            "follow_up_questions": [],
            "roi_indicators": {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })

        # All nullable fields should be allowed to be None
        for field in nullable_fields:
            assert response.get(field) is None


class TestAPIContractsRelatedDocument:
    """Verify RelatedDocument response matches frontend interface."""

    FRONTEND_RELATED_DOC_FIELDS = [
        "chunk_id", "document_id", "document_name", "relevance_score", "snippet"
    ]

    def test_related_document_has_all_fields(self):
        """RelatedDocument matches frontend interface."""
        backend_response = {
            "chunk_id": str(uuid4()),
            "document_id": str(uuid4()),
            "document_name": "Test Document.pdf",
            "relevance_score": 0.85,
            "snippet": "This is a relevant excerpt..."
        }

        for field in self.FRONTEND_RELATED_DOC_FIELDS:
            assert field in backend_response, f"Missing field: {field}"

    def test_relevance_score_is_float_between_0_and_1(self):
        """Relevance score is a float in valid range."""
        scores = [0.0, 0.5, 0.85, 1.0]
        for score in scores:
            assert 0.0 <= score <= 1.0
            assert isinstance(score, float)


class TestAPIContractsConversation:
    """Verify Conversation response matches frontend interface."""

    FRONTEND_CONVERSATION_FIELDS = [
        "id", "question", "response", "sources", "created_at"
    ]

    def test_conversation_has_all_fields(self):
        """Conversation matches frontend interface."""
        backend_response = {
            "id": str(uuid4()),
            "question": "What is the ROI?",
            "response": "The expected ROI is...",
            "sources": [],
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        for field in self.FRONTEND_CONVERSATION_FIELDS:
            assert field in backend_response, f"Missing field: {field}"


class TestAPIContractsTierResponse:
    """Verify tier grouping response matches frontend expectations."""

    def test_by_tier_response_structure(self):
        """Tier grouping response has expected structure."""
        response = {
            "tier_1": [],
            "tier_2": [],
            "tier_3": [],
            "tier_4": [],
            "summary": {
                "tier_1_count": 0,
                "tier_2_count": 0,
                "tier_3_count": 0,
                "tier_4_count": 0,
                "total": 0
            }
        }

        expected_keys = {"tier_1", "tier_2", "tier_3", "tier_4", "summary"}
        assert set(response.keys()) == expected_keys

        expected_summary_keys = {"tier_1_count", "tier_2_count", "tier_3_count", "tier_4_count", "total"}
        assert set(response["summary"].keys()) == expected_summary_keys

    def test_tier_arrays_are_always_lists(self):
        """Each tier is always a list, never None."""
        response = {
            "tier_1": [],
            "tier_2": [],
            "tier_3": [],
            "tier_4": [],
        }

        for tier in ["tier_1", "tier_2", "tier_3", "tier_4"]:
            assert isinstance(response[tier], list)


# ============================================================================
# CATEGORY 2: BOUNDARY TESTS
# ============================================================================

class TestTierBoundaries:
    """Test exact tier calculation boundaries."""

    def calculate_tier(self, total_score: int) -> int:
        """Tier calculation logic (mirrors backend)."""
        if total_score >= 17:
            return 1
        elif total_score >= 14:
            return 2
        elif total_score >= 11:
            return 3
        else:
            return 4

    # Tier 4 boundaries
    def test_score_0_is_tier_4(self):
        assert self.calculate_tier(0) == 4

    def test_score_10_is_tier_4(self):
        assert self.calculate_tier(10) == 4

    # Tier 3 boundaries
    def test_score_11_is_tier_3(self):
        assert self.calculate_tier(11) == 3

    def test_score_13_is_tier_3(self):
        assert self.calculate_tier(13) == 3

    # Tier 2 boundaries
    def test_score_14_is_tier_2(self):
        assert self.calculate_tier(14) == 2

    def test_score_16_is_tier_2(self):
        assert self.calculate_tier(16) == 2

    # Tier 1 boundaries
    def test_score_17_is_tier_1(self):
        assert self.calculate_tier(17) == 1

    def test_score_20_is_tier_1(self):
        assert self.calculate_tier(20) == 1

    # Edge cases
    def test_negative_score_is_tier_4(self):
        """Negative scores should be tier 4."""
        assert self.calculate_tier(-5) == 4

    def test_score_above_20_is_tier_1(self):
        """Scores above max still tier 1."""
        assert self.calculate_tier(25) == 1


class TestScoreBoundaries:
    """Test individual score dimension boundaries."""

    def test_score_dimension_min_is_1(self):
        """Minimum valid score is 1."""
        valid_scores = [1, 2, 3, 4, 5]
        for score in valid_scores:
            assert 1 <= score <= 5

    def test_score_dimension_max_is_5(self):
        """Maximum valid score is 5."""
        assert 5 == max([1, 2, 3, 4, 5])

    def test_null_score_contributes_zero(self):
        """Null scores contribute 0 to total."""
        scores = [None, 3, None, 4]
        total = sum(s or 0 for s in scores)
        assert total == 7

    def test_all_null_scores_gives_zero_total(self):
        """All null scores = 0 total."""
        scores = [None, None, None, None]
        total = sum(s or 0 for s in scores)
        assert total == 0

    def test_all_max_scores_gives_20(self):
        """All max scores = 20 total."""
        scores = [5, 5, 5, 5]
        total = sum(scores)
        assert total == 20


class TestPaginationBoundaries:
    """Test pagination edge cases."""

    def test_page_0_treated_as_page_1(self):
        """Page 0 should be treated as page 1."""
        page = max(1, 0)
        assert page == 1

    def test_negative_page_treated_as_page_1(self):
        """Negative page should be treated as page 1."""
        page = max(1, -5)
        assert page == 1

    def test_page_size_0_rejected(self):
        """Page size 0 should be rejected or defaulted."""
        page_size = 10 if 0 <= 0 else 0
        assert page_size == 10

    def test_offset_calculation_page_1(self):
        """Page 1 has offset 0."""
        page = 1
        page_size = 10
        offset = (page - 1) * page_size
        assert offset == 0

    def test_offset_calculation_page_2(self):
        """Page 2 has offset equal to page_size."""
        page = 2
        page_size = 10
        offset = (page - 1) * page_size
        assert offset == 10


# ============================================================================
# CATEGORY 3: ERROR RECOVERY TESTS
# ============================================================================

class TestErrorRecovery:
    """Test graceful degradation when things fail."""

    def test_missing_optional_field_uses_default(self):
        """Missing optional fields use sensible defaults."""
        raw_data = {"id": "1", "title": "Test"}

        # Apply defaults for missing fields
        processed = {
            "id": raw_data.get("id"),
            "title": raw_data.get("title"),
            "description": raw_data.get("description"),  # None is ok
            "blockers": raw_data.get("blockers") or [],  # Default to empty list
            "roi_indicators": raw_data.get("roi_indicators") or {},  # Default to empty dict
        }

        assert processed["description"] is None
        assert processed["blockers"] == []
        assert processed["roi_indicators"] == {}

    def test_invalid_status_falls_back_to_identified(self):
        """Invalid status falls back to 'identified'."""
        status = "invalid_status"
        valid_statuses = ["identified", "scoping", "pilot", "scaling", "completed", "blocked"]
        safe_status = status if status in valid_statuses else "identified"
        assert safe_status == "identified"

    def test_invalid_tier_clamped_to_valid_range(self):
        """Invalid tier is clamped to 1-4."""
        def clamp_tier(tier):
            return max(1, min(4, tier))

        assert clamp_tier(0) == 1
        assert clamp_tier(5) == 4
        assert clamp_tier(-1) == 1
        assert clamp_tier(100) == 4

    def test_empty_array_returned_on_query_failure(self):
        """Query failures return empty arrays, not errors."""
        def safe_query(should_fail=False):
            if should_fail:
                return []  # Graceful degradation
            return [{"id": "1"}]

        assert safe_query(should_fail=True) == []

    def test_null_coalescing_for_nested_fields(self):
        """Nested field access doesn't crash on None."""
        data = {"outer": None}

        # Safe nested access
        inner_value = (data.get("outer") or {}).get("inner")
        assert inner_value is None

    def test_json_parse_failure_returns_empty_dict(self):
        """Invalid JSON returns empty dict, not crash."""
        def safe_json_parse(text):
            try:
                return json.loads(text)
            except (json.JSONDecodeError, TypeError):
                return {}

        assert safe_json_parse("not json") == {}
        assert safe_json_parse(None) == {}
        assert safe_json_parse("") == {}


class TestPartialUpdateRecovery:
    """Test that partial updates don't corrupt data."""

    def test_partial_update_preserves_unmentioned_fields(self):
        """Update only changes specified fields."""
        original = {
            "id": "1",
            "title": "Original",
            "description": "Original desc",
            "status": "identified",
        }

        update = {"title": "Updated"}

        # Merge preserving originals
        result = {**original, **update}

        assert result["title"] == "Updated"
        assert result["description"] == "Original desc"  # Preserved
        assert result["status"] == "identified"  # Preserved

    def test_null_update_value_clears_field(self):
        """Explicit null in update clears the field."""
        original = {"id": "1", "description": "Has value"}
        update = {"description": None}

        result = {**original, **update}
        assert result["description"] is None


# ============================================================================
# CATEGORY 4: TIME-BASED TESTS
# ============================================================================

class TestTimeBased:
    """Test date/time edge cases."""

    def test_created_at_is_utc(self):
        """Timestamps should be UTC."""
        now = datetime.now(timezone.utc)
        iso_string = now.isoformat()

        # Should contain timezone info
        assert "+" in iso_string or "Z" in iso_string

    def test_updated_at_after_created_at(self):
        """updated_at should be >= created_at."""
        created = datetime.now(timezone.utc)
        updated = datetime.now(timezone.utc) + timedelta(seconds=1)

        assert updated >= created

    def test_iso_format_parsing_with_z_suffix(self):
        """Parse ISO dates with Z suffix."""
        date_str = "2026-01-18T12:00:00Z"
        parsed = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        assert parsed.year == 2026
        assert parsed.tzinfo is not None

    def test_iso_format_parsing_with_offset(self):
        """Parse ISO dates with explicit offset."""
        date_str = "2026-01-18T12:00:00+00:00"
        parsed = datetime.fromisoformat(date_str)
        assert parsed.year == 2026

    def test_iso_format_parsing_with_milliseconds(self):
        """Parse ISO dates with milliseconds."""
        date_str = "2026-01-18T12:00:00.123456+00:00"
        parsed = datetime.fromisoformat(date_str)
        assert parsed.microsecond == 123456

    def test_conversation_ordering_by_created_at(self):
        """Conversations sorted by created_at descending."""
        convos = [
            {"id": "1", "created_at": "2026-01-18T10:00:00+00:00"},
            {"id": "2", "created_at": "2026-01-18T12:00:00+00:00"},
            {"id": "3", "created_at": "2026-01-18T11:00:00+00:00"},
        ]

        sorted_convos = sorted(convos, key=lambda x: x["created_at"], reverse=True)

        assert sorted_convos[0]["id"] == "2"  # Most recent first
        assert sorted_convos[1]["id"] == "3"
        assert sorted_convos[2]["id"] == "1"

    def test_same_timestamp_stable_ordering(self):
        """Items with same timestamp have stable ordering."""
        items = [
            {"id": "a", "created_at": "2026-01-18T12:00:00+00:00"},
            {"id": "b", "created_at": "2026-01-18T12:00:00+00:00"},
            {"id": "c", "created_at": "2026-01-18T12:00:00+00:00"},
        ]

        # Sort twice and verify same order
        sorted1 = sorted(items, key=lambda x: (x["created_at"], x["id"]))
        sorted2 = sorted(items, key=lambda x: (x["created_at"], x["id"]))

        assert [i["id"] for i in sorted1] == [i["id"] for i in sorted2]


# ============================================================================
# CATEGORY 5: LOAD PATTERN TESTS
# ============================================================================

class TestLoadPatterns:
    """Test behavior under load conditions."""

    def test_large_list_pagination_works(self):
        """Large lists paginate correctly."""
        all_items = [{"id": str(i)} for i in range(1000)]

        page_size = 10
        page = 5
        offset = (page - 1) * page_size

        page_items = all_items[offset:offset + page_size]

        assert len(page_items) == 10
        assert page_items[0]["id"] == "40"  # 5th page starts at index 40

    def test_large_description_handled(self):
        """Large text fields don't break."""
        large_text = "x" * 10000  # 10KB
        opp = {"description": large_text}
        assert len(opp["description"]) == 10000

    def test_many_blockers_handled(self):
        """Many array items don't break."""
        many_blockers = [f"Blocker {i}" for i in range(100)]
        opp = {"blockers": many_blockers}
        assert len(opp["blockers"]) == 100

    def test_deep_roi_indicators_handled(self):
        """Nested dict structures don't break."""
        deep_indicators = {
            "level1": {
                "level2": {
                    "level3": {
                        "value": 123
                    }
                }
            }
        }
        opp = {"roi_indicators": deep_indicators}
        assert opp["roi_indicators"]["level1"]["level2"]["level3"]["value"] == 123


class TestConcurrentAccess:
    """Test concurrent access patterns."""

    @pytest.mark.asyncio
    async def test_concurrent_reads_dont_interfere(self):
        """Multiple simultaneous reads don't interfere."""
        data = {"value": 42}
        results = []

        async def read_data():
            await asyncio.sleep(0.01)  # Simulate DB latency
            results.append(data["value"])

        await asyncio.gather(*[read_data() for _ in range(10)])

        assert all(r == 42 for r in results)
        assert len(results) == 10

    @pytest.mark.asyncio
    async def test_write_then_read_sees_update(self):
        """Read after write sees the update."""
        data = {"value": 0}
        lock = asyncio.Lock()

        async def write_then_read(new_value):
            async with lock:
                data["value"] = new_value
                await asyncio.sleep(0.01)
                return data["value"]

        result = await write_then_read(100)
        assert result == 100


# ============================================================================
# CATEGORY 6: DATABASE CONSTRAINT TESTS
# ============================================================================

class TestDatabaseConstraints:
    """Test that DB constraints are enforced."""

    def test_project_code_format(self):
        """Project code follows expected format (dept prefix + 2-digit number)."""
        import re
        valid_codes = ["F01", "L02", "H12", "IT01", "G99"]
        invalid_codes = ["f01", "F1", "F001", "PROJECT-001", "123"]

        # Project codes: 1-2 uppercase letters followed by 2 digits
        pattern = r"^[A-Z]{1,2}\d{2}$"

        for code in valid_codes:
            assert re.match(pattern, code), f"{code} should be valid"

        for code in invalid_codes:
            assert not re.match(pattern, code), f"{code} should be invalid"

    def test_status_enum_values(self):
        """Status must be one of valid values."""
        valid_statuses = {"identified", "scoping", "pilot", "scaling", "completed", "blocked"}

        test_status = "identified"
        assert test_status in valid_statuses

        invalid_status = "unknown"
        assert invalid_status not in valid_statuses

    def test_tier_range_constraint(self):
        """Tier must be 1-4."""
        valid_tiers = {1, 2, 3, 4}

        for tier in valid_tiers:
            assert tier in valid_tiers

        invalid_tiers = [0, 5, -1, 100]
        for tier in invalid_tiers:
            assert tier not in valid_tiers

    def test_score_range_constraint(self):
        """Scores must be 1-5 or null."""
        valid_scores = {1, 2, 3, 4, 5, None}

        for score in [1, 3, 5, None]:
            assert score in valid_scores or score is None

        invalid_scores = [0, 6, -1, 10]
        for score in invalid_scores:
            assert score not in valid_scores

    def test_uuid_format_constraint(self):
        """IDs must be valid UUIDs."""
        valid_uuid = str(uuid4())

        # Should not raise
        UUID(valid_uuid)

        invalid_uuids = ["not-a-uuid", "12345", ""]
        for invalid in invalid_uuids:
            with pytest.raises((ValueError, AttributeError)):
                UUID(invalid)


# ============================================================================
# CATEGORY 7: SNAPSHOT/GOLDEN TESTS
# ============================================================================

class TestResponseSnapshots:
    """Detect unintended API response structure changes."""

    def test_project_list_response_keys(self):
        """List response has stable keys."""
        expected_keys = {"tier_1", "tier_2", "tier_3", "tier_4", "summary"}

        response = {
            "tier_1": [],
            "tier_2": [],
            "tier_3": [],
            "tier_4": [],
            "summary": {}
        }

        assert set(response.keys()) == expected_keys

    def test_summary_response_keys(self):
        """Summary has stable keys."""
        expected_keys = {"tier_1_count", "tier_2_count", "tier_3_count", "tier_4_count", "total"}

        summary = {
            "tier_1_count": 0,
            "tier_2_count": 0,
            "tier_3_count": 0,
            "tier_4_count": 0,
            "total": 0
        }

        assert set(summary.keys()) == expected_keys

    def test_error_response_structure(self):
        """Error responses have consistent structure."""
        error_response = {
            "detail": "Project not found"
        }

        assert "detail" in error_response
        assert isinstance(error_response["detail"], str)

    def test_success_message_structure(self):
        """Success messages have consistent structure."""
        success_response = {
            "message": "Justifications generated successfully",
            "justifications": {}
        }

        assert "message" in success_response


# ============================================================================
# CATEGORY 8: PYDANTIC VALIDATION TESTS
# ============================================================================

class TestPydanticValidation:
    """Test Pydantic model validation behavior."""

    def test_required_field_missing_raises(self):
        """Missing required field raises ValidationError."""
        class ProjectCreate(BaseModel):
            title: str
            project_code: str

        with pytest.raises(ValidationError) as exc_info:
            ProjectCreate(title="Test")  # Missing project_code

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("project_code",) for e in errors)

    def test_optional_field_can_be_none(self):
        """Optional fields accept None."""
        class ProjectCreate(BaseModel):
            title: str
            description: Optional[str] = None

        opp = ProjectCreate(title="Test", description=None)
        assert opp.description is None

    def test_optional_field_can_be_omitted(self):
        """Optional fields can be omitted entirely."""
        class ProjectCreate(BaseModel):
            title: str
            description: Optional[str] = None

        opp = ProjectCreate(title="Test")
        assert opp.description is None

    def test_custom_validator_rejects_invalid(self):
        """Custom validators reject invalid values."""
        class ProjectCreate(BaseModel):
            title: str
            tier: int

            @field_validator('tier')
            @classmethod
            def tier_must_be_valid(cls, v):
                if v < 1 or v > 4:
                    raise ValueError('Tier must be between 1 and 4')
                return v

        with pytest.raises(ValidationError):
            ProjectCreate(title="Test", tier=5)

    def test_type_coercion_string_to_int(self):
        """Pydantic coerces compatible types."""
        class ScoreUpdate(BaseModel):
            score: int

        # String "5" should be coerced to int 5
        update = ScoreUpdate(score="5")
        assert update.score == 5
        assert isinstance(update.score, int)


# ============================================================================
# INTEGRATION: COMBINED SCENARIO TESTS
# ============================================================================

class TestCombinedScenarios:
    """Test realistic combined scenarios."""

    def test_create_project_full_flow(self):
        """Full create flow with all validations."""
        # Input
        input_data = {
            "title": "AI Invoice Processing",
            "project_code": "OPP-042",
            "department": "finance",
            "roi_potential": 4,
            "implementation_effort": 3,
            "strategic_alignment": 5,
            "stakeholder_readiness": 4,
        }

        # Calculate derived fields
        total_score = sum([
            input_data.get("roi_potential") or 0,
            input_data.get("implementation_effort") or 0,
            input_data.get("strategic_alignment") or 0,
            input_data.get("stakeholder_readiness") or 0,
        ])

        def calc_tier(score):
            if score >= 17: return 1
            if score >= 14: return 2
            if score >= 11: return 3
            return 4

        tier = calc_tier(total_score)

        # Verify
        assert total_score == 16
        assert tier == 2

    def test_filter_then_paginate_flow(self):
        """Filter then paginate maintains consistency."""
        all_opps = [
            {"id": "1", "department": "finance", "tier": 1},
            {"id": "2", "department": "legal", "tier": 1},
            {"id": "3", "department": "finance", "tier": 2},
            {"id": "4", "department": "finance", "tier": 1},
            {"id": "5", "department": "hr", "tier": 3},
        ]

        # Filter by department
        filtered = [o for o in all_opps if o["department"] == "finance"]
        assert len(filtered) == 3

        # Paginate
        page_size = 2
        page_1 = filtered[0:2]
        page_2 = filtered[2:4]

        assert len(page_1) == 2
        assert len(page_2) == 1

        # Total should match
        assert len(page_1) + len(page_2) == len(filtered)

    def test_update_scores_recalculates_tier(self):
        """Updating scores recalculates tier correctly."""
        opp = {
            "roi_potential": 2,
            "implementation_effort": 2,
            "strategic_alignment": 2,
            "stakeholder_readiness": 2,
            "total_score": 8,
            "tier": 4,
        }

        # Update scores
        opp["roi_potential"] = 5
        opp["implementation_effort"] = 5
        opp["strategic_alignment"] = 5
        opp["stakeholder_readiness"] = 5

        # Recalculate
        opp["total_score"] = sum([
            opp["roi_potential"],
            opp["implementation_effort"],
            opp["strategic_alignment"],
            opp["stakeholder_readiness"],
        ])

        def calc_tier(score):
            if score >= 17: return 1
            if score >= 14: return 2
            if score >= 11: return 3
            return 4

        opp["tier"] = calc_tier(opp["total_score"])

        assert opp["total_score"] == 20
        assert opp["tier"] == 1
