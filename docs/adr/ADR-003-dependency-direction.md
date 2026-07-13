# ADR-003: Dependency Direction

## Status

Accepted

---

## Date

13 July 2026

---

## Context

AnalystGPT Enterprise consists of business modules (Upload, Cleaning, Quality, Analytics, Reporting) and shared infrastructure located in the `core` package.

Without clear dependency rules, infrastructure could begin depending on business modules, leading to circular dependencies, tight coupling, reduced maintainability, and difficult testing.

A consistent dependency direction is required to preserve architectural boundaries.

---

## Decision

Business modules may depend on the shared infrastructure provided by the `core` package.

The `core` package must never depend on any business module.

The `core` package shall remain independent of business-specific responsibilities.

---

## Alternatives Considered

### Option 1 — Allow dependencies in any direction

**Rejected**

Reason:

This increases architectural complexity, introduces circular dependencies, and makes the system difficult to maintain and refactor.

---

### Option 2 — Enforce one-way dependency direction

**Accepted**

Reason:

One-way dependencies preserve architectural boundaries, reduce coupling, simplify testing, and improve long-term maintainability.

---

## Consequences

### Benefits

- Prevents circular dependencies
- Preserves architectural boundaries
- Simplifies testing
- Easier refactoring
- Lower coupling
- Higher maintainability
- Clear ownership of responsibilities

### Trade-offs

- Business functionality cannot be implemented inside the `core` package
- Some shared functionality must be carefully identified before moving into `core`

---

## Engineering Principles Applied

- Separation of Concerns
- Low Coupling
- High Cohesion
- Dependency Direction
- Maintainability
- Scalability
- Single Responsibility Principle

---

## Related Documents

- ARCHITECTURE.md
- PROJECT_CONSTITUTION.md
- ADR-002: Centralized Shared Logger