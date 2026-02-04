# DISCo Rebrand Session - January 25, 2026

## Summary

Rebranded PuRDy to DISCo (Discovery, Intelligence, Synthesis, Convergence) and reorganized repository structure.

## Changes Made

### Repository Consolidation
- Moved thesis repo to `/vaults/Contentful/GitHub/thesis`
- Merged KB and initiatives from purdy-cf into thesis
- Archived purdy-cf to `/vaults/Contentful/GitHub/archived/purdy-cf`

### UI Rebrand (PuRDy to DISCo)
- Nav link: "PuRDy" -> "DISCo"
- Page title: "DISCo - Discovery, Intelligence, Synthesis, Convergence"
- Status cards updated to DISCo workflow stages:
  - Draft, Triaged, Discovery, Intelligence, Synthesis, Convergence, Archived

### Route Changes
- Frontend routes: `/purdy` -> `/disco`
- API endpoints: unchanged (`/api/purdy/*`) for backwards compatibility
- Components folder: unchanged (`components/purdy/`)

### Simplified Initiative Tabs
- Removed: Synthesis, PRDs tabs
- Kept: Documents, Run Agent, Outputs, Chat
- PRD outputs now appear in the Outputs tab

## Files Modified

### Frontend
- `app/disco/` (renamed from `app/purdy/`)
- `components/PageHeader.tsx`
- `middleware.ts`

### Documentation
- `CLAUDE.md` - Updated paths and branding

## Migration Notes

- Users accessing `/purdy` will need to use `/disco`
- API calls remain unchanged
- Database tables unchanged (`purdy_*` prefix retained)
