# ADR-026 — Data Cleaning Governance and Lineage

**Status:** Proposed (Planned for Sprint 14)

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
