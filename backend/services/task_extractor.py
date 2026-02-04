"""Task Extractor Service.

Extracts potential tasks from KB documents and meeting transcripts.
Supports both explicit patterns ("I will...") and inferred patterns
(context suggests user responsibility).
"""

import logging
import re
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

import anthropic

logger = logging.getLogger(__name__)


@dataclass
class ExtractedTask:
    """A potential task extracted from content."""

    title: str
    priority: int  # 1-5
    priority_label: str
    due_date: Optional[date]
    due_date_text: Optional[str]  # Original text like "by Friday"
    assignee_name: Optional[str]
    source_document: str
    source_text: str  # The original text that led to this extraction
    confidence: str  # 'high' for explicit, 'medium' for inferred
    extraction_pattern: str  # Which pattern matched
    # Rich context fields (populated by LLM extraction)
    description: Optional[str] = None  # Full description with context
    meeting_context: Optional[str] = None  # Summary of meeting/document context
    team: Optional[str] = None  # Team or department involved
    stakeholder_name: Optional[str] = None  # Key stakeholder or requester
    value_proposition: Optional[str] = None  # Business value or impact
    topics: Optional[list[str]] = None  # Related topics/tags


# Task verb pattern for task-like content detection
TASK_VERB_PATTERN = r"\b(?:send|create|write|prepare|review|complete|finish|submit|deliver|schedule|set\s+up|follow[\s-]?up|update|check|confirm|arrange|book|draft|finalize|investigate|research|analyze|compile|document|share|circulate|distribute|forward|reach\s+out|contact|call|email|message|post|publish|upload|download|fix|resolve|address|handle|process|implement|deploy|clean|organize|plan|design|test|validate|notify|remind|track|monitor)\b"

# Explicit patterns (high confidence)
EXPLICIT_PATTERNS = [
    # "I will [action]" patterns (reduced minimum from 10 to 5)
    (r"I(?:'ll| will)\s+(.{5,100}?)(?:\.|$|,\s*(?:and|but))", "i_will"),
    # "Action: [name] to [action]" patterns
    (r"Action:\s*(\w+(?:\s+\w+)?)\s+to\s+(.{5,100}?)(?:\.|$)", "action_to"),
    # "[name] to follow up" patterns
    (r"(\w+(?:\s+\w+)?)\s+to\s+follow\s*up\s+(?:on\s+)?(.{5,100}?)(?:\.|$)", "follow_up"),
    # "[name] owns [deliverable]" patterns
    (r"(\w+(?:\s+\w+)?)\s+owns\s+(.{5,100}?)(?:\.|$)", "owns"),
    # "TODO: [action]" patterns
    (r"TODO:\s*(.{5,200}?)(?:\.|$|\n)", "todo"),
    # "Next step: [action]" patterns
    (r"Next\s+step[s]?:\s*(.{5,200}?)(?:\.|$|\n)", "next_step"),
    # Markdown checkbox patterns: "- [ ] Task" or "* [ ] Task" (always tasks)
    (r"[-*]\s*\[\s*\]\s*(.{5,200}?)(?:\n|$)", "checkbox_unchecked"),
]

# Inferred patterns (medium confidence)
INFERRED_PATTERNS = [
    # "[name] mentioned they would [action]"
    (
        r"(\w+(?:\s+\w+)?)\s+(?:mentioned|said)\s+(?:they|he|she)\s+would\s+(.{10,100}?)(?:\.|$)",
        "mentioned_would",
    ),
    # "We agreed that [name] will [action]"
    (r"[Ww]e\s+agreed\s+that\s+(\w+(?:\s+\w+)?)\s+will\s+(.{10,100}?)(?:\.|$)", "agreed_will"),
    # "[name] is responsible for [deliverable]"
    (r"(\w+(?:\s+\w+)?)\s+is\s+responsible\s+for\s+(.{10,100}?)(?:\.|$)", "responsible_for"),
    # "[name] needs to [action]"
    (r"(\w+(?:\s+\w+)?)\s+needs\s+to\s+(.{10,100}?)(?:\.|$)", "needs_to"),
    # "[name] should [action]"
    (r"(\w+(?:\s+\w+)?)\s+should\s+(.{10,100}?)(?:\.|$)", "should"),
]

# Due date patterns
DUE_DATE_PATTERNS = [
    (r"by\s+(today)", 0),
    (r"by\s+(tomorrow)", 1),
    (r"by\s+(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)", "weekday"),
    (r"by\s+(end\s+of\s+(?:this\s+)?week)", "eow"),
    (r"by\s+(end\s+of\s+(?:this\s+)?month)", "eom"),
    (r"due\s+(today)", 0),
    (r"due\s+(tomorrow)", 1),
    (r"due\s+(\d{1,2}/\d{1,2}(?:/\d{2,4})?)", "date"),
    (r"(\d{1,2}/\d{1,2}(?:/\d{2,4})?)", "date"),
    (r"(next\s+week)", 7),
    (r"(this\s+week)", "eow"),
    (r"(ASAP|urgent|immediately)", 0),
]

# Priority signal patterns
PRIORITY_SIGNALS = {
    "high": [
        r"\b(urgent|ASAP|critical|immediately|high\s*priority|P1|blocking)\b",
        r"\b(must|need\s+to|have\s+to)\b",
    ],
    "low": [
        r"\b(when\s+you\s+(?:get\s+a\s+)?chance|low\s*priority|P4|P5|nice\s+to\s+have)\b",
        r"\b(if\s+(?:you\s+)?possible|eventually|someday)\b",
    ],
}

# False positive filters - phrases that look like tasks but aren't
# These are conversational speech patterns common in meeting transcripts
FALSE_POSITIVE_PATTERNS = [
    # Conversational intros
    r"^(?:just\s+)?(?:go\s+ahead|introduce|say|mention|start|begin)\b",
    r"^(?:just\s+)?(?:do\s+a\s+)?quick\s+intro",
    r"^(?:let\s+me\s+)?(?:just\s+)?(?:say|mention|note|add)\b",
    # Status/availability statements (not actionable)
    r"^be\s+(?:off|out|away|traveling|in|at|back)\b",
    r"^be\s+(?:there|here|around|available)\b",
    # Pleasantries
    r"^(?:let\s+you\s+)?(?:go|talk\s+to\s+you|catch\s+up)\b",
    r"^see\s+you\b",
    # Thinking out loud
    r"^(?:think|say|guess|assume|suppose)\b",
    r"^probably\b",
    r"^maybe\b",
    # Requests to others (not YOUR task)
    r"^(?:have|get|ask)\s+(?:you|them|someone|everybody)\b",
    # Self-referential speech patterns
    r"^(?:just\s+)?(?:keep|continue|move\s+on|wrap\s+up)\b",
    r"^(?:start|end|finish)\s+(?:with|by|off)\b",
    # Interview/meeting speech patterns
    r"^(?:kind\s+of\s+)?(?:dive|jump|get)\s+(?:into|in)\b",
    r"^turn\s+(?:it\s+)?over\s+to\b",
    r"^(?:go\s+)?(?:around|through)\s+(?:the|and)\b",
    r"^(?:hand|pass)\s+(?:it\s+)?(?:over|off)\s+to\b",
    r"^(?:open|close)\s+(?:it\s+)?up\s+(?:to|for)\b",
]

# Verbs that typically indicate real tasks
TASK_VERBS = [
    "send",
    "create",
    "write",
    "prepare",
    "review",
    "complete",
    "finish",
    "submit",
    "deliver",
    "schedule",
    "set up",
    "follow up",
    "follow-up",
    "update",
    "check",
    "confirm",
    "arrange",
    "book",
    "draft",
    "finalize",
    "investigate",
    "research",
    "analyze",
    "compile",
    "document",
    "share",
    "circulate",
    "distribute",
    "forward",
    "reach out",
    "contact",
    "call",
    "email",
    "message",
    "post",
    "publish",
    "upload",
    "download",
    "fix",
    "resolve",
    "address",
    "handle",
    "process",
    "implement",
    "deploy",
]


class TaskExtractor:
    """Extracts potential tasks from document content."""

    def __init__(self, anthropic_client: Optional[anthropic.Anthropic] = None):
        self.anthropic = anthropic_client

    def extract_from_text(
        self,
        text: str,
        source_document: str,
        user_name: Optional[str] = None,
        include_inferred: bool = True,
    ) -> list[ExtractedTask]:
        """Extract potential tasks from text content.

        Args:
            text: The text content to scan
            source_document: Name/identifier of the source document
            user_name: Optional user name to filter tasks for
            include_inferred: Whether to include medium-confidence inferred tasks

        Returns:
            List of ExtractedTask objects
        """
        tasks = []

        # Extract using explicit patterns (high confidence)
        for pattern, pattern_name in EXPLICIT_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                task = self._process_match(match, pattern_name, source_document, "high", user_name)
                if task:
                    tasks.append(task)

        # Extract using inferred patterns (medium confidence)
        if include_inferred:
            for pattern, pattern_name in INFERRED_PATTERNS:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    task = self._process_match(match, pattern_name, source_document, "medium", user_name)
                    if task:
                        tasks.append(task)

        # Deduplicate similar tasks
        tasks = self._deduplicate_tasks(tasks)

        return tasks

    async def extract_with_llm(
        self,
        text: str,
        source_document: str,
        user_name: Optional[str] = None,
        document_date: Optional[str] = None,
        use_fast_model: bool = False,
    ) -> list[ExtractedTask]:
        """Use LLM to extract tasks for complex or ambiguous content.

        Args:
            use_fast_model: If True, uses Haiku for speed (manual scans).
                           If False, uses Sonnet for quality (background extraction).

        Falls back to regex extraction if LLM is not available.
        """
        import json

        if not self.anthropic:
            logger.info("No Anthropic client, falling back to regex extraction")
            return self.extract_from_text(text, source_document, user_name)

        try:
            # Build context string
            date_str = f" (dated {document_date})" if document_date else ""
            user_str = f" for {user_name}" if user_name else ""

            prompt = f"""I need you to find action items{user_str} from this document: "{source_document}"{date_str}

Read this document and identify REAL tasks - things someone committed to DO after the meeting/conversation.

A task is:
- A specific deliverable someone agreed to complete
- Something with a clear owner (explicit or implied)
- An action that requires work AFTER this document was created

NOT a task:
- Meeting facilitation ("Let me share my screen", "Who wants to go next?")
- Vague discussion ("We should think about X")
- Status updates or completed work ("I finished the report")
- Questions or observations

For each genuine task found, return JSON:
{{
  "title": "Action verb + specific deliverable (e.g., 'Send budget proposal to Sarah')",
  "description": "2-3 sentences with FULL CONTEXT: What's the background? Why does this matter? What's the expected outcome? Include the document date.",
  "assignee": "Who owns this (name or '{user_name or "the author"}' for first-person commitments)",
  "priority": "high/medium/low",
  "source_text": "The exact quote that shows this commitment",
  "due_date_text": "Any mentioned deadline",
  "meeting_context": "What was this meeting/document about?",
  "stakeholder_name": "Who requested or cares about this?",
  "topics": ["relevant", "tags"]
}}

Return a JSON array. If there are NO genuine tasks, return: []

DOCUMENT CONTENT:
{text[:8000]}"""

            # Use Haiku for speed on manual scans, Sonnet for quality on background extraction
            model = "claude-haiku-4-20250514" if use_fast_model else "claude-sonnet-4-20250514"
            logger.info(f"Using {model} for task extraction (fast_mode={use_fast_model})")

            response = self.anthropic.messages.create(
                model=model, max_tokens=2048, messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text.strip()
            logger.debug(f"LLM extraction response: {response_text[:500]}")

            # Parse JSON response
            try:
                # Handle potential markdown code blocks
                if response_text.startswith("```"):
                    response_text = response_text.split("```")[1]
                    if response_text.startswith("json"):
                        response_text = response_text[4:]
                    response_text = response_text.strip()

                tasks_data = json.loads(response_text)
                if not isinstance(tasks_data, list):
                    logger.warning("LLM response not a list, falling back to regex")
                    return self.extract_from_text(text, source_document, user_name)

                tasks = []

                for item in tasks_data:
                    if not isinstance(item, dict) or "title" not in item:
                        continue

                    title = item.get("title", "").strip()
                    if len(title) < 5:
                        continue

                    # Handle priority - LLM returns 1-5 integer, but also accept string
                    raw_priority = item.get("priority", 3)
                    if isinstance(raw_priority, int):
                        priority = max(1, min(5, raw_priority))  # Clamp to 1-5
                    elif isinstance(raw_priority, str):
                        priority_map = {"high": 4, "medium": 3, "low": 2, "critical": 5}
                        priority = priority_map.get(raw_priority.lower(), 3)
                    else:
                        priority = 3

                    due_date_text = item.get("due_date_text")
                    due_date = None

                    # Try to parse due date
                    if due_date_text:
                        due_date, _ = self._extract_due_date(due_date_text)

                    # Extract topics (ensure it's a list)
                    topics = item.get("topics")
                    if topics and not isinstance(topics, list):
                        topics = [topics] if isinstance(topics, str) else None

                    # Get assignee - try both field names for compatibility
                    assignee = item.get("assignee_name") or item.get("assignee")

                    tasks.append(
                        ExtractedTask(
                            title=title[:200],
                            priority=priority,
                            priority_label=self._priority_label(priority),
                            due_date=due_date,
                            due_date_text=due_date_text,
                            assignee_name=assignee,
                            source_document=source_document,
                            source_text=item.get("source_text", "")[:300],
                            confidence=item.get("confidence", "high"),
                            extraction_pattern="llm",
                            # Rich context fields
                            description=item.get("description"),
                            meeting_context=item.get("meeting_context"),
                            team=item.get("team"),
                            stakeholder_name=item.get("stakeholder_name"),
                            value_proposition=item.get("value_proposition"),
                            topics=topics,
                        )
                    )

                logger.info(f"LLM extracted {len(tasks)} tasks from {source_document}")
                return tasks

            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse LLM JSON response: {e}")
                return self.extract_from_text(text, source_document, user_name)

        except Exception as e:
            logger.warning(f"LLM extraction failed, falling back to regex: {e}")
            return self.extract_from_text(text, source_document, user_name)

    def _process_match(
        self,
        match: re.Match,
        pattern_name: str,
        source_document: str,
        confidence: str,
        user_name: Optional[str],
    ) -> Optional[ExtractedTask]:
        """Process a regex match into an ExtractedTask."""
        groups = match.groups()
        source_text = match.group(0)

        # Extract assignee and action based on pattern type
        if pattern_name in [
            "i_will",
            "todo",
            "next_step",
            "checkbox_unchecked",
            "bullet_item",
            "numbered_item",
        ]:
            assignee = user_name  # "I will" or checklist items are the user's tasks
            action = groups[0].strip()
        elif pattern_name in [
            "action_to",
            "follow_up",
            "owns",
            "mentioned_would",
            "agreed_will",
            "responsible_for",
            "needs_to",
            "should",
        ]:
            assignee = groups[0].strip() if len(groups) > 1 else None
            action = groups[1].strip() if len(groups) > 1 else groups[0].strip()
        else:
            assignee = None
            action = groups[0].strip() if groups else source_text

        # Skip if we have a user_name filter and this doesn't match
        if user_name and assignee:
            # Check if assignee matches user name (case-insensitive, partial match)
            assignee_lower = assignee.lower()
            user_lower = user_name.lower()
            if not (user_lower in assignee_lower or assignee_lower in user_lower):
                # Also check for "I" which implies the user
                if assignee_lower not in ["i", "me", "my"]:
                    return None

        # Clean up the action text
        action = self._clean_action_text(action)
        if len(action) < 5:  # Too short to be meaningful
            return None

        # Check for false positives (conversational speech, not real tasks)
        if self._is_false_positive(action):
            logger.debug(f"Filtered false positive: {action[:50]}...")
            return None

        # Extract due date from surrounding context
        due_date, due_date_text = self._extract_due_date(source_text)

        # Determine priority from context
        priority = self._infer_priority(source_text)

        return ExtractedTask(
            title=action[:200],  # Limit title length
            priority=priority,
            priority_label=self._priority_label(priority),
            due_date=due_date,
            due_date_text=due_date_text,
            assignee_name=assignee,
            source_document=source_document,
            source_text=source_text[:300],
            confidence=confidence,
            extraction_pattern=pattern_name,
        )

    def _calculate_weekday_date(self, date_text: str, today: date) -> Optional[date]:
        """Calculate the next occurrence of a weekday."""
        weekdays = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6,
        }
        target_day = weekdays.get(date_text.lower())
        if target_day is None:
            return None
        days_ahead = target_day - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return today + timedelta(days=days_ahead)

    def _calculate_eow_date(self, today: date) -> date:
        """Calculate end of week (Friday)."""
        days_until_friday = (4 - today.weekday()) % 7
        if days_until_friday == 0:
            days_until_friday = 7
        return today + timedelta(days=days_until_friday)

    def _calculate_eom_date(self, today: date) -> date:
        """Calculate end of month."""
        if today.month == 12:
            return date(today.year + 1, 1, 1) - timedelta(days=1)
        return date(today.year, today.month + 1, 1) - timedelta(days=1)

    def _parse_date_text(self, date_text: str) -> Optional[date]:
        """Parse a date from text like '1/15' or '1/15/2025'."""
        try:
            parts = date_text.split("/")
            if len(parts) >= 2:
                return date.today().replace(month=int(parts[0]), day=int(parts[1]))
        except (ValueError, IndexError):
            pass
        return None

    def _extract_due_date(self, text: str) -> tuple[Optional[date], Optional[str]]:
        """Extract due date from text using patterns."""
        today = date.today()

        for pattern, offset in DUE_DATE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_text = match.group(1)

                if isinstance(offset, int):
                    return today + timedelta(days=offset), date_text

                if offset == "weekday":
                    result = self._calculate_weekday_date(date_text, today)
                    if result:
                        return result, date_text

                elif offset == "eow":
                    return self._calculate_eow_date(today), date_text

                elif offset == "eom":
                    return self._calculate_eom_date(today), date_text

                elif offset == "date":
                    result = self._parse_date_text(date_text)
                    if result:
                        return result, date_text

        return None, None

    def _infer_priority(self, text: str) -> int:
        """Infer priority from text signals."""
        text_lower = text.lower()

        # Check for high priority signals
        for pattern in PRIORITY_SIGNALS["high"]:
            if re.search(pattern, text_lower):
                return 2  # High

        # Check for low priority signals
        for pattern in PRIORITY_SIGNALS["low"]:
            if re.search(pattern, text_lower):
                return 4  # Low

        return 3  # Default to medium

    def _priority_label(self, priority: int) -> str:
        """Convert priority number to label."""
        labels = {1: "Critical", 2: "High", 3: "Medium", 4: "Low", 5: "Lowest"}
        return labels.get(priority, "Medium")

    def _clean_action_text(self, text: str) -> str:
        """Clean up extracted action text."""
        # Remove leading/trailing whitespace and punctuation
        text = text.strip().strip(".,;:")

        # Capitalize first letter
        if text:
            text = text[0].upper() + text[1:]

        return text

    def _is_false_positive(self, action_text: str) -> bool:
        """Check if the extracted action is a false positive (conversational speech, not a task)."""
        action_lower = action_text.lower().strip()

        # Check against false positive patterns
        for pattern in FALSE_POSITIVE_PATTERNS:
            if re.match(pattern, action_lower, re.IGNORECASE):
                return True

        # Check if "be off/away/traveling" appears anywhere (status statements)
        if re.search(r"\bbe\s+(?:off|out|away|traveling|back|there|here)\b", action_lower):
            return True

        # Check if it contains a real task verb
        has_task_verb = any(verb in action_lower for verb in TASK_VERBS)

        # If no task verb, more likely to be a false positive
        # Require longer text to compensate for missing task verb
        if not has_task_verb and len(action_lower.split()) < 8:
            return True

        # If starts with a fragment or incomplete word (like "Be." from bad extraction)
        if re.match(r"^[a-z]{1,3}\.\s", action_lower):
            return True

        return False

    def _deduplicate_tasks(self, tasks: list[ExtractedTask]) -> list[ExtractedTask]:
        """Remove duplicate or very similar tasks."""
        seen_titles = set()
        unique_tasks = []

        for task in tasks:
            # Normalize title for comparison
            normalized = task.title.lower().strip()

            # Check for exact or near duplicates
            is_duplicate = False
            for seen in seen_titles:
                # Simple similarity check
                if normalized == seen or normalized in seen or seen in normalized:
                    is_duplicate = True
                    break

            if not is_duplicate:
                seen_titles.add(normalized)
                unique_tasks.append(task)

        return unique_tasks


def format_extracted_tasks_for_display(tasks: list[ExtractedTask]) -> str:
    """Format extracted tasks for display to user."""
    if not tasks:
        return "No potential tasks found in this content."

    parts = [f"**{len(tasks)} potential task(s) found:**\n"]

    for i, task in enumerate(tasks, 1):
        confidence_marker = "" if task.confidence == "high" else " (inferred)"
        due_str = f"\n   Due: {task.due_date_text}" if task.due_date_text else ""
        assignee_str = f"\n   Assignee: {task.assignee_name}" if task.assignee_name else ""

        parts.append(
            f"{i}. **[{task.priority_label}]** {task.title}{confidence_marker}"
            f"\n   Source: {task.source_document}"
            f"{due_str}{assignee_str}\n"
        )

    parts.append('\nCreate any of these? (e.g., "create 1 and 3" or "create all")')

    return "\n".join(parts)
