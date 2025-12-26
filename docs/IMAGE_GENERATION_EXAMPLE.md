# Thesis Image Generation - Complete Example

## API Endpoint
```
POST https://thesis-production.up.railway.app/images/generate
```

## Request Format

### Headers
```http
Authorization: Bearer <user-jwt-token>
Content-Type: application/json
```

### Request Body
```json
{
  "prompt": "A friendly learning and development professional coaching a small team in a modern office",
  "model": "gemini-2.5-flash-image"
}
```

## Response Format

### Success Response (200 OK)
```json
{
  "image_data": "iVBORw0KGgoAAAANSUhEUgAAB4AAAAQ4CAYAAADo08aFAAA...(base64 encoded PNG data)...==",
  "mime_type": "image/png",
  "prompt": "A friendly learning and development professional coaching a small team in a modern office",
  "model": "gemini-2.5-flash-image",
  "success": true
}
```

### Error Response (500)
```json
{
  "detail": "Failed to generate image: <error message>"
}
```

## How Frontend Displays the Image

The frontend receives the base64 image data and displays it:

```jsx
// React component example
function ChatMessage({ message }) {
  if (message.image_data) {
    return (
      <div className="chat-message">
        <img
          src={`data:${message.mime_type};base64,${message.image_data}`}
          alt={message.prompt}
          className="generated-image"
        />
        <p className="prompt-text">{message.prompt}</p>
      </div>
    );
  }

  return <div className="chat-message">{message.text}</div>;
}
```

## Complete End-to-End Flow

### 1. User Input
User types in chat:
```
/visualize A customer service representative using the LEAP framework to help a happy customer
```

### 2. Frontend Processing
```javascript
// Frontend detects /visualize command
const prompt = message.replace('/visualize ', '');

// Make API call
const response = await fetch('https://thesis-production.up.railway.app/images/generate', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${userToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ prompt })
});

const imageData = await response.json();
```

### 3. Backend Processing
```python
# images.py route handler
@router.post("/generate")
async def generate_image(request: ImageGenerationRequest, current_user: dict):
    service = get_image_generation_service()

    # Call Google Gemini API
    result = await service.generate_image(
        prompt=request.prompt,
        model="gemini-2.5-flash-image"
    )

    return ImageGenerationResponse(**result)
```

### 4. Google Gemini API Call
```python
# services/image_generation.py
gen_model = genai.GenerativeModel("gemini-2.5-flash-image")
response = gen_model.generate_content(prompt)

# Extract image from response
candidate = response.candidates[0]
for part in candidate.content.parts:
    if hasattr(part, 'inline_data'):
        image_bytes = part.inline_data.data
        mime_type = part.inline_data.mime_type

        # Convert to base64
        image_data = base64.b64encode(image_bytes).decode('utf-8')
```

### 5. Response Back to Frontend
```json
{
  "image_data": "iVBORw0KGgoAAAANS...base64...==",
  "mime_type": "image/png",
  "prompt": "A customer service representative using the LEAP framework...",
  "model": "gemini-2.5-flash-image",
  "success": true
}
```

### 6. Frontend Display
```html
<div class="message-image">
  <img src="data:image/png;base64,iVBORw0KGgoAAAANS...=="
       alt="A customer service representative using the LEAP framework..." />
  <p class="image-caption">Generated with Gemini 2.5 Flash Image</p>
</div>
```

## Image Output Specifications

- **Format**: PNG (base64 encoded)
- **Model**: Google Gemini 2.5 Flash Image (Nano Banana)
- **Max Prompt Length**: 2000 characters
- **Response Time**: Typically 2-5 seconds
- **Image Quality**: High-quality, suitable for L&D illustrations
- **Resolution**: Varies by model, typically 1024x1024 or similar

## Example Prompts for L&D Use Cases

1. **Training Scenario**
   ```
   A professional trainer presenting to a diverse group of learners in an interactive classroom setting
   ```

2. **Process Visualization**
   ```
   A flowchart showing the ADDIE instructional design process with icons representing each phase
   ```

3. **Coaching Scene**
   ```
   A manager providing constructive feedback to an employee in a supportive one-on-one meeting
   ```

4. **Technology Integration**
   ```
   Learners using tablets and laptops for collaborative online learning in a modern training room
   ```

## Batch Generation Example

For generating multiple images at once:

```json
POST /images/generate-batch

{
  "prompts": [
    "A sales professional demonstrating the GROW coaching model",
    "A team brainstorming session using sticky notes on a whiteboard",
    "An online learning platform dashboard showing progress metrics"
  ],
  "model": "gemini-2.5-flash-image"
}
```

Response:
```json
{
  "results": [
    {
      "image_data": "base64...",
      "mime_type": "image/png",
      "prompt": "A sales professional...",
      "model": "gemini-2.5-flash-image",
      "success": true
    },
    // ... 2 more images
  ],
  "total": 3,
  "successful": 3
}
```

## Testing the Deployed System

### 1. Via Frontend (Recommended)
1. Go to https://thesis-woad.vercel.app
2. Sign up / Login
3. Type: `/visualize [your prompt]`
4. Image appears in the chat

### 2. Via API (with authentication)
```bash
# Get auth token first by logging in
TOKEN="your-jwt-token"

# Generate image
curl -X POST https://thesis-production.up.railway.app/images/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A learning professional coaching a team"
  }'
```

### 3. Check Available Models
```bash
curl -X GET https://thesis-production.up.railway.app/images/models \
  -H "Authorization: Bearer $TOKEN"
```

Response:
```json
{
  "models": [
    {
      "id": "gemini-2.5-flash-image",
      "name": "Gemini 2.5 Flash (Nano Banana)",
      "description": "Fast, lightweight image generation",
      "default": true
    },
    {
      "id": "gemini-3-pro-image-preview",
      "name": "Gemini 3 Pro",
      "description": "Higher quality image generation (preview)",
      "default": false
    }
  ]
}
```

## Current Deployment Status

**Backend**: https://thesis-production.up.railway.app
**Frontend**: https://thesis-woad.vercel.app
**Image Generation Endpoint**: `/images/generate` - OPERATIONAL
**Google Generative AI API Key**: Configured in Railway environment
**Model**: gemini-2.5-flash-image (default)

## Summary

The image generation system is **fully deployed and operational**:

1. API endpoint exists and is accessible
2. Google Gemini API integration complete
3. Base64 image encoding/decoding working
4. Authentication required and enforced
5. Error handling implemented
6. Batch generation supported
7. Multiple models available

The system generates **real PNG images** as base64-encoded data that the frontend displays directly in the chat interface.
