"""Repository for Obsidian sync-related collections.

Collections: obsidian_vault_configs, obsidian_sync_log, obsidian_sync_state,
graph_sync_log, graph_sync_state.
"""

import pb_client as pb


# ---------------------------------------------------------------------------
# obsidian_vault_configs
# ---------------------------------------------------------------------------

def list_vault_configs(*, sort: str = "name") -> list[dict]:
    return pb.get_all("obsidian_vault_configs", sort=sort)


def get_vault_config(config_id: str) -> dict | None:
    return pb.get_record("obsidian_vault_configs", config_id)


def create_vault_config(data: dict) -> dict:
    data.pop("client_id", None)
    return pb.create_record("obsidian_vault_configs", data)


def update_vault_config(config_id: str, data: dict) -> dict:
    return pb.update_record("obsidian_vault_configs", config_id, data)


def delete_vault_config(config_id: str) -> None:
    pb.delete_record("obsidian_vault_configs", config_id)


# ---------------------------------------------------------------------------
# obsidian_sync_log
# ---------------------------------------------------------------------------

def list_sync_logs(*, limit: int = 50, sort: str = "-created") -> list[dict]:
    result = pb.list_records("obsidian_sync_log", sort=sort, per_page=limit)
    return result.get("items", [])


def get_sync_log(log_id: str) -> dict | None:
    return pb.get_record("obsidian_sync_log", log_id)


def create_sync_log(data: dict) -> dict:
    return pb.create_record("obsidian_sync_log", data)


def update_sync_log(log_id: str, data: dict) -> dict:
    return pb.update_record("obsidian_sync_log", log_id, data)


def delete_sync_log(log_id: str) -> None:
    pb.delete_record("obsidian_sync_log", log_id)


# ---------------------------------------------------------------------------
# obsidian_sync_state
# ---------------------------------------------------------------------------

def list_sync_states(*, sort: str = "-updated") -> list[dict]:
    return pb.get_all("obsidian_sync_state", sort=sort)


def get_sync_state(state_id: str) -> dict | None:
    return pb.get_record("obsidian_sync_state", state_id)


def create_sync_state(data: dict) -> dict:
    return pb.create_record("obsidian_sync_state", data)


def update_sync_state(state_id: str, data: dict) -> dict:
    return pb.update_record("obsidian_sync_state", state_id, data)


def delete_sync_state(state_id: str) -> None:
    pb.delete_record("obsidian_sync_state", state_id)


# ---------------------------------------------------------------------------
# graph_sync_log
# ---------------------------------------------------------------------------

def list_graph_sync_logs(*, limit: int = 50, sort: str = "-created") -> list[dict]:
    result = pb.list_records("graph_sync_log", sort=sort, per_page=limit)
    return result.get("items", [])


def get_graph_sync_log(log_id: str) -> dict | None:
    return pb.get_record("graph_sync_log", log_id)


def create_graph_sync_log(data: dict) -> dict:
    return pb.create_record("graph_sync_log", data)


def update_graph_sync_log(log_id: str, data: dict) -> dict:
    return pb.update_record("graph_sync_log", log_id, data)


def delete_graph_sync_log(log_id: str) -> None:
    pb.delete_record("graph_sync_log", log_id)


# ---------------------------------------------------------------------------
# graph_sync_state
# ---------------------------------------------------------------------------

def list_graph_sync_states(*, sort: str = "-updated") -> list[dict]:
    return pb.get_all("graph_sync_state", sort=sort)


def get_graph_sync_state(state_id: str) -> dict | None:
    return pb.get_record("graph_sync_state", state_id)


def create_graph_sync_state(data: dict) -> dict:
    return pb.create_record("graph_sync_state", data)


def update_graph_sync_state(state_id: str, data: dict) -> dict:
    return pb.update_record("graph_sync_state", state_id, data)


def delete_graph_sync_state(state_id: str) -> None:
    pb.delete_record("graph_sync_state", state_id)
