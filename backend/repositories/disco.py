"""Repository for DISCO-related collections.

Collections: disco_initiatives, disco_runs, disco_outputs, disco_bundles,
disco_prds, disco_documents, disco_document_chunks, disco_system_kb,
disco_system_kb_chunks, disco_messages, disco_conversations,
disco_checkpoints, disco_initiative_folders, disco_initiative_members,
disco_outcome_metrics, disco_bundle_feedback, disco_run_documents.
"""

import pb_client as pb


# ---------------------------------------------------------------------------
# disco_initiatives
# ---------------------------------------------------------------------------

def list_initiatives(*, status: str = "", sort: str = "-updated") -> list[dict]:
    parts = []
    if status:
        parts.append(f"status='{pb.escape_filter(status)}'")
    return pb.get_all("disco_initiatives", filter=" && ".join(parts), sort=sort)


def get_initiative(initiative_id: str) -> dict | None:
    return pb.get_record("disco_initiatives", initiative_id)


def create_initiative(data: dict) -> dict:
    data.pop("client_id", None)
    data.pop("user_id", None)
    return pb.create_record("disco_initiatives", data)


def update_initiative(initiative_id: str, data: dict) -> dict:
    return pb.update_record("disco_initiatives", initiative_id, data)


# ---------------------------------------------------------------------------
# disco_runs
# ---------------------------------------------------------------------------

def list_runs(initiative_id: str, *, sort: str = "-created") -> list[dict]:
    return pb.get_all(
        "disco_runs",
        filter=f"initiative_id='{pb.escape_filter(initiative_id)}'",
        sort=sort,
    )


def get_run(run_id: str) -> dict | None:
    return pb.get_record("disco_runs", run_id)


def create_run(data: dict) -> dict:
    return pb.create_record("disco_runs", data)


def update_run(run_id: str, data: dict) -> dict:
    return pb.update_record("disco_runs", run_id, data)


# ---------------------------------------------------------------------------
# disco_outputs
# ---------------------------------------------------------------------------

def list_outputs(initiative_id: str, *, agent_type: str = "",
                 sort: str = "-created") -> list[dict]:
    esc = pb.escape_filter(initiative_id)
    parts = [f"initiative_id='{esc}'"]
    if agent_type:
        parts.append(f"agent_type='{pb.escape_filter(agent_type)}'")
    return pb.get_all("disco_outputs", filter=" && ".join(parts), sort=sort)


def get_output(output_id: str) -> dict | None:
    return pb.get_record("disco_outputs", output_id)


def create_output(data: dict) -> dict:
    return pb.create_record("disco_outputs", data)


def update_output(output_id: str, data: dict) -> dict:
    return pb.update_record("disco_outputs", output_id, data)


# ---------------------------------------------------------------------------
# disco_bundles
# ---------------------------------------------------------------------------

def list_bundles(initiative_id: str, *, sort: str = "-created") -> list[dict]:
    return pb.get_all(
        "disco_bundles",
        filter=f"initiative_id='{pb.escape_filter(initiative_id)}'",
        sort=sort,
    )


def get_bundle(bundle_id: str) -> dict | None:
    return pb.get_record("disco_bundles", bundle_id)


def create_bundle(data: dict) -> dict:
    return pb.create_record("disco_bundles", data)


def update_bundle(bundle_id: str, data: dict) -> dict:
    return pb.update_record("disco_bundles", bundle_id, data)


# ---------------------------------------------------------------------------
# disco_prds
# ---------------------------------------------------------------------------

def list_prds(bundle_id: str, *, sort: str = "-created") -> list[dict]:
    return pb.get_all(
        "disco_prds",
        filter=f"bundle_id='{pb.escape_filter(bundle_id)}'",
        sort=sort,
    )


def get_prd(prd_id: str) -> dict | None:
    return pb.get_record("disco_prds", prd_id)


def create_prd(data: dict) -> dict:
    return pb.create_record("disco_prds", data)


def update_prd(prd_id: str, data: dict) -> dict:
    return pb.update_record("disco_prds", prd_id, data)


# ---------------------------------------------------------------------------
# disco_documents
# ---------------------------------------------------------------------------

def list_documents(initiative_id: str, *, sort: str = "-created") -> list[dict]:
    return pb.get_all(
        "disco_documents",
        filter=f"initiative_id='{pb.escape_filter(initiative_id)}'",
        sort=sort,
    )


def create_document(data: dict) -> dict:
    return pb.create_record("disco_documents", data)


def update_document(document_id: str, data: dict) -> dict:
    return pb.update_record("disco_documents", document_id, data)


def delete_document(document_id: str) -> None:
    pb.delete_record("disco_documents", document_id)


# ---------------------------------------------------------------------------
# disco_document_chunks
# ---------------------------------------------------------------------------

def list_document_chunks(document_id: str) -> list[dict]:
    return pb.get_all(
        "disco_document_chunks",
        filter=f"document_id='{pb.escape_filter(document_id)}'",
        sort="chunk_index",
    )


def create_document_chunk(data: dict) -> dict:
    return pb.create_record("disco_document_chunks", data)


# ---------------------------------------------------------------------------
# disco_system_kb
# ---------------------------------------------------------------------------

def list_system_kb(*, sort: str = "-updated") -> list[dict]:
    return pb.get_all("disco_system_kb", sort=sort)


def get_system_kb(kb_id: str) -> dict | None:
    return pb.get_record("disco_system_kb", kb_id)


def create_system_kb(data: dict) -> dict:
    return pb.create_record("disco_system_kb", data)


# ---------------------------------------------------------------------------
# disco_system_kb_chunks
# ---------------------------------------------------------------------------

def list_system_kb_chunks(kb_id: str) -> list[dict]:
    return pb.get_all(
        "disco_system_kb_chunks",
        filter=f"kb_id='{pb.escape_filter(kb_id)}'",
        sort="chunk_index",
    )


def create_system_kb_chunk(data: dict) -> dict:
    return pb.create_record("disco_system_kb_chunks", data)


# ---------------------------------------------------------------------------
# disco_messages
# ---------------------------------------------------------------------------

def list_messages(conversation_id: str, *, sort: str = "created") -> list[dict]:
    return pb.get_all(
        "disco_messages",
        filter=f"conversation_id='{pb.escape_filter(conversation_id)}'",
        sort=sort,
    )


def create_message(data: dict) -> dict:
    return pb.create_record("disco_messages", data)


# ---------------------------------------------------------------------------
# disco_conversations
# ---------------------------------------------------------------------------

def list_conversations(initiative_id: str, *, sort: str = "-created") -> list[dict]:
    return pb.get_all(
        "disco_conversations",
        filter=f"initiative_id='{pb.escape_filter(initiative_id)}'",
        sort=sort,
    )


def create_conversation(data: dict) -> dict:
    data.pop("client_id", None)
    data.pop("user_id", None)
    return pb.create_record("disco_conversations", data)


# ---------------------------------------------------------------------------
# disco_checkpoints
# ---------------------------------------------------------------------------

def list_checkpoints(initiative_id: str, *, sort: str = "-created") -> list[dict]:
    return pb.get_all(
        "disco_checkpoints",
        filter=f"initiative_id='{pb.escape_filter(initiative_id)}'",
        sort=sort,
    )


def create_checkpoint(data: dict) -> dict:
    return pb.create_record("disco_checkpoints", data)


def update_checkpoint(checkpoint_id: str, data: dict) -> dict:
    return pb.update_record("disco_checkpoints", checkpoint_id, data)


# ---------------------------------------------------------------------------
# disco_initiative_folders
# ---------------------------------------------------------------------------

def get_initiative_folders(initiative_id: str) -> list[dict]:
    return pb.get_all(
        "disco_initiative_folders",
        filter=f"initiative_id='{pb.escape_filter(initiative_id)}'",
        sort="folder_path",
    )


def link_folder(initiative_id: str, folder_path: str, **kwargs) -> dict:
    existing = pb.get_first(
        "disco_initiative_folders",
        filter=f"initiative_id='{pb.escape_filter(initiative_id)}' && folder_path='{pb.escape_filter(folder_path)}'",
    )
    if existing:
        return pb.update_record("disco_initiative_folders", existing["id"], kwargs) if kwargs else existing
    return pb.create_record("disco_initiative_folders", {
        "initiative_id": initiative_id,
        "folder_path": folder_path,
        **kwargs,
    })


# ---------------------------------------------------------------------------
# disco_initiative_members
# ---------------------------------------------------------------------------

def get_initiative_members(initiative_id: str) -> list[dict]:
    return pb.get_all(
        "disco_initiative_members",
        filter=f"initiative_id='{pb.escape_filter(initiative_id)}'",
        sort="created",
    )


def add_member(data: dict) -> dict:
    return pb.create_record("disco_initiative_members", data)


# ---------------------------------------------------------------------------
# disco_outcome_metrics
# ---------------------------------------------------------------------------

def list_outcome_metrics(*, initiative_id: str = "", sort: str = "-created") -> list[dict]:
    parts = []
    if initiative_id:
        parts.append(f"initiative_id='{pb.escape_filter(initiative_id)}'")
    return pb.get_all("disco_outcome_metrics", filter=" && ".join(parts), sort=sort)


def get_outcome_metric(metric_id: str) -> dict | None:
    return pb.get_record("disco_outcome_metrics", metric_id)


# ---------------------------------------------------------------------------
# disco_bundle_feedback
# ---------------------------------------------------------------------------

def list_bundle_feedback(bundle_id: str, *, sort: str = "-created") -> list[dict]:
    return pb.get_all(
        "disco_bundle_feedback",
        filter=f"bundle_id='{pb.escape_filter(bundle_id)}'",
        sort=sort,
    )


def create_bundle_feedback(data: dict) -> dict:
    return pb.create_record("disco_bundle_feedback", data)


# ---------------------------------------------------------------------------
# disco_run_documents
# ---------------------------------------------------------------------------

def link_run_document(run_id: str, document_id: str, **kwargs) -> dict:
    return pb.create_record("disco_run_documents", {
        "run_id": run_id,
        "document_id": document_id,
        **kwargs,
    })


def get_run_documents(run_id: str) -> list[dict]:
    return pb.get_all(
        "disco_run_documents",
        filter=f"run_id='{pb.escape_filter(run_id)}'",
        sort="created",
    )
