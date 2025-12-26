# Image Generation Setup Guide

Complete guide for setting up Nano Banana (Google Gemini) image generation in Thesis.

## Table of Contents

- [Quick Start](#quick-start)
- [Getting Your API Key](#getting-your-api-key)
- [Environment Configuration](#environment-configuration)
- [Installation](#installation)
- [Testing the Integration](#testing-the-integration)
- [Security Best Practices](#security-best-practices)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

**TL;DR**: Get a Google AI API key, add it to `.env`, install dependencies, start the app.

```bash
# 1. Get API key from https://aistudio.google.com/app/apikey

# 2. Create backend/.env file
cd backend
cp .env.example .env
# Add your key to GOOGLE_GENERATIVE_AI_API_KEY

# 3. Setup virtual environment and install
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Start backend
uvicorn main:app --reload --port 8000

# 5. In new terminal, start frontend
cd ../frontend
npm run dev

# 6. Visit http://localhost:3000/generate
```

---

## Getting Your API Key

### Step 1: Create Google AI API Key

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click **"Create API Key"** or **"Get API Key"**
4. Copy the generated key (looks like: `AIzaSy...`)
5. **Keep this key secret!**

### What is Nano Banana?

**Nano Banana** is Google's internal name for their fast image generation model:
- Official name: **Gemini 2.5 Flash Image**
- Speed: 10-30 seconds per image
- Quality: Good for most use cases
- Alternative: `gemini-3-pro-image-preview` for higher quality

### API Key Features

With a single Google AI API key you get:
-  Image generation (Nano Banana)
-  Text generation (Gemini models)
-  Free tier: 60 requests/minute
-  No credit card required for testing

---

## Environment Configuration

### Step 1: Create .env File

```bash
cd backend
cp .env.example .env
```

### Step 2: Add Your API Key

Open `backend/.env` and add your Google API key:

```bash
# ============================================================================
# GOOGLE GENERATIVE AI - Image Generation (Nano Banana)
# ============================================================================
GOOGLE_GENERATIVE_AI_API_KEY=your-actual-api-key-here
```

### Step 3: Configure Other Required Variables

For full functionality, you'll also need:

```bash
# DATABASE (Supabase) - Required for authentication
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here

# AI SERVICES - Required for chat features
ANTHROPIC_API_KEY=your-anthropic-api-key
VOYAGE_API_KEY=your-voyage-api-key

# FRONTEND - Required for CORS
FRONTEND_URL=http://localhost:3000
```

**Note**: Image generation will work once you have:
- `GOOGLE_GENERATIVE_AI_API_KEY` (required)
- Supabase credentials (for authentication) (required)
- All other services are optional for image generation

---

## Installation

### Backend Setup

#### 1. Navigate to Backend Directory

```bash
cd /Users/motorthings/Documents/GitHub/thesis/backend
```

#### 2. Create Virtual Environment

**Why?** Python best practice to isolate dependencies.

```bash
# Create virtual environment
python3 -m venv venv

# You should see a new 'venv' folder
ls -la | grep venv
```

#### 3. Activate Virtual Environment

```bash
source venv/bin/activate
```

**You'll know it's active when you see `(venv)` in your terminal prompt:**

```
(venv) motorthings@mac thesis/backend %
```

#### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `google-generativeai>=0.8.3` (Nano Banana)
- `fastapi`, `uvicorn` (API server)
- `anthropic`, `voyageai` (AI services)
- `supabase` (Database)
- And all other requirements

#### 5. Verify Installation

```bash
python3 -c "import google.generativeai as genai; print('Google Generative AI installed successfully')"
```

Expected output:
```
Google Generative AI installed successfully
```

### Frontend Setup

```bash
cd ../frontend

# Install dependencies (if not already done)
npm install

# No additional packages needed - uses backend API
```

---

## Testing the Integration

### Step 1: Start the Backend

```bash
cd backend

# Make sure virtual environment is active
source venv/bin/activate

# Start the server
uvicorn main:app --reload --port 8000
```

**Expected output:**
```
INFO:     Will watch for changes in these directories: ['/Users/motorthings/Documents/GitHub/thesis/backend']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:      All route modules registered
INFO:     Application startup complete
```

### Step 2: Start the Frontend

**In a new terminal window:**

```bash
cd /Users/motorthings/Documents/GitHub/thesis/frontend

npm run dev
```

**Expected output:**
```
  ▲ Next.js 16.0.1
  - Local:        http://localhost:3000

 Ready in 2.3s
```

### Step 3: Test Image Generation

1. **Open your browser**: `http://localhost:3000`

2. **Login** (requires Supabase setup)

3. **Navigate to**: `http://localhost:3000/generate`

4. **Enter a prompt**:
   ```
   A futuristic classroom with AI hologram assistants helping students learn,
   bright natural lighting, modern architecture, warm color palette,
   professional photography style
   ```

5. **Click "Generate Image"**

6. **Wait 10-30 seconds** for generation

7. **Download or view** your generated image!

### Step 4: Test API Directly (Advanced)

Test the API endpoint directly with curl:

```bash
# First, get your JWT token from browser
# Open DevTools → Application → Local Storage → look for 'supabase.auth.token'

curl -X POST http://localhost:8000/api/images/generate \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"A simple test image of a cat"}'
```

**Expected response:**
```json
{
  "image_data": "base64-encoded-image-string...",
  "mime_type": "image/png",
  "prompt": "A simple test image of a cat",
  "model": "gemini-2.5-flash-image",
  "success": true
}
```

---

## Security Best Practices

###  CRITICAL: Never Share Your API Keys

**If you accidentally expose your key:**

1. **Immediately regenerate it**:
   - Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Delete the exposed key
   - Create a new one
   - Update your `.env` file

2. **Common exposure risks**:
   -  Committing `.env` to git
   -  Sharing in chat/email
   -  Posting in screenshots
   -  Hardcoding in source files

###  Security Checklist

- [x] `.env` is in `.gitignore` (already configured)
- [x] API key only in backend `.env` (never in frontend)
- [x] `.env` file permissions set to `600` (owner read/write only)
- [x] Never commit `.env` to version control
- [x] Use separate keys for dev/staging/production
- [x] Regenerate keys if exposed

### File Permissions (Optional but Recommended)

```bash
# Set restrictive permissions on .env file
chmod 600 backend/.env

# Verify
ls -la backend/.env
# Should show: -rw------- (only you can read/write)
```

---

## Troubleshooting

### Backend Won't Start

**Problem**: `ModuleNotFoundError: No module named 'google.generativeai'`

**Solution**:
```bash
cd backend

# Make sure venv is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

---

**Problem**: `command not found: pip`

**Solution**:
```bash
# Use pip3 instead
pip3 install -r requirements.txt

# Or ensure venv is activated
source venv/bin/activate
pip install -r requirements.txt
```

---

**Problem**: `externally-managed-environment` error

**Solution**: You need to use a virtual environment:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

### Image Generation Fails

**Problem**: `Failed to generate image: No valid API key`

**Solution**:
```bash
# Check .env file exists
ls backend/.env

# Verify API key is set
grep GOOGLE_GENERATIVE_AI_API_KEY backend/.env

# Should show:
# GOOGLE_GENERATIVE_AI_API_KEY=AIzaSy...

# Restart backend after adding key
```

---

**Problem**: `401 Unauthorized` or `Authentication required`

**Solution**:
- Image generation requires login
- Make sure Supabase is configured
- Login at `http://localhost:3000/auth/login`
- If Supabase not setup, configure it first

---

**Problem**: `Request timeout` after 60 seconds

**Solutions**:
1. Try a simpler, shorter prompt
2. Check your internet connection
3. Verify API key is valid at [Google AI Studio](https://aistudio.google.com/app/apikey)
4. Check if you've hit rate limits (60/min free tier)

---

**Problem**: Images are low quality

**Solutions**:
1. Write more detailed prompts
2. Specify art style, lighting, composition
3. Use the higher quality model:
   ```typescript
   await generateImage({
     prompt: "your prompt",
     model: "gemini-3-pro-image-preview"  // Higher quality
   })
   ```

---

### Frontend Issues

**Problem**: `/generate` page shows 404

**Solution**:
```bash
# Make sure file exists
ls frontend/app/generate/page.tsx

# If missing, file should be at:
# frontend/app/generate/page.tsx

# Restart frontend
cd frontend
npm run dev
```

---

**Problem**: "Image Generator component not found"

**Solution**:
```bash
# Verify component exists
ls frontend/components/ImageGenerator.tsx

# Restart Next.js dev server
cd frontend
rm -rf .next
npm run dev
```

---

### Rate Limiting

**Problem**: Getting rate limit errors

**Free Tier Limits** (Google AI):
- 60 requests per minute
- 1,500 requests per day

**Solutions**:
1. Wait 60 seconds between batches
2. Upgrade to paid tier for higher limits
3. Implement request queuing in your code

---

### Database Connection Issues

**Problem**: Backend starts but can't connect to Supabase

**Solution**:
```bash
# Verify Supabase credentials in .env
grep SUPABASE backend/.env

# Test connection
curl http://localhost:8000/health

# Should return:
# {"status":"healthy","database":"connected"}
```

---

## Additional Resources

### Documentation
- [Google AI Studio](https://aistudio.google.com/)
- [Gemini API Docs](https://ai.google.dev/docs)
- [Google Generative AI Python SDK](https://github.com/google/generative-ai-python)
- [Nano Banana Guide](https://www.cometapi.com/how-to-use-nano-banana-via-api/)

### Thesis Project Docs
- [Main README](../README.md)
- [Full Setup Guide](../NANO_BANANA_SETUP.md)
- [API Documentation](./API.md)

### Getting Help

1. **Check backend logs**:
   ```bash
   # Backend terminal will show errors
   # Look for lines starting with ERROR or 
   ```

2. **Check browser console**:
   - Open DevTools (F12)
   - Look for errors in Console tab
   - Check Network tab for failed requests

3. **Test API directly**:
   ```bash
   # Health check
   curl http://localhost:8000/health

   # List available models (requires auth)
   curl http://localhost:8000/api/images/models \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
   ```

---

## What's Next?

Once image generation is working, you can:

### Enhance the Integration

1. **Add to Chat Interface**:
   - Detect prompts like "/imagine [description]"
   - Generate images inline in chat
   - Save images to conversation history

2. **Create Prompt Templates**:
   - Pre-built prompts for common use cases
   - "Professional headshot", "Course thumbnail", etc.

3. **Add Image Gallery**:
   - View previously generated images
   - Organize by project/category
   - Search by prompt text

4. **Batch Generation**:
   - Generate variations of same prompt
   - Compare different models/settings
   - A/B test image styles

### Advanced Features

- Image editing and variations
- Image-to-image generation
- Custom model parameters (style, quality)
- Integration with Supabase Storage
- Usage analytics and cost tracking

---

## Quick Reference

### Common Commands

```bash
# Activate virtual environment
source backend/venv/bin/activate

# Start backend
uvicorn main:app --reload --port 8000

# Start frontend
npm run dev

# Install new Python package
pip install package-name
pip freeze > requirements.txt

# Check Python version
python3 --version

# Check if Google AI package installed
python3 -c "import google.generativeai; print('Installed')"
```

### Directory Structure

```
thesis/
├── backend/
│   ├── .env                          # Your secrets (not in git)
│   ├── .env.example                  # Template
│   ├── requirements.txt              # Python dependencies
│   ├── venv/                         # Virtual environment
│   ├── services/
│   │   └── image_generation.py       # Image service
│   └── api/routes/
│       └── images.py                 # API endpoints
├── frontend/
│   ├── app/generate/
│   │   └── page.tsx                  # Image gen page
│   ├── components/
│   │   └── ImageGenerator.tsx        # UI component
│   └── lib/
│       └── api.ts                    # API client
└── docs/
    └── IMAGE_GENERATION_SETUP.md     # This file
```

### Environment Variables

```bash
# Required for image generation
GOOGLE_GENERATIVE_AI_API_KEY=your-key

# Required for authentication
SUPABASE_URL=https://project.supabase.co
SUPABASE_KEY=your-key
SUPABASE_SERVICE_ROLE_KEY=your-key

# Required for chat
ANTHROPIC_API_KEY=your-key
VOYAGE_API_KEY=your-key

# Required for CORS
FRONTEND_URL=http://localhost:3000
```

---

**Last Updated**: December 5, 2024
**Thesis Version**: 1.0.0
**Nano Banana Model**: gemini-2.5-flash-image
