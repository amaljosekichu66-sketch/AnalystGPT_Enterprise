# AnalystGPT Enterprise Architecture

> **Purpose**
>
> This document defines the architecture of AnalystGPT Enterprise.
> It describes the system structure, module responsibilities,
> dependency rules, data flow, and architectural principles.
>
> This document reflects the implementation as of **v4.0.0**.

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

Each business capability is implemented as an independent module with a single, well-defined responsibility.

---

# High-Level Architecture

```text
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
         ReportingManager (Sprint 5)
```

---

# Layered Architecture

```text
Presentation Layer

        main.py

────────────────────────────────────

Business Layer

Upload
Cleaning
Quality
Analytics
Reporting

────────────────────────────────────

Shared Infrastructure

core/

────────────────────────────────────

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

sample_data/

src/
├── analytics/
├── cleaning/
├── core/
├── quality/
├── reporting/
└── upload/

tests/
├── analytics/
├── cleaning/
├── fixtures/
├── integration/
└── quality/

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

Evaluate data quality before analytical processing.

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

Transform analytical results into business-ready reports.

### Planned Outputs

- Console Reports
- JSON Reports
- HTML Reports
- Excel Reports
- PDF Reports

### Status

🚧 Sprint 5

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

Application configuration.

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

Business modules communicate through standardized DataFrames and structured dictionaries rather than direct coupling.

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

ReportingManager (Sprint 5)
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

Managers coordinate workflows.

Business logic remains inside dedicated components.

---

# Logging Strategy

Centralized logging is implemented through:

```text
core/logger.py
```

Every manager should:

- Log pipeline start
- Log pipeline completion
- Log execution timing
- Log warnings
- Log errors
- Log important execution metrics

---

# Exception Strategy

Custom exceptions are defined in:

```text
core/exceptions.py
```

Business modules raise domain-specific exceptions rather than generic exceptions whenever practical.

---

# Testing Strategy

Testing is implemented using **Pytest**.

Current coverage includes:

### Upload

Covered through pipeline integration.

### Cleaning

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

### Integration

- Complete pipeline execution

Current results:

```text
60 Tests Passed
0 Failed
0 Errors
0 Warnings
```

Every completed business component must include automated tests before release.

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

---

# Current Architecture Status

| Layer | Status |
|--------|--------|
| Upload | ✅ Stable |
| Cleaning | ✅ Stable |
| Quality | ✅ Stable |
| Analytics | ✅ Stable |
| Reporting | 🚧 Sprint 5 |
| Core Infrastructure | ✅ Stable |

---

# Future Evolution

The architecture will continue evolving through future sprints:

- Reporting Layer
- SQLite Integration
- PostgreSQL Integration
- REST APIs
- Power BI Integration
- Streamlit UI
- AI Insights
- Production Deployment

Each architectural change affecting module boundaries or dependency direction must be documented through a new Architecture Decision Record (ADR).

---

**Current Architecture Version:** **v4.0.0**