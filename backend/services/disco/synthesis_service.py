"""DISCo Synthesis Service.

Handles the Synthesis stage of the DISCo pipeline:
- Running the synthesis agent to propose initiative bundles
- Managing bundles (CRUD, approve/reject)
- Tracking bundle feedback

The Synthesis stage transforms consolidated insights into actionable
initiative bundles with human checkpoints for review and approval.
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4

from database import get_supabase
from logger_config import get_logger

logger = get_logger(__name__)
supabase = get_supabase()


# ============================================================================
# BUNDLE MANAGEMENT
# ============================================================================


async def create_bundle(
    initiative_id: str,
    name: str,
    description: str,
    impact_score: Optional[str] = None,
    impact_rationale: Optional[str] = None,
    feasibility_score: Optional[str] = None,
    feasibility_rationale: Optional[str] = None,
    urgency_score: Optional[str] = None,
    urgency_rationale: Optional[str] = None,
    complexity_tier: Optional[str] = None,
    complexity_rationale: Optional[str] = None,
    included_items: Optional[List[Dict]] = None,
    stakeholders: Optional[List[Dict]] = None,
    dependencies: Optional[Dict] = None,
    bundling_rationale: Optional[str] = None,
    source_output_id: Optional[str] = None,
) -> Dict:
    """Create a new initiative bundle."""
    bundle_id = str(uuid4())

    bundle_data = {
        "id": bundle_id,
        "initiative_id": initiative_id,
        "name": name,
        "description": description,
        "status": "proposed",
        "impact_score": impact_score,
        "impact_rationale": impact_rationale,
        "feasibility_score": feasibility_score,
        "feasibility_rationale": feasibility_rationale,
        "urgency_score": urgency_score,
        "urgency_rationale": urgency_rationale,
        "complexity_tier": complexity_tier,
        "complexity_rationale": complexity_rationale,
        "included_items": included_items or [],
        "stakeholders": stakeholders or [],
        "dependencies": dependencies or {},
        "bundling_rationale": bundling_rationale,
        "source_output_id": source_output_id,
    }

    result = await asyncio.to_thread(
        lambda: supabase.table("disco_bundles").insert(bundle_data).execute()
    )

    if not result.data:
        raise Exception("Failed to create bundle")

    logger.info(f"Created bundle {bundle_id} for initiative {initiative_id}: {name}")
    return result.data[0]


async def get_bundle(bundle_id: str) -> Optional[Dict]:
    """Get a bundle by ID."""
    result = await asyncio.to_thread(
        lambda: supabase.table("disco_bundles").select("*").eq("id", bundle_id).single().execute()
    )
    return result.data


async def list_bundles(initiative_id: str, status: Optional[str] = None) -> List[Dict]:
    """List bundles for an initiative."""
    query = supabase.table("disco_bundles").select("*").eq("initiative_id", initiative_id)

    if status:
        query = query.eq("status", status)

    query = query.order("created_at", desc=False)

    result = await asyncio.to_thread(lambda: query.execute())
    return result.data or []


async def update_bundle(
    bundle_id: str, updates: Dict, user_id: str, feedback: Optional[str] = None
) -> Dict:
    """Update a bundle and optionally record feedback.

    Args:
        bundle_id: Bundle UUID
        updates: Dict of fields to update
        user_id: User making the update
        feedback: Optional feedback text

    Returns:
        Updated bundle record
    """
    # Remove any fields that shouldn't be updated directly
    safe_updates = {
        k: v for k, v in updates.items() if k not in ["id", "initiative_id", "created_at"]
    }

    result = await asyncio.to_thread(
        lambda: supabase.table("disco_bundles").update(safe_updates).eq("id", bundle_id).execute()
    )

    if not result.data:
        raise ValueError(f"Bundle not found: {bundle_id}")

    # Record feedback if provided
    if feedback:
        await record_bundle_feedback(
            bundle_id=bundle_id,
            user_id=user_id,
            action="edit",
            feedback=feedback,
            changes=safe_updates,
        )

    logger.info(f"Updated bundle {bundle_id}")
    return result.data[0]


async def approve_bundle(bundle_id: str, user_id: str, feedback: Optional[str] = None) -> Dict:
    """Approve a bundle for PRD generation."""
    result = await asyncio.to_thread(
        lambda: supabase.table("disco_bundles")
        .update(
            {
                "status": "approved",
                "approved_at": datetime.now(timezone.utc).isoformat(),
                "approved_by": user_id,
            }
        )
        .eq("id", bundle_id)
        .execute()
    )

    if not result.data:
        raise ValueError(f"Bundle not found: {bundle_id}")

    # Record approval feedback
    await record_bundle_feedback(
        bundle_id=bundle_id,
        user_id=user_id,
        action="approve",
        feedback=feedback or "Approved for PRD generation",
    )

    logger.info(f"Approved bundle {bundle_id}")
    return result.data[0]


async def reject_bundle(bundle_id: str, user_id: str, feedback: str) -> Dict:
    """Reject a bundle (won't proceed to PRD)."""
    result = await asyncio.to_thread(
        lambda: supabase.table("disco_bundles")
        .update({"status": "rejected"})
        .eq("id", bundle_id)
        .execute()
    )

    if not result.data:
        raise ValueError(f"Bundle not found: {bundle_id}")

    # Record rejection feedback
    await record_bundle_feedback(
        bundle_id=bundle_id, user_id=user_id, action="reject", feedback=feedback
    )

    logger.info(f"Rejected bundle {bundle_id}")
    return result.data[0]


async def merge_bundles(
    bundle_ids: List[str],
    merged_name: str,
    merged_description: str,
    user_id: str,
    feedback: Optional[str] = None,
) -> Dict:
    """Merge multiple bundles into a new one.

    Original bundles are marked as 'merged' and a new bundle is created.
    """
    if len(bundle_ids) < 2:
        raise ValueError("Need at least 2 bundles to merge")

    # Get all bundles to merge
    bundles = []
    for bid in bundle_ids:
        bundle = await get_bundle(bid)
        if not bundle:
            raise ValueError(f"Bundle not found: {bid}")
        bundles.append(bundle)

    # Ensure all bundles are from same initiative
    initiative_ids = {b["initiative_id"] for b in bundles}
    if len(initiative_ids) > 1:
        raise ValueError("Cannot merge bundles from different initiatives")

    initiative_id = bundles[0]["initiative_id"]

    # Combine included items
    all_items = []
    for b in bundles:
        all_items.extend(b.get("included_items", []))

    # Combine stakeholders
    all_stakeholders = []
    seen_stakeholders = set()
    for b in bundles:
        for s in b.get("stakeholders", []):
            key = s.get("name", "")
            if key not in seen_stakeholders:
                all_stakeholders.append(s)
                seen_stakeholders.add(key)

    # Create merged bundle
    merged_bundle = await create_bundle(
        initiative_id=initiative_id,
        name=merged_name,
        description=merged_description,
        included_items=all_items,
        stakeholders=all_stakeholders,
        bundling_rationale=f"Merged from: {', '.join(b['name'] for b in bundles)}",
    )

    # Mark original bundles as merged
    for bid in bundle_ids:
        await asyncio.to_thread(
            lambda b=bid: supabase.table("disco_bundles")
            .update({"status": "merged"})
            .eq("id", b)
            .execute()
        )
        await record_bundle_feedback(
            bundle_id=bid,
            user_id=user_id,
            action="merge",
            feedback=f"Merged into bundle: {merged_bundle['id']}",
        )

    # Record creation feedback
    await record_bundle_feedback(
        bundle_id=merged_bundle["id"],
        user_id=user_id,
        action="merge",
        feedback=feedback or f"Created by merging {len(bundles)} bundles",
    )

    logger.info(f"Merged {len(bundles)} bundles into {merged_bundle['id']}")
    return merged_bundle


async def split_bundle(
    bundle_id: str, split_definitions: List[Dict], user_id: str, feedback: Optional[str] = None
) -> List[Dict]:
    """Split a bundle into multiple new bundles.

    Args:
        bundle_id: Original bundle to split
        split_definitions: List of dicts with name, description, item_indices
        user_id: User performing the split
        feedback: Optional feedback text

    Returns:
        List of newly created bundles
    """
    original = await get_bundle(bundle_id)
    if not original:
        raise ValueError(f"Bundle not found: {bundle_id}")

    original_items = original.get("included_items", [])
    new_bundles = []

    for defn in split_definitions:
        # Get items for this split
        indices = defn.get("item_indices", [])
        items = [original_items[i] for i in indices if i < len(original_items)]

        new_bundle = await create_bundle(
            initiative_id=original["initiative_id"],
            name=defn["name"],
            description=defn.get("description", ""),
            included_items=items,
            bundling_rationale=f"Split from: {original['name']}",
        )
        new_bundles.append(new_bundle)

    # Mark original as merged (effectively replaced)
    await asyncio.to_thread(
        lambda: supabase.table("disco_bundles")
        .update({"status": "merged"})
        .eq("id", bundle_id)
        .execute()
    )

    await record_bundle_feedback(
        bundle_id=bundle_id,
        user_id=user_id,
        action="split",
        feedback=feedback or f"Split into {len(new_bundles)} bundles",
    )

    logger.info(f"Split bundle {bundle_id} into {len(new_bundles)} bundles")
    return new_bundles


# ============================================================================
# FEEDBACK TRACKING
# ============================================================================


async def record_bundle_feedback(
    bundle_id: str,
    user_id: str,
    action: str,
    feedback: Optional[str] = None,
    changes: Optional[Dict] = None,
) -> Dict:
    """Record feedback or action on a bundle."""
    feedback_data = {
        "id": str(uuid4()),
        "bundle_id": bundle_id,
        "user_id": user_id,
        "action": action,
        "feedback": feedback,
        "changes": changes,
    }

    result = await asyncio.to_thread(
        lambda: supabase.table("disco_bundle_feedback").insert(feedback_data).execute()
    )

    if not result.data:
        raise Exception("Failed to record feedback")

    return result.data[0]


async def get_bundle_feedback(bundle_id: str) -> List[Dict]:
    """Get all feedback for a bundle."""
    result = await asyncio.to_thread(
        lambda: supabase.table("disco_bundle_feedback")
        .select("*, users(email)")
        .eq("bundle_id", bundle_id)
        .order("created_at", desc=False)
        .execute()
    )
    return result.data or []


# ============================================================================
# BUNDLE PARSING (from Synthesis agent output)
# ============================================================================


def parse_synthesis_output(content_markdown: str, output_id: str) -> List[Dict]:
    """Parse synthesis agent output to extract bundle definitions.

    This is a heuristic parser that extracts bundle information from
    the structured markdown output of the synthesis agent.

    Returns list of bundle dicts ready for create_bundle().
    """
    import re

    bundles = []

    # Find all bundle sections (### Bundle N: Name)
    bundle_pattern = r"### Bundle \d+: (.+?)(?=### Bundle|\Z|## Items Not Bundled|## Dependency Map|## Recommendations)"
    bundle_matches = re.findall(bundle_pattern, content_markdown, re.DOTALL)

    for _i, match in enumerate(bundle_matches, 1):
        lines = match.strip().split("\n")
        if not lines:
            continue

        bundle_name = lines[0].strip()

        # Extract description (usually follows **Description**:)
        desc_match = re.search(r"\*\*Description\*\*:\s*(.+?)(?=\n\*\*|\n\||\Z)", match, re.DOTALL)
        description = desc_match.group(1).strip() if desc_match else ""

        # Extract scores
        impact = _extract_score(match, "Impact")
        feasibility = _extract_score(match, "Feasibility")
        urgency = _extract_score(match, "Urgency")

        # Extract complexity tier
        tier_match = re.search(
            r"\*\*Complexity Tier\*\*:\s*(Light|Medium|Heavy)", match, re.IGNORECASE
        )
        complexity = tier_match.group(1) if tier_match else None

        # Extract included items
        items = _extract_included_items(match)

        # Extract stakeholders
        stakeholders = _extract_stakeholders(match)

        # Extract rationale
        rationale_match = re.search(
            r"\*\*Rationale for Bundling\*\*:\s*(.+?)(?=\n---|\n###|\Z)", match, re.DOTALL
        )
        rationale = rationale_match.group(1).strip() if rationale_match else None

        bundles.append(
            {
                "name": bundle_name,
                "description": description,
                "impact_score": impact.get("score"),
                "impact_rationale": impact.get("rationale"),
                "feasibility_score": feasibility.get("score"),
                "feasibility_rationale": feasibility.get("rationale"),
                "urgency_score": urgency.get("score"),
                "urgency_rationale": urgency.get("rationale"),
                "complexity_tier": complexity,
                "included_items": items,
                "stakeholders": stakeholders,
                "bundling_rationale": rationale,
                "source_output_id": output_id,
            }
        )

    logger.info(f"Parsed {len(bundles)} bundles from synthesis output")
    return bundles


def _extract_score(text: str, dimension: str) -> Dict:
    """Extract score and rationale for a dimension."""
    pattern = rf"\|\s*{dimension}\s*\|\s*(HIGH|MEDIUM|LOW)\s*\|\s*(.+?)\s*\|"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return {"score": match.group(1).upper(), "rationale": match.group(2).strip()}
    return {}


def _extract_included_items(text: str) -> List[Dict]:
    """Extract included items from bundle text."""
    import re

    items = []

    # Look for items section
    items_match = re.search(r"\*\*Included Items\*\*:\s*\n(.+?)(?=\n\*\*|\n\||\Z)", text, re.DOTALL)
    if items_match:
        items_text = items_match.group(1)
        # Parse bullet points
        for line in items_text.split("\n"):
            line = line.strip()
            if line.startswith("- "):
                item_text = line[2:]
                # Try to extract source
                source_match = re.search(r"-\s*source:\s*(.+)$", item_text)
                if source_match:
                    item_text = item_text[: source_match.start()].strip()
                    source = source_match.group(1).strip()
                else:
                    source = None

                items.append({"description": item_text, "source": source})

    return items


def _extract_stakeholders(text: str) -> List[Dict]:
    """Extract stakeholders from bundle text."""
    import re

    stakeholders = []

    # Look for stakeholders section
    stakeholders_match = re.search(
        r"\*\*Affected Stakeholders\*\*:\s*\n(.+?)(?=\n\*\*|\n\||\Z)", text, re.DOTALL
    )
    if stakeholders_match:
        stakeholders_text = stakeholders_match.group(1)
        # Parse bullet points
        for line in stakeholders_text.split("\n"):
            line = line.strip()
            if line.startswith("- "):
                parts = line[2:].split(" - ", 1)
                stakeholders.append(
                    {"name": parts[0].strip(), "stake": parts[1].strip() if len(parts) > 1 else ""}
                )

    return stakeholders


# Need to import re at module level
import re
