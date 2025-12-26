# Help System - Portable Package

A complete AI-powered help chat system that you can drop into any FastAPI + Next.js application.

## What Is This?

This is a fully-functional help system extracted from the SuperAssistant platform, ready to integrate into your other repository. It provides:

- **AI-powered help chat** using Claude Sonnet 4.5
- **Semantic search** across your documentation
- **Conversation history** with persistent chat
- **User feedback** (thumbs up/down)
- **Auto-reindexing** when docs change (via GitHub Actions)
- **Role-based access** to documentation
- **Source citations** showing where answers came from

## Quick Start (5 Minutes)

```bash
# 1. Copy package to your repository
cp -r /path/to/help-system-package /path/to/your-repo/

# 2. Run database migrations
cd your-repo
psql $DATABASE_URL -f help-system-package/database/migrations/add_help_system.sql
psql $DATABASE_URL -f help-system-package/database/migrations/add_help_feedback.sql

# 3. Install dependencies
pip install anthropic voyageai slowapi
npm install react-markdown react-syntax-highlighter

# 4. Copy files to your app
cp help-system-package/backend/api/routes/help_chat.py backend/api/routes/
cp help-system-package/backend/helpers/help_search.py backend/helpers/
cp help-system-package/backend/scripts/index_help_docs.py backend/scripts/
cp help-system-package/frontend/components/* frontend/components/
cp help-system-package/frontend/contexts/HelpChatContext.tsx frontend/contexts/

# 5. Add to your app (see INTEGRATION.md for details)
# - Add router to backend/main.py
# - Add provider to frontend/Providers.tsx
# - Add component to your layout

# 6. Set environment variables
# ANTHROPIC_API_KEY, VOYAGE_API_KEY, HELP_REINDEX_API_KEY

# 7. Create help docs
mkdir -p docs/help/admin docs/help/user

# 8. Index your docs
python backend/scripts/index_help_docs.py

# 9. Test it!
curl http://localhost:8000/api/help/status
```

Done! Your help chat is now live.

## Package Contents

```
help-system-package/
├── README.md                     # This file
├── frontend/
│   ├── components/
│   │   ├── HelpChat.tsx         # Main chat UI
│   │   ├── MarkdownText.tsx     # Markdown renderer
│   │   └── LoadingSpinner.tsx   # Loading indicator
│   └── contexts/
│       └── HelpChatContext.tsx  # State management
├── backend/
│   ├── api/routes/
│   │   └── help_chat.py         # API endpoints
│   ├── helpers/
│   │   └── help_search.py       # Search logic
│   └── scripts/
│       └── index_help_docs.py   # Documentation indexer
├── database/
│   ├── migrations/
│   │   ├── add_help_system.sql  # Core tables
│   │   └── add_help_feedback.sql # Feedback feature
│   └── README.md
├── automation/
│   ├── workflows/
│   │   └── reindex-help-docs.yml # GitHub Actions
│   └── README.md
└── docs/
    ├── INTEGRATION.md           # Step-by-step setup guide
    ├── CONFIGURATION.md         # All config options
    ├── CUSTOMIZATION.md         # How to customize
    └── help/
        └── README.md            # Help docs guide
```

## Prerequisites

Your target repository must have:

- **Backend**: FastAPI Python backend
- **Frontend**: Next.js/React with TypeScript
- **Database**: PostgreSQL with pgvector extension
- **Authentication**: Supabase JWT-based auth
- **User table**: With `id` (UUID) and `role` (TEXT) columns

## Features

### For End Users
- Chat interface with markdown formatting
- Source citations with similarity scores
- Conversation history (load previous chats)
- Thumbs up/down feedback
- Multi-line input (Shift+Enter for newlines)
- Auto-scroll to new messages

### For Admins
- Drop markdown files into `docs/help/` → auto-indexed
- Manual reindex via API endpoint
- Auto-reindex on doc changes (GitHub Actions)
- Health check and stats endpoints
- Feedback analytics

### Technical
- Vector similarity search (pgvector + Voyage embeddings)
- Claude Sonnet 4.5 for responses
- Semantic chunking (respects markdown structure)
- Rate limiting (protects APIs)
- Row-level security (users see only their data)
- Optimized indexes (IVFFlat for fast search)

## Documentation

Detailed guides in the `docs/` directory:

1. **[INTEGRATION.md](docs/INTEGRATION.md)** - Step-by-step setup (START HERE)
2. **[CONFIGURATION.md](docs/CONFIGURATION.md)** - All environment variables and config options
3. **[CUSTOMIZATION.md](docs/CUSTOMIZATION.md)** - How to customize for your needs
4. **[database/README.md](database/README.md)** - Database setup and migrations
5. **[automation/README.md](automation/README.md)** - GitHub Actions auto-reindex setup
6. **[docs/help/README.md](docs/help/README.md)** - Writing help documentation

## Dependencies

### Backend (Python)
```bash
pip install anthropic      # Claude API
pip install voyageai       # Embeddings
pip install slowapi        # Rate limiting
# fastapi, supabase already in your app
```

### Frontend (JavaScript)
```bash
npm install react-markdown react-syntax-highlighter
npm install --save-dev @types/react-syntax-highlighter
# react, next, supabase already in your app
```

## Environment Variables

### Backend (.env)
```env
ANTHROPIC_API_KEY=sk-ant-xxxxx           # Required
VOYAGE_API_KEY=pa-xxxxx                   # Required
HELP_REINDEX_API_KEY=your-secure-key     # Required for auto-reindex
SUPABASE_URL=https://xxx.supabase.co     # Already in your app
SUPABASE_SERVICE_ROLE_KEY=eyJxxx...      # Already in your app
SUPABASE_JWT_SECRET=your-jwt-secret      # Already in your app
```

### Frontend (.env.local)
```env
# No new variables needed - uses existing Supabase config
NEXT_PUBLIC_API_URL=https://your-api.com  # Already in your app
```

## Cost Estimate

Very affordable for most use cases:

- **Indexing 50 docs**: ~$0.05 one-time
- **1,000 queries/month**: ~$3.00
- **10,000 queries/month**: ~$30.00

## Creating Your Help Documentation

1. Create directory structure:
   ```bash
   mkdir -p docs/help/admin
   mkdir -p docs/help/user
   ```

2. Add markdown files:
   ```bash
   # Example: docs/help/user/getting-started.md
   cat > docs/help/user/getting-started.md << 'EOF'
   # Getting Started

   Welcome to our platform!

   ## Creating Your First Project

   1. Click "New Project"
   2. Enter a name
   3. Click "Create"
   EOF
   ```

3. Index documentation:
   ```bash
   python backend/scripts/index_help_docs.py
   ```

4. Test in chat:
   - Open your app
   - Ask: "How do I create a project?"
   - Should get response from your doc

See [docs/help/README.md](docs/help/README.md) for detailed writing guide.

## API Endpoints

Once integrated, you'll have:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/help/ask` | POST | Send question, get AI response |
| `/api/help/conversations` | GET | List user's conversations |
| `/api/help/conversations/{id}` | GET | Load specific conversation |
| `/api/help/conversations/{id}` | DELETE | Delete conversation |
| `/api/help/feedback/{message_id}` | POST | Submit thumbs up/down |
| `/api/help/search` | GET | Direct search (no conversation) |
| `/api/help/stats` | GET | Admin statistics |
| `/api/help/status` | GET | Health check |
| `/api/help/index-docs` | POST | Manual reindex (admin) |
| `/api/help/index-docs-webhook` | POST | Webhook reindex (API key auth) |

## Testing Checklist

After integration:

- [ ] `/api/help/status` returns healthy
- [ ] `/api/help/test-search` returns results
- [ ] Help chat appears in UI
- [ ] Can send message and get response
- [ ] Response includes source citations
- [ ] Can start new conversation
- [ ] Can load conversation history
- [ ] Can delete conversation
- [ ] Thumbs up/down works
- [ ] Role-based access works
- [ ] Manual reindex works
- [ ] Auto-reindex works (if using GitHub Actions)

## Troubleshooting

**Help chat doesn't appear**
- Check `HelpChatProvider` is in Providers.tsx
- Check `<HelpChat />` is in layout
- Check browser console for errors

**No search results**
- Run indexer: `python backend/scripts/index_help_docs.py`
- Check docs exist in `docs/help/`
- Test endpoint: `/api/help/test-search?query=test`

**Authentication errors**
- Verify `SUPABASE_JWT_SECRET` matches frontend and backend
- Check user is logged in

**Rate limit errors**
- Default: 30 requests/minute
- Adjust in `backend/api/routes/help_chat.py`

See [INTEGRATION.md](docs/INTEGRATION.md) for detailed troubleshooting.

## Customization Examples

### Change Sidebar Position
```typescript
// In frontend/components/HelpChat.tsx
<div className="fixed left-0">  {/* Change from right-0 */}
```

### Use Cheaper Model
```python
# In backend/api/routes/help_chat.py
model="claude-haiku-4-20250514"  # Change from sonnet
```

### Add More Sources
```python
# In backend/api/routes/help_chat.py
top_k: int = 5  # Change from 3
```

See [CUSTOMIZATION.md](docs/CUSTOMIZATION.md) for 20+ customization examples.

## Security

- Row-level security on all tables
- JWT authentication required
- Rate limiting on all endpoints
- Webhook API key authentication
- Role-based access to docs
- User data isolation

## Support

For issues or questions:

1. Check documentation in `docs/` directory
2. Review source code comments
3. Test with minimal setup first
4. Check database migrations ran successfully

## What's NOT Included

This package does NOT include:

- Help documentation content (you create your own)
- Main app dependencies (uses your existing setup)
- Embeddings service (instructions provided to add)

Everything else is included and ready to use!

## Next Steps

1. **Read [INTEGRATION.md](docs/INTEGRATION.md)** - Complete setup guide
2. **Set up database** - Run migrations
3. **Copy files** - Move to your repo
4. **Configure** - Set environment variables
5. **Create docs** - Write your help documentation
6. **Index** - Run indexer script
7. **Test** - Verify everything works
8. **Customize** - Make it yours

## License

Extracted from SuperAssistant platform. Use freely in your projects.

---

**Ready to integrate?** Start with [docs/INTEGRATION.md](docs/INTEGRATION.md)

**Have questions?** Check [docs/CONFIGURATION.md](docs/CONFIGURATION.md)

**Want to customize?** See [docs/CUSTOMIZATION.md](docs/CUSTOMIZATION.md)
