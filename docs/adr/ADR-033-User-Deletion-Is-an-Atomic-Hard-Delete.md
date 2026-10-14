# ADR-033 — User Deletion Is an Atomic Hard Delete

**Status:** ✅ **Accepted** — implemented on `pre-sprint-15-hardening`, released in v14.1.0.
**This settles the "soft- vs hard-delete" question that ROADMAP Sprint 15 Phase 4 left open.**

**Date:** 2026-10-14 (decision taken 2026-10-08)

**Sprint:** Pre-Sprint-15 hardening

**Decision Makers:** Lead Software Architect, Security Reviewer, Product Owner

---

# Context

In v14.0.0, `DELETE /api/admin/users/{id}` removed the `users` row. The user's datasets,
dataset versions, pipeline runs, reports and AI jobs stayed in place with their owner set to
NULL, and their files stayed on disk (SEC-20). Those rows were visible to nobody and could be
removed by nobody.

The first fix purged the data, but on its own connection, committed **before** the user row
was deleted on another (P2-14). A failure in between left an account whose data was gone.
Audit rows and log lines still named the deleted person.

ROADMAP Sprint 15 Phase 4 listed "soft- vs hard-delete" as a decision still to make.

# Decision

**Deleting a user is a hard delete, done atomically.**

**What one transaction does.** `UserDataPurger.purge(user_id, expected_username, delete_account=True)`
runs a single database transaction that:

1. checks that `expected_username` matches the stored account, so a stale or mismatched id
   purges nothing;
2. deletes everything the user owns, children before parents:
   - `ai_reports` and `ai_jobs`;
   - `cleaning_executions` and `cleaning_configs`;
   - `dataset_versions`, then `datasets`;
   - `quality_reports`, `analytics_reports` and `reports`;
   - `pipeline_runs`;
   - `cleaning_policy_proposals`;
   - the user's `login_failures` rows;
3. pseudonymises the user's audit rows (`actor_username` and `details` become
   `deleted-user-<id>`; ids, types, times and outcomes are kept, see ADR-032);
4. deletes the `users` row;
5. commits. Any failure rolls back **all** of it: the account and every row remain, and the
   API answers 500.

**After the commit,** the user's artifact and report files are removed from disk. Removing a
file can fail, for example on a permissions error. When it does, the database is already
consistent and the orphan file is logged. `DATASET_RETENTION_DAYS` and
`scripts/purge_ownerless_data.py` also clean up orphans.

**Last admin.** The last active admin cannot be deleted or demoted. The check is an SQL count
taken under a lock (SEC-21).

**Ownerless rows** from before this change, or from explicit `--ownerless` CLI runs, are
counted and removed by `scripts/purge_ownerless_data.py` (dry-run by default).

**Soft delete was considered and rejected.** Deactivating instead of deleting is already
available: status `INACTIVE` or `SUSPENDED` blocks the account on its next request and keeps its
data. A tombstoned "deleted" state that still holds personal data would not satisfy an erasure
request, and would add a third state every query must filter.

# Consequences

- **Positive:**
  - Deletion is all-or-nothing.
  - Erasure requests can be honoured.
  - No unowned data accumulates.
  - The audit trail stays verifiable.
- **Negative:**
  - Deletion is irreversible. The Admin UI's Delete button stays disabled until an explicit
    "Confirm delete (removes all their data)" box is ticked.
  - Reports a deleted user produced are gone for everyone. That is correct while every resource
    is single-owner. If shared workspaces arrive, this ADR must be revisited.
- **ROADMAP:** Sprint 15 Phase 4 no longer needs the soft- vs hard-delete decision. Its delete
  work is the UI confirmation flow and verification against this ADR.

# Verification

- `tests/api/test_erasure_and_audit_chain.py`: account and data deleted together; an injected
  failure part-way leaves both; audit rows pseudonymised; ownerless rows counted and removed.
- `tests/api/test_admin_data_governance.py`: files removed; last-admin guard.

# Related ADRs

- ADR-024 — Enterprise Identity and Multi-User Architecture
- ADR-026 — Data Cleaning Governance and Lineage
- ADR-032 — Durable, Hash-Chained Audit Trail
