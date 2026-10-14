# Changelog

All notable changes to AnalystGPT Enterprise, oldest first. The newest release is at the end:
**[v14.1.0]**. The file begins with the tail of the v5.0.0 entry; earlier releases are described in
docs/project/PROJECT_JOURNAL.md.

---

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

## [v14.0.0] — Enterprise Stabilization, Data Governance & Grounded Reporting

**Sprint:** Sprint 14 — Stabilization / Production Hardening
**Status:** ✅ **Released** — 2026-09-28, tag `v14.0.0`

### Overview

Sprint 14 delivers enterprise stabilization across the presentation, analytical and
governance tiers: asynchronous AI execution with a persistent state machine, transparent
data cleaning governance with end-to-end lineage, semantic data profiling, intelligent
visual analytics planning, publication-grade multi-page PDF reporting, strictly grounded AI
insights, and a frozen OpenAPI 3.1 contract with a technology-neutral frontend service layer.

### Key Deliverables

1. **Streamlit UX Stabilization** — responsive layout hierarchy, scroll-to-top component,
   dedicated AI Insights view, role-aware navigation, session caching.
2. **Asynchronous AI Job Lifecycle** — persistent database-backed state machine
   (`PENDING` → `GENERATING` → `READY` / `FAILED`), thread-pool background execution, retry
   isolation, polling REST endpoints. An AI failure never fails a pipeline run.
3. **Data Cleaning Governance & Lineage** — versioned immutable dataset snapshots,
   policy-driven cleaning execution audit, immutable raw blob artifact storage.
4. **AI Data Context & Analytical Integrity** — authoritative typed `AIDataContext` builder,
   cross-tenant isolation enforcement, semantic serialization.
5. **Semantic Data Profiling** — 20-class domain type classification, measure vs dimension
   separation, intelligent 4–8 chart budget via `VisualizationPlanner`.
6. **Publication-Grade Reporting** — multi-page `%PDF-1.4` report with empirical charts,
   governance tables and lineage cards, plus a rebuilt text exporter.
7. **AI Grounding Remediation** — distinct category cardinality disambiguated from
   percentage frequency in serialized prompts; non-dominance guards in prompt templates.
8. **API Contract Freeze** — OpenAPI 3.1 across **33 paths**, a single `/api` route
   convention, and a React migration blueprint (the *initial* React-readiness foundation;
   the final readiness gate is Sprint 16 and React implementation is Sprint 17 — see ROADMAP.md).

### Changed

- **`src/core/constants.py`** — `APP_VERSION` corrected from `12.0.0` to `14.0.0`. This value
  feeds `GET /`, `GET /api/version` and the OpenAPI `info.version`, so the stale constant was
  visible in the live API surface.
- **`src/core/config.py`** — the *Future Providers* section comment no longer implies the
  cloud provider keys are wired up. `LLMFactory` registers only `"ollama"` and raises
  `ValueError: Unsupported LLM Provider` for anything else; setting `OPENAI_API_KEY`,
  `GEMINI_API_KEY` or `CLAUDE_API_KEY` does not enable those providers.
- **`docs/api/openapi.json`** — re-exported from the live application: 33 paths, 42 schemas,
  `info.version` 14.0.0.
- **`pyproject.toml`** — `black` and `isort` now cover all of `src/` and `tests/`; only
  non-source trees are excluded. Previously 15 of 17 `src/` packages plus all of `tests/`
  were excluded, so both gates ran, reported success, and checked almost nothing. 231 files
  were reformatted across two passes.
- **`pyproject.toml`** — added the `integration` pytest marker and
  `addopts = -ra -m "not integration"`, so the default suite is deterministic on machines
  without a live Ollama server. Run the live path with `pytest -m integration`.

### Dependencies

`requirements.txt` was audited against actual imports across `src/`, `tests/`,
`performance/` and `scripts/`. The header version was corrected from v12.0.0 to v14.0.0.

**Added**

- `psutil` — imported by `performance/stress_test.py`, previously undeclared.
- `matplotlib` — imported at module level by `src/reporting/exporters/pdf_report_exporter.py`
  and `src/frontend/components/charts.py`. Since `ReportingManager` imports the PDF exporter
  at module level, this is a hard dependency of the core application and REST API, not only
  of the frontend. The undeclared import dated to v10.0.0 via `charts.py`, where it affected
  the Streamlit frontend alone.

**Removed — no import anywhere in the repository**

- `psycopg2-binary` — a second, unused driver generation. `src/database/postgresql_connection.py`
  imports `psycopg` (v3).
- `openai`, `tiktoken` — the AI layer is Ollama-only.
- `plotly` — charts are matplotlib. (Note: `src/frontend/components/about_card.py` and
  `footer.py` still list Plotly in their UI tech-stack strings.)
- `python-multipart` — no `UploadFile`, `File()` or `Form()` declaration exists in `src/api/`.
- `requests`, `PyYAML`, `click`, `rich`, `tenacity`, `tqdm`, `GitPython` — unused utilities.
- `prometheus-client`, `structlog` — monitoring was never implemented; logging is stdlib
  `logging` via `src/core/logger.py`.
- `gunicorn` — the Dockerfile and Compose services run `uvicorn`.
- `pywin32`, `comtypes` — unused; the Power BI integration is pure REST/JSON models.

`altair`, `pydeck` and `watchdog` are retained: they are Streamlit's own runtime companions
rather than direct imports, and pinning their floors matches the project's existing strategy.

### Verification

| Gate | Command | Result |
|---|---|---|
| Test suite | `pytest -q` | **714 passed, 0 failed, 15 deselected**, 118.73 s |
| Full collection | `pytest --collect-only -m ""` | 729 collected, 118 modules |
| Lint | `flake8 src tests --count` | 0 |
| Format | `black --check src tests` | 341 files unchanged |
| Imports | `isort --check src tests` | clean |
| Types | `mypy src` | no issues in 210 source files |

The 15 deselected tests are `integration`-marked and require a live Ollama server with
`gemma3:4b`.

> **Superseded figures.** Entries below this point were written while the sprint was in
> flight and quote test totals of 535, 531, 529 and "100% coverage". None of those was ever
> reconciled; all are superseded by the executed **714 passing**. No coverage measurement
> exists in this repository. The entries are retained verbatim for historical fidelity.

### Repository Status

- Upload Module → Stable
- Cleaning Module → Stable
- Quality Module → Stable
- Analytics Module → Stable (Semantic Profiling & Visual Analytics)
- Reporting Module → Stable (PDF & TXT Exporters)
- Identity & RBAC Subsystem → Stable
- Data Governance & Lineage → Stable
- AI Insight Engine → Stable (Async Worker & Grounded Serialization)
- REST API Layer → Stable (33 paths, OpenAPI 3.1, single `/api` convention)
- Streamlit Presentation Layer → Stable
- Automated Tests → **714 passing**
- Static Analysis → flake8 0 · black clean · isort clean · mypy clean
- Release Version → **v14.0.0**

---

### Breaking Changes (v14.0.0)

#### API: unprefixed routes removed

Every router now answers only under the `/api` prefix. Previously `/reports/*`
was mounted **twice** (prefixed and unprefixed), while `/powerbi/*` and the
dashboard router answered **only** unprefixed - two of nine routers disagreeing
with the convention the rest followed.

The unprefixed paths were briefly kept as deprecated aliases while the
Streamlit `APIClient` was migrated. Nothing in the repository uses them now,
and they have been removed.

**Removed (16 paths):**

```
/reports                                /powerbi/categorical
/reports/export/text                    /powerbi/correlation
/reports/export/pdf                     /powerbi/dashboard
/reports/latest/export/text             /powerbi/distribution
/reports/latest/export/pdf              /powerbi/pipeline
/reports/{report_id}/export/text        /powerbi/report
/reports/{report_id}/export/pdf         /powerbi/statistics
                                        /powerbi/status
                                        /powerbi/summary
```

**Migration:** prepend `/api`. Every removed path has an identical prefixed
equivalent with the same contract - `/reports/export/text` becomes
`/api/reports/export/text`, `/powerbi/status` becomes `/api/powerbi/status`.

`docs/api/openapi.json` is regenerated (33 paths). Enforced by
`tests/api/test_openapi_contract.py::test_every_path_is_under_the_api_prefix`.

#### Tooling

- Black and isort now cover **all** of `src/` and `tests/` (previously 15 of 17
  `src/` packages plus all of `tests/` were excluded, so the gates checked
  almost nothing). 231 files reformatted across two passes.
- Formatters must run in UTF-8 mode on Windows. 35 files legitimately contain
  characters outside cp1252, and without `PYTHONUTF8=1` isort cannot read them
  and skips them silently while still exiting 0. `scripts/lint.ps1` sets this;
  `scripts/run_tests.ps1` does too. `PYTHONIOENCODING` is **not** sufficient -
  it affects stdio only, not the locale encoding used to read files.

---

### Documentation — Roadmap Re-baseline (Sprints 15–17)

- `docs/project/ROADMAP.md` — the obsolete *Sprint 15 — React Migration* plan was replaced by
  a three-sprint sequence: Sprint 15 — Enterprise Stabilization, Governance Completion & Product/UX Remediation (v15.0.0) → Sprint 16 — AI Provider Abstraction & Complete React Readiness (v16.0.0) → Sprint 17 — React Migration & Modern Presentation Layer (v17.0.0). React implementation must not begin before Sprint 17.
- `docs/engineering/PROJECT_STATE.md`, `docs/project/ARCHITECTURE.md`, ADR-028 and
  `docs/api/REACT_MIGRATION_MAPPING.md` reconciled to that sequence; the interim Sprint 15 name
  *Refactoring & Architectural Evolution* is superseded.
- Status wording made evidence-based (v14.0.0 was recorded as prepared until this release); Dashboard,
  Streamlit frontend, data governance, Admin UI and technical debt marked as needing Sprint 15
  remediation rather than complete; Sprint 14 Phase 6 recorded as the initial React-readiness
  foundation, with Sprint 16 as the definitive gate.
- `docs/project/ARCHITECTURE.md` — current Ollama model corrected from Qwen3:8B to `gemma3:4b`
  (the `OLLAMA_MODEL` default).
- No application code, tests or configuration were changed by this re-baseline.

### Sprint 14 — working entries (historical)

The three entries below are the per-phase working log kept during the sprint. They overlap,
they disagree with each other on the Phase 7 name, and they quote in-flight test totals.
They are preserved as written; the release summary above is authoritative.

Phase 7 was recorded under two names — *Regression, Contract & Quality Gates* and *Semantic
Profiling, Visual Analytics & AI Grounding Remediation*. Both bodies of work were delivered,
so the disagreement was over naming rather than scope. The combined authoritative title is
*Semantic Profiling, Visual Analytics & Quality Gates* (see PROJECT_STATE.md).

#### Working entry 1 — Sprint 14 remediation & phase summary (2026-08-16)

### Sprint 14 Remediation — Data Profiling, Null Governance & Visual Analytics Refactor
- **Semantic Profiling (`src/profiling/`):** Added 20-category `SemanticType` taxonomy and `AnalyticalRole` classification to separate physical storage types from analytical domain semantics.
- **Null Governance:** Added semantically aware policy recommendations (e.g. median for continuous measures, mode for categories, never numeric interpolation for phones/postal codes) and interactive non-destructive preview.
- **VisualizationPlanner (`src/analytics/`):** Introduced authoritative visualization planner with 4–8 chart budget, identifier/constant exclusion, top-N horizontal bars, and responsive 2×2 / 3×3 grid layout.
- **Enhanced Column Profile:** Upgraded column profile table with physical types, semantic types, analytical roles, missingness, uniqueness, and governance recommendations.
- **Export Redesign:** Enhanced PDF and text exporters with clean typography, column semantic profiles, complete lineage, and clearly demarcated AI insights.

### Sprint 14 — Enterprise Platform Stabilization & Governance-First Maturation
- **Phase 1 (Frontend UX):** Navigation state stabilization, top scroll enforcement, and decoupled AI Insights page.
- **Phase 2 (Async AI Engine):** Complete decoupling of pipeline response from LLM inference; state machine and background worker.
- **Phase 3 (Cleaning Governance & Lineage):** Immutable raw storage, SHA-256 versioning, dataset version lineage.
- **Phase 4 (AI Data Context):** Domain context builder preventing fabricated metrics.
- **Phase 5 (Reporting & PDF Export):** Standards-compliant PDF and text exporters with IDOR protection.
- **Phase 6 (OpenAPI / React Readiness):** Frozen OpenAPI 3.1 contracts and migration blueprint.
- **Phase 7 (Regression & Final Validation):** 100% test coverage and static quality gates.
  *(Correction, pre-Sprint-15 hardening: the "100% test coverage" figure was never measured.
  A measurement on `pre-sprint-15-hardening` gives 81% of `src/` statements.)*

---

#### Working entry 2 — Sprint 14 detailed per-phase log

### Sprint 14 Phase 1: Frontend UX Stabilization (Formally Reviewed & Accepted)

#### Added
- `src/frontend/components/scroll_to_top.py`: Reusable scroll-to-top presentation component executing clientside JavaScript to reset `.main` and `window` scroll position to 0 on view navigation.
- `src/frontend/views/ai_insights_page.py`: Dedicated AI Insights view hosting Executive Summary, Recommendations, Explanations, Narrative, and AI Engine Metadata.
- `tests/frontend/test_navigation.py`: Unit tests for router dictionary, role-aware sidebar navigation, and public access.
- `tests/frontend/test_ux_states.py`: Unit tests for `scroll_to_top`, `render_empty_state` navigation, `loading` context manager, and progress displays.
- `tests/frontend/test_views.py`: Unit tests for view rendering across `ai_insights_page`, `dashboard_page`, `report_page`, and `about_page`.

#### Changed
- `src/frontend/config/settings.py`: Registered `AI_INSIGHTS_PAGE = "AI Insights"`, `ADMIN_PAGE = "Admin"`, `SIGN_IN_PAGE = "Sign In"`.
- `src/frontend/streamlit_app.py`: Registered AI Insights page in `PAGES` router, added AI Insights navigation button, preserved public About page access and role-aware Admin visibility, and sanitized error boundaries.
- `src/frontend/components/sidebar.py`: Updated navigation items to include `AI Insights` and role-aware `Admin` gating.
- `src/frontend/components/empty_state.py`: Enhanced `render_empty_state` with `target_page` argument for contextual navigation routing.
- `src/frontend/components/quick_actions.py`: Added `🧠 AI Insights` shortcut button; updated Refresh Dashboard to clear frontend caches.
- `src/frontend/views/dashboard_page.py`: Reorganized visual layout to prioritize KPIs, pipeline status, operational health, and schema preview; removed embedded AI insights in favor of dedicated view; integrated `scroll_to_top()`.
- `src/frontend/views/report_page.py`: Streamlined layout for report list, preview, and exports with navigation pointer to AI Insights; integrated `scroll_to_top()`.
- `src/frontend/views/about_page.py`, `src/frontend/views/admin_page.py`, `src/frontend/views/upload_page.py`: Integrated `scroll_to_top()`.
- `src/frontend/services/report_service.py`: Implemented session-level caching (`reports_cache`, `reports_dataset`) and `clear_reports_cache()` to prevent redundant backend `/reports` calls during presentation reruns.
- `src/frontend/services/session_manager.py`: Updated `store_dataset()`, `store_pipeline_result()`, `clear_dataset()`, and `clear_authenticated_session()` to purge report and dashboard caches, guaranteeing strict tenant isolation.
- `tests/frontend/test_report_service.py`: Added cache hit and cache clearing test cases.
- `tests/frontend/test_session_manager.py`: Added cache invalidation test cases for `store_dataset` and `store_pipeline_result`.

---

> *Note (2026-10-14): the Sprint 14 phase headings below originally read "(Implemented, Verified)". Under the evidence vocabulary adopted afterwards they were implemented and tested, not verified end to end; several were later found broken (governance policy selection, retry, export by id) and fixed in v14.1.0. The headings are corrected; the bodies are unchanged.*

### Sprint 14 Phase 2: Asynchronous AI Execution, Persistent Job Lifecycle & Performance (Implemented, Tested)

#### Added
- `src/ai/models.py`: Domain entity `AIJob` and enums `AIJobStatus` (`PENDING`, `GENERATING`, `READY`, `FAILED`) and `AIFailureCategory` (`TIMEOUT`, `PROVIDER_UNAVAILABLE`, `MODEL_ERROR`, `INVALID_OUTPUT`, `SYSTEM_ERROR`) with formal finite state machine transitions per ADR-025.
- `src/ai/exceptions.py`: AI subsystem exceptions `AIError`, `AIJobNotFoundError`, `AIStateTransitionError`, `AIRetryableError`, and `AINonRetryableError`.
- `src/ai/job_executor.py`: In-process asynchronous thread pool worker `AIJobExecutor` with atomic conditional claiming, exponential backoff retries, error categorization, and total crash isolation.
- `src/ai/ai_job_service.py`: Domain service `AIJobService` coordinating job creation, dispatching, retrieval, report linking, and manual retries.
- `src/database/repositories/ai_job_repository.py`: Enterprise database repository for `ai_jobs` with scoped access and atomic claiming.
- `src/database/repositories/ai_report_repository.py`: Enterprise database repository for `ai_reports` with JSON serialization and metadata persistence.
- `src/api/models/ai_models.py`: Pydantic response models `AIJobResponse` and `AIJobRetryResponse`.
- `src/api/routes/ai.py`: REST API endpoints for `GET /api/ai/jobs/{job_id}`, `GET /api/ai/jobs/latest/status`, and `POST /api/ai/jobs/{job_id}/retry`.
- `src/frontend/services/ai_service.py`: Frontend presentation service client for asynchronous AI job polling and retry triggering.
- `tests/ai/test_ai_job_state_machine.py`: Unit tests for job state machine validation and transitions.
- `tests/ai/test_ai_job_repository.py`: Unit tests for `ai_jobs` and `ai_reports` persistence.
- `tests/ai/test_ai_job_executor.py`: Unit tests for asynchronous background executor and error isolation.
- `tests/api/test_ai_routes.py`: API integration tests for `/api/ai/*` routes.
- `tests/application/test_async_ai_pipeline.py`: End-to-end integration tests verifying deterministic non-blocking pipeline execution and failure decoupling.

#### Changed
- `src/application/app.py`: Decoupled synchronous AI generation in `run()`; deterministic pipeline finishes and persists immediately, dispatching AI job asynchronously to `AIJobExecutor`.
- `src/application/pipeline_result.py`: Added `ai_job_id` and `ai_job_status` fields.
- `src/database/schema_manager.py`: Added DDL and indexes for `ai_jobs` and `ai_reports` tables across SQLite and PostgreSQL.
- `src/database/sqlite_connection.py` & `src/database/postgresql_connection.py`: Added auto-connection in `get_connection()` and standard `.close()` alias.
- `src/persistence/persistence_manager.py`: Integrated `AIJobRepository` and `AIReportRepository` accessors.
- `src/api/models/response_models.py`: Added `ai_job_id` and `ai_job_status` to `PipelineResponse`.
- `src/api/routes/pipeline.py`: Returned `ai_job_id` and `ai_job_status` from `POST /api/pipeline/run`.
- `src/api/server.py`: Mounted `/api/ai` router.
- `src/frontend/services/api_client.py`: Added API client methods `get_ai_job()`, `get_latest_ai_job()`, `retry_ai_job()`.
- `src/frontend/views/ai_insights_page.py`: Hardened view with dynamic status banners, automatic completion rendering, and retry triggers.

### Sprint 14 Phase 3: Data Cleaning Governance & Lineage (Implemented, Tested)

#### Added
- `src/governance/`: Enterprise dataset governance and versioning models (`DatasetVersion`, `CleaningConfig`, `CleaningExecution`).
- `src/database/repositories/dataset_version_repository.py`: Relational persistence for immutable dataset versions.
- `src/database/repositories/cleaning_config_repository.py`: Configurable cleaning policy repository.
- `src/database/repositories/cleaning_execution_repository.py`: Provenance and transformation lineage repository.
- `src/storage/`: Local artifact store abstraction preserving immutable raw uploaded bytes.
- `src/api/routes/governance.py`: Governance REST API endpoints for impact preview and lineage exploration.
- `tests/governance/`: Comprehensive test suite for data governance and cleaning lineage.

---

### Sprint 14 Phase 4: AI Data Context & Analytical Integrity (Implemented, Tested)

#### Added
- `src/ai/context.py`: Domain data context models (`AIDataContext`, `SourceDataContext`, `CleaningContext`, `QualityContext`, `AnalyticsContext`, `LineageContext`).
- `src/ai/context_builder.py`: Database-backed context builder querying authoritative repository records.
- `tests/ai/test_ai_data_context.py`: Immutability and builder unit tests.
- `tests/ai/test_ai_context_isolation.py`: Strict tenant ownership verification and provenance persistence tests.
- `tests/ai/test_analytical_integrity.py`: Analytical integrity prompt serialization verification.

---

### Sprint 14 Phase 5: Reporting & PDF Export Stabilization (Implemented, Tested)

#### Added
- `src/reporting/exporters/pdf_report_exporter.py`: Standards-compliant `%PDF-1.4` multi-page PDF exporter.
- `src/reporting/exporters/__init__.py`: Package export interface for format-specific report exporters.
- `tests/reporting/test_pdf_report_exporter.py`: Unit tests for PDF structure, pagination, AI demarcation, and lineage.
- `tests/api/test_report_export_api.py`: Integration tests for `/api/reports/{id}/export/*` and `/api/reports/export/*`.
- `tests/application/test_reporting_orchestrator.py`: Orchestrator unit tests for export resolution and tenant isolation.

#### Changed
- `src/core/config.py`: Added `DEFAULT_PDF_REPORT_FILENAME`.
- `src/reporting/exporters/text_report_exporter.py`: Added lineage and demarcated AI interpretation sections with disclaimers.
- `src/reporting/reporting_manager.py`: Integrated `PdfReportExporter` and exposed `export_pdf()` / `export_text()`.
- `src/application/reporting_orchestrator.py`: Implemented `export_text_report()` and `export_pdf_report()` with database-backed tenant isolation and IDOR defense.
- `src/api/routes/reports.py`: Added authenticated file streaming endpoints for plain-text and PDF artifacts.
- `src/api/server.py`: Mounted `/api/reports` routes under `API_PREFIX`.
- `src/frontend/services/report_service.py`: Routed export actions through `ReportingOrchestrator` with session user context.
- `src/frontend/components/export_buttons.py`: Rendered format-aware download buttons (`text/plain` vs `application/pdf`).
- `src/frontend/views/report_page.py`: Rendered immediate download buttons upon export generation success.

---

### Sprint 14 Phase 6: OpenAPI / React Migration Readiness (Implemented, Tested)

#### Added
- `docs/api/openapi.json`: Authoritative, formatted OpenAPI 3.1 specification across all 40 registered API routes.
- `docs/api/REACT_MIGRATION_MAPPING.md`: Complete technical migration specification (routes, component tree, TypeScript client architecture, coexistence strategy).
- `src/frontend/services/upload_service.py`: Standalone frontend `UploadService` interface for file validation, non-destructive cleaning previews, and pipeline execution.
- `src/frontend/services/admin_service.py`: Standalone frontend `AdminService` interface for user administration, role updates, and account lifecycle.
- `tests/api/test_openapi_contract.py`: Automated contract validation test suite for OpenAPI 3.1 schema and response model completeness.
- `tests/frontend/test_upload_service.py`: Unit tests for `UploadService`.
- `tests/frontend/test_admin_service.py`: Unit tests for `AdminService`.

#### Changed
- `src/api/models/response_models.py`: Added `ReportsListResponse`, `ReportDataResponse`, `ReportSectionItem`, `DashboardStatusResponse`, and `ErrorResponse`.
- `src/api/routes/reports.py`: Added `response_model=ReportsListResponse` and explicit error response schemas.
- `src/api/routes/powerbi.py`: Attached explicit response models (`DashboardResponse`, `DashboardSummary`, `DashboardStatistics`, `DashboardCorrelation`, `DashboardDistribution`, `DashboardCategorical`, `PipelineSummary`, `ReportResponse`) across all PowerBI routes.
- `src/api/routes/dashboard.py`: Attached `response_model=DashboardStatusResponse` to dashboard status endpoint.
- `src/frontend/services/__init__.py`: Re-exported `UploadService` and `AdminService`.
- `tests/api/test_reports.py`: Completed integration and contract test suite for reports endpoints.

---

### Sprint 14 Phase 7: Semantic Profiling, Visual Analytics & Publication-Grade Exporter Redesign (Implemented, Tested)

#### Added
- `src/profiling/`: Semantic profiling engine with 20-class `SemanticType` taxonomy, `AnalyticalRole` taxonomy, and deterministic `SemanticClassifier` / `DataProfiler`.
- `src/analytics/visualization_planner.py`: Authoritative `VisualizationPlanner` with strict 4–8 chart budget and responsive 2×2 / 3×3 grid layout planning.
- `tests/profiling/`: Unit test suite for semantic profiling and classification.
- `tests/analytics/test_visualization_planner.py` & `tests/analytics/test_semantic_analytics_integration.py`: Integration tests for visualization planning.
- `tests/reporting/test_enterprise_reporting_ux.py` & `tests/reporting/test_pdf_report_exporter.py`: Publication-grade PDF and text export verification.

#### Changed
- `src/reporting/exporters/pdf_report_exporter.py`: Multi-page enterprise PDF report with executive KPI cards, 13-column governance tables, empirical horizontal bar charts, and lineage provenance cards.
- `src/reporting/exporters/text_report_exporter.py`: Demarcated AI interpretation sections with empirical distributions and analytical disclaimers.
- `src/frontend/components/charts.py`: Replaced brute-force column iteration with responsive planned chart grids.
- `src/frontend/components/column_profile.py`: Upgraded to full 8-column profile table displaying inferred semantic types and roles.

---

### Sprint 14 Final Closure: AI Grounding Remediation & E2E Validation (Implemented, Tested)

#### Added
- `tests/ai/test_ai_grounding_remediation.py`: Dedicated regression test suite ensuring distinct category cardinality cannot be converted to percentage frequency and preventing non-majority dominance claims.

#### Changed
- `src/llm/report_serializer.py`: Implemented `_categorical_section` with explicit semantic labels (`distinct_category_count`, `row_count`, `top_category: value, count, percentage`, `category_distribution: count | percentage`), resolving LLM cardinality vs frequency conflation.
- `src/llm/prompt_builder.py`: Added explicit anti-hallucination and non-dominance rules to prompt templates.
- `src/ai/ai_job_service.py`: Added `recover_stale_jobs()` delegation for background worker health.

---

#### Working entry 3 — Sprint 14 release summary as drafted during the sprint

**Release Date:** 19 August 2026

### Overview

Sprint 14 delivers comprehensive enterprise stabilization, asynchronous AI execution with persistent state machines, transparent data cleaning governance, semantic data profiling, intelligent visual analytics planning, publication-grade multi-page PDF reporting, and strictly grounded AI insights verified against live Ollama `gemma3:4b` inference.

### Key Deliverables

1. **Streamlit UX Stabilization:** Responsive layout hierarchy, scroll-to-top component, dedicated AI Insights view, role-aware navigation, and session caching.
2. **Asynchronous AI Job Lifecycle:** Persistent database-backed state machine (`PENDING` → `GENERATING` → `READY` / `FAILED`), thread-pool background execution, retry isolation, and polling REST endpoints.
3. **Data Cleaning Governance & Lineage:** Versioned dataset snapshot repository, policy-driven cleaning execution audit, and immutable raw blob artifact storage.
4. **AI Data Context & Analytical Integrity:** Authoritative typed `AIDataContext` builder, cross-tenant isolation enforcement, and semantic serialization.
5. **Semantic Data Profiling:** 20-class domain type classification, measure vs dimension separation, and intelligent 4–8 chart budget via `VisualizationPlanner`.
6. **Enterprise Reporting Exporters:** Multi-page `%PDF-1.4` publication report with empirical charts, governance tables, and text report exporter.
7. **AI Grounding Remediation:** Disambiguated cardinality from frequency in serialized prompts; 0 contradicted and 0 unsupported claims.
8. **OpenAPI 3.1 & React Migration Readiness:** Frozen OpenAPI specification across 40 routes and technology-neutral frontend service layer.

### Repository Status

- Upload Module → Stable
- Cleaning Module → Stable
- Quality Module → Stable
- Analytics Module → Stable (Semantic Profiling & Visual Analytics)
- Reporting Module → Stable (PDF & TXT Exporters)
- Identity & RBAC Subsystem → Stable
- AI Insight Engine → Stable (Async Worker & Grounded Serialization)
- REST API Layer → Stable (40 Routes, OpenAPI 3.1)
- Streamlit Presentation Layer → Stable
- Automated Tests → *(in-flight figure: 529 / 535 passing, measured 2026-09-12; superseded by
  the final Sprint 14 total of **714 passing** — see the v14.0.0 summary above and
  PROJECT_STATE.md § Executed Validation)*
- Static Analysis → *(in-flight note: `pyproject.toml` then excluded `tests/` and most `src/*`
  packages from Black and isort, so those gates covered little of the tree. Those exclusions
  were removed before release; all four gates now run over all of `src/` and `tests/` and
  pass. The source-file count is now 210.)*
- Release Version: **v14.0.0**

---

---

## [v14.1.0] — 2026-10-14 — Pre-Sprint-15 Hardening & Sprint 15 Readiness Gate

> Branch `pre-sprint-15-hardening` from `b841b52` (the v14.0.0 baseline), merged to `main` and
> tagged `v14.1.0`. It contains three security and readiness audit passes plus the 40-item Sprint 15
> Readiness Gate, all closed. Every security item was reproduced before it was fixed, and
> re-probed afterwards. Current figures: PROJECT_STATE.md § *Sprint 15 Readiness Gate*.
> Decisions: ADR-029 – ADR-035. Sprint 15 has not started: it starts after a readiness
> re-audit of this release.

### Upgrade notes (read before deploying)

**Configuration — the API refuses to start until these are right**

- `APP_ENVIRONMENT` unset now means **production**.
- `AUTH_SECRET_KEY` must be private and at least 32 bytes. It must not be the published
  development key or the `.env.example` `CHANGE_ME` placeholder.
- Compose also requires `POSTGRES_PASSWORD` and `APP_DB_PASSWORD`, with no fallbacks.
- For local development, start from `cp .env.development.example .env`. `.env.example` is now a
  production template.

**Rotate secrets (I11).** Any deployment that ran v14.0.0 or earlier with default settings
signed tokens with a public key and used the `postgres` password. Rotate `AUTH_SECRET_KEY` and
the database password.

**Everyone signs in again.** Tokens issued by v14.0.0 lack `jti`, `iss` and `aud` and are
rejected. Tokens are now also revoked by:

- logout;
- password change (`POST /api/auth/password`);
- "log out everywhere" (`POST /api/auth/logout-all`);
- role or status changes.

**Review ADMIN accounts.** Before the SEC-01 fix (`0c4d9b2`), anyone could register as ADMIN.
List the admins (`GET /api/admin/users`) and demote or delete any you did not create.
Self-registered accounts are now **VIEWER**; promote them with
`PATCH /api/admin/users/{id}`. `AUTH_SELF_REGISTRATION_ENABLED=false` turns off public sign-up.

**Database**

- The schema migrates once, at the first start (`schema_version` 15). After that, startup runs
  no DDL (ADR-035).
- Startup refuses to run if two users differ only by the case of their username or email (L6).
  Merge or rename them first.
- **Existing PostgreSQL volumes:** run `docker/postgres/init-app-role.sh` once before upgrading.
  The API now connects as the least-privilege `APP_DB_USER`.

**API clients (breaking changes)**

- Datasets:
  - Upload bytes with `POST /api/datasets` and use the returned `dataset_version_id`.
  - `input_path` and `?dataset=` are gone (ADR-029).
  - Uploads need `Content-Length` (411), and `.xls` is no longer accepted.
  - Limits answer 413; job and rate caps answer 429.
- Registration rejects `role` and any other unknown field.
- `POST /api/auth/logout` requires the token being revoked.
- `GET /api/powerbi/status` requires authentication.
- Error bodies carry `request_id` instead of exception text.
- See *Contract* below for everything new.

**Operations**

- **One uvicorn worker.** Lockout state is in the database, but the per-client rate limiter is
  per process.
- **Reverse proxy.** Put the proxy's address in `TRUSTED_PROXY_IPS` and its hostname in
  `API_ALLOWED_HOSTS`.
- **Audit retention.** Audit rows older than `AUDIT_RETENTION_DAYS` (default 365; `0` keeps
  everything) are deleted at startup.
- **CLI.** `python main.py` needs a dataset and `--owner USERNAME`, or an explicit
  `--ownerless`. `python main.py --help` shows the options.
- **Removed settings:** `OPENAI_API_KEY`, `GEMINI_API_KEY`, `CLAUDE_API_KEY` (nothing read them)
  and `AUTH_DEFAULT_ADMIN_*` (there is no bootstrap admin; use `scripts/create_admin.py`).
- **Dependencies.** Install with `pip install --require-hashes -r requirements.lock`. This
  release moves starlette to 1.8.0 and urllib3 to 2.8.0 (PYSEC-2026-4175/4176/4177).

**Local data (P3-07 / I13).** `analystgpt.db` and `data/artifacts/` on development machines
hold real data. Never copy or ship them.

### Security — first pass (blockers B-01 … B-06)

### Security

- **B-01 / SEC-01 — public ADMIN self-registration.** `POST /api/auth/register` accepted a
  caller-supplied `role`. Registration now binds `UserRegistration` (no role, unknown fields →
  422); self-registered accounts are ANALYST *(VIEWER since the third pass, M10)*. `scripts/create_admin.py` bootstraps the first
  ADMIN from a shell on the deployment.
- **B-02 / SEC-02 / SEC-19 — arbitrary server file read.** Client-supplied paths
  (`input_path`, `?dataset=`) are gone. New `POST /api/datasets` (multipart) validates type and
  size before persisting or parsing and returns a server-issued `dataset_version_id`, resolved
  server-side with ownership and managed-store containment checks. Absolute server paths are
  no longer returned (`storage_path` removed; `output_path`/`export_path` are file names; error
  bodies are scrubbed).
- **B-04 / SEC-05 — VIEWER-triggered execution.** Dashboard and Power BI routes are read-only;
  execution requires `POST /api/pipeline` (`PIPELINE_EXECUTE`).
- **B-05 / SEC-03 and SEC-04 — forgeable signing key.** Unset `APP_ENVIRONMENT` now means
  production. Outside development the API refuses to start with a missing, empty, < 32-byte or
  published `AUTH_SECRET_KEY`. Compose sets production and requires the key (no fallback).

### Fixed — first pass

- **B-03 / SEC-06 — crash under concurrent requests.** Per-run / per-request persistence
  sessions replace the shared `PersistenceManager`; results carry their own lineage; caches are
  locked; SQLite waits for a concurrent writer's lock.
- **B-06 — PostgreSQL schema initialization** could never succeed on a fresh database (verified
  on PostgreSQL 16). Column migrations no longer depend on failing statements; the schema is one
  atomic transaction.

### Changed — first pass (breaking for API clients)

- `POST /api/pipeline` body: `{"dataset_version_id": "<uuid>"}` (was `input_path`).
- `/api/powerbi/*`: `?dataset_version_id=` (was `?dataset=`); 404 until the dataset has been run.
- `DatasetVersionResponse.storage_path` removed. `POST /api/auth/register` rejects `role`.
- Local development must set `APP_ENVIRONMENT=development` explicitly *(now via `.env.development.example`)*.
- OpenAPI after the first pass: 34 paths, 43 schemas *(46 paths, 51 schemas at v14.1.0)*.

### Documentation — first pass

- ROADMAP.md, PROJECT_STATE.md, API_REFERENCE.md, DEPLOYMENT_GUIDE.md, REACT_MIGRATION_MAPPING.md,
  ADR-028 and ARCHITECTURE.md corrected where they contradicted the code: governance policy
  selection is **not** persisted (BROKEN), Streamlit views are **not** presentation-only,
  "Production Ready" ratings replaced with evidence-based status, performance validation is
  partial, coverage is 81% (not 100%), and the stale "v14.0.0 release pending" line.

### Verification — first pass

- 870 passed, 1 skipped, 15 deselected, 0 failed (baseline: 714 passed, 15 deselected);
  PostgreSQL integration 4 passed against a throwaway PostgreSQL 16.15; flake8 / black / isort /
  mypy clean. Coverage 81% of `src/`.

### Security — second pass (security finding register SEC-07 … SEC-25)

- **Regression fixed:** report export by id had silently lost its owner check after the B-03
  change (any user could download any report by id); it now fails closed.
- **SEC-07** model output escaped in the Streamlit insights view.
- **SEC-08** progressive login lockout, per-client rate limits on login/registration,
  password policy. **SEC-15** generic duplicate-account message. **SEC-16** `jti`/`iss`/`aud`
  token claims. **SEC-18** non-ASCII tokens → 401.
- **SEC-09** logout requires a valid token; revocation by `jti`, persisted (`revoked_tokens`).
- **SEC-10** `.xlsx` archive checks before decompression, row/column caps, per-user job cap.
- **SEC-11** generic error bodies with `request_id` / `X-Request-ID`; details logged only.
- **SEC-12** per-request export files, deleted after sending.
- **SEC-13** compose requires `POSTGRES_PASSWORD`. **SEC-17** no API docs in production,
  loopback defaults for bind/publish.
- **SEC-14** runtime/dev requirement split, hash-pinned `requirements.lock`, digest-pinned base
  image. **SEC-23** setuptools ≥ 83. **SEC-22** CI security job (gitleaks, pip-audit, bandit),
  SHA-pinned actions, `permissions: contents: read`.
- **SEC-20** deleting a user purges their data and files. **SEC-21** race-free last-admin
  guard. **SEC-25** durable audit trail (`audit_events`), `SECURITY_ALERT` log lines,
  `GET /api/admin/audit-events`.
- **SEC-24** test data uses reserved `example.*` email domains.
- Verification (second pass): 959 passed, 1 skipped, 15 deselected, 0 failed; coverage 82%;
  PostgreSQL 16 integration 4 passed; API image built and smoke-tested; gitleaks, pip-audit and
  bandit (HIGH) clean.

### Security — third pass (2026-09-29 audit: M1 … M12, L1 … L19, I1 … I17, X1)

- **Login path:** constant-time unknown-user check with a real PBKDF2 dummy hash; hashing off
  the event loop; one 401 for disabled accounts; capped and escaped identifiers; canonical
  base64url tokens (M1, M2, L1, L2, I1, I4).
- **Accounts:** self-registration gives VIEWER (`AUTH_SELF_REGISTRATION_ENABLED`); uniqueness
  is case-insensitive (M10, L6). Lockout is keyed on (account, source) and stored in the
  database; an admin can unlock (`POST /api/admin/users/{id}/unlock`). There is a per-source
  spraying counter, and the denylist is SecLists-derived (M11, M12, L5, I3). The API trusts
  `X-Forwarded-For` only from `TRUSTED_PROXY_IPS`.
- **Sessions:** `token_version` (`ver`) revocation; `POST /api/auth/password`,
  `POST /api/auth/logout-all`; `AUTH_TOKEN_MAX_LIFETIME_MINUTES`; the development key is refused
  off loopback (I2, L4).
- **Rendering:** AI text and column names are escaped, prompt delimiters neutralised, autolinks
  broken, and mathtext escaped in charts (M9, L8, I15, L17).
- **Uploads:**
  - every route has a body limit; uploads require `Content-Length`;
  - the archive check works by content, and `.xls` was dropped;
  - shape is capped header-first;
  - the frontend applies the same guards;
  - `defusedxml`;
  - filenames are normalised (M3, M4, M5, M8, I5, I8).
- **Errors, quotas, caches:** generic errors with no tracebacks or input echo. The governance
  preview takes a job slot; AI jobs are quota'd and the queue is bounded. Caches are bounded
  LRU + TTL (L7, M6, M7, L10, I9).
- **AI jobs:** leases, conditional transitions, and interrupted jobs fail visibly (L12, I16).
- **API hygiene:** security headers, `TrustedHostMiddleware`, `allow_credentials=False`, and
  audit events for uploads, runs, exports, cross-tenant admin reads, rejected tokens and 429s
  (L13, L14, I10).
- **Files:** exports are served from memory; report paths are contained; dataset delete and
  optional retention; SQLite foreign keys on every connection; chunked purge (L15, L16, L18,
  I6, I7, I14).
- **Logging:** sizes and digests are logged, not LLM text or data (L9).
- **Infrastructure:**
  - PostgreSQL TLS options and a connect timeout;
  - plain HTTP to a remote Ollama is refused;
  - the PostgreSQL image is pinned by digest, with a least-privilege app role;
  - a Trivy image scan runs in CI (L11, L19, I12).

### Sprint 15 Readiness Gate (P1-01 … P3-10)

- **AI jobs.**
  - Jobs persist their input; retry really re-runs (FAILED or CANCELLED).
  - Interrupted jobs are requeued at startup (`AI_RECOVER_ALL_ON_STARTUP`).
  - `POST /api/ai/jobs/{id}/cancel`.
  - No connection leaks (P2-01, P2-02, P2-20).
- **Reports.** Export by id rebuilds that report from persisted rows or answers 404, never
  another report. Text and PDF match, and `report_id` is returned (P2-03).
- **Governance.** Cleaning-policy proposals (`/api/governance/policies`, with approve, modify and
  reject). `POST /api/pipeline` runs an approved proposal (`cleaning_policy_proposal_id`), and
  lineage records `proposal_id` and `approved_by` (P2-04, ADR-034).
- **Frontend.**
  - It talks only to the API (import-guarded); `GET /api/datasets/{id}/analysis` serves
    profiling.
  - Views are read-only and keyed to their dataset.
  - Uploads have a hash guard; pages show readable errors with the API down.
  - The Admin UI covers delete, unlock, audit and pagination (P2-05 … P2-08, P2-25).
- **Security.**
  - Rate limits are per real client behind the frontend (P1-02).
  - Lockout can't be weaponised (P2-11).
  - Timing is equalised and hashing runs in the threadpool (P2-09, P2-10).
  - Chunked uploads are capped before parsing (P2-12).
  - Error text no longer reaches clients (P2-13).
  - Identifiers are log-safe (P3-06).
  - `/api/powerbi/status` is authenticated and real; token `iat` / `nbf` are checked (P3-05).
- **Data governance.**
  - Account deletion is all-or-nothing: data and the account go in one transaction, and the
    audit trail is pseudonymised (P2-14, ADR-033).
  - The audit trail is hash-chained, with `GET /api/admin/audit-events/verify` and
    `AUDIT_RETENTION_DAYS` (ADR-032).
  - `scripts/purge_ownerless_data.py`.
- **Personal data (P2-15).** Detected by name and by value (e-mail, phone, SSN, IPv4), and
  camelCase names are split. Masked in report, dashboard and Power BI analytics, never charted,
  and masked in previews.
- **Database (P2-16, ADR-035).**
  - `schema_version`: the DDL runs once per version, under a PostgreSQL advisory lock.
  - A fingerprint guard makes CI fail on a DDL change without a version bump.
- **Configuration.**
  - `.env.example` is a refused production template, and `.env.development.example` is added
    (P2-18, ADR-030).
  - Compose AI defaults are aligned (P2-17).
  - `python-multipart` is declared (P2-19).
- **Dead code removed and gated (P2-22).**
  - Unused `Application` methods and the debug print.
  - `ai_orchestrator`; the insight, executive-summary, explanation, narrative and
    recommendation engines.
  - Unused frontend components and `src/frontend/theme/`.
  - Duplicated identity exceptions; unused settings.
  - `vulture` runs in CI with a documented whitelist.
- **CLI (P2-26).** `argparse`, `--help`, a dataset argument, and an accountable `--owner` (or
  explicit `--ownerless`); exit codes 0 / 1 / 2.
- **Tests and CI (P2-21).**
  - An end-to-end API journey test.
  - The OpenAPI contract is diffed as a whole document.
  - Coverage gate at 85%.
  - AppTest for every registered page.
  - A `postgres` CI job runs schema and concurrency tests on PostgreSQL 16.
  - The reviewed bandit B608 count (57) is gated (P3-04).
- **Live AI (P2-24).**
  - A tracked synthetic dataset, `sample_data/support_tickets.xlsx` (seeded:
    `scripts/make_live_sample.py`).
  - `tests/integration/test_live_ollama_pipeline.py`.
  - The recorded run: `docs/verification/live_ollama_run_2026-10-14.log`.
- **Maintenance.**
  - The duplicate `/powerbi/dashboard` route is removed (P3-01).
  - starlette 1.8.0 clears the TestClient deprecation, and pytest now fails on
    starlette/fastapi deprecations (P3-10).
  - urllib3 2.8.0.
- **Documentation.**
  - One start condition in PROJECT_STATE, ROADMAP and PROJECT_JOURNAL (P1-03).
  - ADR-029 – ADR-035 (P1-04).
  - Full reconciliation (P2-23); broken references (P3-03); stale governance documents (P3-08).
- **Release (P1-01).** Merged to `main` through a green CI run and tagged `v14.1.0`. The stale
  `sprint-15-stabilization` branch is deleted (P3-02).

### Verification — v14.1.0

- Default suite: 1,241 passed, 1 skipped, 0 failed (1,242 collected; the two PostgreSQL modules skip without `TEST_POSTGRES_*`); 16 `integration` tests deselected; coverage 88.39% (gate 85%); 15m34s.
- Static gates: flake8, black, isort and mypy are clean. vulture is clean. bandit has 0 HIGH
  and 57 reviewed B608 findings. pip-audit of the lock finds no known vulnerabilities.
- PostgreSQL 16: schema tests 4/4 passed locally against a throwaway container. The schema and
  concurrency tests run in the `postgres` CI job of the release PR.
- Live gemma3:4b: 16 passed (19m41s; end-to-end job READY after 374 s).
