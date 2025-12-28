# Email Integration Plan

## Overview

This document outlines options for integrating email into the Thesis knowledge base, allowing emails to be searchable and available to agents.

**Target User:** charlie.fuller@contentful.com (Microsoft 365)

---

## Option A: Full Inbox Sync (Microsoft Graph API)

### How It Works

OAuth connection to Microsoft 365 that syncs emails directly from your mailbox into the knowledge base.

```
┌─────────────────┐     OAuth 2.0      ┌──────────────────┐
│  Thesis KB      │ ◄──────────────────► │  Microsoft 365   │
│  Connect Button │                      │  (Graph API)     │
└────────┬────────┘                      └────────┬─────────┘
         │                                        │
         ▼                                        ▼
┌─────────────────┐                     ┌──────────────────┐
│ Encrypted Token │                     │  Email Messages  │
│ Storage         │                     │  + Attachments   │
└────────┬────────┘                     └──────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  Background Sync Service (incremental via deltaLink)    │
└─────────────────────────────────────────────────────────┘
```

### Requirements

| Requirement | Details |
|-------------|---------|
| Azure AD App Registration | Created by you or Contentful IT |
| API Permissions | `Mail.Read`, `User.Read` (delegated) |
| IT Approval | May be required depending on Contentful policies |
| Redirect URIs | Dev + production callback URLs |

### Environment Variables

```bash
MICROSOFT_CLIENT_ID=<from Azure app registration>
MICROSOFT_CLIENT_SECRET=<from Azure app registration>
MICROSOFT_REDIRECT_URI=https://your-domain/api/microsoft/callback
MICROSOFT_TENANT_ID=common  # or Contentful's specific tenant ID
```

### Pros

- Automatic sync, no manual action required
- Can sync entire mailbox or filtered subsets
- Captures full email threads and metadata
- Attachments processed automatically

### Cons

- Requires Azure AD app registration
- May need IT approval at Contentful
- More complex implementation
- Privacy considerations (syncs emails automatically)

### Implementation Components

| Component | File | Effort |
|-----------|------|--------|
| Database migration | `/database/migrations/013_microsoft_email_integration.sql` | Small |
| OAuth routes | `/backend/api/routes/microsoft.py` | Medium |
| Sync service | `/backend/services/microsoft_email_sync.py` | Medium |
| Frontend UI | `/frontend/components/kb/MicrosoftEmailConnect.tsx` | Small |
| Filtering UI | `/frontend/components/kb/EmailSyncSettings.tsx` | Medium |

### Filtering Options

- By folder (Inbox, specific folders)
- By sender domain
- By date range
- By subject keywords
- Exclude certain senders

---

## Option B: Forward-to-Ingest (Webhook-based)

### How It Works

Set up a dedicated ingest email address. Forward emails you want in the KB to that address.

```
┌─────────────────────┐     Forward Rule      ┌──────────────────────┐
│  Your Outlook       │ ───────────────────►  │  ingest@thesis.app   │
│  charlie.fuller@... │  (manual or auto)     │  (dedicated address) │
└─────────────────────┘                       └──────────┬───────────┘
                                                         │
                                                         ▼
                                              ┌──────────────────────┐
                                              │  Inbound Email       │
                                              │  Webhook Service     │
                                              └──────────┬───────────┘
                                                         │
                                                         ▼
                                              ┌──────────────────────┐
                                              │  /api/email/ingest   │
                                              │  → Create KB doc     │
                                              │  → Process embeddings│
                                              └──────────────────────┘
```

### Requirements

| Requirement | Details |
|-------------|---------|
| Domain for ingest | e.g., `ingest.thesis-app.com` |
| Email service with inbound parsing | Resend, Mailgun, or SendGrid |
| DNS configuration | MX records pointing to email service |

### Email Service Options

| Service | Status in Codebase | Inbound Parsing | Free Tier |
|---------|-------------------|-----------------|-----------|
| Resend | Already configured | Yes (webhook) | 100 emails/day |
| Mailgun | Not configured | Yes (robust) | 5,000 emails/month |
| SendGrid | Not configured | Yes | 100 emails/day |

### Environment Variables

```bash
# If using Resend (already partially configured)
RESEND_API_KEY=re_xxxxx
RESEND_WEBHOOK_SECRET=whsec_xxxxx
EMAIL_INGEST_DOMAIN=ingest.thesis-app.com

# If using Mailgun
MAILGUN_API_KEY=key-xxxxx
MAILGUN_DOMAIN=ingest.thesis-app.com
MAILGUN_WEBHOOK_SIGNING_KEY=xxxxx
```

### Pros

- No Azure/IT approval needed
- User controls exactly what gets synced
- Simpler implementation
- Works with any email provider (Outlook, Gmail, etc.)
- Can be set up quickly

### Cons

- Requires manual forwarding (or setting up rules)
- Need to configure a domain for receiving emails
- Less automatic than full sync

### Implementation Components

| Component | File | Effort |
|-----------|------|--------|
| Database migration | `/database/migrations/013_email_ingest.sql` | Small |
| Webhook endpoint | `/backend/api/routes/email_ingest.py` | Small |
| Email parser | `/backend/services/email_parser.py` | Small |
| Attachment handler | `/backend/services/email_attachments.py` | Medium |

### User-Specific Ingest Addresses

Each user gets a unique ingest address:
- `ingest-{user_id}@thesis-app.com`
- Or: `{random_token}@ingest.thesis-app.com`

This ensures emails are attributed to the correct user's knowledge base.

---

## Option C: Hybrid Approach

Start with forward-to-ingest for immediate functionality, then add full sync later.

### Phase 1: Forward-to-Ingest
- Quick to implement
- No external approvals needed
- Validates the use case

### Phase 2: Full Microsoft Sync
- Add once email utility is proven
- Coordinate with IT for app registration
- Provides automatic sync for power users

---

## Comparison Matrix

| Aspect | Full Inbox Sync | Forward-to-Ingest |
|--------|-----------------|-------------------|
| Setup complexity | High | Low |
| IT approval needed | Likely | No |
| User effort | None (automatic) | Forward emails manually |
| Control over what syncs | Filter rules | Explicit per-email |
| Implementation time | 2-3 days | 1 day |
| External dependencies | Azure AD | Email service + domain |

---

## Data Model (Shared by Both Options)

### New Database Tables

```sql
-- Email-specific metadata for documents
CREATE TABLE email_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    message_id TEXT,                    -- Email Message-ID header
    thread_id TEXT,                     -- For grouping threads
    from_address TEXT NOT NULL,
    from_name TEXT,
    to_addresses JSONB,                 -- Array of recipients
    cc_addresses JSONB,
    subject TEXT,
    sent_at TIMESTAMPTZ,
    received_at TIMESTAMPTZ,
    has_attachments BOOLEAN DEFAULT FALSE,
    attachment_count INTEGER DEFAULT 0,
    is_reply BOOLEAN DEFAULT FALSE,
    in_reply_to TEXT,                   -- Parent message ID
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Track email sync tokens (for Option A)
CREATE TABLE microsoft_email_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    access_token_encrypted TEXT NOT NULL,
    refresh_token_encrypted TEXT NOT NULL,
    token_expires_at TIMESTAMPTZ NOT NULL,
    delta_link TEXT,                    -- For incremental sync
    last_sync_at TIMESTAMPTZ,
    sync_settings JSONB,                -- Folder filters, etc.
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Track ingest addresses (for Option B)
CREATE TABLE email_ingest_addresses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    ingest_address TEXT UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Document Integration

Emails become documents with:
- `source_platform = 'email'`
- `title` = Email subject
- `content` = Email body (plain text or HTML converted)
- Linked `email_documents` record for metadata
- Attachments as separate linked documents

---

## Next Steps

1. **Determine email setup** - Clarify Azure AD access and/or domain availability
2. **Choose approach** - Based on requirements and constraints
3. **Implement chosen option** - Following existing integration patterns
4. **Configure sync settings** - Folders, filters, retention

---

## Questions to Resolve

- [ ] Can you create Azure AD app registrations at Contentful?
- [ ] Do you have a domain available for ingest emails?
- [ ] Should email threads be grouped or individual messages?
- [ ] Should attachments become separate KB documents?
- [ ] How far back should initial sync go? (30 days, 90 days, all time)
- [ ] Any email addresses/domains to always exclude?
