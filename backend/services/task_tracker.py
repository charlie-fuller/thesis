"""
Task Tracker Service

Provides task querying, categorization, and slippage detection
for the Taskmaster agent. Focuses on personal task accountability.
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional

from supabase import Client

logger = logging.getLogger(__name__)


@dataclass
class TaskSummary:
    """Summary of a single task."""
    id: str
    title: str
    status: str
    priority: int
    priority_label: str
    due_date: Optional[date]
    days_overdue: Optional[int]
    days_until_due: Optional[int]
    is_blocked: bool
    blocker_reason: Optional[str]
    source_type: Optional[str]
    source_id: Optional[str]


@dataclass
class TaskSnapshot:
    """Complete snapshot of user's task status."""
    total_active: int
    overdue: list[TaskSummary]
    due_today: list[TaskSummary]
    due_this_week: list[TaskSummary]
    due_later: list[TaskSummary]
    no_due_date: list[TaskSummary]
    blocked: list[TaskSummary]
    completed_recently: int  # Last 7 days


PRIORITY_LABELS = {
    1: "Critical",
    2: "High",
    3: "Medium",
    4: "Low",
    5: "Lowest"
}


class TaskTracker:
    """Service for tracking and querying user tasks."""

    def __init__(self, supabase: Client):
        self.supabase = supabase

    async def get_user_task_snapshot(
        self,
        user_id: str,
        client_id: Optional[str] = None
    ) -> TaskSnapshot:
        """
        Get a complete snapshot of user's active tasks.

        Args:
            user_id: The user's ID
            client_id: Optional client ID for multi-tenant filtering

        Returns:
            TaskSnapshot with tasks categorized by urgency
        """
        today = date.today()
        week_end = today + timedelta(days=7)
        week_ago = today - timedelta(days=7)

        # Build query for active tasks
        query = self.supabase.table('project_tasks').select(
            'id, title, status, priority, due_date, blocked_at, blocker_reason, '
            'source_type, source_transcript_id, source_conversation_id, '
            'source_research_task_id, source_opportunity_id'
        ).eq('assignee_user_id', user_id).neq('status', 'completed')

        if client_id:
            query = query.eq('client_id', client_id)

        result = query.execute()
        tasks = result.data or []

        # Query completed tasks in last 7 days
        completed_query = self.supabase.table('project_tasks').select(
            'id', count='exact'
        ).eq('assignee_user_id', user_id).eq(
            'status', 'completed'
        ).gte('completed_at', week_ago.isoformat())

        if client_id:
            completed_query = completed_query.eq('client_id', client_id)

        completed_result = completed_query.execute()
        completed_count = completed_result.count or 0

        # Categorize tasks
        overdue = []
        due_today = []
        due_this_week = []
        due_later = []
        no_due_date = []
        blocked = []

        for task in tasks:
            summary = self._task_to_summary(task, today)

            if summary.is_blocked:
                blocked.append(summary)
                continue

            if summary.due_date is None:
                no_due_date.append(summary)
            elif summary.days_overdue and summary.days_overdue > 0:
                overdue.append(summary)
            elif summary.due_date == today:
                due_today.append(summary)
            elif summary.due_date <= week_end:
                due_this_week.append(summary)
            else:
                due_later.append(summary)

        # Sort by priority within each category
        for task_list in [overdue, due_today, due_this_week, due_later, no_due_date, blocked]:
            task_list.sort(key=lambda t: (t.priority, t.due_date or date.max))

        # Sort overdue by days overdue (most overdue first)
        overdue.sort(key=lambda t: (-(t.days_overdue or 0), t.priority))

        return TaskSnapshot(
            total_active=len(tasks),
            overdue=overdue,
            due_today=due_today,
            due_this_week=due_this_week,
            due_later=due_later,
            no_due_date=no_due_date,
            blocked=blocked,
            completed_recently=completed_count
        )

    async def get_focus_recommendations(
        self,
        user_id: str,
        client_id: Optional[str] = None,
        max_recommendations: int = 3
    ) -> list[dict]:
        """
        Get prioritized focus recommendations for the user.

        Args:
            user_id: The user's ID
            client_id: Optional client ID
            max_recommendations: Maximum number of recommendations

        Returns:
            List of recommended tasks with reasoning
        """
        snapshot = await self.get_user_task_snapshot(user_id, client_id)
        recommendations = []

        # Priority 1: Overdue tasks
        for task in snapshot.overdue[:max_recommendations]:
            recommendations.append({
                'task': task,
                'urgency': 'OVERDUE',
                'reasoning': f'{task.days_overdue} day(s) overdue - address immediately',
                'suggested_action': 'Complete or reschedule'
            })

        remaining = max_recommendations - len(recommendations)

        # Priority 2: Due today
        if remaining > 0:
            for task in snapshot.due_today[:remaining]:
                recommendations.append({
                    'task': task,
                    'urgency': 'TODAY',
                    'reasoning': 'Due today - complete before end of day',
                    'suggested_action': 'Block time to complete'
                })

        remaining = max_recommendations - len(recommendations)

        # Priority 3: Blocked items (may need unblocking)
        if remaining > 0:
            for task in snapshot.blocked[:remaining]:
                recommendations.append({
                    'task': task,
                    'urgency': 'BLOCKED',
                    'reasoning': f'Blocked: {task.blocker_reason or "unknown reason"}',
                    'suggested_action': 'Identify and remove blocker'
                })

        remaining = max_recommendations - len(recommendations)

        # Priority 4: Due this week (high priority first)
        if remaining > 0:
            high_priority_this_week = [t for t in snapshot.due_this_week if t.priority <= 2]
            for task in high_priority_this_week[:remaining]:
                recommendations.append({
                    'task': task,
                    'urgency': 'THIS_WEEK',
                    'reasoning': f'High priority, due {task.due_date}',
                    'suggested_action': 'Schedule time this week'
                })

        return recommendations[:max_recommendations]

    async def detect_slippage(
        self,
        user_id: str,
        client_id: Optional[str] = None
    ) -> dict:
        """
        Detect tasks that are slipping or at risk.

        Args:
            user_id: The user's ID
            client_id: Optional client ID

        Returns:
            Dictionary with slippage analysis
        """
        snapshot = await self.get_user_task_snapshot(user_id, client_id)
        today = date.today()

        # Tasks at risk: due within 2 days, still pending, priority <= 3
        at_risk = []
        for task in snapshot.due_this_week:
            if task.due_date and task.status == 'pending':
                days_until = (task.due_date - today).days
                if days_until <= 2 and task.priority <= 3:
                    at_risk.append({
                        'task': task,
                        'days_until_due': days_until,
                        'risk_reason': 'Due soon, not started'
                    })

        return {
            'overdue_count': len(snapshot.overdue),
            'overdue_tasks': snapshot.overdue[:5],
            'at_risk_count': len(at_risk),
            'at_risk_tasks': at_risk[:5],
            'blocked_count': len(snapshot.blocked),
            'blocked_tasks': snapshot.blocked[:3],
            'health_score': self._calculate_health_score(snapshot)
        }

    def _task_to_summary(self, task: dict, today: date) -> TaskSummary:
        """Convert a task dict to TaskSummary."""
        due_date = None
        days_overdue = None
        days_until_due = None

        if task.get('due_date'):
            due_date = datetime.strptime(task['due_date'], '%Y-%m-%d').date()
            delta = (due_date - today).days
            if delta < 0:
                days_overdue = abs(delta)
            else:
                days_until_due = delta

        is_blocked = task.get('status') == 'blocked'
        priority = task.get('priority', 3)

        # Determine source ID
        source_id = (
            task.get('source_transcript_id') or
            task.get('source_conversation_id') or
            task.get('source_research_task_id') or
            task.get('source_opportunity_id')
        )

        return TaskSummary(
            id=task['id'],
            title=task['title'],
            status=task['status'],
            priority=priority,
            priority_label=PRIORITY_LABELS.get(priority, 'Medium'),
            due_date=due_date,
            days_overdue=days_overdue,
            days_until_due=days_until_due,
            is_blocked=is_blocked,
            blocker_reason=task.get('blocker_reason'),
            source_type=task.get('source_type'),
            source_id=source_id
        )

    def _calculate_health_score(self, snapshot: TaskSnapshot) -> int:
        """
        Calculate a task health score (0-100).

        Higher is better. Penalizes overdue and blocked tasks.
        """
        if snapshot.total_active == 0:
            return 100

        # Start at 100, deduct for issues
        score = 100

        # Heavy penalty for overdue tasks
        overdue_penalty = min(len(snapshot.overdue) * 15, 50)
        score -= overdue_penalty

        # Moderate penalty for blocked tasks
        blocked_penalty = min(len(snapshot.blocked) * 10, 30)
        score -= blocked_penalty

        # Small penalty for tasks without due dates (harder to track)
        no_date_penalty = min(len(snapshot.no_due_date) * 2, 10)
        score -= no_date_penalty

        # Bonus for recent completions
        completion_bonus = min(snapshot.completed_recently * 3, 15)
        score += completion_bonus

        return max(0, min(100, score))


def format_task_snapshot_for_context(snapshot: TaskSnapshot) -> str:
    """Format a task snapshot as context string for agent prompts."""
    parts = ["\n[Current Task Status]"]
    parts.append(f"Total active tasks: {snapshot.total_active}")
    parts.append(f"Completed in last 7 days: {snapshot.completed_recently}")
    parts.append(f"Task health score: {_calculate_health_score_from_snapshot(snapshot)}/100")

    if snapshot.overdue:
        parts.append(f"\nOVERDUE ({len(snapshot.overdue)}):")
        for t in snapshot.overdue[:5]:
            parts.append(f"  - [{t.priority_label}] {t.title} ({t.days_overdue}d late)")

    if snapshot.due_today:
        parts.append(f"\nDUE TODAY ({len(snapshot.due_today)}):")
        for t in snapshot.due_today[:5]:
            parts.append(f"  - [{t.priority_label}] {t.title}")

    if snapshot.due_this_week:
        parts.append(f"\nDUE THIS WEEK ({len(snapshot.due_this_week)}):")
        for t in snapshot.due_this_week[:5]:
            parts.append(f"  - [{t.priority_label}] {t.title} (due: {t.due_date})")

    if snapshot.blocked:
        parts.append(f"\nBLOCKED ({len(snapshot.blocked)}):")
        for t in snapshot.blocked[:3]:
            reason = (t.blocker_reason or 'No reason')[:50]
            parts.append(f"  - {t.title}: {reason}")

    if snapshot.no_due_date:
        parts.append(f"\nNO DUE DATE ({len(snapshot.no_due_date)})")

    return "\n".join(parts)


def _calculate_health_score_from_snapshot(snapshot: TaskSnapshot) -> int:
    """Calculate health score from snapshot (standalone function)."""
    if snapshot.total_active == 0:
        return 100

    score = 100
    score -= min(len(snapshot.overdue) * 15, 50)
    score -= min(len(snapshot.blocked) * 10, 30)
    score -= min(len(snapshot.no_due_date) * 2, 10)
    score += min(snapshot.completed_recently * 3, 15)

    return max(0, min(100, score))
