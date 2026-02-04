"""Entity validation service for correcting transcription errors.

Validates person names and organizations against ground truth registries.

Version: 1.0.0
Created: 2026-01-23
"""

import logging
from dataclasses import dataclass
from difflib import SequenceMatcher
from enum import Enum
from typing import Optional

from services.phonetic_matcher import PhoneticMatcher, get_phonetic_matcher

logger = logging.getLogger(__name__)


class ValidationStatus(str, Enum):
    """Status of entity validation."""

    EXACT_MATCH = "exact_match"
    ALIAS_MATCH = "alias_match"
    FUZZY_MATCH = "fuzzy_match"
    PHONETIC_MATCH = "phonetic_match"
    NEW_ENTITY = "new_entity"
    POTENTIAL_ERROR = "potential_error"


@dataclass
class ValidationResult:
    """Result of entity validation."""

    original_value: str
    status: ValidationStatus
    suggested_value: Optional[str]
    confidence: float
    match_reason: str
    registry_entry_id: Optional[str] = None

    def to_candidate_status(self) -> str:
        """Convert to stakeholder_candidates status format."""
        if self.status == ValidationStatus.EXACT_MATCH:
            return "validated"
        elif self.status in (
            ValidationStatus.ALIAS_MATCH,
            ValidationStatus.FUZZY_MATCH,
            ValidationStatus.PHONETIC_MATCH,
        ):
            return "suggested_correction"
        elif self.status == ValidationStatus.NEW_ENTITY:
            return "new"
        else:
            return "potential_error"


class EntityValidator:
    """Validates entities against ground truth registries.

    Uses multiple matching strategies:
    1. Exact match against canonical names
    2. Alias match (known variations/misspellings)
    3. Fuzzy match (Levenshtein similarity)
    4. Phonetic match (Double Metaphone for names)
    """

    def __init__(self, supabase_client, fuzzy_threshold: float = 0.85, phonetic_threshold: float = 0.7):
        self.supabase = supabase_client
        self.fuzzy_threshold = fuzzy_threshold
        self.phonetic_threshold = phonetic_threshold
        self._phonetic_matcher: Optional[PhoneticMatcher] = None

    @property
    def phonetic_matcher(self) -> PhoneticMatcher:
        """Lazy-load phonetic matcher."""
        if self._phonetic_matcher is None:
            try:
                self._phonetic_matcher = get_phonetic_matcher()
            except ImportError:
                logger.warning("Phonetic matching unavailable - metaphone not installed")
        return self._phonetic_matcher

    async def validate_person_name(self, name: str, client_id: str, context: Optional[str] = None) -> ValidationResult:
        """Validate a person's name against the registry.

        Args:
            name: The name to validate
            client_id: Client ID for scoping
            context: Optional context (e.g., organization) for disambiguation

        Returns:
            ValidationResult with match details
        """
        if not name or not name.strip():
            return ValidationResult(
                original_value=name or "",
                status=ValidationStatus.POTENTIAL_ERROR,
                suggested_value=None,
                confidence=0.0,
                match_reason="Empty name",
            )

        clean_name = name.strip()

        # Get metaphone codes for phonetic matching
        metaphone_first = None
        metaphone_last = None
        if self.phonetic_matcher:
            codes = self.phonetic_matcher.get_name_codes(clean_name)
            metaphone_first = codes[0][0] if codes[0][0] else None
            metaphone_last = codes[1][0] if codes[1][0] else None

        # Search registry using RPC function
        try:
            result = self.supabase.rpc(
                "search_person_registry",
                {
                    "p_client_id": client_id,
                    "p_search_term": clean_name,
                    "p_metaphone_first": metaphone_first,
                    "p_metaphone_last": metaphone_last,
                    "p_limit": 5,
                },
            ).execute()

            matches = result.data or []
        except Exception as e:
            logger.error(f"Error searching person registry: {e}")
            matches = []

        if not matches:
            # No matches found - this is a new entity
            return ValidationResult(
                original_value=clean_name,
                status=ValidationStatus.NEW_ENTITY,
                suggested_value=None,
                confidence=1.0,
                match_reason="No matching entries in registry",
            )

        # Evaluate best match
        best = matches[0]
        match_type = best.get("match_type", "fuzzy")
        similarity = best.get("similarity", 0.0)
        canonical = best.get("canonical_name", "")
        registry_id = best.get("id")

        if match_type == "exact":
            return ValidationResult(
                original_value=clean_name,
                status=ValidationStatus.EXACT_MATCH,
                suggested_value=canonical,
                confidence=1.0,
                match_reason="Exact match found",
                registry_entry_id=registry_id,
            )

        if match_type == "alias":
            return ValidationResult(
                original_value=clean_name,
                status=ValidationStatus.ALIAS_MATCH,
                suggested_value=canonical,
                confidence=0.95,
                match_reason=f"Known alias for '{canonical}'",
                registry_entry_id=registry_id,
            )

        if match_type == "phonetic":
            # Verify with our phonetic matcher for confidence
            confidence = 0.85
            if self.phonetic_matcher:
                phonetic_result = self.phonetic_matcher.compare_names(clean_name, canonical)
                confidence = phonetic_result.confidence

            if confidence >= self.phonetic_threshold:
                return ValidationResult(
                    original_value=clean_name,
                    status=ValidationStatus.PHONETIC_MATCH,
                    suggested_value=canonical,
                    confidence=confidence,
                    match_reason=f"Sounds like '{canonical}'",
                    registry_entry_id=registry_id,
                )

        # Fuzzy match
        if similarity >= self.fuzzy_threshold:
            return ValidationResult(
                original_value=clean_name,
                status=ValidationStatus.FUZZY_MATCH,
                suggested_value=canonical,
                confidence=similarity,
                match_reason=f"Similar to '{canonical}' ({similarity:.0%} match)",
                registry_entry_id=registry_id,
            )

        # Low similarity - potential error but not confident enough to suggest
        if similarity >= 0.5:
            return ValidationResult(
                original_value=clean_name,
                status=ValidationStatus.POTENTIAL_ERROR,
                suggested_value=canonical,
                confidence=similarity,
                match_reason=f"Possible match for '{canonical}' ({similarity:.0%})",
                registry_entry_id=registry_id,
            )

        # New entity
        return ValidationResult(
            original_value=clean_name,
            status=ValidationStatus.NEW_ENTITY,
            suggested_value=None,
            confidence=1.0,
            match_reason="No close matches in registry",
        )

    async def validate_organization(self, org_name: str, client_id: str) -> ValidationResult:
        """Validate an organization name against the registry.

        Args:
            org_name: The organization name to validate
            client_id: Client ID for scoping

        Returns:
            ValidationResult with match details
        """
        if not org_name or not org_name.strip():
            return ValidationResult(
                original_value=org_name or "",
                status=ValidationStatus.POTENTIAL_ERROR,
                suggested_value=None,
                confidence=0.0,
                match_reason="Empty organization name",
            )

        clean_name = org_name.strip()

        # Search registry using RPC function
        try:
            result = self.supabase.rpc(
                "search_organization_registry",
                {"p_client_id": client_id, "p_search_term": clean_name, "p_limit": 5},
            ).execute()

            matches = result.data or []
        except Exception as e:
            logger.error(f"Error searching organization registry: {e}")
            matches = []

        if not matches:
            return ValidationResult(
                original_value=clean_name,
                status=ValidationStatus.NEW_ENTITY,
                suggested_value=None,
                confidence=1.0,
                match_reason="No matching organizations in registry",
            )

        # Evaluate best match
        best = matches[0]
        match_type = best.get("match_type", "fuzzy")
        similarity = best.get("similarity", 0.0)
        canonical = best.get("canonical_name", "")
        registry_id = best.get("id")

        if match_type == "exact":
            return ValidationResult(
                original_value=clean_name,
                status=ValidationStatus.EXACT_MATCH,
                suggested_value=canonical,
                confidence=1.0,
                match_reason="Exact match found",
                registry_entry_id=registry_id,
            )

        if match_type == "alias":
            return ValidationResult(
                original_value=clean_name,
                status=ValidationStatus.ALIAS_MATCH,
                suggested_value=canonical,
                confidence=0.95,
                match_reason=f"Known alias for '{canonical}'",
                registry_entry_id=registry_id,
            )

        # Fuzzy match
        if similarity >= self.fuzzy_threshold:
            return ValidationResult(
                original_value=clean_name,
                status=ValidationStatus.FUZZY_MATCH,
                suggested_value=canonical,
                confidence=similarity,
                match_reason=f"Similar to '{canonical}' ({similarity:.0%} match)",
                registry_entry_id=registry_id,
            )

        # Low similarity
        if similarity >= 0.5:
            return ValidationResult(
                original_value=clean_name,
                status=ValidationStatus.POTENTIAL_ERROR,
                suggested_value=canonical,
                confidence=similarity,
                match_reason=f"Possible match for '{canonical}' ({similarity:.0%})",
                registry_entry_id=registry_id,
            )

        return ValidationResult(
            original_value=clean_name,
            status=ValidationStatus.NEW_ENTITY,
            suggested_value=None,
            confidence=1.0,
            match_reason="No close organization matches",
        )

    def calculate_fuzzy_similarity(self, s1: str, s2: str) -> float:
        """Calculate fuzzy similarity between two strings.

        Uses SequenceMatcher for Levenshtein-like comparison.
        """
        if not s1 or not s2:
            return 0.0
        return SequenceMatcher(None, s1.lower().strip(), s2.lower().strip()).ratio()

    async def record_validation(
        self,
        client_id: str,
        entity_type: str,
        result: ValidationResult,
        source_document_id: Optional[str] = None,
    ) -> None:
        """Record validation result in audit table.

        Args:
            client_id: Client ID
            entity_type: 'person' or 'organization'
            result: The validation result
            source_document_id: Optional document ID
        """
        try:
            self.supabase.table("entity_validation_results").insert(
                {
                    "client_id": client_id,
                    "entity_type": entity_type,
                    "original_value": result.original_value,
                    "validation_status": result.status.value,
                    "suggested_value": result.suggested_value,
                    "confidence": result.confidence,
                    "match_reason": result.match_reason,
                    "registry_entry_id": result.registry_entry_id,
                    "source_document_id": source_document_id,
                }
            ).execute()
        except Exception as e:
            logger.error(f"Error recording validation result: {e}")
