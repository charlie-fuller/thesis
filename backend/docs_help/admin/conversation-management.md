# Conversation Management

This guide explains how to view, search, export, and manage conversations across all users in Thesis.

## Accessing Conversation Management

Navigate to **Dashboard** → **Conversations** to open the **All Conversations** page.

The page subtitle reads "View and manage all conversations" and provides comprehensive oversight of user interactions.

## Conversation Summary Stats

At the bottom of the page, three summary cards display:
- **Total Conversations** - Number of all conversations
- **Total Messages** - Combined message count across all conversations
- **Active Users** - Number of unique users with conversations

## Viewing All Conversations

Conversations display in a table with the following columns:
- **Conversation** - Title and partial ID
- **User** - User name and email
- **Messages** - Number of messages in the conversation
- **Last Updated** - Date and time of last activity
- **Actions** - Available operations

## Searching Conversations

Use the **Search** field with placeholder "Search by title or user..." to filter conversations.

The search matches against:
- Conversation titles
- User names
- User email addresses

Results filter in real-time as you type.

### Clearing Search

When a search is active, the page shows how many results match. To clear:
- Delete the search text
- Or click the clear option if available

If no conversations match your search, you'll see: "No conversations match your search" with a **Clear search** link.

## Understanding Conversation Information

### Conversation Title

Each conversation has a title based on its content:
- Usually derived from the first message
- Helps identify the topic
- Displayed in the **Conversation** column

### Conversation ID

A unique identifier shown as a partial ID (first 8 characters followed by "...").

### User Information

The **User** column shows:
- User's display name
- User's email address

### Message Count

The **Messages** column shows the total number of messages:
- Includes both user and assistant messages
- Higher counts indicate longer conversations

### Last Updated

Shows when the conversation was last active:
- Date on the first line
- Time on the second line

## Viewing Individual Conversations

### Opening a Conversation

1. Find the conversation in the table
2. Click the **View icon** (eye icon) in the **Actions** column
3. The conversation detail page opens

### Conversation Detail View

The detail page shows:
- Full conversation title
- All messages in the thread
- Timestamps for each message

### Message Display

Messages are displayed with:
- **[USER]** label for user messages
- **[ASSISTANT]** label for Thesis's responses
- Alternating background colors for visual separation
- Timestamps for each message

### Conversation Metrics

The detail view may show:
- Total messages
- User message count
- Assistant response count
- First and last message timestamps

## Exporting Conversations

### Exporting All Conversations (Bulk Export)

To export the complete conversation history:

1. Navigate to **Dashboard** → **Conversations**
2. Click the **Export All** button in the top right corner
3. The **Export Conversations** modal opens with these options:

#### Date Range Filter (Optional)

- **Start Date** - Only include conversations from this date onward
- **End Date** - Only include conversations up to this date
- Leave both empty to export all conversations

#### Export Format

Choose between two formats:
- **JSON** - Machine-readable format with full metadata, suitable for data analysis or import
- **Text** - Human-readable format suitable for review or archival

4. Click **Export** to download the file
5. The file is named with the date range or "all" if no filter applied

### Export Single Conversation from List

1. Navigate to **Dashboard** → **Conversations**
2. Find the conversation
3. Click the **Download icon** (download arrow) in the **Actions** column
4. A JSON file downloads immediately

### Export from Conversation Detail

On the conversation detail page, two export options are available:
- **Export JSON** - Machine-readable format with full metadata
- **Export TXT** - Human-readable text format

### JSON Export Format

The JSON export includes:
- Conversation ID
- Conversation title
- Client name
- User information
- All messages with timestamps and roles
- Export metadata (date range, total counts)

### TXT Export Format

The TXT export provides:
- Conversation header with title, client, user, and date
- Each message labeled with role and timestamp
- Clear separator between conversations
- Easy-to-read format for reviewing offline

## Deleting Conversations

### Deleting a Single Conversation

1. Navigate to **Dashboard** → **Conversations**
2. Click the **View icon** (eye icon) to open the conversation
3. Click **Delete Conversation**
4. Confirm the deletion when prompted

**Warning**: Conversation deletion is permanent and cannot be undone. All messages in the conversation are permanently removed.

### When to Delete Conversations

Consider deleting conversations when:
- They contain sensitive information that should be removed
- Test or demo conversations clutter the list
- User has requested data removal

## Using Conversations for Quality Assurance

### Reviewing Conversation Quality

Regularly review conversations to:
- Ensure Thesis provides accurate information
- Identify common user questions
- Spot opportunities for improvement
- Verify responses align with organizational standards

### What to Look For

When reviewing conversations:
- Are responses accurate and helpful?
- Does Thesis cite appropriate sources?
- Are there patterns in user confusion?
- Could system instructions be improved?

### Taking Action on Findings

Based on conversation review:
- Update core document mappings if responses miss key content
- Regenerate system instructions if behavior needs adjustment
- Document common issues for training improvements
- Export notable conversations for further analysis

## Monitoring User Activity

### Identifying Active Users

The **Active Users** stat shows how many unique users have conversations.

### Finding Specific User Conversations

1. Use the search field
2. Enter the user's name or email
3. All their conversations appear in results

### Assessing User Engagement

Look at:
- Number of conversations per user
- Message counts (indicates depth of engagement)
- Recency of last activity

## Common Conversation Tasks

### Finding a Recent Conversation

1. **Dashboard** → **Conversations**
2. Sort by **Last Updated** (if available)
3. Recent conversations appear first

### Exporting All Conversations for a User

1. Navigate to **Dashboard** → **Users**
2. Click **View Details** for the user
3. Go to **Chat History** tab
4. Click **Export Chat History (JSON)**

This exports all conversations for that user at once.

### Exporting All Conversations for a Date Range

1. Navigate to **Dashboard** → **Conversations**
2. Click **Export All**
3. Set the **Start Date** and **End Date** to your desired range
4. Select your preferred format (JSON or Text)
5. Click **Export**

This is useful for periodic backups or compliance reporting.

### Reviewing Conversations by Topic

1. **Dashboard** → **Conversations**
2. Use search to find conversations mentioning specific topics
3. Open and review relevant conversations

### Identifying Issues

If users report problems:
1. Search for the user's conversations
2. Review recent interactions
3. Look for error patterns or unexpected responses
4. Document findings for troubleshooting

## Conversation Data Retention

### How Long Are Conversations Kept?

Conversations are retained indefinitely unless manually deleted.

### Privacy Considerations

When handling conversation data:
- Only access conversations when necessary for administration
- Export data securely and delete exports when no longer needed
- Follow organizational data handling policies
- Be aware that conversations may contain sensitive user information

## Best Practices

### Regular Reviews

1. Schedule periodic conversation reviews
2. Sample conversations across different users
3. Document patterns and issues
4. Share insights with relevant stakeholders

### Export Organization

1. Use meaningful filenames for exports
2. Store exports securely
3. Delete exports when no longer needed

### Issue Tracking

1. Note recurring problems
2. Track which users experience issues
3. Document resolution steps
4. Update help documentation as needed
