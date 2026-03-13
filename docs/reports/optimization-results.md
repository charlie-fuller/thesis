# Cold Start Optimization Results

**Date:** 2026-03-12
**Deploy:** Fly.io `thesis-genai-api` (shared-cpu-1x, 512MB, scale-to-zero)
**Commit:** `bc6c4c83` + `37f597be`

## Summary

Reduced cold start time from ~12-15s to ~7s (50% faster) by deferring schedulers, lazy-loading agent modules, and limiting unbounded database queries.

## Changes Made

### Phase 1: Lazy Agent Loading
- `agents/__init__.py` — replaced 17 eager imports with `__getattr__` lazy loading
- `agents/agent_factory.py` — replaced top-level imports with `_get_agent_class()` registry that imports on demand
- **Impact:** Avoids importing 17 agent classes + their transitive dependencies (anthropic, supabase, etc.) at startup

### Phase 2: Deferred Schedulers
- `main.py` — moved all 6 schedulers into `_deferred_schedulers()` async task (30s delay)
- Vault watcher deferred 60s with `initial_sync=False`
- Google Drive sync scheduler removed entirely (packages already removed)
- **Impact:** Health check responds immediately; schedulers start in background

### Phase 3: Query Limits
- `api/routes/chat.py` — conversation history `.limit(50)` (was unbounded, fetched ALL messages)
- `agents/taskmaster.py` — task query `.limit(200)` with `.order("due_date")` (was unbounded)
- **Impact:** Bounds worst-case query cost for long conversations and users with many tasks

### Phase 4: Cleanup
- CORS middleware logging downgraded from `INFO` to `DEBUG` (2 fewer log lines per request)
- Removed unused `opportunities` router import and registration
- Added `.dockerignore` excluding `frontend/`, `venv/`, `.git/`, `docs/` (except `docs/help/`)

## Measured Results

### Cold Start Timeline (from Fly.io logs)

| Event | Timestamp | Elapsed |
|-------|-----------|---------|
| Process start | `03:44:32` | 0s |
| App startup complete | `03:44:38` | 6s |
| Health check passing | `03:44:39` | **7s** |
| Deferred schedulers fire | `03:45:08` | 36s (by design) |
| Vault watcher fires | `03:45:38` | 66s (by design) |

### Before vs After

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Process start to health check | ~12-15s | **7s** | ~50% faster |
| Agent modules imported at startup | 22 | 4 (base only) | -18 modules |
| Schedulers blocking startup | 6 (synchronous) | 0 (deferred 30s) | Eliminated |
| CORS log lines per request | 2 (INFO) | 0 (filtered at DEBUG) | -2 lines/req |
| Conversation history query | Unbounded | `.limit(50)` | Bounded |
| Task query | Unbounded | `.limit(200)` | Bounded |
| Docker build context | ~21MB | 12.56MB | ~40% smaller |
| Warm request latency | ~250ms | ~245ms | No change (expected) |

### Log Evidence

```
03:44:38 - Application startup complete (schedulers deferred 30s)
03:44:39 - Health check 'servicecheck-00-http-8080' is now passing.
03:45:08 - Starting deferred schedulers (30s post-startup)
03:45:08 - Atlas research scheduler started
03:45:08 - Knowledge Graph sync scheduler started
03:45:08 - Stakeholder engagement scheduler started
03:45:08 - Manifesto compliance digest scheduler started
03:45:08 - Discovery scan scheduler started
03:45:08 - All deferred schedulers started
03:45:38 - Vault watcher not started: VAULT_WATCHER_USER_ID not configured
```

## Files Changed

| File | Lines Changed |
|------|--------------|
| `backend/agents/__init__.py` | +88 -90 |
| `backend/agents/agent_factory.py` | +64 -121 |
| `backend/agents/taskmaster.py` | +3 -1 |
| `backend/api/routes/chat.py` | +15 -7 |
| `backend/main.py` | +83 -79 |
| `.dockerignore` | +20 (new) |

## Notes

- The 9s total cold start measured from `curl` includes Fly.io machine wake time (~2s) + app startup (7s)
- Warm requests are unaffected (~245ms) since lazy loading caches after first access
- Fly.io `auto_stop_machines = 'suspend'` means cold starts happen after idle periods
- The `grace_period = "10s"` in `fly.toml` health check config is sufficient for the 7s startup
