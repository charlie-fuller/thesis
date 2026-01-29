# Document Management

Beyond what users can do in the Knowledge Base, admins have additional capabilities for managing documents across the system.

---

## Viewing All Documents

Access the admin document view at `/admin/documents`.

You'll see:
- All documents across all users
- Classification status and confidence scores
- Upload source (manual, Google Drive, local vault, etc.)
- Processing status

Filter by:
- User
- Classification status
- Agent relevance
- Date range
- Source type

---

## Classification Review

Documents are auto-classified by relevance to agents. The system uses confidence thresholds:

| Confidence | Action |
|------------|--------|
| > 80% | Auto-tagged, no review needed |
| 50-80% | Flagged for admin review |
| < 50% | Not tagged, may need manual classification |

**To review pending classifications:**

1. Go to `/admin/documents?status=pending`
2. Click a document to see suggested classifications
3. Accept or reject each suggestion
4. Add manual tags if the system missed something

---

## Bulk Tagging

For batch operations on multiple documents:

1. Select documents using checkboxes
2. Click **Bulk Actions**
3. Choose **Add Tags** or **Remove Tags**
4. Select the agent tags to apply
5. Confirm

Useful for:
- Retroactively tagging documents after new agent additions
- Cleaning up misclassifications
- Applying project-specific tags

---

## Managing Pending Classifications

The pending queue shows documents waiting for human review.

For each pending item:
- **Document preview** - see content excerpt
- **Suggested tags** - what the classifier thinks
- **Confidence scores** - per-tag confidence
- **Actions** - Approve, Reject, Edit

**Approve** accepts the suggested classification.
**Reject** removes the suggestion and optionally adds correct tags.
**Edit** opens the full classification editor.

---

## Document Deletion

Deleting documents requires confirmation due to cascading effects:

**What gets deleted:**
- The document itself
- All embeddings (vector store entries)
- Classification records
- References in conversation history

**What doesn't get deleted:**
- Extracted insights (they become orphaned but persist)
- Tasks/projects created from the document

**To delete:**
1. Select document(s)
2. Click **Delete**
3. Review the impact summary
4. Type "DELETE" to confirm

Bulk deletion follows the same confirmation flow.

---

## Reprocessing Documents

If embeddings or classifications seem wrong, you can reprocess:

1. Select the document
2. Click **Reprocess**
3. Choose what to regenerate:
   - Embeddings only
   - Classification only
   - Full reprocess (both)

Reprocessing is queued - large documents may take a few minutes.

---

## Source-Specific Management

### Manual Uploads
Standard management - can delete, reclassify, reprocess.

### Google Drive Synced
- Deletion removes local copy; doesn't affect Drive
- Re-sync pulls fresh content
- Classification persists across re-syncs

### Local Vault
- Files sync bidirectionally (configurable)
- Deletions can optionally propagate back to vault
- Check sync status at `/admin/integrations/vault`

---

## Monitoring Document Health

The admin dashboard shows document system health:

- **Processing queue depth** - how many documents awaiting processing
- **Classification coverage** - % of documents with tags
- **Embedding freshness** - when vectors were last updated
- **Storage usage** - total document storage consumed

Alerts trigger if:
- Processing queue exceeds threshold
- Classification coverage drops below 80%
- Embedding jobs fail repeatedly

---

## What's Next?

- [Help System](./04-help-system.md) - Managing help documentation
- [Troubleshooting](./05-troubleshooting.md) - Common issues and solutions
