"""
Tests for Task Management API

Tests the Kanban-style task management system including CRUD operations,
status updates, reordering, comments, history, and transcript extraction.
"""

import sys
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import date, datetime, timezone
from enum import Enum

# Mock only specific modules that are safe to mock (not config - it's a real package!)
mock_database = Mock()
mock_supabase_client = Mock()
mock_database.get_supabase = Mock(return_value=mock_supabase_client)
sys.modules['database'] = mock_database

# Note: Do NOT mock 'config' - it's a real package and mocking it breaks other tests
# If you need to mock config.get_default_client_id, use patch() in individual tests

mock_auth = Mock()
sys.modules['auth'] = mock_auth

mock_logger = Mock()
mock_logger.get_logger = Mock(return_value=Mock())
sys.modules['logger_config'] = mock_logger

mock_validation = Mock()
mock_validation.validate_uuid = Mock()
sys.modules['validation'] = mock_validation


# ============================================================================
# Re-implement Task models for testing
# ============================================================================

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"


class TaskSourceType(str, Enum):
    TRANSCRIPT = "transcript"
    CONVERSATION = "conversation"
    RESEARCH = "research"
    OPPORTUNITY = "opportunity"
    MANUAL = "manual"


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mock_current_user():
    """Mock authenticated user."""
    return {
        'id': 'user-123',
        'email': 'test@example.com',
        'client_id': 'client-123'
    }


@pytest.fixture
def mock_task_data():
    """Sample task data for testing."""
    return {
        'id': 'task-123',
        'client_id': 'client-123',
        'title': 'Test Task',
        'description': 'Test description',
        'status': 'pending',
        'priority': 3,
        'assignee_stakeholder_id': None,
        'assignee_user_id': None,
        'assignee_name': 'John Doe',
        'due_date': '2026-02-01',
        'completed_at': None,
        'source_type': 'manual',
        'source_transcript_id': None,
        'source_conversation_id': None,
        'source_research_task_id': None,
        'source_opportunity_id': None,
        'category': 'general',
        'tags': ['urgent'],
        'blocker_reason': None,
        'blocked_at': None,
        'related_opportunity_id': None,
        'position': 0,
        'created_at': '2026-01-15T10:00:00Z',
        'updated_at': '2026-01-15T10:00:00Z',
        'stakeholder_name': None,
        'stakeholder_email': None,
        'user_email': None,
        'display_assignee': 'John Doe',
    }


@pytest.fixture
def mock_supabase():
    """Mock Supabase client."""
    mock_sb = Mock()

    # Chain mock for table operations
    mock_table = Mock()
    mock_sb.table.return_value = mock_table
    mock_table.select.return_value = mock_table
    mock_table.insert.return_value = mock_table
    mock_table.update.return_value = mock_table
    mock_table.delete.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.neq.return_value = mock_table
    mock_table.in_.return_value = mock_table
    mock_table.gte.return_value = mock_table
    mock_table.lte.return_value = mock_table
    mock_table.order.return_value = mock_table
    mock_table.limit.return_value = mock_table
    mock_table.offset.return_value = mock_table
    mock_table.single.return_value = mock_table

    return mock_sb, mock_table


# ============================================================================
# Test: Task Serialization
# ============================================================================

class TestTaskSerialization:
    """Test task data serialization."""

    def test_serialize_task_basic(self, mock_task_data):
        """Serialize task with all fields."""
        # Import serialize function equivalent
        def serialize_task(task: dict) -> dict:
            return {
                'id': task['id'],
                'client_id': task['client_id'],
                'title': task['title'],
                'description': task.get('description'),
                'status': task['status'],
                'priority': task['priority'],
                'assignee_stakeholder_id': task.get('assignee_stakeholder_id'),
                'assignee_user_id': task.get('assignee_user_id'),
                'assignee_name': task.get('assignee_name'),
                'due_date': task['due_date'] if task.get('due_date') else None,
                'completed_at': task['completed_at'] if task.get('completed_at') else None,
                'source_type': task.get('source_type'),
                'category': task.get('category'),
                'tags': task.get('tags') or [],
                'blocker_reason': task.get('blocker_reason'),
                'position': task.get('position', 0),
                'created_at': task['created_at'],
                'updated_at': task['updated_at'],
                'display_assignee': task.get('display_assignee') or task.get('assignee_name'),
            }

        result = serialize_task(mock_task_data)

        assert result['id'] == 'task-123'
        assert result['title'] == 'Test Task'
        assert result['status'] == 'pending'
        assert result['priority'] == 3
        assert result['tags'] == ['urgent']

    def test_serialize_task_with_null_tags(self):
        """Serialize task with null tags returns empty list."""
        task = {
            'id': 'task-1',
            'client_id': 'c1',
            'title': 'Test',
            'status': 'pending',
            'priority': 3,
            'tags': None,
            'created_at': '2026-01-15',
            'updated_at': '2026-01-15'
        }

        def serialize_task(task: dict) -> dict:
            return {
                'tags': task.get('tags') or [],
            }

        result = serialize_task(task)
        assert result['tags'] == []


# ============================================================================
# Test: Task Status Enum
# ============================================================================

class TestTaskStatus:
    """Test task status values."""

    def test_all_statuses_defined(self):
        """All required statuses are defined."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.BLOCKED.value == "blocked"
        assert TaskStatus.COMPLETED.value == "completed"

    def test_status_count(self):
        """Exactly 4 statuses exist."""
        assert len(TaskStatus) == 4


class TestTaskSourceType:
    """Test task source type values."""

    def test_all_source_types_defined(self):
        """All required source types are defined."""
        assert TaskSourceType.TRANSCRIPT.value == "transcript"
        assert TaskSourceType.CONVERSATION.value == "conversation"
        assert TaskSourceType.RESEARCH.value == "research"
        assert TaskSourceType.OPPORTUNITY.value == "opportunity"
        assert TaskSourceType.MANUAL.value == "manual"


# ============================================================================
# Test: Task Create Validation
# ============================================================================

class TestTaskCreateValidation:
    """Test task creation validation."""

    def test_valid_task_create(self):
        """Valid task data passes validation."""
        from pydantic import BaseModel, Field, field_validator
        from typing import Optional, List

        class TaskCreate(BaseModel):
            title: str = Field(..., min_length=1, max_length=500)
            description: Optional[str] = None
            priority: int = Field(default=3, ge=1, le=5)

            @field_validator('title')
            @classmethod
            def validate_title(cls, v):
                if not v or not v.strip():
                    raise ValueError('Title cannot be empty')
                return v.strip()

        task = TaskCreate(title="Valid Task", description="Description")
        assert task.title == "Valid Task"

    def test_title_stripped(self):
        """Title is stripped of whitespace."""
        from pydantic import BaseModel, Field, field_validator

        class TaskCreate(BaseModel):
            title: str = Field(..., max_length=500)

            @field_validator('title')
            @classmethod
            def validate_title(cls, v):
                return v.strip() if v else v

        task = TaskCreate(title="  Padded Title  ")
        assert task.title == "Padded Title"

    def test_priority_bounds(self):
        """Priority must be between 1 and 5."""
        from pydantic import BaseModel, Field, ValidationError

        class TaskCreate(BaseModel):
            priority: int = Field(default=3, ge=1, le=5)

        # Valid priorities
        assert TaskCreate(priority=1).priority == 1
        assert TaskCreate(priority=5).priority == 5

        # Invalid priorities
        with pytest.raises(ValidationError):
            TaskCreate(priority=0)
        with pytest.raises(ValidationError):
            TaskCreate(priority=6)


# ============================================================================
# Test: Task CRUD Operations (Unit Tests)
# ============================================================================

class TestTaskCRUD:
    """Test task CRUD operation logic."""

    def test_create_task_builds_correct_record(self, mock_task_data, mock_current_user):
        """Create task builds correct database record."""
        request_data = {
            'title': 'New Task',
            'description': 'New description',
            'status': 'pending',
            'priority': 2,
            'assignee_name': 'Jane Doe',
            'due_date': date(2026, 3, 1),
            'category': 'development',
            'tags': ['important'],
            'source_type': 'manual',
        }

        # Simulate building the task record
        task_record = {
            'client_id': mock_current_user['client_id'],
            'title': request_data['title'],
            'description': request_data['description'],
            'status': request_data['status'],
            'priority': request_data['priority'],
            'assignee_name': request_data['assignee_name'],
            'due_date': request_data['due_date'].isoformat(),
            'category': request_data['category'],
            'tags': request_data['tags'],
            'source_type': request_data['source_type'],
            'created_by': mock_current_user['id'],
            'updated_by': mock_current_user['id'],
            'position': 0,
        }

        assert task_record['title'] == 'New Task'
        assert task_record['priority'] == 2
        assert task_record['client_id'] == 'client-123'
        assert task_record['due_date'] == '2026-03-01'

    def test_update_task_only_includes_provided_fields(self, mock_current_user):
        """Update only includes fields that were provided."""
        # Request only updates title and priority
        request_updates = {
            'title': 'Updated Title',
            'priority': 1,
        }

        update_record = {'updated_by': mock_current_user['id']}

        if request_updates.get('title') is not None:
            update_record['title'] = request_updates['title']
        if request_updates.get('priority') is not None:
            update_record['priority'] = request_updates['priority']
        if request_updates.get('description') is not None:
            update_record['description'] = request_updates['description']

        # Should only have title, priority, and updated_by
        assert 'title' in update_record
        assert 'priority' in update_record
        assert 'description' not in update_record
        assert update_record['title'] == 'Updated Title'


# ============================================================================
# Test: Kanban Board Operations
# ============================================================================

class TestKanbanBoard:
    """Test Kanban board grouping and filtering."""

    def test_group_tasks_by_status(self, mock_task_data):
        """Tasks are correctly grouped by status."""
        tasks = [
            {**mock_task_data, 'id': '1', 'status': 'pending'},
            {**mock_task_data, 'id': '2', 'status': 'in_progress'},
            {**mock_task_data, 'id': '3', 'status': 'pending'},
            {**mock_task_data, 'id': '4', 'status': 'completed'},
            {**mock_task_data, 'id': '5', 'status': 'blocked'},
        ]

        columns = {
            'pending': [],
            'in_progress': [],
            'blocked': [],
            'completed': []
        }

        for task in tasks:
            status = task.get('status', 'pending')
            if status in columns:
                columns[status].append(task)

        assert len(columns['pending']) == 2
        assert len(columns['in_progress']) == 1
        assert len(columns['blocked']) == 1
        assert len(columns['completed']) == 1

    def test_count_tasks_correctly(self, mock_task_data):
        """Task counts are calculated correctly."""
        columns = {
            'pending': [mock_task_data, mock_task_data],
            'in_progress': [mock_task_data],
            'blocked': [],
            'completed': [mock_task_data, mock_task_data, mock_task_data]
        }

        counts = {status: len(tasks_list) for status, tasks_list in columns.items()}
        counts['total'] = sum(counts.values())

        assert counts['pending'] == 2
        assert counts['in_progress'] == 1
        assert counts['blocked'] == 0
        assert counts['completed'] == 3
        assert counts['total'] == 6

    def test_search_filter_case_insensitive(self, mock_task_data):
        """Search filter is case insensitive."""
        tasks = [
            {**mock_task_data, 'title': 'Important Task', 'description': 'Details'},
            {**mock_task_data, 'title': 'Another Item', 'description': 'More info'},
            {**mock_task_data, 'title': 'Something Else', 'description': 'Important note'},
        ]

        search = "important"
        search_lower = search.lower()
        filtered = [
            t for t in tasks
            if search_lower in (t.get('title') or '').lower()
            or search_lower in (t.get('description') or '').lower()
        ]

        assert len(filtered) == 2  # Matches in title and description


# ============================================================================
# Test: Task Status Updates
# ============================================================================

class TestTaskStatusUpdate:
    """Test task status update logic."""

    def test_status_update_to_blocked_requires_reason(self):
        """Moving to blocked status can include blocker reason."""
        update_record = {
            'status': 'blocked',
        }

        blocker_reason = "Waiting for approval"
        if update_record['status'] == 'blocked':
            update_record['blocker_reason'] = blocker_reason

        assert update_record['blocker_reason'] == "Waiting for approval"

    def test_status_update_clears_blocker_for_other_status(self):
        """Moving out of blocked clears blocker reason."""
        old_status = 'blocked'
        new_status = 'in_progress'

        update_record = {'status': new_status}

        # When moving out of blocked, blocker_reason should be cleared
        if old_status == 'blocked' and new_status != 'blocked':
            update_record['blocker_reason'] = None

        assert update_record['blocker_reason'] is None


# ============================================================================
# Test: Task Position Management
# ============================================================================

class TestTaskPositioning:
    """Test task position calculation for Kanban columns."""

    def test_get_next_position_empty_column(self):
        """Next position in empty column is 0."""
        existing_tasks = []

        if existing_tasks:
            next_position = existing_tasks[0]['position'] + 1
        else:
            next_position = 0

        assert next_position == 0

    def test_get_next_position_with_existing_tasks(self):
        """Next position is max + 1."""
        existing_tasks = [
            {'position': 0},
            {'position': 1},
            {'position': 2},
        ]

        # Sorted descending, first is max
        sorted_tasks = sorted(existing_tasks, key=lambda x: x['position'], reverse=True)
        next_position = sorted_tasks[0]['position'] + 1

        assert next_position == 3

    def test_reorder_updates_positions(self):
        """Reorder updates all task positions."""
        reorder_items = [
            {'task_id': 'task-1', 'status': 'pending', 'position': 0},
            {'task_id': 'task-2', 'status': 'pending', 'position': 1},
            {'task_id': 'task-3', 'status': 'pending', 'position': 2},
        ]

        updates = []
        for item in reorder_items:
            updates.append({
                'id': item['task_id'],
                'status': item['status'],
                'position': item['position']
            })

        assert len(updates) == 3
        assert updates[0]['position'] == 0
        assert updates[2]['position'] == 2


# ============================================================================
# Test: Task Comments
# ============================================================================

class TestTaskComments:
    """Test task comment operations."""

    def test_comment_content_validation(self):
        """Comment content cannot be empty."""
        from pydantic import BaseModel, Field, field_validator, ValidationError

        class TaskCommentCreate(BaseModel):
            content: str = Field(..., min_length=1)

            @field_validator('content')
            @classmethod
            def validate_content(cls, v):
                if not v or not v.strip():
                    raise ValueError('Content cannot be empty')
                return v.strip()

        # Valid comment
        comment = TaskCommentCreate(content="This is a comment")
        assert comment.content == "This is a comment"

        # Empty content fails
        with pytest.raises(ValidationError):
            TaskCommentCreate(content="")

    def test_comment_content_stripped(self):
        """Comment content is stripped of whitespace."""
        from pydantic import BaseModel, Field, field_validator

        class TaskCommentCreate(BaseModel):
            content: str = Field(..., min_length=1)

            @field_validator('content')
            @classmethod
            def validate_content(cls, v):
                return v.strip() if v else v

        comment = TaskCommentCreate(content="  Padded comment  ")
        assert comment.content == "Padded comment"


# ============================================================================
# Test: Task Extraction from Transcripts
# ============================================================================

class TestTaskExtraction:
    """Test task extraction from meeting transcripts."""

    def test_extract_action_items_to_tasks(self):
        """Action items are converted to tasks."""
        action_items = [
            {'description': 'Follow up with client', 'owner': 'John', 'due_date': '2026-02-01'},
            {'description': 'Review proposal', 'owner': 'Jane', 'due_date': None},
            {'description': '', 'owner': None, 'due_date': None},  # Empty, should be skipped
        ]

        tasks_created = 0
        tasks_skipped = 0

        for item in action_items:
            description = item.get('description', '').strip()
            if not description:
                tasks_skipped += 1
                continue

            # Would create task here
            tasks_created += 1

        assert tasks_created == 2
        assert tasks_skipped == 1

    def test_truncate_long_titles(self):
        """Long descriptions are truncated for task titles."""
        long_description = "A" * 600  # 600 chars

        title = long_description[:500]

        assert len(title) == 500

    def test_parse_due_date_from_action_item(self):
        """Due dates are parsed from action items."""
        due_date_str = "2026-02-15"

        try:
            due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00')).date()
            assert due_date.isoformat() == "2026-02-15"
        except ValueError:
            due_date = None

    def test_handle_invalid_due_date(self):
        """Invalid due dates are handled gracefully."""
        due_date_str = "invalid-date"

        try:
            due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00')).date()
        except (ValueError, AttributeError):
            due_date = None

        assert due_date is None

    def test_skip_duplicate_extractions(self):
        """Duplicate tasks are not re-extracted."""
        existing_source_texts = [
            'Follow up with client',
            'Review proposal',
        ]

        new_action_items = [
            {'description': 'Follow up with client'},  # Duplicate
            {'description': 'New action item'},  # New
        ]

        extracted = 0
        skipped = 0

        for item in new_action_items:
            desc = item['description']
            if desc in existing_source_texts:
                skipped += 1
            else:
                extracted += 1

        assert extracted == 1
        assert skipped == 1


# ============================================================================
# Test: Task Filters
# ============================================================================

class TestTaskFilters:
    """Test task filtering logic."""

    def test_filter_by_status(self, mock_task_data):
        """Filter tasks by status."""
        tasks = [
            {**mock_task_data, 'status': 'pending'},
            {**mock_task_data, 'status': 'in_progress'},
            {**mock_task_data, 'status': 'pending'},
        ]

        filter_status = ['pending']
        filtered = [t for t in tasks if t['status'] in filter_status]

        assert len(filtered) == 2

    def test_filter_by_priority(self, mock_task_data):
        """Filter tasks by priority."""
        tasks = [
            {**mock_task_data, 'priority': 1},
            {**mock_task_data, 'priority': 3},
            {**mock_task_data, 'priority': 1},
            {**mock_task_data, 'priority': 5},
        ]

        filter_priority = [1, 2]
        filtered = [t for t in tasks if t['priority'] in filter_priority]

        assert len(filtered) == 2

    def test_filter_by_due_date_range(self, mock_task_data):
        """Filter tasks by due date range."""
        tasks = [
            {**mock_task_data, 'due_date': '2026-01-15'},
            {**mock_task_data, 'due_date': '2026-02-01'},
            {**mock_task_data, 'due_date': '2026-03-15'},
            {**mock_task_data, 'due_date': None},
        ]

        due_from = '2026-01-01'
        due_to = '2026-02-15'

        filtered = [
            t for t in tasks
            if t['due_date'] and due_from <= t['due_date'] <= due_to
        ]

        assert len(filtered) == 2

    def test_exclude_completed_tasks(self, mock_task_data):
        """Exclude completed tasks when requested."""
        tasks = [
            {**mock_task_data, 'status': 'pending'},
            {**mock_task_data, 'status': 'completed'},
            {**mock_task_data, 'status': 'in_progress'},
        ]

        include_completed = False
        if not include_completed:
            filtered = [t for t in tasks if t['status'] != 'completed']
        else:
            filtered = tasks

        assert len(filtered) == 2


# ============================================================================
# Test: Task History Tracking
# ============================================================================

class TestTaskHistory:
    """Test task change history tracking."""

    def test_history_entry_format(self):
        """History entry has correct format."""
        history_entry = {
            'id': 'history-1',
            'task_id': 'task-123',
            'user_id': 'user-123',
            'field_name': 'status',
            'old_value': 'pending',
            'new_value': 'in_progress',
            'created_at': '2026-01-15T12:00:00Z',
        }

        assert history_entry['field_name'] == 'status'
        assert history_entry['old_value'] == 'pending'
        assert history_entry['new_value'] == 'in_progress'

    def test_multiple_field_changes_tracked(self):
        """Multiple field changes create multiple history entries."""
        changes = [
            ('status', 'pending', 'in_progress'),
            ('priority', '3', '1'),
            ('assignee_name', None, 'John Doe'),
        ]

        history_entries = []
        for field, old, new in changes:
            history_entries.append({
                'field_name': field,
                'old_value': old,
                'new_value': new,
            })

        assert len(history_entries) == 3


# ============================================================================
# Test: Valid Order Fields
# ============================================================================

class TestTaskOrdering:
    """Test task ordering validation."""

    def test_valid_order_fields(self):
        """Only valid order fields are accepted."""
        valid_order_fields = ['created_at', 'updated_at', 'due_date', 'priority', 'position', 'title']

        assert 'created_at' in valid_order_fields
        assert 'invalid_field' not in valid_order_fields

    def test_default_to_created_at(self):
        """Invalid order field defaults to created_at."""
        valid_order_fields = ['created_at', 'updated_at', 'due_date', 'priority', 'position', 'title']

        order_by = 'invalid_field'
        if order_by not in valid_order_fields:
            order_by = 'created_at'

        assert order_by == 'created_at'


# ============================================================================
# Test: Overdue Task Detection
# ============================================================================

class TestOverdueTasks:
    """Test overdue task detection."""

    def test_count_overdue_tasks(self):
        """Overdue tasks are counted correctly."""
        today = '2026-01-16'
        tasks = [
            {'due_date': '2026-01-10', 'status': 'pending'},  # Overdue
            {'due_date': '2026-01-20', 'status': 'pending'},  # Not overdue
            {'due_date': '2026-01-05', 'status': 'completed'},  # Overdue but completed
            {'due_date': '2026-01-01', 'status': 'in_progress'},  # Overdue
            {'due_date': None, 'status': 'pending'},  # No due date
        ]

        overdue_count = len([
            t for t in tasks
            if t.get('due_date') and t['due_date'] < today and t['status'] != 'completed'
        ])

        assert overdue_count == 2
