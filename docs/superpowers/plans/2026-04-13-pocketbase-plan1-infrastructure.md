# PocketBase Infrastructure + Schema (Plan 1 of 3)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy PocketBase on Fly.io with all 78 Thesis collections defined, verified, and ready for data.

**Architecture:** PocketBase v0.25.9 on Fly.io (`thesis-db`), Alpine Docker image, persistent volume for pb_data. Migration JS files create all collections in dependency order (leaf first, then relations).

**Tech Stack:** PocketBase 0.25.9, Fly.io, JavaScript migrations

**Spec:** `docs/superpowers/specs/2026-04-13-supabase-to-pocketbase-migration.md`

**Schema reference:** Full Supabase schemas at `/tmp/thesis_all_schemas.json` (queried 2026-04-13). Also available via Supabase Management API.

---

## File Structure

```
thesis/
  Dockerfile.pocketbase              -- Alpine + PB binary
  fly.pocketbase.toml                -- Fly.io config for thesis-db
  pb_migrations/
    1001_core.js                     -- agents, agent_*, ai_projects, stakeholders, strategic_goals
    1002_tasks.js                    -- project_tasks, task_candidates, task_comments, task_history
    1003_chat.js                     -- conversations, messages, message_documents
    1004_documents.js                -- documents, document_chunks, document_classifications, document_tags
    1005_projects.js                 -- projects, project_candidates, project_conversations, project_documents, project_folders, project_stakeholder_link, portfolio_projects, roi_opportunities
    1006_meetings.js                 -- meeting_rooms, meeting_room_messages, meeting_room_participants, meeting_transcripts
    1007_help.js                     -- help_documents, help_chunks, help_conversations, help_messages
    1008_disco.js                    -- all disco_* collections (18 tables)
    1009_purdy.js                    -- all purdy_* collections (11 tables)
    1010_research.js                 -- research_tasks, research_sources, research_schedule
    1011_stakeholder_extras.js       -- stakeholder_candidates, stakeholder_insights, stakeholder_metrics
    1012_obsidian.js                 -- obsidian_*, graph_* collections
    1013_misc.js                     -- api_usage_logs, compass_status_reports, department_kpis, engagement_level_history, glean_*, knowledge_gaps, theme_settings, user_quick_prompts
```

## Field Type Mapping Rules

Apply these rules when translating Postgres columns to PocketBase fields:

| Postgres type | PB type | Notes |
|--------------|---------|-------|
| `uuid` PK | omit (PB auto-generates `id`) | |
| `character varying` | `text` | |
| `text` (short, <5000 chars likely) | `text` | column names like `status`, `name`, `role` |
| `text` (large content) | `editor` | column names like `description`, `content`, `instructions`, `notes`, `summary`, `justification`, `raw_text`, `content_markdown`, `system_instruction`, `source_text`, `result_content` |
| `integer` | `number` | never set `required: true` if 0 is valid |
| `bigint` | `number` | |
| `numeric` / `double precision` | `number` | |
| `boolean` | `bool` | |
| `jsonb` | `json` | |
| `ARRAY` (text[]) | `json` | stored as JSON arrays |
| `timestamp with time zone` for created_at | `autodate` | `{ onCreate: true, onUpdate: false }` |
| `timestamp with time zone` for updated_at | `autodate` | `{ onCreate: true, onUpdate: true }` |
| `timestamp with time zone` (other) | `date` | business dates, completed_at, etc. |
| `date` | `date` | |
| `uuid` FK | `relation` | `{ collectionId: parent.id, cascadeDelete: true/false, maxSelect: 1 }` |
| `USER-DEFINED` (enum) | `text` | PB has no enums |
| `USER-DEFINED` (vector) | omit | handled by vec sidecar in Plan 3 |
| `GENERATED ALWAYS` | omit | computed in application code |

**Skip columns:** `client_id`, `user_id` (auth refs), `created_by`, `updated_by`, `embedding` (vector), `total_score`/`tier` (generated).

**Keep as plain text:** `added_by`, `run_by`, `approved_by`, `rejected_by`, `accepted_by`, `linked_by`, `reviewed_by` -- store the name/identifier as text, not a relation.

---

### Task 1: Create Dockerfile.pocketbase

**Files:**
- Create: `Dockerfile.pocketbase`

- [ ] **Step 1: Create the Dockerfile**

```dockerfile
FROM alpine:latest

ARG PB_VERSION=0.25.9

RUN apk add --no-cache unzip ca-certificates

ADD https://github.com/pocketbase/pocketbase/releases/download/v${PB_VERSION}/pocketbase_${PB_VERSION}_linux_amd64.zip /tmp/pb.zip
RUN unzip /tmp/pb.zip -d /pb/ && rm /tmp/pb.zip

COPY pb_migrations /pb/pb_migrations

EXPOSE 8090

CMD ["/pb/pocketbase", "serve", "--http=0.0.0.0:8090", "--dir=/pb/pb_data", "--migrationsDir=/pb/pb_migrations"]
```

- [ ] **Step 2: Commit**

```bash
git add Dockerfile.pocketbase
git commit -m "feat: add PocketBase Dockerfile for thesis-db"
```

---

### Task 2: Create fly.pocketbase.toml

**Files:**
- Create: `fly.pocketbase.toml`

- [ ] **Step 1: Create the fly config**

```toml
app = "thesis-db"
primary_region = "dfw"

[build]
  dockerfile = "Dockerfile.pocketbase"

[mounts]
  source = "pb_data"
  destination = "/pb/pb_data"

[http_service]
  internal_port = 8090
  force_https = true
  auto_stop_machines = "off"
  auto_start_machines = true
  min_machines_running = 1

  [http_service.concurrency]
    type = "requests"
    soft_limit = 25
    hard_limit = 50

[[http_service.checks]]
  grace_period = "10s"
  interval = "30s"
  method = "GET"
  path = "/api/health"
  timeout = "5s"

[[vm]]
  size = "shared-cpu-1x"
  memory = "256mb"
```

- [ ] **Step 2: Commit**

```bash
git add fly.pocketbase.toml
git commit -m "feat: add Fly.io config for thesis-db PocketBase"
```

---

### Task 3: Migration 1001_core.js

**Files:**
- Create: `pb_migrations/1001_core.js`

This migration creates: `agents`, `agent_topic_mapping`, `ai_projects`, `stakeholders`, `strategic_goals` (leaf collections), then `agent_handoffs`, `agent_instruction_versions`, `agent_knowledge_base` (relation collections).

- [ ] **Step 1: Create the migration file**

```javascript
/// <reference path="../pb_data/types.d.ts" />

// Core collections: agents, agent helpers, projects, stakeholders, goals.
// Two-pass: leaf first, then relations.

migrate((app) => {
  // ===== Pass 1: Leaf collections =====

  const agents = new Collection({
    name: "agents",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "name", type: "text", required: true },
      { name: "display_name", type: "text", required: true },
      { name: "description", type: "editor" },
      { name: "system_instruction", type: "editor" },
      { name: "is_active", type: "bool" },
      { name: "config", type: "json" },
      { name: "capabilities", type: "json" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(agents)

  const agentTopicMapping = new Collection({
    name: "agent_topic_mapping",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "topic_keyword", type: "text", required: true },
      { name: "agent_name", type: "text", required: true },
      { name: "relevance_score", type: "number" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
    ],
  })
  app.save(agentTopicMapping)

  const aiProjects = new Collection({
    name: "ai_projects",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "project_code", type: "text", required: true },
      { name: "title", type: "text", required: true },
      { name: "description", type: "editor" },
      { name: "department", type: "text" },
      { name: "owner_stakeholder_id", type: "text" },
      { name: "current_state", type: "editor" },
      { name: "desired_state", type: "editor" },
      { name: "roi_potential", type: "number" },
      { name: "implementation_effort", type: "number" },
      { name: "strategic_alignment", type: "number" },
      { name: "stakeholder_readiness", type: "number" },
      // total_score and tier are GENERATED -- computed in app code
      { name: "status", type: "text" },
      { name: "next_step", type: "editor" },
      { name: "blockers", type: "json" },
      { name: "follow_up_questions", type: "json" },
      { name: "roi_indicators", type: "json" },
      { name: "source_type", type: "text" },
      { name: "source_id", type: "text" },
      { name: "source_notes", type: "editor" },
      { name: "metadata", type: "json" },
      { name: "project_summary", type: "editor" },
      { name: "roi_justification", type: "editor" },
      { name: "effort_justification", type: "editor" },
      { name: "alignment_justification", type: "editor" },
      { name: "readiness_justification", type: "editor" },
      { name: "project_name", type: "text" },
      { name: "project_description", type: "editor" },
      { name: "scoring_confidence", type: "number" },
      { name: "confidence_questions", type: "json" },
      { name: "goal_alignment_score", type: "number" },
      { name: "goal_alignment_details", type: "json" },
      { name: "initiative_ids", type: "json" },
      { name: "agenticity_score", type: "number" },
      { name: "agenticity_evaluated_at", type: "date" },
      { name: "agenticity_evaluation", type: "json" },
      { name: "agenticity_task_hash", type: "text" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(aiProjects)

  const stakeholders = new Collection({
    name: "stakeholders",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "name", type: "text", required: true },
      { name: "email", type: "text" },
      { name: "phone", type: "text" },
      { name: "role", type: "text" },
      { name: "department", type: "text" },
      { name: "organization", type: "text" },
      { name: "sentiment_score", type: "number" },
      { name: "sentiment_trend", type: "text" },
      { name: "engagement_level", type: "text" },
      { name: "alignment_score", type: "number" },
      { name: "first_interaction", type: "date" },
      { name: "last_interaction", type: "date" },
      { name: "total_interactions", type: "number" },
      { name: "communication_preferences", type: "json" },
      { name: "key_concerns", type: "json" },
      { name: "interests", type: "json" },
      { name: "notes", type: "editor" },
      { name: "reports_to", type: "text" },
      { name: "influences", type: "json" },
      { name: "metadata", type: "json" },
      { name: "last_engagement_calculated", type: "date" },
      { name: "priority_level", type: "text" },
      { name: "ai_priorities", type: "json" },
      { name: "pain_points", type: "json" },
      { name: "win_conditions", type: "json" },
      { name: "communication_style", type: "editor" },
      { name: "relationship_status", type: "text" },
      { name: "open_questions", type: "json" },
      { name: "last_contact", type: "date" },
      { name: "reports_to_name", type: "text" },
      { name: "team_size", type: "number" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(stakeholders)

  const strategicGoals = new Collection({
    name: "strategic_goals",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "level", type: "text", required: true },
      { name: "title", type: "text", required: true },
      { name: "description", type: "editor" },
      { name: "department", type: "text" },
      { name: "owner", type: "text" },
      { name: "target_metric", type: "text" },
      { name: "current_value", type: "number" },
      { name: "target_value", type: "number" },
      { name: "unit", type: "text" },
      { name: "status", type: "text" },
      { name: "priority", type: "number" },
      { name: "parent_goal_id", type: "text" },
      { name: "fiscal_year", type: "text" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(strategicGoals)

  // ===== Pass 2: Collections with relations =====

  const agentHandoffs = new Collection({
    name: "agent_handoffs",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "conversation_id", type: "text", required: true },
      { name: "from_agent_id", type: "relation", collectionId: agents.id, maxSelect: 1 },
      { name: "to_agent_id", type: "relation", collectionId: agents.id, maxSelect: 1 },
      { name: "reason", type: "editor" },
      { name: "context", type: "json" },
      { name: "initiated_at", type: "date" },
      { name: "accepted_at", type: "date" },
      { name: "status", type: "text" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(agentHandoffs)

  const agentInstructionVersions = new Collection({
    name: "agent_instruction_versions",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "agent_id", type: "relation", collectionId: agents.id, required: true, cascadeDelete: true, maxSelect: 1 },
      { name: "version_number", type: "text", required: true },
      { name: "instructions", type: "editor", required: true },
      { name: "description", type: "editor" },
      { name: "is_active", type: "bool" },
      { name: "created_by", type: "text" },
      { name: "activated_at", type: "date" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(agentInstructionVersions)

  const agentKnowledgeBase = new Collection({
    name: "agent_knowledge_base",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "agent_id", type: "relation", collectionId: agents.id, required: true, cascadeDelete: true, maxSelect: 1 },
      { name: "document_id", type: "text", required: true },
      { name: "added_by", type: "text" },
      { name: "notes", type: "editor" },
      { name: "priority", type: "number" },
      { name: "relevance_score", type: "number" },
      { name: "classification_source", type: "text" },
      { name: "classification_confidence", type: "number" },
      { name: "classification_reason", type: "editor" },
      { name: "user_confirmed", type: "bool" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(agentKnowledgeBase)

}, (app) => {
  const names = [
    "agent_knowledge_base", "agent_instruction_versions", "agent_handoffs",
    "strategic_goals", "stakeholders", "ai_projects", "agent_topic_mapping", "agents",
  ]
  for (const name of names) {
    try { const col = app.findCollectionByNameOrId(name); if (col) app.delete(col) } catch (e) {}
  }
})
```

- [ ] **Step 2: Commit**

```bash
git add pb_migrations/1001_core.js
git commit -m "feat: add PB migration 1001 - core collections"
```

---

### Task 4: Migration 1002_tasks.js

**Files:**
- Create: `pb_migrations/1002_tasks.js`

Creates: `project_tasks`, `task_candidates` (leaf), then `task_comments`, `task_history` (relations to project_tasks).

- [ ] **Step 1: Create the migration file**

Query the Supabase schema for these 4 tables using:
```bash
TOKEN=$(security find-generic-password -s "Supabase CLI" -w | sed 's/go-keyring-base64://' | base64 -d)
curl -s -X POST "https://api.supabase.com/v1/projects/imdavfgreeddxluslsdl/database/query" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"query":"SELECT table_name, column_name, data_type FROM information_schema.columns WHERE table_name IN ('\''project_tasks'\'','\''task_candidates'\'','\''task_comments'\'','\''task_history'\'') ORDER BY table_name, ordinal_position"}'
```

Apply the Field Type Mapping Rules from the top of this plan. Key decisions for these tables:

- `project_tasks`: Skip `client_id`, `user_id`, `created_by`, `updated_by`, `embedding` (vector). Keep `assignee_stakeholder_id`, `assignee_user_id` as plain `text`. Fields `description`, `source_text`, `blocker_reason`, `notes` use `editor` type. Arrays (`tags`, `related_stakeholder_ids`, `depends_on`) become `json`.
- `task_candidates`: Skip `client_id`, `user_id`, `accepted_by`, `rejected_by`, `embedding`, `embedding_status`. Fields `source_text`, `meeting_context`, `value_proposition`, `description`, `rejection_reason`, `match_reason` use `editor`. Arrays (`topics`) become `json`.
- `task_comments`: `task_id` is a relation to `project_tasks` with `cascadeDelete: true`. Skip `user_id`. `content` uses `editor`.
- `task_history`: `task_id` is a relation to `project_tasks` with `cascadeDelete: true`. Skip `user_id`.

Write the migration JS following the exact same two-pass pattern as `1001_core.js`: leaf collections first (`project_tasks`, `task_candidates`), then relation collections (`task_comments`, `task_history`). Include the `down` migration that deletes in reverse order.

- [ ] **Step 2: Commit**

```bash
git add pb_migrations/1002_tasks.js
git commit -m "feat: add PB migration 1002 - task collections"
```

---

### Task 5: Migration 1003_chat.js

**Files:**
- Create: `pb_migrations/1003_chat.js`

Creates: `conversations` (leaf), then `messages` (relation to conversations), then `message_documents` (relation to messages).

- [ ] **Step 1: Create the migration file**

Query schema for `conversations`, `messages`, `message_documents`. Apply mapping rules:

- `conversations`: Skip `user_id`, `client_id`. Keep `project_id`, `agent_id`, `initiative_id`, `agent_instruction_version_id` as plain `text` (cross-collection refs resolved in app code). `title` is `text`.
- `messages`: `conversation_id` is a relation to `conversations` with `cascadeDelete: true`. `content` uses `editor`. `metadata` is `json`.
- `message_documents`: `message_id` is a relation to `messages` with `cascadeDelete: true`. `document_id` is plain `text` (cross-migration ref).

Follow the same two-pass pattern. Include down migration.

- [ ] **Step 2: Commit**

```bash
git add pb_migrations/1003_chat.js
git commit -m "feat: add PB migration 1003 - chat collections"
```

---

### Task 6: Migration 1004_documents.js

**Files:**
- Create: `pb_migrations/1004_documents.js`

Creates: `documents` (leaf), then `document_chunks`, `document_classifications`, `document_tags` (relations to documents).

- [ ] **Step 1: Create the migration file**

Query schema for these 4 tables. Apply mapping rules:

- `documents`: Skip `client_id`, `user_id`, `uploaded_by`. 44 columns minus skipped = ~40 fields. Large text fields (`storage_url`, `title`, `digest`) use `editor`. `document_type` and `primary_use_case` are `USER-DEFINED` enums -> `text`. `tags_cache` is `json`. `file_size` is `number`. `related_document_id` is plain `text`.
- `document_chunks`: `document_id` is a relation to `documents` with `cascadeDelete: true`. Skip `embedding` column (vector). `content` uses `editor`. `metadata` is `json`.
- `document_classifications`: `document_id` is a relation to `documents` with `cascadeDelete: true`. Skip `reviewed_by`. `raw_scores` is `json`. `review_reason` uses `editor`.
- `document_tags`: `document_id` is a relation to `documents` with `cascadeDelete: true`. `tag` and `source` are `text`.

Follow two-pass pattern. Include down migration.

- [ ] **Step 2: Commit**

```bash
git add pb_migrations/1004_documents.js
git commit -m "feat: add PB migration 1004 - document collections"
```

---

### Task 7: Migration 1005_projects.js

**Files:**
- Create: `pb_migrations/1005_projects.js`

Creates: `projects`, `portfolio_projects`, `roi_opportunities` (leaf), then `project_candidates`, `project_conversations`, `project_documents`, `project_folders`, `project_stakeholder_link` (these reference ai_projects from 1001 -- use plain `text` for cross-migration refs since PB relation requires collectionId from same migration scope).

- [ ] **Step 1: Create the migration file**

Query schema for these 8 tables. Apply mapping rules:

- `projects`: Skip `user_id`, `client_id`. `title` is `text`, `description` is `editor`, `status` is `text`.
- `portfolio_projects`: Skip `client_id`. All varchar fields are `text`. `description` and `tools_platform` use `editor`.
- `roi_opportunities`: Skip `client_id`. `description` and `outcome_notes` use `editor`. `estimated_value_usd`, `estimated_hours_saved`, `actual_value_usd`, `actual_hours_saved` are `number`. `stakeholder_alignment` and `metadata` are `json`.
- `project_candidates`: Skip `client_id`, `accepted_by`, `rejected_by`. `description`, `source_text`, `potential_impact`, `rejection_reason`, `match_reason` use `editor`. `related_stakeholder_names` is `json`. All `_id` FK refs to other migrations use plain `text`.
- `project_conversations`: Skip `client_id`, `user_id`. `project_id` is plain `text`. `question` and `response` use `editor`. `source_documents` is `json`.
- `project_documents`: `project_id` and `document_id` are plain `text`. `notes` is `editor`.
- `project_folders`: `project_id` is plain `text`. `folder_path` is `text`. `recursive` is `bool`.
- `project_stakeholder_link`: `project_id` and `stakeholder_id` are plain `text`. `role` is `text`. `notes` is `editor`.

All collections are leaf (cross-migration refs stored as text). Include down migration.

- [ ] **Step 2: Commit**

```bash
git add pb_migrations/1005_projects.js
git commit -m "feat: add PB migration 1005 - project collections"
```

---

### Task 8: Migration 1006_meetings.js

**Files:**
- Create: `pb_migrations/1006_meetings.js`

Creates: `meeting_rooms` (leaf), `meeting_transcripts` (leaf), then `meeting_room_messages` and `meeting_room_participants` (relations to meeting_rooms).

- [ ] **Step 1: Create the migration file**

Query schema for these 4 tables. Apply mapping rules:

- `meeting_rooms`: Skip `client_id`, `user_id`. `title` is `text` required. `description` uses `editor`. `config` is `json`. `meeting_type` and `status` are `text`. `total_tokens_used` is `number`. `project_id` and `initiative_id` are plain `text`.
- `meeting_transcripts`: Skip `client_id`, `user_id`. `document_id` is plain `text`. `title` and `meeting_type` are `text`. `raw_text` and `summary` use `editor`. `attendees`, `key_topics`, `sentiment_summary`, `action_items`, `decisions`, `open_questions`, `metadata` are all `json`. `processing_status`, `processing_error` are `text`/`editor`.
- `meeting_room_messages`: `meeting_room_id` is a relation to `meeting_rooms` with `cascadeDelete: true`. `agent_id` is plain `text`. `role`, `agent_name`, `agent_display_name` are `text`. `content` uses `editor`. `metadata` is `json`. `turn_number` is `number`.
- `meeting_room_participants`: `meeting_room_id` is a relation to `meeting_rooms` with `cascadeDelete: true`. `agent_id` is plain `text`. `role_description` uses `editor`. `priority`, `turns_taken`, `tokens_used` are `number`.

Two-pass pattern. Include down migration.

- [ ] **Step 2: Commit**

```bash
git add pb_migrations/1006_meetings.js
git commit -m "feat: add PB migration 1006 - meeting collections"
```

---

### Task 9: Migration 1007_help.js

**Files:**
- Create: `pb_migrations/1007_help.js`

Creates: `help_documents`, `help_conversations` (leaf), then `help_chunks` (relation to help_documents), `help_messages` (relation to help_conversations).

- [ ] **Step 1: Create the migration file**

- `help_documents`: `title` is `text` required. `file_path` and `category` are `text` required. `content` uses `editor` required. `role_access` is `json`. `word_count` is `number`.
- `help_conversations`: `title` is `text`. `help_type` is `text`.
- `help_chunks`: `document_id` is a relation to `help_documents` with `cascadeDelete: true`. `content` uses `editor` required. `chunk_index` is `number` required. `heading_context` is `text`. `role_access` is `json`. `metadata` is `json`. Skip embedding column.
- `help_messages`: `conversation_id` is a relation to `help_conversations` with `cascadeDelete: true`. `role` is `text` required. `content` uses `editor` required. `sources` is `json`. `timestamp` is `date`. `feedback` is `number`. `feedback_timestamp` is `date`.

Two-pass pattern. Include down migration.

- [ ] **Step 2: Commit**

```bash
git add pb_migrations/1007_help.js
git commit -m "feat: add PB migration 1007 - help collections"
```

---

### Task 10: Migration 1008_disco.js

**Files:**
- Create: `pb_migrations/1008_disco.js`

This is the largest migration: 18 DISCO tables. Creates leaf collections first (`disco_initiatives`, `disco_system_kb`), then collections with relations.

- [ ] **Step 1: Create the migration file**

Query schema for all `disco_*` tables. Apply mapping rules:

**Pass 1 (leaf):**
- `disco_initiatives`: `name` text required, `description` editor, `status` text, `created_by` text, various date fields, `goal_alignment_score` number, `goal_alignment_details`/`throughline`/`value_alignment`/`resolution_annotations` json, `target_department` text, `sponsor_stakeholder_id` text, `stakeholder_ids` json, `user_corrections` editor. Skip `decision_velocity_days` (GENERATED).
- `disco_system_kb`: `filename` text required, `content` editor required, `category` text, `description` editor.
- `disco_conversations`: `initiative_id` text (cross-collection), `user_id` text.

**Pass 2 (relations to disco_initiatives):**
- `disco_bundles`: `initiative_id` relation to disco_initiatives (cascade). `name` text required, `description` editor, `status` text, various score/rationale fields as text/editor. `included_items`/`stakeholders`/`dependencies` json. `source_output_id` text. Skip `decision_velocity_days` if present. `solution_type` text.
- `disco_checkpoints`: `initiative_id` relation (cascade). `checkpoint_number` number required, `status` text, `notes` editor, `checklist_items` json.
- `disco_documents`: `initiative_id` relation (cascade). `filename` text required, `content` editor required, `document_type` text, `version` number, `source_run_id` text, `metadata` json, `migrated_to_kb` bool.
- `disco_initiative_documents`: `initiative_id` relation (cascade), `document_id` text, `linked_by` text, `notes` editor.
- `disco_initiative_folders`: `initiative_id` relation (cascade), `folder_path` text required, `recursive` bool, `linked_by` text.
- `disco_initiative_members`: `initiative_id` relation (cascade), `role` text.
- `disco_messages`: `conversation_id` text (cross ref), `role` text required, `content` editor required, `sources` json.
- `disco_outcome_metrics`: All fields nullable (likely a materialized view stored as table). `name` text, `status` text, various date fields, `decision_velocity_days` number, `velocity_category` text, `avg_stakeholder_rating` number, `ratings_count` number, `total_outputs` number.
- `disco_runs`: `initiative_id` text, `agent_type` text required, `run_by` text, `status` text, `error_message` editor, `token_usage`/`metadata` json, `project_id` text.
- `disco_outputs`: `run_id` text, `initiative_id` text, `agent_type` text required, `version` number, `title` text, `recommendation`/`executive_summary`/`content_markdown`/`synthesis_notes` editor, `tier_routing`/`confidence_level`/`synthesis_mode`/`output_format` text, `content_structured`/`intermediate_outputs`/`source_outputs`/`throughline_resolution`/`triage_suggestions` json, `stakeholder_rating` number, `stakeholder_feedback` editor, `project_id` text.
- `disco_document_chunks`: `document_id` text, `initiative_id` relation (cascade), `chunk_index` number, `content` editor, `metadata` json. Skip `embedding`.
- `disco_system_kb_chunks`: `kb_id` relation to disco_system_kb (cascade), `chunk_index` number, `content` editor, `metadata` json. Skip embedding if present.

**Pass 3 (relations to bundles):**
- `disco_bundle_feedback`: `bundle_id` relation to disco_bundles (cascade), `action` text required, `feedback` editor, `changes` json.
- `disco_prds`: `bundle_id` relation to disco_bundles (cascade), `initiative_id` text, `title` text required, `content_markdown` editor required, `content_structured` json, `status` text, `version` number, `source_output_id` text.
- `disco_run_documents`: Junction table. PB needs an id. `run_id` text, `document_id` text. No relations (both are cross-refs).

Include down migration deleting in reverse order.

- [ ] **Step 2: Commit**

```bash
git add pb_migrations/1008_disco.js
git commit -m "feat: add PB migration 1008 - DISCO collections"
```

---

### Task 11: Migration 1009_purdy.js

**Files:**
- Create: `pb_migrations/1009_purdy.js`

11 PuRDy tables. Nearly identical structure to DISCO.

- [ ] **Step 1: Create the migration file**

Query schema for all `purdy_*` tables. Apply mapping rules. Structure mirrors DISCO:

**Pass 1 (leaf):**
- `purdy_initiatives`: `name` text required, `description` editor, `status` text, `created_by` text.
- `purdy_system_kb`: `filename` text required, `content` editor required, `category` text, `description` editor.
- `purdy_conversations`: `initiative_id` text, `user_id` text.

**Pass 2 (relations):**
- `purdy_documents`: `initiative_id` relation to purdy_initiatives (cascade). Same fields as disco_documents.
- `purdy_initiative_members`: `initiative_id` relation (cascade), `role` text.
- `purdy_messages`: `conversation_id` text, `role` text required, `content` editor required, `sources` json.
- `purdy_runs`: `initiative_id` text, `agent_type` text required, `run_by` text, `status` text, `error_message` editor, `token_usage`/`metadata` json.
- `purdy_outputs`: `run_id` text, `initiative_id` text (required), `agent_type` text required, `version` number, `title` text, `recommendation`/`executive_summary`/`content_markdown` editor, `tier_routing`/`confidence_level` text, `content_structured` json.
- `purdy_document_chunks`: `document_id` text, `initiative_id` relation (cascade), `chunk_index` number, `content` editor, `metadata` json. Skip embedding.
- `purdy_system_kb_chunks`: `kb_id` relation to purdy_system_kb (cascade), `chunk_index` number, `content` editor, `metadata` json. Skip embedding.
- `purdy_run_documents`: Junction table. `run_id` text, `document_id` text.

Include down migration.

- [ ] **Step 2: Commit**

```bash
git add pb_migrations/1009_purdy.js
git commit -m "feat: add PB migration 1009 - PuRDy collections"
```

---

### Task 12: Migration 1010_research.js

**Files:**
- Create: `pb_migrations/1010_research.js`

3 tables, all leaf (no inter-table relations within this group).

- [ ] **Step 1: Create the migration file**

- `research_tasks`: Skip `client_id`. `topic` text required, `query` editor required, `focus_area`/`research_type`/`status` text, `priority` number, `context`/`web_sources` json, `result_content`/`result_summary` editor, `result_document_id` text, `error_message` editor, `retry_count` number, various date fields.
- `research_sources`: `domain` text required, `name` text, `credibility_tier` number, `source_type` text, `topics` json, `times_cited` number, `last_cited_at` date, `is_blocked` bool, `notes` editor.
- `research_schedule`: Skip `client_id`. `day_of_week` number, `hour_utc` number, `focus_area` text required, `description` editor, `query_template` editor, `is_active` bool, `priority` number.

All leaf collections. Include down migration.

- [ ] **Step 2: Commit**

```bash
git add pb_migrations/1010_research.js
git commit -m "feat: add PB migration 1010 - research collections"
```

---

### Task 13: Migration 1011_stakeholder_extras.js

**Files:**
- Create: `pb_migrations/1011_stakeholder_extras.js`

3 tables that reference stakeholders (from 1001). Use plain `text` for cross-migration stakeholder_id refs.

- [ ] **Step 1: Create the migration file**

- `stakeholder_candidates`: Skip `client_id`, `accepted_by`, `rejected_by`. `name` text required, `role`/`department`/`organization`/`email` text, `key_concerns`/`interests` json, `initial_sentiment`/`influence_level`/`status`/`confidence` text, `source_document_id`/`source_document_name` text, `source_text`/`extraction_context`/`rejection_reason`/`match_reason` editor, `related_project_ids`/`related_task_ids` json, `potential_match_stakeholder_id`/`created_stakeholder_id`/`merged_into_stakeholder_id`/`matched_candidate_id` text, `match_confidence` number.
- `stakeholder_insights`: `stakeholder_id` text, `source_document_id`/`meeting_transcript_id` text, `insight_type` text required, `content` editor required, `confidence` number, `extracted_quote`/`context`/`resolution_notes` editor, `is_resolved` bool, `resolved_at` date.
- `stakeholder_metrics`: Skip `client_id`. `stakeholder_id` text, `metric_name` text required, `metric_category`/`unit`/`current_value`/`target_value`/`validation_status`/`source` text, `source_date` date, `notes` editor, `questions_to_confirm` json.

All leaf collections. Include down migration.

- [ ] **Step 2: Commit**

```bash
git add pb_migrations/1011_stakeholder_extras.js
git commit -m "feat: add PB migration 1011 - stakeholder extra collections"
```

---

### Task 14: Migration 1012_obsidian.js

**Files:**
- Create: `pb_migrations/1012_obsidian.js`

5 tables: `obsidian_vault_configs` (leaf), `obsidian_sync_log`, `obsidian_sync_state` (relations to vault_configs), `graph_sync_log`, `graph_sync_state` (leaf).

- [ ] **Step 1: Create the migration file**

- `obsidian_vault_configs`: Skip `user_id`, `client_id`. `vault_path` text required, `vault_name` text, `is_active` bool, `last_sync_at` date, `last_error` editor, `sync_options`/`metadata`/`sync_progress` json.
- `obsidian_sync_log`: `config_id` relation to obsidian_vault_configs (cascade). Skip `user_id`. `sync_type`/`status`/`trigger_source` text, `files_scanned`/`files_added`/`files_updated`/`files_deleted`/`files_skipped`/`files_failed`/`duration_ms` number, `error_message` editor, `error_details` json, `started_at`/`completed_at` date.
- `obsidian_sync_state`: `config_id` relation (cascade). `file_path` text required, `document_id` text, `file_mtime` date, `file_hash` text, `file_size` number, `sync_status` text, `last_synced_at` date, `sync_error` editor, `frontmatter` json.
- `graph_sync_log`: Skip `client_id`. `sync_type` text required, `entity_type` text required, `entity_id` text, `synced_at` date, `sync_status` text required, `details` json, `error_message` editor, `duration_ms` number.
- `graph_sync_state`: Skip `client_id`. `entity_type` text required, `last_synced_at` date, `last_sync_status` text, `record_count` number.

Two-pass: vault_configs + graph tables first, then obsidian sync tables. Include down migration.

- [ ] **Step 2: Commit**

```bash
git add pb_migrations/1012_obsidian.js
git commit -m "feat: add PB migration 1012 - obsidian + graph sync collections"
```

---

### Task 15: Migration 1013_misc.js

**Files:**
- Create: `pb_migrations/1013_misc.js`

12 remaining tables, all leaf collections.

- [ ] **Step 1: Create the migration file**

- `api_usage_logs`: Skip `user_id`, `client_id`. `endpoint`/`method`/`operation`/`model` text, `tokens_used`/`input_tokens`/`output_tokens` number, `estimated_cost`/`cost_usd` number, `metadata` json.
- `compass_status_reports`: Skip `user_id`, `client_id`. `report_date` date required, `period_start`/`period_end` date, all `_justification` fields use `editor`, score fields (`strategic_impact`, `execution_quality`, etc.) use `number`, `overall_score` number, `executive_summary` editor, `wins_referenced`/`data_sources`/`improvement_actions` json, `areas_of_strength`/`growth_opportunities`/`recommended_actions` json (arrays), `generation_model` text.
- `department_kpis`: Skip `client_id`. `department`/`kpi_name` text required, `description` editor, `current_value`/`target_value`/`trend_percentage`/`sort_order` number, `unit` text required, `trend`/`status`/`fiscal_year` text, `linked_objective_id`/`linked_goal_id` text.
- `engagement_level_history`: Skip `client_id`. `stakeholder_id` text, `engagement_level` text required, `previous_level` text, `calculation_reason` editor, `signals` json, `calculated_at` date, `calculation_type` text.
- `glean_connectors`: `name`/`display_name` text required, `connector_type`/`status`/`contentful_status` text (USER-DEFINED enums -> text), `category`/`developed_by`/`glean_tier`/`setup_complexity`/`connector_subtype` text, `description`/`notes` editor, `documentation_url` text, `development_date`/`contentful_enabled_date` date, `disco_score` number.
- `glean_connector_gaps`: `connector_name` text, `request_count` number, `priority`/`status` text, `use_cases`/`requesters` editor, `first_requested`/`last_requested` date.
- `glean_connector_requests`: `connector_name` text required, `requested_by` text, `request_source`/`use_case`/`business_justification` editor, `priority`/`status` text, `request_count` number, `connector_id` text, `resolved_at` date.
- `glean_connector_summary`: `contentful_status` text, `disco_score` number, `connector_count` number, `connectors` editor.
- `glean_disco_integration_matrix`: `name`/`display_name` text, `connector_type`/`connector_subtype`/`contentful_status` text, `contentful_enabled_date` date, `disco_score` number, `disco_rating` text.
- `knowledge_gaps`: Skip `client_id`. `topic` text required, `question` editor required, `source_agent` text, `source_conversation_id`/`resolution_task_id` text, `uncertainty_signals` json, `gap_type`/`status` text, `resolved_at` date, `occurrence_count`/`priority` number.
- `theme_settings`: Skip `client_id`. All 38 color/font/border/header fields are `text`. `header_logo_url` is `text`.
- `user_quick_prompts`: Skip `user_id`. `title` text required, `prompt_text` editor required, `display_order` number, `is_auto_generated` bool, `metadata` json.

All leaf. Include down migration.

- [ ] **Step 2: Commit**

```bash
git add pb_migrations/1013_misc.js
git commit -m "feat: add PB migration 1013 - misc collections"
```

---

### Task 16: Deploy PocketBase to Fly.io

**Files:** None (infrastructure task)

- [ ] **Step 1: Create the Fly.io app**

```bash
cd ~/Vault/GitHub/thesis
flyctl apps create thesis-db --org personal
```

- [ ] **Step 2: Create the persistent volume**

```bash
flyctl volumes create pb_data --region dfw --size 1 -a thesis-db
```

- [ ] **Step 3: Deploy**

```bash
flyctl deploy --config fly.pocketbase.toml -a thesis-db
```

Expected: successful deploy, app running at `thesis-db.fly.dev`.

- [ ] **Step 4: Set up superuser account**

Open `https://thesis-db.fly.dev/_/` in a browser. Create the initial superuser account. Save credentials to 1Password as "Thesis PocketBase Superuser".

- [ ] **Step 5: Verify health**

```bash
curl -s https://thesis-db.fly.dev/api/health
```

Expected: `{"code":200,"message":"API is healthy."}` or similar.

---

### Task 17: Verify All Collections

**Files:** None (verification task)

- [ ] **Step 1: Authenticate and list collections**

```bash
# Get auth token
TOKEN=$(curl -s https://thesis-db.fly.dev/api/collections/_superusers/auth-with-password \
  -H "Content-Type: application/json" \
  -d '{"identity":"<email>","password":"<password>"}' | python3 -c "import json,sys; print(json.load(sys.stdin)['token'])")

# List all collections
curl -s https://thesis-db.fly.dev/api/collections \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for c in data.get('items', data if isinstance(data, list) else []):
    fields = len(c.get('fields', []))
    print(f\"{c['name']}: {fields} fields\")
"
```

Expected: 78 collections listed with correct field counts.

- [ ] **Step 2: Spot-check field definitions for ai_projects**

```bash
curl -s https://thesis-db.fly.dev/api/collections/ai_projects \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

Verify: all fields present, correct types (`editor` for large text, `json` for arrays, `number` for integers, autodate for created/updated).

- [ ] **Step 3: Test CRUD on ai_projects**

```bash
# Create
curl -s https://thesis-db.fly.dev/api/collections/ai_projects/records \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_code":"TEST01","title":"Test Project","status":"active"}' | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'Created: {d[\"id\"]}')"

# List
curl -s "https://thesis-db.fly.dev/api/collections/ai_projects/records?filter=project_code='TEST01'" \
  -H "Authorization: Bearer $TOKEN"

# Delete the test record
curl -s -X DELETE "https://thesis-db.fly.dev/api/collections/ai_projects/records/<id>" \
  -H "Authorization: Bearer $TOKEN"
```

- [ ] **Step 4: If any collections have missing fields, patch them**

```bash
# Example: patch ai_projects to add a missing field
curl -s -X PATCH https://thesis-db.fly.dev/api/collections/ai_projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"fields":[...existing fields..., {"name":"missing_field","type":"text"}]}'
```

- [ ] **Step 5: Commit any migration fixes**

```bash
git add pb_migrations/
git commit -m "fix: patch PB migration fields after deploy verification"
```

---

## Plan Self-Review

- **Spec coverage:** All 78 tables from the spec's "Migrated" section are covered across migrations 1001-1013. Excluded tables (gaf_*, views, users, clients, oauth_states, google_drive_*) match the spec. Dockerfile and fly config match the spec's deployment section.
- **Placeholder scan:** No TBDs. Tasks 4-15 describe field mappings rather than providing complete JS -- this is intentional since the subagent has the schema query command and mapping rules to produce the JS. Task 3 provides the complete pattern to follow.
- **Type consistency:** All migrations use the same `new Collection()` pattern with plain field objects, autodate fields, two-pass ordering, and down migration cleanup.

---

## Next Plans

- **Plan 2:** Application Layer + Backend Rewrite (pb_client.py, vec_client.py, config.py, auth.py, repositories, route/service rewrites)
- **Plan 3:** Vector Sidecar + Data Migration + Frontend (sqlite-vec FastAPI app, migration script, frontend auth changes)
