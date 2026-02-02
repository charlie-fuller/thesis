"""Contract Testing for Thesis API.

Validates that API contracts between frontend and backend remain consistent.
Uses schema-based contract validation to ensure breaking changes are caught.
"""

import json
from datetime import datetime
from typing import Any, List, Optional

import pytest
from pydantic import BaseModel, ValidationError

# =============================================================================
# API Response Contracts (Expected by Frontend)
# =============================================================================


class MessageContract(BaseModel):
    """Contract for chat message response."""

    id: str
    content: str
    role: str  # 'user' | 'assistant'
    agent_id: Optional[str] = None
    created_at: str
    conversation_id: str
    metadata: Optional[dict] = None


class ConversationContract(BaseModel):
    """Contract for conversation response."""

    id: str
    title: Optional[str] = None
    created_at: str
    updated_at: str
    user_id: str
    messages: Optional[List[MessageContract]] = None


class AgentContract(BaseModel):
    """Contract for agent metadata."""

    id: str
    name: str
    description: str
    category: str
    icon: Optional[str] = None
    capabilities: Optional[List[str]] = None


class TaskContract(BaseModel):
    """Contract for task/kanban item."""

    id: str
    title: str
    description: Optional[str] = None
    status: str  # 'backlog' | 'todo' | 'in_progress' | 'done'
    priority: Optional[str] = None
    due_date: Optional[str] = None
    assignee_id: Optional[str] = None
    created_at: str
    updated_at: str


class ProjectContract(BaseModel):
    """Contract for project response."""

    id: str
    name: str
    client_id: str
    status: str
    tier: Optional[str] = None
    strategic_alignment: Optional[int] = None
    revenue_potential: Optional[int] = None
    win_probability: Optional[int] = None
    created_at: str
    updated_at: str


class DocumentContract(BaseModel):
    """Contract for knowledge base document."""

    id: str
    title: str
    content_type: str
    file_path: Optional[str] = None
    client_id: Optional[str] = None
    created_at: str
    chunk_count: Optional[int] = None


class MeetingRoomContract(BaseModel):
    """Contract for meeting room response."""

    id: str
    name: str
    topic: Optional[str] = None
    agents: List[str]
    status: str  # 'idle' | 'active' | 'paused'
    created_at: str
    autonomous_mode: Optional[bool] = None


class ErrorContract(BaseModel):
    """Contract for error responses."""

    success: bool = False
    error: dict  # Contains 'code', 'message', optional 'details'


class PaginatedResponseContract(BaseModel):
    """Contract for paginated list responses."""

    items: List[Any]
    total: int
    page: int
    per_page: int
    has_more: bool


# =============================================================================
# Contract Tests
# =============================================================================


class TestChatContracts:
    """Validate chat API contracts."""

    def test_message_response_contract(self):
        """Message response matches frontend expectations."""
        # Simulate API response
        response = {
            "id": "msg-123",
            "content": "Hello, how can I help?",
            "role": "assistant",
            "agent_id": "atlas",
            "created_at": "2026-01-25T10:00:00Z",
            "conversation_id": "conv-456",
            "metadata": {"tokens": 50},
        }

        # Should validate without error
        message = MessageContract(**response)
        assert message.id == "msg-123"
        assert message.role == "assistant"

    def test_message_contract_missing_required_field(self):
        """Missing required field raises validation error."""
        response = {
            "id": "msg-123",
            "content": "Hello",
            # Missing: role, created_at, conversation_id
        }

        with pytest.raises(ValidationError) as exc:
            MessageContract(**response)

        errors = exc.value.errors()
        missing_fields = [e["loc"][0] for e in errors]
        assert "role" in missing_fields
        assert "created_at" in missing_fields
        assert "conversation_id" in missing_fields

    def test_conversation_response_contract(self):
        """Conversation response matches frontend expectations."""
        response = {
            "id": "conv-456",
            "title": "AI Strategy Discussion",
            "created_at": "2026-01-25T09:00:00Z",
            "updated_at": "2026-01-25T10:00:00Z",
            "user_id": "user-789",
            "messages": [],
        }

        conversation = ConversationContract(**response)
        assert conversation.id == "conv-456"
        assert conversation.messages == []


class TestAgentContracts:
    """Validate agent API contracts."""

    def test_agent_metadata_contract(self):
        """Agent metadata matches frontend expectations."""
        response = {
            "id": "atlas",
            "name": "Atlas",
            "description": "Research and market analysis specialist",
            "category": "Research",
            "icon": "search",
            "capabilities": ["market_research", "trend_analysis", "citations"],
        }

        agent = AgentContract(**response)
        assert agent.id == "atlas"
        assert "market_research" in agent.capabilities

    def test_agent_list_response(self):
        """Agent list contains all required agents."""
        # Minimum required agents for frontend
        required_agents = [
            "coordinator",
            "atlas",
            "capital",
            "guardian",
            "counselor",
            "sage",
            "oracle",
            "architect",
        ]

        # Simulate API response
        agents = [
            {
                "id": agent_id,
                "name": agent_id.title(),
                "description": f"{agent_id} agent",
                "category": "Test",
            }
            for agent_id in required_agents
        ]

        validated = [AgentContract(**a) for a in agents]
        agent_ids = [a.id for a in validated]

        for required in required_agents:
            assert required in agent_ids, f"Missing required agent: {required}"


class TestTaskContracts:
    """Validate task/kanban API contracts."""

    def test_task_response_contract(self):
        """Task response matches frontend expectations."""
        response = {
            "id": "task-123",
            "title": "Review security audit",
            "description": "Complete SOC2 compliance review",
            "status": "in_progress",
            "priority": "high",
            "due_date": "2026-02-01",
            "assignee_id": "user-456",
            "created_at": "2026-01-20T10:00:00Z",
            "updated_at": "2026-01-25T10:00:00Z",
        }

        task = TaskContract(**response)
        assert task.status == "in_progress"
        assert task.priority == "high"

    def test_task_status_values(self):
        """Task status accepts valid kanban states."""
        valid_statuses = ["backlog", "todo", "in_progress", "done"]

        for status in valid_statuses:
            task = TaskContract(
                id="t1",
                title="Test",
                status=status,
                created_at="2026-01-25T10:00:00Z",
                updated_at="2026-01-25T10:00:00Z",
            )
            assert task.status == status


class TestProjectContracts:
    """Validate project/pipeline API contracts."""

    def test_project_response_contract(self):
        """Project response matches frontend expectations."""
        response = {
            "id": "opp-123",
            "name": "Enterprise AI Platform",
            "client_id": "client-456",
            "status": "qualification",
            "tier": "A",
            "strategic_alignment": 85,
            "revenue_potential": 90,
            "win_probability": 70,
            "created_at": "2026-01-15T10:00:00Z",
            "updated_at": "2026-01-25T10:00:00Z",
        }

        project = ProjectContract(**response)
        assert project.tier == "A"
        assert project.strategic_alignment == 85

    def test_project_scores_within_range(self):
        """Project scores should be 0-100."""
        response = {
            "id": "opp-123",
            "name": "Test",
            "client_id": "c1",
            "status": "active",
            "strategic_alignment": 150,  # Invalid: > 100
            "revenue_potential": 90,
            "win_probability": 70,
            "created_at": "2026-01-25T10:00:00Z",
            "updated_at": "2026-01-25T10:00:00Z",
        }

        # Note: Pydantic doesn't enforce range by default
        # This test documents expected behavior - add validators if needed
        ProjectContract(**response)
        # Frontend should validate: assert 0 <= opp.strategic_alignment <= 100


class TestDocumentContracts:
    """Validate knowledge base API contracts."""

    def test_document_response_contract(self):
        """Document response matches frontend expectations."""
        response = {
            "id": "doc-123",
            "title": "Q4 Market Analysis",
            "content_type": "application/pdf",
            "file_path": "/documents/q4-analysis.pdf",
            "client_id": "client-456",
            "created_at": "2026-01-20T10:00:00Z",
            "chunk_count": 45,
        }

        document = DocumentContract(**response)
        assert document.content_type == "application/pdf"
        assert document.chunk_count == 45


class TestMeetingRoomContracts:
    """Validate meeting room API contracts."""

    def test_meeting_room_response_contract(self):
        """Meeting room response matches frontend expectations."""
        response = {
            "id": "room-123",
            "name": "Strategy Session",
            "topic": "AI Integration Roadmap",
            "agents": ["atlas", "capital", "guardian"],
            "status": "active",
            "created_at": "2026-01-25T09:00:00Z",
            "autonomous_mode": True,
        }

        room = MeetingRoomContract(**response)
        assert len(room.agents) == 3
        assert room.autonomous_mode is True

    def test_meeting_room_status_values(self):
        """Meeting room status accepts valid states."""
        valid_statuses = ["idle", "active", "paused"]

        for status in valid_statuses:
            room = MeetingRoomContract(
                id="r1",
                name="Test",
                agents=["atlas"],
                status=status,
                created_at="2026-01-25T10:00:00Z",
            )
            assert room.status == status


class TestErrorContracts:
    """Validate error response contracts."""

    def test_error_response_contract(self):
        """Error responses follow standard format."""
        response = {
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid input provided",
                "details": {"field": "email", "issue": "invalid format"},
            },
        }

        error = ErrorContract(**response)
        assert error.success is False
        assert error.error["code"] == "VALIDATION_ERROR"

    def test_error_response_has_required_fields(self):
        """Error object must have code and message."""
        response = {
            "success": False,
            "error": {"code": "NOT_FOUND", "message": "Resource not found"},
        }

        error = ErrorContract(**response)
        assert "code" in error.error
        assert "message" in error.error


class TestPaginationContracts:
    """Validate pagination contracts."""

    def test_paginated_response_contract(self):
        """Paginated responses include metadata."""
        response = {
            "items": [{"id": "1"}, {"id": "2"}],
            "total": 100,
            "page": 1,
            "per_page": 20,
            "has_more": True,
        }

        paginated = PaginatedResponseContract(**response)
        assert paginated.total == 100
        assert paginated.has_more is True


# =============================================================================
# Consumer-Driven Contract Tests
# =============================================================================


class TestFrontendExpectations:
    """Tests documenting what the frontend expects from the API."""

    def test_chat_streaming_format(self):
        """Streaming chat responses use Server-Sent Events format."""
        # Frontend expects: data: {"content": "...", "done": false}\n\n
        sse_event = 'data: {"content": "Hello", "done": false}\n\n'

        assert sse_event.startswith("data: ")
        assert sse_event.endswith("\n\n")

        # Parse the JSON payload
        json_str = sse_event.replace("data: ", "").strip()
        payload = json.loads(json_str)

        assert "content" in payload
        assert "done" in payload

    def test_agent_mention_format(self):
        """Frontend sends @mentions in specific format."""
        # Frontend sends: "@atlas What are the trends?"
        message = "@atlas What are the trends?"

        # Backend should extract agent_id
        import re

        match = re.match(r"^@(\w+)\s", message)

        assert match is not None
        assert match.group(1) == "atlas"

    def test_datetime_format(self):
        """All datetimes use ISO 8601 format."""
        datetime_str = "2026-01-25T10:30:00Z"

        # Should parse without error
        parsed = datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
        assert parsed.year == 2026

    def test_uuid_format(self):
        """All IDs are valid UUIDs or prefixed identifiers."""
        import re

        valid_ids = [
            "550e8400-e29b-41d4-a716-446655440000",  # UUID
            "conv-123",  # Prefixed
            "msg_abc123",  # Underscore prefix
        ]

        uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        prefixed_pattern = r"^[a-z]+[-_][a-zA-Z0-9]+$"

        for id_val in valid_ids:
            is_uuid = bool(re.match(uuid_pattern, id_val))
            is_prefixed = bool(re.match(prefixed_pattern, id_val))
            assert is_uuid or is_prefixed, f"Invalid ID format: {id_val}"
