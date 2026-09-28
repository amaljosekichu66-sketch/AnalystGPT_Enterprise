# ADR-025 — Asynchronous AI Generation and Job Lifecycle

**Status:** ✅ **Accepted** — implemented in Sprint 14, released in v14.0.0

> Implemented in `src/ai/job_executor.py`, `src/ai/models.py`, `src/ai/ai_job_service.py`, `src/database/repositories/ai_job_repository.py`, `src/database/repositories/ai_report_repository.py`, and the `/api/ai/jobs/*` routes.
>
> This ADR was authored as *Proposed (Planned for Sprint 14)*. Sprint 14 is implemented
> and the decision it records is in force; the status is promoted accordingly. The
> decision text below is unchanged.
>
> **Re-baseline note (ROADMAP.md, Sprints 15–17).** Sprint 15 — Enterprise Stabilization,
> Governance Completion & Product/UX Remediation → Sprint 16 — AI Provider Abstraction &
> Complete React Readiness → Sprint 17 — React Migration. The "React Migration Readiness"
> in the Sprint line below refers to the Sprint 14 *initial* foundation; the definitive
> readiness gate is Sprint 16.
>
> *Impact on later sprints.* Implemented and tested; Sprint 15 Phase 1/7 must verify the job
> lifecycle end-to-end through the real API/frontend path (async AI job problems are in Sprint 15
> Phase 5 scope). Sprint 16 provider adapters (Ollama, Google Cloud / Gemini) run *inside*
> this lifecycle: provider timeouts, retries and provider-specific exceptions must map onto the
> existing `PENDING → GENERATING → READY / FAILED` states without changing them. The job states
> are the contract the Sprint 17 React async-job UX consumes.

**Date:** 2026-08-15

**Sprint:** Sprint 14 — UX Stabilization, Performance, Data Governance & React Migration Readiness

**Decision Makers:** Lead Software Architect, Engineering Program Manager

---

# Context

In Sprint 11, the AI Insight Engine was introduced to enrich reporting outputs with intelligent narratives, executive summaries, explanations, and business recommendations using local LLM inference (Ollama with Qwen/Gemma models).

In the initial implementation, AI generation was executed synchronously as the final stage of `Application.run()`. While architecturally clean and non-blocking on failure, local LLM inference takes 45–70 seconds. Consequently, any pipeline run or dashboard view requiring pipeline execution blocks the HTTP request and the frontend interface for over a minute before rendering even basic analytical charts and data summaries.

Users require immediate access to deterministic analytical outputs (cleaning metrics, quality reports, numerical distributions, KPIs), with AI insights populated when available.

---

# Problem Statement

Synchronous AI generation couples fast, deterministic data pipeline execution (~0.1–1.0s) with high-latency, probabilistic LLM inference (45–70s). This results in:
1. Poor perceived frontend performance and browser/client timeout risks.
2. Inability to view deterministic reports and charts while Ollama is generating.
3. Unnecessary re-generation of LLM insights upon dashboard tab switches.
4. Concurrency bottlenecks when multiple users execute pipelines simultaneously.

---

# Decision

1. **Decouple Pipeline Execution from AI Generation**:
   The core pipeline (`Upload → Cleaning → Quality → Analytics → Reporting → Persistence`) shall complete deterministically and return immediate results to the client.

2. **Replaceable Background-Job Abstraction**:
   AI generation shall be dispatched asynchronously via a technology-neutral background job abstraction (`IBackgroundJobExecutor` / `AIJobManager`). This abstraction ensures the domain remains independent of specific queue implementations (threading, AsyncIO, Celery, or Redis).

3. **Database-Backed Job State Machine**:
   AI job state shall be persisted independently of frontend session state with the following lifecycle:
   ```text
   PENDING ──► GENERATING ──► READY
                   │
                   └──► FAILED
   ```

4. **Job Entity & Associations**:
   AI jobs shall be uniquely keyed by `job_id` and associated with `pipeline_run_id`, `user_id`, and `report_id`.

5. **Failure Isolation**:
   AI generation failure (timeout, model crash, invalid output) must never invalidate an otherwise successful analytics pipeline run. Pipeline success and AI generation success remain independent outcomes.

6. **Idempotency & Polling**:
   Duplicate AI generation requests for completed runs shall be prevented. Frontend clients will poll `GET /api/ai/jobs/{job_id}` to retrieve status and results when ready.

---

# Architectural Flow

```text
HTTP Request / UI
       │
       ▼
Application.run() ────────────────────────► Immediate PipelineResult
       │                                     (Dashboard & Reports Ready)
       ▼
Dispatch Background AI Job
       │
       ▼
State: PENDING
       │
       ▼
State: GENERATING (Ollama Inference)
     /            ▼          ▼
State: READY  State: FAILED (Isolated, Retryable)
    │
    ▼
Persisted AI Report (Available via GET /api/ai/jobs/{id})
```

---

# Consequences

### Positive
- **Instantaneous UX**: Deterministic charts and reports render in under 1 second.
- **Resilience**: LLM timeouts or crashes do not impact core analytics data availability.
- **Resource Control**: Background execution allows throttling and job queuing under heavy concurrent load.
- **Multi-Tenant Isolation**: AI jobs carry `user_id` security context and enforce ownership checks upon result retrieval.

### Negative / Trade-offs
- Requires client-side polling or status checking for the AI Insights view.
- Requires job tracking database table and lifecycle state management.

---

# Related ADRs

- ADR-007 — Application Layer Orchestration
- ADR-011 — REST API Architecture
- ADR-020 — AI Insight Engine Architecture
- ADR-024 — Enterprise Identity and Multi-User Architecture
- ADR-021 — LLM Provider Abstraction
