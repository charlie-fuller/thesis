# Stakeholder Auto-Discovery from Meeting Summaries

## Overview
Add automatic stakeholder discovery from meeting transcripts/summaries, following the same pattern as task extraction:
1. LLM extracts stakeholder candidates from documents
2. Candidates staged for user review
3. On accept: create stakeholder + auto-link to related opportunities/tasks

## User Decisions
- **Extraction trigger:** Manual scan only (no auto-extraction on upload)
- **Duplicate handling:** Show merge option, let user decide
- **Review UI location:** "Candidates" tab on /stakeholders page

## Architecture

### Database Schema

**New table: `stakeholder_candidates`**
```sql
CREATE TABLE stakeholder_candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id),

    -- Extracted info
    name TEXT NOT NULL,
    role TEXT,
    department TEXT,
    organization TEXT,
    email TEXT,

    -- Context from extraction
    key_concerns JSONB DEFAULT '[]',      -- ["budget", "timeline"]
    interests JSONB DEFAULT '[]',          -- ["AI automation", "efficiency"]
    initial_sentiment TEXT,                -- positive/neutral/negative
    influence_level TEXT,                  -- high/medium/low

    -- Source tracking
    source_document_id UUID REFERENCES documents(id),
    source_document_name TEXT,
    source_text TEXT,                      -- Evidence quote
    extraction_context TEXT,               -- Meeting context

    -- Related entities found
    related_opportunity_ids UUID[] DEFAULT '{}',
    related_task_ids UUID[] DEFAULT '{}',

    -- Review status
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'rejected', 'merged')),
    confidence TEXT DEFAULT 'medium' CHECK (confidence IN ('high', 'medium', 'low')),

    -- Deduplication
    potential_match_stakeholder_id UUID REFERENCES stakeholders(id),
    match_confidence FLOAT,

    -- Resolution
    accepted_at TIMESTAMPTZ,
    accepted_by UUID REFERENCES auth.users(id),
    created_stakeholder_id UUID REFERENCES stakeholders(id),
    merged_into_stakeholder_id UUID REFERENCES stakeholders(id),
    rejection_reason TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Track document scanning:**
```sql
ALTER TABLE documents ADD COLUMN stakeholders_scanned_at TIMESTAMPTZ;
```

### Services

**1. `stakeholder_extractor.py`** - LLM extraction logic
- Uses Claude Sonnet for quality extraction
- Prompt: "Identify key stakeholders from this meeting summary"
- Returns: name, role, department, concerns, interests, sentiment, influence, evidence

**2. `stakeholder_scanner.py`** - Manual scan coordinator
- Called via API endpoint (no auto-extraction)
- Filters for meeting summaries (Granola, meeting-summaries folder)
- Scans documents that haven't been scanned yet (or force_rescan)

**3. `stakeholder_deduplicator.py`** - Match detection
- Name similarity matching (fuzzy)
- Same email = definite match
- Same name + role + org = likely match
- Returns potential_match_stakeholder_id with confidence

**4. `stakeholder_linker.py`** - Entity linking
- Searches opportunities by department/title keywords
- Searches tasks by assignee_name match
- Populates related_opportunity_ids and related_task_ids

### API Endpoints

**`/api/stakeholders/candidates`**
- `GET /` - List pending candidates with related entities
- `POST /{id}/accept` - Create stakeholder, link to opportunities/tasks
- `POST /{id}/reject` - Reject with reason
- `POST /{id}/merge` - Merge into existing stakeholder
- `POST /bulk` - Bulk accept/reject

**`/api/stakeholders/scan-documents`**
- `POST` - Manual trigger to scan recent meeting docs
- Params: `since_days`, `force_rescan`, `limit`

### Frontend Components

**1. `StakeholderCandidateReviewPanel.tsx`** (Dashboard)
- Shows count of pending stakeholder candidates
- "Review Stakeholders" button → /stakeholders page

**2. `StakeholderCandidatesTable.tsx`** (/stakeholders page)
- Lists candidates with extracted info
- Shows potential matches (merge option)
- Shows related opportunities/tasks as chips
- Accept/Reject/Merge actions

**3. Updates to existing pages:**
- `/stakeholders` - Add "Candidates" tab or banner
- `/opportunities/[id]` - Show linked stakeholders
- `/tasks` - Show stakeholder links on task cards

## Implementation Steps

### Phase 1: Database
1. Create migration `030_stakeholder_candidates.sql`
2. Add `stakeholders_scanned_at` column to documents

### Phase 2: Backend Services
1. Create `stakeholder_extractor.py` (LLM extraction)
2. Create `stakeholder_scanner.py` (manual scan coordinator)
3. Create `stakeholder_deduplicator.py` (match detection)
4. Create `stakeholder_linker.py` (opportunity/task linking)

### Phase 3: API Routes
1. Add `/api/stakeholders/candidates` routes
2. Add `/api/stakeholders/scan-documents` endpoint

### Phase 4: Frontend
1. Create `StakeholderCandidateCard.tsx` component
2. Add candidates section to `/stakeholders` page
3. Add dashboard review panel
4. Update opportunity/task UIs to show stakeholder links

## Key Files to Modify

**Backend:**
- `/backend/api/routes/stakeholders.py` - Add candidate endpoints
- `/backend/services/` - New extraction services (4 files)

**Frontend:**
- `/frontend/app/stakeholders/page.tsx` - Add candidates UI
- `/frontend/app/page.tsx` - Add review panel
- `/frontend/components/opportunities/` - Show linked stakeholders

**Database:**
- `/database/migrations/030_stakeholder_candidates.sql`

## Verification

1. Upload a meeting summary document
2. Click "Scan for Stakeholders" to trigger extraction
3. Check `stakeholder_candidates` table for extracted entries
4. Verify deduplication detects existing stakeholders
5. Accept a candidate → verify stakeholder created
6. Verify auto-linking to opportunities/tasks works
7. Test merge flow with existing stakeholder
