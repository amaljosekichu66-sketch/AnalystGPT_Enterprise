# ADR-001: Upload Module Returns a Pandas DataFrame

## Status

Accepted

---

## Date

13 July 2026

---

## Context

The Upload module is responsible for acquiring data from multiple sources such as CSV, Excel, JSON, APIs, and databases.

If each downstream module (Cleaning, Quality, Analytics, Reporting) had to support multiple input formats, the application would become tightly coupled, difficult to maintain, and harder to extend.

A single, stable contract is required between the Upload module and all downstream business modules.

---

## Decision

The Upload module shall always return a Pandas DataFrame, regardless of the original data source.

All downstream modules will consume only DataFrames.

The Upload module is solely responsible for converting external data into this standard internal representation.

---

## Alternatives Considered

### Option 1 — Return source-specific objects

Examples:

- CSV Reader returns CSV data
- API returns JSON
- Database returns SQL result sets

**Rejected**

Reason:

Every downstream module would need to understand multiple formats, increasing coupling and implementation complexity.

---

### Option 2 — Return Python Lists or Dictionaries

**Rejected**

Reason:

Lists and dictionaries do not provide the rich tabular functionality required for enterprise analytics, validation, transformation, and reporting.

---

### Option 3 — Return a Pandas DataFrame

**Accepted**

Reason:

A DataFrame provides a consistent, well-supported, and scalable tabular structure that integrates naturally with the analytics ecosystem.

---

## Consequences

### Benefits

- Stable module contract
- Loose coupling between modules
- Simplified testing
- Easier maintenance
- Easier addition of new upload sources
- Consistent downstream processing

### Trade-offs

- Introduces a dependency on Pandas
- Upload module is responsible for all format conversions

---

## Engineering Principles Applied

- Stable Module Contracts
- Separation of Concerns
- Low Coupling
- High Cohesion
- Maintainability
- Extensibility

---

## Related Documents

- ARCHITECTURE.md
- PROJECT_CONSTITUTION.md
- PROJECT_STATE.md