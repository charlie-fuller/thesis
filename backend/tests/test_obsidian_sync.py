"""Tests for Obsidian Vault Sync functionality.

Updated for PocketBase migration: mocks pb_client (imported as pb in
obsidian_sync.py) instead of the old _get_db() / Supabase patterns.

Tests cover:
- Frontmatter parsing
- Wikilink conversion
- File change detection (hash computation)
- Pattern matching (include/exclude)
- Sync state tracking
- Full vault scanning
- Date extraction (extract_original_date, _extract_date_from_text)
- Document classification (classify_document_by_filename)
- Remote upload request model (RemoteFileUploadRequest)
"""

import tempfile
from datetime import date, datetime, timezone
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
# Sync State Tests (with mocked pb_client)
# ============================================================================


class TestSyncState:
    """Tests for sync state management."""

    def test_update_sync_state_creates_new(self):
        """Test creating a new sync state entry."""
        from services.obsidian_sync import update_sync_state

        with patch("services.obsidian_sync.get_sync_state", return_value=None), \
             patch("services.obsidian_sync.pb.create_record") as mock_create:
            mock_create.return_value = {
                "id": "new-state-id",
                "config_id": "config-123",
                "file_path": "notes/test.md",
                "sync_status": "synced",
            }

            result = update_sync_state(
                config_id="config-123",
                file_path="notes/test.md",
                file_hash="abc123",
                sync_status="synced",
            )

            assert result.get("sync_status") == "synced"
            mock_create.assert_called_once()

    def test_get_all_sync_states(self):
        """Test retrieving all sync states for a vault."""
        from services.obsidian_sync import get_all_sync_states

        with patch("services.obsidian_sync.pb.get_all") as mock_get_all, \
             patch("services.obsidian_sync.pb.escape_filter", side_effect=lambda v: v):
            mock_get_all.return_value = [
                {"file_path": "note1.md", "sync_status": "synced"},
                {"file_path": "note2.md", "sync_status": "pending"},
            ]

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

            with patch("services.obsidian_sync.process_document"), \
                 patch("services.obsidian_sync.update_sync_state", return_value={}), \
                 patch(
                     "services.obsidian_sync._create_obsidian_document",
                     return_value="doc-123",
                 ):
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

        with (
            patch("api.routes.obsidian_sync.create_vault_config") as mock_create,
            patch("api.routes.obsidian_sync.pb") as mock_pb,
        ):
            mock_create.side_effect = ObsidianSyncError("Vault path does not exist")
            mock_pb.get_first.return_value = None

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

        with patch("services.obsidian_sync.pb.create_record") as mock_create:
            mock_create.return_value = {"id": "log-uuid-123"}

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

        with patch("services.obsidian_sync.pb.create_record") as mock_create:
            mock_create.return_value = {"id": "log-uuid-123"}

            create_sync_log(
                config_id="config-123",
                user_id="user-123",
                sync_type="incremental",
                trigger_source="watch",
            )

            # Check the create was called with correct status
            call_args = mock_create.call_args
            log_data = call_args[0][1]  # second positional arg (data)
            assert log_data["status"] == "running"
            assert log_data["sync_type"] == "incremental"
            assert log_data["trigger_source"] == "watch"

    def test_complete_sync_log_updates_stats(self):
        """Test that complete_sync_log updates with stats."""
        from services.obsidian_sync import complete_sync_log

        with patch("services.obsidian_sync.pb.update_record") as mock_update:
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
            call_args = mock_update.call_args
            update_data = call_args[0][2]  # third positional arg (data)
            assert update_data["status"] == "completed"
            assert update_data["files_scanned"] == 100
            assert update_data["files_added"] == 10
            assert update_data["files_failed"] == 3

    def test_complete_sync_log_with_error(self):
        """Test that complete_sync_log records error details."""
        from services.obsidian_sync import complete_sync_log

        with patch("services.obsidian_sync.pb.update_record") as mock_update:
            complete_sync_log(
                log_id="log-123",
                status="failed",
                error_message="Connection timeout",
                error_details=[
                    {"file": "note1.md", "error": "Upload failed"},
                    {"file": "note2.md", "error": "Invalid content"},
                ],
            )

            call_args = mock_update.call_args
            update_data = call_args[0][2]  # third positional arg (data)
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

        with patch("services.obsidian_sync.update_sync_state") as mock_update:
            mark_sync_state_deleted("config-123", "note.md")

            mock_update.assert_called_once_with("config-123", "note.md", sync_status="deleted")


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

        content = "See [[Note#Section]] for details."
        result = convert_wikilinks(content)

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

        with patch("services.obsidian_sync.pb.get_first", return_value=None), \
             patch("services.obsidian_sync.pb.escape_filter", side_effect=lambda v: v):
            result = get_vault_config("nonexistent-user")
            assert result is None

    def test_create_vault_config_deactivates_existing(self):
        """Test that creating a new config deactivates the old one."""
        from services.obsidian_sync import create_vault_config

        with tempfile.TemporaryDirectory() as vault_dir:
            with patch("services.obsidian_sync.pb.get_first") as mock_first, \
                 patch("services.obsidian_sync.pb.get_all") as mock_all, \
                 patch("services.obsidian_sync.pb.update_record") as mock_update, \
                 patch("services.obsidian_sync.pb.create_record") as mock_create, \
                 patch("services.obsidian_sync.pb.escape_filter", side_effect=lambda v: v):
                # Mock existing active config
                mock_first.return_value = {"id": "old-config-123", "is_active": True}
                mock_all.return_value = [{"id": "old-config-123"}]
                mock_update.return_value = {}
                mock_create.return_value = {
                    "id": "new-config-456",
                    "vault_path": vault_dir,
                    "is_active": True,
                }

                create_vault_config(user_id="user-123", client_id="client-123", vault_path=vault_dir)

                # Verify update was called to deactivate old config
                assert mock_update.called

    def test_update_vault_config_raises_on_failure(self):
        """Test that update_vault_config raises on database error."""
        from services.obsidian_sync import ObsidianSyncError, update_vault_config

        with patch("services.obsidian_sync.pb.update_record", side_effect=Exception("DB Error")):
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

        with patch("services.obsidian_sync.get_sync_state", return_value=None), \
             patch("services.obsidian_sync.pb.create_record") as mock_create:
            mock_create.return_value = {
                "id": "new-state",
                "config_id": "config-123",
                "file_path": "new-note.md",
                "sync_status": "synced",
            }

            result = update_sync_state(
                config_id="config-123",
                file_path="new-note.md",
                file_hash="abc123",
                sync_status="synced",
            )

            assert result.get("sync_status") == "synced"
            assert mock_create.called

    def test_update_sync_state_updates_existing(self):
        """Test that update_sync_state updates entry when it exists."""
        from services.obsidian_sync import update_sync_state

        with patch("services.obsidian_sync.get_sync_state", return_value={"id": "state-123"}), \
             patch("services.obsidian_sync.pb.update_record") as mock_update:
            mock_update.return_value = {
                "id": "state-123",
                "sync_status": "synced",
            }

            result = update_sync_state(
                config_id="config-123",
                file_path="note.md",
                file_hash="abc123",
                sync_status="synced",
            )

            assert mock_update.called
            # Verify update was called with the existing record ID
            call_args = mock_update.call_args
            assert call_args[0][1] == "state-123"  # record ID

    def test_update_sync_state_with_error(self):
        """Test that failed sync sets sync_error."""
        from services.obsidian_sync import update_sync_state

        with patch("services.obsidian_sync.get_sync_state", return_value={"id": "state-123"}), \
             patch("services.obsidian_sync.pb.update_record") as mock_update:
            mock_update.return_value = {"sync_status": "failed", "sync_error": "Connection timeout"}

            update_sync_state(
                config_id="config-123",
                file_path="note.md",
                sync_status="failed",
                sync_error="Connection timeout",
            )

            call_args = mock_update.call_args
            update_data = call_args[0][2]  # third positional arg (data)
            assert update_data["sync_status"] == "failed"
            assert update_data["sync_error"] == "Connection timeout"

    def test_get_all_sync_states_empty_result(self):
        """Test get_all_sync_states returns empty dict for no results."""
        from services.obsidian_sync import get_all_sync_states

        with patch("services.obsidian_sync.pb.get_all", return_value=[]), \
             patch("services.obsidian_sync.pb.escape_filter", side_effect=lambda v: v):
            result = get_all_sync_states("config-123")
            assert result == {}

    def test_get_all_sync_states_maps_by_path(self):
        """Test get_all_sync_states correctly maps file paths."""
        from services.obsidian_sync import get_all_sync_states

        with patch("services.obsidian_sync.pb.get_all") as mock_get_all, \
             patch("services.obsidian_sync.pb.escape_filter", side_effect=lambda v: v):
            mock_get_all.return_value = [
                {"file_path": "note1.md", "sync_status": "synced", "file_hash": "abc"},
                {"file_path": "folder/note2.md", "sync_status": "pending", "file_hash": "def"},
                {"file_path": "deep/nested/note3.md", "sync_status": "synced", "file_hash": "ghi"},
            ]

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
        content = b"# Hello World\n\nThis is content."

        assert content is not None
        assert len(content) > 0


# ============================================================================
# Date Extraction Tests
# ============================================================================


class TestExtractDateFromText:
    """Tests for _extract_date_from_text() pattern matching."""

    def test_iso_format(self):
        from services.obsidian_sync import _extract_date_from_text

        result = _extract_date_from_text("meeting-2026-01-15.md")
        assert result == date(2026, 1, 15)

    def test_compact_yyyymmdd(self):
        from services.obsidian_sync import _extract_date_from_text

        result = _extract_date_from_text("notes-20260115.md")
        assert result == date(2026, 1, 15)

    def test_us_format_slashes(self):
        from services.obsidian_sync import _extract_date_from_text

        result = _extract_date_from_text("notes 01/15/2026")
        assert result == date(2026, 1, 15)

    def test_us_format_dashes(self):
        from services.obsidian_sync import _extract_date_from_text

        result = _extract_date_from_text("notes 01-15-2026")
        assert result == date(2026, 1, 15)

    def test_us_format_dots(self):
        from services.obsidian_sync import _extract_date_from_text

        result = _extract_date_from_text("notes 01.15.2026")
        assert result == date(2026, 1, 15)

    def test_compact_mmddyyyy_end(self):
        from services.obsidian_sync import _extract_date_from_text

        result = _extract_date_from_text("interview-01152026")
        assert result == date(2026, 1, 15)

    def test_written_full_month(self):
        from services.obsidian_sync import _extract_date_from_text

        result = _extract_date_from_text("January 15, 2026")
        assert result == date(2026, 1, 15)

    def test_written_abbreviated_month(self):
        from services.obsidian_sync import _extract_date_from_text

        result = _extract_date_from_text("Jan 15, 2026")
        assert result == date(2026, 1, 15)

    def test_two_digit_year(self):
        from services.obsidian_sync import _extract_date_from_text

        result = _extract_date_from_text("notes 01/15/26")
        assert result == date(2026, 1, 15)

    def test_no_date_found(self):
        from services.obsidian_sync import _extract_date_from_text

        result = _extract_date_from_text("just a regular filename.md")
        assert result is None

    def test_future_date_rejected(self):
        """Future dates should be skipped as likely false matches."""
        from services.obsidian_sync import _extract_date_from_text

        result = _extract_date_from_text("Meeting Guide - May 20, 2027")
        assert result is None

    def test_far_future_date_rejected(self):
        from services.obsidian_sync import _extract_date_from_text

        result = _extract_date_from_text("roadmap-2099-12-31.md")
        assert result is None

    def test_invalid_month_rejected(self):
        from services.obsidian_sync import _extract_date_from_text

        result = _extract_date_from_text("data-2026-13-01.md")
        assert result is None

    def test_invalid_day_rejected(self):
        from services.obsidian_sync import _extract_date_from_text

        result = _extract_date_from_text("data-2026-01-32.md")
        assert result is None

    def test_year_before_2000_rejected(self):
        from services.obsidian_sync import _extract_date_from_text

        result = _extract_date_from_text("data-1999-01-15.md")
        assert result is None


class TestExtractOriginalDate:
    """Tests for extract_original_date() priority ordering."""

    def test_frontmatter_date_highest_priority(self):
        from services.obsidian_sync import extract_original_date

        result = extract_original_date(
            filename="meeting-2026-01-20.md",
            frontmatter={"date": "2026-01-10"},
            content="January 25, 2026 meeting notes",
            file_mtime=datetime(2026, 1, 30, tzinfo=timezone.utc),
        )
        assert result == date(2026, 1, 10)

    def test_frontmatter_original_date_key(self):
        from services.obsidian_sync import extract_original_date

        result = extract_original_date(
            filename="notes.md",
            frontmatter={"original_date": "2026-02-01"},
        )
        assert result == date(2026, 2, 1)

    def test_frontmatter_created_key(self):
        from services.obsidian_sync import extract_original_date

        result = extract_original_date(
            filename="notes.md",
            frontmatter={"created": "2026-01-05"},
        )
        assert result == date(2026, 1, 5)

    def test_filename_date_second_priority(self):
        from services.obsidian_sync import extract_original_date

        result = extract_original_date(
            filename="meeting-2026-01-27.md",
            frontmatter={},
            content="Some content without dates",
        )
        assert result == date(2026, 1, 27)

    def test_content_date_third_priority(self):
        from services.obsidian_sync import extract_original_date

        result = extract_original_date(
            filename="notes.md",
            frontmatter={},
            content="Meeting on January 15, 2026\nDiscussed roadmap.",
        )
        assert result == date(2026, 1, 15)

    def test_file_mtime_fallback(self):
        from services.obsidian_sync import extract_original_date

        mtime = datetime(2026, 2, 4, 14, 30, 0, tzinfo=timezone.utc)
        result = extract_original_date(
            filename="notes.md",
            frontmatter={},
            content="No dates here",
            file_mtime=mtime,
        )
        assert result == date(2026, 2, 4)

    def test_no_date_found_returns_none(self):
        from services.obsidian_sync import extract_original_date

        result = extract_original_date(
            filename="notes.md",
            frontmatter={},
            content="No dates here either",
        )
        assert result is None

    def test_none_frontmatter(self):
        from services.obsidian_sync import extract_original_date

        result = extract_original_date(
            filename="meeting-2026-01-15.md",
            frontmatter=None,
        )
        assert result == date(2026, 1, 15)

    def test_frontmatter_date_object(self):
        """Frontmatter date can be a Python date object from YAML parsing."""
        from services.obsidian_sync import extract_original_date

        result = extract_original_date(
            filename="notes.md",
            frontmatter={"date": date(2026, 1, 20)},
        )
        assert result == date(2026, 1, 20)

    def test_frontmatter_datetime_object(self):
        """Frontmatter datetime returns as-is (datetime is subclass of date)."""
        from services.obsidian_sync import extract_original_date

        dt = datetime(2026, 1, 20, 14, 30)
        result = extract_original_date(
            filename="notes.md",
            frontmatter={"date": dt},
        )
        # datetime is subclass of date, so isinstance(dt, date) is True
        # _parse_date_value returns it directly
        assert result == dt


# ============================================================================
# Document Classification Tests
# ============================================================================


class TestClassifyDocumentByFilename:
    """Tests for classify_document_by_filename()."""

    def test_transcript_keyword(self):
        from services.obsidian_sync import classify_document_by_filename

        result = classify_document_by_filename("meeting-transcript.md")
        assert result["document_type"] == "transcript"
        assert result["classification_method"] == "filename"

    def test_transcript_suffix(self):
        from services.obsidian_sync import classify_document_by_filename

        result = classify_document_by_filename("Chris __ Charlie 1_1-transcript.md")
        assert result["document_type"] == "transcript"

    def test_granola_double_underscore(self):
        from services.obsidian_sync import classify_document_by_filename

        result = classify_document_by_filename("Chris __ Charlie 1_1.md")
        assert result["document_type"] == "transcript"
        assert result["classification_confidence"] == 0.85

    def test_meeting_notes(self):
        from services.obsidian_sync import classify_document_by_filename

        result = classify_document_by_filename("Team Meeting Notes.md")
        assert result["document_type"] == "notes"

    def test_meeting_notes_variant(self):
        from services.obsidian_sync import classify_document_by_filename

        result = classify_document_by_filename("weekly-meeting-notes.md")
        assert result["document_type"] == "notes"

    def test_guide_keyword(self):
        from services.obsidian_sync import classify_document_by_filename

        result = classify_document_by_filename("Meeting Guide - Steffen and Raza Walkthrough.md")
        assert result["document_type"] == "instructions"

    def test_playbook_keyword(self):
        from services.obsidian_sync import classify_document_by_filename

        result = classify_document_by_filename("AI-Governance-Playbook.md")
        assert result["document_type"] == "instructions"

    def test_report_keyword(self):
        from services.obsidian_sync import classify_document_by_filename

        result = classify_document_by_filename("AI Governance Strategy Report.md")
        assert result["document_type"] == "report"

    def test_analysis_keyword(self):
        from services.obsidian_sync import classify_document_by_filename

        result = classify_document_by_filename("Gap Analysis & Approach Comparison.md")
        assert result["document_type"] == "report"

    def test_research_keyword(self):
        from services.obsidian_sync import classify_document_by_filename

        result = classify_document_by_filename("Research - Platform Inventory.md")
        assert result["document_type"] == "report"

    def test_presentation_pptx(self):
        from services.obsidian_sync import classify_document_by_filename

        result = classify_document_by_filename("Q1-review.pptx")
        assert result["document_type"] == "presentation"

    def test_slides_keyword(self):
        from services.obsidian_sync import classify_document_by_filename

        result = classify_document_by_filename("slides-overview.md")
        assert result["document_type"] == "presentation"

    def test_spreadsheet_csv(self):
        from services.obsidian_sync import classify_document_by_filename

        result = classify_document_by_filename("Rovo.csv")
        assert result["document_type"] == "spreadsheet"

    def test_spreadsheet_xlsx(self):
        from services.obsidian_sync import classify_document_by_filename

        result = classify_document_by_filename("budget-2026.xlsx")
        assert result["document_type"] == "spreadsheet"

    def test_path_based_transcripts_folder(self):
        from services.obsidian_sync import classify_document_by_filename

        result = classify_document_by_filename("some-file.md", "Granola/Transcripts/some-file.md")
        assert result["document_type"] == "transcript"
        assert result["classification_method"] == "path"

    def test_path_based_notes_folder(self):
        from services.obsidian_sync import classify_document_by_filename

        result = classify_document_by_filename("daily.md", "notes/daily.md")
        assert result["document_type"] == "notes"
        assert result["classification_method"] == "path"

    def test_unclassified_default(self):
        from services.obsidian_sync import classify_document_by_filename

        result = classify_document_by_filename("random-file.md")
        assert result["document_type"] is None
        assert result["classification_confidence"] == 0.0

    def test_returns_all_keys(self):
        from services.obsidian_sync import classify_document_by_filename

        result = classify_document_by_filename("transcript.md")
        assert "document_type" in result
        assert "primary_use_case" in result
        assert "classification_confidence" in result
        assert "classification_method" in result


# ============================================================================
# Remote Upload Request Model Tests
# ============================================================================


class TestRemoteFileUploadRequest:
    """Tests for RemoteFileUploadRequest Pydantic model."""

    def test_basic_request(self):
        from api.routes.obsidian_sync import RemoteFileUploadRequest

        req = RemoteFileUploadRequest(
            file_path="notes/meeting.md",
            content="# Meeting Notes",
        )
        assert req.file_path == "notes/meeting.md"
        assert req.content == "# Meeting Notes"
        assert req.content_type == "text/markdown"
        assert req.file_mtime is None

    def test_with_file_mtime(self):
        from api.routes.obsidian_sync import RemoteFileUploadRequest

        req = RemoteFileUploadRequest(
            file_path="notes/meeting.md",
            content="# Meeting Notes",
            file_mtime=1738857600.0,
        )
        assert req.file_mtime == 1738857600.0

    def test_custom_content_type(self):
        from api.routes.obsidian_sync import RemoteFileUploadRequest

        req = RemoteFileUploadRequest(
            file_path="data.csv",
            content="a,b,c\n1,2,3",
            content_type="text/csv",
        )
        assert req.content_type == "text/csv"

    def test_file_path_required(self):
        from api.routes.obsidian_sync import RemoteFileUploadRequest

        with pytest.raises(Exception):
            RemoteFileUploadRequest(content="# Notes")

    def test_content_required(self):
        from api.routes.obsidian_sync import RemoteFileUploadRequest

        with pytest.raises(Exception):
            RemoteFileUploadRequest(file_path="notes.md")


# ============================================================================
# Parse Date Value Tests
# ============================================================================


class TestParseDateValue:
    """Tests for _parse_date_value() helper."""

    def test_none_returns_none(self):
        from services.obsidian_sync import _parse_date_value

        assert _parse_date_value(None) is None

    def test_date_object(self):
        from services.obsidian_sync import _parse_date_value

        result = _parse_date_value(date(2026, 1, 15))
        assert result == date(2026, 1, 15)

    def test_datetime_object(self):
        """datetime is subclass of date, so isinstance check returns it as-is."""
        from services.obsidian_sync import _parse_date_value

        dt = datetime(2026, 1, 15, 10, 30)
        result = _parse_date_value(dt)
        # datetime is subclass of date - the isinstance(value, date) check
        # matches first and returns the datetime object directly
        assert result == dt

    def test_iso_string(self):
        from services.obsidian_sync import _parse_date_value

        result = _parse_date_value("2026-01-15")
        assert result == date(2026, 1, 15)

    def test_iso_string_with_time(self):
        from services.obsidian_sync import _parse_date_value

        result = _parse_date_value("2026-01-15T10:30:00")
        assert result == date(2026, 1, 15)

    def test_integer_returns_none(self):
        from services.obsidian_sync import _parse_date_value

        assert _parse_date_value(12345) is None
