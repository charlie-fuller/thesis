"""
Quick Prompt Generator Service
Automatically generates quick prompts based on selected functions from Solomon Stage 2

This service creates 10 quick prompts (2 per function) for the 5 functions selected
during the Solomon configuration process. Prompts can be customized based on user
context from the extraction JSON.

Created: November 21, 2025
"""

from typing import Any, Dict, List, Optional

from database import get_supabase
from logger_config import get_logger

logger = get_logger(__name__)
supabase = get_supabase()

# ADDIE-based prompt library for L&D workflow
# Each prompt now includes ADDIE phase, category, and contextual keywords
ADDIE_PROMPT_LIBRARY = {
    # ANALYSIS PHASE
    "Analysis": [
        {
            "prompt": "What skills gap exists in this situation?",
            "category": "Needs Analysis",
            "addie_phase": "Analysis",
            "priority": 1,
            "contextual_keywords": ["gap", "need", "problem", "challenge", "skills", "competency", "training need"]
        },
        {
            "prompt": "What's the business problem we're trying to solve?",
            "category": "Needs Analysis",
            "addie_phase": "Analysis",
            "priority": 2,
            "contextual_keywords": ["business", "problem", "issue", "challenge", "performance", "goal"]
        },
        {
            "prompt": "Who is the target audience for this learning?",
            "category": "Audience Analysis",
            "addie_phase": "Analysis",
            "priority": 3,
            "contextual_keywords": ["audience", "learner", "participant", "employee", "team", "demographic"]
        },
        {
            "prompt": "What are the current knowledge and skill levels?",
            "category": "Audience Analysis",
            "addie_phase": "Analysis",
            "priority": 4,
            "contextual_keywords": ["baseline", "current", "existing", "knowledge", "skill level", "experience"]
        },
        {
            "prompt": "What constraints or resources do we have?",
            "category": "Context Analysis",
            "addie_phase": "Analysis",
            "priority": 5,
            "contextual_keywords": ["budget", "timeline", "resources", "constraints", "limitations", "technology"]
        }
    ],

    # DESIGN PHASE
    "Design": [
        {
            "prompt": "Create learning objectives for this topic",
            "category": "Learning Objectives",
            "addie_phase": "Design",
            "priority": 1,
            "contextual_keywords": ["objective", "outcome", "goal", "learner will", "by the end", "able to"]
        },
        {
            "prompt": "Design an assessment strategy",
            "category": "Assessment Design",
            "addie_phase": "Design",
            "priority": 2,
            "contextual_keywords": ["assessment", "evaluation", "test", "quiz", "measure", "validate", "check"]
        },
        {
            "prompt": "Map learning outcomes to business goals",
            "category": "Learning Objectives",
            "addie_phase": "Design",
            "priority": 3,
            "contextual_keywords": ["map", "align", "business goal", "outcome", "impact", "ROI"]
        },
        {
            "prompt": "What instructional strategies should we use?",
            "category": "Instructional Strategy",
            "addie_phase": "Design",
            "priority": 4,
            "contextual_keywords": ["strategy", "approach", "method", "technique", "pedagogy", "andragogy"]
        },
        {
            "prompt": "Design the course structure and flow",
            "category": "Course Architecture",
            "addie_phase": "Design",
            "priority": 5,
            "contextual_keywords": ["structure", "sequence", "flow", "outline", "module", "lesson", "unit"]
        }
    ],

    # DEVELOPMENT PHASE
    "Development": [
        {
            "prompt": "Write a detailed course outline",
            "category": "Content Development",
            "addie_phase": "Development",
            "priority": 1,
            "contextual_keywords": ["outline", "structure", "content", "module", "lesson", "topic"]
        },
        {
            "prompt": "Create content modules for this topic",
            "category": "Content Development",
            "addie_phase": "Development",
            "priority": 2,
            "contextual_keywords": ["module", "content", "material", "lesson", "unit", "chapter"]
        },
        {
            "prompt": "Design visuals and multimedia elements",
            "category": "Media Development",
            "addie_phase": "Development",
            "priority": 3,
            "contextual_keywords": ["visual", "graphic", "image", "video", "multimedia", "infographic", "diagram"]
        },
        {
            "prompt": "Write practice activities and exercises",
            "category": "Activity Development",
            "addie_phase": "Development",
            "priority": 4,
            "contextual_keywords": ["activity", "exercise", "practice", "scenario", "case study", "simulation"]
        },
        {
            "prompt": "Develop assessment questions and rubrics",
            "category": "Assessment Development",
            "addie_phase": "Development",
            "priority": 5,
            "contextual_keywords": ["question", "quiz", "test", "rubric", "assessment", "evaluation", "grading"]
        }
    ],

    # IMPLEMENTATION PHASE
    "Implementation": [
        {
            "prompt": "Create a facilitator guide",
            "category": "Facilitation Materials",
            "addie_phase": "Implementation",
            "priority": 1,
            "contextual_keywords": ["facilitator", "instructor", "trainer", "guide", "teaching", "delivery"]
        },
        {
            "prompt": "Design the delivery schedule and timeline",
            "category": "Delivery Planning",
            "addie_phase": "Implementation",
            "priority": 2,
            "contextual_keywords": ["schedule", "timeline", "calendar", "session", "delivery", "rollout"]
        },
        {
            "prompt": "Plan the rollout strategy",
            "category": "Delivery Planning",
            "addie_phase": "Implementation",
            "priority": 3,
            "contextual_keywords": ["rollout", "launch", "implementation", "deployment", "pilot", "release"]
        },
        {
            "prompt": "Prepare participant materials and resources",
            "category": "Learner Materials",
            "addie_phase": "Implementation",
            "priority": 4,
            "contextual_keywords": ["participant", "learner", "student", "handout", "workbook", "resource"]
        },
        {
            "prompt": "Set up the learning environment and technology",
            "category": "Environment Setup",
            "addie_phase": "Implementation",
            "priority": 5,
            "contextual_keywords": ["LMS", "platform", "technology", "setup", "environment", "system", "tool"]
        }
    ],

    # EVALUATION PHASE
    "Evaluation": [
        {
            "prompt": "Design evaluation metrics and KPIs",
            "category": "Evaluation Design",
            "addie_phase": "Evaluation",
            "priority": 1,
            "contextual_keywords": ["metric", "KPI", "measure", "indicator", "success", "effectiveness"]
        },
        {
            "prompt": "Create feedback surveys and forms",
            "category": "Feedback Collection",
            "addie_phase": "Evaluation",
            "priority": 2,
            "contextual_keywords": ["survey", "feedback", "questionnaire", "reaction", "satisfaction", "level 1"]
        },
        {
            "prompt": "Measure learning outcomes and ROI",
            "category": "Impact Measurement",
            "addie_phase": "Evaluation",
            "priority": 3,
            "contextual_keywords": ["ROI", "impact", "outcome", "result", "performance", "transfer", "kirkpatrick"]
        },
        {
            "prompt": "Analyze completion and engagement data",
            "category": "Data Analysis",
            "addie_phase": "Evaluation",
            "priority": 4,
            "contextual_keywords": ["completion", "engagement", "analytics", "data", "participation", "drop-off"]
        },
        {
            "prompt": "Plan for continuous improvement",
            "category": "Continuous Improvement",
            "addie_phase": "Evaluation",
            "priority": 5,
            "contextual_keywords": ["improvement", "iteration", "enhance", "update", "revise", "optimize"]
        }
    ],

    # GENERAL/SLASH COMMANDS
    "General": [
        {
            "prompt": "/image - Generate a visual for this concept",
            "category": "Slash Commands",
            "addie_phase": "General",
            "priority": 1,
            "contextual_keywords": ["visual", "image", "diagram", "graphic"]
        },
        {
            "prompt": "/help - Get help with Thesis's features",
            "category": "Slash Commands",
            "addie_phase": "General",
            "priority": 2,
            "contextual_keywords": ["help", "support", "how to"]
        },
        {
            "prompt": "Summarize this document for learning design",
            "category": "Document Processing",
            "addie_phase": "General",
            "priority": 3,
            "contextual_keywords": ["document", "file", "uploaded", "summarize", "analyze"]
        }
    ]
}

# Legacy prompt library (kept for backward compatibility)
PROMPT_LIBRARY = {
    "Conceptual_Modeler": [
        {
            "prompt": "Help me structure this concept using a framework",
            "priority": 1,
            "context_keys": ["frameworks"]
        },
        {
            "prompt": "What framework would work best for [topic]?",
            "priority": 2,
            "context_keys": ["primary_domain"]
        }
    ],
    "Independence_Identifier": [
        {
            "prompt": "What can I delegate from this list?",
            "priority": 1,
            "context_keys": []
        },
        {
            "prompt": "Who on my team should own this?",
            "priority": 2,
            "context_keys": ["team_size"]
        }
    ],
    "Report_Builder": [
        {
            "prompt": "Draft a strategic brief about [topic]",
            "priority": 1,
            "context_keys": []
        },
        {
            "prompt": "Help me write an executive summary for [project]",
            "priority": 2,
            "context_keys": ["communication_format"]
        }
    ],
    "Feedback_Drafter": [
        {
            "prompt": "Help me draft coaching feedback for [person]",
            "priority": 1,
            "context_keys": ["leadership_styles"]
        },
        {
            "prompt": "Draft constructive feedback on [topic]",
            "priority": 2,
            "context_keys": []
        }
    ],
    "Signal_Analyzer": [
        {
            "prompt": "Is this high-impact or can it wait?",
            "priority": 1,
            "context_keys": []
        },
        {
            "prompt": "What should I focus on today?",
            "priority": 2,
            "context_keys": ["strategic_focus"]
        }
    ],
    "Meeting_Optimizer": [
        {
            "prompt": "Help me prepare an agenda for [meeting]",
            "priority": 1,
            "context_keys": []
        },
        {
            "prompt": "Extract action items from this transcript",
            "priority": 2,
            "context_keys": []
        }
    ],
    "Decision_Accelerator": [
        {
            "prompt": "Help me decide between [options]",
            "priority": 1,
            "context_keys": []
        },
        {
            "prompt": "What are the trade-offs here?",
            "priority": 2,
            "context_keys": ["core_values"]
        }
    ],
    "Stakeholder_Mapper": [
        {
            "prompt": "Who are the key stakeholders for [initiative]?",
            "priority": 1,
            "context_keys": []
        },
        {
            "prompt": "What's my engagement strategy?",
            "priority": 2,
            "context_keys": ["communication_style"]
        }
    ],
    "Knowledge_Synthesizer": [
        {
            "prompt": "Summarize insights from [sources]",
            "priority": 1,
            "context_keys": []
        },
        {
            "prompt": "What patterns do you see here?",
            "priority": 2,
            "context_keys": ["frameworks"]
        }
    ],
    "Goal_Tracker": [
        {
            "prompt": "Review progress on [priority]",
            "priority": 1,
            "context_keys": ["strategic_focus"]
        },
        {
            "prompt": "What's blocking progress on [goal]?",
            "priority": 2,
            "context_keys": []
        }
    ]
}


def generate_quick_prompts(
    user_id: str,
    client_id: str,
    selected_functions: List[str],
    extraction_json: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Auto-generate quick prompts based on selected functions

    Args:
        user_id: User UUID
        client_id: Client UUID
        selected_functions: List of 5 function names from Solomon Stage 2
        extraction_json: Optional user context for customization

    Returns:
        List of generated prompt objects ready for database insertion
    """

    logger.info(f"[Quick Prompts] Generating prompts for user {user_id}, functions: {selected_functions}")

    if len(selected_functions) != 5:
        logger.warning(f"[Quick Prompts] Expected 5 functions, got {len(selected_functions)}")

    generated_prompts = []
    display_order = 1

    # For each selected function, get its prompts
    for function_name in selected_functions:
        if function_name not in PROMPT_LIBRARY:
            logger.warning(f"[Quick Prompts] Function '{function_name}' not found in prompt library")
            continue

        # Get top 2 prompts for this function
        function_prompts = PROMPT_LIBRARY[function_name][:2]

        for prompt_data in function_prompts:
            prompt_text = prompt_data["prompt"]

            # Apply context-aware customization if extraction data available
            if extraction_json:
                prompt_text = customize_prompt(
                    prompt_text,
                    function_name,
                    extraction_json
                )

            # Create prompt object
            prompt_obj = {
                "user_id": user_id,
                "client_id": client_id,
                "prompt_text": prompt_text,
                "function_name": function_name,
                "system_generated": True,
                "editable": True,
                "active": True,
                "display_order": display_order,
                "usage_count": 0
            }

            generated_prompts.append(prompt_obj)
            display_order += 1

    logger.info(f"[Quick Prompts] Generated {len(generated_prompts)} prompts")
    return generated_prompts


def customize_prompt(
    prompt_text: str,
    function_name: str,
    extraction_json: Dict[str, Any]
) -> str:
    """
    Apply user-specific context to prompt templates

    Args:
        prompt_text: Base prompt template
        function_name: Function this prompt activates
        extraction_json: User interview data from Solomon Stage 1

    Returns:
        Customized prompt text
    """

    # Extract context from interview data
    try:
        # Organization info
        org_info = extraction_json.get('organization_info', {})
        primary_domain = org_info.get('primary_domain', '').lower()

        # Team structure
        team_structure = extraction_json.get('team_structure', {})
        direct_reports = team_structure.get('direct_reports', [])
        team_size = len(direct_reports)

        # Frameworks
        frameworks_list = extraction_json.get('frameworks', [])
        framework_names = [f.get('name', '') for f in frameworks_list]

        # Strategic focus
        strategic_focus = extraction_json.get('strategic_focus', {})
        top_priorities = strategic_focus.get('top_priorities', [])

        # Leadership styles
        leadership_styles = extraction_json.get('leadership_styles', [])

        # Communication style
        communication_style = extraction_json.get('communication_style', {})
        comm_format = communication_style.get('format', '')

        # Core values
        core_values = extraction_json.get('core_values', [])

        # Function-specific customizations
        if function_name == "Conceptual_Modeler":
            if primary_domain and "[topic]" in prompt_text:
                prompt_text = prompt_text.replace("[topic]", primary_domain)
            elif "OKRs" in framework_names:
                prompt_text = prompt_text.replace("[topic]", "using OKRs")

        elif function_name == "Independence_Identifier":
            if team_size > 0 and "[team]" in prompt_text:
                prompt_text = prompt_text.replace("[team]", f"{team_size} reports")

        elif function_name == "Report_Builder":
            if comm_format and "bullet" in comm_format.lower():
                prompt_text = prompt_text.replace("[format]", "bullet-point")

        elif function_name == "Feedback_Drafter":
            if "Developer" in leadership_styles:
                prompt_text = prompt_text.replace("feedback", "development feedback")

        elif function_name == "Signal_Analyzer":
            if top_priorities and len(top_priorities) > 0:
                # Could reference specific priorities, but keeping generic for now
                pass

        elif function_name == "Meeting_Optimizer":
            if team_size >= 5:
                # Larger team = more meetings
                pass

        elif function_name == "Decision_Accelerator":
            if core_values and len(core_values) > 0:
                # Could reference values in decision prompts
                pass

        elif function_name == "Goal_Tracker":
            if "OKRs" in framework_names:
                prompt_text = prompt_text.replace("progress on [priority]", "OKR progress")

        logger.debug(f"[Quick Prompts] Customized prompt for {function_name}: {prompt_text}")

    except Exception as e:
        logger.error(f"[Quick Prompts] Error customizing prompt: {e}")
        # Return original prompt if customization fails
        pass

    return prompt_text


def save_quick_prompts(prompts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Save generated prompts to database

    Args:
        prompts: List of prompt objects

    Returns:
        Success/failure status with saved prompts
    """

    try:
        logger.info(f"[Quick Prompts] Saving {len(prompts)} prompts to database")

        # Insert prompts into database
        result = supabase.table('user_quick_prompts').insert(prompts).execute()

        logger.info(f"[Quick Prompts] Successfully saved {len(result.data)} prompts")

        return {
            "success": True,
            "count": len(result.data),
            "prompts": result.data
        }

    except Exception as e:
        logger.error(f"[Quick Prompts] Error saving prompts: {e}")
        return {
            "success": False,
            "error": str(e),
            "count": 0
        }


def get_user_quick_prompts(user_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
    """
    Retrieve quick prompts for a user

    Args:
        user_id: User UUID
        active_only: If True, only return active prompts

    Returns:
        List of quick prompts
    """

    try:
        logger.info(f"[Quick Prompts] Fetching prompts for user {user_id} (active_only={active_only})")

        query = supabase.table('user_quick_prompts').select('*').eq('user_id', user_id)

        if active_only:
            query = query.eq('active', True)

        result = query.order('display_order').execute()

        logger.info(f"[Quick Prompts] Found {len(result.data)} prompts")
        return result.data

    except Exception as e:
        logger.error(f"[Quick Prompts] Error fetching prompts: {e}")
        return []


def update_quick_prompt(
    prompt_id: str,
    user_id: str,
    updates: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update a quick prompt (e.g., edit text, toggle active)

    Args:
        prompt_id: Prompt UUID
        user_id: User UUID (for ownership verification)
        updates: Dictionary of fields to update

    Returns:
        Success/failure status with updated prompt
    """

    try:
        logger.info(f"[Quick Prompts] Updating prompt {prompt_id} for user {user_id}")

        # Verify ownership and update
        result = (
            supabase.table('user_quick_prompts')
            .update(updates)
            .eq('id', prompt_id)
            .eq('user_id', user_id)
            .execute()
        )

        if len(result.data) == 0:
            logger.warning(f"[Quick Prompts] Prompt {prompt_id} not found or not owned by user {user_id}")
            return {
                "success": False,
                "error": "Prompt not found or access denied"
            }

        logger.info(f"[Quick Prompts] Successfully updated prompt {prompt_id}")
        return {
            "success": True,
            "prompt": result.data[0]
        }

    except Exception as e:
        logger.error(f"[Quick Prompts] Error updating prompt: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def delete_quick_prompt(prompt_id: str, user_id: str) -> Dict[str, Any]:
    """
    Delete a quick prompt

    Args:
        prompt_id: Prompt UUID
        user_id: User UUID (for ownership verification)

    Returns:
        Success/failure status
    """

    try:
        logger.info(f"[Quick Prompts] Deleting prompt {prompt_id} for user {user_id}")

        # Verify ownership and delete
        result = (
            supabase.table('user_quick_prompts')
            .delete()
            .eq('id', prompt_id)
            .eq('user_id', user_id)
            .execute()
        )

        if len(result.data) == 0:
            logger.warning(f"[Quick Prompts] Prompt {prompt_id} not found or not owned by user {user_id}")
            return {
                "success": False,
                "error": "Prompt not found or access denied"
            }

        logger.info(f"[Quick Prompts] Successfully deleted prompt {prompt_id}")
        return {
            "success": True
        }

    except Exception as e:
        logger.error(f"[Quick Prompts] Error deleting prompt: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def increment_usage_count(prompt_id: str) -> Dict[str, Any]:
    """
    Increment usage count for a quick prompt (for analytics)

    Args:
        prompt_id: Prompt UUID

    Returns:
        Success/failure status with new usage count
    """

    try:
        # Get current usage count
        result = supabase.table('user_quick_prompts').select('usage_count').eq('id', prompt_id).execute()

        if len(result.data) == 0:
            return {"success": False, "error": "Prompt not found"}

        current_count = result.data[0].get('usage_count', 0)
        new_count = current_count + 1

        # Update usage count
        update_result = (
            supabase.table('user_quick_prompts')
            .update({"usage_count": new_count})
            .eq('id', prompt_id)
            .execute()
        )

        return {
            "success": True,
            "usage_count": new_count
        }

    except Exception as e:
        logger.error(f"[Quick Prompts] Error incrementing usage count: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
# ADDIE-Based Prompt Functions (New for Thesis L&D)
# ============================================================================

def generate_addie_prompts(
    user_id: str,
    client_id: str,
    phases: Optional[List[str]] = None,
    max_per_phase: int = 3
) -> List[Dict[str, Any]]:
    """
    Generate ADDIE-based quick prompts for L&D workflows

    Args:
        user_id: User UUID
        client_id: Client UUID
        phases: List of ADDIE phases to include (default: all phases)
        max_per_phase: Maximum prompts per phase (default: 3)

    Returns:
        List of generated prompt objects ready for database insertion
    """

    logger.info(f"[Quick Prompts] Generating ADDIE prompts for user {user_id}")

    if phases is None:
        phases = ["Analysis", "Design", "Development", "Implementation", "Evaluation", "General"]

    generated_prompts = []
    display_order = 1

    for phase in phases:
        if phase not in ADDIE_PROMPT_LIBRARY:
            logger.warning(f"[Quick Prompts] ADDIE phase '{phase}' not found in library")
            continue

        # Get top N prompts for this phase
        phase_prompts = ADDIE_PROMPT_LIBRARY[phase][:max_per_phase]

        for prompt_data in phase_prompts:
            prompt_obj = {
                "user_id": user_id,
                "client_id": client_id,
                "prompt_text": prompt_data["prompt"],
                "addie_phase": prompt_data["addie_phase"],
                "category": prompt_data["category"],
                "contextual_keywords": prompt_data.get("contextual_keywords", []),
                "system_generated": True,
                "editable": True,
                "active": True,
                "display_order": display_order,
                "usage_count": 0
            }

            generated_prompts.append(prompt_obj)
            display_order += 1

    logger.info(f"[Quick Prompts] Generated {len(generated_prompts)} ADDIE prompts")
    return generated_prompts


def get_contextual_prompts(
    user_id: str,
    conversation_text: str,
    addie_phase: Optional[str] = None,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Get contextually relevant prompts based on conversation content

    Args:
        user_id: User UUID
        conversation_text: Recent conversation text to analyze
        addie_phase: Optional ADDIE phase to filter by
        limit: Maximum number of prompts to return

    Returns:
        List of relevant quick prompts with relevance scores
    """

    try:
        logger.info(f"[Quick Prompts] Finding contextual prompts for user {user_id}")

        # Get all active prompts for user
        query = supabase.table('user_quick_prompts').select('*').eq('user_id', user_id).eq('active', True)

        if addie_phase:
            query = query.eq('addie_phase', addie_phase)

        result = query.execute()
        all_prompts = result.data

        if not all_prompts:
            logger.info(f"[Quick Prompts] No prompts found for user {user_id}")
            return []

        # Score each prompt based on keyword matches in conversation
        conversation_lower = conversation_text.lower()
        scored_prompts = []

        for prompt in all_prompts:
            score = 0
            keywords = prompt.get('contextual_keywords', [])

            if keywords:
                for keyword in keywords:
                    if keyword.lower() in conversation_lower:
                        score += 1

            if score > 0:
                scored_prompts.append({
                    **prompt,
                    'relevance_score': score
                })

        # Sort by relevance score (descending) and return top N
        scored_prompts.sort(key=lambda x: x['relevance_score'], reverse=True)

        logger.info(f"[Quick Prompts] Found {len(scored_prompts)} contextual prompts")
        return scored_prompts[:limit]

    except Exception as e:
        logger.error(f"[Quick Prompts] Error getting contextual prompts: {e}")
        return []


def get_prompts_by_phase(
    user_id: str,
    addie_phase: str,
    active_only: bool = True
) -> List[Dict[str, Any]]:
    """
    Get prompts filtered by ADDIE phase

    Args:
        user_id: User UUID
        addie_phase: ADDIE phase (Analysis, Design, Development, Implementation, Evaluation, General)
        active_only: If True, only return active prompts

    Returns:
        List of prompts for the specified phase
    """

    try:
        logger.info(f"[Quick Prompts] Fetching {addie_phase} prompts for user {user_id}")

        query = supabase.table('user_quick_prompts').select('*').eq('user_id', user_id).eq('addie_phase', addie_phase)

        if active_only:
            query = query.eq('active', True)

        result = query.order('display_order').execute()

        logger.info(f"[Quick Prompts] Found {len(result.data)} {addie_phase} prompts")
        return result.data

    except Exception as e:
        logger.error(f"[Quick Prompts] Error fetching prompts by phase: {e}")
        return []


def detect_addie_phase_from_conversation(conversation_text: str) -> str:
    """
    Detect the most likely ADDIE phase based on conversation content

    Args:
        conversation_text: Recent conversation text to analyze

    Returns:
        Detected ADDIE phase (Analysis, Design, Development, Implementation, Evaluation, or General)
    """

    # Define keywords for each phase
    phase_keywords = {
        "Analysis": ["gap", "need", "problem", "challenge", "audience", "learner", "baseline", "skills", "competency"],
        "Design": ["objective", "outcome", "goal", "assessment", "strategy", "structure", "learning outcome", "align"],
        "Development": ["content", "module", "material", "create", "write", "develop", "activity", "exercise", "visual"],
        "Implementation": ["deliver", "rollout", "launch", "facilitator", "schedule", "deployment", "LMS", "environment"],
        "Evaluation": ["measure", "metric", "KPI", "feedback", "survey", "ROI", "impact", "analytics", "improvement"]
    }

    conversation_lower = conversation_text.lower()
    phase_scores = {}

    # Score each phase based on keyword matches
    for phase, keywords in phase_keywords.items():
        score = sum(1 for keyword in keywords if keyword in conversation_lower)
        phase_scores[phase] = score

    # Return phase with highest score, or General if no clear match
    max_score = max(phase_scores.values())

    if max_score == 0:
        return "General"

    detected_phase = max(phase_scores, key=phase_scores.get)
    logger.info(f"[Quick Prompts] Detected ADDIE phase: {detected_phase} (score: {max_score})")

    return detected_phase
