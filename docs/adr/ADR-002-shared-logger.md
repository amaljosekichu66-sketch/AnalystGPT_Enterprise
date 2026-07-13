# ADR-002: Centralized Shared Logger

## Status

Accepted

---

## Date

13 July 2026

---

## Context

Logging is a cross-cutting concern used by multiple business modules including Upload, Cleaning, Quality, Analytics, and Reporting.

If every module created and configured its own logger, the application would contain duplicated configuration, inconsistent log formatting, and increased maintenance effort.

A shared logging infrastructure is required to ensure consistent behavior across the entire application.

---

## Decision

A single shared logger will be implemented inside the `core` package.

All business modules will import and use this shared logger rather than creating their own logging configuration.

The `core` package owns logging infrastructure, while business modules only consume it.

---

## Alternatives Considered

### Option 1 — Each module creates its own logger

**Rejected**

Reason:

This introduces duplicated configuration, inconsistent formatting, and increases maintenance complexity whenever logging behavior changes.

---

### Option 2 — Create one shared logger inside `core`

**Accepted**

Reason:

A centralized logger promotes consistency, reduces duplication, and separates infrastructure concerns from business logic.

---

## Consequences

### Benefits

- Consistent log formatting across all modules
- Centralized configuration
- Reduced code duplication
- Easier maintenance
- Supports future enhancements such as file logging, cloud logging, or structured logging without changing business modules

### Trade-offs

- Business modules depend on the shared logging infrastructure
- Changes to logging configuration affect the entire application (which is intentional and controlled)

---

## Engineering Principles Applied

- Separation of Concerns
- Single Responsibility Principle
- Low Coupling
- High Cohesion
- Reusability
- Maintainability

---

## Related Documents

- ARCHITECTURE.md
- PROJECT_CONSTITUTION.md
- ADR-003: Dependency Direction