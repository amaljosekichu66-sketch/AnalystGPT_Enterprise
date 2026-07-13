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