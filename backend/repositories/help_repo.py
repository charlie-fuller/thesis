"""Repository for help-related collections.

Named help_repo.py to avoid shadowing the Python builtin help().

Collections: help_documents, help_chunks, help_conversations, help_messages.
"""

import pb_client as pb
import vec_client as vec


# ---------------------------------------------------------------------------
# help_documents
# ---------------------------------------------------------------------------

def list_help_documents(*, sort: str = "-updated") -> list[dict]:
    return pb.get_all("help_documents", sort=sort)


def get_help_document(document_id: str) -> dict | None:
    return pb.get_record("help_documents", document_id)


def create_help_document(data: dict) -> dict:
    return pb.create_record("help_documents", data)


def update_help_document(document_id: str, data: dict) -> dict:
    return pb.update_record("help_documents", document_id, data)


def delete_help_document(document_id: str) -> None:
    pb.delete_record("help_documents", document_id)


def search_help(query: str, limit: int = 5) -> list[dict]:
    """Search help documents via vector similarity on help_chunks."""
    return vec.search("help_chunks", query, limit=limit)


# ---------------------------------------------------------------------------
# help_chunks
# ---------------------------------------------------------------------------

def list_help_chunks(document_id: str) -> list[dict]:
    return pb.get_all(
        "help_chunks",
        filter=f"document_id='{pb.escape_filter(document_id)}'",
        sort="chunk_index",
    )


def get_help_chunk(chunk_id: str) -> dict | None:
    return pb.get_record("help_chunks", chunk_id)


def create_help_chunk(data: dict) -> dict:
    return pb.create_record("help_chunks", data)


def delete_help_chunk(chunk_id: str) -> None:
    pb.delete_record("help_chunks", chunk_id)


# ---------------------------------------------------------------------------
# help_conversations
# ---------------------------------------------------------------------------

def list_help_conversations(*, sort: str = "-created", limit: int = 50) -> list[dict]:
    result = pb.list_records("help_conversations", sort=sort, per_page=limit)
    return result.get("items", [])


def get_help_conversation(conversation_id: str) -> dict | None:
    return pb.get_record("help_conversations", conversation_id)


def create_help_conversation(data: dict) -> dict:
    data.pop("client_id", None)
    data.pop("user_id", None)
    return pb.create_record("help_conversations", data)


def update_help_conversation(conversation_id: str, data: dict) -> dict:
    return pb.update_record("help_conversations", conversation_id, data)


def delete_help_conversation(conversation_id: str) -> None:
    pb.delete_record("help_conversations", conversation_id)


# ---------------------------------------------------------------------------
# help_messages
# ---------------------------------------------------------------------------

def list_help_messages(conversation_id: str) -> list[dict]:
    return pb.get_all(
        "help_messages",
        filter=f"conversation_id='{pb.escape_filter(conversation_id)}'",
        sort="created",
    )


def get_help_message(message_id: str) -> dict | None:
    return pb.get_record("help_messages", message_id)


def create_help_message(data: dict) -> dict:
    return pb.create_record("help_messages", data)


def update_help_message(message_id: str, data: dict) -> dict:
    return pb.update_record("help_messages", message_id, data)


def delete_help_message(message_id: str) -> None:
    pb.delete_record("help_messages", message_id)
