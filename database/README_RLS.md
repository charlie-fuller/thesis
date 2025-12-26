# Row Level Security (RLS) Setup Guide

## Overview
This guide explains how to enable Row Level Security policies for the Thesis database.

## Quick Setup

1. **Open Supabase Dashboard**
   - Go to https://supabase.com/dashboard
   - Select your Thesis project
   - Navigate to SQL Editor

2. **Run the RLS Policies**
   - Open the `rls_policies.sql` file
   - Copy all the SQL content
   - Paste into the Supabase SQL Editor
   - Click "Run" or press `Cmd+Enter` / `Ctrl+Enter`

3. **Verify Policies**
   The SQL file includes verification queries at the bottom (commented out).
   Uncomment and run them to verify the policies are active.

## What These Policies Do

### Documents Table
- **Users**: Can only see documents from their client
- **Client Admins**: Can see and manage all documents for their client
- **Admins**: Can see and manage all documents

### Conversations Table
- **Users**: Can only see, create, and update their own conversations
- **Client Admins**: Can see all conversations for their client
- **Admins**: Can see all conversations

### Messages Table
- **Users**: Can only see and create messages in their own conversations
- **Client Admins**: Can see all messages for their client's conversations
- **Admins**: Can see all messages

## Security Benefits

1. **Database-Level Security**: Even if someone bypasses the API, they can't access unauthorized data
2. **Multi-Tenant Isolation**: Each client's data is completely isolated
3. **User Privacy**: Users can't see each other's conversations
4. **Admin Oversight**: Admins retain full visibility for support and monitoring

## Testing RLS

After applying the policies, test with different user roles:

1. **Test as Regular User**:
   - Log in as a regular user
   - Verify you can only see your own conversations
   - Try to access another user's conversation (should fail)

2. **Test as Client Admin**:
   - Log in as a client admin
   - Verify you can see all conversations for your client
   - Try to access another client's data (should fail)

3. **Test as Admin**:
   - Log in as an admin
   - Verify you can see all data across all clients

## Troubleshooting

### Issue: "Policy already exists" error
**Solution**: The SQL file includes `DROP POLICY IF EXISTS` statements. If you still get errors, manually drop the policies first.

### Issue: Users can't see their data
**Solution**:
1. Verify the user has a `client_id` in the `users` table
2. Check the user's role is set correctly
3. Verify RLS is enabled on the tables

### Issue: Admins can't access data
**Solution**:
1. Verify the admin user has `role = 'admin'` in the `users` table
2. Check the user is properly authenticated

## Next Steps

After applying RLS policies:
1. Test the chat interface with different user roles
2. Verify document uploads work correctly
3. Check conversation creation and message sending
4. Test admin dashboard access

## Additional Resources

- [Supabase RLS Documentation](https://supabase.com/docs/guides/auth/row-level-security)
- [PostgreSQL Row Security Policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
