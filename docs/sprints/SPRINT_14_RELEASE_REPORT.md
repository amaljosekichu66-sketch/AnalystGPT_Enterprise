# Sprint 14 Release Report

**Project:** AnalystGPT Enterprise

**Sprint:** Sprint 14 — Stabilization / Production Hardening

**Version:** v14.0.0

**Status:** ✅ **Released** — 2026-09-28, tag `v14.0.0`

---

> **How to read this report.** The delivery narrative below was written during the sprint and
> is preserved. Every component it names was confirmed to exist and to be non-stub. The
> *Verification & Test Results* section has been updated with executed figures; the in-flight
> totals it originally carried (535 / 531) are superseded by the executed **714 passing**.
> The authoritative current-state record is PROJECT_STATE.md, section *Executed Validation*.

---

# Sprint Goal

Deliver enterprise stabilization across the presentation, analytical, and governance tiers of AnalystGPT Enterprise: decouple synchronous AI generation into an asynchronous database-backed background job lifecycle, introduce immutable dataset versioning and transparent data cleaning governance, implement semantic data profiling and intelligent visualization planning, provide publication-grade multi-page PDF and text reporting, enforce strict evidence grounding in AI interpretations, freeze OpenAPI 3.1 contracts, and prepare technology-neutral frontend service interfaces for the React migration.

---

# Objectives & Phase Delivery

## Phase 1 — Frontend UX Stabilization
- Implemented `ScrollToTop` component (`src/frontend/components/scroll_to_top.py`) resetting scroll position on navigation.
- Redesigned Dashboard information hierarchy with KPI summary cards and structured analytical tabs.
- Created dedicated AI Insights view (`src/frontend/views/ai_insights_page.py`) with asynchronous job polling and retry actions.
- Preserved public unauthenticated access to the About page (`src/frontend/views/about_page.py`).
- Added robust loading, empty, and transition states (`src/frontend/components/empty_state.py`).
- Added session state caching avoiding duplicate network calls (`src/frontend/services/session_manager.py`).

## Phase 2 — Asynchronous AI Generation & Job Lifecycle
- Decoupled analytical pipeline completion from LLM inference in `Application.run()`.
- Implemented persistent database-backed AI job state machine (`PENDING` → `GENERATING` → `READY` / `FAILED`) in `src/ai/models.py`.
- Created thread-pool background execution worker (`src/ai/job_executor.py`) with failure and retry isolation.
- Built database repository abstractions (`AIJobRepository`, `AIReportRepository`) across SQLite and PostgreSQL.
- Exposed REST endpoints for AI job status polling and retries (`/api/ai/jobs/{job_id}`, `/api/ai/jobs/latest/status`, `/api/ai/jobs/{job_id}/retry`).

## Phase 3 — Data Cleaning Governance & Lineage
- Built immutable raw artifact store (`src/storage/artifact_store.py`) preserving original upload bytes with SHA-256 checksums.
- Created separate analytical dataset storage for cleaned datasets (`.parquet`).
- Implemented configurable missing-value and outlier policies (`src/governance/policies.py`).
- Built non-destructive cleaning preview service (`src/governance/preview_service.py`) and interactive UI (`src/frontend/views/upload_page.py`).
- Implemented provenance tracking repository (`CleaningExecutionRepository`) recording before/after quality metrics.

## Phase 4 — AI Analytical Context & Data Integrity
- Created authoritative typed data context entities (`AIDataContext`, `SourceDataContext`, `CleaningContext`, `AnalyticsContext`, `LineageContext`) in `src/ai/context.py`.
- Built database-backed context builder (`src/ai/context_builder.py`) querying authoritative repository records with tenant isolation.
- Updated prompt serialization in `ReportSerializer` to distinguish raw ingested rows from cleaned rows, preventing hallucinated dataset completeness.

## Phase 5 — Reporting & Publication-Grade Exporters
- Designed multi-page `%PDF-1.4` publication report (`src/reporting/exporters/pdf_report_exporter.py`) featuring 5-page A4 layout, executive KPI cards, 13-column governance tables, empirical horizontal distribution bars, AI interpretation cards, and provenance metadata.
- Rebuilt plain-text report exporter (`src/reporting/exporters/text_report_exporter.py`) with demarcated AI interpretation sections.
- Enforced authenticated ownership verification and IDOR prevention on report export streaming endpoints (`/api/reports/{id}/export/*`).

## Phase 6 — OpenAPI 3.1 & React Migration Readiness
- Exported authoritative, frozen OpenAPI 3.1 specification (`docs/api/openapi.json`).
  The initial export counted **40 paths** because `reports_router` was registered twice,
  once unprefixed and once under `/api`. Stabilization removed the unprefixed aliases, so
  the contract is now **33 paths / 42 schemas** — one path per route declaration.
- Added strongly typed Pydantic response models (`src/api/models/response_models.py`).
- Abstracted presentation logic into technology-neutral frontend service interfaces (`UploadService`, `AdminService`, `ReportService`, `AIService`, `DashboardService`, `APIClient`).
- Authored comprehensive React migration mapping blueprint (`docs/api/REACT_MIGRATION_MAPPING.md`).

> **Scope (roadmap re-baseline).** Phase 6 established the *initial* React-readiness
> foundation. The final, definitive readiness audit is a Sprint 16 gate, and React is
> implemented only in Sprint 17.

## Phase 7 — Semantic Profiling, Visual Analytics & AI Grounding Remediation

> **Phase naming, resolved.** Phase 7 circulated under two names — the one above and
> *Regression, Contract & Quality Gates*. Both bodies of work were delivered, so the
> disagreement was over naming rather than scope. The authoritative combined title is
> *Semantic Profiling, Visual Analytics & Quality Gates*; see PROJECT_STATE.md.
- Implemented 20-class `SemanticType` and `AnalyticalRole` taxonomy with deterministic `SemanticClassifier` and `DataProfiler` (`src/profiling/`).
- Built authoritative `VisualizationPlanner` (`src/analytics/visualization_planner.py`) enforcing a 4–8 chart budget and responsive 2×2 / 3×3 grid layout.
- Upgraded Column Profile component (`src/frontend/components/column_profile.py`) with 8-column profiling metadata.
- Resolved AI prompt serialization ambiguity in `ReportSerializer`: explicitly labeled distinct category cardinality (`distinct_category_count: N (cardinality, NOT percentage)`) and provided exact counts and calculated percentage shares.
- Enforced non-dominant category guidelines in `PromptBuilder`, eliminating false "dominance" claims on low-concentration categories.
- Validated end-to-end against live Ollama `gemma3:4b` inference with real-world dataset (`Test_data.xlsx`).

---

# Verification & Test Results

Executed at v14.0.0 (commit `d7f9eb6`).

| Gate | Command | Result |
|---|---|---|
| Test suite | `pytest -q` | ✅ **714 passed, 0 failed, 15 deselected**, 118.73 s |
| Full collection | `pytest --collect-only -m ""` | 729 collected across 118 modules |
| Lint | `flake8 src tests --count` | ✅ 0 |
| Format | `black --check src tests` | ✅ 341 files unchanged |
| Imports | `isort --check src tests` | ✅ clean |
| Types | `mypy src` | ✅ no issues in 210 source files |
| API contract | live `app.openapi()` vs `docs/api/openapi.json` | ✅ 33 paths, 42 schemas, in sync |

- **Deselected tests:** the 15 `integration`-marked tests in
  `tests/ai/test_ollama_connection.py` and `tests/ai/test_ollama_production_path.py` require
  a live Ollama server with `gemma3:4b`. `pyproject.toml` sets
  `addopts = -ra -m "not integration"`; run them with `pytest -m integration`.
- **Source tree:** 210 Python files under `src/`, across 18 packages.
- **Formatter coverage:** `black` and `isort` now check all of `src/` and `tests/`. During the
  sprint they excluded `tests/` and 15 of 17 `src/` packages, so both gates passed while
  checking almost nothing; retiring those exclusions reformatted 231 files.
- **Live E2E verification:** verified on `Test_data.xlsx` with Ollama `gemma3:4b`
  (`ai_job_cd456daeba2f`).
- **AI evidence grounding:** 0 contradicted claims, 0 unsupported claims, 0
  cardinality/frequency conflations.

> **Superseded figures.** Earlier revisions of this section reported *535 / 535 passed*, and
> other documents reported *531* and *529*. None of those was ever reconciled; all are
> superseded by the executed **714**. No coverage measurement exists in this repository, so
> the "100% test coverage" claim that appeared in one CHANGELOG entry is unsupported.

---

# Architectural Impact

- Decoupled synchronous LLM latency from core analytical pipeline execution.
- Established end-to-end data provenance and reproducible cleaning governance.
- Separated domain semantic classification from physical DataFrame dtypes.
- Hardened report export fidelity against empirical data distributions.
- Established strict contract boundary and service abstraction ready for React presentation layer.


---

# Closure Record

Every item raised during the Sprint 14 documentation audit has been resolved.

| # | Item | Resolution |
|---|---|---|
| 1 | `matplotlib` undeclared in `requirements.txt` | ✅ Declared. `ReportingManager` imports the PDF exporter at module level, so it is a hard dependency of the core application and REST API, not only the frontend. |
| 2 | Suite not fully green — 6 live-LLM failures | ✅ Resolved. The live-LLM modules carry the `integration` marker and are deselected by default; the suite is **714 / 714**. The previous guard tested only Ollama *server* reachability, so an environment with a reachable server and no installed model failed rather than skipping. |
| 3 | `docs/api/openapi.json` incorrect and out of sync | ✅ Re-exported from the live application — 33 paths, 42 schemas, `info.version` 14.0.0. The 9 previously missing response properties are present. |
| 4 | Phase 7 definition conflict | ✅ Reconciled to *Semantic Profiling, Visual Analytics & Quality Gates*. Both bodies of work were delivered. |
| 5 | Ollama performance baseline is a single sample | 🟡 Carried as technical debt. `performance/phase2_benchmark_results.md` still records `Successful / Failed: 1 / 2`. |
| 6 | `docs/project/ARCHITECTURE.md` still described the sprint as planned | ✅ Completed. The layered architecture section now documents the delivered design, including where identity, governance, profiling, AI and BI attach to the dependency chain. |
| 7 | Dual `reports_router` registration undecided | ✅ Resolved by removal. Every functional router is mounted once under `API_PREFIX`; the unprefixed aliases were removed as a documented breaking change. |
| 8 | Static-analysis gates not run | ✅ All four executed and passing; the formatter exclusions that made them vacuous were removed. |
| 9 | `src/core/constants.py` still declared `APP_VERSION = "12.0.0"` | ✅ Corrected to `14.0.0`. It feeds `GET /`, `GET /api/version` and the OpenAPI `info.version`. |

## Carried into Sprint 15 — Enterprise Stabilization, Governance Completion & Product/UX Remediation

Recorded as technical debt in PROJECT_STATE.md. None blocks the v14.0.0 release. (This
section originally named Sprint 15 *Refactoring & Architectural Evolution*; that name is
superseded by ROADMAP.md.) Sprint 15 additionally covers the governance end-to-end workflow,
Dashboard product value and Admin user-lifecycle gaps; the single-provider `LLMFactory` is
Sprint 16 scope.

- `.flake8` and `[tool.mypy]` still suppress several error classes.
- The OpenAPI contract test compares only the spec version and the path *count*.
- The Ollama performance baseline needs re-running.
- CI triggers only on `main`, so branch work is validated locally until merge.
- `docker-compose.yml` still pins `AI_CONTEXT_WINDOW: 4096` and `AI_TIMEOUT: 120` against
  the current defaults of `8192` and `600`; `src/core/config.py` defaults `POSTGRES_PORT`
  to `5433` where `.env.example` uses `5432`.
