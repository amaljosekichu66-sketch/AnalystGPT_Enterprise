# ADR-030 — Fail-Closed Environment and Signing-Key Policy

**Status:** ✅ **Accepted** — implemented on `pre-sprint-15-hardening`, released in v14.1.0

**Date:** 2026-10-14 (decisions taken 2026-09-28 to 2026-10-14)

**Sprint:** Pre-Sprint-15 hardening

**Decision Makers:** Lead Software Architect, Security Reviewer

---

# Context

Access tokens are HMAC-SHA256 (HS256). Anyone who knows the signing key can forge a token for
any user and role. In v14.0.0:

- `APP_ENVIRONMENT` defaulted to `development`, and development allowed a built-in signing key
  that is published in this repository.
- Docker Compose set neither `APP_ENVIRONMENT` nor `AUTH_SECRET_KEY`, so the containers ran in
  development mode with the public key. The audit forged an ADMIN token against it (SEC-03).
- An empty `AUTH_SECRET_KEY` passed the production check (SEC-04).
- `.env.example` set `APP_ENVIRONMENT=development`, so a bare-metal deployment copied from it
  had a forgeable key and public API docs (P2-18).

# Decision

1. **An unset `APP_ENVIRONMENT` means `production`.** Development conveniences must be asked
   for by name: the built-in key, API docs, `*` allowed hosts, and header identity for tests.
2. **The API refuses to start** outside development when `AUTH_SECRET_KEY` is missing, empty,
   blank, shorter than 32 bytes (RFC 7518 §3.2 for HS256), or equal to the published
   development key.
3. **In development, the built-in key is refused unless the API binds a loopback address.** A
   development API reachable from the network would accept forged tokens.
4. **Any key containing the `.env.example` placeholder (`CHANGE_ME`) is refused in every
   environment**, so a copied template can never start an API.
5. **Templates:**
   - `.env.example` describes a deployment: `APP_ENVIRONMENT=production` and the placeholder
     key.
   - `.env.development.example` holds the local-development overrides.
   - Compose requires `AUTH_SECRET_KEY` and `POSTGRES_PASSWORD` (`${VAR:?}`), has no fallback,
     and sets `APP_ENVIRONMENT: production`.
6. **Checks happen where the key is used.** `require_auth_secret_key()` runs when the API
   package loads and whenever a `TokenService` is built from configuration. The Streamlit
   frontend imports configuration but never signs tokens, so it does not need the key.

# Consequences

- **Positive:** Every way of starting the API by accident is safe, whether from a copied
  template, a missing variable or a fresh Compose. A misconfiguration is a startup failure with
  a message that names the variable and never echoes its value, not a silent vulnerability.
- **Negative:** Local development needs one explicit step:
  `cp .env.development.example .env`.
- **Operational:** Deployments that ran v14.0.0 or earlier signed tokens with a key that may be
  public. Rotate the key; existing tokens stop verifying, which is intended (see ADR-031).

# Verification

`tests/core/test_auth_secret_config.py` covers every refusal reason. It also starts the real
API in subprocesses: from each template unchanged, with each unsafe key, and with a valid key.
`tests/core/test_deployment_hardening.py` pins the Compose rules.

# Related ADRs

- ADR-022 — Containerization and Multi-Service Topology
- ADR-024 — Enterprise Identity and Multi-User Architecture
- ADR-031 — Token Identity and Persistent Revocation
