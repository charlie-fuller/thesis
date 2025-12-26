# Help System Configuration Guide

Complete reference for all configuration options in the help system.

## Environment Variables

### Backend Required Variables

```env
# Anthropic API - Required for Claude AI responses
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Voyage AI - Required for embeddings generation
VOYAGE_API_KEY=pa-xxxxx

# Supabase - Required for database and auth (should already exist)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJxxxxx...
SUPABASE_JWT_SECRET=your-jwt-secret

# Webhook Auth - Required for auto-reindex (optional if not using GitHub Actions)
HELP_REINDEX_API_KEY=your-secure-random-key
```

### Frontend Required Variables

```env
# Supabase - Should already exist in your app
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJxxxxx...

# Backend API - Should already exist in your app
NEXT_PUBLIC_API_URL=https://your-backend-api.com
```

### Getting API Keys

**Anthropic API Key**:
1. Go to https://console.anthropic.com
2. Sign up or log in
3. Navigate to API Keys
4. Create a new key
5. Add billing information (required for API access)

**Voyage AI API Key**:
1. Go to https://www.voyageai.com
2. Sign up for an account
3. Navigate to API Keys
4. Create a new key
5. Free tier includes 100M tokens (~$120 value)

**Generate Webhook Key**:
```bash
# Generate a secure random key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Or use openssl
openssl rand -base64 32
```

## Indexing Configuration

Edit `backend/scripts/index_help_docs.py` to customize indexing behavior.

### Chunk Size Settings

```python
# Number of characters per chunk
CHUNK_SIZE = 1000  # Default: 1000

# Overlap between chunks (for context continuity)
CHUNK_OVERLAP = 200  # Default: 200
```

**When to adjust**:
- **Smaller chunks (500-800)**: Better for precise, specific answers
- **Larger chunks (1500-2000)**: Better for comprehensive context
- **More overlap (300-400)**: Better continuity, uses more tokens
- **Less overlap (100-150)**: More unique content, less redundancy

### Role Access Mapping

```python
# Define which roles can access which document categories
ROLE_ACCESS_MAP = {
    'admin': ['admin', 'superadmin', 'owner'],
    'user': ['user', 'admin', 'superadmin', 'owner'],
    'system': ['admin', 'superadmin'],
    'technical': ['admin', 'superadmin', 'developer']
}
```

**How it works**:
- Files in `docs/help/admin/` get `role_access = ['admin', 'superadmin', 'owner']`
- Users with role `'user'` only see chunks with `'user'` in `role_access` array
- RLS policies enforce this at database level

**Customizing for your app**:
```python
# Example: Add a 'manager' role
ROLE_ACCESS_MAP = {
    'admin': ['admin', 'superadmin'],
    'user': ['user', 'manager', 'admin'],
    'manager': ['manager', 'admin'],  # New category
    'system': ['admin', 'superadmin']
}
```

Then create `docs/help/manager/` directory with manager-specific docs.

### Document Discovery Path

```python
# Where to find help documentation
HELP_DOCS_PATH = 'docs/help'
```

Change this if you want documentation in a different location:
```python
HELP_DOCS_PATH = 'documentation/user-help'  # Custom path
```

## Search Configuration

Edit `backend/api/routes/help_chat.py` to adjust search behavior.

### Number of Sources Retrieved

```python
# In /api/help/ask endpoint
top_k: int = 3  # Default: retrieve 3 most relevant chunks
```

**Trade-offs**:
- **More sources (5-10)**: More comprehensive context, higher costs, slower
- **Fewer sources (1-2)**: Faster, cheaper, but may miss relevant info
- **Recommended**: 3-5 for most use cases

Change default in endpoint:
```python
@router.post("/ask")
async def ask_help(
    request: HelpAskRequest,
    top_k: int = 5,  # Change from 3 to 5
    current_user: dict = Depends(get_current_user)
):
```

### Vector Search Index

The IVFFlat index is configured in migration:
```sql
CREATE INDEX help_chunks_embedding_idx ON help_chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

**Tuning `lists` parameter**:
- **Small datasets (<10k chunks)**: `lists = 100` (default)
- **Medium datasets (10k-100k)**: `lists = 1000`
- **Large datasets (>100k)**: `lists = 5000`

To change, edit migration file before running or recreate index:
```sql
DROP INDEX help_chunks_embedding_idx;
CREATE INDEX help_chunks_embedding_idx ON help_chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 1000);  -- Adjust this number
```

## AI Model Configuration

### Claude Model Selection

Edit `backend/api/routes/help_chat.py`:

```python
response = anthropic_client.messages.create(
    model="claude-sonnet-4-20250514",  # Change this
    max_tokens=4096,
    system=system_prompt,
    messages=conversation_messages
)
```

**Available models** (as of January 2025):
- `claude-sonnet-4-20250514` - Best balance (default, $3/$15 per M tokens)
- `claude-opus-4-20241129` - Highest quality ($15/$75 per M tokens)
- `claude-haiku-4-20250514` - Fastest, cheapest ($0.25/$1.25 per M tokens)

**When to use each**:
- **Sonnet 4** (default): Best for most help queries, good quality + speed
- **Opus 4**: Very complex technical questions, maximum accuracy needed
- **Haiku 4**: Simple FAQ-style questions, high volume, cost-conscious

### System Prompt Customization

Edit `backend/helpers/help_search.py`:

```python
def build_help_system_prompt(context: str) -> str:
    return f"""You are a helpful assistant for [YOUR PLATFORM NAME].

Your role is to answer questions about using the platform based on the documentation provided.

Guidelines:
- Only answer based on the provided documentation context
- If information is not in the context, say so clearly
- Be concise but comprehensive
- Use markdown formatting for better readability
- Include specific examples when available
- If user needs to take action, provide clear step-by-step instructions

Documentation context:
{context}

Remember to:
1. Focus on the specific question asked
2. Reference the documentation sections you're using
3. Suggest related topics when helpful
4. Escalate to support for billing or account issues
"""
```

### Max Response Tokens

```python
max_tokens=4096  # Maximum response length
```

**Adjust based on needs**:
- **Short answers (1024-2048)**: FAQ-style, simple questions
- **Medium answers (4096)**: Default, handles most questions
- **Long answers (8192)**: Complex troubleshooting, tutorials

## Rate Limiting

Edit `backend/api/routes/help_chat.py` to adjust rate limits.

### Current Limits

```python
@limiter.limit("30/minute")  # Ask endpoint
@limiter.limit("60/minute")  # List conversations, search
@limiter.limit("100/minute")  # Feedback
@limiter.limit("1/hour")  # Reindex endpoints
```

### Customizing Limits

Change decorator values:
```python
@limiter.limit("60/minute")  # Increase from 30 to 60
async def ask_help(...):
```

Or make role-based:
```python
@router.post("/ask")
@limiter.limit("30/minute")  # Default for users
@limiter.limit("100/minute")  # Override for admins
async def ask_help(
    request: HelpAskRequest,
    current_user: dict = Depends(get_current_user)
):
    # Role-based limit logic
    if current_user['role'] in ['admin', 'superadmin']:
        # Higher limit applied via decorator
        pass
```

## Frontend UI Configuration

### Chat Sidebar Styling

Edit `frontend/components/HelpChat.tsx`:

```typescript
// Sidebar width
<div className="w-[400px]">  {/* Change width here */}

// Colors
className="bg-gray-900"  {/* Background color */}
className="text-white"   {/* Text color */}

// Position
className="fixed right-0"  {/* Change to left-0 for left sidebar */}
```

### Message Styling

```typescript
// User message bubble
className="bg-blue-600 text-white"  {/* User message colors */}

// Assistant message bubble
className="bg-gray-700 text-gray-100"  {/* Assistant colors */}

// Source citations
className="text-blue-400"  {/* Citation link color */}
```

### Auto-Scroll Behavior

```typescript
// Enable/disable auto-scroll to new messages
useEffect(() => {
  if (messagesEndRef.current) {
    messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
  }
}, [messages])  // Scrolls when messages change
```

Remove this effect to disable auto-scroll.

### Input Placeholder

```typescript
placeholder="Ask a question about using the platform..."  {/* Customize */}
```

## Database Configuration

### Connection Pooling

For high-traffic deployments, configure connection pooling in `backend/helpers/supabase_helpers.py`:

```python
from supabase import create_client, Client

supabase_client = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY,
    options={
        'schema': 'public',
        'auto_refresh_token': True,
        'persist_session': True,
        'detect_session_in_url': False,
        'headers': {},
        'realtime': {'enabled': False},
        'connection_pool': {
            'max_size': 10,  # Max concurrent connections
            'timeout': 30    # Connection timeout in seconds
        }
    }
)
```

### Row Level Security Policies

The system includes RLS policies for security. To customize, edit the migration file or run:

```sql
-- Custom policy: managers can see manager and user docs
CREATE POLICY "Managers see manager docs"
ON help_chunks FOR SELECT
TO authenticated
USING (
  auth.jwt() ->> 'role' = 'manager'
  AND role_access @> ARRAY['manager']::text[]
);
```

## Performance Tuning

### Embeddings Batch Size

Edit `backend/services/embeddings.py`:

```python
def create_embeddings(
    texts: List[str],
    input_type: str = "document",
    batch_size: int = 128  # Adjust this
):
```

**Tuning**:
- **Larger batches (256-512)**: Faster indexing, more memory
- **Smaller batches (32-64)**: Safer for limited resources

### Vector Index Maintenance

Periodically vacuum and analyze for optimal performance:

```sql
-- Run after large documentation updates
VACUUM ANALYZE help_chunks;

-- Reindex if search becomes slow
REINDEX INDEX help_chunks_embedding_idx;
```

### Caching (Advanced)

Add Redis caching for frequently asked questions (requires Redis setup):

```python
import redis
from functools import lru_cache

redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Cache search results for 1 hour
@lru_cache(maxsize=1000)
def cached_search(query_hash: str, user_role: str, top_k: int):
    cache_key = f"help_search:{query_hash}:{user_role}:{top_k}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    # ... perform search ...
    redis_client.setex(cache_key, 3600, json.dumps(results))
    return results
```

## Monitoring Configuration

### Logging

The system logs to stdout/stderr. Configure log level in `backend/main.py`:

```python
import logging

logging.basicConfig(
    level=logging.INFO,  # Change to DEBUG for verbose logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Analytics Queries

Track usage with SQL queries:

```sql
-- Most asked questions (by conversation titles)
SELECT title, COUNT(*) as count
FROM help_conversations
GROUP BY title
ORDER BY count DESC
LIMIT 20;

-- Feedback statistics
SELECT
  SUM(CASE WHEN feedback = 1 THEN 1 ELSE 0 END) as thumbs_up,
  SUM(CASE WHEN feedback = -1 THEN 1 ELSE 0 END) as thumbs_down,
  COUNT(*) as total_feedback
FROM help_messages
WHERE feedback IS NOT NULL;

-- Most referenced documents
SELECT
  d.title,
  COUNT(*) as reference_count
FROM help_messages m
CROSS JOIN LATERAL jsonb_array_elements(m.sources) as source
JOIN help_documents d ON d.id = (source->>'document_id')::uuid
WHERE m.role = 'assistant'
GROUP BY d.title
ORDER BY reference_count DESC
LIMIT 20;
```

## Cost Optimization

### Reducing API Costs

1. **Use cheaper model**: Switch to `claude-haiku-4-20250514`
2. **Reduce top_k**: Fewer sources = less context = lower costs
3. **Smaller max_tokens**: Set to 2048 instead of 4096
4. **Cache common queries**: Implement Redis caching
5. **Rate limiting**: Prevent abuse with strict limits

### Estimating Costs

**Per query costs** (with default settings):
- Embeddings: ~500 tokens × $0.0001/1k = $0.00005
- Claude Sonnet 4: ~2k input + 1k output × ($3+$15)/2M = $0.003
- **Total**: ~$0.003 per query

**Monthly estimates**:
- 1,000 queries: ~$3
- 10,000 queries: ~$30
- 100,000 queries: ~$300

## Security Configuration

### CORS Settings

If your frontend and backend are on different domains, configure CORS in `backend/main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend.com"],  # Specific domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### API Key Rotation

Regularly rotate webhook API key:

```bash
# Generate new key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Update in:
# 1. Backend .env: HELP_REINDEX_API_KEY
# 2. GitHub Secrets: REINDEX_API_KEY
# 3. Restart backend service
```

## Backup & Recovery

### Backup Help Data

```bash
# Backup help tables
pg_dump $DATABASE_URL \
  --table=help_documents \
  --table=help_chunks \
  --table=help_conversations \
  --table=help_messages \
  > help_system_backup.sql

# Restore
psql $DATABASE_URL < help_system_backup.sql
```

### Disaster Recovery

If embeddings are lost, reindex:

```bash
# Clear existing data
psql $DATABASE_URL -c "TRUNCATE help_chunks, help_documents CASCADE;"

# Reindex all documentation
python backend/scripts/index_help_docs.py
```

## Summary of Key Files

| Configuration Item | File Location | What to Edit |
|-------------------|---------------|--------------|
| Chunk size | `backend/scripts/index_help_docs.py` | `CHUNK_SIZE`, `CHUNK_OVERLAP` |
| Role access | `backend/scripts/index_help_docs.py` | `ROLE_ACCESS_MAP` |
| Search results | `backend/api/routes/help_chat.py` | `top_k` parameter |
| AI model | `backend/api/routes/help_chat.py` | `model` in `anthropic_client.messages.create()` |
| System prompt | `backend/helpers/help_search.py` | `build_help_system_prompt()` function |
| Rate limits | `backend/api/routes/help_chat.py` | `@limiter.limit()` decorators |
| UI styling | `frontend/components/HelpChat.tsx` | className attributes |
| Sidebar width | `frontend/components/HelpChat.tsx` | `w-[400px]` |
| Embeddings | `backend/services/embeddings.py` | `batch_size`, model name |
