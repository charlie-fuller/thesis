# Admin Troubleshooting

Common issues and how to resolve them. This guide covers system-level problems that require admin access.

---

## Agent Issues

### Responses are too generic

**Symptoms:**
- Agents give boilerplate answers
- No reference to uploaded documents
- Responses don't match user's context

**Causes and fixes:**

| Cause | Fix |
|-------|-----|
| Documents not classified | Check classification in `/admin/documents` |
| Embeddings outdated | Reprocess document embeddings |
| Agent instructions too broad | Review and tighten instructions in `/admin/agents` |
| User asking wrong agent | Suggest appropriate agent for the question |

### Wrong agent responding

**Symptoms:**
- Auto mode routes to unexpected agent
- Agent gives off-topic responses

**Fixes:**
1. Check Coordinator instructions at `/admin/agents/coordinator`
2. Review routing rules in the Coordinator's system prompt
3. Verify agent specializations are clearly defined

### Slow responses

**Symptoms:**
- Long delays before response starts
- Timeouts on complex queries

**Causes and fixes:**

| Cause | Fix |
|-------|-----|
| Large context window | Reduce document count in retrieval |
| Complex instructions | Simplify agent system prompts |
| API rate limiting | Check Anthropic API status |
| Database slow | Check Supabase performance metrics |

---

## Document Issues

### Document not found in searches

**Check:**
1. Is it in the database? `/admin/documents?search=filename`
2. Is it classified? Check agent tags
3. Are embeddings generated? Check `document_embeddings` table
4. Is the content extractable? (Some PDFs have issues)

**Fix:**
- Reprocess the document
- Manually add classifications
- Re-upload if extraction failed

### Classification seems wrong

**Check:**
1. View document in admin
2. Review suggested vs actual classifications
3. Check confidence scores

**Fix:**
- Manually correct classifications
- Reprocess with updated classifier
- Add to training data for future improvements

### Sync problems (Obsidian/Google Drive)

**Symptoms:**
- Files not appearing after sync
- Stale content
- Sync errors in logs

**Check:**
1. Integration status at `/admin/integrations`
2. Last successful sync timestamp
3. Error logs for the integration

**Fix:**
- Re-authenticate the integration
- Trigger manual sync
- Check file permissions on source

---

## Database Issues

### Connection errors

**Symptoms:**
- "Connection refused" errors
- Timeouts on database operations
- Intermittent failures

**Check:**
1. Supabase dashboard - is the project running?
2. Connection pool status
3. Network connectivity from backend

**Fix:**
```bash
# Test connection
psql "postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres" -c "SELECT 1"
```

If connection works but app fails:
- Check connection pool limits
- Verify environment variables
- Restart backend service

### Migration state issues

**Symptoms:**
- Missing tables
- Schema mismatch errors
- Foreign key violations

**Check:**
```sql
-- Check migration history (if using migration tracker)
SELECT * FROM schema_migrations ORDER BY applied_at DESC;

-- Check if expected tables exist
\dt disco_*
```

**Fix:**
```bash
# Apply missing migrations
psql "postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres" \
  -f database/migrations/XXX_missing_migration.sql
```

---

## Authentication Issues

### JWT validation failures

**Symptoms:**
- 401 errors on API calls
- "Invalid token" messages
- Users logged out unexpectedly

**Causes:**

| Cause | Symptom | Fix |
|-------|---------|-----|
| Wrong JWT secret | All tokens fail | Update `SUPABASE_JWT_SECRET` with JWK |
| Token expired | Works then fails | Normal - user re-authenticates |
| Clock skew | Intermittent failures | Sync server time |

**Verify JWT config:**
```bash
# Get current JWK
curl -s "https://[PROJECT_REF].supabase.co/auth/v1/.well-known/jwks.json" | jq '.keys[0]'
```

### Session expiry problems

**Symptoms:**
- Users report frequent logouts
- "Session expired" messages

**Check:**
- Supabase auth settings (session duration)
- Refresh token handling in frontend
- Network issues preventing token refresh

---

## Help System Issues

### Stale help results

**Symptoms:**
- Help returns outdated information
- New docs not appearing in answers

**Fix:**
1. Go to `/admin/help`
2. Click **Reindex Help Docs**
3. Choose **Full reindex**

Or via CLI:
```bash
cd backend
python -m scripts.reindex_help --mode full
```

### Help returns nothing

**Check:**
1. Are docs indexed?
```sql
SELECT COUNT(*) FROM help_documents;
SELECT COUNT(*) FROM help_chunks;
```

2. Is Voyage AI working?
```bash
# Test embedding generation
curl -X POST "https://api.voyageai.com/v1/embeddings" \
  -H "Authorization: Bearer $VOYAGE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"input": "test", "model": "voyage-2"}'
```

**Fix:**
- Reindex if tables are empty
- Check Voyage API key if embeddings fail
- Review backend logs for specific errors

---

## Service Health Checks

### Backend health endpoint

```bash
curl https://your-backend.railway.app/health
```

Should return:
```json
{
  "status": "healthy",
  "database": "connected",
  "services": {
    "anthropic": "ok",
    "voyage": "ok",
    "supabase": "ok"
  }
}
```

### Checking logs

**Railway:**
```bash
railway logs --tail
```

**Local:**
```bash
tail -f backend/logs/app.log
```

**Key log patterns to watch:**
- `ERROR` - Immediate issues
- `WARN` - Potential problems
- `timeout` - Performance issues
- `rate limit` - API throttling

---

## Getting Support

When escalating issues, gather:

1. **Error messages** - exact text, not paraphrased
2. **Timestamps** - when did it start?
3. **Reproduction steps** - how to trigger the issue
4. **Affected scope** - one user? all users? specific feature?
5. **Recent changes** - deployments, config changes, etc.

Check:
- Backend logs for the timeframe
- Supabase logs for database issues
- Railway logs for deployment problems

---

## Common Quick Fixes

| Issue | Quick Fix |
|-------|-----------|
| Everything slow | Restart backend service |
| Auth broken | Verify JWK is current |
| Agents generic | Reprocess document embeddings |
| Help outdated | Reindex help docs |
| Sync stuck | Re-authenticate integration |
| DB errors | Check Supabase dashboard |

---

## What's Next?

- [Document Management](./03-document-management.md) - Managing user documents
- [Help System](./04-help-system.md) - Help system administration
- [Agent Management](./01-agents.md) - Managing agent behavior
