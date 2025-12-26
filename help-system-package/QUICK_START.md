# Help System - Quick Start

Get up and running in 10 minutes.

## Prerequisites Check

Before starting, verify:

```bash
# PostgreSQL with pgvector
psql $DATABASE_URL -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Python 3.8+
python --version

# Node.js 18+
node --version

# Your app has Supabase auth
# Your app has FastAPI backend
# Your app has Next.js frontend
```

## Installation Steps

### 1. Get API Keys (5 min)

**Anthropic API Key**: https://console.anthropic.com
- Sign up → API Keys → Create key
- Add billing info (required)

**Voyage AI API Key**: https://www.voyageai.com
- Sign up → API Keys → Create key
- Free tier: 100M tokens (~$120 value)

**Generate Webhook Key**:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Set Environment Variables (1 min)

Add to `backend/.env`:
```env
ANTHROPIC_API_KEY=sk-ant-xxxxx
VOYAGE_API_KEY=pa-xxxxx
HELP_REINDEX_API_KEY=<generated-key>
```

### 3. Run Database Migrations (1 min)

```bash
cd your-repo
psql $DATABASE_URL -f help-system-package/database/migrations/add_help_system.sql
psql $DATABASE_URL -f help-system-package/database/migrations/add_help_feedback.sql
```

Verify:
```sql
SELECT tablename FROM pg_tables WHERE tablename LIKE 'help_%';
-- Should see: help_documents, help_chunks, help_conversations, help_messages
```

### 4. Install Dependencies (1 min)

```bash
# Backend
pip install anthropic voyageai slowapi

# Frontend
cd frontend
npm install react-markdown react-syntax-highlighter
npm install --save-dev @types/react-syntax-highlighter
```

### 5. Copy Backend Files (1 min)

```bash
cd your-repo
cp help-system-package/backend/api/routes/help_chat.py backend/api/routes/
cp help-system-package/backend/helpers/help_search.py backend/helpers/
cp help-system-package/backend/scripts/index_help_docs.py backend/scripts/
```

**Add router to `backend/main.py`**:
```python
from api.routes import help_chat

app.include_router(help_chat.router)
```

**If you don't have `backend/services/embeddings.py`**, create it:
```bash
cp help-system-package/backend/services/embeddings.py backend/services/
```

### 6. Copy Frontend Files (1 min)

```bash
cp help-system-package/frontend/components/* frontend/components/
cp help-system-package/frontend/contexts/HelpChatContext.tsx frontend/contexts/
```

**Add provider to `frontend/components/Providers.tsx`**:
```typescript
import { HelpChatProvider } from '@/contexts/HelpChatContext'

export function Providers({ children }) {
  return (
    <YourExistingProviders>
      <HelpChatProvider>
        {children}
      </HelpChatProvider>
    </YourExistingProviders>
  )
}
```

**Add component to `frontend/app/admin/layout.tsx`**:
```typescript
import HelpChat from '@/components/HelpChat'

export default function AdminLayout({ children }) {
  return (
    <div className="flex">
      <YourSidebar />
      <main>{children}</main>
      <HelpChat />  {/* Add this */}
    </div>
  )
}
```

### 7. Create Help Documentation (2 min)

```bash
# Create directories
mkdir -p docs/help/admin docs/help/user

# Create first document
cat > docs/help/user/getting-started.md << 'EOF'
# Getting Started

Welcome to our platform!

## Creating Your First Project

1. Click the "New Project" button in the dashboard
2. Enter a project name
3. Select your project type
4. Click "Create"

## Next Steps

- Explore the dashboard
- Invite team members
- Configure your settings
EOF
```

### 8. Index Your Documentation (1 min)

```bash
python backend/scripts/index_help_docs.py
```

Expected output:
```
Indexing help documents...
Processing: docs/help/user/getting-started.md
  Created 3 chunks
Indexing complete!
Documents: 1
Chunks: 3
```

### 9. Test the System (2 min)

**Backend health check**:
```bash
curl http://localhost:8000/api/help/status
# Expected: {"status":"healthy","document_count":1,"chunk_count":3}
```

**Test search**:
```bash
curl http://localhost:8000/api/help/test-search?query=getting+started
# Expected: Relevant chunks from your doc
```

**Frontend test**:
1. Start your app: `npm run dev`
2. Log in as a user
3. Look for help chat sidebar on admin pages
4. Type: "How do I create a project?"
5. Should get response from your doc

### 10. Optional: Set Up Auto-Reindex (2 min)

**Copy workflow**:
```bash
cp help-system-package/automation/workflows/reindex-help-docs.yml .github/workflows/
```

**Add GitHub Secrets** (Settings → Secrets → Actions):
- `REINDEX_API_URL` = `https://your-api.com/api/help/index-docs-webhook`
- `REINDEX_API_KEY` = Same value as `HELP_REINDEX_API_KEY` from `.env`

**Test**:
```bash
echo "\n## Test Section\n\nTest content" >> docs/help/user/getting-started.md
git add docs/help/
git commit -m "docs: Test auto-reindex"
git push origin main
# Check GitHub Actions tab - workflow should run
```

## Verification Checklist

- [ ] Database tables created
- [ ] API keys in `.env`
- [ ] Dependencies installed
- [ ] Backend files copied
- [ ] Frontend files copied
- [ ] Router added to `main.py`
- [ ] Provider added to `Providers.tsx`
- [ ] Component added to layout
- [ ] Help docs created
- [ ] Documentation indexed
- [ ] `/api/help/status` returns healthy
- [ ] Help chat appears in UI
- [ ] Can ask questions and get answers
- [ ] Source citations show correctly

## Common Issues

**"Table 'help_documents' does not exist"**
→ Run migrations (Step 3)

**"Module 'voyageai' not found"**
→ `pip install voyageai`

**Help chat doesn't appear**
→ Check `HelpChatProvider` wraps app
→ Check `<HelpChat />` in layout
→ Check browser console for errors

**No search results**
→ Run indexer: `python backend/scripts/index_help_docs.py`
→ Verify docs exist: `ls docs/help/`

**"Authentication failed"**
→ Verify `SUPABASE_JWT_SECRET` matches
→ Check user is logged in

## Next Steps

1. **Add more documentation** - Create more `.md` files in `docs/help/`
2. **Customize styling** - Edit `HelpChat.tsx` colors and layout
3. **Adjust settings** - See [CONFIGURATION.md](docs/CONFIGURATION.md)
4. **Monitor usage** - Check feedback and stats endpoints
5. **Customize prompts** - Edit `help_search.py` system prompt

## Cost Estimate

With default settings:
- **Per query**: ~$0.003
- **1,000 queries/month**: ~$3
- **10,000 queries/month**: ~$30

Very affordable for most use cases!

## File Structure After Integration

```
your-repo/
├── backend/
│   ├── api/routes/
│   │   └── help_chat.py          ← NEW
│   ├── helpers/
│   │   └── help_search.py        ← NEW
│   ├── scripts/
│   │   └── index_help_docs.py    ← NEW
│   ├── services/
│   │   └── embeddings.py         ← NEW (if needed)
│   └── main.py                    ← MODIFIED
├── frontend/
│   ├── components/
│   │   ├── HelpChat.tsx          ← NEW
│   │   ├── MarkdownText.tsx      ← NEW
│   │   └── LoadingSpinner.tsx    ← NEW
│   ├── contexts/
│   │   └── HelpChatContext.tsx   ← NEW
│   ├── components/Providers.tsx   ← MODIFIED
│   └── app/admin/layout.tsx       ← MODIFIED
├── docs/help/                     ← NEW DIRECTORY
│   ├── admin/
│   │   └── your-docs.md
│   └── user/
│       └── getting-started.md
└── .github/workflows/
    └── reindex-help-docs.yml     ← NEW (optional)
```

## Support

- **Full integration guide**: [docs/INTEGRATION.md](docs/INTEGRATION.md)
- **Configuration options**: [docs/CONFIGURATION.md](docs/CONFIGURATION.md)
- **Customization examples**: [docs/CUSTOMIZATION.md](docs/CUSTOMIZATION.md)
- **Writing help docs**: [docs/help/README.md](docs/help/README.md)

## Summary

You now have a complete AI-powered help system! Users can:

- Ask questions in natural language
- Get accurate answers from your documentation
- See source citations with similarity scores
- Access conversation history
- Provide feedback on answers

And you can:

- Drop markdown files into `docs/help/` → auto-indexed
- Monitor usage and feedback
- Customize to match your brand
- Scale affordably

**Total time**: ~10 minutes
**Ongoing cost**: ~$3-30/month depending on usage
**Maintenance**: Just update your markdown docs

Enjoy your new help system!
