# AnalystGPT Enterprise — Performance Report

**Version:** v13.0.0

**Date:** August 2026

**Status:** ✅ Baseline Performance Verified

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

# Sprint 14 Planned Performance Targets

The following performance benchmarks are scheduled for measurement during Sprint 14:

1. **Decoupled AI Latency**:
   - Pipeline API response time before AI generation: Target < 1.0s.
   - Background AI job execution (Ollama): Target baseline characterized.
2. **Dashboard Render Latency**:
   - Initial page render and top-scroll repositioning.
3. **Data Cleaning Governance Overhead**:
   - SHA-256 artifact hashing and raw dataset persistence overhead.
4. **Concurrent Multi-User Throughput**:
   - Multi-tenant query isolation under concurrent pipeline executions.

*Measurement Status:* **Not yet measured — Sprint 14 planned benchmark.**
