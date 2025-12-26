# Help System Integration Checklist

Use this checklist to ensure complete integration.

## Pre-Integration Setup

### API Keys
- [ ] Anthropic API key obtained from https://console.anthropic.com
- [ ] Voyage AI API key obtained from https://www.voyageai.com
- [ ] Webhook API key generated: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

### Environment Setup
- [ ] Backend `.env` has `ANTHROPIC_API_KEY`
- [ ] Backend `.env` has `VOYAGE_API_KEY`
- [ ] Backend `.env` has `HELP_REINDEX_API_KEY`
- [ ] Backend `.env` has existing Supabase vars
- [ ] Frontend `.env.local` has existing Supabase vars
- [ ] Frontend `.env.local` has `NEXT_PUBLIC_API_URL`

### Prerequisites Verified
- [ ] PostgreSQL database accessible
- [ ] pgvector extension enabled: `CREATE EXTENSION IF NOT EXISTS vector;`
- [ ] FastAPI backend running
- [ ] Next.js frontend running
- [ ] Supabase authentication working
- [ ] Users table has `id` (UUID) and `role` (TEXT) columns

## Database Setup

- [ ] Copied migration files to project
- [ ] Ran `add_help_system.sql` migration
- [ ] Ran `add_help_feedback.sql` migration
- [ ] Verified 4 tables created: `SELECT tablename FROM pg_tables WHERE tablename LIKE 'help_%';`
- [ ] Verified `match_help_chunks` function exists: `SELECT proname FROM pg_proc WHERE proname = 'match_help_chunks';`
- [ ] Verified indexes created: `SELECT indexname FROM pg_indexes WHERE tablename LIKE 'help_%';`

## Dependency Installation

### Backend
- [ ] Installed: `pip install anthropic`
- [ ] Installed: `pip install voyageai`
- [ ] Installed: `pip install slowapi`
- [ ] Verified: `pip list | grep -E 'anthropic|voyageai|slowapi'`

### Frontend
- [ ] Installed: `npm install react-markdown react-syntax-highlighter`
- [ ] Installed: `npm install --save-dev @types/react-syntax-highlighter`
- [ ] Verified: `npm list react-markdown react-syntax-highlighter`

## Backend Integration

### File Copying
- [ ] Copied `help_chat.py` to `backend/api/routes/`
- [ ] Copied `help_search.py` to `backend/helpers/`
- [ ] Copied `index_help_docs.py` to `backend/scripts/`
- [ ] Created `embeddings.py` in `backend/services/` (if needed)

### Code Integration
- [ ] Added import in `backend/main.py`: `from api.routes import help_chat`
- [ ] Added router in `backend/main.py`: `app.include_router(help_chat.router)`
- [ ] Verified existing `get_current_user` dependency exists
- [ ] Verified existing `get_supabase_admin_client` function exists

### Backend Testing
- [ ] Backend starts without errors: `python backend/main.py` or `uvicorn main:app`
- [ ] Health endpoint works: `curl http://localhost:8000/api/help/status`
- [ ] Returns: `{"status":"healthy",...}`

## Frontend Integration

### File Copying
- [ ] Copied `HelpChat.tsx` to `frontend/components/`
- [ ] Copied `MarkdownText.tsx` to `frontend/components/`
- [ ] Copied `LoadingSpinner.tsx` to `frontend/components/` (or verified exists)
- [ ] Copied `HelpChatContext.tsx` to `frontend/contexts/`

### Code Integration
- [ ] Added import in `Providers.tsx`: `import { HelpChatProvider } from '@/contexts/HelpChatContext'`
- [ ] Wrapped app with `<HelpChatProvider>` in `Providers.tsx`
- [ ] Added import in layout: `import HelpChat from '@/components/HelpChat'`
- [ ] Added `<HelpChat />` component to layout (usually admin layout)

### Frontend Testing
- [ ] Frontend builds without errors: `npm run build`
- [ ] Frontend starts: `npm run dev`
- [ ] No console errors in browser
- [ ] Help chat sidebar visible on admin pages

## Documentation Setup

### Directory Structure
- [ ] Created `docs/help/` directory
- [ ] Created `docs/help/admin/` subdirectory
- [ ] Created `docs/help/user/` subdirectory
- [ ] Created `docs/help/system/` subdirectory (optional)

### Content Creation
- [ ] Created at least one markdown file in `docs/help/user/`
- [ ] Markdown file has proper structure (headings, content)
- [ ] File follows naming convention: lowercase, hyphens, `.md` extension

### Indexing
- [ ] Ran indexer: `python backend/scripts/index_help_docs.py`
- [ ] Saw output: "Indexing complete! Documents: X, Chunks: Y"
- [ ] Verified in database: `SELECT COUNT(*) FROM help_documents;`
- [ ] Verified in database: `SELECT COUNT(*) FROM help_chunks;`

## End-to-End Testing

### Basic Functionality
- [ ] Health check returns healthy status
- [ ] Test search works: `curl http://localhost:8000/api/help/test-search?query=test`
- [ ] Help chat sidebar appears in UI
- [ ] Can type in chat input
- [ ] Can send a message (Enter key)
- [ ] Receive AI response within 5 seconds
- [ ] Response is relevant to question
- [ ] Response includes source citations
- [ ] Can expand source details
- [ ] Similarity scores shown for sources

### Conversation Management
- [ ] Can start new conversation (button works)
- [ ] New conversation clears current messages
- [ ] Conversation history sidebar visible
- [ ] Can see previous conversations listed
- [ ] Can click to load previous conversation
- [ ] Previous messages load correctly
- [ ] Can delete conversation
- [ ] Deleted conversation removed from list

### Feedback System
- [ ] Thumbs up button visible on assistant messages
- [ ] Thumbs down button visible on assistant messages
- [ ] Can click thumbs up (changes state)
- [ ] Can click thumbs down (changes state)
- [ ] Feedback saved: `SELECT * FROM help_messages WHERE feedback IS NOT NULL;`

### Role-Based Access
- [ ] Logged in as regular user
- [ ] User only sees user-appropriate docs in results
- [ ] Logged in as admin
- [ ] Admin sees admin docs in results
- [ ] Admin sees user docs in results

### UI/UX
- [ ] Messages auto-scroll to bottom
- [ ] Shift+Enter creates new line (doesn't send)
- [ ] Enter key sends message
- [ ] Loading spinner shows while waiting
- [ ] Markdown formatting renders correctly
- [ ] Code blocks have syntax highlighting
- [ ] Links in responses are clickable
- [ ] Sidebar is scrollable
- [ ] Input grows with multi-line text

## Automation Setup (Optional)

### GitHub Actions
- [ ] Copied workflow file to `.github/workflows/reindex-help-docs.yml`
- [ ] Added GitHub Secret: `REINDEX_API_URL`
- [ ] Added GitHub Secret: `REINDEX_API_KEY`
- [ ] Secrets match backend environment variables

### Automation Testing
- [ ] Made change to help doc
- [ ] Committed and pushed to main
- [ ] GitHub Actions workflow triggered
- [ ] Workflow completed successfully (green check)
- [ ] Changes reflected in help chat
- [ ] Verified in Actions tab: no errors

## Production Deployment

### Backend Deployment
- [ ] Environment variables set in production
- [ ] Database migrations run on production database
- [ ] Backend deployed and accessible
- [ ] Health endpoint returns 200: `curl https://your-api.com/api/help/status`

### Frontend Deployment
- [ ] Environment variables set for production build
- [ ] Frontend built successfully
- [ ] Frontend deployed
- [ ] Help chat accessible in production app

### Production Testing
- [ ] Can access help chat in production
- [ ] Can send messages and get responses
- [ ] Responses are accurate
- [ ] Source citations work
- [ ] Conversation history persists
- [ ] Feedback buttons work
- [ ] No console errors

## Performance & Monitoring

### Performance
- [ ] Search responds in <2 seconds
- [ ] AI response generates in <5 seconds
- [ ] No timeouts or errors
- [ ] Database queries are fast
- [ ] Vector search uses index

### Monitoring
- [ ] Monitor API costs (Anthropic dashboard)
- [ ] Monitor embedding costs (Voyage dashboard)
- [ ] Check database size growth
- [ ] Review error logs
- [ ] Check rate limit hits

### Analytics
- [ ] Track conversation count: `SELECT COUNT(*) FROM help_conversations;`
- [ ] Track message count: `SELECT COUNT(*) FROM help_messages;`
- [ ] Review feedback: `SELECT feedback, COUNT(*) FROM help_messages GROUP BY feedback;`
- [ ] Find popular topics: Review conversation titles

## Documentation Maintenance

### Content Quality
- [ ] Help docs are accurate
- [ ] Help docs are up-to-date
- [ ] Help docs cover main features
- [ ] Help docs answer common questions
- [ ] No broken links in docs

### Organization
- [ ] Docs organized by user role
- [ ] File names are descriptive
- [ ] Consistent formatting across docs
- [ ] Proper heading hierarchy (H1, H2, H3)

### Updates
- [ ] Process for updating docs established
- [ ] Team knows how to add new docs
- [ ] Reindex runs after doc updates
- [ ] Regular review schedule set

## Customization (Optional)

- [ ] Adjusted chunk size if needed
- [ ] Configured role access mapping
- [ ] Customized system prompt
- [ ] Adjusted number of sources (top_k)
- [ ] Changed AI model if desired
- [ ] Customized UI colors/styling
- [ ] Adjusted rate limits
- [ ] Added custom metadata

## Security Review

- [ ] API keys stored securely (not in code)
- [ ] Row-level security policies active
- [ ] Rate limiting configured
- [ ] Webhook authentication working
- [ ] User data isolated properly
- [ ] No sensitive data in logs
- [ ] CORS configured correctly
- [ ] JWT validation working

## Final Verification

- [ ] All features working in production
- [ ] No errors in application logs
- [ ] No errors in database logs
- [ ] Users can access help chat
- [ ] Feedback from users is positive
- [ ] Performance is acceptable
- [ ] Costs are within budget
- [ ] Team trained on maintenance

## Success Criteria

**Integration Complete** when:
- All checkboxes above are checked
- Help chat is live in production
- Users can ask questions and get accurate answers
- Source citations are correct
- Conversation history works
- Feedback system works
- Auto-reindex works (if enabled)
- No critical errors

## Rollback Plan (If Needed)

If something goes wrong:

1. **Remove router** from `backend/main.py`
2. **Remove provider** from `frontend/Providers.tsx`
3. **Remove component** from layout
4. **Drop tables** (if needed):
   ```sql
   DROP TABLE help_messages CASCADE;
   DROP TABLE help_conversations CASCADE;
   DROP TABLE help_chunks CASCADE;
   DROP TABLE help_documents CASCADE;
   ```
5. **Restart** backend and frontend

## Getting Help

If stuck:
- [ ] Reviewed [INTEGRATION.md](docs/INTEGRATION.md)
- [ ] Checked [CONFIGURATION.md](docs/CONFIGURATION.md)
- [ ] Reviewed troubleshooting sections
- [ ] Checked application logs
- [ ] Checked database connection
- [ ] Verified API keys are valid
- [ ] Tested with minimal example first

---

**Current Status**: ___ of ___ items complete

**Notes**:

---

**Completed**: __________ (date)

**Verified by**: __________
