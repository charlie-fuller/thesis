"""Template Library Routes.

Exposes the ADDIE prompt library as browsable templates.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from services.quick_prompt_generator import ADDIE_PROMPT_LIBRARY

from auth import get_current_user
from logger_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.get("")
async def get_templates(
    phase: Optional[str] = Query(None, description="Filter by ADDIE phase"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in prompt text"),
    current_user: dict = Depends(get_current_user),
):
    """Get all templates from the ADDIE prompt library.

    Returns templates organized by phase with optional filtering.
    """
    try:
        result = {
            "success": True,
            "templates": [],
            "phases": list(ADDIE_PROMPT_LIBRARY.keys()),
            "categories": set(),
        }

        template_id = 0

        for phase_name, prompts in ADDIE_PROMPT_LIBRARY.items():
            # Apply phase filter
            if phase and phase.lower() != phase_name.lower():
                continue

            for prompt in prompts:
                template_id += 1

                # Apply category filter
                if category and prompt.get("category", "").lower() != category.lower():
                    continue

                # Apply search filter
                if search and search.lower() not in prompt.get("prompt", "").lower():
                    continue

                result["templates"].append(
                    {
                        "id": f"template_{template_id}",
                        "prompt": prompt.get("prompt"),
                        "category": prompt.get("category"),
                        "addie_phase": prompt.get("addie_phase"),
                        "priority": prompt.get("priority", 99),
                        "keywords": prompt.get("contextual_keywords", []),
                    }
                )

                # Collect unique categories
                if prompt.get("category"):
                    result["categories"].add(prompt["category"])

        # Convert categories set to sorted list
        result["categories"] = sorted(result["categories"])

        # Sort by phase and priority
        phase_order = {
            "Analysis": 1,
            "Design": 2,
            "Development": 3,
            "Implementation": 4,
            "Evaluation": 5,
        }
        result["templates"].sort(
            key=lambda x: (phase_order.get(x["addie_phase"], 99), x["priority"])
        )

        return result

    except Exception as e:
        logger.error(f"Error fetching templates: {str(e)}")
        return {"success": False, "error": str(e)}


@router.get("/by-phase")
async def get_templates_by_phase(current_user: dict = Depends(get_current_user)):
    """Get templates organized by ADDIE phase for easy browsing."""
    try:
        result = {"success": True, "phases": {}}

        phase_descriptions = {
            "Analysis": "Identify learning needs, gaps, and audience characteristics",
            "Design": "Create learning objectives, assessments, and course structure",
            "Development": "Build content, activities, and materials",
            "Implementation": "Deploy training and prepare facilitators",
            "Evaluation": "Measure effectiveness and gather feedback",
        }

        phase_colors = {
            "Analysis": "green",
            "Design": "blue",
            "Development": "purple",
            "Implementation": "orange",
            "Evaluation": "pink",
        }

        template_id = 0

        for phase_name, prompts in ADDIE_PROMPT_LIBRARY.items():
            templates = []
            categories = set()

            for prompt in prompts:
                template_id += 1
                templates.append(
                    {
                        "id": f"template_{template_id}",
                        "prompt": prompt.get("prompt"),
                        "category": prompt.get("category"),
                        "priority": prompt.get("priority", 99),
                        "keywords": prompt.get("contextual_keywords", []),
                    }
                )
                if prompt.get("category"):
                    categories.add(prompt["category"])

            result["phases"][phase_name] = {
                "name": phase_name,
                "description": phase_descriptions.get(phase_name, ""),
                "color": phase_colors.get(phase_name, "gray"),
                "categories": sorted(categories),
                "template_count": len(templates),
                "templates": sorted(templates, key=lambda x: x["priority"]),
            }

        return result

    except Exception as e:
        logger.error(f"Error fetching templates by phase: {str(e)}")
        return {"success": False, "error": str(e)}


@router.get("/categories")
async def get_template_categories(current_user: dict = Depends(get_current_user)):
    """Get all unique categories across all phases."""
    try:
        categories = set()

        for _phase_name, prompts in ADDIE_PROMPT_LIBRARY.items():
            for prompt in prompts:
                if prompt.get("category"):
                    categories.add(prompt["category"])

        return {"success": True, "categories": sorted(categories)}

    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}")
        return {"success": False, "error": str(e)}
