"""DISCo PRD Service.

Handles the Convergence stage of the DISCo pipeline:
- Generating PRDs from approved bundles
- Managing PRD lifecycle (draft -> review -> approved -> exported)
- Generating executive summaries across multiple PRDs

The Convergence stage transforms approved initiative bundles into
actionable PRD documents ready for engineering implementation.
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
# PRD GENERATION
# ============================================================================


async def generate_prd_for_bundle(bundle_id: str, initiative_id: str, user_id: str) -> AsyncGenerator[Dict, None]:
    """Generate a PRD for an approved bundle.

    Yields streaming events:
    - status: Progress updates
    - content: Streaming markdown content
    - complete: Final PRD record
    - error: Error message
    """
    import anthropic

    from services.disco.agent_service import (
        DISCO_MODEL_OPUS,
        build_agent_context,
        load_agent_prompt,
    )
    from services.disco.synthesis_service import get_bundle

    # Verify bundle is approved
    bundle = await get_bundle(bundle_id)
    if not bundle:
        yield {"type": "error", "data": "Bundle not found"}
        return

    if bundle["status"] != "approved":
        yield {"type": "error", "data": f"Bundle must be approved (current: {bundle['status']})"}
        return

    yield {"type": "status", "data": "Loading PRD generator..."}

    # Load agent prompt
    try:
        agent_prompt = load_agent_prompt("prd_generator")
    except Exception as e:
        yield {"type": "error", "data": f"Failed to load PRD generator: {e}"}
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

    yield {"type": "status", "data": "Saving PRD..."}

    # Extract title from content
    title = extract_prd_title(full_content) or bundle["name"]

    # Parse structured sections
    structured = parse_prd_sections(full_content)

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
    sections = {}

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
