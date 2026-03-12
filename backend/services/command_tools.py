"""Command Center tool definitions and executor.

Provides tool schemas for Claude's tool_use API and a dispatcher
that executes tools against Supabase and Neo4j.
"""

import asyncio
import json
import os
from datetime import date, datetime, timezone
from typing import Any, Optional

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


async def execute_tool(name: str, tool_input: dict, supabase, client_id: str) -> dict[str, Any]:
    """Execute a command tool and return the result.

    Args:
        name: Tool name
        tool_input: Tool input parameters
        supabase: Supabase client instance
        client_id: Current user's client_id

    Returns:
        Dict with tool execution result
    """
    try:
        handler = _TOOL_HANDLERS.get(name)
        if not handler:
            return {"error": f"Unknown tool: {name}"}
        return await handler(tool_input, supabase, client_id)
    except Exception as e:
        logger.error(f"Tool execution error ({name}): {e}")
        return {"error": str(e)}


# ============================================================================
# Tool Handler Functions
# ============================================================================


async def _list_tasks(params: dict, supabase, client_id: str) -> dict:
    query = supabase.table("v_tasks_with_assignee").select("*").eq("client_id", client_id)

    if params.get("status"):
        query = query.eq("status", params["status"])
    if params.get("priority"):
        query = query.eq("priority", params["priority"])
    if params.get("team"):
        query = query.eq("team", params["team"])
    if params.get("linked_project_id"):
        query = query.eq("linked_project_id", params["linked_project_id"])

    limit = params.get("limit", 25)
    query = query.order("priority").order("created_at", desc=True).limit(limit)

    result = await asyncio.to_thread(lambda: query.execute())
    tasks = result.data or []

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
                "status": t["status"],
                "priority": t["priority"],
                "assignee_name": t.get("assignee_name"),
                "due_date": t.get("due_date"),
                "team": t.get("team"),
                "category": t.get("category"),
            }
            for t in tasks
        ],
    }


async def _create_task(params: dict, supabase, client_id: str) -> dict:
    # Get next position
    status = params.get("status", "pending")
    pos_result = await asyncio.to_thread(
        lambda: supabase.table("project_tasks")
        .select("position")
        .eq("client_id", client_id)
        .eq("status", status)
        .order("position", desc=True)
        .limit(1)
        .execute()
    )
    position = (pos_result.data[0]["position"] + 1) if pos_result.data else 0

    record = {
        "client_id": client_id,
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

    result = await asyncio.to_thread(lambda: supabase.table("project_tasks").insert(record).execute())
    task = result.data[0] if result.data else {}
    return {"created": True, "task": {"id": task.get("id"), "title": task.get("title"), "status": task.get("status")}}


async def _update_task(params: dict, supabase, client_id: str) -> dict:
    task_id = params.pop("task_id")
    updates = {k: v for k, v in params.items() if v is not None}
    if not updates:
        return {"error": "No fields to update"}

    updates["updated_at"] = datetime.now(timezone.utc).isoformat()

    result = await asyncio.to_thread(
        lambda: supabase.table("project_tasks")
        .update(updates)
        .eq("id", task_id)
        .eq("client_id", client_id)
        .execute()
    )
    if not result.data:
        return {"error": f"Task {task_id} not found"}
    t = result.data[0]
    return {"updated": True, "task": {"id": t["id"], "title": t["title"], "status": t["status"]}}


async def _list_projects(params: dict, supabase, client_id: str) -> dict:
    query = supabase.table("ai_projects").select("*").eq("client_id", client_id)

    if params.get("department"):
        query = query.eq("department", params["department"])
    if params.get("tier"):
        query = query.eq("tier", params["tier"])
    if params.get("status"):
        query = query.eq("status", params["status"])

    limit = params.get("limit", 25)
    query = query.order("total_score", desc=True).limit(limit)

    result = await asyncio.to_thread(lambda: query.execute())
    projects = result.data or []

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


async def _create_project(params: dict, supabase, client_id: str) -> dict:
    record = {
        "client_id": client_id,
        "title": params["name"],
        "department": params.get("department"),
        "description": params.get("description"),
        "status": params.get("status", "proposed"),
        "tier": params.get("tier"),
    }
    record = {k: v for k, v in record.items() if v is not None}

    result = await asyncio.to_thread(lambda: supabase.table("ai_projects").insert(record).execute())
    p = result.data[0] if result.data else {}
    return {"created": True, "project": {"id": p.get("id"), "name": p.get("title", ""), "status": p.get("status")}}


async def _update_project(params: dict, supabase, client_id: str) -> dict:
    project_id = params.pop("project_id")
    updates = {k: v for k, v in params.items() if v is not None}

    # Map "name" param to "title" column
    if "name" in updates:
        updates["title"] = updates.pop("name")

    if not updates:
        return {"error": "No fields to update"}

    updates["updated_at"] = datetime.now(timezone.utc).isoformat()

    result = await asyncio.to_thread(
        lambda: supabase.table("ai_projects")
        .update(updates)
        .eq("id", project_id)
        .eq("client_id", client_id)
        .execute()
    )
    if not result.data:
        return {"error": f"Project {project_id} not found"}
    p = result.data[0]
    return {"updated": True, "project": {"id": p["id"], "name": p.get("title", ""), "status": p["status"]}}


async def _list_stakeholders(params: dict, supabase, client_id: str) -> dict:
    query = supabase.table("stakeholders").select("*").eq("client_id", client_id)

    if params.get("department"):
        query = query.eq("department", params["department"])
    if params.get("engagement_level"):
        query = query.eq("engagement_level", params["engagement_level"])

    limit = params.get("limit", 25)
    query = query.order("name").limit(limit)

    result = await asyncio.to_thread(lambda: query.execute())
    stakeholders = result.data or []

    if params.get("search"):
        s = params["search"].lower()
        stakeholders = [sh for sh in stakeholders if s in (sh.get("name") or "").lower()]

    return {
        "count": len(stakeholders),
        "stakeholders": [
            {
                "id": sh["id"],
                "name": sh["name"],
                "role": sh.get("role"),
                "department": sh.get("department"),
                "engagement_level": sh.get("engagement_level"),
                "email": sh.get("email"),
            }
            for sh in stakeholders
        ],
    }


async def _update_stakeholder(params: dict, supabase, client_id: str) -> dict:
    stakeholder_id = params.pop("stakeholder_id")
    updates = {k: v for k, v in params.items() if v is not None}
    if not updates:
        return {"error": "No fields to update"}

    updates["updated_at"] = datetime.now(timezone.utc).isoformat()

    result = await asyncio.to_thread(
        lambda: supabase.table("stakeholders")
        .update(updates)
        .eq("id", stakeholder_id)
        .eq("client_id", client_id)
        .execute()
    )
    if not result.data:
        return {"error": f"Stakeholder {stakeholder_id} not found"}
    sh = result.data[0]
    return {"updated": True, "stakeholder": {"id": sh["id"], "name": sh["name"]}}


async def _search_documents(params: dict, supabase, client_id: str) -> dict:
    from document_processor import search_similar_chunks

    query = params["query"]
    limit = params.get("limit", 5)

    chunks = search_similar_chunks(query, client_id, limit=limit, min_similarity=0.0)

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


async def _list_documents(params: dict, supabase, client_id: str) -> dict:
    query = supabase.table("documents").select("id,filename,classification,file_type,created_at,chunk_count").eq(
        "client_id", client_id
    )

    if params.get("classification"):
        query = query.eq("classification", params["classification"])

    limit = params.get("limit", 25)
    query = query.order("created_at", desc=True).limit(limit)

    result = await asyncio.to_thread(lambda: query.execute())
    docs = result.data or []

    if params.get("search"):
        s = params["search"].lower()
        docs = [d for d in docs if s in (d.get("filename") or "").lower()]

    return {"count": len(docs), "documents": docs}


async def _query_knowledge_graph(params: dict, supabase, client_id: str) -> dict:
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


async def _get_dashboard_summary(params: dict, supabase, client_id: str) -> dict:
    # Tasks by status
    tasks_result = await asyncio.to_thread(
        lambda: supabase.table("project_tasks")
        .select("status", count="exact")
        .eq("client_id", client_id)
        .execute()
    )
    tasks = tasks_result.data or []
    task_counts = {}
    for t in tasks:
        s = t.get("status", "unknown")
        task_counts[s] = task_counts.get(s, 0) + 1

    # Projects by status
    projects_result = await asyncio.to_thread(
        lambda: supabase.table("ai_projects")
        .select("status,tier")
        .eq("client_id", client_id)
        .execute()
    )
    projects = projects_result.data or []
    project_status_counts = {}
    project_tier_counts = {}
    for p in projects:
        s = p.get("status", "unknown")
        project_status_counts[s] = project_status_counts.get(s, 0) + 1
        t = p.get("tier")
        if t:
            project_tier_counts[f"tier_{t}"] = project_tier_counts.get(f"tier_{t}", 0) + 1

    # Stakeholder count
    stakeholders_result = await asyncio.to_thread(
        lambda: supabase.table("stakeholders")
        .select("engagement_level")
        .eq("client_id", client_id)
        .execute()
    )
    stakeholders = stakeholders_result.data or []
    engagement_counts = {}
    for sh in stakeholders:
        e = sh.get("engagement_level", "unknown")
        engagement_counts[e] = engagement_counts.get(e, 0) + 1

    # Documents count
    docs_result = await asyncio.to_thread(
        lambda: supabase.table("documents")
        .select("id", count="exact")
        .eq("client_id", client_id)
        .execute()
    )

    return {
        "tasks": {"total": len(tasks), "by_status": task_counts},
        "projects": {
            "total": len(projects),
            "by_status": project_status_counts,
            "by_tier": project_tier_counts,
        },
        "stakeholders": {"total": len(stakeholders), "by_engagement": engagement_counts},
        "documents": {"total": docs_result.count or 0},
    }


async def _run_sql_query(params: dict, supabase, client_id: str) -> dict:
    sql = params["sql"].strip()

    # Block write operations
    sql_upper = sql.upper().lstrip()
    if not sql_upper.startswith("SELECT") and not sql_upper.startswith("WITH"):
        return {"error": "Only SELECT queries are allowed."}

    blocked = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "CREATE", "GRANT", "REVOKE"]
    for keyword in blocked:
        # Check for keyword as a standalone word
        if f" {keyword} " in f" {sql_upper} ":
            return {"error": f"Write operations not allowed. Found '{keyword}'."}

    try:
        result = await asyncio.to_thread(lambda: supabase.rpc("exec_sql", {"query": sql}).execute())
        data = result.data
        if isinstance(data, list) and len(data) > 100:
            return {"count": len(data), "truncated": True, "rows": data[:100]}
        return {"count": len(data) if isinstance(data, list) else 1, "rows": data}
    except Exception as e:
        error_msg = str(e)
        # If RPC doesn't exist, fall back to a helpful message
        if "exec_sql" in error_msg or "function" in error_msg.lower():
            return {
                "error": "SQL execution RPC not available. Use the specific tools (list_tasks, list_projects, etc.) instead."
            }
        return {"error": f"SQL query failed: {error_msg}"}


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
