"""Document Digest Service.

Generates and manages precomputed document digests (3-5 sentence summaries).
These digests replace raw content truncation in services like Kraken and Taskmaster,
providing broader coverage with more focused context.
"""

import logging
import os
from datetime import datetime, timezone

import anthropic

from supabase import Client

logger = logging.getLogger(__name__)

DIGEST_MODEL = "claude-haiku-4-5-20251001"
DIGEST_MAX_TOKENS = 300
CONTENT_CAP = 12000  # ~3K tokens, keeps cost at ~$0.003/doc

DIGEST_SYSTEM_PROMPT = """You are a document summarization assistant. Produce a concise digest of the provided document.

Rules:
- 3-5 sentences, approximately 200 words
- Capture the key topics, conclusions, and actionable items
- Use plain language, no markdown formatting
- If the document is a meeting transcript, focus on decisions made and action items
- If the document is a strategy/analysis document, focus on the main thesis and recommendations
- Do not include preamble like "This document..." -- start with the substance"""


async def generate_digest(content: str, filename: str = "") -> str | None:
    """Generate a digest for document content using Claude Haiku.

    Args:
        content: The document text content
        filename: Optional filename for context

    Returns:
        Digest string, or None if content is empty/too short
    """
    if not content or len(content.strip()) < 50:
        return None

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set, skipping digest generation")
        return None

    truncated = content[:CONTENT_CAP]

    user_prompt = f"Document: {filename}\n\n{truncated}" if filename else truncated

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=DIGEST_MODEL,
            max_tokens=DIGEST_MAX_TOKENS,
            system=DIGEST_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text.strip()
    except Exception as e:
        logger.error(f"Digest generation failed for {filename}: {e}")
        return None


async def generate_and_store_digest(document_id: str, supabase: Client | None = None) -> str | None:
    """Fetch document content, generate digest, and store it back.

    Args:
        document_id: UUID of the document
        supabase: Optional Supabase client (will import default if not provided)

    Returns:
        The generated digest, or None on failure
    """
    if supabase is None:
        from database import get_supabase

        supabase = get_supabase()

    try:
        # Get document metadata
        doc_result = supabase.table("documents").select("filename, title").eq("id", document_id).single().execute()

        if not doc_result.data:
            logger.warning(f"Document {document_id} not found for digest generation")
            return None

        doc = doc_result.data
        filename = doc.get("filename") or doc.get("title") or ""

        # Assemble content from document_chunks (content lives there, not on documents)
        chunks_result = (
            supabase.table("document_chunks")
            .select("content")
            .eq("document_id", document_id)
            .order("chunk_index")
            .execute()
        )

        if not chunks_result.data:
            logger.info(f"No chunks found for document {document_id}, skipping digest")
            return None

        content = "\n".join(chunk["content"] for chunk in chunks_result.data)

        digest = await generate_digest(content, filename)
        if not digest:
            return None

        supabase.table("documents").update(
            {
                "digest": digest,
                "digest_generated_at": datetime.now(timezone.utc).isoformat(),
            }
        ).eq("id", document_id).execute()

        logger.info(f"Digest generated for {document_id} ({len(digest)} chars)")
        return digest

    except Exception as e:
        logger.error(f"Failed to generate/store digest for {document_id}: {e}")
        return None


def get_digests_for_documents(doc_ids: list[str], supabase: Client) -> dict[str, str]:
    """Batch fetch digests for a list of document IDs.

    Args:
        doc_ids: List of document UUIDs
        supabase: Supabase client

    Returns:
        Dict mapping document_id -> digest (only includes docs with digests)
    """
    if not doc_ids:
        return {}

    try:
        result = (
            supabase.table("documents").select("id, digest").in_("id", doc_ids).not_.is_("digest", "null").execute()
        )
        return {row["id"]: row["digest"] for row in (result.data or [])}
    except Exception as e:
        logger.error(f"Failed to fetch digests: {e}")
        return {}


def get_project_document_digests(project_id: str, supabase: Client) -> list[dict]:
    """Get digests for all documents linked to a project (direct + via initiatives).

    Args:
        project_id: The project UUID
        supabase: Supabase client

    Returns:
        List of {id, title, digest} dicts
    """
    doc_ids = set()

    # Direct project documents
    try:
        result = supabase.table("project_documents").select("document_id").eq("project_id", project_id).execute()
        for row in result.data or []:
            doc_ids.add(row["document_id"])
    except Exception as e:
        logger.warning(f"Failed to fetch project documents: {e}")

    # Initiative-linked documents
    try:
        init_result = (
            supabase.table("project_initiative_links").select("initiative_id").eq("project_id", project_id).execute()
        )
        initiative_ids = [r["initiative_id"] for r in (init_result.data or [])]

        for init_id in initiative_ids[:5]:
            init_docs = (
                supabase.table("disco_initiative_documents")
                .select("document_id")
                .eq("initiative_id", init_id)
                .execute()
            )
            for row in init_docs.data or []:
                doc_ids.add(row["document_id"])
    except Exception as e:
        logger.warning(f"Failed to fetch initiative documents: {e}")

    if not doc_ids:
        return []

    # Fetch titles and digests
    try:
        result = supabase.table("documents").select("id, title, digest").in_("id", list(doc_ids)).execute()
        return [
            {"id": row["id"], "title": row.get("title", "Untitled"), "digest": row.get("digest")}
            for row in (result.data or [])
        ]
    except Exception as e:
        logger.error(f"Failed to fetch document details: {e}")
        return []
