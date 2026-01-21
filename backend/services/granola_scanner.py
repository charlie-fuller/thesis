"""
Granola Meeting Scanner Service

Scans synced Granola meeting documents from the KB and extracts:
- AI opportunities
- Action items/tasks
- Stakeholder mentions

Works with documents already synced via Obsidian vault sync.
Uses existing tables (ai_opportunities, project_tasks, stakeholders) - no new schema needed.
"""

import os
import re
from datetime import datetime, timezone, date
from typing import Any, Dict, List, Optional, Tuple

import yaml
import anthropic
import httpx

from database import get_supabase
from document_processor import process_document
from logger_config import get_logger

logger = get_logger(__name__)

# Get Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
supabase = get_supabase()

# Frontmatter pattern
FRONTMATTER_PATTERN = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)

# Pattern to identify Granola meeting documents in storage paths
GRANOLA_PATH_PATTERN = re.compile(r'Granola[/\\]Meeting-summaries[/\\]', re.IGNORECASE)


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


async def fetch_document_content(storage_url: str) -> Optional[str]:
    """Fetch document content from Supabase storage."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(storage_url, timeout=30.0)
            if response.status_code == 200:
                return response.text
            else:
                logger.warning(f"Failed to fetch document: {response.status_code}")
                return None
    except Exception as e:
        logger.error(f"Error fetching document content: {e}")
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


async def scan_document(
    document: Dict[str, Any],
    user_id: str,
    client_id: str,
    force_rescan: bool = False
) -> Dict[str, Any]:
    """
    Scan a single document from the KB for opportunities, tasks, and stakeholders.

    Returns scan result with status and extracted data.
    """
    document_id = document['id']
    filename = document.get('filename', 'Unknown')
    storage_url = document.get('storage_url')

    logger.info(f"Scanning document: {filename}")

    # Check if already scanned
    if document.get('granola_scanned_at') and not force_rescan:
        logger.debug(f"Already scanned: {filename}")
        return {'status': 'skipped', 'reason': 'already_scanned', 'document_id': document_id}

    if not storage_url:
        logger.warning(f"No storage URL for document: {filename}")
        return {'status': 'skipped', 'reason': 'no_storage_url', 'document_id': document_id}

    try:
        # Fetch document content
        content = await fetch_document_content(storage_url)
        if not content:
            return {'status': 'failed', 'error': 'Could not fetch document content'}

        # Parse frontmatter
        frontmatter, body_content = parse_frontmatter(content)

        title = document.get('title') or frontmatter.get('title') or filename
        created_str = frontmatter.get('created', '')
        meeting_date = parse_date_from_iso(created_str)

        # Extract structured data
        extracted = await extract_structured_data(body_content, title, meeting_date)

        # Update document scan timestamp
        now = datetime.now(timezone.utc).isoformat()
        supabase.table('documents').update({
            'granola_scanned_at': now,
            'updated_at': now
        }).eq('id', document_id).execute()

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
        logger.error(f"Failed to scan document {filename}: {e}")
        return {'status': 'failed', 'error': str(e)}


async def scan_granola_documents(
    user_id: str,
    client_id: str,
    force_rescan: bool = False
) -> Dict[str, Any]:
    """
    Scan Granola meeting documents from the KB.

    Finds documents with storage paths containing 'Granola/Meeting-summaries'
    and extracts opportunities, tasks, and stakeholders.

    Args:
        user_id: User ID
        client_id: Client ID
        force_rescan: Re-process already scanned files

    Returns:
        Scan results with stats
    """
    logger.info("Scanning Granola documents from KB")

    # Find Granola meeting documents in KB
    # Look for documents with storage_path containing Granola/Meeting-summaries
    try:
        query = supabase.table('documents') \
            .select('id, filename, title, storage_url, storage_path, granola_scanned_at') \
            .eq('user_id', user_id) \
            .ilike('storage_path', '%Granola%Meeting-summaries%')

        if not force_rescan:
            query = query.is_('granola_scanned_at', 'null')

        result = query.execute()
        documents = result.data or []
    except Exception as e:
        logger.error(f"Failed to query Granola documents: {e}")
        raise GranolaScannerError(f"Failed to query documents: {e}")

    if not documents:
        logger.info("No unscanned Granola documents found")
        return {
            'status': 'success',
            'stats': {
                'files_scanned': 0,
                'files_processed': 0,
                'files_skipped': 0,
                'files_failed': 0,
                'opportunities_created': 0,
                'tasks_created': 0,
                'stakeholders_created': 0
            },
            'results': []
        }

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

    for doc in documents:
        stats['files_scanned'] += 1

        result = await scan_document(doc, user_id, client_id, force_rescan)
        results.append({'file': doc.get('filename', 'Unknown'), **result})

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


def get_scan_status(user_id: str) -> Dict[str, Any]:
    """
    Get current scan status for Granola documents in the KB.

    Returns counts of scanned vs unscanned Granola meeting documents.
    """
    try:
        # Count total Granola meeting documents
        total_result = supabase.table('documents') \
            .select('id', count='exact') \
            .eq('user_id', user_id) \
            .ilike('storage_path', '%Granola%Meeting-summaries%') \
            .execute()

        total_files = total_result.count or 0

        # Count scanned documents
        scanned_result = supabase.table('documents') \
            .select('id', count='exact') \
            .eq('user_id', user_id) \
            .ilike('storage_path', '%Granola%Meeting-summaries%') \
            .not_.is_('granola_scanned_at', 'null') \
            .execute()

        scanned_count = scanned_result.count or 0

        return {
            'connected': total_files > 0,
            'vault_path': 'KB (Obsidian sync)',
            'total_files': total_files,
            'scanned_files': scanned_count,
            'pending_files': total_files - scanned_count
        }
    except Exception as e:
        logger.error(f"Failed to get scan status: {e}")
        return {
            'connected': False,
            'vault_path': 'KB (Obsidian sync)',
            'total_files': 0,
            'scanned_files': 0,
            'pending_files': 0,
            'error': str(e)
        }


# Keep old function name for backwards compatibility
async def scan_granola_vault(
    user_id: str,
    client_id: str,
    vault_path: str = "",  # Ignored - uses KB
    force_rescan: bool = False
) -> Dict[str, Any]:
    """
    Backwards-compatible wrapper for scan_granola_documents.
    The vault_path parameter is ignored - scanning now uses documents from the KB.
    """
    return await scan_granola_documents(user_id, client_id, force_rescan)
