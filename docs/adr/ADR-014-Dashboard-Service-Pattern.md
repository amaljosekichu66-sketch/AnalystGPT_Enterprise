# ADR-014

# Dashboard Service Pattern

**Status:** Accepted

**Date:** 23 July 2026

**Sprint:** Sprint 9

**Version:** v9.0.0

---

# Context

The Business Intelligence Layer requires a mechanism for exposing
dashboard-ready responses without exposing internal AnalyticsReport or
ReportingReport implementations.

Returning internal report models directly would tightly couple external
clients to internal business contracts and reduce flexibility for future
architectural changes.

A dedicated orchestration component was required to assemble dashboard
responses independently from REST API routing and business modules.

---

# Decision

Introduce **DashboardService** as the single orchestration component
responsible for Business Intelligence responses.

DashboardService:

- executes the analytics pipeline through the Application Layer
- extracts reporting information
- transforms results into dashboard models
- returns Power BI-ready responses

REST API routes communicate only with DashboardService.

DashboardService communicates only with the Application Layer.

---

# Architecture

```text
REST API Route
       │
       ▼
DashboardService
       │
       ▼
Application.run()
       │
       ▼
ReportingReport
       │
       ▼
Dashboard Models
```

---

# Responsibilities

DashboardService owns:

- dashboard generation
- summary extraction
- descriptive statistics
- correlation responses
- distribution responses
- categorical responses
- report aggregation

DashboardService must not:

- perform analytics
- execute SQL
- implement HTTP routing
- modify reporting results

---

# Alternatives Considered

## Option 1

Return AnalyticsReport directly.

Rejected because:

- exposes internal implementation
- tightly couples clients to business modules

---

## Option 2

Return ReportingReport directly.

Rejected because:

- reporting model is not optimized for dashboard consumption
- future reporting changes could break external integrations

---

## Option 3 (Accepted)

Introduce DashboardService.

Advantages:

- reusable
- independent
- maintainable
- hides internal report structures
- supports future dashboard technologies

---

# Consequences

## Positive

- clean separation of responsibilities
- reusable dashboard generation
- stable external API contracts
- simplified REST routes
- future Streamlit integration can reuse DashboardService

## Negative

- additional service layer
- additional response models

---

# Validation

Validated through:

- Dashboard endpoint
- Summary endpoint
- Statistics endpoint
- Correlation endpoint
- Distribution endpoint
- Categorical endpoint
- Report endpoint
- Pipeline endpoint

All validations completed successfully.

---

# Related Documents

- ARCHITECTURE.md
- PROJECT_STATE.md
- CHANGELOG.md
- Sprint 9 Release Report

---

# Decision Summary

DashboardService was introduced as the dedicated orchestration
component for Business Intelligence responses, ensuring dashboard
generation remains independent of REST API routing and business
modules while preserving stable architecture and reusable services.

---

**Decision:** Accepted

**Owner:** AnalystGPT Enterprise Architecture