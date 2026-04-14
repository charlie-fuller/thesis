"""Repository for agent-related collections.

Collections: agents, agent_handoffs, agent_instruction_versions,
agent_knowledge_base, agent_topic_mapping.
"""

import pb_client as pb


# ---------------------------------------------------------------------------
# agents
# ---------------------------------------------------------------------------

def list_agents(*, is_active: bool = True) -> list[dict]:
    filter_str = "is_active=true" if is_active else ""
    return pb.get_all("agents", filter=filter_str, sort="name")


def get_agent(agent_id: str) -> dict | None:
    return pb.get_record("agents", agent_id)


def get_agent_by_name(name: str) -> dict | None:
    return pb.get_first("agents", filter=f"name='{pb.escape_filter(name)}'")


def create_agent(data: dict) -> dict:
    data.pop("client_id", None)
    return pb.create_record("agents", data)


def update_agent(agent_id: str, data: dict) -> dict:
    return pb.update_record("agents", agent_id, data)


def delete_agent(agent_id: str) -> None:
    pb.delete_record("agents", agent_id)


# ---------------------------------------------------------------------------
# agent_handoffs
# ---------------------------------------------------------------------------

def list_agent_handoffs(agent_id: str) -> list[dict]:
    return pb.get_all(
        "agent_handoffs",
        filter=f"source_agent_id='{pb.escape_filter(agent_id)}'",
        sort="priority",
    )


def get_agent_handoff(handoff_id: str) -> dict | None:
    return pb.get_record("agent_handoffs", handoff_id)


def create_agent_handoff(data: dict) -> dict:
    return pb.create_record("agent_handoffs", data)


def update_agent_handoff(handoff_id: str, data: dict) -> dict:
    return pb.update_record("agent_handoffs", handoff_id, data)


def delete_agent_handoff(handoff_id: str) -> None:
    pb.delete_record("agent_handoffs", handoff_id)


# ---------------------------------------------------------------------------
# agent_instruction_versions
# ---------------------------------------------------------------------------

def list_instruction_versions(agent_id: str) -> list[dict]:
    return pb.get_all(
        "agent_instruction_versions",
        filter=f"agent_id='{pb.escape_filter(agent_id)}'",
        sort="-version_number",
    )


def get_instruction_version(version_id: str) -> dict | None:
    return pb.get_record("agent_instruction_versions", version_id)


def create_instruction_version(data: dict) -> dict:
    return pb.create_record("agent_instruction_versions", data)


def update_instruction_version(version_id: str, data: dict) -> dict:
    return pb.update_record("agent_instruction_versions", version_id, data)


def delete_instruction_version(version_id: str) -> None:
    pb.delete_record("agent_instruction_versions", version_id)


# ---------------------------------------------------------------------------
# agent_knowledge_base
# ---------------------------------------------------------------------------

def list_agent_knowledge_base(agent_id: str) -> list[dict]:
    return pb.get_all(
        "agent_knowledge_base",
        filter=f"agent_id='{pb.escape_filter(agent_id)}'",
        sort="-created",
    )


def get_agent_knowledge_base_item(item_id: str) -> dict | None:
    return pb.get_record("agent_knowledge_base", item_id)


def create_agent_knowledge_base_item(data: dict) -> dict:
    return pb.create_record("agent_knowledge_base", data)


def update_agent_knowledge_base_item(item_id: str, data: dict) -> dict:
    return pb.update_record("agent_knowledge_base", item_id, data)


def delete_agent_knowledge_base_item(item_id: str) -> None:
    pb.delete_record("agent_knowledge_base", item_id)


# ---------------------------------------------------------------------------
# agent_topic_mapping
# ---------------------------------------------------------------------------

def list_agent_topic_mappings(agent_id: str) -> list[dict]:
    return pb.get_all(
        "agent_topic_mapping",
        filter=f"agent_id='{pb.escape_filter(agent_id)}'",
        sort="topic",
    )


def get_agent_topic_mapping(mapping_id: str) -> dict | None:
    return pb.get_record("agent_topic_mapping", mapping_id)


def create_agent_topic_mapping(data: dict) -> dict:
    return pb.create_record("agent_topic_mapping", data)


def update_agent_topic_mapping(mapping_id: str, data: dict) -> dict:
    return pb.update_record("agent_topic_mapping", mapping_id, data)


def delete_agent_topic_mapping(mapping_id: str) -> None:
    pb.delete_record("agent_topic_mapping", mapping_id)
