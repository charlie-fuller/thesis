# Document Management

This guide explains how to view, manage, and troubleshoot documents across all clients in Thesis.

## Accessing Document Management

Navigate to **Dashboard** → **Documents** to open the **Documents** page.

The page subtitle reads "Manage all documents across clients" and provides comprehensive tools for document oversight.

## Viewing Documents

Documents are displayed in a table with the following columns:
- **Filename** - Name of the uploaded file
- **Client** - Associated client organization
- **Type** - File format (PDF, DOCX, CSV, TXT)
- **Size** - File size
- **Status** - Processing state
- **Chunks** - Number of text chunks created
- **Uploaded** - Upload timestamp
- **Actions** - Available operations

## Searching Documents

Use the search field with placeholder "Search by filename..." to filter documents.

The search matches against document filenames only. As you type, the list filters in real-time.

## Filtering Documents

### By File Type

Use the **All Types** dropdown to filter by format:
- **All Types** - Shows all documents
- **PDF** - PDF documents only
- **DOCX** - Word documents only
- **CSV** - Spreadsheet files only
- **TXT** - Plain text files only

### By Processing Status

Use the **All Statuses** dropdown to filter by state:
- **All Statuses** - Shows all documents
- **Processed** - Successfully processed and ready for use
- **Processing** - Currently being processed
- **Pending** - Queued for processing
- **Failed** - Processing encountered an error

### By Date Range

Use the **All Time** dropdown to filter by upload date:
- **All Time** - Shows all documents regardless of date
- **Last 7 Days** - Documents uploaded in the past week
- **Last 30 Days** - Documents uploaded in the past month
- **Last 90 Days** - Documents uploaded in the past quarter

## Adjusting Results Per Page

Control how many documents display at once using the results dropdown:
- **20 per page** - Default view
- **50 per page** - Medium density
- **100 per page** - High density for reviewing many documents

## Sorting Documents

Click on table headers to sort:
- **Filename** - Alphabetical order
- **Size** - By file size
- **Uploaded** - By upload date

Click the same header again to reverse the sort order.

## Pagination

When you have more documents than fit on one page:
- Click **Previous** to go back a page
- Click **Next** to advance to the next page
- The current position shows as "Page X of Y"

## Viewing Document Details

### Opening the Details Modal

Click on any document row or the view action to open the **Document Details** modal.

### Information Displayed

The modal shows:
- **Filename** - Full document name
- **Client** - Associated client organization
- **Type** - File format
- **Size** - File size in appropriate units
- **Status** - Current processing state
- **Chunks** - Number of text chunks generated
- **Uploaded** - Date and time of upload
- **Uploaded By** - User who uploaded the document

### Related Conversations

The **Related Conversations** section shows conversations where this document was referenced or used as context.

### Modal Actions

Three buttons are available:
- **Download** - Download the original file
- **Delete** - Remove the document (requires confirmation)
- **Close** - Close the modal

## Downloading Documents

### Individual Download

1. Click on a document to open **Document Details**
2. Click **Download**
3. The original file downloads to your device

### From the Table

Some views may show a download action directly in the table **Actions** column.

## Deleting Documents

### Deleting a Single Document

1. Click on the document to open **Document Details**
2. Click **Delete**
3. Confirm the deletion when prompted
4. The document and all its processed chunks are permanently removed

### Bulk Deletion

To delete multiple documents at once:

1. Select documents using checkboxes in the table
2. Click **Delete Selected**
3. Confirm the bulk deletion
4. All selected documents are permanently removed

**Warning**: Document deletion is permanent and cannot be undone. Associated chunks and references are also deleted.

## Understanding Document Processing

### What is Processing?

When a document is uploaded, Thesis:
1. Receives the file
2. Extracts text content
3. Splits text into chunks for AI retrieval
4. Generates embeddings for each chunk
5. Stores everything in the database

### Processing Statuses

#### Processed
- Document successfully processed
- Ready for AI to reference
- Shows chunk count

#### Processing
- Currently being analyzed
- Text extraction and chunking in progress
- Usually completes within a few minutes

#### Pending
- Queued for processing
- Waiting for processing resources
- Will process automatically

#### Failed
- Processing encountered an error
- May need manual intervention
- Check troubleshooting section

### Chunk Count

The **Chunks** column shows how many text segments were created:
- More chunks typically means a larger document
- Each chunk can be retrieved by the AI when relevant
- Zero chunks with **Processed** status may indicate an issue

## Troubleshooting Document Issues

### Document Stuck in Processing

If a document shows **Processing** for an extended period:

1. Wait at least 10-15 minutes for large documents
2. Check if other documents are processing (system may be busy)
3. If stuck for over an hour, the document may need re-upload

### Document Shows Failed Status

Common causes for **Failed** status:
- Corrupted file
- Password-protected document
- Unsupported format variation
- File too large

To resolve:
1. Download the original file
2. Open it locally to verify it's readable
3. Save as a standard format (e.g., regular PDF)
4. Delete the failed document
5. Re-upload the corrected file

### Zero Chunks After Processing

If **Status** is **Processed** but **Chunks** shows 0:
- Document may be image-only (no extractable text)
- File may be empty
- Encoding issues may have prevented extraction

To fix:
1. Ensure PDF contains actual text (not just images)
2. Use OCR software if document is scanned
3. Re-upload with proper text content

### Missing Document

If a document you expect isn't showing:
1. Clear any active filters
2. Search by filename
3. Check **All Time** date filter
4. Verify document was uploaded to correct client

## Document Best Practices

### Before Uploading

1. Ensure documents are not password-protected
2. Verify text is extractable (not just images)
3. Use standard file formats

### File Naming

1. Use descriptive filenames
2. Include version numbers if applicable
3. Avoid special characters that may cause issues

### Regular Maintenance

1. Review documents periodically for relevance
2. Remove outdated content
3. Check for failed processing and resolve issues

### Organization

1. Monitor document counts per client
2. Ensure important documents are processed successfully
3. Keep track of which documents are mapped to AI instructions

## Common Document Tasks

### Finding a Specific Document

1. **Dashboard** → **Documents**
2. Enter filename in search field
3. Or use filters to narrow results

### Checking Upload Success

1. Upload document through the normal interface
2. Navigate to **Dashboard** → **Documents**
3. Filter by **Last 7 Days** if needed
4. Verify **Status** shows **Processed**
5. Confirm **Chunks** count is greater than 0

### Cleaning Up Old Documents

1. **Dashboard** → **Documents**
2. Sort by **Uploaded** date (oldest first)
3. Review documents for relevance
4. Delete outdated items individually or in bulk
