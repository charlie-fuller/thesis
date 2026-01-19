# Uploading Documents

Step-by-step instructions for getting your documents into Thesis using direct upload, Google Drive, or Notion.

## Direct File Upload

The fastest way to add documents to Thesis.

### From the Chat Interface

1. Open any conversation or start a new one
2. Click the **paperclip icon** in the message input area
3. Select one or more files from your computer
4. Files begin uploading immediately
5. Wait for the "Processing complete" confirmation

### From the Documents Page

1. Click **Documents** in the sidebar
2. Click the **Upload** button
3. Select files from your computer, or drag and drop files onto the upload area
4. Monitor progress in the upload queue

### Supported Files

| Type | Extensions | Max Size |
|------|------------|----------|
| PDF | .pdf | 50 MB |
| Word | .docx, .doc | 50 MB |
| PowerPoint | .pptx, .ppt | 50 MB |
| Text | .txt | 10 MB |

### Upload Tips

- **Batch uploads** - Select multiple files at once to save time
- **Check processing** - Documents aren't searchable until processing completes
- **Use descriptive names** - Rename files before uploading for better organization

## Google Drive Integration

Sync documents directly from your Google Drive for automatic updates.

### Initial Setup

1. Go to **Documents** in the sidebar
2. Click **Connect Google Drive** or the Google Drive icon
3. Sign in with your Google account when prompted
4. Grant Thesis permission to access your Drive files

**Permissions requested:**
- View files and folders
- Access files you select

Thesis only accesses files you explicitly choose - not your entire Drive.

### Selecting Files and Folders

After connecting:

1. Click **Add from Google Drive**
2. Browse your Drive structure or use search
3. Select individual files or entire folders
4. Click **Add Selected**

**Folder behavior:**
- All supported files in the folder are imported
- Subfolders can be included or excluded
- New files added to synced folders are automatically imported

### Sync Settings

For each Google Drive source, you can configure:

| Setting | Options | Recommended |
|---------|---------|-------------|
| **Sync Cadence** | Manual, Daily, Weekly, Monthly | Daily for active projects |
| **Include Subfolders** | Yes/No | Yes for organized folder structures |

To change sync settings:
1. Go to **Documents**
2. Find the Google Drive source
3. Click the **gear icon** or **Settings**
4. Adjust options and save

### Manual Sync

To immediately sync changes from Google Drive:

1. Go to **Documents**
2. Find your Google Drive source
3. Click **Sync Now**

## Notion Integration

Import pages and databases from Notion.

### Initial Setup

1. Go to **Documents** in the sidebar
2. Click **Connect Notion** or the Notion icon
3. Sign in to your Notion workspace
4. Select which pages/databases to share with Thesis
5. Click **Allow Access**

### Selecting Pages

After connecting:

1. Click **Add from Notion**
2. Browse your accessible pages
3. Select pages or databases to import
4. Click **Add Selected**

**What gets imported:**
- Page content (text, headings, lists)
- Nested subpages (if selected)
- Database entries as individual documents

### Sync Settings

Configure how often Notion content updates:

| Setting | Options | Recommended |
|---------|---------|-------------|
| **Sync Cadence** | Manual, Daily, Weekly, Monthly | Weekly for reference materials |

### Notion Tips

- **Share specific pages** - Only pages you explicitly share in the OAuth flow are accessible
- **Structure matters** - Well-organized Notion pages with headers create better search results
- **Database views** - Each database entry becomes a separate searchable document

## Troubleshooting Uploads

### Document Stuck on "Processing"

If a document shows "Processing" for more than 5 minutes:

1. Check the file isn't corrupted by opening it locally
2. Verify the file size is within limits
3. Try re-uploading the file
4. If issues persist, try a different format (e.g., save Word as PDF)

### Upload Failed

Common causes and solutions:

| Issue | Solution |
|-------|----------|
| File too large | Compress or split the document |
| Unsupported format | Convert to PDF, DOCX, or PPTX |
| Corrupted file | Re-export from the original application |
| Connection timeout | Check your internet and try again |

### Google Drive Connection Issues

- **Can't see files** - Ensure you granted proper permissions; try reconnecting
- **Sync not working** - Check your sync cadence settings aren't set to "Manual"
- **Permission denied** - The file owner may have restricted access

### Notion Connection Issues

- **Pages missing** - You may need to share additional pages during Notion authorization
- **Content not updating** - Check sync cadence or trigger a manual sync
- **Formatting lost** - Complex Notion blocks may simplify during import

## Best Practices

### Organize Before Uploading

- Group related documents in folders
- Use consistent naming conventions
- Remove outdated versions before syncing

### Optimize for Search

- Ensure documents have clear titles and headings
- Avoid scanned PDFs without OCR (text must be selectable)
- Break very large documents into logical sections

### Maintain Your Library

- Regularly review and remove outdated documents
- Update synced sources when source files change
- Check processing status after major uploads

## Related Guides

- [Document Management Overview](02-document-management-overview.md) - Understand how documents work
- [Managing Documents](04-managing-documents.md) - Update, delete, and organize your library
