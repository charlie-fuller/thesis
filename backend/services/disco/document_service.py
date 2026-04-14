"""PuRDy Document Service.

Handles document upload, chunking, embedding, and retrieval for PuRDy initiatives.
"""

from typing import Dict, List, Optional
from uuid import uuid4

import pb_client as pb
import repositories.disco as disco_repo
import repositories.documents as docs_repo
from config.constants import DATABASE, EMBEDDING, TEXT_CHUNKING
from document_processor import chunk_text, extract_text_from_file, generate_embeddings
from logger_config import get_logger

logger = get_logger(__name__)


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

    try:
        # Create document record
        doc_data = {
            "initiative_id": initiative_id,
            "filename": filename,
            "content": content,
            "document_type": document_type,
            "version": 1,
            "metadata": metadata or {},
        }
        document = disco_repo.create_document(doc_data)

        if not document:
            raise ValueError("Failed to create document")

        document_id = document["id"]

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
            embeddings = generate_embeddings(chunk_texts, input_type=EMBEDDING.INPUT_TYPE_DOCUMENT)
            logger.info(f"Generated {len(embeddings)} embeddings")

            # Store chunks with embeddings
            all_inserted = []
            for _i, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=False)):
                sanitized_content = chunk["content"].replace("\x00", "")
                chunk_data = {
                    "document_id": document_id,
                    "initiative_id": initiative_id,
                    "chunk_index": chunk["chunk_index"],
                    "content": sanitized_content,
                    "metadata": {"filename": filename, "chunk_size": len(sanitized_content)},
                }
                inserted = disco_repo.create_document_chunk(chunk_data)
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
                            "document_id": document_id,
                            "initiative_id": initiative_id,
                            "chunk_index": inserted_chunk.get("chunk_index", 0),
                        },
                    }
                )

            if pinecone_vectors:
                from services.pinecone_service import upsert_vectors

                upsert_vectors(vectors=pinecone_vectors, namespace="disco_document_chunks")

            logger.info(f"Stored {len(all_inserted)} chunks for document {document_id}")

        document["chunk_count"] = len(chunks)
        return document

    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        # Cleanup on failure
        try:
            if 'document_id' in dir():
                disco_repo.delete_document(document_id)
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
    content = extract_text_from_file(file_data, filename)

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
        filter_parts = [f"initiative_id='{pb.escape_filter(initiative_id)}'"]
        if document_type:
            filter_parts.append(f"document_type='{pb.escape_filter(document_type)}'")
        filter_str = " && ".join(filter_parts)

        page = (offset // limit) + 1 if limit else 1
        result = pb.list_records(
            "disco_documents",
            filter=filter_str,
            sort="-created",
            page=page,
            per_page=limit,
        )

        documents = result.get("items", [])
        total = result.get("totalItems", len(documents))

        return {"documents": documents, "total": total}

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
        doc = pb.get_first(
            "disco_documents",
            filter=f"id='{pb.escape_filter(document_id)}' && initiative_id='{pb.escape_filter(initiative_id)}'",
        )
        return doc
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

        # Delete document (PocketBase cascade rules handle chunks)
        pb.delete_record("disco_documents", document_id)

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
        query_embedding = generate_embeddings([query], input_type=EMBEDDING.INPUT_TYPE_QUERY)[0]

        # Try Pinecone first
        from services.pinecone_service import get_index, query_vectors

        if get_index() is not None:
            pc_filter = {"initiative_id": {"$eq": initiative_id}}
            matches = query_vectors(
                embedding=query_embedding,
                namespace="disco_document_chunks",
                top_k=limit,
                filter=pc_filter,
            )
            matches = [m for m in matches if m["score"] >= min_similarity]

            if matches:
                chunk_ids = [m["id"] for m in matches]
                scores_map = {m["id"]: m["score"] for m in matches}

                # Fetch chunks by IDs
                chunks = []
                for cid in chunk_ids:
                    try:
                        chunk = pb.get_record("disco_document_chunks", cid)
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

        logger.info(f"Found {len(chunks)} matching chunks")

        # Fetch document filenames for context
        if chunks:
            doc_ids = list({c["document_id"] for c in chunks})
            doc_names = {}
            for did in doc_ids:
                try:
                    doc = pb.get_first("disco_documents", filter=f"id='{pb.escape_filter(did)}'")
                    if doc:
                        doc_names[did] = doc.get("filename", "Unknown")
                except Exception:
                    pass

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
        output = pb.get_first(
            "disco_outputs",
            filter=f"id='{pb.escape_filter(output_id)}' && initiative_id='{pb.escape_filter(initiative_id)}'",
        )

        if not output:
            raise ValueError(f"Output {output_id} not found")

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
        pb.update_record(
            "disco_documents",
            document["id"],
            {"source_run_id": output["run_id"]},
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
        links = pb.get_all(
            "disco_initiative_documents",
            filter=f"initiative_id='{pb.escape_filter(initiative_id)}'",
        )

        if not links:
            logger.info("No linked KB documents found for initiative")
            return []

        doc_ids = [link["document_id"] for link in links]
        logger.info(f"Found {len(doc_ids)} linked KB documents")

        # Fetch document metadata from KB
        docs = []
        for did in doc_ids:
            try:
                doc = docs_repo.get_document(did)
                if doc:
                    docs.append({
                        "id": doc.get("id"),
                        "filename": doc.get("filename"),
                        "title": doc.get("title"),
                    })
            except Exception:
                pass

        return docs

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
        links = pb.get_all(
            "disco_initiative_documents",
            filter=f"initiative_id='{pb.escape_filter(initiative_id)}'",
        )

        if not links:
            logger.info("No linked KB documents found for initiative")
            return []

        doc_ids = [link["document_id"] for link in links]
        logger.info(f"Found {len(doc_ids)} linked KB documents")

        # Generate query embedding
        query_embedding = generate_embeddings([query], input_type=EMBEDDING.INPUT_TYPE_QUERY)[0]

        # Search document_chunks for linked documents using vector similarity
        from services.pinecone_service import get_index, query_vectors

        if get_index() is not None:
            pc_filter = {"document_id": {"$in": doc_ids}}
            matches = query_vectors(
                embedding=query_embedding,
                namespace="document_chunks",
                top_k=limit,
                filter=pc_filter,
            )
            matches = [m for m in matches if m["score"] >= min_similarity]

            if matches:
                chunk_ids = [m["id"] for m in matches]
                scores_map = {m["id"]: m["score"] for m in matches}

                # Fetch chunks by IDs
                chunks = []
                for cid in chunk_ids:
                    try:
                        chunk = pb.get_record("document_chunks", cid)
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

        logger.info(f"Found {len(chunks)} matching chunks from linked KB docs")

        # Fetch document filenames for context
        if chunks:
            chunk_doc_ids = list({c["document_id"] for c in chunks})
            doc_names = {}
            for did in chunk_doc_ids:
                try:
                    doc = docs_repo.get_document(did)
                    if doc:
                        doc_names[did] = doc.get("title") or doc.get("filename", "Unknown")
                except Exception:
                    pass

            for chunk in chunks:
                chunk["filename"] = doc_names.get(chunk["document_id"], "Unknown")

        return chunks

    except Exception as e:
        logger.error(f"Error searching linked KB docs: {e}")
        # Return empty list on error - don't fail the entire chat
        return []


async def get_all_initiative_content(initiative_id: str, max_chars: int = 500_000) -> str:
    """Get all document content for an initiative as a single string.

    Used for building agent context. Enforces a character budget to prevent
    exceeding model context limits (~150k tokens = 500k chars).

    Fetches content from linked KB documents (via disco_initiative_documents junction table).
    Documents are included in order until the budget is exhausted.

    Args:
        initiative_id: Initiative UUID
        max_chars: Maximum total characters to return (default 500k = ~150k tokens)

    Returns:
        Concatenated document content (truncated if over budget)
    """
    try:
        # Get linked KB document IDs
        links = pb.get_all(
            "disco_initiative_documents",
            filter=f"initiative_id='{pb.escape_filter(initiative_id)}'",
        )

        if not links:
            return ""

        linked_doc_ids = [link["document_id"] for link in links]

        # Fetch document dates for ordering by creation date (newest first)
        doc_dates = {}
        for did in linked_doc_ids:
            try:
                doc = docs_repo.get_document(did)
                if doc:
                    doc_dates[did] = doc.get("original_date") or doc.get("uploaded_at") or doc.get("created") or ""
            except Exception:
                pass

        # Sort by date, newest first
        doc_ids = sorted(linked_doc_ids, key=lambda did: doc_dates.get(did, ""), reverse=True)
        total_docs = len(doc_ids)

        # Fetch document content from KB (document_chunks table)
        content_parts = [
            "--- LINKED DOCUMENTS (ordered by date, newest first) ---\n"
            "Documents are presented in reverse chronological order. "
            "Newer documents represent the latest findings and should take priority "
            "when they update, refine, or contradict earlier material.\n"
        ]
        current_chars = sum(len(p) for p in content_parts)
        included_docs = 0

        for doc_id in doc_ids:
            # Get document metadata
            doc = docs_repo.get_document(doc_id)

            if not doc:
                continue

            display_name = doc.get("title") or doc.get("filename", "Unknown")
            doc_date = doc.get("original_date") or doc.get("uploaded_at") or doc.get("created", "")
            # Format date for display (just the date portion)
            if doc_date and "T" in str(doc_date):
                doc_date = str(doc_date).split("T")[0]

            # Get document chunks (full content)
            chunks = docs_repo.list_document_chunks(doc_id, sort="chunk_index")

            if chunks:
                # Calculate this document's size before adding
                date_suffix = f" ({doc_date})" if doc_date else ""
                doc_position = f"[{included_docs + 1}/{total_docs}]"
                doc_header = f"\n\n=== {doc_position} {display_name}{date_suffix} ===\n"
                doc_content = "\n".join(chunk["content"] for chunk in chunks)
                doc_size = len(doc_header) + len(doc_content)

                if current_chars + doc_size > max_chars:
                    # Budget exceeded - stop adding documents
                    skipped = total_docs - included_docs
                    content_parts.append(
                        f"\n\n--- CONTEXT BUDGET REACHED ---\n"
                        f"{skipped} of {total_docs} documents omitted to stay within model context limits.\n"
                        f"To include specific documents, reduce the number linked to this initiative."
                    )
                    break

                content_parts.append(doc_header)
                content_parts.append(doc_content)
                current_chars += doc_size
                included_docs += 1

        if included_docs > 0:
            logger.info(
                f"Initiative {initiative_id}: included {included_docs}/{total_docs} documents ({current_chars:,} chars)"
            )

        return "\n".join(content_parts)

    except Exception as e:
        logger.error(f"Error getting initiative content: {e}")
        return ""
