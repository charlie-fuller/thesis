"""Command Center tool definitions and executor.

Provides tool schemas for Claude's tool_use API and a dispatcher
that executes tools against PocketBase and Neo4j.
"""

import json
import os
from datetime import date, datetime, timezone
from typing import Any, Optional

import pb_client as pb
from repositories import documents as documents_repo
from repositories import projects as projects_repo
from repositories import stakeholders as stakeholders_repo
from repositories import tasks as tasks_repo

from logger_config import get_logger

logger = get_logger(__name__)

# ============================================================================
# Tool Schemas (Claude tool_use format)
# ============================================================================

COMMAND_TOOL_SCHEMAS = [
    {
        "name": "list_tasks",
        "description": "List and filter tasks. Returns tasks with title, status, priority, assignee, due date, and team.",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["pending", "in_progress", "blocked", "completed"],
                    "description": "Filter by status",
                },
                "priority": {
                    "type": "integer",
                    "description": "Filter by priority (1=highest, 5=lowest)",
                    "minimum": 1,
                    "maximum": 5,
                },
                "team": {
                    "type": "string",
                    "description": "Filter by team/department",
                },
                "assignee_name": {
                    "type": "string",
                    "description": "Filter by assignee name (partial match)",
                },
                "linked_project_id": {
                    "type": "string",
                    "description": "Filter by linked project UUID",
                },
                "search": {
                    "type": "string",
                    "description": "Search in title and description",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results (default 25)",
                    "default": 25,
                },
            },
        },
    },
    {
        "name": "create_task",
        "description": "Create a new task. Returns the created task.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Task title (required)"},
                "description": {"type": "string", "description": "Task description"},
                "priority": {
                    "type": "integer",
                    "description": "Priority 1-5 (1=highest, default 3)",
                    "minimum": 1,
                    "maximum": 5,
                    "default": 3,
                },
                "status": {
                    "type": "string",
                    "enum": ["pending", "in_progress", "blocked", "completed"],
                    "default": "pending",
                },
                "assignee_name": {"type": "string", "description": "Name of assignee"},
                "due_date": {"type": "string", "description": "Due date (YYYY-MM-DD)"},
                "team": {"type": "string", "description": "Team/department"},
                "category": {"type": "string", "description": "Task category"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tags for the task",
                },
                "linked_project_id": {"type": "string", "description": "Link to a project UUID"},
                "notes": {"type": "string", "description": "Additional notes"},
            },
            "required": ["title"],
        },
    },
    {
        "name": "update_task",
        "description": "Update an existing task by ID. Only provide fields you want to change.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task UUID (required)"},
                "title": {"type": "string"},
                "description": {"type": "string"},
                "status": {
                    "type": "string",
                    "enum": ["pending", "in_progress", "blocked", "completed"],
                },
                "priority": {"type": "integer", "minimum": 1, "maximum": 5},
                "assignee_name": {"type": "string"},
                "due_date": {"type": "string", "description": "YYYY-MM-DD"},
                "team": {"type": "string"},
                "category": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "notes": {"type": "string"},
                "blocker_reason": {"type": "string"},
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "list_projects",
        "description": "List and filter projects. Returns projects with name, status, tier, department, and scores.",
        "input_schema": {
            "type": "object",
            "properties": {
                "department": {"type": "string", "description": "Filter by department"},
                "tier": {
                    "type": "integer",
                    "description": "Filter by tier (1-4)",
                    "minimum": 1,
                    "maximum": 4,
                },
                "status": {"type": "string", "description": "Filter by status"},
                "limit": {"type": "integer", "description": "Max results (default 25)", "default": 25},
            },
        },
    },
    {
        "name": "create_project",
        "description": "Create a new AI project. Returns the created project.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Project name (required)"},
                "department": {"type": "string", "description": "Department"},
                "description": {"type": "string", "description": "Project description"},
                "status": {
                    "type": "string",
                    "enum": ["proposed", "evaluating", "approved", "in_progress", "completed", "on_hold", "rejected"],
                    "default": "proposed",
                },
                "tier": {
                    "type": "integer",
                    "description": "Project tier (1=strategic, 2=high, 3=medium, 4=low)",
                    "minimum": 1,
                    "maximum": 4,
                },
                "use_case": {"type": "string", "description": "AI use case description"},
                "expected_impact": {"type": "string", "description": "Expected business impact"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "update_project",
        "description": "Update an existing project by ID. Only provide fields you want to change.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project UUID (required)"},
                "name": {"type": "string"},
                "department": {"type": "string"},
                "description": {"type": "string"},
                "status": {
                    "type": "string",
                    "enum": ["proposed", "evaluating", "approved", "in_progress", "completed", "on_hold", "rejected"],
                },
                "tier": {"type": "integer", "minimum": 1, "maximum": 4},
                "use_case": {"type": "string"},
                "expected_impact": {"type": "string"},
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "list_stakeholders",
        "description": "List and filter stakeholders. Returns name, role, department, engagement level.",
        "input_schema": {
            "type": "object",
            "properties": {
                "department": {"type": "string", "description": "Filter by department"},
                "engagement_level": {
                    "type": "string",
                    "description": "Filter by engagement level",
                },
                "search": {"type": "string", "description": "Search by name"},
                "limit": {"type": "integer", "description": "Max results (default 25)", "default": 25},
            },
        },
    },
    {
        "name": "update_stakeholder",
        "description": "Update a stakeholder by ID. Only provide fields you want to change.",
        "input_schema": {
            "type": "object",
            "properties": {
                "stakeholder_id": {"type": "string", "description": "Stakeholder UUID (required)"},
                "name": {"type": "string"},
                "role": {"type": "string"},
                "department": {"type": "string"},
                "engagement_level": {"type": "string"},
                "email": {"type": "string"},
                "notes": {"type": "string"},
            },
            "required": ["stakeholder_id"],
        },
    },
    {
        "name": "search_documents",
        "description": "Search the knowledge base using semantic similarity. Returns matching document chunks with relevance scores.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query (required)"},
                "limit": {"type": "integer", "description": "Max results (default 5)", "default": 5},
            },
            "required": ["query"],
        },
    },
    {
        "name": "list_documents",
        "description": "List documents in the knowledge base with optional filters.",
        "input_schema": {
            "type": "object",
            "properties": {
                "search": {"type": "string", "description": "Search in filename"},
                "classification": {"type": "string", "description": "Filter by classification"},
                "limit": {"type": "integer", "description": "Max results (default 25)", "default": 25},
            },
        },
    },
    {
        "name": "query_knowledge_graph",
        "description": "Run a Cypher query against the Neo4j knowledge graph. Use for relationship/network analysis. Read-only.",
        "input_schema": {
            "type": "object",
            "properties": {
                "cypher": {
                    "type": "string",
                    "description": "Cypher query (read-only MATCH/RETURN, no CREATE/DELETE/SET)",
                },
            },
            "required": ["cypher"],
        },
    },
    {
        "name": "get_dashboard_summary",
        "description": "Get a summary of tasks, projects, and stakeholders with counts by status/tier.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "run_sql_query",
        "description": "Run a read-only SQL SELECT query against the database. For ad-hoc data exploration.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "SQL SELECT query (read-only, no INSERT/UPDATE/DELETE)",
                },
            },
            "required": ["sql"],
        },
    },
]


# ============================================================================
# Tool Executor
# ============================================================================


async def execute_tool(name: str, tool_input: dict, supabase=None, client_id: str = "") -> dict[str, Any]:
    """Execute a command tool and return the result.

    Args:
        name: Tool name
        tool_input: Tool input parameters
        supabase: Deprecated, ignored.
        client_id: Deprecated, ignored.

    Returns:
        Dict with tool execution result
    """
    try:
        handler = _TOOL_HANDLERS.get(name)
        if not handler:
            return {"error": f"Unknown tool: {name}"}
        return await handler(tool_input)
    except Exception as e:
        logger.error(f"Tool execution error ({name}): {e}")
        return {"error": str(e)}


# ============================================================================
# Tool Handler Functions
# ============================================================================


async def _list_tasks(params: dict) -> dict:
    filter_parts = []
    if params.get("status"):
        filter_parts.append(f"status='{pb.escape_filter(params['status'])}'")
    if params.get("priority"):
        filter_parts.append(f"priority='{pb.escape_filter(str(params['priority']))}'")
    if params.get("team"):
        filter_parts.append(f"team='{pb.escape_filter(params['team'])}'")
    if params.get("linked_project_id"):
        filter_parts.append(f"linked_project_id='{pb.escape_filter(params['linked_project_id'])}'")

    limit = params.get("limit", 25)
    pb_filter = " && ".join(filter_parts) if filter_parts else None
    result = pb.list_records(
        "project_tasks", filter=pb_filter, sort="priority,-created", per_page=limit
    )
    tasks = result.get("items", [])

    # Client-side filters
    if params.get("search"):
        s = params["search"].lower()
        tasks = [t for t in tasks if s in (t.get("title") or "").lower() or s in (t.get("description") or "").lower()]
    if params.get("assignee_name"):
        s = params["assignee_name"].lower()
        tasks = [t for t in tasks if s in (t.get("assignee_name") or "").lower()]

    # Slim down output for Claude
    return {
        "count": len(tasks),
        "tasks": [
            {
                "id": t["id"],
                "title": t["title"],
                "status": t.get("status"),
                "priority": t.get("priority"),
                "assignee_name": t.get("assignee_name"),
                "due_date": t.get("due_date"),
                "team": t.get("team"),
                "category": t.get("category"),
            }
            for t in tasks
        ],
    }


async def _create_task(params: dict) -> dict:
    # Get next position
    status = params.get("status", "pending")
    esc_status = pb.escape_filter(status)
    pos_result = pb.list_records(
        "project_tasks", filter=f"status='{esc_status}'", sort="-position", per_page=1
    )
    pos_items = pos_result.get("items", [])
    position = (pos_items[0].get("position", 0) + 1) if pos_items else 0

    record = {
        "title": params["title"],
        "description": params.get("description"),
        "status": status,
        "priority": params.get("priority", 3),
        "assignee_name": params.get("assignee_name"),
        "due_date": params.get("due_date"),
        "team": params.get("team"),
        "category": params.get("category"),
        "tags": params.get("tags", []),
        "linked_project_id": params.get("linked_project_id"),
        "notes": params.get("notes"),
        "source_type": "manual",
        "position": position,
    }
    # Remove None values
    record = {k: v for k, v in record.items() if v is not None}

    task = tasks_repo.create_task(record)
    return {"created": True, "task": {"id": task.get("id"), "title": task.get("title"), "status": task.get("status")}}


async def _update_task(params: dict) -> dict:
    task_id = params.pop("task_id")
    updates = {k: v for k, v in params.items() if v is not None}
    if not updates:
        return {"error": "No fields to update"}

    try:
        t = tasks_repo.update_task(task_id, updates)
    except Exception:
        return {"error": f"Task {task_id} not found"}
    return {"updated": True, "task": {"id": t["id"], "title": t.get("title"), "status": t.get("status")}}


async def _list_projects(params: dict) -> dict:
    projects = projects_repo.list_projects(
        department=params.get("department", ""),
        tier=params.get("tier", 0),
        status=params.get("status", ""),
        sort="-total_score",
        limit=params.get("limit", 25),
    )

    return {
        "count": len(projects),
        "projects": [
            {
                "id": p["id"],
                "name": p.get("title") or p.get("project_name") or "Untitled",
                "department": p.get("department"),
                "status": p.get("status"),
                "tier": p.get("tier"),
                "total_score": p.get("total_score"),
                "use_case": p.get("description"),
            }
            for p in projects
        ],
    }


async def _create_project(params: dict) -> dict:
    record = {
        "title": params["name"],
        "department": params.get("department"),
        "description": params.get("description"),
        "status": params.get("status", "proposed"),
        "tier": params.get("tier"),
    }
    record = {k: v for k, v in record.items() if v is not None}

    p = projects_repo.create_project(record)
    return {"created": True, "project": {"id": p.get("id"), "name": p.get("title", ""), "status": p.get("status")}}


async def _update_project(params: dict) -> dict:
    project_id = params.pop("project_id")
    updates = {k: v for k, v in params.items() if v is not None}

    # Map "name" param to "title" column
    if "name" in updates:
        updates["title"] = updates.pop("name")

    if not updates:
        return {"error": "No fields to update"}

    try:
        p = projects_repo.update_project(project_id, updates)
    except Exception:
        return {"error": f"Project {project_id} not found"}
    return {"updated": True, "project": {"id": p["id"], "name": p.get("title", ""), "status": p.get("status")}}


async def _list_stakeholders(params: dict) -> dict:
    all_stakeholders = stakeholders_repo.list_stakeholders(
        department=params.get("department", ""),
    )

    # Client-side filters
    if params.get("engagement_level"):
        lvl = params["engagement_level"].lower()
        all_stakeholders = [sh for sh in all_stakeholders if (sh.get("engagement_level") or "").lower() == lvl]

    if params.get("search"):
        s = params["search"].lower()
        all_stakeholders = [sh for sh in all_stakeholders if s in (sh.get("name") or "").lower()]

    limit = params.get("limit", 25)
    stakeholders = all_stakeholders[:limit]

    return {
        "count": len(stakeholders),
        "stakeholders": [
            {
                "id": sh["id"],
                "name": sh.get("name"),
                "role": sh.get("role"),
                "department": sh.get("department"),
                "engagement_level": sh.get("engagement_level"),
                "email": sh.get("email"),
            }
            for sh in stakeholders
        ],
    }


async def _update_stakeholder(params: dict) -> dict:
    stakeholder_id = params.pop("stakeholder_id")
    updates = {k: v for k, v in params.items() if v is not None}
    if not updates:
        return {"error": "No fields to update"}

    try:
        sh = stakeholders_repo.update_stakeholder(stakeholder_id, updates)
    except Exception:
        return {"error": f"Stakeholder {stakeholder_id} not found"}
    return {"updated": True, "stakeholder": {"id": sh["id"], "name": sh.get("name")}}


async def _search_documents(params: dict) -> dict:
    from document_processor import search_similar_chunks

    query = params["query"]
    limit = params.get("limit", 5)

    chunks = search_similar_chunks(query, limit=limit, min_similarity=0.0)

    return {
        "count": len(chunks),
        "results": [
            {
                "document_id": c.get("document_id"),
                "filename": c.get("metadata", {}).get("filename", "Unknown"),
                "similarity": round(c.get("similarity", 0), 3),
                "content": c.get("content", "")[:500],
            }
            for c in chunks
        ],
    }


async def _list_documents(params: dict) -> dict:
    docs = documents_repo.list_documents(
        classification=params.get("classification", ""),
        sort="-created",
        limit=params.get("limit", 25),
    )

    if params.get("search"):
        s = params["search"].lower()
        docs = [d for d in docs if s in (d.get("filename") or "").lower()]

    return {"count": len(docs), "documents": docs}


async def _query_knowledge_graph(params: dict) -> dict:
    cypher = params["cypher"].strip()

    # Block write operations
    cypher_upper = cypher.upper()
    blocked = ["CREATE", "DELETE", "SET ", "REMOVE", "MERGE", "DROP", "DETACH"]
    for keyword in blocked:
        if keyword in cypher_upper:
            return {"error": f"Write operations not allowed. Found '{keyword}' in query."}

    try:
        from services.graph.connection import Neo4jConnection

        neo4j = Neo4jConnection()
        await neo4j.connect()
        results = await neo4j.execute_query(cypher)
        await neo4j.close()

        # Limit result size
        if len(results) > 100:
            results = results[:100]
            return {"count": len(results), "truncated": True, "results": results}

        return {"count": len(results), "results": results}
    except Exception as e:
        return {"error": f"Graph query failed: {str(e)}"}


async def _get_dashboard_summary(params: dict) -> dict:
    # Tasks by status
    tasks = pb.get_all("project_tasks")
    task_counts = {}
    for t in tasks:
        s = t.get("status", "unknown")
        task_counts[s] = task_counts.get(s, 0) + 1

    # Projects by status and tier (uses repo for computed scores)
    projects = projects_repo.list_projects()
    project_status_counts = {}
    project_tier_counts = {}
    for p in projects:
        s = p.get("status", "unknown")
        project_status_counts[s] = project_status_counts.get(s, 0) + 1
        t = p.get("tier")
        if t:
            project_tier_counts[f"tier_{t}"] = project_tier_counts.get(f"tier_{t}", 0) + 1

    # Stakeholder count
    stakeholders = stakeholders_repo.list_stakeholders()
    engagement_counts = {}
    for sh in stakeholders:
        e = sh.get("engagement_level", "unknown")
        engagement_counts[e] = engagement_counts.get(e, 0) + 1

    # Documents count
    docs_count = pb.count("documents")

    return {
        "tasks": {"total": len(tasks), "by_status": task_counts},
        "projects": {
            "total": len(projects),
            "by_status": project_status_counts,
            "by_tier": project_tier_counts,
        },
        "stakeholders": {"total": len(stakeholders), "by_engagement": engagement_counts},
        "documents": {"total": docs_count},
    }


async def _run_sql_query(params: dict) -> dict:
    # PocketBase does not support raw SQL queries
    # Direct agents to use the specific tools instead
    return {
        "error": "SQL execution is not available with PocketBase. Use the specific tools (list_tasks, list_projects, etc.) instead."
    }


# Handler registry
_TOOL_HANDLERS = {
    "list_tasks": _list_tasks,
    "create_task": _create_task,
    "update_task": _update_task,
    "list_projects": _list_projects,
    "create_project": _create_project,
    "update_project": _update_project,
    "list_stakeholders": _list_stakeholders,
    "update_stakeholder": _update_stakeholder,
    "search_documents": _search_documents,
    "list_documents": _list_documents,
    "query_knowledge_graph": _query_knowledge_graph,
    "get_dashboard_summary": _get_dashboard_summary,
    "run_sql_query": _run_sql_query,
}
