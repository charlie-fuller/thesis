# Thesis Platform Security Assessment Report

**Assessment Date:** January 26, 2026
**Prepared For:** IT Security Review
**Application:** Thesis Multi-Agent GenAI Strategy Platform
**Deployment Target:** Internal enterprise use

---

## Executive Summary

This security assessment was conducted to evaluate the Thesis platform before internal deployment. The application is a multi-agent AI platform for enterprise GenAI strategy that integrates with Anthropic Claude, Supabase, Neo4j, and various Google services.

### Overall Risk Rating: **MEDIUM-HIGH**

| Category | Rating | Action Required |
|----------|--------|-----------------|
| **Secrets Management** | CRITICAL | Immediate rotation required |
| **Authentication** | HIGH | Add auth to public endpoints |
| **Error Handling** | HIGH | Sanitize error messages |
| **API Security** | MEDIUM | Add rate limiting |
| **Dependencies** | MEDIUM | Update python-jose |
| **File Uploads** | MEDIUM | Add magic number validation |
| **Security Testing** | GOOD | Tests already in place |

---

## Critical Issues (Immediate Action Required)

### 1. Exposed Secrets in Repository

**Severity:** CRITICAL
**Risk:** Complete system compromise

The `.env` file contains live API keys and service credentials:

| Secret | Exposure Level | Impact |
|--------|----------------|--------|
| `SUPABASE_SERVICE_ROLE_KEY` | Full access | Database read/write, bypass RLS |
| `SUPABASE_JWT_SECRET` | Auth bypass | Token forgery possible |
| `ANTHROPIC_API_KEY` | API costs | Unlimited Claude API usage |
| `VOYAGE_API_KEY` | API costs | Unlimited embeddings API |
| `NEO4J_PASSWORD` | Full access | Knowledge graph access |

**Additionally found hardcoded secrets in:**
- `scripts/testing/*.py` (10+ files)
- `scripts/diagnostics/*.py` (6+ files)
- `scripts/data/*.py` (4+ files)
- `test_endpoints_manual.sh`
- `test_chat_quick.sh`

**Required Actions:**
1. Rotate ALL exposed credentials immediately
2. Remove secrets from git history using `git filter-repo`
3. Implement secrets scanning in CI/CD pipeline
4. Use environment-based secrets for deployment (Railway environment variables)

---

### 2. Missing Authentication on Public Endpoints

**Severity:** HIGH
**File:** `api/routes/agents.py`

7 critical endpoints have NO authentication requirement:

| Endpoint | Risk |
|----------|------|
| `GET /api/agents` | System architecture exposure |
| `GET /api/agents/{id}` | Agent configuration exposure |
| `GET /api/agents/{id}/conversations` | Data enumeration |
| `GET /api/agents/{id}/instructions` | System prompt exposure |
| `GET /api/agents/{id}/xml-instructions` | Raw instruction XML exposure |
| `GET /api/agents/{id}/documents` | Document list exposure |
| `GET /api/agents/documents/available` | All documents enumeration |

**Root Cause:** Endpoints use `Depends(get_supabase)` instead of `Depends(get_current_user)`

**Required Fix:**
```python
# Change FROM:
async def list_agents(supabase: Client = Depends(get_supabase)):

# Change TO:
async def list_agents(
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
```

---

### 3. Excessive Error Information Disclosure

**Severity:** HIGH
**Instances:** 323 occurrences across multiple route files

**Pattern:**
```python
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))  # VULNERABLE
```

**Risk:** Exception messages expose:
- Internal file paths
- Database table/column names
- API endpoint structures
- Library versions

**Required Fix:**
```python
except Exception as e:
    logger.error(f"Operation failed: {str(e)}")  # Log internally
    raise HTTPException(
        status_code=500,
        detail="An error occurred. Please try again."
    )  # Generic user message
```

---

## High Priority Issues

### 4. Outdated JWT Library

**Severity:** HIGH
**Package:** `python-jose==3.3.0`

- Last release: December 2021 (4+ years old)
- Project appears abandoned
- Multiple known JWT handling issues
- No security patches for recent vulnerabilities

**Recommendation:** Migrate to `PyJWT` which is actively maintained.

---

### 5. OAuth State Not Checked for Expiration

**Severity:** MEDIUM
**File:** `api/routes/google_drive.py` (lines 100-110)

The OAuth callback validates state existence but does NOT verify expiration, enabling replay attacks.

**Required Fix:** Add expiration check before token exchange.

---

## Medium Priority Issues

### 6. Insufficient File Upload Validation

**Severity:** MEDIUM
**Files:** `validation.py`, `api/routes/users.py`

| Issue | Risk |
|-------|------|
| No magic number validation | Executables disguised as PDFs |
| Double extension attacks | `file.pdf.exe` bypass |
| Path traversal in avatar upload | `../../etc/passwd.jpg` |

**Recommendation:** Implement `python-magic` for file signature validation.

---

### 7. CORS Configuration Allows All Localhost

**Severity:** MEDIUM
**File:** `main.py` (lines 137-170)

All localhost origins are automatically allowed regardless of environment:
```python
LOCAL_DEV_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    ...
]
```

**Impact:** Reduces CORS effectiveness in production. Any local malware can access the API.

**Recommendation:** Remove localhost origins in production configuration.

---

### 8. Missing Rate Limiting on Sensitive Endpoints

**Severity:** MEDIUM

Rate limiting is configured for chat (`20/minute`) but missing on:
- `/api/users` (user enumeration)
- `/api/documents/*` (upload abuse)
- Authentication endpoints (brute force)
- Admin endpoints

---

## Positive Security Findings

### What's Working Well

| Area | Implementation |
|------|----------------|
| **JWT Authentication** | Proper token validation, expiration checks, algorithm verification |
| **Database Access** | Supabase ORM with parameterized queries (no SQL injection) |
| **OAuth Token Storage** | AES-128 (Fernet) encryption for stored OAuth tokens |
| **Environment Loading** | Proper `python-dotenv` usage before imports |
| **Security Testing** | Comprehensive test suite in `test_security.py` |
| **CI/CD Security Scanning** | `safety`, `pip-audit`, `bandit` configured in GitHub Actions |

### Security Tests Already Implemented

The codebase includes comprehensive security tests (`tests/test_security.py`):
- JWT validation edge cases
- Cross-user data access prevention
- SQL injection prevention
- XSS attack prevention
- Path traversal prevention
- Rate limiting verification
- Security header validation

---

## Dependency Security Summary

| Package | Version | Status |
|---------|---------|--------|
| fastapi | 0.115.0 | OK - Current |
| pydantic | >=2.11.7 | OK - Range pinned |
| cryptography | >=41.0.7 | WARN - Unpinned upper bound |
| python-jose | 3.3.0 | CRITICAL - Abandoned |
| httpx | 0.27.0 | OK - Pinned |
| anthropic | 0.60.0 | OK - Pinned |
| supabase | 2.24.0 | OK - Pinned |

**Pinning Status:** 50% properly pinned, 33% unpinned (>=)

---

## Recommendations for IT Team

### Before Internal Release (Required)

1. **Rotate all exposed credentials** - Supabase, Anthropic, Voyage, Neo4j
2. **Add authentication** to `/api/agents/*` endpoints
3. **Sanitize error messages** - Remove `str(e)` from HTTPException details
4. **Update python-jose** or migrate to PyJWT
5. **Add OAuth state expiration check**

### Short-Term Improvements

6. Pin all dependency versions with upper bounds
7. Add magic number validation for file uploads
8. Implement rate limiting on all sensitive endpoints
9. Configure CORS to exclude localhost in production
10. Enable security check failure in CI/CD (remove `continue-on-error: true`)

### Before Broader Deployment

11. Implement secrets management (HashiCorp Vault, AWS Secrets Manager)
12. Add secret rotation procedures
13. Implement audit logging for credential access
14. Add pre-commit hooks for secret detection
15. Complete IT compliance controls (marked as xfail in tests)

---

## Risk Matrix

| Risk | Likelihood | Impact | Priority |
|------|------------|--------|----------|
| Credential theft from git history | HIGH | CRITICAL | P0 |
| Unauthenticated agent data access | MEDIUM | HIGH | P1 |
| Error message information leak | MEDIUM | MEDIUM | P1 |
| JWT library vulnerability | LOW | HIGH | P2 |
| File upload attack | LOW | MEDIUM | P2 |
| Rate limit bypass | MEDIUM | LOW | P3 |

---

## Compliance Notes

| Standard | Status |
|----------|--------|
| **OWASP Top 10** | 4/10 issues identified (A01, A05, A06, A07) |
| **SOC 2** | Requires secret management improvements |
| **GDPR** | N/A for internal deployment |

---

## Files Referenced

- `backend/auth.py` - Authentication implementation
- `backend/database.py` - Database connection
- `backend/config/__init__.py` - Configuration management
- `backend/api/routes/agents.py` - Agent endpoints (missing auth)
- `backend/api/routes/google_drive.py` - OAuth implementation
- `backend/validation.py` - Input validation
- `backend/main.py` - CORS configuration
- `backend/services/oauth_crypto.py` - Token encryption
- `backend/tests/test_security.py` - Security tests
- `.github/workflows/test.yml` - CI/CD security scanning

---

**Report Prepared By:** Automated Security Assessment
**Next Review Date:** Before production deployment
