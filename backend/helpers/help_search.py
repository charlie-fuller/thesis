"""Help documentation search module.

Handles vector search and RAG over help documentation.
"""

from typing import Dict, List

from database import get_supabase
from logger_config import get_logger
from services.embeddings import create_embedding

logger = get_logger(__name__)
supabase = get_supabase()


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

    # Step 2: Search help chunks - try Pinecone first, fall back to pgvector
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

            db_result = (
                supabase.table("help_chunks")
                .select("id, document_id, content, heading_context")
                .in_("id", chunk_ids)
                .execute()
            )
            doc_ids_set = list({r["document_id"] for r in (db_result.data or [])})
            docs_result = (
                supabase.table("help_documents")
                .select("id, title, file_path")
                .in_("id", doc_ids_set)
                .execute()
            ) if doc_ids_set else type("R", (), {"data": []})()
            doc_map = {d["id"]: d for d in (docs_result.data or [])}

            for row in db_result.data or []:
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
        # Fallback to pgvector RPC
        help_chunks = supabase.rpc(
            "match_help_chunks",
            {"query_embedding": query_embedding, "match_count": top_k, "user_role": user_role},
        ).execute()
        chunks_data = help_chunks.data or []

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
