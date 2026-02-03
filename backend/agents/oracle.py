"""Oracle Agent - Transcript Analyzer.

The Oracle agent specializes in:
- Parsing meeting transcripts (Granola, Otter.ai, plain text)
- Extracting attendees and inferring roles
- Analyzing sentiment per speaker
- Identifying concerns and enthusiasm signals
- Generating meeting summaries
- Linking speakers to stakeholders
"""

import logging
import re
from datetime import datetime, timezone
from typing import Optional

import anthropic

from supabase import Client

from .base_agent import AgentContext, AgentResponse, BaseAgent

logger = logging.getLogger(__name__)


class OracleAgent(BaseAgent):
    """Oracle - The Transcript Analyzer agent.

    Specializes in extracting stakeholder insights from meeting transcripts.
    """

    def __init__(self, supabase: Client, anthropic_client: anthropic.Anthropic):
        super().__init__(
            name="oracle",
            display_name="Oracle",
            supabase=supabase,
            anthropic_client=anthropic_client,
        )

    def _get_default_instruction(self) -> str:
        """Returns the default Oracle instruction.

        This should match the content in system_instructions/agents/oracle.xml.

        NOTE: The canonical version is in oracle.xml. This is a fallback.
        """
        return """<system>.

<version>
Name: Oracle - Meeting Intelligence and Stakeholder Analyst
Version: 2.0
Date: 2025-12-27
Created_By: Charlie Fuller
Methodology: Gigawatt v4.0 RCCI Framework with Chain-of-Thought
Inspiration: CIPHER v2.1 - transforming conversations into structured intelligence
</version>

<role>
You are Oracle, an advanced AI specialist in transforming meeting transcripts, conversations, and informal communications into structured stakeholder intelligence. Your name reflects your core function: revealing hidden insights and organizational dynamics from conversations that others might miss.

Core Mission: Transform meeting transcripts into actionable stakeholder intelligence that supports successful GenAI implementation. You decode complex organizational knowledge, uncover sentiment patterns, and make hidden dynamics visible.

When approaching any transcript analysis task, follow these systematic steps:
1. Parse the input thoroughly to understand format, participants, and context
2. Break down the conversation into analyzable components
3. Identify patterns in sentiment, concerns, and stakeholder positioning
4. Structure the insights logically and clearly with evidence
5. Generate actionable recommendations based on the analysis
6. Flag uncertainty and areas requiring additional context

Your capabilities include:
- Advanced natural language processing for meeting transcript analysis
- Sophisticated sentiment detection from spoken language patterns
- Pattern recognition for stakeholder dynamics and power structures
- Clear extraction of action items, decisions, and open questions
- Strategic intelligence synthesis for engagement planning
</role>

<capabilities>
## 1. Transcript Parsing and Speaker Analysis
- Parse transcripts from multiple formats (Granola, Otter.ai, Teams, Zoom, plain text)
- Identify speakers and infer organizational roles from context
- Map speaking patterns (who dominates, who stays silent, who gets interrupted)
- Detect conversation flow and topic transitions
- Handle partial transcripts and unclear attributions gracefully

## 2. Sentiment Analysis and Emotional Intelligence
- Analyze sentiment for each speaker on multiple dimensions:
  - Explicit sentiment (what they say)
  - Implicit sentiment (how they say it, what they avoid)
  - Projected sentiment (how others respond to them)
- Extract concern signals:
  - Direct concerns (explicitly stated objections)
  - Hedging language (indicators of uncertainty or resistance)
  - Protective statements (defending turf, deflecting responsibility)
  - Fear signals (job security, capability gaps, change fatigue)
- Identify enthusiasm and support signals:
  - Active engagement and volunteering
  - Building on others' ideas
  - Forward-looking statements and planning
  - Resource commitment offers

## 3. Meeting Intelligence Extraction
- Generate concise meeting summaries capturing key themes
- Extract action items with owners, dependencies, and due dates
- Identify decisions made (explicit and implicit)
- Catalog open questions and unresolved issues
- Detect commitments and promises made
- Note topics that were raised but deflected or tabled

## 4. Stakeholder Dynamic Analysis
- Map influence patterns (who defers to whom)
- Identify coalition structures (who aligns with whom)
- Detect conflict points and relationship tensions
- Assess individual stakeholder engagement levels
- Track position shifts over time (when historical context available)
- Identify champions, skeptics, and fence-sitters

## 5. Strategic Intelligence Synthesis
- Prioritize insights by actionability and urgency
- Connect meeting insights to broader stakeholder management strategy
- Recommend specific follow-up actions per stakeholder
- Flag risks requiring immediate attention
- Identify opportunities for building alignment
- Suggest talking points for future engagements
</capabilities>

<instructions>
## Chain-of-Thought Analysis Process

When analyzing any transcript, work through these steps systematically:

### Step 1: Format Recognition and Parsing
- What format is this transcript in?
- How are speakers identified?
- What context is provided about the meeting purpose?

### Step 2: Participant Mapping
- Who are the participants and what are their likely roles?
- What is each person's likely stake in the AI initiative?
- Who speaks most/least? What might this indicate?

### Step 3: Sentiment Deep-Dive
For each significant participant:
- What is their explicit sentiment? (Quote evidence)
- What implicit signals do they give?
- What concerns do they raise, directly or indirectly?

### Step 4: Content Extraction
- What are the key topics discussed?
- What decisions were made (explicit or implied)?
- What action items were assigned or volunteered?
- What questions remain open?

### Step 5: Relationship and Dynamic Analysis
- Who aligned with whom on key topics?
- Were there any conflicts or tensions?
- Who exercised influence and how was it received?

### Step 6: Strategic Synthesis
- What are the most actionable insights?
- What risks require immediate attention?
- What follow-up actions are recommended per stakeholder?

## Output Format for Transcript Analysis

1. **Meeting Summary** - 2-3 sentence overview
2. **Meeting Metadata** - Date, type, duration estimate
3. **Attendees** - Name, role, organization, engagement level
4. **Sentiment Analysis by Speaker** - Sentiment, score, key statements, concerns
5. **Key Topics Discussed** - Listed by prominence
6. **Action Items** - Description, owner, due date
7. **Decisions Made** - Explicit and implicit
8. **Open Questions** - Unresolved topics
9. **Stakeholder Insights** - Type, content, quote, confidence
10. **Strategic Recommendations** - Follow-up actions, risk flags

## Sentiment Scoring (0.0 to 1.0)
- 0.0-0.2: Strongly negative (active resistance)
- 0.2-0.4: Negative (concerns, skepticism)
- 0.4-0.6: Neutral (balanced, wait-and-see)
- 0.6-0.8: Positive (supportive, engaged)
- 0.8-1.0: Strongly positive (championing, enthusiastic)

## Communication Principles
- Evidence-based: cite specific quotes
- Objective: avoid editorializing
- Nuanced: capture complexity
- Actionable: focus on what can be done
- Honest about uncertainty
</instructions>

<criteria>
## Response Quality Standards
- Evidence-Based: Every sentiment backed by quotes
- Complete: All speakers analyzed
- Actionable: Clear recommendations
- Objective: Balanced without projecting intent
- Strategic: Connected to AI implementation success
</criteria>

<wisdom>
## Core Beliefs

**CONVERSATIONS REVEAL WHAT DOCUMENTS HIDE**
Transcripts contain signals that formal communications filter out.

**SILENCE SPEAKS**
Who stays quiet, who gets interrupted - these patterns reveal power structures.

**HISTORY SHAPES RESPONSE**
Current reactions are shaped by past experiences. Understanding "scar tissue" is essential.

**OBJECTIONS ARE DATA**
Resistance contains valuable risk information. Treat objections as intelligence.

**EVIDENCE FIRST**
Every sentiment assessment should be traceable to specific quotes.
</wisdom>

</system>"""

    async def process(self, context: AgentContext) -> AgentResponse:
        """Process a transcript or transcript-related query."""
        message = context.user_message

        # Check if this looks like a transcript upload
        if self._looks_like_transcript(message):
            return await self._analyze_transcript(message, context)

        # Otherwise, answer questions about transcripts or stakeholders
        return await self._answer_query(context)

    def _looks_like_transcript(self, text: str) -> bool:
        """Detect if the message contains a transcript.

        Transcripts typically have:
        - Speaker labels (Name: or [Name])
        - Multiple speakers
        - Conversational content
        """
        # Common transcript patterns
        patterns = [
            r"^[A-Z][a-z]+\s*:",  # "John:"
            r"^\[[A-Z][a-z]+\]",  # "[John]"
            r"^\*\*[A-Z][a-z]+\*\*:",  # "**John**:"
            r"^Speaker \d+:",  # "Speaker 1:"
        ]

        lines = text.strip().split("\n")
        speaker_lines = 0

        for line in lines[:50]:  # Check first 50 lines
            for pattern in patterns:
                if re.match(pattern, line.strip()):
                    speaker_lines += 1
                    break

        # If more than 3 speaker-labeled lines, likely a transcript
        return speaker_lines >= 3

    async def _analyze_transcript(self, transcript: str, context: AgentContext) -> AgentResponse:
        """Analyze a meeting transcript and extract insights."""
        analysis_prompt = f"""Analyze the following meeting transcript and extract insights.

TRANSCRIPT:
{transcript}

Provide your analysis in the following JSON structure (respond ONLY with valid JSON):

{{
    "meeting_summary": "2-3 sentence summary of the meeting",
    "meeting_date": "YYYY-MM-DD if mentioned, null otherwise",
    "meeting_type": "discovery | planning | review | standup | other",
    "attendees": [
        {{
            "name": "Full Name",
            "role": "Inferred role (e.g., VP Finance, Engineer)",
            "organization": "Company name if mentioned",
            "speaking_time_estimate": "high | medium | low"
        }}
    ],
    "sentiment_by_speaker": [
        {{
            "name": "Speaker name",
            "overall_sentiment": "positive | neutral | negative | mixed",
            "sentiment_score": 0.0 to 1.0 (0 = very negative, 1 = very positive),
            "key_statements": ["Notable quotes that indicate sentiment"],
            "concerns": ["Specific concerns raised"],
            "enthusiasm": ["Signs of support or enthusiasm"]
        }}
    ],
    "key_topics": ["Main topics discussed"],
    "action_items": [
        {{
            "description": "What needs to be done",
            "owner": "Who is responsible (if mentioned)",
            "due_date": "Due date if mentioned"
        }}
    ],
    "decisions": ["Decisions made during the meeting"],
    "open_questions": ["Unresolved questions or topics needing follow-up"],
    "stakeholder_insights": [
        {{
            "stakeholder_name": "Name",
            "insight_type": "concern | enthusiasm | question | commitment | objection",
            "content": "Description of the insight",
            "quote": "Direct quote if available",
            "confidence": 0.0 to 1.0
        }}
    ],
    "recommendations": ["Suggested follow-up actions based on the meeting"]
}}

Respond with ONLY the JSON object, no additional text."""

        try:
            response = self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                messages=[{"role": "user", "content": analysis_prompt}],
            )

            analysis_json = response.content[0].text

            # Parse and validate the JSON
            import json

            analysis = json.loads(analysis_json)

            # Store the analysis in the database
            await self._store_analysis(analysis, transcript, context)

            # Format a readable response
            readable_response = self._format_analysis(analysis)

            return AgentResponse(
                content=readable_response,
                agent_name=self.name,
                agent_display_name=self.display_name,
                extracted_data=analysis,
                save_to_memory=True,
                memory_content=f"Analyzed meeting transcript: {analysis.get('meeting_summary', '')}",
            )

        except Exception as e:
            logger.error(f"Transcript analysis failed: {e}")
            return AgentResponse(
                content=f"I encountered an error analyzing the transcript: {str(e)}. Please try again or check that the transcript format is correct.",
                agent_name=self.name,
                agent_display_name=self.display_name,
            )

    async def _store_analysis(self, analysis: dict, raw_text: str, context: AgentContext) -> None:
        """Store the transcript analysis in the database."""
        try:
            # Parse meeting date if provided
            meeting_date = None
            if analysis.get("meeting_date"):
                try:
                    meeting_date = (
                        datetime.strptime(analysis["meeting_date"], "%Y-%m-%d").date().isoformat()
                    )
                except (ValueError, TypeError):
                    meeting_date = None

            # Create meeting transcript record
            transcript_data = {
                "client_id": context.client_id,
                "user_id": context.user_id,
                "title": analysis.get("meeting_summary", "Untitled Meeting")[:500],
                "meeting_date": meeting_date,
                "meeting_type": analysis.get("meeting_type", "other"),
                "raw_text": raw_text,
                "attendees": analysis.get("attendees", []),
                "summary": analysis.get("meeting_summary"),
                "key_topics": analysis.get("key_topics", []),
                "sentiment_summary": {"by_speaker": analysis.get("sentiment_by_speaker", [])},
                "action_items": analysis.get("action_items", []),
                "decisions": analysis.get("decisions", []),
                "open_questions": analysis.get("open_questions", []),
                "processing_status": "completed",
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "metadata": {"recommendations": analysis.get("recommendations", [])},
            }

            result = self.supabase.table("meeting_transcripts").insert(transcript_data).execute()
            transcript_id = result.data[0]["id"] if result.data else None

            # Create or update stakeholders and insights
            if transcript_id:
                await self._process_stakeholder_insights(
                    analysis.get("stakeholder_insights", []),
                    analysis.get("attendees", []),
                    transcript_id,
                    context,
                )

            logger.info(f"Stored transcript analysis with ID: {transcript_id}")

        except Exception as e:
            logger.error(f"Failed to store transcript analysis: {e}")
            # Don't raise - we still want to return the analysis to the user

    async def _process_stakeholder_insights(
        self, insights: list[dict], attendees: list[dict], transcript_id: str, context: AgentContext
    ) -> None:
        """Process and store stakeholder insights from the analysis."""
        try:
            # First, try to find or create stakeholders for each attendee
            stakeholder_map = {}  # name -> stakeholder_id

            for attendee in attendees:
                name = attendee.get("name", "").strip()
                if not name:
                    continue

                # Try to find existing stakeholder by name
                existing = (
                    self.supabase.table("stakeholders")
                    .select("id")
                    .eq("client_id", context.client_id)
                    .ilike("name", f"%{name}%")
                    .execute()
                )

                if existing.data:
                    stakeholder_map[name] = existing.data[0]["id"]
                else:
                    # Create new stakeholder
                    new_stakeholder = {
                        "client_id": context.client_id,
                        "name": name,
                        "role": attendee.get("role"),
                        "organization": attendee.get("organization", "Contentful"),
                        "first_interaction": datetime.now(timezone.utc).date().isoformat(),
                        "last_interaction": datetime.now(timezone.utc).isoformat(),
                        "total_interactions": 1,
                    }
                    result = self.supabase.table("stakeholders").insert(new_stakeholder).execute()
                    if result.data:
                        stakeholder_map[name] = result.data[0]["id"]

            # Now store insights linked to stakeholders
            for insight in insights:
                stakeholder_name = insight.get("stakeholder_name", "").strip()
                stakeholder_id = stakeholder_map.get(stakeholder_name)

                if stakeholder_id:
                    insight_data = {
                        "stakeholder_id": stakeholder_id,
                        "meeting_transcript_id": transcript_id,
                        "insight_type": insight.get("insight_type", "concern"),
                        "content": insight.get("content", ""),
                        "extracted_quote": insight.get("quote"),
                        "confidence": insight.get("confidence", 0.8),
                    }
                    self.supabase.table("stakeholder_insights").insert(insight_data).execute()

        except Exception as e:
            logger.error(f"Failed to process stakeholder insights: {e}")

    def _format_meeting_info(self, analysis: dict) -> list[str]:
        """Format meeting summary and info."""
        parts = []
        if analysis.get("meeting_summary"):
            parts.append(f"## Meeting Summary\n\n{analysis['meeting_summary']}")

        info_parts = []
        if analysis.get("meeting_date"):
            info_parts.append(f"**Date:** {analysis['meeting_date']}")
        if analysis.get("meeting_type"):
            info_parts.append(f"**Type:** {analysis['meeting_type'].title()}")
        if info_parts:
            parts.append("\n".join(info_parts))
        return parts

    def _format_attendees(self, attendees: list) -> list[str]:
        """Format attendee list."""
        parts = ["\n## Attendees\n"]
        for attendee in attendees:
            role = f" - {attendee.get('role', 'Unknown Role')}" if attendee.get("role") else ""
            org = f" ({attendee.get('organization')})" if attendee.get("organization") else ""
            parts.append(f"- **{attendee.get('name', 'Unknown')}**{role}{org}")
        return parts

    def _format_sentiment(self, speakers: list) -> list[str]:
        """Format sentiment analysis by speaker."""
        parts = ["\n## Sentiment Analysis\n"]
        for speaker in speakers:
            sentiment = speaker.get("overall_sentiment", "neutral").title()
            score = speaker.get("sentiment_score", 0.5)
            emoji = "🟢" if score > 0.6 else "🟡" if score > 0.4 else "🔴"
            parts.append(f"\n### {speaker.get('name', 'Unknown')} - {emoji} {sentiment}")

            if speaker.get("concerns"):
                parts.append("\n**Concerns:**")
                for concern in speaker["concerns"]:
                    parts.append(f"- {concern}")

            if speaker.get("enthusiasm"):
                parts.append("\n**Enthusiasm:**")
                for item in speaker["enthusiasm"]:
                    parts.append(f"- {item}")
        return parts

    def _format_action_items(self, items: list) -> list[str]:
        """Format action items list."""
        parts = ["\n## Action Items\n"]
        for item in items:
            owner = f" [@{item.get('owner')}]" if item.get("owner") else ""
            due = f" (Due: {item.get('due_date')})" if item.get("due_date") else ""
            parts.append(f"- [ ] {item.get('description', '')}{owner}{due}")
        return parts

    def _format_simple_list(self, items: list, header: str) -> list[str]:
        """Format a simple bulleted list with header."""
        parts = [f"\n## {header}\n"]
        for item in items:
            parts.append(f"- {item}")
        return parts

    def _format_analysis(self, analysis: dict) -> str:
        """Format the analysis as readable markdown."""
        parts = []

        # Meeting info
        parts.extend(self._format_meeting_info(analysis))

        # Attendees
        if analysis.get("attendees"):
            parts.extend(self._format_attendees(analysis["attendees"]))

        # Sentiment Analysis
        if analysis.get("sentiment_by_speaker"):
            parts.extend(self._format_sentiment(analysis["sentiment_by_speaker"]))

        # Key Topics
        if analysis.get("key_topics"):
            parts.extend(self._format_simple_list(analysis["key_topics"], "Key Topics"))

        # Action Items
        if analysis.get("action_items"):
            parts.extend(self._format_action_items(analysis["action_items"]))

        # Decisions
        if analysis.get("decisions"):
            parts.extend(self._format_simple_list(analysis["decisions"], "Decisions Made"))

        # Open Questions
        if analysis.get("open_questions"):
            parts.extend(self._format_simple_list(analysis["open_questions"], "Open Questions"))

        # Recommendations
        if analysis.get("recommendations"):
            parts.extend(self._format_simple_list(analysis["recommendations"], "Recommendations"))

        return "\n".join(parts)

    async def _answer_query(self, context: AgentContext) -> AgentResponse:
        """Answer a question about transcripts or stakeholders."""
        messages = self._build_messages(context)

        response = self.anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=self.system_instruction,
            messages=messages,
        )

        return AgentResponse(
            content=response.content[0].text,
            agent_name=self.name,
            agent_display_name=self.display_name,
        )

    def should_handoff(self, context: AgentContext, response: str) -> Optional[tuple[str, str]]:
        """Check if we should hand off to another agent."""
        message_lower = context.user_message.lower()

        # Hand off to Capital for ROI/cost questions
        if any(
            word in message_lower for word in ["roi", "cost", "budget", "savings", "investment"]
        ):
            return ("capital", "Query involves financial analysis")

        # Hand off to Guardian for security/compliance
        if any(word in message_lower for word in ["security", "compliance", "governance", "risk"]):
            return ("guardian", "Query involves security or governance")

        # Hand off to Counselor for legal
        if any(word in message_lower for word in ["legal", "contract", "liability", "ip"]):
            return ("counselor", "Query involves legal considerations")

        # Hand off to Atlas for research
        if any(
            word in message_lower for word in ["research", "study", "best practice", "industry"]
        ):
            return ("atlas", "Query requires research")

        return None
