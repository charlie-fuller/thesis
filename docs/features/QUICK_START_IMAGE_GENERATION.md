# Quick Start: Image Generation Feature

## 5-Minute Setup Guide

### Step 1: Run Database Migration (2 min)

Option A - Supabase Dashboard:
1. Go to your Supabase project dashboard
2. Click "SQL Editor" in left sidebar
3. Create new query
4. Copy/paste contents of `database/migrations/add_conversation_images.sql`
5. Click "Run"
6. Should see "Success. No rows returned"

Option B - Command Line:
```bash
psql postgresql://postgres:[password]@[your-host]/postgres \
  -f database/migrations/add_conversation_images.sql
```

### Step 2: Create Storage Bucket (1 min)

In Supabase Dashboard:
1. Go to "Storage" in left sidebar
2. Click "Create a new bucket"
3. Name: `conversation-images`
4. Check "Public bucket"
5. Click "Create bucket"

Or run this SQL in SQL Editor:
```sql
INSERT INTO storage.buckets (id, name, public)
VALUES ('conversation-images', 'conversation-images', true)
ON CONFLICT (id) DO NOTHING;
```

### Step 3: Verify Environment Variables (1 min)

Check your backend `.env` has:
```bash
GOOGLE_GENERATIVE_AI_API_KEY=AIza...  # Your Gemini API key
SUPABASE_URL=https://...supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJh...     # Service role key (NOT anon key)
```

### Step 4: Test API Endpoint (1 min)

Restart backend:
```bash
cd backend
uvicorn main:app --reload
```

Test in browser or Postman:
```
GET http://localhost:8000/api/images/models
```

Should return models and aspect ratios.

### Step 5: Quick Frontend Test

Create a test page `frontend/app/test-image/page.tsx`:

```tsx
'use client'

import { useState } from 'react'
import AspectRatioSelector from '@/components/AspectRatioSelector'
import InlineChatImage from '@/components/InlineChatImage'
import ImageSuggestionPrompt from '@/components/ImageSuggestionPrompt'
import { generateConversationImage } from '@/lib/api'

export default function TestImagePage() {
  const [image, setImage] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleGenerate = async (aspectRatio: string, model: string) => {
    setLoading(true)
    try {
      const result = await generateConversationImage({
        conversation_id: '00000000-0000-0000-0000-000000000001', // Test conversation
        prompt: 'A beautiful sunset over mountains',
        aspect_ratio: aspectRatio,
        model: model
      })
      setImage(result)
    } catch (error) {
      alert('Error: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Image Generation Test</h1>

      {!image && !loading && (
        <AspectRatioSelector
          onSelect={handleGenerate}
        />
      )}

      {loading && <p>Generating...</p>}

      {image && (
        <InlineChatImage
          image={image}
          onRegenerate={(prompt) => console.log('Regenerate:', prompt)}
          onDelete={(id) => console.log('Delete:', id)}
        />
      )}
    </div>
  )
}
```

Visit: `http://localhost:3000/test-image`

---

## Full Integration Checklist

Once basic setup works, integrate into chat:

### ChatInterface Integration

1. **Import components:**
```tsx
import ImageSuggestionPrompt from '@/components/ImageSuggestionPrompt'
import InlineChatImage from '@/components/InlineChatImage'
import { generateConversationImage, getConversationImages } from '@/lib/api'
```

2. **Add state:**
```tsx
const [conversationImages, setConversationImages] = useState([])
const [pendingImageSuggestion, setPendingImageSuggestion] = useState(null)
const [isGeneratingImage, setIsGeneratingImage] = useState(false)
```

3. **Load images on conversation open:**
```tsx
useEffect(() => {
  if (conversationId) {
    getConversationImages(conversationId).then(response => {
      setConversationImages(response.images)
    })
  }
}, [conversationId])
```

4. **Handle generation:**
```tsx
const handleGenerateImage = async (prompt, aspectRatio, model) => {
  setIsGeneratingImage(true)
  try {
    const result = await generateConversationImage({
      conversation_id: conversationId,
      prompt,
      aspect_ratio: aspectRatio,
      model
    })
    setConversationImages(prev => [result, ...prev])
  } finally {
    setIsGeneratingImage(false)
    setPendingImageSuggestion(null)
  }
}
```

5. **Render in messages:**
```tsx
{pendingImageSuggestion && (
  <ImageSuggestionPrompt
    suggestion={pendingImageSuggestion.suggestion}
    onAccept={handleGenerateImage}
    onDecline={() => setPendingImageSuggestion(null)}
    isGenerating={isGeneratingImage}
  />
)}

{conversationImages.map(image => (
  <InlineChatImage
    key={image.id}
    image={image}
    onRegenerate={handleGenerateImage}
    onDelete={handleDeleteImage}
  />
))}
```

### Backend Chat Endpoint

Add to your chat response handler:

```python
from services.conversation_service import get_conversation_service

# After generating assistant response:
conversation_service = get_conversation_service()
suggestion = conversation_service.should_suggest_image(
    user_message=user_message,
    assistant_response=assistant_response,
    recent_messages=recent_messages[-5:]
)

# Add to message metadata:
if suggestion.get('suggest'):
    message_metadata['image_suggestion'] = suggestion
```

---

## Testing Scenarios

### Test 1: Proactive Suggestion
1. Start conversation
2. Ask: "How does photosynthesis work?"
3. Should see suggestion after response
4. Click "Yes, generate it"
5. Aspect ratio selector appears
6. Select 16:9 and Fast
7. Image generates and displays

### Test 2: Explicit Request
1. Type: "Generate an image of a sunset in 16:9"
2.  Should detect request and show selector
3. Generate
4.  Image appears

### Test 3: Download
1. Generate an image
2. Click "Download" button
3. Image downloads to device

### Test 4: Regenerate
1. Generate an image
2. Click "Regenerate"
3. Selector appears with same prompt
4. Choose different ratio (e.g., 1:1)
5. New image generates

### Test 5: Persistence
1. Generate an image
2. Refresh page
3. Image still appears in conversation

### Test 6: Limit Enforcement
1. Generate 20 images in one conversation
2. Try to generate 21st
3. Error: "Image limit reached. Contact admin."

---

## Troubleshooting

### "No rows returned" error on migration
- **This is normal!** Migration creates tables, doesn't return data.

### "Authentication required" when testing API
- Make sure you're logged in
- Check JWT token in request headers
- Verify `SUPABASE_SERVICE_ROLE_KEY` is set

### Images not uploading to storage
- Verify bucket `conversation-images` exists
- Check bucket is set to **public**
- Check backend logs for upload errors

### Images generate but don't display
- Check storage_url in response
- Verify bucket permissions
- Check browser console for CORS errors
- Try accessing storage_url directly in browser

### Suggestions not appearing
- Check backend logs for `should_suggest_image` output
- Verify message metadata includes `image_suggestion`
- Check throttling (max 1 per 5 messages)

### "Invalid aspect ratio" error
- Use only: `1:1`, `16:9`, `9:16`, `4:3`
- Check for typos in aspect_ratio parameter

---

## Quick Reference

### API Endpoints
```
POST /api/images/generate-in-conversation
GET  /api/images/conversations/{id}
DELETE /api/images/{image_id}
GET  /api/images/models
```

### Aspect Ratios
- `1:1` - Square
- `16:9` - Landscape (default)
- `9:16` - Portrait
- `4:3` - Standard

### Models
- `fast` - Gemini 2.5 Flash (default, quick)
- `quality` - Gemini 3 Pro (slower, higher quality)

### Limits
- 20 images per conversation
- 60s timeout per generation
- Max 1 suggestion per 5 messages

---

## What to Show Users

Add this to system instructions or welcome message:

```
I can now generate images to help visualize concepts!

- I'll suggest images when they'd be helpful
- You can also ask me directly: "generate an image of [description]"
- Choose your preferred aspect ratio (square, landscape, portrait)
- Choose quality level (fast or high quality)
- Download any generated image
```

---

## Next Steps

1. Complete 5-minute setup above
2. Test with test page
3. Integrate into ChatInterface
4. Update system instructions
5. Test all scenarios
6. Deploy!

---

## Need Help?

- **Setup Issues:** Check `IMAGE_GENERATION_INTEGRATION_GUIDE.md`
- **Feature Details:** Check `IMAGE_GENERATION_SUMMARY.md`
- **Code Reference:** Check implementation plan in `.claude/plans/`
- **Backend Logs:** `backend/logs/`
- **Frontend Console:** Browser DevTools
