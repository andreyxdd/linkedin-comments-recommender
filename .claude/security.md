# Security Rules (MANDATORY)

These rules are NOT suggestions.
Any violation must result in refusal or a corrected implementation.

---

## 1. Authentication & Sessions

- Enforce authentication on every non-public endpoint
- Regenerate session IDs after login and privilege changes
- Use secure, httpOnly cookies (NEVER localStorage for sensitive data)

---

## 2. Authorization

- Check authorization on EVERY operation:
  - read
  - write
  - update
  - delete
- Never trust client-supplied IDs without verifying ownership server-side
- Apply least privilege across all users and services

---

## 3. Input & Request Security

- Validate ALL input server-side (frontend validation is irrelevant)
- Add CSRF protection to all state-changing requests
- Use constant-time comparison for secrets and tokens
- Disable unused HTTP methods

---

## 4. Secrets & Credentials

- NEVER hardcode secrets in:
  - source code
  - prompts
  - logs
  - client bundles
- Use environment variables or secure secret storage
- Use separate credentials for dev, staging, production
- Scope tokens to minimum permissions
- Rotate keys regularly
- Use short-lived access tokens + refresh rotation

---

## 5. Passwords & Sensitive Data

- Hash passwords using Argon2 or bcrypt (strong cost)
- NEVER log:
  - passwords
  - API keys
  - session tokens
  - sensitive PII
- Do not expose sensitive data in responses

---

## 6. Transport & Headers

- Enforce HTTPS everywhere (redirect HTTP)
- Set security headers:
  - Content-Security-Policy (strict)
  - X-Frame-Options: DENY (or frame-ancestors)
  - Referrer-Policy (strict)
  - Cache-Control: no-store (for sensitive data)

---

## 7. API & Abuse Protection

- Rate limit:
  - login
  - signup
  - password reset
  - OTP
  - sensitive endpoints
- Never expose stack traces or raw errors in production

---

## 8. File Handling

- Validate file:
  - type
  - size
  - content
- Strip metadata from uploads
- Use short-lived signed URLs for private files
- NEVER expose raw storage paths or public object URLs
- Disable directory listing

---

## 9. Logging & Monitoring

- Log security-relevant events:
  - logins
  - admin actions
  - deletes
  - permission changes
- Logs must NOT contain sensitive data

---

## 10. Dependencies & Supply Chain

- Remove unused dependencies
- Pin versions
- Review all third-party libraries
- Continuously scan for vulnerabilities

---

## 11. Failure Handling

- On any security uncertainty:
  - STOP
  - Explain the risk
  - Provide a safer alternative

---

## 12. Default Mindset

Assume:
- The system is under attack
- Inputs are malicious
- Users will attempt privilege escalation

Design defensively at all times.

---

## Enforcement Rule

If your solution violates ANY rule above:
- You MUST NOT proceed silently
- You MUST explicitly state: "SECURITY VIOLATION"
- Then provide a corrected implementation
