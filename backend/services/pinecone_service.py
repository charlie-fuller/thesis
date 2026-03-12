"""Pinecone Vector Database Service.

Centralized client for vector storage and search operations.
Replaces pgvector (Supabase) for embedding storage and similarity search.
"""

import logging
import os
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Lazy-initialized singleton
_index = None
_initialized = False


def _is_configured() -> bool:
    """Check if Pinecone is configured via environment variables."""
    return bool(os.environ.get("PINECONE_API_KEY"))


def get_index():
    """Get the Pinecone index (singleton).

    Returns:
        Pinecone Index object, or None if not configured.
    """
    global _index, _initialized

    if _initialized:
        return _index

    _initialized = True

    if not _is_configured():
        logger.warning("PINECONE_API_KEY not set - Pinecone disabled, falling back to pgvector")
        return None

    try:
        from pinecone import Pinecone

        api_key = os.environ.get("PINECONE_API_KEY")
        index_name = os.environ.get("PINECONE_INDEX", "thesis")

        pc = Pinecone(api_key=api_key)
        _index = pc.Index(index_name)
        logger.info(f"Pinecone connected to index '{index_name}'")
        return _index

    except Exception as e:
        logger.error(f"Failed to initialize Pinecone: {e}")
        _index = None
        return None


def upsert_vectors(
    vectors: List[Dict],
    namespace: str,
) -> int:
    """Batch upsert vectors to Pinecone.

    Args:
        vectors: List of dicts with keys: id, values, metadata
        namespace: Pinecone namespace (e.g. "document_chunks", "help_chunks")

    Returns:
        Number of vectors upserted, or 0 if Pinecone is not available.
    """
    index = get_index()
    if index is None:
        return 0

    if not vectors:
        return 0

    try:
        # Pinecone recommends batches of 100 for upsert
        batch_size = 100
        total_upserted = 0

        for i in range(0, len(vectors), batch_size):
            batch = vectors[i : i + batch_size]
            # Format: list of (id, values, metadata) tuples
            formatted = [(v["id"], [float(x) for x in v["values"]], v.get("metadata", {})) for v in batch]
            index.upsert(vectors=formatted, namespace=namespace)
            total_upserted += len(batch)

        logger.info(f"Upserted {total_upserted} vectors to namespace '{namespace}'")
        return total_upserted

    except Exception as e:
        logger.error(f"Pinecone upsert error (namespace={namespace}): {e}")
        return 0


def query_vectors(
    embedding: List[float],
    namespace: str,
    top_k: int = 10,
    filter: Optional[Dict] = None,
    include_metadata: bool = True,
) -> List[Dict]:
    """Query Pinecone for similar vectors.

    Args:
        embedding: Query embedding vector
        namespace: Pinecone namespace to search
        top_k: Number of results to return
        filter: Optional metadata filter dict (Pinecone filter syntax)
        include_metadata: Whether to return metadata with results

    Returns:
        List of dicts with keys: id, score, metadata.
        Returns empty list if Pinecone is not available.
    """
    index = get_index()
    if index is None:
        return []

    try:
        result = index.query(
            vector=embedding,
            namespace=namespace,
            top_k=top_k,
            filter=filter,
            include_metadata=include_metadata,
        )

        matches = []
        for match in result.get("matches", []):
            matches.append(
                {
                    "id": match["id"],
                    "score": match["score"],
                    "metadata": match.get("metadata", {}),
                }
            )

        return matches

    except Exception as e:
        logger.error(f"Pinecone query error (namespace={namespace}): {e}")
        return []


def delete_vectors(
    ids: List[str],
    namespace: str,
) -> bool:
    """Delete vectors by ID from Pinecone.

    Args:
        ids: List of vector IDs to delete
        namespace: Pinecone namespace

    Returns:
        True if successful, False otherwise.
    """
    index = get_index()
    if index is None:
        return False

    if not ids:
        return True

    try:
        # Pinecone delete supports up to 1000 IDs at once
        batch_size = 1000
        for i in range(0, len(ids), batch_size):
            batch = ids[i : i + batch_size]
            index.delete(ids=batch, namespace=namespace)

        logger.info(f"Deleted {len(ids)} vectors from namespace '{namespace}'")
        return True

    except Exception as e:
        logger.error(f"Pinecone delete error (namespace={namespace}): {e}")
        return False


def delete_by_metadata(
    filter: Dict,
    namespace: str,
) -> bool:
    """Delete vectors by metadata filter from Pinecone.

    Args:
        filter: Metadata filter dict (Pinecone filter syntax)
        namespace: Pinecone namespace

    Returns:
        True if successful, False otherwise.
    """
    index = get_index()
    if index is None:
        return False

    try:
        index.delete(filter=filter, namespace=namespace)
        logger.info(f"Deleted vectors with filter {filter} from namespace '{namespace}'")
        return True

    except Exception as e:
        logger.error(f"Pinecone delete by metadata error (namespace={namespace}): {e}")
        return False
