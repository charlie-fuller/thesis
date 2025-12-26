# Help Documentation Directory

This is where you'll add your platform's help documentation as markdown files.

## Quick Start

1. **Create your first help document**:
   ```bash
   mkdir -p admin user
   echo "# Getting Started\n\nWelcome to our platform!" > user/getting-started.md
   ```

2. **Index your documentation**:
   ```bash
   python ../../../backend/scripts/index_help_docs.py
   ```

3. **Test in help chat**:
   - Open your app
   - Ask: "How do I get started?"
   - Should see response based on your new doc

## Directory Structure

Organize docs by user role:

```
help/
├── admin/           # Admin-only documentation
│   ├── getting-started.md
│   ├── user-management.md
│   ├── configuration.md
│   └── troubleshooting.md
├── user/            # General user documentation
│   ├── getting-started.md
│   ├── features.md
│   ├── billing.md
│   └── faq.md
└── system/          # Technical/system documentation
    ├── architecture.md
    └── api-reference.md
```

## Markdown File Format

### Basic Structure

```markdown
# Document Title

Introduction paragraph...

## Section 1

Content for section 1...

### Subsection 1.1

More detailed content...

## Section 2

Another major section...
```

### With Frontmatter (Optional)

```markdown
---
category: user
roles: [user, admin]
author: Your Name
updated: 2025-01-15
---

# Document Title

Your content here...
```

## Writing Guidelines

### 1. Use Clear Headings

Headings create searchable sections:

```markdown
# Main Title (H1) - One per document

## Major Section (H2) - Main topics

### Subsection (H3) - Specific details

#### Minor Point (H4) - Fine details
```

### 2. Be Concise

Users ask specific questions - give direct answers:

**Good**:
```markdown
## Resetting Your Password

1. Click "Forgot Password" on the login page
2. Enter your email address
3. Check your email for a reset link
4. Click the link and create a new password
```

**Bad**:
```markdown
## Password Management and Account Security

Passwords are an important part of account security. Our platform
uses industry-standard encryption and hashing algorithms to ensure
that your password is stored securely. In the event that you need
to reset your password, we provide a convenient self-service option...
```

### 3. Use Examples

Include code snippets and examples:

```markdown
## Making an API Call

Use the following format:

\`\`\`bash
curl -X POST https://api.example.com/v1/users \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"name": "John Doe"}'
\`\`\`
```

### 4. Link Related Topics

Help users find related information:

```markdown
## Next Steps

- Learn about [User Management](./user-management.md)
- See [Billing](./billing.md) for pricing information
- Check our [FAQ](./faq.md) for common questions
```

### 5. Include Troubleshooting

Add common issues and solutions:

```markdown
## Troubleshooting

### Error: "Authentication Failed"

**Cause**: Invalid or expired API token

**Solution**:
1. Go to Settings → API Keys
2. Generate a new API key
3. Update your application with the new key
```

## Role-Based Access

Documents are automatically assigned role access based on directory:

| Directory | Accessible By |
|-----------|---------------|
| `admin/` | admin, superadmin, owner |
| `user/` | user, admin, superadmin, owner |
| `system/` | admin, superadmin |

To customize, edit `ROLE_ACCESS_MAP` in `backend/scripts/index_help_docs.py`.

Or use frontmatter:

```markdown
---
roles: [manager, admin]
---

# Manager Documentation

This is only visible to managers and admins.
```

## Best Practices

### Do's

- **Use descriptive titles**: "How to Reset Your Password" not "Passwords"
- **Write in second person**: "You can reset..." not "Users can reset..."
- **Use numbered lists for procedures**: Step-by-step instructions
- **Use bullet lists for features**: Non-sequential items
- **Include screenshots**: Use markdown image syntax
- **Update regularly**: Keep docs current with product changes
- **Test your docs**: Ask the help chat to verify answers are correct

### Don'ts

- **Don't write walls of text**: Break into sections with headings
- **Don't assume knowledge**: Define technical terms
- **Don't duplicate content**: Link to canonical source instead
- **Don't leave outdated info**: Remove or update old content
- **Don't use jargon**: Write for your audience's level

## Content Types

### Getting Started Guide

```markdown
# Getting Started with [Platform]

Welcome! This guide will help you get up and running quickly.

## Creating Your First Project

1. Click "New Project" in the dashboard
2. Enter a project name
3. Choose your project type
4. Click "Create"

## Next Steps

- Explore [Features](./features.md)
- Invite [Team Members](./team-management.md)
- Set up [Integrations](./integrations.md)
```

### FAQ

```markdown
# Frequently Asked Questions

## Account Management

### How do I change my email address?

Go to Settings → Profile → Update your email address.

### Can I have multiple accounts?

Yes, you can create separate accounts with different email addresses.

## Billing

### What payment methods do you accept?

We accept credit cards, debit cards, and PayPal.
```

### Troubleshooting Guide

```markdown
# Troubleshooting Common Issues

## Login Problems

### I forgot my password

1. Click "Forgot Password" on login page
2. Enter your email
3. Check email for reset link
4. Create new password

### Account is locked

Contact support at support@example.com with your account email.
```

### API Reference

```markdown
# API Reference

## Authentication

All API requests require authentication via Bearer token:

\`\`\`bash
Authorization: Bearer YOUR_API_TOKEN
\`\`\`

## Endpoints

### GET /api/users

Retrieve list of users.

**Parameters**:
- `page` (integer): Page number
- `limit` (integer): Results per page

**Response**:
\`\`\`json
{
  "users": [...],
  "total": 100,
  "page": 1
}
\`\`\`
```

## Images and Assets

You can include images:

```markdown
![Dashboard Screenshot](./images/dashboard.png)
```

Store images in `docs/help/images/` or use absolute URLs:

```markdown
![Logo](https://example.com/logo.png)
```

## Indexing Process

When you add or update files:

1. **Automatic** (if GitHub Actions configured):
   - Push changes to main branch
   - Workflow triggers reindex
   - Updates available in ~1 minute

2. **Manual**:
   ```bash
   python backend/scripts/index_help_docs.py
   ```

The indexer:
- Discovers all `.md` files recursively
- Extracts title, category, role access
- Splits into chunks by headings
- Generates embeddings for semantic search
- Stores in database

## Testing Your Documentation

After indexing, test in help chat:

1. Ask questions your docs answer
2. Verify correct information is returned
3. Check source citations are correct
4. Test role-based access (different user roles)

## Maintenance

### Regular Updates

- Review docs quarterly
- Update when product changes
- Remove deprecated features
- Add new feature documentation

### Monitor Usage

Check which docs are most helpful:

```sql
-- Most referenced documents
SELECT
  d.title,
  COUNT(*) as reference_count
FROM help_messages m
CROSS JOIN LATERAL jsonb_array_elements(m.sources) as source
JOIN help_documents d ON d.id = (source->>'document_id')::uuid
WHERE m.role = 'assistant'
GROUP BY d.title
ORDER BY reference_count DESC;
```

### Improve Based on Feedback

Monitor thumbs down feedback to find gaps:

```sql
-- Questions with negative feedback
SELECT
  m.content,
  m.feedback,
  m.feedback_timestamp
FROM help_messages m
WHERE m.feedback = -1
ORDER BY m.feedback_timestamp DESC;
```

## Example Content

See the main platform's `docs/help/` directory for real examples of:
- Admin guides
- User guides
- System documentation
- Troubleshooting guides

Copy and adapt them for your platform's needs.

## Need Help?

- See [INTEGRATION.md](../INTEGRATION.md) for setup instructions
- See [CONFIGURATION.md](../CONFIGURATION.md) for configuration options
- See [CUSTOMIZATION.md](../CUSTOMIZATION.md) for advanced features

Start writing your help docs now - just create `.md` files and run the indexer!
