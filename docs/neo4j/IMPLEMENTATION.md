# Neo4j Graph Integration - Implementation Reference

> **Status**: Complete - Ready for testing
> **Last Updated**: 2025-12-26

## Overview

This document describes the implemented Neo4j graph integration for the Thesis multi-agent platform. The integration syncs data from Supabase (source of truth) to Neo4j for graph-based queries on stakeholder networks, agent coordination, and relationship analysis.

## Architecture

```
Supabase (PostgreSQL)          Neo4j (Graph)
────────────────────           ────────────────
    Source of Truth     →      Derived View

    stakeholders        →      (:Stakeholder)
    meeting_transcripts →      (:Meeting)
    stakeholder_insights →     (:Insight), (:Concern)
    documents           →      (:Document)
    roi_opportunities   →      (:ROIOpportunity)
    agents              →      (:Agent)
                        →      (:Concept) [extracted]
                        →      (:Cluster) [inferred]
```

## File Structure

```
backend/services/graph/
├── __init__.py                 # Module exports
├── connection.py               # Async Neo4j driver management
├── schema.py                   # Constraints, indexes, Cypher templates
├── sync_service.py             # Supabase → Neo4j synchronization
├── query_service.py            # Graph queries for API
└── relationship_extractor.py   # LLM-based relationship inference

backend/api/routes/
└── graph.py                    # REST API endpoints

database/migrations/
└── 004_graph_sync_tracking.sql # Sync state tables
```

## Environment Variables

```bash
# Required
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_PASSWORD=your-password

# Optional (have defaults)
NEO4J_USERNAME=neo4j
NEO4J_DATABASE=neo4j
```

## Node Types

| Node | Properties | Source |
|------|------------|--------|
| `Stakeholder` | id, name, role, organization, client_id, sentiment_score, total_interactions | stakeholders table |
| `Meeting` | id, title, meeting_date, meeting_type, client_id | meeting_transcripts table |
| `Insight` | id, insight_type, content, confidence | stakeholder_insights table |
| `Concern` | id, content, severity | Derived from insights |
| `Document` | id, title, doc_type, summary, client_id | documents table |
| `ROIOpportunity` | id, title, status, annual_savings, client_id | roi_opportunities table |
| `Agent` | id, name, display_name, description, is_active | agents table |
| `Concept` | name, category | LLM-extracted from transcripts |
| `Cluster` | name, client_id, size | Inferred from patterns |

## Relationship Types

| Relationship | Properties | Description |
|--------------|------------|-------------|
| `(:Stakeholder)-[:REPORTS_TO]->(:Stakeholder)` | - | Org hierarchy |
| `(:Stakeholder)-[:INFLUENCES]->(:Stakeholder)` | strength, influence_type | Inferred influence |
| `(:Stakeholder)-[:ATTENDED]->(:Meeting)` | sentiment, speaking_time | Meeting attendance |
| `(:Stakeholder)-[:HAS_INSIGHT]->(:Insight)` | - | Insight ownership |
| `(:Stakeholder)-[:RAISED_CONCERN]->(:Concern)` | quote | Concern attribution |
| `(:Stakeholder)-[:SUPPORTS]->(:ROIOpportunity)` | commitment_level | ROI champions |
| `(:Stakeholder)-[:BLOCKS]->(:ROIOpportunity)` | reason | ROI blockers |
| `(:Meeting)-[:DISCUSSES]->(:Concept)` | frequency | Topic coverage |
| `(:Agent)-[:EXPERT_IN]->(:Concept)` | confidence | Agent expertise |
| `(:Agent)-[:HANDED_OFF_TO]->(:Agent)` | conversation_id, reason, timestamp | Agent coordination |
| `(:Stakeholder)-[:MEMBER_OF]->(:Cluster)` | - | Cluster membership |

## API Endpoints

### Health & Admin
```
GET  /api/graph/health              # Neo4j connection health
POST /api/graph/schema/init         # Initialize constraints/indexes (admin)
GET  /api/graph/schema/verify       # Verify schema state
GET  /api/graph/stats               # Graph statistics for client
```

### Sync Operations
```
POST /api/graph/sync/full           # Full sync for client
POST /api/graph/sync/incremental    # Incremental sync since timestamp
POST /api/graph/sync/stakeholders   # Sync stakeholders only
```

### Stakeholder Network
```
GET  /api/graph/stakeholder/{id}/network     # Network around stakeholder
GET  /api/graph/stakeholder/{id}/concerns    # Stakeholder's concerns
GET  /api/graph/stakeholder/{id}/aligned     # Aligned stakeholders
GET  /api/graph/influence/path               # Path between stakeholders
GET  /api/graph/influence/key-influencers    # Top influencers
GET  /api/graph/influence/chains/{target_id} # Influence chains to target
```

### ROI Analysis
```
GET  /api/graph/roi/{id}/analysis   # Full blocker/supporter analysis
GET  /api/graph/roi/{id}/blockers   # Who is blocking
GET  /api/graph/roi/{id}/strategy   # Recommended approach
```

### Meeting & Concepts
```
GET  /api/graph/meeting/{id}/network         # Meeting attendee network
GET  /api/graph/concepts/{name}/advocates    # Who discusses this topic
GET  /api/graph/concerns/shared              # Shared concerns
```

### Agent Routing
```
GET  /api/graph/agents/routing               # Suggest agent for question
GET  /api/graph/agents/{id}/expertise        # Agent's expertise areas
GET  /api/graph/agents/handoff-patterns      # Handoff frequency analysis
```

### Relationship Inference
```
POST /api/graph/infer/influences             # Infer influence from patterns
POST /api/graph/infer/concepts               # Extract concepts from meetings
POST /api/graph/infer/clusters               # Detect stakeholder clusters
POST /api/graph/meetings/{id}/concepts       # Extract concepts from one meeting
```

## Key Cypher Queries

### Influence Path Finding
```cypher
MATCH path = shortestPath(
    (a:Stakeholder {id: $from_id})-[:INFLUENCES|REPORTS_TO*..5]-(b:Stakeholder {id: $to_id})
)
RETURN path
```

### ROI Blocker Strategy
```cypher
MATCH (blocker:Stakeholder)-[:BLOCKS]->(o:ROIOpportunity {id: $id})
MATCH (supporter:Stakeholder)-[:SUPPORTS]->(o)
OPTIONAL MATCH path = (supporter)-[:INFLUENCES*1..3]->(blocker)
RETURN blocker, supporter, path
```

### Agent Routing
```cypher
MATCH (a:Agent)-[e:EXPERT_IN]->(c:Concept)
WHERE c.name IN $concepts AND a.is_active = true
WITH a, sum(e.confidence) as relevance
RETURN a.name, relevance
ORDER BY relevance DESC
LIMIT 1
```

## Agent Expertise Mapping

The sync service automatically creates EXPERT_IN relationships:

| Agent | Expertise Concepts |
|-------|-------------------|
| Atlas | research, consulting, case studies, thought leadership, genai |
| Fortuna | roi, finance, budget, cost savings, investment |
| Guardian | governance, security, infrastructure, it, compliance |
| Counselor | legal, contracts, compliance, risk, policy |
| Oracle | transcripts, meetings, stakeholders, sentiment, insights |

## Sync Behavior

### Full Sync Order
1. Agents (global, synced first)
2. Stakeholders (with REPORTS_TO, INFLUENCES relationships)
3. Meetings (with ATTENDED relationships)
4. Insights (with HAS_INSIGHT, RAISED_CONCERN)
5. Documents
6. ROI Opportunities (with SUPPORTS, BLOCKS)

### Sync Patterns
- **Upsert**: Uses MERGE to handle creates and updates
- **Fire-and-forget**: Sync errors are logged but don't break the app
- **One-way**: Supabase → Neo4j only (Neo4j is derived view)

## Database Tables

### graph_sync_log
Tracks individual sync operations for auditing.

```sql
CREATE TABLE graph_sync_log (
    id UUID PRIMARY KEY,
    client_id UUID REFERENCES clients(id),
    sync_type TEXT,        -- 'full', 'incremental', 'entity'
    entity_type TEXT,
    entity_id UUID,
    synced_at TIMESTAMPTZ,
    sync_status TEXT,      -- 'started', 'completed', 'failed'
    details JSONB,
    error_message TEXT,
    duration_ms INTEGER
);
```

### graph_sync_state
Tracks last sync time per entity type for incremental sync.

```sql
CREATE TABLE graph_sync_state (
    client_id UUID,
    entity_type TEXT,
    last_synced_at TIMESTAMPTZ,
    last_sync_status TEXT,
    record_count INTEGER,
    UNIQUE(client_id, entity_type)
);
```

## Usage Examples

### Trigger Full Sync
```python
from services.graph import GraphSyncService, get_neo4j_connection
from database import get_supabase_client

supabase = get_supabase_client()
neo4j = await get_neo4j_connection()
sync = GraphSyncService(supabase, neo4j)

result = await sync.full_sync(client_id="your-client-id")
print(result)
# {'agents': {'synced': 5}, 'stakeholders': {'synced': 12}, ...}
```

### Query Influence Network
```python
from services.graph import GraphQueryService, get_neo4j_connection

neo4j = await get_neo4j_connection()
query = GraphQueryService(neo4j)

network = await query.get_stakeholder_network(
    stakeholder_id="stakeholder-uuid",
    depth=2
)
```

### Infer Relationships
```python
from services.graph import RelationshipExtractor, get_neo4j_connection
from database import get_supabase_client

supabase = get_supabase_client()
neo4j = await get_neo4j_connection()
extractor = RelationshipExtractor(supabase, neo4j)

# Infer who influences whom
await extractor.infer_influences(client_id)

# Extract concepts from meetings
await extractor.extract_all_meeting_concepts(client_id)
```

## Testing Checklist

- [ ] Neo4j connection established (check `/api/graph/health`)
- [ ] Schema initialized (`POST /api/graph/schema/init`)
- [ ] Full sync completes (`POST /api/graph/sync/full`)
- [ ] Stakeholder network queries return data
- [ ] Influence path finding works
- [ ] Agent routing suggests correct agents
- [ ] Concept extraction runs without errors

## Troubleshooting

### Connection Issues
- Verify `NEO4J_URI` includes `neo4j+s://` protocol
- Check password doesn't have special characters that need escaping
- Ensure Neo4j Aura instance is running

### Sync Failures
- Check `graph_sync_log` table for error details
- Verify Supabase tables have expected columns
- Look for constraint violations in Neo4j

### Query Performance
- Run `SHOW INDEXES` to verify indexes exist
- Check if queries are using indexes with `EXPLAIN`
- Consider adding composite indexes for common query patterns
