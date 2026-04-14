"""Repository for miscellaneous collections.

Collections: api_usage_logs, compass_status_reports, department_kpis,
engagement_level_history, glean_connectors, glean_connector_gaps,
glean_connector_requests, glean_connector_summary,
glean_disco_integration_matrix, knowledge_gaps, theme_settings,
user_quick_prompts.
"""

import pb_client as pb


# ---------------------------------------------------------------------------
# Generic CRUD factory
# ---------------------------------------------------------------------------

def _list(collection: str, *, sort: str = "-created", limit: int = 0,
          offset: int = 0, **filter_kwargs) -> list[dict]:
    parts = []
    for key, val in filter_kwargs.items():
        if val:
            parts.append(f"{key}='{pb.escape_filter(str(val))}'")
    filter_str = " && ".join(parts)
    if limit:
        page = (offset // limit) + 1 if limit else 1
        result = pb.list_records(collection, filter=filter_str, sort=sort, page=page, per_page=limit)
        return result.get("items", [])
    return pb.get_all(collection, filter=filter_str, sort=sort)


def _get(collection: str, record_id: str) -> dict | None:
    return pb.get_record(collection, record_id)


def _create(collection: str, data: dict) -> dict:
    data.pop("client_id", None)
    data.pop("user_id", None)
    return pb.create_record(collection, data)


def _update(collection: str, record_id: str, data: dict) -> dict:
    return pb.update_record(collection, record_id, data)


def _delete(collection: str, record_id: str) -> None:
    pb.delete_record(collection, record_id)


# ---------------------------------------------------------------------------
# api_usage_logs
# ---------------------------------------------------------------------------

def list_api_usage_logs(**kwargs) -> list[dict]:
    return _list("api_usage_logs", **kwargs)


def get_api_usage_log(log_id: str) -> dict | None:
    return _get("api_usage_logs", log_id)


def create_api_usage_log(data: dict) -> dict:
    return _create("api_usage_logs", data)


def update_api_usage_log(log_id: str, data: dict) -> dict:
    return _update("api_usage_logs", log_id, data)


def delete_api_usage_log(log_id: str) -> None:
    return _delete("api_usage_logs", log_id)


# ---------------------------------------------------------------------------
# compass_status_reports
# ---------------------------------------------------------------------------

def list_compass_status_reports(**kwargs) -> list[dict]:
    return _list("compass_status_reports", **kwargs)


def get_compass_status_report(report_id: str) -> dict | None:
    return _get("compass_status_reports", report_id)


def create_compass_status_report(data: dict) -> dict:
    return _create("compass_status_reports", data)


def update_compass_status_report(report_id: str, data: dict) -> dict:
    return _update("compass_status_reports", report_id, data)


def delete_compass_status_report(report_id: str) -> None:
    return _delete("compass_status_reports", report_id)


# ---------------------------------------------------------------------------
# department_kpis
# ---------------------------------------------------------------------------

def list_department_kpis(**kwargs) -> list[dict]:
    return _list("department_kpis", **kwargs)


def get_department_kpi(kpi_id: str) -> dict | None:
    return _get("department_kpis", kpi_id)


def create_department_kpi(data: dict) -> dict:
    return _create("department_kpis", data)


def update_department_kpi(kpi_id: str, data: dict) -> dict:
    return _update("department_kpis", kpi_id, data)


def delete_department_kpi(kpi_id: str) -> None:
    return _delete("department_kpis", kpi_id)


# ---------------------------------------------------------------------------
# engagement_level_history
# ---------------------------------------------------------------------------

def list_engagement_level_history(**kwargs) -> list[dict]:
    return _list("engagement_level_history", **kwargs)


def get_engagement_level_history_item(item_id: str) -> dict | None:
    return _get("engagement_level_history", item_id)


def create_engagement_level_history_item(data: dict) -> dict:
    return _create("engagement_level_history", data)


def update_engagement_level_history_item(item_id: str, data: dict) -> dict:
    return _update("engagement_level_history", item_id, data)


def delete_engagement_level_history_item(item_id: str) -> None:
    return _delete("engagement_level_history", item_id)


# ---------------------------------------------------------------------------
# glean_connectors
# ---------------------------------------------------------------------------

def list_glean_connectors(**kwargs) -> list[dict]:
    return _list("glean_connectors", **kwargs)


def get_glean_connector(connector_id: str) -> dict | None:
    return _get("glean_connectors", connector_id)


def create_glean_connector(data: dict) -> dict:
    return _create("glean_connectors", data)


def update_glean_connector(connector_id: str, data: dict) -> dict:
    return _update("glean_connectors", connector_id, data)


def delete_glean_connector(connector_id: str) -> None:
    return _delete("glean_connectors", connector_id)


# ---------------------------------------------------------------------------
# glean_connector_gaps
# ---------------------------------------------------------------------------

def list_glean_connector_gaps(**kwargs) -> list[dict]:
    return _list("glean_connector_gaps", **kwargs)


def get_glean_connector_gap(gap_id: str) -> dict | None:
    return _get("glean_connector_gaps", gap_id)


def create_glean_connector_gap(data: dict) -> dict:
    return _create("glean_connector_gaps", data)


def update_glean_connector_gap(gap_id: str, data: dict) -> dict:
    return _update("glean_connector_gaps", gap_id, data)


def delete_glean_connector_gap(gap_id: str) -> None:
    return _delete("glean_connector_gaps", gap_id)


# ---------------------------------------------------------------------------
# glean_connector_requests
# ---------------------------------------------------------------------------

def list_glean_connector_requests(**kwargs) -> list[dict]:
    return _list("glean_connector_requests", **kwargs)


def get_glean_connector_request(request_id: str) -> dict | None:
    return _get("glean_connector_requests", request_id)


def create_glean_connector_request(data: dict) -> dict:
    return _create("glean_connector_requests", data)


def update_glean_connector_request(request_id: str, data: dict) -> dict:
    return _update("glean_connector_requests", request_id, data)


def delete_glean_connector_request(request_id: str) -> None:
    return _delete("glean_connector_requests", request_id)


# ---------------------------------------------------------------------------
# glean_connector_summary
# ---------------------------------------------------------------------------

def list_glean_connector_summary(**kwargs) -> list[dict]:
    return _list("glean_connector_summary", **kwargs)


def get_glean_connector_summary(summary_id: str) -> dict | None:
    return _get("glean_connector_summary", summary_id)


def create_glean_connector_summary(data: dict) -> dict:
    return _create("glean_connector_summary", data)


def update_glean_connector_summary(summary_id: str, data: dict) -> dict:
    return _update("glean_connector_summary", summary_id, data)


def delete_glean_connector_summary(summary_id: str) -> None:
    return _delete("glean_connector_summary", summary_id)


# ---------------------------------------------------------------------------
# glean_disco_integration_matrix
# ---------------------------------------------------------------------------

def list_glean_disco_integration_matrix(**kwargs) -> list[dict]:
    return _list("glean_disco_integration_matrix", **kwargs)


def get_glean_disco_integration_matrix_item(item_id: str) -> dict | None:
    return _get("glean_disco_integration_matrix", item_id)


def create_glean_disco_integration_matrix_item(data: dict) -> dict:
    return _create("glean_disco_integration_matrix", data)


def update_glean_disco_integration_matrix_item(item_id: str, data: dict) -> dict:
    return _update("glean_disco_integration_matrix", item_id, data)


def delete_glean_disco_integration_matrix_item(item_id: str) -> None:
    return _delete("glean_disco_integration_matrix", item_id)


# ---------------------------------------------------------------------------
# knowledge_gaps
# ---------------------------------------------------------------------------

def list_knowledge_gaps(**kwargs) -> list[dict]:
    return _list("knowledge_gaps", **kwargs)


def get_knowledge_gap(gap_id: str) -> dict | None:
    return _get("knowledge_gaps", gap_id)


def create_knowledge_gap(data: dict) -> dict:
    return _create("knowledge_gaps", data)


def update_knowledge_gap(gap_id: str, data: dict) -> dict:
    return _update("knowledge_gaps", gap_id, data)


def delete_knowledge_gap(gap_id: str) -> None:
    return _delete("knowledge_gaps", gap_id)


# ---------------------------------------------------------------------------
# theme_settings
# ---------------------------------------------------------------------------

def list_theme_settings(**kwargs) -> list[dict]:
    return _list("theme_settings", **kwargs)


def get_theme_setting(setting_id: str) -> dict | None:
    return _get("theme_settings", setting_id)


def create_theme_setting(data: dict) -> dict:
    return _create("theme_settings", data)


def update_theme_setting(setting_id: str, data: dict) -> dict:
    return _update("theme_settings", setting_id, data)


def delete_theme_setting(setting_id: str) -> None:
    return _delete("theme_settings", setting_id)


# ---------------------------------------------------------------------------
# user_quick_prompts
# ---------------------------------------------------------------------------

def list_user_quick_prompts(**kwargs) -> list[dict]:
    return _list("user_quick_prompts", **kwargs)


def get_user_quick_prompt(prompt_id: str) -> dict | None:
    return _get("user_quick_prompts", prompt_id)


def create_user_quick_prompt(data: dict) -> dict:
    return _create("user_quick_prompts", data)


def update_user_quick_prompt(prompt_id: str, data: dict) -> dict:
    return _update("user_quick_prompts", prompt_id, data)


def delete_user_quick_prompt(prompt_id: str) -> None:
    return _delete("user_quick_prompts", prompt_id)
