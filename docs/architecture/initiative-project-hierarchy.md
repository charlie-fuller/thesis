# Initiative -> Project -> Task Hierarchy

**Date**: 2026-02-02
**Decision Type**: Architecture
**Status**: Implemented

## Context

During a strategic review of Thesis functionality, we clarified the relationship between Initiatives, Projects, and Tasks. This document captures the decision and rationale.

## Architecture

```
Initiative (discovery, document chat, PRD)
    └── Project (implementation, tasks, tier scoring)
            └── Tasks
```

## Definitions

### Initiative
- **Purpose**: Discovery phase - understanding a problem space, gathering requirements, doing DISCo/PuRDy work
- **Contains**: Documents, stakeholder interviews, discovery artifacts, PRDs
- **Status Values**: `discovery`, `documented`, `prep_complete`, `in_progress`, `closed`
- **Example**: "JD Generator" initiative for exploring AI-generated job descriptions

### Project
- **Purpose**: Implementation phase - building something, tracking work, measuring progress
- **Contains**: Tasks, tier scores (ROI, effort, alignment, readiness), status tracking
- **Link to Initiative**: `initiative_ids` array on `ai_projects` table
- **Status Values**: `identified`, `scoping`, `pilot`, `scaling`, `blocked`, `closed`
- **Example**: "L56 Risk Scoring Agent" project under Legal Kickoff initiative

### Task
- **Purpose**: Individual work items on the kanban board
- **Contains**: Title, description, status, priority, assignee, tags
- **Link to Project**: `linked_project_id` on `project_tasks` table
- **Link to Initiative**: Via tags (e.g., `["jd-generator"]`)
- **Status Values**: `backlog`, `pending`, `in_progress`, `blocked`, `done`

## Key Rules

1. **Default to Initiative** for anything needing discovery or document chat
2. **Add Projects when ready to implement** - projects are spawned from initiatives
3. **Date filter**: Only documents from January 5, 2026 onward are linked
4. **One Initiative can have many Projects** - but projects typically belong to one initiative

## Database Schema

### disco_initiatives
- `id`: UUID
- `name`: Slug-style name (e.g., "jd-generator")
- `description`: Full description
- `status`: Current phase
- `created_by`: User UUID

### disco_initiative_documents
- Junction table linking initiatives to KB documents
- `initiative_id`: UUID
- `document_id`: UUID (from `documents` table)
- `linked_by`: User UUID
- `linked_at`: Timestamp

### ai_projects
- `id`: UUID
- `initiative_ids`: UUID array (links to disco_initiatives)
- Standard project fields (title, scores, status, etc.)

### project_tasks
- `id`: UUID
- `linked_project_id`: UUID (optional link to ai_projects)
- `tags`: Text array (used to associate with initiatives via tag name)

## Initiatives Created

| Name | Status | Documents | Tasks |
|------|--------|-----------|-------|
| strategic-account-planning | documented | 0 | 0 |
| legal-kickoff | prep_complete | 18 | 0 |
| jd-generator | discovery | 8 | 5 |
| agent-factory | discovery | 15 | 5 |
| thesis-platform | in_progress | 13 | 5 |

## API Endpoints

### Initiatives
- `GET /api/disco/initiatives` - List all initiatives
- `POST /api/disco/initiatives` - Create initiative
- `GET /api/disco/initiatives/{id}` - Get initiative details
- `PATCH /api/disco/initiatives/{id}` - Update initiative

### Document Linking
- `POST /api/disco/initiatives/{id}/documents/link` - Link KB documents
- `GET /api/disco/initiatives/{id}/linked-documents` - Get linked documents
- `DELETE /api/disco/initiatives/{id}/linked-documents/{doc_id}` - Unlink document

### Projects
- `PATCH /api/projects/{id}` - Update project (including initiative_ids)

## Implementation Notes

1. Tasks don't have a direct `initiative_id` column yet - use tags as a workaround
2. L56 and L83 projects are already linked to legal-kickoff initiative
3. Strategic Account Planning initiative has no documents linked (still in early discovery)

## Related Files

- `backend/api/routes/disco/initiatives.py` - Initiative API
- `backend/api/routes/disco/documents.py` - Document linking API
- `backend/api/routes/projects.py` - Project API with initiative_ids support
- `database/migrations/062_project_initiatives.sql` - Migration adding initiative_ids

## Future Enhancements

1. Add `initiative_id` column to `project_tasks` for direct linking
2. UI to show initiative -> project -> task hierarchy
3. Auto-suggest project creation when initiative reaches "documented" status
