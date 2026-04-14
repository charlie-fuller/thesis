"""Project Taskmaster Service.

Handles Taskmaster chat within project context.
Extracts tasks from conversation and creates them linked to the project.

All tasks must be grounded in project documentation, agent outputs, or
explicit user statements -- never generated from general assumptions.
"""

import logging
import os
import re
from datetime import datetime, timezone
from typing import Optional

import anthropic

import pb_client as pb
from repositories import projects as projects_repo, tasks as tasks_repo

logger = logging.getLogger(__name__)


async def chat_with_taskmaster(
    project_id: str,
    message: str,
    client_id: str,
    user_id: str,
) -> dict:
    """Chat with Taskmaster about a project.

    Taskmaster will:
    1. Gather all available evidence (docs, agent outputs, project metadata)
    2. Derive tasks grounded in that evidence
    3. Create sequenced tasks with dependencies linked to the project

    Args:
        project_id: The project being discussed
        message: User's message
        client_id: Client ID for scoping
        user_id: User ID for attribution
        supabase: Supabase client

    Returns:
        dict with response, tasks_created count, and task_titles
    """
    # Get project details including metadata
    project = projects_repo.get_project(project_id)
    if not project:
        raise ValueError(f"Project {project_id} not found")

    # Build project context
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

    if project.get("blockers"):
        context_parts.append(f"Blockers: {', '.join(project['blockers'])}")

    # Include metadata context (stakeholders, artifacts, scope)
    metadata = project.get("metadata") or {}
    if metadata.get("stakeholders"):
        stakeholder_lines = []
        for name, info in metadata["stakeholders"].items():
            stakeholder_lines.append(f"  - {name}: {info.get('role', '')} - {info.get('title', '')} ({info.get('notes', '')})")
        context_parts.append(f"Stakeholders:\n" + "\n".join(stakeholder_lines))

    if metadata.get("artifacts"):
        artifact_lines = []
        for name, info in metadata["artifacts"].items():
            status = info.get("status", "unknown")
            notes = info.get("notes", "")
            artifact_lines.append(f"  - {name}: {status}" + (f" ({notes})" if notes else ""))
        context_parts.append(f"Artifacts:\n" + "\n".join(artifact_lines))

    if metadata.get("agent_scope"):
        scope = metadata["agent_scope"]
        if scope.get("in_scope"):
            context_parts.append(f"In Scope: {', '.join(scope['in_scope'])}")
        if scope.get("out_of_scope"):
            context_parts.append(f"Out of Scope: {', '.join(scope['out_of_scope'])}")

    project_context = "\n".join(context_parts)

    # --- EVIDENCE LAYER 1: Previous agent outputs (Discovery Guide, etc.) ---
    agent_output_context = ""
    try:
        esc_pid = pb.escape_filter(project_id)
        outputs = pb.get_all(
            "disco_outputs",
            filter=f"project_id='{esc_pid}'",
            sort="-created",
        )
        if outputs:
            seen_types = set()
            output_parts = ["AGENT ANALYSIS OUTPUTS (use these as primary task sources):"]
            for output in outputs:
                if output["agent_type"] not in seen_types:
                    seen_types.add(output["agent_type"])
                    output_parts.append(f"\n=== {output['agent_type']} (v{output['version']}) ===")
                    if output.get("recommendation"):
                        output_parts.append(f"Recommendation: {output['recommendation']}")
                    if output.get("confidence_level"):
                        output_parts.append(f"Confidence: {output['confidence_level']}")
                    # Include full content but cap at 6000 chars per output
                    content = output.get("content_markdown", "")
                    if len(content) > 6000:
                        content = content[:6000] + "\n... (truncated)"
                    output_parts.append(content)
            agent_output_context = "\n".join(output_parts)
            logger.info(f"Taskmaster: loaded {len(seen_types)} agent outputs as evidence")
    except Exception as e:
        logger.warning(f"Failed to load agent outputs for Taskmaster: {e}")

    # --- EVIDENCE LAYER 2: Document content via RAG ---
    # Use project description + next_step as the search query, not the user message
    rag_context = ""
    try:
        from document_processor import search_similar_chunks

        project_docs = projects_repo.get_project_documents(project_id)
        project_doc_ids = [row["document_id"] for row in project_docs]

        if project_doc_ids:
            # Build a meaningful search query from project context
            search_query = " ".join(filter(None, [
                project.get("description", ""),
                project.get("next_step", ""),
                project.get("desired_state", ""),
                message,
            ]))[:500]

            chunks = search_similar_chunks(
                search_query,
                client_id,
                limit=12,
                min_similarity=0.0,
                document_ids=project_doc_ids,
            )
            if chunks:
                rag_lines = ["RELEVANT DOCUMENT CONTENT:"]
                for chunk in chunks:
                    source = chunk.get("source", chunk.get("filename", "Unknown"))
                    content = chunk.get("content", "")
                    rag_lines.append(f"\n--- From: {source} ---\n{content}")
                rag_context = "\n".join(rag_lines)
                logger.info(
                    f"Taskmaster RAG: found {len(chunks)} relevant chunks from "
                    f"{len(project_doc_ids)} project documents"
                )
    except Exception as e:
        logger.warning(f"Failed to perform RAG search for Taskmaster: {e}")

    # --- EVIDENCE LAYER 3: Document digests as fallback overview ---
    digest_context = ""
    try:
        from services.document_digests import get_project_document_digests

        doc_digests = get_project_document_digests(project_id, supabase)
        docs_with_digests = [d for d in doc_digests if d.get("digest")][:20]
        if docs_with_digests:
            kb_lines = ["DOCUMENT SUMMARIES:"]
            for doc in docs_with_digests:
                kb_lines.append(f"- {doc['title']}: {doc['digest']}")
            digest_context = "\n".join(kb_lines)
    except Exception as e:
        logger.warning(f"Failed to load document digests for Taskmaster: {e}")

    # --- EXISTING TASKS: prevent duplication ---
    existing_tasks_context = ""
    try:
        existing_tasks = tasks_repo.list_tasks(source_project_id=project_id, sort="sequence_number")
        if existing_tasks:
            task_lines = ["EXISTING TASKS (do not duplicate these):"]
            for t in existing_tasks:
                seq = f"#{t['sequence_number']}" if t.get("sequence_number") else ""
                task_lines.append(f"  - [{t['status']}] {seq} {t['title']}")
            existing_tasks_context = "\n".join(task_lines)
    except Exception as e:
        logger.warning(f"Failed to load existing tasks for Taskmaster: {e}")

    # Get user name for task assignment
    user_name = None
    try:
        user_record = pb.get_record("users", user_id)
        if user_record:
            user_name = user_record.get("name") or user_record.get("email", "").split("@")[0]
    except Exception:
        pass

    # Call Taskmaster via Anthropic
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not configured")

    client = anthropic.Anthropic(api_key=api_key)

    system_prompt = f"""You are Taskmaster, a project accountability partner that creates tasks grounded in evidence.

PROJECT CONTEXT:
{project_context}

{agent_output_context}

{rag_context}

{digest_context}

{existing_tasks_context}

CRITICAL RULES:
1. Every task you suggest MUST be derived from a specific source: an agent output finding, a document reference, a project field (next_step, blockers, desired_state), or something the user explicitly stated.
2. For each task, include a "Source:" line citing where the task comes from (e.g. "Source: Discovery Guide recommendation", "Source: project next_step field", "Source: Emily transcript - booking policy review").
3. Do NOT invent tasks from general assumptions about what a project "probably" needs. If the evidence doesn't support a task, don't suggest it.
4. Do NOT duplicate existing tasks listed above. Build on what exists.
5. Sequence tasks in logical execution order with dependencies.

TASK FORMAT (use this exact format):
[TASK] Title: <task title>
Sequence: <integer starting at 1, indicating execution order>
Priority: <1-5>
Due: <relative date like "this week", "next week", "in 2 weeks", or "no date">
Depends On: <comma-separated list of sequence numbers this task depends on, or "none">
Source: <specific document, agent output, or project field this task is derived from>
Description: <brief description grounded in the source>
[/TASK]

GUIDELINES:
- Be conversational but evidence-driven
- Suggest 3-7 tasks at a time
- ALWAYS sequence tasks and set dependencies
- Tasks assigned to: {user_name or "the user"}

After listing tasks, ask if they want to proceed with creating these tasks or modify them."""

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
    pos_result = pb.list_records(
        "project_tasks",
        filter="status='pending'",
        sort="-position",
        per_page=1,
    )
    pos_items = pos_result.get("items", [])
    next_position = (pos_items[0]["position"] + 1) if pos_items else 0

    # First pass: parse all tasks
    parsed_tasks = []
    for block in task_blocks:
        task_data = _parse_task_block(block)
        if task_data:
            parsed_tasks.append(task_data)

    # Get the highest existing sequence_number for this project
    seq_result = pb.list_records(
        "project_tasks",
        filter=f"linked_project_id='{esc_pid}' && sequence_number!=null",
        sort="-sequence_number",
        per_page=1,
    )
    seq_items = seq_result.get("items", [])
    seq_offset = (seq_items[0]["sequence_number"] if seq_items else 0)

    # Second pass: insert tasks, building a sequence-number-to-UUID map for dependencies
    seq_to_uuid = {}
    for task_data in parsed_tasks:
        seq_num = task_data.get("sequence", len(seq_to_uuid) + 1) + seq_offset

        # Resolve depends_on sequence numbers to UUIDs
        depends_on_uuids = []
        for dep_seq in task_data.get("depends_on_seqs", []):
            dep_uuid = seq_to_uuid.get(dep_seq + seq_offset)
            if dep_uuid:
                depends_on_uuids.append(dep_uuid)

        # Build description with source attribution
        description = task_data.get("description", "")
        source = task_data.get("source", "")
        if source and description:
            description = f"{description}\n\nSource: {source}"
        elif source:
            description = f"Source: {source}"

        task_record = {
            "title": task_data["title"],
            "description": description,
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
            "sequence_number": seq_num,
            "tags": [],
            "related_stakeholder_ids": [],
            "depends_on": depends_on_uuids,
        }
        if task_data.get("due_date"):
            task_record["due_date"] = task_data["due_date"]

        try:
            created = tasks_repo.create_task(task_record)
            if created:
                created_id = created["id"]
                seq_to_uuid[seq_num] = created_id
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
        elif line.lower().startswith("sequence:"):
            try:
                task_data["sequence"] = int(line[9:].strip())
            except ValueError:
                pass
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
        elif line.lower().startswith("depends on:"):
            dep_text = line[11:].strip().lower()
            if dep_text and dep_text != "none":
                dep_seqs = []
                for part in dep_text.split(","):
                    part = part.strip()
                    try:
                        dep_seqs.append(int(part))
                    except ValueError:
                        pass
                task_data["depends_on_seqs"] = dep_seqs
        elif line.lower().startswith("source:"):
            task_data["source"] = line[7:].strip()
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
