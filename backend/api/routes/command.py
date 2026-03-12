"""Command Center endpoint.

Provides a terminal-style interface backed by Claude's tool_use API
that can read and write to the thesis database.
"""

import asyncio
import json
import os
from datetime import datetime, timezone

from anthropic import Anthropic
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from auth import get_current_user
from database import get_supabase
from logger_config import get_logger
from services.command_tools import COMMAND_TOOL_SCHEMAS, execute_tool

logger = get_logger(__name__)
router = APIRouter(prefix="/api/command", tags=["command"])
limiter = Limiter(key_func=get_remote_address)
supabase = get_supabase()

# Initialize Anthropic client
anthropic_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are the Thesis Command Center — a terminal-style assistant embedded in the Thesis GenAI Strategy Platform.

You have tools to query and modify the database: tasks, projects, stakeholders, documents, and the knowledge graph.

Guidelines:
- Format output for terminal readability: use tables, lists, and brief text
- For mutations (create, update, delete), confirm the action briefly after completing it
- When listing items, show the most relevant fields in a compact format
- Use markdown tables for structured data
- Be concise — this is a command interface, not a conversation
- When asked to "show" or "list" something, use the appropriate tool rather than guessing
- For ambiguous requests, prefer the most common interpretation
- Current date: {current_date}
"""

MAX_TOOL_ITERATIONS = 10


class CommandRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    history: list[dict] = Field(default_factory=list, description="Previous messages for context")


@router.post("")
@limiter.limit("30/minute")
async def command_stream(
    request: Request,
    command_request: CommandRequest,
    current_user: dict = Depends(get_current_user),
):
    """Stream command responses with tool_use loop."""
    logger.info(
        "Command request received",
        extra={"user_id": current_user["id"], "message_length": len(command_request.message)},
    )

    async def generate():
        try:
            client_id = current_user.get("client_id")
            if not client_id:
                yield f"data: {json.dumps({'type': 'error', 'error': 'No client_id assigned'})}\n\n"
                return

            current_date = datetime.now(timezone.utc).strftime("%B %d, %Y")
            system = SYSTEM_PROMPT.format(current_date=current_date)

            # Build messages from history + current
            messages = []
            for msg in command_request.history[-20:]:  # Keep last 20 for context
                if msg.get("role") in ("user", "assistant") and msg.get("content"):
                    messages.append({"role": msg["role"], "content": msg["content"]})
            messages.append({"role": "user", "content": command_request.message})

            # Tool-use loop
            for iteration in range(MAX_TOOL_ITERATIONS):
                response = await asyncio.to_thread(
                    lambda: anthropic_client.messages.create(
                        model="claude-sonnet-4-5-20250929",
                        max_tokens=4096,
                        temperature=0,
                        system=system,
                        tools=COMMAND_TOOL_SCHEMAS,
                        messages=messages,
                    )
                )

                # Process response content blocks
                assistant_content = response.content
                text_parts = []
                tool_uses = []

                for block in assistant_content:
                    if block.type == "text":
                        text_parts.append(block.text)
                        # Stream text tokens
                        yield f"data: {json.dumps({'type': 'token', 'content': block.text})}\n\n"
                    elif block.type == "tool_use":
                        tool_uses.append(block)
                        # Stream tool call notification
                        yield f"data: {json.dumps({'type': 'tool_call', 'tool': block.name, 'input': block.input})}\n\n"

                # If no tool calls, we're done
                if response.stop_reason == "end_turn" or not tool_uses:
                    break

                # Execute tool calls and build tool results
                # Append the assistant message with all content blocks
                messages.append({"role": "assistant", "content": assistant_content})

                tool_results = []
                for tool_use in tool_uses:
                    result = await execute_tool(tool_use.name, tool_use.input, supabase, client_id)

                    # Stream tool result summary
                    result_summary = _summarize_result(tool_use.name, result)
                    yield f"data: {json.dumps({'type': 'tool_result', 'tool': tool_use.name, 'result': result_summary})}\n\n"

                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use.id,
                            "content": json.dumps(result),
                        }
                    )

                messages.append({"role": "user", "content": tool_results})

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            logger.exception("Command stream error")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


def _summarize_result(tool_name: str, result: dict) -> str:
    """Create a brief summary of a tool result for the UI."""
    if "error" in result:
        return f"Error: {result['error']}"

    count = result.get("count")
    if count is not None:
        entity = tool_name.replace("list_", "").replace("search_", "").replace("get_", "")
        return f"Found {count} {entity}"

    if result.get("created"):
        return f"Created successfully"

    if result.get("updated"):
        return f"Updated successfully"

    return "Done"
