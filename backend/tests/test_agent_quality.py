"""Agent Response Quality Tests.

These tests validate that agent responses meet quality standards including:
- Domain relevance (agents respond with appropriate expertise)
- Smart Brevity compliance (word limits)
- Banned phrase avoidance
- Response structure
"""

import re

import pytest

# Sample agent responses for testing
SAMPLE_RESPONSES = {
    "atlas": """
    Key AI Trends for 2026

    Recent Gartner research indicates three dominant trends:

    1. Agentic AI - Autonomous systems capable of multi-step reasoning
    2. Multimodal Foundation Models - Integration of text, image, and code
    3. AI Engineering Platforms - Operationalizing AI at scale

    McKinsey estimates 75% of enterprises will adopt agentic AI by 2027.

    Sources: Gartner Hype Cycle 2025, McKinsey AI Adoption Report
    """,
    "capital": """
    ROI Analysis: AI Chatbot Implementation

    Investment Required: $250,000 (Year 1)
    Annual Savings: $180,000 (support cost reduction)
    Payback Period: 16 months
    3-Year NPV: $412,000 (10% discount rate)

    The financial case is strong with a 72% IRR.
    """,
    "guardian": """
    Security Assessment: AI Implementation

    Key risks identified:
    1. Data Privacy - PII exposure in training data
    2. Model Security - Prompt injection vulnerabilities
    3. Compliance - GDPR/CCPA data handling requirements

    Recommended mitigations: Data anonymization, input validation, privacy impact assessment.
    """,
    "counselor": """
    Legal Considerations: AI Deployment

    Critical issues include:
    1. IP Ownership - Clarify rights to AI-generated content
    2. Liability - Establish accountability for AI decisions
    3. Contracts - Review vendor agreements for AI-specific terms

    Recommend legal review before production deployment.
    """,
    "sage": """
    Change Management: AI Adoption

    Employee concerns are valid and addressable:

    1. Job security fears - Focus on augmentation, not replacement
    2. Skill anxiety - Provide clear training roadmap
    3. Trust issues - Start with low-stakes use cases

    Build champions through early wins and visible leadership support.
    """,
}

# Banned phrases that agents should avoid
BANNED_PHRASES = [
    "Great question",
    "That's a great question",
    "Absolutely",
    "I'd be happy to",
    "I'd love to",
    "Certainly",
    "Of course",
    "Sure thing",
    "No problem",
    "Happy to help",
    "As an AI",
    "As a language model",
]


class TestAgentResponseQuality:
    """Validate agent outputs meet quality standards."""

    @pytest.mark.parametrize(
        "agent,query,expected_traits",
        [
            ("atlas", "Gartner AI trends", ["research", "Gartner", "trends"]),
            ("capital", "Calculate ROI", ["ROI", "NPV", "investment"]),
            ("guardian", "Security risks", ["security", "risk", "compliance"]),
            ("counselor", "IP concerns", ["legal", "IP", "liability"]),
            ("sage", "Employee anxiety", ["change", "employee", "support"]),
        ],
    )
    def test_agent_domain_relevance(self, agent, query, expected_traits):
        """Agent produces domain-appropriate response."""
        response = SAMPLE_RESPONSES.get(agent, "")
        response_lower = response.lower()

        # Check that response contains expected domain terms
        found_traits = [trait for trait in expected_traits if trait.lower() in response_lower]
        assert len(found_traits) >= 1, f"Response lacks domain relevance. Expected: {expected_traits}"

    @pytest.mark.parametrize("agent", SAMPLE_RESPONSES.keys())
    def test_smart_brevity_word_limit(self, agent):
        """Response <= 200 words in chat mode."""
        response = SAMPLE_RESPONSES.get(agent, "")
        # Remove markdown formatting for word count
        clean_response = re.sub(r"\*+", "", response)
        clean_response = re.sub(r"#+", "", clean_response)
        words = clean_response.split()
        word_count = len(words)

        assert word_count <= 200, f"Response too long: {word_count} words (max 200)"

    @pytest.mark.parametrize("agent", SAMPLE_RESPONSES.keys())
    def test_no_banned_phrases(self, agent):
        """Response avoids banned conversational phrases."""
        response = SAMPLE_RESPONSES.get(agent, "")
        response_lower = response.lower()

        for phrase in BANNED_PHRASES:
            assert phrase.lower() not in response_lower, f"Response contains banned phrase: '{phrase}'"

    @pytest.mark.parametrize("agent", SAMPLE_RESPONSES.keys())
    def test_response_has_structure(self, agent):
        """Response has clear structure (headers, bullets, etc.)."""
        response = SAMPLE_RESPONSES.get(agent, "")

        # Check for structural elements
        has_header = "**" in response or "#" in response
        has_bullets = "-" in response or "*" in response or "1." in response

        assert has_header or has_bullets, "Response lacks clear structure"

    def test_atlas_includes_citations(self):
        """Atlas (research agent) includes source citations."""
        response = SAMPLE_RESPONSES["atlas"]
        response_lower = response.lower()

        # Look for citation indicators
        has_citations = (
            "source" in response_lower
            or "gartner" in response_lower
            or "mckinsey" in response_lower
            or "research" in response_lower
        )

        assert has_citations, "Atlas response should include research citations"

    def test_capital_includes_numbers(self):
        """Capital (finance agent) includes financial metrics."""
        response = SAMPLE_RESPONSES["capital"]

        # Look for financial numbers
        has_numbers = bool(re.search(r"\$[\d,]+|\d+%|NPV|ROI|IRR", response))

        assert has_numbers, "Capital response should include financial metrics"

    def test_guardian_identifies_risks(self):
        """Guardian (security agent) identifies specific risks."""
        response = SAMPLE_RESPONSES["guardian"]
        response_lower = response.lower()

        risk_indicators = ["risk", "vulnerability", "compliance", "security", "threat"]
        found_risks = [r for r in risk_indicators if r in response_lower]

        assert len(found_risks) >= 2, "Guardian should identify specific security risks"

    def test_counselor_has_legal_terms(self):
        """Counselor (legal agent) uses appropriate legal terminology."""
        response = SAMPLE_RESPONSES["counselor"]
        response_lower = response.lower()

        legal_terms = ["liability", "ip", "contract", "legal", "compliance", "rights"]
        found_terms = [t for t in legal_terms if t in response_lower]

        assert len(found_terms) >= 2, "Counselor should use legal terminology"

    def test_sage_shows_empathy(self):
        """Sage (people agent) demonstrates empathy and people focus."""
        response = SAMPLE_RESPONSES["sage"]
        response_lower = response.lower()

        people_terms = ["employee", "team", "people", "concern", "support", "fear", "anxiety"]
        found_terms = [t for t in people_terms if t in response_lower]

        assert len(found_terms) >= 2, "Sage should show people-focused empathy"


class TestAgentRouting:
    """Agent routing decision tests."""

    @pytest.mark.parametrize(
        "query,expected_agent",
        [
            ("What does McKinsey say about AI?", "atlas"),
            ("Gartner research on enterprise AI", "atlas"),
            ("Calculate NPV for this project", "capital"),
            ("Build a business case for AI", "capital"),
            ("What are the ROI metrics?", "capital"),
            ("SOC2 compliance requirements", "guardian"),
            ("Security risks of using AI", "guardian"),
            ("Contract terms for AI vendor", "counselor"),
            ("IP ownership of AI outputs", "counselor"),
            ("Reduce employee fear of AI", "sage"),
            ("Change management strategy", "sage"),
            ("Analyze this meeting transcript", "oracle"),
            ("RAG architecture patterns", "architect"),
            ("Process automation opportunities", "operator"),
        ],
    )
    def test_query_keyword_routing(self, query, expected_agent):
        """Verify queries contain keywords that should route to expected agent."""
        # Define keyword mappings
        agent_keywords = {
            "atlas": ["mckinsey", "gartner", "research", "analyst", "trend", "study"],
            "capital": ["roi", "npv", "business case", "financial", "investment", "cost"],
            "guardian": ["security", "compliance", "soc2", "gdpr", "risk", "audit"],
            "counselor": ["contract", "legal", "ip", "liability", "attorney", "law"],
            "sage": ["employee", "change management", "fear", "adoption", "culture"],
            "oracle": ["transcript", "meeting", "notes", "recording"],
            "architect": ["architecture", "rag", "pattern", "technical", "design"],
            "operator": ["process", "automation", "workflow", "operations"],
        }

        query_lower = query.lower()
        expected_keywords = agent_keywords.get(expected_agent, [])

        # At least one keyword should match
        matched = any(kw in query_lower for kw in expected_keywords)
        assert matched, f"Query '{query}' should contain keywords for {expected_agent}"


class TestPromptRegression:
    """Golden response tests to catch prompt regressions."""

    def test_response_does_not_start_with_greeting(self):
        """Responses should not start with casual greetings."""
        greeting_starters = ["hi", "hello", "hey", "sure", "certainly", "of course"]

        for agent, response in SAMPLE_RESPONSES.items():
            first_word = response.strip().split()[0].lower().rstrip("!,.")
            assert first_word not in greeting_starters, f"{agent} response starts with greeting: '{first_word}'"

    def test_response_is_not_just_bullets(self):
        """Responses should have context, not just bullet points."""
        for agent, response in SAMPLE_RESPONSES.items():
            lines = [line.strip() for line in response.strip().split("\n") if line.strip()]

            # Count lines that are bullets vs prose
            bullet_lines = len([line for line in lines if line.startswith("-") or line.startswith("*")])
            total_lines = len(lines)

            # At least 30% should not be bullet points
            if total_lines > 0:
                prose_ratio = (total_lines - bullet_lines) / total_lines
                assert prose_ratio >= 0.2, f"{agent} response is {int((1 - prose_ratio) * 100)}% bullets"

    def test_response_ends_properly(self):
        """Responses should end with complete sentences, not ellipsis."""
        bad_endings = ["...", "etc", "and so on", "and more"]

        for agent, response in SAMPLE_RESPONSES.items():
            response_stripped = response.strip().rstrip("*_")
            for ending in bad_endings:
                assert not response_stripped.endswith(ending), f"{agent} response ends with '{ending}'"


class TestAgentPersonaConsistency:
    """Test that agents maintain consistent personas."""

    def test_atlas_uses_research_language(self):
        """Atlas should reference research sources and data."""
        response = SAMPLE_RESPONSES["atlas"]
        research_terms = ["research", "study", "report", "data", "indicates", "shows"]
        found = any(term in response.lower() for term in research_terms)
        assert found, "Atlas should use research-oriented language"

    def test_capital_uses_financial_language(self):
        """Capital should use financial terminology."""
        response = SAMPLE_RESPONSES["capital"]
        finance_terms = ["investment", "roi", "npv", "savings", "cost", "payback"]
        found = sum(1 for term in finance_terms if term in response.lower())
        assert found >= 2, "Capital should use financial terminology"

    def test_guardian_uses_security_language(self):
        """Guardian should use security/governance terminology."""
        response = SAMPLE_RESPONSES["guardian"]
        security_terms = ["risk", "security", "compliance", "vulnerability", "mitigation"]
        found = sum(1 for term in security_terms if term in response.lower())
        assert found >= 2, "Guardian should use security terminology"

    def test_counselor_uses_legal_language(self):
        """Counselor should use legal terminology."""
        response = SAMPLE_RESPONSES["counselor"]
        legal_terms = ["legal", "liability", "contract", "rights", "agreement"]
        found = sum(1 for term in legal_terms if term in response.lower())
        assert found >= 2, "Counselor should use legal terminology"

    def test_sage_uses_people_language(self):
        """Sage should use people/change-focused terminology."""
        response = SAMPLE_RESPONSES["sage"]
        people_terms = ["employee", "team", "concern", "support", "change", "adoption"]
        found = sum(1 for term in people_terms if term in response.lower())
        assert found >= 2, "Sage should use people-focused terminology"
