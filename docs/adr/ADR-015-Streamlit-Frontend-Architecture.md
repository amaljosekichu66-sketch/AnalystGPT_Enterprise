# ADR-015 — Streamlit Frontend Architecture

**Status:** Accepted

**Date:** 2026-07-25

**Sprint:** Sprint 10 – Enterprise Streamlit Frontend

**Decision Makers:** Project Architecture Board

---

# Context

By the completion of Sprint 9, AnalystGPT Enterprise had evolved into a mature backend analytics platform comprising:

- Upload Module
- Cleaning Module
- Quality Assessment Module
- Analytics Module
- Reporting Module
- SQLite Persistence Layer
- PostgreSQL Persistence Layer
- REST API
- Power BI Integration

Although the backend architecture was complete, interaction with the system remained primarily through command-line execution and REST endpoints. This significantly limited usability for business users, analysts, recruiters evaluating the project, and future stakeholders.

Sprint 10 introduced the first graphical user interface (GUI) for AnalystGPT Enterprise. The chosen frontend framework needed to satisfy several engineering constraints:

- Rapid implementation.
- Minimal infrastructure overhead.
- Compatibility with Python.
- Tight integration with the existing Application Layer.
- Easy migration to a future React frontend planned for Sprint 15.

The frontend was therefore considered a presentation layer rather than a replacement for the existing architecture.

---

# Problem Statement

The introduction of a frontend presented several architectural risks:

- Business logic could migrate into UI pages.
- Database access could bypass the Application Layer.
- Duplicate orchestration logic could appear in frontend components.
- Future migration to React could require extensive backend redesign.

Without clear architectural boundaries, the frontend could become tightly coupled to backend implementations, reducing maintainability and scalability.

A frontend architecture was therefore required that:

- Preserved Clean Architecture principles.
- Maintained dependency direction.
- Prevented business logic leakage.
- Supported future frontend replacement.

---

# Decision

AnalystGPT Enterprise shall adopt **Streamlit** as the presentation framework for the Minimum Viable Product (MVP).

The Streamlit frontend shall operate exclusively as the Presentation Layer.

The frontend shall be organised into distinct modules:

```
src/frontend/

├── components/
├── config/
├── services/
├── theme/
├── views/
└── streamlit_app.py
```

Each layer has a single responsibility.

---

## Views

Views represent complete application pages.

Examples:

- Dashboard
- Upload
- Reports
- About

Responsibilities:

- Arrange page layout.
- Coordinate UI components.
- Delegate backend communication to frontend services.

Views shall NOT contain:

- Analytics
- Data cleaning
- Database access
- Reporting logic
- Quality assessment

---

## Components

Components are reusable presentation elements.

Examples:

- KPI Cards
- Dataset Summary
- Charts
- Pipeline Status
- Footer
- Sidebar
- Report Preview

Responsibilities:

- Render UI.
- Display supplied data.
- Remain stateless whenever practical.

Components must never communicate directly with backend modules.

---

## Frontend Services

Frontend services provide the communication layer between the UI and the Application Layer.

Examples:

- Dashboard Service
- Report Service
- Session Manager
- API Client

Responsibilities:

- Request backend operations.
- Transform backend responses into presentation-friendly structures.
- Isolate UI from backend implementation details.

---

## Theme

The theme module centralises:

- Colours
- Typography
- Icons
- Spacing
- Shadows

This ensures visual consistency across the application while preparing for future React migration.

---

## Configuration

Frontend configuration stores:

- Page names
- Navigation constants
- UI configuration
- Display settings

Configuration values remain separate from implementation logic.

---

# Architectural Principles

The frontend follows the same engineering principles established throughout AnalystGPT Enterprise.

## Single Responsibility Principle (SRP)

Each module has one clearly defined responsibility.

---

## Dependency Inversion

Dependencies flow downward.

```
Views

↓

Components

↓

Frontend Services

↓

Application Layer

↓

Managers

↓

Persistence Layer
```

Business logic never depends on presentation.

---

## Separation of Concerns

Presentation concerns remain independent from:

- Analytics
- Cleaning
- Quality assessment
- Reporting
- Persistence

---

## High Cohesion

Each module groups closely related functionality.

Examples:

Dashboard functionality remains within Dashboard modules.

Reporting functionality remains within Reporting modules.

---

## Loose Coupling

Views communicate through well-defined service interfaces.

Backend implementations may change without requiring UI redesign.

---

# Architecture Diagram

```
                    Browser

                       │

                       ▼

              Streamlit Application

                       │

        ┌──────────────┴──────────────┐

        ▼                             ▼

      Views                     Components

        │                             │

        └──────────────┬──────────────┘

                       ▼

              Frontend Services

                       ▼

             Application Layer

                       ▼

         Domain Managers / Modules

                       ▼

             Persistence Layer

             SQLite / PostgreSQL
```

---

# Benefits

The selected architecture provides:

## Maintainability

Presentation code remains isolated from backend implementation.

---

## Testability

Views and services can be tested independently.

Business logic remains fully testable without the frontend.

---

## Scalability

Additional pages can be introduced without affecting existing modules.

Examples:

- AI Insights
- Administration
- User Management
- Notifications

---

## Enterprise Readiness

The architecture resembles enterprise applications rather than tutorial-style Streamlit projects.

---

## Future React Migration

The separation between presentation and business logic enables replacement of the Streamlit frontend without modifying backend modules.

Sprint 15 will introduce a React frontend that consumes the same service interfaces and REST APIs.

---

# Trade-offs

## Advantages

- Rapid MVP development.
- Strong architectural boundaries.
- Reduced coupling.
- High code reuse.
- Simplified testing.
- Clear migration path.

---

## Disadvantages

- Additional abstraction layers.
- Slight increase in project complexity.
- More files compared with a monolithic Streamlit application.

These trade-offs are acceptable because they significantly improve long-term maintainability.

---

# Alternatives Considered

## Option 1 — Monolithic Streamlit Application

All code contained within Streamlit pages.

**Rejected**

Reason:

- Violates SRP.
- High coupling.
- Poor maintainability.

---

## Option 2 — Direct Database Access from Streamlit

Views query SQLite/PostgreSQL directly.

**Rejected**

Reason:

- Breaks dependency direction.
- Introduces security concerns.
- Couples presentation to persistence.

---

## Option 3 — Immediate React Frontend

Replace Streamlit with React during Sprint 10.

**Rejected**

Reason:

- Higher development effort.
- Delays MVP.
- Reduces focus on backend completion.

React remains scheduled for Sprint 15.

---

# Consequences

Following this decision:

- Streamlit serves exclusively as the Presentation Layer.
- Business logic remains within backend modules.
- Frontend services mediate all communication.
- Backend architecture remains unchanged.
- React migration becomes significantly simpler.

This decision preserves architectural integrity while enabling rapid delivery of a professional enterprise interface.

---

# Related ADRs

- ADR-006 — Enterprise Module Structure
- ADR-007 — Application Layer Orchestration
- ADR-008 — Persistence Layer Architecture
- ADR-009 — Database Abstraction Layer
- ADR-011 — REST API Architecture
- ADR-014 — Dashboard Service Pattern
- ADR-016 — Frontend Session State Pattern
- ADR-017 — Frontend Service Layer Pattern

---

# References

- Robert C. Martin — *Clean Architecture*
- Robert C. Martin — *Agile Software Development: Principles, Patterns, and Practices*
- Streamlit Documentation
- SOLID Design Principles

---

# Decision Summary

AnalystGPT Enterprise adopts a layered Streamlit frontend architecture in which:

- Streamlit provides the presentation layer.
- Views coordinate page rendering.
- Components render reusable UI elements.
- Frontend services mediate communication with the backend.
- Business logic remains exclusively within the Application Layer.
- The architecture preserves Clean Architecture principles while enabling a low-risk migration to a React frontend in Sprint 15.

This decision establishes a maintainable, scalable, and enterprise-oriented frontend architecture without compromising the integrity of the existing backend.