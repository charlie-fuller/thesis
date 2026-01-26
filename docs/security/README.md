# Security Documentation

This folder contains security-related documentation for the Thesis platform.

## Contents

| Document | Description |
|----------|-------------|
| `SECURITY_ASSESSMENT_REPORT.md` | Comprehensive security audit findings and recommendations |

## Quick Links

- **Credentials Management**: See `/docs/ARCHITECTURE.md#security--credentials-management`
- **1Password Setup**: See `/backend/.claude/commands/1password.md`
- **Credentials Module**: `/backend/scripts/lib/credentials.py`

## Security Practices

### Credential Storage

1. **1Password** (Recommended) - Secure vault with biometric authentication
2. **dotenvx** - Encrypted `.env.vault` for deployment environments
3. **Environment Variables** - For CI/CD pipelines

### Never Commit

- `.env` files with plaintext secrets
- API keys or tokens in source code
- JWT secrets or service role keys

### Security Contacts

For security concerns, contact the repository maintainers.
