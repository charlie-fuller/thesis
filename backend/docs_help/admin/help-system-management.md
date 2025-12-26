# Help System Management

The Help System is a RAG-powered (Retrieval-Augmented Generation) documentation system that provides contextual assistance to both users and administrators. This guide explains how to manage the help system, add new documentation, and monitor its effectiveness.

## Accessing the Help System Page

Navigate to the admin area and click **Help System** in the top navigation bar. This page has three tabs:

1. **System Status** - Overview of indexed documentation
2. **Documents** - Manage and reindex documentation
3. **Analytics** - Monitor help system usage and effectiveness

## System Status Tab

The System Status tab provides an at-a-glance view of your help documentation:

### Status Indicator

- **Green dot** - Documentation is indexed and operational
- **Blue dot (pulsing)** - Documentation is currently being indexed
- **Yellow dot** - Documentation needs indexing

### Documentation Counts

The status panel shows counts for both Admin Help and User Help:

- **Documents** - Number of markdown files indexed
- **Chunks** - Number of searchable text chunks created from those documents

Chunks are smaller sections of documents (split by headings and paragraphs) that enable precise semantic search. A single document typically produces 5-20 chunks depending on its length.

### How the Help System Works

The bottom of the Status tab explains the three-step process:

1. **Documentation** - Markdown files in `docs/help/` are parsed into searchable chunks
2. **Vector Search** - Each chunk is embedded using Voyage AI and stored in the database for fast semantic similarity search
3. **AI Responses** - User questions retrieve relevant chunks, which are passed to the LLM to generate accurate answers

## Documents Tab

The Documents tab is where you manage documentation indexing.

### Indexing Controls

Two buttons control documentation indexing:

#### Scan for New Documents

- **Use when:** Adding new documentation files
- **What it does:** Quickly scans for new markdown files and indexes only those that haven't been indexed yet
- **Speed:** Fast (only processes new files)

#### Reindex All Documents

- **Use when:** Updating existing documentation content or if search results seem stale
- **What it does:** Deletes all existing chunks and regenerates embeddings for every document
- **Speed:** Slower (processes everything)

### Progress Indicator

During indexing, a progress bar shows:
- Percentage complete
- Elapsed time
- Current file being processed

### Document Tables

Documents are displayed in two tables:

#### User Documentation

Documentation available to all users in the help chat. Stored in `docs/help/user/`.

#### Admin Documentation

Documentation available only to admins in the help chat. Stored in `docs/help/admin/`.

Each table shows:
- **Title** - Document title (from the first heading)
- **File Path** - Location relative to docs/help/
- **Chunks** - Number of searchable chunks created
- **Last Indexed** - When the document was last indexed
- **Actions** - Reindex button for individual documents

### Reindexing Individual Documents

Click the **Reindex** button next to any document to regenerate its chunks. Use this when you've updated a single document and don't need to reindex everything.

## Analytics Tab

The Analytics tab helps you understand how the help system is being used and identify areas for improvement.

### Period Selector

Choose the time period for analytics:
- Last 7 days
- Last 30 days
- Last 60 days
- Last 90 days

### Summary Statistics

Four key metrics at the top:

- **Questions Asked** - Total number of questions submitted to the help system
- **Avg Confidence** - Average similarity score of source documents (higher is better)
- **Low Confidence** - Number of responses with low similarity scores
- **Feedback Rate** - Percentage of responses that received user feedback

### Health Status Indicator

The colored dot on the Feedback Rate card indicates overall health:
- **Green** - System is healthy
- **Yellow** - Some attention needed
- **Red** - Critical issues to address

### User Feedback

Shows the breakdown of feedback received:
- **Helpful** (green) - Users marked response as helpful
- **Not Helpful** (red) - Users marked response as unhelpful
- **No Feedback** (gray) - No feedback provided

### Low Confidence Responses

This table shows responses where source documents had similarity scores below 75%. Each row includes:

- **Question** - The conversation title/question asked
- **Context** - Whether the question was asked in Admin or User help (purple badge for Admin, blue for User)
- **Confidence** - The average similarity score (color-coded)
- **Sources** - Number of source documents used
- **Feedback** - Whether the user rated the response
- **Date** - When the question was asked

Low confidence responses indicate potential gaps in your documentation. Review these to identify topics that need better coverage.

### Recent Questions

Shows the most recent questions asked to help you understand what users are looking for. Use this to prioritize new documentation.

### Export Conversations

Click the **Export Conversations** button to download all help conversations for the selected period as a JSON file. The export includes:
- Conversation metadata (user, title, help type)
- All messages with timestamps
- Source documents referenced
- User feedback

## Adding New Help Documentation

### Step 1: Create the Markdown File

Create a new `.md` file in the appropriate directory:
- `docs/help/user/` for user documentation
- `docs/help/admin/` for admin documentation

### Step 2: Structure Your Document

Follow these best practices:
- Start with a main heading (`# Title`)
- Use hierarchical headings (`##`, `###`) to organize content
- Keep sections focused and scannable
- Include practical examples where helpful

### Step 3: Deploy to Backend

For Railway deployments, copy your file to `backend/docs_help/`:
- User docs go in `backend/docs_help/user/`
- Admin docs go in `backend/docs_help/admin/`

### Step 4: Trigger Indexing

1. Go to the Help System page
2. Click the **Documents** tab
3. Click **Scan for New Documents**
4. Wait for indexing to complete

### Step 5: Verify

Check the document tables to confirm your new document appears with the expected chunk count.

## Continuous Improvement Process

The help system is designed for continuous improvement, using actual user questions as the primary driver for documentation evolution. This creates a closed-loop system where user needs directly shape documentation priorities.

### How Questions Drive Improvement

Every question asked of the help system is captured and analyzed:

1. **Question Capture** - Each user question is logged with metadata including user context (admin vs. user), timestamp, and the exact phrasing used

2. **Response Analysis** - The system records which documentation chunks were retrieved, their similarity scores, and whether they successfully answered the question

3. **Feedback Collection** - Users can rate responses as helpful or not helpful, providing direct signal on documentation quality

4. **Gap Identification** - Low confidence scores and negative feedback automatically surface topics where documentation is missing or inadequate

### Using Analytics for Documentation Decisions

The Analytics tab provides data-driven insights for prioritizing documentation work:

#### Identifying Missing Documentation

**Low Confidence Responses** reveal questions the system struggled to answer:
- Sort by confidence score to find the biggest gaps
- Look for patterns - multiple questions about the same topic indicate high-priority gaps
- Questions with "Not Helpful" feedback despite high confidence may indicate outdated or incorrect documentation

**Recent Questions** show what users are actively looking for:
- Recurring question themes suggest need for dedicated documentation
- Questions using unexpected terminology may indicate need for synonyms or alternate phrasings in docs
- Complex multi-part questions may need workflow-oriented guides

#### Measuring Documentation Effectiveness

Track these metrics over time:
- **Avg Confidence trending up** = Documentation is improving
- **Feedback Rate increasing** = Users are more engaged with help
- **Helpful percentage rising** = Documentation quality improving
- **Low Confidence count decreasing** = Gaps are being filled

### The Improvement Workflow

Follow this cycle to continuously improve documentation:

#### Weekly Review (15-30 minutes)

1. Open the **Analytics** tab
2. Review **Low Confidence Responses** from the past 7 days
3. Identify the top 2-3 topics that need attention
4. Note specific question phrasings users are using

#### Documentation Updates

For each identified gap:

1. **Determine the fix type:**
   - Missing topic → Create new documentation
   - Incomplete coverage → Expand existing document
   - Wrong terminology → Add synonyms and alternate phrasings
   - Outdated information → Update existing content

2. **Write with the actual questions in mind:**
   - Use the exact language users used in their questions
   - Structure content to directly answer the questions asked
   - Include variations of the question as section headers

3. **Reindex and verify:**
   - Reindex the updated document
   - Test by asking the original questions
   - Confirm improved confidence scores

#### Monthly Analysis (1 hour)

1. **Export Conversations** for the full month
2. Review for broader patterns:
   - Are certain user segments asking different questions?
   - Are there seasonal or project-phase patterns?
   - Which documentation topics get the most engagement?
3. Plan documentation roadmap for the next month

### Proactive Documentation from Application Changes

Beyond reactive improvement from user questions, the help system should be updated proactively when the application changes:

**After UI Changes:**
- Review affected help documents for accuracy
- Update screenshots, navigation paths, and terminology
- Reindex changed documents

**After Feature Releases:**
- Create documentation for new features before users ask
- Update related existing documentation
- Add to getting-started guides if appropriate

**After Bug Fixes:**
- Remove any workarounds that are no longer needed
- Update troubleshooting guides

### Measuring Long-Term Impact

Track these indicators to measure help system effectiveness over time:

| Metric | What It Indicates | Target Trend |
|--------|-------------------|--------------|
| Questions per user | Help system adoption | Stable or increasing |
| Avg confidence score | Documentation coverage | Increasing |
| Helpful feedback % | Documentation quality | Increasing |
| Repeat questions (same user) | First-answer effectiveness | Decreasing |
| Time to resolution | User efficiency | Decreasing |

### Closing the Loop

The continuous improvement process creates a virtuous cycle:

1. **Users ask questions** → Questions are captured
2. **Analytics reveal gaps** → Admins identify priorities
3. **Documentation improves** → Better answers, higher confidence
4. **Users get better help** → Higher satisfaction, more engagement
5. **More questions asked** → More data for improvement

This data-driven approach ensures documentation effort is always focused on actual user needs rather than assumptions about what users might want to know.

## Best Practices

### Writing Effective Documentation

- **Be specific** - Address concrete tasks and questions
- **Use clear headings** - These become chunk boundaries for better search
- **Include examples** - Practical examples improve search relevance
- **Update regularly** - Outdated documentation reduces user trust

### Monitoring Help System Health

- **Review low confidence responses weekly** - Identify documentation gaps
- **Check feedback trends** - Declining helpful ratings may indicate issues
- **Export and review conversations** - Understand user pain points
- **Reindex after updates** - Keep embeddings current with content

### When to Reindex All

Perform a full reindex when:
- Multiple documents have been updated
- Search results seem inaccurate
- After major documentation restructuring
- If embeddings appear corrupted (very low similarity scores)

## Troubleshooting

### Documents Not Appearing

1. Verify the file is in the correct directory (`docs/help/user/` or `docs/help/admin/`)
2. Check that the file has a `.md` extension
3. Ensure the file has content (not empty)
4. For Railway: verify the file is also in `backend/docs_help/`
5. Try clicking **Scan for New Documents**

### Low Search Quality

1. Check the Analytics tab for low confidence patterns
2. Ensure documents have clear, specific headings
3. Try **Reindex All Documents** to regenerate embeddings
4. Review document content for relevance to common questions

### Indexing Stuck or Failed

1. Check the status message for error details
2. Refresh the page and check indexing status
3. Try starting indexing again
4. Contact technical support if issues persist
