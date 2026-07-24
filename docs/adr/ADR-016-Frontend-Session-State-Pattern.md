# ADR-016 — Frontend Session State Pattern

**Status:** Accepted

**Date:** 2026-07-25

**Sprint:** Sprint 10 – Enterprise Streamlit Frontend

**Decision Makers:** Project Architecture Board

---

# Context

AnalystGPT Enterprise uses **Streamlit** as the presentation layer during Sprint 10.

Unlike traditional web frameworks, Streamlit reruns the entire application script whenever the user interacts with the interface.

Examples include:

- Clicking a button
- Uploading a dataset
- Selecting a report
- Changing navigation
- Filtering data

Without a persistent state management mechanism, every rerun would recreate the application from scratch, resulting in:

- Loss of uploaded datasets
- Reset navigation
- Disappearing dashboard context
- Inconsistent user experience

A lightweight mechanism for preserving temporary frontend state was therefore required.

---

# Problem Statement

The frontend requires temporary application state that survives Streamlit reruns while maintaining strict separation from backend business logic.

The solution must:

- Preserve navigation state.
- Preserve UI selections.
- Preserve uploaded dataset references.
- Avoid storing business logic.
- Avoid replacing the persistence layer.

---

# Decision

AnalystGPT Enterprise shall adopt **Streamlit Session State** as the exclusive mechanism for managing transient frontend state.

Session State shall be limited to presentation-related information only.

Business logic, analytics, persistence, and domain operations shall remain entirely outside Session State.

---

# Scope of Session State

Session State is intended to store only information required to maintain a consistent user interface.

Typical examples include:

```
current_page

uploaded_dataset

selected_report

backend_connected

dashboard_filters

selected_chart

theme_preference

last_uploaded_filename
```

These values exist only for the duration of the user's session.

---

# Data That Must Never Be Stored

Session State shall **not** contain:

- SQL queries
- Database connections
- Analytics results
- Cleaning algorithms
- Quality reports
- Reporting logic
- Machine Learning models
- Persistence objects
- Application services

These responsibilities belong to backend modules.

---

# Architecture

```
User Interaction

        │

        ▼

Streamlit

        │

        ▼

Session State

        │

        ▼

Views

        │

        ▼

Frontend Services

        │

        ▼

Application Layer

        │

        ▼

Business Modules
```

Session State exists only within the Presentation Layer.

---

# Responsibilities

## Session State

Responsible for:

- Current page
- Navigation
- UI selections
- Temporary display preferences
- Uploaded dataset reference
- User interface continuity

---

## Frontend Services

Responsible for:

- Loading backend data
- Formatting UI models
- Calling orchestrators
- Returning presentation-friendly responses

---

## Application Layer

Responsible for:

- Business rules
- Analytics
- Reporting
- Cleaning
- Quality Assessment

---

## Persistence Layer

Responsible for:

- SQLite
- PostgreSQL
- Long-term storage

---

# State Lifecycle

```
Application Starts

        │

        ▼

Session Created

        │

        ▼

User Uploads Dataset

        │

        ▼

Session Updated

        │

        ▼

Dashboard Uses Session

        │

        ▼

Reports Use Session

        │

        ▼

Session Ends

        │

        ▼

Session Destroyed
```

No persistent business information survives beyond the session.

---

# Design Principles

## Single Responsibility Principle

Session State stores presentation state only.

---

## Separation of Concerns

Presentation state remains separate from backend logic.

---

## Loose Coupling

Frontend pages depend only on Session State and Frontend Services.

Backend implementation remains hidden.

---

## High Cohesion

All transient UI information is managed centrally.

---

# Benefits

The adopted approach provides:

## Consistent Navigation

Users retain their current page after every interaction.

---

## Improved User Experience

Uploaded datasets remain available throughout the session.

Dashboard context is preserved.

---

## Simplicity

No external state management framework is required.

The implementation remains lightweight and fully integrated with Streamlit.

---

## Maintainability

Presentation state remains isolated from business logic.

Backend modules remain completely independent.

---

## Future Compatibility

The Session State pattern maps naturally to future React state management solutions such as:

- React Context
- Redux
- Zustand
- React Query

This minimises migration effort during Sprint 15.

---

# Trade-offs

## Advantages

- Simple implementation.
- Native Streamlit support.
- Lightweight.
- Easy debugging.
- Clear responsibility boundaries.
- Minimal overhead.

---

## Disadvantages

- State exists only during the browser session.
- Not shared between users.
- Not intended for persistence.

These limitations are acceptable because Session State is designed exclusively for temporary presentation data.

---

# Alternatives Considered

## Option 1 — Global Variables

**Rejected**

Reason:

- Unsafe.
- Shared across sessions.
- Poor scalability.
- Difficult testing.

---

## Option 2 — Database-backed UI State

**Rejected**

Reason:

- Excessive complexity.
- Unnecessary database traffic.
- Violates separation of concerns.

Persistent storage is already handled by the Persistence Layer.

---

## Option 3 — Local Files

**Rejected**

Reason:

- Slow.
- Difficult cleanup.
- Unsuitable for concurrent users.

---

## Option 4 — No State Management

**Rejected**

Reason:

Every Streamlit interaction would reset the application.

This would significantly degrade usability.

---

# Consequences

Following this decision:

- UI state remains isolated from backend logic.
- Navigation is preserved across reruns.
- Uploaded datasets remain available throughout a session.
- Frontend architecture remains lightweight.
- Backend architecture remains unchanged.
- React migration remains straightforward.

---

# Related ADRs

- ADR-006 — Enterprise Module Structure
- ADR-007 — Application Layer Orchestration
- ADR-008 — Persistence Layer Architecture
- ADR-009 — Database Abstraction Layer
- ADR-011 — REST API Architecture
- ADR-014 — Dashboard Service Pattern
- ADR-015 — Streamlit Frontend Architecture
- ADR-017 — Frontend Service Layer Pattern

---

# References

- Streamlit Documentation
- Clean Architecture — Robert C. Martin
- SOLID Principles
- Enterprise Application Architecture

---

# Decision Summary

AnalystGPT Enterprise adopts **Streamlit Session State** as the exclusive mechanism for managing temporary presentation state.

Session State is limited to user interface information such as navigation, dataset references, and display preferences.

Business logic, persistence, analytics, and reporting remain outside the Presentation Layer, preserving Clean Architecture principles and enabling future migration to a React-based frontend.