# Google Drive OAuth Setup Guide

## Current Issue: 400 Error from Google

The "400. That's an error. The server cannot process the request because it is malformed" error typically means:

1. **Redirect URI mismatch** - The redirect URI in your code doesn't match what's configured in Google Cloud Console
2. **Missing environment variables** - `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, or `GOOGLE_REDIRECT_URI` not set
3. **Unauthorized redirect URI** - The redirect URI needs to be added to your Google Cloud Console OAuth credentials

## Required Environment Variables

Set these in your Railway environment:

```bash
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=https://thesis-production.up.railway.app/api/google-drive/callback
```

## Google Cloud Console Setup

1. **Go to Google Cloud Console**: https://console.cloud.google.com/
2. **Select your project** (or create a new one)
3. **Enable Google Drive API**:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Drive API"
   - Click "Enable"

4. **Create OAuth 2.0 Credentials**:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Application type: "Web application"
   - Name: "Thesis Production"

5. **Configure Authorized Redirect URIs**:
   Add these exact URIs (case-sensitive):
   ```
   https://thesis-production.up.railway.app/api/google-drive/callback
   http://localhost:8000/api/google-drive/callback  (for local testing)
   ```

6. **Configure OAuth Consent Screen**:
   - Go to "APIs & Services" > "OAuth consent screen"
   - User Type: External (for testing) or Internal (if using Google Workspace)
   - Add required info:
     - App name: "Thesis"
     - User support email: your-email@example.com
     - Developer contact: your-email@example.com
   - Scopes: Add `https://www.googleapis.com/auth/drive.readonly`
   - Test users: Add your email address for testing

## Verify Setup

After configuring, check that:

1. `GOOGLE_CLIENT_ID` is set in Railway environment
2. `GOOGLE_CLIENT_SECRET` is set in Railway environment
3. `GOOGLE_REDIRECT_URI` is set to `https://thesis-production.up.railway.app/api/google-drive/callback`
4. The redirect URI in Google Cloud Console **exactly matches** the environment variable
5. OAuth consent screen is configured and published (or in testing mode with your email added)

## Common Issues

### Issue: "redirect_uri_mismatch"
**Solution**: Ensure the redirect URI in Railway env vars exactly matches what's in Google Cloud Console (including https://, trailing slashes, etc.)

### Issue: "access_denied"
**Solution**: Add your email to test users in OAuth consent screen (if app is in testing mode)

### Issue: "invalid_client"
**Solution**: Double-check `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are correctly copied from Google Cloud Console

## Testing

After setup, restart your Railway app and try connecting Google Drive again. The OAuth flow should:
1. Redirect to Google's authorization page
2. Ask you to grant permissions
3. Redirect back to `/api/google-drive/callback`
4. Store encrypted tokens in database
5. Redirect to `/documents?google_drive_connected=true`
