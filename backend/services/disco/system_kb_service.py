"""PuRDy System KB Service.

Manages the global system knowledge base (methodology files).
"""

import asyncio
import os
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

from config.constants import DATABASE, EMBEDDING, TEXT_CHUNKING
from database import get_supabase
from document_processor import chunk_text, generate_embeddings
from logger_config import get_logger

logger = get_logger(__name__)
supabase = get_supabase()

# Configuration (DISCO_REPO_PATH preferred, DISCO_REPO_PATH for legacy)
DISCO_REPO_PATH = os.environ.get("DISCO_REPO_PATH") or os.environ.get("DISCO_REPO_PATH", "")
KB_FOLDER = "KB"

# KB file categories
KB_CATEGORIES = {
    # Core Methodology
    "discovery-checklist.md": "methodology",
    "question-banks.md": "methodology",
    "cinnamon-framework.md": "methodology",
    # Analysis Frameworks
    "analysis-lenses.md": "analysis",
    "trade-off-frameworks.md": "analysis",
    "impact-effort-scoring.md": "analysis",
    "initiative-risk-framework.md": "risk",
    # Problem Analysis (v2.7 additions)
    "a3-problem-solving-template.md": "analysis",
    "muda-mura-muri-diagnosis.md": "analysis",
    "value-stream-mapping-taxonomy.md": "analysis",
    # Risk & Patterns
    "project-failures.md": "risk",
    "stakeholder-personas.md": "analysis",
    "initiative-taxonomy.md": "methodology",
    # Tech Evaluation
    "build-vs-buy.md": "decision",
    "capability-thresholds.md": "decision",
    "contentful-systems.md": "internal",
    # Supporting
    "triage-questions.md": "methodology",
    "genai-considerations.md": "decision",
    "internal-systems.md": "internal",
    # Problem Space Discipline (v1.3 additions)
    "five-whys-deep-methodology.md": "methodology",
    "jobs-to-be-done-framework.md": "methodology",
    "problem-space-discipline.md": "methodology",
    # Evidence & Analysis (v1.3 additions)
    "evidence-evaluation-framework.md": "analysis",
    "pattern-library-reference.md": "analysis",
    "decision-science-frameworks.md": "decision",
    # Clustering & Requirements (v1.3 additions)
    "clustering-methodology.md": "methodology",
    "requirements-prioritization-heuristics.md": "methodology",
    # Solution Taxonomy (v1.3 additions)
    "solution-type-taxonomy.md": "decision",
    "non-build-solution-patterns.md": "decision",
    # Decision-Forcing Canvas (v1.4 additions)
    "decision-forcing-canvas.md": "decision",
}


async def sync_kb_from_filesystem() -> Dict:
    """Sync KB files from filesystem to database.

    Creates or updates KB entries and regenerates embeddings.

    Returns:
        Dict with sync statistics
    """
    logger.info("Syncing KB from filesystem...")

    kb_path = Path(DISCO_REPO_PATH) / KB_FOLDER

    if not kb_path.exists():
        logger.error(f"KB folder not found: {kb_path}")
        raise FileNotFoundError(f"KB folder not found: {kb_path}")

    stats = {"created": 0, "updated": 0, "skipped": 0, "errors": 0, "files_processed": []}

    # Get all markdown files
    md_files = list(kb_path.glob("*.md"))
    logger.info(f"Found {len(md_files)} KB files")

    for filepath in md_files:
        filename = filepath.name
        category = KB_CATEGORIES.get(filename, "general")

        try:
            content = filepath.read_text()

            # Check if file exists in DB
            existing = await asyncio.to_thread(
                lambda fn=filename: supabase.table("disco_system_kb").select("id, content").eq("filename", fn).execute()
            )

            if existing.data:
                # Update if content changed
                kb_record = existing.data[0]
                if kb_record["content"] == content:
                    stats["skipped"] += 1
                    continue

                # Update content
                await asyncio.to_thread(
                    lambda fn=filename, c=content, cat=category: supabase.table("disco_system_kb")
                    .update({"content": c, "category": cat, "updated_at": "now()"})
                    .eq("filename", fn)
                    .execute()
                )

                # Delete old chunks
                await asyncio.to_thread(
                    lambda kb_id=kb_record["id"]: supabase.table("disco_system_kb_chunks")
                    .delete()
                    .eq("kb_id", kb_id)
                    .execute()
                )

                kb_id = kb_record["id"]
                stats["updated"] += 1

            else:
                # Create new KB entry
                kb_id = str(uuid4())
                description = extract_description(content)

                await asyncio.to_thread(
                    lambda kid=kb_id, fn=filename, c=content, cat=category, desc=description: supabase.table(
                        "disco_system_kb"
                    )
                    .insert(
                        {
                            "id": kid,
                            "filename": fn,
                            "content": c,
                            "category": cat,
                            "description": desc,
                        }
                    )
                    .execute()
                )

                stats["created"] += 1

            # Create chunks and embeddings
            chunks = chunk_text(
                content,
                chunk_size=TEXT_CHUNKING.DEFAULT_CHUNK_SIZE,
                overlap=TEXT_CHUNKING.DEFAULT_OVERLAP,
            )

            if chunks:
                chunk_texts = [c["content"] for c in chunks]
                embeddings = await asyncio.to_thread(
                    lambda ct=chunk_texts: generate_embeddings(ct, input_type=EMBEDDING.INPUT_TYPE_DOCUMENT)
                )

                chunks_to_insert = []
                for _i, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=False)):
                    chunks_to_insert.append(
                        {
                            "kb_id": kb_id,
                            "chunk_index": chunk["chunk_index"],
                            "content": chunk["content"].replace("\x00", ""),
                            "embedding": embedding,
                            "metadata": {"filename": filename},
                        }
                    )

                # Batch insert
                batch_size = DATABASE.BATCH_INSERT_SIZE
                for batch_start in range(0, len(chunks_to_insert), batch_size):
                    batch = chunks_to_insert[batch_start : batch_start + batch_size]
                    await asyncio.to_thread(
                        lambda b=batch: supabase.table("disco_system_kb_chunks").insert(b).execute()
                    )

            stats["files_processed"].append(filename)
            logger.info(f"Processed KB file: {filename} ({len(chunks)} chunks)")

        except Exception as e:
            logger.error(f"Error processing KB file {filename}: {e}")
            stats["errors"] += 1

    logger.info(f"KB sync complete: {stats}")
    return stats


async def search_system_kb(
    query: str, limit: int = 10, min_similarity: float = 0.2, category: Optional[str] = None
) -> List[Dict]:
    """Vector search in system KB.

    Args:
        query: Search query
        limit: Max results
        min_similarity: Minimum similarity threshold
        category: Optional category filter

    Returns:
        List of matching KB chunks
    """
    logger.info(f"Searching system KB for: {query[:50]}...")

    try:
        # Generate query embedding
        query_embedding = await asyncio.to_thread(
            lambda: generate_embeddings([query], input_type=EMBEDDING.INPUT_TYPE_QUERY)[0]
        )

        # Call vector search function
        result = await asyncio.to_thread(
            lambda: supabase.rpc(
                "match_disco_system_kb_chunks",
                {
                    "query_embedding": query_embedding,
                    "match_count": limit,
                    "match_threshold": min_similarity,
                },
            ).execute()
        )

        chunks = result.data or []

        # Filter by category if specified
        if category and chunks:
            chunks = [c for c in chunks if c.get("category") == category]

        logger.info(f"Found {len(chunks)} matching KB chunks")
        return chunks

    except Exception as e:
        logger.error(f"Error searching system KB: {e}")
        return []


async def get_kb_files() -> List[Dict]:
    """List all KB files.

    Returns:
        List of KB file records
    """
    try:
        result = await asyncio.to_thread(
            lambda: supabase.table("disco_system_kb")
            .select("id, filename, category, description, created_at, updated_at")
            .order("filename")
            .execute()
        )

        return result.data or []

    except Exception as e:
        logger.error(f"Error listing KB files: {e}")
        return []


async def get_kb_file(kb_id: str) -> Optional[Dict]:
    """Get a single KB file by ID.

    Args:
        kb_id: KB file UUID

    Returns:
        KB file record with content
    """
    try:
        result = await asyncio.to_thread(
            lambda: supabase.table("disco_system_kb").select("*").eq("id", kb_id).single().execute()
        )

        return result.data

    except Exception as e:
        logger.error(f"Error fetching KB file {kb_id}: {e}")
        return None


async def get_kb_by_category(category: str) -> List[Dict]:
    """Get KB files by category.

    Args:
        category: Category filter

    Returns:
        List of KB file records
    """
    try:
        result = await asyncio.to_thread(
            lambda: supabase.table("disco_system_kb")
            .select("id, filename, description")
            .eq("category", category)
            .order("filename")
            .execute()
        )

        return result.data or []

    except Exception as e:
        logger.error(f"Error listing KB files by category: {e}")
        return []


def extract_description(content: str) -> str:
    """Extract description from KB file content.

    Uses first paragraph or first N characters.
    """
    # Split into paragraphs
    paragraphs = content.strip().split("\n\n")

    # Skip headers, get first content paragraph
    for para in paragraphs:
        para = para.strip()
        if para and not para.startswith("#"):
            # Clean and truncate
            desc = para.replace("\n", " ").strip()
            if len(desc) > 300:
                desc = desc[:297] + "..."
            return desc

    return ""


async def get_kb_stats() -> Dict:
    """Get statistics about the system KB.

    Returns:
        Dict with KB statistics
    """
    try:
        # Count files
        files_result = await asyncio.to_thread(
            lambda: supabase.table("disco_system_kb").select("id", count="exact").execute()
        )

        # Count chunks
        chunks_result = await asyncio.to_thread(
            lambda: supabase.table("disco_system_kb_chunks").select("id", count="exact").execute()
        )

        # Count by category
        categories_result = await asyncio.to_thread(
            lambda: supabase.table("disco_system_kb").select("category").execute()
        )

        category_counts = {}
        for item in categories_result.data or []:
            cat = item.get("category", "general")
            category_counts[cat] = category_counts.get(cat, 0) + 1

        return {
            "total_files": files_result.count or 0,
            "total_chunks": chunks_result.count or 0,
            "by_category": category_counts,
        }

    except Exception as e:
        logger.error(f"Error getting KB stats: {e}")
        return {"total_files": 0, "total_chunks": 0, "by_category": {}}
