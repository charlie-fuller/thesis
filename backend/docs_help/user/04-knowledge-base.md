# Knowledge Base

The Knowledge Base is where you make the agents smarter.

Generic AI advice is... fine. But AI advice grounded in *your* documents, *your* org's language, *your* specific situation? That's where the value is.

---

## What Goes in the Knowledge Base

**Documents you can upload:**
- PDFs
- Word documents (.docx)
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

## Uploading Documents

1. Go to **KB** in the navigation
2. Click **Upload Document** (or drag and drop)
3. Give it a title (optional - the system can extract one)
4. Wait for processing

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

**Google Drive:**
Connect your Drive and select folders to sync. Documents stay current as you update them.

**Notion:**
Link your Notion workspace. Pages sync automatically.

**Obsidian Vaults:**
If you use Obsidian, you can sync your vault to the KB:
- File watcher monitors changes (create/modify/delete)
- YAML frontmatter gets parsed (including `thesis-agents` for manual tagging)
- `[[wikilinks]]` convert to standard markdown links
- Incremental sync via content hash detection

**Supported file types in Obsidian sync:**
- Markdown files (.md)
- PDFs (.pdf) - with OCR fallback for image-based PDFs
- Word documents (.docx)
- Excel spreadsheets (.xlsx)
- PowerPoint presentations (.pptx)

**Real-time sync progress:**
When syncing, you'll see a progress bar showing:
- Percentage complete
- Current file being processed
- Total file count

**Folder view:**
In the KB, switch to "Obsidian" view to see your vault's folder structure as a navigable tree. Click folders to expand/collapse.

**Auto-classification:**
Documents are automatically classified by type during sync:
- Meeting transcripts (including Granola format: "Person1 __ Person2.md")
- Meeting notes
- Reports and analysis
- Instructions and guides
- Presentations and spreadsheets

This enables smarter search - when you ask about "recent meetings," the system filters to transcript and notes types automatically.

CLI watcher: `python -m scripts.obsidian_watcher --user-id <uuid>`

---

## Managing Documents

In the KB view, you can:

**Search and filter:**
- Search by document name
- Filter by source (Direct Upload, Google Drive, Notion)

**View document details:**
- Click a document to see its info
- See which agents it's tagged for
- View processing status

**Edit agent visibility:**
- Change which agents can see a document
- Make documents global (all agents) or restricted (specific agents)

**Delete:**
- Remove documents you no longer need

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

## What's Not in the KB

Some things are stored elsewhere:
- **Stakeholders** → Intelligence page
- **Tasks** → Tasks page
- **Opportunities** → Opportunities page

The KB is specifically for reference documents and conversation history.

---

## What's Next?

- [Tasks](./05-tasks.md) - Kanban task management
- [Projects](./06-projects.md) - AI project pipeline
- [Chat Interface](./02-chat.md) - See KB context in action
