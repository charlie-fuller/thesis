"""Repository for research-related collections.

Collections: research_tasks, research_sources, research_schedule.
"""

import pb_client as pb


# ---------------------------------------------------------------------------
# research_tasks
# ---------------------------------------------------------------------------

def list_research_tasks(*, status: str = "", sort: str = "-created") -> list[dict]:
    parts = []
    if status:
        parts.append(f"status='{pb.escape_filter(status)}'")
    return pb.get_all("research_tasks", filter=" && ".join(parts), sort=sort)


def get_research_task(task_id: str) -> dict | None:
    return pb.get_record("research_tasks", task_id)


def create_research_task(data: dict) -> dict:
    data.pop("client_id", None)
    data.pop("user_id", None)
    return pb.create_record("research_tasks", data)


def update_research_task(task_id: str, data: dict) -> dict:
    return pb.update_record("research_tasks", task_id, data)


def delete_research_task(task_id: str) -> None:
    pb.delete_record("research_tasks", task_id)


# ---------------------------------------------------------------------------
# research_sources
# ---------------------------------------------------------------------------

def list_research_sources(*, task_id: str = "", sort: str = "-created") -> list[dict]:
    parts = []
    if task_id:
        parts.append(f"task_id='{pb.escape_filter(task_id)}'")
    return pb.get_all("research_sources", filter=" && ".join(parts), sort=sort)


def get_research_source(source_id: str) -> dict | None:
    return pb.get_record("research_sources", source_id)


def create_research_source(data: dict) -> dict:
    return pb.create_record("research_sources", data)


def update_research_source(source_id: str, data: dict) -> dict:
    return pb.update_record("research_sources", source_id, data)


def delete_research_source(source_id: str) -> None:
    pb.delete_record("research_sources", source_id)


# ---------------------------------------------------------------------------
# research_schedule
# ---------------------------------------------------------------------------

def list_research_schedule(*, sort: str = "-created") -> list[dict]:
    return pb.get_all("research_schedule", sort=sort)


def get_research_schedule_item(item_id: str) -> dict | None:
    return pb.get_record("research_schedule", item_id)


def create_research_schedule_item(data: dict) -> dict:
    return pb.create_record("research_schedule", data)


def update_research_schedule_item(item_id: str, data: dict) -> dict:
    return pb.update_record("research_schedule", item_id, data)


def delete_research_schedule_item(item_id: str) -> None:
    pb.delete_record("research_schedule", item_id)
