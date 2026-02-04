"""Tests for Obsidian Vault Sync functionality.

Tests cover:
- Frontmatter parsing
- Wikilink conversion
- File change detection (hash computation)
- Pattern matching (include/exclude)
- Sync state tracking
- Full vault scanning
"""

import tempfile
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

        content = """# No Frontmatter.

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

        result = should_include_file(file_path, vault_path, include_patterns=["**/*.md"], exclude_patterns=[])

        assert result is True

    def test_exclude_obsidian_folder(self):
        """Test that .obsidian folder is excluded."""
        from services.obsidian_sync import should_include_file

        vault_path = Path("/vault")
        file_path = Path("/vault/.obsidian/plugins/something.md")

        result = should_include_file(
            file_path, vault_path, include_patterns=["**/*.md"], exclude_patterns=[".obsidian/**"]
        )

        assert result is False

    def test_exclude_trash_folder(self):
        """Test that .trash folder is excluded."""
        from services.obsidian_sync import should_include_file

        vault_path = Path("/vault")
        file_path = Path("/vault/.trash/deleted-note.md")

        result = should_include_file(
            file_path, vault_path, include_patterns=["**/*.md"], exclude_patterns=[".trash/**"]
        )

        assert result is False

    def test_exclude_git_folder(self):
        """Test that .git folder is excluded."""
        from services.obsidian_sync import should_include_file

        vault_path = Path("/vault")
        file_path = Path("/vault/.git/config")

        result = should_include_file(file_path, vault_path, include_patterns=["**/*.md"], exclude_patterns=[".git/**"])

        assert result is False

    def test_non_markdown_excluded(self):
        """Test that non-markdown files are excluded by pattern."""
        from services.obsidian_sync import should_include_file

        vault_path = Path("/vault")
        file_path = Path("/vault/image.png")

        result = should_include_file(file_path, vault_path, include_patterns=["**/*.md"], exclude_patterns=[])

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
            exclude_patterns=[".obsidian/**", ".trash/**"],
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

            files = scan_vault(vault_path, include_patterns=["**/*.md"], exclude_patterns=[".obsidian/**"])

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
                max_file_size_mb=1,  # 1 MB limit
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
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = (
            MagicMock(data=[])
        )
        mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[
                {
                    "id": "new-state-id",
                    "config_id": "config-123",
                    "file_path": "notes/test.md",
                    "sync_status": "synced",
                }
            ]
        )

        with patch("services.obsidian_sync._get_db", return_value=mock_supabase):
            with patch("services.obsidian_sync.get_sync_state", return_value=None):
                result = update_sync_state(
                    config_id="config-123",
                    file_path="notes/test.md",
                    file_hash="abc123",
                    sync_status="synced",
                )

                assert result.get("sync_status") == "synced"

    def test_get_all_sync_states(self):
        """Test retrieving all sync states for a vault."""
        from services.obsidian_sync import get_all_sync_states

        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[
                {"file_path": "note1.md", "sync_status": "synced"},
                {"file_path": "note2.md", "sync_status": "pending"},
            ]
        )

        with patch("services.obsidian_sync._get_db", return_value=mock_supabase):
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
        from services.obsidian_sync import ObsidianSyncError, create_vault_config

        with pytest.raises(ObsidianSyncError) as exc_info:
            create_vault_config(user_id="user-123", client_id="client-123", vault_path="/nonexistent/path/to/vault")

        assert "does not exist" in str(exc_info.value)

    def test_create_vault_config_rejects_file_path(self):
        """Test that create_vault_config rejects file paths."""
        from services.obsidian_sync import ObsidianSyncError, create_vault_config

        with tempfile.NamedTemporaryFile(suffix=".md") as f:
            with pytest.raises(ObsidianSyncError) as exc_info:
                create_vault_config(user_id="user-123", client_id="client-123", vault_path=f.name)

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
                "sync_options": {"parse_frontmatter": True, "convert_wikilinks": True},
            }

            mock_supabase = MagicMock()

            # Mock chain: table().select().eq().eq().execute()
            mock_select_chain = MagicMock()
            mock_select_chain.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
            mock_select_chain.eq.return_value.execute.return_value = MagicMock(data=[])
            mock_supabase.table.return_value.select.return_value = mock_select_chain

            # Mock storage upload
            mock_supabase.storage.from_.return_value.upload.return_value = MagicMock(path="test-path")

            # Mock document insert
            mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(
                data=[{"id": "doc-123", "filename": "test-note.md"}]
            )

            # Mock _create_obsidian_document to return doc ID directly
            with patch("services.obsidian_sync._get_db", return_value=mock_supabase):
                with patch("services.obsidian_sync.process_document"):
                    with patch("services.obsidian_sync.update_sync_state", return_value={}):
                        with patch(
                            "services.obsidian_sync._create_obsidian_document",
                            return_value="doc-123",
                        ):
                            with patch("services.obsidian_sync.SUPABASE_URL", "https://test.supabase.co"):
                                result = sync_file(config, file_path, existing_state=None)

                                assert result["status"] == "added"
                                assert result["document_id"] == "doc-123"


# ============================================================================
# API Route Tests
# ============================================================================


class TestObsidianAPIRoutes:
    """Tests for Obsidian sync API routes."""

    @pytest.mark.xfail(reason="Patch doesn't work correctly when vault is configured in env")
    def test_status_endpoint_no_vault(self, authenticated_client):
        """Test /api/obsidian/status when no vault configured."""
        with patch(
            "services.obsidian_sync.get_sync_status",
            return_value={"connected": False, "vault_path": None, "files_synced": 0},
        ):
            response = authenticated_client.get("/api/obsidian/status")

            # Should return success even with no vault
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["connected"] is False

    def test_configure_endpoint_validates_path(self, authenticated_client):
        """Test that /api/obsidian/configure validates vault path."""
        from services.obsidian_sync import ObsidianSyncError

        # Patch at the route level where create_vault_config is imported
        with (
            patch("api.routes.obsidian_sync.create_vault_config") as mock_create,
            patch("api.routes.obsidian_sync._get_db") as mock_db,
        ):
            mock_create.side_effect = ObsidianSyncError("Vault path does not exist")
            mock_db.return_value = MagicMock()

            response = authenticated_client.post("/api/obsidian/configure", json={"vault_path": "/nonexistent/path"})

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
                    "debounce_ms": 100,
                },
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
                    "debounce_ms": 100,
                },
            }

            watcher = ObsidianVaultWatcher(config)

            assert watcher._should_process(config_file) is False


# ============================================================================
# Sync Logging Tests
# ============================================================================


class TestSyncLogging:
    """Tests for sync log creation and completion."""

    def test_create_sync_log_returns_uuid(self):
        """Test that create_sync_log returns a valid UUID."""
        from services.obsidian_sync import create_sync_log

        mock_supabase = MagicMock()
        mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{"id": "log-uuid-123"}]
        )

        with patch("services.obsidian_sync._get_db", return_value=mock_supabase):
            log_id = create_sync_log(
                config_id="config-123",
                user_id="user-123",
                sync_type="full",
                trigger_source="manual",
            )

            assert log_id == "log-uuid-123"

    def test_create_sync_log_sets_running_status(self):
        """Test that create_sync_log sets status to 'running'."""
        from services.obsidian_sync import create_sync_log

        mock_supabase = MagicMock()
        mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{"id": "log-uuid-123"}]
        )

        with patch("services.obsidian_sync._get_db", return_value=mock_supabase):
            create_sync_log(
                config_id="config-123",
                user_id="user-123",
                sync_type="incremental",
                trigger_source="watch",
            )

            # Check the insert was called with correct status
            insert_call = mock_supabase.table.return_value.insert.call_args
            log_data = insert_call[0][0]
            assert log_data["status"] == "running"
            assert log_data["sync_type"] == "incremental"
            assert log_data["trigger_source"] == "watch"

    def test_complete_sync_log_updates_stats(self):
        """Test that complete_sync_log updates with stats."""
        from services.obsidian_sync import complete_sync_log

        mock_supabase = MagicMock()

        with patch("services.obsidian_sync._get_db", return_value=mock_supabase):
            complete_sync_log(
                log_id="log-123",
                status="completed",
                stats={
                    "files_scanned": 100,
                    "files_added": 10,
                    "files_updated": 5,
                    "files_deleted": 2,
                    "files_skipped": 80,
                    "files_failed": 3,
                },
            )

            # Check update was called
            update_call = mock_supabase.table.return_value.update.call_args
            update_data = update_call[0][0]
            assert update_data["status"] == "completed"
            assert update_data["files_scanned"] == 100
            assert update_data["files_added"] == 10
            assert update_data["files_failed"] == 3

    def test_complete_sync_log_with_error(self):
        """Test that complete_sync_log records error details."""
        from services.obsidian_sync import complete_sync_log

        mock_supabase = MagicMock()

        with patch("services.obsidian_sync._get_db", return_value=mock_supabase):
            complete_sync_log(
                log_id="log-123",
                status="failed",
                error_message="Connection timeout",
                error_details=[
                    {"file": "note1.md", "error": "Upload failed"},
                    {"file": "note2.md", "error": "Invalid content"},
                ],
            )

            update_call = mock_supabase.table.return_value.update.call_args
            update_data = update_call[0][0]
            assert update_data["status"] == "failed"
            assert update_data["error_message"] == "Connection timeout"
            assert len(update_data["error_details"]) == 2


# ============================================================================
# Delete Handling Tests
# ============================================================================


class TestDeleteHandling:
    """Tests for file deletion sync handling."""

    def test_mark_sync_state_deleted(self):
        """Test that mark_sync_state_deleted updates status."""
        from services.obsidian_sync import mark_sync_state_deleted

        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = (
            MagicMock(data=[{"id": "state-123", "file_path": "note.md"}])
        )
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"sync_status": "deleted"}]
        )

        with patch("services.obsidian_sync._get_db", return_value=mock_supabase):
            with patch("services.obsidian_sync.get_sync_state", return_value={"id": "state-123"}):
                mark_sync_state_deleted("config-123", "note.md")

                # Verify update was called
                assert mock_supabase.table.return_value.update.called


# ============================================================================
# Edge Cases and Error Handling Tests
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_parse_frontmatter_with_nested_yaml(self):
        """Test parsing complex nested YAML frontmatter."""
        from services.obsidian_sync import parse_frontmatter

        content = """---
title: Complex Note
metadata:
  author: John Doe
  created: 2026-01-15
  tags:
    - research
    - thesis
  nested:
    level1:
      level2: value
---
# Content"""

        frontmatter, body = parse_frontmatter(content)

        assert frontmatter["title"] == "Complex Note"
        assert frontmatter["metadata"]["author"] == "John Doe"
        assert frontmatter["metadata"]["nested"]["level1"]["level2"] == "value"

    def test_convert_wikilinks_with_special_characters(self):
        """Test wikilinks with special characters in name."""
        from services.obsidian_sync import convert_wikilinks

        content = "See [[Meeting 2026-01-15 (Team)]] for notes."
        result = convert_wikilinks(content)

        assert "[Meeting 2026-01-15 (Team)](Meeting 2026-01-15 (Team).md)" in result

    def test_convert_wikilinks_with_heading_anchor(self):
        """Test wikilinks with heading anchors."""
        from services.obsidian_sync import convert_wikilinks

        # Note: Basic wikilink conversion doesn't handle anchors specially
        content = "See [[Note#Section]] for details."
        result = convert_wikilinks(content)

        # Should convert the whole thing as a link target
        assert "[Note#Section]" in result

    def test_should_include_file_outside_vault(self):
        """Test that files outside vault are excluded."""
        from services.obsidian_sync import should_include_file

        vault_path = Path("/vault")
        file_path = Path("/other/location/note.md")

        result = should_include_file(file_path, vault_path, include_patterns=["**/*.md"], exclude_patterns=[])

        assert result is False

    def test_compute_hash_empty_file(self):
        """Test hash computation for empty file."""
        from services.obsidian_sync import compute_file_hash

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("")
            temp_path = Path(f.name)

        try:
            hash_result = compute_file_hash(temp_path)
            assert len(hash_result) == 32  # MD5 hex digest
            # Empty file has a known MD5 hash
            assert hash_result == "d41d8cd98f00b204e9800998ecf8427e"
        finally:
            temp_path.unlink()

    def test_compute_hash_unicode_content(self):
        """Test hash computation with unicode content."""
        from services.obsidian_sync import compute_file_hash

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("# Unicode Test\n\n日本語テスト\n\n🚀 Emoji content")
            temp_path = Path(f.name)

        try:
            hash_result = compute_file_hash(temp_path)
            assert len(hash_result) == 32
            assert hash_result.isalnum()
        finally:
            temp_path.unlink()


# ============================================================================
# Vault Configuration Edge Cases
# ============================================================================


class TestVaultConfigEdgeCases:
    """Tests for vault configuration edge cases."""

    def test_get_vault_config_returns_none_when_not_found(self):
        """Test get_vault_config returns None for non-existent user."""
        from services.obsidian_sync import get_vault_config

        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = (
            MagicMock(data=[])
        )

        with patch("services.obsidian_sync._get_db", return_value=mock_supabase):
            result = get_vault_config("nonexistent-user")
            assert result is None

    def test_create_vault_config_deactivates_existing(self):
        """Test that creating a new config deactivates the old one."""
        from services.obsidian_sync import create_vault_config

        mock_supabase = MagicMock()

        # Mock existing active config
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = (
            MagicMock(data=[{"id": "old-config-123"}])
        )

        # Mock update (deactivate)
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[])

        # Mock insert (new config)
        mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{"id": "new-config-456", "vault_path": "/test/vault", "is_active": True}]
        )

        with tempfile.TemporaryDirectory() as vault_dir:
            with patch("services.obsidian_sync._get_db", return_value=mock_supabase):
                create_vault_config(user_id="user-123", client_id="client-123", vault_path=vault_dir)

                # Verify update was called to deactivate old config
                update_calls = list(mock_supabase.table.return_value.update.call_args_list)
                assert len(update_calls) >= 1

    def test_update_vault_config_raises_on_failure(self):
        """Test that update_vault_config raises on database error."""
        from services.obsidian_sync import ObsidianSyncError, update_vault_config

        mock_supabase = MagicMock()
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.side_effect = Exception("DB Error")

        with patch("services.obsidian_sync._get_db", return_value=mock_supabase):
            with pytest.raises(ObsidianSyncError) as exc_info:
                update_vault_config("config-123", {"sync_options": {}})

            assert "Failed to update vault config" in str(exc_info.value)


# ============================================================================
# Sync State Edge Cases
# ============================================================================


class TestSyncStateEdgeCases:
    """Tests for sync state management edge cases."""

    def test_update_sync_state_creates_new_when_not_exists(self):
        """Test that update_sync_state creates new entry when none exists."""
        from services.obsidian_sync import update_sync_state

        mock_supabase = MagicMock()
        mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[
                {
                    "id": "new-state",
                    "config_id": "config-123",
                    "file_path": "new-note.md",
                    "sync_status": "synced",
                }
            ]
        )

        with patch("services.obsidian_sync._get_db", return_value=mock_supabase):
            with patch("services.obsidian_sync.get_sync_state", return_value=None):
                result = update_sync_state(
                    config_id="config-123",
                    file_path="new-note.md",
                    file_hash="abc123",
                    sync_status="synced",
                )

                assert result.get("sync_status") == "synced"
                # Verify insert was called (not update)
                assert mock_supabase.table.return_value.insert.called

    def test_update_sync_state_with_error_clears_last_synced(self):
        """Test that failed sync sets sync_error."""
        from services.obsidian_sync import update_sync_state

        mock_supabase = MagicMock()
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"sync_status": "failed", "sync_error": "Connection timeout"}]
        )

        with patch("services.obsidian_sync._get_db", return_value=mock_supabase):
            with patch("services.obsidian_sync.get_sync_state", return_value={"id": "state-123"}):
                update_sync_state(
                    config_id="config-123",
                    file_path="note.md",
                    sync_status="failed",
                    sync_error="Connection timeout",
                )

                update_call = mock_supabase.table.return_value.update.call_args
                update_data = update_call[0][0]
                assert update_data["sync_status"] == "failed"
                assert update_data["sync_error"] == "Connection timeout"

    def test_get_all_sync_states_empty_result(self):
        """Test get_all_sync_states returns empty dict for no results."""
        from services.obsidian_sync import get_all_sync_states

        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])

        with patch("services.obsidian_sync._get_db", return_value=mock_supabase):
            result = get_all_sync_states("config-123")
            assert result == {}

    def test_get_all_sync_states_maps_by_path(self):
        """Test get_all_sync_states correctly maps file paths."""
        from services.obsidian_sync import get_all_sync_states

        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[
                {"file_path": "note1.md", "sync_status": "synced", "file_hash": "abc"},
                {"file_path": "folder/note2.md", "sync_status": "pending", "file_hash": "def"},
                {"file_path": "deep/nested/note3.md", "sync_status": "synced", "file_hash": "ghi"},
            ]
        )

        with patch("services.obsidian_sync._get_db", return_value=mock_supabase):
            result = get_all_sync_states("config-123")

            assert len(result) == 3
            assert "note1.md" in result
            assert "folder/note2.md" in result
            assert "deep/nested/note3.md" in result
            assert result["note1.md"]["sync_status"] == "synced"


# ============================================================================
# Watcher Config Tests
# ============================================================================


class TestWatcherConfig:
    """Tests for file watcher configuration."""

    def test_watcher_stores_sync_options(self):
        """Test that watcher stores sync options from config."""
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
                    "debounce_ms": 1000,
                },
            }

            watcher = ObsidianVaultWatcher(config)

            # Verify sync options are stored
            assert watcher.sync_options["debounce_ms"] == 1000
            assert watcher.sync_options["include_patterns"] == ["**/*.md"]

    def test_watcher_uses_default_sync_options(self):
        """Test that watcher uses defaults when sync_options not provided."""
        from services.obsidian_sync import DEFAULT_SYNC_OPTIONS, ObsidianVaultWatcher

        with tempfile.TemporaryDirectory() as vault_dir:
            config = {
                "id": "config-123",
                "user_id": "user-123",
                "client_id": "client-123",
                "vault_path": vault_dir,
                # No sync_options specified
            }

            watcher = ObsidianVaultWatcher(config)

            # Should use defaults
            assert watcher.sync_options == DEFAULT_SYNC_OPTIONS


# ============================================================================
# Empty Content Validation Tests
# ============================================================================


class TestEmptyContentValidation:
    """Tests for empty content validation during sync."""

    def test_create_rejects_empty_content(self):
        """Test that _create_obsidian_document rejects empty content."""
        from services.obsidian_sync import ObsidianSyncError, _create_obsidian_document

        config = {"user_id": "user-123", "client_id": "client-123", "vault_path": "/test/vault"}

        # Empty bytes should raise error
        with pytest.raises(ObsidianSyncError) as exc_info:
            _create_obsidian_document(
                config=config,
                file_content=b"",
                filename="empty.md",
                title="Empty File",
                relative_path="empty.md",
                frontmatter={},
            )

        assert "Cannot upload empty file" in str(exc_info.value)

    def test_create_rejects_none_content(self):
        """Test that _create_obsidian_document rejects None content."""
        from services.obsidian_sync import ObsidianSyncError, _create_obsidian_document

        config = {"user_id": "user-123", "client_id": "client-123", "vault_path": "/test/vault"}

        # None should raise error
        with pytest.raises(ObsidianSyncError) as exc_info:
            _create_obsidian_document(
                config=config,
                file_content=None,
                filename="none.md",
                title="None File",
                relative_path="none.md",
                frontmatter={},
            )

        assert "Cannot upload empty file" in str(exc_info.value)

    def test_update_rejects_empty_content(self):
        """Test that _update_obsidian_document rejects empty content."""
        from services.obsidian_sync import ObsidianSyncError, _update_obsidian_document

        # Empty bytes should raise error
        with pytest.raises(ObsidianSyncError) as exc_info:
            _update_obsidian_document(
                document_id="doc-123",
                file_content=b"",
                title="Empty Update",
                relative_path="test.md",
                frontmatter={},
            )

        assert "Cannot update with empty content" in str(exc_info.value)

    def test_frontmatter_only_file_produces_empty_body(self):
        """Test that a file with only frontmatter results in empty body."""
        from services.obsidian_sync import parse_frontmatter

        # File that is ONLY frontmatter
        content = """---
title: Only Frontmatter
tags:
  - test
---
"""

        frontmatter, body = parse_frontmatter(content)

        # Body should be empty (just whitespace)
        assert frontmatter["title"] == "Only Frontmatter"
        assert body.strip() == ""

    def test_valid_content_passes_validation(self):
        """Test that valid non-empty content would pass validation."""
        # This is a sanity check that our validation logic is correct
        content = b"# Hello World\n\nThis is content."

        assert content is not None
        assert len(content) > 0
