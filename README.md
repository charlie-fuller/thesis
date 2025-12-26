# Thesis - Multi-Agent GenAI Strategy Platform

AI-powered multi-agent platform that helps enterprises implement successful GenAI strategies. Thesis provides specialized agents for research, finance, IT/governance, legal, and meeting analysis to support AI Solutions Partners and strategy teams.

## Quick Links

- [Planning Documentation](docs/planning/) - Implementation plan and session transcripts
- [Context Document](docs/CONTEXT.md) - Project discovery and requirements
- [Getting Started](#getting-started) - Setup and installation instructions

## Overview

Thesis is a multi-agent platform designed for enterprise GenAI strategy implementation. It provides:

- **Specialized Agents** - Research (Atlas), Finance (Fortuna), IT/Governance (Guardian), Legal (Counselor), and Transcript Analysis (Oracle)
- **Stakeholder Intelligence** - Full CRM-style tracking with sentiment analysis, engagement scoring, and relationship mapping
- **Meeting Analysis** - Upload transcripts and extract stakeholder insights, concerns, and action items
- **Research Monitoring** - Proactive tracking of GenAI implementation research, case studies, and thought leadership
- **Agent Coordination** - Hybrid model where agents work independently or collaborate on complex tasks
- **Persistent Memory** - Mem0 integration for cross-conversation context and learning

## Core Agents

| Agent | Name | Purpose |
|-------|------|---------|
| Research | Atlas | Track GenAI research, consulting approaches, case studies, thought leadership |
| Finance | Fortuna | ROI analysis, budget justification, Finance stakeholder support |
| IT/Governance | Guardian | Navigate governance, security, infrastructure considerations |
| Legal | Counselor | Legal considerations, contracts, compliance |
| Transcript Analyzer | Oracle | Extract stakeholder sentiment from meeting transcripts |

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 16, React 19, Tailwind CSS 4 |
| Backend | FastAPI (Python 3.11), Uvicorn |
| Database | Supabase (PostgreSQL + pgvector) |
| AI - Chat | Anthropic Claude |
| AI - Embeddings | Voyage AI |
| AI - Images | Google Gemini 2.5 Flash |
| Memory | Mem0 |
| Integrations | Google Drive, Notion |

## Features

### Transcript Analysis (Oracle)
- Upload meeting transcripts (Granola, Otter.ai, or plain text)
- Extract attendees with inferred roles
- Analyze sentiment per speaker
- Identify concerns and enthusiasm signals
- Generate meeting summaries
- Auto-link speakers to existing stakeholders

### Stakeholder Tracking
- Full CRM-style profiles (contact info, history, touchpoints)
- Sentiment scoring and trend tracking
- Engagement level classification (champion, supporter, neutral, skeptic, blocker)
- Alignment scoring for AI initiatives
- Relationship mapping (influences, reports to)
- Key concerns and interests tracking

### Research Intelligence (Atlas)
- Monitor consulting approaches (Big 4, McKinsey, BCG, Accenture)
- Track corporate case studies
- Ingest thought leadership articles and whitepapers
- Academic research tracking (MIT Sloan, HBR, Gartner, Forrester)
- Proactive alerts when research relates to active work

### Morning Dashboard
- Sentiment trends across stakeholders
- Engagement frequency metrics
- Open concerns summary
- Alignment scores visualization
- Recent transcripts with summaries

## Getting Started

### Prerequisites
- Node.js 18+
- Python 3.11+
- Supabase account
- API keys for Anthropic, Voyage AI, and optionally Gemini

### Installation

```bash
# Clone the repository
git clone https://github.com/motorthings/thesis.git
cd thesis

# Frontend setup
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local with your API keys

# Backend setup
cd ../backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
```

### Development

```bash
# Start frontend (from /frontend)
npm run dev

# Start backend (from /backend)
uvicorn main:app --reload --port 8000
```

## Documentation

- [CLAUDE.md](CLAUDE.md) - Development guidance for AI assistants
- [docs/CONTEXT.md](docs/CONTEXT.md) - Project context and requirements
- [docs/planning/](docs/planning/) - Implementation plan and session transcripts

## Architecture

Thesis is forked from the [Walter](https://github.com/motorthings/walter) L&D assistant platform, adapted for multi-agent GenAI strategy support. Key architectural additions:

- **Agent Router** - Intent detection and agent selection
- **Agent Orchestrator** - Multi-agent coordination for complex tasks
- **Transcript Analyzer** - Meeting intelligence extraction
- **Stakeholder Service** - CRM-style people tracking
- **ROI Detector** - Opportunity identification from conversations

## License

MIT
