# Final Manual Step Required

## Add Google Generative AI API Key to Railway

The Railway API is currently timing out, so this needs to be added manually:

### Steps:

1. **Go to Railway Dashboard:**
   https://railway.app/project/superassistant-mvp

2. **Navigate to Variables:**
   Click on your service → Settings → Variables

3. **Add New Variable:**
   ```
   Name: GOOGLE_GENERATIVE_AI_API_KEY
   Value: AIzaSyBAM4AwdJ16GFqo4M_h5D3umFA-_zaYtEk
   ```

4. **Save and Redeploy:**
   Railway will automatically redeploy with the new variable

---

## Verify Deployment

Once added, test image generation:

```bash
# Test backend health
curl https://superassistant-mvp-production.up.railway.app/health

# The image generation endpoint will now work with the API key
```

In the Thesis app, test with:
```
/visualize A friendly learning professional coaching a team
```

---

## All Other Variables Already Set

These are already configured in Railway:
- ANTHROPIC_API_KEY
- VOYAGE_API_KEY
- SUPABASE_URL
- SUPABASE_KEY
- SUPABASE_JWT_SECRET
- SUPABASE_SERVICE_ROLE_KEY
- FRONTEND_URL

Only missing: `GOOGLE_GENERATIVE_AI_API_KEY` (for Nano Banana image generation)

---

**Status:** Everything else is deployed and ready!
