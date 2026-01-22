"""
Granola Meeting Scanner Service

Scans synced Granola meeting documents from the KB and extracts:
- AI opportunities (as candidates for review)
- Action items/tasks (as candidates for review)
- Stakeholder mentions (as candidates for review)

Works with documents already synced via Obsidian vault sync.
Extracted items go to candidate tables for user review before becoming real entries.
"""

import os
import re
from datetime import datetime, timezone, date
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple

import yaml
import anthropic
import httpx

from database import get_supabase
from document_processor import search_similar_chunks
from logger_config import get_logger
from services.embeddings import create_embedding

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


def fuzzy_match(str1: str, str2: str) -> float:
    """
    Calculate fuzzy similarity between two strings.
    Returns a score between 0 and 1.
    """
    if not str1 or not str2:
        return 0.0
    # Normalize strings
    s1 = str1.lower().strip()
    s2 = str2.lower().strip()
    return SequenceMatcher(None, s1, s2).ratio()


async def find_matching_opportunity(
    client_id: str,
    extracted_title: str,
    extracted_quote: str = ""
) -> Optional[Dict[str, Any]]:
    """
    Check if extracted opportunity matches an existing one.
    Uses multi-layer matching: fuzzy title match + vector similarity.

    Returns dict with matched_opportunity_id, match_confidence, match_reason
    if match found, otherwise None.
    """
    # Layer 1: Title/project_name fuzzy match
    existing = supabase.table('ai_opportunities') \
        .select('id, title, project_name, description') \
        .eq('client_id', client_id) \
        .execute()

    for opp in existing.data or []:
        # Check title similarity
        title_sim = fuzzy_match(extracted_title, opp.get('title', ''))
        if title_sim > 0.85:
            return {
                'matched_opportunity_id': opp['id'],
                'match_confidence': title_sim,
                'match_reason': f"Title match ({title_sim:.0%}): '{opp['title'][:50]}'"
            }

        # Check project_name similarity
        project_name = opp.get('project_name')
        if project_name:
            proj_sim = fuzzy_match(extracted_title, project_name)
            if proj_sim > 0.85:
                return {
                    'matched_opportunity_id': opp['id'],
                    'match_confidence': proj_sim,
                    'match_reason': f"Project name match ({proj_sim:.0%}): '{project_name[:50]}'"
                }

    # Layer 2: Vector similarity search
    try:
        search_text = extracted_title
        if extracted_quote:
            search_text = f"{extracted_title} {extracted_quote[:200]}"

        # Search existing opportunities by embedding their descriptions
        # Use document chunks that may have been linked to opportunities
        chunks = search_similar_chunks(
            query=search_text,
            client_id=client_id,
            limit=5,
            include_conversations=False,
            min_similarity=0.85
        )

        # Check if any chunks are from documents linked to opportunities
        for chunk in chunks:
            doc_id = chunk.get('document_id')
            if not doc_id:
                continue

            # Check if this document is a source for any opportunity
            linked_opp = supabase.table('ai_opportunities') \
                .select('id, title') \
                .eq('source_id', doc_id) \
                .execute()

            if linked_opp.data:
                opp = linked_opp.data[0]
                return {
                    'matched_opportunity_id': opp['id'],
                    'match_confidence': chunk.get('similarity', 0.85),
                    'match_reason': f"Similar content to '{opp['title'][:50]}'"
                }

    except Exception as e:
        logger.warning(f"Vector search for deduplication failed: {e}")

    return None


async def find_matching_task(
    client_id: str,
    extracted_title: str
) -> Optional[Dict[str, Any]]:
    """
    Check if extracted task matches an existing one.
    Uses fuzzy title matching.

    Returns dict with matched_task_id and match_confidence if found.
    """
    existing = supabase.table('project_tasks') \
        .select('id, title') \
        .eq('client_id', client_id) \
        .neq('status', 'completed') \
        .execute()

    for task in existing.data or []:
        title_sim = fuzzy_match(extracted_title, task.get('title', ''))
        if title_sim > 0.85:
            return {
                'matched_task_id': task['id'],
                'match_confidence': title_sim,
                'match_reason': f"Title match ({title_sim:.0%}): '{task['title'][:50]}'"
            }

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
   - description: What the opportunity is (keep it concise, under 200 chars)
   - department: Which department (Legal, HR, Finance, IT, Engineering, Sales, Marketing, Operations, etc.)
   - potential_impact: 1-5 score (5 = transformative)
   - effort_estimate: 1-5 score (5 = very complex)
   - strategic_alignment: 1-5 score (5 = highly strategic)
   - readiness: 1-5 score (5 = champion identified and ready to start)
   - quote: A relevant quote from the content supporting this opportunity

2. **tasks** - Action items, follow-ups, commitments:
   - title: Short task title
   - description: What needs to be done with context
   - assignee_name: Who is responsible (if mentioned)
   - due_date: When it's due (if mentioned, in YYYY-MM-DD format)
   - team: Which team/department this task belongs to (if clear from context)

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

        # Update document scan timestamp (for all extraction types)
        now = datetime.now(timezone.utc).isoformat()
        supabase.table('documents').update({
            'granola_scanned_at': now,
            'opportunities_scanned_at': now,
            'tasks_scanned_at': now,
            'stakeholders_scanned_at': now,
            'updated_at': now
        }).eq('id', document_id).execute()

        # Store extracted opportunities as candidates
        opportunities_created = 0
        for opp in extracted.get('opportunities', []):
            try:
                opp_title = opp.get('description', '')[:200]
                if not opp_title or len(opp_title) < 10:
                    continue

                # Check for duplicate candidate using RPC (avoids PostgREST ilike issues)
                try:
                    existing_cand = supabase.rpc('check_duplicate_opportunity_candidate', {
                        'p_client_id': client_id,
                        'p_title_prefix': opp_title[:50]
                    }).execute()
                except Exception as rpc_err:
                    logger.warning(f"RPC check_duplicate_opportunity_candidate failed: {rpc_err}")
                    existing_cand = type('obj', (object,), {'data': []})()

                if existing_cand.data:
                    logger.debug(f"Skipping duplicate opportunity candidate: {opp_title[:50]}")
                    continue

                # Check for matching existing opportunity (deduplication)
                match = await find_matching_opportunity(
                    client_id,
                    opp_title,
                    opp.get('quote', '')
                )

                candidate_data = {
                    'client_id': client_id,
                    'title': opp_title,
                    'description': opp.get('description', ''),
                    'department': opp.get('department', 'General'),
                    'source_document_id': document_id,
                    'source_document_name': title,
                    'source_text': opp.get('quote', ''),
                    'suggested_roi_potential': opp.get('potential_impact', 3),
                    'suggested_effort': opp.get('effort_estimate', 3),
                    'suggested_alignment': opp.get('strategic_alignment', 3),
                    'suggested_readiness': opp.get('readiness', 3),
                    'potential_impact': opp.get('description', ''),
                    'status': 'pending',
                    'confidence': 'medium',
                    'created_at': now
                }

                # Add deduplication info if match found
                if match:
                    candidate_data['matched_opportunity_id'] = match['matched_opportunity_id']
                    candidate_data['match_confidence'] = match['match_confidence']
                    candidate_data['match_reason'] = match['match_reason']
                    logger.info(f"Potential duplicate found: {match['match_reason']}")

                supabase.table('opportunity_candidates').insert(candidate_data).execute()
                opportunities_created += 1

            except Exception as e:
                logger.warning(f"Failed to create opportunity candidate: {e}")

        # Store extracted tasks as candidates
        tasks_created = 0
        for task in extracted.get('tasks', []):
            try:
                task_title = task.get('title', '')[:200]
                if not task_title or len(task_title) < 5:
                    continue

                # Check for duplicate candidate using RPC (avoids PostgREST ilike issues)
                try:
                    existing_cand = supabase.rpc('check_duplicate_task_candidate', {
                        'p_client_id': client_id,
                        'p_title_prefix': task_title[:50]
                    }).execute()
                except Exception as rpc_err:
                    logger.warning(f"RPC check_duplicate_task_candidate failed: {rpc_err}")
                    existing_cand = type('obj', (object,), {'data': []})()

                if existing_cand.data:
                    logger.debug(f"Skipping duplicate task candidate: {task_title[:50]}")
                    continue

                # Check for matching existing task
                task_match = await find_matching_task(client_id, task_title)

                candidate_data = {
                    'client_id': client_id,
                    'title': task_title,
                    'description': task.get('description', ''),
                    'assignee_name': task.get('assignee_name'),
                    'suggested_due_date': task.get('due_date'),
                    'team': task.get('team'),
                    'meeting_context': f"From meeting: {title}",
                    'document_date': meeting_date.isoformat() if meeting_date else None,
                    'source_document_id': document_id,
                    'source_document_name': title,
                    'source_text': task.get('description', ''),
                    'status': 'pending',
                    'confidence': 'medium',
                    'suggested_priority': 3,
                    'created_at': now
                }

                # Note: task_candidates doesn't have match fields yet
                # but we can log it for awareness
                if task_match:
                    logger.info(f"Similar task exists: {task_match['match_reason']}")
                    # Skip creating if very similar task exists
                    continue

                supabase.table('task_candidates').insert(candidate_data).execute()
                tasks_created += 1

            except Exception as e:
                logger.warning(f"Failed to create task candidate: {e}")

        # Store extracted stakeholders (as candidates for review)
        stakeholders_created = 0
        for sh in extracted.get('stakeholders', []):
            try:
                name = sh.get('name', '').strip()
                if not name or len(name) < 2:
                    continue

                # Check for existing stakeholder using RPC (avoids PostgREST ilike issues)
                try:
                    existing_sh = supabase.rpc('check_existing_stakeholder', {
                        'p_client_id': client_id,
                        'p_name': name
                    }).execute()
                except Exception as rpc_err:
                    logger.warning(f"RPC check_existing_stakeholder failed: {rpc_err}")
                    existing_sh = type('obj', (object,), {'data': []})()

                if not existing_sh.data:
                    # Check for existing candidate using RPC
                    try:
                        existing_cand = supabase.rpc('check_existing_stakeholder_candidate', {
                            'p_client_id': client_id,
                            'p_name': name
                        }).execute()
                    except Exception as rpc_err:
                        logger.warning(f"RPC check_existing_stakeholder_candidate failed: {rpc_err}")
                        existing_cand = type('obj', (object,), {'data': []})()

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

    Finds documents with obsidian_file_path containing 'Granola/Meeting-summaries'
    and extracts opportunities, tasks, and stakeholders.

    Args:
        user_id: User ID
        client_id: Client ID
        force_rescan: Re-process already scanned files

    Returns:
        Scan results with stats
    """
    logger.info("Scanning Granola documents from KB")

    # Find Granola meeting documents in KB using RPC (avoids PostgREST ilike issues)
    try:
        result = supabase.rpc('get_granola_documents_to_scan', {
            'p_user_id': user_id,
            'p_force_rescan': force_rescan
        }).execute()
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
        # Use RPC function to get counts (avoids PostgREST ilike issues)
        result = supabase.rpc('get_granola_scan_status', {'p_user_id': user_id}).execute()

        if result.data and len(result.data) > 0:
            total_files = result.data[0].get('total_files', 0) or 0
            scanned_count = result.data[0].get('scanned_files', 0) or 0
        else:
            total_files = 0
            scanned_count = 0

        return {
            'connected': total_files > 0,
            'vault_path': 'KB (Obsidian sync)',
            'total_files': total_files,
            'scanned_files': scanned_count,
            'pending_files': total_files - scanned_count
        }
    except Exception as e:
        logger.error(f"Failed to get scan status: {e}")
        # Truncate error message to avoid displaying raw HTML/long errors
        error_msg = str(e)
        if len(error_msg) > 200:
            error_msg = "Database connection error. Please try again."
        return {
            'connected': False,
            'vault_path': 'KB (Obsidian sync)',
            'total_files': 0,
            'scanned_files': 0,
            'pending_files': 0,
            'error': error_msg
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
