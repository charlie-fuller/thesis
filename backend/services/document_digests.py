"""Document Digest Service.

Generates and manages precomputed document digests (3-5 sentence summaries).
These digests replace raw content truncation in services like Kraken and Taskmaster,
providing broader coverage with more focused context.
"""

import logging
import os
from datetime import datetime, timezone

import anthropic

import pb_client as pb
from repositories import documents as documents_repo, projects as projects_repo

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


async def generate_and_store_digest(document_id: str, supabase=None) -> str | None:
    """Fetch document content, generate digest, and store it back.

    Args:
        document_id: UUID of the document
        supabase: Ignored (kept for backward compatibility)

    Returns:
        The generated digest, or None on failure
    """
    try:
        # Get document metadata
        doc = documents_repo.get_document(document_id)

        if not doc:
            logger.warning(f"Document {document_id} not found for digest generation")
            return None

        filename = doc.get("filename") or doc.get("title") or ""

        # Assemble content from document_chunks (content lives there, not on documents)
        chunks = documents_repo.list_document_chunks(document_id)

        if not chunks:
            logger.info(f"No chunks found for document {document_id}, skipping digest")
            return None

        # Sort by chunk_index
        chunks.sort(key=lambda c: c.get("chunk_index", 0))
        content = "\n".join(chunk["content"] for chunk in chunks)

        digest = await generate_digest(content, filename)
        if not digest:
            return None

        documents_repo.update_document(document_id, {
            "digest": digest,
            "digest_generated_at": datetime.now(timezone.utc).isoformat(),
        })

        logger.info(f"Digest generated for {document_id} ({len(digest)} chars)")
        return digest

    except Exception as e:
        logger.error(f"Failed to generate/store digest for {document_id}: {e}")
        return None


def get_digests_for_documents(doc_ids: list[str], supabase=None) -> dict[str, str]:
    """Batch fetch digests for a list of document IDs.

    Args:
        doc_ids: List of document UUIDs
        supabase: Ignored (kept for backward compatibility)

    Returns:
        Dict mapping document_id -> digest (only includes docs with digests)
    """
    if not doc_ids:
        return {}

    try:
        result = {}
        for doc_id in doc_ids:
            doc = documents_repo.get_document(doc_id)
            if doc and doc.get("digest"):
                result[doc["id"]] = doc["digest"]
        return result
    except Exception as e:
        logger.error(f"Failed to fetch digests: {e}")
        return {}


def get_project_document_digests(project_id: str, supabase=None) -> list[dict]:
    """Get digests for all documents linked to a project (direct + via initiatives).

    Args:
        project_id: The project UUID
        supabase: Ignored (kept for backward compatibility)

    Returns:
        List of {id, title, digest} dicts
    """
    doc_ids = set()

    # Direct project documents
    try:
        esc_pid = pb.escape_filter(project_id)
        rows = pb.get_all("project_documents", filter=f"project_id='{esc_pid}'")
        for row in rows:
            doc_ids.add(row["document_id"])
    except Exception as e:
        logger.warning(f"Failed to fetch project documents: {e}")

    # Initiative-linked documents
    try:
        esc_pid = pb.escape_filter(project_id)
        init_links = pb.get_all("project_initiative_links", filter=f"project_id='{esc_pid}'")
        initiative_ids = [r["initiative_id"] for r in init_links]

        for init_id in initiative_ids[:5]:
            esc_iid = pb.escape_filter(init_id)
            init_docs = pb.get_all("disco_initiative_documents", filter=f"initiative_id='{esc_iid}'")
            for row in init_docs:
                doc_ids.add(row["document_id"])
    except Exception as e:
        logger.warning(f"Failed to fetch initiative documents: {e}")

    if not doc_ids:
        return []

    # Fetch titles and digests
    try:
        results = []
        for doc_id in doc_ids:
            doc = documents_repo.get_document(doc_id)
            if doc:
                results.append({
                    "id": doc["id"],
                    "title": doc.get("title", "Untitled"),
                    "digest": doc.get("digest"),
                })
        return results
    except Exception as e:
        logger.error(f"Failed to fetch document details: {e}")
        return []
