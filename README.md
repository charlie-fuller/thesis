# Thesis - Multi-Agent GenAI Strategy Platform

AI-powered multi-agent platform that helps enterprises implement successful GenAI strategies. Thesis provides 21 specialized agents representing real stakeholder perspectives, consulting expertise, and internal enablement capabilities to support AI Solutions Partners and strategy teams.

## Quick Links

- [Agent Roster](#agent-roster) - All 21 specialized agents
- [Agent Persona Alignment Report](docs/AGENT_PERSONA_ALIGNMENT_REPORT.md) - How agents map to interview subjects
- [Planning Documentation](docs/planning/) - Implementation plan and session transcripts
- [Context Document](docs/CONTEXT.md) - Project discovery and requirements
- [Getting Started](#getting-started) - Setup and installation instructions

## Overview

Thesis is a multi-agent platform designed for enterprise GenAI strategy implementation. Unlike generic AI assistants, each Thesis agent embodies a specific stakeholder perspective or consulting expertise, providing authentic guidance grounded in real enterprise concerns.

### Key Capabilities

- **21 Specialized Agents** - Stakeholder perspectives, consulting expertise, internal enablement, and systems coordination
- **Persona-Aligned Responses** - Agents embody real interview subjects with authentic concerns
- **Meeting Room** - Multi-agent collaboration space for focused cross-functional discussions
- **Autonomous Discussion** - Agents debate topics amongst themselves for configurable rounds; user can interject anytime
- **Stakeholder Intelligence** - CRM-style tracking with sentiment analysis and relationship mapping
- **Meeting Analysis** - Upload transcripts and extract stakeholder insights with evidence
- **Agent Coordination** - Coordinator seamlessly routes queries to appropriate specialists
- **Persistent Memory** - Mem0 integration for cross-conversation learning
- **Relationship Intelligence** - Neo4j graph database for stakeholder networks and expertise routing
- **Dig Deeper** - One-click elaboration on any response for more detail
- **Task Management** - Kanban-style board with drag-and-drop status updates
- **Project Triage** - AI opportunity pipeline with tier-based scoring (Operator integration)
- **Document Auto-Classification** - Automatic agent relevance tagging on upload
- **Stakeholder Engagement Analytics** - Automatic engagement level calculation with trends

## Agent Roster

Thesis includes 21 specialized agents organized into six categories:

| Category | Agents | Purpose |
|----------|--------|---------|
| [Meta-Agents](#meta-agents) | Facilitator, Reporter | Meeting orchestration and documentation |
| [Stakeholder Perspectives](#stakeholder-perspective-agents) | Atlas, Capital, Guardian, Counselor, Sage, Oracle | Embody real enterprise stakeholder viewpoints |
| [Consulting/Implementation](#consultingimplementation-agents) | Strategist, Architect, Operator, Pioneer | Professional consulting and technical guidance |
| [Internal Enablement](#internal-enablement-agents) | Catalyst, Scholar, Echo, Glean Evaluator, Compass, Manual | Support internal AI adoption and communication |
| [Systems/Coordination](#systemscoordination-agents) | Nexus, Coordinator | Systems thinking and agent orchestration |

---

### Stakeholder Perspective Agents

These agents embody real enterprise stakeholder perspectives, each aligned to an interview subject from discovery research. They provide authentic responses reflecting genuine enterprise concerns, priorities, and communication styles.

#### Atlas - Research Intelligence

| | |
|---|---|
| **Display Name** | Research |
| **Persona Alignment** | Chris Baumgartner (AI Program Manager) |
| **Domain Focus** | GenAI research, Lean methodology, benchmarking |

Atlas serves as the research intelligence engine, monitoring the GenAI implementation landscape across consulting approaches (Big 4, McKinsey, BCG, Accenture), academic research, and corporate case studies. Grounded in Lean/Toyota Production System principles, Atlas provides evidence-based recommendations with specific metrics and benchmarks.

**Key Capabilities:**
- Monitor and synthesize GenAI implementation research
- Benchmark organizational AI maturity against industry standards
- Apply Lean methodology to AI initiatives (eliminate waste, continuous improvement)
- Track consulting firm approaches and methodologies
- Provide evidence-backed recommendations with citations

---

#### Capital - Financial Analysis

| | |
|---|---|
| **Display Name** | Finance |
| **Persona Alignment** | Raul Rivera III (Sr. Director, Global Controller) |
| **Domain Focus** | ROI analysis, SOX compliance, business cases |

Capital provides the CFO/Controller perspective on AI investments, ensuring financial rigor and regulatory compliance. With deep understanding of SOX requirements, audit trails, and business case development, Capital helps justify AI investments with quantifiable returns.

**Key Capabilities:**
- Build comprehensive AI ROI models and business cases
- Ensure SOX compliance for AI-powered financial processes
- Develop audit trail requirements for AI decisions
- Analyze total cost of ownership (TCO) for AI solutions
- Assess financial risk and create mitigation strategies
- Compare build vs. buy economics

---

#### Guardian - IT/Governance

| | |
|---|---|
| **Display Name** | IT & Governance |
| **Persona Alignment** | Danny Leal (Director of IT) |
| **Domain Focus** | Security, compliance, shadow IT, vendor evaluation |

Guardian represents IT leadership concerns around security, governance, and infrastructure. With experience managing shadow IT and vendor relationships, Guardian helps organizations implement AI securely while maintaining control and compliance.

**Key Capabilities:**
- Evaluate AI vendor security postures and certifications
- Design AI governance frameworks and policies
- Identify and address shadow AI usage
- Assess integration requirements with existing infrastructure
- Create security requirements for AI implementations
- Develop data handling and privacy controls

---

#### Counselor - Legal Expertise

| | |
|---|---|
| **Display Name** | Legal |
| **Persona Alignment** | Ashley Adams (Director, Legal Operations) |
| **Domain Focus** | Contracts, AI risks, liability, data privacy |

Counselor provides legal operations perspective on AI adoption, addressing contract requirements, liability concerns, and regulatory compliance. With focus on practical legal risk mitigation, Counselor helps navigate the evolving AI regulatory landscape.

**Key Capabilities:**
- Review AI vendor contracts and licensing terms
- Assess liability exposure from AI-generated content/decisions
- Navigate AI-specific regulatory requirements (EU AI Act, state laws)
- Develop AI acceptable use policies
- Address intellectual property concerns (training data, outputs)
- Create data privacy compliance frameworks for AI

---

#### Sage - People & Change

| | |
|---|---|
| **Display Name** | People |
| **Persona Alignment** | Chad Meek (VP People Team) |
| **Domain Focus** | Change management, adoption, human flourishing |

Sage brings the HR/People perspective focused on the human side of AI transformation. Beyond traditional change management, Sage emphasizes human flourishing, ensuring AI augments rather than diminishes the employee experience.

**Key Capabilities:**
- Design change management strategies for AI adoption
- Address AI anxiety and workforce concerns
- Develop reskilling and upskilling programs
- Create adoption metrics and success measures
- Build AI champion networks within organizations
- Ensure AI initiatives support employee wellbeing

---

#### Oracle - Meeting Intelligence

| | |
|---|---|
| **Display Name** | Meeting Analyst |
| **Persona Alignment** | CIPHER v2.1 (analytical system) |
| **Domain Focus** | Transcript analysis, stakeholder dynamics, sentiment extraction |

Oracle specializes in analyzing meeting transcripts to extract stakeholder insights, power dynamics, and strategic recommendations. Using evidence-based analysis, Oracle identifies concerns, enthusiasm signals, and relationship patterns from meeting content.

**Key Capabilities:**
- Analyze meeting transcripts (Granola, Otter.ai, Teams, Zoom)
- Extract attendees with inferred roles and influence levels
- Identify sentiment per speaker with supporting evidence
- Detect concerns, objections, and enthusiasm signals
- Map stakeholder relationships and power dynamics
- Generate actionable meeting summaries and follow-ups

---

### Consulting/Implementation Agents

These agents provide professional consulting and implementation guidance, representing expertise areas typically found in management consulting and technical architecture roles.

#### Strategist - Executive Strategy

| | |
|---|---|
| **Display Name** | Executive Strategy |
| **Domain Focus** | C-suite engagement, organizational politics, governance design |

Strategist provides executive-level guidance on AI strategy, helping navigate organizational politics, board dynamics, and governance structures. With focus on C-suite communication and strategic positioning, Strategist helps build executive alignment for AI initiatives.

**Key Capabilities:**
- Develop executive communication strategies for AI initiatives
- Navigate organizational politics and power structures
- Design AI governance and steering committee frameworks
- Create board-level AI briefings and presentations
- Align AI initiatives with corporate strategy
- Manage stakeholder expectations and competing priorities

---

#### Architect - Technical Architecture

| | |
|---|---|
| **Display Name** | Technical Architecture |
| **Domain Focus** | Enterprise AI patterns, RAG, integration, build vs. buy |

Architect provides technical leadership for AI implementations, specializing in enterprise architecture patterns, integration strategies, and technology selection. With deep knowledge of RAG systems, LLM deployment, and enterprise integration, Architect guides sound technical decisions.

**Key Capabilities:**
- Design enterprise AI architecture patterns
- Evaluate build vs. buy decisions for AI capabilities
- Architect RAG (Retrieval-Augmented Generation) systems
- Plan LLM deployment strategies (cloud, on-premise, hybrid)
- Design API and integration patterns for AI services
- Assess technical feasibility and create implementation roadmaps

---

#### Operator - Business Operations

| | |
|---|---|
| **Display Name** | Business Operations |
| **Domain Focus** | Process optimization, automation, operational metrics |

Operator focuses on the operational aspects of AI implementation, identifying automation opportunities and optimizing business processes. With emphasis on measurable outcomes and operational efficiency, Operator ensures AI delivers tangible business value.

**Key Capabilities:**
- Identify high-value automation opportunities
- Map and optimize business processes for AI integration
- Design operational metrics and KPIs for AI initiatives
- Create pilot programs with clear success criteria
- Assess process readiness for AI augmentation
- Develop scaling strategies from pilot to production

---

#### Pioneer - Innovation/R&D

| | |
|---|---|
| **Display Name** | Innovation & R&D |
| **Domain Focus** | Emerging technology, hype filtering, maturity assessment |

Pioneer monitors the AI innovation landscape, separating signal from noise in emerging technologies. With focus on practical innovation adoption, Pioneer helps organizations understand which new capabilities are ready for enterprise use and which need more maturation.

**Key Capabilities:**
- Evaluate emerging AI technologies and capabilities
- Filter hype from practical enterprise applications
- Assess technology maturity and enterprise readiness
- Identify innovation opportunities aligned with business needs
- Track AI research trends with enterprise implications
- Create technology watch briefs for leadership

---

### Internal Enablement Agents

These agents support internal AI adoption, communication, and capability building, helping organizations develop sustainable AI competencies.

#### Catalyst - Internal Communications

| | |
|---|---|
| **Display Name** | Internal Communications |
| **Domain Focus** | AI messaging, employee engagement, AI anxiety |

Catalyst specializes in internal AI communications, helping organizations message AI initiatives in ways that build engagement rather than anxiety. With focus on transparent, empathetic communication, Catalyst helps employees understand and embrace AI transformation.

**Key Capabilities:**
- Develop internal AI communication strategies
- Create messaging that addresses AI anxiety and concerns
- Design employee engagement campaigns for AI initiatives
- Build AI awareness and literacy programs
- Craft leadership talking points for AI announcements
- Monitor and respond to employee sentiment around AI

---

#### Scholar - Learning & Development

| | |
|---|---|
| **Display Name** | Learning & Development |
| **Domain Focus** | Training programs, champion enablement, adult learning |

Scholar designs learning experiences that build AI capabilities across the organization. Grounded in adult learning principles, Scholar creates practical training programs that develop both AI literacy and hands-on skills.

**Key Capabilities:**
- Design AI training curricula for various skill levels
- Create AI champion enablement programs
- Develop hands-on learning experiences with AI tools
- Apply adult learning principles to AI education
- Build competency frameworks for AI skills
- Measure learning outcomes and capability growth

---

#### Echo - Brand Voice

| | |
|---|---|
| **Display Name** | Brand Voice |
| **Domain Focus** | Voice analysis, style profiling, AI emulation guidelines |

Echo analyzes and codifies brand voice characteristics, helping organizations maintain consistent voice across AI-generated content. By understanding tone, style, and communication patterns, Echo ensures AI outputs align with brand identity.

**Key Capabilities:**
- Analyze existing content for voice characteristics
- Create brand voice profiles and guidelines
- Develop AI prompt strategies for voice consistency
- Evaluate AI-generated content for brand alignment
- Build voice quality metrics and assessment criteria
- Train teams on maintaining voice in AI workflows

---

#### Manual - Documentation Assistant

| | |
|---|---|
| **Display Name** | Documentation Assistant |
| **Domain Focus** | Platform help, feature explanation, troubleshooting, navigation |

Manual serves as the in-app documentation guide, helping users understand Thesis features, navigate the platform, and troubleshoot common issues. With access to all platform documentation in its knowledge base, Manual provides contextual help while you work.

**Key Capabilities:**
- Explain Thesis features and capabilities
- Guide users through platform navigation
- Troubleshoot common issues and errors
- Recommend the right agent for specific tasks
- Provide step-by-step workflow guidance
- Answer "how do I..." questions about the platform

---

### Systems/Coordination Agents

These agents provide meta-level capabilities for systems thinking and agent coordination.

#### Nexus - Systems Thinking

| | |
|---|---|
| **Display Name** | Systems Thinking |
| **Domain Focus** | Interconnections, feedback loops, leverage points, unintended consequences |

Nexus applies systems thinking methodology to AI initiatives, helping organizations understand complex interdependencies and avoid unintended consequences. By mapping feedback loops and identifying leverage points, Nexus enables more effective interventions.

**Key Capabilities:**
- Map system interconnections and dependencies
- Identify feedback loops (reinforcing and balancing)
- Find high-leverage intervention points
- Anticipate unintended consequences of AI adoption
- Analyze emergent behavior in complex systems
- Create system diagrams and mental models

---

#### Coordinator - Thesis Orchestrator

| | |
|---|---|
| **Display Name** | Thesis |
| **Domain Focus** | Query routing, agent coordination, response synthesis |

Coordinator serves as the unified interface to all Thesis agents, intelligently routing queries to appropriate specialists and synthesizing multi-agent responses. For complex queries spanning multiple domains, Coordinator consults multiple specialists and presents a coherent, integrated response.

**Key Capabilities:**
- Analyze queries to identify relevant domains and agents
- Route to appropriate specialist agents
- Synthesize multi-agent perspectives into coherent responses
- Manage context across agent consultations
- Provide seamless single-interface experience
- Handle handoffs between agents transparently

---

## How It Works

### Single-Agent Mode (Default)

The **Coordinator** agent serves as the unified interface, seamlessly routing queries to the appropriate specialist agents based on the topic:

```
User Query
    |
    v
[Coordinator] --> Analyzes query, identifies relevant domains
    |
    v
[Specialist Agent(s)] --> Atlas, Capital, Guardian, etc.
    |
    v
[Synthesized Response] --> Unified answer from relevant perspectives
```

For complex queries spanning multiple domains, the Coordinator consults multiple specialists and synthesizes their perspectives into a coherent response.

### Meeting Room Mode (Multi-Agent Collaboration)

For focused cross-functional discussions, users can create Meeting Rooms with 2+ selected agents:

```
User creates Meeting Room with: Guardian + Capital + Architect
    |
    v
User Query: "Evaluate this AI vendor proposal"
    |
    v
[Guardian] --> Security assessment (parallel)
[Capital]  --> Financial analysis    (parallel)
[Architect]--> Technical evaluation  (parallel)
    |
    v
Three distinct responses, each from agent's perspective
```

Meeting Rooms are ideal for:
- Security investment discussions (Guardian + Capital)
- Technical architecture reviews (Architect + Pioneer + Operator)
- Change management planning (Sage + Catalyst + Scholar)
- Comprehensive vendor evaluations (Guardian + Capital + Counselor + Architect)

### Autonomous Discussion Mode

Within any Meeting Room, agents can discuss a topic amongst themselves for a configurable number of rounds (1-10). This enables rich cross-functional debate without constant user prompting.

**How it works:**
1. User enters a topic and selects number of discussion rounds
2. Agents take turns responding, building on each other's points
3. Each agent sees the full conversation history and other agents' expertise areas
4. User can interject at any point (pauses discussion for user input)
5. Discussion completes after all rounds or when manually stopped

**Discourse Moves (in priority order):**
1. **QUESTION** - Ask clarifying questions to other agents (curiosity is king!)
2. **CONNECT** - Link ideas across different domains
3. **CHALLENGE** - Respectfully push back with alternative perspectives
4. **EXTEND** - Build on another agent's point with additional depth
5. **SYNTHESIZE** - Combine multiple viewpoints into integrated insight

**Expert Deference:** Agents are aware of each other's specialties and defer to the relevant expert rather than overstepping their domain. For example, Guardian defers to Capital on ROI calculations, while Capital defers to Guardian on security architecture.

```
User: "Discuss the implications of shadow AI in our organization"
    |
    v
[Start Autonomous Discussion: 3 rounds]
    |
    v
Round 1: Each agent establishes their initial position
    Guardian: Security risks and detection strategies
    Counselor: Legal liability and policy gaps
    Sage: Employee anxiety and adoption patterns
    |
    v
Round 2: Agents respond to each other, ask questions, challenge
    Guardian asks Counselor about liability precedents
    Sage connects to Catalyst about communication strategy
    |
    v
Round 3: Synthesis and actionable recommendations
    |
    v
[Discussion Complete]
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 16, React 19, Tailwind CSS 4 |
| Backend | FastAPI (Python 3.11), Uvicorn |
| Database | Supabase (PostgreSQL + pgvector) |
| Graph DB | Neo4j (stakeholder network analysis) |
| AI - Chat | Anthropic Claude |
| AI - Embeddings | Voyage AI |
| AI - Images | Google Gemini 2.5 Flash |
| Memory | Mem0 |

### Why Dual Databases: PostgreSQL + Neo4j

Thesis uses a polyglot persistence architecture combining PostgreSQL (via Supabase) with Neo4j, each optimized for different data patterns:

**PostgreSQL handles:**
- Transactional data (users, conversations, agent configurations)
- Document storage (transcripts, meeting records)
- Vector embeddings for semantic search (pgvector)
- Row-level security for multi-tenancy

**Neo4j handles:**
- Stakeholder relationship networks
- Influence and reporting hierarchies
- Cross-organizational connection patterns
- Dynamic relationship traversal

#### Why This Matters for Stakeholder Intelligence

Enterprise AI initiatives succeed or fail based on stakeholder dynamics. Understanding who influences whom, where resistance clusters form, and which relationships can accelerate adoption requires graph-native thinking:

| Query Type | PostgreSQL Approach | Neo4j Approach |
|------------|---------------------|----------------|
| "Who reports to the CTO?" | Single JOIN, fast | Single hop, fast |
| "Who are 3 levels below the CEO?" | 3 recursive JOINs | 3 hops, still fast |
| "Find all paths between skeptic CFO and champion CTO" | Complex recursive CTE, slow | Native path finding, fast |
| "Which stakeholders connect Finance to Engineering?" | Very complex, potentially infeasible | Simple traversal query |
| "Find influence clusters and bottlenecks" | Not practical | Native graph algorithms |

**Concrete example:** When Oracle analyzes a meeting transcript and identifies that a Finance Director expressed concerns, Thesis can instantly query Neo4j to find:
- Who that Director influences (direct reports, cross-functional peers)
- Whether they have connections to known champions who might help address concerns
- If their skepticism could spread through specific organizational pathways

This relationship intelligence would require expensive recursive queries in PostgreSQL but is a simple 2-3 line Cypher query in Neo4j.

#### Synchronization Architecture

Data flows from PostgreSQL (source of truth) to Neo4j via an event-driven sync service:

```
[Supabase PostgreSQL] ---> [Sync Service] ---> [Neo4j]
     (CRUD operations)      (transforms)       (graph queries)
```

The sync service maintains consistency while allowing each database to excel at its strengths. See [docs/neo4j/SYNC_PLAN.md](docs/neo4j/SYNC_PLAN.md) for implementation details.

## Features

### Meeting Room

Multi-agent collaboration space for focused discussions with selected agents:

- **Create Meetings** - Select 2+ agents for focused cross-functional discussions
- **Collaboration Mode** - Real-time multi-agent responses to your queries
- **Autonomous Discussion** - Let agents debate a topic for multiple rounds without constant prompting
- **User Interjection** - Jump into autonomous discussions anytime; agents pause and respond to you
- **Meeting Prep Mode** - Practice stakeholder conversations and develop talking points
- **Smart Brevity** - Agents use headline-first, bullet-point format for clarity
- **Streaming Responses** - See each agent's response as it's generated
- **Speaking Order Display** - See the priority-based agent queue during autonomous discussions
- **Token Tracking** - Monitor meeting token usage

Use cases:
- Security investment discussions with Guardian + Capital
- Change management planning with Sage + Catalyst
- Technical architecture reviews with Architect + Pioneer
- Cross-functional debates on AI governance (Guardian + Counselor + Strategist)

### Dig Deeper

Request elaboration on any assistant response:

- **One-Click Expansion** - Click "Dig Deeper" on any substantial response
- **Streaming Response** - See elaboration generated in real-time
- **Contextual** - AI remembers the full conversation for relevant expansion
- **More Examples** - Get specific case studies and practical illustrations
- **Next Steps** - Receive actionable implementation guidance
- **Considerations** - Uncover potential challenges not covered initially

Appears on emails, meeting summaries, reports, and any response over 100 characters.

### Agent System Instruction Management

- **Version Control** - Track changes to agent system instructions over time
- **Compare Versions** - Diff view with AI-generated summaries of changes
- **Activate Versions** - Roll forward or back to any instruction version
- **XML-Based Instructions** - Externalized, structured agent configurations

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
- Relationship mapping with Neo4j graph database
- Key concerns and interests tracking

### Research Intelligence (Atlas)

Atlas provides proactive research intelligence beyond just answering questions:

**Automated Research Pipeline**
- **Daily Scheduled Research** - Runs at 6 AM UTC with focus areas by day of week:
  - Monday: Strategic Planning / C-suite engagement
  - Tuesday: Finance ROI / Business cases
  - Wednesday: Governance / Compliance frameworks
  - Thursday: Change Management / Adoption patterns
  - Friday: Weekly synthesis / Emerging trends

**Web Search with Anthropic**
- Uses Claude's native web search tool for real-time research
- **4-Tier Credibility System**:
  | Tier | Sources | Trust Level |
  |------|---------|-------------|
  | 1 | McKinsey, BCG, Gartner, HBR, MIT Sloan | High - cite directly |
  | 2 | Big 4 (Deloitte, PwC, EY, KPMG), major tech | High - cite directly |
  | 3 | Industry publications, WSJ, FT | Medium - verify claims |
  | 4 | Blogs, vendor marketing | Low - signals only |

**Cross-Agent Intelligence**
- **Agent Observation** - Monitors all agent conversations for knowledge gaps
- **Uncertainty Detection** - Identifies when agents express uncertainty in responses
- **Anticipatory Research** - Proactively researches topics based on:
  - New stakeholders added (prepares relevant use cases)
  - ROI opportunities created (gathers supporting benchmarks)
  - Stakeholder concerns raised (researches solutions)
- **Knowledge Distribution** - Research auto-links to relevant agent knowledge bases

**API Endpoints**
```
POST /api/research/trigger    - Trigger immediate research
GET  /api/research/tasks      - View research history
GET  /api/research/schedule   - View/edit schedule
GET  /api/research/gaps       - View knowledge gaps
GET  /api/research/sources    - View credible sources
```

See [Atlas Proactive Research Plan](docs/atlas/PROACTIVE_RESEARCH_PLAN.md) for full architecture.

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.11+
- Supabase account
- API keys for Anthropic, Voyage AI, and optionally Gemini
- Neo4j instance (optional, for stakeholder graph)

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

## Project Structure

```
thesis/
├── frontend/                    # Next.js frontend
│   ├── app/                     # App Router pages
│   │   ├── admin/agents/        # Agent management UI
│   │   ├── chat/                # Main chat interface
│   │   └── meeting-room/        # Multi-agent meeting rooms
│   │       └── [id]/            # Individual meeting page
│   └── components/
│       ├── ChatInterface.tsx    # Main chat with Dig Deeper
│       ├── ChatMessage.tsx      # Message display component
│       └── meeting-room/        # Meeting room components
│           ├── AutonomousDiscussionPanel.tsx  # Autonomous mode controls
│           ├── CreateMeetingModal.tsx
│           ├── MeetingMessage.tsx
│           └── ParticipantBar.tsx             # With speaking order display
├── backend/
│   ├── agents/                  # Agent implementations
│   │   ├── coordinator.py       # Central orchestrator
│   │   ├── base_agent.py        # Base agent class
│   │   ├── atlas.py             # Research agent with web search
│   │   └── [agent].py           # Individual agents
│   ├── system_instructions/
│   │   └── agents/              # XML system instructions
│   ├── api/routes/
│   │   ├── chat.py              # Chat + Dig Deeper endpoints
│   │   ├── meeting_rooms.py     # Meeting room endpoints
│   │   └── research.py          # Atlas research endpoints
│   └── services/
│       ├── meeting_orchestrator.py  # Multi-agent + autonomous orchestration
│       ├── research_scheduler.py    # Daily research scheduler
│       ├── research_context.py      # Topic prioritization
│       ├── agent_observer.py        # Cross-agent monitoring
│       └── web_researcher.py        # Anthropic web search
├── database/
│   └── migrations/
│       ├── 007_meeting_rooms.sql    # Meeting room tables
│       ├── 011_research_system.sql  # Research tables
│       └── 012_autonomous_discussion.sql  # Autonomous discussion mode
└── docs/                        # Documentation
    ├── AGENT_PERSONA_ALIGNMENT_REPORT.md
    ├── CONTEXT.md
    ├── atlas/                   # Atlas research documentation
    │   └── PROACTIVE_RESEARCH_PLAN.md
    └── planning/
```

## Documentation

- [CLAUDE.md](CLAUDE.md) - Development guidance for AI assistants
- [docs/AGENT_PERSONA_ALIGNMENT_REPORT.md](docs/AGENT_PERSONA_ALIGNMENT_REPORT.md) - Agent persona mappings
- [docs/CONTEXT.md](docs/CONTEXT.md) - Project context and requirements
- [docs/atlas/PROACTIVE_RESEARCH_PLAN.md](docs/atlas/PROACTIVE_RESEARCH_PLAN.md) - Atlas research system architecture
- [docs/neo4j/SYNC_PLAN.md](docs/neo4j/SYNC_PLAN.md) - PostgreSQL to Neo4j sync architecture
- [docs/planning/](docs/planning/) - Implementation plan and session transcripts
- [docs/testing/](docs/testing/) - Testing infrastructure and code quality

## Testing & Code Quality

The project includes a comprehensive testing and code review framework:

```bash
# Run backend tests
cd backend
source venv/bin/activate
python -m pytest tests/ -v --tb=short
```

### Testing Documentation

| Document | Purpose |
|----------|---------|
| [TESTING_PROMPT.md](docs/testing/TESTING_PROMPT.md) | Reusable prompt for automated code review and fixes |
| [COMPREHENSIVE_TEST_PLAN.md](docs/testing/COMPREHENSIVE_TEST_PLAN.md) | Full testing framework and strategy |
| [CODE_REVIEW_FINDINGS.md](docs/testing/CODE_REVIEW_FINDINGS.md) | Latest code review findings and action items |

### Code Quality Targets

| Metric | Current | Target |
|--------|---------|--------|
| Backend Tests | 55 | 75+ |
| Test Pass Rate | 100% | 100% |
| Code Quality Score | 7.0 | 9.0 |

The testing prompt enables autonomous code quality improvement with safety-first principles - it will automatically fix high-confidence issues (bare excepts, deprecated patterns, print statements) while reporting low-confidence issues for manual review.

## Development Status

### Completed

- Multi-agent coordinator with intelligent query routing
- 21 specialized agents with XML system instructions (Gigawatt v4.0 framework)
- Agent instruction versioning system with diff comparison
- Persona alignment for stakeholder perspective agents
- Neo4j graph integration for stakeholder networks (schema + sync working)
- Admin UI for agent management with graph stats panel
- Meeting Room feature for multi-agent collaboration
- Dig Deeper feature for response elaboration
- Smart Brevity formatting for meeting responses
- Systems thinking agent (Nexus) for complex interdependencies
- Brand voice agent (Echo) for content consistency
- Graph-based agent routing with expertise matching (8/11 accuracy)
- Real API health checks for Anthropic and Voyage AI services
- Auth-aware frontend components (no more 401 race conditions)
- **Atlas Proactive Research System**:
  - Daily research scheduler (APScheduler, 6 AM UTC)
  - Anthropic web search integration with credibility filtering
  - Agent observation for knowledge gap detection
  - Research context aggregation (stakeholder concerns, ROI opportunities)
  - Cross-agent knowledge distribution
  - Research API endpoints
- **Autonomous Discussion Mode**:
  - Multi-round agent-to-agent discussions (1-10 rounds)
  - Discourse moves: Question, Connect, Challenge, Extend, Synthesize
  - Expert deference system (agents know each other's specialties)
  - User interjection support (pause/resume)
  - Speaking order display with progress tracking
  - Priority-based turn ordering

### In Progress

- Code quality improvements (target: 9.0/10 score)
- Integration testing across agent roster
- Populating stakeholder/meeting data for full graph functionality

### Planned

- Research dashboard UI for Atlas insights
- Customer-facing AI use case agents
- Engineering/Product Management perspectives
- External communications capabilities
- Stakeholder network visualization component
- Expanded test coverage (target: 75+ backend tests)

## License

MIT
