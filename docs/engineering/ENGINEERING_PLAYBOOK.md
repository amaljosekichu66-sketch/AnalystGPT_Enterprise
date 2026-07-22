# AnalystGPT Enterprise Engineering Playbook

## Purpose

This document defines the standard engineering workflow for AnalystGPT Enterprise.

Its purpose is to ensure every feature is designed, implemented, tested, documented, and released using a consistent engineering process.

---

# Engineering Principles

Every contribution should follow:

- Business before Technology
- Architecture before Implementation
- Separation of Concerns
- Single Responsibility Principle (SRP)
- Low Coupling
- High Cohesion
- Maintainability
- Scalability
- Extensibility
- Testability
- Readability over Cleverness

---

# Standard Development Workflow

Every feature follows the same engineering lifecycle.

```text
Business Problem
        ↓
Business Value
        ↓
Architecture Design
        ↓
Implementation
        ↓
Unit Testing
        ↓
Integration Testing (when applicable)
        ↓
Code Review
        ↓
Documentation
        ↓
Release Review
        ↓
Merge
```

---

# Git Workflow

Typical development workflow:

```text
Create Branch
        ↓
Develop Feature
        ↓
Run Tests
        ↓
Review Documentation
        ↓
Commit
        ↓
Push
        ↓
Open Pull Request
        ↓
Code Review
        ↓
Merge
```

Release workflow (at sprint conclusion):

```text
Run Application (end-to-end)
        ↓
Run Full Test Suite
        ↓
Review Documentation Updates
        ↓
Repository Review (status, branch, tags)
        ↓
Create Release Commit
        ↓
Create Git Tag
        ↓
Push to GitHub
```

---

# Branch Naming

Use descriptive branch names.

Examples:

```text
feature/upload-module
feature/json-reader
feature/reporting-module

bugfix/logger-format

refactor/cleaning-manager

docs/architecture-update
```

Avoid:

```text
test
new
branch1
amal
```

---

# Commit Message Convention

Use clear, descriptive commit messages.

Examples:

```text
feat(upload): add Excel reader

feat(analytics): complete Sprint 4 Analytics Module

fix(cleaning): resolve datatype conversion issue

refactor(core): simplify logger configuration

docs(readme): update project overview

test(quality): add completeness checker tests
```

Avoid:

```text
update
fixed
done
changes
```

---

# Release Commit Convention

For sprint releases, use a consistent release commit message.

Example:

```text
release(v7.0.0): PostgreSQL Integration
```

This helps identify releases in the commit history.

---

# Pull Request Expectations

Every Pull Request should:

- Solve one logical problem.
- Pass all automated tests.
- Preserve existing architecture.
- Maintain stable module contracts.
- Respect dependency direction (business modules → core; never the reverse).
- Ensure backward compatibility where applicable.
- Separate business logic from infrastructure (no SQL in business modules).
- Include documentation updates when required.
- Avoid unrelated changes.
- Be understandable without external explanation.

---

# Testing Standards

Every feature should include appropriate automated testing.

### Unit Tests

Required for:

- Business logic
- Managers
- Utility components

### Integration Tests

Required whenever multiple modules participate in the same business workflow.

Current integration pipeline:

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
        ↓
Persistence
        ↓
Database (SQLite / PostgreSQL)
```

### Infrastructure Validation

When database or persistence changes occur, additional validation is required:

- Database initialization and connection lifecycle.
- Schema creation and migration (where applicable).
- Repository integration and CRUD operations.
- Cross-database compatibility (placeholder conversion, dialect support).

---

# Documentation Standards

Whenever architecture or functionality changes, review and update the appropriate documentation.

Potential documents include:

- README.md
- PROJECT_STATE.md
- ARCHITECTURE.md
- CHANGELOG.md
- PROJECT_JOURNAL.md
- ROADMAP.md
- LESSONS_LEARNED.md
- ADRs (Architecture Decision Records)
- Sprint Release Reports
- ENGINEERING_OPERATING_MANUAL.md (when workflow changes)

Avoid duplicating information across documents.

---

# Code Review Checklist

Reviewers should consider the following:

- **Single Responsibility Principle** – Does each component have one clear responsibility?
- **Separation of Concerns** – Are business logic, orchestration, and infrastructure properly separated?
- **Open/Closed Principle** – Can the component be extended without modifying its source?
- **Stable Module Contracts** – Are public interfaces stable and well-defined?
- **Low Coupling** – Are dependencies minimal and explicitly declared?
- **High Cohesion** – Are related responsibilities grouped together?
- **Readability** – Is the code easy to understand and maintain?
- **Testability** – Is the code structured to allow effective unit testing?

---

# Definition of Done

A feature is complete only when:

- Business problem is understood.
- Business value is articulated.
- Architecture is reviewed.
- Code is implemented.
- Unit tests pass.
- Integration tests pass (where applicable).
- No unintended warnings remain.
- Documentation is updated.
- Code review is completed.
- Repository review (branch, tags) is completed.
- Version synchronization across all documentation is verified.
- Feature is ready for release.

---

# Sprint Release Workflow

Every sprint should conclude with the following activities:

```text
Run Application (end-to-end)
        ↓
Run Full Test Suite
        ↓
Resolve Warnings
        ↓
Update Documentation
        ↓
Repository Review (status, branches, tags)
        ↓
Version Update (sync all docs)
        ↓
Create Release Commit
        ↓
Create Git Tag
        ↓
Push to GitHub
```

A sprint is not considered complete until the release workflow has been finished.

---

# Engineering Philosophy

Build software that future engineers can understand, maintain, extend, and confidently deploy.

Optimize for long-term engineering quality rather than short-term implementation speed.