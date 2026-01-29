# Discovery Inbox

Your documents contain more than you realize - projects mentioned in passing, tasks buried in meeting notes, stakeholders referenced but never tracked. Discovery Inbox surfaces these automatically.

It scans your synced documents and extracts candidates: potential tasks, projects, and stakeholders that might be worth adding to your system.

---

## Where to Find It

1. Click **Dashboard** in the navigation
2. Click the **System Health** tab
3. Find the **Discovery Inbox** panel

The panel shows a count: `{N} items to review` when candidates are waiting.

---

## The Vault Panel

Above the inbox, you'll see your Vault status:

| State | What It Means |
|-------|---------------|
| `Syncing...` | Files are being pulled from your vault |
| `Analyzing X more...` | Document scanning in progress |
| `All caught up - no items to review` | Nothing pending |

The scan runs automatically after your vault syncs. You don't need to trigger it manually.

---

## Three Candidate Types

The inbox has three tabs:

### Tasks
Extracted action items with:
- Title and description
- Suggested assignee (if mentioned)
- Due date (if mentioned)
- Confidence badge: `high` (green) or `medium` (yellow)

### Projects
Potential initiatives with:
- Title and description
- Suggested department
- Scoring metrics (when determinable)

### Stakeholders
People mentioned in documents:
- Name and role
- Department
- Sentiment (if discernible from context)

---

## Reviewing Candidates

Use the navigation arrows to move through candidates. The counter shows `1 of 5` style progress.

For each candidate:
- **Preview** shows key details inline
- Click **Expand** to see full extracted information
- Source document is shown with its confidence badge

---

## Accept or Skip

Two actions for each candidate:

| Button | Color | What Happens |
|--------|-------|--------------|
| **Skip** | Red | Dismisses the candidate - won't be shown again |
| **Accept** | Amber | Opens a modal to create the task/project/stakeholder |

When you click **Accept**:
1. A creation modal appears with pre-filled data
2. Edit any fields that need adjustment
3. Confirm to create the item

---

## Duplicate Detection

When you accept a candidate, the system checks for potential duplicates.

If a match is found:
- You'll see "Potential duplicate detected"
- Option to link to the existing item instead
- Or create new if it's actually different

This prevents cluttering your data with redundant entries.

---

## Confidence Levels

Each extraction has a confidence badge:

| Badge | Meaning |
|-------|---------|
| `high` (green) | Strong signal - explicit mention, clear context |
| `medium` (yellow) | Reasonable inference - mentioned but context less clear |

Low-confidence extractions aren't surfaced to avoid noise.

---

## When Scanning Happens

The inbox populates after:
1. Files sync from your connected vault (Obsidian, Google Drive, etc.)
2. New documents are uploaded to the Knowledge Base
3. Meeting transcripts are processed by Oracle

During scanning, you'll see: `Analyzing documents for tasks, projects, stakeholders...`

---

## Candidate Expiration

Candidates don't last forever. Items you haven't reviewed expire after 2 weeks.

This keeps the inbox focused on recent, relevant extractions rather than accumulating stale suggestions.

---

## View All

Click **View All** to see candidates in a full-page view with:
- Filtering by type
- Bulk actions
- Source document links

Useful when you have many candidates to process.

---

## Tips for Better Extractions

1. **Upload meeting transcripts.** They're rich with action items and stakeholder mentions.

2. **Include context in documents.** The scanner needs enough context to extract accurately.

3. **Review regularly.** A quick daily scan prevents inbox buildup and keeps data fresh.

4. **Trust high confidence.** `high` confidence extractions are usually accurate. `medium` ones benefit from a closer look.

5. **Use the source link.** If an extraction seems off, check the source document to understand what triggered it.

---

## What's Next?

- [Tasks](./05-tasks.md) - Managing your task board
- [Projects](./06-projects.md) - The project pipeline
- [Stakeholder Intelligence](./07-stakeholders.md) - Tracking relationships
- [Knowledge Base](./04-knowledge-base.md) - Document management
