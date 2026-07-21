# ADR-008 — Persistence Layer Architecture

**Status:** Accepted

**Date:** 21 July 2026

---

# Context

By the completion of Sprint 5.5, AnalystGPT Enterprise had achieved a
stable enterprise architecture consisting of the following business
pipeline:

```text
Upload
    ↓
Cleaning
    ↓
Quality
    ↓
Analytics
    ↓
Reporting
```

Although the pipeline successfully produced analytical results and
business reports, no execution metadata was retained after the
application finished.

Pipeline executions, dataset information, quality metrics,
analytics summaries, and generated reports existed only in memory.

This prevented:

- Historical pipeline tracking
- Persistent execution records
- Future dashboard integration
- Database-driven reporting
- Enterprise auditability

The project therefore required a dedicated persistence architecture.

---

# Decision

Introduce a dedicated Persistence Layer responsible for all database
operations.

Persistence responsibilities shall remain completely separate from
business logic.

Business modules will continue producing their own report objects.

The Application layer will coordinate persistence through a single
PersistenceManager after each business stage completes.

---

# Architecture

```text
Application
      │
      ▼
PersistenceManager
      │
      ▼
Repository Layer
      │
      ▼
SQLite Database
```

The Persistence Layer becomes the only component responsible for
database interaction.

---

# Repository Pattern

Persistence operations are implemented using the Repository Pattern.

Each repository owns exactly one database entity.

Current repositories include:

- PipelineRunRepository
- DatasetRepository
- QualityRepository
- AnalyticsRepository
- ReportRepository

Repositories isolate SQL from the Application layer and business
modules.

---

# Responsibilities

PersistenceManager coordinates:

- Database initialization
- Schema initialization
- Pipeline lifecycle
- Dataset persistence
- Quality persistence
- Analytics persistence
- Report persistence
- Failure handling
- Database shutdown

Repositories perform:

- SQL execution
- CRUD operations
- Entity persistence

---

# Consequences

## Positive

- Separation of business logic and persistence
- Cleaner Application layer
- Centralized database access
- Easier automated testing
- Reduced coupling
- Simplified future database migration
- Foundation for enterprise reporting
- Foundation for dashboards
- Foundation for REST APIs

## Negative

- Additional architectural layer
- More classes to maintain
- Additional abstraction over direct SQL

These trade-offs were considered acceptable given the project's
enterprise objectives.

---

# Alternatives Considered

## Direct SQLite calls inside Application

Rejected.

This approach would tightly couple orchestration with persistence and
make future database migration significantly more difficult.

---

## Database logic inside business modules

Rejected.

Business modules should remain responsible only for business
processing and report generation.

Persistence is an infrastructure concern.

---

## ORM-based implementation

Rejected.

Introducing an ORM at this stage would increase project complexity and
reduce visibility into SQL fundamentals.

A lightweight Repository Pattern better supports the educational and
architectural goals of the project.

---

# Future Impact

This decision establishes the architectural foundation for:

- PostgreSQL integration
- Database abstraction
- REST APIs
- Dashboard backends
- AI execution history
- Multi-database support

Future persistence implementations should extend the Repository Layer
without affecting business modules.

---

# Related Components

- PersistenceManager
- PersistenceResult
- DatabaseManager
- SchemaManager
- PipelineRunRepository
- DatasetRepository
- QualityRepository
- AnalyticsRepository
- ReportRepository

---

# Related Documents

- ADR-003 — Dependency Direction
- ADR-006 — Enterprise Module Structure
- ADR-007 — Application Layer Orchestration
- ARCHITECTURE.md
- PROJECT_STATE.md
- ROADMAP.md

---

# Decision Summary

AnalystGPT Enterprise adopts a dedicated Persistence Layer built around
a centralized PersistenceManager and Repository Pattern.

This architecture separates persistence from business logic,
preserves modularity, and provides the foundation for future database,
API, dashboard, and enterprise platform capabilities.

---

**Decision:** Accepted