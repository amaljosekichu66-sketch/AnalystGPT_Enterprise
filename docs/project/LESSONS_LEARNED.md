# Lessons Learned

> Permanent engineering concepts learned throughout AnalystGPT Enterprise.
>
> This document serves as a continuously growing engineering knowledge base rather than a project journal.

---

# Last Updated

**Date:** 15 July 2026

---

# Engineering Philosophy

- ✅ Business before Technology
- ✅ Architecture before Code
- ✅ Think **WHY** before **HOW**
- ✅ Design before Implementation
- ✅ Build for Humans, not only Computers
- ✅ Documentation is Part of the Product
- ✅ Testing is Part of Development

---

# Software Engineering Workflow

```text
Business Problem
        ↓
Business Value
        ↓
Architecture
        ↓
Design
        ↓
Implementation
        ↓
Unit Testing
        ↓
Integration Testing
        ↓
Documentation
        ↓
Release
```

---

# Architecture Rules

- ✅ `main.py` only orchestrates
- ✅ One Module = One Responsibility
- ✅ Shared infrastructure belongs in `core`
- ✅ Business modules depend on `core`
- ✅ `core` never depends on business modules
- ✅ Managers coordinate business workflows
- ✅ Business modules communicate through stable contracts

---

# Stable Contracts

## Upload

### Input

- CSV
- Excel
- JSON
- Database *(Planned)*
- REST API *(Planned)*

### Output

- Pandas DataFrame

### Rule

Downstream modules should never know where the data originated.

---

# Core Package

## Purpose

Shared infrastructure used throughout the application.

### Components

- constants.py
- config.py
- logger.py
- exceptions.py

---

# Configuration Rules

## constants.py

Stores application identity and immutable values.

Examples:

- Application Name
- Version
- Encoding

---

## config.py

Stores configurable runtime behavior.

Examples:

- Debug Mode
- Logging Level
- Upload Limits

---

# Logging

Logger

↓

Creates log messages

Handler

↓

Determines where log messages are written

Rule

Business modules must use the shared logger.

Never create independent logging systems.

---

# Exceptions

Prefer:

Specific exceptions

Avoid:

Generic `Exception`

Examples:

- UnsupportedFileTypeError
- EmptyFileError
- FileTooLargeError

---

# Dependency Direction

Correct

```text
Business Modules
        ↓
      Core
```

Incorrect

```text
Core
    ↓
Business Modules
```

Reason

Prevents circular dependencies and preserves modular architecture.

---

# Engineering Principles

- Separation of Concerns
- Single Responsibility Principle (SRP)
- Open / Closed Principle (OCP)
- Low Coupling
- High Cohesion
- Modular Design
- Scalability
- Maintainability
- Extensibility
- Reusability
- Testability

---

# Design Checklist

Before writing code ask:

- □ What business problem am I solving?
- □ Which module owns this responsibility?
- □ What is the module contract?
- □ What can fail?
- □ Can this be extended later?
- □ Does this violate SRP?
- □ Can another engineer understand this quickly?

---

# Python Project Rules

- `src/` contains application code.
- `main.py` remains an orchestrator.
- Prefer many small modules.
- Avoid hardcoding.
- Configuration is not Constants.
- One responsibility per file.

---

# Naming Rules

| Item | Convention |
|------|------------|
| Variables | snake_case |
| Functions | verb_noun() |
| Classes | PascalCase |
| Constants | UPPER_CASE |
| Modules | snake_case.py |

---

# Engineering Mindset

Don't ask:

> "How do I code this?"

Ask:

> "How should this system be designed?"

---

# One-Line Reminders

- Code is for computers.
- Architecture is for humans.
- Contracts reduce coupling.
- Shared infrastructure reduces duplication.
- Good names reduce documentation.
- Design for change.
- Prefer extension over modification.
- Understand before implementing.
- Small modules scale better.
- Documentation preserves engineering knowledge.

---

# Sprint 0.75 Lessons

## Git

- Git records the complete history of a project.
- Every commit should represent one logical change.
- Use the staging area to review changes before committing.
- Annotated tags identify official releases.
- Always verify repository status before committing.

## Engineering Governance

- Good software is governed before it is expanded.
- Architectural decisions belong in ADRs.
- Every feature must satisfy the Definition of Done.
- Documentation should have clear ownership.
- Code reviews protect software quality.

---

# Sprint 1 Lessons

## Architecture

- Every module should have a single responsibility.
- Managers should orchestrate rather than implement business logic.
- Stable DataFrame contracts simplify downstream processing.
- Validation should occur before business logic.

## Engineering

- Logging should exist from the beginning.
- Build architecture before features.
- Prefer reusable components over duplicated logic.

---

# Sprint 2 Lessons

## Architecture

- Separation of Concerns improves maintainability.
- Managers coordinate work rather than perform business logic.
- Stable contracts simplify downstream development.
- Centralized infrastructure reduces duplication.

## Testing

- Automated testing provides confidence during refactoring.
- Small independent unit tests are easier to maintain.
- Every business component deserves dedicated tests.

## Engineering

- Documentation must evolve alongside implementation.
- Repository consistency is part of software quality.
- Enterprise software development extends beyond writing code.

---

# Sprint 3 Lessons

## Architecture

- Data cleaning and data quality assessment are separate responsibilities.
- Report builders improve extensibility.
- Structured outputs preserve module boundaries.
- Small focused classes are easier to maintain.

## Engineering

- Passing tests without warnings improves confidence.
- Sprint completion includes implementation, testing, documentation, and release preparation.
- Documentation should accurately reflect architecture.

---

# Sprint 4 Lessons

## Analytics

- Analytics should be implemented as independent reusable components.
- Managers coordinate analyzers rather than performing analysis directly.
- Standardized analytics reports simplify downstream reporting.

## Testing

- Integration tests validate collaboration between modules rather than individual implementations.
- Unit tests should verify public contracts instead of internal implementation details.
- Shared fixtures reduce duplicated test data and improve maintainability.

## Engineering

- Console output should communicate meaningful business information rather than raw objects.
- Resolve compatibility warnings early to reduce future maintenance effort.
- Release management is a core engineering activity, not an afterthought.
- Every sprint should conclude with repository review, documentation updates, testing, and versioned release.

---

# Current Engineering Milestone

The project now consists of a complete analytics pipeline:

```text
Upload
    ↓
Cleaning
    ↓
Quality
    ↓
Analytics
    ↓
Reporting (Next Sprint)
```

Sprint 4 established the analytical foundation of AnalystGPT Enterprise.


---

# Sprint 5 — Reporting & Performance Lessons

## Enterprise Reporting

- Reporting is a separate business capability and should remain isolated from analytics logic.
- Report generation should consume standardized outputs from upstream modules rather than reprocessing datasets.
- Export functionality should be modular so additional formats can be introduced without affecting existing components.

## Performance Validation

- Functional correctness alone is insufficient; large-scale datasets should be used to validate scalability.
- Benchmarking with small, large, and stress-test datasets helps identify performance bottlenecks early.
- Execution time, memory usage, and pipeline stability are valuable engineering metrics for evaluating production readiness.

## Engineering Practice

- Keep permanent engineering guidance separate from sprint-specific implementation details.
- Update architecture documentation only when architectural boundaries or responsibilities change.
- Use release documentation to record implementation achievements and benchmark results rather than modifying long-term engineering documents.

---

# Sprint 5.5 — Lessons Learned

## Architectural Lessons

Large software systems benefit from separating orchestration from
business logic.

Introducing a dedicated Application Layer significantly simplified
pipeline coordination while preserving module independence.

---

## Design Lessons

Stable contracts are more valuable than exposing implementation
details.

Business modules should communicate only through clearly defined
interfaces.

---

## Software Engineering Lessons

A thin application entry point improves readability, maintainability,
and extensibility.

Future presentation layers (CLI, Streamlit, APIs) can now reuse the
same Application Layer.

---

## Documentation Lessons

Maintaining a clear separation between:

- PROJECT_STATE
- ARCHITECTURE
- ROADMAP
- CHANGELOG
- PROJECT_JOURNAL

reduces duplication and improves long-term maintainability.

---

## Testing Lessons

Major architectural refactors should always be completed alongside
comprehensive automated validation.

Successfully preserving 79 / 79 passing tests throughout the refactor
provided confidence that architectural improvements did not introduce
functional regressions.

---

## Future Guidance

Future architectural work should continue to prioritize:

- Stable contracts
- Independent business modules
- Centralized orchestration
- Strong typing
- Enterprise documentation
- Automated validation

These principles established during Sprint 5.5 should remain guiding
engineering standards throughout future development.