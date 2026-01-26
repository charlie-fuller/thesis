"""
Task Digest Service

Generates daily task digests as Knowledge Base documents.
Creates a markdown summary of task status, overdue items, and focus recommendations.
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Optional
import uuid

from supabase import Client

from .task_tracker import TaskTracker, TaskSnapshot, TaskSummary

logger = logging.getLogger(__name__)


@dataclass
class DigestContent:
    """Generated digest content."""
    user_id: str
    generated_at: datetime
    title: str
    summary: str
    markdown_content: str
    health_score: int
    total_active: int
    overdue_count: int
    due_today_count: int


class TaskDigestService:
    """Service for generating task digest documents."""

    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.tracker = TaskTracker(supabase)

    async def generate_digest(
        self,
        user_id: str,
        client_id: Optional[str] = None
    ) -> DigestContent:
        """
        Generate a task digest for a user.

        Args:
            user_id: The user's ID
            client_id: Optional client ID for multi-tenant filtering

        Returns:
            DigestContent with markdown ready for KB storage
        """
        # Get task snapshot
        snapshot = await self.tracker.get_user_task_snapshot(user_id, client_id)

        # Build digest content
        today = date.today()
        title = f"Task Digest - {today.strftime('%A, %B %d, %Y')}"

        # Calculate health score
        health = self._calculate_health_score(snapshot)
        health_emoji = self._health_indicator(health)

        # Build summary line
        summary_parts = []
        if snapshot.overdue:
            summary_parts.append(f"{len(snapshot.overdue)} overdue")
        if snapshot.due_today:
            summary_parts.append(f"{len(snapshot.due_today)} due today")
        if snapshot.due_this_week:
            summary_parts.append(f"{len(snapshot.due_this_week)} due this week")
        if snapshot.blocked:
            summary_parts.append(f"{len(snapshot.blocked)} blocked")

        if summary_parts:
            summary = f"{health_emoji} Health: {health}/100 | " + ", ".join(summary_parts)
        else:
            summary = f"{health_emoji} Health: {health}/100 | All clear! No urgent tasks."

        # Build markdown content
        markdown = self._build_markdown(title, summary, snapshot, health, today)

        return DigestContent(
            user_id=user_id,
            generated_at=datetime.now(timezone.utc),
            title=title,
            summary=summary,
            markdown_content=markdown,
            health_score=health,
            total_active=snapshot.total_active,
            overdue_count=len(snapshot.overdue),
            due_today_count=len(snapshot.due_today)
        )

    async def save_digest_to_kb(
        self,
        digest: DigestContent,
        client_id: str
    ) -> dict:
        """
        Save a digest as a Knowledge Base document.

        Args:
            digest: The generated digest content
            client_id: Client ID for the document

        Returns:
            dict with document ID and status
        """
        try:
            # Create document record
            doc_id = str(uuid.uuid4())
            filename = f"task-digest-{date.today().isoformat()}.md"

            # Check if a digest for today already exists
            existing = self.supabase.table('documents').select('id').eq(
                'client_id', client_id
            ).eq('filename', filename).execute()

            if existing.data:
                # Update existing digest
                doc_id = existing.data[0]['id']
                self.supabase.table('documents').update({
                    'content': digest.markdown_content,
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }).eq('id', doc_id).execute()

                # Delete old chunks for re-embedding
                self.supabase.table('document_chunks').delete().eq(
                    'document_id', doc_id
                ).execute()

                logger.info(f"Updated existing digest document: {doc_id}")
            else:
                # Create new document
                self.supabase.table('documents').insert({
                    'id': doc_id,
                    'client_id': client_id,
                    'filename': filename,
                    'title': digest.title,
                    'content': digest.markdown_content,
                    'file_type': 'text/markdown',
                    'source': 'taskmaster_digest',
                    'processed': False,
                    'processing_status': 'pending'
                }).execute()

                logger.info(f"Created new digest document: {doc_id}")

            # Tag for Taskmaster agent
            self.supabase.table('agent_knowledge_base').upsert({
                'document_id': doc_id,
                'agent_id': self._get_taskmaster_agent_id(),
                'relevance_score': 1.0,
                'assigned_by': 'system',
                'assignment_type': 'auto'
            }, on_conflict='document_id,agent_id').execute()

            return {
                'status': 'success',
                'document_id': doc_id,
                'filename': filename,
                'is_update': bool(existing.data)
            }

        except Exception as e:
            logger.error(f"Failed to save digest to KB: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def _get_taskmaster_agent_id(self) -> str:
        """Get the Taskmaster agent's database ID."""
        result = self.supabase.table('agents').select('id').eq(
            'name', 'taskmaster'
        ).execute()

        if result.data:
            return result.data[0]['id']
        return None

    def _build_markdown(
        self,
        title: str,
        summary: str,
        snapshot: TaskSnapshot,
        health: int,
        today: date
    ) -> str:
        """Build markdown content for the digest."""
        lines = [
            f"# {title}",
            "",
            f"**{summary}**",
            "",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "---",
            ""
        ]

        # Health score section
        lines.extend([
            "## Task Health",
            "",
            f"- **Score**: {health}/100 {self._health_indicator(health)}",
            f"- **Active Tasks**: {snapshot.total_active}",
            f"- **Completed (7 days)**: {snapshot.completed_recently}",
            ""
        ])

        # Overdue section
        if snapshot.overdue:
            lines.extend([
                "## Overdue Tasks",
                ""
            ])
            for task in snapshot.overdue[:10]:
                priority = self._priority_marker(task.priority)
                lines.append(f"- {priority} **{task.title}** - {task.days_overdue}d overdue")
            if len(snapshot.overdue) > 10:
                lines.append(f"- *...and {len(snapshot.overdue) - 10} more*")
            lines.append("")

        # Due today section
        if snapshot.due_today:
            lines.extend([
                "## Due Today",
                ""
            ])
            for task in snapshot.due_today:
                priority = self._priority_marker(task.priority)
                lines.append(f"- {priority} {task.title}")
            lines.append("")

        # Due this week section
        if snapshot.due_this_week:
            lines.extend([
                "## Due This Week",
                ""
            ])
            for task in snapshot.due_this_week[:10]:
                priority = self._priority_marker(task.priority)
                due_str = task.due_date.strftime('%a %m/%d') if task.due_date else ''
                lines.append(f"- {priority} {task.title} ({due_str})")
            if len(snapshot.due_this_week) > 10:
                lines.append(f"- *...and {len(snapshot.due_this_week) - 10} more*")
            lines.append("")

        # Blocked section
        if snapshot.blocked:
            lines.extend([
                "## Blocked",
                ""
            ])
            for task in snapshot.blocked[:5]:
                reason = task.blocker_reason or "No reason specified"
                lines.append(f"- **{task.title}**: {reason[:80]}")
            lines.append("")

        # Focus recommendation
        lines.extend([
            "## Focus Recommendation",
            ""
        ])

        if snapshot.overdue:
            focus = snapshot.overdue[0]
            lines.append(f"Start with **{focus.title}** - it's {focus.days_overdue} day(s) overdue.")
        elif snapshot.due_today:
            focus = snapshot.due_today[0]
            lines.append(f"Prioritize **{focus.title}** - due today.")
        elif snapshot.blocked:
            focus = snapshot.blocked[0]
            lines.append(f"Unblock **{focus.title}** to make progress.")
        elif snapshot.due_this_week:
            focus = snapshot.due_this_week[0]
            lines.append(f"Get ahead on **{focus.title}** - due {focus.due_date}.")
        else:
            lines.append("No urgent tasks. Great time to tackle something from your backlog!")

        lines.append("")

        return "\n".join(lines)

    def _calculate_health_score(self, snapshot: TaskSnapshot) -> int:
        """Calculate health score from snapshot."""
        if snapshot.total_active == 0:
            return 100

        score = 100
        score -= min(len(snapshot.overdue) * 15, 50)
        score -= min(len(snapshot.blocked) * 10, 30)
        score -= min(len(snapshot.no_due_date) * 2, 10)
        score += min(snapshot.completed_recently * 3, 15)

        return max(0, min(100, score))

    def _health_indicator(self, score: int) -> str:
        """Get health score indicator."""
        if score >= 80:
            return "[Good]"
        elif score >= 60:
            return "[Warning]"
        else:
            return "[Critical]"

    def _priority_marker(self, priority: int) -> str:
        """Get priority marker for markdown."""
        markers = {
            1: "[P1]",
            2: "[P2]",
            3: "[P3]",
            4: "[P4]",
            5: "[P5]"
        }
        return markers.get(priority, "[P3]")
