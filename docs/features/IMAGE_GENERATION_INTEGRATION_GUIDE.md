# Image Generation Integration Guide

## Overview

This guide explains how to integrate the new AI-powered image generation feature into Thesis's chat interface. The feature supports:

- **Proactive AI suggestions** - Thesis suggests images when helpful
- **User-initiated generation** - Users can explicitly request images
- **Aspect ratio selection** - 1:1, 16:9, 9:16, 4:3
- **Model selection** - Fast (Gemini 2.5 Flash) or Quality (Gemini 3 Pro)
- **Image persistence** - Images stored in Supabase Storage and conversation history
- **Download & regenerate** - Users can download or regenerate with different settings

---

## Setup Instructions

### 1. Database Migration

Run the migration to create the `conversation_images` table:

```bash
# Connect to your Supabase database and run:
psql -h your-db-host -U postgres -d postgres -f database/migrations/add_conversation_images.sql
```

Or use the Supabase Dashboard SQL Editor to execute the contents of `database/migrations/add_conversation_images.sql`.

### 2. Supabase Storage Bucket

Create the storage bucket for images:

1. Go to Supabase Dashboard → Storage
2. Create a new bucket named `conversation-images`
3. Set it to **Public** (images are publicly accessible via URL)
4. Or run this SQL in the SQL Editor:

```sql
INSERT INTO storage.buckets (id, name, public)
VALUES ('conversation-images', 'conversation-images', true)
ON CONFLICT (id) DO NOTHING;
```

### 3. Environment Variables

Ensure these environment variables are set:

**Backend (.env):**
```bash
GOOGLE_GENERATIVE_AI_API_KEY=your_gemini_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

**Frontend (.env.local):**
```bash
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000  # or your backend URL
```

---

## Integration into ChatInterface

### Step 1: Import Components and API

Add these imports to your `ChatInterface.tsx` or main chat component:

```typescript
import ImageSuggestionPrompt from '@/components/ImageSuggestionPrompt'
import InlineChatImage from '@/components/InlineChatImage'
import {
  generateConversationImage,
  getConversationImages,
  deleteConversationImage,
  type ConversationImage
} from '@/lib/api'
```

### Step 2: Add State Management

```typescript
const [conversationImages, setConversationImages] = useState<ConversationImage[]>([])
const [pendingImageSuggestion, setPendingImageSuggestion] = useState<{
  messageId: string
  suggestion: {
    suggested_prompt: string
    reason: string
  }
} | null>(null)
const [isGeneratingImage, setIsGeneratingImage] = useState(false)
```

### Step 3: Load Images When Conversation Opens

```typescript
useEffect(() => {
  if (conversationId) {
    loadConversationImages(conversationId)
  }
}, [conversationId])

const loadConversationImages = async (convId: string) => {
  try {
    const response = await getConversationImages(convId)
    setConversationImages(response.images)
  } catch (error) {
    console.error('Failed to load conversation images:', error)
  }
}
```

### Step 4: Handle Image Suggestions from Backend

When the backend chat response includes `image_suggestion` metadata:

```typescript
// In your chat message handler:
const handleChatResponse = (message: Message) => {
  // Check if message has image suggestion
  if (message.metadata?.image_suggestion) {
    setPendingImageSuggestion({
      messageId: message.id,
      suggestion: message.metadata.image_suggestion
    })
  }
}
```

### Step 5: Handle Image Generation

```typescript
const handleGenerateImage = async (
  prompt: string,
  aspectRatio: string,
  model: string
) => {
  if (!conversationId) return

  setIsGeneratingImage(true)
  setPendingImageSuggestion(null)

  try {
    const response = await generateConversationImage({
      conversation_id: conversationId,
      message_id: pendingImageSuggestion?.messageId,
      prompt,
      aspect_ratio: aspectRatio,
      model
    })

    // Add to conversation images
    setConversationImages(prev => [response, ...prev])

    // Show success toast
    toast.success('Image generated successfully!')
  } catch (error) {
    console.error('Failed to generate image:', error)
    toast.error('Failed to generate image. Please try again.')
  } finally {
    setIsGeneratingImage(false)
  }
}

const handleDeclineSuggestion = () => {
  setPendingImageSuggestion(null)
}

const handleRegenerateImage = (prompt: string) => {
  // Re-trigger the suggestion flow with the same prompt
  setPendingImageSuggestion({
    messageId: '',
    suggestion: {
      suggested_prompt: prompt,
      reason: 'Regenerate with different settings'
    }
  })
}

const handleDeleteImage = async (imageId: string) => {
  try {
    await deleteConversationImage(imageId)
    setConversationImages(prev => prev.filter(img => img.id !== imageId))
    toast.success('Image deleted')
  } catch (error) {
    console.error('Failed to delete image:', error)
    toast.error('Failed to delete image')
  }
}
```

### Step 6: Render Components in Chat

```tsx
return (
  <div className="chat-container">
    {/* Messages */}
    {messages.map((message) => (
      <div key={message.id}>
        <MessageBubble message={message} />

        {/* Show image suggestion if this message triggered it */}
        {pendingImageSuggestion?.messageId === message.id && (
          <ImageSuggestionPrompt
            suggestion={pendingImageSuggestion.suggestion}
            onAccept={handleGenerateImage}
            onDecline={handleDeclineSuggestion}
            isGenerating={isGeneratingImage}
          />
        )}

        {/* Show images associated with this message */}
        {conversationImages
          .filter(img => img.message_id === message.id)
          .map(image => (
            <InlineChatImage
              key={image.id}
              image={image}
              onRegenerate={handleRegenerateImage}
              onDelete={handleDeleteImage}
            />
          ))}
      </div>
    ))}

    {/* Show orphaned images (not tied to specific message) at bottom */}
    {conversationImages
      .filter(img => !img.message_id)
      .map(image => (
        <InlineChatImage
          key={image.id}
          image={image}
          onRegenerate={handleRegenerateImage}
          onDelete={handleDeleteImage}
        />
      ))}
  </div>
)
```

---

## Backend Integration (Chat Endpoint)

### Modify Chat Response Handler

Update your chat endpoint to include image suggestion detection:

```python
from services.conversation_service import get_conversation_service

@router.post("/chat")
async def chat_endpoint(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    # ... existing chat logic ...

    # Generate assistant response
    assistant_response = await generate_response(user_message, conversation_history)

    # Check if we should suggest an image
    conversation_service = get_conversation_service()
    suggestion = conversation_service.should_suggest_image(
        user_message=user_message,
        assistant_response=assistant_response,
        recent_messages=conversation_history[-5:]  # Last 5 messages
    )

    # Add suggestion to message metadata
    message_metadata = {}
    if suggestion.get('suggest'):
        message_metadata['image_suggestion'] = {
            'suggested_prompt': suggestion['suggested_prompt'],
            'reason': suggestion['reason']
        }

    # Save message with metadata
    message = save_message(
        conversation_id=conversation_id,
        role='assistant',
        content=assistant_response,
        metadata=message_metadata  # Include suggestion here
    )

    return {
        'message': message,
        'conversation_id': conversation_id
    }
```

### Handle Explicit Image Requests

```python
# Before generating response, check if user is requesting an image
conversation_service = get_conversation_service()
image_request = conversation_service.extract_image_request(user_message)

if image_request.get('is_request'):
    # User explicitly requested an image
    # Return a response that triggers the frontend to show aspect ratio selector
    return {
        'message': {
            'role': 'assistant',
            'content': f"I'll generate an image showing: {image_request['prompt']}",
            'metadata': {
                'image_request': {
                    'prompt': image_request['prompt'],
                    'aspect_ratio': image_request.get('aspect_ratio'),
                    'model': image_request.get('model')
                }
            }
        }
    }
```

---

## First Message / Onboarding

To inform users about the image generation capability, add this to the system instructions or first message:

### Option 1: System Instructions

Add to `clients.system_instructions`:

```
I can generate images to help visualize concepts and explanations. When it would be helpful, I'll suggest creating a diagram or illustration. You can also ask me directly to "generate an image of [description]" and specify your preferred aspect ratio (1:1, 16:9, 9:16, or 4:3) and quality level (fast or high quality).
```

### Option 2: Welcome Message

Add a welcome message when a new conversation starts:

```typescript
const WELCOME_MESSAGE = {
  role: 'assistant',
  content: `Hi! I'm Thesis, your AI assistant. I can help with questions, research, and more.

**New feature:** I can now generate images! Just describe what you'd like to visualize, or I'll suggest images when they'd be helpful. Try asking me to "generate an image of [something]" to get started.`,
  metadata: {}
}
```

---

## Testing Checklist

After integration, test these scenarios:

### Basic Flow
- [ ] User asks about a visual topic → Suggestion appears
- [ ] User clicks "Yes, generate it" → Aspect ratio selector shows
- [ ] User selects ratio and model → Image generates and displays
- [ ] User clicks download → Image downloads successfully
- [ ] Refresh page → Images persist in conversation

### Edge Cases
- [ ] Max 1 suggestion per 5 messages (throttling works)
- [ ] 20 image limit per conversation enforced
- [ ] User declines suggestion → Suggestion disappears
- [ ] Regenerate with different ratio/model works
- [ ] Delete image removes from storage and DB
- [ ] Explicit request: "generate image of sunset in 16:9" works
- [ ] Images load when switching between conversations

### Error Handling
- [ ] Network error during generation shows error message
- [ ] Invalid image URL shows error state
- [ ] Rate limit reached shows appropriate message

---

## Configuration Options

### Adjust Suggestion Frequency

In `conversation_service.py`:

```python
# Change from 5 to your preferred value
if recent_suggestion_count > 0:  # Currently: max 1 per 5 messages
    return {"suggest": False}
```

### Adjust Image Limit

In `images.py` API route:

```python
# Change from 20 to your preferred limit
if current_image_count >= 20:
    raise HTTPException(...)
```

### Add More Aspect Ratios

In `image_generation.py`:

```python
ASPECT_RATIOS = {
    "1:1": {"width": 1024, "height": 1024, "description": "Square"},
    "21:9": {"width": 1920, "height": 823, "description": "Ultrawide"},  # Add new
    # ... etc
}
```

---

## Troubleshooting

### Images not generating

1. Check `GOOGLE_GENERATIVE_AI_API_KEY` is set
2. Check backend logs for API errors
3. Verify Gemini API quota hasn't been exceeded

### Images not uploading to Storage

1. Verify `conversation-images` bucket exists
2. Check `SUPABASE_SERVICE_ROLE_KEY` is set
3. Check bucket permissions (should be public)

### Images not showing in conversation

1. Check browser console for fetch errors
2. Verify RLS policies allow user to view images
3. Check conversation_id matches between image and conversation

### Suggestions not appearing

1. Check message metadata includes `image_suggestion`
2. Verify throttling isn't blocking (check recent messages)
3. Check backend logs for `should_suggest_image` output

---

## Next Steps

After basic integration:

1. **Analytics** - Track image generation usage per user/conversation
2. **Quota Management** - Implement user-specific image limits
3. **Storage Cleanup** - Add cron job to delete old images (90+ days)
4. **Advanced Features**:
   - Image editing/variations
   - Multi-image generation (batch)
   - Image-to-image transformation
   - Custom styles/themes

---

## Support

For issues or questions:
- Check backend logs: `backend/logs/`
- Check browser console for frontend errors
- Review plan document: `.claude/plans/structured-scribbling-lobster.md`
- GitHub Issues: https://github.com/your-org/thesis/issues
