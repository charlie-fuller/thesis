#!/usr/bin/env python3
"""
Backfill existing Supabase vector embeddings to Pinecone.

Migrates embeddings from 3 tables:
  - document_chunks (87K+ rows) -> namespace "document_chunks"
  - help_chunks (305 rows) -> namespace "help_chunks"
  - disco_system_kb_chunks (902 rows) -> namespace "disco_system_kb_chunks"

Usage:
  cd backend
  .venv/bin/python scripts/backfill_pinecone.py [--dry-run] [--table TABLE] [--batch-size N]

Options:
  --dry-run       Show what would be migrated without writing to Pinecone
  --table TABLE   Only migrate a specific table (document_chunks, help_chunks, disco_system_kb_chunks)
  --batch-size N  Rows to fetch per DB query (default: 500)
"""

import sys
import argparse
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from database import get_supabase
from logger_config import get_logger
from services.pinecone_service import upsert_vectors, get_index

logger = get_logger(__name__)


def backfill_document_chunks(supabase, batch_size: int, dry_run: bool) -> int:
    """Backfill document_chunks -> Pinecone namespace 'document_chunks'."""
    namespace = "document_chunks"
    logger.info(f"--- Backfilling {namespace} ---")

    # Get total count
    count_resp = supabase.table("document_chunks").select("id", count="exact").limit(1).execute()
    total = count_resp.count
    logger.info(f"Total rows: {total}")

    if dry_run:
        logger.info(f"[DRY RUN] Would migrate {total} vectors to namespace '{namespace}'")
        return total

    migrated = 0
    offset = 0

    while offset < total:
        # Fetch batch with embedding + join data
        # Supabase client can't easily extract raw vector, so we fetch chunks
        # and join with documents for metadata
        resp = (
            supabase.table("document_chunks")
            .select("id, document_id, chunk_index, embedding, documents(client_id, user_id, source_platform)")
            .range(offset, offset + batch_size - 1)
            .execute()
        )
        rows = resp.data
        if not rows:
            break

        pinecone_vectors = []
        for row in rows:
            emb = row.get("embedding")
            if not emb:
                continue

            # Parse embedding - it comes as a list from Supabase
            if isinstance(emb, str):
                import json
                emb = json.loads(emb)

            doc_info = row.get("documents") or {}
            source_type = "document"
            if doc_info.get("source_platform") == "obsidian":
                source_type = "obsidian"

            pinecone_vectors.append({
                "id": str(row["id"]),
                "values": emb,
                "metadata": {
                    "document_id": str(row["document_id"]),
                    "client_id": str(doc_info.get("client_id", "")),
                    "user_id": str(doc_info.get("user_id", "")),
                    "chunk_index": row.get("chunk_index", 0),
                    "source_type": source_type,
                },
            })

        if pinecone_vectors:
            count = upsert_vectors(vectors=pinecone_vectors, namespace=namespace)
            migrated += count

        offset += batch_size
        logger.info(f"  Progress: {min(offset, total)}/{total} ({migrated} upserted)")

    logger.info(f"Completed {namespace}: {migrated} vectors migrated")
    return migrated


def backfill_help_chunks(supabase, batch_size: int, dry_run: bool) -> int:
    """Backfill help_chunks -> Pinecone namespace 'help_chunks'."""
    namespace = "help_chunks"
    logger.info(f"--- Backfilling {namespace} ---")

    # Role access mapping (from index_help_docs.py)
    ROLE_ACCESS_MAP = {
        "admin": ["admin"],
        "system": ["admin", "user"],
        "user": ["user"],
        "technical": ["admin"],
    }

    resp = (
        supabase.table("help_chunks")
        .select("id, document_id, chunk_index, embedding, heading_context, role_access, help_documents(title, category)")
        .execute()
    )
    rows = resp.data
    total = len(rows)
    logger.info(f"Total rows: {total}")

    if dry_run:
        logger.info(f"[DRY RUN] Would migrate {total} vectors to namespace '{namespace}'")
        return total

    pinecone_vectors = []
    for row in rows:
        emb = row.get("embedding")
        if not emb:
            continue

        if isinstance(emb, str):
            import json
            emb = json.loads(emb)

        doc_info = row.get("help_documents") or {}
        category = doc_info.get("category", "system")
        role_access = row.get("role_access", ["user"])

        # Pinecone stores single value for role_access (first element)
        role_val = role_access[0] if isinstance(role_access, list) and role_access else "user"

        pinecone_vectors.append({
            "id": str(row["id"]),
            "values": emb,
            "metadata": {
                "document_id": str(row["document_id"]),
                "category": category,
                "title": doc_info.get("title", ""),
                "heading": row.get("heading_context", ""),
                "role_access": role_val,
            },
        })

    if pinecone_vectors:
        count = upsert_vectors(vectors=pinecone_vectors, namespace=namespace)
        logger.info(f"Completed {namespace}: {count} vectors migrated")
        return count

    return 0


def backfill_disco_system_kb_chunks(supabase, batch_size: int, dry_run: bool) -> int:
    """Backfill disco_system_kb_chunks -> Pinecone namespace 'disco_system_kb_chunks'."""
    namespace = "disco_system_kb_chunks"
    logger.info(f"--- Backfilling {namespace} ---")

    resp = (
        supabase.table("disco_system_kb_chunks")
        .select("id, kb_id, chunk_index, embedding, disco_system_kb(category)")
        .execute()
    )
    rows = resp.data
    total = len(rows)
    logger.info(f"Total rows: {total}")

    if dry_run:
        logger.info(f"[DRY RUN] Would migrate {total} vectors to namespace '{namespace}'")
        return total

    pinecone_vectors = []
    for row in rows:
        emb = row.get("embedding")
        if not emb:
            continue

        if isinstance(emb, str):
            import json
            emb = json.loads(emb)

        kb_info = row.get("disco_system_kb") or {}

        pinecone_vectors.append({
            "id": str(row["id"]),
            "values": emb,
            "metadata": {
                "kb_id": str(row["kb_id"]),
                "category": kb_info.get("category", ""),
                "chunk_index": row.get("chunk_index", 0),
            },
        })

    if pinecone_vectors:
        count = upsert_vectors(vectors=pinecone_vectors, namespace=namespace)
        logger.info(f"Completed {namespace}: {count} vectors migrated")
        return count

    return 0


TABLE_HANDLERS = {
    "document_chunks": backfill_document_chunks,
    "help_chunks": backfill_help_chunks,
    "disco_system_kb_chunks": backfill_disco_system_kb_chunks,
}


def main():
    parser = argparse.ArgumentParser(description="Backfill Supabase embeddings to Pinecone")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be migrated")
    parser.add_argument("--table", choices=list(TABLE_HANDLERS.keys()), help="Only migrate specific table")
    parser.add_argument("--batch-size", type=int, default=500, help="Rows per DB fetch (default: 500)")
    args = parser.parse_args()

    # Verify Pinecone connection
    if not args.dry_run:
        idx = get_index()
        if idx is None:
            logger.error("Pinecone index not available. Check PINECONE_API_KEY and PINECONE_INDEX env vars.")
            sys.exit(1)
        stats = idx.describe_index_stats()
        logger.info(f"Pinecone index stats before migration: {stats.total_vector_count} vectors")

    supabase = get_supabase()
    tables = [args.table] if args.table else list(TABLE_HANDLERS.keys())

    total_migrated = 0
    start = time.time()

    for table in tables:
        handler = TABLE_HANDLERS[table]
        count = handler(supabase, args.batch_size, args.dry_run)
        total_migrated += count

    elapsed = time.time() - start
    logger.info(f"\n=== Migration complete ===")
    logger.info(f"Total vectors: {total_migrated}")
    logger.info(f"Time: {elapsed:.1f}s")

    if not args.dry_run:
        # Show final stats
        idx = get_index()
        stats = idx.describe_index_stats()
        logger.info(f"Pinecone index stats after migration: {stats.total_vector_count} vectors")
        for ns, ns_stats in stats.namespaces.items():
            logger.info(f"  {ns}: {ns_stats.vector_count} vectors")


if __name__ == "__main__":
    main()
