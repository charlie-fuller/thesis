"""Stakeholder Deduplicator Service.

Detects potential matches between extracted stakeholders and existing stakeholders
in the database. Uses name similarity, email matching, and role/organization context.
"""

import logging
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Optional

from services.stakeholder_extractor import ExtractedStakeholder

logger = logging.getLogger(__name__)


@dataclass
class StakeholderMatch:
    """A potential match between an extracted stakeholder and an existing one."""

    extracted: ExtractedStakeholder
    existing_stakeholder_id: str
    existing_name: str
    existing_role: Optional[str]
    existing_department: Optional[str]
    match_confidence: float  # 0-1
    match_reasons: list[str]


class StakeholderDeduplicator:
    """Detects potential duplicate stakeholders."""

    def __init__(self, supabase_client):
        self.supabase = supabase_client

    async def find_matches(
        self, extracted_stakeholders: list[ExtractedStakeholder], client_id: str
    ) -> dict[int, StakeholderMatch]:
        """Find potential matches for extracted stakeholders.

        Args:
            extracted_stakeholders: List of newly extracted stakeholders
            client_id: Client ID to scope the search

        Returns:
            Dict mapping extracted stakeholder index to match info
        """
        if not extracted_stakeholders:
            return {}

        # Get existing stakeholders for this client
        existing = await self._get_existing_stakeholders(client_id)
        if not existing:
            return {}

        matches = {}
        for idx, extracted in enumerate(extracted_stakeholders):
            match = self._find_best_match(extracted, existing)
            if match:
                matches[idx] = match

        return matches

    async def _get_existing_stakeholders(self, client_id: str) -> list[dict]:
        """Fetch existing stakeholders for the client."""
        try:
            result = (
                self.supabase.table("stakeholders")
                .select("id, name, email, role, department, organization")
                .eq("client_id", client_id)
                .execute()
            )

            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Failed to fetch existing stakeholders: {e}")
            return []

    def _find_best_match(self, extracted: ExtractedStakeholder, existing: list[dict]) -> Optional[StakeholderMatch]:
        """Find the best matching existing stakeholder."""
        best_match = None
        best_score = 0.0

        for existing_s in existing:
            score, reasons = self._calculate_match_score(extracted, existing_s)

            # Only consider matches above threshold
            if score >= 0.5 and score > best_score:
                best_score = score
                best_match = StakeholderMatch(
                    extracted=extracted,
                    existing_stakeholder_id=existing_s["id"],
                    existing_name=existing_s["name"],
                    existing_role=existing_s.get("role"),
                    existing_department=existing_s.get("department"),
                    match_confidence=score,
                    match_reasons=reasons,
                )

        return best_match

    def _calculate_match_score(self, extracted: ExtractedStakeholder, existing: dict) -> tuple[float, list[str]]:
        """Calculate match score between extracted and existing stakeholder.

        Returns:
            Tuple of (score, list of match reasons)
        """
        score = 0.0
        reasons = []

        # Email match is definitive (1.0)
        if extracted.email and existing.get("email"):
            if extracted.email.lower() == existing["email"].lower():
                return 1.0, ["Email match"]

        # Name similarity (up to 0.6)
        name_score = self._name_similarity(extracted.name, existing["name"])
        if name_score >= 0.9:
            score += 0.6
            reasons.append(f"Name match ({name_score:.0%})")
        elif name_score >= 0.7:
            score += 0.4
            reasons.append(f"Name similar ({name_score:.0%})")
        elif name_score >= 0.5:
            score += 0.2
            reasons.append(f"Name partially similar ({name_score:.0%})")

        # If names don't match at all, skip other comparisons
        if name_score < 0.5:
            return 0.0, []

        # Role match (up to 0.2)
        if extracted.role and existing.get("role"):
            role_score = self._name_similarity(extracted.role, existing["role"])
            if role_score >= 0.7:
                score += 0.2
                reasons.append("Role match")
            elif role_score >= 0.5:
                score += 0.1
                reasons.append("Role similar")

        # Department match (up to 0.15)
        if extracted.department and existing.get("department"):
            if extracted.department.lower() == existing["department"].lower():
                score += 0.15
                reasons.append("Department match")

        # Organization match (up to 0.15)
        if extracted.organization and existing.get("organization"):
            org_score = self._name_similarity(extracted.organization, existing["organization"])
            if org_score >= 0.8:
                score += 0.15
                reasons.append("Organization match")

        return min(score, 1.0), reasons

    def _name_similarity(self, name1: str, name2: str) -> float:
        """Calculate name similarity score.

        Handles:
        - Case differences
        - Partial name matches (first name only)
        - Name ordering (John Smith vs Smith, John)
        """
        if not name1 or not name2:
            return 0.0

        # Normalize names
        n1 = name1.lower().strip()
        n2 = name2.lower().strip()

        # Exact match
        if n1 == n2:
            return 1.0

        # Split into parts
        parts1 = set(n1.split())
        parts2 = set(n2.split())

        # Check if all parts of one name are in the other
        if parts1.issubset(parts2) or parts2.issubset(parts1):
            # Partial match (e.g., "John" matches "John Smith")
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


async def find_duplicate_candidates(
    supabase_client, client_id: str, name: str, email: Optional[str] = None
) -> list[dict]:
    """Quick check for existing candidates with similar name/email.

    Used to avoid creating duplicate candidates from the same document.
    """
    try:
        query = (
            supabase_client.table("stakeholder_candidates")
            .select("id, name, email, status, source_document_name")
            .eq("client_id", client_id)
            .eq("status", "pending")
        )

        # If email provided, check for exact email match
        if email:
            query = query.or_(f"email.eq.{email},name.ilike.%{name}%")
        else:
            query = query.ilike("name", f"%{name}%")

        result = query.execute()
        return result.data if result.data else []

    except Exception as e:
        logger.error(f"Error checking for duplicate candidates: {e}")
        return []
