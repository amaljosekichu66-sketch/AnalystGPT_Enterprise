# ADR-010 — Runtime Database Selection

## Status

Accepted

---

## Date

22 July 2026

---

## Context

After introducing support for multiple database engines during Sprint 7,
the application required a mechanism for selecting the active database
implementation without modifying application or business logic.

Database selection should remain an infrastructure concern and should be
controlled through centralized configuration rather than code changes.

The solution needed to support future expansion to additional database
engines while preserving the existing architecture.

---

## Decision

Introduce a dedicated `ConnectionFactory` responsible for creating the
appropriate `DatabaseConnection` implementation at runtime.

Database selection is controlled through centralized configuration.

Current supported engines are:

- SQLite
- PostgreSQL

Application startup requests a connection from the factory, while all
remaining components depend only on the `DatabaseConnection` abstraction.

No business module is aware of the selected database engine.

---

## Alternatives Considered

### Instantiate database implementations directly

Rejected.

This would tightly couple application startup to specific database
implementations and reduce extensibility.

---

### Allow repositories to choose the database

Rejected.

Repositories should operate only on an existing connection and should
not be responsible for infrastructure creation.

---

### Create separate application entry points

Rejected.

Maintaining multiple application startup paths would duplicate
configuration logic and complicate future maintenance.

---

## Consequences

### Positive

- Centralizes database creation.
- Keeps infrastructure configuration in one location.
- Simplifies future database additions.
- Preserves dependency inversion.
- Eliminates database-specific logic from business modules.
- Reduces application startup complexity.

### Negative

- Adds one additional infrastructure component.
- Requires configuration validation during application startup.

---

## Architectural Impact

Runtime database selection becomes an infrastructure responsibility.

Future database engines should be integrated by:

1. Implementing the `DatabaseConnection` interface.
2. Extending `ConnectionFactory`.
3. Adding configuration values.

No changes should be required to business modules, managers, or
repositories beyond the infrastructure layer.

---

## Related ADRs

- ADR-003 — Dependency Direction
- ADR-005 — Centralized Configuration
- ADR-008 — Persistence Layer Architecture
- ADR-009 — Database Abstraction Layer