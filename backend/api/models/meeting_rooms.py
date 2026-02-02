"""Pydantic models for Meeting Room API endpoints."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

# ============================================================================
# REQUEST MODELS
# ============================================================================


class MeetingRoomCreateRequest(BaseModel):
    """Request to create a new meeting room."""

    title: str = Field(max_length=500)
    description: Optional[str] = None
    meeting_type: Literal["collaboration", "meeting_prep"] = "collaboration"
    participant_agent_ids: list[str] = Field(min_length=2)  # At least 2 agents required
    config: Optional[dict] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()

    @field_validator("participant_agent_ids")
    @classmethod
    def validate_participants(cls, v):
        if len(v) < 2:
            raise ValueError("At least 2 agents are required for a meeting")
        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for agent_id in v:
            if agent_id not in seen:
                seen.add(agent_id)
                unique.append(agent_id)
        return unique


class MeetingRoomUpdateRequest(BaseModel):
    """Request to update a meeting room."""

    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    status: Optional[Literal["active", "completed", "archived"]] = None
    config: Optional[dict] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip() if v else v


class ParticipantAddRequest(BaseModel):
    """Request to add a participant to a meeting."""

    agent_id: str
    role_description: Optional[str] = None
    priority: int = 0


class ParticipantUpdateRequest(BaseModel):
    """Request to update a participant's configuration."""

    role_description: Optional[str] = None
    priority: Optional[int] = None


class MeetingChatRequest(BaseModel):
    """Request to send a message in a meeting room."""

    message: str = Field(min_length=1, max_length=10000)
    target_agent_ids: Optional[list[str]] = None  # Direct message to specific agents

    @field_validator("message")
    @classmethod
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError("Message cannot be empty")
        return v.strip()


# ============================================================================
# RESPONSE MODELS
# ============================================================================


class AgentSummary(BaseModel):
    """Summary of an agent for display."""

    id: str
    name: str
    display_name: str
    description: Optional[str] = None


class ParticipantResponse(BaseModel):
    """Response model for a meeting participant."""

    id: str
    agent_id: str
    agent_name: str
    agent_display_name: str
    role_description: Optional[str] = None
    priority: int = 0
    turns_taken: int = 0
    tokens_used: int = 0
    created_at: datetime


class MeetingRoomResponse(BaseModel):
    """Response model for a meeting room."""

    id: str
    client_id: str
    user_id: str
    title: str
    description: Optional[str] = None
    meeting_type: str
    status: str
    config: dict
    total_tokens_used: int
    created_at: datetime
    updated_at: datetime
    participants: list[ParticipantResponse] = []


class MeetingRoomListResponse(BaseModel):
    """Response model for listing meeting rooms."""

    id: str
    title: str
    description: Optional[str] = None
    meeting_type: str
    status: str
    total_tokens_used: int
    participant_count: int
    autonomous_topic: Optional[str] = None  # Set if autonomous discussion was used
    created_at: datetime
    updated_at: datetime


class MeetingMessageResponse(BaseModel):
    """Response model for a meeting message."""

    id: str
    meeting_room_id: str
    role: str  # 'user', 'agent', 'system'
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    agent_display_name: Optional[str] = None
    content: str
    metadata: dict = {}
    turn_number: Optional[int] = None
    created_at: datetime


class MeetingMessagesResponse(BaseModel):
    """Response with paginated messages."""

    messages: list[MeetingMessageResponse]
    total_count: int
    has_more: bool


# ============================================================================
# SSE EVENT MODELS (for documentation/type hints)
# ============================================================================


class AgentTurnStartEvent(BaseModel):
    """SSE event when an agent starts responding."""

    type: Literal["agent_turn_start"] = "agent_turn_start"
    agent_name: str
    agent_display_name: str
    turn_number: int


class AgentTokenEvent(BaseModel):
    """SSE event for streaming token from an agent."""

    type: Literal["agent_token"] = "agent_token"
    agent_name: str
    content: str


class AgentTurnEndEvent(BaseModel):
    """SSE event when an agent finishes responding."""

    type: Literal["agent_turn_end"] = "agent_turn_end"
    agent_name: str
    tokens: dict  # {input: int, output: int}


class RoundCompleteEvent(BaseModel):
    """SSE event when all agents have responded to a user message."""

    type: Literal["round_complete"] = "round_complete"
    agents_responded: list[str]
    total_tokens: dict  # {input: int, output: int}


class MeetingErrorEvent(BaseModel):
    """SSE event for errors during meeting chat."""

    type: Literal["error"] = "error"
    agent_name: Optional[str] = None
    message: str


# ============================================================================
# AUTONOMOUS DISCUSSION MODELS
# ============================================================================


class AutonomousDiscussionRequest(BaseModel):
    """Request to start an autonomous discussion."""

    topic: str = Field(min_length=1, max_length=5000)
    rounds: int = Field(ge=1, le=10, default=3)
    speaking_order: Literal["priority", "round_robin"] = "priority"

    @field_validator("topic")
    @classmethod
    def validate_topic(cls, v):
        if not v or not v.strip():
            raise ValueError("Topic cannot be empty")
        return v.strip()


class AutonomousDiscussionConfig(BaseModel):
    """Config stored in meeting_rooms.config for autonomous mode."""

    is_active: bool = False
    topic: Optional[str] = None
    total_rounds: int = 3
    current_round: int = 0
    speaking_order: str = "priority"
    is_paused: bool = False
    agents_spoken_this_round: list[str] = []


class AutonomousDiscussionStatus(BaseModel):
    """Response for autonomous discussion status."""

    is_active: bool
    topic: Optional[str] = None
    total_rounds: int = 0
    current_round: int = 0
    speaking_order: str = "priority"
    is_paused: bool = False
    can_resume: bool = False


# ============================================================================
# AUTONOMOUS DISCUSSION SSE EVENTS
# ============================================================================


class DiscussionRoundStartEvent(BaseModel):
    """SSE event when a discussion round begins."""

    type: Literal["discussion_round_start"] = "discussion_round_start"
    round_number: int
    total_rounds: int


class DiscussionRoundEndEvent(BaseModel):
    """SSE event when a discussion round completes."""

    type: Literal["discussion_round_end"] = "discussion_round_end"
    round_number: int
    agents_responded: list[str]


class DiscussionCompleteEvent(BaseModel):
    """SSE event when all discussion rounds are finished."""

    type: Literal["discussion_complete"] = "discussion_complete"
    total_rounds_completed: int
    total_tokens: dict  # {input: int, output: int}


class DiscussionPausedEvent(BaseModel):
    """SSE event when discussion is paused (e.g., user interjection)."""

    type: Literal["discussion_paused"] = "discussion_paused"
    reason: Literal["user_interjection", "error", "manual_stop"]
    current_round: int
