# ADR-017 — Frontend Service Layer Pattern

**Status:** Accepted

> **Re-baseline note (2026-09-28).** This ADR's text schedules the React frontend for
> "Sprint 15". That is superseded: read every "Sprint 15" below as **Sprint 17**.
> Sequencing is defined in ROADMAP.md: Sprint 15 — Enterprise Stabilization, Governance
> Completion & Product/UX Remediation (no React work) → Sprint 16 — AI Provider Abstraction &
> Complete React Readiness (final readiness audit; React architecture defined, not built) →
> **Sprint 17 — React Migration & Modern Presentation Layer** (React + TypeScript implemented).
> The decision recorded here is unchanged and remains in force for the Streamlit
> presentation layer; the React-side design is decided in the Sprint 16 architecture ADR.

**Date:** 2026-07-25

**Sprint:** Sprint 10 – Enterprise Streamlit Frontend

**Decision Makers:** Project Architecture Board

---

# Context

Sprint 10 introduced the first enterprise frontend for AnalystGPT Enterprise.

The application provides multiple pages including:

- Dashboard
- Upload
- Reports
- About

Each page requires access to backend functionality such as:

- Dataset metadata
- Pipeline status
- Report information
- Analytics summaries
- Export requests
- Session information

Without a dedicated communication layer, frontend pages would need to directly interact with backend managers or REST APIs.

This would violate the architectural principles established throughout previous sprints.

---

# Problem Statement

Allowing frontend pages to directly communicate with backend modules introduces several architectural issues.

Examples include:

- Tight coupling between UI and backend implementation.
- Duplicate business logic.
- Reduced testability.
- Difficult migration to React.
- Frequent changes across multiple frontend pages when backend interfaces evolve.

The frontend requires a stable abstraction layer that isolates presentation from business implementation.

---

# Decision

Introduce a dedicated **Frontend Service Layer** responsible for all communication between the presentation layer and backend architecture.

The service layer shall:

- Receive requests from Views.
- Coordinate communication with backend systems.
- Transform backend responses into presentation models.
- Handle frontend-specific exceptions.
- Shield UI components from implementation changes.

Views shall never directly access:

- Managers
- Persistence Layer
- Database Connections
- Analytics Modules
- Reporting Modules

All communication must pass through a Frontend Service.

---

# Frontend Service Responsibilities

Frontend Services shall perform:

- Backend communication
- Response transformation
- Data formatting
- Error translation
- Session coordination
- UI-specific preprocessing

Frontend Services shall NOT perform:

- Analytics
- Cleaning
- Quality Assessment
- Report Generation
- SQL Queries
- Persistence
- Business Rules

Those responsibilities remain inside the Application Layer.

---

# Current Service Modules

```
src/frontend/services/

api_client.py

dashboard_service.py

report_service.py

session_manager.py
```

---

## dashboard_service.py

Responsibilities

- Retrieve dashboard information.
- Aggregate presentation data.
- Prepare dashboard metrics.

---

## report_service.py

Responsibilities

- Retrieve report information.
- Submit export requests.
- Format reporting responses.

---

## session_manager.py

Responsibilities

- Manage frontend session state.
- Track current dataset.
- Coordinate page navigation state.

---

## api_client.py

Responsibilities

- Abstract REST communication.
- Provide reusable API methods.
- Isolate HTTP implementation.

---

# Dependency Direction

The dependency chain is strictly enforced.

```
Browser

↓

Streamlit

↓

Views

↓

Frontend Services

↓

Application Layer

↓

Managers

↓

Persistence Layer
```

Dependencies never move upward.

Business modules never depend on presentation.

---

# Architectural Flow

Example:

Dashboard Page

```
Dashboard View

        │

        ▼

Dashboard Service

        │

        ▼

Dashboard Orchestrator

        │

        ▼

Analytics Manager

        │

        ▼

Database
```

Example:

Report Export

```
Reports View

       │

       ▼

Report Service

       │

       ▼

Reporting Orchestrator

       │

       ▼

Reporting Manager

       │

       ▼

Text Exporter
```

---

# Service Design Principles

Every Frontend Service follows the same engineering principles.

## Single Responsibility Principle

Each service performs one well-defined responsibility.

Examples:

Dashboard Service

↓

Dashboard operations

Report Service

↓

Reporting operations

---

## Open/Closed Principle

New backend functionality is introduced through additional services without modifying existing views.

---

## Dependency Inversion

Views depend on service interfaces rather than backend implementations.

---

## Separation of Concerns

Presentation remains independent from:

- Analytics
- Cleaning
- Quality
- Reporting
- Persistence

---

# Benefits

## Loose Coupling

UI pages remain independent of backend changes.

---

## Maintainability

Business logic modifications do not require UI redesign.

---

## Testability

Frontend services can be mocked during testing.

Views can be tested independently.

---

## Scalability

Additional services may be introduced for:

- AI Insights
- Authentication
- Notifications
- Administration
- Scheduling

without modifying existing frontend pages.

---

## React Migration

Sprint 15 replaces Streamlit Views with React components.

Because communication already occurs through Frontend Services, the backend remains unchanged.

Only the presentation layer changes.

---

# Trade-offs

## Advantages

- Clear architecture.
- High cohesion.
- Low coupling.
- Easier testing.
- Better scalability.
- Enterprise design.

---

## Disadvantages

- Additional abstraction.
- More project files.
- Slightly increased learning curve.

These disadvantages are acceptable considering the long-term maintainability improvements.

---

# Alternatives Considered

## Option 1

Views communicate directly with Managers.

**Rejected**

Reason:

Violates layered architecture.

---

## Option 2

Views perform REST API calls directly.

**Rejected**

Reason:

Duplicates networking logic.

Reduces maintainability.

---

## Option 3

Business logic implemented inside Views.

**Rejected**

Reason:

Violates Single Responsibility Principle.

Creates tightly coupled presentation code.

---

## Option 4

Components communicate with backend.

**Rejected**

Reason:

Components must remain reusable presentation elements.

Backend communication belongs to Services.

---

# Consequences

Following this decision:

- Views remain lightweight.
- Components remain presentation-only.
- Backend interfaces remain stable.
- Frontend code becomes easier to maintain.
- React migration requires minimal backend modification.
- Testing becomes significantly simpler.

---

# Architecture Diagram

```
                Browser

                   │

                   ▼

             Streamlit Views

                   │

                   ▼

          Frontend Services

      ┌──────────┼──────────┐

      ▼          ▼          ▼

 Dashboard   Report     API Client

   Service    Service

      │          │

      └──────┬───┘

             ▼

      Application Layer

             ▼

     Domain Managers

             ▼

 Persistence Layer

 SQLite / PostgreSQL
```

---

# Related ADRs

- ADR-006 — Enterprise Module Structure
- ADR-007 — Application Layer Orchestration
- ADR-009 — Database Abstraction Layer
- ADR-011 — REST API Architecture
- ADR-014 — Dashboard Service Pattern
- ADR-015 — Streamlit Frontend Architecture
- ADR-016 — Frontend Session State Pattern
- ADR-018 — Report Export Architecture

---

# References

- Robert C. Martin — Clean Architecture
- Robert C. Martin — Agile Software Development
- SOLID Design Principles
- Layered Architecture Pattern
- Enterprise Application Architecture

---

# Decision Summary

AnalystGPT Enterprise adopts a dedicated **Frontend Service Layer** that mediates all communication between the Streamlit presentation layer and backend architecture.

Frontend Views communicate exclusively with Frontend Services.

Frontend Services coordinate backend operations while preserving Clean Architecture principles.

This decision improves maintainability, testability, scalability, and establishes a stable abstraction that enables seamless migration to the planned React frontend in Sprint 15.