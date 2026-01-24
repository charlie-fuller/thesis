# Plan: IS Goal Alignment Score for Opportunities

**Created**: 2026-01-23
**Status**: Ready for implementation

## Overview
Add an automated alignment score to opportunities that measures how well each opportunity supports the IS team's FY27 strategic goals. This provides an objective measure beyond the manual `strategic_alignment` score.

## IS Team Goals (Source of Truth)

### 4 Strategic Pillars
1. **Decision-Ready Customer Journey** - Connected systems, full visibility, faster decisions
2. **Maximize Business Systems & AI Value** - Portfolio optimization, support AI initiatives, maximize ROI
3. **Data-First Digital Workforce** - Insight 360, agentic capabilities, AI solving problems
4. **High-Trust IS Culture** - Team development, stakeholder communication

### Key KPIs
| KPI | Current | Target |
|-----|---------|--------|
| AI Agent Success Rate | 4% | 80% |
| Production Agents | 15 | 50+ |
| Self-Service Resolution | 45% | 80% |
| Zero Friction Lifecycle | 15/mo | 0/mo |

## Implementation Approach

### 1. Database Migration
Add fields to `ai_opportunities` table:
```sql
-- Migration: 037_goal_alignment.sql
ALTER TABLE ai_opportunities
ADD COLUMN goal_alignment_score INTEGER CHECK (goal_alignment_score >= 0 AND goal_alignment_score <= 100),
ADD COLUMN goal_alignment_details JSONB DEFAULT '{}'::jsonb;

CREATE INDEX idx_opportunities_goal_alignment ON ai_opportunities(client_id, goal_alignment_score);
```

The `goal_alignment_details` JSONB will store:
```json
{
  "pillar_scores": {
    "decision_ready_journey": { "score": 0-25, "rationale": "..." },
    "maximize_systems_ai": { "score": 0-25, "rationale": "..." },
    "data_first_workforce": { "score": 0-25, "rationale": "..." },
    "high_trust_culture": { "score": 0-25, "rationale": "..." }
  },
  "kpi_impacts": ["AI Agent Success Rate", "Production Agents"],
  "summary": "Overall alignment summary",
  "analyzed_at": "2026-01-23T..."
}
```

### 2. Backend Service: `goal_alignment_analyzer.py`
Create `/backend/services/goal_alignment_analyzer.py`:

- `IS_GOALS` constant defining the 4 pillars with descriptions and KPIs
- `analyze_goal_alignment(opportunity: dict) -> tuple[int, dict]`
  - Uses Claude Haiku to analyze opportunity against IS goals
  - Returns (score 0-100, details dict)
  - Prompt includes opportunity context + IS goals definitions
  - Each pillar scored 0-25 points
- `batch_analyze_all(client_id: str) -> dict` for bulk analysis

### 3. API Endpoints
Add to `/backend/api/routes/opportunities.py`:

- `POST /{opportunity_id}/analyze-goal-alignment` - Analyze single opportunity
- `POST /analyze-goal-alignment/all` - Batch analyze all opportunities

### 4. Frontend Display
Update `OpportunityDetailModal.tsx`:

- Add "Goal Alignment" tab (or section in Analysis tab)
- Show overall score (0-100) with color coding
- Display 4-pillar breakdown with individual scores and rationale
- List impacted KPIs
- "Analyze" button to trigger/refresh analysis

## Files to Modify

| File | Changes |
|------|---------|
| `/database/migrations/037_goal_alignment.sql` | New migration for fields |
| `/backend/services/goal_alignment_analyzer.py` | NEW - Analysis service |
| `/backend/api/routes/opportunities.py` | Add 2 endpoints |
| `/frontend/components/opportunities/OpportunityDetailModal.tsx` | Display alignment score |
| `/frontend/components/opportunities/GoalAlignmentSection.tsx` | NEW - Visual component |

## Verification

1. Run migration on database
2. Test endpoint: `POST /api/opportunities/{id}/analyze-goal-alignment`
3. Verify score and details saved to database
4. Open opportunity modal, confirm score displays correctly
5. Test batch analysis endpoint
6. Verify scores update when opportunity details change
