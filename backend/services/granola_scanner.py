"""
Meeting Scanner Service

Scans meeting documents from the KB and extracts:
- AI opportunities (as candidates for review)
- Action items/tasks (as candidates for review)
- Stakeholder mentions (as candidates for review)

Uses heuristics to identify meeting-like documents (transcripts, summaries, etc.)
regardless of their source folder. Prioritizes documents with clear meeting indicators:
- HIGH priority: Granola folder, filenames with "transcript", "meeting", "1:1", etc.
- MEDIUM priority: Documents with meeting-style content sections
- LOW priority: Articles, slides, templates, etc. (marked as scanned but not processed)
- SKIP: Excluded patterns (specific people's meetings, training docs, etc.)

Works with documents already synced via Obsidian vault sync.
Extracted items go to candidate tables for user review before becoming real entries.
"""

import os
import re
import uuid
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
from services.entity_deduplicator import EntityDeduplicator, DeduplicationConfig

logger = get_logger(__name__)

# Get Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
supabase = get_supabase()

# Frontmatter pattern
FRONTMATTER_PATTERN = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)

# Pattern to extract date from filename like "2025-07-27.md" or "...-2026-01-06_09-12-32.md"
FILENAME_DATE_PATTERN = re.compile(r'(\d{4}-\d{2}-\d{2})')

# Pattern to identify Granola meeting documents in storage paths
# Supports both Meeting-summaries and Transcripts folders
GRANOLA_PATH_PATTERN = re.compile(r'Granola[/\\](Meeting-summaries|Transcripts)[/\\]', re.IGNORECASE)

# =============================================================================
# DOCUMENT CLASSIFICATION HEURISTICS
# =============================================================================
# These heuristics help identify documents likely to contain tasks, opportunities,
# and stakeholders - regardless of their source folder.

# HIGH priority filename patterns (likely meetings/transcripts)
HIGH_PRIORITY_FILENAME_PATTERNS = [
    re.compile(r'transcript', re.IGNORECASE),
    re.compile(r'meeting', re.IGNORECASE),
    re.compile(r'summary', re.IGNORECASE),
    re.compile(r'1[:\-_]1|one[:\-_]one', re.IGNORECASE),  # 1:1, 1-1, one-on-one
    re.compile(r'sync\b', re.IGNORECASE),
    re.compile(r'standup|stand[:\-_]up', re.IGNORECASE),
    re.compile(r'retro(spective)?', re.IGNORECASE),
    re.compile(r'all[:\-_]?hands', re.IGNORECASE),
    re.compile(r'kickoff|kick[:\-_]off', re.IGNORECASE),
    re.compile(r'interview', re.IGNORECASE),
    re.compile(r'workshop', re.IGNORECASE),
    re.compile(r'brainstorm', re.IGNORECASE),
    re.compile(r'planning\s+session', re.IGNORECASE),
    re.compile(r'review\s+meeting', re.IGNORECASE),
    re.compile(r'strategy\s+session', re.IGNORECASE),
]

# HIGH priority content patterns (meeting indicators in document body)
HIGH_PRIORITY_CONTENT_PATTERNS = [
    re.compile(r'^#+\s*(participants?|attendees?)', re.IGNORECASE | re.MULTILINE),
    re.compile(r'^#+\s*action\s+items?', re.IGNORECASE | re.MULTILINE),
    re.compile(r'^#+\s*next\s+steps?', re.IGNORECASE | re.MULTILINE),
    re.compile(r'^#+\s*decisions?', re.IGNORECASE | re.MULTILINE),
    re.compile(r'^#+\s*agenda', re.IGNORECASE | re.MULTILINE),
    re.compile(r'^#+\s*summary', re.IGNORECASE | re.MULTILINE),
    re.compile(r'^#+\s*key\s+(points?|takeaways?)', re.IGNORECASE | re.MULTILINE),
    re.compile(r'\*\*(participants?|attendees?):\*\*', re.IGNORECASE),
    re.compile(r'Granola\s+(ID|Notes)', re.IGNORECASE),  # Granola-specific
    re.compile(r'\[speaker\s*\d*\]', re.IGNORECASE),  # Transcript speaker markers
]

# LOW priority filename patterns (unlikely to have tasks/opportunities)
LOW_PRIORITY_FILENAME_PATTERNS = [
    re.compile(r'article', re.IGNORECASE),
    re.compile(r'reference', re.IGNORECASE),
    re.compile(r'guide\b', re.IGNORECASE),
    re.compile(r'slides?|deck', re.IGNORECASE),
    re.compile(r'presentation', re.IGNORECASE),
    re.compile(r'template', re.IGNORECASE),
    re.compile(r'readme', re.IGNORECASE),
    re.compile(r'changelog', re.IGNORECASE),
    re.compile(r'documentation', re.IGNORECASE),
    re.compile(r'tutorial', re.IGNORECASE),
    re.compile(r'example', re.IGNORECASE),
    re.compile(r'sample', re.IGNORECASE),
    re.compile(r'test[:\-_]', re.IGNORECASE),  # test files but not "testing meeting"
    re.compile(r'backup', re.IGNORECASE),
    re.compile(r'archive', re.IGNORECASE),
    re.compile(r'\.excalidraw', re.IGNORECASE),
]

# LOW priority path patterns (folders unlikely to have meeting content)
LOW_PRIORITY_PATH_PATTERNS = [
    re.compile(r'Articles?[/\\]', re.IGNORECASE),
    re.compile(r'Reference[/\\]', re.IGNORECASE),
    re.compile(r'Templates?[/\\]', re.IGNORECASE),
    re.compile(r'Archive[/\\]', re.IGNORECASE),
    re.compile(r'\.claude[/\\]', re.IGNORECASE),
    re.compile(r'node_modules[/\\]', re.IGNORECASE),
]


def classify_document_priority(
    filename: str,
    obsidian_path: Optional[str] = None,
    content: Optional[str] = None
) -> str:
    """
    Classify a document's priority for task/opportunity/stakeholder extraction.

    Returns:
        'high' - Likely a meeting transcript/summary, should be scanned
        'medium' - Unclear, may contain relevant content
        'low' - Unlikely to contain tasks/opportunities (articles, slides, etc.)
        'skip' - Should be excluded entirely
    """
    path_to_check = obsidian_path or filename or ''
    filename_lower = (filename or '').lower()

    # Always HIGH priority: Granola folder (known meeting source)
    if GRANOLA_PATH_PATTERN.search(path_to_check):
        return 'high'

    # Check exclusion patterns first
    for pattern in EXCLUDE_PATTERNS:
        if pattern.search(filename) or pattern.search(path_to_check):
            return 'skip'

    # Check LOW priority path patterns
    for pattern in LOW_PRIORITY_PATH_PATTERNS:
        if pattern.search(path_to_check):
            return 'low'

    # Check LOW priority filename patterns
    for pattern in LOW_PRIORITY_FILENAME_PATTERNS:
        if pattern.search(filename):
            return 'low'

    # Check HIGH priority filename patterns
    for pattern in HIGH_PRIORITY_FILENAME_PATTERNS:
        if pattern.search(filename):
            return 'high'

    # If content is available, check content patterns
    if content:
        content_sample = content[:3000]  # Check first 3000 chars for efficiency
        high_matches = sum(1 for p in HIGH_PRIORITY_CONTENT_PATTERNS if p.search(content_sample))
        if high_matches >= 2:  # Multiple meeting indicators = high priority
            return 'high'
        elif high_matches == 1:
            return 'medium'

    # Default to medium - will be processed but not prioritized
    return 'medium'


def should_scan_document(doc: Dict[str, Any], content: Optional[str] = None) -> Tuple[bool, str]:
    """
    Determine if a document should be scanned for tasks/opportunities/stakeholders.

    Returns:
        (should_scan, reason) tuple
    """
    filename = doc.get('filename', '')
    obsidian_path = doc.get('obsidian_file_path', '')

    priority = classify_document_priority(filename, obsidian_path, content)

    if priority == 'skip':
        return False, 'excluded_by_pattern'
    elif priority == 'low':
        return False, 'low_priority_content'
    elif priority in ('high', 'medium'):
        return True, f'{priority}_priority'

    return False, 'unknown'


# Patterns to EXCLUDE from scanning (case-insensitive)
# These documents are not relevant for opportunity/task/stakeholder extraction
EXCLUDE_PATTERNS = [
    # Specific people's meetings (not Charlie's direct work)
    re.compile(r'Paige', re.IGNORECASE),
    re.compile(r'Vanessa', re.IGNORECASE),
    # People from before Jan 5, 2026 (pre-role)
    re.compile(r'Rudy', re.IGNORECASE),
    re.compile(r'Elizabeth', re.IGNORECASE),
    # Programs/cohorts
    re.compile(r'AI[\s_-]*BuildLab', re.IGNORECASE),
    re.compile(r'Foundations', re.IGNORECASE),
    re.compile(r'Residents', re.IGNORECASE),
    # Onboarding/training docs (generic HR content)
    re.compile(r'New Employee Orient', re.IGNORECASE),
    re.compile(r'IT New Employee', re.IGNORECASE),
    re.compile(r'^Training:', re.IGNORECASE),
    # Casual/non-work meetings
    re.compile(r'Lunch break', re.IGNORECASE),
]

# The user whose tasks we want to extract
TASK_OWNER_NAME = "Charlie"

# Default cutoff date - meetings before this date are not scanned (pre-role)
DEFAULT_SINCE_DATE = date(2026, 1, 5)

# Minimum total score to surface an opportunity (Tier 1 only)
# Scoring: roi_potential + implementation_effort + strategic_alignment + stakeholder_readiness
# Each dimension is 1-5, total max 20
# Tier 1: 17-20, Tier 2: 14-16, Tier 3: 11-13, Tier 4: <11
MIN_OPPORTUNITY_TOTAL_SCORE = 17  # Tier 1 only - requires average of 4.25 across all dimensions


def calculate_opportunity_total_score(opp: Dict[str, Any]) -> int:
    """
    Calculate total score using the same 4-dimension rubric as ai_opportunities.

    Dimensions (1-5 scale each, max 20 total):
    - roi_potential (potential_impact in extraction)
    - implementation_effort (effort_estimate in extraction, higher = easier)
    - strategic_alignment
    - stakeholder_readiness (readiness in extraction)

    Returns total score 4-20.
    """
    roi = opp.get('potential_impact', 3)
    effort = opp.get('effort_estimate', 3)
    alignment = opp.get('strategic_alignment', 3)
    readiness = opp.get('readiness', 3)

    return roi + effort + alignment + readiness

# Key leaders whose task assignments matter (tasks FROM these people are important)
KEY_LEADERS = ['chris baumgartner', 'chris', 'mikki', 'michael stratton']

# Assignees that indicate "not Charlie's task" - skip these
EXCLUDED_ASSIGNEES = [
    'all new hires', 'new hires',
    'it team', 'workplace team', 'team', 'the team',
    'unknown', 'tbd', 'n/a',
    # Specific individuals (not Charlie, not key leaders)
    'paige', 'vanessa', 'ashley', 'wade', 'tyler',
    'elizabeth', 'mickey', 'sara', 'sarah', 'joe',
    'ava', 'danny', 'hannah', 'teresa', 'simone',
]


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


def parse_date_from_filename(filename: str) -> Optional[date]:
    """
    Extract meeting date from filename.
    Supports formats like:
    - 2025-07-27.md
    - Chris __ Charlie-transcript-2026-01-06_09-12-32.md
    """
    if not filename:
        return None
    match = FILENAME_DATE_PATTERN.search(filename)
    if match:
        try:
            return datetime.strptime(match.group(1), '%Y-%m-%d').date()
        except ValueError:
            return None
    return None


def get_document_meeting_date(doc: Dict[str, Any]) -> Optional[date]:
    """
    Determine the meeting date for a document using multiple methods.
    Priority order:
    1. original_date field (if exists and set)
    2. Date parsed from filename (most reliable for Granola)
    3. uploaded_at as fallback
    """
    # Method 1: Check original_date field
    original_date = doc.get('original_date')
    if original_date:
        parsed = parse_date_from_iso(original_date)
        if parsed:
            return parsed

    # Method 2: Parse from filename (works for Granola naming convention)
    filename = doc.get('filename', '')
    filename_date = parse_date_from_filename(filename)
    if filename_date:
        return filename_date

    # Method 3: Check obsidian_file_path for date
    obsidian_path = doc.get('obsidian_file_path', '')
    if obsidian_path:
        path_date = parse_date_from_filename(obsidian_path)
        if path_date:
            return path_date

    # Method 4: Fall back to uploaded_at (sync date, not ideal but better than nothing)
    uploaded_at = doc.get('uploaded_at')
    if uploaded_at:
        return parse_date_from_iso(uploaded_at)

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
    if not storage_url:
        logger.warning("No storage URL provided")
        return None

    logger.info(f"Fetching document from: {storage_url[:100]}...")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(storage_url, timeout=30.0)
            if response.status_code == 200:
                content = response.text
                logger.info(f"Successfully fetched {len(content)} chars")
                return content
            else:
                logger.warning(f"Failed to fetch document: HTTP {response.status_code} - {response.text[:200]}")
                return None
    except Exception as e:
        logger.error(f"Error fetching document content: {type(e).__name__}: {e}")
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

    prompt = f"""Analyze this meeting summary and extract ONLY TIER-1 STRATEGIC items. Be EXTREMELY selective.

Meeting: {title}
Date: {meeting_date.isoformat() if meeting_date else 'Unknown'}

Content:
{content}

Extract the following in JSON format - ONLY include the TOP strategic items (expect 0-2 per meeting):

1. **opportunities** - ONLY transformative AI/automation initiatives:
   Extract ONLY if ALL of these are true:
   - Executive sponsorship explicitly mentioned
   - Clear, quantifiable business case ($X savings, Y% improvement)
   - Directly tied to company strategic priorities
   - Has identified champion or owner

   SCORING RUBRIC (be harsh - most items should score 2-3):
   - potential_impact: 5=company-wide transformation, 4=department transformation, 3=team improvement, 2=individual productivity, 1=nice-to-have
   - effort_estimate: 5=plug-and-play, 4=weeks, 3=months, 2=6+ months, 1=multi-year
   - strategic_alignment: 5=CEO priority, 4=VP priority, 3=director priority, 2=manager interest, 1=grassroots idea
   - readiness: 5=budget approved + team ready, 4=budget likely, 3=exploring, 2=early discussion, 1=just an idea

   ONLY extract if total score >= 17 (average 4.25+ across all dimensions)

   For each opportunity:
   - description: What the opportunity is (concise, under 200 chars)
   - department: Which department
   - potential_impact: 1-5 score (use rubric above - be harsh)
   - effort_estimate: 1-5 score (use rubric above - be harsh)
   - strategic_alignment: 1-5 score (use rubric above - be harsh)
   - readiness: 1-5 score (use rubric above - be harsh)
   - quote: Supporting quote from content

2. **tasks** - ONLY tasks assigned BY or TO key leaders:
   Extract ONLY if:
   - Assigned BY Chris Baumgartner, Mikki, or Michael Stratton (leadership direction)
   - OR Charlie explicitly commits to something strategic (not routine)
   - Has clear business impact or deadline

   DO NOT extract:
   - Routine follow-ups or admin tasks
   - Tasks for other people
   - Vague action items without clear ownership

   For each STRATEGIC task:
   - title: Short task title
   - description: What needs to be done with context
   - assignee_name: Who assigned it or "Charlie" if self-assigned
   - due_date: When due (YYYY-MM-DD) if mentioned
   - team: Which team/department

3. **stakeholders** - Key decision-makers you need to actively manage:
   Extract ONLY if:
   - They are a Manager, VP, Director, or executive with decision authority
   - They expressed strong opinions (support OR concern) about AI initiatives
   - You need to actively engage them for project success

   DO NOT extract:
   - Individual contributors without decision authority
   - People just mentioned in passing
   - Anyone without clear stakes in outcomes

   For each KEY stakeholder:
   - name: Person's name
   - role: Their title (REQUIRED)
   - department: Their department
   - sentiment: positive/neutral/skeptical
   - concerns: Specific concerns (array)
   - interests: Specific interests (array)

Return ONLY valid JSON:
{{
  "opportunities": [...],
  "tasks": [...],
  "stakeholders": [...]
}}

IMPORTANT: It's better to return empty arrays than extract low-value items. Only surface what truly matters strategically."""

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
    force_rescan: bool = False,
    deduplicator: Optional[EntityDeduplicator] = None,
    batch_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Scan a single document from the KB for opportunities, tasks, and stakeholders.

    Args:
        document: Document record from database
        user_id: User ID
        client_id: Client ID
        force_rescan: Re-process already scanned files
        deduplicator: Optional EntityDeduplicator instance for within-batch dedup
        batch_id: Batch ID for within-batch deduplication

    Returns scan result with status and extracted data.
    """
    document_id = document['id']
    filename = document.get('filename', 'Unknown')
    storage_url = document.get('storage_url')
    obsidian_path = document.get('obsidian_file_path', '')

    # Create deduplicator if not provided (for backwards compatibility)
    if deduplicator is None:
        deduplicator = EntityDeduplicator(supabase)
    if batch_id is None:
        batch_id = str(uuid.uuid4())

    logger.info(f"Scanning document: {filename}")

    # Check exclusion patterns (AI BuildLab, Paige, etc.)
    for pattern in EXCLUDE_PATTERNS:
        if pattern.search(filename) or pattern.search(obsidian_path):
            logger.debug(f"Excluded by pattern: {filename}")
            # Mark as scanned so we don't check again
            now = datetime.now(timezone.utc).isoformat()
            supabase.table('documents').update({
                'granola_scanned_at': now,
            }).eq('id', document_id).execute()
            return {'status': 'skipped', 'reason': 'excluded_pattern', 'document_id': document_id}

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

        # Store extracted opportunities as candidates (only Tier 1-2: total score >= 14)
        opportunities_created = 0
        raw_opportunities = extracted.get('opportunities', [])

        # Filter to opportunities meeting minimum score threshold
        qualified_opps = []
        for opp in raw_opportunities:
            opp_title = opp.get('description', '')[:200]
            if not opp_title or len(opp_title) < 10:
                continue
            total_score = calculate_opportunity_total_score(opp)
            if total_score >= MIN_OPPORTUNITY_TOTAL_SCORE:
                qualified_opps.append((total_score, opp))
            else:
                logger.debug(f"Skipping low-score opportunity: {opp_title[:50]} (score={total_score}, min={MIN_OPPORTUNITY_TOTAL_SCORE})")

        logger.info(f"Extracted {len(raw_opportunities)} opportunities, {len(qualified_opps)} meet Tier 1-2 threshold (score >= {MIN_OPPORTUNITY_TOTAL_SCORE})")

        for total_score, opp in qualified_opps:
            try:
                opp_title = opp.get('description', '')[:200]

                # Use unified deduplicator for all checks
                opp_match = await deduplicator.deduplicate_opportunity(
                    client_id=client_id,
                    title=opp_title,
                    quote=opp.get('quote', ''),
                    batch_id=batch_id
                )

                # Block on rejected or batch duplicates
                if opp_match and opp_match.should_block(deduplicator.config):
                    logger.debug(f"Skipping opportunity ({opp_match.match_type}): {opp_match.match_reason}")
                    continue

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

                # Track match info for pending/existing matches (don't block, just track)
                if opp_match:
                    if opp_match.match_type == 'existing':
                        candidate_data['matched_opportunity_id'] = opp_match.matched_id
                    elif opp_match.match_type == 'pending':
                        candidate_data['matched_candidate_id'] = opp_match.matched_id
                    candidate_data['match_confidence'] = opp_match.match_confidence
                    candidate_data['match_reason'] = opp_match.match_reason
                    logger.info(f"Potential duplicate found: {opp_match.match_reason}")

                result = supabase.table('opportunity_candidates').insert(candidate_data).execute()
                opportunities_created += 1

                # Update batch cache with actual ID
                if result.data:
                    deduplicator.update_batch_cache_id('opportunity', batch_id, opp_title, result.data[0]['id'])

            except Exception as e:
                logger.warning(f"Failed to create opportunity candidate: {e}")

        # Store extracted tasks as candidates (only for Charlie)
        tasks_created = 0
        for task in extracted.get('tasks', []):
            try:
                task_title = task.get('title', '')[:200]
                if not task_title or len(task_title) < 5:
                    continue

                # Skip tasks assigned to others (not Charlie or unassigned/first-person)
                assignee_raw = task.get('assignee_name') or ''
                assignee = assignee_raw.lower().strip() if assignee_raw else ''

                # Check against excluded assignees list
                if assignee in EXCLUDED_ASSIGNEES:
                    logger.debug(f"Skipping task - excluded assignee: {assignee} - {task_title[:50]}")
                    continue

                # Also skip if assignee is specified but NOT Charlie (catch-all for names not in list)
                if assignee and assignee not in ['charlie', 'me', 'i', 'myself', '']:
                    logger.debug(f"Skipping task assigned to someone else: {assignee} - {task_title[:50]}")
                    continue

                # Generate embedding for semantic matching
                task_desc = task.get('description', '')
                try:
                    task_embedding = deduplicator.generate_task_embedding(task_title, task_desc)
                except Exception as emb_err:
                    logger.warning(f"Failed to generate task embedding: {emb_err}")
                    task_embedding = None

                # Use unified deduplicator for all checks
                task_match = await deduplicator.deduplicate_task(
                    client_id=client_id,
                    title=task_title,
                    description=task_desc,
                    batch_id=batch_id,
                    embedding=task_embedding
                )

                # Block on rejected or batch duplicates
                if task_match and task_match.should_block(deduplicator.config):
                    logger.debug(f"Skipping task ({task_match.match_type}): {task_match.match_reason}")
                    continue

                candidate_data = {
                    'client_id': client_id,
                    'title': task_title,
                    'description': task_desc,
                    'assignee_name': task.get('assignee_name'),
                    'suggested_due_date': task.get('due_date'),
                    'team': task.get('team'),
                    'meeting_context': f"From meeting: {title}",
                    'document_date': meeting_date.isoformat() if meeting_date else None,
                    'source_document_id': document_id,
                    'source_document_name': title,
                    'source_text': task_desc,
                    'status': 'pending',
                    'confidence': 'medium',
                    'suggested_priority': 3,
                    'created_at': now,
                    # Add embedding for future semantic matching
                    'embedding': task_embedding,
                    'embedding_status': 'completed' if task_embedding else 'pending'
                }

                # Track match info for pending/existing matches (don't block, just track)
                if task_match:
                    if task_match.match_type == 'existing':
                        candidate_data['matched_task_id'] = task_match.matched_id
                    elif task_match.match_type == 'pending':
                        candidate_data['matched_candidate_id'] = task_match.matched_id
                    candidate_data['match_confidence'] = task_match.match_confidence
                    candidate_data['match_reason'] = task_match.match_reason
                    logger.info(f"Potential task duplicate found: {task_match.match_reason}")

                result = supabase.table('task_candidates').insert(candidate_data).execute()
                tasks_created += 1

                # Update batch cache with actual ID
                if result.data:
                    deduplicator.update_batch_cache_id('task', batch_id, task_title, result.data[0]['id'])

            except Exception as e:
                logger.warning(f"Failed to create task candidate: {e}")

        # Store extracted stakeholders (as candidates for review)
        stakeholders_created = 0
        for sh in extracted.get('stakeholders', []):
            try:
                name = sh.get('name', '').strip()
                if not name or len(name) < 2:
                    continue

                # Additional validation: require role for stakeholder extraction
                role = sh.get('role')
                concerns = sh.get('concerns', [])
                interests = sh.get('interests', [])

                # Skip if no role AND no concerns AND no interests (just a name mention)
                if not role and not concerns and not interests:
                    logger.debug(f"Skipping stakeholder with no context: {name}")
                    continue

                # Use unified deduplicator for all checks
                sh_match = await deduplicator.deduplicate_stakeholder(
                    client_id=client_id,
                    name=name,
                    role=role or '',
                    department=sh.get('department', ''),
                    organization=sh.get('organization', ''),
                    email=sh.get('email', ''),
                    batch_id=batch_id
                )

                # Block on rejected or batch duplicates
                if sh_match and sh_match.should_block(deduplicator.config):
                    logger.debug(f"Skipping stakeholder ({sh_match.match_type}): {sh_match.match_reason}")
                    continue

                candidate_data = {
                    'client_id': client_id,
                    'name': name,
                    'role': role,
                    'department': sh.get('department'),
                    'initial_sentiment': sh.get('sentiment', 'neutral'),
                    'key_concerns': concerns,
                    'interests': interests,
                    'source_document_id': document_id,
                    'source_document_name': title,
                    'status': 'pending',
                    'confidence': 'medium',
                    'created_at': now
                }

                # Track match info for pending/existing matches (don't block, just track)
                if sh_match:
                    if sh_match.match_type == 'existing':
                        candidate_data['potential_match_stakeholder_id'] = sh_match.matched_id
                    elif sh_match.match_type == 'pending':
                        candidate_data['matched_candidate_id'] = sh_match.matched_id
                    candidate_data['match_confidence'] = sh_match.match_confidence
                    candidate_data['match_reason'] = sh_match.match_reason
                    logger.info(f"Potential stakeholder duplicate found: {sh_match.match_reason}")

                result = supabase.table('stakeholder_candidates').insert(candidate_data).execute()
                stakeholders_created += 1

                # Update batch cache with actual ID
                if result.data:
                    deduplicator.update_batch_cache_id('stakeholder', batch_id, name, result.data[0]['id'])

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


async def scan_meeting_documents(
    user_id: str,
    client_id: str,
    force_rescan: bool = False,
    since_date: Optional[date] = None,
    include_medium_priority: bool = False
) -> Dict[str, Any]:
    """
    Scan meeting documents from the KB for tasks, opportunities, and stakeholders.

    Uses heuristics to identify meeting-like documents (transcripts, summaries, etc.)
    regardless of their source folder. Prioritizes documents with clear meeting indicators.

    Args:
        user_id: User ID
        client_id: Client ID
        force_rescan: Re-process already scanned files
        since_date: Only scan documents created on or after this date (defaults to Jan 5, 2026)
        include_medium_priority: Also scan medium-priority documents (default: only high priority)

    Returns:
        Scan results with stats
    """
    # Apply default cutoff date if not specified
    effective_since_date = since_date if since_date is not None else DEFAULT_SINCE_DATE
    logger.info(f"Scanning meeting documents from KB (since {effective_since_date})")

    # Find meeting-like documents in KB using heuristics
    try:
        result = supabase.table('documents') \
            .select('id, filename, title, original_date, storage_url, granola_scanned_at, obsidian_file_path, uploaded_at') \
            .eq('user_id', user_id) \
            .limit(2000) \
            .execute()

        all_docs = result.data or []

        # Classify documents by priority using heuristics
        meeting_docs = []
        skipped_low = 0
        skipped_excluded = 0

        for doc in all_docs:
            filename = doc.get('filename', '')
            obsidian_path = doc.get('obsidian_file_path', '')

            priority = classify_document_priority(filename, obsidian_path)

            if priority == 'skip':
                skipped_excluded += 1
                continue
            elif priority == 'low':
                skipped_low += 1
                # Mark low-priority docs as scanned so they don't appear as pending
                if not doc.get('granola_scanned_at'):
                    try:
                        supabase.table('documents').update({
                            'granola_scanned_at': datetime.now(timezone.utc).isoformat()
                        }).eq('id', doc['id']).execute()
                    except Exception:
                        pass  # Non-critical, continue
                continue
            elif priority == 'high' or (priority == 'medium' and include_medium_priority):
                meeting_docs.append(doc)

        logger.info(f"Document classification: {len(meeting_docs)} meeting docs, {skipped_low} low priority, {skipped_excluded} excluded")

        # Filter by already scanned (unless force_rescan)
        if not force_rescan:
            meeting_docs = [d for d in meeting_docs if not d.get('granola_scanned_at')]

        # Filter by date (always applies - uses default cutoff if not specified)
        original_count = len(meeting_docs)
        documents = []
        for doc in meeting_docs:
            # Use get_document_meeting_date for comprehensive date detection
            doc_date = get_document_meeting_date(doc)
            if doc_date and doc_date >= effective_since_date:
                documents.append(doc)
            elif not doc_date:
                # Skip docs without any detectable date (safer than including old docs)
                logger.debug(f"Skipping doc with no date: {doc.get('filename', 'Unknown')[:50]}")
        logger.info(f"Date filter: {original_count} -> {len(documents)} documents (since {effective_since_date})")
    except Exception as e:
        logger.error(f"Failed to query meeting documents: {e}")
        raise GranolaScannerError(f"Failed to query documents: {e}")

    if not documents:
        logger.info("No unscanned meeting documents found")
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

    # Create shared deduplicator with batch ID for within-batch dedup across all documents
    deduplicator = EntityDeduplicator(supabase)
    batch_id = str(uuid.uuid4())

    for doc in documents:
        stats['files_scanned'] += 1

        result = await scan_document(
            doc, user_id, client_id, force_rescan,
            deduplicator=deduplicator,
            batch_id=batch_id
        )
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

    # Clear batch cache after all documents processed
    deduplicator.clear_batch_cache()

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


def get_scan_status(user_id: str, since_date: Optional[date] = None) -> Dict[str, Any]:
    """
    Get current scan status for meeting documents in the KB.

    Uses heuristics to identify meeting-like documents and returns counts
    of scanned vs unscanned. Defaults to counting only documents from
    Jan 5, 2026 onwards (post role-start).
    """
    # Apply default cutoff date if not specified
    effective_since_date = since_date if since_date is not None else DEFAULT_SINCE_DATE

    try:
        # Query documents directly to get original_date for filtering
        # Note: Can't use ilike with PostgREST due to Cloudflare 1101 errors,
        # so we fetch all docs and filter in Python
        result = supabase.table('documents') \
            .select('id, filename, original_date, granola_scanned_at, obsidian_file_path, uploaded_at') \
            .eq('user_id', user_id) \
            .limit(2000) \
            .execute()

        all_docs = result.data or []

        # Filter to meeting documents using heuristics
        meeting_docs = []
        for doc in all_docs:
            filename = doc.get('filename', '')
            obsidian_path = doc.get('obsidian_file_path', '')
            priority = classify_document_priority(filename, obsidian_path)
            # Only count high/medium priority docs (skip low-priority and excluded)
            if priority in ('high', 'medium'):
                meeting_docs.append(doc)

        # Filter by meeting date
        filtered_docs = []
        for doc in meeting_docs:
            doc_date = get_document_meeting_date(doc)
            if doc_date and doc_date >= effective_since_date:
                filtered_docs.append(doc)
            # Skip docs without detectable dates (can't verify they're recent enough)

        total_files = len(filtered_docs)
        scanned_count = sum(1 for d in filtered_docs if d.get('granola_scanned_at'))

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


# Keep old function names for backwards compatibility
async def scan_granola_vault(
    user_id: str,
    client_id: str,
    vault_path: str = "",  # Ignored - uses KB
    force_rescan: bool = False,
    since_date: Optional[date] = None
) -> Dict[str, Any]:
    """
    Backwards-compatible wrapper for scan_meeting_documents.
    The vault_path parameter is ignored - scanning now uses documents from the KB.
    """
    return await scan_meeting_documents(user_id, client_id, force_rescan, since_date)


async def scan_granola_documents(
    user_id: str,
    client_id: str,
    force_rescan: bool = False,
    since_date: Optional[date] = None
) -> Dict[str, Any]:
    """
    Backwards-compatible alias for scan_meeting_documents.
    """
    return await scan_meeting_documents(user_id, client_id, force_rescan, since_date)
