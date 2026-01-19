# User Management

Managing who has access to Thesis and what they can do.

---

## User Roles

Thesis uses Supabase Auth with role-based access:

**Admin:**
- Full access to all features
- Can manage agents and instructions
- Can view all user data
- Access to admin dashboard

**User:**
- Standard access to platform features
- Own conversations and documents
- Can't access admin areas

---

## Viewing Users

Admin dashboard shows:
- All registered users
- Role assignments
- Last activity
- Account status

---

## Managing Access

**Changing roles:**
Update the user's role in Supabase or through admin interface (if configured).

**Deactivating users:**
Disable the account in Supabase Auth. They'll be unable to log in but data is preserved.

**Deleting users:**
Remove from Supabase Auth. Consider data retention policies first.

---

## Authentication

Authentication flows through Supabase:
- Email/password login
- Password reset
- Session management

JWT tokens handle API authorization. Tokens expire; users re-authenticate automatically in most cases.

---

## Row-Level Security

Supabase RLS policies enforce data isolation:
- Users see only their own conversations
- Users see only their own documents
- Admins can access all data

This happens at the database level. Even if the application has bugs, RLS protects data.

---

## Common Tasks

**User can't log in:**
- Check account is active in Supabase
- Verify password (reset if needed)
- Check for session issues

**User needs admin access:**
- Update role to admin in Supabase
- User will see admin menu on next login

**Remove user access:**
- Deactivate in Supabase Auth
- Consider what happens to their data

---

## Best Practices

**Minimal admin access.** Only give admin role when necessary.

**Regular access review.** Periodically check who has what access.

**Clean up inactive users.** Accounts not used in 90+ days might need review.

---

## What's Next?

- [Admin Getting Started](./00-getting-started.md) - Overview
- [Agent Management](./01-agents.md) - Managing agent behavior
