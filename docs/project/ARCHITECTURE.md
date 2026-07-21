# AnalystGPT Enterprise Architecture

> **Purpose**
>
> This document defines the architecture of AnalystGPT Enterprise.
> It describes the system structure, module responsibilities,
> dependency rules, data flow, and architectural principles.
>
> This document reflects the implementation as of **v6.0.0**.

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
- Enterprise Orchestration

Each business capability is implemented as an independent module with a single, well-defined responsibility.

As of Sprint 6, a dedicated Application layer coordinates all business modules while a Persistence layer manages database interactions. Business modules remain persistence-agnostic and never orchestrate one another or execute SQL directly.

---
## Architectural Goals

The architecture is designed to satisfy the following long-term engineering goals:

- Independent module evolution
- Stable public contracts between modules
- High testability through isolated business components
- Clear ownership boundaries
- Predictable dependency direction
- Simple integration of future capabilities
- Enterprise maintainability over long-term development
---

# High-Level Architecture

```text
                     main.py
                        │
                        ▼
                Application.run()
                        │
 ┌──────────────────────┼──────────────────────┐
 │                      │                      │
 ▼                      ▼                      ▼

UploadManager → CleaningManager → QualityManager
                                   │
                                   ▼
                          AnalyticsManager
                                   │
                                   ▼
                          ReportingManager
                                   │
                                   ▼
                        PersistenceManager
                                   │
                                   ▼
                         Repository Layer
                                   │
                                   ▼
                               SQLite
                                   │
                                   ▼
                          PipelineResult
```

---
## Architectural Layers

The repository is intentionally organized into five architectural layers.

### Presentation Layer

Responsible for application startup.

Current component:

- main.py

### Application Layer

Responsible for orchestration only.

### Current Components

- Application
- PipelineResult
---
### Architectural Constraints

The Application layer:

- may call any business manager.
- may build PipelineResult.
- may log pipeline summaries.
- may coordinate execution order.

The Application layer must not implement business logic belonging to individual modules.
---

### Business Layer

Contains independent business modules.

- Upload
- Cleaning
- Quality
- Analytics
- Reporting

### Persistence Layer

Responsible for application persistence.

Current components:

- PersistenceManager
- PersistenceResult

Responsibilities:

- Coordinate persistence workflow
- Isolate repositories from the Application layer
- Manage pipeline lifecycle persistence
- Persist datasets
- Persist quality reports
- Persist analytics reports
- Persist reporting metadata

### Infrastructure Layer

Provides reusable infrastructure, configuration, logging,
exception handling, and database services shared across the
entire application.

---

# Layered Architecture

```text
Presentation Layer

main.py

↓

Application Layer

Application

↓

Business Layer

Upload
Cleaning
Quality
Analytics
Reporting

↓

Persistence Layer

PersistenceManager

↓

Infrastructure Layer

Repository Layer
SQLite Database
Logger
Configuration
Exceptions
Constants

↓

External Libraries

Pandas
SQLite3
Pytest
OpenPyXL
JSON
```

---

# Module Responsibilities

## main.py

Responsibilities

- Start application
- Parse input
- Invoke `Application.run()`

Must never contain business logic or orchestrate business modules directly.

---

## Application Layer

Responsibilities

- Pipeline orchestration
- Workflow sequencing
- Stage coordination
- Persistence lifecycle
- Execution timing
- Error handling
- Pipeline summary logging
- Build `PipelineResult`

The Application layer is the only component allowed to coordinate multiple business modules. Business modules remain independent and unaware of one another.

The Application layer is also responsible for:

- Initializing persistence
- Starting pipeline execution records
- Persisting pipeline outputs
- Marking successful execution
- Recording failed executions
- Gracefully shutting down database resources

---

## Upload Module

### Owner

UploadManager

### Components

- UploadManager
- CSVReader
- ExcelReader
- JSONReader

### Input

Dataset Path

### Supported Formats

- CSV
- Excel
- JSON

### Planned Formats

- SQL Databases
- REST APIs
- XML
- Parquet

### Output

Pandas DataFrame

### Responsibility

Acquire data from supported sources and convert it into a standardized DataFrame.

### Status

✅ Stable

---

## Cleaning Module

### Owner

CleaningManager

### Components

- CleaningManager
- ColumnCleaner
- TextCleaner
- MissingValueCleaner
- DuplicateCleaner
- DataTypeCleaner

### Input

Raw DataFrame

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

### Output

Cleaned DataFrame

### Responsibility

Normalize datasets before quality assessment.

### Status

✅ Stable

---

## Quality Module

### Owner

QualityManager

### Components

- QualityManager
- CompletenessChecker
- ValidityChecker
- ConsistencyChecker
- UniquenessChecker
- OutlierChecker
- QualityReport

### Input

Cleaned DataFrame

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
```

### Output

QualityReport

### Responsibility

Assess dataset quality before analytical processing.

### Status

✅ Stable

---

## Analytics Module

### Owner

AnalyticsManager

### Components

- AnalyticsManager
- DescriptiveStatistics
- NumericalAnalysis
- CategoricalAnalysis
- CorrelationAnalysis
- DistributionAnalysis
- AnalyticsReport

### Input

Validated DataFrame

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
```

### Output

AnalyticsReport

### Responsibility

Generate reusable analytical insights from validated datasets.

### Status

✅ Stable

---

## Reporting Module

### Owner

ReportingManager

### Components

- ReportingManager
- ExecutiveSummary
- KPIFormatter
- ReportBuilder
- StructuredReport
- ReportingReport
- TextReportExporter

### Input

AnalyticsReport

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
ReportingReport
```

### Current Export Format

- Plain Text (.txt)

### Planned Export Formats

- JSON
- HTML
- Excel
- PDF

### Features

- Executive summary generation
- KPI extraction
- Structured business reports
- Timestamped report exports
- Configurable export directory
- Centralized report orchestration

### Output

ReportingReport

### Responsibility

Transform analytical results into structured, professional business reports.

### Status

✅ Stable

---

# Persistence Module

### Owner

PersistenceManager

### Components

- PersistenceManager
- PersistenceReport
- PersistenceResult

### Dependencies

- DatabaseManager
- SchemaManager
- Repository Layer

### Repository Components

- BaseRepository
- PipelineRunRepository
- DatasetRepository
- QualityRepository
- AnalyticsRepository
- ReportRepository

### Input

- QualityReport
- AnalyticsReport
- ReportingReport

### Output

PersistenceResult

### Responsibility

Persist application execution metadata while keeping business modules independent from database concerns.

### Status

✅ Stable

---

# Shared Infrastructure and Database Services

The `core` package provides infrastructure shared across every business module and the Application layer. It remains isolated from business modules — business modules may depend on `core`, but `core` never depends on business modules.

```text
src/core/

config.py
constants.py
logger.py
exceptions.py
```

Database infrastructure now includes:

- SQLiteConnection
- DatabaseManager
- SchemaManager
- BaseRepository
- PipelineRunRepository
- DatasetRepository
- QualityRepository
- AnalyticsRepository
- ReportRepository

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
Application
     │
     ▼
Business Modules
     │
     ▼
Persistence
     │
     ▼
Repository Layer
     │
     ▼
Database
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
 │
 ▼
Application
```

Business modules remain completely unaware of persistence.

Only the Application layer communicates with the Persistence layer.

Repositories are the only components permitted to execute SQL.

This separation allows future database technologies (such as PostgreSQL)
to be introduced without requiring changes to business logic.

---

# Stable Contracts

| Module | Output |
|---------|--------|
| Upload | DataFrame |
| Cleaning | DataFrame |
| Quality | QualityReport |
| Analytics | AnalyticsReport |
| Reporting | ReportingReport |
| Persistence | PersistenceResult |
| Application | PipelineResult |

Stable contracts reduce coupling and simplify future extensions.

---
## Contract Stability Policy

Stable contracts are treated as public interfaces.

Internal implementation may evolve without affecting other modules, provided these contracts remain unchanged.

Breaking a contract requires:

- Architecture review
- Updated ADR
- Updated tests
- Updated documentation

---

# Data Flow

```text
Dataset Path
  ↓
Upload
  ↓
Raw DataFrame
  ↓
Cleaning
  ↓
Clean DataFrame
  ↓
Quality
  ↓
QualityReport
  ↓
Analytics
  ↓
AnalyticsReport
  ↓
Reporting
  ↓
ReportingReport
  ↓
Persistence
  ↓
PersistenceResult
  ↓
PipelineResult
```

---

# Manager-Orchestrator Pattern

Every business module exposes one manager responsible for internal orchestration; the Application layer orchestrates across managers.

| Module | Manager |
|---------|---------|
| Upload | UploadManager |
| Cleaning | CleaningManager |
| Quality | QualityManager |
| Analytics | AnalyticsManager |
| Reporting | ReportingManager |
| Persistence | PersistenceManager |
| Application | Application |

Managers coordinate workflows while business logic remains inside dedicated components.

---

## Ownership Principle

Every architectural component has exactly one owner.

Examples:

- UploadManager owns Upload Module orchestration.
- CleaningManager owns Cleaning Module orchestration.
- QualityManager owns Quality Module orchestration.
- AnalyticsManager owns Analytics Module orchestration.
- ReportingManager owns Reporting Module orchestration.
- PersistenceManager owns Persistence Module orchestration.
- Application owns pipeline orchestration.

Ownership is never shared across modules.

---

# Logging Strategy

Centralized logging is implemented through:

```text
src/core/logger.py
```

Every manager, and the Application layer itself, performs:

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
src/core/exceptions.py
```

Business modules and the Application layer raise domain-specific exceptions instead of generic exceptions whenever practical. The Application layer is responsible for top-level failure handling across the pipeline.

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

### Persistence

- PersistenceManager
- PersistenceResult
- PipelineRunRepository
- DatasetRepository
- QualityRepository
- AnalyticsRepository
- ReportRepository

### Application Layer

Validated through:

- End-to-end integration testing
- Complete pipeline execution
- PipelineResult validation

Dedicated Application unit tests are planned as the Application layer continues to evolve.

### Integration

- Complete end-to-end pipeline execution

Current results:

```text
82 Tests Passed
0 Failed
0 Errors
0 Warnings
```

Every completed component must include automated unit tests before release. Automated testing validates every architectural change.

---

# Performance Validation

The platform has been validated using datasets of increasing scale.

| Dataset | Size | Status |
|---------|------:|--------|
| Sample Dataset | 500 rows | ✅ Passed |
| Large Dataset | 100,000 rows | ✅ Passed |
| Stress Dataset | 1,000,000 rows | ✅ Passed |

## Observed Results

- Successful execution through Application.run()
- Successful pipeline orchestration
- Stable memory usage
- Successful report generation
- Successful report export
- Complete end-to-end validation
- No runtime failures
- 82 / 82 automated tests remained passing after the Sprint 6 persistence integration.

The platform successfully completed:

- Standard dataset execution
- Large dataset execution (~100K rows)
- Stress dataset execution (~1M rows)
- SQLite persistence validation
- Report generation validation

---

# Repository Structure
```text
AnalystGPT_Enterprise/

docs/
├── adr/
├── engineering/
├── project/
└── sprints/

performance/
├── datasets/
├── benchmark_results.md
└── README.md

reports/

sample_data/

src/
├── application/
│   ├── app.py
│   ├── pipeline_result.py
│   └── __init__.py
├── upload/
├── cleaning/
├── quality/
├── analytics/
├── reporting/
│   └── exporters/
├── persistence/
│   ├── persistence_manager.py
│   ├── persistence_result.py
│   ├── persistence_report.py
│   └── __init__.py
├── database/
│   ├── sqlite_connection.py
│   ├── database_manager.py
│   ├── schema_manager.py
│   ├── __init__.py
│   └── repositories/
│       ├── base_repository.py
│       ├── pipeline_run_repository.py
│       ├── dataset_repository.py
│       ├── quality_repository.py
│       ├── analytics_repository.py
│       ├── report_repository.py
│       └── __init__.py
└── core/

tests/
├── analytics/
├── application/
├── cleaning/
├── quality/
├── reporting/
├── persistence/
├── integration/
└── fixtures/

main.py
README.md
CHANGELOG.md
requirements.txt
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
- Enterprise Orchestration
- Typed Domain Models
- Stable Module Contracts

---

# Current Architecture Status

| Layer | Status |
|--------|--------|
| Presentation | ✅ Stable |
| Application | ✅ Stable |
| Upload | ✅ Stable |
| Cleaning | ✅ Stable |
| Quality | ✅ Stable |
| Analytics | ✅ Stable |
| Reporting | ✅ Stable |
| Persistence | ✅ Stable |
| Database Infrastructure | ✅ Stable |
| Core Infrastructure | ✅ Stable |

---

# Sprint 6 — SQLite Persistence

Sprint 6 introduced a dedicated persistence layer that stores pipeline execution metadata, datasets, and reports in SQLite.

Major improvements:

- Introduced Persistence module and PersistenceManager.
- Added SQLite database infrastructure.
- Added SchemaManager for automated schema initialization.
- Added Repository pattern to abstract database operations.
- Added DatabaseManager lifecycle management.
- Isolated all SQL execution inside repositories.
- Integrated persistence into Application.run().
- Preserved business module persistence-agnostic design.
- Extended automated testing to 82 passing tests.
- Successfully validated large and stress datasets.
- Established the foundation for PostgreSQL migration.

---

# Future Evolution

The current architecture provides a stable foundation for continued, sequenced evolution. The Application layer remains the single orchestration point as the platform grows.

## Sprint 7

Production PostgreSQL integration

- PostgreSQL connection management
- Repository compatibility
- Transaction support
- Environment-based configuration
- Database migration preparation

## Sprint 8

Production REST API

- FastAPI
- REST endpoints
- OpenAPI documentation
- Authentication preparation

## Sprint 9

Power BI Integration

- Dashboard publishing
- KPI visualization
- Interactive reporting
- Enterprise reporting connectors

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

**Current Architecture Version:** **v6.0.0**

**Previous Version:** **v5.5.0**