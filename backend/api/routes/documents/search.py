"""Document search and tag-based selection routes."""

from collections import Counter, defaultdict
from typing import Optional

from fastapi import APIRouter, HTTPException

import pb_client as pb
from logger_config import get_logger
from repositories import documents as doc_repo
from validation import validate_uuid

from ._shared import BatchTagsRequest, BulkTagsRequest

logger = get_logger(__name__)
router = APIRouter()


@router.get("/pending-reviews")
async def get_pending_classification_reviews():
    """Get all documents with pending classification reviews."""
    try:
        classifications = pb.get_all(
            "document_classifications",
            filter="requires_user_review=true && status='needs_review'",
            sort="-created",
        )

        pending_reviews = []
        for item in classifications:
            doc = pb.get_record("documents", item["document_id"])
            if not doc:
                continue

            pending_reviews.append(
                {
                    "document_id": item["document_id"],
                    "filename": doc.get("filename"),
                    "detected_type": item.get("detected_type"),
                    "review_reason": item.get("review_reason"),
                    "suggested_agents": pb.parse_json_field(item.get("raw_scores"), {}),
                    "created_at": item.get("created"),
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
):
    """Get all tags with document counts, with optional search and pagination."""
    try:
        all_docs = pb.get_all("documents", fields="tags_cache")

        if not all_docs:
            return {"success": True, "tags": [], "hasMore": False}

        tag_counts: Counter = Counter()
        for doc in all_docs:
            tags_list = pb.parse_json_field(doc.get("tags_cache"), [])
            for tag in tags_list:
                if search and search.lower() not in tag.lower():
                    continue
                tag_counts[tag] += 1

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
):
    """Get tags for multiple documents in a single request."""
    try:
        if not request.document_ids:
            return {"success": True, "tags": {}}

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

        # Fetch tags for each document
        tags_by_doc: dict = {}
        for doc_id in valid_doc_ids:
            tags = doc_repo.list_document_tags(doc_id)
            tags_by_doc[doc_id] = [
                {"tag": t["tag"], "source": t.get("source", "")} for t in tags
            ]

        return {"success": True, "tags": tags_by_doc}

    except Exception as e:
        logger.error(f"Error getting batch tags: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/by-tags")
async def get_documents_by_tags(
    tags: str,
):
    """Get documents that have ALL specified tags (AND logic)."""
    try:
        if not tags or not tags.strip():
            raise HTTPException(status_code=400, detail="At least one tag is required")

        tag_list = [t.strip() for t in tags.split(",") if t.strip()]

        if not tag_list:
            raise HTTPException(status_code=400, detail="At least one valid tag is required")

        first_tag = tag_list[0]

        # Get docs with first tag
        first_tag_records = pb.get_all(
            "document_tags",
            filter=f"tag='{pb.escape_filter(first_tag)}'",
        )

        if not first_tag_records:
            return {"success": True, "tags": tag_list, "count": 0, "documents": []}

        candidate_ids = [row["document_id"] for row in first_tag_records]

        # Narrow by additional tags
        if len(tag_list) > 1:
            for additional_tag in tag_list[1:]:
                tag_records = pb.get_all(
                    "document_tags",
                    filter=f"tag='{pb.escape_filter(additional_tag)}'",
                )
                tag_doc_ids = {row["document_id"] for row in tag_records}
                candidate_ids = [did for did in candidate_ids if did in tag_doc_ids]

                if not candidate_ids:
                    return {
                        "success": True,
                        "tags": tag_list,
                        "count": 0,
                        "documents": [],
                    }

        # Fetch documents
        docs = []
        for doc_id in candidate_ids:
            doc = doc_repo.get_document(doc_id)
            if doc:
                docs.append(doc)

        if not docs:
            return {"success": True, "tags": tag_list, "count": 0, "documents": []}

        # Fetch chunks for each document
        chunks_by_doc: dict = defaultdict(list)
        for doc in docs:
            chunks = doc_repo.list_document_chunks(doc["id"])
            chunks_by_doc[doc["id"]] = chunks

        docs_with_content = []
        for doc in docs:
            doc_chunks = chunks_by_doc.get(doc["id"], [])
            doc_chunks.sort(key=lambda c: c.get("chunk_index", 0))
            content = "\n".join([c["content"] for c in doc_chunks])

            docs_with_content.append(
                {
                    "id": doc["id"],
                    "filename": doc.get("filename"),
                    "title": doc.get("title"),
                    "obsidian_file_path": doc.get("obsidian_file_path"),
                    "uploaded_at": doc.get("uploaded_at"),
                    "content": content,
                    "tags": pb.parse_json_field(doc.get("tags_cache"), []),
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
):
    """Add or remove tags from multiple documents."""
    try:
        if request.operation not in ["add", "remove"]:
            raise HTTPException(status_code=400, detail="Operation must be 'add' or 'remove'")

        if not request.document_ids:
            raise HTTPException(status_code=400, detail="At least one document_id is required")

        if not request.tags:
            raise HTTPException(status_code=400, detail="At least one tag is required")

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

        # Verify documents exist
        authorized_doc_ids = []
        for doc_id in valid_doc_ids:
            doc = doc_repo.get_document(doc_id)
            if not doc:
                results["failed"] += 1
                results["errors"].append({"document_id": doc_id, "error": "Not found"})
            else:
                authorized_doc_ids.append(doc_id)

        # Clean tags list
        clean_tags = [t.strip() for t in request.tags if t.strip()]

        if authorized_doc_ids and clean_tags:
            if request.operation == "add":
                for doc_id in authorized_doc_ids:
                    existing_tags = doc_repo.list_document_tags(doc_id)
                    existing_tag_names = {t["tag"] for t in existing_tags}
                    for tag in clean_tags:
                        if tag not in existing_tag_names:
                            doc_repo.create_document_tag(
                                {
                                    "document_id": doc_id,
                                    "tag": tag,
                                    "source": "manual",
                                }
                            )

            else:  # remove operation
                for doc_id in authorized_doc_ids:
                    existing_tags = doc_repo.list_document_tags(doc_id)
                    for tag_record in existing_tags:
                        if tag_record["tag"] in clean_tags and tag_record.get("source") == "manual":
                            doc_repo.delete_document_tag(tag_record["id"])

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
        # Build filter
        filter_parts = []

        if source and source.strip():
            filter_parts.append(f"source_platform='{pb.escape_filter(source.strip())}'")

        if folder and folder.strip():
            filter_parts.append(f"obsidian_file_path~'{pb.escape_filter(folder.strip())}/%'")

        if q and q.strip():
            search_term = pb.escape_filter(q.strip())
            filter_parts.append(
                f"(filename~'{search_term}' || title~'{search_term}')"
            )

        filter_str = " && ".join(filter_parts)

        # Build sort
        sort_field = sort.strip().lower() if sort else "recent"
        if sort_field == "oldest":
            pb_sort = "uploaded_at"
        elif sort_field == "name_asc":
            pb_sort = "filename"
        elif sort_field == "name_desc":
            pb_sort = "-filename"
        else:  # default to 'recent'
            pb_sort = "-uploaded_at"

        # Fetch total count
        total_count = pb.count("documents", filter=filter_str)

        # Paginate
        page = (offset // limit) + 1 if limit else 1
        result = pb.list_records(
            "documents",
            filter=filter_str,
            sort=pb_sort,
            page=page,
            per_page=limit,
        )
        documents = result.get("items", [])

        # Filter by tags in-memory (PocketBase JSON array contains)
        if tags:
            tag_list = [t.strip() for t in tags.split(",") if t.strip()]
            if tag_list:
                filtered = []
                for doc in documents:
                    doc_tags = pb.parse_json_field(doc.get("tags_cache"), [])
                    if all(tag in doc_tags for tag in tag_list):
                        filtered.append(doc)
                documents = filtered
                # Adjust count for tag filtering (approximate)
                total_count = len(documents) if len(documents) < limit else total_count

        for doc in documents:
            doc["tags"] = pb.parse_json_field(doc.get("tags_cache"), [])
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
):
    """Get all KB documents from a specific Obsidian folder path."""
    try:
        if not folder_path or not folder_path.strip():
            raise HTTPException(status_code=400, detail="folder_path is required")

        folder_path = folder_path.strip()

        documents = pb.get_all(
            "documents",
            filter=f"source_platform='obsidian' && obsidian_file_path~'{pb.escape_filter(folder_path)}%'",
            sort="obsidian_file_path",
        )

        if not documents:
            return {
                "success": True,
                "folder_path": folder_path,
                "count": 0,
                "documents": [],
            }

        # Fetch chunks for each document
        chunks_by_doc: dict = defaultdict(list)
        for doc in documents:
            chunks = doc_repo.list_document_chunks(doc["id"])
            chunks_by_doc[doc["id"]] = chunks

        docs_with_content = []
        for doc in documents:
            doc_chunks = chunks_by_doc.get(doc["id"], [])
            doc_chunks.sort(key=lambda c: c.get("chunk_index", 0))
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
async def get_obsidian_folders():
    """Get unique Obsidian folder paths for the current user with document counts."""
    try:
        all_docs = pb.get_all(
            "documents",
            filter="source_platform='obsidian' && obsidian_file_path!=''",
        )

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
