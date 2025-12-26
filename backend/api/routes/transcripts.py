"""
Transcript API Routes

Endpoints for uploading and analyzing meeting transcripts.
"""

import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from auth import get_current_user
from database import get_supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transcripts", tags=["transcripts"])


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
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """
    Analyze a meeting transcript and extract insights.

    The transcript can be in various formats:
    - Granola format (Speaker: text)
    - Otter.ai format
    - Plain text with speaker labels
    """
    import anthropic
    import os
    from agents import OracleAgent, AgentContext

    try:
        # Initialize Oracle agent
        anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        oracle = OracleAgent(supabase=supabase, anthropic_client=anthropic_client)
        await oracle.initialize()

        # Create context for the agent
        context = AgentContext(
            user_id=current_user["id"],
            client_id=current_user["client_id"],
            conversation_id="transcript-analysis",  # Special ID for direct analysis
            message_history=[],
            user_message=request.content
        )

        # Process the transcript
        response = await oracle.process(context)

        # Get the stored transcript from the database
        result = supabase.table("meeting_transcripts") \
            .select("*") \
            .eq("user_id", current_user["id"]) \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to store transcript analysis")

        transcript = result.data[0]

        return TranscriptResponse(
            id=transcript["id"],
            title=transcript["title"] or "Untitled Meeting",
            meeting_date=transcript.get("meeting_date"),
            summary=transcript.get("summary"),
            attendees=transcript.get("attendees", []),
            sentiment_summary=transcript.get("sentiment_summary", {}),
            action_items=transcript.get("action_items", []),
            processing_status=transcript.get("processing_status", "completed"),
            created_at=transcript["created_at"]
        )

    except Exception as e:
        logger.error(f"Transcript analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_transcript(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    meeting_date: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """
    Upload a transcript file for analysis.

    Supports .txt and .md files.
    """
    # Validate file type
    if not file.filename.endswith(('.txt', '.md', '.markdown')):
        raise HTTPException(
            status_code=400,
            detail="Only .txt and .md files are supported"
        )

    # Read file content
    content = await file.read()
    try:
        text_content = content.decode('utf-8')
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="File must be UTF-8 encoded text"
        )

    # Analyze the transcript
    request = TranscriptAnalysisRequest(
        content=text_content,
        title=title or file.filename,
        meeting_date=meeting_date
    )

    return await analyze_transcript(request, current_user, supabase)


@router.get("/", response_model=list[TranscriptResponse])
async def list_transcripts(
    limit: int = 20,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List all transcripts for the current user."""
    result = supabase.table("meeting_transcripts") \
        .select("*") \
        .eq("user_id", current_user["id"]) \
        .order("created_at", desc=True) \
        .range(offset, offset + limit - 1) \
        .execute()

    return [
        TranscriptResponse(
            id=t["id"],
            title=t["title"] or "Untitled Meeting",
            meeting_date=t.get("meeting_date"),
            summary=t.get("summary"),
            attendees=t.get("attendees", []),
            sentiment_summary=t.get("sentiment_summary", {}),
            action_items=t.get("action_items", []),
            processing_status=t.get("processing_status", "completed"),
            created_at=t["created_at"]
        )
        for t in result.data
    ]


@router.get("/{transcript_id}", response_model=TranscriptResponse)
async def get_transcript(
    transcript_id: str,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get a specific transcript by ID."""
    result = supabase.table("meeting_transcripts") \
        .select("*") \
        .eq("id", transcript_id) \
        .eq("user_id", current_user["id"]) \
        .single() \
        .execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Transcript not found")

    t = result.data
    return TranscriptResponse(
        id=t["id"],
        title=t["title"] or "Untitled Meeting",
        meeting_date=t.get("meeting_date"),
        summary=t.get("summary"),
        attendees=t.get("attendees", []),
        sentiment_summary=t.get("sentiment_summary", {}),
        action_items=t.get("action_items", []),
        processing_status=t.get("processing_status", "completed"),
        created_at=t["created_at"]
    )


@router.get("/{transcript_id}/insights", response_model=list[StakeholderInsight])
async def get_transcript_insights(
    transcript_id: str,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get stakeholder insights extracted from a transcript."""
    # Verify transcript belongs to user
    transcript = supabase.table("meeting_transcripts") \
        .select("id") \
        .eq("id", transcript_id) \
        .eq("user_id", current_user["id"]) \
        .single() \
        .execute()

    if not transcript.data:
        raise HTTPException(status_code=404, detail="Transcript not found")

    # Get insights with stakeholder names
    result = supabase.table("stakeholder_insights") \
        .select("*, stakeholders(name)") \
        .eq("meeting_transcript_id", transcript_id) \
        .execute()

    return [
        StakeholderInsight(
            id=i["id"],
            stakeholder_name=i["stakeholders"]["name"] if i.get("stakeholders") else "Unknown",
            insight_type=i["insight_type"],
            content=i["content"],
            quote=i.get("extracted_quote"),
            confidence=i.get("confidence", 0.8),
            is_resolved=i.get("is_resolved", False)
        )
        for i in result.data
    ]


@router.delete("/{transcript_id}")
async def delete_transcript(
    transcript_id: str,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Delete a transcript."""
    # Verify transcript belongs to user
    result = supabase.table("meeting_transcripts") \
        .delete() \
        .eq("id", transcript_id) \
        .eq("user_id", current_user["id"]) \
        .execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Transcript not found")

    return {"message": "Transcript deleted successfully"}
