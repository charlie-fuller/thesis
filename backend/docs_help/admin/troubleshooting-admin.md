# Troubleshooting Guide for Administrators

This guide covers common issues administrators encounter and how to resolve them.

## User Issues

### User Not Receiving Invitation Email

**Symptoms:**
- New user reports no invitation email
- User checked spam/junk folder

**Solutions:**

1. **Verify email address**
   - Navigate to **Dashboard** → **Users**
   - Find the user and check email spelling

2. **Resend the invitation**
   - Click **Resend Invitation** in the **Actions** column
   - Ask user to check again in 5-10 minutes

3. **Check spam filters**
   - Ask user to check spam/junk folder
   - Add sender address to safe senders list

4. **Try alternate email**
   - If persistent, create new account with different email

### User Can't Log In

**Symptoms:**
- User reports login failures
- Password reset doesn't work

**Solutions:**

1. **Verify account exists**
   - Navigate to **Dashboard** → **Users**
   - Search for user by email

2. **Resend invitation**
   - If found, click **Resend Invitation**
   - New invitation provides fresh login link

3. **Check role and status**
   - Verify role is correct (**Admin** or **User**)
   - Ensure account wasn't disabled

4. **Browser issues**
   - Suggest clearing browser cache and cookies
   - Try incognito/private browsing mode
   - Try a different browser

### User Seeing Wrong Content

**Symptoms:**
- User reports unexpected responses from Thesis
- Content doesn't match their organization

**Solutions:**

1. **Check core document mappings**
   - Navigate to **Dashboard** → **Users** → **View Details**
   - Click **Manage Core Documents**
   - Verify correct documents are mapped

2. **Regenerate instructions**
   - After verifying mappings, click **Regenerate Instructions**
   - Have user start a new conversation

3. **Verify documents are processed**
   - Check **Dashboard** → **Documents**
   - Ensure relevant documents show **Processed** status

## Document Issues

### Document Stuck in Processing

**Symptoms:**
- Document shows **Processing** status for extended time (over 1 hour)

**Solutions:**

1. **Wait and refresh**
   - Large documents may take time
   - Refresh the **Documents** page

2. **Check document format**
   - Verify it's a supported format (PDF, DOCX, CSV, TXT)
   - Ensure file isn't password-protected

3. **Re-upload the document**
   - Delete the stuck document
   - Re-upload the file
   - Monitor processing status

### Document Shows Failed Status

**Symptoms:**
- Document status is **Failed**
- Document won't process

**Solutions:**

1. **Check file integrity**
   - Download and open the original file locally
   - Verify it opens correctly

2. **Address common causes:**
   - Password protection: Remove password and re-upload
   - Corrupted file: Get a fresh copy
   - Unsupported format: Convert to standard format
   - File too large: Split into smaller documents

3. **Re-upload corrected file**
   - Delete the failed document
   - Upload the fixed version
   - Monitor for successful processing

### Missing Document Chunks

**Symptoms:**
- **Chunks** shows 0 for a **Processed** document
- AI doesn't seem to reference the document

**Solutions:**

1. **Check document content**
   - Open file locally
   - Verify it contains actual text (not just images)

2. **For scanned documents**
   - Use OCR software to extract text
   - Re-upload the text-containing version

3. **For image-heavy PDFs**
   - Ensure text layer exists
   - Consider creating a text summary document

### Document Not Appearing in Lists

**Symptoms:**
- Recently uploaded document isn't visible

**Solutions:**

1. **Clear filters**
   - Reset all filters on the **Documents** page
   - Check **All Time** date filter
   - Set **All Types** and **All Statuses**

2. **Search by filename**
   - Use exact filename in search

3. **Verify upload completed**
   - Check if upload confirmation was received
   - Try uploading again if uncertain

## Theme Issues

### Logo Not Displaying

**Symptoms:**
- Uploaded logo doesn't appear in header
- Logo shows as broken image

**Solutions:**

1. **Check file format**
   - Supported: **PNG**, **JPEG**, **GIF**, **SVG**, **WebP**
   - Re-upload in supported format if needed

2. **Check file size**
   - Maximum: **2MB**
   - Compress or resize if too large

3. **Clear browser cache**
   - Force refresh the page (Ctrl+Shift+R or Cmd+Shift+R)
   - Try incognito mode

4. **Re-upload logo**
   - Navigate to **Dashboard** → **Theme** → **Top Nav Bar**
   - Click **Remove** to delete current logo
   - Click **Upload Logo** to add new file

### Colors Not Applying

**Symptoms:**
- Changed colors don't appear
- Theme looks inconsistent

**Solutions:**

1. **Save changes**
   - Click **Save Changes** button
   - Wait for confirmation message

2. **Check for unsaved changes warning**
   - Look for "You have unsaved changes" message
   - Save before leaving the page

3. **Clear browser cache**
   - Hard refresh the browser
   - Clear cached CSS files

4. **Check preset vs custom**
   - Applying a preset overrides custom colors
   - Re-apply custom changes if needed

### Theme Reset Problems

**Symptoms:**
- Can't reset to defaults
- Reset doesn't work properly

**Solutions:**

1. **Click Reset to Defaults**
   - Navigate to **Dashboard** → **Theme**
   - Click **Reset to Defaults**
   - Confirm the reset action

2. **Clear browser cache**
   - Force refresh after reset
   - Theme should return to defaults

3. **Re-apply desired settings**
   - Start fresh with a preset palette
   - Customize from there

## Conversation Issues

### Export Not Working

**Symptoms:**
- **Export JSON** or **Export TXT** buttons don't work
- Download doesn't start

**Solutions:**

1. **Check browser permissions**
   - Allow downloads from the site
   - Check download folder location

2. **Try different format**
   - If JSON fails, try TXT (or vice versa)

3. **Try from conversation list**
   - Navigate to **Dashboard** → **Conversations**
   - Use **Download** action from the list view

4. **Export via user detail**
   - Navigate to **Dashboard** → **Users** → **View Details**
   - Use **Chat History** tab → **Export Chat History (JSON)**

### Missing Conversations

**Symptoms:**
- Expected conversations don't appear
- Conversation count seems low

**Solutions:**

1. **Clear search filter**
   - Remove any search text
   - Look for "Clear search" link

2. **Check correct user**
   - Search by user name or email
   - Verify you're looking for the right person

3. **Verify conversations exist**
   - User may not have started any conversations
   - Check with user directly

## System Issues

### Dashboard Not Loading

**Symptoms:**
- Dashboard page shows loading indefinitely
- Stats don't appear

**Solutions:**

1. **Refresh the page**
   - Standard refresh (F5 or Cmd+R)
   - Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)

2. **Check network connection**
   - Verify internet connectivity
   - Try other pages to confirm

3. **Clear browser cache**
   - Clear all cached data for the site
   - Reload the page

4. **Try different browser**
   - Issue may be browser-specific
   - Test in Chrome, Firefox, Safari, or Edge

### Stats Showing Zero

**Symptoms:**
- **Quick Stats** show 0 for all metrics
- Numbers seem incorrect

**Solutions:**

1. **Wait for data to load**
   - Stats may take a moment to calculate
   - Refresh after a few seconds

2. **Verify data exists**
   - Check if there are actual users/documents/conversations
   - Zero may be accurate for new installations

3. **Check database connectivity**
   - If other features work, data should too
   - Contact technical support if persistent

### Slow Performance

**Symptoms:**
- Pages load slowly
- Actions take a long time

**Solutions:**

1. **Check network connection**
   - Slow internet affects all operations
   - Test other sites for comparison

2. **Clear browser cache**
   - Cached data can slow performance
   - Clear and reload

3. **Close unused tabs**
   - Browser memory affects performance
   - Close unnecessary tabs

4. **Try different browser**
   - Some browsers perform better than others

5. **Check during off-peak hours**
   - Server load may vary by time

## When to Escalate

### Contact Technical Support When:

- Issues persist after trying all solutions
- Multiple users report the same problem
- System-wide issues affect all functionality
- Data appears corrupted or inconsistent
- Security concerns arise

### Information to Provide:

1. Detailed description of the issue
2. Steps to reproduce the problem
3. Browser and operating system used
4. Screenshots or screen recordings
5. Time when issue first occurred
6. Any error messages displayed
7. What you've already tried

## Getting Technical Support

If you need additional help:

1. Document the issue thoroughly
2. Gather relevant screenshots
3. Note any error messages exactly
4. Contact your technical support team
5. Provide all collected information

### Quick Reference: Common Solutions

| Issue | First Try | Second Try |
|-------|-----------|------------|
| Can't login | Resend invitation | Different browser |
| Document stuck | Wait, then re-upload | Check file format |
| Theme not saving | Click Save Changes | Clear browser cache |
| Export failing | Try different format | Different browser |
| Page not loading | Refresh | Clear cache |
