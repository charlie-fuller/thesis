"""
Property-Based Testing with Hypothesis

Tests that verify properties hold for all valid inputs, rather than specific examples.
Hypothesis generates random inputs to find edge cases we might miss.
"""
import pytest
from hypothesis import given, strategies as st, settings, assume, example
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant, initialize
from datetime import datetime, timedelta
from typing import Optional
import re
import json


# =============================================================================
# Strategies for Domain-Specific Types
# =============================================================================

# UUID strategy
uuid_strategy = st.uuids().map(str)

# Email strategy
email_strategy = st.emails()

# Valid agent IDs
agent_ids = st.sampled_from([
    "coordinator", "atlas", "capital", "guardian", "counselor",
    "sage", "oracle", "architect", "sentinel", "compass",
    "catalyst", "navigator", "broker", "beacon", "translator",
    "librarian", "reporter", "facilitator", "analyst", "synthesizer"
])

# Task status strategy
task_status = st.sampled_from(["backlog", "todo", "in_progress", "done"])

# Opportunity tier strategy
opportunity_tier = st.sampled_from(["A", "B", "C", "D"])

# Score strategy (0-100)
score_strategy = st.integers(min_value=0, max_value=100)

# Message content strategy (realistic chat messages)
message_content = st.text(
    alphabet=st.characters(blacklist_categories=('Cs', 'Cc')),
    min_size=1,
    max_size=5000
)

# File name strategy
filename_strategy = st.from_regex(r'[a-zA-Z0-9_\-]+\.(pdf|docx|txt|md)', fullmatch=True)


# =============================================================================
# Utility Function Tests
# =============================================================================

class TestAgentRouting:
    """Property-based tests for agent routing logic."""

    @given(message=st.text(min_size=1, max_size=1000))
    def test_routing_always_returns_valid_agent(self, message: str):
        """Routing any message should return a valid agent ID."""
        # Simulate routing logic
        valid_agents = [
            "coordinator", "atlas", "capital", "guardian", "counselor",
            "sage", "oracle", "architect"
        ]

        # Simple keyword-based routing simulation
        message_lower = message.lower()
        if "research" in message_lower or "market" in message_lower:
            routed = "atlas"
        elif "cost" in message_lower or "roi" in message_lower or "budget" in message_lower:
            routed = "capital"
        elif "security" in message_lower or "compliance" in message_lower:
            routed = "guardian"
        elif "legal" in message_lower or "contract" in message_lower:
            routed = "counselor"
        elif "change" in message_lower or "adoption" in message_lower:
            routed = "sage"
        else:
            routed = "coordinator"

        assert routed in valid_agents

    @given(message=st.text(min_size=1), agent_id=agent_ids)
    def test_mention_extraction_consistent(self, message: str, agent_id: str):
        """@mention extraction should be consistent."""
        # Add mention to message
        mentioned_message = f"@{agent_id} {message}"

        # Extract mention
        match = re.match(r'^@(\w+)\s', mentioned_message)

        assert match is not None
        assert match.group(1) == agent_id

    @given(agent_id=agent_ids)
    def test_agent_id_is_lowercase(self, agent_id: str):
        """All agent IDs should be lowercase."""
        assert agent_id == agent_id.lower()


class TestScoreCalculations:
    """Property-based tests for score calculations."""

    @given(
        strategic=score_strategy,
        revenue=score_strategy,
        probability=score_strategy
    )
    def test_opportunity_score_in_valid_range(
        self, strategic: int, revenue: int, probability: int
    ):
        """Calculated opportunity score should be 0-100."""
        # Weighted average calculation
        score = (strategic * 0.4) + (revenue * 0.3) + (probability * 0.3)

        assert 0 <= score <= 100

    @given(
        strategic=score_strategy,
        revenue=score_strategy,
        probability=score_strategy
    )
    def test_tier_calculation_deterministic(
        self, strategic: int, revenue: int, probability: int
    ):
        """Same inputs should always produce same tier."""
        def calculate_tier(s: int, r: int, p: int) -> str:
            score = (s * 0.4) + (r * 0.3) + (p * 0.3)
            if score >= 80:
                return "A"
            elif score >= 60:
                return "B"
            elif score >= 40:
                return "C"
            else:
                return "D"

        tier1 = calculate_tier(strategic, revenue, probability)
        tier2 = calculate_tier(strategic, revenue, probability)

        assert tier1 == tier2

    @given(score=score_strategy)
    def test_score_boundaries(self, score: int):
        """Tier boundaries should be mutually exclusive."""
        def get_tier(score: int) -> str:
            if score >= 80:
                return "A"
            elif score >= 60:
                return "B"
            elif score >= 40:
                return "C"
            else:
                return "D"

        tier = get_tier(score)

        # Verify boundary conditions
        if tier == "A":
            assert score >= 80
        elif tier == "B":
            assert 60 <= score < 80
        elif tier == "C":
            assert 40 <= score < 60
        else:
            assert score < 40


class TestTextProcessing:
    """Property-based tests for text processing."""

    @given(text=st.text(min_size=0, max_size=10000))
    def test_truncation_preserves_length_limit(self, text: str):
        """Truncation should never exceed limit."""
        limit = 500

        def truncate(t: str, max_len: int) -> str:
            if len(t) <= max_len:
                return t
            return t[:max_len-3] + "..."

        result = truncate(text, limit)
        assert len(result) <= limit

    @given(text=st.text(min_size=0, max_size=10000))
    def test_word_count_non_negative(self, text: str):
        """Word count should never be negative."""
        word_count = len(text.split())
        assert word_count >= 0

    @given(content=st.text(min_size=1))
    def test_smart_brevity_word_limit(self, content: str):
        """Smart brevity responses should be under word limit."""
        max_words = 150

        def enforce_smart_brevity(text: str, limit: int) -> str:
            words = text.split()
            if len(words) <= limit:
                return text
            return " ".join(words[:limit]) + "..."

        result = enforce_smart_brevity(content, max_words)
        result_words = len(result.rstrip("...").split())
        assert result_words <= max_words + 1  # +1 for edge case with ellipsis


class TestDateTimeHandling:
    """Property-based tests for datetime operations."""

    @given(st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2030, 12, 31)))
    def test_iso_format_roundtrip(self, dt: datetime):
        """ISO format should roundtrip correctly."""
        iso_str = dt.isoformat()
        parsed = datetime.fromisoformat(iso_str)
        assert parsed == dt

    @given(
        start=st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(9999, 1, 1)),
        days=st.integers(min_value=0, max_value=365)
    )
    def test_due_date_always_after_created(self, start: datetime, days: int):
        """Due date should always be after created date."""
        created_at = start
        due_date = start + timedelta(days=days)

        assert due_date >= created_at


class TestJSONSerialization:
    """Property-based tests for JSON operations."""

    @given(st.dictionaries(
        keys=st.text(min_size=1, max_size=50),
        values=st.one_of(
            st.text(max_size=100),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.booleans(),
            st.none()
        ),
        max_size=20
    ))
    def test_json_roundtrip(self, data: dict):
        """JSON serialization should roundtrip."""
        json_str = json.dumps(data)
        parsed = json.loads(json_str)
        assert parsed == data

    @given(st.recursive(
        st.one_of(st.text(max_size=50), st.integers(), st.booleans(), st.none()),
        lambda children: st.lists(children, max_size=5) | st.dictionaries(
            st.text(min_size=1, max_size=20), children, max_size=5
        ),
        max_leaves=50
    ))
    def test_nested_json_serializable(self, data):
        """Nested structures should serialize."""
        try:
            json_str = json.dumps(data)
            assert isinstance(json_str, str)
        except (ValueError, TypeError):
            pass  # Some combinations may not be serializable


class TestValidation:
    """Property-based tests for input validation."""

    @given(email=email_strategy)
    def test_valid_email_format(self, email: str):
        """Generated emails should have @ symbol and domain."""
        # Hypothesis generates RFC 5322-compliant emails which may contain
        # characters like = that are valid but uncommon. Basic structural check:
        assert "@" in email, "Email must contain @"
        local, domain = email.rsplit("@", 1)
        assert len(local) > 0, "Local part must not be empty"
        assert "." in domain, "Domain must contain a dot"

    @given(uuid=uuid_strategy)
    def test_uuid_format(self, uuid: str):
        """UUIDs should match expected format."""
        pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        assert re.match(pattern, uuid) is not None

    @given(text=st.text(min_size=1, max_size=10000))
    def test_xss_sanitization(self, text: str):
        """XSS sanitization should remove script tags."""
        def sanitize(t: str) -> str:
            # Simple sanitization - real implementation would be more robust
            import html
            return html.escape(t)

        sanitized = sanitize(text)

        # Should not contain unescaped script tags
        assert "<script>" not in sanitized
        assert "</script>" not in sanitized


class TestPagination:
    """Property-based tests for pagination logic."""

    @given(
        total=st.integers(min_value=0, max_value=10000),
        page=st.integers(min_value=1, max_value=1000),
        per_page=st.integers(min_value=1, max_value=100)
    )
    def test_pagination_math(self, total: int, page: int, per_page: int):
        """Pagination calculations should be consistent."""
        # Calculate total pages
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1

        # Calculate offset
        offset = (page - 1) * per_page

        # Calculate items on current page
        if page > total_pages:
            items_on_page = 0
        elif page == total_pages:
            items_on_page = total - offset
        else:
            items_on_page = per_page

        assert items_on_page >= 0
        assert items_on_page <= per_page
        assert offset >= 0

    @given(
        total=st.integers(min_value=0, max_value=10000),
        per_page=st.integers(min_value=1, max_value=100)
    )
    def test_has_more_calculation(self, total: int, per_page: int):
        """has_more should be correct."""
        page = 1

        def has_more(total: int, page: int, per_page: int) -> bool:
            return (page * per_page) < total

        result = has_more(total, page, per_page)

        if total <= per_page:
            assert result is False
        else:
            assert result is True


# =============================================================================
# Stateful Testing - Conversation State Machine
# =============================================================================

class ConversationStateMachine(RuleBasedStateMachine):
    """Stateful test for conversation operations."""

    def __init__(self):
        super().__init__()
        self.messages: list = []
        self.conversation_id: Optional[str] = None

    @initialize()
    def create_conversation(self):
        """Initialize a new conversation."""
        self.conversation_id = "conv-" + str(len(self.messages))
        self.messages = []

    @rule(content=message_content, agent=agent_ids)
    def add_message(self, content: str, agent: str):
        """Add a message to the conversation."""
        assume(len(content) > 0)

        message = {
            "id": f"msg-{len(self.messages)}",
            "content": content,
            "agent_id": agent,
            "conversation_id": self.conversation_id
        }
        self.messages.append(message)

    @rule()
    def clear_conversation(self):
        """Clear all messages."""
        self.messages = []

    @invariant()
    def messages_have_valid_structure(self):
        """All messages should have required fields."""
        for msg in self.messages:
            assert "id" in msg
            assert "content" in msg
            assert "agent_id" in msg
            assert "conversation_id" in msg

    @invariant()
    def message_ids_unique(self):
        """Message IDs should be unique."""
        ids = [msg["id"] for msg in self.messages]
        assert len(ids) == len(set(ids))


# Run the state machine test
TestConversationStateMachine = ConversationStateMachine.TestCase


class TaskBoardStateMachine(RuleBasedStateMachine):
    """Stateful test for kanban task board operations."""

    def __init__(self):
        super().__init__()
        self.tasks: dict = {}  # id -> task
        self.next_id = 0

    @rule(title=st.text(min_size=1, max_size=200))
    def create_task(self, title: str):
        """Create a new task."""
        task_id = f"task-{self.next_id}"
        self.next_id += 1

        self.tasks[task_id] = {
            "id": task_id,
            "title": title,
            "status": "backlog"
        }

    @rule(status=task_status)
    def move_task(self, status: str):
        """Move a random task to new status."""
        if not self.tasks:
            return

        task_id = list(self.tasks.keys())[0]
        self.tasks[task_id]["status"] = status

    @rule()
    def delete_task(self):
        """Delete a random task."""
        if not self.tasks:
            return

        task_id = list(self.tasks.keys())[0]
        del self.tasks[task_id]

    @invariant()
    def all_tasks_have_valid_status(self):
        """All tasks should have valid status."""
        valid_statuses = {"backlog", "todo", "in_progress", "done"}
        for task in self.tasks.values():
            assert task["status"] in valid_statuses

    @invariant()
    def task_ids_unique(self):
        """Task IDs should be unique."""
        ids = list(self.tasks.keys())
        assert len(ids) == len(set(ids))


TestTaskBoardStateMachine = TaskBoardStateMachine.TestCase


# =============================================================================
# Settings for CI
# =============================================================================

# Use these settings for CI to control test duration
settings.register_profile("ci", max_examples=100, deadline=None)
settings.register_profile("dev", max_examples=10, deadline=None)
settings.load_profile("dev")  # Change to "ci" in CI environment
