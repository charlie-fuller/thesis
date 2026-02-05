# Obsidian Vault Sync

Sync markdown files from a local Obsidian vault to the Thesis Knowledge Base.

## Overview

The Obsidian Vault Sync feature allows users to connect their local Obsidian vault and automatically sync `.md` files to the Thesis KB. Files are processed through the standard document pipeline (text extraction, chunking, Voyage AI embeddings) and become available for RAG retrieval by agents.

## Features

- **File Watching**: Monitor vault directory for create/modify/delete events
- **Incremental Sync**: Only sync changed files (using MD5 hash comparison)
- **Frontmatter Parsing**: Extract YAML metadata including `thesis-agents` for auto-tagging
- **Wikilink Conversion**: Convert `[[wikilinks]]` to standard markdown links
- **Pattern Matching**: Configurable include/exclude patterns
- **Debouncing**: 500ms debounce window for rapid file changes
- **Background Processing**: Syncs run asynchronously, embeddings processed in background
- **Move/Rename Detection**: Detects file moves by content hash matching, preserves document IDs
- **5-Phase Full Resync**: Structured filesystem mirroring (scan, identify, process, cleanup, report)

## Quick Start

### 1. Configure a Vault

```bash
curl -X POST http://localhost:8000/api/obsidian/configure \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "vault_path": "/Users/me/Documents/MyVault",
    "sync_options": {
      "auto_classify": true,
      "sync_on_delete": false
    }
  }'
```

### 2. Trigger Initial Sync

```bash
curl -X POST http://localhost:8000/api/obsidian/sync \
  -H "Authorization: Bearer $TOKEN"
```

### 3. Check Status

```bash
curl http://localhost:8000/api/obsidian/status \
  -H "Authorization: Bearer $TOKEN"
```

### 4. Enable Vault Watcher (Automatic)

The vault watcher starts automatically with the backend server when configured.

Add to your `.env` file:
```bash
VAULT_WATCHER_USER_ID=<your-user-uuid>
```

The watcher will:
- Start automatically when the backend server starts
- Perform an initial sync on startup
- Watch for file changes in real-time
- Stop gracefully when the server shuts down

#### Manual/Standalone Mode (Optional)

For standalone usage without the backend server:

```bash
cd backend
source venv/bin/activate
python -m scripts.vault_watcher --user-id <your-user-uuid>
```

Options:
- `--vault-path /path/to/vault` - Override vault path
- `--initial-sync` - Perform full sync before starting watcher
- `--verbose` - Enable debug logging

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/obsidian/configure` | Configure vault path and sync options |
| GET | `/api/obsidian/status` | Get connection status and sync stats |
| PATCH | `/api/obsidian/settings` | Update sync options |
| POST | `/api/obsidian/sync` | Trigger manual sync (runs in background) |
| POST | `/api/obsidian/sync/full` | Force full resync (clears state first) |
| DELETE | `/api/obsidian/disconnect` | Disconnect vault, optionally remove docs |
| GET | `/api/obsidian/sync-history` | Get recent sync operation logs |
| GET | `/api/obsidian/sync/recent` | Get recently synced files (sorted by last_synced_at) |
| GET | `/api/obsidian/files` | List synced files with status |
| GET | `/api/obsidian/files/pending` | Get pending/failed files |
| POST | `/api/obsidian/files/{path}/retry` | Retry syncing a failed file |

## Sync Options

Configure sync behavior via the `sync_options` object:

```json
{
  "include_patterns": ["**/*.md"],
  "exclude_patterns": [".obsidian/**", ".trash/**", ".git/**"],
  "auto_classify": true,
  "sync_on_delete": false,
  "parse_frontmatter": true,
  "convert_wikilinks": true,
  "max_file_size_mb": 10,
  "debounce_ms": 500
}
```

| Option | Default | Description |
|--------|---------|-------------|
| `include_patterns` | `["**/*.md"]` | Glob patterns for files to include |
| `exclude_patterns` | `[".obsidian/**", ".trash/**", ".git/**"]` | Glob patterns to exclude |
| `auto_classify` | `true` | Auto-classify documents for agent relevance |
| `sync_on_delete` | `false` | Delete KB documents when vault files are deleted |
| `parse_frontmatter` | `true` | Parse YAML frontmatter from files |
| `convert_wikilinks` | `true` | Convert `[[wikilinks]]` to markdown links |
| `max_file_size_mb` | `10` | Skip files larger than this |
| `debounce_ms` | `500` | Debounce window for file watcher |

## Frontmatter Support

The sync respects Obsidian YAML frontmatter:

```yaml
---
title: Project Alpha Analysis
tags:
  - project
  - analysis
thesis-agents:
  - atlas
  - capital
date: 2026-01-15
---
```

### Special Fields

- **`title`**: Used as document title (falls back to filename)
- **`thesis-agents`**: Array of agent names to auto-tag the document for

When `thesis-agents` is specified, the document is automatically linked to those agents in `agent_knowledge_base` with high confidence (1.0) and marked as user-confirmed.

## File Move/Rename Detection

When files are moved or renamed in the vault, the sync detects this and preserves the existing document ID rather than creating a duplicate.

**How It Works**:
1. During sync, new files (not yet in sync state) have their content hash computed
2. The hash is compared against recently deleted or missing files in the sync state
3. If a match is found, the existing document record is updated with the new path
4. All metadata (tags, agent assignments, embeddings, initiative links) is preserved

This works for:
- Simple renames (`notes.md` -> `meeting-notes.md`)
- Folder moves (`inbox/notes.md` -> `meetings/2026/notes.md`)
- Both incremental sync and "Check for Updates" operations

## Full Resync (5-Phase)

The full resync operation uses a structured 5-phase approach for reliability:

1. **Scan**: Discover all files in the vault matching include/exclude patterns
2. **Identify**: Categorize files as new, changed (hash mismatch), or unchanged
3. **Process**: Create or update documents for new/changed files
4. **Cleanup**: Remove orphaned documents (files no longer in vault)
5. **Report**: Return counts of added, updated, deleted, and failed files

This replaces the previous approach where full resync could race between clearing state and processing files.

## Wikilink Conversion

Obsidian wikilinks are converted to standard markdown:

| Obsidian | Converted |
|----------|-----------|
| `[[Note Name]]` | `[Note Name](Note Name.md)` |
| `[[Note\|Alias]]` | `[Alias](Note.md)` |
| `[[folder/Note]]` | `[Note](folder/Note.md)` |

## Database Tables

### obsidian_vault_configs

Stores user vault configurations:

- `vault_path` - Absolute path to the vault directory
- `vault_name` - Display name (derived from folder name)
- `is_active` - Whether sync is active
- `sync_options` - JSONB configuration object
- `last_sync_at` - Timestamp of last successful sync
- `last_error` - Most recent error message

### obsidian_sync_state

Tracks per-file sync state for incremental syncing:

- `file_path` - Relative path from vault root
- `document_id` - Link to synced document
- `file_hash` - MD5 hash for change detection
- `file_mtime` - File modification time
- `sync_status` - Current status (pending, synced, failed, deleted)
- `frontmatter` - Cached parsed frontmatter

### obsidian_sync_log

History of sync operations:

- `sync_type` - full, incremental, or watch
- `trigger_source` - manual, watcher, or scheduled
- `files_added/updated/deleted/failed` - Operation counts
- `error_details` - Array of per-file errors

## File Structure

```
/backend
  /services
    obsidian_sync.py           # Core sync service and file watcher
    vault_watcher_scheduler.py # Auto-start watcher with backend
  /api/routes
    obsidian_sync.py           # API endpoints
  /scripts
    vault_watcher.py           # CLI watcher script (standalone)

/database/migrations
  021_obsidian_sync.sql        # Database schema
```

## Troubleshooting

### Watcher not detecting changes

1. Check that watchdog is installed: `pip install watchdog`
2. Verify vault path exists and is readable
3. Check exclude patterns aren't too broad
4. Look at logs for permission errors

### Files not syncing

1. Check sync status: `GET /api/obsidian/status`
2. View pending files: `GET /api/obsidian/files/pending`
3. Check sync history: `GET /api/obsidian/sync-history`
4. Retry failed files: `POST /api/obsidian/files/{path}/retry`

### Large vault performance

For vaults with 1000+ files:
1. Increase `debounce_ms` to reduce API calls
2. Use more specific `include_patterns`
3. Run initial sync during off-hours
4. Consider excluding large attachments folders

## Dependencies

Added to `requirements.txt`:

```
watchdog>=4.0.0
pyyaml>=6.0.0
```
