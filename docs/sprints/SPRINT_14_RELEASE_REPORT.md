# Sprint 14 Pre-Sprint Baseline & Planning Report

**Project:** AnalystGPT Enterprise

**Sprint:** Sprint 14 — UX Stabilization, Performance, Data Governance & React Migration Readiness

**Target Version:** v14.0.0

**Baseline Date:** August 2026

**Status:** 📋 PRE-SPRINT BASELINE — SPRINT 14 NOT YET IMPLEMENTED

---

# Executive Summary

This report establishes the approved scope, architectural baseline, and quality targets for **Sprint 14**.

**IMPORTANT**: No Sprint 14 features have been implemented yet. The codebase currently stands at **v13.0.0** with **329 passed automated tests**. Sprint 14 implementation will begin following this documentation baseline freeze and environment restart.

---

# Baseline Architecture (v13.0.0)

| Subsystem | Current State | Target in Sprint 14 |
|---|---|---|
| **Presentation (Streamlit)** | Functional MVP UI; scroll reset issue; mixed AI tab | Scroll reset fix; redesigned information hierarchy; dedicated AI Insights page; public About page; role-aware Admin UI |
| **AI Insight Generation** | Synchronous inside `Application.run()` (45–70s latency) | Decoupled asynchronous background job state machine (`PENDING → GENERATING → READY / FAILED`); immediate pipeline returns |
| **Data Cleaning & Lineage** | In-place cleaning during ingestion; no provenance | Versioned immutable raw dataset + separate cleaned analytical dataset; configurable missing-value policies; before/after quality metrics |
| **AI Prompt Context** | Cleaned analytical report context | Privacy-safe aggregated distributions + source quality metadata + cleaning transformation provenance |
| **Report Exports** | In-memory text export; download/PDF defects | Repaired report download and PDF export; authenticated ownership verification; export idempotency |
| **API Contract & React Readiness** | REST API with FastAPI + OpenAPI 3.1 | OpenAPI 3.1 contract freeze; typed response models; frontend-independent service interfaces (`AuthService`, `DashboardService`, etc.) |
| **Automated Tests** | 329 passed tests | 360+ tests targeting async AI, data cleaning policies, lineage, and export reliability |

---

# Approved Phase Delivery Plan

## Phase 1 — Frontend UX Stabilization
- Fix initial scroll position on Dashboard and Reports (open at top).
- Redesign Dashboard metrics hierarchy.
- Relocate AI Insights into a dedicated navigation item.
- Maintain public access to About page.
- Improve loading, empty, and transition states.

## Phase 2 — Asynchronous AI Generation & Job Lifecycle
- Decouple deterministic analytical pipeline from LLM inference.
- Database-backed AI job state machine: `PENDING → GENERATING → READY / FAILED`.
- Associate AI jobs with `pipeline_run_id`, `user_id`, and `report_id`.
- Prevent duplicate generation (idempotency) and establish retry policies.
- Ensure failure isolation: AI failure never fails or corrupts the analytics pipeline.

## Phase 3 — Data Cleaning Governance & Lineage
- Preserve immutable raw uploaded datasets with SHA-256 checksums.
- Store separate cleaned analytical datasets.
- Implement configurable missing-value policies (preserve NULLs, drop rows, drop columns, impute).
- Build cleaning preview and approval workflow.
- Record cleaning provenance and before/after quality metrics.

## Phase 4 — AI Analytical Context & Data Integrity
- Build privacy-safe aggregated prompts (no raw unaggregated PII).
- Pass data cleaning metadata to LLM context to prevent hallucinated completeness.
- Distinguish source-data observations from post-cleaning analytical findings.

## Phase 5 — Reporting & Export Reliability
- Repair report download mechanism and PDF export.
- Verify export idempotency and file integrity.
- Enforce authenticated ownership on all export endpoints.

## Phase 6 — React Migration Readiness
- Freeze OpenAPI 3.1 contracts with typed models.
- Abstract presentation logic into frontend-independent service interfaces.
- Document Streamlit to React component and route mapping.

## Phase 7 — Regression, Quality & Performance Validation
- Execute full automated test suite with zero regressions.
- Validate multi-user concurrent access and AI failure isolation.
- Pass Flake8, Black, isort, and Mypy quality gates.

---

# Definition of Done Criteria for Sprint 14

- [ ] All 7 Sprint 14 phases implemented in sequence.
- [ ] Automated test suite expanded with zero failures or regressions.
- [ ] Asynchronous AI job state machine operational and tested.
- [ ] Data cleaning governance and lineage tracking verified.
- [ ] Report downloads and PDF exports verified.
- [ ] OpenAPI 3.1 contract validated for React migration readiness.
- [ ] Documentation synchronized across all canonical documents.
