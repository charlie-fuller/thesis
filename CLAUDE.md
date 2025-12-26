# Thesis - Multi-Agent GenAI Strategy Platform

## Memory Protocol (IMPORTANT)

### Session Start
At the beginning of each conversation, query Mem0 for recent context:
```
query: "recent decisions, issues, and context"
filters: {"repo": "thesis"}
```
Briefly mention any relevant memories found.

### During Session
Save important information to Mem0 when:
- A significant decision is made (architecture, approach, library choice)
- A tricky bug is solved (save the cause and fix)
- User states a preference or convention
- A TODO or next step is identified for future sessions
- Important stakeholder insights are discovered

### When Saving/Querying
Always use:
- **Save**: `metadata: {"repo": "thesis"}`
- **Query**: `filters: {"repo": "thesis"}`

### Session End
If the conversation included important decisions or unfinished work, save a summary to Mem0 before ending.

## Project Overview

Thesis is a multi-agent platform for enterprise GenAI strategy implementation. It helps AI Solutions Partners guide and manage successful AI initiatives by providing specialized agents for research, finance, IT/governance, legal, and meeting analysis.

**Forked from Walter** - This codebase is based on the Walter L&D assistant platform, adapted for multi-agent GenAI strategy support.

### Core Agents

| Agent | Name | Purpose |
|-------|------|---------|
| Research | Atlas | Track GenAI research, consulting approaches, case studies, thought leadership |
| Finance | Fortuna | ROI analysis, budget justification, Finance stakeholder support |
| IT/Governance | Guardian | Navigate governance, security, infrastructure considerations |
| Legal | Counselor | Legal considerations, contracts, compliance |
| Transcript Analyzer | Oracle | Extract stakeholder sentiment from meeting transcripts |

### Key Capabilities

1. **Transcript Analysis**: Upload meeting transcripts (Granola/Otter format), extract stakeholder insights
2. **Stakeholder Tracking**: Full CRM-style tracking with sentiment, engagement, alignment scores
3. **Research Intelligence**: Proactive monitoring of GenAI implementation research
4. **Agent Coordination**: Hybrid model - some agents work independently, others collaborate
5. **Persistent Memory**: Mem0 integration for cross-conversation learning

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 16, React 19, TypeScript 5, Tailwind CSS 4 |
| Backend | FastAPI (Python 3.11), Uvicorn, Pydantic |
| Database | Supabase (PostgreSQL) with Row-Level Security |
| AI/ML | Anthropic Claude, Voyage AI embeddings, Google Gemini 2.5 Flash (images) |
| Memory | Mem0 for persistent agent memory |
| Integrations | Google Drive, Notion |
| Deployment | Railway (backend), Vercel (frontend) |

## Key Directories

```
/frontend
  /app           - Next.js App Router pages
  /components    - React components
  /contexts      - AuthContext, HelpChatContext, ThemeContext

/backend
  /api/routes    - FastAPI endpoints
  /agents        - Agent implementations (NEW)
  /services      - Business logic including transcript_analyzer (NEW)
  /system_instructions - Agent-specific prompts

/database
  /migrations    - SQL migration scripts
  thesis_schema.sql - Complete schema including agents, stakeholders, ROI

/docs
  /planning      - Implementation plan and session transcripts
  CONTEXT.md     - Discovery context for the project
```

## Development Commands

```bash
# Frontend (from /frontend)
npm run dev          # Start dev server (localhost:3000)
npm run build        # Production build
npm run lint         # ESLint check

# Backend (from /backend)
uvicorn main:app --reload --port 8000   # Dev server
python -m pytest                         # Run tests
```

## Architecture Patterns

- **Multi-agent**: Router + orchestrator for agent coordination
- **Multi-tenancy**: Client-based data isolation via Supabase RLS
- **Streaming**: Server-sent events for real-time chat responses
- **Type safety**: Strict TypeScript + Pydantic validation throughout
- **Agent memory**: Mem0 for persistent cross-conversation context
- **People-first**: All recommendations consider change management

## Code Conventions

- **Frontend**: ESLint + Prettier, functional components, Context API for state
- **Backend**: Black + Ruff formatting, async/await, Pydantic models for all requests
- **Commits**: Conventional commits (fix:, feat:, docs:, etc.)
- **No emojis**: Keep documentation and code professional

## Thesis-Specific Tables

```sql
-- Core new tables (see /database for full schema)
agents                    -- Agent registry
stakeholders              -- CRM-style stakeholder tracking
stakeholder_insights      -- Extracted insights from transcripts
meeting_transcripts       -- Processed transcript metadata
roi_opportunities         -- Identified ROI opportunities
agent_instruction_versions -- Per-agent system instruction versioning
agent_handoffs            -- Tracking agent-to-agent handoffs
```

## Environment Variables

See `/frontend/.env.example` and `/backend/.env.example` for complete reference.

Key variables:
- `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`
- `ANTHROPIC_API_KEY` (Claude)
- `VOYAGE_API_KEY` (embeddings)
- `MEM0_API_KEY` (agent memory)

## Planning Documents

- `/docs/CONTEXT.md` - Full discovery context
- `/docs/planning/IMPLEMENTATION_PLAN.md` - Detailed implementation roadmap
- `/docs/planning/2024-12-26-planning-session.md` - Planning session transcript

## Important Files

- `/backend/main.py` - FastAPI app entry point
- `/backend/agents/` - Agent implementations
- `/backend/services/transcript_analyzer.py` - Meeting analysis
- `/backend/system_instructions/` - Agent behavior configuration
- `/frontend/app/layout.tsx` - Root layout with providers
- `/database/thesis_schema.sql` - Complete DB schema
