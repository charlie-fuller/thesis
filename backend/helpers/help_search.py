"""Help documentation search module.

Handles vector search and RAG over help documentation.
"""

from typing import Dict, List

import pb_client as pb
import vec_client
from logger_config import get_logger
from repositories import help_repo
from services.embeddings import create_embedding

logger = get_logger(__name__)


def search_help_chunks(query: str, user_role: str, top_k: int = 3) -> tuple[List[Dict], str]:
    """Search help chunks via vector similarity.

    Args:
        query: Search query
        user_role: User's role (for access control)
        top_k: Number of results to return

    Returns:
        Tuple of (help_chunks, context_string)
    """
    # Step 1: Generate query embedding
    query_embedding = create_embedding(query, input_type="query")

    # Step 2: Search help chunks - try Pinecone first, fall back to vec_client
    from services.pinecone_service import get_index, query_vectors

    chunks_data = []

    if get_index() is not None:
        pc_filter = None
        if user_role:
            pc_filter = {"role_access": {"$eq": user_role}}

        matches = query_vectors(
            embedding=query_embedding,
            namespace="help_chunks",
            top_k=top_k * 2,
            filter=pc_filter,
        )
        matches = [m for m in matches if m["score"] >= 0.4]

        if matches:
            chunk_ids = [m["id"] for m in matches]
            scores_map = {m["id"]: m["score"] for m in matches}

            # Fetch chunk records from PocketBase
            if chunk_ids:
                or_parts = [f"id='{pb.escape_filter(cid)}'" for cid in chunk_ids]
                or_filter = " || ".join(or_parts)
                chunk_records = pb.get_all("help_chunks", filter=or_filter)
            else:
                chunk_records = []

            doc_ids_set = list({r["document_id"] for r in chunk_records})
            doc_map = {}
            if doc_ids_set:
                doc_or = " || ".join([f"id='{pb.escape_filter(did)}'" for did in doc_ids_set])
                doc_records = pb.get_all("help_documents", filter=doc_or)
                doc_map = {d["id"]: d for d in doc_records}

            for row in chunk_records:
                doc = doc_map.get(row["document_id"], {})
                chunks_data.append({
                    "document_title": doc.get("title", "Unknown"),
                    "heading_context": row.get("heading_context", ""),
                    "file_path": doc.get("file_path", ""),
                    "content": row["content"],
                    "similarity": scores_map.get(str(row["id"]), 0),
                })
            chunks_data.sort(key=lambda x: x.get("similarity", 0), reverse=True)
            chunks_data = chunks_data[:top_k]
    else:
        # Fallback to vector sidecar search
        vec_results = vec_client.search("help_chunks", query, limit=top_k)
        # vec_client returns raw matches; enrich with chunk/doc metadata
        for vr in vec_results:
            chunk_id = vr.get("record_id") or vr.get("id", "")
            chunk_rec = help_repo.get_help_chunk(chunk_id) if chunk_id else None
            if chunk_rec:
                doc = help_repo.get_help_document(chunk_rec["document_id"]) or {}
                chunks_data.append({
                    "document_title": doc.get("title", "Unknown"),
                    "heading_context": chunk_rec.get("heading_context", ""),
                    "file_path": doc.get("file_path", ""),
                    "content": chunk_rec["content"],
                    "similarity": vr.get("score", vr.get("similarity", 0)),
                })
            else:
                chunks_data.append({
                    "document_title": "Unknown",
                    "heading_context": "",
                    "file_path": "",
                    "content": vr.get("text", vr.get("content", "")),
                    "similarity": vr.get("score", vr.get("similarity", 0)),
                })

    if not chunks_data:
        logger.warning(f"No help chunks found for query: {query[:50]}")
        return [], "No specific documentation found for this query."

    # Build context from retrieved chunks
    context_parts = []
    sources = []

    for i, chunk in enumerate(chunks_data):
        context_parts.append(
            f"[Source {i + 1}: {chunk['document_title']} - {chunk['heading_context']}]\n{chunk['content']}"
        )

        sources.append(
            {
                "title": chunk["document_title"],
                "section": chunk["heading_context"],
                "file_path": chunk["file_path"],
                "similarity": chunk["similarity"],
            }
        )

    context = "\n\n---\n\n".join(context_parts)

    return sources, context


def build_help_system_prompt(context: str) -> str:
    """Build system prompt for help assistant.

    Args:
        context: Documentation context from vector search

    Returns:
        Formatted system prompt string
    """
    return f"""You are a helpful assistant for the SuperAssistant platform.

Your role is to answer questions about:
- How to use the admin dashboard
- Understanding metrics and KPIs (Ideation Velocity, Correction Loop, TRIPS)
- How the Solomon Engine works
- Onboarding new clients
- Managing documents and system instructions
- Troubleshooting issues
- Understanding the Bradbury Impact Loop framework
- Technical details about the system

CRITICAL INSTRUCTIONS FOR ANSWERING:

1. **PROCESS/HOW-TO QUESTIONS** (highest priority):
   - If the documentation contains step-by-step instructions, YOU MUST include ALL steps verbatim
   - NEVER summarize or skip steps from documented processes
   - If documentation shows 7 steps, your answer MUST include all 7 steps
   - Use the EXACT formatting from the documentation (numbered lists, bold text, etc.)
   - Include ALL details: tab names, button names, dropdown selections, everything
   - After listing all steps, you MAY offer: "Would you like more detail on any step?"

2. **NAVIGATION PATHS** (critical for all how-to questions):
   - **ALWAYS** include the complete navigation path from the documentation
   - Use **bold** for page names, tab names, and button names exactly as shown in docs
   - Format: "Navigate to **Page Name** → **Tab Name** → **Button/Option**"
   - Include every intermediate step (e.g., if you need to click a tab, say so)
   - Be explicit about WHERE to click, not just WHAT to do

3. **CONCEPTUAL/EXPLANATION QUESTIONS**:
   - Keep answers concise (2-4 sentences) unless documentation provides more detail
   - If documentation has extensive explanation, provide the key points
   - Offer more detail: "Would you like more information about [specific aspect]?"

4. **ACCURACY RULES**:
   - If documentation directly answers the question, quote or paraphrase it EXACTLY
   - Do NOT invent steps, simplify processes, or skip documented details
   - If unsure or documentation is unclear, say so immediately
   - Never contradict the documentation

DOCUMENTATION CONTEXT:
{context}

If the documentation doesn't cover the user's question, acknowledge this briefly
and provide general guidance if possible."""
