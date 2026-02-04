"""DISCo PRD Service.

Handles the Convergence stage of the DISCo pipeline:
- Generating PRDs from approved bundles
- Generating Evaluation Frameworks for research/evaluation bundles
- Generating Decision Frameworks for governance bundles
- Managing document lifecycle (draft -> review -> approved -> exported)
- Generating executive summaries across multiple documents

The Convergence stage transforms approved initiative bundles into
actionable documents ready for implementation or decision-making.
"""

import asyncio
import re
from datetime import datetime, timezone
from typing import AsyncGenerator, Dict, List, Optional
from uuid import uuid4

from database import get_supabase
from logger_config import get_logger

logger = get_logger(__name__)
supabase = get_supabase()


# ============================================================================
# OUTPUT TYPE CONFIGURATION
# ============================================================================

OUTPUT_TYPE_CONFIG = {
    "prd": {
        "agent_prompt": "prd_generator",
        "parser": "parse_prd_sections",
        "label": "Product Requirements Document",
        "description": "For build/development bundles",
    },
    "evaluation_framework": {
        "agent_prompt": "evaluation_framework_generator",
        "parser": "parse_evaluation_sections",
        "label": "Evaluation Framework",
        "description": "For research/evaluation bundles",
    },
    "decision_framework": {
        "agent_prompt": "decision_framework_generator",
        "parser": "parse_decision_sections",
        "label": "Decision Framework",
        "description": "For governance decisions",
    },
}


# ============================================================================
# PRD MANAGEMENT
# ============================================================================


async def create_prd(
    bundle_id: str,
    initiative_id: str,
    title: str,
    content_markdown: str,
    content_structured: Optional[Dict] = None,
    source_output_id: Optional[str] = None,
) -> Dict:
    """Create a new PRD from a bundle."""
    prd_id = str(uuid4())

    prd_data = {
        "id": prd_id,
        "bundle_id": bundle_id,
        "initiative_id": initiative_id,
        "title": title,
        "content_markdown": content_markdown,
        "content_structured": content_structured or {},
        "status": "draft",
        "version": 1,
        "source_output_id": source_output_id,
    }

    result = await asyncio.to_thread(lambda: supabase.table("disco_prds").insert(prd_data).execute())

    if not result.data:
        raise Exception("Failed to create PRD")

    logger.info(f"Created PRD {prd_id} for bundle {bundle_id}: {title}")
    return result.data[0]


async def get_prd(prd_id: str) -> Optional[Dict]:
    """Get a PRD by ID."""
    result = await asyncio.to_thread(
        lambda: supabase.table("disco_prds")
        .select("*, disco_bundles(name, status)")
        .eq("id", prd_id)
        .single()
        .execute()
    )
    return result.data


async def list_prds(initiative_id: str, bundle_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict]:
    """List PRDs for an initiative."""
    query = supabase.table("disco_prds").select("*, disco_bundles(name, status)").eq("initiative_id", initiative_id)

    if bundle_id:
        query = query.eq("bundle_id", bundle_id)
    if status:
        query = query.eq("status", status)

    query = query.order("created_at", desc=True)

    result = await asyncio.to_thread(lambda: query.execute())
    return result.data or []


async def update_prd(prd_id: str, updates: Dict) -> Dict:
    """Update a PRD."""
    # Remove protected fields
    safe_updates = {k: v for k, v in updates.items() if k not in ["id", "bundle_id", "initiative_id", "created_at"]}

    result = await asyncio.to_thread(
        lambda: supabase.table("disco_prds").update(safe_updates).eq("id", prd_id).execute()
    )

    if not result.data:
        raise ValueError(f"PRD not found: {prd_id}")

    logger.info(f"Updated PRD {prd_id}")
    return result.data[0]


async def approve_prd(prd_id: str, user_id: str) -> Dict:
    """Approve a PRD."""
    result = await asyncio.to_thread(
        lambda: supabase.table("disco_prds")
        .update(
            {
                "status": "approved",
                "approved_at": datetime.now(timezone.utc).isoformat(),
                "approved_by": user_id,
            }
        )
        .eq("id", prd_id)
        .execute()
    )

    if not result.data:
        raise ValueError(f"PRD not found: {prd_id}")

    logger.info(f"Approved PRD {prd_id}")
    return result.data[0]


async def increment_prd_version(prd_id: str, new_content: str) -> Dict:
    """Create a new version of a PRD with updated content."""
    # Get current PRD
    current = await get_prd(prd_id)
    if not current:
        raise ValueError(f"PRD not found: {prd_id}")

    # Increment version and update content
    result = await asyncio.to_thread(
        lambda: supabase.table("disco_prds")
        .update(
            {
                "content_markdown": new_content,
                "version": current["version"] + 1,
                "status": "draft",  # Reset to draft for new version
                "approved_at": None,
                "approved_by": None,
            }
        )
        .eq("id", prd_id)
        .execute()
    )

    if not result.data:
        raise Exception("Failed to update PRD version")

    logger.info(f"Incremented PRD {prd_id} to version {current['version'] + 1}")
    return result.data[0]


# ============================================================================
# PROJECT EXTRACTION FROM PRD
# ============================================================================

PRD_PROJECT_EXTRACTION_PROMPT = """
Extract project creation fields from this PRD/document.

Document Title: {title}
Document Type: {output_type}

Document Content:
{content}

Return JSON with fields and confidence levels (high/medium/low/none):
- title: Project title (from document title or executive summary)
- description: 2-3 sentence summary from executive summary
- department: Infer from content (Engineering, Product, Marketing, Finance, Legal, HR, IT, RevOps, Operations, Sales)
- current_state: From problem statement or current situation section
- desired_state: From goals/success metrics or desired outcome section
- roi_potential: 1-5 score based on impact described (5 = very high ROI)
- implementation_effort: 1-5 score based on complexity (5 = easiest to implement)
- strategic_alignment: 1-5 score based on business value described (5 = highly aligned)
- stakeholder_readiness: 1-5 score based on stakeholder section (5 = very ready)

Also extract up to 5 tasks from requirements or next steps sections:
- tasks: Array of {{title, description, priority (high/medium/low)}}

Return ONLY valid JSON in this exact format:
{{
    "title": {{"value": "...", "confidence": "high|medium|low|none"}},
    "description": {{"value": "...", "confidence": "high|medium|low|none"}},
    "department": {{"value": "...", "confidence": "high|medium|low|none"}},
    "current_state": {{"value": "...", "confidence": "high|medium|low|none"}},
    "desired_state": {{"value": "...", "confidence": "high|medium|low|none"}},
    "roi_potential": {{"value": 1-5, "confidence": "high|medium|low|none"}},
    "implementation_effort": {{"value": 1-5, "confidence": "high|medium|low|none"}},
    "strategic_alignment": {{"value": 1-5, "confidence": "high|medium|low|none"}},
    "stakeholder_readiness": {{"value": 1-5, "confidence": "high|medium|low|none"}},
    "tasks": [
        {{"title": "...", "description": "...", "priority": "high|medium|low"}},
        ...
    ]
}}
"""


async def extract_project_from_prd(prd: Dict, initiative_id: str, initiative_name: str) -> Dict:
    """Extract project fields from PRD content using AI.

    Args:
        prd: The PRD record with content_markdown and content_structured
        initiative_id: Parent initiative ID
        initiative_name: Parent initiative name

    Returns:
        Dict with extracted_data, tasks, and source context
    """
    import json

    import anthropic

    from services.disco.agent_service import DISCO_MODEL_SONNET

    # Determine output type from structured content
    output_type = prd.get("content_structured", {}).get("output_type", "prd")
    output_type_label = OUTPUT_TYPE_CONFIG.get(output_type, {}).get("label", "Document")

    # Build prompt
    prompt = PRD_PROJECT_EXTRACTION_PROMPT.format(
        title=prd.get("title", "Untitled"),
        output_type=output_type_label,
        content=prd.get("content_markdown", "")[:15000],  # Limit content length
    )

    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model=DISCO_MODEL_SONNET,
            max_tokens=2000,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}],
        )

        # Parse JSON response
        response_text = response.content[0].text

        # Extract JSON from response (handle markdown code blocks)
        if "```json" in response_text:
            json_start = response_text.index("```json") + 7
            json_end = response_text.index("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.index("```") + 3
            json_end = response_text.index("```", json_start)
            response_text = response_text[json_start:json_end].strip()

        extracted = json.loads(response_text)

        # Build source context
        source_context = f"Created from {output_type_label}: {prd.get('title', 'Untitled')}"
        if prd.get("content_structured", {}).get("executive_summary"):
            summary = prd["content_structured"]["executive_summary"][:200]
            source_context += f"\n\nSummary: {summary}..."

        return {
            "extracted_data": {
                "title": extracted.get("title", {"value": None, "confidence": "none"}),
                "description": extracted.get("description", {"value": None, "confidence": "none"}),
                "department": extracted.get("department", {"value": None, "confidence": "none"}),
                "current_state": extracted.get("current_state", {"value": None, "confidence": "none"}),
                "desired_state": extracted.get("desired_state", {"value": None, "confidence": "none"}),
                "roi_potential": extracted.get("roi_potential", {"value": 3, "confidence": "none"}),
                "implementation_effort": extracted.get("implementation_effort", {"value": 3, "confidence": "none"}),
                "strategic_alignment": extracted.get("strategic_alignment", {"value": 3, "confidence": "none"}),
                "stakeholder_readiness": extracted.get("stakeholder_readiness", {"value": 3, "confidence": "none"}),
            },
            "tasks": extracted.get("tasks", []),
            "initiative_id": initiative_id,
            "initiative_name": initiative_name,
            "prd_id": prd.get("id"),
            "prd_title": prd.get("title"),
            "source_context": source_context,
        }

    except Exception as e:
        logger.error(f"Failed to extract project from PRD: {e}")
        # Return default values with low confidence
        return {
            "extracted_data": {
                "title": {"value": prd.get("title"), "confidence": "medium"},
                "description": {
                    "value": prd.get("content_structured", {}).get("executive_summary", "")[:500],
                    "confidence": "low",
                },
                "department": {"value": None, "confidence": "none"},
                "current_state": {"value": None, "confidence": "none"},
                "desired_state": {"value": None, "confidence": "none"},
                "roi_potential": {"value": 3, "confidence": "none"},
                "implementation_effort": {"value": 3, "confidence": "none"},
                "strategic_alignment": {"value": 3, "confidence": "none"},
                "stakeholder_readiness": {"value": 3, "confidence": "none"},
            },
            "tasks": [],
            "initiative_id": initiative_id,
            "initiative_name": initiative_name,
            "prd_id": prd.get("id"),
            "prd_title": prd.get("title"),
            "source_context": f"Created from document: {prd.get('title', 'Untitled')}",
        }


# ============================================================================
# OUTPUT TYPE SUGGESTION
# ============================================================================


async def suggest_output_type(bundle: Dict) -> Dict:
    """Use AI to suggest the appropriate output type based on bundle content.

    Args:
        bundle: The bundle record with name, description, and included_items

    Returns:
        Dict with suggested_type, confidence, and rationale
    """
    import anthropic

    from services.disco.agent_service import DISCO_MODEL_SONNET

    # Build context for analysis
    bundle_context = f"""Bundle Name: {bundle.get("name", "Unknown")}

Description: {bundle.get("description", "No description")}

Included Items:
"""
    for item in bundle.get("included_items", []):
        bundle_context += f"- {item.get('description', 'Unknown')}"
        if item.get("source"):
            bundle_context += f" (Source: {item['source']})"
        bundle_context += "\n"

    if bundle.get("bundling_rationale"):
        bundle_context += f"\nBundling Rationale: {bundle['bundling_rationale']}\n"

    prompt = f"""Analyze this initiative bundle and suggest the most appropriate output document type.

{bundle_context}

Available output types:
1. **prd** (Product Requirements Document): Best for build/development initiatives, feature implementations, system changes
2. **evaluation_framework**: Best for research/evaluation bundles, vendor/platform comparisons, tool selections
3. **decision_framework**: Best for governance decisions, policy changes, organizational strategy, stakeholder alignment

Respond in JSON format:
{{
    "suggested_type": "prd" | "evaluation_framework" | "decision_framework",
    "confidence": "high" | "medium" | "low",
    "rationale": "Brief explanation of why this output type is most appropriate"
}}

Consider:
- Does the bundle involve comparing options/vendors? -> evaluation_framework
- Does the bundle require stakeholder buy-in for a decision? -> decision_framework
- Does the bundle involve building/implementing something specific? -> prd
"""

    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model=DISCO_MODEL_SONNET,
            max_tokens=500,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}],
        )

        # Parse JSON response
        import json

        response_text = response.content[0].text
        # Extract JSON from response (handle markdown code blocks)
        if "```json" in response_text:
            json_start = response_text.index("```json") + 7
            json_end = response_text.index("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.index("```") + 3
            json_end = response_text.index("```", json_start)
            response_text = response_text[json_start:json_end].strip()

        result = json.loads(response_text)
        return {
            "suggested_type": result.get("suggested_type", "prd"),
            "confidence": result.get("confidence", "medium"),
            "rationale": result.get("rationale", "Based on bundle content analysis"),
        }

    except Exception as e:
        logger.warning(f"Failed to get AI suggestion, defaulting to PRD: {e}")
        return {
            "suggested_type": "prd",
            "confidence": "low",
            "rationale": "Unable to analyze bundle content; defaulting to PRD",
        }


# ============================================================================
# DOCUMENT GENERATION
# ============================================================================


async def generate_prd_for_bundle(
    bundle_id: str, initiative_id: str, user_id: str, output_type: str = "prd"
) -> AsyncGenerator[Dict, None]:
    """Generate a document for an approved bundle.

    Args:
        bundle_id: The approved bundle ID
        initiative_id: The parent initiative ID
        user_id: The user generating the document
        output_type: Type of document to generate (prd, evaluation_framework, decision_framework)

    Yields streaming events:
    - status: Progress updates
    - content: Streaming markdown content
    - complete: Final document record
    - error: Error message
    """
    import anthropic

    from services.disco.agent_service import (
        DISCO_MODEL_OPUS,
        build_agent_context,
        load_agent_prompt,
    )
    from services.disco.synthesis_service import get_bundle

    # Validate output type
    if output_type not in OUTPUT_TYPE_CONFIG:
        yield {"type": "error", "data": f"Invalid output type: {output_type}"}
        return

    config = OUTPUT_TYPE_CONFIG[output_type]

    # Verify bundle is approved
    bundle = await get_bundle(bundle_id)
    if not bundle:
        yield {"type": "error", "data": "Bundle not found"}
        return

    if bundle["status"] != "approved":
        yield {"type": "error", "data": f"Bundle must be approved (current: {bundle['status']})"}
        return

    yield {"type": "status", "data": f"Loading {config['label']} generator..."}

    # Load agent prompt for the appropriate output type
    try:
        agent_prompt = load_agent_prompt(config["agent_prompt"])
    except Exception as e:
        yield {"type": "error", "data": f"Failed to load generator: {e}"}
        return

    yield {"type": "status", "data": "Building context..."}

    # Build context from initiative
    context = await build_agent_context(initiative_id, "prd_generator")

    # Add bundle-specific context
    bundle_context = f"""
## Initiative Bundle: {bundle["name"]}

**Description**: {bundle["description"]}

**Scores**:
- Impact: {bundle["impact_score"]} - {bundle.get("impact_rationale", "N/A")}
- Feasibility: {bundle["feasibility_score"]} - {bundle.get("feasibility_rationale", "N/A")}
- Urgency: {bundle["urgency_score"]} - {bundle.get("urgency_rationale", "N/A")}

**Complexity Tier**: {bundle.get("complexity_tier", "Not specified")}

**Included Items**:
"""
    for item in bundle.get("included_items", []):
        bundle_context += f"- {item.get('description', 'Unknown')}"
        if item.get("source"):
            bundle_context += f" (Source: {item['source']})"
        bundle_context += "\n"

    bundle_context += "\n**Stakeholders**:\n"
    for s in bundle.get("stakeholders", []):
        bundle_context += f"- {s.get('name', 'Unknown')}: {s.get('stake', 'N/A')}\n"

    if bundle.get("bundling_rationale"):
        bundle_context += f"\n**Bundling Rationale**: {bundle['bundling_rationale']}\n"

    # Build full prompt
    full_prompt = f"""# PRD Generation Task

You are generating a PRD (Product Requirements Document) for an approved initiative bundle.

## Agent Instructions

{agent_prompt}

## Initiative Bundle Context

{bundle_context}

## Discovery Context

{context}

---

Please generate a complete PRD following the structure defined in your instructions.
"""

    yield {"type": "status", "data": "Generating PRD with Claude..."}

    # Stream from Claude
    client = anthropic.Anthropic()
    full_content = ""

    try:
        with client.messages.stream(
            model=DISCO_MODEL_OPUS,
            max_tokens=8000,
            temperature=0.6,
            messages=[{"role": "user", "content": full_prompt}],
        ) as stream:
            for text in stream.text_stream:
                full_content += text
                yield {"type": "content", "data": text}

    except Exception as e:
        logger.error(f"PRD generation failed: {e}")
        yield {"type": "error", "data": str(e)}
        return

    yield {"type": "status", "data": f"Saving {config['label']}..."}

    # Extract title from content
    title = extract_prd_title(full_content) or bundle["name"]

    # Parse structured sections using the appropriate parser
    section_parser = get_section_parser(output_type)
    structured = section_parser(full_content)

    # Create PRD record
    try:
        # Create output record first
        output_id = str(uuid4())
        await asyncio.to_thread(
            lambda: supabase.table("disco_outputs")
            .insert(
                {
                    "id": output_id,
                    "run_id": str(uuid4()),  # Standalone PRD generation
                    "initiative_id": initiative_id,
                    "agent_type": "prd_generator",
                    "version": 1,
                    "content_markdown": full_content,
                    "content_structured": structured,
                    "title": title,
                    "recommendation": None,
                    "tier_routing": None,
                    "confidence_level": None,
                    "executive_summary": structured.get("executive_summary"),
                }
            )
            .execute()
        )

        # Create PRD record
        prd = await create_prd(
            bundle_id=bundle_id,
            initiative_id=initiative_id,
            title=title,
            content_markdown=full_content,
            content_structured=structured,
            source_output_id=output_id,
        )

        yield {"type": "complete", "data": prd}

    except Exception as e:
        logger.error(f"Failed to save PRD: {e}")
        yield {"type": "error", "data": f"Failed to save PRD: {e}"}


def extract_prd_title(content: str) -> Optional[str]:
    """Extract the PRD title from markdown content."""
    # Look for first h1
    match = re.search(r"^#\s+(.+?)(?:\s*-\s*Product Requirements Document)?$", content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return None


def parse_prd_sections(content: str) -> Dict:
    """Parse PRD content into structured sections."""
    sections = {"output_type": "prd"}

    # Extract executive summary
    exec_match = re.search(r"## Executive Summary\s*\n(.+?)(?=\n## |$)", content, re.DOTALL)
    if exec_match:
        sections["executive_summary"] = exec_match.group(1).strip()

    # Extract problem statement
    problem_match = re.search(r"## Problem Statement\s*\n(.+?)(?=\n## |$)", content, re.DOTALL)
    if problem_match:
        sections["problem_statement"] = problem_match.group(1).strip()

    # Extract requirements
    req_match = re.search(r"## Requirements\s*\n(.+?)(?=\n## |$)", content, re.DOTALL)
    if req_match:
        sections["requirements"] = req_match.group(1).strip()

    # Extract technical considerations
    tech_match = re.search(r"## Technical Considerations\s*\n(.+?)(?=\n## |$)", content, re.DOTALL)
    if tech_match:
        sections["technical_considerations"] = tech_match.group(1).strip()

    # Extract risks
    risk_match = re.search(r"## Risks & Dependencies\s*\n(.+?)(?=\n## |$)", content, re.DOTALL)
    if risk_match:
        sections["risks"] = risk_match.group(1).strip()

    return sections


def parse_evaluation_sections(content: str) -> Dict:
    """Parse Evaluation Framework content into structured sections."""
    sections = {"output_type": "evaluation_framework"}

    # Extract executive summary
    exec_match = re.search(r"## Executive Summary\s*\n(.+?)(?=\n## |$)", content, re.DOTALL)
    if exec_match:
        sections["executive_summary"] = exec_match.group(1).strip()

    # Extract evaluation scope
    scope_match = re.search(r"## Evaluation Scope & Objectives\s*\n(.+?)(?=\n## |$)", content, re.DOTALL)
    if scope_match:
        sections["evaluation_scope"] = scope_match.group(1).strip()

    # Extract weighted criteria matrix
    criteria_match = re.search(r"## Weighted Criteria Matrix\s*\n(.+?)(?=\n## |$)", content, re.DOTALL)
    if criteria_match:
        sections["criteria_matrix"] = criteria_match.group(1).strip()

    # Extract platform comparison
    comparison_match = re.search(r"## Platform/Option Comparison\s*\n(.+?)(?=\n## |$)", content, re.DOTALL)
    if comparison_match:
        sections["comparison_table"] = comparison_match.group(1).strip()

    # Extract recommendation
    rec_match = re.search(r"## Recommendation\s*\n(.+?)(?=\n## |$)", content, re.DOTALL)
    if rec_match:
        sections["recommendation"] = rec_match.group(1).strip()

    # Extract next steps
    next_match = re.search(r"## Next Steps\s*\n(.+?)(?=\n## |$)", content, re.DOTALL)
    if next_match:
        sections["next_steps"] = next_match.group(1).strip()

    return sections


def parse_decision_sections(content: str) -> Dict:
    """Parse Decision Framework content into structured sections."""
    sections = {"output_type": "decision_framework"}

    # Extract executive summary
    exec_match = re.search(r"## Executive Summary\s*\n(.+?)(?=\n## |$)", content, re.DOTALL)
    if exec_match:
        sections["executive_summary"] = exec_match.group(1).strip()

    # Extract decision context
    context_match = re.search(r"## Decision Context & Background\s*\n(.+?)(?=\n## |$)", content, re.DOTALL)
    if context_match:
        sections["decision_context"] = context_match.group(1).strip()

    # Extract stakeholder analysis
    stakeholder_match = re.search(r"## Stakeholder Analysis\s*\n(.+?)(?=\n## |$)", content, re.DOTALL)
    if stakeholder_match:
        sections["stakeholders"] = stakeholder_match.group(1).strip()

    # Extract decision criteria
    criteria_match = re.search(r"## Decision Criteria\s*\n(.+?)(?=\n## |$)", content, re.DOTALL)
    if criteria_match:
        sections["decision_criteria"] = criteria_match.group(1).strip()

    # Extract options analysis
    options_match = re.search(r"## Options Analysis\s*\n(.+?)(?=\n## |$)", content, re.DOTALL)
    if options_match:
        sections["options_analysis"] = options_match.group(1).strip()

    # Extract risk/benefit assessment
    risk_match = re.search(r"## Risk/Benefit Assessment\s*\n(.+?)(?=\n## |$)", content, re.DOTALL)
    if risk_match:
        sections["risk_benefit"] = risk_match.group(1).strip()

    # Extract recommendation
    rec_match = re.search(r"## Recommendation\s*\n(.+?)(?=\n## |$)", content, re.DOTALL)
    if rec_match:
        sections["recommendation"] = rec_match.group(1).strip()

    # Extract implementation considerations
    impl_match = re.search(r"## Implementation Considerations\s*\n(.+?)(?=\n## |$)", content, re.DOTALL)
    if impl_match:
        sections["implementation"] = impl_match.group(1).strip()

    return sections


def get_section_parser(output_type: str):
    """Get the appropriate section parser for an output type."""
    parsers = {
        "prd": parse_prd_sections,
        "evaluation_framework": parse_evaluation_sections,
        "decision_framework": parse_decision_sections,
    }
    return parsers.get(output_type, parse_prd_sections)


# ============================================================================
# EXECUTIVE SUMMARY GENERATION
# ============================================================================


async def generate_executive_summary(initiative_id: str, user_id: str) -> AsyncGenerator[Dict, None]:
    """Generate an executive summary document across all approved bundles/PRDs.

    This creates a high-level overview suitable for leadership review.
    """
    import anthropic

    from services.disco.agent_service import DISCO_MODEL_OPUS
    from services.disco.synthesis_service import list_bundles

    yield {"type": "status", "data": "Loading initiative data..."}

    # Get initiative
    result = await asyncio.to_thread(
        lambda: supabase.table("disco_initiatives").select("*").eq("id", initiative_id).single().execute()
    )
    initiative = result.data
    if not initiative:
        yield {"type": "error", "data": "Initiative not found"}
        return

    # Get all bundles
    bundles = await list_bundles(initiative_id)
    approved_bundles = [b for b in bundles if b["status"] == "approved"]

    if not approved_bundles:
        yield {"type": "error", "data": "No approved bundles found"}
        return

    # Get PRDs
    prds = await list_prds(initiative_id)
    prd_map = {p["bundle_id"]: p for p in prds}

    yield {"type": "status", "data": "Generating executive summary..."}

    # Build context for summary
    context = f"""# Executive Summary Generation

## Initiative: {initiative["name"]}

**Description**: {initiative.get("description", "No description")}

## Approved Initiative Bundles

"""
    for i, bundle in enumerate(approved_bundles, 1):
        context += f"""
### Bundle {i}: {bundle["name"]}

**Description**: {bundle["description"]}
**Impact**: {bundle["impact_score"]} | **Feasibility**: {bundle["feasibility_score"]} | **Urgency**: {bundle["urgency_score"]}
**Complexity**: {bundle.get("complexity_tier", "Not specified")}

"""
        # Include PRD executive summary if available
        prd = prd_map.get(bundle["id"])
        if prd and prd.get("content_structured", {}).get("executive_summary"):
            context += f"**PRD Executive Summary**:\n{prd['content_structured']['executive_summary']}\n\n"

    context += """
---

## Instructions

Create a high-level executive summary document that:

1. Summarizes the overall discovery findings
2. Lists all initiatives with their priority rationale
3. Provides resource implications overview
4. Recommends prioritization and phasing
5. Identifies key decision points for leadership

Keep it to 500-750 words. Focus on business value and strategic implications.

## Output Format

```markdown
# [Initiative Name] - Executive Summary

## Discovery Overview
[2-3 paragraphs on what was discovered]

## Initiatives Identified

| Initiative | Impact | Feasibility | Urgency | Status |
|------------|--------|-------------|---------|--------|
| ... | ... | ... | ... | ... |

## Recommended Prioritization
1. **[Initiative]** - [Rationale]
2. **[Initiative]** - [Rationale]
...

## Resource Implications
[High-level view of what's needed]

## Key Decision Points
1. [Decision needed]
2. [Decision needed]

## Next Steps
- [Actionable recommendation]
- [Actionable recommendation]
```
"""

    # Stream from Claude
    client = anthropic.Anthropic()
    full_content = ""

    try:
        with client.messages.stream(
            model=DISCO_MODEL_OPUS,
            max_tokens=4000,
            temperature=0.5,
            messages=[{"role": "user", "content": context}],
        ) as stream:
            for text in stream.text_stream:
                full_content += text
                yield {"type": "content", "data": text}

        yield {"type": "complete", "data": {"content": full_content}}

    except Exception as e:
        logger.error(f"Executive summary generation failed: {e}")
        yield {"type": "error", "data": str(e)}
