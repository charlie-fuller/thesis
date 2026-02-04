"""DISCo Services Module.

Discovery-Insights-Synthesis-Convergence (DISCo) services for:
- Initiative management
- Document processing and RAG
- Agent execution
- Chat functionality
- Multi-user sharing
- Global system KB
"""

from .agent_service import (
    build_agent_context,
    get_agent_types,
    load_agent_prompt,
    parse_agent_output,
    run_agent,
)
from .chat_service import (
    ask_question,
    create_conversation,
    get_conversation,
)
from .condenser_service import (
    condense_output,
)
from .document_service import (
    delete_document,
    get_document,
    get_documents,
    promote_output_to_document,
    search_initiative_docs,
    upload_document,
    upload_document_file,
)
from .initiative_service import (
    create_initiative,
    delete_initiative,
    get_initiative,
    list_initiatives,
    update_initiative,
)
from .sharing_service import (
    add_member,
    check_permission,
    list_members,
    remove_member,
    update_member_role,
)
from .system_kb_service import (
    get_kb_files,
    search_system_kb,
    sync_kb_from_filesystem,
)

__all__ = [
    # Initiative
    "create_initiative",
    "get_initiative",
    "list_initiatives",
    "update_initiative",
    "delete_initiative",
    # Document
    "upload_document",
    "upload_document_file",
    "get_documents",
    "get_document",
    "delete_document",
    "search_initiative_docs",
    "promote_output_to_document",
    # Agent
    "load_agent_prompt",
    "build_agent_context",
    "run_agent",
    "parse_agent_output",
    "get_agent_types",
    # Chat
    "ask_question",
    "get_conversation",
    "create_conversation",
    # Sharing
    "add_member",
    "remove_member",
    "list_members",
    "update_member_role",
    "check_permission",
    # System KB
    "sync_kb_from_filesystem",
    "search_system_kb",
    "get_kb_files",
    # Condenser
    "condense_output",
]
