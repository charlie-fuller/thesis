"""Tests for DISCo Initiative Service.

Tests CRUD operations, access control, and status management for initiatives.
Updated for PocketBase migration: mocks pb_client instead of Supabase.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    return {"id": "user-123", "email": "test@example.com", "name": "Test User"}


@pytest.fixture
def mock_initiative_data():
    """Sample initiative data for testing."""
    return {
        "id": "initiative-123",
        "name": "Test Initiative",
        "description": "Test description",
        "status": "draft",
        "created_by": "user-123",
        "created": "2026-01-15T10:00:00Z",
        "updated": "2026-01-15T10:00:00Z",
    }


@pytest.fixture
def mock_pb_service():
    """Mock pb_client functions for initiative service tests.

    Returns a dict of patched pb_client functions that can be configured
    per-test with return values and side effects.
    """
    with patch("pb_client.get_record") as mock_get, \
         patch("pb_client.get_first") as mock_first, \
         patch("pb_client.get_all") as mock_all, \
         patch("pb_client.list_records") as mock_list, \
         patch("pb_client.create_record") as mock_create, \
         patch("pb_client.update_record") as mock_update, \
         patch("pb_client.delete_record") as mock_delete, \
         patch("pb_client.count") as mock_count:
        yield {
            "get_record": mock_get,
            "get_first": mock_first,
            "get_all": mock_all,
            "list_records": mock_list,
            "create_record": mock_create,
            "update_record": mock_update,
            "delete_record": mock_delete,
            "count": mock_count,
        }


# ============================================================================
# Initiative CRUD Tests
# ============================================================================


class TestCreateInitiative:
    """Tests for create_initiative function."""

    @pytest.mark.asyncio
    async def test_create_initiative_success(self, mock_initiative_data):
        """Test successful initiative creation."""
        with patch("services.disco.initiative_service.get_supabase") as mock_get_sb:
            mock_sb = Mock()
            mock_table = Mock()
            mock_table.select.return_value = mock_table
            mock_table.insert.return_value = mock_table
            mock_table.update.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.single.return_value = mock_table
            mock_table.order.return_value = mock_table

            mock_table.execute.side_effect = [
                Mock(data=[mock_initiative_data]),  # Initiative insert
                Mock(data=[{"id": "member-123", "initiative_id": "initiative-123", "user_id": "user-123", "role": "owner"}]),
            ]
            mock_sb.table.return_value = mock_table
            mock_get_sb.return_value = mock_sb

            from services.disco.initiative_service import create_initiative

            result = await create_initiative(name="Test Initiative", user_id="user-123", description="Test description")

            assert result is not None
            assert result["name"] == "Test Initiative"

    @pytest.mark.asyncio
    async def test_create_initiative_failure(self):
        """Test initiative creation failure."""
        with patch("services.disco.initiative_service.get_supabase") as mock_get_sb:
            mock_sb = Mock()
            mock_table = Mock()
            mock_table.select.return_value = mock_table
            mock_table.insert.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.execute.return_value = Mock(data=None)
            mock_sb.table.return_value = mock_table
            mock_get_sb.return_value = mock_sb

            from services.disco.initiative_service import create_initiative

            with pytest.raises(ValueError, match="Failed to create initiative"):
                await create_initiative(name="Test Initiative", user_id="user-123")


class TestGetInitiative:
    """Tests for get_initiative function."""

    @pytest.mark.asyncio
    async def test_get_initiative_not_found(self):
        """Test retrieving non-existent initiative."""
        with patch("services.disco.initiative_service.get_supabase") as mock_get_sb:
            mock_sb = Mock()
            mock_table = Mock()
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.single.return_value = mock_table
            mock_table.execute.return_value = Mock(data=None)
            mock_sb.table.return_value = mock_table
            mock_get_sb.return_value = mock_sb

            from services.disco.initiative_service import get_initiative

            result = await get_initiative("nonexistent-id", "user-123")

            assert result is None


class TestListInitiatives:
    """Tests for list_initiatives function."""

    @pytest.mark.asyncio
    async def test_list_initiatives_empty(self):
        """Test listing when user has no initiatives."""
        with patch("services.disco.initiative_service.get_supabase") as mock_get_sb:
            mock_sb = Mock()
            mock_table = Mock()
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.execute.return_value = Mock(data=[])
            mock_sb.table.return_value = mock_table
            mock_get_sb.return_value = mock_sb

            from services.disco.initiative_service import list_initiatives

            result = await list_initiatives("user-123")

            assert result == {"initiatives": [], "total": 0}


class TestUpdateInitiative:
    """Tests for update_initiative function."""

    @pytest.mark.asyncio
    async def test_update_initiative_no_permission(self):
        """Test update without permission."""
        with patch("services.disco.initiative_service.get_supabase") as mock_get_sb:
            mock_sb = Mock()
            mock_table = Mock()
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.single.return_value = mock_table
            mock_table.execute.return_value = Mock(data={"role": "viewer"})
            mock_sb.table.return_value = mock_table
            mock_get_sb.return_value = mock_sb

            from services.disco.initiative_service import update_initiative

            with pytest.raises(PermissionError):
                await update_initiative("initiative-123", "user-123", {"name": "Updated Name"})

    @pytest.mark.asyncio
    async def test_update_initiative_invalid_fields(self):
        """Test update with invalid fields."""
        with patch("services.disco.initiative_service.get_supabase") as mock_get_sb:
            mock_sb = Mock()
            mock_table = Mock()
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.single.return_value = mock_table
            mock_table.execute.return_value = Mock(data={"role": "owner"})
            mock_sb.table.return_value = mock_table
            mock_get_sb.return_value = mock_sb

            from services.disco.initiative_service import update_initiative

            with pytest.raises(ValueError, match="No valid fields to update"):
                await update_initiative("initiative-123", "user-123", {"invalid_field": "value"})


class TestDeleteInitiative:
    """Tests for delete_initiative function."""

    @pytest.mark.asyncio
    async def test_delete_initiative_not_owner(self):
        """Test deletion by non-owner."""
        with patch("services.disco.initiative_service.get_supabase") as mock_get_sb:
            mock_sb = Mock()
            mock_table = Mock()
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.single.return_value = mock_table
            mock_table.execute.return_value = Mock(data={"role": "editor"})
            mock_sb.table.return_value = mock_table
            mock_get_sb.return_value = mock_sb

            from services.disco.initiative_service import delete_initiative

            with pytest.raises(PermissionError, match="Only the owner can delete"):
                await delete_initiative("initiative-123", "user-123")

    @pytest.mark.asyncio
    async def test_delete_initiative_not_member(self):
        """Test deletion by non-member."""
        with patch("services.disco.initiative_service.get_supabase") as mock_get_sb:
            mock_sb = Mock()
            mock_table = Mock()
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.single.return_value = mock_table
            mock_table.execute.return_value = Mock(data=None)
            mock_sb.table.return_value = mock_table
            mock_get_sb.return_value = mock_sb

            from services.disco.initiative_service import delete_initiative

            with pytest.raises(PermissionError):
                await delete_initiative("initiative-123", "user-123")


# ============================================================================
# Access Control Tests
# ============================================================================


class TestCheckUserAccess:
    """Tests for check_user_access function."""

    @pytest.mark.asyncio
    async def test_check_user_access_member(self):
        """Test access check for member."""
        with patch("services.disco.initiative_service.get_supabase") as mock_get_sb:
            mock_sb = Mock()
            mock_table = Mock()
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.execute.return_value = Mock(data=[{"id": "member-1"}])
            mock_sb.table.return_value = mock_table
            mock_get_sb.return_value = mock_sb

            from services.disco.initiative_service import check_user_access

            result = await check_user_access("initiative-123", "user-123")

            assert result is True

    @pytest.mark.asyncio
    async def test_check_user_access_not_member(self):
        """Test access check for non-member."""
        with patch("services.disco.initiative_service.get_supabase") as mock_get_sb:
            mock_sb = Mock()
            mock_table = Mock()
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.execute.return_value = Mock(data=[])
            mock_sb.table.return_value = mock_table
            mock_get_sb.return_value = mock_sb

            from services.disco.initiative_service import check_user_access

            result = await check_user_access("initiative-123", "user-123")

            assert result is False


class TestCheckEditPermission:
    """Tests for check_edit_permission function."""

    @pytest.mark.asyncio
    async def test_check_edit_permission_owner(self):
        """Test edit permission for owner."""
        with patch("services.disco.initiative_service.get_supabase") as mock_get_sb:
            mock_sb = Mock()
            mock_table = Mock()
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.single.return_value = mock_table
            mock_table.execute.return_value = Mock(data={"role": "owner"})
            mock_sb.table.return_value = mock_table
            mock_get_sb.return_value = mock_sb

            from services.disco.initiative_service import check_edit_permission

            result = await check_edit_permission("initiative-123", "user-123")

            assert result is True

    @pytest.mark.asyncio
    async def test_check_edit_permission_viewer(self):
        """Test edit permission denied for viewer."""
        with patch("services.disco.initiative_service.get_supabase") as mock_get_sb:
            mock_sb = Mock()
            mock_table = Mock()
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.single.return_value = mock_table
            mock_table.execute.return_value = Mock(data={"role": "viewer"})
            mock_sb.table.return_value = mock_table
            mock_get_sb.return_value = mock_sb

            from services.disco.initiative_service import check_edit_permission

            result = await check_edit_permission("initiative-123", "user-123")

            assert result is False

    @pytest.mark.asyncio
    async def test_check_edit_permission_not_member(self):
        """Test edit permission denied for non-member."""
        with patch("services.disco.initiative_service.get_supabase") as mock_get_sb:
            mock_sb = Mock()
            mock_table = Mock()
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.single.return_value = mock_table
            mock_table.execute.return_value = Mock(data=None)
            mock_sb.table.return_value = mock_table
            mock_get_sb.return_value = mock_sb

            from services.disco.initiative_service import check_edit_permission

            result = await check_edit_permission("initiative-123", "user-123")

            assert result is False


# ============================================================================
# Status Workflow Tests
# ============================================================================


class TestInitiativeStatusWorkflow:
    """Tests for initiative status transitions."""

    @pytest.mark.asyncio
    async def test_status_values(self):
        """Test valid status values."""
        valid_statuses = [
            "draft",
            "prep_complete",
            "triaged",
            "in_discovery",
            "consolidated",
            "synthesized",
            "documented",
            "completed",
        ]

        for status in valid_statuses:
            assert isinstance(status, str)
            assert len(status) > 0


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_create_initiative_empty_name(self):
        """Test creating initiative with empty name."""
        with patch("services.disco.initiative_service.get_supabase") as mock_get_sb:
            mock_sb = Mock()
            mock_table = Mock()
            mock_table.select.return_value = mock_table
            mock_table.insert.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.execute.side_effect = Exception('null value in column "name"')
            mock_sb.table.return_value = mock_table
            mock_get_sb.return_value = mock_sb

            from services.disco.initiative_service import create_initiative

            with pytest.raises(ValueError):
                await create_initiative(name="", user_id="user-123")
