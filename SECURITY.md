# Security Policy

## Reporting a vulnerability

If you find a security issue, **do not open a public issue**. Email
**security@tideguard.app** with:

1. A description of the vulnerability.
2. Steps to reproduce.
3. Your assessment of severity (CVSS preferred but not required).

We commit to acknowledging reports within **48 hours** and providing a
resolution timeline within **7 days**.

## Scope

The following are in scope:

- `apps/api/` — server-side code, authentication, RBAC, file upload
- `apps/web/` — XSS, CSRF, SSRF, token leakage
- `apps/mobile/` — token storage, data leakage, insecure comms
- Infrastructure (Docker, fly.toml, CI secrets)

## Known hardening measures

- JWT auth (HS256 with rotatable secret) — no email-as-token.
- Photo uploads: MIME validation, 10 MB limit, EXIF metadata stripped
  (children's privacy protection per GDPR Art. 8 / COPPA).
- Rate limiting via `slowapi` (60 req/min/IP on write endpoints).
- CORS restricted to known origins; `credentials: true` only for
  production frontend origins.
- Pre-commit hooks enforce `ruff` (no obvious code-smell merges).
- CI runs all tests before merge.

## Disclosure policy

We will credit reporters in the CHANGELOG unless they prefer anonymity.
Critical fixes are released within 72 hours; non-critical within 14 days.
