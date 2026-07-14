# Project Journal

## Sprint 0

### Date
03 July 2026

### Completed

- Created project
- Installed VS Code
- Installed Python Extension
- Verified Python 3.10.5
- Selected Interpreter
- Created README
- Created src folder
- Created project modules
- Created main.py
- Executed first Python program

### Lessons Learned

- Business before code
- Architecture before implementation
- main.py is an orchestrator
- src contains application code
- Upload Module should return a DataFrame
- Separation of Concerns
- Modular Design

# Project Journal

## Sprint 0

### Date
03 July 2026

### Completed

- Created project
- Installed VS Code
- Installed Python Extension
- Verified Python 3.10.5
- Selected Interpreter
- Created README
- Created src folder
- Created project modules
- Created main.py
- Executed first Python program

### Lessons Learned

- Business before code
- Architecture before implementation
- main.py is an orchestrator
- src contains application code
- Upload Module should return a DataFrame
- Separation of Concerns
- Modular Design

---

## Sprint 0.5

### Date
### 04 July 2026

### Completed

- Created `core` package
- Added `constants.py`
- Added `config.py`
- Added `logger.py`
- Added `exceptions.py`
- Added `__init__.py` files to all packages
- Implemented basic logging infrastructure
- Implemented application configuration
- Implemented application constants
- Created first custom exception
- Performed first smoke test
- Reviewed application architecture
- Defined module responsibilities
- Defined dependency direction
- Established shared infrastructure design

### Lessons Learned

- Shared infrastructure belongs inside `core`
- Business modules should depend on `core`
- `core` must never depend on business modules
- Stable contracts reduce coupling
- Upload should always return a Pandas DataFrame
- Configuration and constants serve different purposes
- Logger and log are different concepts
- Handlers decide where logs are written
- Custom exceptions improve maintainability
- Good architecture reduces cognitive load
- Design before implementation

# Sprint 0.75 — Enterprise Engineering Workflow

**Status:** ✅ Completed

## Completed

- Installed and configured Git
- Initialized local Git repository
- Created `.gitignore`
- Learned Git workflow:
  - git status
  - git add
  - git commit
  - git log
  - git restore
  - git remote
  - git remote -v
- Connected repository to GitHub
- Created first production-quality commits
- Published repository to GitHub
- Created annotated release tag `v0.75.0`
- Established Engineering Governance
- Created Architecture Decision Records (ADR-001 to ADR-006)
- Added Engineering Playbook
- Added Code Review Checklist
- Added Documentation Standards
- Added Definition of Done
- Added Sprint Retrospective
- Added Sprint Release Report

## Lessons Learned

- Git is a distributed version control system, not cloud storage.
- Commits create immutable snapshots of the repository.
- The staging area allows changes to be reviewed before committing.
- GitHub stores and shares the repository but Git manages version history.
- Tags mark important milestones such as software releases.
- Architecture decisions should be documented rather than remembered.
- Enterprise software requires engineering governance before feature development.

## Release

Version: **v0.75.0**

Sprint Status: ✅ Closed
# Sprint 1 — Upload Module Complete

**Date:** 14 July 2026

## Objective

Develop the first production-ready business module capable of reading multiple data formats while maintaining enterprise architecture standards.

## Completed

- UploadManager
- CSVReader
- ExcelReader
- JSONReader
- Reader registry architecture
- Centralized logging
- Custom exception hierarchy
- Missing file validation
- Unsupported file validation
- Standardized Pandas DataFrame output

## Key Engineering Lessons

- Business modules should have a single responsibility.
- UploadManager should orchestrate, not implement file reading.
- Reader classes should remain independent.
- Every downstream module should consume a standardized DataFrame.
- Enterprise architecture begins with clear separation of concerns.

## Sprint Result

Sprint 1 completed successfully.

Repository version updated to **v1.0.0**.

# Sprint 2 — Cleaning Module

## Objectives

Build a modular enterprise-grade data cleaning pipeline.

## Completed

- Implemented ColumnCleaner
- Implemented TextCleaner
- Implemented MissingValueCleaner
- Implemented DuplicateCleaner
- Implemented DataTypeCleaner
- Built CleaningManager
- Added execution logging
- Added pipeline timing
- Added module tests

## Challenges

- Python package imports
- __init__.py package structure
- Windows module execution
- Logging integration

## Lessons Learned

- Managers should orchestrate, not clean.
- Each cleaner should have one responsibility.
- Centralized logging simplifies debugging.
- Type hints improve readability.
- Modular testing catches regressions.

## Result

Sprint 2 completed successfully.
---

# Sprint 2 — Data Cleaning Module

## Sprint Objective

Develop an enterprise-grade Data Cleaning Module while preserving the architecture and engineering standards established during Sprint 1.

---

## Major Deliverables

### CleaningManager

Implemented a centralized orchestration layer responsible for coordinating the complete cleaning pipeline.

### Cleaning Components

Implemented:

- ColumnCleaner
- TextCleaner
- MissingValueCleaner
- DuplicateCleaner
- DataTypeCleaner

Each cleaner follows the Single Responsibility Principle and can be tested independently.

---

## Integration

Successfully integrated:

```
main.py

↓

UploadManager

↓

CleaningManager

↓

Clean DataFrame
```

The application now follows the intended architecture without bypassing business modules.

---

## Logging

Implemented centralized logging throughout the cleaning pipeline.

Features include:

- Pipeline start
- Pipeline completion
- Individual cleaner execution
- Execution timing
- Error reporting

---

## Automated Testing

Converted demonstration scripts into real automated unit tests using Pytest.

Current status:

- 5 automated tests
- 5 passing
- 0 failures

---

## Architecture Improvements

Completed:

- Upload module import standardization
- Manager orchestration
- Consistent dependency direction
- Standardized exception handling

---

## Lessons Learned

- Managers should orchestrate, not implement business logic.
- Business logic belongs inside isolated components.
- Automated testing is essential for maintainability.
- Consistent imports simplify architecture.
- Logging should replace print statements in production code.
- Documentation should evolve alongside implementation.

---

## Sprint Result

Sprint 2 completed successfully.

Release Version:

**v2.0.0**