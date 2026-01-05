# Stakeholder Profile Method

This document describes the methodology for creating rich stakeholder profiles in Thesis, including the data structure, profile components, and SQL patterns used.

## Overview

Stakeholder profiles in Thesis go beyond basic CRM data to include psychological profiles, communication preferences, relationship dynamics, and strategic intelligence. This enables agents (particularly Oracle and Facilitator) to provide contextually-aware insights during meetings and analysis.

## Database Schema

Stakeholders are stored in the `stakeholders` table with these key fields:

| Field | Type | Purpose |
|-------|------|---------|
| `name` | VARCHAR | Full name |
| `email` | VARCHAR | Contact email (optional) |
| `role` | VARCHAR | Job title |
| `department` | VARCHAR | Functional area (finance, hr, it, legal, executive, product) |
| `organization` | VARCHAR | Company name |
| `engagement_level` | VARCHAR | champion, supporter, neutral, skeptic, blocker |
| `alignment_score` | FLOAT | 0.0-1.0 scale of alignment with AI initiatives |
| `sentiment_score` | FLOAT | 0.0-1.0 scale of overall sentiment |
| `key_concerns` | JSONB | Array of primary concerns |
| `interests` | JSONB | Array of interests and priorities |
| `communication_preferences` | JSONB | How they prefer to communicate |
| `notes` | TEXT | Free-form profile summary |
| `metadata` | JSONB | Rich structured profile data |
| `reports_to` | UUID | Foreign key to manager's stakeholder record |

## Profile Components

### 1. Basic Information
- Name, role, department, organization
- Email (if available)
- Tenure at company

### 2. Engagement & Alignment
- **engagement_level**: champion > supporter > neutral > skeptic > blocker
- **alignment_score**: 0.0 (opposed) to 1.0 (fully aligned)
- **sentiment_score**: 0.0 (negative) to 1.0 (positive)

### 3. Key Concerns (JSONB Array)
Specific worries and risk areas they watch for:
```json
["SOX compliance", "Shadow IT proliferation", "Team overload"]
```

### 4. Interests (JSONB Array)
What they care about and prioritize:
```json
["Process optimization", "Automation ROI", "Team capacity building"]
```

### 5. Communication Preferences (JSONB Object)
How to effectively communicate with them:
```json
{
  "preferred_channel": "structured meetings with data",
  "style": "numbers-driven, show-me-the-ROI",
  "avoid": "vague promises without metrics"
}
```

### 6. Rich Metadata (JSONB Object)
The `metadata` field contains the full psychological profile:

```json
{
  "personality_archetype": "The Pragmatic Enabler",
  "motivations": ["Team efficiency", "Clean audits", "Reducing ticket volume"],
  "concerns": ["Shadow IT", "Security risks", "Team overload"],
  "decision_style": "Data-driven, process-oriented",
  "communication_style": "Concise, structured, prefers async",
  "what_success_looks_like": "Reduced help desk tickets, clean audits",
  "relationship_builders": ["Acknowledge constraints", "Document everything"],
  "relationship_killers": ["Bypassing process", "Creating maintenance burden"],
  "influence_on_ai_adoption": "Gatekeeper for technical integration"
}
```

## Profile Categories by Role Type

### Executive Stakeholders
Focus on: Strategic vision, competitive positioning, ROI at company level
```json
{
  "personality_archetype": "Transformational Leader",
  "influence_on_ai_adoption": "Executive sponsor - sets direction, provides air cover"
}
```

### Finance Stakeholders
Focus on: Compliance, audit readiness, measurable ROI, process accuracy
```json
{
  "personality_archetype": "The Scaling Specialist",
  "pain_points": {
    "monthly_close": "2-3 weeks per month on manual reconciliations",
    "ap_processing": "Invoice processing, 3-way matching bottlenecks"
  },
  "quick_wins": {
    "30_days": "Shadow close process, identify top 3 bottlenecks",
    "60_days": "Deploy pilot on highest-pain lowest-risk process"
  }
}
```

### IT/Governance Stakeholders
Focus on: Security, compliance, system integration, team capacity
```json
{
  "personality_archetype": "The Pragmatic Enabler",
  "pressure_points": {
    "scale_paradox": "Company grew but IT team hasnt scaled proportionally",
    "audit_scrutiny": "SOC 2/ISO 27001 means every tool is potential finding"
  },
  "communication_decoder": {
    "help_me_understand_architecture": "Im concerned about fit and support",
    "interesting_approach": "I have concerns but want to hear you out"
  }
}
```

### People/HR Stakeholders
Focus on: Change management, employee experience, adoption without burnout
```json
{
  "personality_archetype": "People Leader with Passion for Building",
  "champions_failure_context": "Part-time commitment, liked learning but not sharing",
  "what_success_looks_like": "Adoption up, satisfaction high, retention improved"
}
```

### Legal Stakeholders
Focus on: Governance, risk mitigation, compliance, team positioning
```json
{
  "personality_archetype": "Enneagram 3 ENFJ - The Achiever Protagonist",
  "governance_position": {
    "data_privacy": "Requires vendor agreements on data ownership",
    "accuracy": "Rigorous validation, human-in-the-loop"
  }
}
```

### Product Stakeholders (Indirect)
Focus on: How internal AI affects product velocity, learning opportunities
```json
{
  "personality_archetype": "Strategic Product Leader",
  "two_lenses": {
    "force_multiplier": "Does G&A AI boost Product bandwidth?",
    "risk_culture_agent": "Do internal AI experiments set good precedents?"
  },
  "relationship_to_role": {
    "direct_stakeholder": false,
    "update_cadence": "Quarterly briefs via manager"
  }
}
```

## Data Sources for Profiles

Rich profiles are built from:

1. **Interview Prep Documents**: Deep research reports created before stakeholder interviews
2. **Interview Transcripts**: Granola/Otter transcripts analyzed for communication style and priorities
3. **LinkedIn Research**: Career trajectory, credentials, background
4. **Org Chart Analysis**: Reporting relationships, sphere of influence
5. **Meeting Observations**: Oracle extracts insights from meeting transcripts

## SQL Patterns

### Insert New Stakeholder
```sql
INSERT INTO stakeholders (
    client_id,
    name,
    role,
    department,
    organization,
    engagement_level,
    alignment_score,
    sentiment_score,
    key_concerns,
    interests,
    communication_preferences,
    notes,
    metadata
) VALUES (
    '00000000-0000-0000-0000-000000000001'::UUID,
    'Name Here',
    'Title Here',
    'department',
    'Company',
    'supporter',
    0.7,
    0.6,
    '["Concern 1", "Concern 2"]'::JSONB,
    '["Interest 1", "Interest 2"]'::JSONB,
    '{"preferred_channel": "email", "style": "concise"}'::JSONB,
    'Profile summary text here.',
    '{"personality_archetype": "Type", "motivations": [], "concerns": []}'::JSONB
);
```

### Update Existing Stakeholder with Full Profile
```sql
UPDATE stakeholders
SET
    key_concerns = '["Concern 1", "Concern 2"]'::JSONB,
    interests = '["Interest 1", "Interest 2"]'::JSONB,
    communication_preferences = '{"preferred_channel": "meetings"}'::JSONB,
    notes = 'Updated profile summary.',
    metadata = '{"personality_archetype": "Type", "motivations": []}'::JSONB,
    updated_at = NOW()
WHERE name = 'Stakeholder Name'
  AND client_id = '00000000-0000-0000-0000-000000000001'::UUID;
```

### Set Reporting Relationships
```sql
UPDATE stakeholders
SET reports_to = (
    SELECT id FROM stakeholders
    WHERE name = 'Manager Name'
    AND client_id = '00000000-0000-0000-0000-000000000001'::UUID
    LIMIT 1
)
WHERE name = 'Report Name'
  AND client_id = '00000000-0000-0000-0000-000000000001'::UUID;
```

## Agent Usage

### Oracle (Meeting Intelligence)
- Uses stakeholder profiles to contextualize transcript analysis
- Extracts new insights to update profiles
- Identifies sentiment shifts and concern patterns

### Facilitator (Meeting Orchestration)
- References communication preferences when routing questions
- Considers stakeholder concerns when framing discussions
- Uses relationship dynamics to manage participation

### Capital (Finance)
- Aligns ROI discussions with finance stakeholder priorities
- Frames recommendations using their success criteria

### Guardian (IT/Governance)
- Addresses security concerns proactively
- Uses communication decoder patterns to interpret feedback

## Neo4j Graph Integration

Stakeholder profiles sync to Neo4j for relationship visualization:
- `(:Stakeholder)` nodes with properties from metadata
- `[:REPORTS_TO]` relationships from `reports_to` field
- `[:CONCERNED_ABOUT]` relationships to `(:Concern)` nodes
- `[:INTERESTED_IN]` relationships to `(:Topic)` nodes

### Stakeholder-Document Relationships

Stakeholders are automatically linked to documents in the knowledge base:

| Relationship | Direction | Description |
|-------------|-----------|-------------|
| `MENTIONED_IN` | `(:Stakeholder)-[:MENTIONED_IN]->(:Document)` | Stakeholder name appears in document content |
| `PROVIDED` | `(:Stakeholder)-[:PROVIDED]->(:Document)` | Stakeholder provided or authored the document |
| `ABOUT` | `(:Stakeholder)-[:ABOUT]->(:Document)` | Document is about/regarding this stakeholder |

#### Relationship Properties

```cypher
// MENTIONED_IN relationship
(s)-[r:MENTIONED_IN]->(d)
// Properties:
//   r.context - snippet of text around the mention
//   r.mention_count - number of times mentioned
//   r.updated_at - last sync timestamp

// PROVIDED relationship
(s)-[r:PROVIDED]->(d)
// Properties:
//   r.date - when provided
//   r.context - additional context

// ABOUT relationship
(s)-[r:ABOUT]->(d)
// Properties:
//   r.relationship_context - why it's about them
```

#### Automatic Inference

The sync service automatically creates `MENTIONED_IN` relationships by:
1. Scanning document chunks for stakeholder names
2. Matching department keywords (e.g., "finance" docs link to finance stakeholders)
3. Extracting context snippets around mentions

#### Query Methods

```python
# Get all documents for a stakeholder
await query_service.get_stakeholder_documents(stakeholder_id)

# Find documents mentioning a stakeholder by name
await query_service.get_documents_mentioning_stakeholder("Chris Baumgartner", client_id)

# Get the full stakeholder-document network
await query_service.get_stakeholder_document_network(client_id)

# Find stakeholders in a specific document
await query_service.find_stakeholders_in_document(document_id)

# Get relevant docs for meeting participants
await query_service.get_related_documents_for_stakeholders(stakeholder_ids)
```

#### Meeting Context Integration

The `get_meeting_context()` method now includes `stakeholder_documents` in its output, providing agents with relevant KB documents based on stakeholders detected in the conversation.

## Best Practices

1. **Always include personality_archetype** - Gives agents a quick mental model
2. **Document relationship_builders and relationship_killers** - Actionable guidance
3. **Include what_success_looks_like** - Enables outcome-focused recommendations
4. **Add communication_decoder for complex stakeholders** - Helps interpret subtext
5. **Update profiles after meetings** - Keep insights current
6. **Link reporting relationships** - Enables org chart visualization

## Example: Complete Finance Stakeholder

See [CONTENTFUL_STAKEHOLDERS.sql](./CONTENTFUL_STAKEHOLDERS.sql) for the full SQL used to create the Contentful stakeholder profiles including:
- Karthik Rao (CEO)
- Chris Baumgartner (Staff Program Manager, AI)
- Raul Rivera III (Senior Director, Global Controller)
- Danny Leal (Director of IT)
- Chad Meek (VP, TA, Community, People Data)
- Ashley Adams (Director, Legal Operations)
- Michael Stratton (VP of Product)
- Jon Eakin (Recruiter)
