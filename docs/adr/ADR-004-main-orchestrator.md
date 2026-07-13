# ADR-004: main.py as the Application Orchestrator

## Status

Accepted

---

## Date

13 July 2026

---

## Context

AnalystGPT Enterprise is designed as a modular analytics platform where each business capability has a clearly defined owner.

Without architectural boundaries, `main.py` could gradually accumulate business logic from multiple modules such as Upload, Cleaning, Quality, Analytics, and Reporting. This would create a large, tightly coupled entry point that is difficult to maintain, test, and extend.

A clear separation is required between application coordination and business logic.

---

## Decision

`main.py` shall act solely as the application orchestrator.

Its responsibilities are limited to:

- Starting the application
- Coordinating the execution of business modules
- Passing data between modules
- Managing the overall application workflow
- Handling high-level application startup and shutdown

Business logic, data transformation, validation, analytics, and reporting shall remain within the modules that own those responsibilities.

---

## Alternatives Considered

### Option 1 — Implement business logic inside `main.py`

**Rejected**

Reason:

Embedding business logic in `main.py` would violate Separation of Concerns and the Single Responsibility Principle. As the application grows, the entry point would become difficult to maintain, difficult to test, and increasingly coupled to multiple business modules.

---

### Option 2 — Use `main.py` only as an orchestrator

**Accepted**

Reason:

Keeping `main.py` focused on orchestration preserves clear responsibility ownership, improves modularity, simplifies testing, and allows individual business modules to evolve independently.

---

## Consequences

### Benefits

- Clear responsibility ownership
- Separation of Concerns
- Improved maintainability
- Easier unit testing
- Lower coupling between modules
- Improved scalability
- Simplified onboarding for new engineers
- Cleaner application flow

### Trade-offs

- Business functionality must be implemented within dedicated modules rather than directly inside `main.py`
- The application requires well-defined module interfaces and contracts

---

## Engineering Principles Applied

- Separation of Concerns (SoC)
- Single Responsibility Principle (SRP)
- Low Coupling
- High Cohesion
- Stable Module Contracts
- Maintainability
- Scalability
- Extensibility

---

## Related Documents

- ARCHITECTURE.md
- PROJECT_CONSTITUTION.md
- ADR-001: Upload Module Returns a Pandas DataFrame
- ADR-003: Dependency Direction