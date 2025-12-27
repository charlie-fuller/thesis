# Neo4j ↔ Supabase Sync Implementation Plan

> **Context**: Thesis is a multi-agent platform with Supabase (PostgreSQL) as the primary database. We're adding Neo4j to test graph capabilities for stakeholder networks, agent coordination, and concept mapping. The goal is to sync data during the Neo4j trial period to evaluate whether graph queries provide enough value to justify the cost.

## Current State

### Supabase Schema (Source of Truth)
- `stakeholders` - CRM-style stakeholder tracking
- `stakeholder_insights` - Extracted insights from transcripts
- `meeting_transcripts` - Uploaded meeting transcripts
- `roi_opportunities` - Identified ROI opportunities
- `agents` - Agent registry (atlas, fortuna, guardian, counselor, oracle)
- `agent_handoffs` - Agent-to-agent handoff tracking
- `agent_knowledge_base` - Links documents to agents

### Neo4j Schema (Already Defined)
Location: `backend/services/graph/schema.py`

**Nodes:**
- `Stakeholder` - id, name, role, organization, client_id, sentiment_score, total_interactions
- `Agent` - id (need to add)
- `Meeting` - id, title, meeting_date, meeting_type, client_id
- `Insight` - id, insight_type, content, confidence
- `ROIOpportunity` - id, title, status, annual_savings, client_id
- `Concept` - name, category
- `Concern` - id (extracted concerns)
- `Document` - id, client_id

**Relationships:**
- `(:Stakeholder)-[:REPORTS_TO]->(:Stakeholder)`
- `(:Stakeholder)-[:INFLUENCES {strength, influence_type}]->(:Stakeholder)`
- `(:Stakeholder)-[:ATTENDED {sentiment, speaking_time}]->(:Meeting)`
- `(:Stakeholder)-[:HAS_INSIGHT]->(:Insight)`
- `(:Stakeholder)-[:SUPPORTS {commitment_level}]->(:ROIOpportunity)`
- `(:Stakeholder)-[:BLOCKS {reason}]->(:ROIOpportunity)`
- `(:Meeting)-[:DISCUSSES {frequency}]->(:Concept)`

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

## Implementation Order

1. **Week 1**: Sync Service Foundation
   - [ ] Create `sync_service.py` with stakeholder/meeting/ROI sync
   - [ ] Add application-level sync triggers to existing routes
   - [ ] Create initial sync script
   - [ ] Test with sample data

2. **Week 2**: Relationship Inference
   - [ ] Build `relationship_extractor.py`
   - [ ] Add concept extraction (LLM-based)
   - [ ] Create influence inference from co-attendance patterns
   - [ ] Sync relationships to Neo4j

3. **Week 3**: Graph Query API
   - [ ] Implement stakeholder influence queries
   - [ ] Add meeting network endpoints
   - [ ] Build ROI path analysis
   - [ ] Add agent routing queries

4. **Week 4**: Evaluation
   - [ ] Compare query performance
   - [ ] Assess visualization value
   - [ ] Make keep/drop decision before trial ends

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
