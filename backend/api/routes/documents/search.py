"""Document search and tag-based selection routes."""

import asyncio
import json
from collections import Counter, defaultdict
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from auth import get_current_user
from database import get_supabase
from logger_config import get_logger
from validation import validate_uuid

from ._shared import BatchTagsRequest, BulkTagsRequest

logger = get_logger(__name__)
router = APIRouter()
supabase = get_supabase()


@router.get("/pending-reviews")
async def get_pending_classification_reviews(
    current_user: dict = Depends(get_current_user),
):
    """Get all documents with pending classification reviews."""
    try:
        result = await asyncio.to_thread(
            lambda: supabase.table("document_classifications")
            .select(
                "document_id, detected_type, review_reason, raw_scores, created_at, "
                "documents(id, filename, uploaded_by)"
            )
            .eq("requires_user_review", True)
            .eq("status", "needs_review")
            .order("created_at", desc=True)
            .execute()
        )

        pending_reviews = []
        for item in result.data or []:
            doc = item.get("documents")
            if not doc:
                continue

            pending_reviews.append(
                {
                    "document_id": item["document_id"],
                    "filename": doc.get("filename"),
                    "detected_type": item.get("detected_type"),
                    "review_reason": item.get("review_reason"),
                    "suggested_agents": item.get("raw_scores", {}),
                    "created_at": item.get("created_at"),
                }
            )

        return {
            "success": True,
            "pending_reviews": pending_reviews,
            "count": len(pending_reviews),
        }

    except Exception as e:
        logger.warning(f"Error getting pending reviews (returning empty): {e}")
        return {"success": True, "pending_reviews": [], "count": 0}


@router.get("/tags")
async def get_all_tags(
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
):
    """Get all tags with document counts, with optional search and pagination."""
    try:
        user_id = current_user["id"]

        docs_result = await asyncio.to_thread(
            lambda: supabase.table("documents").select("tags_cache").eq("uploaded_by", user_id).execute()
        )

        if not docs_result.data:
            logger.info(f"No documents found for user {user_id}")
            return {"success": True, "tags": [], "hasMore": False}

        tag_counts: Counter = Counter()
        for doc in docs_result.data:
            tags_list = doc.get("tags_cache") or []
            for tag in tags_list:
                if search and search.lower() not in tag.lower():
                    continue
                tag_counts[tag] += 1

        logger.info(
            f"Found {sum(tag_counts.values())} tag entries for user {user_id} across {len(docs_result.data)} documents"
        )

        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[0].lower())
        paginated = sorted_tags[offset : offset + limit + 1]

        has_more = len(paginated) > limit
        if has_more:
            paginated = paginated[:limit]

        tags = [{"tag": t[0], "count": t[1]} for t in paginated]

        return {"success": True, "tags": tags, "hasMore": has_more}

    except Exception as e:
        logger.error(f"Error getting tags: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/tags/batch")
async def get_tags_batch(
    request: BatchTagsRequest,
    current_user: dict = Depends(get_current_user),
):
    """Get tags for multiple documents in a single request."""
    try:
        if not request.document_ids:
            return {"success": True, "tags": {}}

        user_id = current_user["id"]

        valid_doc_ids = []
        for doc_id in request.document_ids:
            try:
                validate_uuid(doc_id, "document_id")
                valid_doc_ids.append(doc_id)
            except Exception:
                continue

        if not valid_doc_ids:
            return {"success": True, "tags": {}}

        valid_doc_ids = valid_doc_ids[:100]

        docs_result = await asyncio.to_thread(
            lambda: supabase.table("documents")
            .select("id")
            .eq("uploaded_by", user_id)
            .in_("id", valid_doc_ids)
            .execute()
        )

        owned_doc_ids = [doc["id"] for doc in (docs_result.data or [])]

        if not owned_doc_ids:
            return {"success": True, "tags": {}}

        tags_result = await asyncio.to_thread(
            lambda: supabase.table("document_tags")
            .select("document_id, tag, source")
            .in_("document_id", owned_doc_ids)
            .execute()
        )

        tags_by_doc: dict = {}
        for tag_record in tags_result.data or []:
            doc_id = tag_record["document_id"]
            if doc_id not in tags_by_doc:
                tags_by_doc[doc_id] = []
            tags_by_doc[doc_id].append({"tag": tag_record["tag"], "source": tag_record["source"]})

        for doc_id in owned_doc_ids:
            if doc_id not in tags_by_doc:
                tags_by_doc[doc_id] = []

        return {"success": True, "tags": tags_by_doc}

    except Exception as e:
        logger.error(f"Error getting batch tags: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/by-tags")
async def get_documents_by_tags(
    tags: str,
    current_user: dict = Depends(get_current_user),
):
    """Get documents that have ALL specified tags (AND logic)."""
    try:
        if not tags or not tags.strip():
            raise HTTPException(status_code=400, detail="At least one tag is required")

        user_id = current_user["id"]
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]

        if not tag_list:
            raise HTTPException(status_code=400, detail="At least one valid tag is required")

        first_tag = tag_list[0]

        result = await asyncio.to_thread(
            lambda: supabase.table("document_tags")
            .select("document_id, documents!inner(id, filename, title, uploaded_by)")
            .eq("tag", first_tag)
            .eq("documents.uploaded_by", user_id)
            .execute()
        )

        if not result.data:
            return {"success": True, "tags": tag_list, "count": 0, "documents": []}

        candidate_ids = [row["document_id"] for row in result.data]

        if len(tag_list) > 1:
            for additional_tag in tag_list[1:]:
                tag_result = await asyncio.to_thread(
                    lambda t=additional_tag, cids=candidate_ids: supabase.table("document_tags")
                    .select("document_id")
                    .eq("tag", t)
                    .in_("document_id", cids)
                    .execute()
                )
                tag_doc_ids = {row["document_id"] for row in (tag_result.data or [])}
                candidate_ids = [did for did in candidate_ids if did in tag_doc_ids]

                if not candidate_ids:
                    return {
                        "success": True,
                        "tags": tag_list,
                        "count": 0,
                        "documents": [],
                    }

        docs_result = await asyncio.to_thread(
            lambda: supabase.table("documents")
            .select("id, filename, title, obsidian_file_path, uploaded_at, tags_cache")
            .in_("id", candidate_ids)
            .execute()
        )

        if not docs_result.data:
            return {"success": True, "tags": tag_list, "count": 0, "documents": []}

        chunks_result = await asyncio.to_thread(
            lambda: supabase.table("document_chunks")
            .select("document_id, content, chunk_index")
            .in_("document_id", candidate_ids)
            .order("chunk_index")
            .execute()
        )

        chunks_by_doc: dict = defaultdict(list)
        for chunk in chunks_result.data or []:
            chunks_by_doc[chunk["document_id"]].append(chunk)

        docs_with_content = []
        for doc in docs_result.data:
            doc_chunks = chunks_by_doc.get(doc["id"], [])
            doc_chunks.sort(key=lambda c: c["chunk_index"])
            content = "\n".join([c["content"] for c in doc_chunks])

            docs_with_content.append(
                {
                    "id": doc["id"],
                    "filename": doc.get("filename"),
                    "title": doc.get("title"),
                    "obsidian_file_path": doc.get("obsidian_file_path"),
                    "uploaded_at": doc.get("uploaded_at"),
                    "content": content,
                    "tags": doc.get("tags_cache") or [],
                }
            )

        return {
            "success": True,
            "tags": tag_list,
            "count": len(docs_with_content),
            "documents": docs_with_content,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting documents by tags: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/bulk-tags")
async def bulk_tag_operation(
    request: BulkTagsRequest,
    current_user: dict = Depends(get_current_user),
):
    """Add or remove tags from multiple documents."""
    try:
        if request.operation not in ["add", "remove"]:
            raise HTTPException(status_code=400, detail="Operation must be 'add' or 'remove'")

        if not request.document_ids:
            raise HTTPException(status_code=400, detail="At least one document_id is required")

        if not request.tags:
            raise HTTPException(status_code=400, detail="At least one tag is required")

        user_id = current_user["id"]
        is_admin = current_user.get("role") == "admin"
        results = {"success": 0, "failed": 0, "errors": []}

        # Validate all UUIDs first
        valid_doc_ids = []
        for doc_id in request.document_ids:
            try:
                validate_uuid(doc_id, "document_id")
                valid_doc_ids.append(doc_id)
            except Exception:
                results["failed"] += 1
                results["errors"].append({"document_id": doc_id, "error": "Invalid UUID"})

        if not valid_doc_ids:
            return {
                "success": True,
                "operation": request.operation,
                "tags": request.tags,
                "results": results,
            }

        # Batch fetch all documents in one query
        docs_result = await asyncio.to_thread(
            lambda: supabase.table("documents").select("id, uploaded_by").in_("id", valid_doc_ids).execute()
        )

        docs_by_id = {d["id"]: d for d in (docs_result.data or [])}

        # Filter authorized documents
        authorized_doc_ids = []
        for doc_id in valid_doc_ids:
            doc = docs_by_id.get(doc_id)
            if not doc:
                results["failed"] += 1
                results["errors"].append({"document_id": doc_id, "error": "Not found"})
            elif not is_admin and doc["uploaded_by"] != user_id:
                results["failed"] += 1
                results["errors"].append({"document_id": doc_id, "error": "Not authorized"})
            else:
                authorized_doc_ids.append(doc_id)

        # Clean tags list
        clean_tags = [t.strip() for t in request.tags if t.strip()]

        if authorized_doc_ids and clean_tags:
            if request.operation == "add":
                # Batch fetch existing tags for all authorized documents
                existing_result = await asyncio.to_thread(
                    lambda: supabase.table("document_tags")
                    .select("document_id, tag")
                    .in_("document_id", authorized_doc_ids)
                    .in_("tag", clean_tags)
                    .execute()
                )

                # Track existing document-tag pairs
                existing_pairs = {(r["document_id"], r["tag"]) for r in (existing_result.data or [])}

                # Build list of new tags to insert
                new_tags = []
                for doc_id in authorized_doc_ids:
                    for tag in clean_tags:
                        if (doc_id, tag) not in existing_pairs:
                            new_tags.append(
                                {
                                    "document_id": doc_id,
                                    "tag": tag,
                                    "source": "manual",
                                }
                            )

                # Batch insert new tags
                if new_tags:
                    await asyncio.to_thread(lambda: supabase.table("document_tags").insert(new_tags).execute())

            else:  # remove operation
                # Batch delete tags - need to do this per tag since we can't combine
                # multiple .eq() conditions with .in_() for different columns
                for tag in clean_tags:
                    await asyncio.to_thread(
                        lambda t=tag: supabase.table("document_tags")
                        .delete()
                        .in_("document_id", authorized_doc_ids)
                        .eq("tag", t)
                        .eq("source", "manual")
                        .execute()
                    )

            results["success"] = len(authorized_doc_ids)

        logger.info(
            f"Bulk tag operation: {request.operation} {request.tags} on "
            f"{len(request.document_ids)} docs - success: {results['success']}, "
            f"failed: {results['failed']}"
        )

        return {
            "success": True,
            "operation": request.operation,
            "tags": request.tags,
            "results": results,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk tag operation: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/search")
async def search_documents(
    q: Optional[str] = None,
    tags: Optional[str] = None,
    sort: Optional[str] = None,
    source: Optional[str] = None,
    folder: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
):
    """Search KB documents by filename, title, content, and/or tags.

    Args:
        q: Search query for filename/title
        tags: Comma-separated list of tags to filter by
        sort: Sort order - 'recent' (default), 'oldest', 'name_asc', 'name_desc'
        source: Filter by source platform - 'obsidian', 'google_drive', 'upload'
        folder: Filter by Obsidian folder path prefix
        limit: Number of results per page
        offset: Pagination offset
    """
    try:
        user_id = current_user["id"]

        query = (
            supabase.table("documents")
            .select(
                "id, filename, title, obsidian_file_path, uploaded_at, original_date, source_platform, "
                "processed, processing_status, processing_error, storage_url, external_url, "
                "file_size, sync_cadence, google_drive_file_id, tags_cache",
                count="exact",
            )
            .eq("uploaded_by", user_id)
        )

        # Apply source platform filter
        if source and source.strip():
            query = query.eq("source_platform", source.strip())

        # Apply folder path filter
        if folder and folder.strip():
            query = query.ilike("obsidian_file_path", f"{folder.strip()}/%")

        # Apply sort order - use uploaded_at as primary for recency (most recently added),
        # with original_date as secondary for documents uploaded at the same time
        sort_field = sort.strip().lower() if sort else "recent"
        if sort_field == "oldest":
            query = query.order("uploaded_at", desc=False).order("original_date", desc=False, nullsfirst=False)
        elif sort_field == "name_asc":
            query = query.order("filename", desc=False)
        elif sort_field == "name_desc":
            query = query.order("filename", desc=True)
        else:  # default to 'recent'
            query = query.order("uploaded_at", desc=True).order("original_date", desc=True, nullsfirst=False)

        if q and q.strip():
            search_term = q.strip()
            query = query.or_(f"filename.ilike.%{search_term}%,title.ilike.%{search_term}%")

        if tags:
            tag_list = [t.strip() for t in tags.split(",") if t.strip()]
            for tag in tag_list:
                query = query.contains("tags_cache", json.dumps([tag]))

        query = query.range(offset, offset + limit - 1)

        result = await asyncio.to_thread(lambda: query.execute())
        documents = result.data or []
        total_count = result.count if result.count is not None else len(documents)

        for doc in documents:
            doc["tags"] = doc.get("tags_cache") or []
            doc.pop("tags_cache", None)

        return {
            "success": True,
            "query": q,
            "tag_filter": tags,
            "total_count": total_count,
            "count": len(documents),
            "documents": documents,
            "hasMore": offset + limit < total_count,
        }

    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/by-folder")
async def get_documents_by_folder(
    folder_path: str,
    current_user: dict = Depends(get_current_user),
):
    """Get all KB documents from a specific Obsidian folder path."""
    try:
        if not folder_path or not folder_path.strip():
            raise HTTPException(status_code=400, detail="folder_path is required")

        folder_path = folder_path.strip()

        result = await asyncio.to_thread(
            lambda: supabase.table("documents")
            .select("id, filename, title, obsidian_file_path, source_platform, uploaded_at, storage_url")
            .eq("source_platform", "obsidian")
            .eq("uploaded_by", current_user["id"])
            .ilike("obsidian_file_path", f"{folder_path}%")
            .order("obsidian_file_path")
            .execute()
        )

        documents = result.data or []

        if not documents:
            return {
                "success": True,
                "folder_path": folder_path,
                "count": 0,
                "documents": [],
            }

        doc_ids = [d["id"] for d in documents]
        chunks_result = await asyncio.to_thread(
            lambda: supabase.table("document_chunks")
            .select("document_id, content, chunk_index")
            .in_("document_id", doc_ids)
            .order("chunk_index")
            .execute()
        )

        chunks_by_doc: dict = defaultdict(list)
        for chunk in chunks_result.data or []:
            chunks_by_doc[chunk["document_id"]].append(chunk)

        docs_with_content = []
        for doc in documents:
            doc_chunks = chunks_by_doc.get(doc["id"], [])
            doc_chunks.sort(key=lambda c: c["chunk_index"])
            content = "\n".join([c["content"] for c in doc_chunks])
            docs_with_content.append({**doc, "content": content})

        return {
            "success": True,
            "folder_path": folder_path,
            "count": len(docs_with_content),
            "documents": docs_with_content,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching documents by folder: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/folders")
async def get_obsidian_folders(current_user: dict = Depends(get_current_user)):
    """Get unique Obsidian folder paths for the current user with document counts."""
    try:
        # Fetch all documents - Supabase defaults to 1000 row limit,
        # so we need to paginate to get complete folder tree
        all_docs = []
        page_size = 1000
        offset = 0
        while True:
            page = await asyncio.to_thread(
                lambda off=offset: supabase.table("documents")
                .select("obsidian_file_path")
                .eq("source_platform", "obsidian")
                .eq("uploaded_by", current_user["id"])
                .not_.is_("obsidian_file_path", "null")
                .range(off, off + page_size - 1)
                .execute()
            )
            rows = page.data or []
            all_docs.extend(rows)
            if len(rows) < page_size:
                break
            offset += page_size

        folders = set()
        folder_counts: Counter = Counter()
        for doc in all_docs:
            path = doc.get("obsidian_file_path", "")
            if path and "/" in path:
                if "github" in path.lower():
                    continue
                parts = path.split("/")
                # Count this doc for every ancestor folder
                for i in range(1, len(parts)):
                    folder_path = "/".join(parts[:i])
                    if "github" not in folder_path.lower():
                        folders.add(folder_path)
                        folder_counts[folder_path] += 1

        sorted_folders = sorted(folders)

        return {
            "success": True,
            "folders": [{"path": f, "count": folder_counts.get(f, 0)} for f in sorted_folders],
        }

    except Exception as e:
        logger.error(f"Error fetching Obsidian folders: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e
