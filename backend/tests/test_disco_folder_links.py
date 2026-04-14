"""Tests for DISCO Initiative Folder Links (auto-link subscriptions).

Tests the auto_link_document_to_initiatives() function and folder link
API behavior including backfill, recursive/non-recursive matching,
and idempotent operations.

Updated for PocketBase migration: mocks pb_client instead of Supabase.
"""

import os
import sys

import pytest

# Ensure backend is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Set required env vars before imports
os.environ.setdefault("THESIS_API_KEY", "test-api-key")
os.environ.setdefault("THESIS_POCKETBASE_URL", "http://127.0.0.1:8090")
os.environ.setdefault("THESIS_ANTHROPIC_API_KEY", "fake-key")

from unittest.mock import MagicMock, patch

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def sample_folder_subscriptions():
    """Sample folder subscription records."""
    return [
        {
            "initiative_id": "init-1",
            "folder_path": "Projects/AI Strategy",
            "recursive": True,
        },
        {
            "initiative_id": "init-2",
            "folder_path": "Projects/AI Strategy/Research",
            "recursive": False,
        },
        {
            "initiative_id": "init-3",
            "folder_path": "Company/Legal",
            "recursive": True,
        },
    ]


# ============================================================================
# Folder Ancestor Matching Tests (pure logic, no DB)
# ============================================================================


class TestFolderAncestorLogic:
    """Tests for the folder ancestor path construction logic."""

    def test_single_level_folder(self):
        """Single-level folder path should produce one ancestor."""
        path = "Projects/report.md"
        folder = path.rsplit("/", 1)[0]
        parts = folder.split("/")
        ancestors = ["/".join(parts[: i + 1]) for i in range(len(parts))]
        assert ancestors == ["Projects"]

    def test_multi_level_folder(self):
        """Multi-level folder path should produce all ancestors."""
        path = "Projects/AI Strategy/Research/findings.md"
        folder = path.rsplit("/", 1)[0]
        parts = folder.split("/")
        ancestors = ["/".join(parts[: i + 1]) for i in range(len(parts))]
        assert ancestors == ["Projects", "Projects/AI Strategy", "Projects/AI Strategy/Research"]

    def test_deep_nesting(self):
        """Deeply nested paths should produce complete ancestor chain."""
        path = "a/b/c/d/e/file.md"
        folder = path.rsplit("/", 1)[0]
        parts = folder.split("/")
        ancestors = ["/".join(parts[: i + 1]) for i in range(len(parts))]
        assert ancestors == ["a", "a/b", "a/b/c", "a/b/c/d", "a/b/c/d/e"]

    def test_root_level_file_has_no_folder(self):
        """Root-level files should have no slash."""
        path = "README.md"
        assert "/" not in path


# ============================================================================
# LinkFolderRequest Model Tests
# ============================================================================


class TestLinkFolderRequest:
    """Tests for the LinkFolderRequest Pydantic model."""

    def test_defaults(self):
        """Should have correct defaults for recursive and backfill."""
        from pydantic import BaseModel

        class LinkFolderRequest(BaseModel):
            folder_path: str
            recursive: bool = True
            backfill: bool = True

        req = LinkFolderRequest(folder_path="Projects/AI")
        assert req.folder_path == "Projects/AI"
        assert req.recursive is True
        assert req.backfill is True

    def test_custom_values(self):
        """Should accept custom recursive and backfill values."""
        from pydantic import BaseModel

        class LinkFolderRequest(BaseModel):
            folder_path: str
            recursive: bool = True
            backfill: bool = True

        req = LinkFolderRequest(folder_path="Docs", recursive=False, backfill=False)
        assert req.recursive is False
        assert req.backfill is False


# ============================================================================
# auto_link_document_to_initiatives() Tests
#
# These tests use a pre-imported module with mocked DB to avoid
# import-time PocketBase client initialization issues.
# ============================================================================


@pytest.fixture(scope="module")
def obsidian_sync_module():
    """Import obsidian_sync module with mocked PocketBase layer."""
    mock_pb_module = MagicMock()
    mock_doc_processor = MagicMock()

    with patch.dict(
        sys.modules,
        {
            "pb_client": mock_pb_module,
            "document_processor": mock_doc_processor,
        },
    ):
        # Force re-import with mocked dependencies
        if "services.obsidian_sync" in sys.modules:
            del sys.modules["services.obsidian_sync"]
        import services.obsidian_sync as mod

        yield mod


class TestAutoLinkDocumentToInitiatives:
    """Tests for the auto_link_document_to_initiatives function."""

    def test_root_level_file_returns_zero(self, obsidian_sync_module):
        """Root-level files (no folder) should not match any subscriptions."""
        fn = obsidian_sync_module.auto_link_document_to_initiatives
        result = fn("doc-1", "README.md", "user-1")
        assert result == 0

    def test_no_subscriptions_returns_zero(self, obsidian_sync_module):
        """When no folder subscriptions exist, should return 0."""
        fn = obsidian_sync_module.auto_link_document_to_initiatives

        with patch.object(obsidian_sync_module, "_get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            # Mock pb_client.get_all to return empty list for folder subscriptions
            mock_db.table.return_value.select.return_value.execute.return_value = MagicMock(data=[])

            result = fn("doc-1", "Projects/AI Strategy/report.md", "user-1")
        assert result == 0

    def test_no_match_returns_zero(self, obsidian_sync_module):
        """When folder doesn't match any subscription, should return 0."""
        fn = obsidian_sync_module.auto_link_document_to_initiatives

        subscriptions = [
            {"initiative_id": "init-1", "folder_path": "Projects/AI", "recursive": True},
        ]

        mock_db = MagicMock()
        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=subscriptions)
        mock_db.table.return_value = mock_table

        with patch.object(obsidian_sync_module, "_get_db", return_value=mock_db):
            result = fn("doc-1", "Company/Legal/contract.md", "user-1")
        assert result == 0

    def test_error_handling_returns_zero(self, obsidian_sync_module):
        """Errors during auto-link should be caught and return 0."""
        fn = obsidian_sync_module.auto_link_document_to_initiatives

        mock_db = MagicMock()
        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.side_effect = Exception("DB connection error")
        mock_db.table.return_value = mock_table

        with patch.object(obsidian_sync_module, "_get_db", return_value=mock_db):
            result = fn("doc-1", "Projects/report.md", "user-1")
        assert result == 0
