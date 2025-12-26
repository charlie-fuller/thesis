# Help System Integration Guide

Step-by-step instructions to integrate the help system into your other repository.

## Prerequisites Checklist

Before starting, verify your target repository has:

- [ ] **Backend**: FastAPI-based Python backend
- [ ] **Frontend**: Next.js/React with TypeScript
- [ ] **Database**: PostgreSQL with pgvector extension enabled
- [ ] **Authentication**: Supabase JWT-based authentication
- [ ] **User table**: Contains `id` (UUID) and `role` (TEXT) columns
- [ ] **Embeddings service**: Either existing or add Voyage AI (instructions below)

## Step 1: Database Setup

### 1.1 Verify pgvector Extension

Connect to your PostgreSQL database and run:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 1.2 Run Migrations

```bash
# From your repository root
psql $SUPABASE_DB_URL -f help-system-package/database/migrations/add_help_system.sql
psql $SUPABASE_DB_URL -f help-system-package/database/migrations/add_help_feedback.sql
```

Or using Supabase CLI:

```bash
supabase db push --db-url $SUPABASE_DB_URL < help-system-package/database/migrations/add_help_system.sql
supabase db push --db-url $SUPABASE_DB_URL < help-system-package/database/migrations/add_help_feedback.sql
```

### 1.3 Verify Tables Created

```sql
-- Should see 4 new tables
SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename LIKE 'help_%';

-- Expected output:
-- help_documents
-- help_chunks
-- help_conversations
-- help_messages
```

## Step 2: Backend Integration

### 2.1 Copy Backend Files

```bash
# From your repository root
cp help-system-package/backend/api/routes/help_chat.py backend/api/routes/
cp help-system-package/backend/helpers/help_search.py backend/helpers/
cp help-system-package/backend/scripts/index_help_docs.py backend/scripts/
```

### 2.2 Add Router to FastAPI App

Edit your `backend/main.py`:

```python
# Add import at the top
from api.routes import help_chat

# Add router with other routers (usually near the bottom)
app.include_router(help_chat.router)
```

**Example integration**:
```python
# backend/main.py
from fastapi import FastAPI
from api.routes import auth, users, help_chat  # Add help_chat

app = FastAPI(title="Your App")

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(help_chat.router)  # Add this line
```

### 2.3 Verify Dependencies Match

Check that these exist in your backend (the help system uses them):

**Required backend files/functions**:
- `helpers/supabase_helpers.py` with `get_supabase_admin_client()`
- `api/dependencies.py` with `get_current_user()` dependency
- `services/embeddings.py` with `create_embedding()` function

**If embeddings.py doesn't exist**, see Section 2.4 below.

### 2.4 Add Embeddings Service (if needed)

If you don't have `backend/services/embeddings.py`, create it:

```python
# backend/services/embeddings.py
import os
import voyageai
from typing import List, Union

VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")
voyage_client = voyageai.Client(api_key=VOYAGE_API_KEY)

def create_embedding(
    text: str,
    input_type: str = "document"
) -> List[float]:
    """
    Create a single embedding for the given text.

    Args:
        text: Text to embed
        input_type: "document" for indexing, "query" for search

    Returns:
        List of floats (1536 dimensions for voyage-3)
    """
    result = voyage_client.embed(
        texts=[text],
        model="voyage-3",
        input_type=input_type
    )
    return result.embeddings[0]

def create_embeddings(
    texts: List[str],
    input_type: str = "document",
    batch_size: int = 128
) -> List[List[float]]:
    """
    Create embeddings for multiple texts in batches.

    Args:
        texts: List of texts to embed
        input_type: "document" or "query"
        batch_size: Process this many at a time

    Returns:
        List of embedding vectors
    """
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        result = voyage_client.embed(
            texts=batch,
            model="voyage-3",
            input_type=input_type
        )
        all_embeddings.extend(result.embeddings)

    return all_embeddings
```

Install dependency:
```bash
pip install voyageai
```

## Step 3: Frontend Integration

### 3.1 Copy Frontend Files

```bash
# From your repository root
cp help-system-package/frontend/components/* frontend/components/
cp help-system-package/frontend/contexts/HelpChatContext.tsx frontend/contexts/
```

### 3.2 Add Provider to App

Edit your `frontend/components/Providers.tsx`:

```typescript
// Add import at the top
import { HelpChatProvider } from '@/contexts/HelpChatContext'

// Wrap your existing providers
export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <SupabaseProvider>
      <OtherProviders>
        <HelpChatProvider>  {/* Add this */}
          {children}
        </HelpChatProvider>
      </OtherProviders>
    </SupabaseProvider>
  )
}
```

### 3.3 Add Component to Layout

Edit your admin layout (e.g., `frontend/app/admin/layout.tsx`):

```typescript
// Add import at the top
import HelpChat from '@/components/HelpChat'

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen">
      {/* Your existing sidebar/nav */}
      <YourSidebar />

      {/* Main content */}
      <main className="flex-1">
        {children}
      </main>

      {/* Help chat sidebar */}
      <HelpChat />  {/* Add this */}
    </div>
  )
}
```

### 3.4 Verify Frontend Dependencies

Check `frontend/package.json` includes:

```json
{
  "dependencies": {
    "react-markdown": "^9.0.0",
    "react-syntax-highlighter": "^15.5.0"
  },
  "devDependencies": {
    "@types/react-syntax-highlighter": "^15.5.0"
  }
}
```

If missing, install:
```bash
cd frontend
npm install react-markdown react-syntax-highlighter
npm install --save-dev @types/react-syntax-highlighter
```

## Step 4: Environment Variables

### 4.1 Backend Environment Variables

Add to your `backend/.env`:

```env
# AI APIs (required)
ANTHROPIC_API_KEY=sk-ant-xxxxx
VOYAGE_API_KEY=pa-xxxxx

# Help system webhook auth (required for auto-reindex)
HELP_REINDEX_API_KEY=your-secure-random-key-here

# Existing vars (already present)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJxxx...
SUPABASE_JWT_SECRET=your-jwt-secret
```

**Generate `HELP_REINDEX_API_KEY`**:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 4.2 Frontend Environment Variables

Your `frontend/.env.local` should already have:

```env
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJxxx...
NEXT_PUBLIC_API_URL=https://your-backend-api.com
```

No additional frontend env vars needed!

## Step 5: Create Help Documentation

### 5.1 Create Directory Structure

```bash
# From your repository root
mkdir -p docs/help/admin
mkdir -p docs/help/user
mkdir -p docs/help/system
```

### 5.2 Add Your First Help Document

Create `docs/help/user/getting-started.md`:

```markdown
# Getting Started

Welcome to [Your Platform Name]! This guide will help you get started.

## Creating Your First Project

To create a project:

1. Click the "New Project" button in the dashboard
2. Enter a project name
3. Select your project type
4. Click "Create"

## Next Steps

- Learn about [Features](./features.md)
- Read the [FAQ](./faq.md)
- Contact support if you need help
```

### 5.3 Add More Documentation

Continue adding `.md` files for your platform. The indexer will automatically:
- Discover all markdown files
- Extract titles and sections
- Chunk content intelligently
- Generate embeddings
- Make searchable in help chat

**Recommended structure**:
```
docs/help/
├── admin/
│   ├── getting-started.md
│   ├── user-management.md
│   ├── configuration.md
│   └── troubleshooting.md
├── user/
│   ├── getting-started.md
│   ├── features.md
│   ├── billing.md
│   └── faq.md
└── system/
    ├── architecture.md
    └── api-reference.md
```

## Step 6: Index Your Documentation

### 6.1 Run Initial Index

```bash
# From your repository root
python backend/scripts/index_help_docs.py
```

**Expected output**:
```
Indexing help documents...
Processing: docs/help/user/getting-started.md
  Created 3 chunks
Processing: docs/help/admin/user-management.md
  Created 5 chunks
...
Indexing complete!
Documents: 8
Chunks: 42
```

### 6.2 Verify in Database

```sql
-- Check documents indexed
SELECT title, category, word_count FROM help_documents;

-- Check chunks created
SELECT COUNT(*) as chunk_count FROM help_chunks;

-- Test vector search (replace with actual embedding)
SELECT * FROM match_help_chunks(
  ARRAY[0.1, 0.2, ...]::vector,  -- Your query embedding
  5,  -- Number of results
  'user'  -- User role
);
```

## Step 7: Test the System

### 7.1 Backend Health Check

```bash
curl http://localhost:8000/api/help/status
```

Expected response:
```json
{
  "status": "healthy",
  "document_count": 8,
  "chunk_count": 42,
  "indexed": true
}
```

### 7.2 Test Search Endpoint

```bash
curl http://localhost:8000/api/help/test-search?query=getting+started
```

Should return relevant chunks from your docs.

### 7.3 Test Frontend

1. Start your frontend: `npm run dev`
2. Log in as a user
3. Look for help chat sidebar on admin pages
4. Type a question: "How do I create a project?"
5. Verify you get a response with source citations

### 7.4 Test Full Conversation Flow

- [ ] Send a message and get response
- [ ] Response includes source citations
- [ ] Can expand sources to see details
- [ ] Can click thumbs up/down on response
- [ ] Can start new conversation
- [ ] Can view conversation history
- [ ] Can load previous conversation
- [ ] Can delete conversation
- [ ] Shift+Enter creates new line (Enter sends)

## Step 8: Set Up Auto-Reindexing (Optional)

This makes documentation updates automatic when you push to GitHub.

### 8.1 Copy GitHub Actions Workflow

```bash
cp help-system-package/automation/workflows/reindex-help-docs.yml .github/workflows/
```

### 8.2 Add GitHub Secrets

In your repository settings (Settings → Secrets → Actions), add:

- `REINDEX_API_URL` = `https://your-backend-api.com/api/help/index-docs-webhook`
- `REINDEX_API_KEY` = Same value as `HELP_REINDEX_API_KEY` from backend `.env`

### 8.3 Test Auto-Reindex

1. Edit a file in `docs/help/`
2. Commit and push to main:
   ```bash
   git add docs/help/user/getting-started.md
   git commit -m "docs: Update getting started guide"
   git push origin main
   ```
3. Check GitHub Actions tab - should see "Reindex Help Documentation" workflow running
4. Verify in your app that changes are reflected

## Troubleshooting

### Issue: "Table 'help_documents' does not exist"

**Solution**: Run database migrations (Step 1.2)

### Issue: "Module 'voyageai' not found"

**Solution**: Install embeddings dependency:
```bash
pip install voyageai
```

### Issue: "No embeddings service found"

**Solution**: Add `VOYAGE_API_KEY` to `.env` and create `embeddings.py` (Step 2.4)

### Issue: Help chat doesn't appear in UI

**Solution**:
1. Verify `HelpChatProvider` wraps your app (Step 3.2)
2. Verify `<HelpChat />` component added to layout (Step 3.3)
3. Check browser console for errors
4. Verify API URL is correct in frontend `.env.local`

### Issue: Search returns no results

**Solution**:
1. Verify documents indexed: `SELECT COUNT(*) FROM help_documents;`
2. Run indexer: `python backend/scripts/index_help_docs.py`
3. Check API key is valid: `echo $VOYAGE_API_KEY`
4. Test endpoint: `/api/help/test-search?query=test`

### Issue: "Authentication failed" errors

**Solution**:
1. Verify `SUPABASE_JWT_SECRET` matches between frontend and backend
2. Check user is logged in (has valid Supabase session)
3. Verify `get_current_user` dependency works in other endpoints

### Issue: GitHub Actions workflow fails

**Solution**:
1. Verify `REINDEX_API_URL` secret is correct
2. Verify `REINDEX_API_KEY` matches backend env var
3. Check workflow logs for specific error
4. Test webhook manually:
   ```bash
   curl -X POST https://your-api.com/api/help/index-docs-webhook \
     -H "Authorization: Bearer YOUR_API_KEY"
   ```

## Next Steps

Once integrated:

1. **Customize the system** - See [CUSTOMIZATION.md](./CUSTOMIZATION.md)
2. **Add more documentation** - Populate `docs/help/` with your content
3. **Configure role access** - Edit `ROLE_ACCESS_MAP` in `index_help_docs.py`
4. **Monitor usage** - Check `/api/help/stats` for analytics
5. **Collect feedback** - Review thumbs up/down data to improve docs

## Support

If you encounter issues not covered here, check:
- [CONFIGURATION.md](./CONFIGURATION.md) - All config options
- [CUSTOMIZATION.md](./CUSTOMIZATION.md) - Customization guide
- Database migration files for schema details
- Source code comments for implementation details
