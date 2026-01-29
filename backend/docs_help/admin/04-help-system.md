# Help System Administration

The help system uses RAG (Retrieval-Augmented Generation) to provide contextual answers. This guide covers how it works and how to maintain it.

---

## How Help Works

When a user asks for help:

1. Query is embedded using Voyage AI
2. Similar chunks are retrieved from the help index
3. Retrieved content is passed to the LLM as context
4. LLM generates a response grounded in help documentation

The system searches both user and admin documentation, filtering by the user's access level.

---

## Documentation Structure

Help docs live in `/docs/help/`:

```
/docs/help/
  README.md           # Index and quick links
  /user/              # End-user documentation
    00-quick-start.md
    01-agents.md
    ...
  /admin/             # Admin documentation
    00-getting-started.md
    01-agents.md
    ...
```

Files are numbered for ordering. The naming convention is `NN-topic.md`.

---

## How Indexing Works

Documents are processed into chunks:

1. **Scanning** - Files are discovered in `/docs/help/`
2. **Parsing** - Markdown is parsed, sections extracted
3. **Chunking** - Content split into ~500 token chunks with overlap
4. **Embedding** - Each chunk gets a Voyage AI embedding
5. **Storage** - Chunks and embeddings stored in Supabase

Two tables store the index:
- `help_documents` - Document metadata (path, title, last indexed)
- `help_chunks` - Individual chunks with embeddings

---

## Triggering a Reindex

### From the Admin UI

1. Go to `/admin/help`
2. Click **Reindex Help Docs**
3. Choose:
   - **Scan for new** - Only process new/changed files
   - **Full reindex** - Reprocess everything

### From Command Line (Local)

```bash
cd backend
python -m scripts.reindex_help --mode scan  # New/changed only
python -m scripts.reindex_help --mode full  # Everything
```

### Via Railway (Production)

```bash
railway run python -m scripts.reindex_help --mode full
```

Or trigger via webhook if configured:
```bash
curl -X POST https://your-backend.railway.app/api/admin/help/reindex \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

## When to Reindex

**Reindex after:**
- Adding new help documentation
- Updating existing documentation
- Changing the chunking strategy
- Upgrading the embedding model

**Scan for new after:**
- Adding a single new file
- Minor updates to existing files

Full reindex takes longer but ensures consistency.

---

## Verifying the Index

Check index health:

```sql
-- Document count
SELECT COUNT(*) FROM help_documents;

-- Chunk count
SELECT COUNT(*) FROM help_chunks;

-- Documents by folder
SELECT
  CASE
    WHEN path LIKE '%/user/%' THEN 'user'
    WHEN path LIKE '%/admin/%' THEN 'admin'
    ELSE 'other'
  END as folder,
  COUNT(*)
FROM help_documents
GROUP BY folder;

-- Recently indexed
SELECT path, indexed_at
FROM help_documents
ORDER BY indexed_at DESC
LIMIT 10;
```

---

## Troubleshooting the Help System

### Help returns irrelevant results
- Check if documents are indexed (`help_documents` table)
- Verify chunks exist (`help_chunks` table)
- Try a full reindex

### Help returns stale content
- Document was updated but not reindexed
- Run scan or full reindex

### Help returns nothing
- Index may be empty
- Check Voyage AI connectivity
- Verify embedding generation isn't failing

### Specific document not found
```sql
SELECT * FROM help_documents WHERE path LIKE '%topic%';
```
If missing, trigger reindex.

---

## Chunk Quality

Good chunks have:
- Coherent, self-contained content
- Section headers for context
- Appropriate length (not too short, not too long)

If help answers seem fragmented:
- Check chunk boundaries in `help_chunks`
- Consider adjusting chunk size in indexing config
- Ensure markdown has clear section breaks

---

## Access Control

Help content is filtered by user role:

| Role | Access |
|------|--------|
| User | `/user/` docs only |
| Admin | `/user/` + `/admin/` docs |

This is enforced at query time, not index time. All docs are indexed; filtering happens on retrieval.

---

## Monitoring

Track help system usage:

- **Query volume** - How often help is invoked
- **Retrieval quality** - Are relevant chunks being found?
- **Response ratings** - If feedback is collected

Logs show:
- Queries that returned no results
- Slow retrieval times
- Embedding failures

---

---

## Testing the Help System

E2E tests for the help system are defined in `backend/tests/e2e_browser_tests.py`. These tests use Chrome DevTools MCP.

### Help System Test Scenarios

| Test ID | Description |
|---------|-------------|
| `help_panel_open` | Open help panel from navigation |
| `help_panel_close` | Close help panel cleanly |
| `help_search_agents` | Search for agent-related help |
| `help_search_disco` | Search for DISCo workflow help |
| `help_search_discovery_inbox` | Search for Discovery Inbox help |
| `help_search_no_results` | Handle empty search results |
| `help_navigate_to_doc` | Navigate to full documentation |
| `help_contextual` | Contextual help based on current page |

### Running Help Tests

```bash
# View available help tests
cd backend
.venv/bin/python -c "from tests.e2e_browser_tests import get_help_tests; print(list(get_help_tests().keys()))"
```

Then execute via Claude Code with Chrome DevTools MCP tools.

### Top 50 Test Queries

These queries should return relevant, accurate help:

**Agent Questions:**
1. "How many agents are there?"
2. "Which agent should I use for security questions?"
3. "How do I use @mentions?"
4. "What's the difference between agents?"
5. "How does auto mode work?"

**Chat Questions:**
6. "How do I send a message?"
7. "Can I use multiple agents at once?"
8. "How do I start a new conversation?"
9. "Do conversations persist?"
10. "What's Smart Brevity?"

**Meeting Room Questions:**
11. "How do I create a meeting room?"
12. "What is autonomous mode?"
13. "How many agents can be in a meeting?"
14. "How do I get a meeting summary?"
15. "What's the difference between chat and meeting rooms?"

**Knowledge Base Questions:**
16. "What file types can I upload?"
17. "How does auto-classification work?"
18. "Can I connect Google Drive?"
19. "How do I sync my vault?"
20. "Why aren't agents using my documents?"

**Task Questions:**
21. "How do I create a task?"
22. "How does the kanban board work?"
23. "Can I drag tasks between columns?"
24. "How do I assign tasks to stakeholders?"
25. "What's the difference between tasks and projects?"

**Project Questions:**
26. "How do I create a project?"
27. "What determines the tier?"
28. "How are scores calculated?"
29. "Can I filter by tier?"
30. "How do I track project progress?"

**DISCo Questions:**
31. "What is DISCo?"
32. "How do I create an initiative?"
33. "What are the workflow stages?"
34. "What does GO/NO-GO mean?"
35. "How do I run a DISCo agent?"
36. "What is Triage?"
37. "How do I approve bundles?"
38. "What's the difference between Discovery and Intelligence?"
39. "How do I share an initiative?"
40. "What is the PRD Generator?"

**Discovery Inbox Questions:**
41. "What is Discovery Inbox?"
42. "Where do I find the inbox?"
43. "What are candidates?"
44. "How do I accept or skip items?"
45. "What does high confidence mean?"
46. "How does duplicate detection work?"
47. "When does scanning happen?"
48. "Do candidates expire?"
49. "Can I bulk process candidates?"
50. "How do I improve extraction quality?"

### Evaluating Help Responses

When testing, verify each response has:

| Criteria | Check |
|----------|-------|
| **Accuracy** | Information matches documentation |
| **Completeness** | All relevant steps included |
| **UI Labels** | Uses exact UI terminology (bold **Navigation**, `button names`) |
| **Clarity** | Easy to follow, no jargon |
| **Links** | References other relevant docs when appropriate |

---

## What's Next?

- [Troubleshooting](./05-troubleshooting.md) - System-wide troubleshooting
- [Document Management](./03-document-management.md) - Managing user documents
