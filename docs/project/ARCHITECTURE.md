# AnalystGPT Enterprise Architecture

> **Purpose**
>
> This document defines the architecture of AnalystGPT Enterprise.
> It describes the system structure, module responsibilities,
> dependency rules, data flow, and architectural principles.
>
> This document reflects the implementation as of **v5.0.0**.

---

# Architecture Philosophy

AnalystGPT Enterprise follows a modular, layered architecture built around:

- Separation of Concerns (SoC)
- SOLID Principles
- Low Coupling
- High Cohesion
- Testability
- Scalability
- Maintainability
- Enterprise Modularity

Each business capability is implemented as an independent module with a single, well-defined responsibility.

---

# High-Level Architecture

                     main.py
                        │
                        ▼
               UploadManager
                        │
                        ▼
              CleaningManager
                        │
                        ▼
               QualityManager
                        │
                        ▼
              AnalyticsManager
                        │
                        ▼
              ReportingManager
                        │
                        ▼
         Structured Business Report
                        │
                        ▼
              Text Report (.txt)
---

# Layered Architecture

```text
Presentation Layer

            main.py

──────────────────────────────────────────

Business Layer

Upload
Cleaning
Quality
Analytics
Reporting

──────────────────────────────────────────

Shared Infrastructure

core/

──────────────────────────────────────────

External Libraries

Pandas
OpenPyXL
JSON
Pytest
Logging
```

---

# Repository Structure

```text
AnalystGPT_Enterprise/

docs/
├── adr/
├── engineering/
└── sprints/

performance/
├── datasets/
└── benchmark_results.md

sample_data/

src/
├── analytics/
├── cleaning/
├── core/
├── quality/
├── reporting/
│   └── exporters/
└── upload/

tests/
├── analytics/
├── cleaning/
├── fixtures/
├── integration/
├── quality/
└── reporting/

main.py
```

---

# Stable Modules

## Upload Module

### Responsibility

Acquire datasets from supported file formats and convert them into a standardized Pandas DataFrame.

### Components

- UploadManager
- CSVReader
- ExcelReader
- JSONReader

### Supported Formats

- CSV
- Excel
- JSON

### Output

```text
Pandas DataFrame
```

### Status

✅ Stable

---

## Cleaning Module

### Responsibility

Normalize uploaded datasets before quality assessment.

### Components

- CleaningManager
- ColumnCleaner
- TextCleaner
- MissingValueCleaner
- DuplicateCleaner
- DataTypeCleaner

### Pipeline

```text
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

Clean DataFrame
```

### Status

✅ Stable

---

## Quality Module

### Responsibility

Evaluate dataset quality before analytical processing.

### Components

- QualityManager
- CompletenessChecker
- ValidityChecker
- ConsistencyChecker
- UniquenessChecker
- OutlierChecker
- QualityReport

### Pipeline

```text
Clean DataFrame

↓

CompletenessChecker

↓

ValidityChecker

↓

ConsistencyChecker

↓

UniquenessChecker

↓

OutlierChecker

↓

QualityReport

↓

Quality Assessment Report
```

### Output

```text
Quality Assessment Report
```

### Status

✅ Stable

---

## Analytics Module

### Responsibility

Generate reusable analytical insights from validated datasets.

### Components

- AnalyticsManager
- DescriptiveStatistics
- NumericalAnalysis
- CategoricalAnalysis
- CorrelationAnalysis
- DistributionAnalysis
- AnalyticsReport

### Pipeline

```text
Validated Data

↓

DescriptiveStatistics

↓

NumericalAnalysis

↓

CategoricalAnalysis

↓

CorrelationAnalysis

↓

DistributionAnalysis

↓

AnalyticsReport

↓

Analytics Summary
```

### Output

```text
Analytics Report
```

### Status

✅ Stable

---

## Reporting Module

### Responsibility

Transform analytical results into structured business reports suitable for enterprise users.

### Components

- ReportingManager
- ExecutiveSummary
- KPIFormatter
- ReportBuilder
- StructuredReport
- ReportingReport
- TextReportExporter

### Current Export Format

- Plain Text (.txt)

### Planned Export Formats

- JSON
- HTML
- Excel
- PDF

### Pipeline

```text
Analytics Report

↓

ExecutiveSummary

↓

KPIFormatter

↓

ReportBuilder

↓

StructuredReport

↓

TextReportExporter

↓

Structured Business Report
      │
      ▼
Text Report (.txt)
```

### Features

- Executive summary generation
- KPI extraction
- Structured business reports
- Timestamped report exports
- Configurable export directory
- Centralized report orchestration

### Status

✅ Stable
---

# Shared Infrastructure

The `core` package provides infrastructure shared across every business module.

```text
core/

config.py
constants.py
logger.py
exceptions.py
```

### Responsibilities

#### config.py

Centralized application configuration including:

- Logging configuration
- Cleaning configuration
- Report export configuration
- Shared application settings

#### constants.py

Application-wide constants.

#### logger.py

Centralized logging configuration.

#### exceptions.py

Custom exception hierarchy.

---

# Dependency Rules

## Allowed

```text
Business Modules
        │
        ▼
      core
```

## Not Allowed

```text
core
 │
 ▼
Business Modules
```

Business modules communicate through standardized DataFrames and structured report objects rather than tightly coupled implementations.

---

# Data Flow

```text
CSV / Excel / JSON

        │

        ▼

UploadManager

        │

        ▼

Pandas DataFrame

        │

        ▼

CleaningManager

        │

        ▼

Clean DataFrame

        │

        ▼

QualityManager

        │

        ▼

Quality Assessment Report

        │

        ▼

AnalyticsManager

        │

        ▼

Analytics Report

        │

        ▼

ReportingManager

        │

        ▼

Structured Report

        │

        ▼

TextReportExporter

        │

        ▼

Timestamped Business Report (.txt)
```

---

# Manager-Orchestrator Pattern

Every business module exposes one manager responsible for orchestration.

| Module | Manager |
|---------|---------|
| Upload | UploadManager |
| Cleaning | CleaningManager |
| Quality | QualityManager |
| Analytics | AnalyticsManager |
| Reporting | ReportingManager |

Managers coordinate workflows while business logic remains inside dedicated components.

---

# Logging Strategy

Centralized logging is implemented through:

```text
core/logger.py
```

Every manager performs:

- Pipeline start logging
- Pipeline completion logging
- Execution timing
- Component execution logging
- Warning logging
- Error logging
- Pipeline summary logging

---

# Exception Strategy

Custom exceptions are defined in:

```text
core/exceptions.py
```

Business modules raise domain-specific exceptions instead of generic exceptions whenever practical.

---

# Testing Strategy

Testing is implemented using **Pytest**.

Current coverage includes:

### Upload

- UploadManager
- CSVReader
- ExcelReader
- JSONReader

### Cleaning

- CleaningManager
- ColumnCleaner
- TextCleaner
- MissingValueCleaner
- DuplicateCleaner
- DataTypeCleaner

### Quality

- QualityManager
- CompletenessChecker
- ValidityChecker
- ConsistencyChecker
- UniquenessChecker
- OutlierChecker
- QualityReport

### Analytics

- AnalyticsManager
- AnalyticsReport
- DescriptiveStatistics
- NumericalAnalysis
- CategoricalAnalysis
- CorrelationAnalysis
- DistributionAnalysis

### Reporting

- ReportingManager
- ExecutiveSummary
- KPIFormatter
- ReportBuilder
- StructuredReport
- ReportingReport
- TextReportExporter

### Integration

- Complete end-to-end pipeline

Current results:

```text
79 Tests Passed
0 Failed
0 Errors
0 Warnings
```

Every completed component must include automated unit tests before release.

---

# Performance Validation

The platform has been validated using datasets of increasing scale.

| Dataset | Size | Status |
|---------|------:|--------|
| Sample Dataset | 500 rows | ✅ Passed |
| Large Dataset | 100,000 rows | ✅ Passed |
| Stress Dataset | 1,000,000 rows | ✅ Passed |

Observed characteristics:

- Stable memory usage
- Successful report generation
- Complete pipeline execution
- No runtime failures
- Timestamped report export
- End-to-end validation completed

Performance datasets are maintained under:

```text
performance/
├── datasets/
└── benchmark_results.md
```

---

# Design Principles

The architecture follows:

- Single Responsibility Principle (SRP)
- Open / Closed Principle (OCP)
- Dependency Inversion Principle (DIP)
- Separation of Concerns (SoC)
- High Cohesion
- Low Coupling
- Reusability
- Testability
- Scalability
- Maintainability
- Enterprise Modularity

---

# Current Architecture Status

| Layer | Status |
|--------|--------|
| Upload | ✅ Stable |
| Cleaning | ✅ Stable |
| Quality | ✅ Stable |
| Analytics | ✅ Stable |
| Reporting | ✅ Stable |
| Core Infrastructure | ✅ Stable |

---

# Future Evolution

The architecture will continue evolving through future releases.

## Sprint 5.5 — Architecture Refactor

- Introduce Application class
- Thin `main.py`
- Strongly typed pipeline contracts
- Standardized report interfaces
- Dependency cleanup
- Integration test simplification

## Sprint 6

SQLite persistence layer

## Sprint 7

PostgreSQL integration

## Sprint 8

REST API layer

## Sprint 9

Power BI integration

## Sprint 10

Interactive Streamlit application

## Sprint 11

AI-generated business insights

## Sprint 12

Production deployment

- Docker
- CI/CD
- Monitoring
- Cloud deployment

Every architectural change affecting module boundaries or dependency direction must be documented through a new Architecture Decision Record (ADR).

---

**Current Architecture Version:** **v5.0.0**