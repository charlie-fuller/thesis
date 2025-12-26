# Database Migration Guide: Client Simplification

## Overview

This guide walks through running the database migration to simplify the architecture from multi-tenant (clients) to single-tenant (users only).

**Migration:** `migration_001_create_default_client.sql`
**Status:** Safe, idempotent, non-destructive
**Estimated Time:** 5-10 minutes

---

## Prerequisites

Before running this migration:

1.  **Database Backup:** Ensure you have a recent backup
2.  **Staging Environment:** Test on staging first (recommended)
3.  **Supabase Access:** You need access to Supabase SQL Editor
4.  **Admin Privileges:** Must have database write access

---

## Option 1: Run via Supabase SQL Editor (Recommended)

### Step 1: Access Supabase Dashboard
1. Go to https://supabase.com/dashboard
2. Select your project: `superassistant-mvp`
3. Click "SQL Editor" in the left sidebar

### Step 2: Execute Migration Script
1. Click "New Query"
2. Copy the entire contents of `migration_001_create_default_client.sql`
3. Paste into the SQL editor
4. Click "Run" button

### Step 3: Review Results
The script will output several verification checks:

**Expected Output:**
```
 Users with NULL client_id: 0
 Conversations with NULL client_id: 0
 Documents with NULL client_id: 0
 Interview Sessions with NULL client_id: 0

Summary Statistics:
- Total Clients: 1 (or more if you had existing clients)
- Users in Default Client: [your count]
- Conversations in Default Client: [your count]
- Documents in Default Client: [your count]
```

### Step 4: Verify Success
Run this quick verification query:
```sql
SELECT
  'Default Client' as check,
  id,
  name,
  status
FROM clients
WHERE id = '00000000-0000-0000-0000-000000000001';
```

**Expected:** Should return 1 row with name "Default Organization"

---

## Option 2: Run via Command Line (Alternative)

If you have PostgreSQL client installed:

```bash
# Set your Supabase connection string
export DATABASE_URL="postgresql://postgres:[PASSWORD]@[PROJECT_REF].supabase.co:5432/postgres"

# Run the migration
psql $DATABASE_URL -f database/migration_001_create_default_client.sql
```

---

## Option 3: Run via Python Script (For Automation)

Create a file `run_migration.py`:

```python
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_KEY")
)

# Read migration file
with open('database/migration_001_create_default_client.sql', 'r') as f:
    sql = f.read()

# Split by semicolons and execute each statement
statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]

for statement in statements:
    if statement:
        try:
            result = supabase.rpc('exec_sql', {'sql': statement})
            print(f" Executed: {statement[:60]}...")
        except Exception as e:
            print(f" Error: {e}")
```

Then run:
```bash
cd /home/user/superassistant-mvp
python run_migration.py
```

---

## What This Migration Does

### Creates Default Client
- **Client ID:** `00000000-0000-0000-0000-000000000001`
- **Client Name:** "Default Organization"
- **Status:** Active
- **Purpose:** Acts as the hidden organization for all users

### Migrates Orphaned Data
If any records lack a `client_id`, they are assigned to the default client:
- Users without client → Default client
- Conversations without client → Default client
- Documents without client → Default client
- Interview sessions without client → Default client

### Verifies Integrity
Runs comprehensive checks to ensure:
- No NULL `client_id` values remain
- All foreign key relationships are valid
- Default client is properly created
- Statistics are accurate

---

## Troubleshooting

### Issue: "relation 'clients' does not exist"
**Cause:** Database schema not initialized
**Solution:** Run the base schema first from `/backend/migrations/` or technical plan

### Issue: "duplicate key value violates unique constraint"
**Cause:** Default client already exists
**Solution:** This is fine! The script is idempotent and will update the existing record

### Issue: "foreign key violation"
**Cause:** Users reference non-existent client
**Solution:** The migration handles this by creating the default client first

### Issue: Migration hangs or times out
**Cause:** Large dataset, long-running UPDATE
**Solution:** Run in batches:
```sql
-- Update users in batches of 1000
UPDATE users
SET client_id = '00000000-0000-0000-0000-000000000001'
WHERE client_id IS NULL
AND id IN (
  SELECT id FROM users WHERE client_id IS NULL LIMIT 1000
);
-- Repeat until no rows affected
```

---

## Rollback Plan

If you need to undo this migration:

### Quick Rollback (if no code changes deployed yet)
```sql
-- This will only work if nothing references the default client yet
DELETE FROM clients WHERE id = '00000000-0000-0000-0000-000000000001';
```

### Full Rollback (if code changes are deployed)
You'll need to:
1. Redeploy previous version of code
2. Reassign users back to original clients (if you had multiple)
3. Delete default client

**Note:** Because this migration is non-destructive, rollback is simple - just revert code changes. The database can stay as-is.

---

## Post-Migration Steps

After successfully running this migration:

1.  **Update Environment Variables:**
   - Add `DEFAULT_CLIENT_ID=00000000-0000-0000-0000-000000000001` to Railway
   - Add to local `.env` file

2.  **Proceed to Phase 2:**
   - Update backend code to use default client
   - See main implementation plan

3.  **Monitor Logs:**
   - Check for any client_id related errors
   - Verify users can still log in

---

## Verification Checklist

After migration, verify:

- [ ] Default client exists in database
- [ ] All users have client_id assigned
- [ ] All conversations have client_id assigned
- [ ] All documents have client_id assigned
- [ ] No NULL client_id values remain
- [ ] Users can still log in
- [ ] Conversations still load
- [ ] Documents still accessible
- [ ] RLS policies still working

---

## FAQ

**Q: Will this delete any data?**
A: No! This migration only CREATES a default client and ASSIGNS orphaned records. No deletions.

**Q: Can I run this on production?**
A: Yes, it's safe. But we recommend testing on staging first.

**Q: What if I have multiple existing clients?**
A: They will remain in the database. Only NULL client_ids are migrated to default. See "MULTI_CLIENT_CONSOLIDATION.md" for consolidation strategy.

**Q: How long does this take?**
A: Usually < 1 minute. Longer for databases with millions of records (unlikely in MVP).

**Q: Is this reversible?**
A: Yes! The migration is non-destructive. Simply revert code changes to restore multi-tenant mode.

---

## Next Steps

Once this migration succeeds:

1. Mark Phase 1 complete
2. Proceed to Phase 2: Backend Simplification
3. Update environment variables
4. Deploy backend changes

See main implementation plan for detailed Phase 2 instructions.
