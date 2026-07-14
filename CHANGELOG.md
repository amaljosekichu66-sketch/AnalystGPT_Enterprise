# Changelog

## Sprint 0.5

### Added

- `src/core/`
- `constants.py`
- `config.py`
- `logger.py`
- `exceptions.py`
- Package `__init__.py` files

### Architecture

- Shared Core Infrastructure
- Stable DataFrame Contract
- Main Orchestrator Pattern
- Shared Logger Architecture
- Dependency Direction Rules

### Testing

- Initial Smoke Test
## [v0.75.0] - 2026-07-13

### Added

- Git version control
- GitHub integration
- Engineering Playbook
- Code Review Checklist
- Documentation Standards
- Definition of Done
- Sprint Retrospective
- Sprint Release Report
- ADR-001 to ADR-006

### Changed

- Repository upgraded to enterprise engineering workflow.

### Release

Official Sprint 0.75 Release

# Sprint 1 - Upload Module

## Added

- UploadManager for upload orchestration
- CSVReader
- ExcelReader
- JSONReader
- Automatic file type detection
- Standardized pandas DataFrame output
- Custom SourceFileNotFoundError
- UnsupportedFileTypeError handling
- Reader registry architecture
- Enterprise logging

## Tested

- CSV upload
- Excel upload
- JSON upload
- Unsupported file types
- Missing file validation

## Status

Sprint 1 completed successfully.# v1.0.0 — Sprint 1 (14 July 2026)

## Added

- UploadManager
- CSVReader
- ExcelReader
- JSONReader
- Automatic file type detection
- Standardized Pandas DataFrame output
- Centralized logging
- Custom exception hierarchy
- File existence validation
- Unsupported file type validation

## Architecture

- Introduced modular Upload Module.
- Implemented reader registry pattern.
- Established standardized DataFrame contract for downstream modules.

## Documentation

- Updated PROJECT_STATE.md
- Updated ROADMAP.md
- Updated README.md
- Updated engineering documentation

## Status

✅ Sprint 1 Completed
## v0.7 - Sprint 2 Complete

### Added

- CleaningManager
- ColumnCleaner
- TextCleaner
- MissingValueCleaner
- DuplicateCleaner
- DataTypeCleaner
- Execution timing
- Enterprise logging
- Cleaning module tests

### Improved

- Modular architecture
- Type hints
- Pipeline orchestration

### Fixed

- Import issues
- Package initialization
- Test execution
---

# v2.0.0 — Sprint 2 (Data Cleaning Module)

**Release Date:** July 2026

## Added

### Cleaning Module

- CleaningManager
- ColumnCleaner
- TextCleaner
- MissingValueCleaner
- DuplicateCleaner
- DataTypeCleaner

### Architecture

- Complete Upload → Cleaning pipeline
- Stable manager-based orchestration
- Standardized DataFrame pipeline
- Consistent dependency direction

### Logging

- Centralized application logging
- Pipeline execution logging
- Cleaner execution logging
- Pipeline execution timing

### Testing

- Automated Pytest suite
- Unit tests for every cleaner
- End-to-end pipeline verification

## Improved

- Import consistency across the project
- Upload module integration
- Exception hierarchy
- Code readability
- Documentation
- Engineering standards

## Fixed

- Upload module import inconsistencies
- Main pipeline orchestration
- Duplicate MissingValueCleaner implementation
- Logging inconsistencies
- Architecture violations

## Repository Status

- Upload Module → Stable
- Cleaning Module → Stable
- Automated Tests → Passing
- Architecture → Stable

**Release Version:** v2.0.0