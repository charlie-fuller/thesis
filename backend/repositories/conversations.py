"""Repository for conversation-related collections.

Collections: conversations, messages, message_documents.
"""

import pb_client as pb


# ---------------------------------------------------------------------------
# conversations
# ---------------------------------------------------------------------------

def list_conversations(*, agent_id: str = "", sort: str = "-updated",
                       limit: int = 0, offset: int = 0) -> list[dict]:
    parts = []
    if agent_id:
        parts.append(f"agent_id='{pb.escape_filter(agent_id)}'")
    filter_str = " && ".join(parts)
    if limit:
        page = (offset // limit) + 1 if limit else 1
        result = pb.list_records("conversations", filter=filter_str, sort=sort, page=page, per_page=limit)
        return result.get("items", [])
    return pb.get_all("conversations", filter=filter_str, sort=sort)


def get_conversation(conversation_id: str) -> dict | None:
    return pb.get_record("conversations", conversation_id)


def create_conversation(data: dict) -> dict:
    data.pop("client_id", None)
    data.pop("user_id", None)
    return pb.create_record("conversations", data)


def update_conversation(conversation_id: str, data: dict) -> dict:
    return pb.update_record("conversations", conversation_id, data)


def delete_conversation(conversation_id: str) -> None:
    pb.delete_record("conversations", conversation_id)


# ---------------------------------------------------------------------------
# messages
# ---------------------------------------------------------------------------

def get_conversation_messages(conversation_id: str) -> list[dict]:
    """Get all messages for a conversation, sorted by created ascending."""
    return pb.get_all(
        "messages",
        filter=f"conversation_id='{pb.escape_filter(conversation_id)}'",
        sort="created",
    )


def get_message(message_id: str) -> dict | None:
    return pb.get_record("messages", message_id)


def create_message(data: dict) -> dict:
    return pb.create_record("messages", data)


def update_message(message_id: str, data: dict) -> dict:
    return pb.update_record("messages", message_id, data)


def delete_message(message_id: str) -> None:
    pb.delete_record("messages", message_id)


# ---------------------------------------------------------------------------
# message_documents
# ---------------------------------------------------------------------------

def get_message_documents(message_id: str) -> list[dict]:
    return pb.get_all(
        "message_documents",
        filter=f"message_id='{pb.escape_filter(message_id)}'",
        sort="created",
    )


def link_message_document(message_id: str, document_id: str) -> dict:
    return pb.create_record("message_documents", {
        "message_id": message_id,
        "document_id": document_id,
    })


def unlink_message_document(message_id: str, document_id: str) -> None:
    record = pb.get_first(
        "message_documents",
        filter=f"message_id='{pb.escape_filter(message_id)}' && document_id='{pb.escape_filter(document_id)}'",
    )
    if record:
        pb.delete_record("message_documents", record["id"])
