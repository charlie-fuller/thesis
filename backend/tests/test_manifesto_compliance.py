"""Tests for manifesto compliance scoring and admin analytics.

Updated for PocketBase migration: admin_client now uses API key auth.
The manifesto compliance scorer itself is pure logic (no DB dependency).
Admin endpoint tests still mock the data layer where the endpoint queries data.
"""

import asyncio
from unittest.mock import MagicMock, patch

from services.manifesto_compliance import (
    AGENT_EXPECTED_PRINCIPLES,
    PRINCIPLE_SIGNALS,
    _get_compliance_level,
    _normalize_agent_name,
    score_manifesto_compliance,
    should_semantic_evaluate,
    trigger_semantic_evaluation,
)

# ============================================================================
# TestManifestoScorer
# ============================================================================


class TestManifestoScorer:
    """Tests for the regex-based manifesto compliance scorer."""

    def test_empty_response_returns_zero(self):
        result = score_manifesto_compliance("")
        assert result["score"] == 0.0
        assert result["signals"] == []
        assert result["gaps"] == []
        assert result["agent"] is None
        assert result["level"] == "misaligned"

    def test_none_response_returns_zero(self):
        result = score_manifesto_compliance(None)
        assert result["score"] == 0.0

    def test_p1_state_change_detection(self):
        text = "We need to measure the state change from baseline to target."
        result = score_manifesto_compliance(text)
        assert "P1_state_change" in result["signals"]

    def test_p3_evidence_detection(self):
        text = "Research shows that the data shows a clear trend based on available data."
        result = score_manifesto_compliance(text)
        assert "P3_evidence_over_eloquence" in result["signals"]

    def test_p4_output_type_detection(self):
        text = "This is a non-deterministic output in the dangerous middle -- an informed interpretation, not ground truth."
        result = score_manifesto_compliance(text)
        assert "P4_know_your_output_type" in result["signals"]

    def test_p5_people_detection(self):
        text = (
            "People are the center of this transformation. We must consider the human experience and meaningful work."
        )
        result = score_manifesto_compliance(text)
        assert "P5_people_are_the_center" in result["signals"]

    def test_p6_humans_decide_detection(self):
        text = "I recommend this approach, but ultimately you decide. This is input to human decision."
        result = score_manifesto_compliance(text)
        assert "P6_humans_decide" in result["signals"]

    def test_strategist_full_signals_scores_1(self):
        """Strategist with all expected signals should score 1.0."""
        text = (
            "Let's measure the state change from baseline to target. "
            "What problem are we solving before jumping to solutions? "
            "This is a non-deterministic informed interpretation. "
            "People are the center of this transformation. "
            "I recommend this approach, but you decide."
        )
        result = score_manifesto_compliance(text, "strategist")
        assert result["score"] == 1.0
        assert result["gaps"] == []
        assert result["level"] == "aligned"

    def test_strategist_partial_signals(self):
        """Strategist with some signals should score proportionally."""
        text = "We need to measure the state change. What problem are we solving?"
        result = score_manifesto_compliance(text, "strategist")
        assert result["score"] == 0.4
        assert result["level"] == "drifting"
        assert len(result["gaps"]) == 3

    def test_unknown_agent_fallback(self):
        """Unknown agent should score based on total principle coverage."""
        text = "Research shows evidence of a state change."
        result = score_manifesto_compliance(text, "nonexistent_agent")
        assert result["agent"] == "nonexistent_agent"
        assert result["score"] > 0.0
        assert result["gaps"] == []

    def test_normalize_agent_name_display_name(self):
        assert _normalize_agent_name("The Strategist") == "strategist"

    def test_normalize_agent_name_prefix(self):
        assert _normalize_agent_name("Agent Oracle") == "oracle"

    def test_normalize_agent_name_lowercase(self):
        assert _normalize_agent_name("CAPITAL") == "capital"

    def test_normalize_agent_name_whitespace(self):
        assert _normalize_agent_name("  reporter  ") == "reporter"

    def test_all_agents_have_valid_principle_keys(self):
        """Every principle in AGENT_EXPECTED_PRINCIPLES must exist in PRINCIPLE_SIGNALS."""
        for agent, principles in AGENT_EXPECTED_PRINCIPLES.items():
            for principle in principles:
                assert (
                    principle in PRINCIPLE_SIGNALS
                ), f"Agent '{agent}' expects principle '{principle}' which is not defined in PRINCIPLE_SIGNALS"

    def test_get_compliance_level_aligned(self):
        assert _get_compliance_level(1.0) == "aligned"
        assert _get_compliance_level(0.60) == "aligned"
        assert _get_compliance_level(0.75) == "aligned"

    def test_get_compliance_level_drifting(self):
        assert _get_compliance_level(0.30) == "drifting"
        assert _get_compliance_level(0.59) == "drifting"
        assert _get_compliance_level(0.45) == "drifting"

    def test_get_compliance_level_misaligned(self):
        assert _get_compliance_level(0.0) == "misaligned"
        assert _get_compliance_level(0.29) == "misaligned"
        assert _get_compliance_level(0.10) == "misaligned"

    def test_source_field_present_when_provided(self):
        result = score_manifesto_compliance("state change test", source="chat")
        assert result["source"] == "chat"

    def test_source_field_absent_when_not_provided(self):
        result = score_manifesto_compliance("state change test")
        assert "source" not in result

    def test_source_field_meeting(self):
        result = score_manifesto_compliance("evidence shows", source="meeting")
        assert result["source"] == "meeting"

    def test_level_field_always_present(self):
        result = score_manifesto_compliance("no signals here")
        assert "level" in result

        result2 = score_manifesto_compliance("state change evidence shows", "strategist")
        assert "level" in result2

    def test_empty_response_with_source(self):
        result = score_manifesto_compliance("", source="chat")
        assert result["source"] == "chat"
        assert result["level"] == "misaligned"


# ============================================================================
# TestAdminEndpoint
# ============================================================================


class TestAdminEndpoint:
    """Tests for the admin manifesto compliance analytics endpoint."""

    def _make_compliance_record(
        self, agent="strategist", score=0.8, signals=None, gaps=None, source="chat", level="aligned"
    ):
        return {
            "agent": agent,
            "score": score,
            "signals": signals or ["P1_state_change", "P3_evidence_over_eloquence"],
            "gaps": gaps or [],
            "source": source,
            "level": level,
        }

    def test_response_structure(self, admin_client):
        """Admin endpoint returns correct top-level structure."""
        response = admin_client.get("/api/admin/analytics/manifesto-compliance")
        assert response.status_code == 200
        data = response.json()
        assert "period_days" in data
        assert "total_scored_messages" in data
        assert "by_agent" in data
        assert "by_principle" in data
        assert "drift_alerts" in data
        assert "level_distribution" in data
        assert "by_source" in data

    def test_empty_data_no_errors(self, admin_client):
        """Empty data should return zeros, not errors."""
        response = admin_client.get("/api/admin/analytics/manifesto-compliance")
        assert response.status_code == 200
        data = response.json()
        assert data["total_scored_messages"] == 0
        assert data["drift_alerts"] == []
        assert data["level_distribution"] == {"aligned": 0, "drifting": 0, "misaligned": 0}

    def test_drift_alert_low_hit_rate(self):
        """Agent with <25% hit rate on expected principle should trigger drift alert."""
        from api.routes.admin.manifesto_compliance import get_manifesto_compliance

        records = [
            self._make_compliance_record(
                agent="strategist",
                score=0.2,
                signals=["P3_evidence_over_eloquence"],
                gaps=[
                    "P1_state_change",
                    "P2_problems_before_solutions",
                    "P4_know_your_output_type",
                    "P5_people_are_the_center",
                ],
                level="misaligned",
            )
            for _ in range(5)
        ]

        mock_sb = MagicMock()
        chat_data = [{"metadata": {"manifesto_compliance": r}} for r in records]
        chat_exec = MagicMock(data=chat_data)
        meeting_exec = MagicMock(data=[])

        table_mock = MagicMock()
        mock_sb.table.return_value = table_mock

        select_mock = MagicMock()
        table_mock.select.return_value = select_mock

        eq_mock = MagicMock()
        select_mock.eq.return_value = eq_mock
        gte_mock = MagicMock()
        eq_mock.gte.return_value = gte_mock
        lte_mock = MagicMock()
        gte_mock.lte.return_value = lte_mock
        lte_mock.execute.return_value = chat_exec

        gte_mock2 = MagicMock()
        select_mock.gte.return_value = gte_mock2
        lte_mock2 = MagicMock()
        gte_mock2.lte.return_value = lte_mock2
        not_mock = MagicMock()
        lte_mock2.not_ = not_mock
        is_mock = MagicMock()
        not_mock.is_.return_value = is_mock
        is_mock.execute.return_value = meeting_exec

        with patch("api.routes.admin.manifesto_compliance.supabase", mock_sb):
            result = asyncio.get_event_loop().run_until_complete(
                get_manifesto_compliance(current_user={"id": "admin", "role": "admin"}, days=30)
            )

        assert len(result["drift_alerts"]) > 0
        p1_alerts = [
            a for a in result["drift_alerts"] if a["agent"] == "strategist" and a["principle"] == "P1_state_change"
        ]
        assert len(p1_alerts) > 0

    def test_no_drift_alert_few_messages(self):
        """Agent with fewer than MIN_MESSAGES_FOR_EVALUATION messages should not trigger drift alerts."""
        from api.routes.admin.manifesto_compliance import get_manifesto_compliance

        records = [
            self._make_compliance_record(
                agent="strategist", score=0.0, signals=[], gaps=["P1_state_change"], level="misaligned"
            )
            for _ in range(2)
        ]

        mock_sb = MagicMock()
        chat_data = [{"metadata": {"manifesto_compliance": r}} for r in records]
        chat_exec = MagicMock(data=chat_data)
        meeting_exec = MagicMock(data=[])

        table_mock = MagicMock()
        mock_sb.table.return_value = table_mock
        select_mock = MagicMock()
        table_mock.select.return_value = select_mock
        eq_mock = MagicMock()
        select_mock.eq.return_value = eq_mock
        gte_mock = MagicMock()
        eq_mock.gte.return_value = gte_mock
        lte_mock = MagicMock()
        gte_mock.lte.return_value = lte_mock
        lte_mock.execute.return_value = chat_exec

        gte_mock2 = MagicMock()
        select_mock.gte.return_value = gte_mock2
        lte_mock2 = MagicMock()
        gte_mock2.lte.return_value = lte_mock2
        not_mock = MagicMock()
        lte_mock2.not_ = not_mock
        is_mock = MagicMock()
        not_mock.is_.return_value = is_mock
        is_mock.execute.return_value = meeting_exec

        with patch("api.routes.admin.manifesto_compliance.supabase", mock_sb):
            result = asyncio.get_event_loop().run_until_complete(
                get_manifesto_compliance(current_user={"id": "admin", "role": "admin"}, days=30)
            )

        strategist_alerts = [a for a in result["drift_alerts"] if a["agent"] == "strategist"]
        assert len(strategist_alerts) == 0

    def test_level_distribution_and_source_in_response(self):
        """Response should include level_distribution and by_source."""
        from api.routes.admin.manifesto_compliance import get_manifesto_compliance

        records = [
            self._make_compliance_record(score=0.8, level="aligned", source="chat"),
            self._make_compliance_record(score=0.4, level="drifting", source="meeting"),
            self._make_compliance_record(score=0.1, level="misaligned", source="chat"),
        ]

        mock_sb = MagicMock()
        chat_data = [{"metadata": {"manifesto_compliance": r}} for r in records]
        chat_exec = MagicMock(data=chat_data)
        meeting_exec = MagicMock(data=[])

        table_mock = MagicMock()
        mock_sb.table.return_value = table_mock
        select_mock = MagicMock()
        table_mock.select.return_value = select_mock
        eq_mock = MagicMock()
        select_mock.eq.return_value = eq_mock
        gte_mock = MagicMock()
        eq_mock.gte.return_value = gte_mock
        lte_mock = MagicMock()
        gte_mock.lte.return_value = lte_mock
        lte_mock.execute.return_value = chat_exec

        gte_mock2 = MagicMock()
        select_mock.gte.return_value = gte_mock2
        lte_mock2 = MagicMock()
        gte_mock2.lte.return_value = lte_mock2
        not_mock = MagicMock()
        lte_mock2.not_ = not_mock
        is_mock = MagicMock()
        not_mock.is_.return_value = is_mock
        is_mock.execute.return_value = meeting_exec

        with patch("api.routes.admin.manifesto_compliance.supabase", mock_sb):
            result = asyncio.get_event_loop().run_until_complete(
                get_manifesto_compliance(current_user={"id": "admin", "role": "admin"}, days=30)
            )

        assert result["level_distribution"]["aligned"] == 1
        assert result["level_distribution"]["drifting"] == 1
        assert result["level_distribution"]["misaligned"] == 1
        assert "chat" in result["by_source"]
        assert "meeting" in result["by_source"]
        assert result["by_source"]["chat"]["messages"] == 2
        assert result["by_source"]["meeting"]["messages"] == 1


# ============================================================================
# TestSemanticScorer
# ============================================================================


class TestSemanticScorer:
    """Tests for semantic evaluation selection logic and trigger."""

    def test_should_evaluate_zero_signals_with_expected(self):
        """Zero signals for an agent with expectations should trigger."""
        result = {"signals": [], "gaps": ["P1_state_change"], "score": 0.0}
        assert should_semantic_evaluate(result, "strategist") is True

    def test_should_evaluate_zero_signals_no_expected(self):
        """Zero signals for unknown agent should not always trigger."""
        result = {"signals": [], "gaps": [], "score": 0.0}
        results = [should_semantic_evaluate(result, "unknown_agent") for _ in range(50)]
        assert False in results

    def test_should_evaluate_with_signals(self):
        """With signals present and no zero-signal trigger, 20% random sample."""
        result = {"signals": ["P1_state_change"], "gaps": [], "score": 0.5}
        results = [should_semantic_evaluate(result, "strategist") for _ in range(100)]
        true_count = sum(results)
        assert 5 <= true_count <= 40

    def test_trigger_no_event_loop(self):
        """trigger_semantic_evaluation should handle no event loop gracefully."""
        trigger_semantic_evaluation(
            "test response",
            "strategist",
            {"signals": [], "score": 0.0},
            message_id=None,
            table_name="messages",
        )

    @patch("services.manifesto_semantic_scorer._check_rate_limit", return_value=False)
    @patch("services.manifesto_semantic_scorer.os.environ.get", return_value="test-key")
    def test_evaluate_rate_limited(self, mock_env, mock_rate):
        """Rate limited evaluations should return None."""
        from services.manifesto_semantic_scorer import evaluate_semantic_compliance

        result = asyncio.get_event_loop().run_until_complete(
            evaluate_semantic_compliance("test", "strategist", {"score": 0.5, "signals": [], "gaps": []})
        )
        assert result is None

    @patch("services.manifesto_semantic_scorer._check_rate_limit", return_value=True)
    def test_evaluate_no_api_key(self, mock_rate):
        """Missing API key should return None."""
        from services.manifesto_semantic_scorer import evaluate_semantic_compliance

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": ""}):
            result = asyncio.get_event_loop().run_until_complete(
                evaluate_semantic_compliance("test", "strategist", {"score": 0.5, "signals": [], "gaps": []})
            )
        assert result is None


# ============================================================================
# TestDriftTracker
# ============================================================================


class TestDriftTracker:
    """Tests for the in-memory compliance drift tracker."""

    def setup_method(self):
        """Reset drift tracker state before each test."""
        from services.compliance_drift_tracker import _conversation_drift, _conversation_gaps

        _conversation_drift.clear()
        _conversation_gaps.clear()

    def test_no_reminder_fewer_than_3_scores(self):
        """No reminder should be generated with fewer than DRIFT_WINDOW scores."""
        from services.compliance_drift_tracker import get_compliance_reminder, record_compliance_score

        record_compliance_score("conv1", "strategist", 0.0, ["P1_state_change"])
        record_compliance_score("conv1", "strategist", 0.0, ["P1_state_change"])
        assert get_compliance_reminder("strategist", "conv1") is None

    def test_no_reminder_above_threshold(self):
        """No reminder when avg score >= drifting threshold."""
        from services.compliance_drift_tracker import get_compliance_reminder, record_compliance_score

        record_compliance_score("conv2", "strategist", 0.5, [])
        record_compliance_score("conv2", "strategist", 0.4, [])
        record_compliance_score("conv2", "strategist", 0.3, [])
        assert get_compliance_reminder("strategist", "conv2") is None

    def test_reminder_generated_when_drifting(self):
        """Reminder generated when 3+ scores avg below threshold."""
        from services.compliance_drift_tracker import get_compliance_reminder, record_compliance_score

        record_compliance_score("conv3", "strategist", 0.1, ["P1_state_change"])
        record_compliance_score("conv3", "strategist", 0.0, ["P1_state_change", "P2_problems_before_solutions"])
        record_compliance_score("conv3", "strategist", 0.2, ["P1_state_change"])
        reminder = get_compliance_reminder("strategist", "conv3")
        assert reminder is not None
        assert "[COMPLIANCE NOTE]" in reminder

    def test_reminder_includes_gap_names(self):
        """Reminder text should include human-readable principle names."""
        from services.compliance_drift_tracker import get_compliance_reminder, record_compliance_score

        record_compliance_score("conv4", "oracle", 0.0, ["P3_evidence_over_eloquence"])
        record_compliance_score("conv4", "oracle", 0.0, ["P4_know_your_output_type"])
        record_compliance_score("conv4", "oracle", 0.1, ["P3_evidence_over_eloquence"])
        reminder = get_compliance_reminder("oracle", "conv4")
        assert reminder is not None
        assert "Evidence Over Eloquence" in reminder
        assert "Know Your Output Type" in reminder

    def test_recovery_clears_reminder(self):
        """Reminder should disappear after scores improve."""
        from services.compliance_drift_tracker import get_compliance_reminder, record_compliance_score

        record_compliance_score("conv5", "strategist", 0.0, ["P1_state_change"])
        record_compliance_score("conv5", "strategist", 0.1, ["P1_state_change"])
        record_compliance_score("conv5", "strategist", 0.0, ["P1_state_change"])
        assert get_compliance_reminder("strategist", "conv5") is not None

        record_compliance_score("conv5", "strategist", 0.8, [])
        record_compliance_score("conv5", "strategist", 0.9, [])
        record_compliance_score("conv5", "strategist", 0.7, [])
        assert get_compliance_reminder("strategist", "conv5") is None

    def test_clear_conversation(self):
        """clear_conversation should remove all tracking data."""
        from services.compliance_drift_tracker import (
            clear_conversation,
            get_compliance_reminder,
            record_compliance_score,
        )

        record_compliance_score("conv6", "strategist", 0.0, ["P1_state_change"])
        record_compliance_score("conv6", "strategist", 0.0, ["P1_state_change"])
        record_compliance_score("conv6", "strategist", 0.0, ["P1_state_change"])
        assert get_compliance_reminder("strategist", "conv6") is not None

        clear_conversation("conv6")
        assert get_compliance_reminder("strategist", "conv6") is None

    def test_memory_limit_eviction(self):
        """Oldest conversations should be evicted past MAX_TRACKED_CONVERSATIONS."""
        from services.compliance_drift_tracker import (
            MAX_TRACKED_CONVERSATIONS,
            _conversation_drift,
            record_compliance_score,
        )

        for i in range(MAX_TRACKED_CONVERSATIONS):
            record_compliance_score(f"conv_{i}", "strategist", 0.5, [])

        assert len(_conversation_drift) == MAX_TRACKED_CONVERSATIONS

        record_compliance_score("conv_new", "strategist", 0.5, [])
        assert len(_conversation_drift) == MAX_TRACKED_CONVERSATIONS
        assert "conv_0" not in _conversation_drift
        assert "conv_new" in _conversation_drift

    def test_self_assessment_in_reminder(self):
        """Reminder should include self-assessment instruction."""
        from services.compliance_drift_tracker import get_compliance_reminder, record_compliance_score

        record_compliance_score("conv7", "strategist", 0.0, ["P1_state_change"])
        record_compliance_score("conv7", "strategist", 0.0, ["P1_state_change"])
        record_compliance_score("conv7", "strategist", 0.0, ["P1_state_change"])
        reminder = get_compliance_reminder("strategist", "conv7")
        assert reminder is not None
        assert "reflect on which principles" in reminder
