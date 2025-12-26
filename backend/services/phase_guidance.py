"""
Phase Guidance Service
Provides proactive guidance on what elements might be missing from each ADDIE phase
"""
from typing import Dict, List

from logger_config import get_logger

logger = get_logger(__name__)

# Key elements that should be addressed in each ADDIE phase
PHASE_CHECKLIST = {
    "Analysis": {
        "required": [
            ("audience", ["audience", "learner", "target", "who will", "participants"]),
            ("business_problem", ["problem", "challenge", "issue", "gap", "need"]),
            ("goals", ["goal", "objective", "outcome", "result", "success"]),
        ],
        "recommended": [
            ("constraints", ["constraint", "limitation", "budget", "timeline", "resource"]),
            ("current_state", ["current", "baseline", "existing", "today", "as-is"]),
            ("stakeholders", ["stakeholder", "sponsor", "manager", "leadership"]),
        ]
    },
    "Design": {
        "required": [
            ("learning_objectives", ["objective", "outcome", "learner will", "able to"]),
            ("assessment_strategy", ["assess", "measure", "evaluate", "test", "quiz"]),
            ("content_structure", ["structure", "outline", "flow", "sequence", "module"]),
        ],
        "recommended": [
            ("instructional_strategies", ["strategy", "method", "approach", "technique"]),
            ("delivery_format", ["format", "modality", "online", "in-person", "blended"]),
            ("timing", ["duration", "time", "length", "minutes", "hours"]),
        ]
    },
    "Development": {
        "required": [
            ("content_materials", ["content", "material", "resource", "asset"]),
            ("activities", ["activity", "exercise", "practice", "interaction"]),
            ("media_elements", ["visual", "video", "image", "graphic", "media"]),
        ],
        "recommended": [
            ("facilitator_guide", ["facilitator", "instructor", "guide", "notes"]),
            ("learner_materials", ["handout", "workbook", "job aid", "reference"]),
            ("technology_setup", ["lms", "platform", "technology", "tool"]),
        ]
    },
    "Implementation": {
        "required": [
            ("delivery_plan", ["deliver", "rollout", "launch", "deploy"]),
            ("pilot_testing", ["pilot", "test", "trial", "beta"]),
            ("communication", ["communicate", "announce", "inform", "notify"]),
        ],
        "recommended": [
            ("facilitator_training", ["train the trainer", "facilitator prep", "instructor"]),
            ("technical_setup", ["setup", "configure", "install", "access"]),
            ("support_plan", ["support", "help desk", "faq", "troubleshoot"]),
        ]
    },
    "Evaluation": {
        "required": [
            ("reaction_feedback", ["feedback", "survey", "reaction", "satisfaction"]),
            ("learning_assessment", ["assessment", "test", "quiz", "knowledge check"]),
            ("performance_metrics", ["performance", "metric", "kpi", "indicator"]),
        ],
        "recommended": [
            ("roi_measurement", ["roi", "return", "business impact", "value"]),
            ("behavior_change", ["behavior", "application", "transfer", "on-the-job"]),
            ("improvement_plan", ["improve", "iterate", "enhance", "next version"]),
        ]
    }
}

# Friendly names for display
ELEMENT_LABELS = {
    "audience": "Target Audience",
    "business_problem": "Business Problem/Need",
    "goals": "Learning Goals",
    "constraints": "Constraints & Resources",
    "current_state": "Current State Assessment",
    "stakeholders": "Key Stakeholders",
    "learning_objectives": "Learning Objectives",
    "assessment_strategy": "Assessment Strategy",
    "content_structure": "Content Structure",
    "instructional_strategies": "Instructional Strategies",
    "delivery_format": "Delivery Format",
    "timing": "Timing/Duration",
    "content_materials": "Content Materials",
    "activities": "Learning Activities",
    "media_elements": "Media/Visual Elements",
    "facilitator_guide": "Facilitator Guide",
    "learner_materials": "Learner Materials",
    "technology_setup": "Technology Setup",
    "delivery_plan": "Delivery Plan",
    "pilot_testing": "Pilot Testing",
    "communication": "Communication Plan",
    "facilitator_training": "Facilitator Training",
    "technical_setup": "Technical Setup",
    "support_plan": "Support Plan",
    "reaction_feedback": "Reaction Feedback",
    "learning_assessment": "Learning Assessment",
    "performance_metrics": "Performance Metrics",
    "roi_measurement": "ROI Measurement",
    "behavior_change": "Behavior Change Tracking",
    "improvement_plan": "Improvement Plan",
}


def check_element_present(content: str, keywords: List[str]) -> bool:
    """Check if any of the keywords are present in the content"""
    content_lower = content.lower()
    return any(keyword.lower() in content_lower for keyword in keywords)


def get_missing_elements(
    phase: str,
    conversation_text: str,
    include_recommended: bool = False
) -> Dict[str, List[str]]:
    """
    Analyze conversation text and return missing elements for the given phase.

    Args:
        phase: Current ADDIE phase (Analysis, Design, Development, Implementation, Evaluation)
        conversation_text: Combined text from the conversation
        include_recommended: Whether to include recommended (optional) elements

    Returns:
        Dictionary with 'required' and optionally 'recommended' missing elements
    """
    if phase not in PHASE_CHECKLIST:
        return {"required": [], "recommended": []}

    checklist = PHASE_CHECKLIST[phase]
    result = {"required": [], "recommended": []}

    # Check required elements
    for element_id, keywords in checklist["required"]:
        if not check_element_present(conversation_text, keywords):
            label = ELEMENT_LABELS.get(element_id, element_id.replace("_", " ").title())
            result["required"].append(label)

    # Check recommended elements if requested
    if include_recommended:
        for element_id, keywords in checklist["recommended"]:
            if not check_element_present(conversation_text, keywords):
                label = ELEMENT_LABELS.get(element_id, element_id.replace("_", " ").title())
                result["recommended"].append(label)

    return result


def get_phase_guidance(
    phase: str,
    conversation_text: str
) -> Dict[str, any]:
    """
    Get comprehensive guidance for the current phase.

    Returns:
        Dictionary containing:
        - phase: Current phase name
        - missing_required: List of required elements not yet addressed
        - missing_recommended: List of recommended elements not yet addressed
        - completeness: Percentage of required elements addressed (0-100)
        - suggestion: Contextual suggestion text
    """
    missing = get_missing_elements(phase, conversation_text, include_recommended=True)

    # Calculate completeness based on required elements only
    if phase in PHASE_CHECKLIST:
        total_required = len(PHASE_CHECKLIST[phase]["required"])
        addressed_required = total_required - len(missing["required"])
        completeness = round((addressed_required / total_required) * 100) if total_required > 0 else 100
    else:
        completeness = 0

    # Generate contextual suggestion
    suggestion = None
    if missing["required"]:
        first_missing = missing["required"][0]
        suggestion = f"Consider addressing: {first_missing}"
        if len(missing["required"]) > 1:
            suggestion += f" (and {len(missing['required']) - 1} more)"
    elif missing["recommended"]:
        suggestion = f"Looking good! You might also want to consider: {missing['recommended'][0]}"
    else:
        suggestion = f"Great work! You've covered all key elements for the {phase} phase."

    return {
        "phase": phase,
        "missing_required": missing["required"],
        "missing_recommended": missing["recommended"],
        "completeness": completeness,
        "suggestion": suggestion
    }


def get_phase_prompts(phase: str, missing_elements: List[str]) -> List[str]:
    """
    Generate helpful prompts based on missing elements.

    Args:
        phase: Current ADDIE phase
        missing_elements: List of missing element labels

    Returns:
        List of suggested prompts to help address missing elements
    """
    prompts = []

    ELEMENT_PROMPTS = {
        "Target Audience": "Who is the target audience for this learning experience?",
        "Business Problem/Need": "What business problem are we trying to solve with this training?",
        "Learning Goals": "What are the main goals we want learners to achieve?",
        "Learning Objectives": "Help me write learning objectives for this topic",
        "Assessment Strategy": "How should we assess whether learners achieved the objectives?",
        "Content Structure": "What should the course structure and flow look like?",
        "Content Materials": "What content and materials do we need to develop?",
        "Learning Activities": "What activities will help learners practice these skills?",
        "Delivery Plan": "How should we roll out this training to learners?",
        "Reaction Feedback": "How will we collect feedback from participants?",
        "Performance Metrics": "What metrics will tell us if this training was successful?",
    }

    for element in missing_elements[:3]:  # Limit to top 3
        if element in ELEMENT_PROMPTS:
            prompts.append(ELEMENT_PROMPTS[element])

    return prompts
