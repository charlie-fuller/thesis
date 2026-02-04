"""DISCo Chat routes - Chat and Project Extraction."""

import json
import os

import anthropic
from fastapi import APIRouter, Depends, HTTPException

from database import get_supabase
from logger_config import get_logger
from services.disco import ask_question, get_conversation, get_initiative

from ._shared import ChatQuestion, require_disco_access, require_initiative_access

supabase = get_supabase()

logger = get_logger(__name__)
router = APIRouter()


# ============================================================================
# CHAT
# ============================================================================


@router.get("/initiatives/{initiative_id}/chat", deprecated=True)
async def api_get_chat(
    initiative_id: str,
    current_user: dict = Depends(require_disco_access),
):
    """Get or create chat conversation.

    DEPRECATED: Use the unified chat interface at /chat?initiative_id={initiative_id} instead.
    This endpoint will be removed in a future release.
    """
    logger.warning(
        f"Deprecated endpoint GET /initiatives/{initiative_id}/chat called. Use /chat?initiative_id={initiative_id} instead."
    )
    await require_initiative_access(initiative_id, current_user, "viewer")

    try:
        conversation = await get_conversation(initiative_id, current_user["id"])
        return {"success": True, "conversation": conversation}
    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/initiatives/{initiative_id}/chat", deprecated=True)
async def api_ask_question(
    initiative_id: str,
    data: ChatQuestion,
    current_user: dict = Depends(require_disco_access),
):
    """Ask a question about the initiative.

    DEPRECATED: Use the unified chat interface at /chat?initiative_id={initiative_id} instead.
    This endpoint will be removed in a future release.
    """
    logger.warning(
        f"Deprecated endpoint POST /initiatives/{initiative_id}/chat called. Use /chat?initiative_id={initiative_id} instead."
    )
    await require_initiative_access(initiative_id, current_user, "viewer")

    try:
        result = await ask_question(
            initiative_id=initiative_id,
            question=data.question,
            user_id=current_user["id"],
            conversation_id=data.conversation_id,
        )
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# PROJECT EXTRACTION FROM CHAT
# ============================================================================

PROJECT_EXTRACTION_PROMPT = """You are analyzing a conversation from a DISCo initiative chat to extract project information and related tasks.

CRITICAL: Extract ONLY the MOST RECENTLY discussed project idea.

The conversation is structured as:
- [CURRENT FOCUS] = The most recent messages where the user's CURRENT project is discussed. Extract from HERE.
- [BACKGROUND] = Earlier messages that may provide additional context. Use ONLY for context about the current project.

MULTI-PROJECT HANDLING:
- If multiple different projects were discussed, IGNORE earlier projects completely.
- Focus ONLY on the project being discussed in [CURRENT FOCUS] messages.
- Earlier messages about DIFFERENT projects should be treated as irrelevant.
- Use [BACKGROUND] only if it contains additional context about the SAME project in [CURRENT FOCUS].

For each project field, provide:
1. The extracted value (or null if not found)
2. A confidence level: "high" (explicitly stated), "medium" (implied/inferred), "low" (guessed from context), "none" (cannot determine)

Project fields to extract:
- title: A concise project name (max 100 chars)
- description: What this project aims to accomplish (2-3 sentences)
- department: Which department this relates to (finance, legal, hr, it, revops, marketing, sales, operations)
- current_state: The current situation/pain point
- desired_state: The target outcome/goal
- roi_potential: Score 1-5 (5=highest potential ROI)
- implementation_effort: Score 1-5 (5=easiest to implement)
- strategic_alignment: Score 1-5 (5=highest strategic value)
- stakeholder_readiness: Score 1-5 (5=most ready stakeholders)

TASKS: Also extract any tasks, action items, or next steps mentioned for this project.
- Look for phrases like "we need to", "next step is", "should do", "action item", "todo", etc.
- Each task needs: title (concise action), description (optional context), priority (low/medium/high)
- Extract up to 10 tasks maximum
- Only extract tasks related to the CURRENT project being extracted

Respond in this exact JSON format:
{
  "title": {"value": "string or null", "confidence": "high|medium|low|none"},
  "description": {"value": "string or null", "confidence": "high|medium|low|none"},
  "department": {"value": "string or null", "confidence": "high|medium|low|none"},
  "current_state": {"value": "string or null", "confidence": "high|medium|low|none"},
  "desired_state": {"value": "string or null", "confidence": "high|medium|low|none"},
  "roi_potential": {"value": "number 1-5 or null", "confidence": "high|medium|low|none"},
  "implementation_effort": {"value": "number 1-5 or null", "confidence": "high|medium|low|none"},
  "strategic_alignment": {"value": "number 1-5 or null", "confidence": "high|medium|low|none"},
  "stakeholder_readiness": {"value": "number 1-5 or null", "confidence": "high|medium|low|none"},
  "source_summary": "A brief 1-2 sentence summary of the CURRENT project being extracted (not earlier projects)",
  "tasks": [
    {"title": "Task title", "description": "Optional details", "priority": "low|medium|high"},
    ...
  ]
}

Return ONLY valid JSON, no markdown formatting."""


@router.post("/initiatives/{initiative_id}/extract-project")
async def api_extract_project_from_chat(
    initiative_id: str,
    current_user: dict = Depends(require_disco_access),
):
    """Extract project fields from initiative chat conversation using AI.

    Analyzes the full conversation with emphasis on recent messages.
    Returns extracted fields with confidence levels.
    Skips projects that have already been created from this initiative.
    """
    await require_initiative_access(initiative_id, current_user, "viewer")

    try:
        # Get initiative name for context
        initiative = await get_initiative(initiative_id, current_user["id"])
        initiative_name = (
            initiative.get("name", "Unknown Initiative") if initiative else "Unknown Initiative"
        )

        # Check for existing projects linked to this initiative
        existing_projects = []
        try:
            # Query projects that have this initiative in their initiative_ids array
            # or have source_id matching this initiative
            result = (
                supabase.table("projects")
                .select("id, title, project_code")
                .or_(f"source_id.eq.{initiative_id},initiative_ids.cs.{{{initiative_id}}}")
                .execute()
            )
            existing_projects = result.data or []
        except Exception as e:
            logger.warning(f"Failed to check existing projects: {e}")

        # Get conversation
        conversation = await get_conversation(initiative_id, current_user["id"])

        if not conversation or not conversation.get("messages"):
            return {
                "success": False,
                "error": "No conversation found. Start a chat first to discuss the project.",
            }

        messages = conversation.get("messages", [])
        if not messages:
            return {
                "success": False,
                "error": "No messages in conversation. Discuss your project idea first.",
            }

        # Format conversation for analysis
        # Use last 8 messages as "current focus"
        current_focus_start = max(0, len(messages) - 8)

        background_messages = []
        current_focus_messages = []

        for i, msg in enumerate(messages):
            role = "User" if msg.get("role") == "user" else "Assistant"
            content = msg.get("content", "")
            if i < current_focus_start:
                background_messages.append(f"{role}: {content}")
            else:
                current_focus_messages.append(f"{role}: {content}")

        # Build conversation text with clear sections
        conversation_parts = []
        if background_messages:
            conversation_parts.append("[BACKGROUND - Earlier discussion, use only for context]")
            conversation_parts.extend(background_messages)
            conversation_parts.append("")
        conversation_parts.append("[CURRENT FOCUS - Extract project from here]")
        conversation_parts.extend(current_focus_messages)

        conversation_text = "\n\n".join(conversation_parts)

        # Build the prompt
        existing_projects_note = ""
        if existing_projects:
            project_list = ", ".join(
                [f'"{p.get("title", p.get("project_code", "Unknown"))}"' for p in existing_projects]
            )
            existing_projects_note = f"""

IMPORTANT: The following project(s) have ALREADY been created from this conversation:
{project_list}

You MUST find a DIFFERENT project idea discussed in this conversation. If no other project ideas exist besides the ones already created, respond with all fields having null values and confidence "none", and set source_summary to "No additional project ideas found - all discussed projects have been created."
"""

        full_prompt = f"""Initiative: {initiative_name}
{existing_projects_note}
Conversation:
{conversation_text}

Now extract project information from this conversation."""

        # Call Claude
        anthropic_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        response = anthropic_client.messages.create(
            model=os.environ.get("DISCO_EXTRACTION_MODEL", "claude-sonnet-4-20250514"),
            max_tokens=1500,
            system=PROJECT_EXTRACTION_PROMPT,
            messages=[{"role": "user", "content": full_prompt}],
        )

        # Parse response
        response_text = response.content[0].text.strip()
        # Remove any markdown formatting if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        response_text = response_text.strip()

        try:
            extracted = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse extraction response: {e}")
            logger.error(f"Response was: {response_text[:500]}")
            raise HTTPException(
                status_code=500, detail="Failed to parse AI extraction response"
            ) from e

        # Check if no additional projects were found (all key fields are null)
        title_value = extracted.get("title", {}).get("value")
        description_value = extracted.get("description", {}).get("value")
        if not title_value and not description_value:
            # No additional project ideas found
            existing_count = len(existing_projects)
            if existing_count > 0:
                project_names = ", ".join(
                    [p.get("title", p.get("project_code", "Unknown")) for p in existing_projects]
                )
                return {
                    "success": False,
                    "error": f"All project ideas in this conversation have already been created. Existing project(s): {project_names}",
                    "existing_projects": existing_projects,
                }
            else:
                return {
                    "success": False,
                    "error": "No project ideas found in this conversation. Discuss a project idea first.",
                }

        # Build source context
        recent_summary = extracted.get("source_summary", "")
        source_context = f"Created from DISCo initiative '{initiative_name}' chat. {recent_summary}"

        # Format response
        return {
            "success": True,
            "extracted": {
                "title": {
                    "value": extracted.get("title", {}).get("value"),
                    "confidence": extracted.get("title", {}).get("confidence", "none"),
                },
                "description": {
                    "value": extracted.get("description", {}).get("value"),
                    "confidence": extracted.get("description", {}).get("confidence", "none"),
                },
                "department": {
                    "value": extracted.get("department", {}).get("value"),
                    "confidence": extracted.get("department", {}).get("confidence", "none"),
                },
                "current_state": {
                    "value": extracted.get("current_state", {}).get("value"),
                    "confidence": extracted.get("current_state", {}).get("confidence", "none"),
                },
                "desired_state": {
                    "value": extracted.get("desired_state", {}).get("value"),
                    "confidence": extracted.get("desired_state", {}).get("confidence", "none"),
                },
                "roi_potential": {
                    "value": extracted.get("roi_potential", {}).get("value"),
                    "confidence": extracted.get("roi_potential", {}).get("confidence", "none"),
                },
                "implementation_effort": {
                    "value": extracted.get("implementation_effort", {}).get("value"),
                    "confidence": extracted.get("implementation_effort", {}).get(
                        "confidence", "none"
                    ),
                },
                "strategic_alignment": {
                    "value": extracted.get("strategic_alignment", {}).get("value"),
                    "confidence": extracted.get("strategic_alignment", {}).get(
                        "confidence", "none"
                    ),
                },
                "stakeholder_readiness": {
                    "value": extracted.get("stakeholder_readiness", {}).get("value"),
                    "confidence": extracted.get("stakeholder_readiness", {}).get(
                        "confidence", "none"
                    ),
                },
            },
            "tasks": extracted.get("tasks", []),
            "source_context": source_context,
            "initiative_id": initiative_id,
            "initiative_name": initiative_name,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting project from chat: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e
