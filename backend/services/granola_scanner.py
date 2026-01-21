"""
Granola Meeting Scanner Service

Scans the Granola vault for meeting summaries and extracts:
- AI opportunities
- Action items/tasks
- Stakeholder mentions

Uses existing tables (ai_opportunities, project_tasks, stakeholders) - no new schema needed.
"""

import hashlib
import os
import re
from datetime import datetime, timezone, date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
import anthropic

from database import get_supabase
from document_processor import process_document
from logger_config import get_logger

logger = get_logger(__name__)

# Get Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
supabase = get_supabase()

# Default Granola vault path
DEFAULT_GRANOLA_PATH = "/Users/charlie.fuller/vaults/Contentful/Granola"

# Frontmatter pattern
FRONTMATTER_PATTERN = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)


class GranolaScannerError(Exception):
    """Raised when Granola scanning operations fail"""
    pass


def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """Parse YAML frontmatter from markdown content."""
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


def compute_file_hash(file_path: Path) -> str:
    """Compute MD5 hash of file content for change detection."""
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)
    return hasher.hexdigest()


def parse_date_from_iso(date_str: str) -> Optional[date]:
    """Parse ISO date string to date object."""
    if not date_str:
        return None
    try:
        # Handle ISO format with timezone
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.date()
    except (ValueError, TypeError):
        return None


async def extract_structured_data(
    content: str,
    title: str,
    meeting_date: Optional[date]
) -> Dict[str, Any]:
    """
    Use Claude to extract opportunities, tasks, and stakeholders from meeting content.

    Returns dict with:
    - opportunities: List of {description, department, potential_impact, effort_estimate, quote}
    - tasks: List of {title, description, assignee_name, due_date}
    - stakeholders: List of {name, role, department, sentiment, concerns, interests}
    """
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    prompt = f"""Analyze this meeting summary and extract structured data.

Meeting: {title}
Date: {meeting_date.isoformat() if meeting_date else 'Unknown'}

Content:
{content}

Extract the following in JSON format:

1. **opportunities** - AI/automation opportunities mentioned:
   - description: What the opportunity is
   - department: Which department (Legal, HR, Finance, IT, Engineering, etc.)
   - potential_impact: 1-5 score (5 = transformative)
   - effort_estimate: 1-5 score (5 = very complex)
   - strategic_alignment: 1-5 score (5 = highly strategic)
   - quote: A relevant quote from the content (if any)

2. **tasks** - Action items, follow-ups, commitments:
   - title: Short task title
   - description: What needs to be done
   - assignee_name: Who is responsible (if mentioned)
   - due_date: When it's due (if mentioned, in YYYY-MM-DD format)

3. **stakeholders** - People mentioned with context:
   - name: Person's name
   - role: Their role/title (if mentioned)
   - department: Their department (if mentioned)
   - sentiment: positive/neutral/skeptical based on their AI stance
   - concerns: Any concerns they raised (array of strings)
   - interests: What they're interested in (array of strings)

Return ONLY valid JSON with this structure:
{{
  "opportunities": [...],
  "tasks": [...],
  "stakeholders": [...]
}}

If no items found for a category, return an empty array.
Be conservative - only extract items that are clearly present in the content."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse JSON from response
        response_text = response.content[0].text

        # Extract JSON from response (handle markdown code blocks)
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            import json
            return json.loads(json_match.group())

        return {"opportunities": [], "tasks": [], "stakeholders": []}

    except Exception as e:
        logger.error(f"Failed to extract structured data: {e}")
        return {"opportunities": [], "tasks": [], "stakeholders": []}


def get_scan_state(user_id: str, granola_id: str) -> Optional[Dict]:
    """Check if a meeting has already been scanned."""
    try:
        result = supabase.table('documents') \
            .select('id, granola_id, granola_scanned_at') \
            .eq('user_id', user_id) \
            .eq('granola_id', granola_id) \
            .execute()

        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Failed to get scan state: {e}")
        return None


async def scan_meeting_file(
    file_path: Path,
    user_id: str,
    client_id: str,
    force_rescan: bool = False
) -> Dict[str, Any]:
    """
    Scan a single Granola meeting summary file.

    Returns scan result with status and extracted data.
    """
    logger.info(f"Scanning: {file_path.name}")

    try:
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse frontmatter
        frontmatter, body_content = parse_frontmatter(content)

        granola_id = frontmatter.get('granola_id')
        if not granola_id:
            logger.warning(f"No granola_id in {file_path.name}, skipping")
            return {'status': 'skipped', 'reason': 'no_granola_id'}

        # Check if already scanned
        existing = get_scan_state(user_id, granola_id)
        if existing and existing.get('granola_scanned_at') and not force_rescan:
            logger.debug(f"Already scanned: {file_path.name}")
            return {'status': 'skipped', 'reason': 'already_scanned', 'document_id': existing['id']}

        title = frontmatter.get('title', file_path.stem)
        created_str = frontmatter.get('created', '')
        meeting_date = parse_date_from_iso(created_str)
        attendees = frontmatter.get('attendees', [])

        # Extract structured data
        extracted = await extract_structured_data(body_content, title, meeting_date)

        # Create or update document in KB
        file_hash = compute_file_hash(file_path)
        now = datetime.now(timezone.utc).isoformat()

        if existing:
            # Update existing document
            document_id = existing['id']
            supabase.table('documents').update({
                'title': title,
                'granola_scanned_at': now,
                'updated_at': now
            }).eq('id', document_id).execute()
        else:
            # Create new document
            # First upload content to storage
            import uuid
            unique_id = str(uuid.uuid4())
            safe_filename = re.sub(r'[^\w\s\-\.]', '', file_path.name).strip() or 'meeting.md'
            storage_path = f"granola/{client_id}/{unique_id}_{safe_filename}"

            file_content = content.encode('utf-8')
            supabase.storage.from_('documents').upload(
                path=storage_path,
                file=file_content,
                file_options={"content-type": "text/markdown"}
            )

            storage_url = f"{SUPABASE_URL}/storage/v1/object/public/documents/{storage_path}"

            doc_result = supabase.table('documents').insert({
                'user_id': user_id,
                'client_id': client_id,
                'uploaded_by': user_id,
                'filename': file_path.name,
                'title': title,
                'storage_url': storage_url,
                'storage_path': storage_path,
                'source_platform': 'granola',
                'granola_id': granola_id,
                'granola_scanned_at': now,
                'original_date': meeting_date.isoformat() if meeting_date else None,
                'document_type': 'transcript',  # Use existing enum value
                'processed': False,
                'uploaded_at': now
            }).execute()

            document_id = doc_result.data[0]['id']

        # Process document for embeddings
        process_document(document_id)

        # Store extracted opportunities
        opportunities_created = 0
        for opp in extracted.get('opportunities', []):
            try:
                # Generate opportunity code based on department
                dept = opp.get('department', 'General')
                dept_prefix = dept[0].upper() if dept else 'G'

                # Get next number for this department
                existing = supabase.table('ai_opportunities') \
                    .select('opportunity_code') \
                    .eq('client_id', client_id) \
                    .ilike('opportunity_code', f'{dept_prefix}%') \
                    .execute()

                next_num = len(existing.data) + 1 if existing.data else 1
                opp_code = f"{dept_prefix}{next_num:02d}"

                supabase.table('ai_opportunities').insert({
                    'client_id': client_id,
                    'opportunity_code': opp_code,
                    'title': opp.get('description', '')[:200],
                    'description': opp.get('description', ''),
                    'department': dept,
                    'roi_potential': opp.get('potential_impact', 3),
                    'implementation_effort': opp.get('effort_estimate', 3),
                    'strategic_alignment': opp.get('strategic_alignment', 3),
                    'stakeholder_readiness': 3,  # Default
                    'status': 'identified',
                    'source_type': 'meeting',
                    'source_id': document_id,
                    'source_notes': opp.get('quote', ''),
                    'created_at': now
                }).execute()
                opportunities_created += 1
            except Exception as e:
                logger.warning(f"Failed to create opportunity: {e}")

        # Store extracted tasks
        tasks_created = 0
        for task in extracted.get('tasks', []):
            try:
                task_title = task.get('title', '')[:200]
                if not task_title:
                    continue

                # Check for duplicate by title
                existing_task = supabase.table('project_tasks') \
                    .select('id') \
                    .eq('client_id', client_id) \
                    .eq('title', task_title) \
                    .execute()

                if not existing_task.data:
                    supabase.table('project_tasks').insert({
                        'client_id': client_id,
                        'title': task_title,
                        'description': task.get('description', ''),
                        'assignee_name': task.get('assignee_name'),
                        'due_date': task.get('due_date'),
                        'status': 'pending',
                        'priority': 3,
                        'source_type': 'meeting',
                        'source_document_id': document_id,
                        'created_at': now
                    }).execute()
                    tasks_created += 1
            except Exception as e:
                logger.warning(f"Failed to create task: {e}")

        # Store extracted stakeholders (as candidates for review)
        stakeholders_created = 0
        for sh in extracted.get('stakeholders', []):
            try:
                name = sh.get('name', '').strip()
                if not name or len(name) < 2:
                    continue

                # Check for existing stakeholder
                existing_sh = supabase.table('stakeholders') \
                    .select('id') \
                    .eq('client_id', client_id) \
                    .ilike('name', f'%{name}%') \
                    .execute()

                if not existing_sh.data:
                    # Check for existing candidate
                    existing_cand = supabase.table('stakeholder_candidates') \
                        .select('id') \
                        .eq('client_id', client_id) \
                        .ilike('name', f'%{name}%') \
                        .execute()

                    if not existing_cand.data:
                        supabase.table('stakeholder_candidates').insert({
                            'client_id': client_id,
                            'name': name,
                            'role': sh.get('role'),
                            'department': sh.get('department'),
                            'initial_sentiment': sh.get('sentiment', 'neutral'),
                            'key_concerns': sh.get('concerns', []),
                            'interests': sh.get('interests', []),
                            'source_document_id': document_id,
                            'source_document_name': title,
                            'status': 'pending',
                            'confidence': 'medium',
                            'created_at': now
                        }).execute()
                        stakeholders_created += 1
            except Exception as e:
                logger.warning(f"Failed to create stakeholder candidate: {e}")

        return {
            'status': 'processed',
            'document_id': document_id,
            'title': title,
            'meeting_date': meeting_date.isoformat() if meeting_date else None,
            'opportunities_created': opportunities_created,
            'tasks_created': tasks_created,
            'stakeholders_created': stakeholders_created
        }

    except Exception as e:
        logger.error(f"Failed to scan {file_path.name}: {e}")
        return {'status': 'failed', 'error': str(e)}


async def scan_granola_vault(
    user_id: str,
    client_id: str,
    vault_path: str = DEFAULT_GRANOLA_PATH,
    force_rescan: bool = False
) -> Dict[str, Any]:
    """
    Scan the Granola vault for new meeting summaries.

    Args:
        user_id: User ID
        client_id: Client ID
        vault_path: Path to Granola vault
        force_rescan: Re-process already scanned files

    Returns:
        Scan results with stats
    """
    logger.info(f"\nScanning Granola vault: {vault_path}")

    vault = Path(vault_path)
    summaries_dir = vault / "Meeting-summaries"

    if not summaries_dir.exists():
        raise GranolaScannerError(f"Meeting-summaries folder not found: {summaries_dir}")

    stats = {
        'files_scanned': 0,
        'files_processed': 0,
        'files_skipped': 0,
        'files_failed': 0,
        'opportunities_created': 0,
        'tasks_created': 0,
        'stakeholders_created': 0
    }

    results = []

    # Scan all .md files in Meeting-summaries
    for file_path in sorted(summaries_dir.glob('*.md')):
        if file_path.name.startswith('.'):
            continue

        stats['files_scanned'] += 1

        result = await scan_meeting_file(file_path, user_id, client_id, force_rescan)
        results.append({'file': file_path.name, **result})

        if result['status'] == 'processed':
            stats['files_processed'] += 1
            stats['opportunities_created'] += result.get('opportunities_created', 0)
            stats['tasks_created'] += result.get('tasks_created', 0)
            stats['stakeholders_created'] += result.get('stakeholders_created', 0)
        elif result['status'] == 'skipped':
            stats['files_skipped'] += 1
        else:
            stats['files_failed'] += 1

    logger.info(f"\nScan complete!")
    logger.info(f"  Scanned: {stats['files_scanned']}")
    logger.info(f"  Processed: {stats['files_processed']}")
    logger.info(f"  Skipped: {stats['files_skipped']}")
    logger.info(f"  Failed: {stats['files_failed']}")
    logger.info(f"  Opportunities: {stats['opportunities_created']}")
    logger.info(f"  Tasks: {stats['tasks_created']}")
    logger.info(f"  Stakeholders: {stats['stakeholders_created']}")

    return {
        'status': 'success',
        'stats': stats,
        'results': results
    }


def get_scan_status(user_id: str, vault_path: str = DEFAULT_GRANOLA_PATH) -> Dict[str, Any]:
    """
    Get current scan status for the Granola vault.

    Returns counts of scanned vs unscanned files.
    """
    vault = Path(vault_path)
    summaries_dir = vault / "Meeting-summaries"

    if not summaries_dir.exists():
        return {
            'connected': False,
            'vault_path': vault_path,
            'error': 'Meeting-summaries folder not found'
        }

    # Count total files
    total_files = len(list(summaries_dir.glob('*.md')))

    # Count scanned documents
    scanned_result = supabase.table('documents') \
        .select('id', count='exact') \
        .eq('user_id', user_id) \
        .eq('source_platform', 'granola') \
        .not_.is_('granola_scanned_at', 'null') \
        .execute()

    scanned_count = scanned_result.count or 0

    return {
        'connected': True,
        'vault_path': vault_path,
        'total_files': total_files,
        'scanned_files': scanned_count,
        'pending_files': total_files - scanned_count
    }
