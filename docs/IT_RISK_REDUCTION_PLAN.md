# Thesis AI - IT Risk Reduction Action Plan

**Date**: January 25, 2026
**Current Risk Level**: MEDIUM
**Target Risk Level**: LOW
**Timeline**: 8 weeks

---

## Executive Summary

This plan outlines specific actions to reduce IT risk for the Thesis AI application from MEDIUM to LOW. Actions are prioritized by risk reduction impact and implementation effort.

---

## Phase 1: Immediate Actions (Week 1-2)

### 1.1 Authentication Hardening

| Action | Owner | Deadline | Status |
|--------|-------|----------|--------|
| Enable MFA requirement for all users | IT Admin | Week 1 | [ ] |
| Set session timeout to 8 hours max | Backend Dev | Week 1 | [ ] |
| Implement session revocation endpoint | Backend Dev | Week 1 | [ ] |
| Add failed login attempt throttling (5/15min) | Backend Dev | Week 2 | [ ] |

**Implementation**:
```python
# backend/config/security.py
SESSION_CONFIG = {
    "max_age_hours": 8,
    "refresh_threshold_minutes": 30,
    "max_concurrent_sessions": 3,
    "require_mfa": True,
}

RATE_LIMITS = {
    "login_attempts": {"max": 5, "window_minutes": 15},
    "chat_requests": {"max": 20, "window_minutes": 1},
    "file_uploads": {"max": 10, "window_minutes": 1},
}
```

### 1.2 Audit Logging Enhancements

| Action | Owner | Deadline | Status |
|--------|-------|----------|--------|
| Add structured JSON logging | Backend Dev | Week 1 | [ ] |
| Log all authentication events | Backend Dev | Week 1 | [ ] |
| Log all data access events | Backend Dev | Week 1 | [ ] |
| Configure log retention (90 days) | DevOps | Week 2 | [ ] |
| Set up log alerting for anomalies | DevOps | Week 2 | [ ] |

**Required Log Fields**:
```json
{
  "timestamp": "ISO8601",
  "event_type": "auth|data_access|api_call|error",
  "user_id": "uuid",
  "client_id": "uuid",
  "action": "login|logout|read|write|delete",
  "resource_type": "conversation|document|task",
  "resource_id": "uuid",
  "ip_address": "string",
  "user_agent": "string",
  "success": "boolean",
  "metadata": {}
}
```

### 1.3 Cost Controls

| Action | Owner | Deadline | Status |
|--------|-------|----------|--------|
| Set per-user API spending limits | Backend Dev | Week 1 | [ ] |
| Add department-level budget caps | Backend Dev | Week 2 | [ ] |
| Configure cost threshold alerts | DevOps | Week 2 | [ ] |
| Create usage dashboard | Frontend Dev | Week 2 | [ ] |

**Configuration**:
```yaml
# config/cost_limits.yaml
limits:
  per_user:
    daily_tokens: 100000
    monthly_tokens: 2000000
    daily_embeddings: 1000
  per_department:
    monthly_budget_usd: 500
  alerts:
    warn_at_percent: 80
    block_at_percent: 100
```

---

## Phase 2: Short-term Actions (Week 3-4)

### 2.1 SSO Integration (Priority: HIGH)

| Action | Owner | Deadline | Status |
|--------|-------|----------|--------|
| Evaluate SSO providers (Okta, Azure AD) | IT Admin | Week 3 | [ ] |
| Implement SAML/OIDC integration | Backend Dev | Week 3-4 | [ ] |
| Configure user provisioning | IT Admin | Week 4 | [ ] |
| Test with pilot group | QA | Week 4 | [ ] |

**Requirements**:
- Support SAML 2.0 and OIDC
- Map corporate roles to app roles
- Support Just-in-Time (JIT) provisioning
- Enable group-based access control

### 2.2 Secret Management

| Action | Owner | Deadline | Status |
|--------|-------|----------|--------|
| Deploy HashiCorp Vault (or AWS Secrets Manager) | DevOps | Week 3 | [ ] |
| Migrate API keys from env vars to Vault | DevOps | Week 3 | [ ] |
| Implement secret rotation | DevOps | Week 4 | [ ] |
| Remove secrets from deployment configs | DevOps | Week 4 | [ ] |

**Secrets to Migrate**:
- `ANTHROPIC_API_KEY`
- `VOYAGE_API_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_JWT_SECRET`
- `NEO4J_PASSWORD`
- `MEM0_API_KEY`

### 2.3 Data Classification & Protection

| Action | Owner | Deadline | Status |
|--------|-------|----------|--------|
| Tag PII fields in database | Backend Dev | Week 3 | [ ] |
| Implement PII auto-detection in prompts | Backend Dev | Week 3 | [ ] |
| Add data masking in logs | Backend Dev | Week 4 | [ ] |
| Create data retention policy | Compliance | Week 4 | [ ] |

---

## Phase 3: Medium-term Actions (Week 5-6)

### 3.1 Network Security

| Action | Owner | Deadline | Status |
|--------|-------|----------|--------|
| Implement API gateway (Kong/AWS API Gateway) | DevOps | Week 5 | [ ] |
| Configure WAF rules | DevOps | Week 5 | [ ] |
| Enable DDoS protection | DevOps | Week 5 | [ ] |
| Implement IP allowlisting for admin routes | Backend Dev | Week 6 | [ ] |

### 3.2 Disaster Recovery

| Action | Owner | Deadline | Status |
|--------|-------|----------|--------|
| Document backup procedures | DevOps | Week 5 | [ ] |
| Test database restore (Supabase) | DevOps | Week 5 | [ ] |
| Create incident response runbook | IT Admin | Week 6 | [ ] |
| Conduct tabletop exercise | IT Team | Week 6 | [ ] |

### 3.3 Compliance Documentation

| Action | Owner | Deadline | Status |
|--------|-------|----------|--------|
| Complete vendor DPA inventory | Legal | Week 5 | [ ] |
| Document data flows (DPIA) | Compliance | Week 5 | [ ] |
| Create acceptable use policy | Legal | Week 6 | [ ] |
| User training materials | Training | Week 6 | [ ] |

---

## Phase 4: Ongoing Actions (Week 7-8+)

### 4.1 Continuous Monitoring

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Failed login rate | < 5% | > 10% |
| API error rate | < 1% | > 5% |
| P95 latency | < 500ms | > 1000ms |
| Token usage per user | < 50K/day avg | > 100K/day |
| Unusual access patterns | N/A | > 2 std dev |

### 4.2 Regular Reviews

| Review | Frequency | Owner |
|--------|-----------|-------|
| Access certification | Quarterly | IT Admin |
| Security scan | Monthly | Security |
| Penetration test | Annually | External |
| Vendor risk assessment | Annually | Compliance |
| Cost review | Monthly | Finance |

---

## Risk Mitigation Summary

### Before Implementation

| Risk Area | Level | Concern |
|-----------|-------|---------|
| Authentication | MEDIUM | No MFA, no SSO |
| Data exposure | MEDIUM | Third-party APIs |
| Secrets | HIGH | In env vars |
| Audit trail | MEDIUM | Basic logging |
| Cost control | HIGH | No limits |
| Vendor lock-in | MEDIUM | Cloud dependencies |

### After Implementation

| Risk Area | Level | Mitigation |
|-----------|-------|------------|
| Authentication | LOW | SSO + MFA required |
| Data exposure | LOW | DPA + encryption + PII detection |
| Secrets | LOW | Vault with rotation |
| Audit trail | LOW | Structured logs + alerts |
| Cost control | LOW | Per-user limits + budgets |
| Vendor lock-in | LOW | Abstraction layer exists |

---

## Vendor Risk Summary

| Vendor | Data Sent | DPA | SOC2 | Training Opt-out |
|--------|-----------|-----|------|------------------|
| Anthropic | Prompts/responses | Yes | Type II | Confirmed |
| Voyage AI | Document text | Yes | Type II | Yes |
| Supabase | All app data | Yes | Type II | N/A |
| Railway | Logs only | Yes | Type II | N/A |
| Vercel | Static assets | Yes | Type II | N/A |

---

## Budget Estimate

| Item | One-time | Monthly |
|------|----------|---------|
| HashiCorp Vault | $0 (OSS) | $50 (managed) |
| SSO Integration | $5,000 | Included in IdP |
| API Gateway | $0 (AWS free tier) | $100+ |
| Log aggregation | $0 | $200+ |
| Penetration test | $10,000/year | N/A |
| **Total** | ~$15,000 | ~$350+ |

---

## Approval & Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| IT Director | | | |
| Security Lead | | | |
| Compliance Officer | | | |
| Engineering Lead | | | |

---

## Appendix: Quick Reference Commands

### Run Security Tests
```bash
cd backend
./scripts/run-all-tests.sh security
```

### Generate IT Audit Report
```bash
cd backend
./scripts/run-all-tests.sh it-audit
```

### Check Current Security Status
```bash
# Run security scan
bandit -r backend/ -f json -o security-report.json

# Check dependencies
pip-audit -r requirements.txt
npm audit --prefix frontend
```

---

*Document generated: January 25, 2026*
*Next review: April 25, 2026*
