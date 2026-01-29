# Update Project Documentation

Update project documentation based on recent code changes. Reviews recent commits and ensures documentation reflects the current state of the codebase.

## Usage

```
/update-docs           # Update docs based on recent changes
/update-docs --full    # Full documentation audit
```

## Instructions

### Step 1: Review Recent Changes

Get commits from the last 7 days:

```bash
cd /Users/charlie.fuller/vaults/Contentful/GitHub/thesis
git log --oneline --since="7 days ago" | head -30
```

For each significant commit, note:
- Feature additions
- API changes
- New capabilities
- Configuration changes
- Database schema changes

### Step 2: Identify Documentation to Update

Check these files for needed updates:

| File | Purpose | Update When |
|------|---------|-------------|
| `docs/ARCHITECTURE.md` | Agent roster, capabilities, database schema | New agents, features, or schema changes |
| `docs/JANUARY_2026_RELEASE_NOTES.md` | Monthly release notes | Any user-facing changes |
| `docs/obsidian-sync-readme.md` | Obsidian sync documentation | Sync feature changes |
| `docs/deployment/DEPLOYMENT_GUIDE.md` | Deployment instructions | Infrastructure changes |

### Step 3: Read Current Documentation

Read each file that needs updates:

```bash
# Read architecture doc
cat docs/ARCHITECTURE.md

# Read release notes
cat docs/JANUARY_2026_RELEASE_NOTES.md
```

### Step 4: Make Updates

For each documentation file:

1. **Identify gaps** - What's missing or outdated?
2. **Draft updates** - Write clear, concise additions
3. **Preserve structure** - Match existing formatting
4. **Add to appropriate section** - Don't create new sections unless necessary

### Step 5: Update Release Notes

Add entries to `docs/JANUARY_2026_RELEASE_NOTES.md` for user-facing changes:

```markdown
### [Date] - [Category]

- **[Feature/Fix Name]**: Brief description of what changed and why it matters to users
```

Categories: Features, Fixes, Improvements, Infrastructure

### Step 6: Verify and Commit

After making updates:

```bash
# Check what changed
git diff docs/

# Commit documentation updates
git add docs/
git commit -m "docs: update documentation for recent changes

- [List specific doc updates]

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

## Documentation Standards

### Writing Style
- Use present tense ("The system classifies..." not "The system will classify...")
- Be concise - bullet points over paragraphs
- Include code examples where helpful
- Link to related documentation

### Architecture.md Structure
- Agent Roster: Table format with Agent, Name, Purpose
- Capabilities: Numbered list with bold feature names
- Database Schema: Table definitions with column descriptions

### Release Notes Format
```markdown
### January 29, 2026 - Knowledge Base

- **Document Auto-Classification**: Documents synced from Obsidian are now automatically classified by type (transcript, notes, report, etc.) enabling smarter search filtering
```

## Do NOT Update

- `CLAUDE.md` - Managed separately
- `docs/archive/*` - Historical reference only
- `docs/help/*` - Use `/update-help-docs` instead
