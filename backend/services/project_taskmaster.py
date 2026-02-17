"""Project Taskmaster Service.

Handles Taskmaster chat within project context.
Extracts tasks from conversation and creates them as task_candidates
linked to the project.
"""

import logging
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Optional

import anthropic

from supabase import Client

logger = logging.getLogger(__name__)


async def chat_with_taskmaster(
    project_id: str,
    message: str,
    client_id: str,
    user_id: str,
    supabase: Client,
) -> dict:
    """Chat with Taskmaster about a project.

    Taskmaster will:
    1. Respond to the user's message with task suggestions
    2. Extract concrete tasks from the conversation
    3. Create task_candidates linked to the project

    Args:
        project_id: The project being discussed
        message: User's message
        client_id: Client ID for scoping
        user_id: User ID for attribution
        supabase: Supabase client

    Returns:
        dict with response, tasks_created count, and task_titles
    """
    # Get project details for context
    project_result = (
        supabase.table("ai_projects")
        .select(
            "id, title, description, project_name, project_description, current_state, "
            "desired_state, next_step, department, status"
        )
        .eq("id", project_id)
        .eq("client_id", client_id)
        .single()
        .execute()
    )

    if not project_result.data:
        raise ValueError(f"Project {project_id} not found")

    project = project_result.data

    # Build context for Taskmaster
    context_parts = [
        f"Project: {project.get('project_name') or project['title']}",
    ]

    if project.get("project_description"):
        context_parts.append(f"Project Description: {project['project_description']}")
    elif project.get("description"):
        context_parts.append(f"Description: {project['description']}")

    if project.get("current_state"):
        context_parts.append(f"Current State: {project['current_state']}")

    if project.get("desired_state"):
        context_parts.append(f"Desired State: {project['desired_state']}")

    if project.get("next_step"):
        context_parts.append(f"Next Step Already Identified: {project['next_step']}")

    if project.get("department"):
        context_parts.append(f"Department: {project['department']}")

    project_context = "\n".join(context_parts)

    # Add KB document awareness via digests
    try:
        from services.document_digests import get_project_document_digests

        doc_digests = get_project_document_digests(project_id, supabase)
        docs_with_digests = [d for d in doc_digests if d.get("digest")][:20]
        if docs_with_digests:
            kb_lines = ["", "KNOWLEDGE BASE DOCUMENTS:"]
            for doc in docs_with_digests:
                kb_lines.append(f"- {doc['title']}: {doc['digest']}")
            project_context += "\n".join(kb_lines)
    except Exception as e:
        logger.warning(f"Failed to load document digests for Taskmaster: {e}")

    # Get user name for task assignment
    user_result = supabase.table("users").select("name, email").eq("id", user_id).single().execute()

    user_name = None
    if user_result.data:
        user_name = user_result.data.get("name") or user_result.data.get("email", "").split("@")[0]

    # Call Taskmaster via Anthropic
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not configured")

    client = anthropic.Anthropic(api_key=api_key)

    system_prompt = f"""You are Taskmaster, a personal accountability partner helping break down a project into tasks.

PROJECT CONTEXT:
{project_context}

YOUR ROLE:
1. Help the user break this project into concrete, actionable tasks
2. Suggest tasks with clear titles, priorities (1=Critical to 5=Lowest), and due date suggestions
3. When you suggest tasks, format them clearly so they can be extracted

TASK FORMAT (use this exact format when suggesting tasks):
[TASK] Title: <task title>
Priority: <1-5>
Due: <relative date like "this week", "next week", "in 2 weeks", or "no date">
Description: <brief description>
[/TASK]

GUIDELINES:
- Be conversational and helpful
- Ask clarifying questions if needed
- Suggest 3-5 tasks at a time, not overwhelming lists
- Consider dependencies between tasks
- Focus on immediate next actions, not the entire project
- Tasks assigned to: {user_name or "the user"}

After listing tasks, always ask if they want to proceed with creating these tasks or modify them."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        system=system_prompt,
        messages=[{"role": "user", "content": message}],
    )

    response_text = response.content[0].text

    # Extract tasks from response
    tasks_created = 0
    task_titles = []

    # Parse task blocks from response
    task_pattern = r"\[TASK\](.*?)\[/TASK\]"
    task_blocks = re.findall(task_pattern, response_text, re.DOTALL)

    # Get next position for pending tasks
    pos_result = (
        supabase.table("project_tasks")
        .select("position")
        .eq("client_id", client_id)
        .eq("status", "pending")
        .order("position", desc=True)
        .limit(1)
        .execute()
    )
    next_position = (pos_result.data[0]["position"] + 1) if pos_result.data else 0

    for block in task_blocks:
        task_data = _parse_task_block(block)
        if task_data:
            task_record = {
                "client_id": client_id,
                "title": task_data["title"],
                "description": task_data.get("description"),
                "status": "pending",
                "priority": task_data.get("priority", 3),
                "assignee_name": user_name,
                "team": project.get("department"),
                "linked_project_id": project_id,
                "source_project_id": project_id,
                "source_type": "ai_generated",
                "source_text": f"Generated by Taskmaster for {project.get('project_name') or project['title']}",
                "created_by": user_id,
                "updated_by": user_id,
                "position": next_position,
                "tags": [],
                "related_stakeholder_ids": [],
                "depends_on": [],
            }
            if task_data.get("due_date"):
                task_record["due_date"] = task_data["due_date"]

            try:
                supabase.table("project_tasks").insert(task_record).execute()
                tasks_created += 1
                task_titles.append(task_data["title"])
                next_position += 1
            except Exception as e:
                logger.warning(f"Failed to create project task: {e}")

    return {
        "response": response_text,
        "tasks_created": tasks_created,
        "task_titles": task_titles,
    }


def _parse_task_block(block: str) -> Optional[dict]:
    """Parse a task block into structured data."""
    lines = block.strip().split("\n")

    task_data = {}

    for line in lines:
        line = line.strip()
        if line.lower().startswith("title:"):
            task_data["title"] = line[6:].strip()
        elif line.lower().startswith("priority:"):
            try:
                priority = int(line[9:].strip())
                task_data["priority"] = max(1, min(5, priority))
            except ValueError:
                task_data["priority"] = 3
        elif line.lower().startswith("due:"):
            due_text = line[4:].strip()
            task_data["due_text"] = due_text
            task_data["due_date"] = _parse_relative_date(due_text)
        elif line.lower().startswith("description:"):
            task_data["description"] = line[12:].strip()

    # Must have at least a title
    if not task_data.get("title"):
        return None

    return task_data


def _parse_relative_date(text: str) -> Optional[str]:
    """Parse relative date text into ISO date string."""
    from datetime import timedelta

    today = datetime.now(timezone.utc).date()
    text_lower = text.lower()

    if "no date" in text_lower or "none" in text_lower:
        return None
    elif "today" in text_lower:
        return today.isoformat()
    elif "tomorrow" in text_lower:
        return (today + timedelta(days=1)).isoformat()
    elif "this week" in text_lower:
        # End of this week (Friday)
        days_until_friday = (4 - today.weekday()) % 7
        if days_until_friday == 0:
            days_until_friday = 7
        return (today + timedelta(days=days_until_friday)).isoformat()
    elif "next week" in text_lower:
        # End of next week
        days_until_friday = (4 - today.weekday()) % 7 + 7
        return (today + timedelta(days=days_until_friday)).isoformat()
    elif "2 weeks" in text_lower or "two weeks" in text_lower:
        return (today + timedelta(days=14)).isoformat()
    elif "month" in text_lower:
        return (today + timedelta(days=30)).isoformat()

    return None
