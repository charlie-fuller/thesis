# Thesis Documentation

Complete documentation for the Thesis multi-agent GenAI strategy platform.

---

## Quick Links

| Document | Purpose |
|----------|---------|
| [CLAUDE.md](/CLAUDE.md) | **Primary Reference** - Development guidance, tech stack, conventions |
| [README.md](/README.md) | Project overview with full agent roster |
| [AGENT_GUARDRAILS.md](./AGENT_GUARDRAILS.md) | Agent behavior rules, brevity limits, conversational coherence |
| [JANUARY_2026_RELEASE_NOTES.md](./JANUARY_2026_RELEASE_NOTES.md) | Latest features and changes |

---

## Strategic Vision

Thesis is a multi-agent platform for enterprise GenAI strategy implementation. It helps AI Solutions Partners guide successful AI initiatives by providing specialized agents that embody real stakeholder perspectives.

### Core Philosophy

1. **People-First**: Every recommendation considers change management and human impact
2. **Evidence-Based**: All insights backed by data, quotes, and citations
3. **Multi-Perspective**: Surface diverse viewpoints rather than forcing consensus
4. **Brevity-First**: Concise responses with dig-deeper expansion on demand

### How Agents Work Together

```
User Query
    |
    v
[Coordinator] --> Analyzes query, identifies domains
    |
    v
[Specialist Agents] --> Atlas, Capital, Guardian, etc.
    |
    v
[Synthesized Response] --> Unified answer from relevant perspectives
```

In **Meeting Rooms**, multiple agents collaborate directly:
- Facilitator orchestrates, invites speakers, weaves threads
- Specialist agents contribute domain expertise
- Reporter synthesizes discussions into shareable summaries
- Autonomous discussion mode enables agent-to-agent debate

---

## Documentation Structure

### Current Documentation

| Directory | Contents |
|-----------|----------|
| `/` (root) | [CLAUDE.md](/CLAUDE.md) - Primary reference for development |
| `/` (root) | [README.md](/README.md) - Project overview with agent roster |

### Feature Documentation

| Directory | Contents |
|-----------|----------|
| [atlas/](./atlas/) | Atlas research system architecture |
| [neo4j/](./neo4j/) | Graph database implementation and sync |
| [sage/](./sage/) | Sage agent updates |
| [stakeholders/](./stakeholders/) | Stakeholder profiling methodology |
| [features/](./features/) | Help system integration |
| [glean/](./glean/) | Glean connector registry data |

### Operational Documentation

| Directory | Contents |
|-----------|----------|
| [deployment/](./deployment/) | Deployment guides, Railway/Vercel setup |
| [deployment/archive/](./deployment/archive/) | Historical deployment notes |
| [testing/](./testing/) | Test plans, code review history |

### Help System Content

| Directory | Contents |
|-----------|----------|
| [help/user/](./help/user/) | End-user help documentation |
| [help/admin/](./help/admin/) | Administrator help documentation |

### Historical Planning Documents

| Directory | Contents |
|-----------|----------|
| [planning/](./planning/) | Original implementation plans (historical) |
| [archive/](./archive/) | Archived pre-Thesis documents |

### Reference Files

| File | Purpose |
|------|---------|
| [AGENT_GUARDRAILS.md](./AGENT_GUARDRAILS.md) | Agent behavior constraints |
| [AGENT_PERSONA_ALIGNMENT_REPORT.md](./AGENT_PERSONA_ALIGNMENT_REPORT.md) | Agent-to-interview-subject mapping |
| [CONTEXT.md](./CONTEXT.md) | Historical project discovery context |
| [EMAIL_INTEGRATION_PLAN.md](./EMAIL_INTEGRATION_PLAN.md) | Email integration planning |
| [GOOGLE_OAUTH_SETUP.md](./GOOGLE_OAUTH_SETUP.md) | OAuth configuration guide |
| [obsidian-sync-readme.md](./obsidian-sync-readme.md) | Obsidian vault sync documentation |

---

## Platform Capabilities

### Agent System (20 Agents)

**Meta-Agents**:
- **Facilitator** - Meeting orchestration, routing, synthesis
- **Reporter** - Meeting documentation with domain labels

**Stakeholder Perspectives**:
- **Atlas** (Research) - GenAI research, benchmarking
- **Capital** (Finance) - ROI analysis, SOX compliance
- **Guardian** (IT/Governance) - Security, compliance, vendors
- **Counselor** (Legal) - Contracts, AI risks, privacy
- **Sage** (People) - Change management, adoption
- **Oracle** (Meeting Intelligence) - Transcript analysis

**Consulting/Implementation**:
- **Strategist** - C-suite engagement, politics
- **Architect** - Technical patterns, RAG, integration
- **Operator** - Process optimization, Project Triage
- **Pioneer** - Emerging tech, hype filtering

**Internal Enablement**:
- **Catalyst** - Internal communications, AI messaging
- **Scholar** - Training, champion enablement
- **Echo** - Brand voice analysis
- **Glean Evaluator** - Platform fit assessment
- **Compass** - Career coaching, win tracking

**Systems/Coordination**:
- **Nexus** - Systems thinking, feedback loops
- **Coordinator** - Query routing, response synthesis

### Key Features

| Feature | Description |
|---------|-------------|
| **Meeting Room** | Multi-agent collaboration with autonomous discussion |
| **Task Management** | Kanban board with drag-and-drop |
| **Opportunities Pipeline** | Tier-based AI opportunity scoring |
| **Knowledge Base** | Document upload with auto-classification |
| **Stakeholder Tracking** | CRM-style with engagement analytics |
| **Meeting Prep** | Stakeholder briefing pages |
| **Obsidian Sync** | Local vault integration |

---

## Development References

### Backend
- `/backend/agents/` - Agent implementations
- `/backend/system_instructions/agents/` - XML behavior configs
- `/backend/services/` - Business logic services
- `/backend/api/routes/` - FastAPI endpoints

### Frontend
- `/frontend/app/` - Next.js pages
- `/frontend/components/` - React components
- `/frontend/contexts/` - Auth, Theme, HelpChat contexts

### Database
- `/database/migrations/` - SQL migration scripts
- `/database/thesis_schema.sql` - Complete schema

---

## Deployment

| Service | Platform | URL Pattern |
|---------|----------|-------------|
| Frontend | Vercel | thesis-*.vercel.app |
| Backend | Railway | thesis-production.up.railway.app |
| Database | Supabase | Managed PostgreSQL |
| Graph DB | Neo4j Aura | Cloud hosted |

---

## Contributing

1. Follow conventions in [CLAUDE.md](/CLAUDE.md)
2. Use conventional commits (feat:, fix:, docs:)
3. Maintain agent brevity guidelines
4. No emojis in documentation or code

---

**Last Updated**: January 2026
**Primary Reference**: [CLAUDE.md](/CLAUDE.md)
