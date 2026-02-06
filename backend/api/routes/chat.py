"""Chat endpoint routes.

Handles AI chat interactions with RAG (Retrieval Augmented Generation).
"""

import asyncio
import json
import os
from datetime import datetime, timezone

from anthropic import Anthropic
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from api.models.requests import ChatRequest
from auth import get_current_user
from database import get_supabase
from document_processor import search_similar_chunks
from logger_config import get_logger
from services.chat_agent_service import get_chat_agent_service
from services.conversation_service import get_conversation_service
from services.project_context import build_project_context, get_scoring_related_documents
from services.useable_output_detector import process_conversation_for_useable_output
from system_instructions_loader import (
    get_active_system_instruction_version,
    get_system_instructions_for_user,
    get_system_instructions_for_version,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])
limiter = Limiter(key_func=get_remote_address)
supabase = get_supabase()

# Initialize Anthropic client
anthropic_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


def _get_date_context() -> str:
    """Generate a date context block to prepend to system prompts.

    This ensures agents always know the current date.
    """
    current_date = datetime.now(timezone.utc).strftime("%B %d, %Y")  # e.g., "January 29, 2026"
    return f"""<current_context>
Today's date: {current_date}
</current_context>

"""


def _message_has_substantial_content(message: str) -> bool:
    """Determine if a message has enough content to generate an image directly.

    without needing to pull from conversation history.

    Uses multiple heuristics to be more flexible than strict formatting checks:
    1. Character count thresholds
    2. Sentence detection
    3. Structural indicators (lists, bullets, etc.)
    4. Word count analysis

    Args:
        message: The user's message

    Returns:
        True if the message has substantial content for image generation
    """
    if not message:
        return False

    # Strip the image request prefix to analyze actual content
    # e.g., "create a diagram of this:" -> analyze what comes after
    content = message
    prefixes_to_strip = [
        "create a diagram of this:",
        "create a diagram of these:",
        "generate an image of this:",
        "make a visual of this:",
        "create a mind map of this:",
        "create a flowchart of this:",
        "please create a diagram of:",
        "create a diagram showing:",
        "diagram of this:",
        "visualize this:",
        "show this:",
    ]
    content_lower = content.lower()
    for prefix in prefixes_to_strip:
        if content_lower.startswith(prefix):
            content = content[len(prefix) :].strip()
            break

    # Heuristic 1: Sufficient length (lowered threshold)
    if len(content) >= 200:
        # Has enough raw content - likely has something to visualize
        logger.debug(f"Content detection: sufficient length ({len(content)} chars)")
        return True

    # Heuristic 2: Multiple sentences (3+ sentences suggest substantial content)
    sentences = [s.strip() for s in content.replace("!", ".").replace("?", ".").split(".") if s.strip()]
    if len(sentences) >= 3:
        logger.debug(f"Content detection: multiple sentences ({len(sentences)} sentences)")
        return True

    # Heuristic 3: Structural indicators (lists, bullets, numbered items)
    structural_indicators = [
        # Numbered lists
        any(f"{i}." in content or f"{i})" in content or f"{i}:" in content for i in range(1, 20)),
        # Bullet points
        "\n-" in content or "\n•" in content or "\n*" in content,
        # Multiple line breaks suggest structured content
        content.count("\n") >= 2,
        # Colons often indicate structured content
        content.count(":") >= 2,
    ]
    if any(structural_indicators):
        logger.debug("Content detection: structural indicators found")
        return True

    # Heuristic 4: Word count - LOWERED from 15 to 5 words
    # Short requests like "a chicken that looks like a pigeon" (7 words) are specific enough
    words = content.split()
    if len(words) >= 5:
        logger.debug(f"Content detection: sufficient word count ({len(words)} words)")
        return True

    # If none of the heuristics match, message is too vague
    logger.debug(
        f"Content detection: message too vague (len={len(content)}, words={len(words)}, sentences={len(sentences)})"
    )
    return False


@router.post("")
@limiter.limit("20/minute")
async def chat(request: Request, chat_request: ChatRequest, current_user: dict = Depends(get_current_user)):
    """Chat endpoint with RAG (Retrieval Augmented Generation).

    Processes user messages and generates AI responses using Claude,
    optionally enhanced with context from user's documents.

    **Request Body:**
    - conversation_id: UUID of conversation to save messages
    - message: User's question/message (1-10000 chars)
    - document_ids: Optional list of document IDs to search (uses all if empty)

    **Returns:**
    - response: AI-generated response
    - context_used: Number of document chunks used for context
    - tokens_used: Token usage statistics

    **Rate Limit:** 20 requests per minute

    **Errors:**
    - 400: Invalid request (missing required fields, message too long)
    - 401: Not authenticated
    - 429: Rate limit exceeded
    - 500: Server error (AI API failure, database error)
    """
    logger.info(
        "Chat request received",
        extra={
            "user_id": current_user["id"],
            "conversation_id": chat_request.conversation_id,
            "message_length": len(chat_request.message),
        },
    )

    try:
        # Detect simple greetings or conversational messages that don't need RAG
        simple_messages = {
            "hello",
            "hi",
            "hey",
            "greetings",
            "good morning",
            "good afternoon",
            "good evening",
            "howdy",
            "yo",
            "sup",
            "what's up",
            "whats up",
            "thanks",
            "thank you",
            "bye",
            "goodbye",
            "see you",
            "ok",
            "okay",
        }
        message_lower = chat_request.message.lower().strip()
        is_simple_message = message_lower in simple_messages or len(chat_request.message.split()) <= 2

        # Build context from documents using RAG (conditionally)
        context_chunks = []

        # Only search if use_rag is enabled and message isn't a simple greeting
        if chat_request.use_rag and not is_simple_message:
            logger.info("Searching knowledge base for context")

            # Get user's client_id for document filtering
            client_id = current_user.get("client_id")

            # Search documents in the user's knowledge base
            # If document_ids are provided, only search within those documents
            # min_similarity=0.0 allows search_similar_chunks to use adaptive thresholds
            # based on query type (factual vs exploratory)
            # conversation_id is passed to prioritize files referenced in the conversation
            search_results = search_similar_chunks(
                chat_request.message,
                client_id,
                limit=5,
                min_similarity=0.0,  # Use adaptive threshold based on query type
                document_ids=chat_request.document_ids,  # Filter by uploaded documents if provided
                conversation_id=chat_request.conversation_id,
            )
            context_chunks = search_results
            logger.info(f"Found {len(context_chunks)} relevant chunks")
        else:
            logger.info(f"Skipping RAG - use_rag={chat_request.use_rag}, is_simple_message={is_simple_message}")

        # Load system instructions with version binding
        # Priority:
        # 1. If conversation has a bound version, use that (consistency within conversation)
        # 2. If no bound version, use active version and bind it to the conversation
        # 3. Fallback to legacy per-user instructions if versioning not set up
        try:
            system_prompt = None
            version_id_to_bind = None

            # Check if conversation exists and has a bound version
            if chat_request.conversation_id:
                conv_result = await asyncio.to_thread(
                    lambda: supabase.table("conversations")
                    .select("system_instruction_version_id")
                    .eq("id", chat_request.conversation_id)
                    .single()
                    .execute()
                )

                if conv_result.data:
                    bound_version_id = conv_result.data.get("system_instruction_version_id")

                    if bound_version_id:
                        # Use the bound version for consistency
                        try:
                            system_prompt = get_system_instructions_for_version(
                                version_id=bound_version_id, user_data=current_user
                            )
                            logger.info(f"Using bound version {bound_version_id} for conversation")
                        except ValueError as ve:
                            logger.warning(f"Bound version not found: {ve}, falling back")
                    else:
                        # No bound version - get active version and bind it
                        active_version = get_active_system_instruction_version()
                        if active_version:
                            system_prompt = get_system_instructions_for_version(
                                version_id=active_version["id"], user_data=current_user
                            )
                            version_id_to_bind = active_version["id"]
                            logger.info(f"Binding conversation to version {active_version['version_number']}")

            # If we still don't have a prompt, try active version or legacy fallback
            if not system_prompt:
                active_version = get_active_system_instruction_version()
                if active_version:
                    system_prompt = get_system_instructions_for_version(
                        version_id=active_version["id"], user_data=current_user
                    )
                    if chat_request.conversation_id:
                        version_id_to_bind = active_version["id"]
                else:
                    # Fallback to legacy per-user instructions
                    system_prompt = get_system_instructions_for_user(user_id=current_user["id"], user_data=current_user)

            # Bind the version to the conversation if needed (async, non-blocking)
            if version_id_to_bind and chat_request.conversation_id:
                try:
                    await asyncio.to_thread(
                        lambda: supabase.table("conversations")
                        .update({"system_instruction_version_id": version_id_to_bind})
                        .eq("id", chat_request.conversation_id)
                        .execute()
                    )
                    logger.info(f"Bound conversation {chat_request.conversation_id} to version {version_id_to_bind}")
                except Exception as bind_error:
                    logger.warning(f"Failed to bind version to conversation: {bind_error}")

        except Exception as e:
            logger.warning(f"Could not load system instructions: {e}")
            user_name = current_user.get("name", "User")
            system_prompt = (
                f"You are Thesis, a helpful AI assistant for {user_name}. "
                "Provide clear, accurate, and professional assistance."
            )

        user_prompt = chat_request.message

        # Track if RAG was attempted but found nothing
        rag_attempted_no_results = chat_request.use_rag and not is_simple_message and not context_chunks

        # Only add context if we have relevant chunks (above threshold)
        source_documents = []
        if context_chunks:
            context_parts = []
            for i, chunk in enumerate(context_chunks):
                # Build source info with metadata
                source_info = f"[Source {i + 1} - Relevance: {chunk['similarity']:.2f}"

                # Add document metadata if available
                metadata = chunk.get("metadata", {})
                if metadata:
                    if metadata.get("filename"):
                        source_info += f" - File: {metadata['filename']}"
                    elif metadata.get("conversation_title"):
                        source_info += f" - Conversation: {metadata['conversation_title']}"

                # Add document date if available (helps agent understand recency)
                doc_date = chunk.get("created_at")
                if doc_date:
                    # Extract just the date portion (YYYY-MM-DD)
                    date_str = str(doc_date)[:10] if doc_date else None
                    if date_str:
                        source_info += f" - Date: {date_str}"

                source_info += "]"
                context_parts.append(f"{source_info}:\n{chunk['content']}")

                # Create source document object for frontend
                source_documents.append(
                    {
                        "chunk_id": chunk.get("id", f"chunk_{i}"),
                        "document_id": chunk.get("document_id", ""),
                        "document_name": metadata.get("filename", metadata.get("conversation_title", "Unknown")),
                        "relevance_score": chunk["similarity"],
                        "snippet": chunk["content"][:500],  # First 500 chars as snippet
                        "metadata": metadata,
                    }
                )

            context_text = "\n\n".join(context_parts)
            user_prompt = f"""You have access to the user's knowledge base. Here are the most relevant excerpts related to their question:

<knowledge_base_context>
{context_text}
</knowledge_base_context>

User's question: {chat_request.message}

CRITICAL INSTRUCTIONS - PRIORITIZE KB CONTEXT:
- The knowledge base above contains REAL information from the user's documents
- If the KB context addresses the question, you MUST reference it specifically
- Quote relevant passages and cite sources (e.g., "According to the interview transcript...")
- DO NOT ignore KB content in favor of general knowledge when specific data exists
- If KB context is incomplete or doesn't address the question, say so explicitly
- Be specific about which parts come from KB versus general knowledge"""
        elif rag_attempted_no_results:
            # RAG was attempted but no relevant documents were found
            # Add a note so the assistant can be honest about this
            user_prompt = f"""<knowledge_base_search_result>
I searched your knowledge base but could not find any documents relevant to this query. This could mean:
- The document hasn't finished processing yet (try again in a moment)
- The document content doesn't closely match your question's wording
- No documents have been uploaded yet
</knowledge_base_search_result>

User's question: {chat_request.message}

Instructions:
- Be honest that you couldn't find relevant content in the knowledge base
- If the user is asking about a specific document they uploaded, let them know you couldn't locate it and suggest they verify the upload or try rephrasing
- You can still provide general assistance, but clearly distinguish between knowledge base content (which you don't have) and general knowledge"""

        logger.info("Calling Claude API")

        # Build conversation history for Claude
        conversation_messages = []
        if chat_request.conversation_id:
            # Fetch ALL previous messages from this conversation
            # Claude Sonnet 4 has 200K token context - let it use full conversation
            history_result = (
                supabase.table("messages")
                .select("role,content")
                .eq("conversation_id", chat_request.conversation_id)
                .order("created_at", desc=False)
                .execute()
            )

            if history_result.data:
                for msg in history_result.data:
                    # Claude expects 'user' or 'assistant' roles
                    if msg["role"] in ["user", "assistant"] and msg["content"]:
                        conversation_messages.append({"role": msg["role"], "content": msg["content"]})
                logger.info(f"Loaded {len(conversation_messages)} messages from conversation history")

        # Add the current user message (with RAG context if available)
        conversation_messages.append({"role": "user", "content": user_prompt})

        # Call Claude API with prompt caching for system instructions
        # Cached tokens are 90% cheaper - significant savings for repeated chats
        # Prepend date context so agent knows current date
        full_system_prompt = _get_date_context() + system_prompt
        message = anthropic_client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2048,  # Reduced from 4096 to encourage more concise responses
            temperature=0.3,  # Lower temperature for more focused, concise responses
            system=[
                {
                    "type": "text",
                    "text": full_system_prompt,
                    "cache_control": {"type": "ephemeral"},  # Cache for 5 minutes
                }
            ],
            messages=conversation_messages,
        )

        response_text = message.content[0].text

        # Extract cache statistics if available
        cache_read_tokens = getattr(message.usage, "cache_read_input_tokens", 0) or 0
        cache_creation_tokens = getattr(message.usage, "cache_creation_input_tokens", 0) or 0

        logger.info(
            "Response generated",
            extra={
                "output_tokens": message.usage.output_tokens,
                "input_tokens": message.usage.input_tokens,
                "cache_read_tokens": cache_read_tokens,
                "cache_creation_tokens": cache_creation_tokens,
            },
        )

        # Save messages to database if conversation_id provided
        if chat_request.conversation_id:
            # Check if we should suggest an image
            conversation_service = get_conversation_service()

            # Get recent messages for context
            recent_messages_result = (
                supabase.table("messages")
                .select("*")
                .eq("conversation_id", chat_request.conversation_id)
                .order("created_at", desc=True)
                .limit(5)
                .execute()
            )

            recent_messages = recent_messages_result.data if recent_messages_result.data else []

            # Check if we should suggest an image
            suggestion = conversation_service.should_suggest_image(
                user_message=chat_request.message,
                assistant_response=response_text,
                recent_messages=recent_messages,
            )

            # Prepare assistant message metadata
            assistant_metadata = {}
            if suggestion.get("suggest"):
                assistant_metadata["image_suggestion"] = {
                    "suggested_prompt": suggestion["suggested_prompt"],
                    "reason": suggestion["reason"],
                    "image_type": suggestion.get("image_type"),
                    "subject": suggestion.get("subject"),
                }
                logger.info(
                    f"Image suggestion added: {suggestion.get('image_type', 'general')} - {suggestion['suggested_prompt']}"
                )

            # Batch insert both messages in a single DB call for better performance
            messages_to_insert = [
                {
                    "conversation_id": chat_request.conversation_id,
                    "role": "user",
                    "content": chat_request.message,
                },
                {
                    "conversation_id": chat_request.conversation_id,
                    "role": "assistant",
                    "content": response_text,
                    "metadata": assistant_metadata if assistant_metadata else None,
                },
            ]
            result = supabase.table("messages").insert(messages_to_insert).execute()

            logger.info("Messages saved to conversation")

            # Link uploaded documents to the user's message
            if chat_request.document_ids and len(chat_request.document_ids) > 0:
                # Get the user message ID (first inserted message)
                user_message_id = result.data[0]["id"]

                # Create message-document links
                message_docs_to_insert = [
                    {"message_id": user_message_id, "document_id": doc_id} for doc_id in chat_request.document_ids
                ]

                supabase.table("message_documents").insert(message_docs_to_insert).execute()
                logger.info(f"Linked {len(chat_request.document_ids)} documents to message")

            # Process for useable output detection (Bradbury Impact Loop)
            # This runs keyword analysis to detect when useable output is achieved
            try:
                process_conversation_for_useable_output(chat_request.conversation_id)
            except Exception as detection_error:
                # Log but don't fail the request if detection fails
                logger.warning(f"Useable output detection failed: {detection_error}")

        return {
            "success": True,
            "response": response_text,
            "context_used": len(context_chunks),
            "source_documents": source_documents,
            "tokens": {
                "input": message.usage.input_tokens,
                "output": message.usage.output_tokens,
                "total": message.usage.input_tokens + message.usage.output_tokens,
                "cache_read": cache_read_tokens,
                "cache_creation": cache_creation_tokens,
            },
        }

    except Exception:
        logger.exception("Error processing chat request", exc_info=True, extra={"user_id": current_user["id"]})
        raise


@router.post("/stream")
@limiter.limit("20/minute")
async def chat_stream(request: Request, chat_request: ChatRequest, current_user: dict = Depends(get_current_user)):
    """Streaming chat endpoint with RAG (Retrieval Augmented Generation).

    Streams AI responses in real-time using Server-Sent Events (SSE).
    Provides better UX with incremental response display.

    **Request Body:**
    - conversation_id: UUID of conversation to save messages
    - message: User's question/message (1-10000 chars)
    - document_ids: Optional list of document IDs to search (uses all if empty)

    **Response:**
    Server-Sent Events stream with:
    - `data: {"type": "token", "content": "..."}` - Text chunks
    - `data: {"type": "done", "tokens": {...}}` - Stream complete with token stats
    - `data: {"type": "error", "error": "..."}` - Error occurred

    **Rate Limit:** 20 requests per minute

    **Errors:**
    - 400: Invalid request (missing required fields, message too long)
    - 401: Not authenticated
    - 429: Rate limit exceeded
    - 500: Server error (AI API failure, database error)
    """
    logger.info(
        "Streaming chat request received",
        extra={
            "user_id": current_user["id"],
            "conversation_id": chat_request.conversation_id,
            "message_length": len(chat_request.message),
        },
    )

    async def generate_stream():
        """Generator function for SSE stream."""
        try:
            logger.info(f"Processing chat request: {chat_request.message[:100]}")

            # Check if the previous message was awaiting image confirmation
            if chat_request.conversation_id:
                last_assistant_msg = (
                    supabase.table("messages")
                    .select("metadata")
                    .eq("conversation_id", chat_request.conversation_id)
                    .eq("role", "assistant")
                    .order("created_at", desc=True)
                    .limit(1)
                    .execute()
                )

                if last_assistant_msg.data and last_assistant_msg.data[0].get("metadata"):
                    metadata = last_assistant_msg.data[0]["metadata"]
                    if metadata.get("awaiting_image_confirmation"):
                        # Check if user is confirming
                        user_msg_lower = chat_request.message.lower().strip()
                        # Expanded confirmation phrases including common variations
                        confirmation_phrases = [
                            "yes",
                            "yep",
                            "yeah",
                            "yup",
                            "ya",
                            "yea",
                            "proceed",
                            "go ahead",
                            "go for it",
                            "do it",
                            "go",
                            "ok",
                            "okay",
                            "k",
                            "sure",
                            "absolutely",
                            "definitely",
                            "please",
                            "please do",
                            "yes please",
                            "generate",
                            "create it",
                            "make it",
                            "build it",
                            "let's do it",
                            "let's go",
                            "sounds good",
                            "looks good",
                            "that works",
                            "perfect",
                            "great",
                            "good",
                            "fine",
                            "approved",
                            "confirm",
                            "confirmed",
                            "affirmative",
                            "try",
                            "try it",
                            "give it a try",
                            "let's try",
                        ]

                        # Check for confirmation - either exact match or phrase contained
                        is_confirmed = (
                            user_msg_lower in confirmation_phrases  # Exact match
                            or any(phrase in user_msg_lower for phrase in confirmation_phrases)  # Contains phrase
                        )

                        # Check for explicit decline/cancel
                        decline_phrases = [
                            "no",
                            "nope",
                            "nah",
                            "cancel",
                            "stop",
                            "nevermind",
                            "never mind",
                            "forget it",
                            "skip",
                            "don't",
                            "dont",
                            "not now",
                            "later",
                        ]
                        is_declined = user_msg_lower in decline_phrases or any(
                            phrase in user_msg_lower for phrase in decline_phrases
                        )

                        # Check for simple greetings/unrelated messages
                        greeting_phrases = [
                            "hello",
                            "hi",
                            "hey",
                            "greetings",
                            "good morning",
                            "good afternoon",
                            "good evening",
                            "howdy",
                            "yo",
                            "sup",
                            "what's up",
                            "whats up",
                        ]
                        is_greeting = user_msg_lower in greeting_phrases

                        if is_declined:
                            # User declined - clear the pending state and acknowledge
                            logger.info("User declined image generation")

                            # Clear awaiting_image_confirmation by updating metadata
                            supabase.table("messages").update(
                                {
                                    "metadata": {
                                        "awaiting_image_confirmation": False,
                                        "declined": True,
                                    }
                                }
                            ).eq("conversation_id", chat_request.conversation_id).eq("role", "assistant").order(
                                "created_at", desc=True
                            ).limit(1).execute()

                            response = "No problem! Let me know if you'd like to create a visual later, or if there's something else I can help with."
                            for char in response:
                                yield f"data: {json.dumps({'type': 'token', 'content': char})}\n\n"
                                await asyncio.sleep(0.005)

                            # Save messages
                            messages_to_insert = [
                                {
                                    "conversation_id": chat_request.conversation_id,
                                    "role": "user",
                                    "content": chat_request.message,
                                },
                                {
                                    "conversation_id": chat_request.conversation_id,
                                    "role": "assistant",
                                    "content": response,
                                },
                            ]
                            supabase.table("messages").insert(messages_to_insert).execute()

                            yield f"data: {json.dumps({'type': 'done', 'tokens': {'input': 0, 'output': 0, 'total': 0}})}\n\n"
                            return

                        if is_greeting:
                            # User sent a greeting while we were waiting for confirmation
                            # Clear the pending state and respond to greeting naturally
                            logger.info("User sent greeting while awaiting image confirmation - clearing state")

                            # Clear awaiting_image_confirmation
                            supabase.table("messages").update(
                                {
                                    "metadata": {
                                        "awaiting_image_confirmation": False,
                                        "interrupted": True,
                                    }
                                }
                            ).eq("conversation_id", chat_request.conversation_id).eq("role", "assistant").order(
                                "created_at", desc=True
                            ).limit(1).execute()

                            response = "Hello! I was waiting for your preference on the image options. Would you still like me to create that visual, or is there something else I can help you with?"
                            for char in response:
                                yield f"data: {json.dumps({'type': 'token', 'content': char})}\n\n"
                                await asyncio.sleep(0.005)

                            # Save messages
                            messages_to_insert = [
                                {
                                    "conversation_id": chat_request.conversation_id,
                                    "role": "user",
                                    "content": chat_request.message,
                                },
                                {
                                    "conversation_id": chat_request.conversation_id,
                                    "role": "assistant",
                                    "content": response,
                                },
                            ]
                            supabase.table("messages").insert(messages_to_insert).execute()

                            yield f"data: {json.dumps({'type': 'done', 'tokens': {'input': 0, 'output': 0, 'total': 0}})}\n\n"
                            return

                        if is_confirmed:
                            logger.info("User confirmed image generation - proceeding with image creation")

                            # Import services
                            from database import DatabaseService
                            from services.image_generation import get_image_generation_service
                            from services.storage_service import get_storage_service

                            try:
                                user_id = current_user.get("id")

                                # Get prompt from the new image_suggestion format OR legacy format
                                image_suggestion = metadata.get("image_suggestion", {})
                                if image_suggestion.get("suggested_prompt"):
                                    # New format
                                    prompt = image_suggestion["suggested_prompt"]
                                    visual_type = image_suggestion.get("visual_type", "visual")
                                else:
                                    # Legacy format fallback
                                    visual_type = metadata.get("suggested_visual_type", "visual")
                                    suggested_content = metadata.get("suggested_content", "")
                                    prompt = f"Create a {visual_type} showing: {suggested_content}"

                                if not prompt or prompt.strip() == f"Create a {visual_type} showing: ":
                                    raise Exception("No valid prompt found in pending image suggestion")

                                logger.info(f"Generating image from confirmation with prompt: {prompt[:100]}...")

                                # Generate the image
                                image_service = get_image_generation_service()
                                result = await image_service.generate_image(
                                    prompt=prompt, model="fast", aspect_ratio="16:9"
                                )

                                if not result.get("success"):
                                    raise Exception("Image generation failed")

                                logger.info(f"Image generated from confirmation: {len(result['image_data'])} bytes")

                                # Upload to storage
                                storage_service = get_storage_service()
                                mime_type = result["mime_type"]
                                file_ext = mime_type.split("/")[-1] if "/" in mime_type else "png"

                                upload_result = storage_service.upload_image(
                                    image_data=result["image_data"],
                                    user_id=user_id,
                                    conversation_id=chat_request.conversation_id,
                                    file_extension=file_ext,
                                )

                                if not upload_result:
                                    raise Exception("Failed to upload image")

                                # Store in database
                                db = DatabaseService.get_client()
                                image_record = {
                                    "conversation_id": chat_request.conversation_id,
                                    "message_id": None,
                                    "prompt": prompt,
                                    "aspect_ratio": "16:9",
                                    "model": result["model"],
                                    "storage_url": upload_result["storage_url"],
                                    "storage_path": upload_result["storage_path"],
                                    "mime_type": upload_result["content_type"],
                                    "file_size": upload_result["file_size"],
                                    "metadata": {"from_confirmation": True},
                                }

                                insert_result = db.table("conversation_images").insert(image_record).execute()
                                stored_image = insert_result.data[0]

                                # Clear the awaiting_image_confirmation state from the previous message
                                supabase.table("messages").update(
                                    {
                                        "metadata": {
                                            "awaiting_image_confirmation": False,
                                            "image_generated": True,
                                        }
                                    }
                                ).eq("conversation_id", chat_request.conversation_id).eq("role", "assistant").order(
                                    "created_at", desc=True
                                ).limit(1).execute()

                                # No text response - just show the image
                                yield f"data: {json.dumps({'type': 'image_generated', 'image_id': stored_image['id'], 'storage_url': stored_image['storage_url'], 'prompt': prompt[:200] if prompt else '', 'aspect_ratio': '16:9', 'model': result['model'], 'mime_type': upload_result['content_type'], 'file_size': upload_result['file_size']})}\n\n"
                                yield f"data: {json.dumps({'type': 'done', 'tokens': {'input': 0, 'output': 0, 'total': 0}})}\n\n"

                                # Save messages (minimal - just to track the exchange)
                                messages_to_insert = [
                                    {
                                        "conversation_id": chat_request.conversation_id,
                                        "role": "user",
                                        "content": chat_request.message,
                                    },
                                    {
                                        "conversation_id": chat_request.conversation_id,
                                        "role": "assistant",
                                        "content": "",
                                        "metadata": {
                                            "has_image": True,
                                            "image_id": stored_image["id"],
                                        },
                                    },
                                ]
                                supabase.table("messages").insert(messages_to_insert).execute()

                                return  # Exit - image generated from confirmation

                            except Exception as confirm_error:
                                logger.error(
                                    f"Image generation from confirmation failed: {confirm_error}",
                                    exc_info=True,
                                )

                                # Clear the pending state even on error
                                supabase.table("messages").update(
                                    {
                                        "metadata": {
                                            "awaiting_image_confirmation": False,
                                            "error": str(confirm_error),
                                        }
                                    }
                                ).eq("conversation_id", chat_request.conversation_id).eq("role", "assistant").order(
                                    "created_at", desc=True
                                ).limit(1).execute()

                                error_msg = "I'm sorry, I encountered an error generating the image. Please try again."
                                yield f"data: {json.dumps({'type': 'token', 'content': error_msg})}\n\n"
                                yield f"data: {json.dumps({'type': 'done', 'tokens': {'input': 0, 'output': 0, 'total': 0}})}\n\n"
                                return

                        # If we reach here, user said something else while we were awaiting confirmation
                        # Clear the pending state and continue processing their new message
                        logger.info(
                            "User sent new message while awaiting image confirmation - clearing pending state and processing new request"
                        )
                        supabase.table("messages").update(
                            {"metadata": {"awaiting_image_confirmation": False, "superseded": True}}
                        ).eq("conversation_id", chat_request.conversation_id).eq("role", "assistant").order(
                            "created_at", desc=True
                        ).limit(1).execute()
                        # Fall through to process the new message normally

            # Check if this is an explicit image generation request
            conversation_service = get_conversation_service()
            image_request = conversation_service.extract_image_request(chat_request.message)
            logger.info(f"Image request check result: {image_request}")

            if image_request.get("is_request") and chat_request.conversation_id:
                # This is an image generation request - handle it directly
                logger.info(f"Detected image generation request: {image_request['prompt'][:50]}...")

                # Import services directly
                import google.generativeai as genai

                from database import DatabaseService
                from services.image_generation import get_image_generation_service
                from services.storage_service import get_storage_service

                try:
                    user_id = current_user.get("id")
                    image_request["prompt"]
                    full_message = chat_request.message  # The complete user message
                    image_request.get("aspect_ratio") or "16:9"
                    image_request.get("model") or "fast"

                    # Determine the visual type from the original request
                    visual_type = "visual"
                    for vtype in [
                        "mind map",
                        "mindmap",
                        "flowchart",
                        "flow chart",
                        "diagram",
                        "infographic",
                        "timeline",
                        "chart",
                        "comparison",
                    ]:
                        if vtype in full_message.lower():
                            visual_type = vtype.replace("_", " ")
                            break

                    # IMPROVED CONTENT DETECTION LOGIC:
                    # 1. If message has enough content, use it directly (more flexible detection)
                    # 2. If message is vague, check conversation history and ASK USER to confirm

                    # Check if message itself has substantial content
                    # More flexible detection - doesn't require strict formatting
                    message_has_content = _message_has_substantial_content(full_message)

                    prompt = None

                    if message_has_content:
                        # User provided the content - extract prompt and ASK for preferences
                        logger.info("Message contains content - extracting prompt and asking for preferences")
                        # Just use the full message as context for Gemini to create the prompt
                        genai.configure(api_key=os.environ.get("GOOGLE_GENERATIVE_AI_API_KEY"))
                        gemini_model = genai.GenerativeModel("gemini-2.0-flash")

                        extraction_prompt = f"""Create a CONCISE image generation prompt (max 200 words) from this content.

CONTENT:
{full_message}

Create a {visual_type} prompt that captures the KEY items and structure.
Do NOT include lengthy descriptions or quotes from the original text.
Focus on visual elements: layout, colors, icons, structure.

Output ONLY the concise image prompt, nothing else."""

                        response = gemini_model.generate_content(extraction_prompt)
                        prompt = response.text.strip().strip("\"'")
                        logger.info(f"Extracted prompt: {prompt[:100]}...")

                        # Instead of generating immediately, send suggestion event for user to choose options
                        # Save the user message first
                        (
                            supabase.table("messages")
                            .insert(
                                {
                                    "conversation_id": chat_request.conversation_id,
                                    "role": "user",
                                    "content": chat_request.message,
                                }
                            )
                            .execute()
                        )

                        # Create assistant message with pending image suggestion
                        assistant_msg_result = (
                            supabase.table("messages")
                            .insert(
                                {
                                    "conversation_id": chat_request.conversation_id,
                                    "role": "assistant",
                                    "content": "",
                                    "metadata": {
                                        "awaiting_image_confirmation": True,
                                        "image_suggestion": {
                                            "suggested_prompt": prompt,
                                            "reason": f"Ready to create your {visual_type}",
                                            "image_type": visual_type,
                                            "visual_type": visual_type,
                                        },
                                    },
                                }
                            )
                            .execute()
                        )

                        assistant_msg_id = assistant_msg_result.data[0]["id"] if assistant_msg_result.data else None

                        # Send the image suggestion event so frontend shows the options dialog
                        suggestion_event = {
                            "type": "image_suggestion",
                            "suggestion": {
                                "message_id": assistant_msg_id,
                                "suggested_prompt": prompt,
                                "reason": f"Ready to create your {visual_type}",
                                "image_type": visual_type,
                            },
                        }
                        yield f"data: {json.dumps(suggestion_event)}\n\n"
                        yield f"data: {json.dumps({'type': 'done', 'tokens': {'input': 0, 'output': 0, 'total': 0}})}\n\n"
                        logger.info(f"Sent image suggestion for explicit request: {prompt[:50]}...")
                        return  # Exit - wait for user to select options

                    else:
                        # Message is vague - need to look at conversation history
                        # BUT instead of guessing, we should confirm with the user
                        logger.info("Message is vague - checking conversation history and will confirm with user")

                        context_messages_result = (
                            supabase.table("messages")
                            .select("role,content,created_at")
                            .eq("conversation_id", chat_request.conversation_id)
                            .order("created_at", desc=True)
                            .limit(20)
                            .execute()
                        )

                        context_messages = context_messages_result.data or []

                        if context_messages:
                            context_messages.reverse()

                            # Use Gemini to understand what the user likely wants
                            genai.configure(api_key=os.environ.get("GOOGLE_GENERATIVE_AI_API_KEY"))
                            gemini_model = genai.GenerativeModel("gemini-2.0-flash")

                            context_text = "\n\n".join(
                                [
                                    f"{msg['role'].upper()}: {msg['content'][:1500]}"
                                    for msg in context_messages[-10:]  # Last 10 messages
                                ]
                            )

                            understanding_prompt = f"""Based on this conversation, the user wants to create a {visual_type}.

CONVERSATION:
{context_text}

USER'S REQUEST: "{full_message}"

What specific content from the conversation should be visualized in this {visual_type}?
Be specific - list the actual items, concepts, or topics that should appear.

Your response (be specific about what to visualize):"""

                            response = gemini_model.generate_content(understanding_prompt)
                            suggested_content = response.text.strip()

                            # Create a prompt from the suggested content
                            prompt_from_context = f"{visual_type} showing: {suggested_content}"

                            # Save user message
                            supabase.table("messages").insert(
                                {
                                    "conversation_id": chat_request.conversation_id,
                                    "role": "user",
                                    "content": chat_request.message,
                                }
                            ).execute()

                            # Create assistant message with pending image suggestion
                            assistant_msg_result = (
                                supabase.table("messages")
                                .insert(
                                    {
                                        "conversation_id": chat_request.conversation_id,
                                        "role": "assistant",
                                        "content": "",
                                        "metadata": {
                                            "awaiting_image_confirmation": True,
                                            "image_suggestion": {
                                                "suggested_prompt": prompt_from_context,
                                                "reason": f"Based on our conversation, I can create a {visual_type} showing:\n\n{suggested_content}",
                                                "image_type": visual_type,
                                                "visual_type": visual_type,
                                            },
                                        },
                                    }
                                )
                                .execute()
                            )

                            assistant_msg_id = assistant_msg_result.data[0]["id"] if assistant_msg_result.data else None

                            # Send image suggestion event for user to choose options
                            suggestion_event = {
                                "type": "image_suggestion",
                                "suggestion": {
                                    "message_id": assistant_msg_id,
                                    "suggested_prompt": prompt_from_context,
                                    "reason": f"Based on our conversation, I can create a {visual_type} showing:\n\n{suggested_content}",
                                    "image_type": visual_type,
                                },
                            }
                            yield f"data: {json.dumps(suggestion_event)}\n\n"
                            yield f"data: {json.dumps({'type': 'done', 'tokens': {'input': 0, 'output': 0, 'total': 0}})}\n\n"
                            logger.info(f"Sent image suggestion from context: {prompt_from_context[:50]}...")
                            return  # Exit - wait for user to select options

                        else:
                            # No conversation history - ask user what they want
                            no_context_response = f"""I'd like to create a {visual_type} for you, but I need more details about what to include.

Could you tell me what specific content, items, or concepts you'd like me to visualize?"""

                            for char in no_context_response:
                                yield f"data: {json.dumps({'type': 'token', 'content': char})}\n\n"
                                await asyncio.sleep(0.005)

                            messages_to_insert = [
                                {
                                    "conversation_id": chat_request.conversation_id,
                                    "role": "user",
                                    "content": chat_request.message,
                                },
                                {
                                    "conversation_id": chat_request.conversation_id,
                                    "role": "assistant",
                                    "content": no_context_response,
                                },
                            ]
                            supabase.table("messages").insert(messages_to_insert).execute()

                            yield f"data: {json.dumps({'type': 'done', 'tokens': {'input': 0, 'output': 0, 'total': 0}})}\n\n"
                            return  # Exit - wait for user to provide content

                    # If we reach here without a prompt and no confirmation was sent,
                    # something went wrong - DO NOT fall through silently
                    if not prompt:
                        logger.warning("No prompt generated for image request - providing helpful message to user")
                        # Give the user a helpful message instead of silently falling through
                        helpful_message = f"""I detected you want to create a {visual_type}, but I need a bit more detail to proceed.

Could you please provide:
- The specific content, items, or concepts you want me to visualize
- Or paste the text/information you'd like me to turn into a {visual_type}

For example: "Create a diagram of the 10 learning design issues we discussed" or paste the content directly."""

                        for char in helpful_message:
                            yield f"data: {json.dumps({'type': 'token', 'content': char})}\n\n"
                            await asyncio.sleep(0.005)

                        # Save the exchange
                        if chat_request.conversation_id:
                            messages_to_insert = [
                                {
                                    "conversation_id": chat_request.conversation_id,
                                    "role": "user",
                                    "content": chat_request.message,
                                },
                                {
                                    "conversation_id": chat_request.conversation_id,
                                    "role": "assistant",
                                    "content": helpful_message,
                                    "metadata": {
                                        "needs_image_content": True,
                                        "requested_visual_type": visual_type,
                                    },
                                },
                            ]
                            supabase.table("messages").insert(messages_to_insert).execute()

                        yield f"data: {json.dumps({'type': 'done', 'tokens': {'input': 0, 'output': 0, 'total': 0}})}\n\n"
                        return  # Exit - don't fall through to normal chat

                except Exception as img_error:
                    logger.error(f"Image generation failed: {img_error}", exc_info=True)
                    # Send error message and stop - don't fall through to chat
                    error_message = (
                        "I apologize, but I encountered an error while generating the image. Please try again."
                    )
                    yield f"data: {json.dumps({'type': 'token', 'content': error_message})}\n\n"
                    yield f"data: {json.dumps({'type': 'done', 'tokens': {'input': 0, 'output': 0, 'total': 0}})}\n\n"
                    return  # Stop here - don't continue to normal chat

            # Detect simple greetings or conversational messages that don't need RAG
            simple_messages = {
                "hello",
                "hi",
                "hey",
                "greetings",
                "good morning",
                "good afternoon",
                "good evening",
                "howdy",
                "yo",
                "sup",
                "what's up",
                "whats up",
                "thanks",
                "thank you",
                "bye",
                "goodbye",
                "see you",
                "ok",
                "okay",
            }
            message_lower = chat_request.message.lower().strip()
            is_simple_message = message_lower in simple_messages or len(chat_request.message.split()) <= 2

            # Build context from documents using RAG (conditionally)
            context_chunks = []

            # Only search if use_rag is enabled and message isn't a simple greeting
            if chat_request.use_rag and not is_simple_message:
                logger.info("Searching knowledge base for context")

                # Get user's client_id for document filtering
                client_id = current_user.get("client_id")

                # Search all documents in the user's knowledge base
                # conversation_id is passed to prioritize files referenced in the conversation
                search_results = search_similar_chunks(
                    chat_request.message,
                    client_id,
                    limit=5,
                    min_similarity=0.0,  # Use adaptive threshold based on query type
                    document_ids=chat_request.document_ids,
                    conversation_id=chat_request.conversation_id,
                )
                context_chunks = search_results
                logger.info(f"Found {len(context_chunks)} relevant chunks")

                # Send context info to client
                yield f"data: {json.dumps({'type': 'context', 'count': len(context_chunks)})}\n\n"
            else:
                logger.info(f"Skipping RAG - use_rag={chat_request.use_rag}, is_simple_message={is_simple_message}")

            # Select agent and load system instructions
            # Priority: 1) Explicit agent_ids from request, 2) @mention in message, 3) Coordinator routing
            chat_agent_service = get_chat_agent_service()

            # Get conversation context for agent continuity
            conversation_context = None
            if chat_request.conversation_id:
                conversation_context = await chat_agent_service.get_conversation_agent_context(
                    chat_request.conversation_id
                )

            # Get fallback instruction (per-user) in case no agent instruction found
            try:
                fallback_instruction = get_system_instructions_for_user(
                    user_id=current_user["id"], user_data=current_user
                )
            except FileNotFoundError:
                user_name = current_user.get("name", "User")
                fallback_instruction = (
                    f"You are Thesis, a helpful AI assistant for {user_name}. "
                    "Provide clear, accurate, and professional assistance."
                )

            # Select the agent and get their instruction
            agent_selection = await chat_agent_service.select_agent(
                message=chat_request.message,
                agent_ids=chat_request.agent_ids,
                conversation_context=conversation_context,
                fallback_instruction=fallback_instruction,
            )

            system_prompt = agent_selection.system_instruction
            selected_agent = agent_selection.primary_agent
            agent_display_name = agent_selection.display_name

            logger.info(
                f"Agent selected: {selected_agent} ({agent_selection.reason})",
                extra={
                    "agent": selected_agent,
                    "confidence": agent_selection.confidence,
                    "supporting_agents": agent_selection.supporting_agents,
                },
            )

            # Send agent info to client
            yield f"data: {json.dumps({'type': 'agent', 'agent': selected_agent, 'display_name': agent_display_name})}\n\n"

            user_prompt = chat_request.message

            # Inject project context for project_agent conversations
            if selected_agent == "project_agent" and chat_request.conversation_id:
                try:
                    conv_result = await asyncio.to_thread(
                        lambda: supabase.table("conversations")
                        .select("project_id")
                        .eq("id", chat_request.conversation_id)
                        .single()
                        .execute()
                    )
                    project_id = conv_result.data.get("project_id") if conv_result.data else None
                    if project_id:
                        proj_result = await asyncio.to_thread(
                            lambda: supabase.table("ai_projects").select("*").eq("id", project_id).single().execute()
                        )
                        if proj_result.data:
                            related_docs = get_scoring_related_documents(
                                project=proj_result.data, client_id=client_id, limit=5
                            )
                            project_context_text = build_project_context(proj_result.data, related_docs)
                            user_prompt = f"""{project_context_text}

User's question: {chat_request.message}"""
                            logger.info(f"Injected project context for project {project_id}")
                except Exception as proj_err:
                    logger.warning(f"Failed to load project context: {proj_err}")

            # Track if RAG was attempted but found nothing
            rag_attempted_no_results = chat_request.use_rag and not is_simple_message and not context_chunks

            # ============================================================================
            # ATLAS WEB RESEARCH - Auto-research when knowledge base has no results
            # ============================================================================
            web_research_context = None
            web_research_citations = []

            if selected_agent == "atlas" and rag_attempted_no_results:
                # Atlas was selected but no KB results - perform web research automatically
                logger.info("Atlas selected with no KB results - performing web research")
                yield f"data: {json.dumps({'type': 'status', 'message': 'Researching the web...'})}\n\n"

                try:
                    from services.web_researcher import research_topic_with_web

                    # Perform web research on the user's query
                    web_context, citations = await research_topic_with_web(
                        topic=chat_request.message, focus_area="general", max_sources=8
                    )

                    if web_context and citations:
                        web_research_context = web_context
                        web_research_citations = citations
                        logger.info(f"Web research found {len(citations)} sources")
                        yield f"data: {json.dumps({'type': 'status', 'message': f'Found {len(citations)} sources'})}\n\n"
                    else:
                        logger.info("Web research returned no results")

                except Exception as web_err:
                    logger.warning(f"Web research failed: {web_err}")
                    # Continue without web research - don't fail the request

            # Only add context if we have relevant chunks (above threshold)
            source_documents = []
            if context_chunks:
                context_parts = []
                for i, chunk in enumerate(context_chunks):
                    # Build source info with metadata
                    source_info = f"[Source {i + 1} - Relevance: {chunk['similarity']:.2f}"

                    # Add document metadata if available
                    metadata = chunk.get("metadata", {})
                    if metadata:
                        if metadata.get("filename"):
                            source_info += f" - File: {metadata['filename']}"
                        elif metadata.get("conversation_title"):
                            source_info += f" - Conversation: {metadata['conversation_title']}"

                    source_info += "]"
                    context_parts.append(f"{source_info}:\n{chunk['content']}")

                    # Create source document object for frontend
                    source_documents.append(
                        {
                            "chunk_id": chunk.get("id", f"chunk_{i}"),
                            "document_id": chunk.get("document_id", ""),
                            "document_name": metadata.get("filename", metadata.get("conversation_title", "Unknown")),
                            "relevance_score": chunk["similarity"],
                            "snippet": chunk["content"][:500],  # First 500 chars as snippet
                            "metadata": metadata,
                        }
                    )

                context_text = "\n\n".join(context_parts)
                user_prompt = f"""You have access to the user's knowledge base. Here are the most relevant excerpts related to their question:

<knowledge_base_context>
{context_text}
</knowledge_base_context>

User's question: {chat_request.message}

CRITICAL INSTRUCTIONS - PRIORITIZE KB CONTEXT:
- The knowledge base above contains REAL information from the user's documents
- If the KB context addresses the question, you MUST reference it specifically
- Quote relevant passages and cite sources (e.g., "According to the interview transcript...")
- DO NOT ignore KB content in favor of general knowledge when specific data exists
- If KB context is incomplete or doesn't address the question, say so explicitly
- Be specific about which parts come from KB versus general knowledge"""
            elif rag_attempted_no_results:
                # RAG was attempted but no relevant documents were found
                if web_research_context:
                    # Atlas with web research results - provide comprehensive context
                    user_prompt = f"""<knowledge_base_search_result>
I searched your knowledge base but found no relevant documents for this query.
However, I performed web research and found the following sources:
</knowledge_base_search_result>

<web_research_context>
{web_research_context}
</web_research_context>

User's question: {chat_request.message}

Instructions:
- Use the web research context above to provide a comprehensive, evidence-based response
- Cite specific sources when making claims (use the source names/URLs provided)
- Prioritize Tier 1-2 sources for key claims, use Tier 3-4 as supporting signals
- Follow your standard research synthesis format
- Be clear that this information comes from web research, not the user's internal knowledge base"""
                else:
                    # No KB results and no web research - standard fallback
                    user_prompt = f"""<knowledge_base_search_result>
I searched your knowledge base but could not find any documents relevant to this query. This could mean:
- The document hasn't finished processing yet (try again in a moment)
- The document content doesn't closely match your question's wording
- No documents have been uploaded yet
</knowledge_base_search_result>

User's question: {chat_request.message}

Instructions:
- Be honest that you couldn't find relevant content in the knowledge base
- If the user is asking about a specific document they uploaded, let them know you couldn't locate it and suggest they verify the upload or try rephrasing
- You can still provide general assistance, but clearly distinguish between knowledge base content (which you don't have) and general knowledge"""

            logger.info("Calling Claude API (streaming)")

            # Build conversation history for Claude
            conversation_messages = []

            if chat_request.conversation_id:
                # Fetch conversation history
                history_result = (
                    supabase.table("messages")
                    .select("role,content,metadata")
                    .eq("conversation_id", chat_request.conversation_id)
                    .order("created_at", desc=False)
                    .execute()
                )

                if history_result.data:
                    for msg in history_result.data:
                        if msg["role"] in ["user", "assistant"] and msg.get("content"):
                            # Skip empty placeholder messages from image flows
                            metadata = msg.get("metadata") or {}
                            if metadata.get("awaiting_image_confirmation") and not msg["content"]:
                                continue
                            conversation_messages.append({"role": msg["role"], "content": msg["content"]})

                    logger.info(f"Loaded {len(conversation_messages)} messages from conversation history")

            # Add the current user message (with RAG context if available)
            conversation_messages.append({"role": "user", "content": user_prompt})

            # Call Claude API with streaming and prompt caching
            # Cached tokens are 90% cheaper - significant savings for repeated chats
            # Prepend date context so agent knows current date
            full_system_prompt = _get_date_context() + system_prompt
            full_response = ""
            input_tokens = 0
            output_tokens = 0

            with anthropic_client.messages.stream(
                model="claude-sonnet-4-5-20250929",
                max_tokens=2048,  # Reduced from 4096 to encourage more concise responses
                temperature=0.3,  # Lower temperature for more focused, concise responses
                system=[
                    {
                        "type": "text",
                        "text": full_system_prompt,
                        "cache_control": {"type": "ephemeral"},  # Cache for 5 minutes
                    }
                ],
                messages=conversation_messages,
            ) as stream:
                for text in stream.text_stream:
                    full_response += text
                    # Send each chunk to the client
                    yield f"data: {json.dumps({'type': 'token', 'content': text})}\n\n"

                # Get final message with token usage
                final_message = stream.get_final_message()
                input_tokens = final_message.usage.input_tokens
                output_tokens = final_message.usage.output_tokens
                cache_read_tokens = getattr(final_message.usage, "cache_read_input_tokens", 0) or 0
                cache_creation_tokens = getattr(final_message.usage, "cache_creation_input_tokens", 0) or 0

            logger.info(
                "Streaming response complete",
                extra={
                    "output_tokens": output_tokens,
                    "input_tokens": input_tokens,
                    "cache_read_tokens": cache_read_tokens,
                    "cache_creation_tokens": cache_creation_tokens,
                },
            )

            # Append web research citations if we used web research
            if web_research_citations:
                from services.web_researcher import format_citations_for_output

                citation_section = format_citations_for_output(web_research_citations)
                if citation_section:
                    # Stream the citations to the client
                    for char in citation_section:
                        yield f"data: {json.dumps({'type': 'token', 'content': char})}\n\n"
                    full_response += citation_section
                    logger.info(f"Appended {len(web_research_citations)} web citations to response")

            # Save messages to database if conversation_id provided
            image_suggestion_data = None  # Will hold suggestion to send as SSE event

            if chat_request.conversation_id:
                # Batch insert both messages in a single DB call
                def save_messages():
                    nonlocal image_suggestion_data

                    # Check if we should suggest an image
                    conversation_service = get_conversation_service()

                    # Get recent messages for context
                    recent_messages_result = (
                        supabase.table("messages")
                        .select("*")
                        .eq("conversation_id", chat_request.conversation_id)
                        .order("created_at", desc=True)
                        .limit(5)
                        .execute()
                    )

                    recent_messages = recent_messages_result.data if recent_messages_result.data else []

                    # Check if we should suggest an image
                    suggestion = conversation_service.should_suggest_image(
                        user_message=chat_request.message,
                        assistant_response=full_response,
                        recent_messages=recent_messages,
                    )

                    # Prepare assistant message metadata
                    assistant_metadata = {
                        "agent_name": selected_agent,
                        "agent_display_name": agent_display_name,
                    }

                    # Add web research metadata if used
                    if web_research_citations:
                        assistant_metadata["web_research"] = {
                            "used": True,
                            "source_count": len(web_research_citations),
                            "sources": [
                                {
                                    "url": c.get("url"),
                                    "title": c.get("title"),
                                    "tier": c.get("credibility_tier"),
                                }
                                for c in web_research_citations[:5]  # Store top 5 for reference
                            ],
                        }

                    if suggestion.get("suggest"):
                        assistant_metadata["image_suggestion"] = {
                            "suggested_prompt": suggestion["suggested_prompt"],
                            "reason": suggestion["reason"],
                            "image_type": suggestion.get("image_type"),
                            "subject": suggestion.get("subject"),
                        }
                        # Store for SSE event
                        image_suggestion_data = assistant_metadata["image_suggestion"]
                        logger.info(
                            f"Image suggestion added: {suggestion.get('image_type', 'general')} - {suggestion['suggested_prompt']}"
                        )

                    messages_to_insert = [
                        {
                            "conversation_id": chat_request.conversation_id,
                            "role": "user",
                            "content": chat_request.message,
                        },
                        {
                            "conversation_id": chat_request.conversation_id,
                            "role": "assistant",
                            "content": full_response,
                            "metadata": assistant_metadata if assistant_metadata else None,
                        },
                    ]
                    result = supabase.table("messages").insert(messages_to_insert).execute()

                    # Store the assistant message ID for the suggestion event
                    if image_suggestion_data and result.data and len(result.data) > 1:
                        image_suggestion_data["message_id"] = result.data[1]["id"]

                    # Link uploaded documents to the user's message
                    if chat_request.document_ids and len(chat_request.document_ids) > 0:
                        # Get the user message ID (first inserted message)
                        user_message_id = result.data[0]["id"]

                        # Create message-document links
                        message_docs_to_insert = [
                            {"message_id": user_message_id, "document_id": doc_id}
                            for doc_id in chat_request.document_ids
                        ]

                        supabase.table("message_documents").insert(message_docs_to_insert).execute()
                        logger.info(f"Linked {len(chat_request.document_ids)} documents to message")

                    return result

                # Run DB insert in thread pool to avoid blocking
                await asyncio.to_thread(save_messages)
                logger.info("Messages saved to conversation")

                # Process for useable output detection (Bradbury Impact Loop)
                # Run in thread pool to avoid blocking the stream
                try:
                    await asyncio.to_thread(process_conversation_for_useable_output, chat_request.conversation_id)
                except Exception as detection_error:
                    logger.warning(f"Useable output detection failed: {detection_error}")

            # Send source documents if available
            if source_documents:
                yield f"data: {json.dumps({'type': 'sources', 'sources': source_documents})}\n\n"

            # Send image suggestion event if we have one (BEFORE done event)
            if image_suggestion_data:
                yield f"data: {json.dumps({'type': 'image_suggestion', 'suggestion': image_suggestion_data})}\n\n"
                logger.info(
                    f"Sent image suggestion SSE event: {image_suggestion_data.get('suggested_prompt', '')[:50]}..."
                )

            # Send completion message with token stats
            completion_data = {
                "type": "done",
                "tokens": {
                    "input": input_tokens,
                    "output": output_tokens,
                    "total": input_tokens + output_tokens,
                    "cache_read": cache_read_tokens,
                    "cache_creation": cache_creation_tokens,
                },
                "context_used": len(context_chunks),
            }
            yield f"data: {json.dumps(completion_data)}\n\n"

        except Exception as e:
            logger.exception(
                "Error processing streaming chat request",
                exc_info=True,
                extra={"user_id": current_user["id"]},
            )
            # Send error to client
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


from typing import Optional

from pydantic import BaseModel, Field


class DigDeeperRequest(BaseModel):
    """Request to elaborate on a previous assistant response."""

    conversation_id: str
    message_id: str  # The assistant message ID to dig deeper on
    original_content: str  # The content of the original message
    custom_prompt: Optional[str] = Field(None, max_length=500)  # Optional specific request


class DigDeeperSectionRequest(BaseModel):
    """Request to expand a specific section of an assistant response (inline dig-deeper)."""

    conversation_id: str
    message_id: str  # The assistant message ID containing the section
    original_content: str  # The full content of the original message
    section_id: str  # The section identifier from dig-deeper:section_id link
    section_context: Optional[str] = None  # Optional surrounding context for the section


# ============================================================================
# Dig Deeper Endpoint
# ============================================================================


@router.post("/dig-deeper")
@limiter.limit("15/minute")
async def dig_deeper(request: Request, dig_request: DigDeeperRequest, current_user: dict = Depends(get_current_user)):
    """Dig deeper into a previous assistant response.

    Takes an existing assistant message and asks for more detail, examples,
    or elaboration. Streams the extended response.

    Use cases:
    - Email drafts that need more detail
    - Meeting summaries that need expansion
    - Reports that need deeper analysis
    - Any assistant output that could benefit from elaboration
    """
    logger.info(
        "Dig deeper request received",
        extra={
            "user_id": current_user["id"],
            "conversation_id": dig_request.conversation_id,
            "message_id": dig_request.message_id,
        },
    )

    async def generate_stream():
        """Generator function for SSE stream."""
        try:
            # Build the dig deeper prompt
            if dig_request.custom_prompt:
                dig_deeper_prompt = f"""The user wants you to elaborate on your previous response with this specific request:

"{dig_request.custom_prompt}"

Your previous response was:
---
{dig_request.original_content}
---

Please provide more detail as requested. Maintain the same format and tone as your original response."""
            else:
                dig_deeper_prompt = f"""The user clicked "Dig Deeper" on your previous response, requesting more detail and depth.

Your previous response was:
---
{dig_request.original_content}
---

Please elaborate with:
- **More specific examples** or case studies if applicable
- **Deeper analysis** of the key points you mentioned
- **Practical next steps** or implementation considerations
- **Potential challenges** or considerations you didn't cover

Maintain the same format and style as your original response, but provide more comprehensive detail."""

            # Load system instructions
            try:
                system_prompt = get_system_instructions_for_user(user_id=current_user["id"], user_data=current_user)
            except FileNotFoundError as e:
                logger.warning(f"Could not load system instructions: {e}")
                user_name = current_user.get("name", "User")
                system_prompt = (
                    f"You are Thesis, a helpful AI assistant for {user_name}. "
                    "Provide clear, accurate, and professional assistance."
                )

            # Get conversation history for context
            conversation_messages = []
            if dig_request.conversation_id:
                history_result = (
                    supabase.table("messages")
                    .select("role,content")
                    .eq("conversation_id", dig_request.conversation_id)
                    .order("created_at", desc=False)
                    .execute()
                )

                if history_result.data:
                    for msg in history_result.data:
                        if msg["role"] in ["user", "assistant"] and msg.get("content"):
                            conversation_messages.append({"role": msg["role"], "content": msg["content"]})

            # Add the dig deeper request as a user message
            conversation_messages.append({"role": "user", "content": dig_deeper_prompt})

            # Stream the response
            # Prepend date context so agent knows current date
            full_system_prompt = _get_date_context() + system_prompt
            full_response = ""
            input_tokens = 0
            output_tokens = 0

            with anthropic_client.messages.stream(
                model="claude-sonnet-4-5-20250929",
                max_tokens=4096,  # Higher limit for dig deeper responses
                temperature=0.3,
                system=[
                    {
                        "type": "text",
                        "text": full_system_prompt,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=conversation_messages,
            ) as stream:
                for text in stream.text_stream:
                    full_response += text
                    yield f"data: {json.dumps({'type': 'token', 'content': text})}\n\n"

                final_message = stream.get_final_message()
                input_tokens = final_message.usage.input_tokens
                output_tokens = final_message.usage.output_tokens

            # Save the dig deeper exchange to the conversation
            if dig_request.conversation_id:
                # Save as a special "dig deeper" exchange
                messages_to_insert = [
                    {
                        "conversation_id": dig_request.conversation_id,
                        "role": "user",
                        "content": dig_request.custom_prompt or "[Dig Deeper]",
                        "metadata": {
                            "dig_deeper": True,
                            "original_message_id": dig_request.message_id,
                        },
                    },
                    {
                        "conversation_id": dig_request.conversation_id,
                        "role": "assistant",
                        "content": full_response,
                        "metadata": {
                            "dig_deeper_response": True,
                            "original_message_id": dig_request.message_id,
                        },
                    },
                ]
                await asyncio.to_thread(lambda: supabase.table("messages").insert(messages_to_insert).execute())
                logger.info("Dig deeper messages saved to conversation")

            # Send completion
            yield f"data: {json.dumps({'type': 'done', 'tokens': {'input': input_tokens, 'output': output_tokens, 'total': input_tokens + output_tokens}})}\n\n"

        except Exception as e:
            logger.exception("Error processing dig deeper request", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ============================================================================
# Dig Deeper Section Expansion Endpoint (Inline)
# ============================================================================


# Mapping of section IDs to human-readable topics for prompt clarity
SECTION_TOPIC_MAP = {
    # Research/Evidence
    "benchmarks": "industry benchmarks and comparative data",
    "case_studies": "real-world case studies and examples",
    "evidence": "supporting evidence and research",
    "sources": "source citations and references",
    "methodology": "methodology and approach",
    "data": "underlying data and statistics",
    # Implementation
    "implementation": "implementation steps and approach",
    "steps": "detailed step-by-step process",
    "timeline": "timeline and milestones",
    "requirements": "requirements and prerequisites",
    "prerequisites": "prerequisites and preparation",
    # Analysis
    "analysis": "detailed analysis",
    "breakdown": "detailed breakdown",
    "comparison": "comparison of options",
    "tradeoffs": "tradeoffs and considerations",
    "alternatives": "alternative approaches",
    # Risks
    "risks": "risks and potential issues",
    "caveats": "caveats and limitations",
    "limitations": "limitations and constraints",
    "considerations": "important considerations",
    "challenges": "challenges and obstacles",
    # Financial
    "roi_analysis": "ROI analysis and financial metrics",
    "costs": "cost breakdown and estimates",
    "savings": "potential savings and benefits",
    "investment": "investment requirements",
    "payback": "payback period analysis",
    # Technical
    "technical_details": "technical details and specifications",
    "architecture": "architecture and design",
    "integration": "integration approach",
    "security": "security considerations",
    # People/Change
    "change_management": "change management approach",
    "adoption": "adoption strategy",
    "training": "training requirements",
    "stakeholders": "stakeholder considerations",
    # Actions
    "next_steps": "next steps and actions",
    "recommendations": "specific recommendations",
    "success_factors": "success factors",
    "mitigation": "mitigation strategies",
}


@router.post("/dig-deeper-section")
@limiter.limit("20/minute")
async def dig_deeper_section(
    request: Request,
    section_request: DigDeeperSectionRequest,
    current_user: dict = Depends(get_current_user),
):
    """Expand a specific section of an assistant response (inline dig-deeper).

    When users click on inline [link](dig-deeper:section_id) links, this endpoint
    provides focused elaboration on just that topic without repeating the full response.

    Returns the expanded content directly (not streamed) for inline insertion.
    """
    logger.info(
        "Dig deeper section request received",
        extra={
            "user_id": current_user["id"],
            "conversation_id": section_request.conversation_id,
            "message_id": section_request.message_id,
            "section_id": section_request.section_id,
        },
    )

    try:
        # Get human-readable topic from section ID
        section_topic = SECTION_TOPIC_MAP.get(section_request.section_id, section_request.section_id.replace("_", " "))

        # Build the section expansion prompt - CONCISE expansion
        expansion_prompt = f"""The user clicked "dig deeper" on: **{section_topic}**

Original response (for context only - do NOT repeat):
---
{section_request.original_content}
---

EXPAND ONLY the "{section_topic}" topic. STRICT RULES:

1. MAXIMUM 100-150 words - this is a focused mini-expansion, NOT a full response
2. Start IMMEDIATELY with the first useful detail - no intro sentences
3. Use 3-5 bullet points MAX
4. Include ONE specific example or metric if relevant
5. NO paragraphs - bullets only
6. Do NOT repeat anything from the original response
7. Do NOT add dig-deeper links in expansions (keep them simple)

FORMAT:
- Bullet 1: specific detail
- Bullet 2: specific detail
- Bullet 3: example or metric

That's it. Keep it SHORT."""

        # Load system instructions
        try:
            system_prompt = get_system_instructions_for_user(user_id=current_user["id"], user_data=current_user)
        except FileNotFoundError:
            user_name = current_user.get("name", "User")
            system_prompt = (
                f"You are Thesis, a helpful AI assistant for {user_name}. "
                "Provide clear, accurate, and professional assistance."
            )

        # Get conversation history for context (limited to recent messages)
        conversation_messages = []
        if section_request.conversation_id:
            history_result = (
                supabase.table("messages")
                .select("role,content")
                .eq("conversation_id", section_request.conversation_id)
                .order("created_at", desc=False)
                .limit(10)
                .execute()
            )

            if history_result.data:
                for msg in history_result.data:
                    if msg["role"] in ["user", "assistant"] and msg.get("content"):
                        conversation_messages.append({"role": msg["role"], "content": msg["content"]})

        # Add the expansion request
        conversation_messages.append({"role": "user", "content": expansion_prompt})

        # Generate the expansion (non-streaming for inline insertion)
        # Prepend date context so agent knows current date
        full_system_prompt = _get_date_context() + system_prompt
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=400,  # Short - ~100-150 words max for focused expansion
            temperature=0.3,
            system=[{"type": "text", "text": full_system_prompt, "cache_control": {"type": "ephemeral"}}],
            messages=conversation_messages,
        )

        expanded_content = response.content[0].text

        # Save the expansion to the conversation (as metadata, not as separate messages)
        # This avoids cluttering the chat but preserves the data
        if section_request.conversation_id:
            try:
                # Update the original message's metadata to include expansions
                await asyncio.to_thread(
                    lambda: supabase.rpc(
                        "append_message_expansion",
                        {
                            "p_message_id": section_request.message_id,
                            "p_section_id": section_request.section_id,
                            "p_expanded_content": expanded_content,
                        },
                    ).execute()
                )
            except Exception as save_err:
                # Log but don't fail - expansion still works even if save fails
                logger.warning(f"Could not save expansion to message metadata: {save_err}")

        return {
            "section_id": section_request.section_id,
            "expanded_content": expanded_content,
            "tokens": {
                "input": response.usage.input_tokens,
                "output": response.usage.output_tokens,
            },
        }

    except Exception:
        logger.exception("Error processing dig deeper section request", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from None
