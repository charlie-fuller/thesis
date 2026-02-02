"""Phonetic matching service for name comparison.

Uses Double Metaphone algorithm for sound-alike matching.

Version: 1.0.0
Created: 2026-01-23
"""

from dataclasses import dataclass
from typing import Optional, Tuple

try:
    from metaphone import doublemetaphone
except ImportError:
    doublemetaphone = None


@dataclass
class PhoneticMatch:
    """Result of phonetic comparison between two names."""

    is_match: bool
    primary_match: bool
    secondary_match: bool
    name1_codes: Tuple[str, str]
    name2_codes: Tuple[str, str]
    confidence: float


class PhoneticMatcher:
    """Matches names using Double Metaphone phonetic algorithm.

    Particularly effective for transcription errors where names
    sound similar but are spelled differently:
    - "Charlie" vs "Charley" (sound identical)
    - "Sara" vs "Sarah" (sound identical)
    - "Steven" vs "Stephen" (sound identical)
    """

    def __init__(self):
        if doublemetaphone is None:
            raise ImportError(
                "metaphone package not installed. Install with: pip install metaphone"
            )

    def get_metaphone_codes(self, name: str) -> Tuple[str, str]:
        """Get Double Metaphone codes for a name.

        Returns tuple of (primary_code, secondary_code).
        Secondary code may be empty string if no alternate pronunciation.
        """
        if not name or not name.strip():
            return ("", "")

        # Clean the name
        cleaned = name.strip().upper()

        # Get metaphone codes
        codes = doublemetaphone(cleaned)
        return (codes[0] or "", codes[1] or "")

    def get_name_codes(self, full_name: str) -> Tuple[Tuple[str, str], Tuple[str, str]]:
        """Get metaphone codes for first and last name separately.

        Returns ((first_primary, first_secondary), (last_primary, last_secondary))
        """
        parts = full_name.strip().split()

        if len(parts) == 0:
            return (("", ""), ("", ""))
        elif len(parts) == 1:
            first_codes = self.get_metaphone_codes(parts[0])
            return (first_codes, ("", ""))
        else:
            # First name is first part, last name is all remaining parts
            first_codes = self.get_metaphone_codes(parts[0])
            last_name = " ".join(parts[1:])
            last_codes = self.get_metaphone_codes(last_name)
            return (first_codes, last_codes)

    def compare_names(
        self, name1: str, name2: str, require_both_parts: bool = True
    ) -> PhoneticMatch:
        """Compare two names phonetically.

        Args:
            name1: First name to compare
            name2: Second name to compare
            require_both_parts: If True, both first and last names must match
                              for multi-word names. If False, matches if any
                              part matches.

        Returns:
            PhoneticMatch with match details and confidence score.
        """
        codes1 = self.get_name_codes(name1)
        codes2 = self.get_name_codes(name2)

        first1, last1 = codes1
        first2, last2 = codes2

        # Check first name match
        first_primary_match = bool(first1[0] and first2[0] and first1[0] == first2[0])
        first_secondary_match = bool(
            (first1[0] and first2[1] and first1[0] == first2[1])
            or (first1[1] and first2[0] and first1[1] == first2[0])
        )
        first_match = first_primary_match or first_secondary_match

        # Check last name match (if both have last names)
        has_last_names = bool(last1[0] and last2[0])
        if has_last_names:
            last_primary_match = last1[0] == last2[0]
            last_secondary_match = bool(
                (last1[0] and last2[1] and last1[0] == last2[1])
                or (last1[1] and last2[0] and last1[1] == last2[0])
            )
            last_match = last_primary_match or last_secondary_match
        else:
            # One or both don't have last names
            last_match = not has_last_names  # Match if neither has last name
            last_primary_match = False
            last_secondary_match = False

        # Determine overall match
        if require_both_parts and has_last_names:
            is_match = first_match and last_match
        else:
            is_match = first_match

        # Calculate confidence
        confidence = self._calculate_confidence(
            first_match=first_match,
            first_primary=first_primary_match,
            last_match=last_match if has_last_names else None,
            last_primary=last_primary_match if has_last_names else None,
        )

        return PhoneticMatch(
            is_match=is_match,
            primary_match=first_primary_match and (last_primary_match if has_last_names else True),
            secondary_match=first_secondary_match
            or (last_secondary_match if has_last_names else False),
            name1_codes=(first1, last1),
            name2_codes=(first2, last2),
            confidence=confidence,
        )

    def _calculate_confidence(
        self,
        first_match: bool,
        first_primary: bool,
        last_match: Optional[bool],
        last_primary: Optional[bool],
    ) -> float:
        """Calculate confidence score for phonetic match.

        Primary matches are weighted higher than secondary matches.
        """
        if not first_match:
            return 0.0

        score = 0.0

        # First name contribution (50% of total)
        if first_primary:
            score += 0.5
        elif first_match:
            score += 0.35  # Secondary match is less confident

        # Last name contribution (50% of total, if applicable)
        if last_match is None:
            # No last name to compare, scale up first name
            score *= 1.6  # Max ~0.8 for first-name-only match
        elif last_match:
            if last_primary:
                score += 0.5
            else:
                score += 0.35

        return min(score, 1.0)

    def find_best_match(
        self, target_name: str, candidates: list[str], threshold: float = 0.7
    ) -> Optional[Tuple[str, float]]:
        """Find the best phonetic match from a list of candidates.

        Args:
            target_name: Name to match
            candidates: List of potential matches
            threshold: Minimum confidence score to consider a match

        Returns:
            Tuple of (best_match, confidence) or None if no match above threshold.
        """
        best_match = None
        best_confidence = 0.0

        for candidate in candidates:
            result = self.compare_names(target_name, candidate)
            if result.is_match and result.confidence > best_confidence:
                best_match = candidate
                best_confidence = result.confidence

        if best_confidence >= threshold:
            return (best_match, best_confidence)
        return None


# Singleton instance for convenience
_matcher: Optional[PhoneticMatcher] = None


def get_phonetic_matcher() -> PhoneticMatcher:
    """Get singleton PhoneticMatcher instance."""
    global _matcher
    if _matcher is None:
        _matcher = PhoneticMatcher()
    return _matcher
