"""
PuRDy Services Module

Product Requirements Document (PuRDy) services for:
- Initiative management
- Document processing and RAG
- Agent execution
- Chat functionality
- Multi-user sharing
- Global system KB
"""

from .initiative_service import (
    create_initiative,
    get_initiative,
    list_initiatives,
    update_initiative,
    delete_initiative,
)

from .document_service import (
    upload_document,
    upload_document_file,
    get_documents,
    get_document,
    delete_document,
    search_initiative_docs,
    promote_output_to_document,
)

from .agent_service import (
    load_agent_prompt,
    build_agent_context,
    run_agent,
    parse_agent_output,
    get_agent_types,
)

from .chat_service import (
    ask_question,
    get_conversation,
    create_conversation,
)

from .sharing_service import (
    add_member,
    remove_member,
    list_members,
    update_member_role,
    check_permission,
)

from .system_kb_service import (
    sync_kb_from_filesystem,
    search_system_kb,
    get_kb_files,
)

__all__ = [
    # Initiative
    'create_initiative',
    'get_initiative',
    'list_initiatives',
    'update_initiative',
    'delete_initiative',
    # Document
    'upload_document',
    'upload_document_file',
    'get_documents',
    'get_document',
    'delete_document',
    'search_initiative_docs',
    'promote_output_to_document',
    # Agent
    'load_agent_prompt',
    'build_agent_context',
    'run_agent',
    'parse_agent_output',
    'get_agent_types',
    # Chat
    'ask_question',
    'get_conversation',
    'create_conversation',
    # Sharing
    'add_member',
    'remove_member',
    'list_members',
    'update_member_role',
    'check_permission',
    # System KB
    'sync_kb_from_filesystem',
    'search_system_kb',
    'get_kb_files',
]
