"""PuRDy Document Service.

Handles document upload, chunking, embedding, and retrieval for PuRDy initiatives.
"""

import asyncio
from typing import Dict, List, Optional
from uuid import uuid4

from config.constants import DATABASE, EMBEDDING, TEXT_CHUNKING
from database import get_supabase
from document_processor import chunk_text, extract_text_from_file, generate_embeddings
from logger_config import get_logger

logger = get_logger(__name__)
supabase = get_supabase()


async def upload_document(
    initiative_id: str,
    filename: str,
    content: str,
    user_id: str,
    document_type: str = "uploaded",
    metadata: Optional[Dict] = None,
) -> Dict:
    """Upload and process a document for an initiative.

    Args:
        initiative_id: Initiative UUID
        filename: Document filename
        content: Document text content (pre-extracted)
        user_id: Uploading user's ID
        document_type: Type of document (uploaded, triage_output, etc.)
        metadata: Optional metadata dict

    Returns:
        Created document record with chunk count
    """
    logger.info(f"Uploading document '{filename}' to initiative {initiative_id}")

    document_id = str(uuid4())

    try:
        # Create document record
        doc_result = await asyncio.to_thread(
            lambda: supabase.table("disco_documents")
            .insert(
                {
                    "id": document_id,
                    "initiative_id": initiative_id,
                    "filename": filename,
                    "content": content,
                    "document_type": document_type,
                    "version": 1,
                    "metadata": metadata or {},
                }
            )
            .execute()
        )

        if not doc_result.data:
            raise ValueError("Failed to create document")

        document = doc_result.data[0]

        # Chunk the content
        chunks = chunk_text(
            content,
            chunk_size=TEXT_CHUNKING.DEFAULT_CHUNK_SIZE,
            overlap=TEXT_CHUNKING.DEFAULT_OVERLAP,
        )
        logger.info(f"Created {len(chunks)} chunks for document {document_id}")

        if chunks:
            # Generate embeddings
            chunk_texts = [chunk["content"] for chunk in chunks]
            embeddings = await asyncio.to_thread(
                lambda: generate_embeddings(chunk_texts, input_type=EMBEDDING.INPUT_TYPE_DOCUMENT)
            )
            logger.info(f"Generated {len(embeddings)} embeddings")

            # Store chunks with embeddings
            chunks_to_insert = []
            for _i, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=False)):
                sanitized_content = chunk["content"].replace("\x00", "")
                chunks_to_insert.append(
                    {
                        "document_id": document_id,
                        "initiative_id": initiative_id,
                        "chunk_index": chunk["chunk_index"],
                        "content": sanitized_content,
                        "embedding": embedding,
                        "metadata": {"filename": filename, "chunk_size": len(sanitized_content)},
                    }
                )

            # Batch insert chunks
            batch_size = DATABASE.BATCH_INSERT_SIZE
            for batch_start in range(0, len(chunks_to_insert), batch_size):
                batch = chunks_to_insert[batch_start : batch_start + batch_size]
                await asyncio.to_thread(lambda b=batch: supabase.table("disco_document_chunks").insert(b).execute())

            logger.info(f"Stored {len(chunks_to_insert)} chunks for document {document_id}")

        document["chunk_count"] = len(chunks)
        return document

    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        # Cleanup on failure
        try:
            await asyncio.to_thread(lambda: supabase.table("disco_documents").delete().eq("id", document_id).execute())
        except Exception:
            pass
        raise


async def upload_document_file(initiative_id: str, file_data: bytes, filename: str, user_id: str) -> Dict:
    """Upload a file, extract text, and process it.

    Args:
        initiative_id: Initiative UUID
        file_data: Raw file bytes
        filename: Original filename
        user_id: Uploading user's ID

    Returns:
        Created document record
    """
    logger.info(f"Processing file upload: {filename}")

    # Extract text from file
    content = await asyncio.to_thread(lambda: extract_text_from_file(file_data, filename))

    return await upload_document(
        initiative_id=initiative_id,
        filename=filename,
        content=content,
        user_id=user_id,
        document_type="uploaded",
    )


async def get_documents(
    initiative_id: str, document_type: Optional[str] = None, limit: int = 100, offset: int = 0
) -> Dict:
    """List documents for an initiative.

    Args:
        initiative_id: Initiative UUID
        document_type: Optional filter by type
        limit: Max results
        offset: Pagination offset

    Returns:
        Dict with documents list and total count
    """
    logger.info(f"Fetching documents for initiative {initiative_id}")

    try:
        query = supabase.table("disco_documents").select("*", count="exact").eq("initiative_id", initiative_id)

        if document_type:
            query = query.eq("document_type", document_type)

        query = query.order("uploaded_at", desc=True).range(offset, offset + limit - 1)

        result = await asyncio.to_thread(lambda: query.execute())

        return {"documents": result.data or [], "total": result.count or 0}

    except Exception as e:
        logger.error(f"Error fetching documents: {e}")
        raise


async def get_document(document_id: str, initiative_id: str) -> Optional[Dict]:
    """Get a single document by ID.

    Args:
        document_id: Document UUID
        initiative_id: Initiative UUID (for access check)

    Returns:
        Document record or None
    """
    try:
        result = await asyncio.to_thread(
            lambda: supabase.table("disco_documents")
            .select("*")
            .eq("id", document_id)
            .eq("initiative_id", initiative_id)
            .single()
            .execute()
        )
        return result.data
    except Exception as e:
        logger.error(f"Error fetching document {document_id}: {e}")
        return None


async def delete_document(document_id: str, initiative_id: str) -> bool:
    """Delete a document and its chunks.

    Args:
        document_id: Document UUID
        initiative_id: Initiative UUID (for access check)

    Returns:
        True if deleted
    """
    logger.info(f"Deleting document {document_id}")

    try:
        # Verify document belongs to initiative
        doc = await get_document(document_id, initiative_id)
        if not doc:
            raise ValueError(f"Document {document_id} not found in initiative {initiative_id}")

        # Delete document (cascades to chunks)
        await asyncio.to_thread(lambda: supabase.table("disco_documents").delete().eq("id", document_id).execute())

        logger.info(f"Deleted document {document_id}")
        return True

    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise


async def search_initiative_docs(
    initiative_id: str, query: str, limit: int = 10, min_similarity: float = 0.2
) -> List[Dict]:
    """Vector search within initiative documents.

    Args:
        initiative_id: Initiative UUID
        query: Search query
        limit: Max results
        min_similarity: Minimum similarity threshold

    Returns:
        List of matching chunks with similarity scores
    """
    logger.info(f"Searching initiative {initiative_id} for: {query[:50]}...")

    try:
        # Generate query embedding
        query_embedding = await asyncio.to_thread(
            lambda: generate_embeddings([query], input_type=EMBEDDING.INPUT_TYPE_QUERY)[0]
        )

        # Call vector search function
        result = await asyncio.to_thread(
            lambda: supabase.rpc(
                "match_disco_document_chunks",
                {
                    "query_embedding": query_embedding,
                    "match_count": limit,
                    "match_threshold": min_similarity,
                    "p_initiative_id": initiative_id,
                },
            ).execute()
        )

        chunks = result.data or []
        logger.info(f"Found {len(chunks)} matching chunks")

        # Fetch document filenames for context
        if chunks:
            doc_ids = list({c["document_id"] for c in chunks})
            docs_result = await asyncio.to_thread(
                lambda: supabase.table("disco_documents").select("id, filename").in_("id", doc_ids).execute()
            )
            doc_names = {d["id"]: d["filename"] for d in (docs_result.data or [])}

            for chunk in chunks:
                chunk["filename"] = doc_names.get(chunk["document_id"], "Unknown")

        return chunks

    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        raise


async def promote_output_to_document(output_id: str, initiative_id: str) -> Dict:
    """Promote an agent output to a document in the initiative.

    Args:
        output_id: Output UUID
        initiative_id: Initiative UUID

    Returns:
        Created document record
    """
    logger.info(f"Promoting output {output_id} to document")

    try:
        # Fetch the output
        output_result = await asyncio.to_thread(
            lambda: supabase.table("disco_outputs")
            .select("*")
            .eq("id", output_id)
            .eq("initiative_id", initiative_id)
            .single()
            .execute()
        )

        if not output_result.data:
            raise ValueError(f"Output {output_id} not found")

        output = output_result.data

        # Generate filename based on agent type and version
        agent_type = output["agent_type"]
        version = output["version"]
        filename = f"{agent_type}_output_v{version}.md"

        # Create document from output
        document = await upload_document(
            initiative_id=initiative_id,
            filename=filename,
            content=output["content_markdown"],
            user_id=None,  # System-generated
            document_type=f"{agent_type}_output",
            metadata={
                "source_output_id": output_id,
                "source_run_id": output["run_id"],
                "agent_type": agent_type,
                "version": version,
            },
        )

        # Update document with source_run_id
        await asyncio.to_thread(
            lambda: supabase.table("disco_documents")
            .update({"source_run_id": output["run_id"]})
            .eq("id", document["id"])
            .execute()
        )

        logger.info(f"Promoted output {output_id} to document {document['id']}")
        return document

    except Exception as e:
        logger.error(f"Error promoting output to document: {e}")
        raise


async def get_linked_document_names(initiative_id: str) -> List[Dict]:
    """Get list of linked KB document titles/filenames for context.

    This provides a list of all documents linked to an initiative,
    useful for answering meta-questions like "what documents do you have?"

    Args:
        initiative_id: Initiative UUID

    Returns:
        List of {id, filename, title} for each linked document
    """
    logger.info(f"Fetching linked document names for initiative {initiative_id}")

    try:
        # Get linked document IDs from junction table
        links_result = await asyncio.to_thread(
            lambda: supabase.table("disco_initiative_documents")
            .select("document_id")
            .eq("initiative_id", initiative_id)
            .execute()
        )

        if not links_result.data:
            logger.info("No linked KB documents found for initiative")
            return []

        doc_ids = [link["document_id"] for link in links_result.data]
        logger.info(f"Found {len(doc_ids)} linked KB documents")

        # Fetch document metadata from KB
        docs_result = await asyncio.to_thread(
            lambda: supabase.table("documents").select("id, filename, title").in_("id", doc_ids).execute()
        )

        return docs_result.data or []

    except Exception as e:
        logger.error(f"Error fetching linked document names: {e}")
        return []


async def search_linked_kb_docs(
    initiative_id: str, query: str, limit: int = 8, min_similarity: float = 0.2
) -> List[Dict]:
    """Vector search within KB documents linked to an initiative.

    Searches the main KB's document_chunks table for documents that are
    linked to this initiative via disco_initiative_documents junction table.

    Args:
        initiative_id: Initiative UUID
        query: Search query
        limit: Max results
        min_similarity: Minimum similarity threshold

    Returns:
        List of matching chunks with similarity scores
    """
    logger.info(f"Searching linked KB docs for initiative {initiative_id}: {query[:50]}...")

    try:
        # Get linked document IDs from junction table
        links_result = await asyncio.to_thread(
            lambda: supabase.table("disco_initiative_documents")
            .select("document_id")
            .eq("initiative_id", initiative_id)
            .execute()
        )

        if not links_result.data:
            logger.info("No linked KB documents found for initiative")
            return []

        doc_ids = [link["document_id"] for link in links_result.data]
        logger.info(f"Found {len(doc_ids)} linked KB documents")

        # Generate query embedding
        query_embedding = await asyncio.to_thread(
            lambda: generate_embeddings([query], input_type=EMBEDDING.INPUT_TYPE_QUERY)[0]
        )

        # Search document_chunks for linked documents using vector similarity
        # Using raw SQL via RPC since there's no built-in function for this specific case
        result = await asyncio.to_thread(
            lambda: supabase.rpc(
                "match_document_chunks_by_ids",
                {
                    "query_embedding": query_embedding,
                    "match_count": limit,
                    "match_threshold": min_similarity,
                    "p_document_ids": doc_ids,
                },
            ).execute()
        )

        chunks = result.data or []
        logger.info(f"Found {len(chunks)} matching chunks from linked KB docs")

        # Fetch document filenames for context
        if chunks:
            chunk_doc_ids = list({c["document_id"] for c in chunks})
            docs_result = await asyncio.to_thread(
                lambda: supabase.table("documents").select("id, filename, title").in_("id", chunk_doc_ids).execute()
            )
            doc_names = {d["id"]: d.get("title") or d.get("filename", "Unknown") for d in (docs_result.data or [])}

            for chunk in chunks:
                chunk["filename"] = doc_names.get(chunk["document_id"], "Unknown")

        return chunks

    except Exception as e:
        logger.error(f"Error searching linked KB docs: {e}")
        # Return empty list on error - don't fail the entire chat
        return []


async def get_all_initiative_content(initiative_id: str) -> str:
    """Get all document content for an initiative as a single string.

    Used for building agent context.

    Fetches content from linked KB documents (via disco_initiative_documents junction table).

    Args:
        initiative_id: Initiative UUID

    Returns:
        Concatenated document content
    """
    try:
        # Get linked KB document IDs
        links_result = await asyncio.to_thread(
            lambda: supabase.table("disco_initiative_documents")
            .select("document_id")
            .eq("initiative_id", initiative_id)
            .execute()
        )

        if not links_result.data:
            return ""

        doc_ids = [link["document_id"] for link in links_result.data]

        # Fetch document content from KB (document_chunks table)
        content_parts = []
        for doc_id in doc_ids:
            # Get document metadata
            doc_result = await asyncio.to_thread(
                lambda d=doc_id: supabase.table("documents").select("filename, title").eq("id", d).single().execute()
            )

            if not doc_result.data:
                continue

            doc = doc_result.data
            display_name = doc.get("title") or doc.get("filename", "Unknown")

            # Get document chunks (full content)
            chunks_result = await asyncio.to_thread(
                lambda d=doc_id: supabase.table("document_chunks")
                .select("content, chunk_index")
                .eq("document_id", d)
                .order("chunk_index")
                .execute()
            )

            if chunks_result.data:
                content_parts.append(f"\n\n=== {display_name} ===\n")
                # Concatenate all chunks
                for chunk in chunks_result.data:
                    content_parts.append(chunk["content"])

        return "\n".join(content_parts)

    except Exception as e:
        logger.error(f"Error getting initiative content: {e}")
        return ""
