#  Railway Backend Deployment Required

## Issue

The frontend (Vercel) has been updated with image generation, but the **backend (Railway) is still running old code** without the image generation endpoints.

**Error:** `GET /api/images/conversations/{id}` returns `404 Not Found`

## Why This Happened

-  Vercel auto-deploys from GitHub `main` branch → Frontend is up to date
-  Railway didn't auto-deploy → Backend is missing new endpoints

## Solution

You need to deploy the latest backend code to Railway.

---

##  Option 1: Manual Deploy (Recommended - Takes 2 minutes)

1. **Go to Railway Dashboard:**
   - Visit: https://railway.app/dashboard
   - Log in to your account

2. **Find Your Backend Service:**
   - Look for project named "thesis" or "thesis-backend"
   - Click on the backend service (not database)

3. **Trigger Deployment:**
   - Click **"Deployments"** tab
   - Click **"Deploy"** button (top right)
   - Select **"Deploy latest commit from main"**
   - Wait 2-3 minutes for build to complete

4. **Verify Deployment:**
   - Check deployment logs for "Application startup complete"
   - Test endpoint: `https://thesis-production.up.railway.app/api/images/models`
   - Should return JSON with models and aspect ratios

---

##  Option 2: Force Redeploy via Empty Commit

If Railway is configured to auto-deploy on push:

```bash
cd backend
git commit --allow-empty -m "Trigger Railway redeploy for image generation endpoints"
git push origin main
```

Then check Railway dashboard for new deployment.

---

##  Option 3: Configure Auto-Deploy (Prevents Future Issues)

In Railway Dashboard:

1. Go to your backend service
2. Click **"Settings"** tab
3. Find **"Service"** section
4. Under **"Source"**, ensure:
   - Repository: `motorthings/thesis`
   - Branch: `main`
   - Auto-deploy: **ENABLED** 
   - Root Directory: `.` or `backend`

This ensures Railway auto-deploys whenever you push to `main`.

---

##  What Got Deployed (Already in main branch)

These commits contain the backend image generation code:

- **`446b0ba`** - Main image generation feature
  - `backend/api/routes/images.py` - Image generation endpoints
  - `backend/services/image_generation.py` - Gemini API integration
  - `backend/services/storage_service.py` - Supabase Storage uploads
  - `backend/services/conversation_service.py` - AI suggestion logic
  - `backend/api/routes/chat.py` - Image suggestion detection

- **`ae7ed92`** - System instructions update
  - `backend/system_instructions/default.txt` - Thesis knows about images

- **`ebcaad1`** - Critical UX fixes
  - Updated system instructions for better behavior

All dependencies are already in `backend/requirements.txt`:
- `google-generativeai>=0.8.3` 
- All required packages 

---

##  How to Verify Deployment Succeeded

### Test 1: Check Endpoint Exists

```bash
curl https://thesis-production.up.railway.app/api/images/models
```

**Expected Response:**
```json
{
  "models": [
    {"id": "fast", "name": "Gemini 2.5 Flash", ...},
    {"id": "quality", "name": "Gemini 3 Pro", ...}
  ],
  "aspect_ratios": [...]
}
```

### Test 2: Check Railway Logs

In Railway dashboard:
1. Click your backend service
2. Click **"Logs"** tab
3. Look for:
   ```
   INFO:     Application startup complete.
   INFO:     Uvicorn running on http://0.0.0.0:XXXX
   ```
4. Search logs for "images" to see route registration:
   ```
   Registered route: /api/images/models
   Registered route: /api/images/generate-in-conversation
   Registered route: /api/images/conversations/{conversation_id}
   ```

### Test 3: Test on Production Site

1. Go to https://thesis.vercel.app
2. Start a conversation
3. Ask: "How does photosynthesis work?"
4. Look for image suggestion after Thesis's response
5. Generate an image
6. Verify no 404 errors in browser console

---

##  Common Issues

### Issue: Railway build fails

**Symptom:** Deployment shows "Failed" status in Railway

**Check:**
- Railway logs for error messages
- Ensure `requirements.txt` is complete
- Verify `GOOGLE_GENERATIVE_AI_API_KEY` is set in Railway environment variables

**Fix:**
- Check Railway build logs for specific error
- May need to add missing environment variables

### Issue: Deployment succeeds but still 404

**Symptom:** Deployment shows "Success" but endpoint returns 404

**Check:**
- Railway deployed the correct directory (should be root or `backend/`)
- Start command is correct: `cd backend && python -m uvicorn main:app --host 0.0.0.0 --port $PORT`

**Fix:**
- In Railway settings, verify "Root Directory" and "Start Command"
- May need to adjust `config/railway.json`

### Issue: Railway shows old code

**Symptom:** Railway logs show old version, new endpoints missing

**Fix:**
- In Railway dashboard, click "Redeploy" and select latest commit
- Verify Railway is watching correct branch (`main`)

---

##  Pre-Deployment Checklist

Before deploying to Railway, verify:

- [x] Code committed to GitHub `main` branch
- [x] `backend/api/routes/images.py` exists
- [x] `backend/services/image_generation.py` exists
- [x] `backend/services/storage_service.py` exists
- [x] `backend/services/conversation_service.py` exists
- [x] Dependencies in `requirements.txt`
- [ ] **Railway environment variables set:**
  - `GOOGLE_GENERATIVE_AI_API_KEY` ← CHECK THIS!
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_ROLE_KEY`
  - `ANTHROPIC_API_KEY`
  - All other required variables

---

##  After Deployment

Once Railway deployment completes:

1. **Test the endpoint:**
   ```bash
   curl https://thesis-production.up.railway.app/api/images/models
   ```

2. **Test on live site:**
   - Visit https://thesis.vercel.app
   - Generate an image
   - Verify it works end-to-end

3. **Monitor logs:**
   - Check Railway logs for any errors
   - Check Supabase logs for image uploads
   - Check for any API rate limiting or quota issues

4. **Clean up:**
   - Delete this file once deployment is verified
   - Or keep it for future reference

---

##  Quick Links

- **Railway Dashboard:** https://railway.app/dashboard
- **Backend URL:** https://thesis-production.up.railway.app
- **Frontend URL:** https://thesis.vercel.app
- **GitHub Repo:** https://github.com/motorthings/thesis

---

**Status:**  Waiting for Railway deployment

**Next Step:** Go to Railway dashboard and trigger redeploy

**ETA:** 2-3 minutes for build + deploy
