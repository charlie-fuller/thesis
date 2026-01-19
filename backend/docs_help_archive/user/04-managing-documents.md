# Managing Documents

Learn how to maintain, update, and organize your document library for optimal performance.

## Viewing Your Documents

### Documents Page

Access your full document library:

1. Click **Documents** in the sidebar
2. View all your uploaded and synced documents
3. See processing status, file type, and upload date

### Document Information

Click any document to view details:

| Field | Description |
|-------|-------------|
| **Title** | Document name (from filename or metadata) |
| **Source** | Upload method (Direct, Google Drive, Notion) |
| **Status** | Processing state (Completed, Processing, Failed) |
| **Uploaded** | Date the document was added |
| **Size** | File size |
| **Chunks** | Number of searchable passages created |

## Sync Cadence Settings

For documents from Google Drive or Notion, configure how often they update.

### Available Options

| Cadence | Behavior | Best For |
|---------|----------|----------|
| **Manual** | Only syncs when you click "Sync Now" | Stable reference materials |
| **Daily** | Checks for updates every 24 hours | Active project documents |
| **Weekly** | Checks for updates every 7 days | Moderately changing content |
| **Monthly** | Checks for updates every 30 days | Archived or rarely updated docs |

### Changing Sync Cadence

1. Go to **Documents**
2. Find the integration source (Google Drive folder or Notion page)
3. Click the **settings icon** (gear)
4. Select your preferred cadence
5. Click **Save**

### Triggering Manual Sync

To immediately pull the latest version:

1. Go to **Documents**
2. Find the document or integration source
3. Click **Sync Now**
4. Wait for processing to complete

## Updating Documents

### Directly Uploaded Files

To update a directly uploaded document:

1. Delete the existing version
2. Upload the new version with the same filename

Thesis will reprocess and reindex the content.

### Google Drive Documents

For documents synced from Google Drive:

1. Update the file in Google Drive
2. Wait for the next scheduled sync, OR
3. Click **Sync Now** to pull changes immediately

The updated content replaces the previous version automatically.

### Notion Documents

For pages synced from Notion:

1. Edit the page in Notion
2. Wait for the next scheduled sync, OR
3. Click **Sync Now** to pull changes immediately

## Deleting Documents

### Removing Individual Documents

1. Go to **Documents**
2. Find the document you want to remove
3. Click the **delete icon** (trash can)
4. Confirm deletion

**What happens:**
- Document is removed from your library
- All chunks and embeddings are deleted
- Previous conversations that referenced this document still work, but new searches won't find it

### Disconnecting Integration Sources

To stop syncing from Google Drive or Notion:

1. Go to **Documents**
2. Find the integration source
3. Click **Disconnect** or the disconnect icon
4. Confirm the action

**What happens:**
- All documents from that source are removed
- The integration connection is revoked
- You'll need to reconnect and reauthorize to sync again

## Document Status Reference

### Processing States

| Status | Meaning | Action |
|--------|---------|--------|
| **Processing** | Being extracted and indexed | Wait 1-5 minutes |
| **Completed** | Ready for search | None needed |
| **Failed** | Processing error occurred | Try re-uploading |

### Troubleshooting Failed Documents

If a document shows "Failed":

1. **Check the file** - Open it locally to ensure it isn't corrupted
2. **Verify format** - Ensure it's a supported file type (PDF, DOCX, PPTX, TXT)
3. **Check size** - Confirm it's under the size limit
4. **Try conversion** - Save as a different format (e.g., Word to PDF)
5. **Re-upload** - Delete the failed document and upload again

## Storage Management

### Checking Your Usage

1. Go to **Documents**
2. View the **Storage** indicator at the top of the page

The indicator shows:
- Used storage
- Total allocation
- Percentage used

### Freeing Up Space

If you're running low on storage:

1. **Remove duplicates** - Check for multiple versions of the same document
2. **Delete outdated files** - Remove documents no longer relevant
3. **Archive large files** - Download and store locally, remove from Thesis
4. **Disconnect unused sources** - Remove integrations you no longer need

### Requesting More Storage

Contact your administrator if you need increased storage allocation.

## Organization Best Practices

### Naming Conventions

Use consistent, descriptive filenames:

**Good examples:**
- `2024-Q1-Sales-Training-Curriculum.pdf`
- `Customer-Service-Facilitator-Guide-v2.docx`
- `Leadership-Competency-Model.pdf`

**Avoid:**
- `doc1.pdf`
- `training.docx`
- `final_final_v3.pptx`

### Document Hygiene

Regular maintenance improves search quality:

- **Monthly review** - Remove outdated documents
- **Version control** - Keep only the current version
- **Consolidate** - Merge related small documents when possible

### Working with Core Documents

Core documents (managed by administrators) provide organization-wide context. If you need changes to core documents:

1. Contact your administrator
2. Explain what updates are needed
3. Provide the updated content if possible

Don't upload duplicates of core documents - this can create conflicting search results.

## Related Guides

- [Document Management Overview](02-document-management-overview.md) - How documents power Thesis
- [Uploading Documents](03-uploading-documents.md) - Getting documents into Thesis
- [FAQ and Troubleshooting](12-faq-and-troubleshooting.md) - Common issues and solutions
