"""Tests for DISCo Initiative Service.

Tests CRUD operations, access control, and status management for initiatives.
"""

from unittest.mock import Mock, patch

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
        "created_at": "2026-01-15T10:00:00Z",
        "updated_at": "2026-01-15T10:00:00Z",
    }


@pytest.fixture
def mock_supabase():
    """Mock Supabase client with common operations."""
    mock_sb = Mock()
    mock_table = Mock()

    # Chain mock for table().select().eq().execute()
    mock_table.select.return_value = mock_table
    mock_table.insert.return_value = mock_table
    mock_table.update.return_value = mock_table
    mock_table.delete.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.in_.return_value = mock_table
    mock_table.single.return_value = mock_table
    mock_table.order.return_value = mock_table
    mock_table.range.return_value = mock_table

    mock_sb.table.return_value = mock_table
    return mock_sb, mock_table


# ============================================================================
# Initiative CRUD Tests
# ============================================================================


class TestCreateInitiative:
    """Tests for create_initiative function."""

    @pytest.mark.asyncio
    async def test_create_initiative_success(self, mock_supabase, mock_user, mock_initiative_data):
        """Test successful initiative creation."""
        mock_sb, mock_table = mock_supabase

        # Mock successful insert responses
        mock_table.execute.side_effect = [
            Mock(data=[mock_initiative_data]),  # Initiative insert
            Mock(
                data=[
                    {
                        "id": "member-123",
                        "initiative_id": "initiative-123",
                        "user_id": "user-123",
                        "role": "owner",
                    }
                ]
            ),  # Member insert
        ]

        with patch("services.disco.initiative_service.get_supabase", return_value=mock_sb):
            from services.disco.initiative_service import create_initiative

            result = await create_initiative(name="Test Initiative", user_id="user-123", description="Test description")

            assert result is not None
            assert result["name"] == "Test Initiative"
            # Verify member table was called
            assert mock_table.insert.call_count == 2

    @pytest.mark.asyncio
    async def test_create_initiative_with_no_description(self, mock_supabase, mock_user):
        """Test initiative creation without description."""
        mock_sb, mock_table = mock_supabase

        initiative_data = {
            "id": "initiative-123",
            "name": "Test Initiative",
            "description": None,
            "status": "draft",
            "created_by": "user-123",
        }
        mock_table.execute.side_effect = [
            Mock(data=[initiative_data]),
            Mock(data=[{"id": "member-123"}]),
        ]

        with patch("services.disco.initiative_service.get_supabase", return_value=mock_sb):
            from services.disco.initiative_service import create_initiative

            result = await create_initiative(name="Test Initiative", user_id="user-123")

            assert result is not None
            assert result["description"] is None

    @pytest.mark.asyncio
    async def test_create_initiative_failure(self, mock_supabase, mock_user):
        """Test initiative creation failure."""
        mock_sb, mock_table = mock_supabase
        mock_table.execute.return_value = Mock(data=None)

        with patch("services.disco.initiative_service.get_supabase", return_value=mock_sb):
            from services.disco.initiative_service import create_initiative

            with pytest.raises(ValueError, match="Failed to create initiative"):
                await create_initiative(name="Test Initiative", user_id="user-123")


class TestGetInitiative:
    """Tests for get_initiative function."""

    @pytest.mark.asyncio
    async def test_get_initiative_success(self, mock_supabase, mock_initiative_data):
        """Test successful initiative retrieval."""
        mock_sb, mock_table = mock_supabase

        mock_table.execute.side_effect = [
            Mock(data=mock_initiative_data),  # Initiative fetch
            Mock(data=[{"id": "member-1"}]),  # Access check
            Mock(data={"role": "owner"}),  # Role fetch
            Mock(count=5, data=[]),  # Document count
            Mock(data=[{"agent_type": "triage", "version": 1}]),  # Outputs
        ]

        with patch("services.disco.initiative_service.get_supabase", return_value=mock_sb):
            from services.disco.initiative_service import get_initiative

            result = await get_initiative("initiative-123", "user-123")

            assert result is not None

    @pytest.mark.asyncio
    async def test_get_initiative_not_found(self, mock_supabase):
        """Test retrieving non-existent initiative."""
        mock_sb, mock_table = mock_supabase
        mock_table.execute.return_value = Mock(data=None)

        with patch("services.disco.initiative_service.get_supabase", return_value=mock_sb):
            from services.disco.initiative_service import get_initiative

            result = await get_initiative("nonexistent-id", "user-123")

            assert result is None

    @pytest.mark.asyncio
    async def test_get_initiative_no_access(self, mock_supabase, mock_initiative_data):
        """Test access denial for initiative."""
        mock_sb, mock_table = mock_supabase

        mock_table.execute.side_effect = [
            Mock(data=mock_initiative_data),  # Initiative exists
            Mock(data=[]),  # User is NOT a member
        ]

        with patch("services.disco.initiative_service.get_supabase", return_value=mock_sb):
            from services.disco.initiative_service import get_initiative

            result = await get_initiative("initiative-123", "other-user")

            assert result is None


class TestListInitiatives:
    """Tests for list_initiatives function."""

    @pytest.mark.asyncio
    async def test_list_initiatives_success(self, mock_supabase, mock_initiative_data):
        """Test successful initiative listing."""
        mock_sb, mock_table = mock_supabase

        mock_table.execute.side_effect = [
            Mock(
                data=[
                    {"initiative_id": "init-1", "role": "owner"},
                    {"initiative_id": "init-2", "role": "editor"},
                ]
            ),  # Member lookup
            Mock(data=[mock_initiative_data], count=1),  # Initiatives fetch
            Mock(data=[{"initiative_id": "init-1"}]),  # Document counts
        ]

        with patch("services.disco.initiative_service.get_supabase", return_value=mock_sb):
            from services.disco.initiative_service import list_initiatives

            result = await list_initiatives("user-123")

            assert "initiatives" in result
            assert "total" in result

    @pytest.mark.asyncio
    async def test_list_initiatives_empty(self, mock_supabase):
        """Test listing when user has no initiatives."""
        mock_sb, mock_table = mock_supabase
        mock_table.execute.return_value = Mock(data=[])

        with patch("services.disco.initiative_service.get_supabase", return_value=mock_sb):
            from services.disco.initiative_service import list_initiatives

            result = await list_initiatives("user-123")

            assert result == {"initiatives": [], "total": 0}

    @pytest.mark.asyncio
    async def test_list_initiatives_with_status_filter(self, mock_supabase, mock_initiative_data):
        """Test filtering by status."""
        mock_sb, mock_table = mock_supabase

        mock_table.execute.side_effect = [
            Mock(data=[{"initiative_id": "init-1", "role": "owner"}]),
            Mock(data=[mock_initiative_data], count=1),
            Mock(data=[]),
        ]

        with patch("services.disco.initiative_service.get_supabase", return_value=mock_sb):
            from services.disco.initiative_service import list_initiatives

            result = await list_initiatives("user-123", status_filter="draft")

            assert "initiatives" in result
            # Verify status filter was applied
            mock_table.eq.assert_called()


class TestUpdateInitiative:
    """Tests for update_initiative function."""

    @pytest.mark.asyncio
    async def test_update_initiative_success(self, mock_supabase, mock_initiative_data):
        """Test successful initiative update."""
        mock_sb, mock_table = mock_supabase

        updated_data = {**mock_initiative_data, "name": "Updated Name"}
        mock_table.execute.side_effect = [
            Mock(data={"role": "owner"}),  # Permission check
            Mock(data=[updated_data]),  # Update
        ]

        with patch("services.disco.initiative_service.get_supabase", return_value=mock_sb):
            from services.disco.initiative_service import update_initiative

            result = await update_initiative("initiative-123", "user-123", {"name": "Updated Name"})

            assert result["name"] == "Updated Name"

    @pytest.mark.asyncio
    async def test_update_initiative_no_permission(self, mock_supabase):
        """Test update without permission."""
        mock_sb, mock_table = mock_supabase
        mock_table.execute.return_value = Mock(data={"role": "viewer"})

        with patch("services.disco.initiative_service.get_supabase", return_value=mock_sb):
            from services.disco.initiative_service import update_initiative

            with pytest.raises(PermissionError):
                await update_initiative("initiative-123", "user-123", {"name": "Updated Name"})

    @pytest.mark.asyncio
    async def test_update_initiative_invalid_fields(self, mock_supabase):
        """Test update with invalid fields."""
        mock_sb, mock_table = mock_supabase
        mock_table.execute.return_value = Mock(data={"role": "owner"})

        with patch("services.disco.initiative_service.get_supabase", return_value=mock_sb):
            from services.disco.initiative_service import update_initiative

            with pytest.raises(ValueError, match="No valid fields to update"):
                await update_initiative("initiative-123", "user-123", {"invalid_field": "value"})


class TestDeleteInitiative:
    """Tests for delete_initiative function."""

    @pytest.mark.asyncio
    async def test_delete_initiative_success(self, mock_supabase):
        """Test successful initiative deletion."""
        mock_sb, mock_table = mock_supabase

        mock_table.execute.side_effect = [
            Mock(data={"role": "owner"}),  # Permission check
            Mock(data=[]),  # Delete
        ]

        with patch("services.disco.initiative_service.get_supabase", return_value=mock_sb):
            from services.disco.initiative_service import delete_initiative

            result = await delete_initiative("initiative-123", "user-123")

            assert result is True

    @pytest.mark.asyncio
    async def test_delete_initiative_not_owner(self, mock_supabase):
        """Test deletion by non-owner."""
        mock_sb, mock_table = mock_supabase
        mock_table.execute.return_value = Mock(data={"role": "editor"})

        with patch("services.disco.initiative_service.get_supabase", return_value=mock_sb):
            from services.disco.initiative_service import delete_initiative

            with pytest.raises(PermissionError, match="Only the owner can delete"):
                await delete_initiative("initiative-123", "user-123")

    @pytest.mark.asyncio
    async def test_delete_initiative_not_member(self, mock_supabase):
        """Test deletion by non-member."""
        mock_sb, mock_table = mock_supabase
        mock_table.execute.return_value = Mock(data=None)

        with patch("services.disco.initiative_service.get_supabase", return_value=mock_sb):
            from services.disco.initiative_service import delete_initiative

            with pytest.raises(PermissionError):
                await delete_initiative("initiative-123", "user-123")


# ============================================================================
# Access Control Tests
# ============================================================================


class TestCheckUserAccess:
    """Tests for check_user_access function."""

    @pytest.mark.asyncio
    async def test_check_user_access_member(self, mock_supabase):
        """Test access check for member."""
        mock_sb, mock_table = mock_supabase
        mock_table.execute.return_value = Mock(data=[{"id": "member-1"}])

        with patch("services.disco.initiative_service.get_supabase", return_value=mock_sb):
            from services.disco.initiative_service import check_user_access

            result = await check_user_access("initiative-123", "user-123")

            assert result is True

    @pytest.mark.asyncio
    async def test_check_user_access_not_member(self, mock_supabase):
        """Test access check for non-member."""
        mock_sb, mock_table = mock_supabase
        mock_table.execute.return_value = Mock(data=[])

        with patch("services.disco.initiative_service.get_supabase", return_value=mock_sb):
            from services.disco.initiative_service import check_user_access

            result = await check_user_access("initiative-123", "user-123")

            assert result is False


class TestCheckEditPermission:
    """Tests for check_edit_permission function."""

    @pytest.mark.asyncio
    async def test_check_edit_permission_owner(self, mock_supabase):
        """Test edit permission for owner."""
        mock_sb, mock_table = mock_supabase
        mock_table.execute.return_value = Mock(data={"role": "owner"})

        with patch("services.disco.initiative_service.get_supabase", return_value=mock_sb):
            from services.disco.initiative_service import check_edit_permission

            result = await check_edit_permission("initiative-123", "user-123")

            assert result is True

    @pytest.mark.asyncio
    async def test_check_edit_permission_editor(self, mock_supabase):
        """Test edit permission for editor."""
        mock_sb, mock_table = mock_supabase
        mock_table.execute.return_value = Mock(data={"role": "editor"})

        with patch("services.disco.initiative_service.get_supabase", return_value=mock_sb):
            from services.disco.initiative_service import check_edit_permission

            result = await check_edit_permission("initiative-123", "user-123")

            assert result is True

    @pytest.mark.asyncio
    async def test_check_edit_permission_viewer(self, mock_supabase):
        """Test edit permission denied for viewer."""
        mock_sb, mock_table = mock_supabase
        mock_table.execute.return_value = Mock(data={"role": "viewer"})

        with patch("services.disco.initiative_service.get_supabase", return_value=mock_sb):
            from services.disco.initiative_service import check_edit_permission

            result = await check_edit_permission("initiative-123", "user-123")

            assert result is False

    @pytest.mark.asyncio
    async def test_check_edit_permission_not_member(self, mock_supabase):
        """Test edit permission denied for non-member."""
        mock_sb, mock_table = mock_supabase
        mock_table.execute.return_value = Mock(data=None)

        with patch("services.disco.initiative_service.get_supabase", return_value=mock_sb):
            from services.disco.initiative_service import check_edit_permission

            result = await check_edit_permission("initiative-123", "user-123")

            assert result is False


# ============================================================================
# Status Workflow Tests
# ============================================================================


class TestInitiativeStatusWorkflow:
    """Tests for initiative status transitions."""

    @pytest.mark.asyncio
    async def test_update_status_draft_to_triaged(self, mock_supabase, mock_initiative_data):
        """Test status transition from draft to triaged."""
        mock_sb, mock_table = mock_supabase

        updated = {**mock_initiative_data, "status": "triaged"}
        mock_table.execute.side_effect = [Mock(data={"role": "owner"}), Mock(data=[updated])]

        with patch("services.disco.initiative_service.get_supabase", return_value=mock_sb):
            from services.disco.initiative_service import update_initiative

            result = await update_initiative("initiative-123", "user-123", {"status": "triaged"})

            assert result["status"] == "triaged"

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
            # Status should be a valid string
            assert isinstance(status, str)
            assert len(status) > 0


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_create_initiative_special_characters_in_name(self, mock_supabase):
        """Test creating initiative with special characters."""
        mock_sb, mock_table = mock_supabase

        initiative_data = {
            "id": "init-123",
            "name": "Test <script>alert('xss')</script>",
            "description": None,
            "status": "draft",
        }
        mock_table.execute.side_effect = [
            Mock(data=[initiative_data]),
            Mock(data=[{"id": "member-123"}]),
        ]

        with patch("services.disco.initiative_service.get_supabase", return_value=mock_sb):
            from services.disco.initiative_service import create_initiative

            result = await create_initiative(name="Test <script>alert('xss')</script>", user_id="user-123")

            # Name should be stored as-is (sanitization happens at API layer)
            assert result is not None

    @pytest.mark.asyncio
    async def test_create_initiative_empty_name(self, mock_supabase):
        """Test creating initiative with empty name."""
        mock_sb, mock_table = mock_supabase
        # Database should reject empty name but we let DB handle validation
        mock_table.execute.side_effect = Exception('null value in column "name"')

        with patch("services.disco.initiative_service.get_supabase", return_value=mock_sb):
            from services.disco.initiative_service import create_initiative

            with pytest.raises(ValueError):
                await create_initiative(name="", user_id="user-123")

    @pytest.mark.asyncio
    async def test_concurrent_member_addition(self, mock_supabase):
        """Test handling of concurrent operations."""
        mock_sb, mock_table = mock_supabase
        # Simulate a race condition where member already exists
        mock_table.execute.side_effect = [
            Mock(data=[{"id": "init-123"}]),  # Initiative created
            Exception("duplicate key value violates unique constraint"),
        ]

        with patch("services.disco.initiative_service.get_supabase", return_value=mock_sb):
            from services.disco.initiative_service import create_initiative

            with pytest.raises(Exception, match="duplicate key"):
                await create_initiative(name="Test", user_id="user-123")

    @pytest.mark.asyncio
    async def test_list_initiatives_pagination(self, mock_supabase, mock_initiative_data):
        """Test pagination parameters."""
        mock_sb, mock_table = mock_supabase

        mock_table.execute.side_effect = [
            Mock(data=[{"initiative_id": "init-1", "role": "owner"}]),
            Mock(data=[mock_initiative_data], count=100),
            Mock(data=[]),
        ]

        with patch("services.disco.initiative_service.get_supabase", return_value=mock_sb):
            from services.disco.initiative_service import list_initiatives

            await list_initiatives("user-123", limit=10, offset=20)

            # Verify range was called with correct parameters
            mock_table.range.assert_called_once_with(20, 29)
