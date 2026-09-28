# AnalystGPT Enterprise — PROJECT_STATE.md

> **Purpose**
>
> This document is the primary engineering context for AnalystGPT Enterprise.
>
> It serves as the project's "boot memory" for engineers and AI assistants —
> read this first, in under two minutes, to know exactly where the project stands.
>
> This document intentionally describes the **current** state only.
>
> Historical implementation details belong in:
>
> - PROJECT_JOURNAL.md
> - CHANGELOG.md
> - Sprint Release Reports
>
> Full architectural detail (per-module components, pipelines, dependency
> rules, test coverage, performance data) lives in **ARCHITECTURE.md**.
> This document is the summary; ARCHITECTURE.md is the reference.

---

# Quick Orientation

| | |
|---|---|
| **Current version** | **v14.0.0** — released 2026-09-28 (tag `v14.0.0`, `main`) |
| **Previous version** | v13.0.0 (tag `v13.0.0` = `c5ddf06`) |
| **Current sprint** | **Sprint 14 — Stabilization / Production Hardening** |
| **Sprint 14 status** | ✅ **Released as v14.0.0** |
| **Next sprint** | **Sprint 15 — Enterprise Stabilization, Governance Completion & Product/UX Remediation** (planned, not started) |
| **Sequence** | Sprint 15 (Stabilization) → Sprint 16 (AI Provider Abstraction & React Readiness) → Sprint 17 (React Migration) — see ROADMAP.md |

AnalystGPT Enterprise is an enterprise-grade analytics pipeline (Upload →
Cleaning → Quality → Analytics → Reporting → **AI Insight Engine** → REST API → Power BI →
Streamlit Frontend → **Enterprise Identity & Multi-User Platform**), built as a self-directed
software engineering exercise to develop production-level architecture, testing, and
delivery skills.

Sprint 14 delivered the **Enterprise Stabilization & Governance Platform**:

- Asynchronous AI job lifecycle (`PENDING` → `GENERATING` → `READY` / `FAILED`) with non-blocking background workers and a database-backed state machine (`ai_jobs`, `ai_reports`)
- Transparent data cleaning governance (`src/governance/`, `DatasetVersionRepository`, `CleaningExecutionRepository`) over an immutable artifact store (`src/storage/`)
- Semantic data profiling (`SemanticClassifier`, `DataProfiler`) and intelligent chart budgeting (`VisualizationPlanner`)
- Publication-grade reporting (`PdfReportExporter`, `TextReportExporter`) with empirical distribution charts, executive KPI summaries, and data lineage cards
- Evidence-grounded AI serialization in `ReportSerializer` and `PromptBuilder`, strictly distinguishing distinct category cardinality from percentage frequencies
- A single `/api` route convention — the unprefixed `/reports/*` and `/powerbi/*` aliases were removed (**breaking**; see CHANGELOG.md)
- Frozen OpenAPI 3.1 contract (`docs/api/openapi.json`, 33 paths) and a technology-neutral frontend service layer preparing for the React migration (`docs/api/REACT_MIGRATION_MAPPING.md`)
- Full formatter coverage: `black` and `isort` now check all of `src/` and `tests/`

All backend and frontend contracts other than the removed unprefixed aliases remain
backward compatible.

---

# Sprint 14 Status — Verified Against the Repository

> **Status vocabulary used throughout this repository's documentation:**
> **Implemented** · **Implemented and test-covered** · **Validated** · **Released** ·
> **Deferred** · **Known issue**.
>
> A claim is recorded here as verified only when it is supported by repository
> evidence: files, implementation, tests, configuration, or an executed command.

| Dimension | Status | Evidence |
|---|---|---|
| **1. Implementation** | ✅ **Complete** | All seven Sprint 14 phases are implemented across commits `00e33af`, `b59df37`, `0f6d5eb` plus the stabilization work in the current tree. The packages `src/governance/`, `src/profiling/`, `src/storage/`, the asynchronous AI job layer (`src/ai/job_executor.py`, `src/ai/models.py`) and `src/reporting/exporters/pdf_report_exporter.py` are present and non-stub — the only `NotImplementedError` bodies in `src/` are `abc.abstractmethod` declarations. |
| **2. Validation** | ✅ **Passing** | `pytest -q` → **714 passed, 15 deselected, 0 failed**, 118.73 s. See *Executed Validation* below. |
| **3. Quality gates** | ✅ **Passing** | `flake8 src tests` → 0. `black --check src tests` → 341 files unchanged. `isort --check src tests` → clean. `mypy src` → no issues in 210 source files. |

**Sprint 14 is released as v14.0.0 (tag `v14.0.0`, merged to `main`). Sprint 15 — Enterprise Stabilization, Governance
Completion & Product/UX Remediation — has not started; no Sprint 15 work exists in this
repository.**

---

## Executed Validation — authoritative

This is the single authoritative figure for the current baseline. Every other total in this
repository is historical and is scoped as such below.

**Command:** `pytest -q` (project virtualenv, Python 3.11, Windows)

| Metric | Value |
|---|---|
| Test functions defined | **695** (`def test_*` under `tests/**/test_*.py`) |
| Collected, all markers | **729** (695 definitions plus 34 further cases from 9 `@pytest.mark.parametrize` decorators) |
| Collected, default marker filter | **714** |
| **Passed** | **714** |
| **Failed** | **0** |
| Deselected | **15** (`-m "not integration"`, set in `pyproject.toml`) |
| Collection errors | **0** |
| Test modules | **118** |
| Warnings | 1 (third-party `anyio` deprecation via `starlette.testclient`) |
| Duration | 118.73 s |

`714 passed + 15 deselected = 729 collected.` The accounting reconciles exactly.

### The 15 deselected tests

`pyproject.toml` sets `addopts = -ra -m "not integration"` and registers the marker:

> `integration: requires live external infrastructure (Ollama, REST API). Deselected by
> default; run with pytest -m integration.`

The 15 deselected tests live in `tests/ai/test_ollama_connection.py` and
`tests/ai/test_ollama_production_path.py`. They require a reachable Ollama server with
`gemma3:4b` installed and are run deliberately with `pytest -m integration`. They are neither
failures nor skips. This closes the earlier open question about live-LLM tests failing in
environments where the model is absent.

### Static analysis — executed

| Gate | Command | Result |
|---|---|---|
| Lint | `flake8 src tests --count` | **0** |
| Format | `black --check src tests` | **341 files unchanged** |
| Imports | `isort --check src tests` | **clean** |
| Types | `mypy src` | **no issues found in 210 source files** |

Run the formatters in UTF-8 mode on Windows (`PYTHONUTF8=1`, set by `scripts/lint.ps1`): 35
files legitimately contain characters outside cp1252, and without it `isort` skips them
silently while still exiting 0.

### Historical test totals, explicitly scoped

These figures appear in older documents. None of them describes the current baseline.

| Number | Scope |
|---|---|
| **714** | **Current.** Passing tests at v14.0.0. |
| **535 / 529** | Historical Sprint 14 in-flight totals, recorded before the suite was completed and before the `integration` marker existed. |
| **531** | Historical claim from the Sprint 14 closure entry. Never reconciled; superseded. |
| **329** | Historical **Sprint 13** total. |
| **180** | Historical **Sprint 11** total (ARCHITECTURE.md, correctly scoped there). |

---

## Resolved During Sprint 14 Stabilization

These were open blockers during the sprint and are now closed. They are listed because
several documents in this repository referred to them as outstanding.

| Item | Resolution |
|---|---|
| Unused `src/llm/llm_service.py` wrapper | Removed with its test; all LLM access goes through `LLMFactory`. |
| Undeclared `matplotlib` dependency | Declared in `requirements.txt`. `ReportingManager` imports the PDF exporter at module level, so `matplotlib` is a hard dependency of the core application and REST API, not only of the frontend. |
| Live-LLM tests failing without `gemma3:4b` | Resolved by the `integration` marker and the default `-m "not integration"` filter in `pyproject.toml`. |
| Formatter gates covering almost nothing | `pyproject.toml` previously excluded `tests/` and 15 of 17 `src/` packages from `black` and `isort`. All of `src/` and `tests/` is now covered; only non-source trees are excluded. 231 files were reformatted across two passes. |
| Dual registration of `reports_router` | Removed. Every functional router is mounted once, under `API_PREFIX`. Enforced by `tests/api/test_openapi_contract.py::test_every_path_is_under_the_api_prefix`. |
| `docs/api/openapi.json` out of sync | Re-exported from the live application: **33 paths, 42 schemas, `info.version` 14.0.0**. |
| Test runs writing into the developer's working tree | `SQLITE_DATABASE_PATH`, `REPORT_OUTPUT_DIRECTORY` and `ARTIFACT_STORE_DIRECTORY` are overridable and are redirected to a temporary directory by `tests/conftest.py`. |

---

## Known Technical Debt

Verified against the current repository. None of these blocks the v14.0.0 release; all are
in scope for Sprint 15 (or Sprint 16 where noted), per ROADMAP.md.

- **Relaxed lint and type configuration.** `.flake8` sets `extend-ignore = E203, W503, E302,
  E303, E304, E305, W292, W293, W391, E501, F401, F541`; `[tool.mypy]` sets
  `disable_error_code = ["var-annotated", "union-attr", "arg-type", "return-value",
  "assignment"]`. Both gates pass, but they check less than a default configuration would.
  Tightening them is a candidate for Sprint 15.
- **The OpenAPI contract freeze is weakly enforced.** `tests/api/test_openapi_contract.py`
  compares only the `openapi` version string and the *number* of paths between
  `docs/api/openapi.json` and the live schema. A rename, or a request/response schema change
  that preserves the path count, would pass undetected.
- **The Ollama performance baseline rests on a single sample.**
  `performance/phase2_benchmark_results.md` records `Successful / Failed: 1 / 2`; its min,
  p50, p95, p99 and max are all `88.44 s` from that one successful run, with a standard
  deviation of `0.00`, and it contains no comparison against a prior baseline.
- **CI does not run on feature branches.** `.github/workflows/ci.yml` triggers only on
  `push` / `pull_request` targeting `main`, so branch work is validated locally until merge.
- **Configuration defaults disagree across files.** `src/core/config.py` defaults
  `POSTGRES_PORT` to `5433` while `.env.example` and the Compose service use `5432`; and
  `docker-compose.yml` still pins `AI_CONTEXT_WINDOW: 4096` and `AI_TIMEOUT: 120`, which
  `src/core/config.py` and `.env.example` have since raised to `8192` and `600`. These are
  behavioural defaults rather than documentation, and are recorded here rather than changed.
- **Plotly is advertised but unused.** `src/frontend/components/about_card.py` and
  `footer.py` list Plotly in the UI tech-stack strings, but no module imports `plotly` — the
  charts are matplotlib. The dependency was dropped in the v14.0.0 `requirements.txt` audit
  and the UI strings still claim it.
- **Admin UI does not match backend capability.** `DELETE /api/admin/users/{user_id}`
  (`src/api/routes/admin.py` → `UserService.delete_user_admin`, last-admin safeguard) and
  `AdminService.delete_user` exist, but `src/frontend/views/admin_page.py` only exposes
  ACTIVE / INACTIVE / SUSPENDED. Deletion is *Implemented*, not *Verified* end-to-end. Sprint 15 Phase 4.
- **Governance workflow not verified end-to-end.** `src/governance/` and `src/storage/` are
  implemented and tested, but the preview → approval → execution → lineage workflow has not
  been proven through the real API/frontend path and is reported as not functioning as
  intended. Sprint 15 Phase 2.
- **Dashboard duplicates the pipeline result.** The Dashboard largely overlaps the upload
  result, limiting its decision-support value. Sprint 15 Phase 3.
- **Single LLM provider.** `src/llm/llm_factory.py` registers only `ollama`; no Gemini or
  other adapter exists. Sprint 16 Phase 1.

---

# Project Health Dashboard

| Area | Status |
|------|--------|
| Project | AnalystGPT Enterprise |
| Version | **v14.0.0** (released 2026-09-28) |
| Repository Status | ✅ Sprint 14 released — all 7 phases, 714 / 714 tests passing, all four static gates passing |
| Current Sprint | ✅ **Sprint 14 — Stabilization / Production Hardening (released as v14.0.0)**; Sprint 15 next |
| Current Focus | **Sprint 15 — Enterprise Stabilization, Governance Completion & Product/UX Remediation** |
| Architecture | ✅ Enterprise Layered Architecture + REST API + Streamlit Frontend + AI Insight Engine + Docker Containerization + GitHub Actions CI + Enterprise Identity & Authentication Engine + Resource Ownership & Data Isolation + Declarative RBAC & Admin Management + Frontend Authentication & Session Isolation + Stabilized Frontend UX + Asynchronous AI Job Lifecycle & Persistent Background Worker + Semantic Data Profiling & Visual Analytics + Data Cleaning Governance + Publication-Grade PDF/TXT Exporters |
| Documentation | 🟡 Reconciled with ROADMAP.md; ARCHITECTURE.md, ADR-028 and REACT_MIGRATION_MAPPING.md pending Sprint 15 Phase 8 |
| Frontend UX Stabilization | ✅ Implemented (Sprint 14 Phase 1 Accepted) |
| Scroll Reset & Layout Hierarchy | ✅ Implemented (Sprint 14 Phase 1 Accepted) |
| Dedicated AI Insights Page | ✅ Implemented (Sprint 14 Phase 1 Accepted) |
| Role-Aware Navigation & Public About | ✅ Implemented (Sprint 14 Phase 1 Accepted) |
| Session Caching & Backend Call Audit | ✅ Implemented (Sprint 14 Phase 1 Accepted) |
| Asynchronous AI Execution & Decoupling | ✅ Implemented (Sprint 14 Phase 2 Accepted) |
| Persistent AI Job State Machine | ✅ Implemented (Sprint 14 Phase 2 Accepted) |
| Background AI Worker & Retry Isolation | ✅ Implemented (Sprint 14 Phase 2 Accepted) |
| Database Repositories (ai_jobs, ai_reports)| ✅ Implemented (Sprint 14 Phase 2 Accepted) |
| AI REST Endpoints & Status Polling | ✅ Implemented (Sprint 14 Phase 2 Accepted) |
| Data Cleaning Governance & Lineage | 🟡 Implemented & tested (Sprint 14 Phase 3); end-to-end workflow needs remediation — Sprint 15 |
| AI Data Context & Grounding Integrity | ✅ Implemented (Sprint 14 Phase 4 Accepted) |
| Reporting & PDF/TXT Exporter Redesign | ✅ Implemented (Sprint 14 Phase 5 Accepted) |
| OpenAPI 3.1 & React Migration Readiness| ✅ Initial foundation implemented (Sprint 14 Phase 6); final readiness gate is Sprint 16 |
| Semantic Profiling & Visual Analytics | ✅ Implemented (Sprint 14 Phase 7 Accepted) |
| AI Grounding & Categorical Remediation | ✅ Implemented (Sprint 14 Final Remediation) |
| Identity Domain Models & RBAC | ✅ Complete (Sprint 13 Phase 1) |
| Security Request Context | ✅ Complete (Sprint 13 Phase 1) |
| Cryptographic Password Hasher | ✅ Complete (Sprint 13 Phase 1) |
| User Repository Abstraction | ✅ Complete (Sprint 13 Phase 1) |
| Auth Dependency Injection | ✅ Complete (Sprint 13 Phase 1 & 2) |
| Identity Schema & Migration | ✅ Complete (Sprint 13 Phase 1 & 3) |
| UserService Domain Service | ✅ Complete (Sprint 13 Phase 2 & 4) |
| Signed Access Token Engine | ✅ Complete (Sprint 13 Phase 2) |
| User Registration & Login API | ✅ Complete (Sprint 13 Phase 2) |
| Token Revocation & Logout | ✅ Complete (Sprint 13 Phase 2) |
| Resource Ownership & Isolation | ✅ Complete (Sprint 13 Phase 3) |
| IDOR Prevention & Query Scoping | ✅ Complete (Sprint 13 Phase 3) |
| Multi-User Application Caching | ✅ Complete (Sprint 13 Phase 3) |
| Declarative RBAC Dependencies | ✅ Complete (Sprint 13 Phase 4) |
| Admin User Management API | ✅ Implemented & tested (Sprint 13 Phase 4); delete endpoint not exposed in UI — Sprint 15 |
| Structured Security Audit Trail | ✅ Complete (Sprint 13 Phase 4) |
| Frontend Authentication UI | ✅ Complete (Sprint 13 Phase 5) |
| Frontend Session & Tenant Isolation | ✅ Complete (Sprint 13 Phase 5) |
| Role-Aware Navigation & Admin UI | 🟡 Implemented (Sprint 13 Phase 5); Admin UI lacks user deletion — Sprint 15 |
| Upload Module | ✅ Complete |
| Cleaning Module | ✅ Complete |
| Quality Module | ✅ Complete |
| Analytics Module | ✅ Complete |
| Reporting Module | ✅ Complete |
| Application Layer | ✅ Complete |
| Database Abstraction Layer | ✅ Complete |
| SQLite Support | ✅ Complete |
| PostgreSQL Integration | ✅ Implemented |
| Repository Layer | ✅ Complete |
| API Layer | ✅ Complete |
| REST API | ✅ Complete |
| Swagger Documentation | ✅ Complete |
| OpenAPI Generation | ✅ Complete |
| Power BI Integration | ✅ Complete |
| Dashboard Service | ✅ Complete |
| Dashboard Models | ✅ Complete |
| Streamlit Frontend | 🟡 Implemented & tested; defect/UX remediation pending Sprint 15 |
| Dashboard View | 🟡 Implemented; product value/information architecture needs remediation — Sprint 15 |
| Upload Interface | ✅ Complete |
| Reports Centre | ✅ Complete (Session Cached) |
| AI Insights Page | ✅ Complete (Dedicated Destination) |
| About Page | ✅ Complete (Public Access Preserved) |
| Frontend Components | ✅ Complete |
| Frontend Services | ✅ Complete |
| Session Management | ✅ Complete |
| Enterprise Navigation | ✅ Complete |
| AI Insight Engine | ✅ Complete |
| Production Logging & Rotation | ✅ Complete (Sprint 12 Phase 2) |
| Multi-Stage Dockerfile | ✅ Complete (Sprint 12 Phase 3) |
| Docker Compose Topology | ✅ Complete (Sprint 12 Phase 4) |
| GitHub Actions CI Pipeline | ✅ Complete (Sprint 12 Phase 5) |
| Deployment Architecture & ADRs | ✅ Complete (Sprint 12 Phase 6) |
| Automated Testing | ✅ **714 / 714 passing.** 729 collected, 714 passed, 0 failed, 15 deselected (`integration`), 0 errors — see *Executed Validation* |
| Static Analysis | ✅ flake8 0 · black clean (341 files) · isort clean · mypy clean (210 files) |
| Integration Testing | ✅ Passed |
| Frontend Validation | ✅ Passed |
| Large Dataset Validation | ✅ Passed |
| Stress Testing | ✅ Passed |
| AI Pipeline Validation | ✅ Passed (Ollama gemma3:4b verified) |
| Technical Debt | 🟡 Not verified as low — itemised under *Known Technical Debt*; audit in Sprint 15 |
| Next Sprint | **Sprint 15 — Enterprise Stabilization, Governance Completion & Product/UX Remediation** (planned, not started) |

---

# Mission

Build an enterprise-grade analytics platform while developing the ability
to independently design, architect, implement, test, document, optimize,
review, and deploy production-quality analytics software.

---

# Current Architecture

```
Browser
   │
   ▼
Streamlit Frontend
   │
   ▼
Views (Dashboard, Upload, Reports, About)
   │
   ▼
Components (Reusable UI Library)
   │
   ▼
Frontend Services (API Client, Session Manager)
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
   ├── Upload
   ├── Cleaning
   ├── Quality
   ├── Analytics
   ├── Reporting
   ├── Persistence
   ├── PipelineReport
   ├── AI Insight Engine
   │     ├── Executive Summary Engine
   │     ├── Recommendation Engine
   │     ├── Explanation Engine
   │     └── Narrative Engine
   │     │
   │     ▼
   │   BaseLLM
   │     │
   │     ▼
   │   LLMFactory
   │     │
   │     ▼
   │   OllamaClient
   │     │
   │     ▼
   │   Ollama (configured default: `gemma3:4b`)
   │
   ├── AIResult
   │
   ▼
REST API / Streamlit / Power BI
```

The architecture emphasises that **all orchestration is owned by Application.run()**.
The pipeline first produces a `ReportingReport`, then persists it, and finally wraps it
into a `PipelineReport` which is enriched by the AI engines. The AI layer does **not**
replace the reporting or persistence stages — it adds insights after the fact.
The frontend communicates solely via the REST API, preserving the integrity of
the backend contracts.

Detailed architecture is documented in ARCHITECTURE.md.

---

# Stable Module Contracts

| Module | Input | Output |
|--------|-------|--------|
| Upload | Dataset Path | Pandas DataFrame |
| Cleaning | Raw DataFrame | Cleaned DataFrame |
| Quality | Cleaned DataFrame | QualityReport |
| Analytics | Cleaned DataFrame | AnalyticsReport |
| Reporting | AnalyticsReport | ReportingReport |
| **AI Manager** | **PipelineReport** | **AIResult** |
| **Executive Summary Engine** | **ReportingReport** | **str** |
| **Recommendation Engine** | **ReportingReport** | **list[str]** |
| **Explanation Engine** | **ReportingReport** | **list[str]** |
| **Narrative Engine** | **ReportingReport** | **str** |
| **LLMFactory** | **Provider Name** | **BaseLLM** |
| **OllamaClient** | **Prompt** | **Generated Text** |
| Persistence | Report Objects | PersistenceResult |
| Application | Dataset Path | PipelineResult |
| API Layer | HTTP Request | HTTP Response |
| DashboardService | ReportingReport | Dashboard Models |
| Power BI API | HTTP Request | Dashboard Response |
| Frontend Views | User Interaction | UI Render |
| Frontend Components | Props | UI Elements |
| Frontend Services | API Request | API Response |

All contracts are stable and backward‑compatible.

---

# Current Engineering Rules

The following architectural rules are considered stable:

- `main.py` is an application entry point only.
- `Application` owns end‑to‑end pipeline orchestration.
- Each business capability has a single Manager.
- Business modules never orchestrate other business modules.
- Managers communicate using stable contracts.
- Shared services remain inside `src/core`.
- Report objects replace loosely typed dictionaries.
- The application returns a strongly typed `PipelineResult`.
- Logging is centralized.
- Configuration is centralized.
- Automated testing validates every architectural change.
- Every architectural change to module boundaries or dependency
  direction requires a new ADR (see ARCHITECTURE.md).
- Application owns persistence lifecycle.
- Business modules never execute SQL.
- Repository classes own all database operations.
- PersistenceManager coordinates repositories.
- Database infrastructure remains isolated from business logic.
- DatabaseConnection is the only database abstraction.
- ConnectionFactory owns database selection.
- DatabaseManager owns connection lifecycle.
- SchemaManager supports multiple SQL dialects.
- Repository classes never know concrete database engines.
- Business logic remains database‑independent.
- API layer contains no business logic.
- API routes communicate only with Application Layer.
- Dependency Injection owns Application lifecycle.
- Request validation handled by Pydantic.
- Response serialization handled by Pydantic.
- Global exception handling centralized.
- OpenAPI generated automatically.
- Swagger documentation must remain operational.
- REST API contracts remain backward compatible.
- DashboardService owns dashboard generation.
- Power BI endpoints never access business modules directly.
- Business Intelligence Layer communicates only with Application Layer.
- Dashboard models remain immutable.
- Power BI contracts remain backward compatible.
- Views contain no business logic.
- Components are presentation‑only.
- Frontend Services communicate with Application Layer through REST API.
- Views never access persistence.
- Frontend remains backend‑independent.
- React migration must not require backend changes.
- Business logic remains outside Streamlit.
- Navigation is centralized.
- Session State stores presentation state only.
- **AI Manager orchestrates all LLM interactions.**
- **AI engines are isolated and focused on single responsibilities.**
- **Prompt Builder abstracts prompt construction.**
- **LLM clients are pluggable via LLMFactory.**
- **AI responses are validated and parsed into structured objects.**
- **AI never stores or mutates business data — it only enhances reports.**

---

## Presentation-Layer Replacement Constraint (Sprint 17)

> The React migration is planned for **Sprint 17**, after Sprint 15 (stabilization) and
> Sprint 16 (AI provider abstraction and the final React-readiness gate). No React work may
> start before Sprint 17. The constraint below is a standing architectural rule, not a
> description of work in progress.

The Streamlit frontend serves as the MVP presentation layer.

Any future React migration must preserve:

- REST API contracts
- Application Layer
- Business modules
- Persistence Layer
- AI Insight Engine contracts

**Only the presentation layer is expected to change.**

This constraint ensures that the architectural integrity of the backend
and the service boundaries remain intact, allowing a smooth transition
to a modern React frontend when the time comes.

---

# Repository Structure

Verified against the working tree: **210 Python files under `src/`**, in 18 packages.

```
src/
├── core/                        # Shared infrastructure (no dependencies on business modules)
│   ├── config.py                # All environment-driven configuration
│   ├── constants.py             # APP_VERSION, API prefixes, AI section names
│   ├── exceptions.py            # AnalystGPTError hierarchy, incl. identity errors
│   ├── logger.py                # Centralized logger + RotatingFileHandler
│   └── pii.py                   # Shared contact-PII column-name rule
│
├── application/                 # Orchestration — owns the end-to-end pipeline
│   ├── app.py                   # Application.run()
│   ├── ai_orchestrator.py
│   ├── dashboard_orchestrator.py
│   ├── reporting_orchestrator.py
│   ├── pipeline_report.py
│   └── pipeline_result.py
│
├── upload/                      # csv / excel / json readers + UploadManager
├── cleaning/                    # column, text, missing-value, duplicate, datatype cleaners
├── quality/                     # completeness, validity, consistency, uniqueness, outliers
├── analytics/                   # descriptive, numerical, categorical, correlation,
│                                # distribution, statistical interpretation,
│                                # visualization_planner.py
├── profiling/                   # SemanticClassifier, DataProfiler, profiling models
├── reporting/
│   ├── report_builder.py, reporting_manager.py, structured_report.py,
│   ├── executive_summary.py, kpi_formatter.py, reporting_report.py
│   └── exporters/
│       ├── pdf_report_exporter.py
│       └── text_report_exporter.py
│
├── governance/                  # Cleaning governance, policies, lineage
│   ├── governance_service.py, preview_service.py, policies.py,
│   └── custom_registry.py, models.py
├── storage/                     # Immutable artifact store (raw bytes + cleaned parquet)
│
├── ai/                          # AI Insight Engine + asynchronous job lifecycle
│   ├── ai_manager.py, ai_report.py, ai_result.py, unified_report_engine.py
│   ├── executive_summary_engine.py, recommendation_engine.py,
│   ├── explanation_engine.py, narrative_engine.py
│   ├── confidence_evaluator.py, insight_engine.py, insight_validator.py
│   ├── models.py                # AIJob, AIJobStatus, AIFailureCategory
│   ├── job_executor.py          # AIJobExecutor (ThreadPoolExecutor worker)
│   ├── ai_job_service.py
│   ├── context.py, context_builder.py
│   └── exceptions.py
│
├── llm/                         # Provider abstraction
│   ├── base_llm.py, llm_factory.py, ollama_client.py
│   └── prompt_builder.py, report_serializer.py, response_parser.py
│
├── identity/                    # Enterprise identity, authn & authz
│   ├── models.py                # User, UserRole, UserStatus
│   ├── permissions.py           # Permission enum + ROLE_PERMISSIONS matrix
│   ├── password_hasher.py       # PBKDF2-HMAC-SHA256, 600,000 iterations
│   ├── token_service.py         # HMAC-SHA256 signed tokens (HS256)
│   ├── token_revocation.py, user_service.py, audit.py
│   ├── interfaces.py, in_memory_user_repository.py
│   ├── context.py               # UserContext
│   └── exceptions.py
│
├── api/                         # REST API — no business logic
│   ├── server.py                # FastAPI app, CORS, routers, lifespan
│   ├── routes/                  # root, health, version, auth, admin, pipeline,
│   │                            # dashboard, reports, powerbi, ai, governance
│   ├── models/                  # request_models, response_models, ai_models,
│   │                            # governance_models
│   ├── dependencies/            # application_dependency, auth_dependencies
│   └── exceptions/              # exception_handlers
│
├── persistence/                 # PersistenceManager + result/report contracts
├── database/                    # Database Abstraction Layer
│   ├── database_connection.py, sqlite_connection.py, postgresql_connection.py
│   ├── connection_factory.py, database_manager.py, schema_manager.py
│   └── repositories/            # base, pipeline_run, dataset, quality, analytics,
│                                # report, user, ai_job, ai_report,
│                                # dataset_version, cleaning_config,
│                                # cleaning_execution
│
├── integrations/
│   └── powerbi/                 # dashboard_service + dashboard/summary/statistics/
│                                # correlation/distribution/categorical + models
│
└── frontend/                    # Streamlit presentation layer
    ├── streamlit_app.py
    ├── views/                   # dashboard, upload, report, ai_insights,
    │                            # admin, about, login
    ├── components/              # 22 presentation-only components
    ├── services/                # api_client, auth, dashboard, report, ai,
    │                            # upload, admin, session_manager
    ├── config/settings.py
    └── theme/                   # colours, icons, shadows, spacing, typography
```

## Database schema

`src/database/schema_manager.py` creates 11 tables across both SQLite and PostgreSQL:

`users` · `pipeline_runs` · `datasets` · `quality_reports` · `analytics_reports` ·
`reports` · `ai_jobs` · `ai_reports` · `dataset_versions` · `cleaning_configs` ·
`cleaning_executions`

Ownership indexes on `user_id` back the server-side scoping that prevents IDOR.

## Repository root

```
main.py                  CLI entry point (batch pipeline execution)
requirements.txt         Runtime + tooling dependencies
pyproject.toml           black / isort / mypy / pytest configuration
Dockerfile               Multi-stage: base, builder, runtime-base, api, frontend, cli
docker-compose.yml       postgres + api + frontend on analystgpt_network
.env.example             Environment template
.flake8                  Lint configuration
.github/workflows/ci.yml 5-job CI pipeline
scripts/                 lint.ps1, run_tests.ps1, gemma_benchmark.py
tests/                   118 test modules
performance/             Benchmarks and stress tests
docs/                    ADRs, API, deployment, engineering, project, sprints
```

---

# Validation Status

## Unit Testing

All modules and layers are covered by an automated test suite.

**Status:** ✅ **714 / 714 passing** across **118 test modules**, plus 15 `integration`-marked
tests deselected by default and run with `pytest -m integration`. See *Executed Validation*
for the full accounting.
The figure of *180 tests* shown in ARCHITECTURE.md is the Sprint 11 total and is scoped as
such there.
(Per‑component breakdown: see ARCHITECTURE.md → Testing Strategy)

---

## Integration Testing

Validated complete pipeline execution:

REST API
→ Swagger Validation
→ OpenAPI Validation
→ Pipeline Endpoint
→ Dependency Injection
→ End‑to‑end Pipeline
→ Persistence Layer
→ Database Abstraction Layer
→ PipelineResult
→ Power BI API
→ Dashboard Endpoints
→ Summary, Statistics, Correlation, Distribution, Categorical endpoints
→ **AI Insight Engine** (all engines)
→ **PipelineReport** enrichment

**Status:** ✅ Passed

---

## Frontend Validation

- Dashboard view renders correctly
- Upload interface processes files
- Reports centre displays results
- About page loads
- Navigation operates correctly
- Session state persists
- API client communicates with backend
- REST API compatibility verified
- Power BI compatibility verified
- Large dataset validation passes
- Stress testing passes
- Performance validation passes

**Status:** ✅ Passed

---

## AI Pipeline Validation

- Prompt generation produces well‑structured inputs
- Response parsing correctly extracts structured outputs
- All AI engines integrate with the reporting pipeline
- End‑to‑end AI enrichment executes without errors
- LLM client (Ollama) responds within acceptable latency

**Status:** ✅ Passed

---

## Performance Validation

Validated successfully using:

| Dataset | Approximate Rows | Status |
|----------|-----------------:|--------|
| `sample_data/customer_data.csv` | 500 | ✅ Passed |
| `performance/datasets/customer_data_large.csv` | ~100,000 | ✅ Passed |
| `performance/datasets/customer_data_stress_test.csv` | ~1,000,000 | ✅ Passed |

Validation included:

- Functional correctness
- Large dataset execution
- Stress testing
- SQLite persistence
- PostgreSQL architecture validation
- Report generation
- Pipeline stability
- REST API validation
- Swagger documentation validation
- OpenAPI generation
- Pipeline execution through REST API
- Power BI endpoint validation
- Dashboard service validation
- Frontend rendering performance
- API response times
- Session state management
- **AI generation with large reports**
- **LLM response times**

Performance benchmarks are maintained in:

performance/benchmark_results.md

---

# Completed Sprint Timeline

Quick‑scan history — full detail in PROJECT_JOURNAL.md and CHANGELOG.md.

| Sprint | Delivered |
|--------|-----------|
| 0 – 0.75 | Project foundation, repo structure, engineering governance, ADR framework |
| 1 | Upload Module (CSV/Excel/JSON readers) |
| 2 | Cleaning Module (columns, text, missing values, duplicates, dtypes) |
| 3 | Quality Module (completeness, validity, consistency, uniqueness, outliers) |
| 4 | Analytics Module (descriptive, numerical, categorical, correlation, distribution) |
| 5 | Reporting Module (executive summaries, KPIs, timestamped text export) + performance validation up to 1M rows |
| 5.5 | Application layer, `PipelineResult`, thin `main.py`, typed report contracts across all modules |
| 6 | SQLite persistence, repository layer, database schema, PersistenceManager, Application integration, stress testing |
| 7 | Database Abstraction Layer, DatabaseConnection, ConnectionFactory, PostgreSQL implementation, SchemaManager dialect support, repository compatibility, persistence refactoring |
| 8 | REST API Layer, FastAPI, Dependency Injection, Request/Response Models, Swagger, OpenAPI, REST API Testing, Live Endpoint Validation |
| 9 | Power BI Integration, DashboardService, Dashboard Models, Power BI REST Endpoints, PostgreSQL and SQLite runtime validation, Stress Testing, Performance Benchmarking |
| 10 | Enterprise Streamlit Frontend, Dashboard View, Upload Interface, Reports Centre, About Page, Reusable Component Library, Frontend Services, Session Management, Enterprise Navigation, Backend Integration, React‑ready Architecture |
| 11 | AI Insight Engine, Local LLM Architecture, Ollama Integration, LLM Abstraction, Executive Summary, Recommendation, Explanation and Narrative Engines, PipelineReport, AIResult, Prompt Builder, Response Parser |
| 12 | Production Deployment, Multi-Stage Dockerfile (`api`, `frontend`, `cli`), Docker Compose Topology, Bounded Rotating File Logging, GitHub Actions 5-Job CI Pipeline, ADR-022, ADR-023, Deployment Guide |
| 13 | Enterprise Identity & Multi-User Platform, Domain Models, PBKDF2 Password Hasher, Signed TokenService, TokenRevocationService, UserService, UserRepository, Server-Side Data Isolation & IDOR Defense, Declarative RBAC, Admin Management API & UI, Streamlit Auth & Session Isolation, Audit Trail, ADR-024, 329 Automated Tests |
| 14 | Stabilization / Production Hardening: Asynchronous AI Job Lifecycle (`ai_jobs`, `ai_reports`, `AIJobExecutor`), Data Cleaning Governance & Lineage (`src/governance/`, `src/storage/`, `dataset_versions`, `cleaning_configs`, `cleaning_executions`), Semantic Profiling (`src/profiling/`) & VisualizationPlanner, Publication-Grade PDF/TXT Exporters, AI Grounding & Cardinality Remediation, OpenAPI 3.1 Contract Freeze (33 paths) & React Migration Blueprint, single `/api` route convention (breaking), full formatter coverage, ADR-025 – ADR-028, 714 Automated Tests |

---

# Development Environment

- Python 3.11
- Pandas 3.x
- Pytest
- FastAPI
- Uvicorn
- Pydantic
- HTTPX (testing)
- SQLite
- PostgreSQL
- psycopg 3
- Streamlit
- Plotly
- **Ollama**
- **`gemma3:4b`** — the configured default (`src/core/config.py` `OLLAMA_MODEL`,
  `.env.example`), and the model used for Sprint 14 live E2E validation. Earlier revisions of
  this document listed *Qwen3:8B*; that was the Sprint 11-era model and no longer matches
  configuration. The provider/model abstraction (`LLMFactory`) keeps both interchangeable.
- **ollama Python SDK**
- Visual Studio Code
- Git
- GitHub
- Power BI
- Docker & Docker Compose

---

# Engineering Governance

The following documents define repository standards and engineering policies:

| Document | Purpose |
|----------|---------|
| PROJECT_CONSTITUTION.md | Engineering principles |
| ENGINEERING_OPERATING_MANUAL.md | Development workflow |
| ENGINEERING_PLAYBOOK.md | Engineering practices |
| CODE_REVIEW_CHECKLIST.md | Review standards |
| DEFINITION_OF_DONE.md | Completion criteria |
| DOCUMENTATION_STANDARDS.md | Documentation conventions |
| ADR/ | Architecture decision history |

---

# Canonical Project Documents

| Document | Purpose |
|----------|---------|
| PROJECT_STATE.md | Current project status (this document) |
| ARCHITECTURE.md | System architecture, components, tests, performance |
| ROADMAP.md | Future development |
| PROJECT_JOURNAL.md | Engineering history |
| CHANGELOG.md | Version history |
| ADR/ | Architecture decisions |

---

# Current Engineering Maturity

> **Scope of these ratings.** These are a self-assessment of the **v14.0.0** baseline: the
> code in this repository, with the suite and all four static gates passing. They are an
> engineering judgement, not an external audit or a production-traffic record.

| Area | Maturity Level |
|------|----------------|
| Architecture | Production Ready |
| Backend | Production Ready |
| Frontend | MVP (Streamlit) — remediation pending Sprint 15 |
| Database | Production Ready |
| REST API | Production Ready |
| Power BI Integration | Production Ready |
| **AI Layer** | **Production Ready (Local LLM Integration)** |
| **Deployment** | **Production Ready (Docker & CI)** |
| **Enterprise Identity & Multi-User** | **Production Ready (PBKDF2 + JWT + RBAC)** |
| **Data Governance & Lineage** | **Implemented & tested (`src/governance/`, `src/storage/`); end-to-end verification pending Sprint 15** |
| **Asynchronous AI Job Lifecycle** | **Production Ready (`ai_jobs` / `ai_reports` state machine, background worker)** |
| **Semantic Profiling & Visual Analytics** | **Production Ready (`src/profiling/`, `VisualizationPlanner`)** |
| AI Provider Abstraction | Planned (Sprint 16 — Ollama + Gemini; not started) |
| React Presentation Layer | Planned (Sprint 17; not started) |

---

# Current Focus

Sprint 13 was completed and released as **v13.0.0**.

**Sprint 14 — Stabilization / Production Hardening — is implemented and validated locally.
Its release as v14.0.0 (tag + merge to `main`) is pending.**

## Sprint 14 — delivered phases

All seven phases are implemented, test-covered, and passing the full quality gate set.

| Phase | Delivery | Principal modules |
|---|---|---|
| **1 — Frontend UX Stabilization** | ✅ Complete | Scroll reset on navigation, redesigned dashboard hierarchy, dedicated AI Insights page, public About, role-aware Admin nav, session caching (`src/frontend/components/scroll_to_top.py`, `views/ai_insights_page.py`, `services/session_manager.py`) |
| **2 — Asynchronous AI Job Lifecycle** | ✅ Complete | Pipeline response decoupled from Ollama inference; database-backed state machine `PENDING → GENERATING → READY / FAILED` with idempotency and failure isolation (`src/ai/models.py`, `job_executor.py`, `ai_job_service.py`, `ai_jobs` / `ai_reports` repositories, `/api/ai/*`) |
| **3 — Data Cleaning Governance & Lineage** | ✅ Complete | Immutable raw dataset version vs separate cleaned analytical dataset, configurable missing-value policies, before/after quality metrics, provenance tracking (`src/governance/`, `src/storage/artifact_store.py`, `/api/governance/*`) |
| **4 — AI Analytical Context & Data Integrity** | ✅ Complete | Privacy-safe aggregated context separated from source-data quality metadata; cleaning transformation context carried into prompts (`src/ai/context.py`, `context_builder.py`) |
| **5 — Reporting & Export Reliability** | ✅ Complete | Publication-grade PDF and text exporters, authenticated ownership verification, direct REST export endpoints (`src/reporting/exporters/`, `src/application/reporting_orchestrator.py`, `/api/reports/**/export/*`) |
| **6 — API Contract & Migration Readiness** | ✅ Complete (initial foundation; final gate Sprint 16) | OpenAPI 3.1 contract freeze across **33 paths**, strongly typed response models, technology-neutral frontend services (`AuthService`, `DashboardService`, `ReportService`, `AIService`, `UploadService`, `AdminService`), migration blueprint in `docs/api/REACT_MIGRATION_MAPPING.md` |
| **7 — Semantic Profiling, Visual Analytics & Quality Gates** | ✅ Complete | 20-class `SemanticType` taxonomy and `AnalyticalRole` classification, `VisualizationPlanner` 4–8 chart budget, AI grounding and cardinality-vs-frequency remediation, plus the regression/contract suites and the four static gates (`src/profiling/`, `src/analytics/visualization_planner.py`, `src/llm/report_serializer.py`, `src/llm/prompt_builder.py`) |

> **Phase 7 naming, resolved.** Two names for Phase 7 circulated during the sprint —
> *Regression, Contract & Quality Gates* and *Semantic Profiling, Visual Analytics & AI
> Grounding Remediation*. Both bodies of work were delivered, so the disagreement was over
> naming rather than scope. The combined title above is the authoritative one, and
> ROADMAP.md now uses it. The "478 tests" figure that
> appeared alongside the older phrasing has no supporting evidence anywhere in the
> repository and is superseded by the executed count of **714**.

---

# Next Sprint

Scope and Definitions of Done are defined in ROADMAP.md. None of these sprints has started;
nothing in this repository should be read as their delivery.

| Sprint | Release | Purpose | Status |
|---|---|---|---|
| **15** | v15.0.0 | Enterprise Stabilization, Governance Completion & Product/UX Remediation — end-to-end workflow correctness, governance remediation, Dashboard product value, Admin/RBAC reconciliation, defect/UX remediation, regression baseline, documentation reconciliation. React out of scope. | 📋 Planned |
| **16** | v16.0.0 | AI Provider Abstraction (Ollama + Gemini, configuration-driven) & final React-readiness audit; React architecture defined, not built. | 📋 Planned |
| **17** | v17.0.0 | React + TypeScript migration of the presentation layer; Streamlit coexistence/deprecation. | 📋 Planned |

Dependency chain: Sprint 14 release → Sprint 15 → Sprint 16 → Sprint 17.

---

# Current Blockers

**None.** v14.0.0 is released. Known product defects are Sprint 15 scope.

Current repository status:

- ✅ Stable Architecture
- ✅ Stable Application Layer
- ✅ Stable Module Contracts
- ✅ **714 / 714 automated tests passing**, 0 failed, 15 `integration`-marked tests deselected by default
- ✅ All four static gates passing (flake8, black, isort, mypy)
- ✅ Stable Performance
- ✅ Stable REST API — 33 paths, single `/api` convention, OpenAPI 3.1 contract in sync
- ✅ Stable Power BI Integration
- 🟡 Streamlit Frontend implemented & tested; remediation pending Sprint 15
- ✅ Stable AI Insight Engine with asynchronous job lifecycle
- ✅ Stable Production Deployment & Docker Topology
- ✅ Stable Enterprise Identity & Multi-User Platform
- 🟡 Data Cleaning Governance & Lineage implemented & tested; end-to-end remediation pending Sprint 15
- 🟡 PROJECT_STATE reconciled with ROADMAP.md; remaining documents pending Sprint 15
- ✅ Sprint 13 complete (v13.0.0)
- ✅ **Sprint 14 released (v14.0.0)**
- 📋 Sprint 15 → Sprint 16 → Sprint 17 planned, not started

Items that remain open are recorded under *Known Technical Debt* near the top of this
document. They are debt, not blockers.

---

# Documentation Reconciliation Notes

This revision reconciled repository documentation with the v14.0.0 implemented state,
verified against the source tree, the executed test suite, the executed static gates, and
the live FastAPI schema. Historical statements were **scoped, not deleted**.

| Area | Correction |
|---|---|
| Release | v14.0.0 released 2026-09-28 (release commit + tag `v14.0.0`, `main` fast-forwarded). |
| Version and sprint status | *Superseded by the roadmap reconciliation (pre-release):* an earlier revision recorded v14.0.0 as the current baseline. Git evidence (no `v14.0.0` tag; `main` at `c5ddf06`) shows it is prepared, not released; this document now says so, matching ROADMAP.md. |
| Sprint 15–17 sequence | Sprint 15 renamed from *Refactoring & Architectural Evolution* to *Enterprise Stabilization, Governance Completion & Product/UX Remediation*; Sprint 16 (AI Provider Abstraction & React Readiness) and Sprint 17 (React Migration) added, matching ROADMAP.md. |
| Test counts | Superseded by a single executed figure: **714 passed / 729 collected / 15 deselected**. The historical 535 / 531 / 529 / 329 / 180 totals are catalogued and scoped. |
| Static analysis | Previously recorded as "not run" and as covering only 4 of 18 `src/` packages. Both statements are now false: all four gates were executed and pass, and `pyproject.toml` covers all of `src/` and `tests/`. |
| API surface | The API has **33 paths**, not 40. The unprefixed `/reports/*` and `/powerbi/*` aliases were removed, and every functional router is mounted once under `/api`. |
| `docs/api/openapi.json` | Re-exported from the live application; `info.version` now tracks `APP_VERSION` at 14.0.0. The previously reported 9 missing response properties are present. |
| Phase 7 | The two competing names are reconciled into one authoritative title above. |
| `src/core/constants.py` | `APP_VERSION` was `12.0.0` and is now `14.0.0`. It feeds `GET /`, `GET /api/version` and the OpenAPI `info.version`, so the stale value was visible in the live API. |
| `requirements.txt` | Header corrected from v12.0.0 to v14.0.0, and the dependency set reconciled against actual imports. |
| `docs/deployment/DEPLOYMENT_GUIDE.md` | Identity environment variables corrected to the names `src/core/config.py` actually reads; macOS-absolute links made repository-relative. |
| `docs/api/API_REFERENCE.md` | Endpoint tables corrected to the real `/api`-prefixed paths and the real auth requirements. |
| ADR-025 – ADR-028 | Status promoted from *Proposed (Planned for Sprint 14)* to *Accepted*, matching the delivered implementation. |

---

# Resolved Questions

These were previously recorded as open. All are now answered from repository evidence.

1. **What is the authoritative passing-test count?** **714**, executed. Recorded once, under
   *Executed Validation*; every other document references that section rather than
   restating a number.
2. **Which Phase 7 definition is correct?** Both bodies of work were delivered; the
   combined title under *Current Focus* is authoritative.
3. **Is the dual registration of `reports_router` intentional?** Resolved by removal. Every
   functional router is mounted once under `API_PREFIX`, enforced by
   `tests/api/test_openapi_contract.py::test_every_path_is_under_the_api_prefix`. The
   removal of the unprefixed aliases is recorded as a breaking change in CHANGELOG.md.
4. **Should the relaxed lint/format/type gate configuration be tightened?** The formatter
   exclusions are gone — `black` and `isort` now cover all of `src/` and `tests/`. The
   `.flake8` and `[tool.mypy]` suppression lists remain and are carried as technical debt
   for Sprint 15 (Phase 7 — Regression & Quality).
5. **Should the Ollama performance baseline be re-run?** Yes — it is still a single
   successful sample out of three attempts. Carried as technical debt.

---

# Definition of Success

The project succeeds when I can independently:

- Design enterprise software architecture.
- Build modular and scalable applications.
- Apply SOLID principles consistently.
- Develop production‑quality ETL pipelines.
- Implement comprehensive automated testing.
- Build interactive analytical dashboards.
- Package desktop applications.
- Design database architectures.
- Integrate external systems and APIs.
- Produce enterprise reporting solutions.
- Deploy production‑ready systems.
- Review and optimize software architecture.
- Defend architectural decisions through ADRs.
- Communicate engineering trade‑offs clearly.
- Design enterprise REST APIs.
- Build service‑oriented architectures.
- Design API contracts.
- Build production‑ready backend services.
- Integrate analytics platforms through REST APIs.
- Build enterprise dashboard applications.
- Design Business Intelligence integrations.
- Deliver production‑ready analytics dashboards.
- Design enterprise frontend architectures.
- Build service‑oriented UI applications.
- Implement AI‑assisted analytics.
- Implement enterprise identity, authentication, and RBAC systems.
- Enforce strict server-side multi-user data isolation and IDOR prevention.
- Lead React migration projects (planned: Sprint 17).
- Develop enterprise dashboard solutions.
- Demonstrate software architecture leadership.
- Deliver production‑quality software engineering.

---

**Current version:** **v14.0.0** — Enterprise Stabilization, Data Governance & Grounded Reporting (released 2026-09-28)

**Previous version:** **v13.0.0** — Enterprise Identity & Multi-User Platform

**Last completed sprint:** **Sprint 14 — Stabilization / Production Hardening (released)**

**Next sprint:** **Sprint 15 — Enterprise Stabilization, Governance Completion & Product/UX Remediation** (planned, not started)

---
