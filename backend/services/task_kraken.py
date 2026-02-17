"""Kraken Task Evaluation and Execution Service.

Handles two phases:
1. Evaluate: Assess all project tasks for AI workability, compute agenticity score
2. Execute: Run approved tasks non-destructively (output as comments + KB docs)
"""

import hashlib
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator

import anthropic

from supabase import Client

logger = logging.getLogger(__name__)

KRAKEN_MODEL = "claude-sonnet-4-20250514"
EVALUATION_MAX_TOKENS = 4096
EXECUTION_MAX_TOKENS = 4096

# Web search tool definition - gives Kraken real-time web access
WEB_SEARCH_TOOL = {
    "type": "web_search_20250305",
    "name": "web_search",
    "max_uses": 5,
}


def _extract_text_from_response(response) -> str:
    """Extract all text content from a response that may contain web search blocks.

    When web search is enabled, the response contains mixed content blocks:
    text, server_tool_use, web_search_tool_result, and text with citations.
    This function extracts and concatenates just the text parts.
    """
    parts = []
    for block in response.content:
        if hasattr(block, "type") and block.type == "text":
            parts.append(block.text)
    return "".join(parts)


def _compute_task_hash(tasks: list[dict]) -> str:
    """Compute MD5 hash of task IDs + updated_at for staleness detection."""
    parts = sorted(f"{t['id']}:{t.get('updated_at', '')}" for t in tasks)
    return hashlib.md5("|".join(parts).encode()).hexdigest()


def _load_system_instructions() -> str:
    """Load the Kraken agent system instructions from XML."""
    xml_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "system_instructions",
        "agents",
        "kraken.xml",
    )
    try:
        with open(xml_path) as f:
            return f.read()
    except FileNotFoundError:
        logger.warning("Kraken XML not found, using inline instructions")
        return ""


def _build_project_context(project: dict) -> str:
    """Build a context string from project data."""
    parts = [f"Project: {project.get('project_name') or project.get('title', 'Unknown')}"]

    if project.get("project_description"):
        parts.append(f"Description: {project['project_description']}")
    elif project.get("description"):
        parts.append(f"Description: {project['description']}")

    if project.get("current_state"):
        parts.append(f"Current State: {project['current_state']}")
    if project.get("desired_state"):
        parts.append(f"Desired State: {project['desired_state']}")
    if project.get("department"):
        parts.append(f"Department: {project['department']}")
    if project.get("status"):
        parts.append(f"Status: {project['status']}")
    if project.get("next_step"):
        parts.append(f"Next Step: {project['next_step']}")

    return "\n".join(parts)


def _build_task_list(tasks: list[dict]) -> str:
    """Build a formatted task list for the prompt."""
    lines = []
    for i, task in enumerate(tasks, 1):
        status = task.get("status", "pending")
        priority_label = {5: "Critical", 4: "High", 3: "Medium", 2: "Low", 1: "Lowest"}.get(
            task.get("priority", 3), "Medium"
        )
        lines.append(f"\n### Task {i}")
        lines.append(f"- **ID**: {task['id']}")
        lines.append(f"- **Title**: {task.get('title', 'Untitled')}")
        if task.get("description"):
            lines.append(f"- **Description**: {task['description']}")
        if task.get("notes"):
            lines.append(f"- **Notes**: {task['notes']}")
        lines.append(f"- **Status**: {status}")
        lines.append(f"- **Priority**: {priority_label}")
        if task.get("assignee_name"):
            lines.append(f"- **Assignee**: {task['assignee_name']}")
        if task.get("due_date"):
            lines.append(f"- **Due**: {task['due_date']}")

    return "\n".join(lines)


def _fetch_kb_context(project_id: str, supabase: Client, client_id: str) -> str:
    """Fetch linked KB documents and initiative docs for context.

    Uses direct document content (up to 25 project docs + 10 per initiative)
    with generous content previews to give Kraken rich context for evaluation.
    """
    context_parts = []

    # Fetch project-linked documents
    try:
        doc_result = (
            supabase.table("project_documents")
            .select("document_id, documents(id, title, content)")
            .eq("project_id", project_id)
            .limit(25)
            .execute()
        )

        if doc_result.data:
            for link in doc_result.data:
                doc = link.get("documents")
                if doc and doc.get("content"):
                    content_preview = doc["content"][:4000]
                    context_parts.append(f"## KB Document: {doc.get('title', 'Untitled')}\n{content_preview}")
    except Exception as e:
        logger.warning(f"Failed to fetch project documents: {e}")

    # Fetch initiative-linked documents if project has linked initiatives
    try:
        project_result = (
            supabase.table("project_initiative_links").select("initiative_id").eq("project_id", project_id).execute()
        )

        if project_result.data:
            initiative_ids = [r["initiative_id"] for r in project_result.data]
            for init_id in initiative_ids[:5]:
                init_docs = (
                    supabase.table("disco_initiative_documents")
                    .select("document_id, documents(id, title, content)")
                    .eq("initiative_id", init_id)
                    .limit(10)
                    .execute()
                )
                if init_docs.data:
                    for link in init_docs.data:
                        doc = link.get("documents")
                        if doc and doc.get("content"):
                            content_preview = doc["content"][:3000]
                            context_parts.append(
                                f"## Initiative Document: {doc.get('title', 'Untitled')}\n{content_preview}"
                            )
    except Exception as e:
        logger.warning(f"Failed to fetch initiative documents: {e}")

    if context_parts:
        return "\n\n---\n\n".join(context_parts)
    return ""


async def evaluate_project_tasks(
    project_id: str,
    client_id: str,
    user_id: str,
    supabase: Client,
) -> AsyncGenerator[dict, None]:
    """Phase 1: Evaluate all tasks in a project for agentic workability.

    Yields SSE events:
    - {"type": "status", "data": "message"}
    - {"type": "evaluation_complete", "data": {evaluations, summary, agenticity_score}}
    - {"type": "error", "data": "message"}
    """
    yield {"type": "status", "data": "Loading project tasks..."}

    # 1. Fetch project
    project_result = (
        supabase.table("ai_projects")
        .select(
            "id, title, description, project_name, project_description, "
            "current_state, desired_state, next_step, department, status"
        )
        .eq("id", project_id)
        .eq("client_id", client_id)
        .single()
        .execute()
    )

    if not project_result.data:
        yield {"type": "error", "data": "Project not found"}
        return

    project = project_result.data

    # 2. Fetch tasks
    tasks_result = (
        supabase.table("project_tasks")
        .select("id, title, description, notes, status, priority, assignee_name, due_date, updated_at")
        .eq("linked_project_id", project_id)
        .eq("client_id", client_id)
        .order("priority", desc=True)
        .execute()
    )

    tasks = tasks_result.data or []
    if not tasks:
        yield {"type": "error", "data": "No tasks found for this project"}
        return

    yield {"type": "status", "data": f"Evaluating {len(tasks)} tasks..."}

    # 3. Build context
    project_context = _build_project_context(project)
    task_list = _build_task_list(tasks)
    kb_context = _fetch_kb_context(project_id, supabase, client_id)

    # 4. Build evaluation prompt
    system_instructions = _load_system_instructions()

    evaluation_prompt = f"""Evaluate the following project tasks for AI workability.

PROJECT CONTEXT:
{project_context}

{f"KNOWLEDGE BASE CONTEXT:{chr(10)}{kb_context}" if kb_context else "No KB documents linked to this project."}

TASKS TO EVALUATE:
{task_list}

INSTRUCTIONS:
For each task, assess whether it can be completed by an AI agent (you) working with:
- The project context above
- The KB documents above
- Your general knowledge and reasoning abilities
- Text generation capabilities (drafting, analyzing, recommending)
- Web search for real-time research and data gathering

You CANNOT: access external systems (Jira, Salesforce, etc.), send emails, run code, or perform real-world actions.

Use the 5-dimension confidence framework:
1. Information Sufficiency (0-20): Is enough info available in context + KB + web search?
2. Output Clarity (0-20): Is the deliverable well-defined?
3. Execution Feasibility (0-20): Can this be done with text generation + web research?
4. Completeness Achievable (0-20): Can you produce a usable end result?
5. Domain Fit (0-20): Is this the type of work AI excels at?

Return your evaluation as a JSON block wrapped in <evaluation> tags:

<evaluation>
{{
  "evaluations": [
    {{
      "task_id": "uuid",
      "title": "Task title",
      "category": "automatable|assistable|manual",
      "confidence": 85,
      "reasoning": "Clear explanation of the assessment",
      "proposed_action": "Specifically what the agent would do",
      "estimated_quality": "high|medium|low"
    }}
  ],
  "summary": {{
    "total": 10,
    "automatable": 4,
    "assistable": 3,
    "manual": 3,
    "agenticity_score": 55.0
  }}
}}
</evaluation>
"""

    # 5. Call Claude
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        yield {"type": "error", "data": "ANTHROPIC_API_KEY not configured"}
        return

    client = anthropic.Anthropic(api_key=api_key)

    try:
        messages = [{"role": "user", "content": evaluation_prompt}]
        response = client.messages.create(
            model=KRAKEN_MODEL,
            max_tokens=EVALUATION_MAX_TOKENS,
            system=system_instructions if system_instructions else "You are Kraken, a task evaluation specialist.",
            tools=[WEB_SEARCH_TOOL],
            messages=messages,
        )

        # Handle pause_turn (web search may cause Claude to pause mid-turn)
        max_continuations = 5
        while response.stop_reason == "pause_turn" and max_continuations > 0:
            messages.append({"role": "assistant", "content": response.content})
            response = client.messages.create(
                model=KRAKEN_MODEL,
                max_tokens=EVALUATION_MAX_TOKENS,
                system=system_instructions if system_instructions else "You are Kraken, a task evaluation specialist.",
                tools=[WEB_SEARCH_TOOL],
                messages=messages,
            )
            max_continuations -= 1

        response_text = _extract_text_from_response(response)

        # 6. Parse evaluation
        import re

        eval_match = re.search(r"<evaluation>(.*?)</evaluation>", response_text, re.DOTALL)
        if not eval_match:
            yield {"type": "error", "data": "Failed to parse evaluation response"}
            return

        eval_json = json.loads(eval_match.group(1).strip())
        evaluations = eval_json.get("evaluations", [])
        summary = eval_json.get("summary", {})

        # Compute agenticity score
        total = len(evaluations)
        automatable = sum(1 for e in evaluations if e.get("category") == "automatable")
        assistable = sum(1 for e in evaluations if e.get("category") == "assistable")
        agenticity_score = round((automatable + 0.5 * assistable) / total * 100, 1) if total > 0 else 0

        summary["agenticity_score"] = agenticity_score
        summary["total"] = total
        summary["automatable"] = automatable
        summary["assistable"] = assistable
        summary["manual"] = total - automatable - assistable

        # 7. Compute task hash for staleness detection
        task_hash = _compute_task_hash(tasks)

        # 8. Store evaluation on project
        supabase.table("ai_projects").update(
            {
                "agenticity_score": agenticity_score,
                "agenticity_evaluated_at": datetime.now(timezone.utc).isoformat(),
                "agenticity_evaluation": eval_json,
                "agenticity_task_hash": task_hash,
            }
        ).eq("id", project_id).execute()

        yield {
            "type": "evaluation_complete",
            "data": {
                "evaluations": evaluations,
                "summary": summary,
                "agenticity_score": agenticity_score,
                "task_hash": task_hash,
            },
        }

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Kraken evaluation JSON: {e}")
        yield {"type": "error", "data": "Failed to parse evaluation results"}
    except Exception as e:
        logger.error(f"Kraken evaluation error: {e}")
        yield {"type": "error", "data": str(e)}


async def execute_approved_tasks(
    project_id: str,
    task_ids: list[str],
    client_id: str,
    user_id: str,
    supabase: Client,
) -> AsyncGenerator[dict, None]:
    """Phase 2: Execute approved tasks, adding output as comments + KB docs.

    Yields SSE events:
    - {"type": "status", "data": "message"}
    - {"type": "task_started", "data": {"task_id": ..., "title": ...}}
    - {"type": "task_complete", "data": {"task_id": ..., "comment_id": ..., "doc_id": ...}}
    - {"type": "all_complete", "data": {"tasks_completed": N, "docs_created": N}}
    - {"type": "error", "data": "message"}
    """
    yield {"type": "status", "data": "Loading project context..."}

    # 1. Fetch project
    project_result = (
        supabase.table("ai_projects")
        .select(
            "id, title, description, project_name, project_description, "
            "current_state, desired_state, next_step, department, status, project_code"
        )
        .eq("id", project_id)
        .eq("client_id", client_id)
        .single()
        .execute()
    )

    if not project_result.data:
        yield {"type": "error", "data": "Project not found"}
        return

    project = project_result.data
    project_context = _build_project_context(project)
    project_code = project.get("project_code", "UNK")

    # 2. Fetch approved tasks
    tasks_result = (
        supabase.table("project_tasks")
        .select("id, title, description, notes, status, priority, assignee_name, due_date")
        .in_("id", task_ids)
        .eq("client_id", client_id)
        .execute()
    )

    tasks = tasks_result.data or []
    if not tasks:
        yield {"type": "error", "data": "No approved tasks found"}
        return

    # 3. Fetch KB context
    kb_context = _fetch_kb_context(project_id, supabase, client_id)

    # 4. Load system instructions
    system_instructions = _load_system_instructions()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        yield {"type": "error", "data": "ANTHROPIC_API_KEY not configured"}
        return

    client = anthropic.Anthropic(api_key=api_key)

    tasks_completed = 0
    docs_created = 0

    for task in tasks:
        task_id = task["id"]
        task_title = task.get("title", "Untitled")

        yield {"type": "task_started", "data": {"task_id": task_id, "title": task_title}}
        yield {"type": "status", "data": f"Working on: {task_title}"}

        # Build task-specific execution prompt
        execution_prompt = f"""Execute the following task and produce substantive, actionable output.

PROJECT CONTEXT:
{project_context}

{f"KNOWLEDGE BASE CONTEXT:{chr(10)}{kb_context}" if kb_context else "No KB documents linked."}

TASK TO EXECUTE:
- **Title**: {task_title}
- **Description**: {task.get('description', 'No description provided')}
{f"- **Notes**: {task['notes']}" if task.get('notes') else ""}
- **Priority**: {task.get('priority', 3)}
- **Status**: {task.get('status', 'pending')}

INSTRUCTIONS:
1. Execute this task by producing real, substantive output - not a description of what you would do.
2. Use the project context and KB documents to ground your work.
3. Use web search to research current information when the task requires it.
4. Structure your output with clear headers and actionable content.
5. If any part requires human input or decision, mark it clearly with [USER INPUT NEEDED]: explanation.
6. End with a brief "Next Steps" section.
7. Do NOT use emojis.
8. Aim for completeness - produce a usable deliverable, not just an outline.
9. Cite sources when using web search results.
"""

        try:
            exec_messages = [{"role": "user", "content": execution_prompt}]
            response = client.messages.create(
                model=KRAKEN_MODEL,
                max_tokens=EXECUTION_MAX_TOKENS,
                system=system_instructions if system_instructions else "You are Kraken, executing a task.",
                tools=[WEB_SEARCH_TOOL],
                messages=exec_messages,
            )

            # Handle pause_turn for web search continuation
            max_continuations = 10
            while response.stop_reason == "pause_turn" and max_continuations > 0:
                exec_messages.append({"role": "assistant", "content": response.content})
                response = client.messages.create(
                    model=KRAKEN_MODEL,
                    max_tokens=EXECUTION_MAX_TOKENS,
                    system=system_instructions if system_instructions else "You are Kraken, executing a task.",
                    tools=[WEB_SEARCH_TOOL],
                    messages=exec_messages,
                )
                max_continuations -= 1

            output_text = _extract_text_from_response(response)
            word_count = len(output_text.split())

            # Add as task comment
            comment_content = output_text
            doc_id = None

            # For substantial outputs (>200 words), also create a KB document
            if word_count > 200:
                # Create KB document
                doc_id = str(uuid.uuid4())
                doc_title = f"Kraken: {task_title}"
                doc_tags = ["kraken", "auto-generated", project_code]

                try:
                    supabase.table("documents").insert(
                        {
                            "id": doc_id,
                            "client_id": client_id,
                            "filename": f"kraken-{task_id[:8]}.md",
                            "title": doc_title,
                            "content": output_text,
                            "file_type": "text/markdown",
                            "source": "kraken",
                            "processed": False,
                            "processing_status": "pending",
                            "tags": doc_tags,
                        }
                    ).execute()

                    # Link to project
                    supabase.table("project_documents").upsert(
                        {
                            "project_id": project_id,
                            "document_id": doc_id,
                            "linked_by": user_id,
                        },
                        on_conflict="project_id,document_id",
                    ).execute()

                    docs_created += 1

                    # Shorten comment to summary + reference
                    summary_lines = output_text.split("\n")[:10]
                    summary_text = "\n".join(summary_lines)
                    comment_content = f"{summary_text}\n\n---\n" f'Full output saved as KB document: "{doc_title}"'

                except Exception as e:
                    logger.warning(f"Failed to create KB doc for task {task_id}: {e}")
                    # Fall back to full comment
                    comment_content = output_text

            # Insert task comment
            comment_record = {
                "task_id": task_id,
                "user_id": user_id,
                "content": f"[Kraken Execution Output]\n\n{comment_content}",
            }

            comment_result = supabase.table("task_comments").insert(comment_record).execute()
            comment_id = comment_result.data[0]["id"] if comment_result.data else None

            tasks_completed += 1

            yield {
                "type": "task_complete",
                "data": {
                    "task_id": task_id,
                    "title": task_title,
                    "comment_id": comment_id,
                    "doc_id": doc_id,
                    "word_count": word_count,
                },
            }

        except Exception as e:
            logger.error(f"Kraken execution error for task {task_id}: {e}")
            yield {
                "type": "task_error",
                "data": {
                    "task_id": task_id,
                    "title": task_title,
                    "error": str(e),
                },
            }

    yield {
        "type": "all_complete",
        "data": {
            "tasks_completed": tasks_completed,
            "docs_created": docs_created,
        },
    }


async def get_evaluation(
    project_id: str,
    client_id: str,
    supabase: Client,
) -> dict | None:
    """Get stored evaluation results for a project."""
    result = (
        supabase.table("ai_projects")
        .select("agenticity_score, agenticity_evaluated_at, agenticity_evaluation, agenticity_task_hash")
        .eq("id", project_id)
        .eq("client_id", client_id)
        .single()
        .execute()
    )

    if not result.data:
        return None

    data = result.data
    if not data.get("agenticity_evaluation"):
        return None

    # Check staleness
    tasks_result = (
        supabase.table("project_tasks")
        .select("id, updated_at")
        .eq("linked_project_id", project_id)
        .eq("client_id", client_id)
        .execute()
    )

    tasks = tasks_result.data or []
    current_hash = _compute_task_hash(tasks) if tasks else ""
    is_stale = current_hash != data.get("agenticity_task_hash", "")

    return {
        "agenticity_score": data.get("agenticity_score"),
        "evaluated_at": data.get("agenticity_evaluated_at"),
        "evaluation": data.get("agenticity_evaluation"),
        "task_hash": data.get("agenticity_task_hash"),
        "is_stale": is_stale,
        "current_task_count": len(tasks),
    }
