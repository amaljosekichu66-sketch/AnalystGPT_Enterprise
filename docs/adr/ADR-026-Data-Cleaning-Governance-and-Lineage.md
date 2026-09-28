# ADR-026 — Data Cleaning Governance and Lineage

**Status:** ✅ **Accepted** — implemented in Sprint 14 (v14.0.0 prepared; not yet tagged or merged to `main`)

> Implemented in `src/governance/` (policies, preview service, governance service, custom registry), `src/storage/artifact_store.py`, `src/database/repositories/cleaning_execution_repository.py`, `src/database/repositories/dataset_version_repository.py`, and the `/api/governance/*` routes.
>
> This ADR was authored as *Proposed (Planned for Sprint 14)*. Sprint 14 is implemented
> and the decision it records is in force; the status is promoted accordingly. The
> decision text below is unchanged.
>
> **Re-baseline note (ROADMAP.md, Sprints 15–17).** Sprint 15 — Enterprise Stabilization,
> Governance Completion & Product/UX Remediation → Sprint 16 — AI Provider Abstraction &
> Complete React Readiness → Sprint 17 — React Migration. The "React Migration Readiness"
> in the Sprint line below refers to the Sprint 14 *initial* foundation; the definitive
> readiness gate is Sprint 16.
>
> *Impact on later sprints.* The governance components are **implemented and tested but not
> verified end-to-end**: the preview → approval/modification/rejection → persistence →
> execution → lineage workflow has not been proven through the real API/frontend path and is
> reported as not functioning as intended. Proving and remediating it is **Sprint 15 Phase 2**,
> fixed at the backend root cause, not with a frontend workaround. This ADR's decision stands;
> Sprint 15 may amend it only through a follow-up ADR if the audit shows the design itself is at fault.

**Date:** 2026-08-15

**Sprint:** Sprint 14 — UX Stabilization, Performance, Data Governance & React Migration Readiness

**Decision Makers:** Lead Software Architect, Engineering Program Manager

---

# Context

AnalystGPT Enterprise provides automated data cleaning (column renaming, type coercion, missing value imputation, duplicate removal, text trimming). In earlier sprints, data cleaning executed automatically during pipeline ingestion, silently transforming or dropping rows before downstream quality assessment and reporting.

In enterprise analytical environments, automated data alteration without governance poses significant risks:
- Analysts cannot audit why certain records were excluded.
- Destructive operations (e.g. dropping rows with missing values) alter dataset statistical distributions without analyst approval.
- Downstream consumers lack traceability regarding dataset transformations.

---

# Problem Statement

1. **Silent Data Loss**: Dropping rows or imputing values without provenance obscures original dataset quality defects.
2. **Lack of Reproducibility**: Downstream analytical findings cannot be verified against the exact transformations applied without immutable source datasets and policy records.
3. **Rigid Cleaning Policies**: Different business domains require different missing-value treatments (e.g., preserving NULLs vs imputing means vs dropping).

---

# Decision

1. **Immutable Raw Dataset Storage**:
   The uploaded source dataset shall be preserved immutably using a storage abstraction with SHA-256 content hashing and versioning metadata persisted in the database.

2. **Separated Cleaned Analytical Dataset**:
   The cleaned analytical dataset shall be maintained separately from the raw dataset.

3. **Configurable Missing-Value Policies**:
   Introduce declarative, domain-configurable cleaning policies:
   - `PRESERVE_NULLS`: Leave missing values intact.
   - `DROP_ROWS`: Remove rows exceeding missingness criteria.
   - `DROP_COLUMNS`: Drop columns with missing values above threshold (e.g. > 50%).
   - `IMPUTE_NUMERIC`: Mean, median, or mode substitution.
   - `IMPUTE_CATEGORICAL`: Mode or constant ("Unknown") substitution.

4. **Cleaning Preview & Approval Workflow**:
   Introduce an explicit pipeline stage allowing analysts to review a transformation impact assessment (rows affected, columns altered, quality delta) before committing destructive operations.

5. **End-to-End Data Lineage & Provenance**:
   Persist cleaning configuration (policy version, parameters) with every pipeline run, generating before/after data-quality metrics (completeness, validity, consistency).

---

# Architectural Lineage Model

```text
Original Source File (CSV/Excel/JSON)
         │
         ▼
Raw Dataset Version (Immutable + SHA-256 Hash)
         │
         ▼
Cleaning Configuration Policy (Versioned & Recorded)
         │
         ▼
Cleaning Execution & Impact Assessment
         │
         ▼
Cleaned Analytical Dataset
         │
         ▼
Pipeline Run (Recorded Quality Delta)
         ├── Quality Report (Before vs After)
         ├── Analytics Report
         ├── Structured Reports
         └── AI Insights
```

---

# Consequences

### Positive
- **Full Traceability**: Complete audit trail from raw source data to AI narrative generation.
- **Enterprise Governance**: Eliminates silent data loss; empowers analysts to choose appropriate cleaning policies.
- **Reproducibility**: Any analytical result can be reproduced from the raw dataset hash and recorded cleaning policy.

### Negative / Trade-offs
- Increased storage footprint from storing raw and cleaned datasets separately.
- Additional database entities for cleaning policies and lineage metadata.

---

# Related ADRs

- ADR-002 — Cleaning Module Architecture
- ADR-003 — Quality Assessment Module
- ADR-006 — Persistence Architecture
- ADR-024 — Enterprise Identity and Multi-User Architecture
