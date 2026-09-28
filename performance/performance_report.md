# AnalystGPT Enterprise — Performance Report

**Current version:** **v14.0.0** (released 2026-09-28; tag `v14.0.0`)

**Baseline measured at:** v13.0.0 (carried forward; not re-measured)

**Date:** August 2026

**Status:** 🟡 Baseline verified at v13.0.0; Sprint 14 targets partially measured

---

# Executive Summary

This report documents performance baseline benchmarks for AnalystGPT Enterprise across data pipeline execution, database persistence, REST API throughput, and multi-user security overhead.

---

# Baseline Benchmarks (v13.0.0)

| Benchmark Category | Dataset / Scenario | Metric | Status |
|---|---|---|---|
| Pipeline Ingestion & Clean | Small Dataset (~100 rows) | < 0.05s | ✅ Passed |
| Pipeline Ingestion & Clean | Large Dataset (~100K rows) | ~1.2s | ✅ Passed |
| Pipeline Stress Execution | Stress Dataset (~1M rows) | ~18.5s | ✅ Passed |
| Password Hasher (PBKDF2) | 600,000 iterations (1 verification) | ~0.18s | ✅ Passed |
| Token Service (HMAC-SHA256) | Token Issuance & Verification | < 0.001s | ✅ Passed |
| Scoped Database Query | User-scoped dataset retrieval | < 0.005s | ✅ Passed |

---

# Sprint 14 Performance Targets

These were the targets set for Sprint 14. Sprint 14 is released (v14.0.0); per-item measurement status
is recorded beneath the list.

1. **Decoupled AI Latency**:
   - Pipeline API response time before AI generation: Target < 1.0s.
   - Background AI job execution (Ollama): Target baseline characterized.
2. **Dashboard Render Latency**:
   - Initial page render and top-scroll repositioning.
3. **Data Cleaning Governance Overhead**:
   - SHA-256 artifact hashing and raw dataset persistence overhead.
4. **Concurrent Multi-User Throughput**:
   - Multi-tenant query isolation under concurrent pipeline executions.

*Measurement status at v14.0.0:* **Partially measured.** Re-measurement is Sprint 15 Phase 7 scope.

> Corrected during the Sprint 14 documentation audit. A Sprint 14 Phase 2 benchmark artifact
> exists in this directory (`performance/phase2_benchmark_results.md`, committed in `00e33af`),
> so "not yet measured" was inaccurate for the whole list. Per-item status, verified against
> that artifact:
>
> | # | Target | Status |
> |---|---|---|
> | 1 | Decoupled AI latency | **Measured** — pipeline REST latency (min/p50/p95/p99/max) and an Ollama generation baseline are recorded. ⚠️ The Ollama figure rests on **1 successful run of 3**, so it is a weak baseline, not a validated result. |
> | 2 | Dashboard render latency | **Not measured** — no dashboard or scroll timing appears in the artifact. |
> | 3 | Data cleaning governance overhead (SHA-256) | **Not measured** — no hashing or artifact-persistence timing appears. |
> | 4 | Concurrent multi-user throughput | **Not measured** — no concurrency or multi-tenant timing appears. |
>
> No measurement has been invented here. Items 2-4 remain genuinely unmeasured and are
> outstanding validation work.
