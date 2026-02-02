"""Entity Deduplicator Service

Unified deduplication service for tasks, opportunities, and stakeholders.
Provides consistent deduplication logic across all entity types during
Granola/Obsidian sync.

Key features:
- Within-batch deduplication (prevents same item from multiple docs)
- Rejected item blocking (prevents re-creating declined items)
- Pending candidate matching (tracks potential duplicates)
- Existing item matching (tracks matches to approved items)
- Hybrid matching: fuzzy (SequenceMatcher) + semantic (vector similarity)

Behavior:
- BLOCK creation for: rejected matches, within-batch duplicates, existing items
- CREATE + track match info for: pending candidates
"""

import logging
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple

from services.embeddings import create_embedding

logger = logging.getLogger(__name__)


@dataclass
class DeduplicationConfig:
    """Configuration thresholds for deduplication matching."""

    # Fuzzy matching threshold (SequenceMatcher ratio, 0-1)
    fuzzy_threshold: float = 0.80
    # Semantic matching threshold (cosine similarity, 0-1)
    semantic_threshold: float = 0.75
    # Whether to block on rejected item matches
    block_on_rejected: bool = True
    # Whether to block on within-batch duplicates
    block_on_batch_duplicate: bool = True
    # Whether to block on existing item matches (prevents duplicate candidates)
    block_on_existing: bool = True


@dataclass
class MatchResult:
    """Result of a deduplication check."""

    matched_id: str
    match_type: str  # 'existing', 'pending', 'rejected', 'batch'
    match_confidence: float
    match_reason: str
    is_semantic: bool = False

    def should_block(self, config: DeduplicationConfig) -> bool:
        """Determine if this match should block item creation."""
        if self.match_type == "rejected" and config.block_on_rejected:
            return True
        if self.match_type == "batch" and config.block_on_batch_duplicate:
            return True
        if self.match_type == "existing" and config.block_on_existing:
            return True
        return False


@dataclass
class BatchCache:
    """Cache for within-batch deduplication."""

    tasks: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    opportunities: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    stakeholders: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def clear(self):
        """Clear all caches."""
        self.tasks.clear()
        self.opportunities.clear()
        self.stakeholders.clear()


def fuzzy_match(str1: str, str2: str) -> float:
    """Calculate fuzzy similarity between two strings.
    Returns a score between 0 and 1.
    """
    if not str1 or not str2:
        return 0.0
    s1 = str1.lower().strip()
    s2 = str2.lower().strip()
    return SequenceMatcher(None, s1, s2).ratio()


def normalize_for_cache_key(text: str) -> str:
    """Normalize text for use as a cache key."""
    return text.lower().strip()[:100]


class EntityDeduplicator:
    """Unified deduplication service for all entity types.

    Usage:
        deduplicator = EntityDeduplicator(supabase)
        batch_id = str(uuid.uuid4())

        # For each extracted item:
        match = await deduplicator.deduplicate_task(client_id, title, desc, batch_id)
        if match and match.should_block(deduplicator.config):
            continue  # Skip this item

        # After sync completes:
        deduplicator.clear_batch_cache()
    """

    def __init__(self, supabase_client, config: Optional[DeduplicationConfig] = None):
        self.supabase = supabase_client
        self.config = config or DeduplicationConfig()
        self._batch_cache = BatchCache()

    def clear_batch_cache(self):
        """Clear all entity caches after sync completes."""
        self._batch_cache.clear()

    # =========================================================================
    # TASK DEDUPLICATION
    # =========================================================================

    async def deduplicate_task(
        self,
        client_id: str,
        title: str,
        description: str = "",
        batch_id: Optional[str] = None,
        embedding: Optional[List[float]] = None,
    ) -> Optional[MatchResult]:
        """Check for duplicate tasks.

        Check order:
        1. Within-batch (BLOCK if match)
        2. Rejected candidates (BLOCK if match)
        3. Pending candidates (CREATE + track)
        4. Existing project_tasks (CREATE + track)

        Args:
            client_id: Client ID
            title: Task title
            description: Task description (optional)
            batch_id: Batch ID for within-batch dedup (optional)
            embedding: Pre-computed embedding (optional, will generate if needed)

        Returns:
            MatchResult if match found, None otherwise
        """
        cache_key = normalize_for_cache_key(title)

        # 1. Within-batch check (exact + fuzzy)
        if batch_id:
            # First check exact match
            batch_key = f"{batch_id}:{cache_key}"
            if batch_key in self._batch_cache.tasks:
                cached = self._batch_cache.tasks[batch_key]
                return MatchResult(
                    matched_id=cached["id"],
                    match_type="batch",
                    match_confidence=1.0,
                    match_reason=f"Duplicate in same batch: '{cached['title'][:50]}'",
                )
            # Also check fuzzy match against all batch items
            for key, cached in self._batch_cache.tasks.items():
                if key.startswith(f"{batch_id}:"):
                    similarity = fuzzy_match(title, cached["title"])
                    if similarity > self.config.fuzzy_threshold:
                        return MatchResult(
                            matched_id=cached["id"],
                            match_type="batch",
                            match_confidence=similarity,
                            match_reason=f"Similar to batch item: '{cached['title'][:50]}'",
                        )
            # Add to cache for future checks
            self._batch_cache.tasks[batch_key] = {"id": "pending", "title": title}

        # 2. Check rejected candidates (fuzzy match)
        rejected_match = await self._check_rejected_tasks(client_id, title)
        if rejected_match:
            return rejected_match

        # 3. Check pending candidates (fuzzy + semantic)
        pending_match = await self._check_pending_task_candidates(
            client_id, title, description, embedding
        )
        if pending_match:
            return pending_match

        # 4. Check existing project_tasks (fuzzy + semantic)
        existing_match = await self._check_existing_tasks(client_id, title, description, embedding)
        if existing_match:
            return existing_match

        return None

    async def _check_rejected_tasks(self, client_id: str, title: str) -> Optional[MatchResult]:
        """Check if task matches a rejected candidate."""
        try:
            result = (
                self.supabase.table("task_candidates")
                .select("id, title")
                .eq("client_id", client_id)
                .eq("status", "rejected")
                .execute()
            )

            for rejected in result.data or []:
                similarity = fuzzy_match(title, rejected.get("title", ""))
                if similarity > self.config.fuzzy_threshold:
                    return MatchResult(
                        matched_id=rejected["id"],
                        match_type="rejected",
                        match_confidence=similarity,
                        match_reason=f"Similar to rejected: '{rejected['title'][:50]}'",
                    )
        except Exception as e:
            logger.warning(f"Error checking rejected tasks: {e}")
        return None

    async def _check_pending_task_candidates(
        self, client_id: str, title: str, description: str, embedding: Optional[List[float]]
    ) -> Optional[MatchResult]:
        """Check if task matches a pending candidate."""
        try:
            # Fuzzy match first
            result = (
                self.supabase.table("task_candidates")
                .select("id, title")
                .eq("client_id", client_id)
                .eq("status", "pending")
                .execute()
            )

            for pending in result.data or []:
                similarity = fuzzy_match(title, pending.get("title", ""))
                if similarity > self.config.fuzzy_threshold:
                    return MatchResult(
                        matched_id=pending["id"],
                        match_type="pending",
                        match_confidence=similarity,
                        match_reason=f"Similar to pending candidate: '{pending['title'][:50]}'",
                    )

            # Semantic match if embedding available
            if embedding:
                try:
                    semantic_result = self.supabase.rpc(
                        "match_task_candidates",
                        {
                            "query_embedding": embedding,
                            "p_client_id": client_id,
                            "match_threshold": self.config.semantic_threshold,
                            "match_count": 1,
                        },
                    ).execute()

                    if semantic_result.data:
                        match = semantic_result.data[0]
                        return MatchResult(
                            matched_id=match["id"],
                            match_type="pending",
                            match_confidence=match["similarity"],
                            match_reason=f"Semantically similar to: '{match['title'][:50]}'",
                            is_semantic=True,
                        )
                except Exception as e:
                    logger.debug(f"Semantic task candidate match failed: {e}")

        except Exception as e:
            logger.warning(f"Error checking pending task candidates: {e}")
        return None

    async def _check_existing_tasks(
        self, client_id: str, title: str, description: str, embedding: Optional[List[float]]
    ) -> Optional[MatchResult]:
        """Check if task matches an existing project_task."""
        try:
            # Fuzzy match
            result = (
                self.supabase.table("project_tasks")
                .select("id, title")
                .eq("client_id", client_id)
                .neq("status", "completed")
                .execute()
            )

            for task in result.data or []:
                similarity = fuzzy_match(title, task.get("title", ""))
                if similarity > self.config.fuzzy_threshold:
                    return MatchResult(
                        matched_id=task["id"],
                        match_type="existing",
                        match_confidence=similarity,
                        match_reason=f"Similar to existing task: '{task['title'][:50]}'",
                    )

            # Semantic match if embedding available
            if embedding:
                try:
                    semantic_result = self.supabase.rpc(
                        "match_existing_tasks",
                        {
                            "query_embedding": embedding,
                            "p_client_id": client_id,
                            "match_threshold": self.config.semantic_threshold,
                            "match_count": 1,
                        },
                    ).execute()

                    if semantic_result.data:
                        match = semantic_result.data[0]
                        return MatchResult(
                            matched_id=match["id"],
                            match_type="existing",
                            match_confidence=match["similarity"],
                            match_reason=f"Semantically similar to: '{match['title'][:50]}'",
                            is_semantic=True,
                        )
                except Exception as e:
                    logger.debug(f"Semantic existing task match failed: {e}")

        except Exception as e:
            logger.warning(f"Error checking existing tasks: {e}")
        return None

    # =========================================================================
    # OPPORTUNITY DEDUPLICATION
    # =========================================================================

    async def deduplicate_opportunity(
        self,
        client_id: str,
        title: str,
        quote: str = "",
        batch_id: Optional[str] = None,
        embedding: Optional[List[float]] = None,
    ) -> Optional[MatchResult]:
        """Check for duplicate opportunities.

        Check order:
        1. Within-batch (BLOCK if match)
        2. Rejected candidates (BLOCK if match)
        3. Pending candidates (CREATE + track)
        4. Existing ai_projects (CREATE + track)

        Args:
            client_id: Client ID
            title: Opportunity title/description
            quote: Supporting quote from document
            batch_id: Batch ID for within-batch dedup
            embedding: Pre-computed embedding (optional)

        Returns:
            MatchResult if match found, None otherwise
        """
        cache_key = normalize_for_cache_key(title)

        # 1. Within-batch check (exact + fuzzy)
        if batch_id:
            # First check exact match
            batch_key = f"{batch_id}:{cache_key}"
            if batch_key in self._batch_cache.opportunities:
                cached = self._batch_cache.opportunities[batch_key]
                return MatchResult(
                    matched_id=cached["id"],
                    match_type="batch",
                    match_confidence=1.0,
                    match_reason=f"Duplicate in same batch: '{cached['title'][:50]}'",
                )
            # Also check fuzzy match against all batch items
            for key, cached in self._batch_cache.opportunities.items():
                if key.startswith(f"{batch_id}:"):
                    similarity = fuzzy_match(title, cached["title"])
                    if similarity > self.config.fuzzy_threshold:
                        return MatchResult(
                            matched_id=cached["id"],
                            match_type="batch",
                            match_confidence=similarity,
                            match_reason=f"Similar to batch item: '{cached['title'][:50]}'",
                        )
            self._batch_cache.opportunities[batch_key] = {"id": "pending", "title": title}

        # 2. Check rejected candidates
        rejected_match = await self._check_rejected_opportunities(client_id, title)
        if rejected_match:
            return rejected_match

        # 3. Check pending candidates
        pending_match = await self._check_pending_project_candidates(client_id, title)
        if pending_match:
            return pending_match

        # 4. Check existing opportunities
        existing_match = await self._check_existing_opportunities(client_id, title, quote)
        if existing_match:
            return existing_match

        return None

    async def _check_rejected_opportunities(
        self, client_id: str, title: str
    ) -> Optional[MatchResult]:
        """Check if opportunity matches a rejected candidate."""
        try:
            result = (
                self.supabase.table("project_candidates")
                .select("id, title")
                .eq("client_id", client_id)
                .eq("status", "rejected")
                .execute()
            )

            for rejected in result.data or []:
                similarity = fuzzy_match(title, rejected.get("title", ""))
                if similarity > self.config.fuzzy_threshold:
                    return MatchResult(
                        matched_id=rejected["id"],
                        match_type="rejected",
                        match_confidence=similarity,
                        match_reason=f"Similar to rejected: '{rejected['title'][:50]}'",
                    )
        except Exception as e:
            logger.warning(f"Error checking rejected opportunities: {e}")
        return None

    async def _check_pending_project_candidates(
        self, client_id: str, title: str
    ) -> Optional[MatchResult]:
        """Check if opportunity matches a pending candidate."""
        try:
            result = (
                self.supabase.table("project_candidates")
                .select("id, title")
                .eq("client_id", client_id)
                .eq("status", "pending")
                .execute()
            )

            for pending in result.data or []:
                similarity = fuzzy_match(title, pending.get("title", ""))
                if similarity > self.config.fuzzy_threshold:
                    return MatchResult(
                        matched_id=pending["id"],
                        match_type="pending",
                        match_confidence=similarity,
                        match_reason=f"Similar to pending: '{pending['title'][:50]}'",
                    )
        except Exception as e:
            logger.warning(f"Error checking pending opportunity candidates: {e}")
        return None

    async def _check_existing_opportunities(
        self, client_id: str, title: str, quote: str
    ) -> Optional[MatchResult]:
        """Check if opportunity matches an existing one."""
        try:
            result = (
                self.supabase.table("ai_projects")
                .select("id, title, project_name, description")
                .eq("client_id", client_id)
                .execute()
            )

            for opp in result.data or []:
                # Check title
                title_sim = fuzzy_match(title, opp.get("title", ""))
                if title_sim > 0.85:
                    return MatchResult(
                        matched_id=opp["id"],
                        match_type="existing",
                        match_confidence=title_sim,
                        match_reason=f"Title match ({title_sim:.0%}): '{opp['title'][:50]}'",
                    )

                # Check project_name
                project_name = opp.get("project_name")
                if project_name:
                    proj_sim = fuzzy_match(title, project_name)
                    if proj_sim > 0.85:
                        return MatchResult(
                            matched_id=opp["id"],
                            match_type="existing",
                            match_confidence=proj_sim,
                            match_reason=f"Project name match ({proj_sim:.0%}): '{project_name[:50]}'",
                        )
        except Exception as e:
            logger.warning(f"Error checking existing opportunities: {e}")
        return None

    # =========================================================================
    # STAKEHOLDER DEDUPLICATION
    # =========================================================================

    async def deduplicate_stakeholder(
        self,
        client_id: str,
        name: str,
        role: str = "",
        department: str = "",
        organization: str = "",
        email: str = "",
        batch_id: Optional[str] = None,
    ) -> Optional[MatchResult]:
        """Check for duplicate stakeholders.

        Check order:
        1. Within-batch (BLOCK if match)
        2. Rejected candidates (BLOCK if match)
        3. Pending candidates (CREATE + track)
        4. Existing stakeholders (CREATE + track)

        Args:
            client_id: Client ID
            name: Stakeholder name
            role: Job role/title
            department: Department
            organization: Organization name
            email: Email address
            batch_id: Batch ID for within-batch dedup

        Returns:
            MatchResult if match found, None otherwise
        """
        cache_key = normalize_for_cache_key(name)

        # 1. Within-batch check (exact + fuzzy)
        if batch_id:
            # First check exact match
            batch_key = f"{batch_id}:{cache_key}"
            if batch_key in self._batch_cache.stakeholders:
                cached = self._batch_cache.stakeholders[batch_key]
                return MatchResult(
                    matched_id=cached["id"],
                    match_type="batch",
                    match_confidence=1.0,
                    match_reason=f"Duplicate in same batch: '{cached['name']}'",
                )
            # Also check fuzzy match against all batch items (catches name variations)
            for key, cached in self._batch_cache.stakeholders.items():
                if key.startswith(f"{batch_id}:"):
                    similarity = fuzzy_match(name, cached["name"])
                    if similarity > 0.90:  # Higher threshold for names
                        return MatchResult(
                            matched_id=cached["id"],
                            match_type="batch",
                            match_confidence=similarity,
                            match_reason=f"Similar to batch item: '{cached['name']}'",
                        )
            self._batch_cache.stakeholders[batch_key] = {"id": "pending", "name": name}

        # 2. Check rejected candidates
        rejected_match = await self._check_rejected_stakeholders(client_id, name)
        if rejected_match:
            return rejected_match

        # 3. Check pending candidates
        pending_match = await self._check_pending_stakeholder_candidates(client_id, name, email)
        if pending_match:
            return pending_match

        # 4. Check existing stakeholders
        existing_match = await self._check_existing_stakeholders(
            client_id, name, role, department, organization, email
        )
        if existing_match:
            return existing_match

        return None

    async def _check_rejected_stakeholders(
        self, client_id: str, name: str
    ) -> Optional[MatchResult]:
        """Check if stakeholder matches a rejected candidate."""
        try:
            result = (
                self.supabase.table("stakeholder_candidates")
                .select("id, name")
                .eq("client_id", client_id)
                .eq("status", "rejected")
                .execute()
            )

            for rejected in result.data or []:
                similarity = self._name_similarity(name, rejected.get("name", ""))
                if similarity > 0.85:
                    return MatchResult(
                        matched_id=rejected["id"],
                        match_type="rejected",
                        match_confidence=similarity,
                        match_reason=f"Similar to rejected: '{rejected['name']}'",
                    )
        except Exception as e:
            logger.warning(f"Error checking rejected stakeholders: {e}")
        return None

    async def _check_pending_stakeholder_candidates(
        self, client_id: str, name: str, email: str
    ) -> Optional[MatchResult]:
        """Check if stakeholder matches a pending candidate."""
        try:
            result = (
                self.supabase.table("stakeholder_candidates")
                .select("id, name, email")
                .eq("client_id", client_id)
                .eq("status", "pending")
                .execute()
            )

            for pending in result.data or []:
                # Email match is definitive
                if email and pending.get("email"):
                    if email.lower() == pending["email"].lower():
                        return MatchResult(
                            matched_id=pending["id"],
                            match_type="pending",
                            match_confidence=1.0,
                            match_reason=f"Email match: {email}",
                        )

                # Name similarity
                similarity = self._name_similarity(name, pending.get("name", ""))
                if similarity > 0.85:
                    return MatchResult(
                        matched_id=pending["id"],
                        match_type="pending",
                        match_confidence=similarity,
                        match_reason=f"Similar to pending: '{pending['name']}'",
                    )
        except Exception as e:
            logger.warning(f"Error checking pending stakeholder candidates: {e}")
        return None

    async def _check_existing_stakeholders(
        self, client_id: str, name: str, role: str, department: str, organization: str, email: str
    ) -> Optional[MatchResult]:
        """Check if stakeholder matches an existing one."""
        try:
            result = (
                self.supabase.table("stakeholders")
                .select("id, name, email, role, department, organization")
                .eq("client_id", client_id)
                .execute()
            )

            for existing in result.data or []:
                # Email match is definitive
                if email and existing.get("email"):
                    if email.lower() == existing["email"].lower():
                        return MatchResult(
                            matched_id=existing["id"],
                            match_type="existing",
                            match_confidence=1.0,
                            match_reason=f"Email match: {email}",
                        )

                # Calculate overall match score
                score, reasons = self._calculate_stakeholder_match(
                    name, role, department, organization, existing
                )

                if score >= 0.5:
                    return MatchResult(
                        matched_id=existing["id"],
                        match_type="existing",
                        match_confidence=score,
                        match_reason=", ".join(reasons),
                    )
        except Exception as e:
            logger.warning(f"Error checking existing stakeholders: {e}")
        return None

    def _name_similarity(self, name1: str, name2: str) -> float:
        """Calculate name similarity score.
        Handles case differences, partial names, name ordering.
        """
        if not name1 or not name2:
            return 0.0

        n1 = name1.lower().strip()
        n2 = name2.lower().strip()

        if n1 == n2:
            return 1.0

        # Split into parts
        parts1 = set(n1.split())
        parts2 = set(n2.split())

        # Check if one name is subset of other (e.g., "John" matches "John Smith")
        if parts1.issubset(parts2) or parts2.issubset(parts1):
            overlap = len(parts1 & parts2)
            total = max(len(parts1), len(parts2))
            return 0.7 + (0.3 * overlap / total)

        # Check word overlap
        if parts1 & parts2:
            overlap = len(parts1 & parts2)
            total = max(len(parts1), len(parts2))
            return 0.5 + (0.3 * overlap / total)

        # Fall back to sequence matching
        return SequenceMatcher(None, n1, n2).ratio()

    def _calculate_stakeholder_match(
        self, name: str, role: str, department: str, organization: str, existing: Dict[str, Any]
    ) -> Tuple[float, List[str]]:
        """Calculate overall match score for stakeholder."""
        score = 0.0
        reasons = []

        # Name similarity (up to 0.6)
        name_score = self._name_similarity(name, existing.get("name", ""))
        if name_score >= 0.9:
            score += 0.6
            reasons.append(f"Name match ({name_score:.0%})")
        elif name_score >= 0.7:
            score += 0.4
            reasons.append(f"Name similar ({name_score:.0%})")
        elif name_score >= 0.5:
            score += 0.2
            reasons.append(f"Name partially similar ({name_score:.0%})")
        else:
            return 0.0, []  # Names don't match at all

        # Role match (up to 0.2)
        if role and existing.get("role"):
            role_score = fuzzy_match(role, existing["role"])
            if role_score >= 0.7:
                score += 0.2
                reasons.append("Role match")
            elif role_score >= 0.5:
                score += 0.1
                reasons.append("Role similar")

        # Department match (up to 0.15)
        if department and existing.get("department"):
            if department.lower() == existing["department"].lower():
                score += 0.15
                reasons.append("Department match")

        # Organization match (up to 0.15)
        if organization and existing.get("organization"):
            org_score = fuzzy_match(organization, existing["organization"])
            if org_score >= 0.8:
                score += 0.15
                reasons.append("Organization match")

        return min(score, 1.0), reasons

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def generate_task_embedding(self, title: str, description: str = "") -> List[float]:
        """Generate embedding for a task."""
        text = title
        if description:
            text = f"{title} {description[:200]}"
        return create_embedding(text, input_type="document")

    def update_batch_cache_id(self, entity_type: str, batch_id: str, title: str, actual_id: str):
        """Update the batch cache with the actual ID after insertion.
        Call this after successfully inserting a candidate.
        """
        cache_key = normalize_for_cache_key(title)
        batch_key = f"{batch_id}:{cache_key}"

        if entity_type == "task" and batch_key in self._batch_cache.tasks:
            self._batch_cache.tasks[batch_key]["id"] = actual_id
        elif entity_type == "opportunity" and batch_key in self._batch_cache.opportunities:
            self._batch_cache.opportunities[batch_key]["id"] = actual_id
        elif entity_type == "stakeholder" and batch_key in self._batch_cache.stakeholders:
            self._batch_cache.stakeholders[batch_key]["id"] = actual_id
