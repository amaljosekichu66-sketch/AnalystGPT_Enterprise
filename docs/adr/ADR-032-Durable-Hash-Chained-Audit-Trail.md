# ADR-032 — Durable, Hash-Chained Audit Trail with Retention

**Status:** ✅ **Accepted** — implemented on `pre-sprint-15-hardening`, released in v14.1.0

**Date:** 2026-10-14 (decisions taken 2026-09-28 to 2026-10-08)

**Sprint:** Pre-Sprint-15 hardening

**Decision Makers:** Lead Software Architect, Security Reviewer

---

# Context

In v14.0.0, security events lived in a process-memory list capped at 1,000 entries, plus log
lines (SEC-25). A restart erased them, and anyone with database access could edit them without
trace. They kept a deleted user's name and email forever, and had no retention policy (P2-14).

# Decision

**Storage.** Events are written to the `audit_events` table by `DatabaseAuditSink`, which opens
its own connection for each write.

The event types (`AuditEventType`) cover:

- authentication: login success and failure, logout, a rejected (invalid or revoked) token,
  and a rate-limit refusal;
- accounts: registration, update, status and role changes, deletion, a denied access, and a
  blocked administrative operation such as removing the last admin;
- data: dataset upload and deletion, pipeline execution, report export, and policy proposal,
  approval and rejection;
- administrators reading another tenant's resources, as a distinct event type.

Security-relevant events also emit a `SECURITY_ALERT` log line for alerting.

**Tamper evidence.** Each row stores `prev_hash` and
`row_hash = SHA-256(prev_hash ‖ canonical(event_id, event_type, occurred_at, actor_id, target_id, target_resource, action, outcome))`.

`GET /api/admin/audit-events/verify` (ADMIN) recomputes the chain and reports the first broken
row. Editing or deleting a row breaks it.

**What the hash covers.** The hash deliberately **excludes** `actor_username` and `details`. Those
fields are what pseudonymisation rewrites when an account is deleted (ADR-033). The chain
therefore stays valid after erasure, and still proves who did what, when, and with what
outcome, by user id.

**Retention.** `AUDIT_RETENTION_DAYS` (default 365) prunes older rows at startup. Pruning
removes whole rows from the start of the chain, so verification starts from the oldest row that
remains.

**Reading.** `GET /api/admin/audit-events` (ADMIN, filterable). The Admin UI shows the log.

# Consequences

- **Positive:**
  - The trail survives restarts and is shared by every API process.
  - Tampering is detectable.
  - Erasure and the audit trail are compatible.
  - Retention is a single setting.
- **Negative:** Writes are serialised through the previous row's hash, which is fine at the
  current event rate. The chain is evidence, not prevention: someone who can rewrite the table
  can also recompute it. Export the verify result, or ship the `SECURITY_ALERT` log lines to an
  external store, when that threat matters.
- **Limits:** Details fields are not covered by the hash, as explained above.

# Verification

`tests/api/test_erasure_and_audit_chain.py` checks:

- the chain verifies;
- an edit, or a deleted row, is detected;
- pseudonymisation keeps the chain valid;
- retention prunes;
- the verify endpoint is ADMIN-only.

`tests/api/test_admin_data_governance.py` covers the events emitted.

# Related ADRs

- ADR-024 — Enterprise Identity and Multi-User Architecture
- ADR-033 — User Deletion Is an Atomic Hard Delete
