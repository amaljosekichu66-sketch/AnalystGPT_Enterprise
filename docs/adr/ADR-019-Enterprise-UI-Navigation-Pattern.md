# ADR-019 — Enterprise UI Navigation Pattern

**Status:** Accepted

**Date:** 2026-07-25

**Sprint:** Sprint 10 – Enterprise Streamlit Frontend

**Decision Makers:** Project Architecture Board

---

# Context

Sprint 10 introduced the first graphical user interface for AnalystGPT Enterprise.

As the application expanded beyond a single upload page, users required navigation between multiple functional areas including:

- Dashboard
- Upload
- Reports
- About

Future sprints will introduce additional pages, including:

- AI Insights
- Administration
- User Management
- Notifications
- System Monitoring
- Settings

A consistent navigation strategy was required that could scale with the application while remaining compatible with both the current Streamlit implementation and the planned React frontend in Sprint 15.

---

# Problem Statement

Without a standardized navigation architecture:

- Page routing becomes duplicated.
- Navigation logic spreads across multiple files.
- State management becomes inconsistent.
- User experience becomes fragmented.
- Migration to React requires significant redesign.

Navigation must remain centralized, predictable, and independent from business logic.

---

# Decision

Adopt a centralized navigation architecture driven by a single application entry point.

The navigation flow shall be:

```
Sidebar

↓

Session State

↓

Page Router

↓

View

↓

Components

↓

Frontend Services

↓

Application Layer
```

Navigation state shall be maintained using Streamlit Session State.

Each page shall expose a single public `render()` function.

The application entry point (`streamlit_app.py`) shall act as the sole router responsible for rendering pages.

---

# Navigation Architecture

```
                User

                 │

                 ▼

          Sidebar Navigation

                 │

                 ▼

      Streamlit Session State

                 │

                 ▼

        Frontend Page Router

                 │

      ┌──────────┼──────────┐

      ▼          ▼          ▼

 Dashboard     Upload     Reports

      │          │          │

      └──────────┼──────────┘

                 ▼

          Reusable Components

                 ▼

         Frontend Services

                 ▼

        Application Layer
```

---

# Navigation Principles

## Centralized Routing

Routing decisions shall exist only within the Streamlit entry point.

Individual pages shall never determine navigation.

---

## Stateless Views

Each view shall be independently renderable.

Views shall not assume previous navigation history.

---

## Session-Based Navigation

Current page selection shall be stored in Session State.

Example:

```
current_page

Dashboard

Upload

Reports

About
```

This ensures navigation persists across Streamlit reruns.

---

## Component Independence

Components shall never perform routing.

Components only render presentation elements supplied by views.

---

## Service Independence

Navigation shall never bypass the Frontend Service Layer.

Business operations remain independent from UI navigation.

---

# Responsibilities

## Sidebar

Responsible for:

- Displaying navigation controls.
- Updating current page.
- Displaying application status.
- Displaying backend connection state.

---

## Session State

Responsible for:

- Current page.
- Navigation persistence.
- User interface state.

Not responsible for:

- Business logic.
- Analytics.
- Database operations.

---

## Page Router

Responsible for:

- Selecting the active view.
- Handling invalid page requests.
- Displaying fallback pages.
- Delegating rendering.

---

## Views

Responsible for:

- Rendering page layout.
- Coordinating components.
- Calling frontend services.

Views never perform navigation.

---

# Benefits

The navigation architecture provides:

## Consistency

All pages behave identically.

---

## Scalability

New pages require only:

- New View
- Router registration
- Sidebar entry

No architectural modifications.

---

## Maintainability

Navigation logic exists in a single location.

Future updates become straightforward.

---

## Testability

Routing behaviour can be validated independently.

Views remain isolated.

---

## React Migration

Sprint 15 will replace the Streamlit router with React Router.

The backend architecture remains unchanged.

Only the Presentation Layer changes.

---

# Future React Mapping

Current implementation:

```
Sidebar

↓

Session State

↓

Page Router

↓

View
```

Future implementation:

```
React Sidebar

↓

React Router

↓

Route

↓

React Component
```

The overall navigation architecture remains unchanged.

---

# Trade-offs

## Advantages

- Simple navigation model.
- Clear dependency direction.
- Consistent user experience.
- Easy extension.
- React-ready architecture.

---

## Disadvantages

- Session State is Streamlit-specific.
- Browser refresh resets transient UI state.
- Limited compared with dedicated frontend routers.

These limitations are acceptable for the MVP.

---

# Alternatives Considered

## Option 1 — Multiple Independent Navigation Controls

Each page controls navigation independently.

**Rejected**

Reason:

- Inconsistent behaviour.
- Duplicate routing logic.
- Difficult maintenance.

---

## Option 2 — URL-Based Navigation

Navigation driven entirely by URL parameters.

**Rejected**

Reason:

- Unnecessary complexity for Streamlit MVP.
- Less intuitive implementation.
- React migration already planned.

---

## Option 3 — Direct Component Navigation

Components modify application state directly.

**Rejected**

Reason:

- Violates Separation of Concerns.
- Increases coupling.
- Makes testing more difficult.

---

# Consequences

Following this decision:

- Navigation remains centralized.
- Views remain independent.
- Components remain reusable.
- Services remain backend-focused.
- Business logic remains isolated.
- React migration becomes low risk.

The architecture supports continued expansion without structural redesign.

---

# Related ADRs

- ADR-006 — Enterprise Module Structure
- ADR-007 — Application Layer Orchestration
- ADR-011 — REST API Architecture
- ADR-014 — Dashboard Service Pattern
- ADR-015 — Streamlit Frontend Architecture
- ADR-016 — Frontend Session State Pattern
- ADR-017 — Frontend Service Layer Pattern

---

# References

- Robert C. Martin — *Clean Architecture*
- Streamlit Documentation
- React Router Documentation
- SOLID Design Principles

---

# Decision Summary

AnalystGPT Enterprise adopts a centralized navigation architecture in which:

- Navigation originates from a single sidebar.
- Session State maintains transient navigation state.
- The Streamlit application entry point serves as the sole router.
- Views remain independent and stateless.
- Components remain presentation-only.
- Backend services remain isolated from navigation concerns.

This architecture provides a scalable, maintainable, and enterprise-ready navigation model while ensuring a smooth transition to a React-based frontend in Sprint 15.