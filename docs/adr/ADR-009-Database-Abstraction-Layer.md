# ADR-009 — Database Abstraction Layer

## Status

Accepted

---

## Date

22 July 2026

---

## Context

Sprint 6 introduced the Persistence Layer using SQLite as the project's
first database implementation.

While SQLite satisfied the project's immediate persistence requirements,
the architecture tightly coupled the infrastructure to a single database
engine. Supporting additional relational databases would require changes
throughout the persistence layer, reducing maintainability and violating
the project's goal of designing for extensibility.

Sprint 7 required AnalystGPT Enterprise to support both SQLite and
PostgreSQL while preserving stable business module contracts and avoiding
database-specific logic outside the infrastructure layer.

---

## Decision

Introduce a database abstraction layer centered around a common
`DatabaseConnection` interface.

All database implementations must implement the same contract, including:

- Connection lifecycle
- Transaction management
- Database identification
- Access to the underlying driver connection

Concrete implementations include:

- SQLiteConnection
- PostgreSQLConnection

Infrastructure components, including:

- DatabaseManager
- SchemaManager
- BaseRepository
- Repository implementations

depend only on the `DatabaseConnection` abstraction rather than concrete
database implementations.

Business modules remain completely independent of the selected database
engine.

---

## Alternatives Considered

### Continue using SQLite only

Rejected.

This would prevent future database support without significant
architectural changes.

---

### Add PostgreSQL using conditional logic

Rejected.

Adding database-specific conditionals throughout repositories and
managers would increase coupling, duplicate logic, and reduce
maintainability.

---

### Maintain separate persistence implementations

Rejected.

Separate implementations would duplicate repository logic and make future
maintenance more difficult.

---

## Consequences

### Positive

- Supports multiple relational databases.
- Infrastructure depends on stable abstractions.
- Business modules remain database-independent.
- Future database engines can be added with minimal architectural impact.
- Improves maintainability and extensibility.
- Preserves existing application contracts.

### Negative

- Introduces additional abstraction.
- Requires every database implementation to satisfy the shared contract.

---

## Architectural Impact

This decision establishes database abstraction as a permanent
architectural principle within AnalystGPT Enterprise.

Future database engines should integrate by implementing the
`DatabaseConnection` interface without requiring changes to business
modules.

---

## Related ADRs

- ADR-003 — Dependency Direction
- ADR-006 — Enterprise Module Structure
- ADR-008 — Persistence Layer Architecture