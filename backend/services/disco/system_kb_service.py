"""PuRDy System KB Service.

Manages the global system knowledge base (methodology files).
"""

import os
from pathlib import Path
from typing import Dict, List, Optional

import pb_client as pb
import repositories.disco as disco_repo
from config.constants import DATABASE, EMBEDDING, TEXT_CHUNKING
from document_processor import chunk_text, generate_embeddings
from logger_config import get_logger

logger = get_logger(__name__)

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
            existing = pb.get_first(
                "disco_system_kb",
                filter=f"filename='{pb.escape_filter(filename)}'",
            )

            if existing:
                # Update if content changed
                if existing.get("content") == content:
                    stats["skipped"] += 1
                    continue

                kb_id = existing["id"]

                # Update content
                pb.update_record("disco_system_kb", kb_id, {
                    "content": content,
                    "category": category,
                })

                # Delete old chunks
                old_chunks = pb.get_all(
                    "disco_system_kb_chunks",
                    filter=f"kb_id='{pb.escape_filter(kb_id)}'",
                )
                for chunk in old_chunks:
                    pb.delete_record("disco_system_kb_chunks", chunk["id"])

                stats["updated"] += 1

            else:
                # Create new KB entry
                description = extract_description(content)

                result = disco_repo.create_system_kb({
                    "filename": filename,
                    "content": content,
                    "category": category,
                    "description": description,
                })
                kb_id = result["id"]

                stats["created"] += 1

            # Create chunks and embeddings
            chunks = chunk_text(
                content,
                chunk_size=TEXT_CHUNKING.DEFAULT_CHUNK_SIZE,
                overlap=TEXT_CHUNKING.DEFAULT_OVERLAP,
            )

            if chunks:
                chunk_texts = [c["content"] for c in chunks]
                embeddings = generate_embeddings(chunk_texts, input_type=EMBEDDING.INPUT_TYPE_DOCUMENT)

                all_inserted = []
                for _i, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=False)):
                    chunk_data = {
                        "kb_id": kb_id,
                        "chunk_index": chunk["chunk_index"],
                        "content": chunk["content"].replace("\x00", ""),
                        "metadata": {"filename": filename},
                    }
                    inserted = disco_repo.create_system_kb_chunk(chunk_data)
                    if inserted:
                        all_inserted.append(inserted)

                # Upsert vectors to Pinecone
                pinecone_vectors = []
                for inserted_chunk, embedding in zip(all_inserted, embeddings, strict=False):
                    pinecone_vectors.append(
                        {
                            "id": str(inserted_chunk["id"]),
                            "values": embedding,
                            "metadata": {
                                "kb_id": kb_id,
                                "filename": filename,
                                "category": category,
                                "chunk_index": inserted_chunk.get("chunk_index", 0),
                            },
                        }
                    )

                if pinecone_vectors:
                    from services.pinecone_service import upsert_vectors

                    upsert_vectors(vectors=pinecone_vectors, namespace="disco_system_kb_chunks")

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
        query_embedding = generate_embeddings([query], input_type=EMBEDDING.INPUT_TYPE_QUERY)[0]

        # Try Pinecone first
        from services.pinecone_service import get_index, query_vectors

        if get_index() is not None:
            pc_filter = {}
            if category:
                pc_filter["category"] = {"$eq": category}

            matches = query_vectors(
                embedding=query_embedding,
                namespace="disco_system_kb_chunks",
                top_k=limit,
                filter=pc_filter if pc_filter else None,
            )
            matches = [m for m in matches if m["score"] >= min_similarity]

            if matches:
                chunk_ids = [m["id"] for m in matches]
                scores_map = {m["id"]: m["score"] for m in matches}

                # Fetch chunks by IDs
                chunks = []
                for cid in chunk_ids:
                    try:
                        chunk = pb.get_record("disco_system_kb_chunks", cid)
                        if chunk:
                            chunk["similarity"] = scores_map.get(str(chunk["id"]), 0)
                            chunks.append(chunk)
                    except Exception:
                        pass
                chunks.sort(key=lambda x: x.get("similarity", 0), reverse=True)
            else:
                chunks = []
        else:
            # No Pinecone fallback available without pgvector RPC
            chunks = []

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
        return disco_repo.list_system_kb(sort="filename")

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
        return disco_repo.get_system_kb(kb_id)

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
        return pb.get_all(
            "disco_system_kb",
            filter=f"category='{pb.escape_filter(category)}'",
            sort="filename",
        )

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
        total_files = pb.count("disco_system_kb")

        # Count chunks
        total_chunks = pb.count("disco_system_kb_chunks")

        # Count by category
        all_kb = disco_repo.list_system_kb()
        category_counts = {}
        for item in all_kb:
            cat = item.get("category", "general")
            category_counts[cat] = category_counts.get(cat, 0) + 1

        return {
            "total_files": total_files,
            "total_chunks": total_chunks,
            "by_category": category_counts,
        }

    except Exception as e:
        logger.error(f"Error getting KB stats: {e}")
        return {"total_files": 0, "total_chunks": 0, "by_category": {}}
