# ADR-031 — Token Identity and Persistent Revocation

**Status:** ✅ **Accepted** — implemented on `pre-sprint-15-hardening`, released in v14.1.0

**Date:** 2026-10-14 (decisions taken 2026-09-28 to 2026-10-14)

**Sprint:** Pre-Sprint-15 hardening

**Decision Makers:** Lead Software Architect, Security Reviewer

---

# Context

In v14.0.0 a token held `sub`, `role`, `iat` and `exp`. It had no unique identifier, so two
logins in the same second produced the **same** token (SEC-16). Logout stored the raw token
string in a process-memory set that:

- anyone could fill without authenticating (SEC-09);
- was lost on restart;
- was not shared between workers.

A password, role or status change left existing tokens valid until they expired. Validation
did not check that `iat` was in the past or honour `nbf` (P3-05).

# Decision

**Claims.** Every token carries:

| Claim | Meaning |
|---|---|
| `jti` | random 128-bit id, which is what revocation is keyed on |
| `iss`, `aud` | bound to this service (`AUTH_TOKEN_ISSUER`, `AUTH_TOKEN_AUDIENCE`) |
| `ver` | the user's `token_version` at issue time |
| `iat`, `exp` | integer seconds |

**Revocation is persisted.** `POST /api/auth/logout` requires the token being revoked and
stores `jti` with its expiry in the `revoked_tokens` table. Expired rows are pruned as new
revocations are written. Revocations survive restarts and are shared by every API process.

**Revocation by version.** `users.token_version` is incremented on:

- a password change (`POST /api/auth/password`, which requires the current password);
- a role or status change by an administrator;
- "log out everywhere" (`POST /api/auth/logout-all`).

Every request compares `ver` with the stored value, so all of a user's tokens are revoked with
one update.

**Validation refuses:**

- a token with a bad signature, padded or non-canonical base64url, or an `alg` other than HS256;
- a token that has expired, or whose lifetime exceeds `AUTH_TOKEN_MAX_LIFETIME_MINUTES`;
- `iat` more than 60 s in the future, or `nbf` not yet reached;
- non-integer time claims;
- a wrong `type`, `iss` or `aud`, or a missing `jti`.

**Each request re-reads the user,** so a suspended or deleted account loses access on its next
request whatever its token says.

# Consequences

- **Positive:** Logout and credential changes take effect immediately and stay in effect after
  a restart. Revocation is per token (`jti`) or per user (`ver`).
- **Negative:** One indexed lookup per request (`revoked_tokens` by `jti`), on top of the user
  lookup that already happened.
- **Breaking:** Tokens issued by v14.0.0 lack `jti`, `iss` and `aud` and are rejected after the
  upgrade. Users sign in again. This is in the v14.1.0 upgrade notes.
- **Not chosen:** refresh tokens and an external store such as Redis. Neither is needed at
  current scale; ADR-024's single-issuer model stands.

# Verification

`tests/api/test_auth_hardening.py`, `tests/identity/test_token_time_claims.py`, and the
session-lifecycle tests for password change, logout-all and role changes.

# Related ADRs

- ADR-024 — Enterprise Identity and Multi-User Architecture
- ADR-030 — Fail-Closed Environment and Signing-Key Policy
