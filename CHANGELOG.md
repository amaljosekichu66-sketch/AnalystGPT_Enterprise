
### Improved

- Reporting architecture
- Pipeline orchestration
- Import consistency
- Package structure
- Data cleaning configuration
- Logging consistency
- Report exporting
- Test coverage
- Documentation
- Repository organization

### Fixed

- ReportingManager import issue
- Missing src package initialization
- Duplicate MissingValueCleaner implementation
- Aggressive TextCleaner behavior
- DataTypeCleaner logging
- Hardcoded report paths
- Configuration consistency

### Repository Status

- Upload Module → Stable
- Cleaning Module → Stable
- Quality Module → Stable
- Analytics Module → Stable
- Reporting Module → Stable
- Automated Tests → **79 Passed**
- Warnings → **0**
- Small Dataset Validation → Passed
- Large Dataset Validation → Passed
- Stress Test Validation → Passed
- Architecture → Stable

**Release Version:** v5.0.0

---

---

## [v5.5.0] — Enterprise Architecture Refactor

**Release Date:** July 2026

### Overview

Sprint 5.5 represents the largest architectural refactor completed
since the project began.

The primary objective was to separate pipeline orchestration from the
application entry point while preserving stable business module
contracts and improving long-term maintainability.

---

### Added

#### Application Layer

- Introduced dedicated `Application` class.
- Introduced reusable `Application.run()` pipeline.
- Established the Application Layer as the single orchestration point.

#### Application Contracts

- Added `PipelineResult`.
- Standardized application execution result.
- Improved type safety across the pipeline.

#### Architecture

- Introduced enterprise layered architecture.
- Centralized pipeline orchestration.
- Improved dependency direction.
- Reduced orchestration duplication.

#### Documentation

Updated:

- README
- PROJECT_STATE
- ARCHITECTURE
- ROADMAP
- ADRs
- Sprint documentation

---

### Changed

- `main.py` became a thin application entry point.
- Pipeline execution moved into `Application.run()`.
- Report models became standardized contracts.
- Repository documentation reorganized.
- Engineering documentation synchronized.

---

### Validation

Successfully validated using:

- ✅ 79 / 79 Automated Tests
- ✅ Integration Testing
- ✅ Sample Dataset
- ✅ Large Dataset (100,000 rows)
- ✅ Stress Dataset (1,000,000 rows)

---

### Result

Sprint 5.5 establishes the architectural foundation for:

- SQLite
- PostgreSQL
- REST APIs
- Streamlit
- AI Insights
- Production Deployment

---

---

## [v6.0.0] — Sprint 6 (SQLite Persistence)

**Release Date:** 21 July 2026

---

### Overview

Sprint 6 introduced the Persistence Layer, enabling AnalystGPT Enterprise
to persist pipeline execution metadata while preserving the enterprise
layered architecture established in previous releases.

This release focused on platform capabilities rather than business
features, laying the foundation for future PostgreSQL support and
enterprise-scale data management.

---

### Added

#### Persistence Module

- PersistenceManager
- PersistenceResult
- PersistenceReport

#### Database Infrastructure

- SQLiteConnection
- DatabaseManager
- SchemaManager

#### Repository Layer

- BaseRepository
- PipelineRunRepository
- DatasetRepository
- QualityRepository
- AnalyticsRepository
- ReportRepository

#### Application Integration

Application.run() now performs:

- Database initialization
- Pipeline execution registration
- Dataset persistence
- Quality report persistence
- Analytics report persistence
- Reporting metadata persistence
- Pipeline completion handling
- Pipeline failure handling
- Graceful database shutdown

---

### Changed

#### Architecture

- Introduced dedicated Persistence Layer.
- Extended layered architecture to support database operations.
- Application layer now coordinates persistence lifecycle.
- Repository Pattern adopted for all SQL operations.
- Business modules remain persistence-agnostic.
- SQL execution isolated within repository classes.

#### Database

- Automatic SQLite database creation.
- Automatic schema initialization.
- Centralized database lifecycle management.

#### Documentation

Updated:

- PROJECT_STATE.md
- ARCHITECTURE.md
- PROJECT_JOURNAL.md
- ROADMAP.md
- README.md
- Sprint documentation

---

### Validation

Successfully validated using:

- ✅ 82 / 82 Automated Tests
- ✅ Integration Testing
- ✅ SQLite Persistence
- ✅ Sample Dataset
- ✅ Large Dataset (100,000 rows)
- ✅ Stress Dataset (1,000,000 rows)

---

### Performance

Successfully validated:

- Database initialization
- Repository operations
- Persistence lifecycle
- Pipeline execution tracking
- Report persistence
- Large dataset execution
- Stress dataset execution

No architectural regressions observed.

---

### Result

Sprint 6 transforms AnalystGPT Enterprise from an in-memory analytics
pipeline into a persistence-enabled enterprise platform while preserving
stable module contracts and layered architecture.

This release establishes the foundation for production database support
in future releases.

---

### Next Release

**v7.0.0 — PostgreSQL Integration**

---

---

## [v7.0.0] — Sprint 7 (PostgreSQL Integration & Database Abstraction)

**Release Date:** 22 July 2026

---

### Overview

Sprint 7 is an architectural evolution rather than a feature release.
The objective was to transform the persistence layer from a SQLite‑specific
implementation into a database‑agnostic architecture supporting multiple
relational database engines while preserving stable business module contracts.

The release focused on architecture, maintainability, extensibility, and
enterprise readiness rather than introducing new analytics functionality.

---

### Added

#### Database Abstraction Layer

- DatabaseConnection abstraction
- Database lifecycle abstraction
- Common transaction interface
- Common connection interface

#### PostgreSQL Support

- PostgreSQLConnection
- psycopg integration
- PostgreSQL configuration
- PostgreSQL engine selection
- Dictionary row support

#### Database Infrastructure

- ConnectionFactory
- Runtime database engine selection
- Multi‑database support
- Cross‑database compatibility

#### Repository Improvements

- Cross‑database repository compatibility
- Automatic SQL placeholder conversion
- Shared repository behavior
- Database‑independent CRUD operations

#### Schema Management

- SQL dialect abstraction
- Cross‑engine schema generation
- SQLite compatibility
- PostgreSQL compatibility

---

### Changed

#### Architecture

- Database layer became database‑agnostic.
- Repository layer now depends on DatabaseConnection.
- Connection lifecycle centralized.
- SchemaManager now supports multiple SQL dialects.
- SQLite implementation refactored behind abstraction.
- PersistenceManager updated to use dependency injection.
- Business modules remain persistence‑agnostic.

#### Persistence

- Improved transaction handling.
- Improved rollback behavior.
- Improved commit handling.
- Better separation of infrastructure responsibilities.

#### Configuration

- Added centralized database configuration.
- Support for `DATABASE_ENGINE`
- SQLite configuration
- PostgreSQL configuration

#### Documentation

Updated:

- README.md
- PROJECT_STATE.md
- ARCHITECTURE.md
- ENGINEERING_OPERATING_MANUAL.md
- PROJECT_JOURNAL.md
- CHANGELOG.md

---

### Improved

- Dependency Injection
- SOLID compliance
- Repository abstraction
- Database extensibility
- Enterprise architecture
- Maintainability
- Cross‑database compatibility
- Code readability
- Infrastructure organization

---

### Validation

Successfully validated using:

- ✅ 82 / 82 Automated Tests
- ✅ SQLite Runtime Validation
- ✅ Integration Testing
- ✅ Sample Dataset
- ✅ Large Dataset (100,000 rows)
- ✅ Stress Dataset (1,000,000 rows)

PostgreSQL architecture implemented and ready for runtime validation.

---

### Performance

Validated:

- Database abstraction
- Repository operations
- Persistence lifecycle
- Connection management
- Schema generation
- Large dataset execution
- Stress dataset execution

No architectural regressions observed.

---

### Result

Sprint 7 transforms AnalystGPT Enterprise from a persistence‑enabled SQLite
application into a database‑agnostic enterprise analytics platform capable
of supporting multiple relational database engines through a unified
abstraction layer.

This release establishes the foundation for:

- MySQL (future)
- SQL Server (future)
- Cloud‑hosted relational databases
- REST API integration
- Enterprise deployment

---

### Next Release

**v8.0.0 — REST API**

---

---

## [v8.0.0] — Sprint 8 (REST API Integration)

**Release Date:** 23 July 2026

---

### Overview

Sprint 8 introduces the REST API Layer, transforming AnalystGPT Enterprise
from a command-line analytics application into an enterprise service capable
of exposing its analytics pipeline through standardized HTTP endpoints.

This release focuses on service-oriented architecture, API contracts,
request validation, response serialization, dependency injection, and
enterprise-grade documentation while preserving the existing layered
architecture and business module contracts.

---

### Added

#### REST API Layer

- FastAPI server
- API routing infrastructure
- Root endpoint
- Health endpoint
- Version endpoint
- Pipeline execution endpoint

#### Request & Response Contracts

- PipelineRequest
- PipelineResponse
- RootResponse
- HealthResponse
- VersionResponse
- APIResponse base model

#### API Infrastructure

- Dependency Injection
- Application dependency provider
- Global exception handlers
- Standardized API error responses
- OpenAPI 3.1 specification
- Swagger UI documentation

#### API Validation

- Request validation
- Response validation
- Automatic OpenAPI schema generation
- Interactive API documentation

#### Testing

- REST API integration tests
- Root endpoint tests
- Health endpoint tests
- Version endpoint tests
- Pipeline endpoint tests

---

### Changed

#### Architecture

- Introduced dedicated API Layer.
- Application layer exposed through REST endpoints.
- API layer remains independent of business logic.
- Dependency Injection adopted for application orchestration.
- Request/Response contracts standardized using Pydantic models.
- Global exception handling centralized.
- API routing organized into modular packages.

#### Documentation

Updated:

- README.md
- CHANGELOG.md
- PROJECT_STATE.md
- PROJECT_JOURNAL.md
- ROADMAP.md
- ARCHITECTURE.md
- Sprint documentation

---

### Improved

- Enterprise architecture
- API maintainability
- Request validation
- Response serialization
- Dependency Injection
- Documentation quality
- API discoverability
- Developer experience
- Service extensibility

---

### Validation

Successfully validated using:

- ✅ 90 / 90 Automated Tests
- ✅ REST API Integration Tests
- ✅ Swagger UI Validation
- ✅ OpenAPI 3.1 Generation
- ✅ Live Endpoint Validation
- ✅ Pipeline Execution through REST API
- ✅ Sample Dataset
- ✅ Large Dataset (100,000 rows)
- ✅ Stress Dataset (1,000,000 rows)

---

### Performance

Successfully validated:

- API startup
- Endpoint routing
- Request validation
- Response serialization
- Dependency Injection
- Pipeline execution
- Report generation
- End-to-end REST pipeline execution

No architectural regressions observed.

---

### Result

Sprint 8 transforms AnalystGPT Enterprise from a persistence-enabled
analytics platform into a service-oriented enterprise analytics platform
capable of exposing its complete processing pipeline through a documented,
tested, and production-ready REST API.

This release establishes the foundation for:

- Power BI Integration
- React Frontend
- External client applications
- Authentication & Authorization
- Cloud deployment
- Enterprise integrations

---

### Next Release

**v9.0.0 — Power BI Integration**

---

## [v9.0.0] — Sprint 9 (Power BI Integration)

**Release Date:** 23 July 2026

---

### Overview

Sprint 9 introduces the Business Intelligence Integration Layer,
transforming AnalystGPT Enterprise into a platform capable of exposing
analytics results through Power BI–ready REST endpoints.

The release focuses on enterprise dashboard integration, standardized
dashboard contracts, business intelligence services, API extensibility,
and production-grade validation while preserving the layered architecture
established in previous releases.

---

### Added

#### Business Intelligence Layer

- Power BI Integration package
- DashboardService
- Power BI dashboard orchestration
- Dashboard data extraction
- Dashboard response generation

#### Dashboard Models

- DashboardSummary
- DashboardStatistics
- DashboardCorrelation
- DashboardDistribution
- DashboardCategorical

#### Power BI API

- Dashboard endpoint
- Summary endpoint
- Statistics endpoint
- Correlation endpoint
- Distribution endpoint
- Categorical endpoint
- Report endpoint
- Pipeline endpoint

#### API Integration

- Power BI router
- Dashboard service integration
- Standardized dashboard responses
- Business Intelligence response contracts

#### Performance Engineering

- Benchmark framework
- Stress testing framework
- Benchmark result generation
- Performance reporting

#### Testing

- Power BI endpoint integration tests
- Dashboard endpoint tests
- Summary endpoint tests
- Statistics endpoint tests
- Correlation endpoint tests
- Distribution endpoint tests
- Categorical endpoint tests
- Report endpoint tests

---

### Changed

#### Architecture

- Introduced dedicated Business Intelligence Integration Layer.
- Dashboard generation separated from REST API routing.
- Dashboard services isolated from business logic.
- Standardized dashboard response models.
- API routing extended for Power BI consumption.
- Integration layer remains independent of analytics modules.

#### Performance

- Added automated benchmarking framework.
- Added enterprise stress testing framework.
- Added performance reporting assets.
- Improved validation workflow.

#### Documentation

Updated:

- README.md
- CHANGELOG.md
- PROJECT_STATE.md
- PROJECT_JOURNAL.md
- ARCHITECTURE.md
- ENGINEERING_OPERATING_MANUAL.md
- Performance documentation
- Sprint documentation

---

### Improved

- Business Intelligence integration
- API extensibility
- Dashboard maintainability
- Performance validation
- Enterprise architecture
- Documentation quality
- Testing coverage
- Service organization
- Release validation

---

### Validation

Successfully validated using:

- ✅ 98 / 98 Automated Tests
- ✅ Power BI Endpoint Validation
- ✅ Swagger UI Validation
- ✅ SQLite Runtime Validation
- ✅ PostgreSQL Runtime Validation
- ✅ Sample Dataset
- ✅ Large Dataset (100,000 rows)
- ✅ Stress Dataset (1,000,000 rows)
- ✅ End-to-End Pipeline Validation

---

### Performance

Successfully validated:

- Power BI dashboard generation
- Dashboard service execution
- REST endpoint execution
- SQLite persistence
- PostgreSQL persistence
- Benchmark framework
- Stress testing framework
- Large dataset execution
- One million row execution

No architectural regressions observed.

---

### Result

Sprint 9 transforms AnalystGPT Enterprise from a REST-enabled analytics
platform into a Business Intelligence platform capable of serving
Power BI dashboards through standardized enterprise APIs while
maintaining clean architecture, database independence, and production-
ready validation.

This release establishes the foundation for:

- Streamlit Frontend
- Interactive dashboards
- Executive reporting
- AI Insights
- Cloud deployment
- Enterprise BI integrations
---

## [v10.0.0] — Sprint 10 (Enterprise Streamlit Frontend)

**Release Date:** 24–25 July 2026

---

### Overview

Sprint 10 introduces the Enterprise Presentation Layer, transforming
AnalystGPT Enterprise from a backend-driven analytics platform into a
complete enterprise analytics application with a modern graphical user
interface.

This release focuses on frontend architecture, reusable UI components,
service-oriented presentation logic, enterprise navigation, session
management, and dashboard visualization while preserving the existing
Application Layer, REST API Layer, Business Intelligence Layer, and
database abstraction architecture.

The Streamlit frontend consumes existing services and REST APIs without
introducing business logic into the presentation layer, maintaining
strict adherence to Clean Architecture and SOLID principles.

---

### Added

#### Enterprise Streamlit Frontend

- Streamlit application entry point
- Enterprise page routing
- Sidebar navigation
- Session state management
- Frontend configuration
- Theme system
- Enterprise layout

#### Dashboard

- KPI Cards
- Pipeline Status
- Dataset Summary
- Dataset Preview
- Dataset Schema
- Quick Actions
- Dashboard footer
- Dashboard services

#### Upload Interface

- Dataset upload page
- Upload validation
- Upload preview
- Upload workflow
- Session integration

#### Reports Centre

- Report listing
- Report preview
- Report metadata
- Export workflow
- Reporting service integration

#### About Page

- Project overview
- Architecture summary
- Technology overview
- Version information
- Enterprise capability summary

#### Frontend Components

- Sidebar
- KPI Cards
- Dashboard Summary
- Pipeline Status
- Dataset Information
- Dataset Quality
- Dataset Schema
- Dataset Preview
- Report List
- Report Preview
- Quick Actions
- Footer
- About Card
- Metrics

#### Frontend Services

- Dashboard Service
- Report Service
- API Client
- Session Manager

#### Documentation

Added:

- ADR-015 — Streamlit Frontend Architecture
- ADR-016 — Frontend Session State Pattern
- ADR-017 — Frontend Service Layer Pattern
- ADR-018 — Report Export Architecture
- ADR-019 — Enterprise UI Navigation Pattern
- ADR-020 — AI Insight Engine Architecture

---

### Changed

#### Architecture

- Introduced dedicated Presentation Layer.
- Streamlit views communicate exclusively through frontend services.
- Business logic remains isolated inside the Application Layer.
- REST APIs continue serving as stable service interfaces.
- Frontend organized into reusable component architecture.
- Session state isolated from business state.
- Navigation centralized.
- Frontend prepared for future React migration.

#### User Experience

- Enterprise dashboard introduced.
- Interactive dataset preview added.
- Report centre implemented.
- Upload workflow modernized.
- Navigation simplified.
- Consistent enterprise styling adopted.

#### Documentation

Updated:

- README.md
- CHANGELOG.md
- PROJECT_STATE.md
- PROJECT_JOURNAL.md
- ROADMAP.md
- ARCHITECTURE.md
- ENGINEERING_OPERATING_MANUAL.md
- Sprint documentation
- Architecture Decision Records

---

### Improved

- Enterprise frontend architecture
- Dashboard usability
- Navigation consistency
- Session management
- Frontend maintainability
- Component reusability
- Service abstraction
- API integration
- Documentation quality
- Repository organization

---

### Validation

Successfully validated using:

- ✅ Dashboard Rendering
- ✅ Upload Workflow
- ✅ Report Workflow
- ✅ About Page
- ✅ Session State Validation
- ✅ REST API Integration
- ✅ SQLite Runtime Validation
- ✅ PostgreSQL Runtime Validation
- ✅ Sample Dataset
- ✅ Large Dataset (100,000 rows)
- ✅ Stress Dataset (1,000,000 rows)
- ✅ End-to-End Pipeline Validation

---

### Performance

Successfully validated:

- Dashboard rendering
- Dataset preview
- Session management
- Frontend responsiveness
- REST API communication
- SQLite persistence
- PostgreSQL persistence
- Large dataset rendering
- One million row dataset execution

No architectural regressions observed.

---

### Result

Sprint 10 transforms AnalystGPT Enterprise from a Business Intelligence
platform into a complete enterprise analytics application by introducing
a dedicated Presentation Layer while preserving the existing layered
architecture, stable module contracts, and service-oriented design.

The platform now includes:

- Enterprise Analytics Pipeline
- Persistence Layer
- Database Abstraction Layer
- REST API Platform
- Business Intelligence Layer
- Enterprise Streamlit Frontend
- Reusable Component Library
- Frontend Service Layer
- Session Management
- Enterprise Dashboard
- Reports Centre

This release establishes the foundation for:

- AI Insight Engine
- Executive Recommendations
- Explainable Analytics
- Natural Language Reports
- React Frontend Migration
- Production Deployment

---

---

## [v11.0.0] — AI Insight Engine

**Release Date:** 26 July 2026

### Overview

Sprint 11 introduces a dedicated AI Insight Engine to AnalystGPT Enterprise,
enriching the reporting pipeline with intelligent executive summaries,
actionable business recommendations, analytical explanations, and publication-ready
narratives generated by local Large Language Models (Ollama with Qwen3:8B).

The AI subsystem preserves existing layered architecture and stable contracts,
operating post-persistence without mutating business data, and providing
resilient, non-blocking fallback when AI services are unavailable.

---

### Added

#### AI Insight Subsystem (`src/ai/`)

- `AIManager`: Coordinates AI generation, exceptions, timings, and result packaging.
- `AIReport`: Immutable dataclass contract for generated insights and execution metadata.
- `AIResult`: Immutable execution result returned by the AI subsystem.
- `UnifiedReportEngine`: Single-prompt generation engine producing all four insight sections with regex heading detection, alias support, and truncation diagnostics.
- `ExecutiveSummaryEngine`: Isolated engine for executive summaries.
- `RecommendationEngine`: Isolated engine for prioritized business recommendations.
- `ExplanationEngine`: Isolated engine for explainable analytics.
- `NarrativeEngine`: Isolated engine for executive business narratives.
- `InsightEngine`: Legacy/auxiliary engine for bulleted business observations.

#### LLM Abstraction Layer (`src/llm/`)

- `BaseLLM`: Abstract provider interface defining `@property model` and `generate(prompt: str) -> str`.
- `LLMFactory`: Provider factory creating configured LLM implementations (`ollama`).
- `OllamaClient`: Concrete LLM adapter for local Ollama server inference.
- `PromptBuilder`: Centralized prompt templates with strict anti-hallucination guardrails.
- `ReportSerializer`: Structured report serializer with section truncation and recursive dictionary summarization.
- `ResponseParser`: Output cleaner stripping `<think>` tags, code fences, headings, and formatting.
- `LLMService`: Enterprise wrapper with configurable retry logic.

#### Application Orchestration Contracts

- `PipelineReport`: Canonical business report encapsulating `ReportingReport` and optional `AIReport`.
- Integrated AI generation into `Application.run()` post-persistence.

#### Testing

- Added unit tests for AI Manager, all individual engines, PromptBuilder, ReportSerializer, ResponseParser, and LLMService.
- Added end-to-end integration tests for AI pipeline enrichment in `Application.run()`.
- Total test suite expanded to **180 passed automated tests**.

---

### Changed

#### Architecture

- Introduced AI Insight Engine Layer as a post-persistence enrichment stage.
- `Application.run()` coordinates AI generation on `ReportingReport` after persistence.
- Enforced non-blocking fallback: AI errors are logged as warnings and pipeline execution continues with `ai_report = None`.
- AI subsystem consumes stable contracts without mutating business DataFrames or metrics.

---

### Improved

- Business reporting value with natural language executive summaries and insights.
- Local LLM inference speed via single-request unified prompt architecture.
- Anti-hallucination guarantees via explicit report delimitation and source-of-truth prompts.
- Test coverage across all pipeline layers (180 passing tests).

---

### Validation

Successfully validated using:

- ✅ Automated Testing (180 tests passing)
- ✅ Local LLM Inference (Ollama / Qwen3:8B)
- ✅ Single-prompt Unified Report Generation
- ✅ PromptBuilder Anti-Hallucination Formatting
- ✅ Response Parsing and Reasoning Tag Removal
- ✅ Truncation Detection and Alias Matching
- ✅ Non-blocking Fallback on LLM Service Failure
- ✅ End-to-End Pipeline Execution with AI Enrichment
- ✅ REST API & Streamlit Frontend Compatibility
- ✅ Large Dataset Validation (~100k rows)
- ✅ Stress Dataset Validation (~1M rows)

---

### Result

Sprint 11 successfully delivers the AI Insight Engine, completing the core analytical
capabilities of AnalystGPT Enterprise. The platform now combines data ingestion,
cleaning, quality validation, statistical analytics, structured reporting,
relational persistence, REST APIs, Power BI integration, interactive Streamlit frontend,
and local LLM-powered business insights.

The platform is now ready for production deployment.

---

---

## [v12.0.0] — Production Deployment

**Release Date:** August 2026

### Overview

Sprint 12 establishes production-grade deployment, containerization, observability,
and continuous integration infrastructure for AnalystGPT Enterprise.

The platform is transformed into a containerized multi-service topology orchestrated
by Docker Compose, supported by centralized environment-driven configuration, size-bounded
rotating file logging, and automated GitHub Actions continuous integration with strict
blocking quality gates.

---

### Added

#### Infrastructure & Containerization
- `Dockerfile`: Multi-stage build defining target stages (`base`, `builder`, `runtime-base`, `api`, `frontend`, `cli`) executing under non-root `appuser` (UID 1000).
- `docker-compose.yml`: Multi-service topology orchestrating `postgres` (PostgreSQL 16 Alpine), `api` (FastAPI REST service), and `frontend` (Streamlit UI).
- `.dockerignore`: Comprehensive build-context exclusions preventing secret, bytecode, and cache ingestion.
- `.env.example`: Sanitized reference configuration covering all 25 runtime environment variables.

#### Production Logging & Observability (`src/core/logger.py`)
- `configure_logger()`: Dynamic logger factory supporting unified stdout console logging and optional `RotatingFileHandler`.
- Size-based rotation parameters (`LOG_MAX_BYTES`, `LOG_BACKUP_COUNT`) guaranteeing strict disk utilization bounds.
- Handler deduplication and automatic parent directory creation (`/app/logs`).

#### Continuous Integration (`.github/workflows/ci.yml`)
- 5-job GitHub Actions pipeline on Ubuntu 22.04 / Python 3.11:
  - `quality`: Strict blocking Flake8 syntax checks, Flake8 style rules, Black check, isort check, and Mypy static typing.
  - `test`: Full pytest regression execution (201 tests).
  - `docker-build`: Multi-stage BuildKit compilation of `api`, `frontend`, and `cli` image targets.
  - `compose-validation`: Schema and compose configuration verification.
  - `compose-integration`: Full stack startup, health polling, HTTP live verification (`/api/health`, `/_stcore/health`), and guaranteed teardown (`docker compose down -v`).
- Added `.flake8` and `pyproject.toml` tool configurations.

#### Architecture Decisions & Deployment Documentation
- `docs/adr/ADR-022-Containerization-and-Multi-Service-Topology.md`
- `docs/adr/ADR-023-Continuous-Integration-with-GitHub-Actions.md`
- `docs/deployment/DEPLOYMENT_GUIDE.md`: Comprehensive operational procedures, backup commands, and environment taxonomy.

#### Testing
- Added `tests/core/test_config.py` (12 unit tests).
- Added `tests/core/test_logger.py` (9 unit tests).
- Total test suite expanded from 180 to **201 passed automated tests**.

---

### Changed
- `src/core/config.py`: Centralized dynamic environment parsing for networking, logging, database, and AI parameters.
- `src/core/constants.py`: Bumped `APP_VERSION` to `12.0.0`.
- `src/frontend/config/settings.py`: Integrated `API_BASE_URL` from centralized config for seamless container DNS routing (`http://api:8000`).

---

### Validation
- ✅ Automated Testing: **201 passed tests** (0 failed, 0 errors, 0 regressions)
- ✅ Flake8 Syntax & Style Gates: **PASS (0 errors)**
- ✅ Black Formatting Check: **PASS (0 errors)**
- ✅ Isort Import Ordering Check: **PASS (0 errors)**
- ✅ Mypy Static Type Analysis: **PASS (0 errors in 154 files)**
- ✅ Docker Multi-Stage Architecture: **PASS (Statically validated)**
- ✅ Docker Compose Schema & Dependency Topology: **PASS (PyYAML validated)**
- ✅ Healthcheck Verification: `/api/health` and `/_stcore/health`
- ✅ Security & Secret Audit: **PASS** (Zero credentials committed, non-root user, private PostgreSQL network)

---

### Result

Sprint 12 successfully packages AnalystGPT Enterprise for production deployment with containerization, observability, automated CI quality validation, and full deployment documentation.

---

**Release Version:** **v12.0.0**

---

---

## [v13.0.0] - 2026-08-15

### Added

#### Frontend Authentication, Session Management & Admin UI (`src/frontend/`)
- `src/frontend/services/session_manager.py`: Added authentication session keys (`AUTH_TOKEN_KEY`, `AUTH_USER_KEY`, `AUTH_STATUS_KEY`), getters, setters, and `clear_authenticated_session()` for thorough cross-tenant cache and state purging.
- `src/frontend/services/api_client.py`: Enhanced with automatic `Authorization: Bearer <token>` header injection, auth endpoints (`login`, `register`, `me`, `logout`), and administration endpoints (`admin_list_users`, `admin_get_user`, `admin_update_user`, `admin_delete_user`).
- `src/frontend/services/auth_service.py`: Domain frontend service for authentication workflows, session synchronization, and safe error message translation.
- `src/frontend/views/login_page.py`: Enterprise Sign In view with credential validation and feedback.
- `src/frontend/views/admin_page.py`: Administrative user management view for user listing and role/status lifecycle administration.
- `src/frontend/components/sidebar.py`: Updated sidebar with user profile, role badge, dynamic navigation, and clean logout trigger.
- `src/frontend/streamlit_app.py`: Integrated authentication state gating and role-aware navigation while preserving public access to the About page.

#### API Security & Role-Based Access Control (RBAC) (`src/identity/`, `src/api/`)
- `src/identity/permissions.py`: Extended `Permission` enumeration (`USER_READ`, `AUDIT_READ`) and defined complete `ROLE_PERMISSIONS` matrix for `ADMIN`, `ANALYST`, and `VIEWER`.
- `src/identity/models.py`: Added `AdminUserUpdate` (mass-assignment mitigation), `PaginatedUserResponse`, `AuditEventType`, and `AuditEvent` models.
- `src/identity/exceptions.py`: Added `AdminOperationError` for administrative guard violations.
- `src/identity/audit.py`: Created structured `AuditService` with sanitization preventing credential, hash, token, and secret leakage in logs.
- `src/identity/user_service.py`: Added `list_users`, `count_users`, `update_user_admin`, `delete_user_admin` with last-admin safeguards and audit event emission.
- `src/api/dependencies/auth_dependencies.py`: Enhanced `require_permission` and `require_role` with active user verification and denial audit logging.
- `src/api/routes/admin.py`: Created administrative user management router (`GET /api/admin/users`, `GET /api/admin/users/{user_id}`, `PATCH /api/admin/users/{user_id}`, `DELETE /api/admin/users/{user_id}`).
- `src/api/routes/pipeline.py`: Protected with `require_permission(Permission.PIPELINE_EXECUTE)`.
- `src/api/routes/reports.py`: Protected with `require_permission(Permission.REPORT_VIEW)`.
- `src/api/routes/dashboard.py`: Protected with `require_permission(Permission.DASHBOARD_VIEW)`.
- `src/api/routes/powerbi.py`: Protected with `require_permission(Permission.REPORT_VIEW)` / `Permission.DASHBOARD_VIEW`.
- `src/api/exceptions/exception_handlers.py`: Registered exception handler for `AdminOperationError` (400 Bad Request).

#### Resource Ownership & Data Isolation (`src/database/`, `src/persistence/`, `src/application/`)
- `src/database/schema_manager.py`: Safe column migration and composite performance indexes on `user_id` across `pipeline_runs`, `datasets`, and `reports`.
- `src/database/repositories/base_repository.py`: Added server-side scoped query helpers (`get_by_id_scoped`, `get_all_scoped`, `delete_scoped`).
- `src/database/repositories/pipeline_run_repository.py`: Updated with ownership parameterization and query scoping (`user_id`).
- `src/database/repositories/dataset_repository.py`: Updated with ownership parameterization and query scoping (`user_id`).
- `src/database/repositories/report_repository.py`: Updated with ownership parameterization and query scoping (`user_id`).
- `src/persistence/persistence_manager.py`: Propagated `user_id` through pipeline execution lifecycle and entity persistence.
- `src/application/app.py`: Tenant-isolated pipeline caching (`_user_pipeline_results: dict[int | None, PipelineResult]`), preventing cross-tenant cached data leakage.
- `src/application/reporting_orchestrator.py`: User-scoped report resolution (`get_reports(user_id=...)`).
- `src/application/dashboard_orchestrator.py`: User-scoped pipeline execution with authenticated security context.
- `src/api/routes/pipeline.py`, `src/api/routes/reports.py`, `src/api/routes/dashboard.py`: Injected `UserContext` and enforced server-side ownership.

#### Enterprise Identity & Access Management Subsystem (`src/identity/`)
- `src/identity/models.py`: Domain entity `User`, enumerations `UserRole` (`ADMIN`, `ANALYST`, `VIEWER`) and `UserStatus` (`ACTIVE`, `INACTIVE`, `SUSPENDED`), and Pydantic validation schemas (`UserCreate`, `UserUpdate`, `UserResponse`, `UserLogin`, `TokenResponse`, `LogoutResponse`).
- `src/identity/context.py`: `UserContext` structure and async context variable management (`get_current_user_context`, `set_current_user_context`).
- `src/identity/permissions.py`: Fine-grained `Permission` enumeration and `ROLE_PERMISSIONS` RBAC matrix.
- `src/identity/interfaces.py`: Pluggable abstract protocols (`IPasswordHasher`, `IUserRepository`, `IAuthenticator`, `IAuthorizationService`, `ITokenService`, `ITokenRevocationService`).
- `src/identity/password_hasher.py`: `PBKDF2PasswordHasher` implementing PBKDF2-HMAC-SHA256 with 600,000 iterations, 16-byte random salts, and constant-time digest verification.
- `src/identity/token_service.py`: `TokenService` implementing stateless HMAC-SHA256 signed access tokens with standard claims and expiration validation.
- `src/identity/token_revocation.py`: `TokenRevocationService` managing server-side token invalidation upon user logout.
- `src/identity/user_service.py`: `UserService` domain service orchestrating registration, credential verification, timing attack mitigation, and token issuance.
- `src/identity/in_memory_user_repository.py`: Thread-safe in-memory repository for unit testing and detached operations.
- `src/identity/exceptions.py`: Domain identity and security exceptions (`AuthenticationError`, `AuthorizationError`, `PermissionDeniedError`, `UserAlreadyExistsError`, `UserDisabledError`, `UserNotFoundError`).

#### Database Repositories & Migrations (`src/database/`)
- `src/database/schema_manager.py`: Added `users` table schema and optional `user_id` relations on `pipeline_runs`, `datasets`, and `reports`.
- `src/database/repositories/user_repository.py`: Concrete `UserRepository` for SQLite and PostgreSQL.

#### API Authentication & Exception Handling (`src/api/`)
- `src/api/routes/auth.py`: Authentication endpoints (`POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`, `POST /api/auth/logout`).
- `src/api/dependencies/auth_dependencies.py`: Dependency injection hooks supporting `Authorization: Bearer <token>` resolution, `get_user_service` provider, and role/permission enforcement.
- `src/api/exceptions/exception_handlers.py`: Exception handlers for identity errors mapping to standard HTTP status codes (401, 403, 404, 409).

#### Application Layer (`src/application/`)
- `src/application/app.py`: `Application.run()` accepts optional `user_context: UserContext | None = None` while preserving 100% backward compatibility for legacy and unauthenticated executions.

#### Architecture Decisions & Governance
- `docs/adr/ADR-024-Enterprise-Identity-and-Multi-User-Architecture.md`: Architecture Decision Record for Enterprise Identity, Authentication, and Multi-User Architecture.

#### Automated Testing
- Added 128 new automated tests across `tests/identity/`, `tests/api/`, and `tests/frontend/` (54 in Phase 1, 31 in Phase 2, 5 in Phase 3, 24 in Phase 4, 14 in Phase 5).
- Total test suite expanded from 201 to **329 passed automated tests**.

---

### Validation
- ✅ Automated Testing: **329 passed tests** (0 failed, 0 errors, 0 regressions)
- ✅ Security & Authentication Gates: **PASS** (Cryptographic PBKDF2 hashing, signed token lifecycle, constant-time validation)
- ✅ IDOR Prevention & Data Isolation: **PASS** (Server-side scoped queries across datasets, pipeline runs, and reports)
- ✅ Tenant Cache Partitioning: **PASS** (Per-user in-memory cache isolation)
- ✅ Role-Based Access Control: **PASS** (ADMIN, ANALYST, VIEWER permissions and last-admin safeguards)
- ✅ Frontend Session Isolation: **PASS** (Cross-tenant session purger and state boundary gating)

---

### Result

Sprint 13 transforms AnalystGPT Enterprise into a multi-user enterprise platform with robust authentication, role-based access control, resource ownership, and cross-user data isolation.

---

**Release Version:** **v13.0.0**

---

---

## [Unreleased] — Sprint 14 (UX Stabilization, Performance, Data Governance & React Migration Readiness)

### Planned

#### Frontend UX Stabilization
- Scroll reset to top when navigating to Dashboard and Reports.
- Redesigned Dashboard information hierarchy.
- Relocate AI Insights to dedicated navigation item.
- Public About page preservation and role-aware Admin navigation.

#### Asynchronous AI Job Lifecycle
- Decoupled pipeline execution returning analytical results immediately.
- Background AI job state machine: `PENDING → GENERATING → READY / FAILED`.
- Database persistence of AI generation jobs with failure isolation and retry policies.

#### Data Cleaning Governance & Lineage
- Immutable raw dataset storage with SHA-256 checksums.
- Separated cleaned analytical dataset storage.
- Configurable missing-value policies (NULL preservation, threshold removal, imputation).
- Cleaning preview and approval workflow with before/after quality metrics.
- Comprehensive provenance tracking from source to final analytical outputs.

#### AI Analytical Context & Data Integrity
- Privacy-safe aggregated context formatting for LLM prompts.
- Inclusion of data cleaning transformations and data loss statistics in AI context.
- Distinguish original data observations from cleaned analytical findings.

#### Reporting & Export Reliability
- Repaired report download and PDF export functionality.
- Export idempotency and authenticated ownership verification.

#### React Migration Readiness
- OpenAPI 3.1 contract freeze with typed API models.
- Frontend-independent service interfaces (`AuthService`, `DashboardService`, `ReportService`, `AIInsightService`, `UploadService`, `AdminService`).
- Streamlit to React migration mapping.