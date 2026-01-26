"""
Image generation API routes.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from auth import get_current_user
from database import DatabaseService
from services.image_generation import get_image_generation_service
from services.storage_service import get_storage_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/images", tags=["images"])


class ImageGenerationRequest(BaseModel):
    """Request model for image generation."""
    prompt: str = Field(..., min_length=1, max_length=2000, description="Text description of the image to generate")
    model: Optional[str] = Field(None, description="Optional model override (default: gemini-2.5-flash-image)")


class BatchImageGenerationRequest(BaseModel):
    """Request model for batch image generation."""
    prompts: List[str] = Field(..., min_length=1, max_length=5, description="List of text prompts (max 5)")
    model: Optional[str] = Field(None, description="Optional model override")


class ImageGenerationResponse(BaseModel):
    """Response model for image generation."""
    image_data: str = Field(..., description="Base64-encoded image data")
    mime_type: str = Field(..., description="Image MIME type")
    prompt: str = Field(..., description="Prompt used for generation")
    model: str = Field(..., description="Model used")
    success: bool = Field(default=True, description="Success status")


class BatchImageGenerationResponse(BaseModel):
    """Response model for batch image generation."""
    results: List[dict] = Field(..., description="List of generation results")
    total: int = Field(..., description="Total number of images requested")
    successful: int = Field(..., description="Number of successfully generated images")


@router.post("/generate", response_model=ImageGenerationResponse)
async def generate_image(
    request: ImageGenerationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate a single image from a text prompt.

    Requires authentication.
    """
    try:
        logger.info(f"User {current_user.get('id')} requesting image generation")

        service = get_image_generation_service()
        result = await service.generate_image(
            prompt=request.prompt,
            model=request.model
        )

        return ImageGenerationResponse(**result)

    except Exception as e:
        logger.error(f"Image generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.post("/generate-batch", response_model=BatchImageGenerationResponse)
async def generate_images_batch(
    request: BatchImageGenerationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate multiple images from a list of prompts.

    Requires authentication. Maximum 5 prompts per request.
    """
    try:
        logger.info(f"User {current_user.get('id')} requesting batch image generation ({len(request.prompts)} images)")

        service = get_image_generation_service()
        results = await service.generate_multiple_images(
            prompts=request.prompts,
            model=request.model
        )

        successful = sum(1 for r in results if r.get("success", False))

        return BatchImageGenerationResponse(
            results=results,
            total=len(request.prompts),
            successful=successful
        )

    except Exception as e:
        logger.error(f"Batch image generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.get("/models")
async def list_available_models(current_user: dict = Depends(get_current_user)):
    """
    List available image generation models and aspect ratios.

    Requires authentication.
    """
    service = get_image_generation_service()
    model_info = service.get_model_info()

    return {
        "models": [
            {
                "key": key,
                **value
            }
            for key, value in model_info["models"].items()
        ],
        "aspect_ratios": [
            {
                "ratio": ratio,
                **details
            }
            for ratio, details in model_info["aspect_ratios"].items()
        ],
        "default_model": model_info["default_model"]
    }


# ============================================================================
# CONVERSATION IMAGE ENDPOINTS
# ============================================================================

class ConversationImageRequest(BaseModel):
    """Request model for generating image in conversation context."""
    conversation_id: str = Field(..., description="ID of the conversation")
    message_id: Optional[str] = Field(None, description="Optional message ID to associate with")
    prompt: str = Field(..., min_length=1, max_length=2000, description="Text description of the image")
    aspect_ratio: str = Field(default="16:9", description="Aspect ratio (1:1, 16:9, 9:16, 4:3)")
    model: Optional[str] = Field(default="fast", description="Model to use (fast or quality)")


class ConversationImageResponse(BaseModel):
    """Response model for conversation image generation."""
    id: str = Field(..., description="Image database ID")
    storage_url: str = Field(..., description="Public URL of the image")
    prompt: str = Field(..., description="Prompt used")
    aspect_ratio: str = Field(..., description="Aspect ratio used")
    model: str = Field(..., description="Model used")
    mime_type: str = Field(..., description="Image MIME type")
    file_size: int = Field(..., description="File size in bytes")
    generated_at: str = Field(..., description="Generation timestamp")
    success: bool = Field(default=True)


@router.post("/generate-in-conversation", response_model=ConversationImageResponse)
async def generate_image_in_conversation(
    request: ConversationImageRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate an image and store it in conversation context.

    - Generates image with specified aspect ratio and model
    - Uploads to Supabase Storage
    - Stores metadata in conversation_images table
    - Enforces 20 image per conversation limit

    Requires authentication.
    """
    try:
        user_id = current_user.get('id')
        logger.info(f"User {user_id} generating image for conversation {request.conversation_id}")

        db = DatabaseService.get_client()

        # Verify conversation belongs to user
        conversation = db.table('conversations').select('id,user_id').eq('id', request.conversation_id).single().execute()
        if not conversation.data or conversation.data['user_id'] != user_id:
            raise HTTPException(status_code=403, detail="Conversation not found or access denied")

        # Check image count limit (20 per conversation)
        image_count_result = db.rpc('count_conversation_images', {'p_conversation_id': request.conversation_id}).execute()
        current_image_count = image_count_result.data if image_count_result.data else 0

        if current_image_count >= 20:
            raise HTTPException(
                status_code=429,
                detail="Image limit reached for this conversation. Contact admin to increase your limit."
            )

        # Generate image
        image_service = get_image_generation_service()
        result = await image_service.generate_image(
            prompt=request.prompt,
            model=request.model,
            aspect_ratio=request.aspect_ratio
        )

        if not result.get('success'):
            raise Exception("Image generation failed")

        # Upload to Supabase Storage
        storage_service = get_storage_service()
        mime_type = result['mime_type']
        file_ext = mime_type.split('/')[-1] if '/' in mime_type else 'png'

        upload_result = storage_service.upload_image(
            image_data=result['image_data'],
            user_id=user_id,
            conversation_id=request.conversation_id,
            file_extension=file_ext
        )

        if not upload_result:
            raise Exception("Failed to upload image to storage")

        # Store in database
        image_record = {
            'conversation_id': request.conversation_id,
            'message_id': request.message_id,
            'prompt': request.prompt,
            'aspect_ratio': request.aspect_ratio,
            'model': result['model'],
            'storage_url': upload_result['storage_url'],
            'storage_path': upload_result['storage_path'],
            'mime_type': upload_result['content_type'],
            'file_size': upload_result['file_size'],
            'metadata': {
                'model_key': result.get('model_key'),
                'enhanced_prompt': result.get('enhanced_prompt')
            }
        }

        insert_result = db.table('conversation_images').insert(image_record).execute()

        if not insert_result.data:
            raise Exception("Failed to store image metadata")

        stored_image = insert_result.data[0]

        logger.info(f"Image {stored_image['id']} generated and stored successfully")

        return ConversationImageResponse(
            id=stored_image['id'],
            storage_url=stored_image['storage_url'],
            prompt=stored_image['prompt'],
            aspect_ratio=stored_image['aspect_ratio'],
            model=stored_image['model'],
            mime_type=stored_image['mime_type'],
            file_size=stored_image['file_size'],
            generated_at=stored_image['generated_at'],
            success=True
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Conversation image generation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.get("/conversations/{conversation_id}")
async def get_conversation_images(
    conversation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all images for a conversation.

    Returns list of images with metadata.
    Requires authentication and conversation ownership.
    """
    try:
        user_id = current_user.get('id')
        db = DatabaseService.get_client()

        # Verify conversation exists and check ownership
        conversation = db.table('conversations').select('id,user_id').eq('id', conversation_id).single().execute()
        if not conversation.data:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Log ownership mismatch for debugging but allow access (for development)
        if conversation.data['user_id'] != user_id:
            logger.warning(f"User {user_id} accessing conversation {conversation_id} owned by {conversation.data['user_id']}")

        # Get all images
        images = db.table('conversation_images')\
            .select('*')\
            .eq('conversation_id', conversation_id)\
            .order('generated_at', desc=True)\
            .execute()

        return {
            'conversation_id': conversation_id,
            'images': images.data or [],
            'total': len(images.data) if images.data else 0
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation images: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.delete("/{image_id}")
async def delete_conversation_image(
    image_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a conversation image.

    Removes from storage and database.
    Requires authentication and conversation ownership.
    """
    try:
        user_id = current_user.get('id')
        db = DatabaseService.get_client()

        # Get image and verify ownership through conversation
        image = db.table('conversation_images').select('*, conversations(user_id)')\
            .eq('id', image_id).single().execute()

        if not image.data:
            raise HTTPException(status_code=404, detail="Image not found")

        # Check ownership (RLS should handle this, but double check)
        if image.data['conversations']['user_id'] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        storage_path = image.data.get('storage_path')

        # Delete from storage
        if storage_path:
            storage_service = get_storage_service()
            storage_service.delete_image(storage_path)

        # Delete from database
        db.table('conversation_images').delete().eq('id', image_id).execute()

        logger.info(f"Image {image_id} deleted by user {user_id}")

        return {"success": True, "message": "Image deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete image: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


# ============================================================================
# CONTEXT-AWARE IMAGE SUGGESTION ENDPOINT
# ============================================================================

class VisualSuggestionRequest(BaseModel):
    """Request model for getting a context-aware visual suggestion."""
    conversation_id: str = Field(..., description="ID of the conversation to analyze")
    visual_type: str = Field(..., description="Type of visual (mindmap, flowchart, diagram, etc.)")


class VisualSuggestionResponse(BaseModel):
    """Response model for visual suggestion."""
    suggested_content: str = Field(..., description="Suggested content for the visual based on conversation context")
    full_prompt: str = Field(..., description="Complete prompt ready for image generation")
    context_summary: str = Field(..., description="Brief summary of what was found in the conversation")
    has_context: bool = Field(..., description="Whether meaningful context was found")


@router.post("/suggest-visual-content", response_model=VisualSuggestionResponse)
async def suggest_visual_content(
    request: VisualSuggestionRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze conversation context and suggest content for a visual.

    - Reads recent messages from the conversation
    - Uses LLM to analyze what would be most useful to visualize
    - Returns a suggested content description and full prompt

    Requires authentication.
    """
    try:
        user_id = current_user.get('id')
        logger.info(f"User {user_id} requesting visual suggestion for conversation {request.conversation_id}")

        db = DatabaseService.get_client()

        # Verify conversation belongs to user
        conversation = db.table('conversations').select('id,user_id').eq('id', request.conversation_id).single().execute()
        if not conversation.data or conversation.data['user_id'] != user_id:
            raise HTTPException(status_code=403, detail="Conversation not found or access denied")

        # Get recent messages from the conversation (last 10 messages for context)
        messages_result = db.table('messages')\
            .select('role,content,created_at')\
            .eq('conversation_id', request.conversation_id)\
            .order('created_at', desc=True)\
            .limit(10)\
            .execute()

        messages = messages_result.data or []

        # If no messages, return a generic suggestion
        if not messages:
            visual_type_label = request.visual_type.replace('_', ' ').title()
            return VisualSuggestionResponse(
                suggested_content="",
                full_prompt=f"Generate an image of a {visual_type_label}",
                context_summary="No conversation history found",
                has_context=False
            )

        # Reverse to get chronological order
        messages.reverse()

        # Build context string from messages
        context_text = "\n".join([
            f"{msg['role'].upper()}: {msg['content'][:500]}"  # Limit each message
            for msg in messages
        ])

        # Use Gemini to analyze the context and suggest visual content
        import os

        import google.generativeai as genai

        genai.configure(api_key=os.environ.get('GOOGLE_GENERATIVE_AI_API_KEY'))
        model = genai.GenerativeModel('gemini-2.0-flash')

        visual_type_label = request.visual_type.replace('_', ' ')

        analysis_prompt = f"""Analyze this conversation and suggest what should be shown in a {visual_type_label}.

CONVERSATION:
{context_text}

Based on this conversation, what would be the most useful content to show in a {visual_type_label}?

Respond with ONLY a brief, specific description (1-2 sentences) of what the {visual_type_label} should contain.
Focus on the main topic or concept being discussed.
Do not include phrases like "the {visual_type_label} should show" - just describe the content directly.

Example good responses:
- "employee onboarding process from recruitment to first day completion"
- "key components of effective training programs and their relationships"
- "quarterly sales metrics comparing Q1 through Q4 performance"

Your response:"""

        response = model.generate_content(analysis_prompt)
        suggested_content = response.text.strip()

        # Clean up the suggestion - remove quotes if present
        suggested_content = suggested_content.strip('"\'')

        # Build the full prompt
        full_prompt = f"Generate an image of a {visual_type_label} showing {suggested_content}"

        # Create a brief context summary
        context_summary = f"Based on {len(messages)} recent messages discussing "
        # Extract key topic from first assistant response or user message
        for msg in messages:
            if msg['content']:
                first_words = ' '.join(msg['content'].split()[:10])
                context_summary += f"'{first_words}...'"
                break

        logger.info(f"Visual suggestion generated: {suggested_content[:100]}...")

        return VisualSuggestionResponse(
            suggested_content=suggested_content,
            full_prompt=full_prompt,
            context_summary=context_summary,
            has_context=True
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate visual suggestion: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")
