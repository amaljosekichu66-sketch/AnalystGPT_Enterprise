# AnalystGPT Enterprise Roadmap

> **Purpose**
>
> This roadmap defines the long-term engineering direction for
> AnalystGPT Enterprise.
>
> Each sprint delivers one stable capability while preserving
> enterprise architecture, software quality, automated testing,
> documentation, and engineering standards.
>
> This document focuses on future engineering direction.
>
> Historical implementation details belong in:
>
> - PROJECT_JOURNAL.md
> - CHANGELOG.md
> - Sprint Release Reports
>
> Current repository status is maintained in PROJECT_STATE.md.
> Detailed architecture is maintained in ARCHITECTURE.md.

---

# Current Project Status

| Item | Status |
|------|--------|
| Last Released Version | **v14.0.0** (released 2026-09-28, tag `v14.0.0`) |
| Previous Released Version | v13.0.0 |
| Repository Status | ✅ Sprint 14 released as v14.0.0 (714 passed, 4 static gates — per PROJECT_STATE.md) |
| Current Sprint | ✅ Sprint 14 released; 📋 Sprint 15 next (not started) |
| Current Focus | **Start Sprint 15 — Enterprise Stabilization, Governance Completion & Product/UX Remediation** |
| Next Planned Sprint | 📋 Sprint 15 — Enterprise Stabilization, Governance Completion & Product/UX Remediation (v15.0.0) |
| Subsequent Sprints | 📋 Sprint 16 — AI Provider Abstraction & Complete React Readiness (v16.0.0) → 📋 Sprint 17 — React Migration & Modern Presentation Layer (v17.0.0) |
| Architecture | Enterprise Layered Architecture + Presentation Layer + REST API + Business Intelligence + Database Abstraction + AI Insight Engine + Production Deployment + Enterprise Identity & RBAC Multi-User Platform + Governance & Stabilization Platform |
| Application Layer | ✅ Stable |
| Persistence Layer | ✅ Stable |
| Database Abstraction Layer | ✅ Stable |
| REST API Layer | ✅ Stable |
| Business Intelligence Layer | ✅ Stable |
| Frontend Layer | 🟡 Implemented & tested (Streamlit); defects, UX and state handling NEED REMEDIATION in Sprint 15 |
| AI Layer | ✅ Stable |
| Production Deployment & Docker | ✅ Stable |
| Enterprise Identity & RBAC | ✅ Complete |
| User Authentication & Sessions | ✅ Complete |
| Resource Ownership & Isolation | ✅ Complete |
| Admin User Management | 🟡 Backend implemented (incl. `DELETE /api/admin/users/{user_id}`); Streamlit Admin UI exposes status changes only — reconciliation in Sprint 15 |
| Security Audit Trail | ✅ Complete |
| Power BI Integration | ✅ Complete |
| Enterprise Streamlit Frontend | 🟡 Released (v10.0.0), implemented & tested; known defects/UX issues — needs remediation (pending Sprint 15) |
| Dashboard | 🟡 Implemented; product value NEEDS REMEDIATION — overlaps the pipeline result; information architecture redesign in Sprint 15 |
| Upload Interface | ✅ Complete |
| Reports Centre | ✅ Complete |
| About Page | ✅ Complete |
| Frontend Components | ✅ Complete |
| Frontend Services | ✅ Complete |
| Theme System | ✅ Complete |
| Session Management | ✅ Complete |
| Enterprise Navigation | ✅ Complete |
| OpenAPI | ✅ Operational |
| Swagger | ✅ Operational |
| Docker Multi-Stage Build | ✅ Operational |
| Docker Compose Topology | ✅ Operational |
| Automated Testing | 🟡 PROJECT_STATE.md records **714 passed, 0 failed, 15 deselected** (`integration`, 729 collected). Earlier roadmap figure (529 / 535, 6 live-LLM failures) is superseded; not re-executed for this roadmap update. Trustworthy regression baseline is a Sprint 15 deliverable |
| Performance Validation | ✅ Completed |
| Technical Debt | 🟡 Not verified as low — known debt (quality-gate exclusions, duplication/dead code, UI/API mismatches) scheduled for Sprint 15 audit |

---

# Project Vision

Build an enterprise-grade analytics platform capable of:

- Multi-source dataset ingestion
- Enterprise data cleaning
- Data quality assessment
- Statistical analytics
- Enterprise reporting
- Enterprise persistence
- SQL database integration
- Multi-database support
- REST API integration
- Business intelligence
- AI-assisted analytics
- Production deployment
- REST API Platform
- Service-Oriented Architecture
- External Analytics Integration
- API-first Architecture
- Power BI integration
- Dashboard APIs
- Business Intelligence services
- Enterprise-grade user interface
- Interactive dashboards
- AI-powered insights

The long-term objective is to demonstrate production-quality
software engineering practices while building a complete analytics
platform.

---

# Engineering Philosophy

Every sprint must:

- Preserve modular architecture.
- Preserve stable module contracts.
- Follow SOLID principles.
- Maintain separation of concerns.
- Include automated testing.
- Update documentation.
- Produce a releasable version.
- Pass the Definition of Done.
- Maintain enterprise engineering quality.
- Preserve REST API contracts.
- Preserve API backward compatibility.
- Maintain OpenAPI documentation.
- Validate API endpoints.
- Preserve dependency injection architecture.
- Preserve Business Intelligence contracts.
- Preserve dashboard response models.
- Maintain Power BI endpoint compatibility.
- Preserve Presentation Layer independence.
- Maintain Frontend Service Layer contracts.
- Ensure stable frontend contracts.
- Preserve React migration compatibility.
- Reusable component architecture.
- Session state isolation.
- API-first frontend design.

---

# Completed Engineering Milestones

## Sprint 0 — Foundation ✅

### Delivered

- Repository initialization
- Development environment
- Initial architecture
- Core documentation
- Project structure

---

## Sprint 0.5 — Core Infrastructure ✅

### Delivered

- Shared Core package
- Centralized configuration
- Constants
- Centralized logging
- Custom exceptions
- Shared infrastructure

---

## Sprint 0.75 — Enterprise Engineering Foundation ✅

### Delivered

- Git & GitHub workflow
- Engineering governance
- Documentation standards
- Architecture Decision Records
- Engineering Playbook
- Engineering Operating Manual
- Definition of Done
- Code Review Checklist

---

## Sprint 1 — Upload Module ✅

### Delivered

- UploadManager
- CSV Reader
- Excel Reader
- JSON Reader
- Standardized DataFrame contract
- Validation
- Logging
- Exception handling

### Output

```text
Dataset Files
      │
      ▼
Standardized DataFrame
```

---

## Sprint 2 — Cleaning Module ✅

### Delivered

- CleaningManager
- ColumnCleaner
- TextCleaner
- MissingValueCleaner
- DuplicateCleaner
- DataTypeCleaner

### Achievements

- Modular cleaning pipeline
- Enterprise logging
- Automated testing
- Stable DataFrame contract

### Output

```text
Raw DataFrame
      │
      ▼
Clean DataFrame
```

---

## Sprint 3 — Quality Module ✅

### Delivered

- QualityManager
- CompletenessChecker
- ValidityChecker
- ConsistencyChecker
- UniquenessChecker
- OutlierChecker
- QualityReport

### Achievements

- Structured quality assessment
- Enterprise report model
- Stable module contracts
- Complete module integration

### Output

```text
Clean DataFrame
      │
      ▼
QualityReport
```

---

## Sprint 4 — Analytics Module ✅

### Delivered

- AnalyticsManager
- DescriptiveStatistics
- NumericalAnalysis
- CategoricalAnalysis
- CorrelationAnalysis
- DistributionAnalysis
- AnalyticsReport

### Achievements

- Statistical analytics pipeline
- Dataset profiling
- Structured analytics contract
- Full module integration
- Enterprise reporting foundation

### Output

```text
Validated Data
      │
      ▼
AnalyticsReport
```

---

## Sprint 5 — Reporting Module ✅

### Delivered

- ReportingManager
- ExecutiveSummary
- KPIFormatter
- ReportBuilder
- StructuredReport
- ReportingReport
- TextReportExporter

### Achievements

- Complete Upload → Reporting pipeline
- Executive reporting
- KPI generation
- Timestamped report export
- Performance validation
- Enterprise reporting architecture

### Validation

Successfully validated using:

- Sample dataset
- Large dataset (100,000 rows)
- Stress dataset (1,000,000 rows)

### Output

```text
AnalyticsReport
      │
      ▼
Enterprise Business Report
```

---

## Sprint 5.5 — Enterprise Architecture Refactor ✅

### Delivered

- Dedicated Application layer
- Thin `main.py`
- `Application.run()` orchestration
- `PipelineResult`
- Strongly typed report contracts
- Stable module interfaces
- Centralized pipeline execution
- Centralized pipeline summary
- Improved dependency direction

### Achievements

Sprint 5.5 established the architectural foundation for all future
development by introducing enterprise orchestration while preserving
independent business modules.

### Validation

- All automated tests passed
- Integration testing passed
- Large dataset validation passed
- Stress dataset validation passed
- Architecture validation completed

---

## Sprint 6 — SQLite Persistence ✅

### Delivered

- PersistenceManager
- PersistenceResult
- SQLiteConnection
- DatabaseManager
- SchemaManager
- BaseRepository
- PipelineRunRepository
- DatasetRepository
- QualityRepository
- AnalyticsRepository
- ReportRepository

### Achievements

- Introduced dedicated Persistence Layer
- Implemented Repository Pattern
- Integrated SQLite database support
- Added automatic schema initialization
- Preserved business module independence
- Established foundation for PostgreSQL migration

### Validation

- All automated tests passed
- Integration testing passed
- SQLite database initialization validated
- Repository layer validated
- Persistence workflow validated
- Large dataset validation passed
- Stress dataset validation passed

### Output

```text
Application
      │
      ▼
PersistenceManager
      │
      ▼
Repository Layer
      │
      ▼
SQLite Database
```

---

## Sprint 7 — Database Abstraction & PostgreSQL Integration ✅

### Delivered

- DatabaseConnection abstraction
- SQLiteConnection (refactored)
- PostgreSQLConnection with psycopg 3
- ConnectionFactory
- DatabaseManager
- SchemaManager dialect support
- Cross-database repository compatibility
- Centralized database configuration

### Achievements

- Transformed persistence layer into a database-agnostic architecture
- Enabled interchangeable SQLite and PostgreSQL backends
- Introduced runtime database engine selection
- Preserved all stable module contracts and business logic
- Validated SQLite runtime and PostgreSQL architecture

### Validation

- All automated tests passed
- SQLite runtime validation passed
- Integration testing passed
- Repository abstraction validated
- Large dataset validation passed
- Stress dataset validation passed

### Output

```text
Application
      │
      ▼
PersistenceManager
      │
      ▼
DatabaseManager
      │
      ▼
ConnectionFactory
      │
      ▼
DatabaseConnection
    ▲          ▲
    │          │
SQLiteConnection PostgreSQLConnection
    │          │
 sqlite3     psycopg
    │          │
    └────┬─────┘
         │
         ▼
Repository Layer
         │
         ▼
PipelineResult
```

---

## Sprint 8 — REST API Integration ✅

### Delivered

- FastAPI Server
- REST API Layer
- API Routing
- Dependency Injection
- Pipeline Endpoint
- Root Endpoint
- Health Endpoint
- Version Endpoint
- Request Models
- Response Models
- Global Exception Handlers
- Swagger UI
- OpenAPI 3.1

### Achievements

- Introduced dedicated REST API Layer
- Preserved layered architecture
- Business logic remained inside Application Layer
- Added service-oriented architecture
- Standardized API contracts
- Introduced enterprise dependency injection
- Added interactive API documentation
- Preserved stable module contracts

### Validation

- All automated tests passed
- REST API Integration Tests Passed
- Swagger Validation Passed
- OpenAPI Validation Passed
- Live Endpoint Validation Passed
- End-to-End Pipeline Validation Passed

### Output

```text
Client
   │
   ▼
FastAPI Server
   │
   ▼
API Routes
   │
   ▼
Dependency Injection
   │
   ▼
Application.run()
   │
   ▼
Business Modules
   │
   ▼
Persistence Layer
   │
   ▼
PipelineResponse
```

---

## Sprint 9 — Power BI Integration ✅

### Delivered

- Business Intelligence Layer
- DashboardService
- DashboardSummary
- DashboardStatistics
- DashboardCorrelation
- DashboardDistribution
- DashboardCategorical
- Power BI REST Endpoints
- Benchmark Framework
- Stress Testing Framework

### Achievements

- Introduced dedicated Business Intelligence Layer
- Preserved layered architecture
- Dashboard generation isolated from analytics
- Added Power BI–ready REST endpoints
- Validated SQLite runtime
- Validated PostgreSQL runtime
- Successfully validated one million row datasets

### Validation

- All automated tests passed
- SQLite validation passed
- PostgreSQL validation passed
- Power BI endpoint validation passed
- Benchmark validation passed
- Stress testing passed

### Output

```text
Power BI Client
        │
        ▼
 DashboardService
        │
        ▼
 REST API
        │
        ▼
 Application.run()
```

---

## Sprint 10 — Enterprise Streamlit Frontend ✅

### Delivered

- Enterprise Streamlit Frontend
- Dashboard View
- Upload Interface
- Reports Centre
- About Page
- Reusable Component Library
- Frontend Services (API Client, Session Manager)
- Theme System
- Enterprise Navigation
- Presentation Layer
- Service-oriented frontend architecture
- React-ready architecture
- REST API integration
- Session state management

### Achievements

- Introduced a dedicated Presentation Layer
- Delivered a complete, interactive web interface
- Preserved all backend contracts and service boundaries
- Demonstrated frontend-backend separation
- Prepared codebase for future React migration
- Added stable frontend service contracts
- Implemented reusable component system
- Centralized navigation and session management

### Validation

- Frontend validation passed
- Dashboard rendering validated
- Upload workflow validated
- Report workflow validated
- Navigation and session state validated
- REST API compatibility confirmed
- Power BI compatibility confirmed
- Large dataset rendering validated
- Stress dataset compatibility validated
- Architecture validation confirmed stable service boundaries

### Output Diagram

```text
Browser
      │
      ▼
Streamlit Frontend
      │
      ▼
Views
      ▼
Components
      ▼
Frontend Services
      ▼
REST API
      ▼
Application.run()
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
      ▼
Dashboard / Reports
```

---

## Sprint 11 — AI Insight Engine ✅

### Delivered

- BaseLLM abstraction
- LLMFactory
- OllamaClient
- PromptBuilder
- ResponseParser
- ReportSerializer
- ExecutiveSummaryEngine
- RecommendationEngine
- ExplanationEngine
- NarrativeEngine
- AIManager
- AIReport
- AIResult
- PipelineReport
- Local Ollama integration
- Qwen3:8B support

### Achievements

- Introduced enterprise AI layer
- Preserved layered architecture
- AI consumes ReportingReport objects
- Pluggable LLM providers
- Local inference support
- Stable AI contracts
- Enterprise prompt architecture

### Validation

- Automated tests passed
- AI integration tests passed
- Prompt generation validated
- Response parsing validated
- End-to-end AI pipeline validated
- Large report validation completed

### Output

```text
ReportingReport
      │
      ▼
PipelineReport
      │
      ▼
AIManager
      │
      ▼
Executive Summary
Recommendations
Explanations
Narrative
      │
      ▼
AIResult
```

## Sprint 12 — Production Deployment ✅

### Objective

Prepare AnalystGPT Enterprise for production-quality deployment.

### Delivered

- Multi-stage Dockerfile (`base`, `builder`, `runtime-base`, `api`, `frontend`, `cli`)
- Docker Compose multi-service topology (`postgres`, `api`, `frontend`)
- Centralized environment configuration and `.env.example`
- Production logging with size-based rotation (`RotatingFileHandler`)
- GitHub Actions CI pipeline (`quality`, `test`, `docker-build`, `compose-validation`, `compose-integration`)
- Blocking quality gates (Flake8, Black, isort, Mypy)
- ADR-022 and ADR-023
- Production Deployment Guide (`docs/deployment/DEPLOYMENT_GUIDE.md`)
- 201 automated tests passing

### Achievements

- Introduced containerized production deployment architecture
- Configured multi-service Docker Compose orchestration (PostgreSQL, FastAPI, Streamlit)
- Established centralized production environment configuration
- Implemented size-based rotating production file logging
- Integrated automated GitHub Actions CI with blocking quality gates
- Enforced non-root container security and isolated PostgreSQL internal networking

### Validation

- ✅ Full automated regression test suite: 201 tests passed
- ✅ Strict blocking quality gates passed (Flake8, Black, isort, Mypy)
- ✅ Docker Multi-Stage architecture validated
- ✅ Docker Compose multi-service topology validated
- ✅ Healthcheck endpoints verified (`/api/health`, `/_stcore/health`)
- ✅ Non-root container security and isolated PostgreSQL networking verified

### Output

```text
Docker Compose Topology
   ├── postgres  (PostgreSQL Database, internal network)
   ├── api       (FastAPI Backend, port 8000)
   └── frontend  (Streamlit UI, port 8501)
```

---

## Sprint 13 — Enterprise Identity & Multi-User Platform ✅

### Phase Breakdown

| Phase | Description | Status |
|---|---|---|
| **Phase 1** | **Architecture Reconnaissance & Foundation** | ✅ **Complete** |
| **Phase 2** | **Core Identity & Authentication Engine** | ✅ **Complete** |
| **Phase 3** | **Resource Ownership & Data Isolation** | ✅ **Complete** |
| **Phase 4** | **API Security & Role-Based Access Control (RBAC)** | ✅ **Complete** |
| **Phase 5** | **Frontend Authentication & Sprint Closure** | ✅ **Complete** |

### Delivered

- Domain user models (`User`, `UserRole`, `UserStatus`, `UserCreate`, `UserUpdate`, `UserResponse`, `UserLogin`, `TokenResponse`, `LogoutResponse`, `AdminUserUpdate`, `PaginatedUserResponse`)
- Cryptographic password hasher (`PBKDF2PasswordHasher` with PBKDF2-HMAC-SHA256, 600,000 iterations, 16-byte random salt)
- Signed stateless token service (`TokenService` with HMAC-SHA256 and standard JWT claims)
- Server-side token revocation tracking (`TokenRevocationService`)
- Domain `UserService` managing user lifecycle, authentication, timing-attack mitigation, and last-admin safeguards
- Repository persistence for users across SQLite and PostgreSQL (`UserRepository`, `InMemoryUserRepository`)
- Database schema migrations for `users` table and `user_id` ownership foreign keys/indexes
- Server-side query scoping and IDOR prevention across datasets, pipeline runs, and reports
- Multi-user in-memory application cache isolation (`_user_pipeline_results`)
- Declarative RBAC permission matrix and FastAPI dependency injection (`require_permission`, `require_role`, `get_user_context`)
- Authentication API endpoints (`POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`, `POST /api/auth/logout`)
- Administrative user management API endpoints (`GET /api/admin/users`, `GET /api/admin/users/{user_id}`, `PATCH /api/admin/users/{user_id}`, `DELETE /api/admin/users/{user_id}`)
- Structured security audit logging (`AuditService`) with zero-credential leakage sanitization
- Streamlit authentication UI (`login_page.py`) and role-aware navigation
- Frontend session management with authentication token persistence and cross-tenant session purging (`SessionManager`)
- Frontend `APIClient` automatic `Authorization: Bearer <token>` injection
- Frontend `AuthService` and administrative user management view (`admin_page.py`)
- ADR-024 (`docs/adr/ADR-024-Enterprise-Identity-and-Multi-User-Architecture.md`)
- 128 new automated security, unit, integration, and frontend tests (329 total tests passing)

### Achievements

- Transformed application from a single-user tool into an authenticated, multi-user enterprise platform
- Implemented strict server-side resource ownership and data isolation preventing IDOR vulnerabilities
- Preserved 100% backward compatibility across all business modules and existing API contracts
- Enforced declarative RBAC with clear role boundaries (`ADMIN`, `ANALYST`, `VIEWER`)
- Delivered enterprise sign-in and administrative management in the Streamlit frontend

### Validation

- ✅ Full automated regression test suite: 329 tests passed (0 failures, 0 regressions)
- ✅ Cryptographic password hashing and constant-time verification validated
- ✅ Token issuance, signature verification, expiration, and revocation validated
- ✅ Cross-user data isolation and tenant cache partitioning verified
- ✅ IDOR prevention across API endpoints and repositories verified
- ✅ RBAC permission matrices and 401/403 HTTP semantics verified
- ✅ Frontend authentication gating and cross-tenant session cleanup verified

### Output

```text
Browser / API Client
       │
       ▼
FastAPI Authentication Boundary (Bearer Token)
       │
       ▼
Security Request Context (UserContext + RBAC)
       │
       ▼
Application.run(user_context=...)
       │
       ├── Business Modules (Upload, Clean, Quality, Analytics, Reporting, AI)
       │
       ▼
Persistence Layer (Scoped by user_id)
       │
       ▼
Database Repositories (Isolated per Tenant)
```

---

# Release Timeline

| Version | Release |
|---------|---------|
| v0.5.0 | Core Infrastructure |
| v0.75.0 | Enterprise Engineering Foundation |
| v1.0.0 | Upload Module |
| v2.0.0 | Cleaning Module |
| v3.0.0 | Quality Module |
| v4.0.0 | Analytics Module |
| v5.0.0 | Reporting Module |
| **v5.5.0** | **Enterprise Architecture Refactor** ✅ |
| **v6.0.0** | **SQLite Persistence** ✅ |
| **v7.0.0** | **Database Abstraction & PostgreSQL Integration** ✅ |
| **v8.0.0** | **REST API Integration** ✅ |
| **v9.0.0** | **Power BI Integration** ✅ |
| **v10.0.0** | **Enterprise Streamlit Frontend** ✅ |
| **v11.0.0** | **AI Insight Engine** ✅ |
| **v12.0.0** | **Production Deployment** ✅ |
| **v13.0.0** | **Enterprise Identity & Multi-User Platform** ✅ |
| **v14.0.0** | **Enterprise Stabilization, Data Governance & Grounded Reporting** ✅ |
| *v15.0.0* | *Enterprise Stabilization, Governance Completion & Product/UX Remediation* 📋 |
| *v16.0.0* | *AI Provider Abstraction & Complete React Readiness* 📋 |
| *v17.0.0* | *React Migration & Modern Presentation Layer* 📋 |

---

# Future Engineering Roadmap

The following sprints build upon the enterprise architecture
introduced in Sprint 5.5, persistence from Sprint 6, database
abstraction from Sprint 7, REST API from Sprint 8, Business
Intelligence from Sprint 9, Presentation Layer from Sprint 10,
AI Insight Engine from Sprint 11, Production Deployment from Sprint 12,
Enterprise Identity & Multi-User Platform from Sprint 13, and
Enterprise Stabilization & Governance from Sprint 14.

---

## Sprint 14 — Enterprise Stabilization, Data Governance & Grounded Reporting ✅

> **Status:** **Released as v14.0.0 (2026-09-28).** Validated per PROJECT_STATE.md
> § *Executed Validation*.
>
> All seven phases were implemented on `sprint-14-stabilization` (commits `00e33af`,
> `b59df37`, `0f6d5eb`, `d7f9eb6`), followed by documentation reconciliation (`30476c7`) and
> the `release(v14.0.0)` commit; `main` was fast-forwarded and tagged `v14.0.0`.
>
> This section previously read *COMPLETED & VERIFIED (v14.0.0)*. That wording described the
> intended end state, not verified Git state. See PROJECT_STATE.md § *Sprint 14 Status —
> Verified Against the Repository*.

### Objective

Stabilize the Streamlit presentation layer, improve user experience and perceived performance, correct report/export defects, introduce transparent data-cleaning governance, decouple AI generation from dashboard rendering, establish clear AI job lifecycle and failure isolation, semantic profiling, visual analytics planning, grounded AI serialization, and prepare stable frontend/API contracts for the planned React migration.

---

### Critical Architectural Principles

**Pipeline completion must not depend on AI generation completion.**

The pipeline API must return the deterministic analytical result first, while AI generation is dispatched as a separate asynchronous job. This resolves the 45–70 second UX problem where users wait for Ollama before seeing any dashboard content.

**Privacy-safe AI context by default.**

Do not transmit the complete raw dataset to the LLM. Instead, provide structured source-data quality metadata and aggregated analytical context. This protects PII and keeps context sizes manageable.

**Cleaning preview before destructive transformations.**

Analysts must review and approve cleaning policies before execution, preventing silent information loss.

---

### Technology-Neutral Architecture

Asynchronous execution uses a **replaceable background-job abstraction**; implementation must not couple the application layer to a specific queue/worker technology. This allows the simplest reliable mechanism now and evolution toward Celery/Redis/etc. later if actual load requires it.

---

## Scope & Planned Deliverables

---

#### Phase 1 — Frontend UX Stabilization ✅ Complete (Accepted)

- Fix Dashboard initial scroll position (reliably opens at the top).
- Fix Reports initial scroll position (reliably opens at the top).
- Redesign Dashboard information hierarchy (KPIs, operational health, and schema preview).
- Move AI Insights into dedicated navigation item (`AI Insights`), separate from Dashboard.
- Preserve About as public page.
- Maintain role-aware Admin navigation (`ADMIN` role gated).
- Improve loading, empty, error, and transition states.
- Ensure navigation does not unnecessarily trigger expensive backend operations (session-level caching).
- 22 new automated unit and UX tests (351 total tests passing).

---

#### Phase 2 — AI Execution, Job Lifecycle & Performance ✅ Complete (Implemented & Verified)

**Asynchronous AI Job Architecture**

- Introduce asynchronous AI generation execution boundary:
  - Pipeline request returns deterministic analytical results immediately.
  - AI generation is dispatched as a separate background job (`AIJobExecutor`).
  - Dashboard and Reports are renderable before AI generation completes.

- Implement AI generation job lifecycle:
  - Persist AI generation status independently of frontend session state (stored in `ai_jobs` table).
  - Associate AI generation jobs with `pipeline_run_id`, `user_id`, and `report_id`.
  - State machine: `PENDING → GENERATING → READY / FAILED`.
  - Automatically initiate AI generation after successful pipeline completion.

- Duplicate prevention and idempotency:
  - Prevent duplicate AI generation for an already-completed pipeline/report.
  - Define retry behavior for transient AI failures (exponential backoff, crash isolation).
  - 25 dedicated unit and integration tests (373 total tests passing).

- Status and observability:
  - Surface AI generation status in AI Insights page with progress indicators.
  - Allow frontend clients to poll or retrieve AI generation status without blocking pipeline execution.
  - Persist generation timestamps, model/provider metadata, and failure information.

- Failure isolation (critical):
  - AI generation failures must not invalidate an otherwise successful analytics pipeline.
  - Pipeline success ≠ AI success. Both are independent outcomes.

**Performance Benchmarking**

- Establish performance baselines:
  - API response latency (p50, p95, p99)
  - Dashboard load time
  - Pipeline execution time (cleaning, quality, analytics, reporting)
  - AI generation time (Ollama, with and without optimizations)
  - Report generation and export times

- Define measurable performance acceptance criteria.
- Record benchmark methodology and results.
- Detect performance regressions against established baselines.
- Benchmark Ollama latency and investigate optimization opportunities (model quantization, prompt size reduction, provider tuning).
- Preserve provider/model abstraction for future cloud or alternative LLM providers.

---

#### Phase 3 — Data Cleaning Governance & Lineage ✅ Implemented

> Implemented in `00e33af`: `src/governance/` (policies, preview service, governance service,
> custom registry), `src/storage/artifact_store.py`, and the `DatasetVersionRepository` /
> `CleaningExecutionRepository` repositories, covered by 10 test modules under `tests/governance/`.
> This heading previously carried no status marker while the Sprint 14 Definition of Done below
> ticked every Phase 3 item.

**Immutable Raw Dataset Storage**

- Preserve immutable raw uploaded dataset through a versioned artifact-storage abstraction.
- Store dataset with checksum/hash and metadata persisted in the database.
- The application should not care whether storage is local filesystem, S3, GCS, or Azure Blob.

- Maintain cleaned analytical dataset separately (database table or separate artifact).

**Configurable Missing-Value Policies**

- Implement configurable policies:
  - Preserve NULLs
  - Remove rows with missing values
  - Remove columns above threshold
  - Fill numeric (mean/median/mode)
  - Fill categorical (mode/constant)
  - Custom policy

**Cleaning Preview & Approval Workflow**

- Add explicit pipeline state: `UPLOADED → PROFILED → CLEANING_POLICY_REVIEW → USER_APPROVES/MODIFIES → CLEANING → QUALITY → ANALYTICS → REPORTING → AI_JOB`.
- Allow analysts to review cleaning policy before execution.
- Display impact assessment: rows affected, columns affected, percentage of data altered.
- Analyst can approve, modify, or reject the cleaning policy.
- Selected policy is persisted with the pipeline run.

**Cleaning Provenance & Lineage**

- Record cleaning decisions and transformation statistics:
  - Rows removed and percentage
  - Columns affected
  - Missing value treatment applied per column

- Expose before/after data-quality metrics (completeness, validity, consistency).
- Prevent silent information loss – notify user when cleaning materially changes the dataset.

- Assign immutable identifiers and checksums/hashes to source dataset versions.
- Persist cleaning configuration (policy version, parameters) associated with each pipeline run.
- Ensure analytical results are reproducible from the source dataset and recorded transformation configuration.

- Enable traceability:
  ```text
  Original Dataset
        │
        ▼
  Dataset Version (ID + checksum)
        │
        ▼
  Cleaning Configuration (versioned)
        │
        ▼
  Cleaning Execution
        │
        ▼
  Analytical Dataset
        │
        ▼
  Pipeline Run
        │
        ├── Quality Report
        ├── Analytics Report
        ├── Business Report
        └── AI Report
  ```

- Expose cleaning provenance in the UI and in report metadata.

---

#### Phase 4 — AI Data Context & Analytical Integrity ✅ Implemented

> Implemented in `00e33af`: `src/ai/context.py`, `src/ai/context_builder.py`, and the
> serialization changes in `src/llm/report_serializer.py`, covered by `tests/ai/test_ai_data_context.py`
> and `tests/ai/test_ai_context_isolation.py`. This heading previously carried no status marker
> while the Sprint 14 Definition of Done below ticked every Phase 4 item.

**Privacy-Safe AI Context**

- Provide AI with structured source-data quality metadata:
  - Original row count
  - Missing values (per column)
  - Duplicate rows
  - Invalid values
  - Outlier counts

- Provide AI with **aggregated analytical context** rather than the complete raw dataset:
  - Descriptive statistics
  - Distributions
  - Categorical frequencies
  - Correlations
  - Quality results

- Include cleaning transformations and data-loss statistics in AI context.
- Prevent AI from interpreting removed missing values as evidence that the original dataset had no missing data.

- Distinguish source-data observations from post-cleaning analytical findings:
  - Label insights clearly: "Based on the cleaned dataset of 1,480 rows (original: 2,358)…"
  - Add analytical caveats when cleaning materially changes the dataset.

**Optional Controlled Raw-Data Access**

- Implement optional controlled raw-data sampling only where analytically justified.
- Never expose unnecessary PII to the AI context by default.
- Clearly label whether an insight is based on source metadata, cleaned analytical results, or approved sample data.

---

#### Phase 5 — Reporting & Export Reliability ✅ Complete

- Repaired Report download functionality (ensured generated file is correct and downloadable).
- Implemented and stabilized PDF export (`PdfReportExporter` generating valid `%PDF-` documents with structured content).
- Validated generated files (integrity, vector format, typography, multi-page pagination).
- Ensured repeated export requests do not corrupt or unintentionally duplicate persisted report artifacts (idempotency).
- Enforced authenticated user ownership at database and orchestrator levels (strict multi-tenant isolation, IDOR defense).
- Established frontend-independent report export contracts (`GET /api/reports/{id}/export/text` and `GET /api/reports/{id}/export/pdf`).
- Added comprehensive export unit and integration test coverage.

---

#### Phase 6 — React Migration Readiness Foundation ✅ Implemented (foundation only)

> **Scope note (re-baseline):** Sprint 14 established the *initial* React-readiness foundation
> (API contracts, typed models, frontend service interfaces, migration mapping). It is not the
> final readiness gate. Sprint 15 stabilizes the product and workflows; **Sprint 16 performs the
> final, definitive React-readiness audit** after stabilization and provider changes. The
> statements below record what Sprint 14 claimed at the time.

**Critical Gate: Backend Usable Without Streamlit**

- Core application workflows are fully exercisable through REST APIs without Streamlit.
- Zero business logic resides exclusively inside Streamlit components.
- React migration can consume existing API contracts without backend redesign.
- Streamlit is treated strictly as a presentation client rather than an application-layer dependency.

**API Contracts & Typing**

- Froze and documented frontend/backend API contracts (OpenAPI 3.1) in `docs/api/openapi.json`.
- Stabilized strongly typed API response models across all API endpoints (33 paths after the duplicate `reports_router` registration was removed; the initial export counted 40) (`ReportsListResponse`, `ReportDataResponse`, `DashboardSummary`, `DashboardStatistics`, `DashboardCorrelation`, `DashboardDistribution`, `DashboardCategorical`, `PipelineSummary`, `ReportResponse`, `DashboardStatusResponse`, `ErrorResponse`).
- Created automated contract validation test suite in `tests/api/test_openapi_contract.py`.
- Validated standardized API error responses (`ErrorResponse`, status codes, messages).
- Validated authentication/authorization behavior across all frontend service boundaries.

**Frontend Service Architecture**

- Established technology-neutral frontend service interfaces independent of Streamlit:
  - `AuthService` (`src/frontend/services/auth_service.py`)
  - `DashboardService` (`src/frontend/services/dashboard_service.py`)
  - `ReportService` (`src/frontend/services/report_service.py`)
  - `AIService` (`src/frontend/services/ai_service.py`)
  - `UploadService` (`src/frontend/services/upload_service.py`)
  - `AdminService` (`src/frontend/services/admin_service.py`)

- Separated UI presentation state from application logic.
- Ensured all frontend functionality communicates through service/API boundaries.

**React Migration Mapping**

- Produced comprehensive migration architecture guide in `docs/api/REACT_MIGRATION_MAPPING.md`:
  - Streamlit page → React route mapping
  - Streamlit component hierarchy → React component tree
  - Streamlit service layer → React TypeScript API client
  - Session state → React AuthContext & DatasetContext
- Defined coexistence topology for Streamlit + React concurrent execution against FastAPI backend.

---

#### Phase 7 — Semantic Profiling, Visual Analytics & Quality Gates ✅ Implemented

> ✅ **Naming conflict resolved.** Phase 7 was previously titled *Regression, Contract &
> Quality Validation* here and *Semantic Profiling, Visual Analytics & AI Grounding
> Remediation* elsewhere. Both bodies of work were delivered; the combined title above is
> authoritative, matching PROJECT_STATE.md. The "478 tests" figure has no supporting evidence
> and is superseded by the executed **714**.

**Automated Testing**

- Full automated regression suite (backend and frontend).
- Frontend integration tests (authentication, upload, dashboard, reports, AI insights, admin).
- Export tests (download and PDF).
- AI workflow tests (asynchronous generation, status polling, retries, failure handling).
- Cleaning-policy tests (all configurable policies, data lineage tracking).
- Data-lineage tests (traceability from source to final outputs).
- Multi-user isolation regression tests (ensure Sprint 13 identity/ownership remains intact).

**Concurrency & Resource Testing**

- Concurrent pipeline execution testing.
- Concurrent AI-generation testing (duplicate job prevention).
- Multi-user concurrent access testing (resource contention).
- Resource contention testing for AI generation and database operations.

**Failure Isolation Testing**

- AI generation failure does not fail or corrupt successful pipeline execution.
- Export failure does not affect persisted reports.
- Frontend failure does not affect backend pipeline execution.
- Temporary AI/provider unavailability is represented as an AI-generation failure state rather than an application-wide failure.

**Performance & Security**

- Performance benchmarking and regression comparison.
- Security contract tests (authentication, authorization, RBAC enforcement).

**Quality Gates**

- Flake8 / Black / Isort / Mypy quality gates.
- `git diff --check` for whitespace and merge conflict markers.
- Documentation synchronization (update ARCHITECTURE.md, PROJECT_STATE.md, ADRs).
- **No Git commit by the assistant** – all changes are reviewed and committed by the lead engineer.

---

## Sprint 14 Definition of Done

> **How to read this checklist.** The ticks below record the sprint team's self-assessment at
> the time of writing. They are preserved unchanged for historical fidelity. Three of them are
> **contradicted by current repository evidence** and are annotated inline with ⚠️ below; one is
> not verifiable from the repository. Ticking this checklist did not, and does not, constitute
> a release: see PROJECT_STATE.md § *Sprint 14 Status — Verified Against the Repository*.

### UX & Frontend
- [x] Dashboard opens at top
- [x] Reports opens at top
- [x] AI Insights moved to dedicated navigation item
- [x] Navigation does not unnecessarily trigger expensive backend operations

### AI Execution & Job Lifecycle
- [x] Pipeline completion is independent of AI generation completion
- [x] Dashboard/Reports can render deterministic pipeline results before AI generation completes
- [x] AI generation executes asynchronously from pipeline completion
- [x] AI generation status is persisted independently of frontend state
- [x] AI generation associated with `pipeline_run_id`, `user_id`, `report_id`
- [x] AI generation state tracking implemented (`PENDING → GENERATING → READY / FAILED`)
- [x] Duplicate AI generation prevented (idempotency)
- [x] AI retry/failure behavior defined and tested
- [x] AI failure does not invalidate successful pipeline execution
- [x] AI job status and generated insights respect authenticated user ownership and ADMIN authorization
- [x] Asynchronous execution uses a replaceable background-job abstraction; implementation must not couple the application layer to a specific queue/worker technology

### Performance
- [x] Performance baselines established (API latency, dashboard load, pipeline, AI, exports)
  - ⚠️ *Qualified:* `performance/phase2_benchmark_results.md` records `Successful / Failed: 1 / 2`
    for the Ollama benchmark; its min/p50/p95/p99/max are all `88.44 s` from one successful run.
    The deterministic-pipeline latency figures are based on multiple runs and are unaffected.
- [x] Performance acceptance criteria defined
- [x] Performance regression comparison completed and documented
  - ⚠️ *Contradicted:* the benchmark artifact contains no comparison against any prior baseline.
    It reports absolute figures and a decoupling ratio only.

### Data Governance & Lineage
- [x] Raw dataset preserved through versioned artifact-storage abstraction
- [x] Source dataset has immutable identifier and checksum/hash
- [x] Cleaned dataset maintained separately
- [x] Configurable missing-value policies implemented
- [x] Cleaning preview available before destructive transformations
- [x] Analyst can approve or modify cleaning policy before execution
- [x] Selected policy is persisted with the pipeline run
- [x] Cleaning provenance recorded (rows removed, affected columns, percentage, policy details)
- [x] Before/after data-quality metrics exposed
- [x] Data lineage traceable from source → cleaning → pipeline → reports → AI
- [x] Cleaning configuration is versioned and persisted
- [x] Cleaning execution is reproducible from recorded configuration

### AI Data Context & Integrity
- [x] AI context includes source-data quality metadata
- [x] AI receives privacy-safe aggregated analytical context (not complete raw dataset)
- [x] AI distinguishes source-data observations from cleaned analytical findings
- [x] Analytical caveats included when cleaning materially changes the dataset
- [x] Optional controlled raw-data sampling available only where justified

### Reporting & Exports
- [x] Report download functional
- [x] PDF export functional
- [x] Export idempotency verified
- [x] Export integration tests passing
- [x] Exports respect authenticated user ownership

### React Migration Readiness (initial foundation — final gate is Sprint 16)
- [x] Core application workflows can be exercised through REST APIs without Streamlit
- [x] No business logic required by the React migration (now Sprint 17) resides exclusively inside Streamlit components
- [x] React migration can consume existing API contracts without backend redesign
- [x] Streamlit is treated as a presentation client rather than an application-layer dependency
- [x] Frontend/backend API contracts frozen and documented
- [x] API contract tests implemented (request/response schemas, backward compatibility, error responses)
- [x] Typed API response models stabilized
- [x] Frontend service interfaces established independent of Streamlit
- [x] React migration mapping documented
- [x] REST API parity validated for React migration readiness (re-verified in Sprint 16)

### Testing & Quality
- [x] Full regression suite passing
  - 🟡 *Partially substantiated by measurement:* executed 2026-09-12 — 535 collected, **529 passed**,
    6 failed, 0 skipped, 0 collection errors. The suite is not fully green: all 6 failures are
    live-LLM tests in `tests/ai/test_ollama_connection.py` that require a locally installed
    `gemma3:4b`. See PROJECT_STATE.md § *Executed Validation*.
  - ✅ *Superseded:* the later executed run records **714 passed, 0 failed, 15 deselected**
    (the live-LLM tests are now marked `integration` and deselected by default).
- [x] Concurrent pipeline execution tested
- [x] Concurrent AI generation tested
- [x] AI job idempotency tested
- [x] Multi-user concurrency tested
- [x] AI failure isolation verified
- [x] Export failure isolation verified
- [x] Performance benchmarking completed and documented
- [x] Flake8 / Black / Isort / Mypy quality gates passing
  - ⚠️ *Qualified:* `pyproject.toml` excludes `tests/` and 14 of the 18 `src/*` packages from Black and
    isort, and `.flake8` / `[tool.mypy]` disable several error classes, so these gates cover less
    than the wording implies. The three packages added by Sprint 14 (`src/governance/`,
    `src/profiling/`, `src/storage/`) are *not* excluded and are genuinely checked. These
    exclusions pre-date Sprint 14 and were inherited from `main`.
- [x] `git diff --check` passing
- [x] Documentation synchronized (ARCHITECTURE, PROJECT_STATE, ADRs)
  - ⚠️ *Contradicted at the time it was ticked:* `docs/project/ARCHITECTURE.md` was not modified
    by any Sprint 14 commit and still described Sprint 14 as *Planned*; no ADR was added or
    revised (ADR-025–028 already existed on `main` before this branch); and
    `docs/project/LESSONS_LEARNED.md` was likewise untouched. A documentation reconciliation
    pass has since annotated those files.
- [x] **No Git commit by the assistant** – all changes reviewed and committed by lead engineer
  - ℹ️ *Not verifiable from repository evidence.* All three Sprint 14 commits are authored
    `Amal jose <amaljose@Amals-MBP.Vortex.local>`; authorship metadata cannot establish who
    performed the review.
- [x] Definition of Done satisfied

---

## Re-baselined Sequence (Sprints 15–17)

The earlier plan defined Sprint 15 as the React migration. That plan is **obsolete**. Before
the presentation layer is replaced, the existing product has to be proven correct and the
AI/provider architecture has to be proven frontend-independent.

| Sprint | Purpose | Main Question |
|--------|---------|---------------|
| **Sprint 15** | Enterprise Stabilization, Governance Completion & Product/UX Remediation | Is the existing product actually correct, reliable, and valuable? |
| **Sprint 16** | AI Provider Abstraction & Complete React Readiness | Is the backend/provider architecture truly ready for a frontend replacement? |
| **Sprint 17** | React Migration & Modern Presentation Layer | Can we replace Streamlit without redesigning the backend? |

### Dependencies

```text
Sprint 14 release (v14.0.0)
      │
      ▼
Sprint 15 — Stabilization & Remediation (v15.0.0)
      │
      ▼
Sprint 16 — AI Provider Abstraction & React Readiness (v16.0.0)
      │
      ▼
Sprint 17 — React Migration (v17.0.0)
```

- Each sprint starts only after the previous one is released and merged to `main`.
- **React implementation must not begin in Sprint 15 or Sprint 16.**

### Evidence Vocabulary

Roadmap claims use: **Implemented** (code exists) · **Tested** (automated tests cover it) ·
**Verified** (exercised end-to-end through the real API/frontend path) · **Released** (tagged
and merged to `main`) · **Planned** (not started). A class, repository, endpoint or passing
unit test on its own does not make a feature *Verified*.

---

## Sprint 15 — Enterprise Stabilization, Governance Completion & Product/UX Remediation 📋

> **Status:** PLANNED / NOT STARTED. Starts after the v14.0.0 release is merged to `main`.

### Objective

Make AnalystGPT Enterprise a stable, internally consistent, tested product before introducing
additional architectural complexity. This is a structured engineering stabilization and
remediation release covering functional correctness, product value, governance,
administration, UX, regression risk, technical debt, and documentation/reality
reconciliation. It is not an open-ended bug-fixing sprint.

**React implementation is explicitly OUT OF SCOPE.** Current Streamlit defects are fixed at the
root cause, not deferred to the future React layer.

### Phase 1 — End-to-End Workflow Correctness

Audit and validate the real workflow through the actual application/API/frontend path:

```text
Upload → Preprocessing/Profile → Governance/Cleaning Review → Approval
       → Cleaning → Quality → Analytics → Reporting → AI
```

For each stage verify: input/output contracts, state transitions, persistence, error handling,
loading/processing states, retry behavior, ownership/RBAC, frontend/backend integration,
reproducibility, and downstream compatibility. Identify and fix broken or partially
implemented workflows.

### Phase 2 — Data Governance & Preprocessing Remediation

Prove the documented governance workflow functional end-to-end, and investigate why it does
not currently behave as intended. Audit and fix: profiling, cleaning policy generation,
cleaning preview, approval/modification/rejection, policy persistence, execution, provenance,
lineage, before/after quality metrics, reproducibility, dataset versioning, user ownership,
and UI/API synchronization.

No cosmetic frontend workaround for a backend governance defect.

### Phase 3 — Dashboard Product Value

The upload result and the Dashboard currently expose substantially overlapping information,
which weakens the Dashboard's decision-support value. Define what the Dashboard provides that
the immediate pipeline result/report does not, and redesign its information architecture
around ongoing analytical/operational value — for example: executive overview, KPI
monitoring, operational/data health, trends and changes over time, recent activity,
dataset/report history, anomalies or notable changes, AI insight status, and drill-down into
detailed analysis and reports.

Do not duplicate the pipeline result in a new layout. The backend remains the source of
analytical truth; no business logic moves into the frontend.

### Phase 4 — Admin / Identity / RBAC

Audit the admin experience against backend capability. Repository evidence at re-baseline:
`DELETE /api/admin/users/{user_id}` exists (`src/api/routes/admin.py` → `UserService.delete_user_admin`,
with a last-admin safeguard) and `AdminService.delete_user` exists in the frontend service
layer, but `src/frontend/views/admin_page.py` only exposes status changes
(ACTIVE / INACTIVE / SUSPENDED). The endpoint is *Implemented*; it is not yet *Verified*
end-to-end.

Reconcile frontend and backend. Expose user deletion only if the architecture supports it
safely, considering: ADMIN-only authorization, confirmation flow, audit logging, consequences
for owned datasets/reports/jobs, last-admin safeguards, soft- vs hard-delete, API/UI
consistency, and regression tests. Security and tenant isolation must not be weakened.

### Phase 5 — Functional Defect / UX Remediation

Systematic defect audit covering: broken workflows, API/frontend mismatches, stale state,
incorrect state transitions, loading/empty/error states, authentication/session issues, RBAC
issues, export problems, async AI job problems, navigation, duplicated and dead code,
misleading UI, edge cases, incorrect persistence, configuration issues, and
documentation/repository contradictions. Fix root causes.

### Phase 6 — Refactoring / Technical Debt

Refactor only where justified by defects, coupling, duplication, maintainability, or
React/provider readiness. Priorities: clear module boundaries, separation of concerns, stable
contracts, low coupling, high cohesion, removal of obsolete code, elimination of duplicated
business logic, cleaner dependency direction. No unnecessary rewrites.

### Phase 7 — Regression & Quality

Establish a trustworthy regression baseline: investigate every failing test, fix failures
that represent real defects, add regression tests for important fixes, and validate
integration workflows, security/RBAC, multi-user isolation, API contracts, async AI
workflows, concurrency where applicable, and exports. Run all quality gates, and review the
Black/isort/mypy/flake8 exclusions noted in the Sprint 14 Definition of Done.

Not permitted: deleting useful tests, weakening assertions without evidence, marking defects
as expected to obtain a green suite, or hiding implementation-caused failures.

### Phase 8 — Documentation Reconciliation

Reconcile ROADMAP, PROJECT_STATE, ARCHITECTURE, CHANGELOG, PROJECT_JOURNAL and relevant ADRs
with repository evidence, clearly distinguishing implemented, tested, verified, released,
pending and unresolved work.

### Sprint 15 Definition of Done

- [ ] Core workflow (Upload → … → AI) verified end-to-end through the real API/frontend path
- [ ] Governance/preprocessing workflow functional end-to-end (preview, approval/modification/rejection, persistence, execution, lineage, before/after quality)
- [ ] Dashboard information architecture redefined with value distinct from the pipeline result
- [ ] Admin UI capabilities match backend capabilities (user lifecycle incl. deletion decision)
- [ ] User deletion, if exposed, is ADMIN-only, confirmed, audited, and last-admin safe
- [ ] Important functional defects resolved at the root cause
- [ ] Regression tests added for every critical fix
- [ ] All failing tests investigated; no assertions weakened or tests removed without evidence
- [ ] Security, RBAC and multi-user isolation validated
- [ ] API contracts, async AI workflows and exports validated
- [ ] Quality gates passing
- [ ] Documentation matches repository reality
- [ ] No known critical / P0 / P1 blockers remain
- [ ] No React implementation introduced
- [ ] Definition of Done satisfied

---

## Sprint 16 — AI Provider Abstraction & Complete React Readiness 📋

> **Status:** PLANNED / NOT STARTED. Depends on the v15.0.0 release.

### Objective

Make the AI layer vendor-neutral and complete the final architecture/readiness work required
before Streamlit is replaced by React.

### Phase 1 — Pluggable AI Provider Architecture

Build on the existing abstraction (`src/llm/base_llm.py` `BaseLLM`, `src/llm/llm_factory.py`
`LLMFactory`, which currently registers only `ollama` → `OllamaClient`). Do not create a
parallel framework unless repository evidence proves the existing abstraction inadequate.

```text
AI Business Logic → Provider Interface → Selected Provider (Ollama | Gemini | future)
```

Supported providers: **Ollama** and **Google Cloud / Gemini API**, selected by configuration.
Business logic must not know which provider executes a request; future providers (e.g. Groq)
must be addable as isolated adapters.

Define and validate: provider interface; registration/factory mechanism; model selection;
provider configuration; environment variables/secrets; request/response normalization;
timeouts; retries and transient-failure handling; mapping of provider-specific exceptions to
stable application errors; logging and observability; provider/model metadata; testability;
deterministic provider selection; backward compatibility with current AI workflows.
Validate switching between Ollama and Gemini without changing AI business logic.

### Phase 2 — Final React Readiness Audit

End-to-end readiness review across core/configuration, upload, cleaning, governance, quality,
analytics, reporting, export, persistence, database abstraction, FastAPI, OpenAPI, BI/Power
BI, AI, authentication, authorization/RBAC, async jobs, storage, frontend services, session
handling, Docker/deployment, testing and documentation.

Verify that: React can consume the APIs without backend redesign; no business logic is trapped
in Streamlit; API contracts are stable; request/response schemas are typed and documented;
error responses are consistent; authentication/RBAC is API-driven; async AI job states are
externally consumable; upload/export/download is frontend-independent; ownership/isolation is
enforced server-side; and no hidden Streamlit dependency blocks migration.

Sprint 14 Phase 6 established the initial readiness foundation; this audit is the **definitive
readiness gate** before React implementation, run after Sprint 15 remediation and Sprint 16
provider changes.

### Phase 3 — React Technical Architecture Definition

**Do not implement the React application.** Define and document (ADR) the architecture Sprint
17 will implement: React + TypeScript, application structure, routing, API client strategy,
server-state/data-fetching strategy, authentication/session strategy, RBAC model, component
architecture, design system and design tokens, accessibility standards, responsive behavior,
charting/visualization strategy, forms, error/loading/empty states, async AI job UX model,
testing strategy, build/deployment strategy, and Streamlit + React coexistence strategy.

Evaluate and document the visual-system approach rather than adopting a component library by
default. The goal is a high-quality enterprise analytics UX, not a generic dashboard.

### Sprint 16 Definition of Done

- [ ] Ollama provider works through the provider interface
- [ ] Google Cloud / Gemini provider works through the provider interface
- [ ] Provider selection is configuration-driven and deterministic
- [ ] Provider errors mapped to stable application errors; timeouts/retries defined and tested
- [ ] Future providers can be added as isolated adapters
- [ ] AI business logic remains provider-agnostic (switching verified without code changes)
- [ ] Backend/API contracts verified for React consumption
- [ ] Final React readiness audit (definitive gate) passes; frontend-independent backend behavior proven
- [ ] React architecture and design-system decisions documented (ADR)
- [ ] No React application built
- [ ] Documentation synchronized
- [ ] Definition of Done satisfied

---

## Sprint 17 — React Migration & Modern Presentation Layer 📋

> **Status:** PLANNED / NOT STARTED. Depends on the v16.0.0 release.

### Objective

Replace Streamlit incrementally with React + TypeScript while preserving backend behavior and
API contracts, implementing the architecture defined in Sprint 16.

### Critical Architectural Constraint

**Only the presentation layer may be replaced.** REST API endpoints and OpenAPI contracts,
dependency injection, application-layer orchestration, business modules, persistence and
database abstraction, the AI layer and provider abstraction, authentication/authorization/RBAC,
ownership models, and security/isolation boundaries remain stable and backward compatible.

### Core Scope

- React + TypeScript application with an enterprise design system and reusable components
- Authentication, session management, RBAC-aware navigation
- Dashboard, Upload, Reports, AI Insights, Admin, Profile/account
- API integration and async AI job states
- Loading/error/empty states, responsive UX, accessibility
- Analytics visualization
- Frontend unit/component tests and E2E validation
- Production build and deployment

### Migration Principles

- React consumes the existing backend/API layer; no business logic moves into React.
- Streamlit remains available during migration and validation.
- Migrate incrementally, workflow by workflow, preserving functional parity where applicable.
- Apply the product/UX requirements identified in Sprint 15; do not reproduce known Sprint 15 defects.

### React Design System

A coherent AnalystGPT Enterprise design system defining typography, spacing, colors, surface
hierarchy, borders/radii, elevation, interaction states, accessibility, component behavior,
data-visualization conventions and responsive rules. Use the minimum necessary dependencies.

### Sprint 17 Definition of Done

- [ ] Functional parity with Streamlit demonstrated per migrated workflow
- [ ] API contract compatibility validated
- [ ] Authentication and RBAC-aware UI working
- [ ] Dashboard, Upload, Reports, AI Insights, Admin and Profile workflows work end-to-end
- [ ] Frontend unit/component and E2E tests passing
- [ ] Accessibility baseline passes
- [ ] Responsive behavior validated
- [ ] No backend business logic embedded in React
- [ ] Streamlit coexistence/deprecation plan completed
- [ ] Documentation synchronized
- [ ] Definition of Done satisfied

React becomes the validated primary presentation layer only when all items above are met.

---

# Engineering Standards

Every future sprint must preserve:

- Enterprise layered architecture
- Stable module contracts
- SOLID principles
- Separation of concerns
- High cohesion
- Low coupling
- Automated unit testing
- Integration testing
- Performance validation
- Documentation quality
- Engineering governance
- Architecture Decision Records
- Definition of Done compliance
- Stable REST API contracts
- OpenAPI compliance
- Swagger validation
- Dependency Injection validation
- API integration testing
- Multi-user data isolation
- Server-side authorization enforcement
- Enterprise identity and RBAC
- Structured operational logging
- End-to-end request correlation
- Operational health and readiness semantics
- Container security and non-root execution
- Presentation Layer independence
- Frontend Service Layer contracts
- Stable frontend contracts
- React migration compatibility
- Reusable component architecture
- Session state isolation
- API-first frontend design

No sprint is considered complete until all engineering standards
are satisfied.

---

# Release Policy

Every release must include:

- Updated documentation
- Passing automated tests
- Successful integration tests
- Performance validation (where applicable)
- Updated Architecture Decision Records
- Updated CHANGELOG
- Updated PROJECT_JOURNAL
- Updated PROJECT_STATE
- Updated ARCHITECTURE (if architecture changes)

Only releasable software progresses to the next sprint.

---

# Repository Maturity Goals

The roadmap gradually evolves the repository through the following
engineering maturity levels:

| Phase | Goal |
|--------|------|
| Foundation | ✅ Complete |
| Core Infrastructure | ✅ Complete |
| Enterprise Governance | ✅ Complete |
| Analytics Pipeline | ✅ Complete |
| Enterprise Reporting | ✅ Complete |
| Enterprise Architecture | ✅ Complete |
| Database Layer | ✅ Complete |
| SQLite Persistence | ✅ Complete |
| PostgreSQL Support | ✅ Complete |
| External Integrations | ✅ Complete |
| Business Intelligence | ✅ Complete |
| User Interface | ✅ Complete |
| AI Layer | ✅ Complete |
| Production Deployment | ✅ Complete |
| Enterprise Identity & Multi-User | ✅ Complete |
| UX Stabilization & Data Governance | 🟡 Implemented & tested, released in v14.0.0; end-to-end governance behavior NEEDS REMEDIATION in Sprint 15 |
| Product Stabilization & Governance Completion | 📋 Sprint 15 |
| AI Provider Abstraction & React Readiness | 📋 Sprint 16 |
| React Migration | 📋 Sprint 17 |

---

# Long-Term Vision

Upon completion, AnalystGPT Enterprise will demonstrate practical
experience across multiple software engineering disciplines.

## Software Engineering

- Enterprise architecture
- Design patterns
- Modular systems
- Large-scale documentation
- Release engineering

---

## Data Engineering

- Data ingestion
- ETL pipelines
- Data quality
- Database engineering
- Data persistence

---

## Analytics Engineering

- Statistical analytics
- Reporting
- Business intelligence
- Dashboard integration
- Decision support

---

## Platform Engineering

- REST APIs
- Desktop application
- Cloud deployment
- CI/CD
- Monitoring
- Production operations
- FastAPI
- REST Services
- OpenAPI
- Swagger
- Service-Oriented Architecture
- Enterprise identity & multi-user architecture
- Observability & operational reliability

---

## Frontend Engineering

- Enterprise frontend architecture
- Service-oriented UI architecture
- React + TypeScript architecture (defined Sprint 16, implemented Sprint 17)
- Enterprise design system
- Component-based design
- State management
- API integration

---

## Artificial Intelligence

- LLM integration
- AI-generated reports
- Business recommendations
- Executive summaries
- Natural language analytics
- Explainable AI
- Vendor-neutral LLM provider architecture (Ollama, Gemini, future adapters)

---

# Success Criteria

The project will be considered complete when it demonstrates the
ability to independently:

- Design enterprise software architecture
- Build modular and scalable systems
- Develop production-quality analytics pipelines
- Engineer database-backed applications
- Integrate external APIs
- Produce enterprise reporting solutions
- Build business intelligence integrations
- Apply automated testing throughout the system
- Maintain comprehensive engineering documentation
- Defend architectural decisions through ADRs
- Deliver production-ready software
- Design enterprise REST APIs
- Build service-oriented architectures
- Design stable API contracts
- Develop documented backend services
- Integrate BI platforms through REST APIs
- Build interactive analytical dashboards
- Develop Business Intelligence services
- Deliver enterprise dashboard APIs
- Design enterprise frontend architecture
- Develop reusable UI component systems
- Architect service-oriented frontend applications
- Design AI-assisted analytics systems
- Build explainable analytics platforms
- Deploy containerized multi-service architectures with Docker and Docker Compose
- Implement enterprise authentication, authorization, and RBAC
- Enforce strict server-side multi-user data isolation
- Implement production observability with structured logging and request correlation
- Deliver reliability controls, operational health probes, and disaster recovery validation
- Operate a vendor-neutral, configuration-driven AI provider layer
- Migrate presentation layer to modern React while preserving backend contracts

---

# Current Roadmap Status

Current repository state:

- ✅ Stable Enterprise Architecture
- ✅ Stable Application Layer
- ✅ Stable Module Contracts
- 🟡 Automated Test Suite implemented & passing per PROJECT_STATE.md; trustworthy regression baseline pending Sprint 15
- ✅ Stable Performance Validation
- 🟡 Engineering Documentation extensive; known documentation/repository contradictions — reconciliation pending Sprint 15
- ✅ Stable Persistence Layer
- ✅ Stable Repository Layer
- ✅ Stable Database Abstraction Layer
- ✅ Stable REST API Layer
- ✅ Stable API Contracts
- ✅ Stable Swagger Documentation
- ✅ Stable OpenAPI Specification
- ✅ Stable Business Intelligence Layer
- ✅ Stable Power BI Integration
- 🟡 Frontend Layer implemented & tested; remediation planned in Sprint 15
- 🟡 Streamlit Frontend released (v10.0.0); needs remediation (pending Sprint 15)
- 🟡 Dashboard implemented; product value/information architecture needs remediation (pending Sprint 15)
- ✅ Stable AI Insight Engine
- ✅ Stable Production Deployment & Docker Containerization
- ✅ Enterprise Identity & Multi-User Platform released (v13.0.0); 🟡 Admin UI/backend user-lifecycle reconciliation pending Sprint 15
- 🟡 Technical Debt not verified as low — known duplication, dead code, quality-gate exclusions and UI/API mismatches pending Sprint 15
- 📋 AI provider abstraction (Ollama + Gemini) and final React-readiness gate pending Sprint 16
- ✅ Sprint 13 Complete
- ✅ Sprint 14 released (v14.0.0)
- 📋 Sprint 15 (Stabilization & Remediation) is next — may begin now that v14.0.0 is released
- 📋 Sprint 16 (AI Provider Abstraction & React Readiness) follows v15.0.0
- 📋 Sprint 17 (React Migration) follows v16.0.0 — no React work before then

---

**Roadmap covers through:** **v17.0.0 (planned)**

**Last released version:** **v14.0.0**

**Next Planned Sprint Release:** **v15.0.0 — Sprint 15: Enterprise Stabilization, Governance Completion & Product/UX Remediation** → v16.0.0 (Sprint 16) → v17.0.0 (Sprint 17)