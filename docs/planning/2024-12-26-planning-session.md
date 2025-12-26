# Thesis Planning Session - December 26, 2024

> Full transcript of the planning session between Charlie and Claude for the Thesis platform.

---

## Session Overview

**Date:** December 26, 2024
**Duration:** Extended planning session
**Participants:** Charlie (User), Claude (Assistant)

## Context Established

Charlie is starting as an **AI Solutions Partner at Contentful** on January 5, 2025. He is one of four people implementing GenAI strategies company-wide, with a focus on G&A (General & Administrative) - working with Finance, IT, Legal, and Governance teams.

## Key Discoveries

### Platform Vision
- Multi-agent platform for enterprise GenAI strategy implementation
- Named "Thesis" - implying a well-reasoned, structured approach
- Should be extensible and federalizable to other teams

### Core Agents Defined

| Agent | Name | Purpose |
|-------|------|---------|
| Research | Atlas | Track consulting approaches, case studies, thought leadership with proactive alerts |
| Finance | Fortuna | ROI analysis, budget justification, Finance stakeholder support |
| IT/Governance | Guardian | Navigate governance, security, infrastructure |
| Legal | Counselor | Legal considerations, contracts, compliance |
| Transcript Analyzer | Oracle | Extract stakeholder sentiment from meeting transcripts |

### Architecture Decisions Made

1. **Hybrid coordination** - Some agents work independently, others collaborate
2. **Mem0 integration** - Persistent cross-conversation memory
3. **Full CRM-style stakeholder tracking** - Contact info, history, touchpoints, preferences
4. **Confident auto-linking** - Match transcript speakers to existing stakeholders
5. **Generic platform design** - Ready for open-source, configured for Contentful
6. **Full mobile access** - Upload transcripts and chat from phone
7. **Surface conflicting perspectives** - When agents disagree, show both views
8. **Data synced to Obsidian/Notion** - Backup and offline access

### Usage Patterns Identified

- **Morning briefing**: Dashboard with sentiment trends, engagement, concerns, alignment
- **Post-meeting processing**: Upload Granola/Otter transcripts (markdown/txt format)
- **On-demand queries**: Ask agents questions as needed

### Success Metrics (90 days)

1. Identified 2-3 concrete ROI opportunities
2. Stakeholder alignment (Finance/IT/Legal bought in)
3. Organized, searchable knowledge base in use
4. Credibility established as go-to GenAI resource

### Dashboard Key Metrics

1. Sentiment trend - Are stakeholders getting more/less positive?
2. Engagement frequency - Who haven't I talked to recently?
3. Open concerns - Unresolved issues across meetings
4. Alignment scores - Stakeholder alignment with AI initiatives

### Technical Foundation

Fork from **Thesis** platform, which provides:
- Full-stack: Next.js, FastAPI, Supabase (PostgreSQL + pgvector)
- RAG pipeline: Voyage AI embeddings, vector search
- Document processing: PDF, DOCX, PPTX, XLSX, TXT
- Integrations: Google Drive, Notion
- Help system: Context-aware user and admin documentation
- System instruction versioning: Multiple versions, comparison, rollback

## Questions Asked and Answers

### Architecture Questions
- **Agent coordination?** → Hybrid approach (some independent, some collaborative)
- **Primary workflows?** → Synthesizing, Generating artifacts, Advising stakeholders
- **Transcript output focus?** → Stakeholder sentiment (concerns, enthusiasm, resistance)
- **Extensibility model?** → Shared knowledge base with different interfaces by role

### People-First Approach
- **What does people-first mean?** → All of: change management focus, human-in-the-loop, stakeholder awareness

### Deployment & Usage
- **Deployment location?** → Need guidance (likely Railway + Vercel)
- **MVP scope?** → Oracle (transcript analyzer) for Day 1 value
- **Data sources?** → All: manual uploads, automated ingestion, web scraping

### UX & Features
- **Morning briefing format?** → Dashboard view
- **Transcript source?** → Granola/Otter (markdown/txt export)
- **Mobile access?** → Full mobile capability needed
- **Notifications?** → In-app only for MVP

### Memory & Learning
- **Agent learning?** → Mem0 integration for persistent memory
- **Memory scope?** → Cross-conversation (using Mem0 MCP)

### Stakeholder Tracking
- **Depth of stakeholder data?** → Full CRM-style
- **Auto-linking speakers?** → Confident auto-link when names/roles match

### Corrections & Feedback
- **Handling wrong analysis?** → Multiple methods: inline edit, feedback loop, re-analyze

### Compliance & Exit Strategy
- **Agent conflict resolution?** → Surface both perspectives
- **Exit strategy?** → Exportable + open-source + transferable
- **Compliance concerns?** → Check with Contentful before storing data externally

### Platform Design
- **Generic vs Contentful-specific?** → Generic from start, ready to share
- **Backup plan?** → Data synced to Obsidian/Notion

## Important Notes

### Existing Thesis Repository
A GitHub repository named "thesis" was already created at: https://github.com/motorthings/thesis

### Thesis's Help System
The help system from Thesis should be preserved in Thesis:
- Context-aware assistance for users
- Admin documentation generation
- Help chat interface

### System Instruction Management
Each agent needs Thesis-style instruction versioning:
- Multiple versions with history
- Activation/deactivation
- Side-by-side comparison
- Rollback capability
- Track which version used per conversation

## Pre-Launch Checklist

- [ ] Verify with Contentful what data can be stored externally
- [ ] Set up Supabase with appropriate encryption/access controls
- [ ] Import test transcripts to validate the pipeline
- [ ] Test mobile upload flow

## Files Created This Session

1. `/thesis/docs/CONTEXT.md` - Discovery context for future sessions
2. `/thesis/docs/planning/IMPLEMENTATION_PLAN.md` - Full implementation roadmap
3. `/thesis/docs/planning/2024-12-26-planning-session.md` - This file

---

## Next Steps

1. Fork Thesis repository to Thesis
2. Preserve Thesis's help system
3. Set up new Supabase project
4. Apply database migrations
5. Create base agent infrastructure
6. Implement Oracle (transcript analyzer) first
7. Deploy to Railway + Vercel
