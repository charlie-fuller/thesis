"""Repository for document-related collections.

Collections: documents, document_chunks, document_classifications, document_tags.
Embedding fields are skipped -- vector search is handled by vec_client.
"""

import pb_client as pb
import vec_client as vec


# ---------------------------------------------------------------------------
# documents
# ---------------------------------------------------------------------------

def list_documents(*, classification: str = "", sort: str = "-created",
                   limit: int = 0, offset: int = 0) -> list[dict]:
    parts = []
    if classification:
        parts.append(f"classification='{pb.escape_filter(classification)}'")
    filter_str = " && ".join(parts)
    if limit:
        page = (offset // limit) + 1 if limit else 1
        result = pb.list_records("documents", filter=filter_str, sort=sort, page=page, per_page=limit)
        return result.get("items", [])
    return pb.get_all("documents", filter=filter_str, sort=sort)


def get_document(document_id: str) -> dict | None:
    return pb.get_record("documents", document_id)


def create_document(data: dict) -> dict:
    data.pop("client_id", None)
    data.pop("user_id", None)
    return pb.create_record("documents", data)


def update_document(document_id: str, data: dict) -> dict:
    return pb.update_record("documents", document_id, data)


def delete_document(document_id: str) -> None:
    pb.delete_record("documents", document_id)


def search_documents(query: str, limit: int = 5) -> list[dict]:
    """Search documents via vector similarity on document_chunks, then fetch parent docs."""
    chunks = vec.search("document_chunks", query, limit=limit)
    doc_ids = list(dict.fromkeys(c.get("document_id") or c.get("record_id", "") for c in chunks))
    results = []
    for doc_id in doc_ids:
        doc = get_document(doc_id)
        if doc:
            results.append(doc)
    return results


# ---------------------------------------------------------------------------
# document_chunks
# ---------------------------------------------------------------------------

def list_document_chunks(document_id: str) -> list[dict]:
    return pb.get_all(
        "document_chunks",
        filter=f"document_id='{pb.escape_filter(document_id)}'",
        sort="chunk_index",
    )


def get_document_chunk(chunk_id: str) -> dict | None:
    return pb.get_record("document_chunks", chunk_id)


def create_document_chunk(data: dict) -> dict:
    return pb.create_record("document_chunks", data)


def delete_document_chunk(chunk_id: str) -> None:
    pb.delete_record("document_chunks", chunk_id)


# ---------------------------------------------------------------------------
# document_classifications
# ---------------------------------------------------------------------------

def list_document_classifications(document_id: str) -> list[dict]:
    return pb.get_all(
        "document_classifications",
        filter=f"document_id='{pb.escape_filter(document_id)}'",
        sort="-confidence",
    )


def get_document_classification(classification_id: str) -> dict | None:
    return pb.get_record("document_classifications", classification_id)


def create_document_classification(data: dict) -> dict:
    return pb.create_record("document_classifications", data)


def update_document_classification(classification_id: str, data: dict) -> dict:
    return pb.update_record("document_classifications", classification_id, data)


def delete_document_classification(classification_id: str) -> None:
    pb.delete_record("document_classifications", classification_id)


# ---------------------------------------------------------------------------
# document_tags
# ---------------------------------------------------------------------------

def list_document_tags(document_id: str) -> list[dict]:
    return pb.get_all(
        "document_tags",
        filter=f"document_id='{pb.escape_filter(document_id)}'",
        sort="tag",
    )


def get_document_tag(tag_id: str) -> dict | None:
    return pb.get_record("document_tags", tag_id)


def create_document_tag(data: dict) -> dict:
    return pb.create_record("document_tags", data)


def delete_document_tag(tag_id: str) -> None:
    pb.delete_record("document_tags", tag_id)
