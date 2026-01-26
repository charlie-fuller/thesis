# Thesis - Multi-Agent GenAI Strategy Platform

## Memory Protocol (IMPORTANT)

### Session Start
Query Mem0 for recent context:
```
query: "recent decisions, issues, and context"
filters: {"repo": "thesis"}
```

### During Session
Save to Mem0 when:
- Significant decision made (architecture, approach, library)
- Tricky bug solved (cause and fix)
- User states preference or convention
- TODO identified for future sessions

### When Saving/Querying
- **Save**: `metadata: {"repo": "thesis"}`
- **Query**: `filters: {"repo": "thesis"}`

## Project Overview

Multi-agent platform for enterprise GenAI strategy. 21 specialized agents for research, finance, IT/governance, legal, meeting analysis, and more.

**Key features**: Agent chat with @mentions, Knowledge Base with auto-classification, Meeting Rooms with autonomous discussion, Kanban tasks, Opportunities pipeline, Stakeholder tracking, Obsidian sync, DISCo product discovery.

See `/docs/ARCHITECTURE.md` for full agent roster, capabilities, and database schema.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 16, React 19, TypeScript 5, Tailwind CSS 4 |
| Backend | FastAPI (Python 3.12), Uvicorn, Pydantic |
| Database | Supabase (PostgreSQL) with RLS |
| Graph DB | Neo4j Aura |
| AI/ML | Anthropic Claude, Voyage AI embeddings |
| Memory | Mem0 |
| Deployment | Railway (backend), Vercel (frontend) |

## Key Directories

```
/frontend
  /app           - Next.js pages (kb, chat, meeting-room, tasks, opportunities, disco)
  /components    - React components
  /contexts      - AuthContext, ThemeContext

/backend
  /api/routes    - FastAPI endpoints
  /agents        - Agent implementations (21 agents)
  /services      - Business logic
    /disco       - DISCo services (Discovery-Insights-Synthesis-Capabilities)
  /system_instructions - Agent prompts (XML)

/database
  /migrations    - SQL migration scripts

/docs
  ARCHITECTURE.md - Full reference documentation
  AGENT_GUARDRAILS.md - Agent behavior rules
  /testing       - Testing guides
```

## Development Commands

```bash
# Frontend (from /frontend)
npm run dev          # Dev server (localhost:3000)
npm run build        # Production build

# Backend (from /backend)
uvicorn main:app --reload --port 8000
uv run pytest tests/ -v
```

## Code Conventions

- **Frontend**: ESLint + Prettier, functional components, Context API
- **Backend**: Black + Ruff, async/await, Pydantic models
- **Commits**: Conventional commits (fix:, feat:, docs:)
- **No emojis** in documentation or code

## Agent Instructions

Agents use **Gigawatt v4.0 RCCI Framework** with XML structure. All include `shared/smart_brevity.xml` for concise responses (100-150 words max).

**Smart Brevity Format**:
1. The Big Thing (1-2 sentences)
2. Why It Matters (1-2 sentences)
3. Key Details (3-5 bullets)
4. Dig-Deeper Links

**KB Context Rule**: Always prioritize and cite KB content over general knowledge.

**Meeting Room Limits**: 50-100 words per turn, 75 words in autonomous mode.

## Environment Variables

See `/frontend/.env.example` and `/backend/.env.example`.

Key: `SUPABASE_*`, `NEO4J_*`, `ANTHROPIC_API_KEY`, `VOYAGE_API_KEY`, `MEM0_API_KEY`, `DISCO_REPO_PATH`

## Known Issues & Fixes

### Python 3.12 f-strings
Backslashes cannot appear inside f-string expressions `{}`. Pre-compute strings:

```python
# BAD
f"{('Header:\n' + content) if content else 'Empty'}"

# GOOD
header_text = f"Header:\n{content}" if content else "Empty"
f"{header_text}"
```

### Agent Icons (Single Source of Truth)
All agent icons/colors in `/frontend/components/AgentIcon.tsx`. Update there when adding agents.

### FastAPI Route Ordering
Static routes BEFORE parameterized routes:

```python
# GOOD
@router.get("/documents/available")  # Static first
@router.get("/{agent_id}/documents") # Parameterized second
```

### Lucide Icons
No `title` attribute - wrap in `<span>` for tooltips.

### Granola Scanner
- Debug: `GET /api/pipeline/granola/debug`
- Default date cutoff: Jan 5, 2026
- Adjust with `since_date=YYYY-MM-DD` or `days_back=N`
- Empty docs: resync via `POST /api/obsidian/sync/full`

### Supabase Database Migrations
Run migrations directly with psql (not `supabase db push` - it has sync issues):

```bash
# Get project ref from linked project
cat backend/supabase/.temp/project-ref  # e.g., imdavfgreeddxluslsdl

# Connection string format
psql "postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres" -f database/migrations/XXX_migration.sql

# Example (password in Supabase Dashboard > Settings > Database)
psql "postgresql://postgres:[DB_PASSWORD]@db.imdavfgreeddxluslsdl.supabase.co:5432/postgres" -f database/migrations/048_disco_synthesis.sql
```

Notes:
- Members table is `disco_initiative_members` (not `disco_members`)
- Use `\dt disco_*` to list tables
- RLS policies reference `auth.uid()` for row-level security

## Testing

```bash
# From the repo root:
cd backend
uv run pytest tests/test_document_classifier.py tests/test_tasks.py \
  tests/test_opportunities.py tests/test_engagement.py tests/test_agents_new.py -v
```

See `/docs/testing/TESTING_PLAN.md` for full guide.
