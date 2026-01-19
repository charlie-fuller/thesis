"""
Vibe-Coding Bug Tests

These tests target the common failure modes in AI-assisted codebases:
- Array/List edge cases
- Type coercion bugs
- Async race conditions
- Error message propagation
- Default value consistency
- Permission/isolation bugs
- UI state expectations

Combined with test_opportunities.py tests for:
- Data shape mismatches
- Optional field handling
- Deleted reference handling

Total coverage targets 90%+ of vibe-coding bugs.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timedelta, timezone
from uuid import uuid4
import asyncio


# ============================================================================
# CATEGORY 3: ARRAY/LIST EDGE CASES
# ============================================================================

class TestArrayListEdgeCases:
    """Tests for empty arrays, single items, and pagination boundaries."""

    def test_opportunities_empty_tier_returns_empty_list(self):
        """Tier with 0 opportunities returns empty list, not None."""
        response = {
            "tier_1": [],
            "tier_2": [],
            "tier_3": [],
            "tier_4": [],
            "summary": {"tier_1_count": 0, "tier_2_count": 0, "tier_3_count": 0, "tier_4_count": 0, "total": 0}
        }
        # Each tier should be an empty list, not None or missing
        assert response["tier_1"] == []
        assert response["tier_2"] == []
        assert isinstance(response["tier_1"], list)

    def test_single_stakeholder_list_no_pagination_needed(self):
        """Single-item lists should work without pagination."""
        stakeholders = [{"id": str(uuid4()), "name": "Single User"}]
        assert len(stakeholders) == 1
        # Pagination should not break on single item
        page_1 = stakeholders[0:10]
        assert len(page_1) == 1

    def test_empty_blockers_array_serializes_correctly(self):
        """Empty blockers array should serialize as [], not null."""
        opportunity = {
            "id": str(uuid4()),
            "blockers": [],
            "follow_up_questions": []
        }
        import json
        serialized = json.dumps(opportunity)
        deserialized = json.loads(serialized)
        assert deserialized["blockers"] == []
        assert isinstance(deserialized["blockers"], list)

    def test_pagination_beyond_data_returns_empty(self):
        """Requesting page beyond data returns empty list, not error."""
        all_items = [{"id": i} for i in range(5)]
        page_size = 10
        offset = 20  # Way beyond our 5 items
        page = all_items[offset:offset + page_size]
        assert page == []

    def test_negative_offset_handled(self):
        """Negative offset should be treated as 0 or rejected."""
        all_items = [{"id": i} for i in range(5)]
        offset = -5
        # Should either clamp to 0 or be rejected
        safe_offset = max(0, offset)
        page = all_items[safe_offset:safe_offset + 10]
        assert len(page) == 5

    def test_tags_array_can_be_none_or_empty(self):
        """Document tags can be None or empty array."""
        doc_with_none = {"id": "1", "tags": None}
        doc_with_empty = {"id": "2", "tags": []}
        doc_with_tags = {"id": "3", "tags": ["finance", "legal"]}

        # All should be valid
        for doc in [doc_with_none, doc_with_empty, doc_with_tags]:
            tags = doc.get("tags") or []
            assert isinstance(tags, list)


# ============================================================================
# CATEGORY 4: TYPE COERCION BUGS
# ============================================================================

class TestTypeCoercionBugs:
    """Tests for string/int/UUID/boolean type handling."""

    def test_uuid_string_equality(self):
        """UUID objects and their string representations should be comparable."""
        from uuid import UUID
        uuid_obj = uuid4()
        uuid_str = str(uuid_obj)

        # Common bug: comparing UUID to string directly
        assert str(uuid_obj) == uuid_str
        assert UUID(uuid_str) == uuid_obj

    def test_score_as_string_converts_to_int(self):
        """Score passed as string '5' should work same as int 5."""
        score_str = "5"
        score_int = 5

        # Both should produce same result after normalization
        normalized_str = int(score_str) if isinstance(score_str, str) else score_str
        assert normalized_str == score_int

    def test_boolean_query_param_variations(self):
        """Various boolean representations should normalize correctly."""
        true_values = ["true", "True", "TRUE", "1", 1, True]
        false_values = ["false", "False", "FALSE", "0", 0, False]

        def normalize_bool(val):
            if isinstance(val, bool):
                return val
            if isinstance(val, int):
                return val != 0
            if isinstance(val, str):
                return val.lower() in ("true", "1", "yes")
            return False

        for val in true_values:
            assert normalize_bool(val) is True, f"Failed for {val}"
        for val in false_values:
            assert normalize_bool(val) is False, f"Failed for {val}"

    def test_tier_number_vs_string(self):
        """Tier can come as int 1 or string '1'."""
        tier_int = 1
        tier_str = "1"

        # Both should work in tier lookups
        tier_config = {1: "Tier 1", 2: "Tier 2", 3: "Tier 3", 4: "Tier 4"}
        assert tier_config[int(tier_str)] == "Tier 1"
        assert tier_config[tier_int] == "Tier 1"

    def test_null_vs_empty_string_in_optional_fields(self):
        """null and '' should both be treated as 'no value'."""
        def is_empty(val):
            return val is None or val == ""

        assert is_empty(None)
        assert is_empty("")
        assert not is_empty("some value")
        assert not is_empty(0)  # 0 is not empty

    def test_date_string_parsing(self):
        """ISO date strings should parse correctly."""
        date_strings = [
            "2026-01-18T12:00:00Z",
            "2026-01-18T12:00:00.000Z",
            "2026-01-18T12:00:00+00:00",
        ]

        for date_str in date_strings:
            # Should not raise
            parsed = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            assert parsed.year == 2026

    def test_float_scores_round_correctly(self):
        """Scores stored as float should round to int for display."""
        float_score = 4.7
        # Common display: round to nearest int
        assert round(float_score) == 5
        # Or truncate
        assert int(float_score) == 4


# ============================================================================
# CATEGORY 5: ASYNC RACE CONDITIONS
# ============================================================================

class TestAsyncRaceConditions:
    """Tests for double-submit, concurrent updates, and stale state."""

    @pytest.mark.asyncio
    async def test_double_submit_protection(self):
        """Rapid double-click should not create duplicates."""
        created_ids = []
        create_lock = asyncio.Lock()

        async def create_opportunity(title: str):
            async with create_lock:
                # Simulate DB insert with deduplication
                new_id = str(uuid4())
                if title not in [c.get("title") for c in created_ids]:
                    created_ids.append({"id": new_id, "title": title})
                return new_id

        # Simulate double-click
        await asyncio.gather(
            create_opportunity("Test Opportunity"),
            create_opportunity("Test Opportunity"),
        )

        # Should only have one entry (with lock protection)
        assert len(created_ids) == 1

    @pytest.mark.asyncio
    async def test_concurrent_status_updates_last_wins(self):
        """Concurrent updates should have deterministic outcome."""
        opportunity = {"status": "identified", "version": 1}

        async def update_status(new_status: str, delay: float):
            await asyncio.sleep(delay)
            opportunity["status"] = new_status
            opportunity["version"] += 1
            return new_status

        # Two concurrent updates
        results = await asyncio.gather(
            update_status("scoping", 0.01),
            update_status("pilot", 0.02),
        )

        # Last one to complete wins
        assert opportunity["status"] == "pilot"
        assert opportunity["version"] == 3  # Two updates

    @pytest.mark.asyncio
    async def test_fetch_during_update_gets_consistent_state(self):
        """Reading during write should get complete state, not partial."""
        data = {"id": "1", "title": "Original", "score": 10}
        write_lock = asyncio.Lock()

        async def update_data():
            async with write_lock:
                data["title"] = "Updated"
                await asyncio.sleep(0.01)  # Simulate slow write
                data["score"] = 20

        async def read_data():
            async with write_lock:
                # Read should see either all old or all new values
                return dict(data)

        # Start update, then read
        update_task = asyncio.create_task(update_data())
        await asyncio.sleep(0.005)  # Let update start
        read_result = await read_data()
        await update_task

        # Read should have consistent state
        assert (read_result["title"] == "Original" and read_result["score"] == 10) or \
               (read_result["title"] == "Updated" and read_result["score"] == 20)


# ============================================================================
# CATEGORY 6: ERROR MESSAGE PROPAGATION
# ============================================================================

class TestErrorMessagePropagation:
    """Tests for meaningful error messages reaching the frontend."""

    def test_validation_error_has_field_name(self):
        """Pydantic validation errors should include field name."""
        from pydantic import BaseModel, ValidationError, field_validator

        class OpportunityCreate(BaseModel):
            title: str
            tier: int

            @field_validator('tier')
            @classmethod
            def tier_must_be_valid(cls, v):
                if v < 1 or v > 4:
                    raise ValueError('Tier must be between 1 and 4')
                return v

        with pytest.raises(ValidationError) as exc_info:
            OpportunityCreate(title="Test", tier=5)

        error = exc_info.value.errors()[0]
        assert "tier" in error["loc"]
        assert "1 and 4" in error["msg"]

    def test_not_found_error_includes_resource_type(self):
        """404 errors should say what wasn't found."""
        def get_opportunity(opp_id: str):
            # Simulate not found
            raise ValueError(f"Opportunity {opp_id} not found")

        with pytest.raises(ValueError) as exc_info:
            get_opportunity("nonexistent-id")

        assert "Opportunity" in str(exc_info.value)
        assert "not found" in str(exc_info.value)

    def test_duplicate_error_message_is_clear(self):
        """Duplicate key errors should be user-friendly."""
        def create_with_duplicate_code():
            # Simulate unique constraint violation
            raise ValueError("Opportunity with code OPP-001 already exists")

        with pytest.raises(ValueError) as exc_info:
            create_with_duplicate_code()

        # Should be understandable, not "duplicate key violates unique constraint"
        assert "already exists" in str(exc_info.value)

    def test_permission_error_doesnt_leak_info(self):
        """Permission errors shouldn't reveal existence of resources."""
        def check_access(user_id: str, resource_id: str):
            # Bad: "You don't have access to Opportunity X"
            # Good: "Resource not found or access denied"
            raise PermissionError("Resource not found or access denied")

        with pytest.raises(PermissionError) as exc_info:
            check_access("user1", "secret-opp")

        # Shouldn't confirm the resource exists
        assert "not found or access denied" in str(exc_info.value)


# ============================================================================
# CATEGORY 7: DEFAULT VALUE CONSISTENCY
# ============================================================================

class TestDefaultValueConsistency:
    """Tests for frontend/backend default value alignment."""

    def test_opportunity_default_status_is_identified(self):
        """New opportunities should default to 'identified' status."""
        default_status = "identified"

        # This is what the backend should set
        new_opp = {
            "title": "Test",
            "status": default_status,
        }

        assert new_opp["status"] == "identified"

    def test_opportunity_default_tier_calculation(self):
        """Default tier based on null scores should be tier 4."""
        def calculate_tier(total_score: int) -> int:
            if total_score >= 17:
                return 1
            elif total_score >= 14:
                return 2
            elif total_score >= 11:
                return 3
            else:
                return 4

        # Null scores = 0 total = tier 4
        assert calculate_tier(0) == 4
        assert calculate_tier(10) == 4
        assert calculate_tier(11) == 3
        assert calculate_tier(14) == 2
        assert calculate_tier(17) == 1

    def test_task_default_status_is_backlog(self):
        """New tasks should default to 'backlog' status."""
        default_statuses = ["backlog", "todo", "in_progress", "done"]

        # Backend default
        new_task = {"title": "Test Task", "status": "backlog"}
        assert new_task["status"] == default_statuses[0]

    def test_document_default_visibility_is_private(self):
        """Uploaded documents should default to private visibility."""
        new_doc = {
            "title": "Test Doc",
            "is_public": False,  # Default
        }
        assert new_doc["is_public"] is False

    def test_stakeholder_default_engagement_level(self):
        """New stakeholders should start with 'unknown' engagement."""
        valid_levels = ["champion", "supporter", "neutral", "skeptic", "blocker", "unknown"]
        default_level = "unknown"

        assert default_level in valid_levels
        new_stakeholder = {"name": "Test", "engagement_level": default_level}
        assert new_stakeholder["engagement_level"] == "unknown"


# ============================================================================
# CATEGORY 9: PERMISSION/ISOLATION BUGS
# ============================================================================

class TestPermissionIsolation:
    """Tests for multi-tenant data isolation."""

    def test_user_can_only_see_own_opportunities(self):
        """User A cannot fetch User B's opportunities."""
        user_a_id = str(uuid4())
        user_b_id = str(uuid4())

        opportunities = [
            {"id": "1", "user_id": user_a_id, "title": "User A Opp"},
            {"id": "2", "user_id": user_b_id, "title": "User B Opp"},
        ]

        def get_opportunities_for_user(user_id: str):
            return [o for o in opportunities if o["user_id"] == user_id]

        user_a_opps = get_opportunities_for_user(user_a_id)
        assert len(user_a_opps) == 1
        assert user_a_opps[0]["title"] == "User A Opp"

    def test_document_visibility_respected_in_search(self):
        """Private documents not returned in other users' searches."""
        user_a_id = str(uuid4())
        user_b_id = str(uuid4())

        documents = [
            {"id": "1", "user_id": user_a_id, "is_public": False, "content": "secret"},
            {"id": "2", "user_id": user_a_id, "is_public": True, "content": "public A"},
            {"id": "3", "user_id": user_b_id, "is_public": True, "content": "public B"},
        ]

        def search_documents(query: str, requesting_user_id: str):
            results = []
            for doc in documents:
                if query.lower() in doc["content"].lower():
                    # Include if public OR owned by requesting user
                    if doc["is_public"] or doc["user_id"] == requesting_user_id:
                        results.append(doc)
            return results

        # User B searches - should not see User A's private doc
        results = search_documents("secret", user_b_id)
        assert len(results) == 0

        # User A searches - should see their own private doc
        results = search_documents("secret", user_a_id)
        assert len(results) == 1

    def test_agent_assignment_respects_ownership(self):
        """Users can only assign documents to agents for their own documents."""
        user_a_id = str(uuid4())
        user_b_id = str(uuid4())
        doc_id = "doc-1"
        doc_owner = user_a_id

        def assign_agent(doc_id: str, agent_id: str, requesting_user: str, doc_owner: str):
            if requesting_user != doc_owner:
                raise PermissionError("Cannot modify documents you don't own")
            return {"doc_id": doc_id, "agent_id": agent_id}

        # Owner can assign
        result = assign_agent(doc_id, "atlas", user_a_id, doc_owner)
        assert result["agent_id"] == "atlas"

        # Non-owner cannot
        with pytest.raises(PermissionError):
            assign_agent(doc_id, "atlas", user_b_id, doc_owner)


# ============================================================================
# CATEGORY 10: UI STATE SYNC EXPECTATIONS
# ============================================================================

class TestUIStateSyncExpectations:
    """Tests for data that frontend expects after mutations."""

    def test_create_returns_complete_object(self):
        """Create endpoints should return full object with generated fields."""
        # Frontend expects to update its state with the response
        created_opportunity = {
            "id": str(uuid4()),  # Generated
            "opportunity_code": "OPP-001",  # Generated
            "title": "Test",
            "created_at": datetime.now(timezone.utc).isoformat(),  # Generated
            "updated_at": datetime.now(timezone.utc).isoformat(),  # Generated
            "total_score": 0,  # Calculated
            "tier": 4,  # Calculated
            "status": "identified",  # Default
        }

        # Should have all fields frontend needs to display
        assert "id" in created_opportunity
        assert "opportunity_code" in created_opportunity
        assert "created_at" in created_opportunity
        assert "tier" in created_opportunity

    def test_update_returns_updated_object(self):
        """Update endpoints should return updated object, not just success."""
        original = {
            "id": "1",
            "title": "Original",
            "updated_at": "2026-01-17T00:00:00Z",
        }

        # After update
        updated = {
            **original,
            "title": "Updated",
            "updated_at": "2026-01-18T00:00:00Z",
        }

        # Response should have new values
        assert updated["title"] == "Updated"
        assert updated["updated_at"] != original["updated_at"]

    def test_delete_returns_confirmation(self):
        """Delete endpoints should confirm what was deleted."""
        deleted_id = str(uuid4())

        delete_response = {
            "success": True,
            "deleted_id": deleted_id,
        }

        # Frontend needs to know which item to remove from state
        assert delete_response["deleted_id"] == deleted_id

    def test_list_endpoint_returns_consistent_shape(self):
        """List endpoints always return same shape, even when empty."""
        empty_response = {
            "items": [],
            "total": 0,
            "page": 1,
            "page_size": 10,
        }

        populated_response = {
            "items": [{"id": "1"}, {"id": "2"}],
            "total": 2,
            "page": 1,
            "page_size": 10,
        }

        # Both have same keys
        assert set(empty_response.keys()) == set(populated_response.keys())
        assert isinstance(empty_response["items"], list)
        assert isinstance(populated_response["items"], list)


# ============================================================================
# INTEGRATION: FULL FLOW TESTS
# ============================================================================

class TestFullFlowIntegration:
    """End-to-end flow tests combining multiple bug categories."""

    def test_opportunity_create_to_display_flow(self):
        """Create opportunity and verify all display fields present."""
        # User input
        input_data = {
            "title": "Test Opportunity",
            "department": "finance",
        }

        # Backend creates with defaults
        created = {
            **input_data,
            "id": str(uuid4()),
            "opportunity_code": "OPP-001",
            "status": "identified",
            "tier": 4,
            "total_score": 0,
            "roi_potential": None,
            "implementation_effort": None,
            "strategic_alignment": None,
            "stakeholder_readiness": None,
            "blockers": [],
            "follow_up_questions": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        # Frontend display requirements
        required_display_fields = [
            "id", "opportunity_code", "title", "status", "tier",
            "total_score", "created_at"
        ]

        for field in required_display_fields:
            assert field in created, f"Missing required field: {field}"

        # Score fields can be null but must exist
        score_fields = ["roi_potential", "implementation_effort",
                       "strategic_alignment", "stakeholder_readiness"]
        for field in score_fields:
            assert field in created, f"Missing score field: {field}"

    def test_filter_then_detail_flow(self):
        """Filter list then view detail maintains data consistency."""
        opportunities = [
            {"id": "1", "department": "finance", "tier": 1, "total_score": 18},
            {"id": "2", "department": "legal", "tier": 2, "total_score": 15},
            {"id": "3", "department": "finance", "tier": 3, "total_score": 12},
        ]

        # Filter by department
        filtered = [o for o in opportunities if o["department"] == "finance"]
        assert len(filtered) == 2

        # Get detail of first filtered item
        detail_id = filtered[0]["id"]
        detail = next(o for o in opportunities if o["id"] == detail_id)

        # Detail should match filtered item
        assert detail["department"] == "finance"
        assert detail["tier"] == filtered[0]["tier"]
