# Neo4j ↔ Supabase Sync Implementation Plan

> **Context**: Thesis is a multi-agent platform with Supabase (PostgreSQL) as the primary database. Neo4j provides comprehensive graph capabilities for stakeholder networks, agent coordination, knowledge graph, and semantic relationships across ALL platform data.

## Design Principles

1. **Comprehensive Coverage**: Every entity in the platform is graphed - documents, transcripts, conversations, meetings, stakeholders, agents, and all their relationships
2. **One-Way Sync**: Supabase is source of truth. Neo4j is a derived graph view.
3. **Relationship-First**: The value is in the connections - inferred relationships, concept links, influence patterns
4. **Multi-Tenant Isolation**: All nodes include `client_id` for data isolation

---

## Complete Entity Mapping

### Core Entities (Direct Sync from Supabase)

| Supabase Table | Neo4j Node | Properties | Priority |
|----------------|------------|------------|----------|
| `clients` | `:Client` | id, name, assistant_name | P0 |
| `users` | `:User` | id, email, name, role, client_id | P0 |
| `agents` | `:Agent` | id, name, display_name, persona, is_active | P0 |
| `documents` | `:Document` | id, filename, file_type, source_platform, client_id, is_core_document | P0 |
| `document_chunks` | `:Chunk` | id, document_id, chunk_index, content (truncated) | P1 |
| `conversations` | `:Conversation` | id, title, user_id, client_id, archived, in_knowledge_base | P0 |
| `messages` | `:Message` | id, conversation_id, role, content (truncated), agent_id | P1 |
| `meeting_transcripts` | `:Meeting` | id, title, meeting_date, meeting_type, client_id | P0 |
| `meeting_rooms` | `:MeetingRoom` | id, name, description, client_id, status | P0 |
| `meeting_room_messages` | `:MeetingRoomMessage` | id, meeting_room_id, agent_id, content (truncated) | P1 |
| `stakeholders` | `:Stakeholder` | id, name, role, organization, sentiment_score, client_id | P0 |
| `stakeholder_insights` | `:Insight` | id, insight_type, content, confidence, sentiment | P0 |
| `roi_opportunities` | `:ROIOpportunity` | id, title, status, annual_savings, client_id | P0 |
| `agent_instruction_versions` | `:AgentInstruction` | id, agent_id, version, is_active | P2 |

### Inferred Entities (LLM-Extracted)

| Entity | Source | Neo4j Node | Extraction Method |
|--------|--------|------------|-------------------|
| Concepts/Topics | Document chunks, Transcripts, Messages | `:Concept` | LLM topic extraction |
| Concerns | Stakeholder insights | `:Concern` | Insight parsing |
| Action Items | Meeting transcripts | `:ActionItem` | LLM extraction |
| Skills/Expertise | Agent instructions, KB docs | `:Expertise` | LLM analysis |

### Relationship Types

**Organizational/Structural:**
```
(:User)-[:BELONGS_TO]->(:Client)
(:Document)-[:OWNED_BY]->(:Client)
(:Document)-[:UPLOADED_BY]->(:User)
(:Chunk)-[:PART_OF]->(:Document)
(:Message)-[:IN_CONVERSATION]->(:Conversation)
(:Conversation)-[:OWNED_BY]->(:User)
```

**Agent-Related:**
```
(:Agent)-[:HAS_KNOWLEDGE_OF {priority}]->(:Document)
(:Agent)-[:EXPERT_IN {confidence}]->(:Expertise)
(:Agent)-[:HANDED_OFF_TO {reason, timestamp}]->(:Agent)
(:Agent)-[:PARTICIPATED_IN]->(:MeetingRoom)
(:Agent)-[:AUTHORED]->(:Message)
(:Agent)-[:AUTHORED]->(:MeetingRoomMessage)
```

**Stakeholder-Related:**
```
(:Stakeholder)-[:REPORTS_TO]->(:Stakeholder)
(:Stakeholder)-[:INFLUENCES {strength, type}]->(:Stakeholder)
(:Stakeholder)-[:ATTENDED {sentiment, speaking_time}]->(:Meeting)
(:Stakeholder)-[:HAS_INSIGHT]->(:Insight)
(:Stakeholder)-[:SUPPORTS {commitment_level}]->(:ROIOpportunity)
(:Stakeholder)-[:BLOCKS {reason}]->(:ROIOpportunity)
(:Stakeholder)-[:RAISED]->(:Concern)
(:Stakeholder)-[:ASSIGNED]->(:ActionItem)
```

**Semantic/Content:**
```
(:Document)-[:DISCUSSES {frequency}]->(:Concept)
(:Chunk)-[:MENTIONS]->(:Concept)
(:Meeting)-[:DISCUSSES {frequency}]->(:Concept)
(:Conversation)-[:ABOUT]->(:Concept)
(:Message)-[:REFERENCES]->(:Document)
(:Insight)-[:RELATES_TO]->(:Concept)
(:Concept)-[:RELATED_TO {strength}]->(:Concept)
```

**Cross-Entity:**
```
(:Conversation)-[:MENTIONS]->(:Stakeholder)
(:Document)-[:ABOUT]->(:Stakeholder)
(:Meeting)-[:GENERATED]->(:Insight)
(:Meeting)-[:IDENTIFIED]->(:ROIOpportunity)
```

---

## Implementation Tasks

### Phase 1: Sync Service Foundation

#### 1.1 Create Base Sync Service
**File**: `backend/services/graph/sync_service.py`

```python
class GraphSyncService:
    """
    Handles bidirectional sync between Supabase and Neo4j.
    Supabase is source of truth - Neo4j is derived.
    """

    async def sync_stakeholder(self, stakeholder_id: UUID) -> None
    async def sync_meeting(self, meeting_id: UUID) -> None
    async def sync_roi_opportunity(self, roi_id: UUID) -> None
    async def full_sync(self, client_id: UUID) -> SyncResult
    async def delete_node(self, node_type: str, node_id: UUID) -> None
```

**Key Design Decisions:**
- One-way sync: Supabase → Neo4j (never write back to Supabase from Neo4j)
- Upsert pattern: Use MERGE in Cypher to handle creates and updates
- ID mapping: Use Supabase UUIDs as Neo4j node IDs (no separate mapping table)

#### 1.2 Relationship Inference
**File**: `backend/services/graph/relationship_extractor.py`

Neo4j's value comes from relationships. We need to infer relationships that aren't explicit in Supabase:

```python
class RelationshipExtractor:
    """
    Infers graph relationships from Supabase data.
    """

    async def infer_influences(self, client_id: UUID) -> list[Influence]
        """
        Analyze meeting co-attendance and interaction patterns
        to infer who influences whom.
        """

    async def extract_concepts(self, meeting_id: UUID) -> list[Concept]
        """
        Use LLM to extract key concepts/topics from meeting transcripts.
        """

    async def detect_stakeholder_clusters(self, client_id: UUID) -> list[Cluster]
        """
        Identify natural groupings of stakeholders based on
        meeting patterns and shared concerns.
        """
```

---

### Phase 2: Sync Triggers

#### 2.1 Event-Driven Sync via Supabase Webhooks
**Option A: Supabase Database Webhooks**
```sql
-- In Supabase, create webhook triggers
CREATE OR REPLACE FUNCTION notify_graph_sync()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify('graph_sync', json_build_object(
        'table', TG_TABLE_NAME,
        'action', TG_OP,
        'id', NEW.id
    )::text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER stakeholder_graph_sync
AFTER INSERT OR UPDATE ON stakeholders
FOR EACH ROW EXECUTE FUNCTION notify_graph_sync();

CREATE TRIGGER meeting_graph_sync
AFTER INSERT OR UPDATE ON meeting_transcripts
FOR EACH ROW EXECUTE FUNCTION notify_graph_sync();

CREATE TRIGGER roi_graph_sync
AFTER INSERT OR UPDATE ON roi_opportunities
FOR EACH ROW EXECUTE FUNCTION notify_graph_sync();
```

**Option B: Application-Level Sync (Simpler)**
Call sync after each Supabase write in the API routes:

```python
# In stakeholder routes
@router.post("/stakeholders")
async def create_stakeholder(...):
    stakeholder = await supabase.insert(...)

    # Fire-and-forget sync to Neo4j
    background_tasks.add_task(
        graph_sync.sync_stakeholder,
        stakeholder["id"]
    )

    return stakeholder
```

**Recommendation**: Start with Option B (simpler), migrate to Option A when scale requires it.

#### 2.2 Batch Sync for Initial Load
**File**: `backend/scripts/graph/initial_sync.py`

```python
async def initial_sync(client_id: UUID):
    """
    One-time sync of all existing data from Supabase to Neo4j.
    Run this when first setting up Neo4j or after schema changes.
    """
    # 1. Sync all stakeholders
    # 2. Sync all meetings
    # 3. Sync all ROI opportunities
    # 4. Infer and create relationships
    # 5. Extract and link concepts
```

---

### Phase 3: Graph-Specific Features

#### 3.1 Stakeholder Influence Analysis
**API**: `GET /api/graph/stakeholders/{id}/influence`

```cypher
// Find influence chain from a stakeholder to decision makers
MATCH path = (s:Stakeholder {id: $stakeholder_id})-[:INFLUENCES*1..3]->(dm:Stakeholder)
WHERE dm.role CONTAINS 'Director' OR dm.role CONTAINS 'VP' OR dm.role CONTAINS 'Chief'
RETURN path, length(path) as hops
ORDER BY hops
```

#### 3.2 Meeting Network Analysis
**API**: `GET /api/graph/meetings/{id}/network`

```cypher
// Find all stakeholders connected through a meeting and their relationships
MATCH (s:Stakeholder)-[:ATTENDED]->(m:Meeting {id: $meeting_id})<-[:ATTENDED]-(other:Stakeholder)
OPTIONAL MATCH (s)-[r:INFLUENCES|REPORTS_TO]-(other)
RETURN s, other, r, m
```

#### 3.3 Concept Clustering
**API**: `GET /api/graph/concepts/clusters`

```cypher
// Find concepts that frequently appear together in meetings
MATCH (m:Meeting)-[:DISCUSSES]->(c1:Concept)
MATCH (m)-[:DISCUSSES]->(c2:Concept)
WHERE c1.name < c2.name
WITH c1, c2, count(m) as co_occurrences
WHERE co_occurrences > 2
RETURN c1.name, c2.name, co_occurrences
ORDER BY co_occurrences DESC
```

#### 3.4 ROI Opportunity Path Analysis
**API**: `GET /api/graph/roi/{id}/blockers`

```cypher
// Find the path from blockers to supporters - who can influence whom?
MATCH (blocker:Stakeholder)-[:BLOCKS]->(roi:ROIOpportunity {id: $roi_id})
MATCH (supporter:Stakeholder)-[:SUPPORTS]->(roi)
MATCH path = shortestPath((supporter)-[:INFLUENCES*..4]-(blocker))
RETURN blocker, supporter, path
```

---

### Phase 4: Agent Coordination Graph

#### 4.1 Add Agent Nodes
```python
async def sync_agents(self):
    """Sync agent registry to Neo4j."""
    agents = await supabase.table("agents").select("*").execute()

    for agent in agents.data:
        await neo4j.execute_write("""
            MERGE (a:Agent {id: $id})
            SET a.name = $name,
                a.display_name = $display_name,
                a.is_active = $is_active
        """, agent)
```

#### 4.2 Track Agent Handoffs as Relationships
```cypher
// Create handoff relationship
MATCH (from:Agent {id: $from_agent_id})
MATCH (to:Agent {id: $to_agent_id})
CREATE (from)-[:HANDED_OFF_TO {
    conversation_id: $conversation_id,
    reason: $reason,
    timestamp: datetime()
}]->(to)
```

#### 4.3 Agent Expertise Graph
```cypher
// Link agents to concepts they're experts in
MATCH (a:Agent {name: 'fortuna'})
MERGE (c:Concept {name: 'ROI'})
MERGE (a)-[:EXPERT_IN {confidence: 0.95}]->(c)

// Query: Which agent should handle a question about X?
MATCH (a:Agent)-[e:EXPERT_IN]->(c:Concept)
WHERE c.name IN $question_concepts
RETURN a.name, sum(e.confidence) as relevance
ORDER BY relevance DESC
LIMIT 1
```

---

## File Structure

```
backend/services/graph/
├── __init__.py              # ✓ Exists
├── connection.py            # ✓ Exists - Neo4j connection management
├── schema.py                # ✓ Exists - Schema initialization
├── sync_service.py          # NEW - Main sync orchestration
├── relationship_extractor.py # NEW - Infer relationships from data
├── queries/
│   ├── __init__.py
│   ├── stakeholder_queries.py  # Stakeholder-specific graph queries
│   ├── meeting_queries.py      # Meeting network queries
│   ├── roi_queries.py          # ROI path analysis
│   └── agent_queries.py        # Agent coordination queries
└── api/
    └── graph_routes.py      # FastAPI routes for graph endpoints
```

---

## API Endpoints to Add

```
POST   /api/graph/sync/full              # Trigger full sync for a client
POST   /api/graph/sync/stakeholder/{id}  # Sync single stakeholder
GET    /api/graph/health                 # Neo4j health check

GET    /api/graph/stakeholders/{id}/influence    # Influence analysis
GET    /api/graph/stakeholders/{id}/network      # Network visualization data
GET    /api/graph/stakeholders/clusters          # Stakeholder clusters

GET    /api/graph/meetings/{id}/network          # Meeting network
GET    /api/graph/concepts/clusters              # Topic clusters
GET    /api/graph/concepts/{name}/stakeholders   # Who discusses this topic?

GET    /api/graph/roi/{id}/blockers              # Blocker analysis
GET    /api/graph/roi/{id}/path-to-approval      # Influence path to approval

GET    /api/graph/agents/routing                 # Agent expertise mapping
```

---

## Testing the Value Proposition

During the Neo4j trial, track these metrics:

### Queries to Compare
| Query | Supabase (SQL) | Neo4j (Cypher) | Winner |
|-------|---------------|----------------|--------|
| Direct stakeholder lookup | ✓ Fast | ✓ Fast | Tie |
| 2-hop influence chain | Complex CTE | Simple MATCH | ? |
| Shortest path between stakeholders | Very complex | Built-in | ? |
| Cluster detection | Needs application code | Algorithm library | ? |
| Pattern matching (who attended X and discussed Y) | Multiple JOINs | Single MATCH | ? |

### Decision Criteria
Keep Neo4j if:
- Graph queries are 5x+ faster for multi-hop traversals
- You're writing recursive CTEs in Postgres that Neo4j handles natively
- Visualization of stakeholder networks is valuable
- Agent routing benefits from graph-based expertise matching

Drop Neo4j if:
- Most queries are simple 1-hop relationships
- The data volume stays small (<1000 stakeholders)
- Sync complexity isn't worth the insight value
- $65+/month doesn't justify the features used

---

## Implementation Status

> **Last Updated**: December 28, 2024

### Completed Components

| Component | Status | File |
|-----------|--------|------|
| Connection Manager | Done | `backend/services/graph/connection.py` |
| Schema Definition (20 node types) | Done | `backend/services/graph/schema.py` |
| Full Sync Service (15 entity types) | Done | `backend/services/graph/sync_service.py` |
| Relationship Extractor | Done | `backend/services/graph/relationship_extractor.py` |
| Query Service | Done | `backend/services/graph/query_service.py` |
| Graph API Routes | Done | `backend/api/routes/graph.py` |
| Graph Sync Scheduler | Done | `backend/services/graph_sync_scheduler.py` |
| Admin Dashboard Integration | Done | Manual sync trigger in System Health panel |

### Entities Synced

**Core Entities (P0)**:
- [x] Clients
- [x] Users (with BELONGS_TO Client)
- [x] Agents (15 agents with expertise mapping)
- [x] Documents (with UPLOADED_BY User, OWNED_BY Client)
- [x] Conversations (with OWNED_BY User)
- [x] Stakeholders
- [x] Meetings (meeting_transcripts)
- [x] Meeting Rooms
- [x] Insights (stakeholder_insights)
- [x] ROI Opportunities

**Extended Entities (P1)**:
- [x] Document Chunks (with PART_OF Document)
- [x] Messages (with IN_CONVERSATION, AUTHORED by Agent)
- [x] Meeting Room Messages
- [x] Agent Knowledge Base links (HAS_KNOWLEDGE_OF)
- [x] Agent Handoffs (HANDED_OFF_TO)

**Inferred Entities**:
- [x] Concepts (extracted from meetings via LLM)
- [x] Expertise (agent capability areas)
- [x] Clusters (stakeholder groupings)
- [ ] Concerns (pending: insight parsing)
- [ ] Action Items (pending: meeting extraction)

### Cypher Templates (40 total)

The schema includes comprehensive Cypher templates for:
- All CRUD operations for each entity type
- Relationship creation (INFLUENCES, REPORTS_TO, ATTENDED, etc.)
- Agent knowledge and expertise linking
- Cross-entity references (MESSAGE-REFERENCES-DOCUMENT, etc.)

### API Endpoints Available

```
# Health & Admin
GET  /graph/health
POST /graph/schema/init
GET  /graph/schema/verify
GET  /graph/stats

# Sync Operations
POST /graph/sync/full
POST /graph/sync/incremental
POST /graph/sync/stakeholders
POST /graph/sync/trigger              # Manual sync trigger from dashboard
GET  /graph/sync/scheduler-status     # Get scheduler status

# Stakeholder Network
GET  /graph/stakeholder/{id}/network
GET  /graph/stakeholder/{id}/concerns
GET  /graph/stakeholder/{id}/aligned
GET  /graph/influence/path
GET  /graph/influence/key-influencers
GET  /graph/influence/chains/{target_id}

# ROI Analysis
GET  /graph/roi/{id}/analysis
GET  /graph/roi/{id}/blockers
GET  /graph/roi/{id}/strategy

# Meetings & Concepts
GET  /graph/meeting/{id}/network
GET  /graph/concepts/{name}/advocates
GET  /graph/concerns/shared

# Agent Routing
GET  /graph/agents/routing
GET  /graph/agents/{id}/expertise
GET  /graph/agents/handoff-patterns

# Inference Operations
POST /graph/infer/influences
POST /graph/infer/concepts
POST /graph/infer/clusters
POST /graph/meetings/{id}/concepts
```

---

## Remaining Work

1. **Concern & Action Item Extraction**
   - [ ] Parse insights to extract concerns with severity
   - [ ] Extract action items from meeting transcripts
   - [ ] Link to responsible stakeholders

2. **Concept Extraction Enhancement**
   - [ ] Run concept extraction on document chunks
   - [ ] Create RELATED_TO relationships between concepts
   - [ ] Build concept co-occurrence graph

3. **Frontend Integration**
   - [x] Admin dashboard sync trigger button (System Health panel)
   - [ ] Add graph visualization component
   - [ ] Show stakeholder network on profile page
   - [ ] Display influence paths in ROI analysis

4. **Performance Testing**
   - [ ] Benchmark graph queries vs SQL for multi-hop traversals
   - [ ] Test with larger data volumes
   - [ ] Evaluate keep/drop decision

---

## Environment Variables Needed

```bash
# Neo4j Aura connection
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_PASSWORD=your-password
NEO4J_USERNAME=neo4j
NEO4J_DATABASE=neo4j
```

---

## Notes for Implementation Thread

- **Source of truth**: Always Supabase. Neo4j is a derived view.
- **Sync pattern**: Upsert (MERGE) to handle both creates and updates
- **Error handling**: Sync failures should log but not break the main app
- **Background processing**: Use FastAPI BackgroundTasks for sync operations
- **Relationship inference**: This is where the real value is - don't just mirror Supabase
- **Start simple**: Get basic node sync working before adding complex relationship inference
