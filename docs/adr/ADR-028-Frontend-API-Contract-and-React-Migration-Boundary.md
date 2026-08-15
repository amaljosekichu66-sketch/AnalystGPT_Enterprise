# ADR-028 — Frontend API Contract and React Migration Boundary

**Status:** Proposed (Planned for Sprint 14)

**Date:** 2026-08-15

**Sprint:** Sprint 14 — UX Stabilization, Performance, Data Governance & React Migration Readiness

**Decision Makers:** Lead Software Architect, Engineering Program Manager

---

# Context

AnalystGPT Enterprise was designed with a layered architecture where the Streamlit user interface (Sprint 10) acts as an MVP presentation layer. Sprint 15 is scheduled for the full migration to a modern, production-grade React presentation layer.

To execute this migration without backend disruption or architectural regressions, Sprint 14 must establish strict frontend-backend service boundaries, freeze OpenAPI contracts, and ensure zero business logic resides inside Streamlit components.

---

# Problem Statement

If the frontend components communicate directly with application layer internals, depend on Streamlit-specific session magic, or lack formalized API contracts:
- React developers will face ambiguous backend interfaces.
- The migration will require backend refactoring.
- Parity between Streamlit and React during coexistence will be impossible to verify.

---

# Decision

1. **OpenAPI 3.1 Contract Freeze**:
   The FastAPI REST API shall serve as the sole, authoritative contract boundary for all frontend interactions. All endpoints, schemas, parameters, and error responses will be frozen and verified via automated contract tests.

2. **Frontend-Independent Service Interfaces**:
   All presentation logic must interact with backend APIs strictly through technology-neutral service interfaces:
   - `AuthService` (login, registration, user profile, logout, session state)
   - `DashboardService` (summary metrics, charts, distributions, correlations)
   - `ReportService` (report listings, details, exports)
   - `AIInsightService` (job status polling, insight retrieval)
   - `UploadService` (file validation, ingestion dispatch, cleaning preview)
   - `AdminService` (user management, status/role updates, audit logs)

3. **Zero Business Logic in Presentation Components**:
   Streamlit views and components are restricted to presentation-only logic. All data transformation, aggregation, and business rules remain strictly in the Application and Business layers.

4. **Coexistence and Drop-In Replacement**:
   During Sprint 15, the React application will consume the identical REST API endpoints. Both Streamlit and React frontends will be capable of running concurrently against the same backend services without conflicts.

---

# Architectural Boundary

```text
Streamlit Frontend (MVP)           React Frontend (Sprint 15)
       │                                     │
       └───────────────────┬─────────────────┘
                           │
                           ▼
             Frontend Service Layer (Typed)
              (Auth, Dashboard, Reports, AI)
                           │
                           ▼
          ═════════════════════════════════════
          OpenAPI 3.1 REST API Contract Boundary
          ═════════════════════════════════════
                           │
                           ▼
                   FastAPI Application
                           │
                           ▼
                   Application Layer
```

---

# Consequences

### Positive
- **Seamless Migration**: React development can proceed independently against stable, mockable OpenAPI specifications.
- **Testability**: API contract tests guarantee that backend changes never break frontend clients.
- **Architectural Purity**: Clean separation between presentation concerns and application core.

### Negative / Trade-offs
- Strict discipline required to prevent shortcuts or embedding domain logic in UI components.

---

# Related ADRs

- ADR-011 — REST API Architecture
- ADR-015 — Streamlit Frontend Architecture
- ADR-017 — Frontend Service Layer Pattern
- ADR-024 — Enterprise Identity and Multi-User Architecture
