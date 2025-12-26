# Help System Automation

This directory contains automation for keeping help documentation up-to-date.

## GitHub Actions Workflow

### File: `workflows/reindex-help-docs.yml`

Automatically reindexes documentation when markdown files change in `docs/help/`.

### How It Works

1. **Trigger**: Fires when `.md` files in `docs/help/` are pushed to `main` branch
2. **Action**: Calls your backend webhook endpoint
3. **Backend**: Runs indexing script to update embeddings
4. **Result**: Help chat uses updated documentation immediately

### Setup

#### 1. Copy Workflow File

```bash
cp automation/workflows/reindex-help-docs.yml .github/workflows/
```

#### 2. Configure GitHub Secrets

Go to your repository: **Settings → Secrets and variables → Actions**

Add these secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `REINDEX_API_URL` | `https://your-api.com/api/help/index-docs-webhook` | Full webhook URL |
| `REINDEX_API_KEY` | Same as `HELP_REINDEX_API_KEY` in backend `.env` | Authentication token |

**Generate API Key:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Add this same value to:
- GitHub Secret: `REINDEX_API_KEY`
- Backend `.env`: `HELP_REINDEX_API_KEY`

#### 3. Test Workflow

Make a change to any help documentation:

```bash
# Edit a help document
echo "\n## New Section\n\nNew content" >> docs/help/user/getting-started.md

# Commit and push
git add docs/help/
git commit -m "docs: Update getting started guide"
git push origin main
```

#### 4. Verify Execution

1. Go to **Actions** tab in GitHub
2. Look for "Reindex Help Documentation" workflow
3. Click on the run to see logs
4. Should complete in ~30-60 seconds

Successful output:
```
Calling reindex webhook...
Response: 200 OK
{
  "status": "success",
  "documents_indexed": 8,
  "chunks_created": 42
}
```

## Manual Reindex Options

### Option 1: Via API (Requires Admin JWT)

```bash
curl -X POST https://your-api.com/api/help/index-docs?force=true \
  -H "Authorization: Bearer YOUR_ADMIN_JWT_TOKEN"
```

### Option 2: Via Webhook (Uses API Key)

```bash
curl -X POST https://your-api.com/api/help/index-docs-webhook \
  -H "Authorization: Bearer YOUR_REINDEX_API_KEY"
```

### Option 3: Run Script Directly

```bash
cd backend
python scripts/index_help_docs.py
```

## Workflow Customization

### Change Trigger Path

Edit workflow file to watch different directory:

```yaml
on:
  push:
    branches: [main]
    paths:
      - 'documentation/help/**/*.md'  # Custom path
```

### Add Slack Notification

```yaml
- name: Notify Slack
  if: success()
  run: |
    curl -X POST ${{ secrets.SLACK_WEBHOOK_URL }} \
      -H 'Content-Type: application/json' \
      -d '{"text":"Help docs reindexed successfully!"}'
```

### Run on Schedule (Nightly Reindex)

```yaml
on:
  schedule:
    - cron: '0 2 * * *'  # 2 AM daily
  push:
    branches: [main]
    paths:
      - 'docs/help/**/*.md'
```

### Add Quality Checks

```yaml
- name: Validate markdown
  run: |
    npm install -g markdownlint-cli
    markdownlint docs/help/**/*.md

- name: Check broken links
  run: |
    npm install -g markdown-link-check
    find docs/help -name "*.md" -exec markdown-link-check {} \;
```

## Rate Limiting

The webhook endpoint is rate-limited to **1 request per hour** to prevent abuse.

If workflow runs frequently (multiple commits to `docs/help/`), they may be rate-limited.

**Solutions:**

1. **Batch commits**: Combine doc changes into one commit
2. **Increase rate limit**: Edit `backend/api/routes/help_chat.py`:
   ```python
   @limiter.limit("5/hour")  # Increase from 1/hour to 5/hour
   ```
3. **Use manual reindex**: Run script directly when needed

## Monitoring

### View Workflow History

GitHub Actions → Reindex Help Documentation → All workflow runs

### Check Logs

Click on any workflow run → View job logs

### Common Errors

**401 Unauthorized**
- Check `REINDEX_API_KEY` secret matches backend env var
- Verify secret is set in repository settings

**404 Not Found**
- Check `REINDEX_API_URL` is correct
- Ensure backend is deployed and accessible

**429 Too Many Requests**
- Hit rate limit (1/hour)
- Wait 1 hour or manually run script

**500 Internal Server Error**
- Check backend logs for indexing script errors
- Verify `VOYAGE_API_KEY` is valid
- Ensure database connection is working

## Disable Auto-Reindex

If you don't want automatic reindexing:

1. Don't copy the workflow file, or
2. Delete it from `.github/workflows/`:
   ```bash
   rm .github/workflows/reindex-help-docs.yml
   ```

You can still manually reindex using the script.

## Security Notes

- Webhook uses Bearer token authentication
- API key should be kept secret (don't commit to code)
- Rotate API key periodically:
  ```bash
  # Generate new key
  python -c "import secrets; print(secrets.token_urlsafe(32))"

  # Update in:
  # 1. GitHub Secrets
  # 2. Backend .env
  # 3. Restart backend
  ```

## Alternative: Webhook from Other Sources

You can trigger reindex from anywhere, not just GitHub:

**From CI/CD (Jenkins, CircleCI, etc.)**:
```bash
curl -X POST $REINDEX_URL -H "Authorization: Bearer $API_KEY"
```

**From CMS** (when admin publishes new docs):
```javascript
await fetch(process.env.REINDEX_URL, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${process.env.API_KEY}`
  }
})
```

**From Cron Job**:
```bash
# Add to crontab for nightly reindex
0 2 * * * curl -X POST https://your-api.com/api/help/index-docs-webhook -H "Authorization: Bearer YOUR_KEY"
```

## Summary

- **Automatic**: Workflow triggers on doc changes
- **Manual**: Multiple options (API, webhook, script)
- **Secure**: Bearer token authentication
- **Rate-limited**: Prevents abuse
- **Customizable**: Easy to modify triggers and add steps
