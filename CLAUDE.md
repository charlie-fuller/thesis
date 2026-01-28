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

**Key features**: Agent chat with @mentions, Knowledge Base with auto-classification, Meeting Rooms with autonomous discussion, Kanban tasks, Projects pipeline, Stakeholder tracking, Obsidian sync, DISCo product discovery.

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
  /app           - Next.js pages (kb, chat, meeting-room, tasks, projects, disco)
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

# Backend (from /backend) - requires environment setup
uv run pytest tests/ -v
```

### Backend Startup (IMPORTANT)

The backend uses encrypted `.env` (dotenvx) and requires a Supabase JWK for ES256 JWT validation.

**Quick Start:**
```bash
# 1. Get the JWK from Supabase (or 1Password: "Thesis Supabase JWT JWK")
JWK=$(curl -s "https://imdavfgreeddxluslsdl.supabase.co/auth/v1/.well-known/jwks.json" | jq -c '.keys[0]')

# 2. Start backend with dotenvx decryption + JWK override
cd backend
SUPABASE_JWT_SECRET="$JWK" \
DOTENV_PRIVATE_KEY=4980b243281755774eab2a5107d475ceecdeceb0b7aef97e014d9cfcece1c230 \
dotenvx run -f .env -- .venv/bin/python -m uvicorn main:app --reload --port 8000
```

**Why this is needed:**
- Supabase issues ES256 JWTs (not HS256) for user authentication
- The backend needs the JWK public key to verify these tokens
- The `.env` file is encrypted with dotenvx - use `DOTENV_PRIVATE_KEY` to decrypt

**1Password:** The JWK is stored in "Thesis Supabase JWT JWK" in Employee vault.

## Available Tools & Services

Claude has access to these CLIs and services for Thesis development:

### Infrastructure CLIs
| Tool | Usage | Notes |
|------|-------|-------|
| `supabase` | `supabase projects list`, `supabase projects api-keys --project-ref imdavfgreeddxluslsdl` | Linked project: Thesis (imdavfgreeddxluslsdl) |
| `op` (1Password) | `op item get "Thesis Supabase JWT JWK"`, `op item list --vault "Employee"` | Secrets storage |
| `dotenvx` | Decrypt `.env` files with `DOTENV_PRIVATE_KEY` | Private key in backend/.env.keys |
| `railway` | Deploy backend, check logs | MCP server available |
| `gh` (GitHub) | PRs, issues, code search | Full repo access, can push |
| `git` | Commits, branches, push to origin | Main branch: main |

### Browser Automation (Chrome DevTools MCP)
- `take_snapshot` - Get page DOM for element IDs
- `click`, `fill`, `navigate_page` - Interact with pages
- `list_console_messages` - Check for JS errors
- `list_network_requests` - Debug API calls
- Use for testing frontend at localhost:3000

### Supabase Project Info
- **Project Ref:** imdavfgreeddxluslsdl
- **JWKS Endpoint:** `https://imdavfgreeddxluslsdl.supabase.co/auth/v1/.well-known/jwks.json`
- **JWT Algorithm:** ES256 (requires JWK public key, not HMAC secret)

### GitHub
- **Repo:** anthropics/thesis (or charlie.fuller's fork)
- Can create branches, commits, PRs
- Use `gh pr create`, `gh issue list`, etc.

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

### Quick Commands

```bash
# All backend tests (recommended)
cd backend
DOTENV_PRIVATE_KEY=4980b243281755774eab2a5107d475ceecdeceb0b7aef97e014d9cfcece1c230 \
./scripts/run_all_tests.sh

# Quick mode - core tests only
./scripts/run_all_tests.sh --quick

# Individual test file
.venv/bin/python -m pytest tests/test_tasks.py -v
```

### Test Coverage

| Layer | Tests | File |
|-------|-------|------|
| Unit | 370+ | `tests/test_*.py` |
| Integration | 35+ | `tests/test_integration.py` |
| Obsidian | 55+ | `tests/test_obsidian_sync.py` |
| E2E Browser | 66 | `tests/e2e_browser_tests.py` |

### E2E Browser Tests

E2E tests use Chrome DevTools MCP. Requires servers running:

```bash
# Check available scenarios
.venv/bin/python tests/e2e_browser_tests.py
```

Key scenarios: `auth_login_success`, `chat_send_message`, `kb_upload_pdf`, `tasks_create`, `projects_create`

See `/docs/testing/CLAUDE_TESTING_GUIDE.md` for full E2E instructions.
