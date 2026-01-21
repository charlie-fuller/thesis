"""
Task Auto-Extractor Service

Automatically extracts potential tasks from newly uploaded documents.
Stores candidates for user review before creating actual tasks.
"""

import logging
from datetime import datetime
from typing import Optional
import uuid

from supabase import Client

from .task_extractor import TaskExtractor, ExtractedTask

logger = logging.getLogger(__name__)


async def extract_tasks_from_document(
    document_id: str,
    supabase: Client,
    user_name: Optional[str] = None,
    auto_store: bool = True
) -> dict:
    """
    Extract potential tasks from a document and optionally store as candidates.

    Args:
        document_id: The document to scan
        supabase: Supabase client
        user_name: Optional user name to filter tasks for
        auto_store: Whether to store extracted tasks as candidates

    Returns:
        dict with extraction results
    """
    try:
        # Get document info
        doc_result = supabase.table('documents').select(
            'id, filename, title, client_id, user_id'
        ).eq('id', document_id).single().execute()

        if not doc_result.data:
            logger.warning(f"Document {document_id} not found for task extraction")
            return {'status': 'skipped', 'reason': 'document_not_found'}

        document = doc_result.data
        source_name = document.get('title') or document.get('filename', 'Unknown')

        # Get document chunks for content (increased from 10 to 30 for better coverage)
        chunks_result = supabase.table('document_chunks').select(
            'content'
        ).eq('document_id', document_id).order('chunk_index').limit(30).execute()

        if not chunks_result.data:
            logger.info(f"No chunks found for document {document_id}, skipping task extraction")
            return {'status': 'skipped', 'reason': 'no_content'}

        # Combine chunks for extraction (limit to ~8000 chars for LLM context)
        content = "\n\n".join([c['content'] for c in chunks_result.data])
        if len(content) > 8000:
            content = content[:8000]

        # Get user name if not provided
        if not user_name and document.get('user_id'):
            user_result = supabase.table('users').select(
                'full_name, email'
            ).eq('id', document['user_id']).single().execute()

            if user_result.data:
                user_name = user_result.data.get('full_name') or user_result.data.get('email', '').split('@')[0]

        # Extract tasks using LLM (Claude Haiku) with regex fallback
        import anthropic
        import os

        anthropic_client = None
        try:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if api_key:
                anthropic_client = anthropic.Anthropic(api_key=api_key)
        except Exception as e:
            logger.warning(f"Failed to initialize Anthropic client: {e}")

        extractor = TaskExtractor(anthropic_client=anthropic_client)

        # Use LLM extraction if available, otherwise fall back to regex
        if anthropic_client:
            tasks = await extractor.extract_with_llm(
                text=content,
                source_document=source_name,
                user_name=user_name
            )
        else:
            tasks = extractor.extract_from_text(
                text=content,
                source_document=source_name,
                user_name=user_name,
                include_inferred=True
            )

        if not tasks:
            logger.info(f"No tasks found in document {document_id}")
            return {
                'status': 'completed',
                'tasks_found': 0,
                'tasks_stored': 0
            }

        logger.info(f"Found {len(tasks)} potential tasks in document {document_id}")

        # Store as candidates if enabled
        stored_count = 0
        if auto_store:
            for task in tasks:
                try:
                    candidate_id = str(uuid.uuid4())
                    supabase.table('task_candidates').insert({
                        'id': candidate_id,
                        'client_id': document['client_id'],
                        'user_id': document.get('user_id'),
                        'source_document_id': document_id,
                        'source_document_name': source_name,
                        'title': task.title,
                        'suggested_priority': task.priority,
                        'suggested_due_date': task.due_date.isoformat() if task.due_date else None,
                        'due_date_text': task.due_date_text,
                        'assignee_name': task.assignee_name,
                        'source_text': task.source_text,
                        'confidence': task.confidence,
                        'extraction_pattern': task.extraction_pattern,
                        'status': 'pending'  # pending, accepted, rejected
                    }).execute()
                    stored_count += 1
                except Exception as e:
                    logger.warning(f"Failed to store task candidate: {e}")

        return {
            'status': 'completed',
            'tasks_found': len(tasks),
            'tasks_stored': stored_count,
            'tasks': [
                {
                    'title': t.title,
                    'priority': t.priority_label,
                    'confidence': t.confidence,
                    'assignee': t.assignee_name
                }
                for t in tasks
            ]
        }

    except Exception as e:
        logger.error(f"Task extraction failed for document {document_id}: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }


async def get_pending_task_candidates(
    user_id: str,
    client_id: str,
    supabase: Client,
    limit: int = 20
) -> list[dict]:
    """
    Get pending task candidates for a user to review.

    Args:
        user_id: User's ID
        client_id: Client ID
        supabase: Supabase client
        limit: Max candidates to return

    Returns:
        List of pending task candidates
    """
    result = supabase.table('task_candidates').select(
        '*'
    ).eq('client_id', client_id).eq(
        'status', 'pending'
    ).order('created_at', desc=True).limit(limit).execute()

    return result.data or []


async def accept_task_candidate(
    candidate_id: str,
    user_id: str,
    supabase: Client,
    overrides: Optional[dict] = None
) -> dict:
    """
    Accept a task candidate and create an actual task.

    Args:
        candidate_id: The candidate to accept
        user_id: User accepting the task
        supabase: Supabase client
        overrides: Optional overrides for task fields (title, priority, due_date)

    Returns:
        dict with created task info
    """
    # Get candidate
    candidate_result = supabase.table('task_candidates').select(
        '*'
    ).eq('id', candidate_id).single().execute()

    if not candidate_result.data:
        return {'status': 'error', 'message': 'Candidate not found'}

    candidate = candidate_result.data

    # Build task data
    task_data = {
        'id': str(uuid.uuid4()),
        'client_id': candidate['client_id'],
        'title': overrides.get('title', candidate['title']) if overrides else candidate['title'],
        'priority': overrides.get('priority', candidate['suggested_priority']) if overrides else candidate['suggested_priority'],
        'due_date': overrides.get('due_date', candidate['suggested_due_date']) if overrides else candidate['suggested_due_date'],
        'assignee_user_id': user_id,
        'assignee_name': candidate.get('assignee_name'),
        'status': 'pending',
        'source_type': 'document',
        'source_text': candidate['source_text'],
        'source_extracted_at': datetime.utcnow().isoformat(),
        'created_by': user_id,
        'metadata': {
            'extracted_from': candidate['source_document_name'],
            'extraction_pattern': candidate['extraction_pattern'],
            'confidence': candidate['confidence']
        }
    }

    # Create task
    try:
        supabase.table('project_tasks').insert(task_data).execute()

        # Mark candidate as accepted
        supabase.table('task_candidates').update({
            'status': 'accepted',
            'accepted_at': datetime.utcnow().isoformat(),
            'accepted_by': user_id,
            'created_task_id': task_data['id']
        }).eq('id', candidate_id).execute()

        return {
            'status': 'success',
            'task_id': task_data['id'],
            'title': task_data['title']
        }

    except Exception as e:
        logger.error(f"Failed to create task from candidate: {e}")
        return {'status': 'error', 'message': str(e)}


async def reject_task_candidate(
    candidate_id: str,
    user_id: str,
    supabase: Client,
    reason: Optional[str] = None
) -> dict:
    """
    Reject a task candidate.

    Args:
        candidate_id: The candidate to reject
        user_id: User rejecting
        supabase: Supabase client
        reason: Optional rejection reason

    Returns:
        dict with status
    """
    try:
        supabase.table('task_candidates').update({
            'status': 'rejected',
            'rejected_at': datetime.utcnow().isoformat(),
            'rejected_by': user_id,
            'rejection_reason': reason
        }).eq('id', candidate_id).execute()

        return {'status': 'success'}

    except Exception as e:
        logger.error(f"Failed to reject task candidate: {e}")
        return {'status': 'error', 'message': str(e)}


async def bulk_action_candidates(
    candidate_ids: list[str],
    action: str,  # 'accept' or 'reject'
    user_id: str,
    supabase: Client
) -> dict:
    """
    Accept or reject multiple candidates at once.

    Args:
        candidate_ids: List of candidate IDs
        action: 'accept' or 'reject'
        user_id: User performing action
        supabase: Supabase client

    Returns:
        dict with counts
    """
    success = 0
    failed = 0

    for cid in candidate_ids:
        if action == 'accept':
            result = await accept_task_candidate(cid, user_id, supabase)
        else:
            result = await reject_task_candidate(cid, user_id, supabase)

        if result['status'] == 'success':
            success += 1
        else:
            failed += 1

    return {
        'status': 'completed',
        'action': action,
        'success': success,
        'failed': failed
    }
