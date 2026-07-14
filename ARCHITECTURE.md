# AnalystGPT Enterprise Architecture

> **Purpose**
>
> This document describes the software architecture of AnalystGPT Enterprise.
> It defines the responsibilities, boundaries, dependencies, and data flow
> between modules.
>
> This document reflects the current implementation as of **v2.0.0**.

---

# Architecture Philosophy

AnalystGPT Enterprise follows a modular, layered architecture designed around
Separation of Concerns (SoC), SOLID principles, and maintainability.

Each business capability is implemented as an independent module with a single,
well-defined responsibility.

---

# High-Level Architecture

```
                    main.py
                       │
                       ▼
              Upload Manager
                       │
                       ▼
            Standardized DataFrame
                       │
                       ▼
             Cleaning Manager
                       │
                       ▼
               Clean DataFrame
                       │
                       ▼
              Quality Manager
                       │
                       ▼
            Validated DataFrame
                       │
                       ▼
             Analytics Manager
                       │
                       ▼
             Reporting Manager
```

---

# Layered Architecture

```
Presentation Layer

        main.py

──────────────────────────────────

Business Layer

Upload
Cleaning
Quality
Analytics
Reporting

──────────────────────────────────

Shared Infrastructure

core/

──────────────────────────────────

External Libraries

Pandas
OpenPyXL
JSON
Pytest
Logging
```

---

# Repository Structure

```
AnalystGPT_Enterprise/

docs/

sample_data/

src/

    upload/
    cleaning/
    quality/
    analytics/
    reporting/
    core/

tests/

main.py
```

---

# Current Stable Modules

## Upload Module

### Responsibility

Acquire data from supported file formats and convert it into a standardized
Pandas DataFrame.

### Components

- UploadManager
- CSVReader
- ExcelReader
- JSONReader

### Supported Formats

- CSV
- Excel (.xlsx, .xls)
- JSON

### Output

```
Pandas DataFrame
```

### Status

✅ Stable

---

## Cleaning Module

### Responsibility

Normalize uploaded data before quality validation.

### Components

- CleaningManager
- ColumnCleaner
- TextCleaner
- MissingValueCleaner
- DuplicateCleaner
- DataTypeCleaner

### Processing Pipeline

```
Raw DataFrame

↓

ColumnCleaner

↓

TextCleaner

↓

MissingValueCleaner

↓

DuplicateCleaner

↓

DataTypeCleaner

↓

Reset Index

↓

Clean DataFrame
```

### Status

✅ Stable

---

## Quality Module

### Responsibility

Validate cleaned datasets before analytical processing.

### Planned Components

- QualityManager
- CompletenessChecker
- ValidityChecker
- ConsistencyChecker
- UniquenessChecker
- OutlierChecker
- QualityReport

### Planned Output

```
Validated DataFrame

+

Quality Report
```

### Status

🟡 Planned (Sprint 3)

---

## Analytics Module

### Responsibility

Generate business insights from validated datasets.

### Planned Components

- AnalyticsManager
- KPI Engine
- Statistical Analysis
- Business Metrics

### Status

⚪ Planned

---

## Reporting Module

### Responsibility

Generate reports for business users.

### Planned Outputs

- Excel
- PDF
- HTML
- Dashboard datasets

### Status

⚪ Planned

---

# Shared Infrastructure

The `core` package contains reusable infrastructure shared across all business
modules.

```
core/

config.py

constants.py

logger.py

exceptions.py
```

Responsibilities

### config.py

Centralized application configuration.

### constants.py

Immutable application constants.

### logger.py

Centralized logging configuration.

### exceptions.py

Custom application exceptions.

---

# Dependency Rules

Business modules may depend on `core`.

Business modules may not depend on each other directly except through
well-defined manager interfaces.

The `core` package must never depend on any business module.

```
Allowed

Cleaning

↓

core

Not Allowed

core

↓

Cleaning
```

---

# Data Flow

```
CSV / Excel / JSON

↓

UploadManager

↓

Pandas DataFrame

↓

CleaningManager

↓

Clean DataFrame

↓

QualityManager

↓

Validated DataFrame

↓

AnalyticsManager

↓

Business Insights

↓

ReportingManager

↓

Reports
```

---

# Manager Pattern

Every business module exposes one orchestration class.

| Module | Manager |
|---------|----------|
| Upload | UploadManager |
| Cleaning | CleaningManager |
| Quality | QualityManager |
| Analytics | AnalyticsManager |
| Reporting | ReportingManager |

Managers coordinate components but do not contain business logic.

---

# Logging Strategy

Logging is centralized through:

```
core/logger.py
```

Every business module should:

- Log execution start
- Log execution completion
- Log warnings
- Log errors
- Log significant metrics

---

# Exception Strategy

All custom exceptions are defined in:

```
core/exceptions.py
```

Business modules raise domain-specific exceptions while avoiding generic
exceptions wherever practical.

---

# Testing Strategy

Testing is implemented using **Pytest**.

Current automated coverage:

- ColumnCleaner
- TextCleaner
- MissingValueCleaner
- DuplicateCleaner
- DataTypeCleaner

Current Result

```
5 Tests Passed
```

Every new component added to the project must include automated tests before
being considered complete.

---

# Design Principles

The architecture follows these principles:

- Single Responsibility Principle (SRP)
- Open/Closed Principle (OCP)
- Dependency Inversion Principle (DIP)
- Separation of Concerns (SoC)
- High Cohesion
- Low Coupling
- Reusability
- Testability
- Scalability
- Maintainability

---

# Current Architecture Status

| Layer | Status |
|--------|--------|
| Upload | ✅ Stable |
| Cleaning | ✅ Stable |
| Quality | 🟡 Next Sprint |
| Analytics | ⚪ Planned |
| Reporting | ⚪ Planned |
| Core Infrastructure | ✅ Stable |

---

# Architecture Governance

Changes affecting module boundaries, dependency direction, manager
responsibilities, or data flow require a new Architecture Decision Record (ADR).

This ensures architectural consistency as the project evolves.

---

**Current Architecture Version:** v2.0.0