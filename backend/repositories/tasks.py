"""Repository for task-related collections.

Collections: project_tasks, task_candidates, task_comments, task_history.
"""

import pb_client as pb


def list_tasks(*, project_id: str = "", status: str = "", priority: str = "",
               sort: str = "-updated", limit: int = 0, offset: int = 0) -> list[dict]:
    parts = []
    if project_id:
        esc = pb.escape_filter(project_id)
        parts.append(f"(source_project_id='{esc}' || linked_project_id='{esc}')")
    if status:
        parts.append(f"status='{pb.escape_filter(status)}'")
    if priority:
        parts.append(f"priority='{pb.escape_filter(priority)}'")
    filter_str = " && ".join(parts)
    if limit:
        page = (offset // limit) + 1 if limit else 1
        result = pb.list_records("project_tasks", filter=filter_str, sort=sort, page=page, per_page=limit)
        return result.get("items", [])
    return pb.get_all("project_tasks", filter=filter_str, sort=sort)


def get_task(task_id: str) -> dict | None:
    return pb.get_record("project_tasks", task_id)


def create_task(data: dict) -> dict:
    data.pop("client_id", None)
    data.pop("user_id", None)
    return pb.create_record("project_tasks", data)


def update_task(task_id: str, data: dict) -> dict:
    return pb.update_record("project_tasks", task_id, data)


def delete_task(task_id: str) -> None:
    pb.delete_record("project_tasks", task_id)


# task_candidates
def list_task_candidates(*, status: str = "pending", limit: int = 50) -> list[dict]:
    result = pb.list_records("task_candidates", filter=f"status='{pb.escape_filter(status)}'", sort="-created", per_page=limit)
    return result.get("items", [])


def get_task_candidate(candidate_id: str) -> dict | None:
    return pb.get_record("task_candidates", candidate_id)


def update_task_candidate(candidate_id: str, data: dict) -> dict:
    return pb.update_record("task_candidates", candidate_id, data)


def count_pending_task_candidates() -> int:
    return pb.count("task_candidates", filter="status='pending'")


# task_comments
def get_task_comments(task_id: str) -> list[dict]:
    return pb.get_all("task_comments", filter=f"task_id='{pb.escape_filter(task_id)}'", sort="created")


def create_task_comment(data: dict) -> dict:
    return pb.create_record("task_comments", data)


# task_history
def get_task_history(task_id: str) -> list[dict]:
    return pb.get_all("task_history", filter=f"task_id='{pb.escape_filter(task_id)}'", sort="-created")


def create_task_history(data: dict) -> dict:
    return pb.create_record("task_history", data)
