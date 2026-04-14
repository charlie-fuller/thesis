"""Repository for project-related collections.

Collections: ai_projects, project_candidates, project_documents,
project_folders, project_conversations, project_stakeholder_link,
portfolio_projects, roi_opportunities.
"""

import pb_client as pb


# ---------------------------------------------------------------------------
# Computed fields (replaces PostgreSQL GENERATED columns)
# ---------------------------------------------------------------------------

def compute_scores(project: dict) -> dict:
    """Add computed total_score and tier to a project dict."""
    scores = [
        project.get("roi_potential") or 0,
        project.get("implementation_effort") or 0,
        project.get("strategic_alignment") or 0,
        project.get("stakeholder_readiness") or 0,
    ]
    total = sum(scores)
    if total >= 16:
        tier = 1
    elif total >= 12:
        tier = 2
    elif total >= 8:
        tier = 3
    else:
        tier = 4
    return {**project, "total_score": total, "tier": tier}


def _with_scores(projects: list[dict]) -> list[dict]:
    return [compute_scores(p) for p in projects]


# ---------------------------------------------------------------------------
# ai_projects
# ---------------------------------------------------------------------------

def list_projects(
    *,
    department: str = "",
    tier: int = 0,
    status: str = "",
    owner_stakeholder_id: str = "",
    sort: str = "-updated",
    limit: int = 0,
    offset: int = 0,
) -> list[dict]:
    parts = []
    if department:
        parts.append(f"department='{pb.escape_filter(department)}'")
    if status:
        parts.append(f"status='{pb.escape_filter(status)}'")
    if owner_stakeholder_id:
        parts.append(f"owner_stakeholder_id='{pb.escape_filter(owner_stakeholder_id)}'")
    filter_str = " && ".join(parts)

    if limit:
        page = (offset // limit) + 1 if limit else 1
        result = pb.list_records("ai_projects", filter=filter_str, sort=sort, page=page, per_page=limit)
        projects = _with_scores(result.get("items", []))
    else:
        projects = _with_scores(pb.get_all("ai_projects", filter=filter_str, sort=sort))

    if tier:
        projects = [p for p in projects if p.get("tier") == tier]

    return projects


def get_project(project_id: str) -> dict | None:
    record = pb.get_record("ai_projects", project_id)
    return compute_scores(record) if record else None


def create_project(data: dict) -> dict:
    data.pop("client_id", None)
    data.pop("total_score", None)
    data.pop("tier", None)
    return compute_scores(pb.create_record("ai_projects", data))


def update_project(project_id: str, data: dict) -> dict:
    data.pop("client_id", None)
    data.pop("total_score", None)
    data.pop("tier", None)
    return compute_scores(pb.update_record("ai_projects", project_id, data))


def delete_project(project_id: str) -> None:
    pb.delete_record("ai_projects", project_id)


def get_projects_summary() -> dict:
    projects = _with_scores(pb.get_all("ai_projects"))
    tier_counts = {1: 0, 2: 0, 3: 0, 4: 0}
    status_counts: dict[str, int] = {}
    dept_counts: dict[str, int] = {}
    for p in projects:
        tier_counts[p.get("tier", 4)] = tier_counts.get(p.get("tier", 4), 0) + 1
        s = p.get("status", "backlog")
        status_counts[s] = status_counts.get(s, 0) + 1
        d = p.get("department") or "unassigned"
        dept_counts[d] = dept_counts.get(d, 0) + 1
    return {"total": len(projects), "by_tier": tier_counts, "by_status": status_counts, "by_department": dept_counts}


# ---------------------------------------------------------------------------
# project_candidates
# ---------------------------------------------------------------------------

def list_project_candidates(*, status: str = "pending", limit: int = 50, offset: int = 0) -> list[dict]:
    page = (offset // limit) + 1 if limit else 1
    result = pb.list_records(
        "project_candidates",
        filter=f"status='{pb.escape_filter(status)}'",
        sort="-created",
        page=page,
        per_page=limit,
    )
    return result.get("items", [])


def get_project_candidate(candidate_id: str) -> dict | None:
    return pb.get_record("project_candidates", candidate_id)


def update_project_candidate(candidate_id: str, data: dict) -> dict:
    return pb.update_record("project_candidates", candidate_id, data)


def count_pending_candidates() -> int:
    return pb.count("project_candidates", filter="status='pending'")


# ---------------------------------------------------------------------------
# project_documents (junction table)
# ---------------------------------------------------------------------------

def get_project_documents(project_id: str) -> list[dict]:
    esc = pb.escape_filter(project_id)
    return pb.get_all("project_documents", filter=f"project_id='{esc}'", sort="-created")


def link_document(project_id: str, document_id: str, linked_by: str = "") -> dict:
    existing = pb.get_first("project_documents", filter=f"project_id='{pb.escape_filter(project_id)}' && document_id='{pb.escape_filter(document_id)}'")
    if existing:
        return existing
    return pb.create_record("project_documents", {
        "project_id": project_id,
        "document_id": document_id,
        "linked_by": linked_by,
    })


def unlink_document(project_id: str, document_id: str) -> None:
    record = pb.get_first("project_documents", filter=f"project_id='{pb.escape_filter(project_id)}' && document_id='{pb.escape_filter(document_id)}'")
    if record:
        pb.delete_record("project_documents", record["id"])


# ---------------------------------------------------------------------------
# project_folders
# ---------------------------------------------------------------------------

def get_project_folders(project_id: str) -> list[dict]:
    return pb.get_all("project_folders", filter=f"project_id='{pb.escape_filter(project_id)}'", sort="folder_path")


def link_folder(project_id: str, folder_path: str, recursive: bool = True, linked_by: str = "") -> dict:
    existing = pb.get_first("project_folders", filter=f"project_id='{pb.escape_filter(project_id)}' && folder_path='{pb.escape_filter(folder_path)}'")
    if existing:
        return pb.update_record("project_folders", existing["id"], {"recursive": recursive, "linked_by": linked_by})
    return pb.create_record("project_folders", {
        "project_id": project_id,
        "folder_path": folder_path,
        "recursive": recursive,
        "linked_by": linked_by,
    })


def unlink_folder(project_id: str, folder_path: str) -> None:
    record = pb.get_first("project_folders", filter=f"project_id='{pb.escape_filter(project_id)}' && folder_path='{pb.escape_filter(folder_path)}'")
    if record:
        pb.delete_record("project_folders", record["id"])


# ---------------------------------------------------------------------------
# project_stakeholder_link
# ---------------------------------------------------------------------------

def get_project_stakeholder_links(project_id: str) -> list[dict]:
    return pb.get_all("project_stakeholder_link", filter=f"project_id='{pb.escape_filter(project_id)}'")


def link_stakeholder(project_id: str, stakeholder_id: str, role: str = "involved", notes: str = "") -> dict:
    return pb.create_record("project_stakeholder_link", {
        "project_id": project_id,
        "stakeholder_id": stakeholder_id,
        "role": role,
        "notes": notes,
    })


def unlink_stakeholder(project_id: str, stakeholder_id: str) -> None:
    record = pb.get_first("project_stakeholder_link", filter=f"project_id='{pb.escape_filter(project_id)}' && stakeholder_id='{pb.escape_filter(stakeholder_id)}'")
    if record:
        pb.delete_record("project_stakeholder_link", record["id"])


# ---------------------------------------------------------------------------
# project_conversations
# ---------------------------------------------------------------------------

def get_project_conversations(project_id: str, *, limit: int = 20, offset: int = 0) -> list[dict]:
    page = (offset // limit) + 1 if limit else 1
    result = pb.list_records(
        "project_conversations",
        filter=f"project_id='{pb.escape_filter(project_id)}'",
        sort="-created",
        page=page,
        per_page=limit,
    )
    return result.get("items", [])


def create_project_conversation(data: dict) -> dict:
    return pb.create_record("project_conversations", data)


# ---------------------------------------------------------------------------
# portfolio_projects
# ---------------------------------------------------------------------------

def list_portfolio_projects(**kwargs) -> list[dict]:
    parts = []
    for key, val in kwargs.items():
        if val:
            parts.append(f"{key}='{pb.escape_filter(str(val))}'")
    return pb.get_all("portfolio_projects", filter=" && ".join(parts), sort="-updated")


# ---------------------------------------------------------------------------
# roi_opportunities
# ---------------------------------------------------------------------------

def list_roi_opportunities(**kwargs) -> list[dict]:
    parts = []
    for key, val in kwargs.items():
        if val:
            parts.append(f"{key}='{pb.escape_filter(str(val))}'")
    return pb.get_all("roi_opportunities", filter=" && ".join(parts), sort="-updated")
