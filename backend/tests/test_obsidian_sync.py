"""
Tests for Obsidian Vault Sync functionality.

Tests cover:
- Frontmatter parsing
- Wikilink conversion
- File change detection (hash computation)
- Pattern matching (include/exclude)
- Sync state tracking
- Full vault scanning
"""

import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ============================================================================
# Frontmatter Parsing Tests
# ============================================================================

class TestFrontmatterParsing:
    """Tests for YAML frontmatter parsing."""

    def test_parse_frontmatter_basic(self):
        """Test parsing basic frontmatter."""
        from services.obsidian_sync import parse_frontmatter

        content = """---
title: My Note
tags:
  - project
  - thesis
---
# Content here
This is the body."""

        frontmatter, body = parse_frontmatter(content)

        assert frontmatter["title"] == "My Note"
        assert frontmatter["tags"] == ["project", "thesis"]
        assert body.strip().startswith("# Content here")

    def test_parse_frontmatter_with_thesis_agents(self):
        """Test parsing frontmatter with thesis-agents field."""
        from services.obsidian_sync import parse_frontmatter

        content = """---
title: Financial Analysis
thesis-agents:
  - atlas
  - capital
date: 2026-01-15
---
# Analysis

Content goes here."""

        frontmatter, body = parse_frontmatter(content)

        assert frontmatter["title"] == "Financial Analysis"
        assert frontmatter["thesis-agents"] == ["atlas", "capital"]
        assert "date" in frontmatter

    def test_parse_frontmatter_empty(self):
        """Test parsing content without frontmatter."""
        from services.obsidian_sync import parse_frontmatter

        content = """# No Frontmatter

Just regular markdown content."""

        frontmatter, body = parse_frontmatter(content)

        assert frontmatter == {}
        assert body == content

    def test_parse_frontmatter_incomplete(self):
        """Test parsing incomplete frontmatter (no closing ---)."""
        from services.obsidian_sync import parse_frontmatter

        content = """---
title: Incomplete
This has no closing delimiter."""

        frontmatter, body = parse_frontmatter(content)

        # Should return empty frontmatter if malformed
        assert frontmatter == {}
        assert body == content

    def test_parse_frontmatter_invalid_yaml(self):
        """Test parsing invalid YAML in frontmatter."""
        from services.obsidian_sync import parse_frontmatter

        content = """---
title: [invalid yaml
  - missing bracket
---
# Content"""

        frontmatter, body = parse_frontmatter(content)

        # Should handle gracefully
        assert frontmatter == {}


# ============================================================================
# Wikilink Conversion Tests
# ============================================================================

class TestWikilinkConversion:
    """Tests for Obsidian [[wikilink]] to markdown link conversion."""

    def test_convert_simple_wikilink(self):
        """Test converting simple [[Note Name]] wikilinks."""
        from services.obsidian_sync import convert_wikilinks

        content = "See [[My Note]] for details."
        result = convert_wikilinks(content)

        assert result == "See [My Note](My Note.md) for details."

    def test_convert_wikilink_with_alias(self):
        """Test converting [[Note|Alias]] wikilinks."""
        from services.obsidian_sync import convert_wikilinks

        content = "Check out [[Long Note Title|this note]]."
        result = convert_wikilinks(content)

        assert result == "Check out [this note](Long Note Title.md)."

    def test_convert_wikilink_with_path(self):
        """Test converting [[folder/Note]] wikilinks."""
        from services.obsidian_sync import convert_wikilinks

        content = "See [[projects/Project Alpha]] for more."
        result = convert_wikilinks(content)

        assert result == "See [Project Alpha](projects/Project Alpha.md) for more."

    def test_convert_multiple_wikilinks(self):
        """Test converting multiple wikilinks in one document."""
        from services.obsidian_sync import convert_wikilinks

        content = """
# Meeting Notes

Discussed [[Project Alpha]] and [[Project Beta|Beta project]].
Also see [[meetings/2026-01-15]].
"""
        result = convert_wikilinks(content)

        assert "[Project Alpha](Project Alpha.md)" in result
        assert "[Beta project](Project Beta.md)" in result
        assert "[2026-01-15](meetings/2026-01-15.md)" in result

    def test_convert_wikilink_already_has_extension(self):
        """Test that .md extension is not duplicated."""
        from services.obsidian_sync import convert_wikilinks

        content = "See [[Note.md]] link."
        result = convert_wikilinks(content)

        # Should not add .md again
        assert result == "See [Note.md](Note.md) link."

    def test_no_wikilinks(self):
        """Test content without wikilinks is unchanged."""
        from services.obsidian_sync import convert_wikilinks

        content = "Regular markdown with [standard](links.md)."
        result = convert_wikilinks(content)

        assert result == content


# ============================================================================
# File Hash Tests
# ============================================================================

class TestFileHash:
    """Tests for file content hash computation."""

    def test_compute_file_hash(self):
        """Test MD5 hash computation for change detection."""
        from services.obsidian_sync import compute_file_hash

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Test Content\n\nSome text here.")
            f.flush()
            temp_path = Path(f.name)

        try:
            hash1 = compute_file_hash(temp_path)
            assert len(hash1) == 32  # MD5 hex digest length
            assert hash1.isalnum()

            # Same content should produce same hash
            hash2 = compute_file_hash(temp_path)
            assert hash1 == hash2

        finally:
            temp_path.unlink()

    def test_hash_changes_with_content(self):
        """Test that hash changes when file content changes."""
        from services.obsidian_sync import compute_file_hash

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("Original content")
            f.flush()
            temp_path = Path(f.name)

        try:
            hash1 = compute_file_hash(temp_path)

            # Modify file
            with open(temp_path, "w") as f:
                f.write("Modified content")

            hash2 = compute_file_hash(temp_path)

            assert hash1 != hash2

        finally:
            temp_path.unlink()


# ============================================================================
# Pattern Matching Tests
# ============================================================================

class TestPatternMatching:
    """Tests for file include/exclude pattern matching."""

    def test_include_markdown_files(self):
        """Test that .md files are included by default pattern."""
        from services.obsidian_sync import should_include_file

        vault_path = Path("/vault")
        file_path = Path("/vault/notes/my-note.md")

        result = should_include_file(
            file_path,
            vault_path,
            include_patterns=["**/*.md"],
            exclude_patterns=[]
        )

        assert result is True

    def test_exclude_obsidian_folder(self):
        """Test that .obsidian folder is excluded."""
        from services.obsidian_sync import should_include_file

        vault_path = Path("/vault")
        file_path = Path("/vault/.obsidian/plugins/something.md")

        result = should_include_file(
            file_path,
            vault_path,
            include_patterns=["**/*.md"],
            exclude_patterns=[".obsidian/**"]
        )

        assert result is False

    def test_exclude_trash_folder(self):
        """Test that .trash folder is excluded."""
        from services.obsidian_sync import should_include_file

        vault_path = Path("/vault")
        file_path = Path("/vault/.trash/deleted-note.md")

        result = should_include_file(
            file_path,
            vault_path,
            include_patterns=["**/*.md"],
            exclude_patterns=[".trash/**"]
        )

        assert result is False

    def test_exclude_git_folder(self):
        """Test that .git folder is excluded."""
        from services.obsidian_sync import should_include_file

        vault_path = Path("/vault")
        file_path = Path("/vault/.git/config")

        result = should_include_file(
            file_path,
            vault_path,
            include_patterns=["**/*.md"],
            exclude_patterns=[".git/**"]
        )

        assert result is False

    def test_non_markdown_excluded(self):
        """Test that non-markdown files are excluded by pattern."""
        from services.obsidian_sync import should_include_file

        vault_path = Path("/vault")
        file_path = Path("/vault/image.png")

        result = should_include_file(
            file_path,
            vault_path,
            include_patterns=["**/*.md"],
            exclude_patterns=[]
        )

        assert result is False

    def test_nested_markdown_included(self):
        """Test that nested markdown files are included."""
        from services.obsidian_sync import should_include_file

        vault_path = Path("/vault")
        file_path = Path("/vault/projects/2026/january/meeting-notes.md")

        result = should_include_file(
            file_path,
            vault_path,
            include_patterns=["**/*.md"],
            exclude_patterns=[".obsidian/**", ".trash/**"]
        )

        assert result is True


# ============================================================================
# Vault Scanning Tests
# ============================================================================

class TestVaultScanning:
    """Tests for vault directory scanning."""

    def test_scan_vault_finds_markdown_files(self):
        """Test that scan_vault finds all markdown files."""
        from services.obsidian_sync import scan_vault

        with tempfile.TemporaryDirectory() as vault_dir:
            vault_path = Path(vault_dir)

            # Create test structure
            (vault_path / "note1.md").write_text("# Note 1")
            (vault_path / "folder").mkdir()
            (vault_path / "folder" / "note2.md").write_text("# Note 2")
            (vault_path / "image.png").write_bytes(b"fake image")

            # Create .obsidian folder (should be excluded)
            (vault_path / ".obsidian").mkdir()
            (vault_path / ".obsidian" / "config.md").write_text("config")

            files = scan_vault(
                vault_path,
                include_patterns=["**/*.md"],
                exclude_patterns=[".obsidian/**"]
            )

            file_names = [f.name for f in files]

            assert "note1.md" in file_names
            assert "note2.md" in file_names
            assert "config.md" not in file_names
            assert len(files) == 2

    def test_scan_vault_respects_size_limit(self):
        """Test that scan_vault respects max file size."""
        from services.obsidian_sync import scan_vault

        with tempfile.TemporaryDirectory() as vault_dir:
            vault_path = Path(vault_dir)

            # Create small file
            (vault_path / "small.md").write_text("small content")

            # Create large file (> 1 MB)
            (vault_path / "large.md").write_text("x" * (2 * 1024 * 1024))

            files = scan_vault(
                vault_path,
                include_patterns=["**/*.md"],
                exclude_patterns=[],
                max_file_size_mb=1  # 1 MB limit
            )

            file_names = [f.name for f in files]

            assert "small.md" in file_names
            assert "large.md" not in file_names


# ============================================================================
# Sync State Tests (with mocked database)
# ============================================================================

class TestSyncState:
    """Tests for sync state management."""

    def test_update_sync_state_creates_new(self):
        """Test creating a new sync state entry."""
        from services.obsidian_sync import update_sync_state

        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{
            "id": "new-state-id",
            "config_id": "config-123",
            "file_path": "notes/test.md",
            "sync_status": "synced"
        }])

        with patch("services.obsidian_sync.supabase", mock_supabase):
            with patch("services.obsidian_sync.get_sync_state", return_value=None):
                result = update_sync_state(
                    config_id="config-123",
                    file_path="notes/test.md",
                    file_hash="abc123",
                    sync_status="synced"
                )

                assert result.get("sync_status") == "synced"

    def test_get_all_sync_states(self):
        """Test retrieving all sync states for a vault."""
        from services.obsidian_sync import get_all_sync_states

        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[
            {"file_path": "note1.md", "sync_status": "synced"},
            {"file_path": "note2.md", "sync_status": "pending"},
        ])

        with patch("services.obsidian_sync.supabase", mock_supabase):
            states = get_all_sync_states("config-123")

            assert "note1.md" in states
            assert "note2.md" in states
            assert states["note1.md"]["sync_status"] == "synced"


# ============================================================================
# Vault Configuration Tests
# ============================================================================

class TestVaultConfiguration:
    """Tests for vault configuration management."""

    def test_create_vault_config_validates_path(self):
        """Test that create_vault_config validates the vault path exists."""
        from services.obsidian_sync import create_vault_config, ObsidianSyncError

        with pytest.raises(ObsidianSyncError) as exc_info:
            create_vault_config(
                user_id="user-123",
                client_id="client-123",
                vault_path="/nonexistent/path/to/vault"
            )

        assert "does not exist" in str(exc_info.value)

    def test_create_vault_config_rejects_file_path(self):
        """Test that create_vault_config rejects file paths."""
        from services.obsidian_sync import create_vault_config, ObsidianSyncError

        with tempfile.NamedTemporaryFile(suffix=".md") as f:
            with pytest.raises(ObsidianSyncError) as exc_info:
                create_vault_config(
                    user_id="user-123",
                    client_id="client-123",
                    vault_path=f.name
                )

            assert "not a directory" in str(exc_info.value)


# ============================================================================
# Integration-style Tests (with mocked external services)
# ============================================================================

class TestSyncFile:
    """Tests for single file sync operation."""

    def test_sync_file_creates_document(self):
        """Test that sync_file creates a document for new files."""
        from services.obsidian_sync import sync_file

        with tempfile.TemporaryDirectory() as vault_dir:
            vault_path = Path(vault_dir)
            file_path = vault_path / "test-note.md"
            file_path.write_text("""---
title: Test Note
---
# Test Content

This is test content.""")

            config = {
                "id": "config-123",
                "user_id": "user-123",
                "client_id": "client-123",
                "vault_path": str(vault_path),
                "sync_options": {
                    "parse_frontmatter": True,
                    "convert_wikilinks": True
                }
            }

            mock_supabase = MagicMock()
            # Mock storage upload
            mock_supabase.storage.from_.return_value.upload.return_value = MagicMock()
            # Mock document insert
            mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(
                data=[{"id": "doc-123", "filename": "test-note.md"}]
            )
            # Mock agents query (empty - no thesis-agents in frontmatter)
            mock_supabase.table.return_value.select.return_value.in_.return_value.execute.return_value = MagicMock(data=[])

            with patch("services.obsidian_sync.supabase", mock_supabase):
                with patch("services.obsidian_sync.process_document"):
                    with patch("services.obsidian_sync.update_sync_state", return_value={}):
                        with patch("services.obsidian_sync.SUPABASE_URL", "https://test.supabase.co"):
                            result = sync_file(config, file_path, existing_state=None)

                            assert result["status"] == "added"
                            assert result["document_id"] == "doc-123"


# ============================================================================
# API Route Tests
# ============================================================================

class TestObsidianAPIRoutes:
    """Tests for Obsidian sync API routes."""

    def test_status_endpoint_no_vault(self, authenticated_client):
        """Test /api/obsidian/status when no vault configured."""
        with patch("services.obsidian_sync.get_sync_status", return_value={
            "connected": False,
            "vault_path": None,
            "files_synced": 0
        }):
            response = authenticated_client.get("/api/obsidian/status")

            # Should return success even with no vault
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["connected"] is False

    def test_configure_endpoint_validates_path(self, authenticated_client):
        """Test that /api/obsidian/configure validates vault path."""
        with patch("services.obsidian_sync.create_vault_config") as mock_create:
            from services.obsidian_sync import ObsidianSyncError
            mock_create.side_effect = ObsidianSyncError("Vault path does not exist")

            response = authenticated_client.post(
                "/api/obsidian/configure",
                json={"vault_path": "/nonexistent/path"}
            )

            assert response.status_code == 400
            assert "does not exist" in response.json()["detail"]


# ============================================================================
# Watcher Tests
# ============================================================================

class TestObsidianVaultWatcher:
    """Tests for the file watcher functionality."""

    def test_watcher_should_process_markdown(self):
        """Test that watcher processes markdown files."""
        from services.obsidian_sync import ObsidianVaultWatcher

        with tempfile.TemporaryDirectory() as vault_dir:
            config = {
                "id": "config-123",
                "user_id": "user-123",
                "client_id": "client-123",
                "vault_path": vault_dir,
                "sync_options": {
                    "include_patterns": ["**/*.md"],
                    "exclude_patterns": [".obsidian/**"],
                    "debounce_ms": 100
                }
            }

            watcher = ObsidianVaultWatcher(config)

            # Test internal method
            md_file = Path(vault_dir) / "test.md"
            md_file.write_text("# Test")

            assert watcher._should_process(md_file) is True

            txt_file = Path(vault_dir) / "test.txt"
            assert watcher._should_process(txt_file) is False

    def test_watcher_excludes_obsidian_folder(self):
        """Test that watcher excludes .obsidian folder."""
        from services.obsidian_sync import ObsidianVaultWatcher

        with tempfile.TemporaryDirectory() as vault_dir:
            vault_path = Path(vault_dir)

            # Create .obsidian folder
            obsidian_dir = vault_path / ".obsidian"
            obsidian_dir.mkdir()
            config_file = obsidian_dir / "config.md"
            config_file.write_text("config")

            config = {
                "id": "config-123",
                "user_id": "user-123",
                "client_id": "client-123",
                "vault_path": vault_dir,
                "sync_options": {
                    "include_patterns": ["**/*.md"],
                    "exclude_patterns": [".obsidian/**"],
                    "debounce_ms": 100
                }
            }

            watcher = ObsidianVaultWatcher(config)

            assert watcher._should_process(config_file) is False
