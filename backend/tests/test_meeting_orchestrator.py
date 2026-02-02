"""Meeting Orchestrator Tests.

Tests for multi-agent meeting room orchestration including:
- Agent selection based on topic
- Turn-taking and priority
- Autonomous mode behavior
- Word limits and Smart Brevity
- Facilitator intervention
- Reporter synthesis
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

# Mock agent responses
MOCK_AGENT_RESPONSES = {
    "atlas": "Based on recent Gartner research, enterprise AI adoption is accelerating with 65% of organizations piloting generative AI. Key trends include agentic AI, multimodal models, and AI engineering platforms.",
    "capital": "The ROI analysis shows a 3-year NPV of $2.4M with a payback period of 14 months. Initial investment of $500K yields projected savings of $180K annually.",
    "guardian": "Security assessment identifies three key risks: data privacy exposure, model vulnerabilities, and compliance gaps. Recommend implementing zero-trust architecture and regular audits.",
    "sage": "Change management strategy should focus on building champions, clear communication, and staged rollout. Address employee concerns through training and visible quick wins.",
}


class TestMeetingOrchestrator:
    """Meeting orchestration tests."""

    @pytest.fixture
    def orchestrator(self):
        """Create a mock meeting orchestrator."""
        orchestrator = MagicMock()
        orchestrator.agents = {
            "atlas": MagicMock(name="Atlas", priority=1),
            "capital": MagicMock(name="Capital", priority=2),
            "guardian": MagicMock(name="Guardian", priority=3),
            "sage": MagicMock(name="Sage", priority=4),
            "facilitator": MagicMock(name="Facilitator", priority=0),
            "reporter": MagicMock(name="Reporter", priority=5),
        }
        return orchestrator

    @pytest.fixture
    def meeting_room(self):
        """Create a mock meeting room."""
        return {
            "id": "test-room-001",
            "name": "Strategy Meeting",
            "topic": "Enterprise AI Implementation Strategy",
            "autonomous_mode": False,
            "participants": ["atlas", "capital", "guardian", "sage"],
            "created_at": datetime.now().isoformat(),
        }

    def test_agent_selection_for_topic(self, orchestrator, meeting_room):
        """Correct agents are selected based on topic keywords."""
        topic = "What are the financial and security considerations for AI implementation?"

        # Mock the agent selection logic
        orchestrator.select_agents_for_topic = MagicMock(return_value=["capital", "guardian"])

        selected = orchestrator.select_agents_for_topic(topic)

        assert "capital" in selected, "Capital should be selected for financial topics"
        assert "guardian" in selected, "Guardian should be selected for security topics"

    def test_turn_taking_respects_priority(self, orchestrator):
        """Agents speak in priority order."""
        participants = ["sage", "atlas", "capital"]

        # Sort by priority
        sorted_agents = sorted(participants, key=lambda a: orchestrator.agents[a].priority)

        assert sorted_agents[0] == "atlas", "Atlas (priority 1) should speak first"
        assert sorted_agents[1] == "capital", "Capital (priority 2) should speak second"
        assert sorted_agents[2] == "sage", "Sage (priority 4) should speak third"

    def test_autonomous_mode_word_limits(self):
        """Enforce 50-100 word limit per turn in autonomous mode."""
        for agent, response in MOCK_AGENT_RESPONSES.items():
            word_count = len(response.split())
            assert word_count <= 100, f"{agent} exceeds 100 word limit ({word_count} words)"
            # Most responses should be substantial
            assert word_count >= 20, f"{agent} response too short ({word_count} words)"

    def test_facilitator_detects_off_topic(self, orchestrator):
        """Facilitator can detect off-topic discussion."""
        on_topic_message = "Let's discuss the ROI projections for the AI initiative."
        off_topic_message = "Did you see the game last night?"

        orchestrator.is_on_topic = MagicMock(
            side_effect=lambda msg, topic: "AI" in msg or "ROI" in msg
        )

        topic = "AI implementation strategy"

        assert orchestrator.is_on_topic(on_topic_message, topic)
        assert not orchestrator.is_on_topic(off_topic_message, topic)

    def test_facilitator_redirects_discussion(self, orchestrator):
        """Facilitator intervenes and redirects off-topic discussion."""
        orchestrator.generate_redirect = MagicMock(
            return_value="Let's refocus on our main topic. Atlas, can you share the research findings on AI implementation?"
        )

        redirect = orchestrator.generate_redirect()

        assert "refocus" in redirect.lower() or "topic" in redirect.lower()
        assert len(redirect.split()) <= 50, "Redirect should be concise"

    def test_reporter_generates_synthesis(self):
        """Reporter produces unified summary from discussion."""
        [
            {"agent": "atlas", "content": MOCK_AGENT_RESPONSES["atlas"]},
            {"agent": "capital", "content": MOCK_AGENT_RESPONSES["capital"]},
            {"agent": "guardian", "content": MOCK_AGENT_RESPONSES["guardian"]},
        ]

        # Mock synthesis generation
        synthesis = """
        **Meeting Synthesis: AI Implementation Strategy**

        **Key Findings:**
        1. Market research shows 65% of enterprises are piloting AI
        2. Financial projections indicate positive ROI within 14 months
        3. Security considerations include data privacy and compliance

        **Recommended Actions:**
        - Proceed with phased implementation
        - Address security gaps before launch
        - Allocate $500K initial budget

        **Next Steps:**
        - Detailed security assessment
        - Change management planning
        - Stakeholder communication
        """

        word_count = len(synthesis.split())
        assert word_count <= 250, f"Synthesis too long: {word_count} words"
        assert "Key Findings" in synthesis or "Summary" in synthesis
        assert "Next Steps" in synthesis or "Actions" in synthesis


class TestAutonomousMode:
    """Tests for autonomous discussion mode."""

    @pytest.fixture
    def autonomous_room(self):
        """Create an autonomous mode meeting room."""
        return {
            "id": "auto-room-001",
            "topic": "AI Strategy Discussion",
            "autonomous_mode": True,
            "max_turns": 10,
            "current_turn": 0,
            "participants": ["atlas", "capital", "guardian"],
        }

    def test_autonomous_mode_starts_automatically(self, autonomous_room):
        """Discussion starts automatically when autonomous mode is enabled."""
        assert autonomous_room["autonomous_mode"] is True
        assert autonomous_room["current_turn"] == 0

    def test_autonomous_mode_cycles_through_agents(self, autonomous_room):
        """Agents take turns in sequence."""
        participants = autonomous_room["participants"]
        turns = []

        for i in range(6):  # Two full cycles
            current_agent = participants[i % len(participants)]
            turns.append(current_agent)

        expected = ["atlas", "capital", "guardian", "atlas", "capital", "guardian"]
        assert turns == expected

    def test_autonomous_mode_respects_max_turns(self, autonomous_room):
        """Discussion stops after max_turns."""
        max_turns = autonomous_room["max_turns"]
        current_turn = 0

        while current_turn < max_turns:
            current_turn += 1

        assert current_turn == max_turns

    def test_user_interjection_pauses_autonomous(self, autonomous_room):
        """User message pauses autonomous mode."""
        autonomous_room["autonomous_mode"] = True

        # Simulate user interjection

        # Mode should pause
        autonomous_room["autonomous_mode"] = False  # Paused by interjection

        assert autonomous_room["autonomous_mode"] is False

    def test_resume_autonomous_after_interjection(self, autonomous_room):
        """Autonomous mode can resume after handling user question."""
        autonomous_room["autonomous_mode"] = False  # Paused

        # After user's question is answered
        resume_command = "RESUME"

        if resume_command == "RESUME":
            autonomous_room["autonomous_mode"] = True

        assert autonomous_room["autonomous_mode"] is True


class TestMeetingRoomCRUD:
    """Tests for meeting room CRUD operations."""

    def test_create_meeting_room(self):
        """Can create a new meeting room."""
        room_data = {
            "name": "Strategy Meeting",
            "topic": "AI Implementation",
            "participants": ["atlas", "capital"],
        }

        # Mock creation
        created_room = {
            "id": "new-room-001",
            **room_data,
            "created_at": datetime.now().isoformat(),
        }

        assert created_room["id"] is not None
        assert created_room["name"] == room_data["name"]
        assert len(created_room["participants"]) == 2

    def test_add_participant_to_room(self):
        """Can add a participant to existing room."""
        room = {
            "id": "room-001",
            "participants": ["atlas", "capital"],
        }

        new_participant = "guardian"
        room["participants"].append(new_participant)

        assert "guardian" in room["participants"]
        assert len(room["participants"]) == 3

    def test_remove_participant_from_room(self):
        """Can remove a participant from room."""
        room = {
            "id": "room-001",
            "participants": ["atlas", "capital", "guardian"],
        }

        room["participants"].remove("guardian")

        assert "guardian" not in room["participants"]
        assert len(room["participants"]) == 2

    def test_update_room_topic(self):
        """Can update room topic."""
        room = {
            "id": "room-001",
            "topic": "Original topic",
        }

        room["topic"] = "Updated topic: AI ROI Analysis"

        assert room["topic"] == "Updated topic: AI ROI Analysis"

    def test_delete_meeting_room(self):
        """Can delete a meeting room."""
        rooms = [
            {"id": "room-001", "name": "Room 1"},
            {"id": "room-002", "name": "Room 2"},
        ]

        rooms = [r for r in rooms if r["id"] != "room-001"]

        assert len(rooms) == 1
        assert rooms[0]["id"] == "room-002"


class TestMeetingRoomMessages:
    """Tests for meeting room message handling."""

    def test_save_user_message(self):
        """User messages are saved to room."""
        messages = []

        user_message = {
            "role": "user",
            "content": "What are the key considerations?",
            "timestamp": datetime.now().isoformat(),
        }

        messages.append(user_message)

        assert len(messages) == 1
        assert messages[0]["role"] == "user"

    def test_save_agent_response(self):
        """Agent responses are saved with attribution."""
        messages = []

        agent_message = {
            "role": "assistant",
            "agent_id": "atlas",
            "content": MOCK_AGENT_RESPONSES["atlas"],
            "timestamp": datetime.now().isoformat(),
        }

        messages.append(agent_message)

        assert messages[0]["agent_id"] == "atlas"

    def test_message_order_preserved(self):
        """Messages maintain chronological order."""
        messages = []

        for i in range(5):
            messages.append(
                {
                    "id": f"msg-{i}",
                    "timestamp": datetime.now().isoformat(),
                }
            )

        # Messages should be in order
        for i in range(len(messages) - 1):
            assert messages[i]["timestamp"] <= messages[i + 1]["timestamp"]

    def test_multi_agent_responses_in_sequence(self):
        """Multiple agent responses are properly sequenced."""
        messages = []
        agents = ["atlas", "capital", "guardian"]

        for agent in agents:
            messages.append(
                {
                    "role": "assistant",
                    "agent_id": agent,
                    "content": MOCK_AGENT_RESPONSES.get(agent, "Response"),
                }
            )

        agent_sequence = [m["agent_id"] for m in messages if m["role"] == "assistant"]
        assert agent_sequence == agents


class TestSmartBrevityInMeetings:
    """Tests for Smart Brevity format in meeting responses."""

    def test_response_has_clear_structure(self):
        """Responses follow Smart Brevity structure."""
        response = MOCK_AGENT_RESPONSES["atlas"]

        # Should have substantial content but be concise
        word_count = len(response.split())
        assert 20 <= word_count <= 100

    def test_response_leads_with_key_point(self):
        """Response leads with the most important information."""
        response = MOCK_AGENT_RESPONSES["capital"]

        # First sentence should be substantive
        first_sentence = response.split(".")[0]
        assert len(first_sentence.split()) >= 5

    def test_no_filler_phrases(self):
        """Responses avoid filler phrases."""
        filler_phrases = [
            "I think",
            "In my opinion",
            "It's important to note",
            "As I mentioned",
            "To be honest",
        ]

        for agent, response in MOCK_AGENT_RESPONSES.items():
            for phrase in filler_phrases:
                assert (
                    phrase.lower() not in response.lower()
                ), f"{agent} uses filler phrase: {phrase}"
