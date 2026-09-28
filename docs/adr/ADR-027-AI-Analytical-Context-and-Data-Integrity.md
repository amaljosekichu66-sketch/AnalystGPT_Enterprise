# ADR-027 — AI Analytical Context and Data Integrity

**Status:** ✅ **Accepted** — implemented in Sprint 14, released in v14.0.0

> Implemented in `src/ai/context.py`, `src/ai/context_builder.py`, and the serialization changes in `src/llm/report_serializer.py` and `src/llm/prompt_builder.py`.
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
> *Impact on later sprints.* Sprint 16 adds a hosted provider (Google Cloud / Gemini) alongside
> local Ollama. The privacy-safe aggregated context defined here becomes more important, not less:
> every provider adapter must receive the same `AIDataContext`-derived prompt, and no provider may
> be sent raw dataset rows. Provider selection must not change context construction.

**Date:** 2026-08-15

**Sprint:** Sprint 14 — UX Stabilization, Performance, Data Governance & React Migration Readiness

**Decision Makers:** Lead Software Architect, Engineering Program Manager

---

# Context

The AI Insight Engine (Sprint 11) converts analytical reports into prompts for local LLMs (Ollama) to produce executive summaries and recommendations. When data cleaning removes rows with missing values or invalid data, the downstream analytical report only contains statistics for the remaining cleaned records.

Without explicit provenance metadata in the LLM prompt:
1. The LLM may hallucinate that the original dataset had 100% completeness because it only observed post-cleaning statistics.
2. The LLM is unaware of data attrition (e.g. 30% of records dropped during cleaning), leading to overconfident business conclusions.
3. Transmitting raw dataset tables to LLMs risks leaking Personally Identifiable Information (PII) and exhausts token context windows.

---

# Problem Statement

LLMs require accurate context regarding both the source dataset quality and the post-cleaning analytical results to generate faithful insights without hallucination or privacy violations.

---

# Decision

1. **Privacy-Safe Aggregated Context**:
   The AI prompt builder shall supply structured source-data quality metadata and aggregated analytical distributions rather than unaggregated raw records.

2. **Explicit Data Cleaning & Quality Attribution**:
   Prompts must provide explicit context on:
   - Original source row and column counts.
   - Missing value counts and duplicate counts detected prior to cleaning.
   - Cleaning transformation actions applied (e.g. "450 rows removed due to missing values").
   - Final analytical dataset row and column counts.

3. **Contextual Narrative Labeling**:
   Generated AI insights must explicitly distinguish between source observations and cleaned findings (e.g., "Based on 1,550 analyzed transactions following the removal of 200 duplicate entries...").

4. **Analytical Caveats**:
   When cleaning materially alters the dataset (> 5% data loss), the Prompt Builder instructs the LLM to emit appropriate analytical caveats regarding sample bias.

---

# Context Pipeline Flow

```text
Source Data Metadata (Original: 2,000 rows, 200 missing)
                 │
                 ├──► Data Cleaning Provenance (200 rows dropped)
                 │
                 └──► Analytical Results (Cleaned: 1,800 rows analyzed)
                             │
                             ▼
                    AI Prompt Builder
          (Structured, Privacy-Safe Context)
                             │
                             ▼
                    LLM Inference (Ollama)
                             │
                             ▼
        Faithful Narrative with Provenance Caveats
```

---

# Consequences

### Positive
- **Hallucination Prevention**: LLM cannot falsely claim data is complete when missingness was cleaned.
- **Privacy & Security**: Raw PII is not exposed to the LLM context window.
- **Analytical Integrity**: Executive summaries reflect accurate business reality and data confidence levels.

### Negative / Trade-offs
- Requires prompt builder enhancements and schema additions to pass provenance metadata to the AI subsystem.

---

# Related ADRs

- ADR-020 — AI Insight Engine Architecture
- ADR-021 — LLM Provider Abstraction
- ADR-025 — Asynchronous AI Generation and Job Lifecycle
- ADR-026 — Data Cleaning Governance and Lineage
