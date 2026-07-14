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