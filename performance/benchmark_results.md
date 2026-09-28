# Performance Benchmark Results

> **Purpose**
>
> This document records performance validation results for AnalystGPT Enterprise.
> It tracks execution benchmarks across representative datasets and validates
> scalability, stability, and architectural performance for each release.

---

# Last Updated

**Version:** v9.0.0

**Date:** 23 July 2026

---

# Benchmark Environment

| Item | Value |
|------|-------|
| Application | AnalystGPT Enterprise |
| Version | v9.0.0 |
| Python | 3.11.9 |
| Architecture | Enterprise Layered Architecture + REST API + Business Intelligence Layer |
| Database | SQLite / PostgreSQL |
| REST Framework | FastAPI |
| API Specification | OpenAPI 3.1 |
| Business Intelligence | Power BI Integration |
| Report Export | Plain Text |
| Operating System | Windows 11 |
| Test Type | End-to-End Pipeline |

---

# Benchmark Methodology

Each benchmark executes the complete analytics platform:

```text
Upload
   ↓
Cleaning
   ↓
Quality
   ↓
Analytics
   ↓
Reporting
   ↓
Persistence
   ↓
Business Intelligence
```

The reported execution time includes:

- Dataset loading
- Data cleaning
- Data quality assessment
- Statistical analytics
- Report generation
- Report export
- SQLite/PostgreSQL persistence
- Dashboard generation
- REST API serialization
- Pipeline completion

---

# Benchmark Results

| Dataset | Rows | Execution Mode | Result |
|---------|-----:|---------------|--------|
| Sample Dataset | 500 | CLI | ✅ Passed |
| Sample Dataset | 500 | REST API | ✅ Passed |
| Large Dataset | ~100,000 | CLI | ✅ Passed |
| Large Dataset | ~100,000 | REST API | ✅ Passed |
| Stress Dataset | ~1,000,000 | CLI | ✅ Passed |
| Stress Dataset | ~1,000,000 | REST API | ✅ Passed |
| Power BI Dashboard | ~1,000,000 | REST API | ✅ Passed |

---

# REST API Validation

Validated endpoints:

- GET /
- GET /api/health
- GET /api/version
- POST /api/pipeline
- GET /powerbi/dashboard
- GET /powerbi/summary
- GET /powerbi/statistics
- GET /powerbi/correlation
- GET /powerbi/distribution
- GET /powerbi/categorical
- GET /powerbi/report
- GET /powerbi/pipeline

Status:

✅ All endpoints operational

---

# Database Validation

Successfully validated:

## SQLite

- Database initialization
- Schema creation
- Repository operations
- Pipeline persistence

Status:

✅ Passed

---

## PostgreSQL

- Connection
- Schema initialization
- Repository operations
- Pipeline persistence

Status:

✅ Passed

---

# Power BI Validation

Successfully validated:

- Dashboard generation
- Executive summary
- Descriptive statistics
- Correlation analysis
- Distribution analysis
- Categorical analysis
- Complete report generation

Status:

✅ Passed

---

# Automated Testing

| Validation | Status |
|------------|--------|
| Automated Tests | ✅ 98 / 98 Passed |
| Integration Tests | ✅ Passed |
| Power BI Tests | ✅ Passed |
| REST API Tests | ✅ Passed |

---

# Performance Observations

Sprint 9 successfully validated:

- Stable memory utilization
- Stable execution times
- Enterprise dashboard generation
- REST endpoint execution
- SQLite persistence
- PostgreSQL persistence
- Large dataset processing
- Stress dataset processing
- One million row execution
- Business Intelligence layer integration

No architectural regressions were observed.

---

# Engineering Conclusions

Sprint 9 demonstrates that the platform now supports:

- Enterprise analytics
- Multi-database persistence
- REST API services
- Business Intelligence integration
- Dashboard-ready APIs
- Large-scale analytics processing

The addition of the Business Intelligence Layer introduced no measurable
architectural regressions while preserving clean separation of concerns.

---

# Benchmark Status

| Validation | Status |
|------------|--------|
| Sample Dataset | ✅ Passed |
| Large Dataset | ✅ Passed |
| Stress Dataset | ✅ Passed |
| SQLite Validation | ✅ Passed |
| PostgreSQL Validation | ✅ Passed |
| REST API Validation | ✅ Passed |
| Power BI Validation | ✅ Passed |
| Dashboard Generation | ✅ Passed |
| End-to-End Pipeline | ✅ Passed |

---

# Future Benchmarks

### Sprint 14 Benchmark Scope

Planned at the start of Sprint 14; per-item measurement status is recorded below.

- End-to-end API response latency (p50, p95, p99)
- Dashboard load time and initial scroll rendering
- Asynchronous AI job lifecycle execution & status polling latency
- Ollama inference duration across report sizes
- Multi-user concurrent execution & cache isolation overhead
- Report export and streaming latency

*Status on the Sprint 14 working tree (v14.0.0 prepared):* **Partially measured.**

> Corrected during the Sprint 14 documentation audit against
> `performance/phase2_benchmark_results.md` (committed in `00e33af`):
>
> | Planned benchmark | Status |
> |---|---|
> | End-to-end API response latency (p50, p95, p99) | **Measured** |
> | Dashboard load time and initial scroll rendering | **Not measured** |
> | Asynchronous AI job lifecycle execution & status polling latency | **Measured** (AI job creation/dispatch and job-status API latency) |
> | Ollama inference duration across report sizes | **Partially measured** — one model (`gemma3:4b`) and one dataset only, with **1 successful run of 3**; not varied across report sizes |
> | Multi-user concurrent execution & cache isolation overhead | **Not measured** |
> | Report export and streaming latency | **Not measured** |
>
> The measured items are a **baseline**, not a completed regression validation: the artifact
> contains no comparison against any prior baseline.

---

**Current version:** **v14.0.0** (prepared — not yet tagged or merged to `main`; last released v13.0.0)

**Baseline measured at:** **v13.0.0.** The deterministic pipeline figures above have not been
re-measured since, so they are labelled with the version they were taken at rather than
restamped to v14.0.0. **No regression comparison against this baseline has been run for
Sprint 14**; absence of a measured regression is not evidence of none.

**Status:** 🟡 Baseline preserved. Sprint 14 benchmarks **partially measured** (see the table
above); dashboard load, governance overhead, concurrency and export latency remain
**unmeasured**, and the Ollama figure rests on a single successful run of three. Re-running
the baseline is carried as technical debt into Sprint 15 (Phase 7 — Regression & Quality) —
see PROJECT_STATE.md, section *Known Technical Debt*.