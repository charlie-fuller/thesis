# Post-Deployment Verification Guide

##  Deployment Complete - Next Steps

Your AI-powered image generation feature has been deployed to production! Here's how to verify everything is working correctly.

---

##  Step 1: Access Your Production Site

1. Go to **https://thesis.vercel.app**
2. Log in with your account
3. You should be redirected to `/chat`

**Expected Result:** Chat interface loads normally

---

##  Step 2: Test Image Suggestion Flow

### Test Case 1: Proactive AI Suggestion

1. **Start a new conversation** (or use existing one)
2. **Ask a visual question:**
   ```
   How does photosynthesis work?
   ```
3. **Wait for Thesis's response**
4. **Look for the suggestion prompt** below Thesis's message:
   - Should show:  lightbulb icon
   - Text: "This would be clearer with a visual"
   - Suggested prompt shown
   - Buttons: "Yes, generate it" | "Customize prompt" | "No, thanks"

**Expected Result:** Image suggestion appears after Thesis's educational response

---

##  Step 3: Test Aspect Ratio Selection

1. **Click "Yes, generate it"** on the suggestion
2. **Aspect ratio selector should appear:**
   - Four options with visual previews:
     - 1:1 (Square)
     - 16:9 (Landscape - presentation)
     - 9:16 (Portrait - mobile)
     - 4:3 (Standard)
   - Model selector:
     - Fast  (Gemini 2.5 Flash - Quick generation)
     - Quality  (Gemini 3 Pro - Higher quality)
3. **Select your preference** (e.g., 16:9 and Fast)
4. **Click "Generate Image"**

**Expected Result:** Aspect ratio and model selectors display correctly

---

##  Step 4: Test Image Generation

1. After clicking "Generate Image":
   - Loading state should show: "Generating image..."
   - Wait 5-10 seconds
2. **Image should appear** inline in the conversation
3. **Verify image displays:**
   - Image loads from Supabase Storage URL
   - No broken image icons
   - Image matches selected aspect ratio visually

**Expected Result:** Image generates and displays inline in chat

---

##  Step 5: Test Image Actions

### Test Download
1. **Click the Download button** on a generated image
2. **Verify:**
   - Browser download dialog appears
   - File downloads successfully
   - Filename format: `prompt-text_timestamp.png`
   - Image opens correctly in image viewer

**Expected Result:** Image downloads to device

### Test Regenerate
1. **Click the Regenerate button** on a generated image
2. **Verify:**
   - Aspect ratio selector appears again
   - Prompt is pre-filled (same as original)
   - Can select different aspect ratio or model
3. **Select different settings** (e.g., switch from 16:9 to 1:1)
4. **Click "Generate Image"**
5. **Verify:**
   - New image generates with same prompt
   - New aspect ratio is applied
   - New image replaces or appears alongside original

**Expected Result:** Can regenerate with different settings

### Test Delete
1. **Click the Delete button** on a generated image
2. **Verify:**
   - Confirmation dialog appears (or image immediately deletes)
   - Image disappears from conversation
3. **Refresh the page**
4. **Verify:**
   - Deleted image does NOT reappear

**Expected Result:** Image is permanently deleted

---

##  Step 6: Test Persistence

1. **Generate an image** in a conversation
2. **Refresh the page** (F5 or Cmd+R)
3. **Wait for conversation to reload**
4. **Verify:**
   - Image still appears in the conversation
   - Image loads from storage URL
   - Download/Regenerate/Delete buttons still work

**Expected Result:** Images persist after page refresh

---

##  Step 7: Test Explicit Image Request

1. **Type a direct image request:**
   ```
   Generate an image of a sunset over mountains in 16:9
   ```
2. **Send the message**
3. **Verify:**
   - Thesis detects the image request
   - Aspect ratio selector appears (may pre-select 16:9 if detected)
   - Image generation flow proceeds normally

**Expected Result:** Explicit requests trigger image generation

---

##  Step 8: Test Throttling

1. **Generate 1 image** in a conversation
2. **Send 4 more messages** (non-visual topics)
3. **Verify:**
   - No image suggestions appear for next 4 messages
4. **On the 5th message**, ask another visual question:
   ```
   Explain how a combustion engine works
   ```
5. **Verify:**
   - Image suggestion CAN appear again (if topic is visual)

**Expected Result:** Max 1 suggestion per 5 messages

---

##  Step 9: Test Image Limit

This test is optional (requires generating 20 images):

1. **Generate 20 images** in a single conversation
2. **Try to generate the 21st image**
3. **Verify:**
   - Error message appears: "Image limit reached. Contact admin to increase your image generation limit."
   - Cannot generate more images in this conversation
4. **Start a new conversation**
5. **Verify:**
   - Can generate images again (limit is per conversation)

**Expected Result:** 20 image limit enforced per conversation

---

##  Step 10: Test Different Topics

Try these test prompts to verify AI suggestion logic:

### Should Trigger Suggestions:
- "How does the water cycle work?"
- "Explain the structure of DNA"
- "What does the solar system look like?"
- "Show me how a volcano erupts"
- "Visualize the layers of Earth's atmosphere"

### Should NOT Trigger Suggestions:
- "What's the capital of France?" (factual, not visual)
- "Tell me a joke" (conversational)
- "What's 25 * 34?" (mathematical)
- "How are you today?" (greeting)

**Expected Result:** Suggestions appear for visual/educational topics only

---

##  Troubleshooting

###  No Image Suggestions Appearing

**Check:**
1. Backend logs for `should_suggest_image` output
2. Message metadata in database - should have `image_suggestion` field
3. Try explicit visual keywords: "diagram", "visualize", "show me"

**Fix:**
- Verify `backend/services/conversation_service.py` deployed correctly
- Check backend environment variable `GOOGLE_GENERATIVE_AI_API_KEY` is set

---

###  Images Not Generating

**Check:**
1. Browser console for errors (F12 → Console tab)
2. Network tab for `/api/images/generate-in-conversation` request status
3. Backend logs for Gemini API errors

**Fix:**
- Verify `GOOGLE_GENERATIVE_AI_API_KEY` in production backend
- Test endpoint directly: `POST https://your-backend.com/api/images/generate-in-conversation`
- Check Gemini API quota/billing

---

###  Images Not Uploading to Storage

**Check:**
1. Supabase Dashboard → Storage → `conversation-images` bucket exists
2. Bucket is set to **Public**
3. Backend logs for upload errors

**Fix:**
- Recreate bucket if needed: `INSERT INTO storage.buckets (id, name, public) VALUES ('conversation-images', 'conversation-images', true)`
- Verify `SUPABASE_SERVICE_ROLE_KEY` is correct in production backend
- Check Supabase project is active (not paused)

---

###  Images Not Displaying

**Check:**
1. Storage URL format in database: should be `https://...supabase.co/storage/v1/object/public/conversation-images/...`
2. Browser console for CORS errors
3. Try accessing storage URL directly in browser

**Fix:**
- Verify bucket is **Public**
- Check RLS policies on `conversation_images` table
- Verify frontend `NEXT_PUBLIC_SUPABASE_URL` matches backend

---

###  Download Not Working

**Check:**
1. Browser console for blob creation errors
2. Storage URL accessibility (try opening in new tab)
3. Browser download permissions

**Fix:**
- Clear browser cache
- Try different browser
- Check browser allows downloads from site

---

###  "Authentication required" Errors

**Check:**
1. User is logged in to Thesis
2. JWT token is valid (check browser localStorage)
3. Backend authentication middleware

**Fix:**
- Log out and log back in
- Clear browser cookies/localStorage
- Verify Supabase JWT secret matches between frontend and backend

---

##  Success Metrics to Monitor

After 24-48 hours of production use:

### Database Queries

Run these in your **production Supabase SQL Editor:**

```sql
-- Total images generated
SELECT COUNT(*) as total_images FROM conversation_images;

-- Images generated in last 24 hours
SELECT COUNT(*) as images_last_24h
FROM conversation_images
WHERE generated_at > NOW() - INTERVAL '24 hours';

-- Most popular aspect ratios
SELECT aspect_ratio, COUNT(*) as count
FROM conversation_images
GROUP BY aspect_ratio
ORDER BY count DESC;

-- Most popular models
SELECT model, COUNT(*) as count
FROM conversation_images
GROUP BY model
ORDER BY count DESC;

-- Conversations with images
SELECT COUNT(DISTINCT conversation_id) as conversations_with_images
FROM conversation_images;

-- Average images per conversation
SELECT AVG(image_count) as avg_images_per_conversation
FROM (
    SELECT conversation_id, COUNT(*) as image_count
    FROM conversation_images
    GROUP BY conversation_id
) subquery;

-- Messages with image suggestions
SELECT COUNT(*) as messages_with_suggestions
FROM messages
WHERE metadata->'image_suggestion' IS NOT NULL;

-- Top prompts (most common)
SELECT prompt, COUNT(*) as count
FROM conversation_images
GROUP BY prompt
ORDER BY count DESC
LIMIT 10;

-- Storage usage
SELECT
    COUNT(*) as total_images,
    SUM(file_size) as total_bytes,
    ROUND(SUM(file_size) / 1024.0 / 1024.0, 2) as total_mb
FROM conversation_images;
```

### Target Metrics (After 1 Week)
- **Image Generation Rate**: 15% of conversations should include at least 1 image
- **Suggestion Acceptance Rate**: >40% of suggestions accepted
- **Average Generation Time**: 5-10 seconds
- **Error Rate**: <1% of generation attempts
- **Storage Growth**: ~2-5MB per day (depends on usage)

---

##  Feature Adoption Checklist

- [ ] At least 1 user successfully generated an image
- [ ] All aspect ratios tested (1:1, 16:9, 9:16, 4:3)
- [ ] Both models tested (Fast and Quality)
- [ ] Download functionality verified
- [ ] Regenerate functionality verified
- [ ] Delete functionality verified
- [ ] Images persist after page refresh
- [ ] Throttling verified (1 per 5 messages)
- [ ] No console errors during normal operation
- [ ] Backend logs show no critical errors
- [ ] Supabase storage usage is within quota

---

##  Support Checklist

If issues persist after troubleshooting:

1. **Check Vercel deployment logs:**
   - Go to https://vercel.com/dashboard
   - Find "thesis" project
   - Click latest deployment
   - Review build and runtime logs

2. **Check backend application logs:**
   - Access your backend hosting platform (Render/Railway/etc.)
   - Review recent logs for errors
   - Search for "image" or "generate" keywords

3. **Check Supabase logs:**
   - Go to Supabase Dashboard → Logs
   - Filter by timeframe (last 1 hour)
   - Look for storage upload errors or RLS policy violations

4. **Check browser console:**
   - Open DevTools (F12)
   - Go to Console tab
   - Look for errors related to image generation or API calls

---

##  You're Live!

Once you've completed the verification steps above, your AI-powered image generation feature is **fully operational in production**!

**Next steps:**
1. Monitor usage and metrics over next 24-48 hours
2. Gather user feedback on image quality and relevance
3. Adjust suggestion keywords in `conversation_service.py` if needed
4. Consider adding analytics tracking for feature usage

---

##  Quick Reference

- **Production Site**: https://thesis.vercel.app
- **Test Page**: https://thesis.vercel.app/test-image
- **Vercel Dashboard**: https://vercel.com/dashboard
- **Supabase Dashboard**: https://app.supabase.com/project/quizuqhnapsemfvjublt
- **Storage Bucket**: conversation-images
- **API Endpoints**:
  - `POST /api/images/generate-in-conversation`
  - `GET /api/images/conversations/{id}`
  - `DELETE /api/images/{image_id}`
  - `GET /api/images/models`

---

**Last Updated**: Deployment completed
**Feature Status**:  Ready for production testing

 **Your AI-powered image generation feature is live! Start testing!**
