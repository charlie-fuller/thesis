# System Instructions

This directory contains system instructions (system prompts) for the Thesis multi-agent platform.

## Directory Structure

```
system_instructions/
├── README.md              # This file
├── agents/                # Agent-specific XML instructions (SOURCE OF TRUTH)
│   ├── atlas.xml          # Research agent
│   ├── fortuna.xml        # Finance agent
│   ├── guardian.xml       # IT/Governance agent
│   ├── counselor.xml      # Legal agent
│   ├── oracle.xml         # Transcript analysis agent
│   ├── sage.xml           # People/Change agent
│   ├── strategist.xml     # Executive strategy agent
│   ├── architect.xml      # Technical architecture agent
│   ├── operator.xml       # Business operations agent
│   ├── pioneer.xml        # Innovation/R&D agent
│   ├── catalyst.xml       # Internal communications agent
│   ├── scholar.xml        # Learning & development agent
│   ├── nexus.xml          # Systems thinking agent
│   ├── echo.xml           # Brand voice agent
│   └── coordinator.xml    # Central orchestrator
├── default.txt            # Legacy fallback (deprecated)
├── system_prompt.txt      # Legacy template (deprecated)
└── users/                 # Legacy per-user instructions (deprecated)
```

## Agent Instructions Architecture

### Single Source of Truth

**XML files in `agents/` are the canonical source** for agent system instructions:

1. **Edit**: Modify XML files in `agents/` directory
2. **Sync**: Run sync script to push changes to database
3. **Activate**: Database `agent_instruction_versions` table serves runtime

### Instruction Loading Hierarchy

When an agent initializes, it loads instructions in this order:

1. **Database** (`agent_instruction_versions` table with `is_active=true`)
2. **XML File** (if database has no entry or placeholder)
3. **Python Default** (`_get_default_instruction()` method in agent class)

### Syncing XML to Database

After editing XML files, sync them to the database:

```bash
cd backend

# Using direct PostgreSQL connection (bypasses schema cache issues)
DATABASE_URL="postgresql://postgres:PASSWORD@db.PROJECT.supabase.co:5432/postgres" \
  ./venv/bin/python scripts/sync_all_xml_to_db_direct.py

# Or using Supabase REST API (may have schema cache delays)
./venv/bin/python scripts/sync_all_xml_to_db.py
```

The sync script will:
- Create new versions for agents without instructions
- Replace placeholder instructions with real XML content
- Skip agents that already have real instructions (>200 chars)

## XML Instruction Format (Gigawatt v4.0 RCCI Framework)

Each agent XML file follows this structure:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<system>

<version>
Name: Agent Name
Version: 1.0
Date: 2025-01-01
Created_By: Author Name
</version>

<role>
Core role and mission statement.
</role>

<context>
Background information and domain knowledge.
</context>

<capabilities>
1. Capability Area One
   - Sub-capability
   - Sub-capability

2. Capability Area Two
   - Sub-capability
</capabilities>

<instructions>
## Section One
Step-by-step instructions...

## Section Two
More instructions...
</instructions>

<criteria>
## Quality Standards
- Standard 1
- Standard 2

## Output Format
Expected format specifications...
</criteria>

<few_shot_examples>
Example inputs and outputs...
</few_shot_examples>

<wisdom>
Key insights and principles...
</wisdom>

<anti_patterns>
What NOT to do...
</anti_patterns>

</system>
```

## Agent Roster (15 Agents)

### Stakeholder Perspective Agents
| Agent | XML File | Purpose |
|-------|----------|---------|
| Atlas | `atlas.xml` | GenAI research, Lean methodology, benchmarking |
| Fortuna | `fortuna.xml` | ROI analysis, SOX compliance, business cases |
| Guardian | `guardian.xml` | Security, compliance, shadow IT, vendor evaluation |
| Counselor | `counselor.xml` | Contracts, AI risks, liability, data privacy |
| Sage | `sage.xml` | Change management, human flourishing, adoption |
| Oracle | `oracle.xml` | Transcript analysis, stakeholder dynamics, sentiment |

### Consulting/Implementation Agents
| Agent | XML File | Purpose |
|-------|----------|---------|
| Strategist | `strategist.xml` | C-suite engagement, organizational politics, governance |
| Architect | `architect.xml` | Enterprise AI patterns, RAG, integration, build vs. buy |
| Operator | `operator.xml` | Process optimization, automation, operational metrics |
| Pioneer | `pioneer.xml` | Emerging technology, hype filtering, maturity assessment |

### Internal Enablement Agents
| Agent | XML File | Purpose |
|-------|----------|---------|
| Catalyst | `catalyst.xml` | AI messaging, employee engagement, AI anxiety |
| Scholar | `scholar.xml` | Training programs, champion enablement, adult learning |
| Echo | `echo.xml` | Voice analysis, style profiling, AI emulation guidelines |

### Systems/Coordination Agents
| Agent | XML File | Purpose |
|-------|----------|---------|
| Nexus | `nexus.xml` | Interconnections, feedback loops, leverage points |
| Coordinator | `coordinator.xml` | Central orchestrator, query routing, response synthesis |

## Version Management

The `agent_instruction_versions` table tracks instruction versions:

```sql
SELECT
    a.name,
    v.version_number,
    v.is_active,
    LENGTH(v.instructions) as chars,
    v.activated_at
FROM agent_instruction_versions v
JOIN agents a ON v.agent_id = a.id
ORDER BY a.name, v.version_number;
```

### Creating New Versions via Admin UI

1. Go to Admin > Agents > Select agent
2. Edit instructions in the textarea or upload an XML file
3. Click "Save & Activate"
4. New version is created and marked active

### Activating Previous Versions

1. Go to Admin > Agents > Select agent > Version History
2. Click "Activate" on desired version
3. Previous active version is deactivated

## Legacy Files (Deprecated)

The following files are from the original Walter system and are no longer used:

- `default.txt` - Legacy fallback template
- `system_prompt.txt` - Legacy system prompt template
- `users/` - Legacy per-user instruction files

These remain for reference but are not loaded by the multi-agent system.

## Related Files

- `backend/services/instruction_loader.py` - XML file loading utilities
- `backend/scripts/sync_all_xml_to_db.py` - REST API sync script
- `backend/scripts/sync_all_xml_to_db_direct.py` - Direct PostgreSQL sync script
- `backend/agents/base_agent.py` - Base agent class with instruction loading
- `backend/api/routes/agents.py` - Agent management endpoints

---

**Last Updated**: December 27, 2025
**System**: Multi-agent XML instructions with database versioning
