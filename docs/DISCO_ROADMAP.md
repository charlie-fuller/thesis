# DISCO System Roadmap

This document captures planned improvements to the DISCO (Discovery-Intelligence-Synthesis-Convergence-Operationalize) system based on the AI Platform Governance initiative restructuring work.

## Background

When restructuring the "Agent Factory" initiative into a proper hierarchy with the "AI Platform Governance" initiative as the parent, several system limitations became apparent. This roadmap documents the changes needed to improve DISCO's flexibility.

---

## Part 2: Future DISCO System Changes

### 2.1 Flexible Output Types

**Current State:** DISCO produces PRDs (Product Requirements Documents) only via the Synthesis stage.

**Needed:** Flexible output types based on initiative/bundle type.

| Bundle Type | Output Document | Project Type |
|-------------|-----------------|--------------|
| Build a product | Product Requirements Doc | Development project |
| Evaluate options | Evaluation Framework | Research project |
| Create a process | Process Specification | Implementation project |
| Make a decision | Decision Framework | Governance project |

**Implementation:**

1. Add `output_type` field to `disco_bundles` and `disco_prds` tables:
   ```sql
   ALTER TABLE disco_bundles ADD COLUMN output_type VARCHAR(50) DEFAULT 'prd';
   ALTER TABLE disco_prds ADD COLUMN output_type VARCHAR(50) DEFAULT 'prd';
   ```

2. Modify Requirements Generator agent (`backend/agents/disco/requirements_generator.py`) to:
   - Accept `output_type` parameter
   - Use different prompt templates based on output type
   - Generate appropriate document structure

3. Update UI (`frontend/app/disco/[initiative_id]/synthesis/`) to:
   - Allow selecting output type when creating a bundle
   - Display appropriate labels/icons based on output type

**Files to Modify:**
- `backend/api/routes/disco/synthesis.py`
- `backend/services/disco/prd_service.py`
- `backend/agents/disco/requirements_generator.py`
- `frontend/app/disco/[initiative_id]/synthesis/page.tsx`
- New migration: `database/migrations/XXX_disco_output_types.sql`

---

### 2.2 Create Project from PRD/Bundle

**Current State:** PRDs are the end of the DISCO workflow. No automated way to spawn a Project.

**Needed:** Action to create a Project from an approved PRD/Bundle.

**Implementation:**

1. Add endpoint: `POST /api/disco/prds/{prd_id}/create-project`
   ```python
   @router.post("/prds/{prd_id}/create-project")
   async def create_project_from_prd(prd_id: str, current_user: dict):
       prd = await get_prd(prd_id)
       project = await create_project(
           title=prd["name"],
           description=prd["summary"],
           initiative_ids=[prd["initiative_id"]],
           source_type="disco_prd",
           source_id=prd_id,
           # Auto-populate scores from PRD if available
       )
       return {"project": project}
   ```

2. Add "Create Project" button on approved PRDs in UI

3. Auto-populate project fields from PRD content:
   - Title from PRD name
   - Description from PRD summary
   - `initiative_ids` links back to parent initiative
   - `source_type` = "disco_prd"
   - `source_id` = PRD ID

4. Attach PRD as project document

**Files to Modify:**
- `backend/api/routes/disco/synthesis.py` - Add create-project endpoint
- `backend/services/disco/prd_service.py` - Project creation logic
- `frontend/app/disco/[initiative_id]/synthesis/page.tsx` - Add button
- `frontend/components/disco/PrdCard.tsx` - Add action button

---

### 2.3 Initiative to Projects View

**Current State:** Can filter projects by initiative from Projects page, but no reverse view from initiative.

**Needed:** View showing all projects linked to an initiative directly from the initiative detail page.

**Current Implementation (Already Working):**
- Projects page supports `?initiative=<id>` query parameter
- Initiative detail page shows "Projects X" button with count
- Clicking links to filtered Projects page

**Enhancement Opportunity:**
Add embedded projects list in initiative detail view (optional):

1. Add endpoint: `GET /api/disco/initiatives/{id}/projects`
   ```python
   @router.get("/initiatives/{initiative_id}/projects")
   async def get_initiative_projects(initiative_id: str):
       supabase = await get_supabase()
       result = await supabase.table("ai_projects")\
           .select("*")\
           .contains("initiative_ids", [initiative_id])\
           .execute()
       return {"projects": result.data}
   ```

2. Add "Projects" tab to initiative detail view showing:
   - Project title, status, tier
   - Quick scoring indicators
   - Link to full project detail

**Files to Modify:**
- `backend/api/routes/disco/initiatives.py` - Add projects endpoint
- `frontend/app/disco/[initiative_id]/page.tsx` - Add projects tab
- `frontend/components/disco/InitiativeProjects.tsx` - New component

---

## Implementation Priority

1. ~~**High Priority:** Create Project from PRD (closes the workflow loop)~~ **COMPLETED** (Feb 4, 2026)
2. ~~**Medium Priority:** Flexible output types (enables research initiatives)~~ **COMPLETED** (Feb 4, 2026)
3. ~~**Low Priority:** Embedded projects view (nice-to-have, current linking works)~~ **COMPLETED** (Feb 4, 2026)

---

## Part 3: Throughline Enhancement (Completed Feb 12, 2026)

### 3.1 Structured Input Framing

**Completed.** Initiatives now support structured throughline data: problem statements, hypotheses (with type: assumption/belief/prediction), known gaps (with type: data/people/process/capability), and desired outcome state.

### 3.2 Agent Throughline Threading

**Completed.** All 4 consolidated agents updated to v1.1 prompts with throughline awareness. Throughline context injected into agent prompts when present.

### 3.3 Convergence Resolution

**Completed.** Requirements Generator produces structured throughline resolution: hypothesis resolutions, gap statuses, state changes, and "So What?" analysis. Parsed and stored in `disco_outputs.throughline_resolution`.

**Migration:** `071_initiative_throughline.sql`
**Files:** `backend/disco_agents/*-v1.1.md`, `backend/services/disco/agent_service.py`, `frontend/components/disco/ThroughlineEditor.tsx`, `frontend/components/disco/ThroughlineSummary.tsx`

---

## Related Files Reference

**Backend:**
- `backend/api/routes/disco/synthesis.py` - Synthesis/PRD endpoints
- `backend/api/routes/disco/initiatives.py` - Initiative CRUD
- `backend/services/disco/prd_service.py` - PRD business logic
- `backend/api/routes/projects.py` - Project management

**Frontend:**
- `frontend/app/disco/[initiative_id]/page.tsx` - Initiative detail
- `frontend/app/disco/[initiative_id]/synthesis/page.tsx` - Synthesis stage
- `frontend/app/projects/` - Projects pages

**Database:**
- `database/migrations/048_disco_synthesis.sql` - Bundles/PRDs tables
- `database/migrations/062_project_initiatives.sql` - Initiative linking

---

## Completed (Part 1)

The following was completed manually via the UI:

1. Created "AI Platform Governance" initiative with comprehensive description including:
   - Strategic framing question
   - Platform inventory (GLEAN, Rovo, Gemini, Agentspace, Vercel AI, Claude API, Thesis, NotebookLM)
   - Expected outputs (Decision Framework, Platform evaluations, Agent Factory)

2. Linked existing "Agent Factory" project to the new initiative:
   - Project T06 now linked to both "agent-factory" and "AI Platform Governance" initiatives
   - Bidirectional linking verified (initiative shows "1 project", project shows both initiatives)

**Initiative ID:** `477ca75f-203f-416e-881f-e946d3d09655`
**URL:** https://thesis-mvp.vercel.app/disco/477ca75f-203f-416e-881f-e946d3d09655
