"""
Obsidian Vault Sync Service

Handles syncing markdown files from local Obsidian vaults to the Thesis Knowledge Base.
Supports file watching, incremental sync, frontmatter parsing, and wikilink conversion.

Flow:
1. Configure vault path and sync options
2. Scan vault for .md files (respecting include/exclude patterns)
3. Parse frontmatter and convert wikilinks
4. Create/update document records in database
5. Save document content to Supabase storage
6. Trigger document processor for embedding generation
7. Track sync state for incremental updates
"""

import asyncio
import fnmatch
import hashlib
import os
import re
import uuid
from datetime import datetime, timezone, date
from pathlib import Path
import threading
import time as time_module
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import yaml

from database import get_supabase
from document_processor import process_document
from logger_config import get_logger

logger = get_logger(__name__)

# Get Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "")

# Get centralized Supabase client
supabase = get_supabase()

# Default sync options
DEFAULT_SYNC_OPTIONS = {
    "include_patterns": ["**/*.md"],
    "exclude_patterns": [".obsidian/**", ".trash/**", ".git/**", "node_modules/**"],
    "auto_classify": True,
    "sync_on_delete": False,
    "parse_frontmatter": True,
    "convert_wikilinks": True,
    "max_file_size_mb": 10,
    "debounce_ms": 500
}

# Frontmatter patterns
FRONTMATTER_PATTERN = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)

# Wikilink pattern: [[target|alias]] or [[target]]
WIKILINK_PATTERN = re.compile(r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]')

# Date patterns for extraction from filenames and content
# Order matters - more specific patterns should come first
DATE_PATTERNS = [
    # ISO format: 2024-01-15, 2024-1-5
    (re.compile(r'(\d{4})-(\d{1,2})-(\d{1,2})'), 'ymd'),
    # Compact MMDDYYYY at end: interview-11122025 = Nov 12, 2025
    (re.compile(r'(\d{2})(\d{2})(20\d{2})$'), 'mdy_compact_end'),
    # Compact YYYYMMDD: 20240115, 2024_01_15
    (re.compile(r'(20\d{2})[\-_]?(\d{2})[\-_]?(\d{2})'), 'ymd_compact'),
    # US format with slashes: 01/15/2024, 1/15/24
    (re.compile(r'(\d{1,2})/(\d{1,2})/(\d{2,4})'), 'mdy'),
    # US format with dashes: 01-15-2024, 1-15-24
    (re.compile(r'(\d{1,2})-(\d{1,2})-(\d{2,4})'), 'mdy'),
    # Month.Day: 1.15, 01.15 (assumes current year)
    (re.compile(r'\b(\d{1,2})\.(\d{1,2})\b'), 'md'),
    # Written: January 15, 2024 or Jan 15, 2024
    (re.compile(r'(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})(?:,?\s+(\d{4}))?', re.IGNORECASE), 'written'),
]

MONTH_MAP = {
    'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
    'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6, 'july': 7, 'jul': 7,
    'august': 8, 'aug': 8, 'september': 9, 'sep': 9, 'october': 10, 'oct': 10,
    'november': 11, 'nov': 11, 'december': 12, 'dec': 12
}


class ObsidianSyncError(Exception):
    """Raised when Obsidian sync operations fail"""
    pass


# ============================================================================
# Date Extraction
# ============================================================================

def extract_original_date(
    filename: str,
    frontmatter: Optional[Dict] = None,
    content: Optional[str] = None,
    file_mtime: Optional[datetime] = None
) -> Optional[date]:
    """
    Extract the original date from a document.

    Priority order:
    1. Frontmatter 'date' or 'original_date' field
    2. Date in filename
    3. Date in first 500 chars of content (for meeting headers)
    4. File modification time (fallback)

    Args:
        filename: The document filename
        frontmatter: Parsed frontmatter dict
        content: Document content (first 500 chars checked)
        file_mtime: File modification time from filesystem

    Returns:
        Extracted date or None if not found
    """
    # 1. Check frontmatter first
    if frontmatter:
        for key in ['date', 'original_date', 'created', 'meeting_date']:
            if key in frontmatter:
                parsed = _parse_date_value(frontmatter[key])
                if parsed:
                    return parsed

    # 2. Check filename
    parsed = _extract_date_from_text(filename)
    if parsed:
        return parsed

    # 3. Check content (first 500 chars - typically contains meeting headers)
    if content:
        parsed = _extract_date_from_text(content[:500])
        if parsed:
            return parsed

    # 4. Fall back to file modification time
    if file_mtime:
        if isinstance(file_mtime, datetime):
            return file_mtime.date()

    return None


def _parse_date_value(value: Any) -> Optional[date]:
    """Parse a date value from frontmatter (could be string, date, or datetime)."""
    if value is None:
        return None

    # Already a date object
    if isinstance(value, date):
        return value

    # Datetime object
    if isinstance(value, datetime):
        return value.date()

    # String - try parsing
    if isinstance(value, str):
        # Try ISO format first
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00')).date()
        except ValueError:
            pass

        # Try extracting from string
        return _extract_date_from_text(value)

    return None


def _extract_date_from_text(text: str) -> Optional[date]:
    """Extract a date from text using various patterns."""
    current_year = datetime.now().year

    for pattern, format_type in DATE_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue

        try:
            if format_type == 'ymd':
                year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
            elif format_type == 'ymd_compact':
                year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
            elif format_type == 'mdy_compact_end':
                # MMDDYYYY at end of string: 11122025 = Nov 12, 2025
                month, day, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
            elif format_type == 'mdy':
                month, day, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
                if year < 100:
                    year += 2000
            elif format_type == 'md':
                month, day = int(match.group(1)), int(match.group(2))
                year = current_year
            elif format_type == 'written':
                month = MONTH_MAP.get(match.group(1).lower())
                day = int(match.group(2))
                year = int(match.group(3)) if match.group(3) else current_year
            else:
                continue

            # Validate the date
            if 1 <= month <= 12 and 1 <= day <= 31 and 2000 <= year <= 2100:
                return date(year, month, day)

        except (ValueError, TypeError):
            continue

    return None


# ============================================================================
# Markdown Processing
# ============================================================================

def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """
    Parse YAML frontmatter from markdown content.

    Args:
        content: Raw markdown content

    Returns:
        Tuple of (frontmatter_dict, content_without_frontmatter)
    """
    match = FRONTMATTER_PATTERN.match(content)
    if not match:
        return {}, content

    try:
        frontmatter_yaml = match.group(1)
        frontmatter = yaml.safe_load(frontmatter_yaml) or {}
        content_without_frontmatter = content[match.end():]
        return frontmatter, content_without_frontmatter
    except yaml.YAMLError as e:
        logger.warning(f"Failed to parse frontmatter: {e}")
        return {}, content


def convert_wikilinks(content: str, vault_path: Optional[str] = None) -> str:
    """
    Convert Obsidian [[wikilinks]] to standard markdown links.

    Converts:
    - [[Note Name]] -> [Note Name](Note Name.md)
    - [[Note Name|Alias]] -> [Alias](Note Name.md)
    - [[folder/Note]] -> [Note](folder/Note.md)

    Args:
        content: Markdown content with wikilinks
        vault_path: Optional vault path for resolving relative links

    Returns:
        Content with wikilinks converted to markdown links
    """
    def replace_wikilink(match: re.Match) -> str:
        target = match.group(1).strip()
        alias = match.group(2)

        # Use alias if provided, otherwise use target name
        display_text = alias.strip() if alias else target.split('/')[-1]

        # Add .md extension if not present
        if not target.endswith('.md'):
            target = f"{target}.md"

        return f"[{display_text}]({target})"

    return WIKILINK_PATTERN.sub(replace_wikilink, content)


def compute_file_hash(file_path: Path) -> str:
    """
    Compute MD5 hash of file content for change detection.

    Args:
        file_path: Path to the file

    Returns:
        MD5 hash hex string
    """
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)
    return hasher.hexdigest()


# ============================================================================
# File Discovery
# ============================================================================

def should_include_file(
    file_path: Path,
    vault_path: Path,
    include_patterns: List[str],
    exclude_patterns: List[str]
) -> bool:
    """
    Check if a file should be included based on patterns.

    Args:
        file_path: Absolute path to the file
        vault_path: Absolute path to vault root
        include_patterns: Glob patterns for files to include
        exclude_patterns: Glob patterns for files to exclude

    Returns:
        True if file should be synced
    """
    # Get relative path from vault root
    try:
        relative_path = file_path.relative_to(vault_path)
    except ValueError:
        return False

    relative_str = str(relative_path)

    # Check exclusions first (higher priority)
    for pattern in exclude_patterns:
        if fnmatch.fnmatch(relative_str, pattern):
            return False

    # Check inclusions
    for pattern in include_patterns:
        if fnmatch.fnmatch(relative_str, pattern):
            return True

    return False


def scan_vault(
    vault_path: Path,
    include_patterns: List[str],
    exclude_patterns: List[str],
    max_file_size_mb: float = 10
) -> List[Path]:
    """
    Scan vault directory for markdown files to sync.

    Args:
        vault_path: Path to Obsidian vault
        include_patterns: Glob patterns for files to include
        exclude_patterns: Glob patterns for files to exclude
        max_file_size_mb: Maximum file size in MB

    Returns:
        List of file paths to sync
    """
    files_to_sync = []
    max_size_bytes = max_file_size_mb * 1024 * 1024

    for root, dirs, files in os.walk(vault_path):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]

        for filename in files:
            file_path = Path(root) / filename

            # Check file size
            try:
                if file_path.stat().st_size > max_size_bytes:
                    logger.debug(f"Skipping large file: {file_path}")
                    continue
            except OSError:
                continue

            # Check patterns
            if should_include_file(file_path, vault_path, include_patterns, exclude_patterns):
                files_to_sync.append(file_path)

    return sorted(files_to_sync)


# ============================================================================
# Vault Configuration
# ============================================================================

def get_vault_config(user_id: str) -> Optional[Dict]:
    """
    Get active vault configuration for a user.

    Args:
        user_id: UUID of the user

    Returns:
        Vault config record or None if not configured
    """
    try:
        result = supabase.table('obsidian_vault_configs') \
            .select('*') \
            .eq('user_id', user_id) \
            .eq('is_active', True) \
            .execute()

        return result.data[0] if result.data else None

    except Exception as e:
        logger.error(f"Failed to get vault config: {e}")
        return None


def get_vault_config_by_id(config_id: str) -> Optional[Dict]:
    """
    Get vault configuration by ID.

    Args:
        config_id: UUID of the config

    Returns:
        Vault config record or None if not found
    """
    try:
        result = supabase.table('obsidian_vault_configs') \
            .select('*') \
            .eq('id', config_id) \
            .execute()

        return result.data[0] if result.data else None

    except Exception as e:
        logger.error(f"Failed to get vault config: {e}")
        return None


def create_vault_config(
    user_id: str,
    client_id: str,
    vault_path: str,
    sync_options: Optional[Dict] = None
) -> Dict:
    """
    Create a new vault configuration.

    Args:
        user_id: UUID of the user
        client_id: UUID of the client
        vault_path: Absolute path to Obsidian vault
        sync_options: Optional sync options (merged with defaults)

    Returns:
        Created config record

    Raises:
        ObsidianSyncError: If creation fails or path is invalid
    """
    # Validate path exists
    vault_path_obj = Path(vault_path).expanduser().resolve()
    if not vault_path_obj.exists():
        raise ObsidianSyncError(f"Vault path does not exist: {vault_path}")
    if not vault_path_obj.is_dir():
        raise ObsidianSyncError(f"Vault path is not a directory: {vault_path}")

    # Check for existing active config
    existing = supabase.table('obsidian_vault_configs') \
        .select('id') \
        .eq('user_id', user_id) \
        .eq('is_active', True) \
        .execute()

    if existing.data:
        # Deactivate existing config
        supabase.table('obsidian_vault_configs') \
            .update({'is_active': False}) \
            .eq('id', existing.data[0]['id']) \
            .execute()

    # Merge sync options with defaults
    merged_options = {**DEFAULT_SYNC_OPTIONS}
    if sync_options:
        merged_options.update(sync_options)

    # Derive vault name from folder
    vault_name = vault_path_obj.name

    try:
        now = datetime.now(timezone.utc).isoformat()
        config_data = {
            'user_id': user_id,
            'client_id': client_id,
            'vault_path': str(vault_path_obj),
            'vault_name': vault_name,
            'is_active': True,
            'sync_options': merged_options,
            'created_at': now,
            'updated_at': now
        }

        result = supabase.table('obsidian_vault_configs') \
            .insert(config_data) \
            .execute()

        logger.info(f"Created vault config for {vault_name}: {result.data[0]['id']}")
        return result.data[0]

    except Exception as e:
        raise ObsidianSyncError(f"Failed to create vault config: {e}")


def update_vault_config(
    config_id: str,
    updates: Dict
) -> Dict:
    """
    Update a vault configuration.

    Args:
        config_id: UUID of the config
        updates: Fields to update

    Returns:
        Updated config record
    """
    try:
        result = supabase.table('obsidian_vault_configs') \
            .update(updates) \
            .eq('id', config_id) \
            .execute()

        return result.data[0] if result.data else {}

    except Exception as e:
        raise ObsidianSyncError(f"Failed to update vault config: {e}")


def deactivate_vault_config(config_id: str, remove_documents: bool = False) -> Dict:
    """
    Deactivate a vault configuration.

    Args:
        config_id: UUID of the config
        remove_documents: Whether to delete synced documents

    Returns:
        Status dict
    """
    try:
        # Get config for user/client info
        config = get_vault_config_by_id(config_id)
        if not config:
            raise ObsidianSyncError(f"Config not found: {config_id}")

        documents_removed = 0

        if remove_documents:
            # Get all synced documents
            sync_states = supabase.table('obsidian_sync_state') \
                .select('document_id') \
                .eq('config_id', config_id) \
                .not_.is_('document_id', 'null') \
                .execute()

            doc_ids = [s['document_id'] for s in sync_states.data if s.get('document_id')]

            if doc_ids:
                # Delete document chunks
                supabase.table('document_chunks') \
                    .delete() \
                    .in_('document_id', doc_ids) \
                    .execute()

                # Delete documents
                supabase.table('documents') \
                    .delete() \
                    .in_('id', doc_ids) \
                    .execute()

                documents_removed = len(doc_ids)
                logger.info(f"Removed {documents_removed} synced documents")

        # Delete sync state
        supabase.table('obsidian_sync_state') \
            .delete() \
            .eq('config_id', config_id) \
            .execute()

        # Deactivate config
        supabase.table('obsidian_vault_configs') \
            .update({'is_active': False}) \
            .eq('id', config_id) \
            .execute()

        return {
            'status': 'success',
            'config_id': config_id,
            'documents_removed': documents_removed
        }

    except Exception as e:
        raise ObsidianSyncError(f"Failed to deactivate vault: {e}")


# ============================================================================
# Sync State Management
# ============================================================================

def get_sync_state(config_id: str, file_path: str) -> Optional[Dict]:
    """
    Get sync state for a file.

    Args:
        config_id: UUID of the vault config
        file_path: Relative path from vault root

    Returns:
        Sync state record or None
    """
    try:
        result = supabase.table('obsidian_sync_state') \
            .select('*') \
            .eq('config_id', config_id) \
            .eq('file_path', file_path) \
            .execute()

        return result.data[0] if result.data else None

    except Exception as e:
        logger.error(f"Failed to get sync state: {e}")
        return None


def get_all_sync_states(config_id: str) -> Dict[str, Dict]:
    """
    Get all sync states for a vault config.

    Args:
        config_id: UUID of the vault config

    Returns:
        Dict mapping file_path to sync state
    """
    try:
        result = supabase.table('obsidian_sync_state') \
            .select('*') \
            .eq('config_id', config_id) \
            .execute()

        return {s['file_path']: s for s in result.data}

    except Exception as e:
        logger.error(f"Failed to get sync states: {e}")
        return {}


def update_sync_state(
    config_id: str,
    file_path: str,
    document_id: Optional[str] = None,
    file_mtime: Optional[datetime] = None,
    file_hash: Optional[str] = None,
    file_size: Optional[int] = None,
    frontmatter: Optional[Dict] = None,
    sync_status: str = 'synced',
    sync_error: Optional[str] = None
) -> Dict:
    """
    Update or create sync state for a file.

    Args:
        config_id: UUID of the vault config
        file_path: Relative path from vault root
        document_id: UUID of the synced document
        file_mtime: File modification time
        file_hash: MD5 hash of file content
        file_size: File size in bytes
        frontmatter: Parsed frontmatter dict
        sync_status: Current sync status
        sync_error: Error message if sync failed

    Returns:
        Updated sync state record
    """
    now = datetime.now(timezone.utc).isoformat()

    state_data = {
        'config_id': config_id,
        'file_path': file_path,
        'sync_status': sync_status,
        'updated_at': now
    }

    if document_id is not None:
        state_data['document_id'] = document_id
    if file_mtime is not None:
        state_data['file_mtime'] = file_mtime.isoformat() if isinstance(file_mtime, datetime) else file_mtime
    if file_hash is not None:
        state_data['file_hash'] = file_hash
    if file_size is not None:
        state_data['file_size'] = file_size
    if frontmatter is not None:
        # Serialize any datetime objects in frontmatter for JSON storage
        def serialize_value(v):
            if isinstance(v, datetime):
                return v.isoformat()
            if isinstance(v, date):
                return v.isoformat()
            if isinstance(v, list):
                return [serialize_value(item) for item in v]
            if isinstance(v, dict):
                return {k: serialize_value(val) for k, val in v.items()}
            return v
        state_data['frontmatter'] = {k: serialize_value(v) for k, v in frontmatter.items()}
    if sync_status == 'synced':
        state_data['last_synced_at'] = now
        state_data['sync_error'] = None
    if sync_error is not None:
        state_data['sync_error'] = sync_error

    try:
        # Try update first
        existing = get_sync_state(config_id, file_path)
        if existing:
            result = supabase.table('obsidian_sync_state') \
                .update(state_data) \
                .eq('id', existing['id']) \
                .execute()
        else:
            state_data['created_at'] = now
            result = supabase.table('obsidian_sync_state') \
                .insert(state_data) \
                .execute()

        return result.data[0] if result.data else {}

    except Exception as e:
        logger.error(f"Failed to update sync state: {e}")
        return {}


def mark_sync_state_deleted(config_id: str, file_path: str) -> None:
    """
    Mark a file as deleted in sync state.

    Args:
        config_id: UUID of the vault config
        file_path: Relative path from vault root
    """
    update_sync_state(config_id, file_path, sync_status='deleted')


# ============================================================================
# Sync Logging
# ============================================================================

def create_sync_log(
    config_id: str,
    user_id: str,
    sync_type: str = 'full',
    trigger_source: str = 'manual'
) -> str:
    """
    Create a sync log entry.

    Args:
        config_id: UUID of the vault config
        user_id: UUID of the user
        sync_type: Type of sync (full, incremental, watch)
        trigger_source: What triggered the sync

    Returns:
        UUID of the created log entry
    """
    log_data = {
        'config_id': config_id,
        'user_id': user_id,
        'sync_type': sync_type,
        'trigger_source': trigger_source,
        'status': 'running',
        'started_at': datetime.now(timezone.utc).isoformat()
    }

    result = supabase.table('obsidian_sync_log') \
        .insert(log_data) \
        .execute()

    return result.data[0]['id']


def complete_sync_log(
    log_id: str,
    status: str,
    stats: Optional[Dict] = None,
    error_message: Optional[str] = None,
    error_details: Optional[List[Dict]] = None
) -> None:
    """
    Complete a sync log entry.

    Args:
        log_id: UUID of the log entry
        status: Final status (completed, failed)
        stats: Sync statistics
        error_message: Error message if failed
        error_details: Detailed error list
    """
    now = datetime.now(timezone.utc).isoformat()

    update_data = {
        'status': status,
        'completed_at': now
    }

    if stats:
        update_data.update({
            'files_scanned': stats.get('files_scanned', 0),
            'files_added': stats.get('files_added', 0),
            'files_updated': stats.get('files_updated', 0),
            'files_deleted': stats.get('files_deleted', 0),
            'files_skipped': stats.get('files_skipped', 0),
            'files_failed': stats.get('files_failed', 0)
        })

    if error_message:
        update_data['error_message'] = error_message

    if error_details:
        update_data['error_details'] = error_details

    supabase.table('obsidian_sync_log') \
        .update(update_data) \
        .eq('id', log_id) \
        .execute()


# ============================================================================
# Document Sync
# ============================================================================

def sync_file(
    config: Dict,
    file_path: Path,
    existing_state: Optional[Dict] = None
) -> Dict:
    """
    Sync a single file from the vault.

    Args:
        config: Vault config record
        file_path: Absolute path to the file
        existing_state: Existing sync state if available

    Returns:
        Sync result dict
    """
    vault_path = Path(config['vault_path'])
    relative_path = str(file_path.relative_to(vault_path))
    sync_options = config.get('sync_options', DEFAULT_SYNC_OPTIONS)

    logger.info(f"   Syncing: {relative_path}")

    try:
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Get file stats
        stats = file_path.stat()
        file_mtime = datetime.fromtimestamp(stats.st_mtime, tz=timezone.utc)
        file_size = stats.st_size
        file_hash = compute_file_hash(file_path)

        # Check if file has changed (skip if unchanged)
        if existing_state:
            if existing_state.get('file_hash') == file_hash:
                logger.debug(f"      Skipping (unchanged): {relative_path}")
                return {'status': 'skipped', 'reason': 'unchanged'}

        # Parse frontmatter if enabled
        frontmatter = {}
        processed_content = content
        if sync_options.get('parse_frontmatter', True):
            frontmatter, processed_content = parse_frontmatter(content)
            if frontmatter:
                logger.debug(f"      Parsed frontmatter: {list(frontmatter.keys())}")

        # Convert wikilinks if enabled
        if sync_options.get('convert_wikilinks', True):
            processed_content = convert_wikilinks(processed_content, str(vault_path))

        # Determine document title from frontmatter or filename
        title = frontmatter.get('title') or file_path.stem

        # Extract original date from frontmatter, filename, content, or file mtime
        original_date_value = extract_original_date(
            filename=file_path.name,
            frontmatter=frontmatter,
            content=content,
            file_mtime=file_mtime
        )
        if original_date_value:
            logger.debug(f"      Extracted original_date: {original_date_value}")

        # Encode content for storage
        file_content = processed_content.encode('utf-8')

        # Validate content is not empty before proceeding
        if len(file_content) == 0:
            logger.warning(f"      Skipping empty file: {relative_path}")
            return {'status': 'skipped', 'reason': 'empty_content'}

        # Check if we're updating or creating
        document_id = existing_state.get('document_id') if existing_state else None

        if document_id:
            # Update existing document
            logger.debug(f"      Updating existing document: {document_id}")
            updated = _update_obsidian_document(
                document_id=document_id,
                file_content=file_content,
                title=title,
                relative_path=relative_path,
                frontmatter=frontmatter,
                original_date=original_date_value
            )
            action = 'updated'
        else:
            # Check for existing document with same path (deduplication)
            # This prevents duplicates if sync state was lost/corrupted
            existing_doc = supabase.table('documents') \
                .select('id') \
                .eq('user_id', config['user_id']) \
                .eq('obsidian_file_path', relative_path) \
                .execute()

            if existing_doc.data:
                # Document exists, update instead of create
                document_id = existing_doc.data[0]['id']
                logger.info(f"      Found existing document (dedup): {document_id}")
                updated = _update_obsidian_document(
                    document_id=document_id,
                    file_content=file_content,
                    title=title,
                    relative_path=relative_path,
                    frontmatter=frontmatter,
                    original_date=original_date_value
                )
                action = 'updated'
            else:
                # Create new document
                logger.debug(f"      Creating new document")
                document_id = _create_obsidian_document(
                    config=config,
                    file_content=file_content,
                    filename=file_path.name,
                    title=title,
                    relative_path=relative_path,
                    frontmatter=frontmatter,
                    original_date=original_date_value
                )
                action = 'added'

        # Update sync state
        update_sync_state(
            config_id=config['id'],
            file_path=relative_path,
            document_id=document_id,
            file_mtime=file_mtime,
            file_hash=file_hash,
            file_size=file_size,
            frontmatter=frontmatter,
            sync_status='synced'
        )

        # Process document for embeddings
        logger.debug(f"      Processing for embeddings...")
        process_document(document_id)

        logger.info(f"      Done ({action})")
        return {'status': action, 'document_id': document_id}

    except Exception as e:
        error_msg = str(e)
        logger.error(f"      Failed: {error_msg}")

        # Update sync state with error
        update_sync_state(
            config_id=config['id'],
            file_path=relative_path,
            sync_status='failed',
            sync_error=error_msg[:500]
        )

        return {'status': 'failed', 'error': error_msg}


def _create_obsidian_document(
    config: Dict,
    file_content: bytes,
    filename: str,
    title: str,
    relative_path: str,
    frontmatter: Dict,
    original_date: Optional[date] = None
) -> str:
    """
    Create a new document record for an Obsidian file.

    Returns:
        UUID of created document

    Raises:
        ObsidianSyncError: If content is empty or upload fails
    """
    # Validate content is not empty
    if not file_content or len(file_content) == 0:
        raise ObsidianSyncError(f"Cannot upload empty file: {filename}")

    user_id = config['user_id']
    client_id = config['client_id']
    vault_path = config['vault_path']

    # Generate unique storage path (sanitize filename for storage)
    unique_id = str(uuid.uuid4())
    # Remove emojis and special chars from filename for storage key
    safe_filename = re.sub(r'[^\w\s\-\.]', '', filename).strip()
    if not safe_filename:
        safe_filename = 'document.md'
    storage_path = f"obsidian/{client_id}/{unique_id}_{safe_filename}"

    # Upload to Supabase storage with error handling
    logger.info(f"Uploading {len(file_content)} bytes to storage: {storage_path}")
    try:
        upload_result = supabase.storage.from_('documents').upload(
            path=storage_path,
            file=file_content,
            file_options={"content-type": "text/markdown"}
        )
        # Check for upload errors (Supabase returns error in response, not exception)
        if hasattr(upload_result, 'error') and upload_result.error:
            raise ObsidianSyncError(f"Storage upload failed: {upload_result.error}")
        logger.info(f"Upload successful: {storage_path}")
    except ObsidianSyncError:
        raise
    except Exception as e:
        raise ObsidianSyncError(f"Storage upload failed for {filename}: {e}")

    storage_url = f"{SUPABASE_URL}/storage/v1/object/public/documents/{storage_path}"

    # Create document record
    now = datetime.now(timezone.utc).isoformat()
    document_data = {
        'user_id': user_id,
        'client_id': client_id,
        'uploaded_by': user_id,
        'filename': filename,
        'title': title,
        'storage_url': storage_url,
        'storage_path': storage_path,
        'source_platform': 'obsidian',
        'obsidian_vault_path': vault_path,
        'obsidian_file_path': relative_path,
        'last_synced_at': now,
        'processed': False,
        'uploaded_at': now,
        'original_date': original_date.isoformat() if original_date else None
        # Note: frontmatter is stored in obsidian_sync_state, not documents
    }

    result = supabase.table('documents').insert(document_data).execute()
    document = result.data[0]

    # Check for thesis-agents in frontmatter for auto-tagging
    thesis_agents = frontmatter.get('thesis-agents', [])
    if thesis_agents and isinstance(thesis_agents, list):
        _link_document_to_agents(document['id'], user_id, thesis_agents)

    # Sync tags from file path (folder structure becomes tags)
    path_tags = _extract_path_tags(relative_path)
    if path_tags:
        _sync_document_tags(document['id'], path_tags, source='path')

    # Also sync any explicit tags from frontmatter
    frontmatter_tags = frontmatter.get('tags', [])
    if frontmatter_tags and isinstance(frontmatter_tags, list):
        _sync_document_tags(document['id'], frontmatter_tags, source='frontmatter')

    return document['id']


def _update_obsidian_document(
    document_id: str,
    file_content: bytes,
    title: str,
    relative_path: str,
    frontmatter: Optional[Dict] = None,
    original_date: Optional[date] = None
) -> Dict:
    """
    Update an existing Obsidian document.

    Args:
        document_id: UUID of the document
        file_content: Processed markdown content
        title: Document title from frontmatter or filename
        relative_path: Relative path within the vault
        frontmatter: Parsed frontmatter dict for tag syncing

    Returns:
        Updated document record

    Raises:
        ObsidianSyncError: If content is empty or upload fails
    """
    # Validate content is not empty
    if not file_content or len(file_content) == 0:
        raise ObsidianSyncError(f"Cannot update with empty content: {document_id}")

    # Get existing document
    doc_result = supabase.table('documents') \
        .select('storage_url, filename') \
        .eq('id', document_id) \
        .execute()

    if not doc_result.data:
        raise ObsidianSyncError(f"Document not found: {document_id}")

    storage_url = doc_result.data[0]['storage_url']
    filename = doc_result.data[0].get('filename', document_id)
    storage_path = storage_url.split('/documents/')[-1]

    # Update file in storage with error handling
    logger.info(f"Updating {len(file_content)} bytes in storage: {storage_path}")
    try:
        update_result = supabase.storage.from_('documents').update(
            path=storage_path,
            file=file_content,
            file_options={"upsert": "true"}
        )
        # Check for update errors
        if hasattr(update_result, 'error') and update_result.error:
            raise ObsidianSyncError(f"Storage update failed: {update_result.error}")
        logger.info(f"Update successful: {storage_path}")
    except ObsidianSyncError:
        raise
    except Exception as e:
        raise ObsidianSyncError(f"Storage update failed for {filename}: {e}")

    # Delete old embeddings
    supabase.table('document_chunks') \
        .delete() \
        .eq('document_id', document_id) \
        .execute()

    # Update document record
    now = datetime.now(timezone.utc).isoformat()
    update_data = {
        'title': title,
        'obsidian_file_path': relative_path,
        'last_synced_at': now,
        'processed': False
    }

    # Only update original_date if provided and not already set
    if original_date:
        # Check if original_date is already set
        existing_doc = supabase.table('documents').select('original_date').eq('id', document_id).execute()
        if existing_doc.data and not existing_doc.data[0].get('original_date'):
            update_data['original_date'] = original_date.isoformat()

    result = supabase.table('documents') \
        .update(update_data) \
        .eq('id', document_id) \
        .execute()

    # Sync tags from file path (folder structure becomes tags)
    path_tags = _extract_path_tags(relative_path)
    if path_tags:
        _sync_document_tags(document_id, path_tags, source='path')

    # Also sync any explicit tags from frontmatter
    if frontmatter:
        frontmatter_tags = frontmatter.get('tags', [])
        if isinstance(frontmatter_tags, list):
            _sync_document_tags(document_id, frontmatter_tags, source='frontmatter')

    return result.data[0] if result.data else {}


def _extract_path_tags(relative_path: str) -> List[str]:
    """
    Extract tags from the file path based on folder structure.

    For example: "Projects/AI Strategy/meeting-notes.md" -> ["Projects", "AI Strategy"]

    Args:
        relative_path: Relative path from vault root (e.g., "folder/subfolder/file.md")

    Returns:
        List of folder names as tags (excludes the filename itself)
    """
    from pathlib import PurePath
    path = PurePath(relative_path)

    # Get all parent folders (exclude the filename)
    parts = list(path.parts[:-1])  # Exclude last part (filename)

    # Filter out empty parts and return
    return [part for part in parts if part and part.strip()]


def _sync_document_tags(document_id: str, tags: List[str], source: str = 'frontmatter') -> None:
    """
    Sync tags to document_tags table.

    For path and frontmatter sources, replaces existing tags of that source on each sync
    while preserving manual tags.

    Args:
        document_id: UUID of the document
        tags: List of tag strings
        source: Tag source - 'path' (from folder structure), 'frontmatter', or 'manual'
    """
    # Delete existing tags of this source type (preserve other sources)
    if source in ('frontmatter', 'path'):
        try:
            supabase.table('document_tags') \
                .delete() \
                .eq('document_id', document_id) \
                .eq('source', source) \
                .execute()
        except Exception as e:
            logger.warning(f"Failed to delete existing {source} tags: {e}")

    # Insert new tags
    for tag in tags:
        if isinstance(tag, str) and tag.strip():
            try:
                supabase.table('document_tags').upsert({
                    'document_id': document_id,
                    'tag': tag.strip(),
                    'source': source
                }, on_conflict='document_id,tag').execute()
                logger.debug(f"      Synced tag: {tag}")
            except Exception as e:
                logger.warning(f"      Failed to sync tag '{tag}': {e}")


def _link_document_to_agents(document_id: str, user_id: str, agent_names: List[str]) -> None:
    """
    Link document to agents based on thesis-agents frontmatter.

    Args:
        document_id: UUID of the document
        user_id: UUID of the user
        agent_names: List of agent names from frontmatter
    """
    # Get agent IDs for the specified names
    agents_result = supabase.table('agents') \
        .select('id, name') \
        .in_('name', [name.lower() for name in agent_names]) \
        .execute()

    agent_map = {a['name'].lower(): a['id'] for a in agents_result.data}

    for agent_name in agent_names:
        agent_id = agent_map.get(agent_name.lower())
        if agent_id:
            try:
                supabase.table('agent_knowledge_base').insert({
                    'agent_id': agent_id,
                    'document_id': document_id,
                    'added_by': user_id,
                    'priority': 0,
                    'relevance_score': 0.9,
                    'classification_source': 'frontmatter',
                    'classification_confidence': 1.0,
                    'user_confirmed': True
                }).execute()
                logger.debug(f"      Linked to agent: {agent_name}")
            except Exception as e:
                logger.warning(f"      Failed to link to agent {agent_name}: {e}")
        else:
            logger.warning(f"      Unknown agent in frontmatter: {agent_name}")


# ============================================================================
# Full Sync
# ============================================================================

def sync_vault(
    config: Dict,
    trigger_source: str = 'manual'
) -> Dict:
    """
    Perform a full vault sync.

    Args:
        config: Vault config record
        trigger_source: What triggered the sync

    Returns:
        Sync results dict
    """
    logger.info(f"\n Obsidian sync for vault: {config['vault_name']}")
    logger.info(f"   Path: {config['vault_path']}")

    # Create sync log
    log_id = create_sync_log(
        config_id=config['id'],
        user_id=config['user_id'],
        sync_type='full',
        trigger_source=trigger_source
    )

    stats = {
        'files_scanned': 0,
        'files_added': 0,
        'files_updated': 0,
        'files_deleted': 0,
        'files_skipped': 0,
        'files_failed': 0
    }
    error_details = []

    try:
        vault_path = Path(config['vault_path'])
        sync_options = config.get('sync_options', DEFAULT_SYNC_OPTIONS)

        # Scan vault for files
        files = scan_vault(
            vault_path=vault_path,
            include_patterns=sync_options.get('include_patterns', ['**/*.md']),
            exclude_patterns=sync_options.get('exclude_patterns', ['.obsidian/**']),
            max_file_size_mb=sync_options.get('max_file_size_mb', 10)
        )

        stats['files_scanned'] = len(files)
        logger.info(f"   Found {len(files)} files to sync")

        # Get existing sync states
        existing_states = get_all_sync_states(config['id'])
        synced_paths: Set[str] = set()

        # Sync each file
        for file_path in files:
            relative_path = str(file_path.relative_to(vault_path))
            synced_paths.add(relative_path)

            existing_state = existing_states.get(relative_path)
            result = sync_file(config, file_path, existing_state)

            if result['status'] == 'added':
                stats['files_added'] += 1
            elif result['status'] == 'updated':
                stats['files_updated'] += 1
            elif result['status'] == 'skipped':
                stats['files_skipped'] += 1
            elif result['status'] == 'failed':
                stats['files_failed'] += 1
                error_details.append({
                    'file_path': relative_path,
                    'error': result.get('error', 'Unknown error')
                })

        # Handle deleted files
        sync_on_delete = sync_options.get('sync_on_delete', False)
        for existing_path, state in existing_states.items():
            if existing_path not in synced_paths and state.get('sync_status') != 'deleted':
                if sync_on_delete and state.get('document_id'):
                    # Delete the document
                    try:
                        doc_id = state['document_id']
                        supabase.table('document_chunks') \
                            .delete() \
                            .eq('document_id', doc_id) \
                            .execute()
                        supabase.table('documents') \
                            .delete() \
                            .eq('id', doc_id) \
                            .execute()
                        logger.info(f"   Deleted: {existing_path}")
                    except Exception as e:
                        logger.warning(f"   Failed to delete {existing_path}: {e}")

                mark_sync_state_deleted(config['id'], existing_path)
                stats['files_deleted'] += 1

        # Update config with last sync time
        update_vault_config(config['id'], {
            'last_sync_at': datetime.now(timezone.utc).isoformat(),
            'last_error': None
        })

        # Complete sync log
        complete_sync_log(log_id, 'completed', stats, error_details=error_details if error_details else None)

        logger.info("\n Sync complete!")
        logger.info(f"   Added: {stats['files_added']}")
        logger.info(f"   Updated: {stats['files_updated']}")
        logger.info(f"   Skipped: {stats['files_skipped']}")
        logger.info(f"   Deleted: {stats['files_deleted']}")
        logger.info(f"   Failed: {stats['files_failed']}")

        return {
            'status': 'success',
            'sync_log_id': log_id,
            **stats
        }

    except Exception as e:
        error_msg = str(e)
        logger.error(f"\n Sync failed: {error_msg}")

        # Update config with error
        update_vault_config(config['id'], {
            'last_error': error_msg[:500]
        })

        # Complete sync log with failure
        complete_sync_log(log_id, 'failed', stats, error_message=error_msg)

        raise ObsidianSyncError(f"Vault sync failed: {e}")


# ============================================================================
# Status and Connection Management
# ============================================================================

def get_sync_status(user_id: str) -> Dict:
    """
    Get Obsidian sync status for a user.

    Args:
        user_id: UUID of the user

    Returns:
        Status dict with connection info
    """
    config = get_vault_config(user_id)

    if not config:
        return {
            'connected': False,
            'vault_path': None,
            'vault_name': None,
            'is_active': False,
            'files_synced': 0,
            'last_sync': None,
            'pending_changes': 0
        }

    # Count synced files
    synced_result = supabase.table('obsidian_sync_state') \
        .select('id', count='exact') \
        .eq('config_id', config['id']) \
        .eq('sync_status', 'synced') \
        .execute()

    # Count pending/failed files
    pending_result = supabase.table('obsidian_sync_state') \
        .select('id', count='exact') \
        .eq('config_id', config['id']) \
        .in_('sync_status', ['pending', 'failed']) \
        .execute()

    return {
        'connected': True,
        'config_id': config['id'],
        'vault_path': config['vault_path'],
        'vault_name': config['vault_name'],
        'is_active': config['is_active'],
        'files_synced': synced_result.count or 0,
        'last_sync': config.get('last_sync_at'),
        'last_error': config.get('last_error'),
        'pending_changes': pending_result.count or 0,
        'sync_options': config.get('sync_options', {})
    }


# ============================================================================
# File Watcher (using watchdog)
# ============================================================================

class ObsidianVaultWatcher:
    """
    File watcher for Obsidian vault using watchdog library.

    Monitors configured vault directory for .md file changes and
    syncs them to the Thesis Knowledge Base.
    """

    def __init__(
        self,
        config: Dict,
        on_sync_complete: Optional[Callable[[str, Dict], None]] = None
    ):
        """
        Initialize the vault watcher.

        Args:
            config: Vault configuration record
            on_sync_complete: Optional callback for sync completion
        """
        self.config = config
        self.vault_path = Path(config['vault_path'])
        self.sync_options = config.get('sync_options', DEFAULT_SYNC_OPTIONS)
        self.on_sync_complete = on_sync_complete

        self._observer = None
        self._debounce_timers: Dict[str, float] = {}  # file_path -> scheduled_time
        self._pending_changes: Dict[str, Tuple[str, Path]] = {}  # file_path -> (event_type, file_path)
        self._lock = asyncio.Lock()
        self._running = False
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None
        self._process_task: Optional[asyncio.Task] = None

    def _should_process(self, file_path: Path) -> bool:
        """Check if a file should be processed based on patterns."""
        return should_include_file(
            file_path,
            self.vault_path,
            self.sync_options.get('include_patterns', ['**/*.md']),
            self.sync_options.get('exclude_patterns', ['.obsidian/**'])
        )

    def _handle_file_event(self, event_type: str, src_path: str) -> None:
        """
        Handle a file system event with debouncing.

        This is called from the watchdog thread, so we need to be thread-safe.
        We queue events and let the async processor handle them.

        Args:
            event_type: Type of event (created, modified, deleted, moved)
            src_path: Path to the file
        """
        file_path = Path(src_path)

        # Skip non-markdown files and excluded paths
        if not file_path.suffix == '.md':
            return
        if not self._should_process(file_path):
            return

        relative_path = str(file_path.relative_to(self.vault_path))
        debounce_ms = self.sync_options.get('debounce_ms', 500)
        debounce_secs = debounce_ms / 1000.0

        # Schedule this event to be processed after debounce period
        # Store the time when it should be processed
        process_time = time_module.time() + debounce_secs
        self._debounce_timers[relative_path] = process_time
        self._pending_changes[relative_path] = (event_type, file_path)

        logger.debug(f"[Watcher] Queued {event_type}: {relative_path}")

    async def _process_pending_changes(self) -> None:
        """
        Background task that processes pending file changes.

        Runs continuously while the watcher is active, checking for
        debounced events that are ready to be processed.
        """
        while self._running:
            try:
                # Find events that are ready to process (debounce time has passed)
                current_time = time_module.time()
                ready_to_process = []

                for relative_path, process_time in list(self._debounce_timers.items()):
                    if current_time >= process_time:
                        if relative_path in self._pending_changes:
                            event_type, file_path = self._pending_changes.pop(relative_path)
                            ready_to_process.append((event_type, file_path, relative_path))
                        del self._debounce_timers[relative_path]

                # Process ready events
                for event_type, file_path, relative_path in ready_to_process:
                    await self._process_file_change(event_type, file_path)

                # Small sleep to avoid busy-waiting
                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"[Watcher] Error in change processor: {e}")
                await asyncio.sleep(1)  # Back off on error

    async def _process_file_change(self, event_type: str, file_path: Path) -> None:
        """
        Process a file change after debounce period.

        Args:
            event_type: Type of change
            file_path: Path to the file
        """
        relative_path = str(file_path.relative_to(self.vault_path))

        async with self._lock:
            # Remove from debounce timers
            self._debounce_timers.pop(relative_path, None)

            logger.info(f"[Watcher] {event_type}: {relative_path}")

            # Create a mini sync log for this single file
            log_id = create_sync_log(
                config_id=self.config['id'],
                user_id=self.config['user_id'],
                sync_type='watch',
                trigger_source='watcher'
            )

            stats = {
                'files_scanned': 1,
                'files_added': 0,
                'files_updated': 0,
                'files_deleted': 0,
                'files_skipped': 0,
                'files_failed': 0
            }

            try:
                if event_type == 'deleted':
                    # Handle deletion
                    existing_state = get_sync_state(self.config['id'], relative_path)
                    if existing_state and existing_state.get('document_id'):
                        if self.sync_options.get('sync_on_delete', False):
                            doc_id = existing_state['document_id']
                            supabase.table('document_chunks') \
                                .delete() \
                                .eq('document_id', doc_id) \
                                .execute()
                            supabase.table('documents') \
                                .delete() \
                                .eq('id', doc_id) \
                                .execute()
                        mark_sync_state_deleted(self.config['id'], relative_path)
                        stats['files_deleted'] = 1
                else:
                    # Handle create/modify
                    if file_path.exists():
                        existing_state = get_sync_state(self.config['id'], relative_path)
                        result = sync_file(self.config, file_path, existing_state)

                        if result['status'] == 'added':
                            stats['files_added'] = 1
                        elif result['status'] == 'updated':
                            stats['files_updated'] = 1
                        elif result['status'] == 'skipped':
                            stats['files_skipped'] = 1
                        elif result['status'] == 'failed':
                            stats['files_failed'] = 1

                complete_sync_log(log_id, 'completed', stats)

                if self.on_sync_complete:
                    self.on_sync_complete(relative_path, stats)

            except Exception as e:
                logger.error(f"[Watcher] Error processing {relative_path}: {e}")
                complete_sync_log(log_id, 'failed', stats, error_message=str(e))

    def start(self) -> None:
        """Start the file watcher."""
        try:
            from watchdog.events import FileSystemEventHandler
            from watchdog.observers import Observer
        except ImportError:
            raise ObsidianSyncError(
                "watchdog library not installed. Install with: pip install watchdog"
            )

        if self._running:
            return

        # Store reference to the event loop for thread-safe scheduling
        try:
            self._event_loop = asyncio.get_running_loop()
        except RuntimeError:
            self._event_loop = asyncio.get_event_loop()

        class EventHandler(FileSystemEventHandler):
            def __init__(handler_self, watcher):
                handler_self.watcher = watcher

            def on_created(handler_self, event):
                if not event.is_directory:
                    handler_self.watcher._handle_file_event('created', event.src_path)

            def on_modified(handler_self, event):
                if not event.is_directory:
                    handler_self.watcher._handle_file_event('modified', event.src_path)

            def on_deleted(handler_self, event):
                if not event.is_directory:
                    handler_self.watcher._handle_file_event('deleted', event.src_path)

            def on_moved(handler_self, event):
                if not event.is_directory:
                    handler_self.watcher._handle_file_event('deleted', event.src_path)
                    handler_self.watcher._handle_file_event('created', event.dest_path)

        self._observer = Observer()
        self._observer.schedule(
            EventHandler(self),
            str(self.vault_path),
            recursive=True
        )
        self._observer.start()
        self._running = True

        # Start the background task for processing pending changes
        self._process_task = asyncio.create_task(self._process_pending_changes())

        logger.info(f"[Watcher] Started watching: {self.vault_path}")

    def stop(self) -> None:
        """Stop the file watcher."""
        if self._observer and self._running:
            self._running = False

            # Cancel the background processing task
            if self._process_task and not self._process_task.done():
                self._process_task.cancel()
                try:
                    # Give it a moment to cancel
                    pass
                except Exception:
                    pass

            self._observer.stop()
            self._observer.join()

            # Clear pending changes
            self._debounce_timers.clear()
            self._pending_changes.clear()

            logger.info("[Watcher] Stopped")

    def is_running(self) -> bool:
        """Check if watcher is running."""
        return self._running
