"""Transcript API Routes.

Endpoints for uploading and analyzing meeting transcripts.
"""

import logging
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

import pb_client as pb
from repositories.meetings import (
    list_meeting_transcripts,
    get_meeting_transcript,
    create_meeting_transcript,
    delete_meeting_transcript as repo_delete_meeting_transcript,
)
from repositories.stakeholders import list_stakeholder_insights

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/transcripts", tags=["transcripts"])


class TranscriptAnalysisRequest(BaseModel):
    """Request to analyze a transcript."""

    content: str
    title: Optional[str] = None
    meeting_date: Optional[str] = None


class TranscriptResponse(BaseModel):
    """Response from transcript analysis."""

    id: str
    title: str
    meeting_date: Optional[str]
    summary: Optional[str]
    attendees: list
    sentiment_summary: dict
    action_items: list
    processing_status: str
    created_at: str


class StakeholderInsight(BaseModel):
    """A stakeholder insight extracted from a transcript."""

    id: str
    stakeholder_name: str
    insight_type: str
    content: str
    quote: Optional[str]
    confidence: float
    is_resolved: bool


@router.post("/analyze", response_model=TranscriptResponse)
async def analyze_transcript(
    request: TranscriptAnalysisRequest,
):
    """Analyze a meeting transcript and extract insights.

    The transcript can be in various formats:
    - Granola format (Speaker: text)
    - Otter.ai format
    - Plain text with speaker labels
    """
    import os

    import anthropic

    from agents import AgentContext, OracleAgent

    try:
        # Initialize Oracle agent
        anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        # NOTE: services will be rewritten later; passing None for supabase
        oracle = OracleAgent(supabase=None, anthropic_client=anthropic_client)
        await oracle.initialize()

        # Create context for the agent
        context = AgentContext(
            user_id="system",
            client_id="system",
            conversation_id="transcript-analysis",  # Special ID for direct analysis
            message_history=[],
            user_message=request.content,
        )

        # Process the transcript
        await oracle.process(context)

        # Get the stored transcript from the database (most recent)
        transcripts = list_meeting_transcripts(sort="-created")
        if not transcripts:
            raise HTTPException(status_code=500, detail="Failed to store transcript analysis")

        transcript = transcripts[0]

        return TranscriptResponse(
            id=transcript["id"],
            title=transcript["title"] or "Untitled Meeting",
            meeting_date=transcript.get("meeting_date"),
            summary=transcript.get("summary"),
            attendees=transcript.get("attendees", []),
            sentiment_summary=transcript.get("sentiment_summary", {}),
            action_items=transcript.get("action_items", []),
            processing_status=transcript.get("processing_status", "completed"),
            created_at=transcript["created"],
        )

    except Exception as e:
        logger.error(f"Transcript analysis failed: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/upload")
async def upload_transcript(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    meeting_date: Optional[str] = Form(None),
):
    """Upload a transcript file for analysis.

    Supports .txt and .md files.
    """
    # Validate file type
    if not file.filename.endswith((".txt", ".md", ".markdown")):
        raise HTTPException(status_code=400, detail="Only .txt and .md files are supported")

    # Read file content
    content = await file.read()
    try:
        text_content = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded text") from None

    # Analyze the transcript
    request = TranscriptAnalysisRequest(content=text_content, title=title or file.filename, meeting_date=meeting_date)

    return await analyze_transcript(request)


class TranscriptsListResponse(BaseModel):
    """Response for list transcripts endpoint."""

    transcripts: list[TranscriptResponse]
    total: int


@router.get("/", response_model=TranscriptsListResponse)
async def list_transcripts_endpoint(
    limit: int = 20,
    offset: int = 0,
):
    """List all transcripts."""
    # Get count
    total = pb.count("meeting_transcripts")

    # Get paginated results
    page = (offset // limit) + 1 if limit else 1
    result = pb.list_records(
        "meeting_transcripts",
        sort="-created",
        page=page,
        per_page=limit,
    )
    items = result.get("items", [])

    transcripts = [
        TranscriptResponse(
            id=t["id"],
            title=t["title"] or "Untitled Meeting",
            meeting_date=t.get("meeting_date"),
            summary=t.get("summary"),
            attendees=t.get("attendees", []),
            sentiment_summary=t.get("sentiment_summary", {}),
            action_items=t.get("action_items", []),
            processing_status=t.get("processing_status", "completed"),
            created_at=t["created"],
        )
        for t in items
    ]

    return TranscriptsListResponse(transcripts=transcripts, total=total)


@router.get("/{transcript_id}", response_model=TranscriptResponse)
async def get_transcript_endpoint(
    transcript_id: str,
):
    """Get a specific transcript by ID."""
    t = get_meeting_transcript(transcript_id)

    if not t:
        raise HTTPException(status_code=404, detail="Transcript not found")

    return TranscriptResponse(
        id=t["id"],
        title=t["title"] or "Untitled Meeting",
        meeting_date=t.get("meeting_date"),
        summary=t.get("summary"),
        attendees=t.get("attendees", []),
        sentiment_summary=t.get("sentiment_summary", {}),
        action_items=t.get("action_items", []),
        processing_status=t.get("processing_status", "completed"),
        created_at=t["created"],
    )


@router.get("/{transcript_id}/insights", response_model=list[StakeholderInsight])
async def get_transcript_insights(
    transcript_id: str,
):
    """Get stakeholder insights extracted from a transcript."""
    # Verify transcript exists
    transcript = get_meeting_transcript(transcript_id)
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")

    # Get insights for this transcript (without join -- separate lookup for stakeholder name)
    insights = pb.get_all(
        "stakeholder_insights",
        filter=f"meeting_transcript_id='{pb.escape_filter(transcript_id)}'",
    )

    result = []
    for i in insights:
        # Look up stakeholder name
        stakeholder_name = "Unknown"
        if i.get("stakeholder_id"):
            stakeholder = pb.get_record("stakeholders", i["stakeholder_id"])
            if stakeholder:
                stakeholder_name = stakeholder.get("name", "Unknown")

        result.append(
            StakeholderInsight(
                id=i["id"],
                stakeholder_name=stakeholder_name,
                insight_type=i["insight_type"],
                content=i["content"],
                quote=i.get("extracted_quote"),
                confidence=i.get("confidence", 0.8),
                is_resolved=i.get("is_resolved", False),
            )
        )

    return result


@router.delete("/{transcript_id}")
async def delete_transcript(
    transcript_id: str,
):
    """Delete a transcript."""
    transcript = get_meeting_transcript(transcript_id)
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")

    repo_delete_meeting_transcript(transcript_id)

    return {"message": "Transcript deleted successfully"}
