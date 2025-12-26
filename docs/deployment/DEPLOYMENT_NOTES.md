# Thesis System Instructions - Deployment Notes

**Date:** December 11, 2025
**Status:** Complete

## What Was Done

Combined all 5 P0 sections into a single production-ready system instructions file.

### Files Created/Updated

1. **`system-instructions/thesis-instructions.md`** (Master Copy)
   - Combined sections 1-5 from individual P0 files
   - Markdown format with XML code blocks
   - Wrapped in `<system>` tags for Claude compatibility
   - **Keep this file** - it's your master version for editing

2. **`backend/system_instructions/default.txt`** (Production File)
   - Extracted pure XML from thesis-instructions.md
   - 39,679 characters
   - Used by the application's `system_instructions_loader.py`
   - Auto-generated from master file

## How It Works

The application loads system instructions through this flow:

```
User starts chat
    ↓
system_instructions_loader.py
    ↓
Priority 1: Supabase Storage (users/{user_id}.txt)
Priority 2: Local user file (backend/system_instructions/users/{user_id}.txt)
Priority 3: Default fallback (backend/system_instructions/default.txt) ← NEW FILE
    ↓
Template variables replaced ({user_name}, {client_name}, etc.)
    ↓
Cached in Redis (1-hour TTL)
    ↓
Sent to Claude API as system prompt
```

## Making Changes

### To Update System Instructions:

1. **Edit the master file:**
   ```bash
   # Edit this file with your changes
   system-instructions/thesis-instructions.md
   ```

2. **Regenerate the production file:**
   ```bash
   python3 << 'PYTHON_EOF'
   import re

   # Read the markdown file
   with open('system-instructions/thesis-instructions.md', 'r') as f:
       content = f.read()

   # Extract all XML blocks
   xml_blocks = re.findall(r'```xml\n(.*?)\n```', content, re.DOTALL)
   combined_xml = '\n\n'.join(xml_blocks)

   # Wrap in XML document structure
   final_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
   <thesis_system_instructions version="1.0" updated="2025-12-11">

       <!-- ===================================================================== -->
       <!-- THESIS SYSTEM INSTRUCTIONS - PRODUCTION VERSION                      -->
       <!-- Combined from P0 Sections 1-5                                        -->
       <!-- Last Updated: December 11, 2025                                      -->
       <!-- ===================================================================== -->

   {combined_xml}

   </thesis_system_instructions>
   '''

   # Write to production file
   with open('backend/system_instructions/default.txt', 'w', encoding='utf-8') as f:
       f.write(final_xml)

   print("Production file updated")
   PYTHON_EOF
   ```

3. **Restart the server:**
   ```bash
   cd backend
   # Stop current server (Ctrl+C)
   source venv/bin/activate
   uvicorn app:app --reload
   ```

### Quick Update Script

Create a file `update-instructions.sh` in the root:

```bash
#!/bin/bash
python3 << 'PYTHON_EOF'
import re
with open('system-instructions/thesis-instructions.md', 'r') as f:
    content = f.read()
xml_blocks = re.findall(r'```xml\n(.*?)\n```', content, re.DOTALL)
combined_xml = '\n\n'.join(xml_blocks)
final_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<thesis_system_instructions version="1.0" updated="2025-12-11">
{combined_xml}
</thesis_system_instructions>'''
with open('backend/system_instructions/default.txt', 'w', encoding='utf-8') as f:
    f.write(final_xml)
print("Updated")
PYTHON_EOF
echo "Remember to restart the backend server!"
```

## Architecture Notes

### System Instructions Loader
- File: `backend/system_instructions_loader.py`
- Supports per-user customization
- Template variable replacement
- Redis caching with 1-hour TTL
- LRU cache in Python (cleared on restart)

### Storage Priority
1. **Supabase Storage** - Persistent, production (if bucket exists)
2. **Local user files** - Per-user overrides
3. **Default file** - Fallback for all users ← Your new instructions

### Cache Behavior
- **Redis Cache:** 1-hour TTL (if Redis available)
- **LRU Cache:** In-memory, cleared on server restart
- **Result:** Restart server to apply changes immediately

## What Users Will Experience

After deployment, Thesis will:

- Use the **Thesis Bishop + Mr. Miyagi** persona
- Apply **Bradbury Architecture Method** (BAM) externally
- Keep **LTEM framework** black-boxed internally
- Prioritize **ROI-first, data-driven** approach
- Teach through doing (not gate-keeping)
- Use adaptive modes: Coach, Developer, Analyst, Advisor
- Support command shortcuts: `/visualize`, `/assess`, `/roi`, etc.
- Apply enhanced guardrails against prompt injection

## Testing

To verify the instructions are loaded:

```bash
cd backend
source venv/bin/activate
python3 << 'PYTHON_EOF'
from dotenv import load_dotenv
load_dotenv()
from system_instructions_loader import load_user_system_instructions

instructions = load_user_system_instructions(
    user_id="test-123",
    user_name="Test User",
    client_name="Test Org"
)

# Check for all 5 sections
sections = ['core_philosophy', 'output_format', 'operating_modes',
            'command_shortcuts', 'enhanced_guardrails']
found = [s for s in sections if f'<{s}>' in instructions]

print(f"Loaded {len(instructions):,} characters")
print(f"Found {len(found)}/5 sections: {', '.join(found)}")
PYTHON_EOF
```

## Rollback Plan

If you need to revert:

```bash
# Restore old default.txt from git
git checkout HEAD -- backend/system_instructions/default.txt

# Or restore from backup
cp backend/system_instructions/default.txt.backup backend/system_instructions/default.txt

# Restart server
cd backend && uvicorn app:app --reload
```

## Production Deployment

When deploying to production (Railway, etc.):

1. The file `backend/system_instructions/default.txt` is already in the repo
2. It will be deployed automatically with your code
3. **Note:** Supabase Storage bucket is not configured (local files work fine)
4. If you want Supabase Storage, create the bucket and upload:
   ```bash
   # Create bucket in Supabase dashboard first, then:
   cd backend
   python3 upload_system_instructions.py --help
   ```

## Next Steps

1. **Done:** Master file created and production file generated
2. **Now:** Restart backend server to apply changes
3. **Test:** Start a new chat and verify Thesis's behavior
4. **Document:** Update any user-facing documentation about Thesis's capabilities

---

**Questions or Issues?**
- Master file location: `system-instructions/thesis-instructions.md`
- Production file: `backend/system_instructions/default.txt`
- Loader code: `backend/system_instructions_loader.py`
