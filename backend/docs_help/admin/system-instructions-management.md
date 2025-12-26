# System Instructions Management

The System Instructions page allows administrators to manage, version, compare, and deploy Thesis's core AI behavior configuration. This is the master control center for how Thesis responds to users, including personality, capabilities, guardrails, and operating modes.

## Accessing System Instructions

Navigate to the admin area and click **System Instructions** in the sidebar. The page has four tabs:

1. **Active Version** - View the currently deployed system instructions
2. **Version History** - Browse and manage all instruction versions
3. **Upload New** - Create new versions by uploading instruction files
4. **Compare Versions** - Analyze differences between any two versions

## Understanding System Instructions

System instructions are the foundational text that defines Thesis's behavior. They include:

- **Core Philosophy** - Thesis's approach to learning design and ROI-driven training
- **Output Format** - How Thesis structures responses (visual-first, progressive disclosure)
- **Operating Modes** - Coach, Developer, and Analyst modes
- **Guardrails** - IP protection, professional integrity, and safety constraints
- **Tool Use** - Image generation, document handling, and technical capabilities

Changes to system instructions affect all new conversations. Existing conversations continue using the version they started with.

## Active Version Tab

The Active Version tab displays the currently deployed system instructions.

### Version Information

At the top, you'll see:
- **Version number** - Semantic version (e.g., 1.3)
- **Active indicator** - Green pulsing dot confirming this is the live version
- **Activation timestamp** - When this version was deployed

### Metadata Grid

Four cards showing:
- **File Size** - Size of the instruction file
- **Word Count** - Total words in the instructions
- **Characters** - Character count for reference
- **Activated** - Date and time of activation

### Version Notes

If notes were provided when this version was created, they appear here explaining what changed.

### Content

The full system instructions content is displayed in a scrollable code block. This is read-only; to make changes, upload a new version.

## Version History Tab

The Version History tab shows all system instruction versions ever created.

### Version Table

Each row displays:
- **Version** - Version number with "Active" badge if currently deployed
- **Status** - "active" (available) or "archived" (historical)
- **Size** - File size
- **Created** - Creation date and creator name
- **Notes** - Truncated version notes
- **Actions** - View, Activate, or Delete buttons

### Version Actions

#### View
Opens a modal with the complete version details including:
- Full metadata
- Conversation count (how many chats use this version)
- Complete instruction content

#### Activate
Deploys this version as the active system instructions:
1. Confirmation dialog appears
2. Current active version is deactivated
3. Selected version becomes active
4. System instruction caches are cleared
5. All new conversations will use this version

#### Delete
Permanently removes a version. Cannot delete:
- The currently active version
- Versions that are bound to existing conversations

Use **Archive** instead of delete for versions you want to hide but preserve.

## Upload New Tab

The Upload New tab lets you create new instruction versions.

### Version Number

Enter a semantic version number:
- Format: `X.Y` or `X.Y-suffix`
- Examples: `1.4`, `2.0`, `1.5-beta`
- Must be unique (cannot reuse existing version numbers)

### File Upload

Click or drag to upload your instruction file:
- Accepted formats: `.txt` or `.xml`
- Maximum size: 50MB
- Must be UTF-8 encoded

The file content appears in the preview panel on the right.

### Version Notes

Describe what changed in this version. Good notes include:
- Summary of changes
- Reason for the update
- Areas of the instructions affected

### Creating the Version

Click **Upload Version** to create:
1. File is validated and processed
2. Version is created with status "active" (available but not deployed)
3. You're redirected to Version History
4. New version appears but is NOT automatically activated

To deploy the new version, go to Version History and click **Activate**.

## Compare Versions Tab

The Compare Versions tab provides powerful tools for understanding differences between instruction versions.

### Selecting Versions

Use the two dropdowns to select:
- **Version A (Older)** - The baseline version
- **Version B (Newer)** - The version to compare against

Click **Generate Comparison** to analyze differences.

### Stats Summary

After comparison, a summary bar shows:
- Version numbers being compared
- Total additions (green)
- Total deletions (red)
- Total changes

### Three Collapsible Panels

#### AI Summary Panel

Generates a natural language analysis of changes using Claude:

Click **Generate AI Summary** to get:
- **Overview** - High-level summary of what changed
- **Key Changes** - Bullet points of significant modifications
- **Impact Assessment** - How changes affect Thesis's behavior
- **Recommendations** - Suggestions for testing or validation

This uses the Anthropic API to analyze the diff and provide actionable insights.

#### Line-by-Line Diff Panel

Technical comparison showing exact changes:
- **Green lines** (with +) - Additions in Version B
- **Red lines** (with -) - Deletions from Version A
- **Blue lines** (with @@) - Context markers showing location

Scroll through to see every line that changed.

#### Version Changelogs Panel

Displays changelog documentation files if they exist:
- Looks for files like `v1.1-changelog.md` or `v1.1-update-log.md`
- Shows changelogs for both compared versions
- "None" badge appears if no changelogs exist

Changelogs should be stored in `docs/system-instructions/` with naming convention:
- `v{version}-changelog.md`
- `v{version}-update-log.md`

## Version Binding

When a conversation starts, it captures and binds to the active system instruction version. This ensures:

- **Consistency** - Each conversation uses the same instructions throughout its lifetime
- **Auditability** - You can see which version was used for any conversation
- **Safe Updates** - Activating a new version doesn't affect existing conversations

The conversation count shown on each version indicates how many chats are using it.

## Best Practices

### Before Making Changes

1. **Export current version** - Download or copy the active instructions as backup
2. **Review in staging** - Test major changes in a development environment first
3. **Document changes** - Write clear version notes for future reference

### Version Numbering

Follow semantic versioning principles:
- **Major (X.0)** - Significant behavioral changes, new operating modes
- **Minor (1.X)** - New features, expanded capabilities
- **Patch (1.1-hotfix)** - Bug fixes, typo corrections

### Testing New Versions

After activating a new version:
1. Start a new conversation
2. Test each operating mode (Coach, Developer, Analyst)
3. Verify guardrails are working
4. Check image generation capabilities
5. Confirm expected personality and tone

### Rollback Procedure

If issues are discovered after activation:
1. Go to Version History
2. Find the previous known-good version
3. Click **Activate** on that version
4. New conversations will use the stable version

## Troubleshooting

### Upload Fails

- Verify file is `.txt` or `.xml` format
- Check file is under 50MB
- Ensure file is UTF-8 encoded
- Confirm version number format is valid

### Version Not Activating

- Check you have admin permissions
- Ensure no other activation is in progress
- Refresh page and try again
- Check backend logs for errors

### Compare Not Working

- Verify both versions have content
- Ensure you selected two different versions
- Check network connection
- Try refreshing the page

### AI Summary Not Generating

- Verify ANTHROPIC_API_KEY is configured in environment
- Check API rate limits
- Try again after a moment
- Falls back to diff-only view if API unavailable

## Security Considerations

System instructions are sensitive configuration:

- **Access Control** - Only admins can view or modify instructions
- **Audit Trail** - All changes are logged with user and timestamp
- **No Deletion of Active** - Cannot delete the currently active version
- **Conversation Binding** - Historical versions preserved for audit
