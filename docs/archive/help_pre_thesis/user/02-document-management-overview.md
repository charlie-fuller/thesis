# Document Management Overview

Learn how documents power Thesis's contextual intelligence and how to organize your L&D materials effectively.

## Why Documents Matter

Thesis uses **RAG (Retrieval Augmented Generation)** to provide contextually relevant responses. When you upload documents, Thesis can:

- Reference your organization's terminology and style
- Align recommendations with existing training programs
- Provide guidance consistent with your approved methodologies
- Understand your industry-specific requirements

**The more relevant documents you upload, the more tailored Thesis's responses become.**

## How Document Search Works

When you ask Thesis a question, here's what happens:

1. Your question is converted into a semantic search query
2. Thesis searches through your uploaded documents for relevant passages
3. The most relevant content is included as context for the response
4. Thesis generates an answer that incorporates your organizational knowledge

This means Thesis doesn't just give generic advice - it gives advice grounded in *your* materials.

## Document Types

### Supported File Formats

| Format | Extensions | Best For |
|--------|------------|----------|
| **PDF** | .pdf | Training manuals, published guides, branded materials |
| **Word** | .docx, .doc | Draft content, facilitator guides, internal docs |
| **PowerPoint** | .pptx, .ppt | Presentation decks, visual training content |
| **Text** | .txt | Plain text notes, raw content |

### What to Upload

**Highly Recommended:**
- Existing training curricula and facilitator guides
- Company style guides and branding documents
- L&D strategy documents and frameworks
- Competency models and skill frameworks
- Sample assessments and evaluation rubrics
- Industry-specific compliance materials

**Good to Include:**
- Past project documentation
- Client-specific requirements or preferences
- Research papers relevant to your practice
- Templates you frequently use

### Core Documents vs. User Documents

Thesis distinguishes between two types of documents:

| Type | Description | Who Manages |
|------|-------------|-------------|
| **Core Documents** | Organization-wide materials available to all users | Administrators |
| **User Documents** | Personal uploads visible only to you | You |

Core documents ensure consistency across your team. Your personal uploads let you customize Thesis for your specific projects.

## Document Processing

When you upload a document, Thesis:

1. **Extracts text** from the file (including from PDFs and presentations)
2. **Chunks the content** into searchable passages
3. **Creates embeddings** - mathematical representations for semantic search
4. **Indexes everything** for fast retrieval

### Processing Status

Documents show their current state:

| Status | Meaning |
|--------|---------|
| **Processing** | Upload received, extraction in progress |
| **Completed** | Ready to use in conversations |
| **Failed** | Processing error - try re-uploading |

Most documents process within 30-60 seconds. Large files (50+ pages) may take longer.

## Storage and Quotas

Your account has a document storage allocation. You can view your current usage:

1. Go to **Documents** in the sidebar
2. Check the **Storage** indicator at the top

If you're approaching your limit:
- Remove outdated documents
- Consolidate similar files
- Contact your administrator for increased storage

## Document Organization Tips

### For Best Search Results

- **Use descriptive filenames** - "2024-Sales-Training-Curriculum.pdf" beats "document1.pdf"
- **Include metadata in your docs** - Titles, headers, and structured content help Thesis find relevant sections
- **Keep documents focused** - One topic per document improves retrieval accuracy
- **Update regularly** - Remove outdated content that might confuse recommendations

### For Team Consistency

- Coordinate with your administrator on core documents
- Avoid uploading duplicates of core documents
- Use consistent naming conventions across your team

## Integration Sources

Beyond direct uploads, Thesis can sync documents from:

- **Google Drive** - Connect folders for automatic syncing
- **Notion** - Import pages and databases

See [Uploading Documents](03-uploading-documents.md) for setup instructions.

## Privacy and Security

- Your documents are encrypted at rest and in transit
- User documents are private to your account
- Core documents are visible to all users in your organization
- Documents are only used to enhance *your* conversations

## Related Guides

- [Uploading Documents](03-uploading-documents.md) - Step-by-step upload instructions
- [Managing Documents](04-managing-documents.md) - Sync settings, updates, and deletion
- [Quick Start Guide](00-quick-start.md) - Get started fast
