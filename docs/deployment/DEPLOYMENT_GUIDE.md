# Thesis - Complete Setup & Deployment Guide

## Table of Contents
1. [Local Development Setup](#local-development-setup)
2. [Testing Guide](#testing-guide)
3. [Production Deployment](#production-deployment)
4. [Troubleshooting](#troubleshooting)

---

## Local Development Setup

### Prerequisites
- Python 3.11+ installed
- Node.js 18+ and npm installed
- Git installed
- Supabase account (free tier works)
- API keys for: Anthropic Claude, Voyage AI, Google Generative AI

### Backend Setup

#### 1. Clone and Navigate
```bash
git clone <repository-url>
cd thesis/backend
```

#### 2. Create Python Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Configure Environment Variables
Create `.env` file in `backend/` directory:

```bash
# Database (Supabase)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
SUPABASE_JWT_SECRET=your-jwt-secret-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here

# Anthropic Claude API
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx

# Voyage AI Embeddings
VOYAGE_API_KEY=pa-xxxxx

# Google Generative AI (Nano Banana - Image Generation)
GOOGLE_GENERATIVE_AI_API_KEY=AIzaSyxxxxx

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:3000

# Default client configuration
DEFAULT_CLIENT_ID=00000000-0000-0000-0000-000000000001
CLIENT_NAME=Your Organization
ASSISTANT_NAME=Thesis
MULTI_TENANT_MODE=false
```

#### 5. Set Up Supabase Database

**Option A: Run Full Schema (Fresh Database)**
```bash
# In Supabase SQL Editor, run:
cat database/thesis_full_schema.sql | pbcopy  # macOS
# Then paste into Supabase SQL Editor and execute
```

**Option B: Run Migrations Sequentially**
```bash
# In Supabase SQL Editor, run migrations in order:
# backend/migrations/002_*.sql
# backend/migrations/003_*.sql
# ... etc.
```

#### 6. Start Backend Server
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

Verify backend is running:
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","database":"connected","version":"1.0.0"}
```

---

### Frontend Setup

#### 1. Navigate to Frontend
```bash
cd thesis/frontend
```

#### 2. Install Dependencies
```bash
npm install
```

#### 3. Configure Environment Variables
Create `.env.local` file in `frontend/` directory:

```bash
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here

# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

#### 4. Start Frontend Server
```bash
npm run dev
```

Frontend will be available at: **http://localhost:3000**

---

## Testing Guide

### 1. User Authentication Flow

#### Create Test User
1. Open browser: http://localhost:3000
2. Click "Sign Up" (or navigate to `/auth/signup`)
3. Create account with email/password
4. Verify email if required (check Supabase Auth settings)
5. Login with credentials

**Expected Result:** Should redirect to main chat interface

---

### 2. Thesis L&D Persona Verification

#### Test System Instructions Loading

**Test Chat:**
1. Login to application
2. Start new conversation
3. Send message: "What should I start with when planning a learning program?"

**Expected Thesis Response:**
Thesis should respond with ROI-first approach, mentioning:
- DDLD framework (Data, Desired state, Learning gap, Difference)
- Business problem before solution
- KPIs to impact
- Behavior change before content design

**Verify Persona:**
- Tone: Warm, curious, not preachy
- References: Should mention "augmenting human expertise"
- Structure: Clear headings, bullet points
- Should ask clarifying questions about business context

---

### 3. Document Upload & RAG Pipeline

#### Test Document Upload

**Prepare Test Documents:**
Three sample L&D documents are in `/test-documents/`:
- `customer_service_excellence_program.md`
- `sales_leadership_coaching_program.md`
- `technical_writing_fundamentals.md`

**Upload Flow:**
1. Login to Thesis
2. Navigate to Documents section (or upload button)
3. Upload `customer_service_excellence_program.md`
4. Wait for processing (status should change from "pending" to "completed")

**Verify in Supabase:**
```sql
-- Check document was uploaded
SELECT id, filename, processing_status, chunk_count
FROM documents
WHERE filename LIKE '%customer_service%';

-- Check chunks were created
SELECT COUNT(*) as total_chunks
FROM document_chunks
WHERE document_id = 'your-document-id';

-- Expected: chunk_count > 0 (should be 20-50 chunks depending on document size)
```

#### Test RAG-Powered Search

**Test Query:**
1. After uploading `customer_service_excellence_program.md`
2. In chat, ask: "What are the success metrics for the customer service program?"

**Expected Response:**
- Thesis should reference specific metrics from the document:
  - CSAT score target: 4.5+
  - First-call resolution: 85%+
  - Customer escalation rate: <10%
  - ROI: 1,233% over 12 months
- Should cite the document as source

**Verify RAG is Working:**
If Thesis responds with generic L&D advice instead of specific metrics from the document, RAG is not working correctly.

---

### 4. Image Generation with Nano Banana

#### Test Image Generation API

**Direct API Test:**
```bash
curl -X POST http://localhost:8000/api/images/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "prompt": "A friendly learning and development professional coaching a team in a modern office, professional illustration style"
  }'
```

**Expected Response:**
```json
{
  "image_url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
  "prompt": "A friendly learning...",
  "model": "gemini-2.5-flash-image",
  "created_at": "2025-12-05T..."
}
```

#### Test Image Generation in Chat

**Using Slash Command:**
1. In chat interface, type: `/visualize A customer service representative successfully helping a happy customer using the LEAP framework`
2. Thesis should generate an image using Nano Banana

**Expected Result:**
- Image appears in chat
- Thesis provides context about the visual
- Image reflects the L&D scenario described

---

### 5. End-to-End Workflow Test

#### Complete Learning Program Design Workflow

**Scenario:** Design a learning program for onboarding new sales reps

**Step 1: Start with ROI (Thesis's mandate)**
```
User: "I need to create an onboarding program for new sales reps. Where should I start?"

Expected: Thesis asks about business problem (DDLD), KPIs, current performance gaps
```

**Step 2: Upload Reference Materials**
```
User: [Uploads sales_leadership_coaching_program.md]

Expected: Thesis acknowledges document, suggests it as reference
```

**Step 3: Use RAG Context**
```
User: "Can you suggest success metrics based on what worked in other sales programs?"

Expected: Thesis references uploaded document's metrics (quota attainment, turnover, pipeline velocity)
```

**Step 4: Generate Visual Assets**
```
User: "/visualize A new sales rep confidently making their first successful pitch"

Expected: Thesis generates image using Nano Banana
```

**Step 5: Create Structured Output**
```
User: "/outline Create a 4-week onboarding program outline"

Expected: Thesis uses structured output format with clear phases, activities, assessments
```

---

## Production Deployment

### Backend Deployment (Railway)

#### 1. Prepare Backend for Deployment
```bash
cd backend
```

Ensure `Procfile` exists:
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

Ensure `runtime.txt` specifies Python version:
```
python-3.11.0
```

#### 2. Deploy to Railway

**Option A: Via Railway CLI**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link project (or create new)
railway link

# Set environment variables
railway variables set SUPABASE_URL=https://your-project.supabase.co
railway variables set SUPABASE_KEY=your-anon-key
railway variables set SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
railway variables set SUPABASE_JWT_SECRET=your-jwt-secret
railway variables set ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
railway variables set VOYAGE_API_KEY=pa-xxxxx
railway variables set GOOGLE_GENERATIVE_AI_API_KEY=AIzaSyxxxxx
railway variables set FRONTEND_URL=https://your-app.vercel.app

# Deploy
railway up
```

**Option B: Via GitHub Integration**
1. Connect Railway to your GitHub repository
2. Set environment variables in Railway dashboard
3. Push to `main` branch → Auto-deploy

**Verify Deployment:**
```bash
curl https://your-backend.railway.app/health
```

---

### Frontend Deployment (Vercel)

#### 1. Prepare Frontend for Deployment
```bash
cd frontend
```

Ensure `vercel.json` exists (if not, create):
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "framework": "nextjs"
}
```

#### 2. Deploy to Vercel

**Option A: Via Vercel CLI**
```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy
vercel

# Set environment variables
vercel env add NEXT_PUBLIC_SUPABASE_URL production
vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY production
vercel env add NEXT_PUBLIC_API_URL production

# Redeploy with env vars
vercel --prod
```

**Option B: Via GitHub Integration**
1. Connect Vercel to your GitHub repository
2. Configure environment variables:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `NEXT_PUBLIC_API_URL` (your Railway backend URL)
3. Push to `main` branch → Auto-deploy

**Verify Deployment:**
Open browser to: `https://your-app.vercel.app`

---

## Troubleshooting

### Backend Issues

#### "ModuleNotFoundError: No module named 'dotenv'"
**Solution:** Ensure virtual environment is activated and dependencies installed
```bash
source venv/bin/activate
pip install -r requirements.txt
```

#### "Connection refused" when testing health endpoint
**Solution:** Backend server not running
```bash
uvicorn main:app --reload --port 8000
```

#### "Database connection failed"
**Solution:** Check Supabase credentials in `.env`
```bash
# Verify credentials in Supabase Dashboard → Settings → API
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Image generation returns error
**Solution:** Verify Google Generative AI API key
```bash
# Test API key directly
curl -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent?key=YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"test"}]}]}'
```

---

### Frontend Issues

#### "Failed to fetch" in browser console
**Solution:** CORS issue - verify backend CORS configuration
```python
# In backend/main.py, check:
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### "Invalid JWT" error
**Solution:** Supabase JWT secret mismatch
- Verify `SUPABASE_JWT_SECRET` in backend `.env` matches Supabase project settings

#### Documents upload but don't appear in chat context
**Solution:** RAG pipeline not processing
1. Check document processing status in Supabase:
   ```sql
   SELECT id, filename, processing_status, processing_error
   FROM documents
   WHERE processing_status = 'error';
   ```
2. Check backend logs for embedding errors
3. Verify Voyage AI API key is valid

---

### RAG Pipeline Issues

#### Documents upload but chunks not created
**Solution:** Document processing failed
```sql
-- Check for processing errors
SELECT id, filename, processing_status, processing_error
FROM documents
WHERE processing_status != 'completed';
```

**Common Causes:**
- Voyage AI API key invalid
- Document format not supported (only PDF, DOCX, TXT, MD supported)
- File too large (check size limits)

#### Chat doesn't use uploaded documents
**Solution:** Vector search not returning results
```sql
-- Test vector search manually
SELECT content, 1 - (embedding <=> query_embedding) as similarity
FROM document_chunks
WHERE 1 - (embedding <=> query_embedding) > 0.7
ORDER BY similarity DESC
LIMIT 5;
```

**Verify:**
- Embeddings were generated (check `embedding` column is not NULL)
- Similarity threshold not too high (try lowering from 0.7 to 0.5)

---

## Performance Optimization

### Backend
- Enable Redis caching for frequently accessed documents
- Use connection pooling for Supabase (already configured)
- Monitor API rate limits (Anthropic, Voyage AI)

### Frontend
- Enable Next.js Image optimization for generated images
- Implement lazy loading for chat history
- Use React.memo for chat message components

### Database
- Add indexes on frequently queried columns (already in migrations)
- Vacuum and analyze database regularly
- Monitor vector search performance (pgvector)

---

## Monitoring & Observability

### Sentry Integration (Already Configured)
- Frontend errors: Tracked in Sentry dashboard
- Backend errors: Configure Sentry SDK in Python

### Key Metrics to Monitor
- **Chat API Response Time:** <2 seconds average
- **Document Processing Time:** <30 seconds per document
- **RAG Search Performance:** <500ms for vector search
- **Image Generation Time:** <5 seconds per image

---

## Security Best Practices

### API Keys
- Never commit `.env` files to git (already in `.gitignore`)
- Use environment variables in production
- Rotate API keys quarterly
- Use separate keys for dev/staging/production

### Database
- Row-level security enabled in Supabase (check policies)
- Service role key only in backend (never expose to frontend)
- User isolation (documents tied to user_id)

### Authentication
- JWT tokens expire after 1 hour (Supabase default)
- Refresh tokens stored securely (httpOnly cookies)
- Password requirements enforced (Supabase Auth)

---

## Next Steps After Deployment

1. **Create Default User:** Set up admin account via Supabase dashboard
2. **Upload Sample Documents:** Add 3-5 L&D reference documents to test RAG
3. **Test End-to-End:** Run through complete workflow (signup → upload → chat → generate image)
4. **Monitor Errors:** Check Sentry for any frontend/backend errors
5. **Optimize:** Review performance metrics and optimize bottlenecks

---

**Last Updated:** December 5, 2025
**Maintained By:** L&D Engineering Team
**Questions?** Open an issue in GitHub repository
