"""Repository for stakeholder-related collections.

Collections: stakeholders, stakeholder_candidates, stakeholder_insights,
stakeholder_metrics.
"""

import pb_client as pb


# ---------------------------------------------------------------------------
# stakeholders
# ---------------------------------------------------------------------------

def list_stakeholders(*, department: str = "", sort: str = "name") -> list[dict]:
    parts = []
    if department:
        parts.append(f"department='{pb.escape_filter(department)}'")
    return pb.get_all("stakeholders", filter=" && ".join(parts), sort=sort)


def get_stakeholder(stakeholder_id: str) -> dict | None:
    return pb.get_record("stakeholders", stakeholder_id)


def search_stakeholders(query: str) -> list[dict]:
    esc = pb.escape_filter(query)
    return pb.get_all(
        "stakeholders",
        filter=f"name~'{esc}' || email~'{esc}'",
        sort="name",
    )


def create_stakeholder(data: dict) -> dict:
    data.pop("client_id", None)
    return pb.create_record("stakeholders", data)


def update_stakeholder(stakeholder_id: str, data: dict) -> dict:
    return pb.update_record("stakeholders", stakeholder_id, data)


def delete_stakeholder(stakeholder_id: str) -> None:
    pb.delete_record("stakeholders", stakeholder_id)


# ---------------------------------------------------------------------------
# stakeholder_candidates
# ---------------------------------------------------------------------------

def list_stakeholder_candidates(*, status: str = "pending", limit: int = 50) -> list[dict]:
    result = pb.list_records(
        "stakeholder_candidates",
        filter=f"status='{pb.escape_filter(status)}'",
        sort="-created",
        per_page=limit,
    )
    return result.get("items", [])


def get_stakeholder_candidate(candidate_id: str) -> dict | None:
    return pb.get_record("stakeholder_candidates", candidate_id)


def update_stakeholder_candidate(candidate_id: str, data: dict) -> dict:
    return pb.update_record("stakeholder_candidates", candidate_id, data)


# ---------------------------------------------------------------------------
# stakeholder_insights
# ---------------------------------------------------------------------------

def list_stakeholder_insights(stakeholder_id: str) -> list[dict]:
    return pb.get_all(
        "stakeholder_insights",
        filter=f"stakeholder_id='{pb.escape_filter(stakeholder_id)}'",
        sort="-created",
    )


def get_stakeholder_insight(insight_id: str) -> dict | None:
    return pb.get_record("stakeholder_insights", insight_id)


def create_stakeholder_insight(data: dict) -> dict:
    return pb.create_record("stakeholder_insights", data)


def update_stakeholder_insight(insight_id: str, data: dict) -> dict:
    return pb.update_record("stakeholder_insights", insight_id, data)


def delete_stakeholder_insight(insight_id: str) -> None:
    pb.delete_record("stakeholder_insights", insight_id)


# ---------------------------------------------------------------------------
# stakeholder_metrics
# ---------------------------------------------------------------------------

def list_stakeholder_metrics(stakeholder_id: str) -> list[dict]:
    return pb.get_all(
        "stakeholder_metrics",
        filter=f"stakeholder_id='{pb.escape_filter(stakeholder_id)}'",
        sort="-created",
    )


def get_stakeholder_metric(metric_id: str) -> dict | None:
    return pb.get_record("stakeholder_metrics", metric_id)


def create_stakeholder_metric(data: dict) -> dict:
    return pb.create_record("stakeholder_metrics", data)


def update_stakeholder_metric(metric_id: str, data: dict) -> dict:
    return pb.update_record("stakeholder_metrics", metric_id, data)


def delete_stakeholder_metric(metric_id: str) -> None:
    pb.delete_record("stakeholder_metrics", metric_id)
