# Atlas Proactive Research System - Design Plan

**Location:** `docs/atlas/PROACTIVE_RESEARCH_PLAN.md`
**Created:** 2025-12-27
**Status:** Phase 1 Complete, Phase 2 In Progress

## Implementation Status

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1: Core Infrastructure | Complete | Scheduler, routes, migration deployed |
| Phase 2: Web Search Integration | In Progress | Web researcher service exists |
| Phase 3: Agent Observation | Planned | |
| Phase 4: Knowledge Distribution | Planned | |
| Phase 5: Admin UI | Planned | |

### Phase 1 Completed Items
- `backend/services/research_scheduler.py` - APScheduler with daily research at 6 AM UTC
- `backend/services/research_context.py` - Platform context gathering
- `backend/api/routes/research.py` - Research API endpoints
- `database/migrations/011_research_system.sql` - Applied with:
  - `research_tasks` table
  - `research_schedule` table (5 daily schedules seeded)
  - `research_sources` table (22 credible sources, Tier 1-4)
  - `research_knowledge_gaps` table
  - `agent_research_topics` table (65 agent-topic mappings)
- Research scheduler registered in `backend/main.py` startup

---

## Design Decisions (Confirmed)

| Decision | Choice |
|----------|--------|
| Research Scope | **Global + client layer** - Base industry research plus client-specific |
| Approval Flow | **Auto-publish** - Research goes directly to KB |
| Web Search | **Yes** - Atlas can search web for fresh research/news |
| Agent Integration | **Deep** - Observe conversations, fill gaps, anticipatory research |

---

## Executive Summary

Transform Atlas from a **reactive** agent (answers questions when asked) to a **proactive** research intelligence system that:
1. Performs daily automated research based on platform context
2. Understands what you and other agents are working on
3. Uses current tasks/stakeholder concerns as research guidance
4. Contributes findings back to the shared knowledge base
5. **Searches the web for fresh research, case studies, and industry news**
6. **Deeply integrates with other agents to fill knowledge gaps**

---

## Files to Create/Modify

### New Files
| File | Purpose |
|------|---------|
| `backend/services/research_scheduler.py` | APScheduler job for daily research |
| `backend/services/research_context.py` | Gathers platform context (concerns, gaps, opportunities) |
| `backend/services/agent_observer.py` | Monitors agent conversations, detects knowledge gaps |
| `backend/services/web_researcher.py` | Web search integration with credibility filtering |
| `backend/api/routes/research.py` | API endpoints for research management |
| `database/migrations/011_research_system.sql` | Research tasks and schedule tables |

### Modified Files
| File | Changes |
|------|---------|
| `backend/agents/atlas.py` | Add web search capability, research synthesis methods |
| `backend/main.py` | Register research scheduler on startup |
| `backend/services/graph/sync_service.py` | Sync research artifacts to Neo4j |

---

## Current State

**Atlas Today:**
- Responds to user queries with research synthesis
- Embodies Chris Baumgartner persona (Lean/operational excellence)
- Has access to Mem0, Supabase, Anthropic Claude
- Can hand off to other agents (Fortuna, Guardian, Counselor, Oracle)

**Existing Infrastructure:**
- `sync_scheduler.py` - APScheduler pattern for background jobs (used for Google Drive sync)
- `agent_knowledge_base` table - Links documents to agents with priority scoring
- Neo4j graph - Stakeholders, concerns, insights, ROI opportunities
- Mem0 - Cross-session memory (structure exists, needs full implementation)

---

## Proposed Architecture

### Three Operating Modes for Atlas

```
┌─────────────────────────────────────────────────────────────────┐
│                        ATLAS OPERATING MODES                     │
├─────────────────┬─────────────────────┬─────────────────────────┤
│   REACTIVE      │    OBSERVATIONAL    │      PROACTIVE          │
│   (Current)     │      (New)          │        (New)            │
├─────────────────┼─────────────────────┼─────────────────────────┤
│ User asks       │ Monitors other      │ Daily scheduled         │
│ question →      │ agent activity →    │ research runs →         │
│ Atlas answers   │ Notes patterns      │ Publishes findings      │
└─────────────────┴─────────────────────┴─────────────────────────┘
```

---

## Component 1: Research Task Scheduler

**New file:** `backend/services/research_scheduler.py`

```python
# Pattern mirrors sync_scheduler.py
class ResearchScheduler:
    def __init__(self, supabase, anthropic_client):
        self.scheduler = BackgroundScheduler(timezone='UTC')
        self.atlas = AtlasAgent(supabase, anthropic_client)

    def start(self):
        # Daily research at 6 AM UTC
        self.scheduler.add_job(
            func=self.run_daily_research,
            trigger=CronTrigger(hour=6, minute=0),
            id='atlas_daily_research'
        )

    async def run_daily_research(self):
        # 1. Gather context (what needs research?)
        # 2. Generate research queries
        # 3. Execute Atlas research
        # 4. Store results to knowledge base
```

**Scheduling Options:**
| Schedule | Research Focus |
|----------|----------------|
| Daily 6 AM | Context-driven research based on stakeholder concerns |
| Monday | Strategic planning / C-suite engagement patterns |
| Tuesday | Finance use cases / ROI benchmarks |
| Wednesday | IT governance / compliance frameworks |
| Thursday | Change management / adoption patterns |
| Friday | Weekly synthesis + emerging trends |

---

## Component 2: Context Awareness System

Atlas needs to understand "what we're all working on." Three context sources:

### A. Stakeholder Concerns (from Graph)
```sql
-- Unresolved concerns drive research
SELECT content, stakeholder_name, department
FROM stakeholder_insights
WHERE insight_type = 'concern' AND is_resolved = FALSE
```

### B. Agent Activity (from Conversations)
```sql
-- What are other agents discussing?
SELECT agent_name, message_content, created_at
FROM conversations c
JOIN messages m ON c.id = m.conversation_id
WHERE m.role = 'assistant'
  AND m.created_at > NOW() - INTERVAL '7 days'
```

### C. ROI Opportunities (from Business Intelligence)
```sql
-- Opportunities needing research support
SELECT title, department, estimated_value, status
FROM roi_opportunities
WHERE status IN ('identified', 'evaluating')
```

### Context Aggregation Service

**New file:** `backend/services/research_context.py`

```python
class ResearchContextService:
    async def get_research_priorities(self, client_id: str) -> list[ResearchTopic]:
        """
        Analyzes platform state to determine what Atlas should research.
        Returns prioritized list of research topics with rationale.
        """
        concerns = await self.get_unresolved_concerns(client_id)
        opportunities = await self.get_pending_opportunities(client_id)
        agent_gaps = await self.identify_knowledge_gaps(client_id)

        return self.prioritize_topics(concerns, opportunities, agent_gaps)
```

---

## Component 3: Research Execution Pipeline

### Step 1: Query Generation
```python
def generate_research_query(topic: ResearchTopic) -> str:
    """
    Transform a research topic into an Atlas-friendly query.

    Example:
    Topic: Finance concern about AI ROI measurement
    Query: "What are proven frameworks for measuring AI ROI in Finance
            departments? Include specific metrics, benchmarks from
            comparable companies, and common pitfalls."
    """
```

### Step 2: Atlas Execution
```python
async def execute_research(query: str, context: ResearchContext) -> ResearchOutput:
    # Build agent context with relevant memories
    agent_context = AgentContext(
        user_id="system_atlas",
        client_id=context.client_id,
        conversation_id=uuid4(),
        message_history=[],
        user_message=query,
        memories=await get_relevant_memories(query)
    )

    # Execute Atlas
    response = await atlas.process(agent_context)

    return ResearchOutput(
        content=response.content,
        topic=context.topic,
        stakeholder_relevance=context.stakeholders,
        generated_at=datetime.now(timezone.utc)
    )
```

### Step 3: Quality Validation
```python
def validate_research_output(output: ResearchOutput) -> ValidationResult:
    """
    Ensure research meets quality standards before storing.

    Checks:
    - Contains actionable insights (not just theory)
    - Includes specific metrics/benchmarks
    - Has proper citations
    - Minimum substantive length
    - Doesn't duplicate recent research
    """
```

---

## Component 4: Knowledge Contribution Pipeline

### Storage Strategy

Research outputs become documents in the knowledge base:

```python
async def store_research(output: ResearchOutput) -> Document:
    # 1. Create document record
    doc = await supabase.table('documents').insert({
        'filename': f"atlas_research_{output.topic.slug}_{date}.md",
        'file_type': 'research_artifact',
        'content': output.content,
        'metadata': {
            'generated_by': 'atlas',
            'topic': output.topic.name,
            'stakeholders': output.stakeholder_relevance,
            'quality_score': output.validation.score
        }
    })

    # 2. Link to Atlas knowledge base
    await supabase.table('agent_knowledge_base').insert({
        'agent_id': ATLAS_AGENT_ID,
        'document_id': doc.id,
        'priority': calculate_priority(output),
        'notes': f"Auto-generated research on {output.topic.name}"
    })

    # 3. Optionally link to other relevant agents
    for agent_id in get_relevant_agents(output.topic):
        await link_to_agent_kb(agent_id, doc.id)

    # 4. Save key insights to Mem0
    await save_to_mem0(output.key_insights)

    return doc
```

### Cross-Agent Knowledge Sharing

Research relevant to other agents gets linked to their knowledge bases:

| Research Topic | Primary Agent | Also Relevant To |
|----------------|---------------|------------------|
| Finance AI ROI | Atlas | Fortuna, Strategist |
| Compliance frameworks | Atlas | Guardian, Counselor |
| Change management | Atlas | Sage, Catalyst |
| Technical architecture | Atlas | Architect, Guardian |

---

## Component 5: Observational Learning

Atlas should "observe" what other agents are doing to:
1. Avoid duplicating research they've already covered
2. Identify gaps in collective knowledge
3. Provide supporting research for ongoing conversations

### Agent Activity Monitor

```python
class AgentActivityMonitor:
    async def get_recent_topics(self, days: int = 7) -> list[TopicSummary]:
        """
        Analyze recent agent conversations to understand current focus areas.
        """
        conversations = await self.get_recent_conversations(days)

        return [
            TopicSummary(
                agent='fortuna',
                topics=['ROI modeling', 'SOX compliance'],
                open_questions=['What's industry-standard payback period?']
            ),
            TopicSummary(
                agent='guardian',
                topics=['Shadow AI governance', 'Vendor security'],
                open_questions=['Best practices for AI use policies?']
            )
        ]
```

### Research Gap Detection

```python
async def identify_knowledge_gaps() -> list[ResearchGap]:
    """
    Find questions asked but not well-answered across agents.

    Example gaps:
    - User asked about "AI ethics frameworks" but no agent had substantive answer
    - Multiple conversations about "change resistance" without research backing
    """
```

---

## Database Schema Additions

### New Table: `research_tasks`

```sql
CREATE TABLE research_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id),
    topic VARCHAR(255) NOT NULL,
    query TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',  -- pending, running, completed, failed
    priority INTEGER DEFAULT 5,
    context JSONB,  -- stakeholders, concerns, opportunities driving this
    result_document_id UUID REFERENCES documents(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    error_message TEXT
);

CREATE INDEX idx_research_tasks_status ON research_tasks(status);
CREATE INDEX idx_research_tasks_client ON research_tasks(client_id);
```

### New Table: `research_schedule`

```sql
CREATE TABLE research_schedule (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id),
    day_of_week INTEGER,  -- 0=Sunday, 1=Monday, etc.
    focus_area VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Default schedule
INSERT INTO research_schedule (client_id, day_of_week, focus_area) VALUES
(NULL, 1, 'strategic_planning'),
(NULL, 2, 'finance_roi'),
(NULL, 3, 'governance_compliance'),
(NULL, 4, 'change_management'),
(NULL, 5, 'weekly_synthesis');
```

---

## API Endpoints

### Research Management

```
GET  /api/research/tasks              - List research tasks
POST /api/research/tasks              - Create manual research task
GET  /api/research/tasks/{id}         - Get task details + results
POST /api/research/trigger            - Trigger immediate research run

GET  /api/research/schedule           - Get research schedule
PUT  /api/research/schedule           - Update schedule

GET  /api/research/insights           - Get recent research insights
GET  /api/research/gaps               - Get identified knowledge gaps
```

### Atlas-Specific Extensions

```
GET  /api/agents/atlas/activity       - What has Atlas researched recently?
GET  /api/agents/atlas/contributions  - Documents Atlas has created
GET  /api/agents/atlas/impact         - How often is Atlas research referenced?
```

---

## User Interface Considerations

### Admin Dashboard: Research Overview

```
┌──────────────────────────────────────────────────────────────┐
│  Atlas Research Intelligence                                  │
├──────────────────────────────────────────────────────────────┤
│  This Week's Research                                         │
│  ├─ Monday: "C-Suite AI Governance Patterns" ✅               │
│  ├─ Tuesday: "Finance Automation ROI Benchmarks" ✅           │
│  ├─ Wednesday: [Running...] Compliance Frameworks             │
│  ├─ Thursday: Change Management (Scheduled)                   │
│  └─ Friday: Weekly Synthesis (Scheduled)                      │
│                                                               │
│  Driven By:                                                   │
│  • 3 unresolved stakeholder concerns                          │
│  • 2 pending ROI opportunities                                │
│  • Fortuna asked about payback benchmarks                     │
│                                                               │
│  [View All Research] [Trigger Now] [Edit Schedule]            │
└──────────────────────────────────────────────────────────────┘
```

---

## Implementation Sequence

### Phase 1: Core Research Infrastructure
**Goal:** Atlas can run scheduled research and store results

1. Create `backend/services/research_scheduler.py`
   - APScheduler integration (mirror sync_scheduler.py pattern)
   - Daily research job at configurable time
   - Manual trigger endpoint

2. Create `database/migrations/011_research_system.sql`
   - `research_tasks` table (topic, status, result)
   - `research_schedule` table (day, focus_area)
   - `research_sources` table (url, credibility_tier)

3. Create `backend/api/routes/research.py`
   - `POST /research/trigger` - manual research run
   - `GET /research/tasks` - list research history
   - `GET /research/schedule` - view/edit schedule

4. Modify `backend/main.py`
   - Register research scheduler on startup

### Phase 2: Web Search Integration
**Goal:** Atlas can search the web for fresh information

1. Create `backend/services/web_researcher.py`
   - Web search execution (Anthropic web search or external API)
   - Source credibility filtering (Tier 1-4)
   - Result caching to avoid duplicate searches

2. Modify `backend/agents/atlas.py`
   - Add `research_with_web()` method
   - Integrate web results into synthesis
   - Source citation formatting

### Phase 3: Agent Observation
**Goal:** Atlas understands what other agents are working on

1. Create `backend/services/agent_observer.py`
   - Query recent conversations by agent
   - Detect knowledge gaps (uncertainty signals)
   - Summarize agent focus areas

2. Create `backend/services/research_context.py`
   - Aggregate stakeholder concerns
   - Aggregate ROI opportunities
   - Generate prioritized research topics

3. Modify research scheduler
   - Use context service to drive topic selection
   - Balance global vs client-specific research

### Phase 4: Knowledge Distribution
**Goal:** Research auto-publishes and links to relevant agents

1. Implement auto-publish pipeline
   - Create document from research output
   - Link to Atlas knowledge base
   - Classify topics and link to relevant agents

2. Modify `backend/services/graph/sync_service.py`
   - Sync research documents to Neo4j
   - Create relationships to stakeholders/concepts

3. Implement Mem0 integration
   - Save key insights as memories
   - Query memories to avoid duplication

### Phase 5: Admin UI (Optional)
**Goal:** Visibility into Atlas research activity

1. Research dashboard page
   - Recent research with status
   - Schedule configuration
   - Knowledge gap visualization
   - Impact metrics (if agents reference research)

---

## Web Search Integration

Atlas will use web search (via Anthropic's built-in web search or a dedicated tool) to:

### Research Types Requiring Web Search
| Type | Example Query | Freshness Need |
|------|---------------|----------------|
| Industry news | "GenAI enterprise adoption 2025" | Very fresh (days) |
| Case studies | "JPMorgan AI implementation results" | Recent (months) |
| Consulting reports | "McKinsey AI adoption statistics 2024-2025" | Recent (months) |
| Regulatory updates | "EU AI Act implementation timeline" | Very fresh (days) |
| Vendor announcements | "Anthropic Claude enterprise features" | Very fresh (days) |

### Web Search Implementation
```python
class AtlasWebResearcher:
    async def research_with_web(self, topic: str, context: ResearchContext) -> ResearchOutput:
        # 1. Generate search queries from topic
        queries = self.generate_search_queries(topic)

        # 2. Execute web searches
        web_results = await self.execute_searches(queries)

        # 3. Filter and rank results by credibility
        credible_sources = self.filter_credible_sources(web_results)

        # 4. Synthesize with Atlas persona
        return await self.atlas.synthesize_research(
            topic=topic,
            web_sources=credible_sources,
            context=context
        )
```

### Source Credibility Tiers
| Tier | Sources | Trust Level |
|------|---------|-------------|
| Tier 1 | McKinsey, BCG, Gartner, Forrester, MIT Sloan, HBR | High - cite directly |
| Tier 2 | Big 4 reports, major tech companies, academic papers | High - cite directly |
| Tier 3 | Industry publications, reputable news (WSJ, FT) | Medium - verify claims |
| Tier 4 | Blog posts, vendor marketing | Low - use for signals only |

---

## Deep Agent Integration

### Observation Layer

Atlas monitors all agent activity to understand platform-wide context:

```python
class AgentObserver:
    async def get_platform_context(self) -> PlatformContext:
        return PlatformContext(
            recent_conversations=await self.get_recent_agent_chats(days=7),
            unanswered_questions=await self.identify_knowledge_gaps(),
            active_stakeholders=await self.get_engaged_stakeholders(),
            pending_opportunities=await self.get_roi_pipeline(),
            agent_topics=await self.summarize_agent_focus_areas()
        )
```

### Gap Detection

Identify questions agents couldn't fully answer:

```python
async def detect_knowledge_gaps() -> list[KnowledgeGap]:
    """
    Analyze conversations for:
    - Questions answered with uncertainty ("I'm not sure but...")
    - Follow-up questions indicating incomplete answers
    - Requests for "more research" or "more data"
    - Topics with no supporting documents in KB
    """
```

### Anticipatory Research

Predict what agents will need based on patterns:

| Trigger | Anticipatory Research |
|---------|----------------------|
| New stakeholder added (Finance) | Prepare Finance AI use cases |
| ROI opportunity created | Research supporting benchmarks |
| Guardian discussing security | Prepare compliance frameworks |
| Sage discussing change mgmt | Research adoption patterns |

### Cross-Agent Knowledge Contribution

When Atlas produces research, automatically link to relevant agents:

```python
AGENT_TOPIC_MAPPING = {
    'roi': ['fortuna', 'strategist'],
    'compliance': ['guardian', 'counselor'],
    'change_management': ['sage', 'catalyst'],
    'architecture': ['architect', 'guardian'],
    'adoption': ['sage', 'scholar'],
    'security': ['guardian', 'architect'],
    'contracts': ['counselor'],
    'innovation': ['pioneer'],
}

async def distribute_research(output: ResearchOutput):
    # 1. Classify research topics
    topics = classify_topics(output.content)

    # 2. Link to all relevant agent KBs
    for topic in topics:
        for agent_name in AGENT_TOPIC_MAPPING.get(topic, []):
            await link_to_agent_kb(agent_name, output.document_id)

    # 3. Always link to Atlas
    await link_to_agent_kb('atlas', output.document_id)
```

---

## Global vs Client-Specific Research

### Two-Layer Research Model

```
┌─────────────────────────────────────────────────────────────┐
│                    GLOBAL RESEARCH LAYER                     │
│  (Shared across all clients - industry trends, benchmarks)   │
├─────────────────────────────────────────────────────────────┤
│  • GenAI adoption statistics (monthly)                       │
│  • Consulting firm best practices (weekly)                   │
│  • Regulatory updates (as needed)                            │
│  • Technology announcements (as needed)                      │
│  • Academic research summaries (monthly)                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                CLIENT-SPECIFIC RESEARCH LAYER                │
│  (Tailored to each client's stakeholders and concerns)       │
├─────────────────────────────────────────────────────────────┤
│  • Research driven by stakeholder concerns                   │
│  • Industry-specific case studies (client's industry)        │
│  • Department-specific deep dives (based on active depts)    │
│  • ROI opportunity support research                          │
│  • Anticipatory research based on agent conversations        │
└─────────────────────────────────────────────────────────────┘
```

### Global Research Schedule
| Frequency | Research Type |
|-----------|---------------|
| Daily | News scan - major AI announcements, regulatory |
| Weekly | Consulting firm publications, case study digest |
| Monthly | Industry benchmarks synthesis, trend analysis |

### Client-Specific Research Triggers
| Trigger | Research Action |
|---------|-----------------|
| New stakeholder with concern | Research addressing that concern |
| ROI opportunity created | Benchmark data for that use case |
| Agent couldn't answer question | Fill the knowledge gap |
| Meeting transcript analyzed | Follow-up research on key topics |
