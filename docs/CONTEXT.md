> **HISTORICAL DOCUMENT**
>
> This document was created on December 26, 2024 and captures the original discovery
> and planning context. The platform has evolved significantly since then.
>
> For current documentation, see [CLAUDE.md](/CLAUDE.md) - the authoritative reference.
> For current agent roster (20 agents), see [README.md](/README.md).
>
> Preserved for historical context and decision-making reference.

---

# Thesis Platform - Context Document (HISTORICAL)

> This document captures the discovery and planning context for future development sessions.

## Project Overview

**Thesis** is a multi-agent platform for enterprise GenAI strategy implementation, designed to support Charlie's role as AI Solutions Partner at Contentful starting January 5, 2025.

## The Role

- One of four people implementing GenAI strategies company-wide at Contentful
- Focus area: **G&A (General & Administrative)** - Finance, IT, Legal, Governance
- Contentful already has GenAI in their CMS product, so organizational familiarity exists

## Platform Vision

A suite of specialized agents that work together (hybrid coordination model) to:
1. **Synthesize** - Pull insights together from research, meetings, documents
2. **Generate** - Create artifacts like proposals, documentation, presentations
3. **Advise** - Prepare for and follow up on stakeholder conversations

## Core Agents

| Agent | Name | Purpose |
|-------|------|---------|
| Research | Atlas | Track GenAI implementation research, consulting approaches, corporate case studies, thought leadership - with proactive alerts |
| Finance | Capital | ROI analysis, budget justification, Finance stakeholder support |
| IT/Governance | Guardian | Navigate governance, security, infrastructure considerations |
| Legal | Counselor | Legal considerations, contracts, compliance |
| Transcript Analyzer | Oracle | Extract stakeholder sentiment from meeting transcripts |

## Architecture Decisions

- **Hybrid coordination**: Some agents work independently, others collaborate on complex tasks
- **Shared knowledge base**: Same platform, different interfaces/views based on role (federalizable)
- **People-first approach**: Change management focus, human-in-the-loop, stakeholder awareness in every recommendation
- **Transcript focus**: Primary meeting analysis output is stakeholder sentiment (concerns, enthusiasm, resistance patterns)
- **Conflict resolution**: Surface both perspectives when agents disagree - transparency over forced resolution
- **Agent memory**: Mem0 integration for persistent cross-conversation memory and preference learning
- **Stakeholder tracking**: Full CRM-style (contact info, meeting history, all touchpoints, preferences)
- **Auto-linking**: Confidently auto-link transcript speakers to existing stakeholders when names/roles match
- **Exit strategy**: All data exportable, open-sourceable, transferable to successor

## Usage Patterns

- **Morning briefing**: Dashboard view showing new research, stakeholder changes, pending actions
- **Post-meeting processing**: Upload Granola/Otter transcript (markdown/txt), get stakeholder insights
- **On-demand queries**: Ask any agent questions when needed

## Dashboard Key Metrics

1. **Sentiment trend**: Are stakeholders getting more/less positive over time?
2. **Engagement frequency**: How often am I talking to each person/department?
3. **Open concerns**: What unresolved issues are floating across conversations?
4. **Alignment score**: How aligned are key stakeholders with AI initiatives?

## Additional Requirements

- **Mobile access**: Full mobile capability - upload transcripts and chat with agents from phone
- **Notifications**: In-app only (no email/Slack for now)
- **Correction mechanisms**:
  - Edit extracted data inline
  - Mark as incorrect with feedback loop
  - Re-analyze with additional context
- **Initial data**: Some transcripts to import on Day 1 (not starting completely fresh)
- **Generic design**: Build as a generic platform from the start, configure for Contentful - ready to open source
- **Data backup**: Key insights synced to Obsidian/Notion for redundancy and offline access
- **Compliance**: Check with Contentful before storing company meeting transcripts/stakeholder data externally

## Pre-Launch Checklist

- [ ] Verify with Contentful what data can be stored externally
- [ ] Set up Supabase with appropriate encryption/access controls
- [ ] Import a few test transcripts to validate the pipeline
- [ ] Test mobile upload flow

## Atlas Research Focus Areas

The Research Agent (Atlas) should actively monitor and synthesize:

1. **Consulting Approaches**: What are Big 4, McKinsey, BCG, Accenture recommending for GenAI implementation?
2. **Corporate Case Studies**: What are companies (especially similar to Contentful - SaaS, content/marketing tech) finding useful vs. not useful?
3. **Thought Leadership**: Articles, blog posts, whitepapers on GenAI implementation methodologies
4. **Academic Research**: MIT Sloan, Harvard Business Review, Gartner, Forrester findings on what makes AI projects successful
5. **Failure Patterns**: What causes GenAI initiatives to fail? Implementation anti-patterns to avoid
6. **People/Change Management**: How do successful companies handle the human side of AI adoption?

**Proactive Behavior**: Atlas should notify when it finds research relevant to active work streams (e.g., "This new McKinsey article addresses the Finance stakeholder concerns you discussed in yesterday's meeting")

## Data Sources

- Manual uploads (transcripts, PDFs, documents)
- Automated ingestion (Google Drive, Notion, email)
- Web scraping (research sites, news, publications)

## Success Metrics (90 days)

1. Identified 2-3 concrete ROI opportunities where GenAI can deliver measurable value
2. Stakeholder alignment - Key people in Finance/IT/Legal are bought in and engaged
3. Knowledge organized - Searchable, synthesized knowledge base actually in use
4. Credibility established - Seen as the go-to resource for GenAI implementation

## Technical Foundation

Thesis will fork/adapt from the **Thesis** platform, which provides:
- Full-stack: Next.js, FastAPI, Supabase (PostgreSQL + pgvector)
- RAG pipeline: Voyage AI embeddings, vector search, adaptive thresholds
- Document processing: PDF, DOCX, PPTX, XLSX, TXT support
- Integrations: Google Drive OAuth sync, Notion sync
- Multi-tenancy: RLS-based data isolation
- Auth, rate limiting, usage analytics
- **Help System**: Context-aware documentation for users and admins (MUST PRESERVE)
- **System Instruction Versioning**: Version history, comparison, rollback

**What Thesis adds:**
- Multi-agent architecture with router and orchestrator
- Specialized agents with domain expertise
- Stakeholder tracking database
- Meeting transcript analysis
- ROI opportunity detection
- Agent handoff mechanisms

## MVP Scope (Weeks 1-3)

1. Fork Thesis, set up new infrastructure
2. Agent registry and basic router
3. Atlas (Research) agent with web search
4. Oracle (Transcript Analyzer) with stakeholder extraction
5. Capital (Finance) agent with ROI detection
6. Basic handoff mechanism between agents
7. Stakeholder database populated from transcripts

## Key References

- **Thesis Repository**: `/Users/motorthings/Documents/GitHub/thesis/`
- **DISCo System Instructions**: Planning methodology reference at `/Users/motorthings/Documents/GitHub/disco/` (formerly PuRDy at `purdy/`)
- **Deployment**: Railway (backend) + Vercel (frontend) + Supabase (database)

## Planning Session Date

December 26, 2024

---

*This context document should be updated as the platform evolves.*
