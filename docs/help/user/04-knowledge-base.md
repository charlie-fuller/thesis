# Knowledge Base

The Knowledge Base is where you make the agents smarter.

Generic AI advice is... fine. But AI advice grounded in *your* documents, *your* org's language, *your* specific situation? That's where the value is.

---

## What Goes in the Knowledge Base

**Documents you can upload:**
- PDFs
- Word documents (.docx)
- RTF files (.rtf)
- Markdown files
- CSV and JSON data
- XML files
- Plain text

**The good stuff to upload:**
- Security policies and compliance docs (Guardian will reference them)
- Financial analyses and business cases (Capital uses these)
- Meeting transcripts (Oracle analyzes them)
- Strategy documents
- Technical architecture docs
- Change management materials
- Training materials and guides

Basically: anything that gives the agents context about your world.

---

## The Finder Layout

The KB uses a Finder-style layout with two panes:

**Left sidebar** - Folder tree showing your vault's folder structure
- Click a folder to see its documents in the content pane
- Click "All Documents" at the top to see everything
- Folders show document counts
- Expand/collapse folders by clicking the arrow

**Right content pane** - Documents in the selected folder
- Breadcrumb path at the top
- Column headers: Name, Source, Created (document date), Added (sync date)
- Documents sorted by Created date (original document date, not upload time)
- Source badges (Vault, Drive, Notion, Upload) on each document
- Click a document to open its detail modal
- Infinite scroll loads more documents as you scroll down

**Toolbar** (above the two panes):
- **Search** - Search across all documents by name
- **Source filter** - Filter by All Sources, Google Drive, Vault, or Uploads
- **Sync status** - Shows when last synced and pending count
- **Gear icon** - Opens sync settings modal (Vault, Drive, Notion, Uploads)

---

## Uploading Documents

1. Go to **KB** in the navigation
2. Click the **gear icon** to open Sync Settings
3. Go to the **Uploads** tab
4. Click **Upload Document** (or drag and drop)
5. Wait for processing

**What happens behind the scenes:**
1. Document gets chunked into pieces
2. Each chunk gets embedded (via Voyage AI)
3. The system auto-classifies which agents should know about it
4. Content becomes searchable in vector database

---

## Auto-Classification

This is one of my favorite features.

When you upload a document, the system analyzes it and tags it with relevant agents:

- Security policy? Tagged for Guardian
- Financial model? Tagged for Capital
- Interview transcript? Tagged for Oracle and maybe Sage

**How it works:**
1. Keyword scoring looks for domain-specific terms
2. If confidence is high (>80%), auto-tags it
3. If ambiguous (40-80%), uses Claude Haiku to classify
4. Ambiguous results get flagged for your review

**The review banner:** If documents need confirmation, you'll see a banner at the top of KB. Click through to confirm or adjust the agent tags.

---

## Agent-Filtered Retrieval

Here's why the tagging matters:

When Guardian answers a question, it prioritizes documents tagged for Guardian. Capital pulls from financial docs. Each agent sees the content most relevant to their domain first.

This isn't just filtering - it's making each agent a specialist in your specific context.

---

## Integrations

All integrations are configured through the **Sync Settings** modal (click the gear icon in the KB toolbar).

**Google Drive** (Sync Settings > Drive tab):
Connect your Drive and select folders to sync. Documents stay current as you update them.

**Notion** (Sync Settings > Notion tab):
Link your Notion workspace. Pages sync automatically.

**Local Vault** (Sync Settings > Vault tab):
Sync your local markdown vault to the KB:
- File watcher monitors changes (create/modify/delete)
- YAML frontmatter gets parsed (including `thesis-agents` for manual tagging)
- `[[wikilinks]]` convert to standard markdown links
- Incremental sync via content hash detection
- **Move/rename detection**: When you move or rename files in your vault, the sync preserves the existing document ID instead of creating duplicates. All tags, agent assignments, and initiative links are preserved.

**Supported file types in vault sync:**
- Markdown files (.md)
- PDFs (.pdf) - with OCR fallback for image-based PDFs
- Word documents (.docx)
- RTF files (.rtf)
- Excel spreadsheets (.xlsx)
- PowerPoint presentations (.pptx)

**Real-time sync progress:**
When syncing, you'll see a progress bar showing:
- Current phase (scanning, syncing changes, detecting moves, cleaning up, verifying)
- Phase-specific file count (e.g., "3 of 5 changes" not cumulative total)
- Percentage complete within the current phase
- Current file being processed

**Folder view:**
The KB's left sidebar always shows your vault's folder structure as a navigable tree. Click folders to browse, use the arrows to expand/collapse.

**Check for Updates** (Sync Settings > Vault tab):
Click the **Check for Updates** button to scan for files that have been modified since the last sync. This is useful when you've made changes outside the watcher.

**Full Resync** (Sync Settings > Vault tab):
Mirrors your vault using a 5-phase process. Changes are processed first for fast feedback, then moves are detected, deleted files are cleaned up, and unchanged files are verified. The folder tree stays visible throughout (sync states are never cleared). Progress shows phase-specific labels like "Scanning vault for changes...", "Syncing changes... 3 of 5", "Detecting moved files...", and "Verifying...". If no changes are found, the sync finishes quickly without verification.

**Linked document protection:**
During cleanup, documents linked to DISCO initiatives or projects are never deleted, even if their source file is missing from the vault. This prevents accidental loss of curated document associations. Unlinked orphan documents are cleaned up normally.

**Reverse vault sync:**
Documents created inside the app (e.g., saved from Discovery Agent chat conversations) are flagged for reverse sync. On the next sync cycle, `remote_vault_sync.py --reverse-sync` pulls these documents and writes them to your local Obsidian vault. This keeps your vault and KB in two-way sync -- vault files flow into the KB, and app-created documents flow back out.

**Pending files:**
If pending files are detected, the toolbar shows a pending count badge. Click the pending count in Sync Settings to see which files are queued for sync.

**Auto-classification:**
Documents are automatically classified by type during sync:
- Meeting transcripts (including formats like "Person1 __ Person2.md")
- Meeting notes
- Reports and analysis
- Instructions and guides
- Presentations and spreadsheets

This enables smarter search - when you ask about "recent meetings," the system filters to transcript and notes types automatically.

CLI watcher: `python -m scripts.vault_watcher --user-id <uuid>`

---

## Managing Documents

In the content pane, you can:

**Search and filter:**
- Search by document name using the toolbar search box
- Filter by source (All Sources, Google Drive, Vault, Uploads) using the dropdown
- Select a folder in the sidebar to browse by location

**View document details:**
- Click a document to open the info modal
- See which agents it's tagged for
- View processing status
- Edit tags, agent assignments, and sync cadence

**Edit agent visibility:**
- Change which agents can see a document
- Make documents global (all agents) or restricted (specific agents)

**Bulk delete:**
- Select multiple documents using checkboxes
- Use "Select all" in the header to select the entire page
- Click the bulk delete button (shows count of selected)
- Documents linked to DISCO initiatives show a warning before deletion

---

## Tag Manager

The **Tag Manager** tab provides a powerful document browser for managing tags across multiple documents at once.

**Layout:**
- Left panel (40%): Document list with checkboxes and preview buttons
- Right panel (60%): Toggle between **Manage Tags** and **Preview** views

**Features:**
- **Search and filter**: Search bar (60%) + tag filter (40%) at the top
- **Sort options**: Most Recent, Oldest First, Name A-Z, Name Z-A
- **Source filter**: All Sources, Vault, Google Drive, Notion, Uploaded
- **Multi-select**: Check multiple documents to apply tags in bulk

**Managing tags:**
1. Select documents using checkboxes
2. Switch to the **Manage Tags** panel
3. Click tags to add (green) or click the minus button to remove (red)
4. Create new tags using the input field
5. Click **Apply Tag Changes** to save

**Preview mode:**
Click the eye icon on any document to preview its content in the right panel.

---

## Conversations Tab

The KB also stores your conversation history. Switch to the **Conversations** tab to:
- View past conversations
- Search conversation content
- See which agents participated

---

## How Documents Improve Responses

Before:
> "Your AI governance framework should include policies around data access, model validation, and monitoring."

After (with your documents uploaded):
> "Based on your Security Policy v2.3, you already require SOC 2 compliance for third-party tools. Your AI governance framework should extend this to include model validation per your Vendor Assessment Template, and monitoring aligned with your existing SLA requirements in Section 4.2."

The agents cite sources. They reference your specific documents. They speak your org's language.

---

## Best Practices

**Upload early, upload often.** The more context agents have, the better.

**Use clear titles.** "Q1 2025 Security Review" beats "document.pdf"

**Review classifications.** The auto-tagger is good but not perfect. Check the review banner.

**Keep documents current.** If you update a policy, re-upload it or use an integration that syncs.

**Tag manually when needed.** Some documents are relevant to multiple agents. Use the edit function to add tags.

---

## KB and DISCO Integration

The Knowledge Base is the single source of truth for documents used in DISCO discoveries.

**Linking documents to initiatives:**
1. In a DISCO discovery, go to the **Documents** tab
2. Click **Link from KB**
3. Use the document browser to search or filter by tags
4. Select documents and click **Link Selected**

**The KB document browser features:**
- Search field (60% width) and tag filter (40% width)
- Preview panel shows document content
- Selected documents highlight in the list
- Multi-select for linking multiple documents at once

**Why this matters:**
- No document duplication between KB and DISCO
- Documents stay in sync automatically
- Delete from KB and it's removed from linked initiatives (with warning)

---

## What's Not in the KB

Some things are stored elsewhere:
- **Stakeholders** → Intelligence page
- **Tasks** → Tasks page
- **Projects** → Projects page

The KB is specifically for reference documents and conversation history.

---

## What's Next?

- [Tasks](./05-tasks.md) - Kanban task management
- [Projects](./06-projects.md) - AI project pipeline
- [Chat Interface](./02-chat.md) - See KB context in action
