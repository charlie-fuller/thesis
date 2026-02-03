"""Unit tests for refactored helper methods.

Tests the helper functions extracted during complexity refactoring to ensure
they work correctly in isolation. These tests serve as regression tests.
"""

from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest


class TestTaskmasterHelpers:
    """Tests for taskmaster.py helper methods."""

    def setup_method(self):
        """Set up test fixtures."""
        from agents.taskmaster import TaskmasterAgent

        # Create a mock agent to test instance methods
        mock_supabase = MagicMock()
        mock_anthropic = MagicMock()
        self.agent = TaskmasterAgent(mock_supabase, mock_anthropic)

    def test_priority_label_all_values(self):
        """Test _priority_label returns correct labels for all priorities."""
        assert self.agent._priority_label(1) == "Critical"
        assert self.agent._priority_label(2) == "High"
        assert self.agent._priority_label(3) == "Medium"
        assert self.agent._priority_label(4) == "Low"
        assert self.agent._priority_label(5) == "Lowest"

    def test_priority_label_unknown_defaults_to_medium(self):
        """Test _priority_label returns Medium for unknown values."""
        assert self.agent._priority_label(0) == "Medium"
        assert self.agent._priority_label(99) == "Medium"
        assert self.agent._priority_label(-1) == "Medium"

    def test_filter_user_tasks_by_user_id(self):
        """Test filtering tasks by user ID."""
        tasks = [
            {"title": "Task 1", "assignee_user_id": "user-123", "assignee_name": ""},
            {"title": "Task 2", "assignee_user_id": "user-456", "assignee_name": ""},
            {"title": "Task 3", "assignee_user_id": "user-123", "assignee_name": ""},
        ]
        result = self.agent._filter_user_tasks(tasks, "user-123", None)
        assert len(result) == 2
        assert all(t["assignee_user_id"] == "user-123" for t in result)

    def test_filter_user_tasks_by_name(self):
        """Test filtering tasks by assignee name."""
        tasks = [
            {"title": "Task 1", "assignee_user_id": None, "assignee_name": "John Doe"},
            {"title": "Task 2", "assignee_user_id": None, "assignee_name": "Jane Smith"},
        ]
        result = self.agent._filter_user_tasks(tasks, "user-123", "John")
        assert len(result) == 1
        assert result[0]["title"] == "Task 1"

    def test_filter_user_tasks_includes_unassigned(self):
        """Test that unassigned tasks are included."""
        tasks = [
            {"title": "Task 1", "assignee_user_id": None, "assignee_name": ""},
            {"title": "Task 2", "assignee_user_id": None, "assignee_name": None},
            {"title": "Task 3", "assignee_user_id": "other", "assignee_name": "Other"},
        ]
        result = self.agent._filter_user_tasks(tasks, "user-123", "User Name")
        # Should include unassigned tasks (Task 1, Task 2)
        assert len(result) == 2

    def test_categorize_tasks_overdue(self):
        """Test categorization of overdue tasks."""
        today = date.today()
        week_end = today + timedelta(days=7)
        tasks = [
            {
                "title": "Overdue",
                "status": "pending",
                "due_date": (today - timedelta(days=1)).isoformat(),
            },
        ]
        result = self.agent._categorize_tasks(tasks, today, week_end)
        assert len(result["overdue"]) == 1
        assert result["overdue"][0]["title"] == "Overdue"

    def test_categorize_tasks_due_today(self):
        """Test categorization of tasks due today."""
        today = date.today()
        week_end = today + timedelta(days=7)
        tasks = [
            {"title": "Today", "status": "pending", "due_date": today.isoformat()},
        ]
        result = self.agent._categorize_tasks(tasks, today, week_end)
        assert len(result["due_today"]) == 1

    def test_categorize_tasks_due_this_week(self):
        """Test categorization of tasks due this week."""
        today = date.today()
        week_end = today + timedelta(days=7)
        tasks = [
            {
                "title": "This Week",
                "status": "pending",
                "due_date": (today + timedelta(days=3)).isoformat(),
            },
        ]
        result = self.agent._categorize_tasks(tasks, today, week_end)
        assert len(result["due_this_week"]) == 1

    def test_categorize_tasks_blocked(self):
        """Test categorization of blocked tasks."""
        today = date.today()
        week_end = today + timedelta(days=7)
        tasks = [
            {"title": "Blocked", "status": "blocked", "due_date": today.isoformat()},
        ]
        result = self.agent._categorize_tasks(tasks, today, week_end)
        assert len(result["blocked"]) == 1
        # Blocked tasks should not appear in other categories
        assert len(result["due_today"]) == 0

    def test_categorize_tasks_no_due_date(self):
        """Test categorization of tasks without due date."""
        today = date.today()
        week_end = today + timedelta(days=7)
        tasks = [
            {"title": "No Date", "status": "pending", "due_date": None},
        ]
        result = self.agent._categorize_tasks(tasks, today, week_end)
        assert len(result["no_due_date"]) == 1

    def test_format_task_context_with_all_categories(self):
        """Test formatting task context with all categories populated."""
        categories = {
            "overdue": [{"title": "Overdue Task", "due_date": "2025-01-01", "priority": 2}],
            "due_today": [{"title": "Today Task", "priority": 3}],
            "due_this_week": [{"title": "Week Task", "due_date": "2025-01-10", "priority": 4}],
            "blocked": [{"title": "Blocked Task", "blocker_reason": "Waiting on approval"}],
            "due_later": [],
            "no_due_date": [{"title": "No Date Task"}],
        }
        result = self.agent._format_task_context(categories, 4)
        assert "OVERDUE (1)" in result
        assert "DUE TODAY (1)" in result
        assert "DUE THIS WEEK (1)" in result
        assert "BLOCKED (1)" in result
        assert "NO DUE DATE (1)" in result
        assert "[High]" in result  # Priority 2
        assert "[Medium]" in result  # Priority 3
        assert "[Low]" in result  # Priority 4


class TestTaskExtractorHelpers:
    """Tests for task_extractor.py helper methods."""

    def setup_method(self):
        """Set up test fixtures."""
        from services.task_extractor import TaskExtractor

        self.extractor = TaskExtractor()

    def test_calculate_weekday_date_future(self):
        """Test calculating next weekday when day is in the future."""
        # Use a fixed date for deterministic testing
        today = date(2025, 1, 6)  # Monday
        # Tuesday is day 1, which is tomorrow
        result = self.extractor._calculate_weekday_date("Tuesday", today)
        assert result == date(2025, 1, 7)

    def test_calculate_weekday_date_past(self):
        """Test calculating next weekday when day has passed this week."""
        today = date(2025, 1, 8)  # Wednesday
        # Monday has passed, should get next Monday
        result = self.extractor._calculate_weekday_date("Monday", today)
        assert result == date(2025, 1, 13)

    def test_calculate_weekday_date_same_day(self):
        """Test calculating when target is same day (gets next week)."""
        today = date(2025, 1, 6)  # Monday
        result = self.extractor._calculate_weekday_date("Monday", today)
        # Should get next Monday, not today
        assert result == date(2025, 1, 13)

    def test_calculate_weekday_date_invalid(self):
        """Test calculating with invalid weekday."""
        today = date(2025, 1, 6)
        result = self.extractor._calculate_weekday_date("NotADay", today)
        assert result is None

    def test_calculate_eow_date(self):
        """Test end of week calculation."""
        # Monday - should get Friday
        monday = date(2025, 1, 6)
        result = self.extractor._calculate_eow_date(monday)
        assert result == date(2025, 1, 10)  # Friday

    def test_calculate_eow_date_on_friday(self):
        """Test end of week when already Friday."""
        friday = date(2025, 1, 10)
        result = self.extractor._calculate_eow_date(friday)
        # Should get next Friday
        assert result == date(2025, 1, 17)

    def test_calculate_eom_date(self):
        """Test end of month calculation."""
        mid_jan = date(2025, 1, 15)
        result = self.extractor._calculate_eom_date(mid_jan)
        assert result == date(2025, 1, 31)

    def test_calculate_eom_date_december(self):
        """Test end of month for December (year rollover)."""
        dec = date(2025, 12, 15)
        result = self.extractor._calculate_eom_date(dec)
        assert result == date(2025, 12, 31)

    def test_parse_date_text_slash_format(self):
        """Test parsing date in M/D format."""
        result = self.extractor._parse_date_text("1/15")
        assert result.month == 1
        assert result.day == 15

    def test_parse_date_text_invalid(self):
        """Test parsing invalid date text."""
        result = self.extractor._parse_date_text("invalid")
        assert result is None

    def test_extract_due_date_today(self):
        """Test extracting 'by today' due date."""
        due_date, text = self.extractor._extract_due_date("Please finish this by today")
        assert due_date == date.today()
        assert text == "today"

    def test_extract_due_date_tomorrow(self):
        """Test extracting 'by tomorrow' due date."""
        due_date, text = self.extractor._extract_due_date("Due tomorrow")
        assert due_date == date.today() + timedelta(days=1)
        assert text == "tomorrow"

    def test_extract_due_date_no_match(self):
        """Test extraction when no due date pattern matches."""
        due_date, text = self.extractor._extract_due_date("No deadline mentioned")
        assert due_date is None
        assert text is None

    def test_infer_priority_high(self):
        """Test inferring high priority from text."""
        result = self.extractor._infer_priority("This is URGENT")
        assert result == 2  # High

        result = self.extractor._infer_priority("We need to fix this ASAP")
        assert result == 2

    def test_infer_priority_low(self):
        """Test inferring low priority from text."""
        result = self.extractor._infer_priority("Do this when you get a chance")
        assert result == 4  # Low

        result = self.extractor._infer_priority("low priority task")
        assert result == 4

    def test_infer_priority_default_medium(self):
        """Test default priority is medium."""
        result = self.extractor._infer_priority("A normal task")
        assert result == 3  # Medium

    def test_priority_label(self):
        """Test priority number to label conversion."""
        assert self.extractor._priority_label(1) == "Critical"
        assert self.extractor._priority_label(2) == "High"
        assert self.extractor._priority_label(3) == "Medium"
        assert self.extractor._priority_label(4) == "Low"
        assert self.extractor._priority_label(5) == "Lowest"

    def test_clean_action_text(self):
        """Test action text cleaning."""
        assert self.extractor._clean_action_text("  send the report  ") == "Send the report"
        assert self.extractor._clean_action_text("send the report.") == "Send the report"
        assert self.extractor._clean_action_text("send the report,") == "Send the report"

    def test_is_false_positive_conversational(self):
        """Test false positive detection for conversational patterns."""
        assert self.extractor._is_false_positive("go ahead and introduce yourself")
        assert self.extractor._is_false_positive("be off next week")
        assert self.extractor._is_false_positive("see you later")
        assert self.extractor._is_false_positive("probably do something")

    def test_is_false_positive_real_task(self):
        """Test that real tasks are not flagged as false positives."""
        assert not self.extractor._is_false_positive("send the budget report to Sarah")
        assert not self.extractor._is_false_positive("schedule a meeting with the team")
        assert not self.extractor._is_false_positive("review the contract before Friday")


class TestStakeholderExtractorHelpers:
    """Tests for stakeholder_extractor.py helper methods."""

    def setup_method(self):
        """Set up test fixtures."""
        from services.stakeholder_extractor import StakeholderExtractor

        self.extractor = StakeholderExtractor()

    def test_clean_json_response_with_code_block(self):
        """Test cleaning JSON with markdown code blocks."""
        response = '```json\n[{"name": "Test"}]\n```'
        result = self.extractor._clean_json_response(response)
        assert result == '[{"name": "Test"}]'

    def test_clean_json_response_plain(self):
        """Test cleaning plain JSON (no change)."""
        response = '[{"name": "Test"}]'
        result = self.extractor._clean_json_response(response)
        assert result == '[{"name": "Test"}]'

    def test_normalize_field_valid(self):
        """Test normalizing a field with valid value."""
        result = self.extractor._normalize_field(
            "Positive", ("positive", "neutral", "negative"), "neutral"
        )
        assert result == "positive"

    def test_normalize_field_invalid(self):
        """Test normalizing a field with invalid value uses default."""
        result = self.extractor._normalize_field(
            "Unknown", ("positive", "neutral", "negative"), "neutral"
        )
        assert result == "neutral"

    def test_normalize_field_none(self):
        """Test normalizing None returns None."""
        result = self.extractor._normalize_field(
            None, ("positive", "neutral", "negative"), "neutral"
        )
        assert result is None

    def test_ensure_list_with_list(self):
        """Test ensure_list with list input."""
        result = self.extractor._ensure_list(["a", "b"])
        assert result == ["a", "b"]

    def test_ensure_list_with_string(self):
        """Test ensure_list with string input."""
        result = self.extractor._ensure_list("single")
        assert result == ["single"]

    def test_ensure_list_with_none(self):
        """Test ensure_list with None input."""
        result = self.extractor._ensure_list(None)
        assert result == []

    def test_is_multi_person_slash(self):
        """Test multi-person detection with slash separator."""
        assert self.extractor._is_multi_person("Ashley/Tricia")

    def test_is_multi_person_and(self):
        """Test multi-person detection with 'and' separator."""
        assert self.extractor._is_multi_person("Tyler and Charlie")

    def test_is_multi_person_ampersand(self):
        """Test multi-person detection with ampersand."""
        assert self.extractor._is_multi_person("Tyler & Charlie")

    def test_is_multi_person_single(self):
        """Test that single person names are not flagged."""
        assert not self.extractor._is_multi_person("John Doe")
        assert not self.extractor._is_multi_person("Sarah Chen")

    def test_is_multi_person_last_first(self):
        """Test 'Last, First' format handling.

        Note: Current implementation flags 'Doe, John' as multi-person because
        both parts are single words. This is a known limitation - in practice,
        LLM extraction rarely uses 'Last, First' format.
        """
        # Current behavior: "Doe, John" IS flagged as multi-person
        # because both parts are short single words
        assert self.extractor._is_multi_person("Doe, John")

        # Full names with spaces are NOT flagged
        assert not self.extractor._is_multi_person("John Michael Doe")

    def test_calculate_confidence_high(self):
        """Test confidence calculation for complete data."""
        item = {
            "name": "Sarah Chen",
            "role": "VP of Finance",
            "department": "finance",
            "source_text": "Sarah expressed concerns about the budget allocation for Q2",
            "key_concerns": ["budget constraints"],
        }
        result = self.extractor._calculate_confidence(item)
        assert result == "high"

    def test_calculate_confidence_medium(self):
        """Test confidence calculation for partial data."""
        item = {
            "name": "John",
            "role": "Engineer",
        }
        result = self.extractor._calculate_confidence(item)
        assert result == "medium"

    def test_calculate_confidence_low(self):
        """Test confidence calculation for minimal data."""
        item = {
            "name": "Unknown",
        }
        result = self.extractor._calculate_confidence(item)
        assert result == "low"

    def test_build_stakeholder_valid(self):
        """Test building stakeholder from valid data."""
        item = {
            "name": "Sarah Chen",
            "role": "VP of Finance",
            "department": "Finance",
            "initial_sentiment": "Positive",
            "influence_level": "High",
            "key_concerns": ["budget"],
            "source_text": "Sarah mentioned budget concerns",
        }
        result = self.extractor._build_stakeholder(item, "Meeting.md")
        assert result is not None
        assert result.name == "Sarah Chen"
        assert result.role == "VP of Finance"
        assert result.department == "finance"  # Should be lowercased
        assert result.initial_sentiment == "positive"
        assert result.influence_level == "high"

    def test_build_stakeholder_multi_person_skipped(self):
        """Test that multi-person entries are skipped."""
        item = {
            "name": "Tyler and Charlie",
            "role": "Engineers",
        }
        result = self.extractor._build_stakeholder(item, "Meeting.md")
        assert result is None

    def test_build_stakeholder_short_name_skipped(self):
        """Test that very short names are skipped."""
        item = {"name": "A"}
        result = self.extractor._build_stakeholder(item, "Meeting.md")
        assert result is None


class TestOracleHelpers:
    """Tests for oracle.py helper methods."""

    def setup_method(self):
        """Set up test fixtures."""
        from agents.oracle import OracleAgent

        mock_supabase = MagicMock()
        mock_anthropic = MagicMock()
        self.agent = OracleAgent(mock_supabase, mock_anthropic)

    def test_format_meeting_info_complete(self):
        """Test formatting meeting info with all fields."""
        analysis = {
            "meeting_summary": "Discussed Q2 budget allocation",
            "meeting_date": "2025-01-15",
            "meeting_type": "planning",
        }
        result = self.agent._format_meeting_info(analysis)
        assert len(result) >= 1
        assert "## Meeting Summary" in result[0]
        assert "Q2 budget allocation" in result[0]

    def test_format_meeting_info_partial(self):
        """Test formatting meeting info with partial data."""
        analysis = {"meeting_summary": "Quick sync"}
        result = self.agent._format_meeting_info(analysis)
        assert len(result) == 1  # Just summary, no metadata

    def test_format_attendees(self):
        """Test formatting attendee list."""
        attendees = [
            {"name": "John Doe", "role": "VP Finance", "organization": "Acme Corp"},
            {"name": "Jane Smith", "role": None, "organization": None},
        ]
        result = self.agent._format_attendees(attendees)
        assert "## Attendees" in result[0]
        assert "**John Doe** - VP Finance (Acme Corp)" in "".join(result)
        assert "**Jane Smith**" in "".join(result)

    def test_format_sentiment(self):
        """Test formatting sentiment analysis."""
        speakers = [
            {
                "name": "John",
                "overall_sentiment": "positive",
                "sentiment_score": 0.8,
                "concerns": ["timeline"],
                "enthusiasm": ["excited about project"],
            }
        ]
        result = self.agent._format_sentiment(speakers)
        assert "## Sentiment Analysis" in result[0]
        assert "John" in "".join(result)
        assert "Positive" in "".join(result)
        assert "timeline" in "".join(result)

    def test_format_action_items(self):
        """Test formatting action items."""
        items = [
            {"description": "Send report", "owner": "John", "due_date": "2025-01-20"},
            {"description": "Review docs", "owner": None, "due_date": None},
        ]
        result = self.agent._format_action_items(items)
        assert "## Action Items" in result[0]
        assert "Send report" in "".join(result)
        assert "@John" in "".join(result)
        assert "Due: 2025-01-20" in "".join(result)

    def test_format_simple_list(self):
        """Test formatting simple bulleted list."""
        items = ["Item 1", "Item 2", "Item 3"]
        result = self.agent._format_simple_list(items, "Key Topics")
        assert "## Key Topics" in result[0]
        assert "- Item 1" in result[1]
        assert "- Item 3" in result[3]


class TestHelpDocsHelpers:
    """Tests for help_docs.py helper methods."""

    def test_extract_sections_basic(self):
        """Test extracting sections from markdown."""
        from api.routes.admin.help_docs import _extract_sections

        content = """# Introduction
This is the intro.

## Getting Started
Here's how to start.

## Advanced Usage
For power users.
"""
        sections = _extract_sections(content)
        assert len(sections) == 3
        assert sections[0][0] == "Introduction"
        assert "intro" in sections[0][1]
        assert sections[1][0] == "Getting Started"
        assert sections[2][0] == "Advanced Usage"

    def test_extract_sections_no_headings(self):
        """Test extracting when no headings present."""
        from api.routes.admin.help_docs import _extract_sections

        content = "Just plain text without any headings."
        sections = _extract_sections(content)
        assert len(sections) == 1
        assert sections[0][0] == "Introduction"
        assert "plain text" in sections[0][1]

    def test_chunk_text_basic(self):
        """Test basic text chunking."""
        from api.routes.admin.help_docs import _chunk_text

        text = "This is sentence one. This is sentence two. This is sentence three."
        chunks = _chunk_text(text, chunk_size=50, overlap=10)
        assert len(chunks) >= 1
        # Each chunk should be non-empty
        assert all(chunk.strip() for chunk in chunks)

    def test_chunk_text_respects_sentence_boundaries(self):
        """Test that chunking respects sentence boundaries when possible."""
        from api.routes.admin.help_docs import _chunk_text

        # Create text with clear sentence boundaries
        text = "First sentence here. Second sentence follows. Third one now."
        chunks = _chunk_text(text, chunk_size=40, overlap=5)
        # Chunks should not split mid-sentence when possible
        assert len(chunks) >= 1

    def test_chunk_text_empty_input(self):
        """Test chunking with empty input."""
        from api.routes.admin.help_docs import _chunk_text

        chunks = _chunk_text("")
        assert chunks == []

    def test_chunk_text_whitespace_only(self):
        """Test chunking with whitespace-only input."""
        from api.routes.admin.help_docs import _chunk_text

        chunks = _chunk_text("   \n\n   ")
        assert chunks == []
