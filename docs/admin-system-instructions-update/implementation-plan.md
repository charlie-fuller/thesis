# System Instructions Versioning & Upload - Implementation Plan

## Overview

Add admin functionality to upload, manage, and version global system instructions in the Thesis application. New chat sessions will use the latest active version, while existing chats maintain their original version for consistency.

---

## Requirements Summary

**Scope:**
- Global system instructions only (no per-user customization)
- Version history with full audit trail
- File upload interface for new versions
- Immediate activation for new chats
- Existing chats continue with their bound version

**Features:**
- ✅ Admin upload interface (multipart file upload)
- ✅ Version history display (list all versions with metadata)
- ✅ Version comparison (diff viewer)
- ✅ Rollback capability (activate any previous version)
- ✅ Version notes/changelog (admin adds description per version)
- ✅ Audit trail (who uploaded/activated, when)

---

## Database Schema

### New Table: `system_instruction_versions`

```sql
CREATE TABLE IF NOT EXISTS system_instruction_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    version_number VARCHAR(20) NOT NULL UNIQUE,
    content TEXT NOT NULL,
    storage_path TEXT,
    file_size BIGINT DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    is_active BOOLEAN DEFAULT FALSE,
    version_notes TEXT,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    activated_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    activated_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',

    CONSTRAINT version_number_format CHECK (version_number ~ '^[0-9]+\.[0-9]+(-.+)?$')
);

CREATE INDEX idx_system_instruction_versions_status ON system_instruction_versions(status);
CREATE INDEX idx_system_instruction_versions_is_active ON system_instruction_versions(is_active);
CREATE INDEX idx_system_instruction_versions_created_at ON system_instruction_versions(created_at DESC);

-- Ensure only one active version at a time
CREATE UNIQUE INDEX idx_only_one_active_version
    ON system_instruction_versions(is_active)
    WHERE is_active = TRUE;
```

### Update `conversations` Table

```sql
ALTER TABLE conversations
ADD COLUMN system_instruction_version_id UUID REFERENCES system_instruction_versions(id) ON DELETE SET NULL;

CREATE INDEX idx_conversations_si_version_id ON conversations(system_instruction_version_id);
```

### Migration Strategy

**File:** `/Users/motorthings/Documents/GitHub/thesis/database/migrations/add_system_instruction_versioning.sql`

1. Create `system_instruction_versions` table
2. Migrate existing `/backend/system_instructions/default.txt` to version 1.3
3. Add `system_instruction_version_id` column to `conversations`
4. Bind all existing conversations to version 1.3

---

## Backend Implementation

### 1. New Admin API Routes

**File:** `/Users/motorthings/Documents/GitHub/thesis/backend/api/routes/system_instructions.py` (NEW)

**Endpoints:**
```python
POST   /api/admin/system-instructions/upload
       - Upload new system instructions file
       - Params: file (UploadFile), version_number (str), version_notes (str)
       - Returns: Created version object
       - Auth: Admin only

GET    /api/admin/system-instructions/versions
       - List all versions with metadata
       - Query params: limit, offset, status filter
       - Returns: Array of version objects
       - Auth: Admin only

GET    /api/admin/system-instructions/versions/{version_id}
       - Get full details of specific version
       - Returns: Version object with full content
       - Auth: Admin only

GET    /api/admin/system-instructions/versions/active
       - Get currently active version
       - Returns: Active version object
       - Auth: All authenticated users

POST   /api/admin/system-instructions/versions/{version_id}/activate
       - Activate a version (makes it default for new chats)
       - Deactivates current active, activates selected
       - Invalidates all system instruction caches
       - Returns: Updated version object
       - Auth: Admin only

POST   /api/admin/system-instructions/versions/compare
       - Generate diff between two versions
       - Body: {version_a_id, version_b_id}
       - Returns: {diff: [...], stats: {additions, deletions}}
       - Auth: Admin only

DELETE /api/admin/system-instructions/versions/{version_id}
       - Delete a version (cannot delete active or bound versions)
       - Returns: Success message
       - Auth: Admin only

PATCH  /api/admin/system-instructions/versions/{version_id}
       - Update version notes/changelog
       - Body: {version_notes}
       - Returns: Updated version object
       - Auth: Admin only
```

**Key Implementation Details:**
- Use existing document upload pattern from `/backend/api/routes/documents.py`
- Validate file type (.txt, .xml only), size (max 50MB)
- Store content directly in database `content` column (files typically <100KB)
- Use database transactions for activation to prevent race conditions
- Clear Redis cache on activation

### 2. Update System Instructions Loader

**File:** `/Users/motorthings/Documents/GitHub/thesis/backend/system_instructions_loader.py` (MODIFY)

**Add new functions:**

```python
@lru_cache(maxsize=32)
def get_active_system_instruction_version() -> dict:
    """Get currently active version from database"""
    result = supabase.table('system_instruction_versions')\
        .select('*')\
        .eq('is_active', True)\
        .single()\
        .execute()

    if not result.data:
        raise HTTPException(500, "No active system instruction version")

    return result.data

@lru_cache(maxsize=128)
def get_system_instructions_for_version(version_id: str, user_data: dict) -> str:
    """Load system instructions for specific version with template vars replaced"""
    result = supabase.table('system_instruction_versions')\
        .select('content')\
        .eq('id', version_id)\
        .single()\
        .execute()

    if not result.data:
        raise ValueError(f"Version {version_id} not found")

    content = result.data['content']

    # Replace template variables
    variables = {
        "user_name": user_data.get('name', 'User'),
        "user_email": user_data.get('email', ''),
        "user_role": user_data.get('role', 'user'),
        "client_id": user_data.get('client_id') or get_default_client_id(),
        "client_name": get_client_name(),
        "assistant_name": get_assistant_name()
    }
    content = replace_template_variables(content, variables)

    return content
```

### 3. Update Chat Endpoint with Version Binding

**File:** `/Users/motorthings/Documents/GitHub/thesis/backend/api/routes/chat.py` (MODIFY)

**Location:** Lines 187-199 (system instructions loading section)

**Replace current logic with:**

```python
# Load system instructions with version binding
try:
    if chat_request.conversation_id:
        # Existing conversation - check for bound version
        conversation = supabase.table('conversations')\
            .select('system_instruction_version_id')\
            .eq('id', chat_request.conversation_id)\
            .single()\
            .execute()

        version_id = conversation.data.get('system_instruction_version_id')

        if version_id:
            # Use bound version
            system_prompt = get_system_instructions_for_version(
                version_id=version_id,
                user_data=current_user
            )
        else:
            # First message - bind to active version
            active_version = get_active_system_instruction_version()
            system_prompt = get_system_instructions_for_version(
                version_id=active_version['id'],
                user_data=current_user
            )

            # Bind conversation to this version
            supabase.table('conversations')\
                .update({'system_instruction_version_id': active_version['id']})\
                .eq('id', chat_request.conversation_id)\
                .execute()

            logger.info(f"Bound conversation {chat_request.conversation_id} to version {active_version['version_number']}")
    else:
        # No conversation context - use active version (won't persist binding)
        active_version = get_active_system_instruction_version()
        system_prompt = get_system_instructions_for_version(
            version_id=active_version['id'],
            user_data=current_user
        )

except Exception as e:
    logger.warning(f"Could not load system instructions: {e}")
    # Fallback prompt
    system_prompt = (
        f"You are Thesis, a helpful AI assistant for {current_user.get('name', 'User')}. "
        "Provide clear, accurate, and professional assistance."
    )
```

### 4. Update Caching Strategy

**File:** `/Users/motorthings/Documents/GitHub/thesis/backend/cache.py` (MODIFY)

**Add version-aware caching:**

```python
def cache_system_instruction_version(version_id: str, content: str, ttl: int = 3600):
    """Cache system instructions for specific version"""
    return cache_set(f"version:{version_id}", content, ttl=ttl, namespace="sys_inst")

def get_cached_system_instruction_version(version_id: str) -> Optional[str]:
    """Get cached system instructions for version"""
    return cache_get(f"version:{version_id}", namespace="sys_inst")

def invalidate_version_cache(version_id: str):
    """Invalidate cache for specific version"""
    cache_delete(f"version:{version_id}", namespace="sys_inst")

def invalidate_all_version_caches():
    """Invalidate all version caches (called on activation)"""
    # Clear all keys in sys_inst namespace
    invalidate_all_system_instructions()
```

---

## Frontend Implementation

### 1. Admin Page: Instructions Dashboard with Tabs

**File:** `/Users/motorthings/Documents/GitHub/thesis/frontend/app/admin/system-instructions/page.tsx` (NEW)

**Page Structure:**
```tsx
<InstructionsDashboard>
  <Tabs>
    <Tab label="Active Instructions">
      <ActiveInstructionsView />
    </Tab>
    <Tab label="Version History">
      <VersionHistoryTable />
    </Tab>
    <Tab label="Upload New">
      <UploadVersionForm />
    </Tab>
    <Tab label="Compare Versions">
      <VersionComparisonTool />
    </Tab>
  </Tabs>
</InstructionsDashboard>
```

**Tab 1: Active Instructions**
- Display current active version number
- Show full content (read-only, syntax-highlighted)
- Display metadata: activated by, activated date, version notes
- Action buttons: "Rollback to Previous", "View History"
- File size and word/character count

**Tab 2: Version History**
- Version history table (sortable, filterable)
- Pagination for version list
- Filter by status (active, archived)
- Sort by date, version number
- Search by version notes
- Actions per row: View, Activate, Compare, Delete

**Tab 3: Upload New**
- Upload form (not modal - integrated into tab)
- Version number input with format validation
- File upload (.txt or .xml files)
- Version notes/changelog textarea
- Preview uploaded content before saving
- Submit button creates new version

**Tab 4: Compare Versions**
- Dropdown to select Version A
- Dropdown to select Version B
- "Generate Comparison" button
- Diff viewer (side-by-side or unified)
- Stats: additions, deletions, unchanged lines

**Key Features:**
- Persistent tab state (URL-based: `/admin/system-instructions?tab=history`)
- Keyboard shortcuts (Ctrl+1/2/3/4 for tab switching)
- Responsive design for mobile admin access

### 2. Tab Components

**Files to create:**

**a) ActiveInstructionsView.tsx** (NEW ~200 lines)
- Displays current active version
- Shows full system instructions content with syntax highlighting
- Metadata display: version number, activated by, activated date
- Quick actions: "Rollback to Previous", "View in History"

**b) UploadVersionForm.tsx** (NEW ~200 lines)
- Integrated form (not modal) in Upload New tab
- Form fields: version number, file upload, version notes
- Real-time validation
- File preview before submission
- Success/error messaging

**Form Fields:**
- Version number (e.g., "2.0", "1.4-beta") - validated format
- File upload (.txt or .xml files only)
- Version notes/changelog (textarea)
- Preview section (shows uploaded content)

**Validation:**
- Version number format: `^\d+\.\d+(-.+)?$`
- File extension: .txt or .xml
- File size: max 50MB
- Required: version number and file

**Flow:**
1. User fills form
2. File upload triggers preview
3. Submit creates FormData with file + metadata
4. POST to `/api/admin/system-instructions/upload`
5. On success: Switch to Version History tab, highlight new version

**c) VersionComparisonTool.tsx** (NEW ~250 lines)
- Integrated comparison tool in Compare Versions tab
- Two dropdowns for version selection
- "Generate Comparison" button
- Inline diff display (no modal)
- Toggle unified/split view

### 3. Version History Table Component

**File:** `/Users/motorthings/Documents/GitHub/thesis/frontend/components/VersionHistoryTable.tsx` (NEW)

**Columns:**
- Version Number (with active badge)
- Status (active/archived)
- File Size
- Created By (user name)
- Created At (timestamp)
- Activated At (timestamp)
- Version Notes (truncated with "Show more")
- Actions (dropdown: View, Activate, Compare, Delete)

**Features:**
- Row click to view full version details
- Inline activation with confirmation
- Compare: Select two versions → open diff modal
- Delete: Confirmation dialog (prevents delete if active or bound)

### 4. Diff Viewer Component

**File:** `/Users/motorthings/Documents/GitHub/thesis/frontend/components/DiffViewer.tsx` (NEW)

**Technology:**
- Use `diff` npm package for generating diffs
- Display unified or side-by-side view

**Features:**
- Line-by-line comparison
- Syntax highlighting (optional for XML)
- Stats: +X additions, -Y deletions
- Toggle between unified/split view

**Flow:**
1. User selects two versions in table
2. Clicks "Compare"
3. POST to `/api/admin/system-instructions/versions/compare`
4. Display diff in modal

### 5. Add Navigation Link

**File:** `/Users/motorthings/Documents/GitHub/thesis/frontend/app/admin/layout.tsx` (MODIFY)

Add link to admin sidebar:
```tsx
<Link href="/admin/system-instructions">
  System Instructions
</Link>
```

---

## Implementation Steps (6-Day Plan)

### Day 1: Database & Migration
1. Create migration file `add_system_instruction_versioning.sql`
2. Write schema: table, indexes, constraints, RLS policies
3. Write migration logic: import default.txt as version 1.3
4. Test migration on local dev environment
5. Verify: `SELECT * FROM system_instruction_versions;`
6. Verify: All conversations bound to version 1.3

### Day 2: Backend API - Part 1
1. Create `/backend/api/routes/system_instructions.py`
2. Implement upload endpoint (file validation, database insert)
3. Implement list versions endpoint (with pagination)
4. Implement get version endpoint
5. Implement get active version endpoint
6. Add route to main FastAPI app
7. Test with Postman/curl

### Day 3: Backend API - Part 2
1. Implement activate version endpoint (with transaction)
2. Implement compare versions endpoint (using difflib)
3. Implement delete version endpoint (with validations)
4. Implement update version notes endpoint
5. Add comprehensive error handling
6. Write unit tests for critical endpoints
7. Test full API flow

### Day 4: Backend Integration
1. Update `system_instructions_loader.py` with new functions
2. Update `chat.py` with version binding logic (lines 187-199)
3. Update `cache.py` with version-aware caching
4. Test chat flow: new chat uses active version
5. Test: activate new version, verify new chats use it
6. Test: existing chat continues with old version
7. Monitor logs for errors

### Day 5: Frontend UI
1. Create reusable Tabs component `/components/ui/Tabs.tsx`
2. Create main admin page `/app/admin/system-instructions/page.tsx` with tabs
3. Create ActiveInstructionsView component (Tab 1)
4. Create UploadVersionForm component (Tab 3)
5. Create VersionHistoryTable component (Tab 2)
6. Create VersionComparisonTool component (Tab 4)
7. Create DiffViewer component (use `diff` package)
8. Add navigation link in admin layout ("System Instructions")
9. Style all components (follow existing admin design patterns)
10. Test tab switching, URL state persistence
11. Test upload → activate → new chat flow in browser

### Day 6: Testing & Deployment
1. End-to-end testing:
   - Upload new version → verify in database
   - Activate version → verify cache invalidated
   - Start new chat → verify uses new version
   - Continue old chat → verify uses old version
   - Compare two versions → verify diff correct
   - Rollback to previous → verify activation works
   - Delete unused version → verify validation works
2. Load testing (multiple concurrent uploads/activations)
3. Deploy to staging
4. Smoke test on staging
5. Deploy to production
6. Monitor production logs for 24 hours

---

## Critical Files Summary

**Backend (7 files):**
1. `/Users/motorthings/Documents/GitHub/thesis/database/migrations/add_system_instruction_versioning.sql` - NEW (Database schema)
2. `/Users/motorthings/Documents/GitHub/thesis/backend/api/routes/system_instructions.py` - NEW (~500 lines, Admin API)
3. `/Users/motorthings/Documents/GitHub/thesis/backend/system_instructions_loader.py` - MODIFY (+50 lines, Version loading)
4. `/Users/motorthings/Documents/GitHub/thesis/backend/api/routes/chat.py` - MODIFY (lines 187-199, Version binding)
5. `/Users/motorthings/Documents/GitHub/thesis/backend/cache.py` - MODIFY (+20 lines, Version caching)
6. `/Users/motorthings/Documents/GitHub/thesis/backend/auth.py` - READ (Verify `require_admin` exists)
7. `/Users/motorthings/Documents/GitHub/thesis/backend/validation.py` - READ (Verify file validation functions)

**Frontend (8 files):**
1. `/Users/motorthings/Documents/GitHub/thesis/frontend/app/admin/system-instructions/page.tsx` - NEW (~300 lines, Main tabbed dashboard)
2. `/Users/motorthings/Documents/GitHub/thesis/frontend/components/ActiveInstructionsView.tsx` - NEW (~200 lines, Active version tab)
3. `/Users/motorthings/Documents/GitHub/thesis/frontend/components/UploadVersionForm.tsx` - NEW (~200 lines, Upload tab)
4. `/Users/motorthings/Documents/GitHub/thesis/frontend/components/VersionHistoryTable.tsx` - NEW (~150 lines, Version history tab)
5. `/Users/motorthings/Documents/GitHub/thesis/frontend/components/VersionComparisonTool.tsx` - NEW (~250 lines, Compare tab)
6. `/Users/motorthings/Documents/GitHub/thesis/frontend/components/DiffViewer.tsx` - NEW (~200 lines, Diff display component)
7. `/Users/motorthings/Documents/GitHub/thesis/frontend/components/ui/Tabs.tsx` - NEW (~100 lines, Reusable tab component)
8. `/Users/motorthings/Documents/GitHub/thesis/frontend/app/admin/layout.tsx` - MODIFY (+5 lines, Navigation)

---

## Edge Cases & Mitigations

### 1. Race Condition During Activation
**Problem:** Two admins activate different versions simultaneously.

**Mitigation:**
- Use database transaction with unique constraint on `is_active = TRUE`
- Transaction atomically: deactivate current → activate new
- Second request fails with clear error message

### 2. Long-Running Chat Sessions
**Problem:** User has chat open for hours; version gets updated.

**Solution:**
- Conversation binds to version on first message
- All subsequent messages use bound version
- User must start new chat to use new version
- Optional: Show UI banner "New system instructions available"

### 3. Corrupted or Invalid File Upload
**Problem:** Admin uploads malformed file.

**Mitigation:**
- Pre-upload validation: file extension, size, encoding (UTF-8)
- XML files: validate XML syntax before saving
- Store as draft/inactive initially
- Admin must manually activate after review

### 4. Cannot Delete Active or Bound Version
**Problem:** Admin tries to delete version in use.

**Mitigation:**
- API validation: `if version.is_active: raise 403`
- Additional check: `if conversations exist with this version_id: raise 403`
- Provide "Archive" status instead of delete

### 5. Storage Growth
**Problem:** Many versions accumulate over time.

**Mitigation:**
- Archive old versions (status = 'archived')
- Soft delete unused versions after 90 days
- Monitor `file_size` column, set alerts if >100MB total

---

## Testing Checklist

**Database:**
- [ ] Migration runs successfully
- [ ] Version 1.3 created from default.txt
- [ ] All conversations bound to version 1.3
- [ ] Only one active version constraint works
- [ ] RLS policies prevent non-admin writes

**Backend API:**
- [ ] Upload new version succeeds
- [ ] Upload invalid file fails with clear error
- [ ] List versions returns paginated results
- [ ] Get active version returns correct version
- [ ] Activate version deactivates old, activates new
- [ ] Activate clears cache
- [ ] Compare versions returns accurate diff
- [ ] Delete active version fails
- [ ] Delete bound version fails
- [ ] Update version notes succeeds

**Chat Integration:**
- [ ] New chat binds to active version
- [ ] Bound chat uses correct version
- [ ] Activate new version → new chats use new version
- [ ] Existing chats continue with old version
- [ ] Template variables replaced correctly
- [ ] Cache hit/miss logged correctly

**Frontend:**
- [ ] Upload modal validates inputs
- [ ] Upload succeeds and refreshes list
- [ ] Version history table displays all versions
- [ ] Active version badge shows correctly
- [ ] Activate button works with confirmation
- [ ] Diff viewer shows accurate comparison
- [ ] Delete confirmation prevents mistakes
- [ ] Navigation link accessible from admin menu

---

## Rollback Plan

If issues arise in production:

1. **Database rollback:**
   ```sql
   BEGIN;
   ALTER TABLE conversations DROP COLUMN system_instruction_version_id;
   DROP TABLE system_instruction_versions CASCADE;
   COMMIT;
   ```

2. **Code rollback:**
   - Revert changes to `chat.py` (restore lines 187-199)
   - Revert changes to `system_instructions_loader.py`
   - Remove `system_instructions.py` route
   - Redeploy previous version

3. **Data preservation:**
   - Before rollback, export version data: `pg_dump -t system_instruction_versions`
   - Store export for future re-migration

---

## Success Criteria

✅ Admin can upload new system instructions file via UI
✅ Version history displays all versions with metadata
✅ Admin can view diff between any two versions
✅ Admin can activate any version (becomes default for new chats)
✅ Admin can rollback to previous version
✅ New chats use latest active version
✅ Existing chats continue with their bound version
✅ Cache invalidated on activation
✅ Audit trail tracks all uploads/activations
✅ Cannot delete active or bound versions
✅ All endpoints require admin authentication

---

## Estimated Effort

- **Database & Migration:** 4 hours
- **Backend API:** 12 hours
- **Backend Integration:** 6 hours
- **Frontend UI:** 10 hours
- **Testing & QA:** 6 hours
- **Deployment & Monitoring:** 2 hours

**Total:** ~40 hours (5 days for 1 developer)

---

## Post-Implementation Enhancements (Future)

- Preview mode: Test version before activation
- Scheduled activation: Set future activation time
- Automatic versioning: Auto-increment version numbers
- Version tagging: Add tags like "production", "testing", "experimental"
- Email notifications: Notify admins when version activated
- Per-user overrides: Allow specific users to use different versions (reintroduce user-specific logic)