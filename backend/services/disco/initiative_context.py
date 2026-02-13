"""Initiative Context Builder.

Builds XML context for the Discovery Agent by fetching initiative metadata,
throughline, agent outputs, linked documents, and value alignment from Supabase.
Follows the same pattern as services/project_context.py build_project_context().
"""

import json
from typing import Dict, Optional

from database import get_supabase
from logger_config import get_logger

logger = get_logger(__name__)


async def build_initiative_context(initiative_id: str, user_id: str) -> str:
    """Build XML context string for a DISCO initiative.

    Fetches initiative metadata, throughline, latest agent outputs,
    linked documents, and value alignment. Returns formatted XML
    for injection into the Discovery Agent's user prompt.

    Args:
        initiative_id: UUID of the initiative
        user_id: UUID of the requesting user

    Returns:
        Formatted XML context string
    """
    supabase = get_supabase()
    parts = ["<initiative_context>"]

    # 1. Initiative metadata + throughline
    try:
        init_result = (
            supabase.table("disco_initiatives")
            .select("name, description, status, target_department, throughline, value_alignment, brief")
            .eq("id", initiative_id)
            .single()
            .execute()
        )
        init_data = init_result.data if init_result.data else {}
    except Exception as e:
        logger.warning(f"Failed to fetch initiative {initiative_id}: {e}")
        init_data = {}

    if not init_data:
        return "<initiative_context>Initiative not found.</initiative_context>"

    parts.append(f"<name>{init_data.get('name', 'Unknown')}</name>")
    if init_data.get("description"):
        parts.append(f"<description>{init_data['description']}</description>")
    if init_data.get("brief"):
        parts.append(f"<brief>{init_data['brief'][:500]}</brief>")
    parts.append(f"<status>{init_data.get('status', 'draft')}</status>")
    if init_data.get("target_department"):
        parts.append(f"<department>{init_data['target_department']}</department>")

    # 2. Throughline (structured framing)
    throughline = init_data.get("throughline")
    if throughline:
        parts.append("<current_throughline>")
        if isinstance(throughline, str):
            try:
                throughline = json.loads(throughline)
            except json.JSONDecodeError:
                throughline = {}

        ps = throughline.get("problem_statements", [])
        if ps:
            parts.append("  <problem_statements>")
            for item in ps:
                item_id = item.get("id", "")
                parts.append(f'    <statement id="{item_id}">{item.get("text", "")}</statement>')
            parts.append("  </problem_statements>")

        hyps = throughline.get("hypotheses", [])
        if hyps:
            parts.append("  <hypotheses>")
            for item in hyps:
                item_id = item.get("id", "")
                h_type = item.get("type", "assumption")
                parts.append(f'    <hypothesis id="{item_id}" type="{h_type}">')
                parts.append(f"      {item.get('statement', '')}")
                if item.get("rationale"):
                    parts.append(f"      Rationale: {item['rationale']}")
                parts.append("    </hypothesis>")
            parts.append("  </hypotheses>")

        gaps = throughline.get("gaps", [])
        if gaps:
            parts.append("  <gaps>")
            for item in gaps:
                item_id = item.get("id", "")
                g_type = item.get("type", "data")
                parts.append(f'    <gap id="{item_id}" type="{g_type}">{item.get("description", "")}</gap>')
            parts.append("  </gaps>")

        dos = throughline.get("desired_outcome_state")
        if dos:
            parts.append(f"  <desired_outcome_state>{dos}</desired_outcome_state>")

        parts.append("</current_throughline>")
    else:
        parts.append("<current_throughline>No framing defined yet.</current_throughline>")

    # 3. Value alignment
    value_alignment = init_data.get("value_alignment")
    if value_alignment:
        if isinstance(value_alignment, str):
            try:
                value_alignment = json.loads(value_alignment)
            except json.JSONDecodeError:
                value_alignment = {}
        if value_alignment:
            parts.append("<value_alignment>")
            for key, val in value_alignment.items():
                if val:
                    parts.append(f"  <{key}>{val}</{key}>")
            parts.append("</value_alignment>")

    # 4. Latest agent output summaries (recommendation + confidence only to save tokens)
    try:
        outputs_result = (
            supabase.table("disco_outputs")
            .select("agent_name, recommendation, confidence, status, created_at")
            .eq("initiative_id", initiative_id)
            .order("created_at", desc=True)
            .limit(20)
            .execute()
        )
        outputs = outputs_result.data if outputs_result.data else []
    except Exception as e:
        logger.warning(f"Failed to fetch agent outputs for {initiative_id}: {e}")
        outputs = []

    if outputs:
        # Deduplicate: keep latest per agent
        seen_agents = set()
        unique_outputs = []
        for out in outputs:
            agent = out.get("agent_name", "")
            if agent not in seen_agents:
                seen_agents.add(agent)
                unique_outputs.append(out)

        parts.append("<agent_outputs>")
        for out in unique_outputs:
            agent = out.get("agent_name", "unknown")
            rec = out.get("recommendation", "")
            conf = out.get("confidence", "")
            status = out.get("status", "")
            # Truncate recommendation to ~200 chars to stay within token budget
            if rec and len(rec) > 200:
                rec = rec[:200] + "..."
            parts.append(f'  <output agent="{agent}" confidence="{conf}" status="{status}">')
            parts.append(f"    {rec}")
            parts.append("  </output>")
        parts.append("</agent_outputs>")
    else:
        parts.append("<agent_outputs>No agent analyses have been run yet.</agent_outputs>")

    # 5. Linked document names
    try:
        docs_result = (
            supabase.table("disco_initiative_documents")
            .select("document_id, documents(id, title, filename, folder)")
            .eq("initiative_id", initiative_id)
            .limit(30)
            .execute()
        )
        linked_docs = docs_result.data if docs_result.data else []
    except Exception as e:
        logger.warning(f"Failed to fetch linked documents for {initiative_id}: {e}")
        linked_docs = []

    if linked_docs:
        parts.append("<linked_documents>")
        for doc_link in linked_docs:
            doc = doc_link.get("documents", {})
            if doc:
                title = doc.get("title") or doc.get("filename", "Unknown")
                folder = doc.get("folder", "")
                folder_str = f' folder="{folder}"' if folder else ""
                parts.append(f"  <document{folder_str}>{title}</document>")
        parts.append("</linked_documents>")
    else:
        parts.append("<linked_documents>No documents linked yet.</linked_documents>")

    parts.append("</initiative_context>")

    context = "\n".join(parts)
    logger.info(
        f"Built initiative context for {initiative_id}: "
        f"{len(context)} chars, {len(outputs)} outputs, {len(linked_docs)} docs"
    )
    return context
