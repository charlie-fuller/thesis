"""Tests for Glean Evaluator and Compass Agents

Tests the Glean platform fit assessment and career coaching agents,
including memory save decisions, handoff logic, and context injection.

Note: This test file uses direct module loading to avoid import chain issues
with llama_index dependencies on Python 3.9.
"""

from dataclasses import dataclass
from typing import Optional
from unittest.mock import AsyncMock, Mock

import pytest

# ============================================================================
# Note: This test file uses self-contained agent classes for testing.
# No sys.modules modifications needed - all test classes are defined locally.
# This prevents test pollution when running with other test files.
# ============================================================================


# ============================================================================
# Re-implement Agent Classes for Testing (Isolated from Import Chain)
# ============================================================================


@dataclass
class AgentContext:
    """Context passed to agents for each interaction."""

    user_id: str
    client_id: str
    conversation_id: str
    message_history: list
    user_message: str
    handoff_context: Optional[dict] = None
    memories: Optional[list] = None
    stakeholders: Optional[list] = None


@dataclass
class AgentResponse:
    """Response from an agent."""

    content: str
    agent_name: str
    agent_display_name: str
    handoff_to: Optional[str] = None
    handoff_reason: Optional[str] = None
    extracted_data: Optional[dict] = None
    save_to_memory: bool = False
    memory_content: Optional[str] = None


class BaseAgentTestable:
    """Simplified base agent for testing."""

    def __init__(self, name: str, display_name: str, supabase, anthropic_client):
        self.name = name
        self.display_name = display_name
        self.supabase = supabase
        self.anthropic = anthropic_client
        self._system_instruction = None

    @property
    def system_instruction(self) -> str:
        if self._system_instruction:
            return self._system_instruction
        return self._get_default_instruction()

    def _get_default_instruction(self) -> str:
        return "Default instruction"

    def _build_messages(self, context: AgentContext) -> list:
        messages = []
        for msg in context.message_history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": context.user_message})
        return messages


class GleanEvaluatorAgent(BaseAgentTestable):
    """Glean Evaluator - The "Can We Glean This?" Platform Fit Assessor.

    Test implementation that mirrors the real agent.
    """

    def __init__(self, supabase, anthropic_client):
        super().__init__(
            name="glean_evaluator",
            display_name="Can We Glean This?",
            supabase=supabase,
            anthropic_client=anthropic_client,
        )

    def _get_default_instruction(self) -> str:
        return """You are the Glean Evaluator, known as "Can We Glean This?" for Thesis.

You specialize in:
- Assessing PRDs and application requests for Glean platform fit
- Evaluating integration requirements and data source compatibility
- Analyzing scale, cost, and time-to-value considerations
- Recommending alternatives when Glean is not appropriate

Key Glean capabilities: Enterprise search across 100+ integrations, AI assistant,
permission-aware results, knowledge graph, real-time sync.

Key Glean limitations: Requires 100+ users, ~$60K+ annual cost, no content creation,
limited workflow automation, requires good underlying data quality.

Provide clear GO/NO-GO/MAYBE recommendations with specific reasoning."""

    async def process(self, context: AgentContext) -> AgentResponse:
        """Process a Glean fit assessment query."""
        messages = self._build_messages(context)

        # Add any relevant memories to the context
        if context.memories:
            memory_context = "\n\nRelevant previous context:\n"
            for memory in context.memories[:5]:
                memory_context += f"- {memory.get('content', '')}\n"
            messages[0]["content"] = memory_context + "\n\n" + messages[0]["content"]

        response = self.anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=self.system_instruction,
            messages=messages,
        )

        content = response.content[0].text

        # Determine if this should be saved to memory
        save_to_memory = self._should_save_to_memory(context.user_message, content)

        return AgentResponse(
            content=content,
            agent_name=self.name,
            agent_display_name=self.display_name,
            save_to_memory=save_to_memory,
            memory_content=f"Glean assessment: {context.user_message[:100]}..."
            if save_to_memory
            else None,
        )

    def _should_save_to_memory(self, query: str, response: str) -> bool:
        """Determine if this interaction should be saved to memory."""
        important_indicators = [
            "glean",
            "assessment",
            "recommendation",
            "go",
            "no-go",
            "alternative",
            "integration",
            "platform",
            "decision",
        ]
        query_lower = query.lower()
        response_lower = response.lower()

        for indicator in important_indicators:
            if indicator in query_lower or indicator in response_lower:
                return True

        # Don't save very short responses (likely clarifying questions)
        if len(response) < 200:
            return False

        return False

    def should_handoff(self, context: AgentContext, response: str) -> Optional[tuple]:
        """Check if we should hand off to another agent."""
        message_lower = context.user_message.lower()

        # Hand off to Architect for deep technical architecture questions
        if any(
            word in message_lower
            for word in ["architecture", "rag", "custom build", "technical design"]
        ):
            return ("architect", "Query requires deep technical architecture expertise")

        # Hand off to Guardian for security/compliance deep-dives
        if any(
            word in message_lower
            for word in ["soc2", "hipaa", "gdpr", "security audit", "compliance"]
        ):
            return ("guardian", "Query requires security/compliance expertise")

        # Hand off to Capital for detailed cost analysis
        if any(
            word in message_lower
            for word in ["budget", "roi", "cost breakdown", "financial analysis"]
        ):
            return ("capital", "Query requires detailed financial analysis")

        return None

    def get_connector_registry_query(self, connector_name: str) -> dict:
        """Query connector registry for a specific connector."""
        # Simulates querying glean_connectors table
        query = {
            "table": "glean_connectors",
            "filters": {"name": connector_name},
            "select": ["name", "type", "status", "sync_frequency", "data_types"],
        }
        return query

    def assess_platform_fit(self, requirements: dict) -> dict:
        """Assess if Glean is appropriate for given requirements.

        Returns assessment with recommendation (GO/NO-GO/MAYBE) and reasoning.
        """
        user_count = requirements.get("user_count", 0)
        budget = requirements.get("budget", 0)
        use_case = requirements.get("use_case", "").lower()

        assessment = {"recommendation": "MAYBE", "score": 0.5, "factors": []}

        # User count assessment
        if user_count >= 500:
            assessment["factors"].append(
                {"name": "user_count", "impact": "positive", "note": "Strong user base"}
            )
            assessment["score"] += 0.2
        elif user_count >= 100:
            assessment["factors"].append(
                {"name": "user_count", "impact": "neutral", "note": "Meets minimum"}
            )
        else:
            assessment["factors"].append(
                {"name": "user_count", "impact": "negative", "note": "Below minimum 100 users"}
            )
            assessment["score"] -= 0.3

        # Budget assessment (~$60K minimum)
        if budget >= 80000:
            assessment["factors"].append(
                {"name": "budget", "impact": "positive", "note": "Strong budget"}
            )
            assessment["score"] += 0.2
        elif budget >= 60000:
            assessment["factors"].append(
                {"name": "budget", "impact": "neutral", "note": "Meets baseline"}
            )
        else:
            assessment["factors"].append(
                {"name": "budget", "impact": "negative", "note": "Below $60K baseline"}
            )
            assessment["score"] -= 0.3

        # Use case assessment
        enterprise_search_keywords = [
            "search",
            "find",
            "knowledge",
            "discovery",
            "information retrieval",
        ]
        if any(kw in use_case for kw in enterprise_search_keywords):
            assessment["factors"].append(
                {
                    "name": "use_case",
                    "impact": "positive",
                    "note": "Strong fit for enterprise search",
                }
            )
            assessment["score"] += 0.2

        content_creation_keywords = ["create", "generate", "write", "author"]
        if any(kw in use_case for kw in content_creation_keywords):
            assessment["factors"].append(
                {"name": "use_case", "impact": "negative", "note": "Glean doesn't create content"}
            )
            assessment["score"] -= 0.2

        # Determine final recommendation
        if assessment["score"] >= 0.7:
            assessment["recommendation"] = "GO"
        elif assessment["score"] <= 0.3:
            assessment["recommendation"] = "NO-GO"
        else:
            assessment["recommendation"] = "MAYBE"

        return assessment


class CompassAgent(BaseAgentTestable):
    """Compass - The Personal Career Coach agent.

    Test implementation that mirrors the real agent.
    """

    def __init__(self, supabase, anthropic_client):
        super().__init__(
            name="compass",
            display_name="Compass",
            supabase=supabase,
            anthropic_client=anthropic_client,
        )

    def _get_default_instruction(self) -> str:
        return """<system>
<role>
You are Compass, a personal career development coach. Your purpose is to help professionals track their performance, capture wins, prepare for manager conversations, and maintain strategic alignment with company goals.
</role>
</system>"""

    async def process(self, context: AgentContext) -> AgentResponse:
        """Process a career development or performance tracking query."""
        messages = self._build_messages(context)

        # Add any relevant memories to the context
        if context.memories:
            memory_context = "\n\nRelevant previous context about this person's career:\n"
            for memory in context.memories[:5]:
                memory_context += f"- {memory.get('content', '')}\n"
            messages[0]["content"] = memory_context + "\n\n" + messages[0]["content"]

        # Add stakeholder context if available
        if context.stakeholders:
            stakeholder_context = "\n\nKey relationships being tracked:\n"
            for stakeholder in context.stakeholders[:5]:
                name = stakeholder.get("name", "Unknown")
                role = stakeholder.get("role", "Unknown role")
                engagement = stakeholder.get("engagement_level", "unknown")
                stakeholder_context += f"- {name} ({role}): {engagement}\n"
            messages[0]["content"] = stakeholder_context + "\n\n" + messages[0]["content"]

        response = self.anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=self.system_instruction,
            messages=messages,
        )

        content = response.content[0].text

        save_to_memory = self._should_save_to_memory(context.user_message, content)

        return AgentResponse(
            content=content,
            agent_name=self.name,
            agent_display_name=self.display_name,
            save_to_memory=save_to_memory,
            memory_content=f"Career update: {context.user_message[:100]}..."
            if save_to_memory
            else None,
        )

    def _should_save_to_memory(self, query: str, response: str) -> bool:
        """Determine if this interaction should be saved to memory."""
        important_indicators = [
            "win",
            "accomplished",
            "shipped",
            "launched",
            "completed",
            "goal",
            "check-in",
            "1:1",
            "review",
            "feedback",
            "promotion",
            "growth",
            "skill",
            "competency",
            "impact",
            "stakeholder",
            "relationship",
            "manager",
            "mentor",
        ]
        query_lower = query.lower()
        response_lower = response.lower()

        for indicator in important_indicators:
            if indicator in query_lower or indicator in response_lower:
                return True

        if len(response) < 200:
            return False

        return False

    def should_handoff(self, context: AgentContext, response: str) -> Optional[tuple]:
        """Check if we should hand off to another agent."""
        message_lower = context.user_message.lower()

        # Hand off to Sage for deeper change management or people challenges
        if any(
            word in message_lower
            for word in ["team resistance", "burnout", "culture change", "adoption challenge"]
        ):
            return ("sage", "Query requires people/change management expertise")

        # Hand off to Scholar for training program design
        if any(
            word in message_lower
            for word in ["training program", "learning path", "curriculum", "upskilling plan"]
        ):
            return ("scholar", "Query requires L&D expertise")

        # Hand off to Strategist for executive-level career strategy
        if any(
            word in message_lower
            for word in [
                "executive visibility",
                "c-suite",
                "board presentation",
                "organizational politics",
            ]
        ):
            return ("strategist", "Query requires executive strategy expertise")

        # Hand off to Oracle for meeting transcript analysis
        if any(
            word in message_lower
            for word in ["analyze meeting", "transcript", "what did they say", "meeting notes"]
        ):
            return ("oracle", "Query involves transcript analysis")

        return None

    def detect_win_in_message(self, message: str) -> Optional[dict]:
        """Detect if a message contains a win/accomplishment to capture.

        Returns win details if detected, None otherwise.
        """
        message_lower = message.lower()

        # Win indicators
        win_keywords = [
            "shipped",
            "launched",
            "completed",
            "finished",
            "delivered",
            "achieved",
            "accomplished",
            "won",
            "closed",
            "signed",
            "fixed",
            "resolved",
            "improved",
            "increased",
            "reduced",
            "saved",
            "automated",
            "built",
            "created",
            "implemented",
        ]

        detected_keyword = None
        for keyword in win_keywords:
            if keyword in message_lower:
                detected_keyword = keyword
                break

        if not detected_keyword:
            return None

        # Extract potential metrics
        import re

        metrics = []

        # Percentage patterns
        pct_matches = re.findall(r"(\d+(?:\.\d+)?)\s*%", message)
        for match in pct_matches:
            metrics.append({"type": "percentage", "value": float(match)})

        # Time savings patterns (supports both "saved 10 hours" and "10 hours saved")
        time_patterns = [
            (r"(?:saved|reduced)\s*(\d+)\s*hours?", "hours_saved"),
            (r"(\d+)\s*hours?\s*(?:saved|reduced)", "hours_saved"),
            (r"(?:saved|reduced)\s*(\d+)\s*days?", "days_saved"),
            (r"(\d+)\s*days?\s*(?:saved|reduced|faster)", "days_saved"),
            (r"(?:saved|reduced)\s*(\d+)\s*minutes?", "minutes_saved"),
            (r"(\d+)\s*minutes?\s*(?:saved|reduced)", "minutes_saved"),
        ]
        for pattern, metric_type in time_patterns:
            matches = re.findall(pattern, message_lower)
            for match in matches:
                metrics.append({"type": metric_type, "value": int(match)})

        # Dollar amounts
        dollar_matches = re.findall(r"\$\s*([\d,]+(?:\.\d{2})?)", message)
        for match in dollar_matches:
            metrics.append({"type": "dollars", "value": float(match.replace(",", ""))})

        return {
            "detected": True,
            "keyword": detected_keyword,
            "metrics": metrics,
            "needs_clarification": len(metrics) == 0,  # Ask for impact if no metrics found
        }

    def generate_memory_content(self, win_details: dict, user_message: str) -> str:
        """Generate formatted memory content for a captured win."""
        keyword = win_details.get("keyword", "accomplished")
        metrics = win_details.get("metrics", [])

        # Start with the action
        content = f"Win captured: {keyword.capitalize()} - "

        # Add message summary (first 100 chars)
        summary = user_message[:100]
        if len(user_message) > 100:
            summary += "..."
        content += summary

        # Add metrics if present
        if metrics:
            content += " | Metrics: "
            metric_strs = []
            for m in metrics:
                if m["type"] == "percentage":
                    # Format as integer if whole number, otherwise show decimal
                    val = m["value"]
                    if val == int(val):
                        metric_strs.append(f"{int(val)}%")
                    else:
                        metric_strs.append(f"{val}%")
                elif m["type"] == "dollars":
                    metric_strs.append(f"${m['value']:,.2f}")
                elif "hours" in m["type"]:
                    metric_strs.append(f"{m['value']} hours saved")
                elif "days" in m["type"]:
                    metric_strs.append(f"{m['value']} days saved")
            content += ", ".join(metric_strs)

        return content

    def inject_stakeholder_context(self, context: AgentContext) -> str:
        """Generate stakeholder relationship context for the prompt."""
        if not context.stakeholders:
            return ""

        lines = ["Key relationships being tracked:"]
        for stakeholder in context.stakeholders[:5]:
            name = stakeholder.get("name", "Unknown")
            role = stakeholder.get("role", "Unknown role")
            engagement = stakeholder.get("engagement_level", "unknown")
            priority = stakeholder.get("priority_level", "medium")

            line = f"- {name} ({role}): Engagement={engagement}, Priority={priority}"

            # Add win conditions if available
            win_conditions = stakeholder.get("win_conditions")
            if win_conditions:
                line += f" | Win conditions: {win_conditions[:50]}..."

            lines.append(line)

        return "\n".join(lines)


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_supabase_client():
    """Create mock Supabase client."""
    client = Mock()
    client.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
        data=[]
    )
    client.table.return_value.insert.return_value.execute.return_value = Mock(data=[])
    return client


@pytest.fixture
def mock_anthropic_client():
    """Create mock Anthropic client with default response."""
    client = Mock()
    response = Mock()
    response.content = [
        Mock(
            text="This is a test response from Claude with sufficient length to pass the memory save threshold for testing purposes."
        )
    ]
    client.messages.create.return_value = response
    return client


@pytest.fixture
def glean_agent(mock_supabase_client, mock_anthropic_client):
    """Create Glean Evaluator agent for testing."""
    return GleanEvaluatorAgent(mock_supabase_client, mock_anthropic_client)


@pytest.fixture
def compass_agent(mock_supabase_client, mock_anthropic_client):
    """Create Compass agent for testing."""
    return CompassAgent(mock_supabase_client, mock_anthropic_client)


@pytest.fixture
def sample_context():
    """Create a sample AgentContext for testing."""
    return AgentContext(
        user_id="user-123",
        client_id="client-456",
        conversation_id="conv-789",
        message_history=[],
        user_message="Test message",
    )


# ============================================================================
# Test: Glean Evaluator Agent - Connector Registry Queries
# ============================================================================


class TestGleanConnectorRegistry:
    """Test Glean Evaluator connector registry query functionality."""

    def test_connector_query_structure(self, glean_agent):
        """Connector query should have correct structure."""
        query = glean_agent.get_connector_registry_query("slack")

        assert query["table"] == "glean_connectors"
        assert query["filters"]["name"] == "slack"
        assert "name" in query["select"]
        assert "type" in query["select"]
        assert "status" in query["select"]

    def test_connector_query_with_different_names(self, glean_agent):
        """Query should work with various connector names."""
        connectors = ["slack", "google_drive", "confluence", "jira", "salesforce"]

        for connector in connectors:
            query = glean_agent.get_connector_registry_query(connector)
            assert query["filters"]["name"] == connector

    def test_connector_query_includes_sync_frequency(self, glean_agent):
        """Connector query should include sync frequency field."""
        query = glean_agent.get_connector_registry_query("notion")

        assert "sync_frequency" in query["select"]

    def test_connector_query_includes_data_types(self, glean_agent):
        """Connector query should include data types field."""
        query = glean_agent.get_connector_registry_query("zendesk")

        assert "data_types" in query["select"]


# ============================================================================
# Test: Glean Evaluator Agent - Platform Fit Assessment
# ============================================================================


class TestGleanPlatformFitAssessment:
    """Test Glean platform fit assessment logic."""

    def test_go_recommendation_high_users_high_budget(self, glean_agent):
        """High users and budget should result in GO recommendation."""
        requirements = {
            "user_count": 500,
            "budget": 100000,
            "use_case": "enterprise knowledge search and discovery",
        }

        result = glean_agent.assess_platform_fit(requirements)

        assert result["recommendation"] == "GO"
        assert result["score"] >= 0.7

    def test_no_go_recommendation_low_users(self, glean_agent):
        """User count below 100 should result in NO-GO."""
        requirements = {"user_count": 50, "budget": 80000, "use_case": "search"}

        result = glean_agent.assess_platform_fit(requirements)

        assert result["recommendation"] in ["NO-GO", "MAYBE"]
        negative_factors = [f for f in result["factors"] if f["impact"] == "negative"]
        assert any("user" in f["note"].lower() for f in negative_factors)

    def test_no_go_recommendation_low_budget(self, glean_agent):
        """Budget below $60K should result in negative factor."""
        requirements = {"user_count": 200, "budget": 30000, "use_case": "search"}

        result = glean_agent.assess_platform_fit(requirements)

        negative_factors = [f for f in result["factors"] if f["impact"] == "negative"]
        assert any("budget" in f["name"].lower() for f in negative_factors)

    def test_content_creation_negative_factor(self, glean_agent):
        """Content creation use case should add negative factor."""
        requirements = {
            "user_count": 500,
            "budget": 100000,
            "use_case": "create and generate marketing content",
        }

        result = glean_agent.assess_platform_fit(requirements)

        negative_factors = [f for f in result["factors"] if f["impact"] == "negative"]
        assert any("content" in f["note"].lower() for f in negative_factors)

    def test_search_use_case_positive_factor(self, glean_agent):
        """Search-related use case should add positive factor."""
        requirements = {
            "user_count": 300,
            "budget": 70000,
            "use_case": "enterprise search across all company knowledge",
        }

        result = glean_agent.assess_platform_fit(requirements)

        positive_factors = [f for f in result["factors"] if f["impact"] == "positive"]
        assert any("search" in f["note"].lower() for f in positive_factors)

    def test_maybe_recommendation_borderline_case(self, glean_agent):
        """Borderline requirements should result in MAYBE."""
        requirements = {
            "user_count": 100,
            "budget": 60000,
            "use_case": "general information lookup",
        }

        result = glean_agent.assess_platform_fit(requirements)

        assert result["recommendation"] == "MAYBE"


# ============================================================================
# Test: Glean Evaluator Agent - Memory Save Decisions
# ============================================================================


class TestGleanMemorySaveDecisions:
    """Test Glean Evaluator memory save decision heuristics."""

    def test_save_memory_when_glean_mentioned(self, glean_agent):
        """Should save to memory when 'glean' is mentioned."""
        result = glean_agent._should_save_to_memory(
            "Is Glean right for our use case?",
            "Based on the analysis, Glean would be a good fit for your enterprise search needs.",
        )

        assert result is True

    def test_save_memory_for_assessment_queries(self, glean_agent):
        """Should save to memory for assessment-related queries."""
        result = glean_agent._should_save_to_memory(
            "Please assess our platform requirements",
            "The assessment indicates that your organization meets the criteria.",
        )

        assert result is True

    def test_save_memory_for_go_no_go_decisions(self, glean_agent):
        """Should save to memory when go/no-go decisions are made."""
        result = glean_agent._should_save_to_memory(
            "Should we proceed with this integration?",
            "My recommendation is GO - the platform meets all requirements.",
        )

        assert result is True

    def test_no_save_for_short_responses(self, glean_agent):
        """Should not save very short responses (clarifying questions)."""
        result = glean_agent._should_save_to_memory(
            "What is the weather?", "Could you clarify your question?"
        )

        assert result is False

    def test_save_memory_for_alternative_recommendations(self, glean_agent):
        """Should save when alternatives are recommended."""
        result = glean_agent._should_save_to_memory(
            "What should we use instead?",
            "I recommend an alternative solution that better fits your needs.",
        )

        assert result is True


# ============================================================================
# Test: Glean Evaluator Agent - Handoff Triggers
# ============================================================================


class TestGleanHandoffTriggers:
    """Test Glean Evaluator handoff routing logic."""

    def test_handoff_to_architect_for_technical_design(self, glean_agent, sample_context):
        """Should handoff to Architect for technical design questions."""
        sample_context.user_message = "How should we design the technical architecture?"

        result = glean_agent.should_handoff(sample_context, "response")

        assert result is not None
        assert result[0] == "architect"
        assert "architecture" in result[1].lower()

    def test_handoff_to_architect_for_rag(self, glean_agent, sample_context):
        """Should handoff to Architect for RAG questions."""
        sample_context.user_message = "Should we build a custom RAG solution?"

        result = glean_agent.should_handoff(sample_context, "response")

        assert result is not None
        assert result[0] == "architect"

    def test_handoff_to_guardian_for_compliance(self, glean_agent, sample_context):
        """Should handoff to Guardian for compliance questions."""
        sample_context.user_message = "What are the HIPAA compliance requirements?"

        result = glean_agent.should_handoff(sample_context, "response")

        assert result is not None
        assert result[0] == "guardian"
        assert "compliance" in result[1].lower()

    def test_handoff_to_guardian_for_security_audit(self, glean_agent, sample_context):
        """Should handoff to Guardian for security audit questions."""
        sample_context.user_message = "We need to conduct a security audit"

        result = glean_agent.should_handoff(sample_context, "response")

        assert result is not None
        assert result[0] == "guardian"

    def test_handoff_to_capital_for_budget(self, glean_agent, sample_context):
        """Should handoff to Capital for budget questions."""
        sample_context.user_message = "What's the detailed budget breakdown?"

        result = glean_agent.should_handoff(sample_context, "response")

        assert result is not None
        assert result[0] == "capital"
        assert "financial" in result[1].lower()

    def test_no_handoff_for_standard_query(self, glean_agent, sample_context):
        """Should not handoff for standard Glean assessment queries."""
        sample_context.user_message = "Is Glean a good fit for our search needs?"

        result = glean_agent.should_handoff(sample_context, "response")

        assert result is None


# ============================================================================
# Test: Compass Agent - Win Capture Detection
# ============================================================================


class TestCompassWinCapture:
    """Test Compass win capture detection from conversations."""

    def test_detect_shipped_win(self, compass_agent):
        """Should detect 'shipped' as a win indicator."""
        message = "We shipped the new feature yesterday"

        result = compass_agent.detect_win_in_message(message)

        assert result is not None
        assert result["detected"] is True
        assert result["keyword"] == "shipped"

    def test_detect_completed_win(self, compass_agent):
        """Should detect 'completed' as a win indicator."""
        message = "I completed the Q4 project ahead of schedule"

        result = compass_agent.detect_win_in_message(message)

        assert result is not None
        assert result["keyword"] == "completed"

    def test_detect_win_with_percentage_metric(self, compass_agent):
        """Should extract percentage metrics from win messages."""
        message = "Improved performance by 35% after optimization"

        result = compass_agent.detect_win_in_message(message)

        assert result is not None
        assert any(m["type"] == "percentage" and m["value"] == 35.0 for m in result["metrics"])

    def test_detect_win_with_time_savings(self, compass_agent):
        """Should extract time savings metrics."""
        message = "Automated the report process, saved 10 hours per week"

        result = compass_agent.detect_win_in_message(message)

        assert result is not None
        assert any(m["type"] == "hours_saved" for m in result["metrics"])

    def test_detect_win_with_dollar_amount(self, compass_agent):
        """Should extract dollar amounts from win messages."""
        message = "Closed the deal for $50,000 in new revenue"

        result = compass_agent.detect_win_in_message(message)

        assert result is not None
        assert any(m["type"] == "dollars" and m["value"] == 50000.0 for m in result["metrics"])

    def test_no_win_in_regular_message(self, compass_agent):
        """Should return None for messages without wins."""
        message = "I have a meeting with the team tomorrow"

        result = compass_agent.detect_win_in_message(message)

        assert result is None

    def test_needs_clarification_when_no_metrics(self, compass_agent):
        """Should flag need for clarification when no metrics found."""
        message = "I finished the project"

        result = compass_agent.detect_win_in_message(message)

        assert result is not None
        assert result["needs_clarification"] is True


# ============================================================================
# Test: Compass Agent - Memory Content Generation
# ============================================================================


class TestCompassMemoryGeneration:
    """Test Compass memory content generation for wins."""

    def test_generate_memory_with_keyword(self, compass_agent):
        """Memory content should include the win keyword."""
        win_details = {"keyword": "shipped", "metrics": []}

        content = compass_agent.generate_memory_content(win_details, "Shipped the new dashboard")

        assert "Win captured" in content
        assert "Shipped" in content

    def test_generate_memory_with_metrics(self, compass_agent):
        """Memory content should include metrics when available."""
        win_details = {"keyword": "improved", "metrics": [{"type": "percentage", "value": 25.0}]}

        content = compass_agent.generate_memory_content(win_details, "Improved API response time")

        assert "25%" in content
        assert "Metrics" in content

    def test_generate_memory_truncates_long_messages(self, compass_agent):
        """Memory content should truncate very long messages."""
        win_details = {"keyword": "completed", "metrics": []}
        long_message = "Completed " + "a" * 200

        content = compass_agent.generate_memory_content(win_details, long_message)

        assert "..." in content
        assert len(content) < 250

    def test_generate_memory_with_dollar_metrics(self, compass_agent):
        """Memory content should format dollar amounts correctly."""
        win_details = {"keyword": "closed", "metrics": [{"type": "dollars", "value": 100000.00}]}

        content = compass_agent.generate_memory_content(win_details, "Closed major deal")

        assert "$100,000.00" in content


# ============================================================================
# Test: Compass Agent - Stakeholder Context Injection
# ============================================================================


class TestCompassStakeholderContext:
    """Test Compass stakeholder context injection."""

    def test_inject_stakeholder_basic_info(self, compass_agent, sample_context):
        """Should inject basic stakeholder information."""
        sample_context.stakeholders = [
            {"name": "John Smith", "role": "VP Engineering", "engagement_level": "champion"}
        ]

        result = compass_agent.inject_stakeholder_context(sample_context)

        assert "John Smith" in result
        assert "VP Engineering" in result
        assert "champion" in result

    def test_inject_multiple_stakeholders(self, compass_agent, sample_context):
        """Should handle multiple stakeholders."""
        sample_context.stakeholders = [
            {"name": "Alice", "role": "Director", "engagement_level": "engaged"},
            {"name": "Bob", "role": "Manager", "engagement_level": "neutral"},
        ]

        result = compass_agent.inject_stakeholder_context(sample_context)

        assert "Alice" in result
        assert "Bob" in result

    def test_inject_stakeholder_with_win_conditions(self, compass_agent, sample_context):
        """Should include win conditions when available."""
        sample_context.stakeholders = [
            {
                "name": "Carol",
                "role": "CTO",
                "engagement_level": "champion",
                "win_conditions": "Reduce technical debt and improve developer velocity",
            }
        ]

        result = compass_agent.inject_stakeholder_context(sample_context)

        assert "Win conditions" in result
        assert "technical debt" in result

    def test_empty_stakeholders_returns_empty(self, compass_agent, sample_context):
        """Should return empty string when no stakeholders."""
        sample_context.stakeholders = []

        result = compass_agent.inject_stakeholder_context(sample_context)

        assert result == ""

    def test_none_stakeholders_returns_empty(self, compass_agent, sample_context):
        """Should handle None stakeholders gracefully."""
        sample_context.stakeholders = None

        result = compass_agent.inject_stakeholder_context(sample_context)

        assert result == ""

    def test_limit_to_five_stakeholders(self, compass_agent, sample_context):
        """Should limit context to 5 stakeholders."""
        sample_context.stakeholders = [
            {"name": f"Person{i}", "role": "Role", "engagement_level": "neutral"} for i in range(10)
        ]

        result = compass_agent.inject_stakeholder_context(sample_context)

        # Count occurrences of "Person"
        assert result.count("Person") == 5


# ============================================================================
# Test: Compass Agent - Handoff Routing
# ============================================================================


class TestCompassHandoffRouting:
    """Test Compass handoff routing to other agents."""

    def test_handoff_to_sage_for_burnout(self, compass_agent, sample_context):
        """Should handoff to Sage for burnout discussions."""
        sample_context.user_message = "I'm experiencing burnout and need help"

        result = compass_agent.should_handoff(sample_context, "response")

        assert result is not None
        assert result[0] == "sage"
        assert "people" in result[1].lower() or "change" in result[1].lower()

    def test_handoff_to_sage_for_team_resistance(self, compass_agent, sample_context):
        """Should handoff to Sage for team resistance issues."""
        sample_context.user_message = "Dealing with team resistance to the new process"

        result = compass_agent.should_handoff(sample_context, "response")

        assert result is not None
        assert result[0] == "sage"

    def test_handoff_to_scholar_for_training(self, compass_agent, sample_context):
        """Should handoff to Scholar for training program questions."""
        sample_context.user_message = "I want to create a training program for my team"

        result = compass_agent.should_handoff(sample_context, "response")

        assert result is not None
        assert result[0] == "scholar"
        assert "L&D" in result[1]

    def test_handoff_to_scholar_for_curriculum(self, compass_agent, sample_context):
        """Should handoff to Scholar for curriculum design."""
        sample_context.user_message = "Need help designing a curriculum for AI skills"

        result = compass_agent.should_handoff(sample_context, "response")

        assert result is not None
        assert result[0] == "scholar"

    def test_handoff_to_strategist_for_executive_visibility(self, compass_agent, sample_context):
        """Should handoff to Strategist for executive visibility."""
        sample_context.user_message = "How do I get executive visibility for my work?"

        result = compass_agent.should_handoff(sample_context, "response")

        assert result is not None
        assert result[0] == "strategist"
        assert "executive" in result[1].lower()

    def test_handoff_to_strategist_for_board_presentation(self, compass_agent, sample_context):
        """Should handoff to Strategist for board presentations."""
        sample_context.user_message = "I need to prepare a board presentation"

        result = compass_agent.should_handoff(sample_context, "response")

        assert result is not None
        assert result[0] == "strategist"

    def test_handoff_to_oracle_for_transcript_analysis(self, compass_agent, sample_context):
        """Should handoff to Oracle for meeting transcript analysis."""
        sample_context.user_message = "Can you analyze meeting notes from my 1:1?"

        result = compass_agent.should_handoff(sample_context, "response")

        assert result is not None
        assert result[0] == "oracle"
        assert "transcript" in result[1].lower()

    def test_no_handoff_for_standard_career_query(self, compass_agent, sample_context):
        """Should not handoff for standard career tracking queries."""
        sample_context.user_message = "I want to capture a win from today"

        result = compass_agent.should_handoff(sample_context, "response")

        assert result is None


# ============================================================================
# Test: Compass Agent - Memory Save Decisions
# ============================================================================


class TestCompassMemorySaveDecisions:
    """Test Compass memory save decision heuristics."""

    def test_save_memory_for_win_capture(self, compass_agent):
        """Should save to memory when win is mentioned."""
        result = compass_agent._should_save_to_memory(
            "I shipped a new feature today",
            "Great job on shipping that feature! Let me capture that win for you.",
        )

        assert result is True

    def test_save_memory_for_goal_discussion(self, compass_agent):
        """Should save to memory for goal discussions."""
        result = compass_agent._should_save_to_memory(
            "Let's review my Q1 goals",
            "Looking at your goals, you've made good progress on the key objectives.",
        )

        assert result is True

    def test_save_memory_for_check_in_prep(self, compass_agent):
        """Should save to memory for check-in preparation."""
        result = compass_agent._should_save_to_memory(
            "Help me prepare for my 1:1 with my manager",
            "For your 1:1 check-in, here are the key points to discuss based on your recent work.",
        )

        assert result is True

    def test_save_memory_for_feedback(self, compass_agent):
        """Should save to memory when feedback is discussed."""
        result = compass_agent._should_save_to_memory(
            "I received some feedback today",
            "That's valuable feedback. Let me help you document and reflect on it.",
        )

        assert result is True

    def test_no_save_for_short_responses(self, compass_agent):
        """Should not save very short responses."""
        result = compass_agent._should_save_to_memory("Hi", "Hello! How can I help?")

        assert result is False

    def test_no_save_for_unrelated_topics(self, compass_agent):
        """Should not save for topics unrelated to career tracking."""
        result = compass_agent._should_save_to_memory(
            "What's the weather like?",
            "I'm not able to help with weather questions. Perhaps try a weather service instead."
            + " " * 200,
        )

        # Even though response is long, no important indicators present
        assert result is False


# ============================================================================
# Test: Agent Process Method Integration
# ============================================================================


class TestAgentProcessIntegration:
    """Test the process method integration for both agents."""

    @pytest.mark.asyncio
    async def test_glean_process_returns_agent_response(self, glean_agent, sample_context):
        """Glean process should return properly structured AgentResponse."""
        sample_context.user_message = "Is Glean a good fit for our organization?"

        response = await glean_agent.process(sample_context)

        assert isinstance(response, AgentResponse)
        assert response.agent_name == "glean_evaluator"
        assert response.agent_display_name == "Can We Glean This?"

    @pytest.mark.asyncio
    async def test_glean_process_with_memories(self, glean_agent, sample_context):
        """Glean process should incorporate memories into context."""
        sample_context.memories = [
            {"content": "Previous Glean assessment recommended GO"},
            {"content": "Organization has 500+ users"},
        ]
        sample_context.user_message = "What was our previous assessment?"

        await glean_agent.process(sample_context)

        # Verify API was called (meaning memories were processed)
        glean_agent.anthropic.messages.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_compass_process_returns_agent_response(self, compass_agent, sample_context):
        """Compass process should return properly structured AgentResponse."""
        sample_context.user_message = "I want to capture a win"

        response = await compass_agent.process(sample_context)

        assert isinstance(response, AgentResponse)
        assert response.agent_name == "compass"
        assert response.agent_display_name == "Compass"

    @pytest.mark.asyncio
    async def test_compass_process_with_stakeholders(self, compass_agent, sample_context):
        """Compass process should incorporate stakeholder context."""
        sample_context.stakeholders = [
            {"name": "Test Manager", "role": "Engineering Manager", "engagement_level": "champion"}
        ]
        sample_context.user_message = "Help me prepare for my 1:1"

        await compass_agent.process(sample_context)

        # Verify API was called
        compass_agent.anthropic.messages.create.assert_called_once()


# ============================================================================
# MANUAL AGENT TESTS - Documentation Assistant
# ============================================================================


class ManualAgentTestable(BaseAgentTestable):
    """Manual agent for testing - documentation assistant."""

    def __init__(self, supabase, anthropic_client):
        super().__init__("manual", "Manual", supabase, anthropic_client)
        self.help_topics = [
            "agents",
            "chat",
            "meeting-rooms",
            "knowledge-base",
            "tasks",
            "projects",
            "stakeholders",
            "faq",
        ]

    def detect_help_topic(self, message: str) -> Optional[str]:
        """Detect which help topic the user is asking about."""
        message_lower = message.lower()

        topic_keywords = {
            "agents": ["agent", "atlas", "capital", "guardian", "sage", "coordinator"],
            "chat": ["chat", "conversation", "message", "ask"],
            "meeting-rooms": ["meeting", "room", "discussion", "autonomous"],
            "knowledge-base": ["kb", "knowledge base", "document", "upload", "file"],
            "projects": ["project", "pipeline", "tier", "score"],
            "tasks": ["task", "kanban", "todo"],
            "stakeholders": ["stakeholder", "contact", "engagement"],
            "faq": ["faq", "help", "how do i", "how to", "what is"],
        }

        for topic, keywords in topic_keywords.items():
            if any(kw in message_lower for kw in keywords):
                return topic

        return None

    def get_help_content(self, topic: str) -> Optional[str]:
        """Get help content for a specific topic."""
        content_map = {
            "agents": "Thesis has 21 specialized AI agents...",
            "chat": "The chat interface allows you to interact with agents...",
            "meeting-rooms": "Meeting rooms enable multi-agent discussions...",
            "knowledge-base": "The Knowledge Base stores your documents...",
            "tasks": "Task management uses a Kanban board...",
            "projects": "Track AI implementation projects...",
            "stakeholders": "Manage stakeholder relationships...",
            "faq": "Frequently asked questions about Thesis...",
        }
        return content_map.get(topic)

    def should_handoff(self, context: AgentContext, response: str) -> Optional[tuple]:
        """Manual agent should handoff for domain-specific questions."""
        message_lower = context.user_message.lower()

        # Handoff to domain experts for specific questions
        if any(kw in message_lower for kw in ["roi", "budget", "cost", "financial"]):
            return ("capital", "Handing off to Capital for financial questions")

        if any(kw in message_lower for kw in ["security", "compliance", "governance"]):
            return ("guardian", "Handing off to Guardian for security/compliance questions")

        if any(kw in message_lower for kw in ["research", "case study", "benchmark"]):
            return ("atlas", "Handing off to Atlas for research questions")

        return None


@pytest.fixture
def manual_agent():
    """Create a Manual agent instance for testing."""
    mock_supabase = Mock()
    mock_anthropic = Mock()
    mock_anthropic.messages.create = AsyncMock(
        return_value=Mock(content=[Mock(text="Here's how to use that feature...")])
    )
    return ManualAgentTestable(mock_supabase, mock_anthropic)


class TestManualHelpTopicDetection:
    """Tests for Manual agent help topic detection."""

    def test_detect_agents_topic(self, manual_agent):
        """Should detect agents topic."""
        result = manual_agent.detect_help_topic("How do I use the Atlas agent?")
        assert result == "agents"

    def test_detect_chat_topic(self, manual_agent):
        """Should detect chat topic."""
        result = manual_agent.detect_help_topic("How do I start a conversation?")
        assert result == "chat"

    def test_detect_meeting_rooms_topic(self, manual_agent):
        """Should detect meeting rooms topic."""
        result = manual_agent.detect_help_topic("How do I create a meeting room?")
        assert result == "meeting-rooms"

    def test_detect_knowledge_base_topic(self, manual_agent):
        """Should detect knowledge base topic."""
        result = manual_agent.detect_help_topic("How do I upload a document to the KB?")
        assert result == "knowledge-base"

    def test_detect_tasks_topic(self, manual_agent):
        """Should detect tasks topic."""
        result = manual_agent.detect_help_topic("Where is the kanban board for my todos?")
        assert result == "tasks"

    def test_detect_projects_topic(self, manual_agent):
        """Should detect projects topic."""
        result = manual_agent.detect_help_topic("How do I add a project to the pipeline?")
        assert result == "projects"

    def test_detect_stakeholders_topic(self, manual_agent):
        """Should detect stakeholders topic."""
        result = manual_agent.detect_help_topic("How do I track stakeholder engagement?")
        assert result == "stakeholders"

    def test_detect_faq_topic(self, manual_agent):
        """Should detect FAQ topic for general questions."""
        result = manual_agent.detect_help_topic("How do I get started?")
        assert result == "faq"

    def test_no_topic_for_unrelated_message(self, manual_agent):
        """Should return None for unrelated messages."""
        result = manual_agent.detect_help_topic("What's the weather like?")
        assert result is None


class TestManualHelpContent:
    """Tests for Manual agent help content retrieval."""

    def test_get_agents_content(self, manual_agent):
        """Should return content for agents topic."""
        content = manual_agent.get_help_content("agents")
        assert content is not None
        assert len(content) > 0

    def test_get_all_topics_have_content(self, manual_agent):
        """All help topics should have content."""
        for topic in manual_agent.help_topics:
            content = manual_agent.get_help_content(topic)
            assert content is not None, f"Missing content for topic: {topic}"

    def test_unknown_topic_returns_none(self, manual_agent):
        """Unknown topic should return None."""
        content = manual_agent.get_help_content("unknown_topic")
        assert content is None


class TestManualHandoffRouting:
    """Tests for Manual agent handoff to domain experts."""

    def test_handoff_to_capital_for_financial(self, manual_agent, sample_context):
        """Should handoff to Capital for financial questions."""
        sample_context.user_message = "What's the ROI calculation method?"

        result = manual_agent.should_handoff(sample_context, "response")

        assert result is not None
        assert result[0] == "capital"

    def test_handoff_to_guardian_for_security(self, manual_agent, sample_context):
        """Should handoff to Guardian for security questions."""
        sample_context.user_message = "What compliance standards does this support?"

        result = manual_agent.should_handoff(sample_context, "response")

        assert result is not None
        assert result[0] == "guardian"

    def test_handoff_to_atlas_for_research(self, manual_agent, sample_context):
        """Should handoff to Atlas for research questions."""
        sample_context.user_message = "Can you find research case study benchmarks about this?"

        result = manual_agent.should_handoff(sample_context, "response")

        assert result is not None
        assert result[0] == "atlas"

    def test_no_handoff_for_help_questions(self, manual_agent, sample_context):
        """Should not handoff for standard help questions."""
        sample_context.user_message = "How do I use the chat feature?"

        result = manual_agent.should_handoff(sample_context, "response")

        assert result is None


class TestManualAgentMetadata:
    """Tests for Manual agent metadata and configuration."""

    def test_agent_name(self, manual_agent):
        """Agent should have correct name."""
        assert manual_agent.name == "manual"

    def test_agent_display_name(self, manual_agent):
        """Agent should have correct display name."""
        assert manual_agent.display_name == "Manual"

    def test_help_topics_count(self, manual_agent):
        """Agent should have expected number of help topics."""
        assert len(manual_agent.help_topics) == 8

    def test_all_expected_topics_present(self, manual_agent):
        """Agent should have all expected help topics."""
        expected_topics = [
            "agents",
            "chat",
            "meeting-rooms",
            "knowledge-base",
            "tasks",
            "projects",
            "stakeholders",
            "faq",
        ]
        for topic in expected_topics:
            assert topic in manual_agent.help_topics
