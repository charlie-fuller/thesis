"""Stakeholder Extractor Service

Extracts potential stakeholders from meeting summaries and transcripts using LLM.
Uses Claude Sonnet for high-quality extraction of names, roles, departments,
concerns, interests, sentiment, and influence level.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Optional

import anthropic

logger = logging.getLogger(__name__)


@dataclass
class ExtractedStakeholder:
    """A potential stakeholder extracted from content."""

    name: str
    role: Optional[str] = None
    department: Optional[str] = None
    organization: Optional[str] = None
    email: Optional[str] = None

    # Context from extraction
    key_concerns: list[str] = field(default_factory=list)
    interests: list[str] = field(default_factory=list)
    initial_sentiment: Optional[str] = None  # positive/neutral/negative
    influence_level: Optional[str] = None  # high/medium/low

    # Source tracking
    source_document: str = ""
    source_text: str = ""  # Evidence quote
    extraction_context: str = ""  # Meeting context

    # Extraction metadata
    confidence: str = "medium"  # high/medium/low


class StakeholderExtractor:
    """Extracts potential stakeholders from document content using LLM."""

    def __init__(self, anthropic_client: Optional[anthropic.Anthropic] = None):
        self.anthropic = anthropic_client

    async def extract_with_llm(
        self,
        text: str,
        source_document: str,
        document_date: Optional[str] = None,
    ) -> list[ExtractedStakeholder]:
        """Use LLM to extract stakeholders from meeting content.

        Args:
            text: The document content to analyze
            source_document: Name/identifier of the source document
            document_date: Optional date of the document

        Returns:
            List of ExtractedStakeholder objects
        """
        if not self.anthropic:
            logger.warning("No Anthropic client available for stakeholder extraction")
            return []

        try:
            date_str = f" (dated {document_date})" if document_date else ""

            prompt = f"""Analyze this meeting summary/transcript and identify KEY STAKEHOLDERS who were discussed or participated.

Document: "{source_document}"{date_str}

A stakeholder is:
- A person mentioned by name who has influence over or is affected by AI/business initiatives
- Someone with a clear role, concerns, or interests mentioned in the document
- A decision-maker, team lead, or subject matter expert

NOT a stakeholder for our purposes:
- Generic references ("the team", "management", "someone")
- The meeting host/author unless they have a clear stakeholder role
- People only mentioned in passing without context

For each stakeholder found, extract:
- name: Full name as mentioned
- role: Job title or function if mentioned
- department: Which department they're in (finance, IT, legal, HR, marketing, operations, etc.)
- organization: Company name if different from the default
- email: Email address if mentioned
- key_concerns: What they're worried about or pushing back on
- interests: What they're excited about or advocating for
- initial_sentiment: Their attitude toward AI/the initiative (positive/neutral/negative)
- influence_level: How much decision-making power they have (high/medium/low)
- source_text: A direct quote that shows this person's involvement or stance
- extraction_context: Brief summary of the meeting context

Return a JSON array. If there are NO clear stakeholders, return: []

Example output:
```json
[
  {{
    "name": "Sarah Chen",
    "role": "VP of Finance",
    "department": "finance",
    "organization": null,
    "email": null,
    "key_concerns": ["budget constraints", "ROI visibility"],
    "interests": ["automation of manual reporting"],
    "initial_sentiment": "neutral",
    "influence_level": "high",
    "source_text": "Sarah expressed concerns about the budget but was interested in the reporting automation potential",
    "extraction_context": "Quarterly planning meeting discussing AI initiative priorities"
  }}
]
```

DOCUMENT CONTENT:
{text[:10000]}"""

            # Use Sonnet for quality extraction
            response = self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = response.content[0].text.strip()
            logger.debug(f"Stakeholder extraction response: {response_text[:500]}")

            # Parse JSON response
            stakeholders = self._parse_response(response_text, source_document)
            logger.info(f"Extracted {len(stakeholders)} stakeholders from {source_document}")
            return stakeholders

        except Exception as e:
            logger.error(f"Stakeholder extraction failed: {e}")
            return []

    def _parse_response(
        self, response_text: str, source_document: str
    ) -> list[ExtractedStakeholder]:
        """Parse LLM response into ExtractedStakeholder objects."""
        try:
            # Handle potential markdown code blocks
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            stakeholders_data = json.loads(response_text)
            if not isinstance(stakeholders_data, list):
                logger.warning("LLM response not a list")
                return []

            stakeholders = []
            for item in stakeholders_data:
                if not isinstance(item, dict) or "name" not in item:
                    continue

                name = item.get("name", "").strip()
                if len(name) < 2:
                    continue

                # Skip multi-person entries (e.g., "ashley/tricia", "tyler & charlie")
                if self._is_multi_person(name):
                    logger.debug(f"Skipping multi-person entry: {name}")
                    continue

                # Normalize department to lowercase
                department = item.get("department")
                if department:
                    department = department.lower().strip()

                # Normalize sentiment
                sentiment = item.get("initial_sentiment")
                if sentiment:
                    sentiment = sentiment.lower().strip()
                    if sentiment not in ("positive", "neutral", "negative"):
                        sentiment = "neutral"

                # Normalize influence level
                influence = item.get("influence_level")
                if influence:
                    influence = influence.lower().strip()
                    if influence not in ("high", "medium", "low"):
                        influence = "medium"

                # Ensure lists
                key_concerns = item.get("key_concerns", [])
                if not isinstance(key_concerns, list):
                    key_concerns = [key_concerns] if key_concerns else []

                interests = item.get("interests", [])
                if not isinstance(interests, list):
                    interests = [interests] if interests else []

                # Determine confidence based on available info
                confidence = self._calculate_confidence(item)

                stakeholders.append(
                    ExtractedStakeholder(
                        name=name,
                        role=item.get("role"),
                        department=department,
                        organization=item.get("organization"),
                        email=item.get("email"),
                        key_concerns=key_concerns,
                        interests=interests,
                        initial_sentiment=sentiment,
                        influence_level=influence,
                        source_document=source_document,
                        source_text=item.get("source_text", "")[:500],
                        extraction_context=item.get("extraction_context", "")[:500],
                        confidence=confidence,
                    )
                )

            return stakeholders

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM JSON response: {e}")
            return []
        except Exception as e:
            logger.warning(f"Error parsing stakeholder response: {e}")
            return []

    def _is_multi_person(self, name: str) -> bool:
        """Check if a name represents multiple people."""
        # Common separators for multiple people
        multi_person_patterns = [
            "/",  # ashley/tricia
            " & ",  # tyler & charlie
            " and ",  # tyler and charlie
            ", and ",  # tyler, and charlie
            " + ",  # tyler + charlie
            " or ",  # tyler or charlie (ambiguous reference)
        ]

        name_lower = name.lower()
        for pattern in multi_person_patterns:
            if pattern in name_lower:
                return True

        # Check for patterns like "Name1, Name2" (but not "Last, First")
        # If there's a comma and both parts look like first names (no spaces), it's likely multiple people
        if ", " in name:
            parts = name.split(", ")
            # "Last, First" typically has 2 parts where second part has no comma
            # "Name1, Name2" would have simple names on both sides
            if len(parts) == 2:
                # If both parts are single words and roughly same length, likely multiple people
                if " " not in parts[0] and " " not in parts[1]:
                    # Probably "FirstName1, FirstName2" not "LastName, FirstName"
                    if len(parts[0]) < 15 and len(parts[1]) < 15:
                        return True

        return False

    def _calculate_confidence(self, item: dict) -> str:
        """Calculate extraction confidence based on available information."""
        score = 0

        # Name always present (required)
        score += 1

        # Role adds confidence
        if item.get("role"):
            score += 2

        # Department adds confidence
        if item.get("department"):
            score += 1

        # Source text (evidence) adds confidence
        if item.get("source_text") and len(item["source_text"]) > 20:
            score += 2

        # Concerns or interests add confidence (shows deeper analysis)
        if item.get("key_concerns") or item.get("interests"):
            score += 1

        # Map score to confidence level
        if score >= 6:
            return "high"
        elif score >= 3:
            return "medium"
        else:
            return "low"


def format_extracted_stakeholders_for_display(stakeholders: list[ExtractedStakeholder]) -> str:
    """Format extracted stakeholders for display to user."""
    if not stakeholders:
        return "No potential stakeholders found in this content."

    parts = [f"**{len(stakeholders)} potential stakeholder(s) found:**\n"]

    for i, s in enumerate(stakeholders, 1):
        role_str = f" - {s.role}" if s.role else ""
        dept_str = f" ({s.department})" if s.department else ""
        sentiment_str = f"Sentiment: {s.initial_sentiment}" if s.initial_sentiment else ""
        influence_str = f"Influence: {s.influence_level}" if s.influence_level else ""

        meta_parts = [x for x in [sentiment_str, influence_str] if x]
        meta_str = f"\n   {' | '.join(meta_parts)}" if meta_parts else ""

        concerns_str = ""
        if s.key_concerns:
            concerns_str = f"\n   Concerns: {', '.join(s.key_concerns[:3])}"

        interests_str = ""
        if s.interests:
            interests_str = f"\n   Interests: {', '.join(s.interests[:3])}"

        parts.append(
            f"{i}. **{s.name}**{role_str}{dept_str}"
            f"\n   [{s.confidence} confidence]"
            f"{meta_str}{concerns_str}{interests_str}\n"
        )

    return "\n".join(parts)
