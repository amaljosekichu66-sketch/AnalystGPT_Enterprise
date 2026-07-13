# ADR-005: Centralized Configuration

## Status

Accepted

---

## Date

13 July 2026

---

## Context

AnalystGPT Enterprise requires configuration values such as file paths, application settings, default parameters, and environment-specific values.

If configuration is hardcoded across multiple modules, updates become difficult, duplication increases, and the risk of inconsistent behavior grows.

A centralized configuration mechanism is required to improve maintainability and consistency.

---

## Decision

All application configuration shall be centralized within the `core/config.py` module.

Business modules shall consume configuration values from this shared configuration rather than defining or hardcoding them independently.

---

## Alternatives Considered

### Option 1 — Hardcode configuration inside business modules

**Rejected**

Reason:

Hardcoded values increase duplication, reduce maintainability, and require changes across multiple modules whenever configuration changes.

---

### Option 2 — Centralize configuration within `core/config.py`

**Accepted**

Reason:

Centralized configuration provides a single source of truth, improves consistency, simplifies maintenance, and supports future environment-based configuration.

---

## Consequences

### Benefits

- Single source of truth
- Improved maintainability
- Reduced duplication
- Consistent application behavior
- Easier future environment management

### Trade-offs

- Business modules depend on shared configuration infrastructure
- Configuration changes may affect multiple modules simultaneously

---

## Engineering Principles Applied

- Separation of Concerns
- Single Responsibility Principle
- Reusability
- Maintainability
- Scalability

---

## Related Documents

- ARCHITECTURE.md
- PROJECT_CONSTITUTION.md
- ADR-002: Centralized Shared Logger