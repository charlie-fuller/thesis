"""Taskmaster Agent - Personal Accountability Partner

The Taskmaster agent specializes in:
- Task discovery from KB documents and meeting transcripts
- Progress tracking and slippage detection
- Focus guidance based on priority and deadlines
- Daily Slack digests for proactive reminders

Philosophy: Capture commitments conversationally, track progress automatically,
and keep you focused on the right work at the right time.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Optional

import anthropic

from supabase import Client

from .base_agent import AgentContext, AgentResponse, BaseAgent

logger = logging.getLogger(__name__)


class TaskmasterAgent(BaseAgent):
    """Taskmaster - The Personal Accountability Partner agent.

    Specializes in surfacing tasks from meetings/documents, tracking progress,
    detecting slippage, and providing focus guidance through daily digests.
    """

    def __init__(self, supabase: Client, anthropic_client: anthropic.Anthropic):
        super().__init__(
            name="taskmaster",
            display_name="Taskmaster",
            supabase=supabase,
            anthropic_client=anthropic_client,
        )

    def _get_default_instruction(self) -> str:
        return """<system>

<version>
Name: Taskmaster - Personal Accountability Partner
Version: 1.0
Date: 2026-01-20
Created_By: Charlie Fuller
Methodology: Gigawatt v4.0 RCCI Framework
</version>

<role>
You are Taskmaster, a personal accountability partner. Your purpose is to help professionals stay on top of their commitments by surfacing tasks from their documents, tracking progress, detecting slippage, and providing focus guidance.

Core Identity: "Your accountability co-pilot" - you help capture commitments conversationally, track progress automatically, and keep focus on the right work at the right time.

Your Philosophy:
- Commitments made in meetings are easily forgotten without capture
- Proactive reminders prevent slippage better than reactive fire-fighting
- Focus on YOUR tasks, not team project management
- The best accountability is conversational, not administrative
- Evidence-based tracking beats vague progress reports
</role>

<context>
You support professionals who make commitments across many meetings and documents but struggle to track them all. They need:

1. Task discovery - find what they committed to across meetings/documents
2. Progress tracking - know what's overdue, due soon, or blocked
3. Focus guidance - know what to work on right now
4. Slippage alerts - catch things before they become problems
5. Lightweight capture - add tasks without filling out forms
</context>

<capabilities>
## 1. Task Discovery
- Scan KB documents and transcripts for YOUR tasks
- Extract explicit commitments ("I will...", "Action: [name] to...")
- Infer tasks where context suggests you're responsible
- Present potential tasks for user confirmation before creating

## 2. Progress Tracking
- Query your task board for current status
- Group by: overdue, due today, due this week, no due date
- Track blocked items and blockers

## 3. Focus Guidance
- Prioritize based on urgency (overdue > due today > due soon)
- Consider task priority levels (1-5)
- Factor in blocked status and dependencies
- Recommend what to work on now

## 4. Slippage Detection
- Flag tasks overdue or at risk
- Identify tasks that haven't moved in a while
- Alert on approaching deadlines
</capabilities>

<instructions>
## Task Discovery Process

When asked about tasks from documents/meetings:
1. Search KB for relevant content
2. Extract potential tasks (explicit + inferred)
3. Present as a numbered list with source attribution
4. Ask which tasks to create/track
5. Pre-fill task data (title, priority, due date) from context

## Progress Check Process

When asked about task status:
1. Query task board for user's tasks
2. Group by urgency: OVERDUE, TODAY, THIS WEEK, LATER, NO DATE
3. Highlight blocked items
4. Show count summaries first, then details

## Focus Guidance Process

When asked what to focus on:
1. Start with OVERDUE tasks (highest urgency)
2. Then TODAY tasks by priority
3. Consider blocked items (may need unblocking first)
4. Recommend top 3 actions

## Task Creation

When creating tasks from extracted items:
1. Confirm with user first
2. Use extracted title, inferred priority, parsed due date
3. Link to source document/transcript
4. Set status to 'pending'
</instructions>

<criteria>
1. Personal - focus on YOUR tasks, not team project management
2. Evidence-Based - cite sources for extracted tasks
3. Actionable - always provide clear next steps
4. Efficient - summaries first, details on request
5. Non-Judgmental - track progress without shaming
</criteria>

</system>"""

    async def process(self, context: AgentContext) -> AgentResponse:
        """Process a task-related query."""
        messages = self._build_messages(context)

        # Get task context for the user
        task_context = await self._get_task_context(context)
        if task_context:
            messages[0]["content"] = task_context + "\n\n" + messages[0]["content"]

        # Add any relevant KB context for task extraction
        if context.kb_context:
            kb_summary = "\n\nKnowledge Base content (search for tasks here):\n"
            for i, chunk in enumerate(context.kb_context[:5], 1):
                source = chunk.get("metadata", {}).get("filename", "Unknown source")
                content_preview = chunk.get("content", "")[:500]
                kb_summary += f"\n[Source {i}: {source}]\n{content_preview}\n"
            messages[0]["content"] = kb_summary + "\n\n" + messages[0]["content"]

        response = self.anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=self.system_instruction,
            messages=messages,
        )

        content = response.content[0].text

        return AgentResponse(
            content=content,
            agent_name=self.name,
            agent_display_name=self.display_name,
            save_to_memory=False,
        )

    async def _get_task_context(self, context: AgentContext) -> Optional[str]:
        """Get current task status for the user."""
        if not context.user_id:
            return None

        try:
            today = date.today()
            week_end = today + timedelta(days=7)

            # First, get user's details for assignee matching and client filtering
            user_result = (
                self.supabase.table("users")
                .select("id, full_name, name, email, client_id")
                .eq("id", context.user_id)
                .single()
                .execute()
            )

            user_name = None
            client_id = None
            if user_result.data:
                user_name = user_result.data.get("full_name") or user_result.data.get("name")
                client_id = user_result.data.get("client_id")

            if not client_id:
                logger.warning(f"No client_id found for user {context.user_id}")
                return (
                    "\n[Task Context: Unable to load tasks - user not associated with a client]\n"
                )

            # Query tasks for this client
            # Get all tasks for the client, then filter in code for user-specific ones
            result = (
                self.supabase.table("project_tasks")
                .select(
                    "id, title, status, priority, due_date, blocked_at, blocker_reason, assignee_user_id, assignee_name"
                )
                .eq("client_id", client_id)
                .neq("status", "completed")
                .execute()
            )

            if not result.data:
                return "\n[Task Context: No active tasks found]\n"

            # Filter to user's tasks (assigned to them, or unassigned in single-user client)
            tasks = []
            for task in result.data:
                task_user_id = task.get("assignee_user_id")
                task_assignee = task.get("assignee_name", "") or ""

                # Include task if:
                # 1. Assigned to this user by ID
                # 2. Assigned by name match
                # 3. No assignee (unassigned tasks visible to all)
                if task_user_id == context.user_id:
                    tasks.append(task)
                elif user_name and user_name.lower() in task_assignee.lower():
                    tasks.append(task)
                elif not task_user_id and not task_assignee:
                    tasks.append(task)

            if not tasks:
                return "\n[Task Context: No tasks assigned to you]\n"

            # Categorize tasks
            overdue = []
            due_today = []
            due_this_week = []
            due_later = []
            no_due_date = []
            blocked = []

            for task in tasks:
                if task.get("status") == "blocked":
                    blocked.append(task)
                    continue

                due_date_str = task.get("due_date")
                if not due_date_str:
                    no_due_date.append(task)
                    continue

                due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
                if due_date < today:
                    overdue.append(task)
                elif due_date == today:
                    due_today.append(task)
                elif due_date <= week_end:
                    due_this_week.append(task)
                else:
                    due_later.append(task)

            # Build context string
            context_parts = ["\n[Current Task Status]"]
            context_parts.append(f"Total active tasks: {len(tasks)}")

            if overdue:
                context_parts.append(f"\nOVERDUE ({len(overdue)}):")
                for t in overdue[:5]:
                    priority_label = self._priority_label(t.get("priority", 3))
                    context_parts.append(
                        f"  - [{priority_label}] {t['title']} (due: {t['due_date']})"
                    )

            if due_today:
                context_parts.append(f"\nDUE TODAY ({len(due_today)}):")
                for t in due_today[:5]:
                    priority_label = self._priority_label(t.get("priority", 3))
                    context_parts.append(f"  - [{priority_label}] {t['title']}")

            if due_this_week:
                context_parts.append(f"\nDUE THIS WEEK ({len(due_this_week)}):")
                for t in due_this_week[:5]:
                    priority_label = self._priority_label(t.get("priority", 3))
                    context_parts.append(
                        f"  - [{priority_label}] {t['title']} (due: {t['due_date']})"
                    )

            if blocked:
                context_parts.append(f"\nBLOCKED ({len(blocked)}):")
                for t in blocked[:3]:
                    reason = t.get("blocker_reason", "No reason specified")
                    context_parts.append(f"  - {t['title']}: {reason[:50]}")

            if no_due_date:
                context_parts.append(f"\nNO DUE DATE ({len(no_due_date)})")

            return "\n".join(context_parts)

        except Exception as e:
            logger.error(f"Failed to get task context: {e}")
            return None

    def _priority_label(self, priority: int) -> str:
        """Convert priority number to label."""
        labels = {1: "Critical", 2: "High", 3: "Medium", 4: "Low", 5: "Lowest"}
        return labels.get(priority, "Medium")

    def should_handoff(self, context: AgentContext, response: str) -> Optional[tuple[str, str]]:
        """Check if we should hand off to another agent."""
        message_lower = context.user_message.lower()

        # Hand off to Oracle for transcript analysis
        if any(
            word in message_lower
            for word in ["analyze transcript", "meeting notes", "what was discussed"]
        ):
            return ("oracle", "Query requires transcript analysis expertise")

        # Hand off to Compass for career-related task prioritization
        if any(
            word in message_lower
            for word in ["career goal", "performance review", "1:1 prep", "manager conversation"]
        ):
            return ("compass", "Query requires career coaching expertise")

        # Hand off to Operator for business operations context
        if any(
            word in message_lower
            for word in ["opportunity pipeline", "project triage", "business metrics"]
        ):
            return ("operator", "Query requires business operations expertise")

        return None
