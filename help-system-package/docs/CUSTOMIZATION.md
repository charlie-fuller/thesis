# Help System Customization Guide

How to customize the help system for your specific needs.

## Common Customizations

### 1. Change Sidebar Position

Move help chat from right to left side:

**In `frontend/components/HelpChat.tsx`:**

```typescript
// Change from:
<div className="fixed right-0 top-0 h-screen w-[400px]">

// To:
<div className="fixed left-0 top-0 h-screen w-[400px]">
```

### 2. Make Sidebar Collapsible

Add expand/collapse toggle:

```typescript
const [isExpanded, setIsExpanded] = useState(false)

return (
  <div className={`fixed right-0 top-0 h-screen transition-transform ${
    isExpanded ? 'w-[400px]' : 'w-12'
  }`}>
    {/* Toggle button */}
    <button
      onClick={() => setIsExpanded(!isExpanded)}
      className="absolute left-2 top-2 p-2"
    >
      {isExpanded ? '→' : '←'}
    </button>

    {/* Content only shows when expanded */}
    {isExpanded && (
      <div className="p-4">
        {/* Existing chat UI */}
      </div>
    )}
  </div>
)
```

### 3. Change Brand Colors

**Edit `frontend/components/HelpChat.tsx`:**

```typescript
// Update all color classes to match your brand
<div className="bg-[#YOUR_PRIMARY_COLOR]">  {/* Sidebar background */}
<div className="bg-[#YOUR_ACCENT_COLOR]">   {/* User messages */}
<div className="text-[#YOUR_TEXT_COLOR]">   {/* Text color */}
```

### 4. Add Welcome Message

Show a greeting when chat opens:

**In `frontend/contexts/HelpChatContext.tsx`:**

```typescript
const [messages, setMessages] = useState<HelpMessage[]>([
  {
    id: 'welcome',
    role: 'assistant',
    content: 'Hi! I\'m here to help you with [Your Platform]. What can I help you with today?',
    timestamp: new Date().toISOString(),
    sources: []
  }
])
```

### 5. Customize Message Timestamps

Show relative time instead of full timestamp:

```typescript
// Add this helper function
const formatRelativeTime = (timestamp: string) => {
  const now = new Date()
  const messageTime = new Date(timestamp)
  const diffMs = now.getTime() - messageTime.getTime()
  const diffMins = Math.floor(diffMs / 60000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`
  return `${Math.floor(diffMins / 1440)}d ago`
}

// Use in message display
<span className="text-xs text-gray-400">
  {formatRelativeTime(message.timestamp)}
</span>
```

## Advanced Customizations

### 6. Add Suggested Questions

Show clickable question suggestions:

**In `frontend/components/HelpChat.tsx`:**

```typescript
const SUGGESTED_QUESTIONS = [
  "How do I get started?",
  "How do I reset my password?",
  "What are the pricing plans?",
  "How do I contact support?"
]

// Add before the input field
{messages.length <= 1 && (
  <div className="p-4 space-y-2">
    <p className="text-sm text-gray-400">Try asking:</p>
    {SUGGESTED_QUESTIONS.map((question, i) => (
      <button
        key={i}
        onClick={() => sendMessage(question)}
        className="block w-full text-left p-2 text-sm bg-gray-700 hover:bg-gray-600 rounded"
      >
        {question}
      </button>
    ))}
  </div>
)}
```

### 7. Add Typing Indicator

Show "thinking" animation while waiting for response:

```typescript
const [isTyping, setIsTyping] = useState(false)

// In sendMessage function:
const sendMessage = async (content: string) => {
  setIsTyping(true)
  try {
    // ... existing code ...
  } finally {
    setIsTyping(false)
  }
}

// In message display area:
{isTyping && (
  <div className="flex items-center gap-2 text-gray-400">
    <div className="flex gap-1">
      <span className="animate-bounce">●</span>
      <span className="animate-bounce delay-100">●</span>
      <span className="animate-bounce delay-200">●</span>
    </div>
    <span className="text-sm">Thinking...</span>
  </div>
)}
```

### 8. Add Message Reactions

Let users react to messages:

```typescript
// Add to HelpMessage interface
interface HelpMessage {
  // ... existing fields ...
  reaction?: 'helpful' | 'not-helpful' | 'needs-improvement'
}

// Add reaction buttons
<div className="flex gap-2 mt-2">
  <button onClick={() => reactToMessage(message.id, 'helpful')}>
    Helpful
  </button>
  <button onClick={() => reactToMessage(message.id, 'not-helpful')}>
    Not helpful
  </button>
</div>
```

### 9. Export Conversation

Let users download conversation history:

```typescript
const exportConversation = () => {
  const conversationText = messages.map(m =>
    `[${m.role}] ${m.content}\n\n`
  ).join('')

  const blob = new Blob([conversationText], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `help-conversation-${new Date().toISOString()}.txt`
  a.click()
  URL.revokeObjectURL(url)
}

// Add export button in UI
<button onClick={exportConversation}>
  Export Conversation
</button>
```

### 10. Add Search Within Conversation

Filter messages in current conversation:

```typescript
const [searchQuery, setSearchQuery] = useState('')

const filteredMessages = messages.filter(m =>
  m.content.toLowerCase().includes(searchQuery.toLowerCase())
)

// Add search input
<input
  type="text"
  placeholder="Search this conversation..."
  value={searchQuery}
  onChange={(e) => setSearchQuery(e.target.value)}
  className="w-full p-2 bg-gray-700 rounded"
/>

// Display filteredMessages instead of messages
{filteredMessages.map(message => (
  // ... message display ...
))}
```

## Backend Customizations

### 11. Add Custom Metadata to Documents

Track additional document metadata:

**In `backend/scripts/index_help_docs.py`:**

```python
# Add custom metadata extraction
def extract_custom_metadata(content: str) -> dict:
    """Extract custom metadata from markdown frontmatter"""
    import yaml

    # Check for YAML frontmatter
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            frontmatter = yaml.safe_load(parts[1])
            return {
                'author': frontmatter.get('author'),
                'last_updated': frontmatter.get('updated'),
                'tags': frontmatter.get('tags', []),
                'difficulty': frontmatter.get('difficulty', 'beginner')
            }
    return {}

# Update chunk creation
chunk_metadata = {
    'section': heading_context,
    'chunk_index': chunk_index,
    **extract_custom_metadata(content)  # Add custom metadata
}
```

**Example document with frontmatter:**

```markdown
---
author: Jane Doe
updated: 2025-01-15
tags: [getting-started, beginner]
difficulty: easy
---

# Getting Started

Your documentation content here...
```

### 12. Filter Results by User Preferences

Personalize search based on user settings:

**In `backend/helpers/help_search.py`:**

```python
async def search_help_chunks(
    query: str,
    user_role: str,
    user_preferences: dict = None,  # Add preferences
    top_k: int = 3
):
    # Apply preference filters
    filters = []

    if user_preferences:
        # Filter by difficulty if set
        if 'difficulty' in user_preferences:
            filters.append(
                f"metadata->>'difficulty' = '{user_preferences['difficulty']}'"
            )

        # Filter by tags if set
        if 'preferred_tags' in user_preferences:
            tags = "','".join(user_preferences['preferred_tags'])
            filters.append(
                f"metadata->'tags' ?| array['{tags}']"
            )

    # Add to RPC call
    filter_clause = ' AND '.join(filters) if filters else '1=1'

    # ... rest of search logic with filters applied
```

### 13. Add Multi-Language Support

Support documentation in multiple languages:

**Structure:**
```
docs/help/
├── en/
│   ├── admin/
│   └── user/
├── es/
│   ├── admin/
│   └── user/
└── fr/
    ├── admin/
    └── user/
```

**In `backend/scripts/index_help_docs.py`:**

```python
def detect_language(file_path: str) -> str:
    """Detect language from file path"""
    parts = file_path.split('/')
    if len(parts) > 2 and parts[2] in ['en', 'es', 'fr', 'de']:
        return parts[2]
    return 'en'  # Default language

# Add language to document metadata
document_data = {
    'title': title,
    'file_path': relative_path,
    'category': category,
    'language': detect_language(relative_path),  # Add language
    # ... rest of fields
}
```

**Filter by user language:**

```python
# In search function
async def search_help_chunks(
    query: str,
    user_role: str,
    user_language: str = 'en',
    top_k: int = 3
):
    # Add language filter to RPC call
    result = supabase.rpc(
        'match_help_chunks',
        {
            'query_embedding': query_embedding,
            'match_count': top_k,
            'user_role': user_role,
            'user_language': user_language  # Add this
        }
    )
```

**Update RPC function:**

```sql
CREATE OR REPLACE FUNCTION match_help_chunks(
  query_embedding vector(1536),
  match_count int,
  user_role text,
  user_language text DEFAULT 'en'  -- Add this parameter
)
RETURNS TABLE (
  id uuid,
  content text,
  heading_context text,
  document_id uuid,
  document_title text,
  file_path text,
  similarity float
)
LANGUAGE sql STABLE
AS $$
  SELECT
    hc.id,
    hc.content,
    hc.heading_context,
    hc.document_id,
    hd.title AS document_title,
    hd.file_path,
    1 - (hc.embedding <=> query_embedding) AS similarity
  FROM help_chunks hc
  JOIN help_documents hd ON hc.document_id = hd.id
  WHERE
    hc.role_access @> ARRAY[user_role]::text[]
    AND hd.metadata->>'language' = user_language  -- Add language filter
  ORDER BY hc.embedding <=> query_embedding
  LIMIT match_count;
$$;
```

### 14. Add Conversation Context Window

Limit how much conversation history is sent to Claude:

**In `backend/api/routes/help_chat.py`:**

```python
# Instead of sending all messages
MAX_CONTEXT_MESSAGES = 10  # Only send last 10 messages

# Get recent messages only
recent_messages = conversation_messages[-MAX_CONTEXT_MESSAGES:]

response = anthropic_client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=4096,
    system=system_prompt,
    messages=recent_messages  # Use recent_messages instead
)
```

This reduces costs and keeps context focused on recent discussion.

### 15. Add Confidence Scores

Show how confident the AI is in its answer:

**In `backend/api/routes/help_chat.py`:**

```python
# After getting search results
avg_similarity = sum(r['similarity'] for r in results) / len(results)

# Add to response metadata
response_data = {
    'conversation_id': conversation_id,
    'message_id': assistant_message_id,
    'response': ai_response,
    'sources': sources,
    'confidence': 'high' if avg_similarity > 0.8 else 'medium' if avg_similarity > 0.6 else 'low'
}
```

**Display in frontend:**

```typescript
{message.confidence === 'low' && (
  <div className="mt-2 p-2 bg-yellow-900/20 border border-yellow-600 rounded text-sm">
    Warning: I'm not very confident about this answer. You may want to contact support.
  </div>
)}
```

### 16. Add Usage Analytics

Track which documents are most helpful:

```python
# Add analytics table
"""
CREATE TABLE help_analytics (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id uuid REFERENCES help_documents(id),
  event_type text,  -- 'view', 'helpful', 'not_helpful'
  user_id uuid REFERENCES users(id),
  created_at timestamptz DEFAULT now()
);
"""

# Track when document is cited
async def track_document_view(document_id: uuid, user_id: uuid):
    supabase.table('help_analytics').insert({
        'document_id': document_id,
        'event_type': 'view',
        'user_id': user_id
    }).execute()

# Analytics query
"""
SELECT
  d.title,
  COUNT(CASE WHEN a.event_type = 'helpful' THEN 1 END) as helpful_count,
  COUNT(CASE WHEN a.event_type = 'not_helpful' THEN 1 END) as not_helpful_count,
  COUNT(CASE WHEN a.event_type = 'view' THEN 1 END) as view_count
FROM help_documents d
LEFT JOIN help_analytics a ON d.id = a.document_id
GROUP BY d.id, d.title
ORDER BY helpful_count DESC;
"""
```

## UI/UX Customizations

### 17. Add Dark/Light Mode Toggle

```typescript
const [theme, setTheme] = useState<'dark' | 'light'>('dark')

const themeClasses = theme === 'dark'
  ? 'bg-gray-900 text-white'
  : 'bg-white text-gray-900'

<div className={themeClasses}>
  <button onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
    {theme === 'dark' ? 'Light Mode' : 'Dark Mode'}
  </button>
  {/* Rest of chat UI */}
</div>
```

### 18. Add Keyboard Shortcuts

```typescript
useEffect(() => {
  const handleKeyDown = (e: KeyboardEvent) => {
    // Cmd/Ctrl + K to focus search
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault()
      inputRef.current?.focus()
    }

    // Escape to close/minimize
    if (e.key === 'Escape') {
      setIsExpanded(false)
    }
  }

  window.addEventListener('keydown', handleKeyDown)
  return () => window.removeEventListener('keydown', handleKeyDown)
}, [])
```

### 19. Add Attachments

Let users attach screenshots:

```typescript
const [attachments, setAttachments] = useState<File[]>([])

const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
  if (e.target.files) {
    setAttachments(Array.from(e.target.files))
  }
}

// Upload to storage and include URLs in message
const uploadAttachments = async (files: File[]) => {
  const urls = await Promise.all(
    files.map(file => {
      // Upload to Supabase Storage or S3
      const formData = new FormData()
      formData.append('file', file)
      return fetch('/api/upload', { method: 'POST', body: formData })
        .then(r => r.json())
        .then(data => data.url)
    })
  )
  return urls
}

// Include in message
const sendMessage = async (content: string) => {
  const attachmentUrls = await uploadAttachments(attachments)
  const messageWithAttachments = `${content}\n\nAttachments: ${attachmentUrls.join(', ')}`
  // ... send message
}
```

### 20. Add Quick Actions

Pre-defined buttons for common tasks:

```typescript
const QUICK_ACTIONS = [
  { label: 'Reset Password', query: 'How do I reset my password?' },
  { label: 'Billing Info', query: 'Where can I update my billing information?' },
  { label: 'Contact Support', query: 'How do I contact support?' }
]

<div className="flex gap-2 p-2 border-t">
  {QUICK_ACTIONS.map(action => (
    <button
      key={action.label}
      onClick={() => sendMessage(action.query)}
      className="px-3 py-1 bg-blue-600 rounded text-sm hover:bg-blue-700"
    >
      {action.label}
    </button>
  ))}
</div>
```

## Summary

The help system is highly customizable. Common customization points:

- **UI**: Colors, position, size, animations
- **Behavior**: Auto-scroll, typing indicators, suggestions
- **Search**: Number of results, confidence scores, filters
- **Content**: Metadata, multi-language, categorization
- **Analytics**: Usage tracking, feedback analysis
- **Performance**: Context windows, caching, batching

Start with small changes and test thoroughly before deploying to production.
