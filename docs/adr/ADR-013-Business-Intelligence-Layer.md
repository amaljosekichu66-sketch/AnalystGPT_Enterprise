# ADR-013

# Business Intelligence Integration Layer

**Status:** Accepted

**Date:** 23 July 2026

**Sprint:** Sprint 9

**Version:** v9.0.0

---

# Context

Sprint 8 introduced a REST API Layer that exposes the analytics
pipeline through standardized HTTP endpoints.

Although external clients could execute the pipeline and retrieve
results, the platform lacked a dedicated layer responsible for
producing dashboard-oriented responses suitable for Business
Intelligence platforms such as Power BI.

Generating dashboard responses directly inside the REST API Layer
would introduce presentation concerns into HTTP routing, while
implementing them inside the Analytics or Reporting modules would
violate their existing responsibilities.

A dedicated integration layer was required to preserve the existing
layered architecture while enabling external dashboard consumption.

---

# Decision

Introduce a dedicated **Business Intelligence Integration Layer**
positioned between the REST API Layer and the Application Layer.

The layer is responsible for:

- Dashboard orchestration
- Dashboard response generation
- Business Intelligence integration
- Transformation of reporting results into dashboard-ready models

The layer consists of:

- DashboardService
- DashboardSummary
- DashboardStatistics
- DashboardCorrelation
- DashboardDistribution
- DashboardCategorical

Business modules remain unchanged and unaware of Business Intelligence
concerns.

---

# Architecture

```text
Power BI Client
        │
        ▼
REST API Layer
        │
        ▼
Business Intelligence Layer
        │
        ▼
DashboardService
        │
        ▼
Application.run()
        │
        ▼
Business Modules
```

---

# Alternatives Considered

## Option 1

Generate dashboard responses inside the REST API Layer.

Rejected because:

- mixes HTTP and dashboard logic
- violates Separation of Concerns
- reduces maintainability

---

## Option 2

Generate dashboards inside ReportingManager.

Rejected because:

- Reporting becomes responsible for visualization
- tightly couples reporting with external integrations
- violates Single Responsibility Principle

---

## Option 3 (Accepted)

Introduce a dedicated Business Intelligence Layer.

Advantages:

- preserves layered architecture
- reusable across future BI platforms
- isolates integration concerns
- simplifies future frontend development

---

# Consequences

## Positive

- REST API remains thin
- Business modules remain unchanged
- Dashboard generation becomes reusable
- Future BI platforms can reuse the same services
- Stable module contracts preserved

## Negative

- Adds a new architectural layer
- Introduces additional response models

---

# Validation

Validated through:

- 98 / 98 Automated Tests
- SQLite Runtime Validation
- PostgreSQL Runtime Validation
- Swagger UI Validation
- OpenAPI Validation
- Power BI Endpoint Validation
- Stress Testing (~1,000,000 rows)

---

# Related Documents

- ARCHITECTURE.md
- PROJECT_STATE.md
- CHANGELOG.md
- PROJECT_JOURNAL.md
- ROADMAP.md

---

# Decision Summary

A dedicated Business Intelligence Integration Layer was introduced to
support dashboard-oriented APIs while preserving the enterprise
layered architecture and stable business module contracts.

---

**Decision:** Accepted

**Owner:** AnalystGPT Enterprise Architecture