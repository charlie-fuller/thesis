"""
Oracle Agent - Transcript Analyzer

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
from typing import Optional
from datetime import datetime

import anthropic
from supabase import Client

from .base_agent import BaseAgent, AgentContext, AgentResponse

logger = logging.getLogger(__name__)


class OracleAgent(BaseAgent):
    """
    Oracle - The Transcript Analyzer agent.

    Specializes in extracting stakeholder insights from meeting transcripts.
    """

    def __init__(self, supabase: Client, anthropic_client: anthropic.Anthropic):
        super().__init__(
            name="oracle",
            display_name="Oracle",
            supabase=supabase,
            anthropic_client=anthropic_client
        )

    def _get_default_instruction(self) -> str:
        return """You are Oracle, the Transcript Analyzer agent for Thesis.

Your role is to help analyze meeting transcripts and extract valuable stakeholder insights.

CAPABILITIES:
1. Parse transcripts from various formats (Granola, Otter.ai, plain text)
2. Identify speakers and infer their roles from context
3. Analyze sentiment for each speaker (positive, neutral, negative)
4. Extract explicit concerns and implicit resistance signals
5. Identify enthusiasm and support signals
6. Generate concise meeting summaries
7. Extract action items and decisions
8. Link speakers to existing stakeholders when possible

ANALYSIS APPROACH:
- Be objective and evidence-based in sentiment analysis
- Quote specific statements when identifying concerns or enthusiasm
- Consider context when inferring roles and sentiment
- Flag uncertainty when making inferences
- Prioritize actionable insights

OUTPUT FORMAT:
When analyzing a transcript, structure your response as:
1. **Meeting Summary** - 2-3 sentence overview
2. **Attendees** - Name, inferred role, organization (if mentioned)
3. **Sentiment Analysis** - Per-speaker sentiment with evidence
4. **Key Insights** - Notable concerns, questions, commitments
5. **Action Items** - Tasks mentioned with owners if specified
6. **Recommendations** - Follow-up actions based on the analysis

TONE:
- Professional and analytical
- Objective without editorializing
- Concise but thorough
- Supportive of the user's strategic goals"""

    async def process(self, context: AgentContext) -> AgentResponse:
        """Process a transcript or transcript-related query."""
        message = context.user_message

        # Check if this looks like a transcript upload
        if self._looks_like_transcript(message):
            return await self._analyze_transcript(message, context)

        # Otherwise, answer questions about transcripts or stakeholders
        return await self._answer_query(context)

    def _looks_like_transcript(self, text: str) -> bool:
        """
        Detect if the message contains a transcript.

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
                messages=[{"role": "user", "content": analysis_prompt}]
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
                memory_content=f"Analyzed meeting transcript: {analysis.get('meeting_summary', '')}"
            )

        except Exception as e:
            logger.error(f"Transcript analysis failed: {e}")
            return AgentResponse(
                content=f"I encountered an error analyzing the transcript: {str(e)}. Please try again or check that the transcript format is correct.",
                agent_name=self.name,
                agent_display_name=self.display_name
            )

    async def _store_analysis(self, analysis: dict, raw_text: str, context: AgentContext) -> None:
        """Store the transcript analysis in the database."""
        try:
            # Parse meeting date if provided
            meeting_date = None
            if analysis.get("meeting_date"):
                try:
                    meeting_date = datetime.strptime(analysis["meeting_date"], "%Y-%m-%d").date().isoformat()
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
                "sentiment_summary": {
                    "by_speaker": analysis.get("sentiment_by_speaker", [])
                },
                "action_items": analysis.get("action_items", []),
                "decisions": analysis.get("decisions", []),
                "open_questions": analysis.get("open_questions", []),
                "processing_status": "completed",
                "processed_at": datetime.utcnow().isoformat(),
                "metadata": {
                    "recommendations": analysis.get("recommendations", [])
                }
            }

            result = self.supabase.table("meeting_transcripts").insert(transcript_data).execute()
            transcript_id = result.data[0]["id"] if result.data else None

            # Create or update stakeholders and insights
            if transcript_id:
                await self._process_stakeholder_insights(
                    analysis.get("stakeholder_insights", []),
                    analysis.get("attendees", []),
                    transcript_id,
                    context
                )

            logger.info(f"Stored transcript analysis with ID: {transcript_id}")

        except Exception as e:
            logger.error(f"Failed to store transcript analysis: {e}")
            # Don't raise - we still want to return the analysis to the user

    async def _process_stakeholder_insights(
        self,
        insights: list[dict],
        attendees: list[dict],
        transcript_id: str,
        context: AgentContext
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
                existing = self.supabase.table("stakeholders") \
                    .select("id") \
                    .eq("client_id", context.client_id) \
                    .ilike("name", f"%{name}%") \
                    .execute()

                if existing.data:
                    stakeholder_map[name] = existing.data[0]["id"]
                else:
                    # Create new stakeholder
                    new_stakeholder = {
                        "client_id": context.client_id,
                        "name": name,
                        "role": attendee.get("role"),
                        "organization": attendee.get("organization", "Contentful"),
                        "first_interaction": datetime.utcnow().date().isoformat(),
                        "last_interaction": datetime.utcnow().isoformat(),
                        "total_interactions": 1
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
                        "confidence": insight.get("confidence", 0.8)
                    }
                    self.supabase.table("stakeholder_insights").insert(insight_data).execute()

        except Exception as e:
            logger.error(f"Failed to process stakeholder insights: {e}")

    def _format_analysis(self, analysis: dict) -> str:
        """Format the analysis as readable markdown."""
        parts = []

        # Meeting Summary
        if analysis.get("meeting_summary"):
            parts.append(f"## Meeting Summary\n\n{analysis['meeting_summary']}")

        # Meeting Info
        info_parts = []
        if analysis.get("meeting_date"):
            info_parts.append(f"**Date:** {analysis['meeting_date']}")
        if analysis.get("meeting_type"):
            info_parts.append(f"**Type:** {analysis['meeting_type'].title()}")
        if info_parts:
            parts.append("\n".join(info_parts))

        # Attendees
        if analysis.get("attendees"):
            parts.append("\n## Attendees\n")
            for attendee in analysis["attendees"]:
                role = f" - {attendee.get('role', 'Unknown Role')}" if attendee.get("role") else ""
                org = f" ({attendee.get('organization')})" if attendee.get("organization") else ""
                parts.append(f"- **{attendee.get('name', 'Unknown')}**{role}{org}")

        # Sentiment Analysis
        if analysis.get("sentiment_by_speaker"):
            parts.append("\n## Sentiment Analysis\n")
            for speaker in analysis["sentiment_by_speaker"]:
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

        # Key Topics
        if analysis.get("key_topics"):
            parts.append("\n## Key Topics\n")
            for topic in analysis["key_topics"]:
                parts.append(f"- {topic}")

        # Action Items
        if analysis.get("action_items"):
            parts.append("\n## Action Items\n")
            for item in analysis["action_items"]:
                owner = f" [@{item.get('owner')}]" if item.get("owner") else ""
                due = f" (Due: {item.get('due_date')})" if item.get("due_date") else ""
                parts.append(f"- [ ] {item.get('description', '')}{owner}{due}")

        # Decisions
        if analysis.get("decisions"):
            parts.append("\n## Decisions Made\n")
            for decision in analysis["decisions"]:
                parts.append(f"- {decision}")

        # Open Questions
        if analysis.get("open_questions"):
            parts.append("\n## Open Questions\n")
            for question in analysis["open_questions"]:
                parts.append(f"- {question}")

        # Recommendations
        if analysis.get("recommendations"):
            parts.append("\n## Recommendations\n")
            for rec in analysis["recommendations"]:
                parts.append(f"- {rec}")

        return "\n".join(parts)

    async def _answer_query(self, context: AgentContext) -> AgentResponse:
        """Answer a question about transcripts or stakeholders."""
        messages = self._build_messages(context)

        response = self.anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=self.system_instruction,
            messages=messages
        )

        return AgentResponse(
            content=response.content[0].text,
            agent_name=self.name,
            agent_display_name=self.display_name
        )

    def should_handoff(self, context: AgentContext, response: str) -> Optional[tuple[str, str]]:
        """Check if we should hand off to another agent."""
        message_lower = context.user_message.lower()

        # Hand off to Fortuna for ROI/cost questions
        if any(word in message_lower for word in ["roi", "cost", "budget", "savings", "investment"]):
            return ("fortuna", "Query involves financial analysis")

        # Hand off to Guardian for security/compliance
        if any(word in message_lower for word in ["security", "compliance", "governance", "risk"]):
            return ("guardian", "Query involves security or governance")

        # Hand off to Counselor for legal
        if any(word in message_lower for word in ["legal", "contract", "liability", "ip"]):
            return ("counselor", "Query involves legal considerations")

        # Hand off to Atlas for research
        if any(word in message_lower for word in ["research", "study", "best practice", "industry"]):
            return ("atlas", "Query requires research")

        return None
