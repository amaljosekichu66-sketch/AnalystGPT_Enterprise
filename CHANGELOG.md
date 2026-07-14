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