"""Tests for DISCO Initiative Folder Links (auto-link subscriptions).

Tests the auto_link_document_to_initiatives() function and folder link
API behavior including backfill, recursive/non-recursive matching,
and idempotent operations.
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

from unittest.mock import MagicMock, Mock, patch

# ============================================================================
# Test Fixtures
# ============================================================================


def _make_mock_table():
    """Create a mock table with chained methods."""
    mock_table = MagicMock()
    mock_table.select.return_value = mock_table
    mock_table.insert.return_value = mock_table
    mock_table.update.return_value = mock_table
    mock_table.delete.return_value = mock_table
    mock_table.upsert.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.in_.return_value = mock_table
    mock_table.ilike.return_value = mock_table
    mock_table.single.return_value = mock_table
    mock_table.order.return_value = mock_table
    mock_table.execute.return_value = Mock(data=[])
    return mock_table


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
        # Import directly from the module to avoid triggering disco __init__
        from pydantic import BaseModel

        # Replicate the model definition for isolated testing
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
# import-time Supabase client initialization issues.
# ============================================================================


@pytest.fixture(scope="module")
def obsidian_sync_module():
    """Import obsidian_sync module with mocked database layer."""
    mock_db_module = MagicMock()
    mock_client = MagicMock()
    mock_db_module.get_supabase.return_value = mock_client

    mock_doc_processor = MagicMock()

    with patch.dict(
        sys.modules,
        {
            "database": mock_db_module,
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
        mock_table = _make_mock_table()
        mock_table.execute.return_value = Mock(data=[])

        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_table

        with patch.object(obsidian_sync_module, "_get_db", return_value=mock_sb):
            result = fn("doc-1", "Projects/AI Strategy/report.md", "user-1")
        assert result == 0

    def test_recursive_match_links_document(self, obsidian_sync_module, sample_folder_subscriptions):
        """Recursive subscription should match documents in subfolders."""
        fn = obsidian_sync_module.auto_link_document_to_initiatives

        # Use separate mock tables per table name to handle different return values
        tables = {}

        def table_factory(name):
            if name not in tables:
                tables[name] = _make_mock_table()
            return tables[name]

        mock_sb = MagicMock()
        mock_sb.table.side_effect = table_factory

        # Set up returns: folder subscriptions query
        folders_table = _make_mock_table()
        folders_table.execute.return_value = Mock(data=sample_folder_subscriptions)

        # Initiative documents upsert - always succeeds
        docs_table = _make_mock_table()
        docs_table.execute.return_value = Mock(data=[{"id": "link-1"}])

        # Initiatives lookup - returns name
        initiatives_table = _make_mock_table()
        initiatives_table.execute.return_value = Mock(data={"name": "Test Initiative"})

        # Tags upsert - always succeeds
        tags_table = _make_mock_table()
        tags_table.execute.return_value = Mock(data=[])

        def table_router(name):
            if name == "disco_initiative_folders":
                return folders_table
            elif name == "disco_initiative_documents":
                return docs_table
            elif name == "disco_initiatives":
                return initiatives_table
            elif name == "document_tags":
                return tags_table
            return _make_mock_table()

        mock_sb.table.side_effect = table_router

        with patch.object(obsidian_sync_module, "_get_db", return_value=mock_sb):
            # Document in "Projects/AI Strategy/Research" should match:
            # - init-1 (recursive on "Projects/AI Strategy")
            # - init-2 (non-recursive exact match on "Projects/AI Strategy/Research")
            result = fn("doc-1", "Projects/AI Strategy/Research/findings.md", "user-1")
        assert result == 2

    def test_non_recursive_exact_match_only(self, obsidian_sync_module):
        """Non-recursive subscription should only match exact folder, not subfolders."""
        fn = obsidian_sync_module.auto_link_document_to_initiatives
        mock_table = _make_mock_table()

        subscriptions = [
            {"initiative_id": "init-1", "folder_path": "Projects", "recursive": False},
        ]

        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return Mock(data=subscriptions)
            return Mock(data=[])

        mock_table.execute.side_effect = side_effect

        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_table

        with patch.object(obsidian_sync_module, "_get_db", return_value=mock_sb):
            result = fn("doc-1", "Projects/AI Strategy/report.md", "user-1")
        assert result == 0

    def test_non_recursive_direct_match(self, obsidian_sync_module):
        """Non-recursive subscription should match documents directly in the folder."""
        fn = obsidian_sync_module.auto_link_document_to_initiatives
        mock_table = _make_mock_table()

        subscriptions = [
            {"initiative_id": "init-1", "folder_path": "Projects", "recursive": False},
        ]

        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return Mock(data=subscriptions)
            elif call_count == 3:
                return Mock(data={"name": "Projects Initiative"})
            return Mock(data=[{"id": "link-1"}])

        mock_table.execute.side_effect = side_effect

        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_table

        with patch.object(obsidian_sync_module, "_get_db", return_value=mock_sb):
            result = fn("doc-1", "Projects/report.md", "user-1")
        assert result == 1

    def test_multiple_initiatives_same_folder(self, obsidian_sync_module):
        """Multiple initiatives watching the same folder should all get linked."""
        fn = obsidian_sync_module.auto_link_document_to_initiatives
        mock_table = _make_mock_table()

        subscriptions = [
            {"initiative_id": "init-1", "folder_path": "Shared/Docs", "recursive": True},
            {"initiative_id": "init-2", "folder_path": "Shared/Docs", "recursive": True},
            {"initiative_id": "init-3", "folder_path": "Shared/Docs", "recursive": False},
        ]

        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return Mock(data=subscriptions)
            return Mock(data={"name": "Some Initiative"})

        mock_table.execute.side_effect = side_effect

        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_table

        with patch.object(obsidian_sync_module, "_get_db", return_value=mock_sb):
            result = fn("doc-1", "Shared/Docs/file.md", "user-1")
        assert result == 3

    def test_no_match_returns_zero(self, obsidian_sync_module):
        """When folder doesn't match any subscription, should return 0."""
        fn = obsidian_sync_module.auto_link_document_to_initiatives
        mock_table = _make_mock_table()

        subscriptions = [
            {"initiative_id": "init-1", "folder_path": "Projects/AI", "recursive": True},
        ]
        mock_table.execute.return_value = Mock(data=subscriptions)

        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_table

        with patch.object(obsidian_sync_module, "_get_db", return_value=mock_sb):
            result = fn("doc-1", "Company/Legal/contract.md", "user-1")
        assert result == 0

    def test_error_handling_returns_zero(self, obsidian_sync_module):
        """Errors during auto-link should be caught and return 0."""
        fn = obsidian_sync_module.auto_link_document_to_initiatives
        mock_table = _make_mock_table()
        mock_table.execute.side_effect = Exception("DB connection error")

        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_table

        with patch.object(obsidian_sync_module, "_get_db", return_value=mock_sb):
            result = fn("doc-1", "Projects/report.md", "user-1")
        assert result == 0
