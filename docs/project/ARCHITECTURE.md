```markdown
# AnalystGPT Enterprise Architecture

> **Purpose**
>
> This document defines the architecture of AnalystGPT Enterprise.
> It describes the system structure, module responsibilities,
> dependency rules, data flow, and architectural principles.
>
> This document reflects the implementation as of **v10.0.0**.

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

As of Sprint 7, a dedicated Application layer coordinates all business modules while a Database Abstraction Layer manages database engine selection and connection lifecycle. Business modules remain persistence-agnostic and never orchestrate one another or execute SQL directly.

Sprint 8 introduced a dedicated REST API Layer that exposes the Application Layer through HTTP endpoints while preserving existing business module independence. The API layer is built on FastAPI, uses dependency injection for application lifecycle management, and provides OpenAPI 3.1 documentation and Swagger UI. The API layer remains thin, containing no business logic, and delegates all operations to the Application Layer.

Sprint 9 introduced a dedicated Business Intelligence Integration Layer
that exposes dashboard-ready analytics through Power BI endpoints.

The Business Intelligence Layer remains an integration layer rather than
a business layer. It communicates only with the Application Layer,
preserving existing module independence and stable business contracts.

Sprint 10 introduced a dedicated Enterprise Streamlit Frontend Layer
that provides an interactive web interface for the analytics pipeline.

The Frontend Layer is built using Streamlit with a React-ready architecture,
consuming the REST API as its sole backend interface. It contains zero
business logic and communicates exclusively through the established REST API,
preserving the integrity of the enterprise layered architecture and enabling
future migration to React without backend changes.

---

# Architectural Goals

The architecture is designed to satisfy the following long-term engineering goals:

- Independent module evolution
- Stable public contracts between modules
- High testability through isolated business components
- Clear ownership boundaries
- Predictable dependency direction
- Simple integration of future capabilities
- Enterprise maintainability over long-term development
- Database independence across relational engines
- Interface-driven infrastructure for runtime interchangeability
- Service-oriented architecture
- Stable REST API contracts
- External analytics integration
- API-first architecture
- HTTP interface abstraction
- Business Intelligence integration
- Dashboard abstraction
- Standardized dashboard contracts
- Visualization-ready data services
- External BI platform compatibility
- Frontend-backend separation
- React-ready presentation layer
- Future migration without backend changes

---

# High-Level Architecture

```text
Browser
   │
   ▼
Enterprise Streamlit Frontend
   │
   ▼
Views
   │
   ▼
Components
   │
   ▼
Frontend Services
   │
   ▼
REST API (FastAPI)
   │
   ▼
Application Layer
   │
   ▼
Application.run()
   │
   ▼
Upload
   ▼
Cleaning
   ▼
Quality
   ▼
Analytics
   ▼
Reporting
   ▼
Persistence
   │
   ▼
Database Abstraction Layer
   │
   ├── SQLite
   └── PostgreSQL
   │
   ▼
Repository Layer
   │
   ▼
DashboardService
   │
   ▼
Power BI Models
   │
   ▼
Power BI Dashboard
```

---

# Architectural Layers

The repository is intentionally organized into eight architectural layers.

## Frontend Layer

Responsible for the user interface and client-side interaction.

Current components:

- Streamlit Application
- Views
- Components
- Frontend Services
- Theme
- Session Management

Responsibilities:

- Render interactive dashboards
- Provide file upload interface
- Display reports and analytics
- Manage session state
- Handle navigation
- Communicate with REST API

Architectural constraints:

- Views contain no business logic.
- Components are presentation-only.
- Frontend Services communicate only with the REST API.
- Views never access persistence.
- Frontend remains backend-independent.
- React migration must not require backend changes.
- Business logic remains outside Streamlit.
- Navigation is centralized.
- Session State stores presentation state only.

## Presentation Layer

Responsible for application startup (legacy CLI entry point).

Current component:

- main.py

## REST API Layer

Responsible for exposing the application through HTTP endpoints.

Current components:

- FastAPI Server
- API Routes
- Dependency Injection
- Request/Response Models
- Exception Handlers

## Business Intelligence Layer

Responsible for exposing dashboard-ready analytical data.

Current components:

- DashboardService
- DashboardSummary
- DashboardStatistics
- DashboardCorrelation
- DashboardDistribution
- DashboardCategorical

Responsibilities:

- Transform reporting output into dashboard models
- Prepare visualization-ready responses
- Remain independent from analytics implementation
- Support external BI platforms

## Application Layer

Responsible for orchestration only.

### Current Components

- Application
- PipelineResult

### Architectural Constraints

The Application layer:

- may call any business manager.
- may build PipelineResult.
- may log pipeline summaries.
- may coordinate execution order.

The Application layer must not implement business logic belonging to individual modules.

## Business Layer

Contains independent business modules.

- Upload
- Cleaning
- Quality
- Analytics
- Reporting

## Persistence Layer

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

## Infrastructure Layer

Provides reusable infrastructure, configuration, logging,
exception handling, and database services shared across the
entire application.

---

# REST API Layer

### Responsibilities

- Expose REST endpoints
- Validate requests
- Serialize responses
- Delegate to Application Layer
- Generate OpenAPI
- Serve Swagger UI

### Components

- FastAPI Server
- API Routes
- Dependency Injection
- Request Models
- Response Models
- Exception Handlers

### Architectural Constraints

The REST API Layer:

- may communicate only with the Application Layer.
- must never implement business logic.
- must never communicate directly with business modules.
- must remain stateless.

---

# Frontend Layer

### Responsibilities

- Render user interface
- Handle user interactions
- Display dashboards and reports
- Manage file uploads
- Maintain session state
- Navigate between views
- Communicate with backend via REST API

### Components

- Streamlit Application
- Views (Dashboard, Upload, Reports, About)
- Reusable Components (charts, metrics, tables, navigation, uploader)
- Frontend Services (API client, session manager)
- Configuration (settings)
- Theme (styles)

### Architectural Constraints

The Frontend Layer:

- may communicate only with the REST API Layer.
- must never implement business logic.
- must never communicate directly with business modules, persistence, or repositories.
- must remain independent of backend implementation details.
- must preserve REST API contracts during future migration.

---

# Layered Architecture

```text
Frontend Layer

Browser → Streamlit → Views → Components → Frontend Services

↓

REST API Layer

FastAPI Server
API Routes
Dependency Injection
Request/Response Models
Exception Handlers

↓

Business Intelligence Layer

DashboardService
Dashboard Models

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
DatabaseManager
ConnectionFactory
DatabaseConnection
SQLiteConnection
PostgreSQLConnection
Logger
Configuration
Exceptions
Constants

↓

External Libraries

FastAPI
Pydantic
Uvicorn
Pytest
Pandas
SQLite3
psycopg 3
OpenPyXL
JSON
Streamlit
Plotly
```

---

# Module Responsibilities

## Frontend Layer

### Owner

Streamlit Application

### Components

- Views
- Components
- Frontend Services
- Session Manager

### Status

✅ Stable (MVP)

## main.py

Responsibilities

- Start application (CLI)
- Parse input
- Invoke `Application.run()`

Must never contain business logic or orchestrate business modules directly.

---

## REST API Layer

### Owner

FastAPI Server

### Responsibilities

- HTTP Interface
- Request Validation
- Response Serialization
- Endpoint Routing
- Dependency Injection
- OpenAPI
- Swagger

### Status

✅ Stable

---

## Business Intelligence Module

### Owner

DashboardService

### Components

- DashboardService
- DashboardSummary
- DashboardStatistics
- DashboardCorrelation
- DashboardDistribution
- DashboardCategorical

### Input

ReportingReport

### Output

Dashboard Models

### Responsibility

Prepare standardized, visualization-ready dashboard data
for Power BI and future Business Intelligence clients.

### Status

✅ Stable

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
- ConnectionFactory
- DatabaseConnection
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

- DatabaseConnection
- SQLiteConnection
- PostgreSQLConnection
- ConnectionFactory
- DatabaseManager
- SchemaManager
- BaseRepository
- PipelineRunRepository
- DatasetRepository
- QualityRepository
- AnalyticsRepository
- ReportRepository

REST infrastructure now includes:

- API Server
- Dependency Provider
- Request Models
- Response Models
- Exception Handlers

Business Intelligence infrastructure includes:

- DashboardService
- Dashboard Models
- Power BI Router

### Responsibilities

#### config.py

Centralized application configuration including:

- Logging configuration
- Cleaning configuration
- Report export configuration
- Shared application settings
- Database engine selection
- Connection parameters

#### constants.py

Application-wide constants including:

- Application identity
- API configuration
- Endpoint paths

#### logger.py

Centralized logging configuration.

#### exceptions.py

Custom exception hierarchy.

---

# Dependency Rules

## Allowed

```text
Browser
   │
   ▼
Frontend Layer
   │
   ▼
REST API
   │
   ▼
Business Intelligence
   │
   ▼
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
DatabaseConnection
   │
   ▼
SQLiteConnection / PostgreSQLConnection
   │
   ▼
Database Engine
   │
   ▼
core
```

## Not Allowed

```text
Frontend Layer
   │
   ▼
Business Modules
```

```text
Frontend Layer
   │
   ▼
Persistence
```

```text
Frontend Layer
   │
   ▼
Repositories
```

```text
REST API
   │
   ▼
Business Modules
```

```text
REST API
   │
   ▼
Persistence
```

```text
REST API
   │
   ▼
Repositories
```

```text
Business Intelligence
   │
   ▼
Business Modules (directly)
```

```text
core
   │
   ▼
Business Modules
```

```text
core
   │
   ▼
Application
```

Business modules remain completely unaware of persistence, HTTP, and UI concerns.

Only the Application layer communicates with the Persistence layer.

Repositories are the only components permitted to execute SQL, and they operate through the DatabaseConnection abstraction.

The REST API Layer communicates only with the Application Layer through dependency injection.

The Business Intelligence Layer communicates only with the
Application Layer and must never access business modules
or persistence components directly.

The Frontend Layer communicates only with the REST API Layer.

This separation allows future frontend technologies, database technologies, and API changes to be introduced without requiring changes to business logic.

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
| REST API | PipelineResponse |
| DashboardService | Dashboard Models |
| Power BI API | Dashboard Responses |
| Frontend Views | UI Render |
| Frontend Components | UI Elements |
| Frontend Services | API Requests |

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
Browser Interaction
      │
      ▼
Frontend View
      │
      ▼
Frontend Service (API Client)
      │
      ▼
REST API Endpoint
      │
      ▼
Application.run()
      │
      ▼
Upload
      ▼
Cleaning
      ▼
Quality
      ▼
Analytics
      ▼
Reporting
      ▼
Dashboard Models
      ▼
REST Response
      ▼
Frontend Render
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
| Business Intelligence | DashboardService |
| Frontend | Streamlit Application |

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
- FastAPI Server owns REST API Layer.
- DashboardService owns Business Intelligence orchestration.
- Streamlit Application owns Frontend Layer.

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

REST API logging includes:

- Request logging
- Response logging
- Endpoint execution logging

Frontend logging includes:

- User actions
- Navigation events
- API request/response logging (development)

---

# Exception Strategy

Custom exceptions are defined in:

```text
src/core/exceptions.py
```

Business modules and the Application layer raise domain-specific exceptions instead of generic exceptions whenever practical. The Application layer is responsible for top-level failure handling across the pipeline.

Global REST exception handlers provide:

- Consistent HTTP error responses
- Standardized error format
- Proper HTTP status codes

Frontend error handling:

- Display user-friendly error messages
- Log errors for debugging
- Graceful degradation

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

### API Layer

- Root Endpoint
- Health Endpoint
- Version Endpoint
- Pipeline Endpoint
- Swagger Validation
- OpenAPI Validation

### Business Intelligence

- Dashboard endpoint
- Summary endpoint
- Statistics endpoint
- Correlation endpoint
- Distribution endpoint
- Categorical endpoint
- Report endpoint
- Pipeline endpoint

### Frontend

- Dashboard view
- Upload interface
- Reports view
- About page
- Navigation
- Session state
- Frontend services
- API client integration

### Application Layer

Validated through:

- End-to-end integration testing
- Complete pipeline execution
- PipelineResult validation
- REST API execution validation
- Frontend-to-backend integration testing

### Integration

- Complete end-to-end pipeline execution
- REST API integration testing
- Frontend-backend integration testing

Current results:

All available automated tests passing.

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
- All automated tests remained passing after Business Intelligence and Frontend integration.
- REST API execution validated
- Swagger validation passed
- OpenAPI generation validated
- HTTP request/response validation passed
- Power BI endpoint validation
- Dashboard generation validation
- SQLite runtime validation
- PostgreSQL runtime validation
- Benchmark execution validation
- Stress testing validation
- Frontend rendering performance
- API response times
- Session state management

The platform successfully completed:

- Standard dataset execution
- Large dataset execution (~100K rows)
- Stress dataset execution (~1M rows)
- SQLite persistence validation
- PostgreSQL architecture validation
- Report generation validation
- REST API validation
- End-to-end HTTP pipeline execution
- Frontend interface validation

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
├── api/
│   ├── server.py
│   ├── routes/
│   │   ├── root.py
│   │   ├── health.py
│   │   ├── version.py
│   │   ├── pipeline.py
│   │   └── __init__.py
│   ├── models/
│   │   ├── request_models.py
│   │   ├── response_models.py
│   │   └── __init__.py
│   ├── dependencies/
│   │   ├── app_dependency.py
│   │   └── __init__.py
│   ├── exceptions/
│   │   ├── exception_handlers.py
│   │   └── __init__.py
│   └── __init__.py
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
│   ├── database_connection.py
│   ├── sqlite_connection.py
│   ├── postgresql_connection.py
│   ├── connection_factory.py
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
├── integrations/
│   ├── __init__.py
│   └── powerbi/
│       ├── __init__.py
│       ├── dashboard_service.py
│       └── powerbi_models.py
├── frontend/
│   ├── streamlit_app.py
│   ├── views/
│   │   ├── dashboard_page.py
│   │   ├── upload_page.py
│   │   ├── report_page.py
│   │   └── about_page.py
│   ├── components/
│   │   ├── charts.py
│   │   ├── metrics.py
│   │   ├── tables.py
│   │   ├── navigation.py
│   │   └── uploader.py
│   ├── services/
│   │   ├── api_client.py
│   │   └── session_manager.py
│   ├── config/
│   │   └── settings.py
│   ├── theme/
│   │   └── styles.py
│   ├── assets/
│   └── static/
└── core/

tests/
├── analytics/
├── application/
├── cleaning/
├── quality/
├── reporting/
├── persistence/
├── api/
│   ├── test_root.py
│   ├── test_health.py
│   ├── test_version.py
│   ├── test_pipeline.py
│   ├── test_powerbi.py
│   └── __init__.py
├── frontend/
│   ├── test_views.py
│   ├── test_services.py
│   └── __init__.py
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
- Dependency Injection
- Database Abstraction
- Interface Segregation
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
- REST API Design
- API-first Architecture
- Service-oriented Architecture
- Request/Response Contracts
- Frontend-Backend Separation
- React-ready Architecture

---

# Current Architecture Status

| Layer | Status |
|--------|--------|
| Frontend | ✅ MVP Complete |
| Presentation | ✅ Stable |
| REST API Layer | ✅ Stable |
| Business Intelligence Layer | ✅ Stable |
| Application | ✅ Stable |
| Upload | ✅ Stable |
| Cleaning | ✅ Stable |
| Quality | ✅ Stable |
| Analytics | ✅ Stable |
| Reporting | ✅ Stable |
| Persistence | ✅ Stable |
| Database Abstraction Layer | ✅ Stable |
| Core Infrastructure | ✅ Stable |
| OpenAPI | ✅ Stable |
| Swagger | ✅ Stable |

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
- Extended automated testing.
- Successfully validated large and stress datasets.
- Established the foundation for PostgreSQL migration.

---

# Sprint 7 — Database Abstraction & PostgreSQL Integration

Sprint 7 transformed the persistence layer into a database-agnostic architecture, enabling interchangeable SQLite and PostgreSQL backends.

Major improvements:

- Introduced DatabaseConnection abstraction and common interface.
- Added PostgreSQLConnection with psycopg 3 integration.
- Added ConnectionFactory for runtime database engine selection.
- Refactored SQLiteConnection to implement DatabaseConnection.
- Extended SchemaManager to support multiple SQL dialects.
- Made repositories cross-database compatible with placeholder conversion.
- Updated PersistenceManager to use dependency injection.
- Centralized database configuration for engine selection.
- Preserved all stable module contracts and business logic.
- Maintained automated test passing.
- Validated SQLite runtime and PostgreSQL architecture.

---

# Sprint 8 — REST API Integration

Sprint 8 introduced a dedicated REST API Layer that exposes the complete analytics pipeline through HTTP endpoints.

Major improvements:

- Introduced FastAPI server and REST API Layer.
- Added API routing infrastructure with root, health, version, and pipeline endpoints.
- Implemented dependency injection for Application lifecycle management.
- Created standardized request and response contracts using Pydantic.
- Added global exception handlers for consistent error responses.
- Generated OpenAPI 3.1 specification automatically.
- Served Swagger UI for interactive API documentation.
- Preserved all stable module contracts and business logic.
- Extended automated testing.
- Validated REST API execution, Swagger UI, and OpenAPI generation.
- Successfully validated large and stress datasets through HTTP endpoints.

---

# Sprint 9 — Power BI Integration

Sprint 9 introduced a dedicated Business Intelligence Integration Layer
that exposes dashboard-ready analytics through Power BI endpoints.

Major improvements:

- Introduced Business Intelligence Layer.
- Added DashboardService.
- Added dashboard response models.
- Added Power BI REST endpoints.
- Added benchmark framework.
- Added stress testing framework.
- Extended automated testing.
- Validated SQLite runtime.
- Validated PostgreSQL runtime.
- Successfully validated one million row datasets.

---

# Sprint 10 — Enterprise Streamlit Frontend

Sprint 10 introduced a dedicated Enterprise Streamlit Frontend Layer
that provides an interactive web interface for the analytics pipeline.

Major improvements:

- Added Frontend Layer with Streamlit.
- Implemented Dashboard view.
- Added Upload interface.
- Added Reports Centre.
- Added About page.
- Created reusable component library.
- Implemented Frontend Services (API client, session manager).
- Added enterprise navigation.
- Integrated with REST API.
- Ensured React-ready architecture.
- Preserved all stable module contracts and business logic.
- Extended automated testing (frontend validation).
- Validated frontend-backend integration.
- Prepared for future React migration.

---

# React Migration Constraint

The Streamlit frontend serves as the MVP presentation layer.

Future React migration shall preserve:

- REST API contracts
- Application Layer
- Business modules
- Persistence Layer
- Database Abstraction Layer

Only the Presentation Layer (Frontend) may be replaced.

All backend infrastructure and contracts must remain unchanged during the migration.

This constraint ensures that the architectural integrity of the backend
and the service boundaries remain intact, allowing a smooth transition
to a modern React frontend when the time comes.

---

# Future Evolution

The current architecture provides a stable foundation for continued, sequenced evolution. The Application layer remains the single orchestration point as the platform grows, while the REST API Layer provides the interface for external integrations.

## Sprint 11 — AI Insight Engine

- Executive Summary Generator
- Recommendation Engine
- Narrative Generation
- Explainable Analytics
- Dashboard AI
- Report AI

## Sprint 12 — Production Deployment

- Docker
- CI/CD
- Monitoring
- Cloud deployment

## Sprint 15 — React Migration

- Replace Streamlit with React
- Preserve all backend contracts
- Maintain service boundaries

Every architectural change affecting module boundaries or dependency direction must be documented through a new Architecture Decision Record (ADR).

---

**Current Architecture Version:** **v10.0.0**

**Previous Version:** **v9.0.0**
```