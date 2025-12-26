# Image Generation Guide - Google Gemini (Nano Banana)

**Last Updated:** December 8, 2024

This document provides instructions for using Google's Gemini image generation API (branded as "nano banana") in the Thesis project.

## Overview

Thesis uses Google's `gemini-2.5-flash-image` model for image generation via direct HTTP REST API calls.

## Why HTTP REST API Instead of SDK?

The Python `google-generativeai` SDK (v0.8.5) does not properly extract `inlineData` from image generation responses. The HTTP REST API works reliably and returns base64-encoded PNG images.

## Environment Setup

### Required Environment Variable

```bash
GOOGLE_GENERATIVE_AI_API_KEY=AIzaSy...
```

Set in `/Users/motorthings/Documents/GitHub/thesis/backend/.env`

### API Key Source

- Obtained from: [Google AI Studio](https://aistudio.google.com/)
- Navigate to: API Keys section
- Generate new key or use existing one

## Implementation

### Service Location

```
/Users/motorthings/Documents/GitHub/thesis/backend/services/image_generation.py
```

### HTTP Endpoint

```
POST https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent
```

### Request Format

```bash
curl -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent" \
  -H "x-goog-api-key: $GOOGLE_GENERATIVE_AI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [{
      "parts": [
        {"text": "A friendly robot assistant, digital art style"}
      ]
    }]
  }'
```

### Response Format

```json
{
  "candidates": [{
    "content": {
      "parts": [
        {
          "text": "Description of the image..."
        },
        {
          "inlineData": {
            "mimeType": "image/png",
            "data": "base64EncodedImageData..."
          }
        }
      ]
    }
  }]
}
```

The `inlineData.data` field contains the base64-encoded PNG image.

## Usage in Code

### Single Image Generation

```python
from services.image_generation import get_image_generation_service

service = get_image_generation_service()

result = await service.generate_image(
    prompt="A futuristic robot assistant in a modern office"
)

# result contains:
# {
#   "image_data": "base64string...",
#   "mime_type": "image/png",
#   "prompt": "original prompt",
#   "model": "gemini-2.5-flash-image",
#   "success": True
# }
```

### Batch Generation

```python
prompts = [
    "A happy robot with a smile",
    "A peaceful zen garden"
]

results = await service.generate_multiple_images(prompts)

# Returns list of result dictionaries
for result in results:
    if result.get("success"):
        image_data = result["image_data"]
        # Process image...
```

### Decoding Base64 to Image File

```python
import base64
from pathlib import Path

image_bytes = base64.b64decode(result["image_data"])
Path("output.png").write_bytes(image_bytes)
```

## API Endpoints

### FastAPI Routes

Located in: `backend/api/routes/images.py`

#### Generate Single Image
```
POST /images/generate
```

**Request:**
```json
{
  "prompt": "A cute robot assistant",
  "model": "gemini-2.5-flash-image"  // optional
}
```

**Response:**
```json
{
  "image_data": "base64...",
  "mime_type": "image/png",
  "prompt": "A cute robot assistant",
  "model": "gemini-2.5-flash-image",
  "success": true
}
```

#### Generate Batch
```
POST /images/generate-batch
```

**Request:**
```json
{
  "prompts": [
    "A red apple",
    "A blue butterfly"
  ],
  "model": "gemini-2.5-flash-image"  // optional
}
```

**Response:**
```json
{
  "results": [...],
  "total": 2,
  "successful": 2
}
```

#### List Models
```
GET /images/models
```

Returns available image generation models.

## Testing

### Quick Test Script

```bash
cd /Users/motorthings/Documents/GitHub/thesis/backend
source venv/bin/activate
python3 test_imagen_http.py
```

### Test Files Location

```
/Users/motorthings/Documents/GitHub/thesis/backend/
├── test_imagen_http.py           # Direct HTTP API test
├── test_image_service_final.py   # Service integration test
└── test_gemini_models.py         # List available models
```

### Example Test Images

Located in: `/Users/motorthings/Documents/GitHub/thesis/images/`

- `nanobana_output.png` (1.5 MB)
- `test_single_output.png` (1.6 MB)
- `test_batch_1.png` (1.3 MB)
- `test_batch_2.png` (1.8 MB)

## Model Details

### Model Name
```
gemini-2.5-flash-image
```

### Alternative Names
- "nano banana" (marketing name)
- Gemini 2.5 Flash Image

### Other Available Models

```
gemini-2.0-flash-exp-image-generation  # Experimental, returns text only (broken)
imagen-4.0-generate-001                # Alternative endpoint (different API format)
```

**Note:** Use `gemini-2.5-flash-image` - it's the most reliable.

## Performance Characteristics

- **Response Time:** 10-30 seconds per image
- **Image Size:** ~1-2 MB per PNG
- **Format:** PNG only
- **Resolution:** High quality (specific resolution not documented)
- **Timeout:** Set to 60 seconds in service

## Troubleshooting

### Common Issues

#### 1. SDK Returns Text Instead of Images

**Problem:** Using `google-generativeai` SDK with `GenerativeModel.generate_content()` returns text descriptions instead of images.

**Solution:** Use HTTP REST API directly (already implemented in service).

#### 2. Empty inlineData

**Problem:** Response has `inlineData` but `data` field is empty or 0 bytes.

**Solution:** Check model name - use `gemini-2.5-flash-image` not experimental versions.

#### 3. Policy Violations

**Problem:** "This query violates the policy..."

**Solution:** Avoid prompts with:
- Named individuals (real people)
- Potentially harmful content
- Copyrighted characters

Use generic descriptions like "a robot assistant" instead of "Thesis the robot."

#### 4. API Key Errors

**Problem:** 401 Unauthorized or API key not found.

**Solution:**
- Verify `GOOGLE_GENERATIVE_AI_API_KEY` is set in `.env`
- Check API key is valid in Google AI Studio
- Ensure key has image generation quota available

### Checking API Credits

Visit [Google AI Studio](https://aistudio.google.com/) to check:
- API quota usage
- Rate limits
- Available credits

## Important Notes

- **Working:** HTTP REST API with `gemini-2.5-flash-image`
- **Not Working:** Python SDK extraction of image data
- **Avoid:** Experimental models (`gemini-2.0-flash-exp-image-generation`)
- **Dependencies:** `requests` library (already in requirements)
- **Auth:** API key in header as `x-goog-api-key`

## Code Changes Made (Dec 8, 2024)

### Before (Broken)
```python
import google.generativeai as genai
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash-image")
response = model.generate_content(prompt)
# image_data would be None or empty
```

### After (Working)
```python
import requests
url = f"{base_url}/models/gemini-2.5-flash-image:generateContent"
headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
payload = {"contents": [{"parts": [{"text": prompt}]}]}
response = requests.post(url, headers=headers, json=payload, timeout=60)
data = response.json()
image_data = data["candidates"][0]["content"]["parts"][1]["inlineData"]["data"]
# Returns base64 image data
```

## References

- [Google AI Gemini API - Image Generation](https://ai.google.dev/gemini-api/docs/image-generation)
- [Google AI Studio](https://aistudio.google.com/)
- [Gemini 2.5 Flash Image Model](https://aistudio.google.com/models/gemini-2-5-flash-image)

## Quick Reference Commands

```bash
# Test image generation
cd backend && source venv/bin/activate && python3 test_imagen_http.py

# List available models
python3 test_gemini_models.py

# Check API key
echo $GOOGLE_GENERATIVE_AI_API_KEY

# View generated test images
open images/nanobana_output.png
```

---

**Last tested:** December 8, 2024
**Status:** Working with API key `AIzaSyBAM4AwdJ1...aYtEk`
**Test results:** 4 successful image generations (single + batch)
