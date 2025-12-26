"""
Quick Prompts Auto-Generation Service

Generates 5-10 contextual prompts based on selected assistant functions.
Maps the 10-function library to activation prompts that help users get started.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Function → Quick Prompt Mapping
# Each function can generate multiple contextual prompts
FUNCTION_PROMPT_MAP: Dict[str, List[str]] = {
    # Priority Sorting & Context Switching
    "priority_sorting_context_switching": [
        "Help me prioritize my tasks for today",
        "What should I focus on right now?",
        "Help me decide what to work on next",
        "Sort my priorities based on urgency and importance",
        "What are the most important tasks on my list?"
    ],

    # Decision Support with Trade-Off Analysis
    "decision_support_tradeoff_analysis": [
        "Help me evaluate the pros and cons of this decision",
        "What are the trade-offs I should consider?",
        "Help me make a decision about [topic]",
        "Analyze the risks and benefits of these options",
        "What factors should I consider for this decision?"
    ],

    # Strategic Thinking & Future Planning
    "strategic_thinking_future_planning": [
        "Help me plan for the next quarter",
        "What strategic initiatives should I focus on?",
        "Help me think through long-term goals",
        "What should I consider for our 6-month plan?",
        "Help me develop a strategic approach to [goal]"
    ],

    # Meeting Preparation & Follow-Up
    "meeting_prep_followup": [
        "Help me prepare for my upcoming meeting",
        "Create an agenda for my meeting with [person/team]",
        "Summarize the action items from our last discussion",
        "Help me follow up after today's meeting",
        "What should I cover in my meeting about [topic]?"
    ],

    # Communication Drafting
    "communication_drafting": [
        "Help me draft an email about [topic]",
        "Write a message to my team about [update]",
        "Draft a response to [person] about [subject]",
        "Help me communicate [decision] clearly",
        "Create a status update for stakeholders"
    ],

    # Problem Breakdown & Root Cause Analysis
    "problem_breakdown_root_cause": [
        "Help me understand what's causing this problem",
        "Break down this complex issue for me",
        "What's the root cause of [issue]?",
        "Help me analyze why [problem] is happening",
        "What are the underlying factors in this situation?"
    ],

    # Goal Setting & Tracking
    "goal_setting_tracking": [
        "Help me set realistic goals for [timeframe]",
        "How can I track progress on [goal]?",
        "Define success metrics for [initiative]",
        "Help me break down this goal into milestones",
        "What should my objectives be for [project]?"
    ],

    # Learning & Skill Development
    "learning_skill_development": [
        "What should I learn next to improve at [skill]?",
        "Help me create a learning plan for [topic]",
        "How can I develop expertise in [area]?",
        "What resources would help me learn [subject]?",
        "Create a growth plan for my professional development"
    ],

    # Workflow Optimization
    "workflow_optimization": [
        "How can I make this process more efficient?",
        "Help me streamline my workflow for [task]",
        "What's slowing me down and how can I fix it?",
        "Optimize my approach to [recurring task]",
        "How can I reduce time spent on [activity]?"
    ],

    # Ideation & Brainstorming
    "ideation_brainstorming": [
        "Help me brainstorm ideas for [project]",
        "What are some creative approaches to [challenge]?",
        "Generate ideas for improving [process]",
        "What alternatives should I consider for [situation]?",
        "Help me think outside the box about [topic]"
    ]
}


def generate_quick_prompts(
    selected_functions: List[str],
    max_prompts: int = 7,
    user_context: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """
    Generate quick prompts based on selected assistant functions.

    Args:
        selected_functions: List of function keys that are enabled for this user
        max_prompts: Maximum number of prompts to return (default: 7)
        user_context: Optional user context to personalize prompts (name, role, industry)

    Returns:
        List of prompt objects with text and metadata
    """
    prompts = []

    # Distribute prompts across all selected functions
    prompts_per_function = max(1, max_prompts // len(selected_functions)) if selected_functions else 0

    for function_key in selected_functions:
        if function_key not in FUNCTION_PROMPT_MAP:
            logger.warning(f"Unknown function key: {function_key}")
            continue

        # Get prompts for this function
        function_prompts = FUNCTION_PROMPT_MAP[function_key]

        # Take up to prompts_per_function from this function
        selected = function_prompts[:prompts_per_function]

        for prompt_text in selected:
            prompts.append({
                "text": prompt_text,
                "function": function_key,
                "category": _get_function_category(function_key)
            })

    # If we have fewer than max_prompts, add more from top functions
    if len(prompts) < max_prompts and selected_functions:
        remaining = max_prompts - len(prompts)
        used_prompts = {p["text"] for p in prompts}

        for function_key in selected_functions:
            if remaining <= 0:
                break

            function_prompts = FUNCTION_PROMPT_MAP.get(function_key, [])
            for prompt_text in function_prompts:
                if prompt_text not in used_prompts:
                    prompts.append({
                        "text": prompt_text,
                        "function": function_key,
                        "category": _get_function_category(function_key)
                    })
                    used_prompts.add(prompt_text)
                    remaining -= 1

                    if remaining <= 0:
                        break

    # Personalize prompts if user context provided
    if user_context:
        prompts = _personalize_prompts(prompts, user_context)

    return prompts[:max_prompts]


def _get_function_category(function_key: str) -> str:
    """Map function keys to high-level categories for grouping."""
    category_map = {
        "priority_sorting_context_switching": "Productivity",
        "decision_support_tradeoff_analysis": "Decision Making",
        "strategic_thinking_future_planning": "Strategy",
        "meeting_prep_followup": "Meetings",
        "communication_drafting": "Communication",
        "problem_breakdown_root_cause": "Problem Solving",
        "goal_setting_tracking": "Goals",
        "learning_skill_development": "Learning",
        "workflow_optimization": "Efficiency",
        "ideation_brainstorming": "Creativity"
    }
    return category_map.get(function_key, "General")


def _personalize_prompts(prompts: List[Dict[str, Any]], user_context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Personalize prompts based on user context.

    This is a placeholder for future enhancement - could use:
    - User's industry/domain
    - Recent conversations
    - Time of day
    - User's role (manager, IC, executive)
    """
    # For now, just return prompts as-is
    # Future: Replace placeholders like [topic], [team], [project] with actual user data
    return prompts


def get_all_available_prompts() -> Dict[str, List[str]]:
    """Return the complete function → prompts mapping for reference."""
    return FUNCTION_PROMPT_MAP.copy()
