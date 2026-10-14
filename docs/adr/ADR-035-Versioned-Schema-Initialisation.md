# ADR-035 — Versioned Schema Initialisation (no migration framework yet)

**Status:** ✅ **Accepted** — implemented on `pre-sprint-15-hardening`, released in v14.1.0

**Date:** 2026-10-14

**Sprint:** Pre-Sprint-15 hardening

**Decision Makers:** Lead Software Architect

---

# Context

`SchemaManager.initialize_schema()` ran the **whole** DDL every time any persistence session
started: every pipeline run, every audit write, every throttle lookup. On PostgreSQL that
included `ALTER TABLE … ADD COLUMN IF NOT EXISTS`, which takes an `ACCESS EXCLUSIVE` lock even
when the column already exists. Nothing recorded which schema a database had. Concurrency
(B-03) had been proven on SQLite only (P2-16).

The options were Alembic (a full migration framework) or a version marker on the existing,
idempotent DDL.

# Decision

**Keep the single, idempotent DDL in `SchemaManager`, and record the version applied.**

- **Version marker.** `SCHEMA_VERSION` (now 15) is written to a one-row `schema_version` table
  at the end of a successful migration. `initialize_schema()` reads it first. A current database
  costs **one SELECT and no DDL**; a missing or older version runs the DDL once.
- **Locking on PostgreSQL.** The migration takes `pg_advisory_xact_lock`, then re-reads the
  version inside the lock. Of several processes starting together, one migrates and the others
  find the work done. Column additions look in `information_schema` before issuing `ALTER`.
- **Transactions.** The whole migration is one transaction (ADR-022 / B-06): it applies
  completely or not at all.
- **Guard against stale versions.** A test pins a fingerprint of the DDL methods to
  `SCHEMA_VERSION`. Changing the DDL without bumping the version fails CI, because a forgotten
  bump would mean existing databases never receive the change.
- **Changes stay additive:** new tables, new nullable columns, new indexes.

# Consequences

- **Positive:** Request paths no longer run DDL or take table locks. Startup is safe under
  concurrency. There is no new dependency.
- **Negative:** There are no down-migrations, and no data migrations beyond what idempotent DDL
  can express. Columns added after a table was created carry no foreign key on SQLite.
  Ownership integrity is enforced by the code and the purge, not by the database.
- **Revisit when** a change cannot be additive: a rename, a type change, a backfill, or a
  constraint on existing data. At that point adopt Alembic, starting from the schema at the then
  current `SCHEMA_VERSION`.

# Verification

- `tests/database/test_schema_manager_migrations.py`: a current database runs no DDL; the
  version is recorded; the fingerprint guard; legacy upgrade.
- `tests/integration/test_postgresql_schema.py` and `test_postgresql_concurrency.py`, run by the
  `postgres` CI job against PostgreSQL 16: fresh, idempotent, failure rollback, legacy upgrade,
  8 simultaneous initialisations, and 2 users × 3 overlapped pipeline runs with ownership
  checked.

# Related ADRs

- ADR-022 — Containerization and Multi-Service Topology
- ADR-023 — Continuous Integration with GitHub Actions
