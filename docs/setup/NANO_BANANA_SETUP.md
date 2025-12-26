# Nano Banana Image Generation - Setup Guide

This guide walks you through setting up image generation capabilities in the Thesis app using Google's Gemini (Nano Banana) API.

## What is Nano Banana?

**Nano Banana** is Google's internal name for their fast image generation model (Gemini 2.5 Flash Image). It allows you to generate images from text prompts directly in the Thesis app.

## Quick Setup

### 1. Get Your Google AI API Key

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy the generated key

### 2. Install Dependencies

```bash
# Navigate to backend directory
cd backend

# Install the Google Generative AI package
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Add your API key to the backend `.env` file:

```bash
# Backend .env file
GOOGLE_GENERATIVE_AI_API_KEY=your-google-api-key-here
```

**Note:** The frontend doesn't need any additional environment variables - it communicates with the backend API.

### 4. Start the Application

```bash
# Start backend (from backend directory)
uvicorn main:app --reload --port 8000

# Start frontend (from frontend directory)
npm run dev
```

### 5. Access Image Generation

Once the app is running, navigate to:
```
http://localhost:3000/generate
```

Or click the "Generate Images" link in the navigation menu.

## Features

### What You Can Do

- **Text-to-Image**: Generate images from descriptive text prompts
- **Fast Generation**: Typically 10-30 seconds per image
- **Download**: Save generated images to your device
- **Multiple Formats**: PNG, JPEG support
- **Model Selection**: Choose between fast and high-quality models

### API Endpoints

The integration adds these new endpoints:

```
POST /api/images/generate
  - Generate a single image from a prompt
  - Body: { prompt: string, model?: string }
  - Returns: Base64-encoded image data

POST /api/images/generate-batch
  - Generate up to 5 images at once
  - Body: { prompts: string[], model?: string }
  - Returns: Array of image results

GET /api/images/models
  - List available image generation models
  - Returns: Array of model info
```

## Architecture

### Backend Components

```
backend/
├── services/
│   └── image_generation.py      # Core image generation service
├── api/routes/
│   └── images.py                 # API endpoints for images
└── requirements.txt              # Added google-generativeai
```

### Frontend Components

```
frontend/
├── app/generate/
│   └── page.tsx                  # Image generation page
├── components/
│   └── ImageGenerator.tsx        # Image generation UI component
└── lib/
    └── api.ts                    # Added image API methods
```

## Usage Examples

### Basic Image Generation

```typescript
import { generateImage } from '@/lib/api';

const result = await generateImage({
  prompt: "A futuristic classroom with AI assistants"
});

// result.image_data contains base64-encoded image
// result.mime_type contains the image type (e.g., 'image/png')
```

### Batch Generation

```typescript
import { generateImageBatch } from '@/lib/api';

const results = await generateImageBatch({
  prompts: [
    "A modern office space",
    "A collaborative learning environment",
    "An AI-powered workspace"
  ]
});

// results.results contains array of generated images
// results.successful contains count of successful generations
```

## Writing Good Prompts

For best results, include:

1. **Subject**: What you want to see
2. **Style**: Art style, medium, or aesthetic
3. **Colors**: Specific color palette or mood
4. **Composition**: Layout, perspective, framing
5. **Details**: Lighting, textures, atmosphere

### Examples

**Poor Prompt**: "a room"

**Good Prompt**: "A modern classroom with natural lighting, wooden desks arranged in small groups, plants by the windows, warm color palette, professional architectural photography style"

**Poor Prompt**: "person at computer"

**Good Prompt**: "A professional woman working at a sleek laptop in a bright co-working space, soft natural light from large windows, minimalist design, shallow depth of field, contemporary lifestyle photography"

## Available Models

| Model ID | Name | Speed | Quality | Best For |
|----------|------|-------|---------|----------|
| `gemini-2.5-flash-image` | Nano Banana | Fast | Good | Quick iterations, drafts |
| `gemini-3-pro-image-preview` | Gemini 3 Pro | Slower | Excellent | Final production images |

## Pricing & Limits

- **Free Tier**: 60 requests per minute
- **Cost**: Check [Google AI Pricing](https://ai.google.dev/pricing)
- **Image Size**: Up to 1024x1024 pixels
- **Timeout**: 60 seconds per request

## Troubleshooting

### "No valid API key"

**Problem**: The backend can't find your Google API key

**Solution**:
```bash
# Check your backend/.env file has:
GOOGLE_GENERATIVE_AI_API_KEY=your-actual-key-here

# Restart the backend server
```

### "Failed to generate image"

**Problem**: API request failed

**Solutions**:
1. Check your API key is valid at [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Verify you haven't exceeded rate limits (60/min free tier)
3. Check backend logs for detailed error messages
4. Try a simpler prompt to test basic functionality

### "Request timeout"

**Problem**: Image generation took too long

**Solutions**:
1. Try a simpler, shorter prompt
2. Use the faster model: `gemini-2.5-flash-image`
3. Check your internet connection

### Backend not starting

**Problem**: Missing dependencies

**Solution**:
```bash
cd backend
pip install -r requirements.txt
```

## Development Notes

### Adding Image Generation to Chat

The current implementation provides a standalone `/generate` page. To integrate image generation into the chat interface:

1. Detect image generation requests in chat (e.g., messages starting with "/imagine")
2. Call `generateImage()` from `ChatInterface.tsx`
3. Display generated images inline with chat messages
4. Store image references in conversation history

### Security Considerations

- API key is stored server-side only (backend `.env`)
- Frontend never sees the Google API key
- All requests require authentication (JWT from Supabase)
- Rate limiting is enforced on API endpoints

## Resources

- [Google AI Studio](https://aistudio.google.com/)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [Google Generative AI Python SDK](https://github.com/google/generative-ai-python)
- [Nano Banana Guide](https://www.cometapi.com/how-to-use-nano-banana-via-api/)

## Support

If you encounter issues:

1. Check the backend logs: `tail -f backend/logs/app.log`
2. Verify API key validity at Google AI Studio
3. Test the API endpoint directly with curl:

```bash
curl -X POST http://localhost:8000/api/images/generate \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"A simple test image"}'
```

## Next Steps

- [ ] Add image generation button to chat interface
- [ ] Support image editing and variations
- [ ] Add image history/gallery view
- [ ] Implement prompt templates for common use cases
- [ ] Add image-to-image generation
- [ ] Support custom model parameters (style, quality, etc.)
