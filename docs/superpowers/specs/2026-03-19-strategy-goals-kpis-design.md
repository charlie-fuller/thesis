# Strategy Goals & KPIs Management

## Problem

The Strategy tab has hardcoded company objectives (FY26/FY27) and database-backed KPIs (just added). Goals need to be database-backed too, and users need a proper form to create goals and KPIs without code changes. Team-level goals are a new concept that sits between company objectives and department KPIs.

## Decisions

- **Two tables**: `strategic_goals` (company + team goals) and `department_kpis` (metrics). Goals are aspirations; KPIs are measurements.
- **Unified modal form** with a type dropdown (Company Goal / Team Goal / KPI) that adapts fields dynamically.
- **Modal triggered from Strategy tab** -- "Add" button visible on both sub-tabs.
- **Progress auto-calculated** from current_value / target_value when both exist.
- **Status manually set** (on_track / at_risk / behind / achieved) -- judgment call, not derived.
- **Icons auto-assigned** from a fixed rotation based on priority order. No icon picker.
- **KPI-to-Goal linking optional** -- dropdown of existing goals, not required.

## Data Model

### `strategic_goals` table (new)

```sql
CREATE TABLE strategic_goals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    level VARCHAR(20) NOT NULL CHECK (level IN ('company', 'team')),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    department VARCHAR(100),          -- null for company-level
    owner VARCHAR(255),               -- free text (not FK to stakeholders)
    target_metric VARCHAR(255),
    current_value NUMERIC,
    target_value NUMERIC,
    unit VARCHAR(50),
    status VARCHAR(20) DEFAULT 'on_track' CHECK (status IN ('on_track', 'at_risk', 'behind', 'achieved')),
    priority INTEGER DEFAULT 0,       -- sort order within level
    parent_goal_id UUID REFERENCES strategic_goals(id) ON DELETE SET NULL,
    fiscal_year VARCHAR(10) DEFAULT 'FY27',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

Indexes: `client_id`, `level`, `fiscal_year`, `parent_goal_id`.
RLS: same pattern as `department_kpis`.
Trigger: `updated_at` auto-update.

Progress is computed in the frontend: `Math.round((current_value / target_value) * 100)` when both values exist, otherwise null.

Icons assigned from a fixed array by priority index: `[Target, TrendingUp, Sparkles, Users, BarChart3, Building2]`.

### `department_kpis` table (modify)

Add column:
```sql
ALTER TABLE department_kpis ADD COLUMN linked_goal_id UUID REFERENCES strategic_goals(id) ON DELETE SET NULL;
```

The existing `linked_objective_id` (varchar) is kept for backward compatibility during migration but ignored by the frontend going forward.

## API

### Goals endpoints (`backend/api/routes/strategy.py` -- extend existing file)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/strategy/goals` | List goals. Filter by `level`, `department`, `fiscal_year`. |
| POST | `/api/strategy/goals` | Create a goal. |
| PATCH | `/api/strategy/goals/{id}` | Update a goal. |
| DELETE | `/api/strategy/goals/{id}` | Delete a goal. Linked KPIs get `linked_goal_id` set to null (DB cascade). |

Auth: `get_current_user` + `client_id` scoping. Same pattern as KPI endpoints.

### KPI endpoints (modify existing)

- `KPICreate` and `KPIUpdate` models: add `linked_goal_id: Optional[str] = None`.
- To unlink a KPI from a goal, PATCH with `linked_goal_id: null`. The update endpoint must use `model_dump(exclude_unset=True)` (not `if v is not None` filtering) so that an explicit `null` is distinguished from "field not sent". Apply the same pattern to the Goals update endpoint.

## Frontend

### New component: `StrategyFormModal.tsx`

Unified modal with a type dropdown as the first field:

**Type = "Company Goal":**
- title, description, target_metric, target_value, unit, status, fiscal_year, priority

**Type = "Team Goal":**
- title, description, department, owner, target_metric, target_value, unit, status, fiscal_year, priority, parent_goal (dropdown of company goals for selected fiscal_year)

**Type = "KPI":**
- kpi_name, description, department, target_value, unit, linked_goal (dropdown of all goals, optional), fiscal_year

The modal supports both create (empty form) and edit (pre-filled from existing record) modes. Edit mode locks the type field.

### Modify: `StrategyContent.tsx`

**Company Objectives tab:**
- Remove `FY26_OBJECTIVES` and `FY27_OBJECTIVES` hardcoded arrays.
- Fetch from `GET /api/strategy/goals?level=company&fiscal_year=FY27` (and FY26 for that tab).
- Render with same card layout. Progress computed client-side.
- Pencil icon on hover opens `StrategyFormModal` in edit mode.

**Department KPIs tab:**
- Existing inline edit stays.
- Pencil icon can optionally open the modal for a richer edit experience.

**Shared "Add" button:**
- Placed in the header area, visible on both sub-tabs.
- Opens `StrategyFormModal` in create mode.
- Pre-fills type based on which sub-tab is active (Company Goal if on objectives tab, KPI if on department tab).

### Team Goals display

Team goals appear as a new collapsible section within the Department KPIs tab, grouped by department. Each department section shows its team goals (if any) above its KPIs. This avoids a third top-level tab.

Team goals are fetched via `GET /api/strategy/goals?level=team` on mount (same useEffect as KPIs). The frontend merges goals and KPIs client-side by department for display.

## Migration

### `054_strategic_goals.sql`

1. Create `strategic_goals` table with indexes, RLS, trigger.
2. Add `linked_goal_id` column to `department_kpis`.
3. Seed FY26 objectives (4 rows) and FY27 objectives (4 rows) from the current hardcoded data. FY26 goals carry over `current_value` fields (null, 113, 5, 92). FY27 goals all have `current_value = NULL`.
4. Backfill `linked_goal_id` on existing KPIs: insert goals one at a time in a PL/pgSQL block, capturing each UUID. Then UPDATE `department_kpis` SET `linked_goal_id` = captured UUID WHERE `linked_objective_id` matches the goal's priority number (e.g., KPIs with `linked_objective_id = '2'` get the FY27 goal with `priority = 2`).

## Files

| File | Action |
|------|--------|
| `backend/migrations/054_strategic_goals.sql` | New -- table, alter department_kpis, seed, backfill |
| `backend/api/routes/strategy.py` | Edit -- add goals CRUD endpoints, add linked_goal_id to KPI models |
| `frontend/components/StrategyFormModal.tsx` | New -- unified create/edit modal |
| `frontend/components/StrategyContent.tsx` | Edit -- remove hardcoded objectives, fetch from API, add button, team goals display |

## Verification

1. Run migration against Supabase.
2. `GET /api/strategy/goals` returns 8 seeded goals (4 FY26 + 4 FY27).
3. `GET /api/strategy/kpis` still returns 10 KPIs (now with linked_goal_id populated).
4. Frontend: Company Objectives tab renders from database (identical to current appearance).
5. Frontend: "Add" button opens modal, create a team goal, verify it appears under the right department.
6. Frontend: Create a KPI linked to a goal, verify the link displays.
7. `npx tsc --noEmit` passes clean.
