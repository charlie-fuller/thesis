# Discovery Inbox

Your documents contain more than you realize - projects mentioned in passing, tasks buried in meeting notes, stakeholders referenced but never tracked. Discovery Inbox surfaces these automatically.

It scans your synced documents and extracts candidates: potential tasks, projects, and stakeholders that might be worth adding to your system.

---

## Where to Find It

1. Click **Dashboard** in the navigation
2. The **Discovery Inbox** panel is on the **System Health** tab

The panel header shows a count: `{N} items to review` when candidates are waiting.

---

## Three Panels, One View

The inbox displays three vertical panels simultaneously:

### Tasks Panel
Extracted action items with:
- Title and description
- Team assignment (if mentioned)
- Source document reference

### Projects Panel
Potential initiatives with:
- Title and description
- ROI and Effort scores (when determinable)
- Source document reference

### Stakeholders Panel
People mentioned in documents:
- Name, role, and department
- Source document reference

Each panel shows one candidate at a time with navigation arrows to browse through items.

---

## Reviewing Candidates

Each panel has its own navigation. Use the `<` and `>` arrows to move through candidates in that category. The counter shows `1/5` style progress.

For each candidate:
- **Source document** shown at the top
- **Title and description** displayed inline
- **Type-specific metadata** (scores, role, team, etc.)

---

## Accept or Skip

Two actions for each candidate, shown as icon buttons:

| Button | Icon | What Happens |
|--------|------|--------------|
| **Skip** | X (red) | Dismisses the candidate - won't be shown again |
| **Accept** | Checkmark (green) | Creates the task/project/stakeholder |

When you click **Accept**, the item is created immediately and removed from the inbox.

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
1. Files sync from your connected sources (local vault, Google Drive, etc.)
2. New documents are uploaded to the Knowledge Base
3. Meeting transcripts are processed by Oracle

During scanning, you'll see: `Analyzing documents for tasks, projects, stakeholders...`

---

## Candidate Expiration

Candidates don't last forever. Items you haven't reviewed expire after 2 weeks.

This keeps the inbox focused on recent, relevant extractions rather than accumulating stale suggestions.

---

## Scanning Status

When documents are being analyzed, you'll see a status indicator:
`Analyzing X more...`

The scan runs automatically after your vault syncs. You don't need to trigger it manually.

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
