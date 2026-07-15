# Lessons Learned

> Permanent engineering concepts learned throughout AnalystGPT Enterprise.
> This document is a quick engineering reference, not a project journal.

---

## Last Updated

**Date:** 04 July 2026

---

# Engineering Philosophy

✅ Business before Technology

✅ Architecture before Code

✅ Think WHY before HOW

✅ Design before Implementation

✅ Build for Humans, not only Computers

---

# Software Engineering Workflow

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
Testing
↓
Documentation
↓
Deployment

---

# Architecture Rules

✅ main.py only orchestrates

✅ One Module = One Responsibility

✅ Shared infrastructure belongs in `core`

✅ Business modules depend on `core`

✅ `core` never depends on business modules

✅ Modules communicate using stable contracts

---

# Stable Contracts

### Upload

Input

- CSV
- Excel
- JSON
- API
- Database

Output

- Pandas DataFrame

Rule

Downstream modules never know where the data came from.

---

# Core Package

Purpose

Shared infrastructure used by every business module.

Contents

- constants.py
- config.py
- logger.py
- exceptions.py

---

# Configuration Rules

### constants.py

Application identity

Examples

- App Name
- Version
- Encoding

---

### config.py

Environment behaviour

Examples

- Debug Mode
- Log Level
- Upload Size

---

# Logging

Logger

→ Creates log messages

Log

→ Recorded message

Handler

→ Decides where logs go

Rule

Business modules use the shared logger.

Never create independent logging systems.

---

# Exceptions

Use

Specific exceptions

Never

Generic Exception

Good

- UnsupportedFileTypeError
- EmptyFileError
- FileTooLargeError

---

# Dependency Direction

Correct

Business Modules

↓

Core

Wrong

Core

↓

Business Modules

Reason

Prevents circular dependencies.

---

# Engineering Principles

- Separation of Concerns
- Single Responsibility Principle (SRP)
- Open / Closed Principle (OCP)
- Abstraction
- Low Coupling
- High Cohesion
- Modular Design
- Scalability
- Maintainability
- Extensibility
- Reusability

---

# Design Checklist

Before writing code ask:

□ What business problem am I solving?

□ Which module owns this?

□ What is the module contract?

□ What can fail?

□ Can this be extended later?

□ Does this violate SRP?

□ Can another engineer understand this quickly?

---

# Python Project Rules

✅ src contains application code

✅ main.py stays small

✅ Prefer many small modules

✅ Avoid hardcoding

✅ Configuration ≠ Constants

✅ One responsibility per file

---

# Naming Rules

Variables

snake_case

Functions

verb_noun()

Classes

PascalCase

Constants

UPPER_CASE

Modules

snake_case.py

---

# Engineering Mindset

Don't ask

"How do I code this?"

Ask

"How should this system be designed?"

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
# Sprint 0.75

## Git

- Git records the complete history of a project through immutable commits.
- Every commit should represent one logical change.
- The staging area exists to review changes before committing.
- Annotated tags should be used for official software releases.
- Always verify repository status before committing.

## Engineering Governance

- Good software is governed before it is expanded.
- Architecture decisions should be documented using ADRs.
- Every feature should satisfy a Definition of Done.
- Documentation should have clearly defined ownership.
- Code reviews protect software quality.

## Architecture

- Shared infrastructure belongs in `core/`.
- Business modules must never create circular dependencies.
- Stable module contracts reduce coupling.
- Separation of Concerns improves maintainability.
# Sprint 1 Lessons

## Technical Lessons

- Every module should have a single responsibility.
- UploadManager should orchestrate, not read files.
- Readers should only read their own file types.
- All readers should return the same abstraction (DataFrame).
- Custom exceptions improve maintainability.
- Logging should exist from the beginning of a project.
- Validation should happen before business logic.

## Engineering Lessons

- Build architecture before adding features.
- Keep modules small and focused.
- Design for future extension.
- Prefer reusable components over duplicated logic.
## Sprint 2

### Software Engineering

- Separation of Concerns is easier to maintain.
- Logging should exist at orchestration level.
- Testing each module independently reduces debugging time.
- Package structure matters.
- Use python -m for package-based execution.

### Python

- Type hints improve readability.
- reset_index() should be used after row deletions.
- Logging is better than print().
---

# Sprint 2 Lessons Learned

## Architecture

- Separation of Concerns improves maintainability.
- Managers should coordinate work rather than perform business logic.
- Stable module contracts simplify downstream development.
- Centralized infrastructure reduces duplication.

---

## Python

- Type hints improve readability.
- Pathlib provides cleaner path handling.
- Custom exceptions make error handling clearer.
- Logging should replace print statements in production applications.

---

## Testing

- Automated tests provide confidence during refactoring.
- Pytest offers a clean and scalable testing framework.
- Small independent unit tests are easier to maintain.
- Every business component should have dedicated tests.

---

## Engineering

- Documentation must remain synchronized with implementation.
- Git history should reflect completed milestones.
- Repository consistency is part of software quality.
- Enterprise software development extends beyond writing code.

---

## Personal Growth

During Sprint 2 I strengthened my understanding of:

- Modular software architecture
- Pipeline orchestration
- Data cleaning design
- Automated testing
- Logging
- Custom exception handling
- Repository organization
- Engineering documentation

These lessons establish the foundation for implementing the Quality Module in Sprint 3. 

---

# Sprint 3 — Quality Module

## Technical Lessons

- Data cleaning and data quality assessment are separate responsibilities and should remain independent modules.
- Managers should orchestrate workflows rather than contain business logic.
- Every checker should perform exactly one responsibility.
- A dedicated report builder simplifies future expansion and improves maintainability.
- Enterprise software benefits from small, focused classes rather than large multifunctional components.
- Automated testing should be developed alongside implementation to validate architecture and behavior.

## Architecture Lessons

- Separating orchestration from execution results in a cleaner and more maintainable design.
- Returning structured assessment results instead of modifying the DataFrame preserves module boundaries.
- Designing for extensibility early reduces future refactoring effort.
- Consistent coding standards across modules improve readability and long-term maintainability.

## Engineering Lessons

- Completing a sprint includes implementation, integration, testing, documentation, and release preparation.
- Documentation should evolve together with the codebase and accurately reflect the implemented architecture.
- Passing tests without warnings provides greater confidence in code quality than simply achieving passing assertions.

## Sprint 3 Milestone

Sprint 3 completed the data preparation foundation of AnalystGPT Enterprise.

Current architecture:

```
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

The project is now ready to begin Sprint 4 — Analytics Module.