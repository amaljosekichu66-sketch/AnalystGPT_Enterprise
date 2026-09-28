# AnalystGPT Enterprise Architecture

> **Purpose**
>
> This document defines the architecture of AnalystGPT Enterprise.
> It describes the system structure, module responsibilities,
> dependency rules, data flow, and architectural principles.
>
> This document reflects the implementation as of **v14.0.0** (Sprint 14 — Stabilization /
> Production Hardening, released 2026-09-28). Future sequencing (Sprints 15–17) is defined in
> ROADMAP.md.

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

Sprint 9 introduced a dedicated Business Intelligence Integration Layer that exposes dashboard-ready analytics through Power BI endpoints. The Business Intelligence Layer remains an integration layer rather than a business layer. It communicates only with the Application Layer, preserving existing module independence and stable business contracts.

Sprint 10 introduced a dedicated Enterprise Streamlit Frontend Layer that provides an interactive web interface for the analytics pipeline. The Frontend Layer is built using Streamlit with a React-ready architecture, consuming the REST API as its sole backend interface. It contains zero business logic and communicates exclusively through the established REST API, preserving the integrity of the enterprise layered architecture and enabling future migration to React without backend changes.

Sprint 11 introduced an AI Insight Engine that enriches the reporting output with intelligent narratives, executive summaries, recommendations, and explanations. The AI layer is built on a local LLM (Ollama with Qwen3:8B) and follows a pluggable architecture via `BaseLLM` and `LLMFactory`. It consumes the `ReportingReport` and produces an `AIResult`, which is then attached to the `PipelineReport`. The AI layer is completely isolated from business logic, uses only stable contracts, and preserves the existing layered architecture.

Sprint 12 introduced Production Deployment Infrastructure, including multi-stage Docker containerization (`Dockerfile`), multi-service Docker Compose topology (`docker-compose.yml`), bounded rotating file logging (`RotatingFileHandler`), centralized environment configuration, and automated GitHub Actions CI/CD (`.github/workflows/ci.yml`). The deployment architecture provides service isolation (`postgres`, `api`, `frontend`), internal networking, non-root execution, and strict blocking quality gates without altering application contracts or business logic.

Sprint 13 delivered the Enterprise Identity & Multi-User Platform subsystem (`src/identity/`), establishing domain user models (`User`, `UserRole`, `UserStatus`), cryptographic password hashing (PBKDF2-HMAC-SHA256, 600,000 iterations), granular Role-Based Access Control (RBAC) permission matrices, request security context (`UserContext`), user persistence repositories (`UserRepository`), domain service orchestration (`UserService`), stateless HMAC-SHA256 token issuance/validation (`TokenService`), server-side token revocation tracking (`TokenRevocationService`), and FastAPI authentication endpoints (`POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`, `POST /api/auth/logout`) with dependency injection hooks, server-side resource ownership/data isolation across all repositories, and Streamlit session authentication gating, while preserving 100% backward compatibility for all business modules.



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
- AI-assisted analytics
- Local LLM integration
- Pluggable LLM providers
- Explainable AI outputs
- Enterprise prompt engineering

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
PipelineReport
   │
   ▼
AI Insight Engine
   │
   ├── Executive Summary Engine
   ├── Recommendation Engine
   ├── Explanation Engine
   └── Narrative Engine
   │
   ▼
BaseLLM
   │
   ▼
LLMFactory
   │
   ▼
OllamaClient
   │
   ▼
Ollama (gemma3:4b — `OLLAMA_MODEL` default)
   │
   ▼
AIResult
   │
   ▼
REST API / Streamlit / Power BI
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

The repository is intentionally organized into nine architectural layers.

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

## AI Insight Engine Layer

Responsible for generating intelligent narratives, executive summaries, recommendations, and explanations from reporting data.

Current components:

- AIManager
- AIReport
- AIResult
- ExecutiveSummaryEngine
- RecommendationEngine
- ExplanationEngine
- NarrativeEngine
- PromptBuilder
- ReportSerializer
- ResponseParser

**LLM Infrastructure:**

- BaseLLM (abstract interface)
- LLMFactory
- OllamaClient
- (future) OpenAIClient, etc.

Responsibilities:

- Transform structured reporting data into human-readable insights
- Generate executive summaries
- Produce actionable recommendations
- Explain key metrics and outliers
- Compose coherent narratives
- Manage prompt engineering
- Serialize reports for LLM context
- Parse LLM responses into structured objects
- Support multiple LLM providers via factory pattern

Architectural constraints:

- AI layer consumes only ReportingReport (via PipelineReport).
- AI layer never accesses raw data, persistence, or business modules.
- AI engines are isolated and single-responsibility.
- LLM clients are pluggable via LLMFactory.
- Prompt engineering is abstracted in PromptBuilder.
- All AI outputs are validated and parsed into strongly typed objects.
- AI never mutates business data or persists state.

## Application Layer

Responsible for orchestration only.

### Current Components

- Application
- PipelineResult
- PipelineReport

### Architectural Constraints

The Application layer:

- may call any business manager.
- may call PersistenceManager.
- may call AIManager.
- may build PipelineReport and PipelineResult.
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

# AI Insight Engine Layer

### Responsibilities

- Generate executive summary from reporting data
- Produce actionable recommendations
- Provide explanations for key metrics
- Create coherent narratives
- Manage prompt construction and response parsing
- Interface with local LLM via Ollama
- Support pluggable LLM providers

### Components

- AIManager
- AIReport
- AIResult
- ExecutiveSummaryEngine
- RecommendationEngine
- ExplanationEngine
- NarrativeEngine
- PromptBuilder
- ReportSerializer
- ResponseParser
- BaseLLM (abstract)
- LLMFactory
- OllamaClient

### Architectural Constraints

The AI Layer:

- consumes only PipelineReport (via ReportingReport).
- must never access raw datasets or business logic.
- must never persist state.
- must remain pluggable for different LLM providers.
- must validate and parse all LLM responses.
- must use stable contracts (AIResult, AIReport).

---

# Layered Architecture

The load-bearing dependency chain is linear and one-directional. Each layer depends only on
the layer beneath it; nothing calls upward.

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ PRESENTATION                                              src/frontend/  │
│   streamlit_app.py → views/ → components/ → services/                    │
│   Views hold no business logic; components are presentation-only.        │
│   Frontend services speak HTTP only — never to src/application/ direct.  │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │  HTTP / JSON  (the only channel)
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ API                                                            src/api/  │
│   server.py  · routes/ · models/ · dependencies/ · exceptions/           │
│   Validates, authenticates, authorizes, serializes. No business logic.   │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │  Depends() → Application
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ APPLICATION                                            src/application/  │
│   Application.run()  — sole owner of end-to-end orchestration            │
│   ai_orchestrator · dashboard_orchestrator · reporting_orchestrator      │
│   PipelineResult · PipelineReport                                        │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │  calls each Manager; Managers never
                                 │  call one another
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ BUSINESS MODULES                    one Manager per capability           │
│   src/upload/     UploadManager        → DataFrame                       │
│   src/cleaning/   CleaningManager      → cleaned DataFrame               │
│   src/quality/    QualityManager       → QualityReport                   │
│   src/analytics/  AnalyticsManager     → AnalyticsReport                 │
│   src/reporting/  ReportingManager     → ReportingReport (+ exporters)   │
│   Persistence-agnostic. Never execute SQL. Never orchestrate each other. │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ PERSISTENCE                                            src/persistence/  │
│   PersistenceManager coordinates the repositories                        │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ DATABASE ABSTRACTION                                      src/database/  │
│   repositories/  (12) — own every SQL statement, scoped by user_id       │
│   DatabaseManager → ConnectionFactory → DatabaseConnection               │
│                        ├── SQLiteConnection                              │
│                        └── PostgreSQLConnection   (psycopg 3)            │
│   SchemaManager emits DDL for both dialects (11 tables)                  │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 ▼
                        SQLite file  /  PostgreSQL 16
```

---

## Where the cross-cutting subsystems actually sit

These do **not** sit between Presentation and Database in the chain above. Each attaches at
one specific layer, and knowing which one is the point of this section.

### Identity, Authentication & Authorization — `src/identity/`

A domain package consumed by the **API layer**, not by business modules.

| Concern | Location | Attaches at |
|---|---|---|
| Domain models (`User`, `UserRole`, `UserStatus`) | `src/identity/models.py` | — |
| Password hashing (PBKDF2-HMAC-SHA256, 600,000 iterations, 16-byte salt) | `src/identity/password_hasher.py` | `UserService` |
| Token issue/verify (HMAC-SHA256, `HS256`, standard JWT claims — no third-party JWT library) | `src/identity/token_service.py` | `UserService` |
| Server-side revocation on logout | `src/identity/token_revocation.py` | `UserService` |
| Permission matrix (`Permission` × `ROLE_PERMISSIONS`) | `src/identity/permissions.py` | route dependencies |
| Per-request identity | `src/identity/context.py` (`UserContext`) | route dependencies |
| Security audit trail | `src/identity/audit.py` | `UserService`, routes |
| Persistence | `src/database/repositories/user_repository.py` | Database layer |
| Enforcement | `src/api/dependencies/auth_dependencies.py` — `get_current_active_user`, `require_permission`, `require_role` | **API layer** |

Authorization is declarative: a route declares
`Depends(require_permission(Permission.REPORT_EXPORT))` and the dependency resolves the
bearer token, loads the user, and checks the matrix before the handler runs.

**Data isolation is enforced below the API, not at it.** Repository queries are scoped by
`user_id` in `src/database/repositories/`, so a handler cannot accidentally widen a query.
This is what makes IDOR structurally hard rather than a per-route discipline.

### AI Insight Engine — `src/ai/` + `src/llm/`

Attaches **after** the deterministic pipeline, dispatched by the Application layer. An AI
failure never fails a pipeline run.

```text
Application.run()  ──► deterministic pipeline completes and persists
        │
        └──► AIJobService.create()        ai_jobs row, status PENDING
                   │
                   ▼
             AIJobExecutor                ThreadPoolExecutor, background
                   │                      atomic claim, retry, error class
                   ▼
             PENDING → GENERATING → READY | FAILED
                   │
                   ├── AIManager ── engines: executive summary, recommendation,
                   │                explanation, narrative, unified report
                   ├── context_builder.py → AIDataContext (repository-backed,
                   │                        tenant-scoped, privacy-safe)
                   └── src/llm/: PromptBuilder → ReportSerializer → LLMFactory
                                 → OllamaClient → Ollama (gemma3:4b)
                   │
                   ▼
             ai_reports row ── polled by GET /api/ai/jobs/{job_id}
```

`LLMFactory` registers exactly one provider, `"ollama"`, and raises
`ValueError: Unsupported LLM Provider` for anything else.

**Grounding safeguards.** `src/analytics/statistical_interpretation.py` turns skewness and
kurtosis into deterministic, mathematically correct prose (and flags identifier-like numeric
columns); `ReportSerializer` hands that wording to the model as authoritative.
`src/ai/insight_validator.py`, called from `AIManager`, checks generated text against the
computed statistics and records contradictions or unsupported conclusions on the report's
`limitations` list rather than failing the report.

The former `src/llm/llm_service.py` wrapper was removed in the Sprint 14 stabilization pass;
all LLM access goes through `LLMFactory`.

### Business Intelligence — `src/integrations/powerbi/`

Sits **beside** the API layer, not between it and the Application layer.
`DashboardService` consumes a `ReportingReport` produced by the Application layer and emits
immutable dashboard models. The `/api/powerbi/*` routes call it through
`DashboardOrchestrator`; they never touch business modules directly.

### Data Governance & Lineage — `src/governance/` + `src/storage/`

Attaches at the **business-module boundary**, around Cleaning.

- `src/storage/artifact_store.py` — immutable raw upload bytes (SHA-256) and the cleaned
  analytical dataset as `.parquet`.
- `src/governance/policies.py` — configurable missing-value and outlier policies.
- `src/governance/preview_service.py` — non-destructive impact preview before any write.
- `src/governance/governance_service.py` — records provenance.
- Persisted through `dataset_versions`, `cleaning_configs`, `cleaning_executions`.

Lineage is therefore end-to-end: raw version + policy version → cleaned version → report →
AI report.

### Semantic Profiling — `src/profiling/`

A pure analytical service consumed by Analytics and the frontend. `SemanticClassifier`
separates domain semantics (`SemanticType`, `AnalyticalRole`) from pandas dtypes, so a
postal code is not charted as a number. `src/analytics/visualization_planner.py` consumes
it to plan a bounded 4–8 chart set.

### Configuration, Logging & Shared Infrastructure — `src/core/`

The only package every layer may import, and it imports none of them.

| Module | Responsibility |
|---|---|
| `config.py` | Every environment-driven setting, read once at import. Enforces the deployment guards: a non-development `APP_ENVIRONMENT` refuses the built-in `AUTH_SECRET_KEY` and refuses `AUTH_ALLOW_HEADER_IDENTITY`. |
| `constants.py` | `APP_NAME`, `APP_VERSION`, API prefixes, AI section names, frontend chrome. |
| `logger.py` | One configured logger; stdout always, optional bounded `RotatingFileHandler`. Handlers are torn down on reconfiguration so reloads cannot duplicate output. |
| `exceptions.py` | `AnalystGPTError` hierarchy, including the identity errors. |
| `pii.py` | Shared token-level rule for deciding whether a column name denotes contact PII. |

### Where the frontend services stop — `src/frontend/services/`

`APIClient` is the single HTTP boundary; `AuthService`, `DashboardService`,
`ReportService`, `AIService`, `UploadService` and `AdminService` are built on it, and
`SessionManager` holds presentation state only. This is the seam a future React client
replaces: it consumes the same REST contract, so nothing below the API layer changes.

---

## External libraries

Only what the repository actually imports.

| Layer | Libraries |
|---|---|
| Presentation | `streamlit`, `matplotlib` (charts) |
| API | `fastapi`, `starlette`, `uvicorn`, `pydantic` |
| Business | `pandas`, `numpy`, `openpyxl` (Excel via pandas), `pyarrow` (parquet via pandas) |
| Reporting | `matplotlib` (`PdfPages`, `pyplot`, `patches`) |
| Database | `sqlite3` (stdlib), `psycopg` 3 |
| AI | `ollama` |
| HTTP | `httpx` |
| Configuration | `python-dotenv` |
| Identity | `hashlib`, `hmac`, `secrets`, `base64` (stdlib only — no third-party crypto or JWT library) |

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

## AI Insight Engine Module

### Owner

AIManager

### Components

- AIManager
- AIReport
- AIResult
- ExecutiveSummaryEngine
- RecommendationEngine
- ExplanationEngine
- NarrativeEngine
- PromptBuilder
- ReportSerializer
- ResponseParser

### Input

PipelineReport (containing ReportingReport)

### Output

AIResult (with summary, recommendations, explanations, narrative)

### Responsibility

Transform structured reporting data into intelligent, human-readable insights using local LLM.

### Status

✅ Stable

---

## LLM Infrastructure

### Owner

LLMFactory, BaseLLM

### Components

- BaseLLM (abstract)
- LLMFactory
- OllamaClient

### Input

Prompt (string), model parameters

### Output

Generated text (string)

### Responsibility

Provide a pluggable interface to LLM providers. Currently only local Ollama is registered
(default model `gemma3:4b`); additional providers (Google Cloud / Gemini, future adapters such
as Groq) are planned for Sprint 16.

### Status

✅ Stable

---

## Application Layer

Responsibilities

- Pipeline orchestration
- Workflow sequencing
- Stage coordination
- Persistence lifecycle
- AI orchestration
- Execution timing
- Error handling
- Pipeline summary logging
- Build `PipelineResult`

The Application layer is the only component allowed to coordinate multiple business modules, the persistence layer, and the AI layer. Business modules remain independent and unaware of one another.

The Application layer is also responsible for:

- Initializing persistence
- Starting pipeline execution records
- Persisting pipeline outputs
- Calling AIManager with PipelineReport
- Building final PipelineResult
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

AI infrastructure includes:

- BaseLLM
- LLMFactory
- OllamaClient
- PromptBuilder
- ReportSerializer
- ResponseParser

### Responsibilities

#### config.py

Centralized application configuration including:

- Logging configuration
- Cleaning configuration
- Report export configuration
- Shared application settings
- Database engine selection
- Connection parameters
- **LLM settings (model, provider, timeouts)**

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
   ├── Business Modules
   │   │
   │   ├── Upload
   │   ├── Cleaning
   │   ├── Quality
   │   ├── Analytics
   │   └── Reporting
   │   │
   │   ▼
   │   Persistence
   │   │
   │   ▼
   │   Repository Layer
   │   │
   │   ▼
   │   DatabaseConnection
   │   │
   │   ├── SQLiteConnection
   │   └── PostgreSQLConnection
   │   │
   │   ▼
   │   Database Engine
   │   │
   │   ▼
   │   core
   │
   └── AI Insight Engine
        │
        ├── Engines
        ├── PromptBuilder
        ├── ReportSerializer
        ├── ResponseParser
        │
        ▼
        LLM Infrastructure
        │
        ├── BaseLLM
        ├── LLMFactory
        └── OllamaClient
        │
        ▼
        Ollama (external)
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
AI Layer
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
AI Layer
```

```text
Business Intelligence
   │
   ▼
Business Modules (directly)
```

```text
AI Layer
   │
   ▼
Business Modules (directly)
```

```text
AI Layer
   │
   ▼
Persistence
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

Business modules remain completely unaware of persistence, HTTP, AI, and UI concerns.

Only the Application layer communicates with the Persistence layer and the AI layer.

Repositories are the only components permitted to execute SQL, and they operate through the DatabaseConnection abstraction.

The REST API Layer communicates only with the Application Layer through dependency injection.

The Business Intelligence Layer communicates only with the Application Layer and must never access business modules or persistence components directly.

The AI Layer communicates only with the Application Layer and consumes only `PipelineReport` (via `ReportingReport`). It never accesses business modules or persistence.

The Frontend Layer communicates only with the REST API Layer.

This separation allows future frontend technologies, database technologies, LLM providers, and API changes to be introduced without requiring changes to business logic.

---

# Stable Contracts

| Module | Output |
|--------|--------|
| Upload | DataFrame |
| Cleaning | DataFrame |
| Quality | QualityReport |
| Analytics | AnalyticsReport |
| Reporting | ReportingReport |
| Persistence | PersistenceResult |
| AI Manager | AIResult |
| Executive Summary Engine | str |
| Recommendation Engine | list[str] |
| Explanation Engine | list[str] |
| Narrative Engine | str |
| LLMFactory | BaseLLM |
| OllamaClient | str |
| Application | PipelineResult (with PipelineReport) |
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
Persistence
      │
      ▼
PipelineReport
      │
      ▼
AI Insight Engine
      │
      ├── Executive Summary
      ├── Recommendations
      ├── Explanations
      └── Narrative
      │
      ▼
AIResult
      │
      ▼
PipelineResult
      │
      ▼
Dashboard Models (via DashboardService)
      │
      ▼
REST Response
      │
      ▼
Frontend Render
```

---

# Manager-Orchestrator Pattern

Every business module exposes one manager responsible for internal orchestration; the Application layer orchestrates across managers.

| Module | Manager |
|--------|---------|
| Upload | UploadManager |
| Cleaning | CleaningManager |
| Quality | QualityManager |
| Analytics | AnalyticsManager |
| Reporting | ReportingManager |
| Persistence | PersistenceManager |
| AI Insight Engine | AIManager |
| Application | Application |
| Business Intelligence | DashboardService |
| Frontend | Streamlit Application |
| LLM | LLMFactory (factory, not manager) |

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
- AIManager owns AI Insight Engine orchestration.
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

AI layer logging includes:

- Prompt generation logging
- LLM request logging
- Response parsing logging
- Generation time logging

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

AI-specific exceptions are defined in `src/ai/exceptions.py` (or `src/core/exceptions.py`). Global REST exception handlers provide:

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

### AI Insight Engine

- AIManager
- AIReport
- AIResult
- ExecutiveSummaryEngine
- RecommendationEngine
- ExplanationEngine
- NarrativeEngine
- PromptBuilder
- ReportSerializer
- ResponseParser
- LLMFactory
- OllamaClient (mocked)

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
- AI pipeline integration testing

Current results:

**714 automated tests passing** at v14.0.0 (729 collected, 714 passed, 0 failed,
15 `integration`-marked tests deselected by default) across 118 test modules. The executed
accounting, including the four static gates, is recorded once in PROJECT_STATE.md, section
*Executed Validation*.

> The figure of **180 automated tests** shown in earlier revisions of this section was the
> **Sprint 11** total and is retained here only as historical scope.

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
- **AI generation with large reports**
- **LLM response times (acceptable for local inference)**

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
- AI pipeline validation with various report sizes

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
│   ├── pipeline_report.py
│   └── __init__.py
├── upload/
├── cleaning/
├── quality/
├── analytics/
├── reporting/
│   └── exporters/
├── ai/
│   ├── __init__.py
│   ├── ai_manager.py
│   ├── ai_report.py
│   ├── ai_result.py
│   ├── executive_summary_engine.py
│   ├── recommendation_engine.py
│   ├── explanation_engine.py
│   ├── narrative_engine.py
│   └── exceptions.py  (optional)
├── llm/
│   ├── __init__.py
│   ├── base_llm.py
│   ├── llm_factory.py
│   ├── ollama_client.py
│   ├── prompt_builder.py
│   ├── report_serializer.py
│   └── response_parser.py
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
├── ai/
│   ├── test_ai_manager.py
│   ├── test_ai_result.py
│   ├── test_engines.py
│   ├── test_prompt_builder.py
│   ├── test_report_serializer.py
│   ├── test_response_parser.py
│   ├── test_llm_factory.py
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
- LLM Abstraction
- Provider Pluggability
- Prompt Engineering Isolation
- Structured AI Outputs

---

# Current Architecture Status

| Layer | Status |
|--------|--------|
| Frontend | ✅ MVP Complete |
| Presentation | ✅ Stable |
| REST API Layer | ✅ Stable |
| Business Intelligence Layer | ✅ Stable |
| AI Insight Engine | ✅ Stable |
| Application | ✅ Stable |
| Upload | ✅ Stable |
| Cleaning | ✅ Stable |
| Quality | ✅ Stable |
| Analytics | ✅ Stable |
| Reporting | ✅ Stable |
| Persistence | ✅ Stable |
| Database Abstraction Layer | ✅ Stable |
| Core Infrastructure | ✅ Stable |
| OpenAPI | ✅ Stable (3.1, 33 paths, contract in sync) |
| Swagger | ✅ Stable |
| Identity / Authentication / Authorization | ✅ Stable (`src/identity/`, Sprint 13) |
| Data Governance & Lineage | 🟡 Implemented & tested (`src/governance/`, `src/storage/`, Sprint 14); end-to-end workflow verification/remediation pending Sprint 15 |
| Semantic Profiling & Visual Analytics | ✅ Stable (`src/profiling/`, `VisualizationPlanner`, Sprint 14) |
| Asynchronous AI Job Lifecycle | ✅ Stable (`ai_jobs` / `ai_reports`, `AIJobExecutor`, Sprint 14) |
| Report Exporters (PDF / TXT) | ✅ Stable (`src/reporting/exporters/`, Sprint 14) |
| Containerization & CI | ✅ Stable (Docker multi-stage, Compose, 5-job GitHub Actions) |

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

# Sprint 11 — AI Insight Engine

Sprint 11 introduced a dedicated AI Insight Engine that enriches reporting data with intelligent narratives, executive summaries, recommendations, and explanations using a local LLM.

Major improvements:

- Added AI Layer with AIManager, AIReport, AIResult.
- Implemented ExecutiveSummaryEngine, RecommendationEngine, ExplanationEngine, NarrativeEngine.
- Added PromptBuilder for prompt engineering.
- Added ReportSerializer for converting reporting data to LLM context.
- Added ResponseParser for validating and parsing LLM responses.
- Added LLM infrastructure: BaseLLM, LLMFactory, OllamaClient.
- Integrated AI layer into Application orchestration (via PipelineReport).
- Preserved all stable module contracts and business logic.
- Extended automated testing (AI unit and integration tests).
- Validated AI pipeline with various report sizes.
- Ensured pluggable LLM provider architecture.
- Maintained separation of concerns: AI layer never accesses raw data or persistence.

---

# React Migration Constraint

The Streamlit frontend serves as the MVP presentation layer.

The React migration is planned for **Sprint 17**. It follows Sprint 15 (stabilization and
remediation) and Sprint 16 (AI provider abstraction and the final React-readiness audit, which
is the definitive gate). No React implementation may begin before Sprint 17.

The React migration shall preserve:

- REST API contracts
- Application Layer
- Business modules
- Persistence Layer
- Database Abstraction Layer
- AI Insight Engine contracts and the provider abstraction (Sprint 16)

Only the Presentation Layer (Frontend) may be replaced.

All backend infrastructure and contracts must remain unchanged during the migration.

This constraint ensures that the architectural integrity of the backend
and the service boundaries remain intact, allowing a smooth transition
to a modern React frontend when the time comes.

---

# Sprint 13 — Enterprise Identity & Multi-User Architecture

Sprint 13 transforms AnalystGPT Enterprise into a multi-tenant, secure enterprise platform with domain identity modeling, cryptographic authentication, role-based access control, user-owned resources, and IDOR prevention.

### Architectural Invariants
1. **Server-Side Authorization**: Resource ownership and permission enforcement occur strictly at the Application, API, and Persistence boundaries. Client-supplied IDs in request parameters are never trusted.
2. **Business Module Isolation**: Data processing engines (Upload, Cleaning, Quality, Analytics, Reporting, AI) remain completely decoupled from authentication and identity logic.
3. **Multi-User Cache Isolation**: In-memory analytical result caching in the Application layer is strictly partitioned per user (`_user_pipeline_results: dict[int | None, PipelineResult]`), preventing cross-tenant leakage.
4. **Data Isolation & IDOR Immunity**: Repositories enforce user scoping (`WHERE user_id = ?`) preventing unauthorized horizontal privilege escalation.
5. **Pluggable & Extensible**: Pluggable interfaces for password hashing, user storage, token validation, and revocation enable seamless enterprise SSO/OAuth2 evolution.

```
                    ┌─────────────────────────┐
                    │ Client / UI / REST API  │
                    └───────────┬─────────────┘
                                │ Bearer Token
                                ▼
                    ┌─────────────────────────┐
                    │ FastAPI Auth Dependency │
                    │   (Resolves UserContext) │
                    └───────────┬─────────────┘
                                │ user_context
                                ▼
                    ┌─────────────────────────┐
                    │    Application Layer    │
                    │ (Tenant-Scoped Cache)   │
                    └───────────┬─────────────┘
                                │ user_id
                                ▼
                    ┌─────────────────────────┐
                    │   Persistence Manager   │
                    └───────────┬─────────────┘
                                │ Scoped queries (WHERE user_id = ?)
                                ▼
                    ┌─────────────────────────┐
                    │ Database (SQLite/PG)    │
                    │ users, pipeline_runs,   │
                    │ datasets, reports       │
                    └─────────────────────────┘
```

# Sprint 14 — Stabilization & Governance Architecture (Delivered)

> **Status: DELIVERED — released in v14.0.0.** Earlier
> revisions of this section were headed *Target Architecture* and marked
> "PLANNED / NOT YET IMPLEMENTED"; every element below is now implemented, test-covered and
> passing the quality gates. The implementing modules are named inline.
>
> The cross-cutting placement of these subsystems — where each one attaches to the
> Presentation → API → Application → Business → Persistence → Database chain — is documented
> under *Layered Architecture* above.

Sprint 14 delivered performance stabilization, asynchronous AI job execution, data-cleaning
governance and lineage tracking, privacy-safe AI context construction, report export
reliability, and a frozen API contract with a technology-neutral frontend service layer.


### 1. Asynchronous AI Job Lifecycle & State Machine
- **Decoupled Pipeline Execution**: Pipeline API requests return deterministic analytical results immediately (`Upload → Cleaning → Quality → Analytics → Reporting → Persistence`).
- **AI Background Job**: Dispatches AI generation as an independent asynchronous task, decoupling 45–70s Ollama generation from user-visible dashboard rendering.
- **Job State Machine**: `PENDING → GENERATING → READY / FAILED`, persisted in database with `pipeline_run_id`, `user_id`, and `report_id`.
- **Failure Isolation**: An AI generation failure never invalidates or fails the underlying analytics pipeline run.

```text
Upload Request
      │
      ▼
Pipeline Execution (Deterministic) ───────────► Dashboard & Reports (Immediate)
      │
      └──► Background AI Job
                 │
                 ▼
         State: PENDING ──► GENERATING ──► READY / FAILED
                                               │
                                               ▼
                                      AI Insights View (Polled)
```

### 2. Data Cleaning Governance & Lineage Architecture
- **Immutable Raw Dataset Artifact**: Source dataset stored immutably with SHA-256 checksum and metadata persisted in database.
- **Cleaned Analytical Dataset**: Separated analytical dataset generated via configurable, explicit missing-value policies.
- **Cleaning Provenance Tracking**: Comprehensive record of transformations (rows removed, columns modified, imputation rules applied, quality metrics before vs after).
- **Reproducibility**: Complete traceability from raw dataset version + cleaning policy version → analytical dataset → reports → AI insights.

### 3. AI Analytical Context & Integrity
- **Privacy-Safe Aggregated Context**: AI prompt receives structured source-data quality metadata and aggregated analytical distributions, rather than raw unaggregated PII.
- **Contextual Integrity**: Prompt includes data cleaning statistics so the LLM correctly distinguishes original missingness from post-cleaning analytical rows.

### 4. Frontend Service Interface Layer & React Migration Boundary
- **Service Interfaces**: Frontend logic abstracted into technology-neutral service interfaces:
  - `AuthService`
  - `DashboardService`
  - `ReportService`
  - `AIInsightService`
  - `UploadService`
  - `AdminService`
- **Zero Backend Logic in Streamlit**: Streamlit views operate strictly as presentation components consuming the REST API via services.
- **OpenAPI 3.1 Contract Freeze**: Authoritative backend API contract forming the initial React-readiness foundation. The final readiness audit is a Sprint 16 gate; the React presentation layer itself is Sprint 17.

> **Known gaps carried into Sprint 15** (see ROADMAP.md): the governance workflow is not yet
> verified end-to-end through the real API/frontend path; the Dashboard largely duplicates the
> pipeline result; and `DELETE /api/admin/users/{user_id}` exists but is not exposed in
> `src/frontend/views/admin_page.py`.

---

# Future Evolution

The current architecture provides a stable foundation for continued, sequenced evolution. The Application layer remains the single orchestration point as the platform grows, while the REST API Layer provides the interface for external integrations.

## Sprint 13 — Enterprise Identity & Multi-User Platform (Complete)

- Phase 1: Architecture Reconnaissance & Foundation ✅
- Phase 2: Core Identity & Authentication Engine ✅
- Phase 3: Resource Ownership & Data Isolation ✅
- Phase 4: API Security & Role-Based Access Control (RBAC) ✅
- Phase 5: Frontend Authentication & Sprint Closure ✅

## Sprint 14 — Stabilization / Production Hardening (Released — v14.0.0)

> Released as **v14.0.0**. All seven phases are implemented,
> test-covered, and passing the full quality gate set.

- Phase 1: Frontend UX Stabilization (Scroll reset, information hierarchy, dedicated AI Insights nav, public About)
- Phase 2: Asynchronous AI Execution & Job Lifecycle (Decoupled execution, state machine, failure isolation)
- Phase 3: Data Cleaning Governance & Lineage (Immutable raw dataset, configurable policies, provenance)
- Phase 4: AI Analytical Context & Data Integrity (Source metadata vs analytical context, privacy-safe prompts)
- Phase 5: Reporting & Export Reliability (Repaired report download & PDF export, ownership enforcement)
- Phase 6: React Migration Readiness — initial foundation (OpenAPI contract freeze, typed models, frontend-independent service interfaces); final gate in Sprint 16
- Phase 7: Semantic Profiling, Visual Analytics & Quality Gates (`src/profiling/`, `VisualizationPlanner`, AI grounding remediation, 714 tests, multi-user isolation, CI quality gates)

## Sprints 15–17 — Planned (not started)

Scope and Definitions of Done are defined in ROADMAP.md. No work for these sprints exists in
this repository. Dependency chain: Sprint 14 release → Sprint 15 → Sprint 16 → Sprint 17.

| Sprint | Release | Architectural impact |
|---|---|---|
| **15 — Enterprise Stabilization, Governance Completion & Product/UX Remediation** | v15.0.0 | No new architecture. Root-cause fixes and justified refactoring only (module boundaries, duplicated business logic, dependency direction). Business logic stays in the backend. React out of scope. |
| **16 — AI Provider Abstraction & Complete React Readiness** | v16.0.0 | Extends the existing `BaseLLM` / `LLMFactory` abstraction to configuration-driven providers (Ollama, Google Cloud / Gemini; future adapters such as Groq), with normalized errors, timeouts, retries and observability. Final React-readiness audit; React architecture documented (ADR), not built. |
| **17 — React Migration & Modern Presentation Layer** | v17.0.0 | React + TypeScript replaces Streamlit incrementally as the presentation layer, consuming the existing REST API. Streamlit coexists until parity. See *React Migration Constraint* above. |

Every architectural change affecting module boundaries or dependency direction must be documented through a new Architecture Decision Record (ADR).

---

**Current Architecture Version:** **v14.0.0** — Sprint 14, Stabilization / Production Hardening (released)

**Previous Version:** **v13.0.0** — Enterprise Identity & Multi-User Platform

**Next Planned:** v15.0.0 (Sprint 15) → v16.0.0 (Sprint 16) → v17.0.0 (Sprint 17)
