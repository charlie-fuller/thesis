"""Repository for PuRDy-related collections.

Collections: purdy_sessions, purdy_runs, purdy_outputs, purdy_documents,
purdy_document_chunks, purdy_conversations, purdy_messages,
purdy_checkpoints, purdy_session_folders, purdy_session_members,
purdy_prds.
"""

import pb_client as pb


# ---------------------------------------------------------------------------
# purdy_sessions
# ---------------------------------------------------------------------------

def list_sessions(*, status: str = "", sort: str = "-updated") -> list[dict]:
    parts = []
    if status:
        parts.append(f"status='{pb.escape_filter(status)}'")
    return pb.get_all("purdy_sessions", filter=" && ".join(parts), sort=sort)


def get_session(session_id: str) -> dict | None:
    return pb.get_record("purdy_sessions", session_id)


def create_session(data: dict) -> dict:
    data.pop("client_id", None)
    data.pop("user_id", None)
    return pb.create_record("purdy_sessions", data)


def update_session(session_id: str, data: dict) -> dict:
    return pb.update_record("purdy_sessions", session_id, data)


# ---------------------------------------------------------------------------
# purdy_runs
# ---------------------------------------------------------------------------

def list_runs(session_id: str, *, sort: str = "-created") -> list[dict]:
    return pb.get_all(
        "purdy_runs",
        filter=f"session_id='{pb.escape_filter(session_id)}'",
        sort=sort,
    )


def get_run(run_id: str) -> dict | None:
    return pb.get_record("purdy_runs", run_id)


def create_run(data: dict) -> dict:
    return pb.create_record("purdy_runs", data)


def update_run(run_id: str, data: dict) -> dict:
    return pb.update_record("purdy_runs", run_id, data)


# ---------------------------------------------------------------------------
# purdy_outputs
# ---------------------------------------------------------------------------

def list_outputs(session_id: str, *, agent_type: str = "",
                 sort: str = "-created") -> list[dict]:
    esc = pb.escape_filter(session_id)
    parts = [f"session_id='{esc}'"]
    if agent_type:
        parts.append(f"agent_type='{pb.escape_filter(agent_type)}'")
    return pb.get_all("purdy_outputs", filter=" && ".join(parts), sort=sort)


def get_output(output_id: str) -> dict | None:
    return pb.get_record("purdy_outputs", output_id)


def create_output(data: dict) -> dict:
    return pb.create_record("purdy_outputs", data)


def update_output(output_id: str, data: dict) -> dict:
    return pb.update_record("purdy_outputs", output_id, data)


# ---------------------------------------------------------------------------
# purdy_documents
# ---------------------------------------------------------------------------

def list_documents(session_id: str, *, sort: str = "-created") -> list[dict]:
    return pb.get_all(
        "purdy_documents",
        filter=f"session_id='{pb.escape_filter(session_id)}'",
        sort=sort,
    )


def create_document(data: dict) -> dict:
    return pb.create_record("purdy_documents", data)


def update_document(document_id: str, data: dict) -> dict:
    return pb.update_record("purdy_documents", document_id, data)


def delete_document(document_id: str) -> None:
    pb.delete_record("purdy_documents", document_id)


# ---------------------------------------------------------------------------
# purdy_document_chunks
# ---------------------------------------------------------------------------

def list_document_chunks(document_id: str) -> list[dict]:
    return pb.get_all(
        "purdy_document_chunks",
        filter=f"document_id='{pb.escape_filter(document_id)}'",
        sort="chunk_index",
    )


def create_document_chunk(data: dict) -> dict:
    return pb.create_record("purdy_document_chunks", data)


# ---------------------------------------------------------------------------
# purdy_conversations
# ---------------------------------------------------------------------------

def list_conversations(session_id: str, *, sort: str = "-created") -> list[dict]:
    return pb.get_all(
        "purdy_conversations",
        filter=f"session_id='{pb.escape_filter(session_id)}'",
        sort=sort,
    )


def create_conversation(data: dict) -> dict:
    data.pop("client_id", None)
    data.pop("user_id", None)
    return pb.create_record("purdy_conversations", data)


# ---------------------------------------------------------------------------
# purdy_messages
# ---------------------------------------------------------------------------

def list_messages(conversation_id: str, *, sort: str = "created") -> list[dict]:
    return pb.get_all(
        "purdy_messages",
        filter=f"conversation_id='{pb.escape_filter(conversation_id)}'",
        sort=sort,
    )


def create_message(data: dict) -> dict:
    return pb.create_record("purdy_messages", data)


# ---------------------------------------------------------------------------
# purdy_checkpoints
# ---------------------------------------------------------------------------

def list_checkpoints(session_id: str, *, sort: str = "-created") -> list[dict]:
    return pb.get_all(
        "purdy_checkpoints",
        filter=f"session_id='{pb.escape_filter(session_id)}'",
        sort=sort,
    )


def create_checkpoint(data: dict) -> dict:
    return pb.create_record("purdy_checkpoints", data)


def update_checkpoint(checkpoint_id: str, data: dict) -> dict:
    return pb.update_record("purdy_checkpoints", checkpoint_id, data)


# ---------------------------------------------------------------------------
# purdy_session_folders
# ---------------------------------------------------------------------------

def get_session_folders(session_id: str) -> list[dict]:
    return pb.get_all(
        "purdy_session_folders",
        filter=f"session_id='{pb.escape_filter(session_id)}'",
        sort="folder_path",
    )


def link_folder(session_id: str, folder_path: str, **kwargs) -> dict:
    existing = pb.get_first(
        "purdy_session_folders",
        filter=f"session_id='{pb.escape_filter(session_id)}' && folder_path='{pb.escape_filter(folder_path)}'",
    )
    if existing:
        return pb.update_record("purdy_session_folders", existing["id"], kwargs) if kwargs else existing
    return pb.create_record("purdy_session_folders", {
        "session_id": session_id,
        "folder_path": folder_path,
        **kwargs,
    })


# ---------------------------------------------------------------------------
# purdy_session_members
# ---------------------------------------------------------------------------

def get_session_members(session_id: str) -> list[dict]:
    return pb.get_all(
        "purdy_session_members",
        filter=f"session_id='{pb.escape_filter(session_id)}'",
        sort="created",
    )


def add_member(data: dict) -> dict:
    return pb.create_record("purdy_session_members", data)


# ---------------------------------------------------------------------------
# purdy_prds
# ---------------------------------------------------------------------------

def list_prds(session_id: str, *, sort: str = "-created") -> list[dict]:
    return pb.get_all(
        "purdy_prds",
        filter=f"session_id='{pb.escape_filter(session_id)}'",
        sort=sort,
    )


def get_prd(prd_id: str) -> dict | None:
    return pb.get_record("purdy_prds", prd_id)


def create_prd(data: dict) -> dict:
    return pb.create_record("purdy_prds", data)


def update_prd(prd_id: str, data: dict) -> dict:
    return pb.update_record("purdy_prds", prd_id, data)
