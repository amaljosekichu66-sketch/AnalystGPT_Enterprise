# ADR-020 — AI Insight Engine Architecture

**Status:** ✅ **Accepted** — delivered in Sprint 11 (v11.0.0)

> The design this ADR records has been in production since v11.0.0 (`src/ai/`,
> `src/llm/`) and was extended by ADR-025 and ADR-027 in Sprint 14. The status line
> read *Proposed*, which no longer described reality; the decision text is unchanged.

> **Re-baseline note (2026-09-28).** References below to a "future React frontend" now map
> to **Sprint 17**.
> Sequencing is defined in ROADMAP.md: Sprint 15 — Enterprise Stabilization, Governance
> Completion & Product/UX Remediation (no React work) → Sprint 16 — AI Provider Abstraction &
> Complete React Readiness (final readiness audit; React architecture defined, not built) →
> **Sprint 17 — React Migration & Modern Presentation Layer** (React + TypeScript implemented).
> The decision text is unchanged.

**Date:** 2026-07-25

**Sprint:** Sprint 11 – AI Insights

**Decision Makers:** Project Architecture Board

---

# Context

Following the successful completion of Sprint 10, AnalystGPT Enterprise provides a complete end-to-end analytics workflow consisting of:

- Dataset Upload
- Data Cleaning
- Data Quality Assessment
- Statistical Analytics
- Reporting
- REST API
- Power BI Integration
- Enterprise Streamlit Frontend

Although users can access comprehensive analytics, they are still required to manually interpret the generated results.

Modern analytics platforms increasingly provide AI-assisted interpretation that explains results, identifies anomalies, and recommends next steps. Sprint 11 introduces an AI Insight Engine to automate these tasks while preserving the existing architecture.

The AI Insight Engine is intended to augment the platform with intelligent recommendations without altering the existing analytics pipeline.

---

# Problem Statement

Current analytics outputs provide numerical and statistical results but do not explain:

- What the results mean.
- Which findings are important.
- What potential issues exist.
- What actions should be taken.
- How business users should interpret the data.

Embedding AI logic within existing analytics modules would:

- Violate the Single Responsibility Principle.
- Increase coupling.
- Reduce maintainability.
- Make future AI model replacement difficult.

A dedicated AI architecture is therefore required.

---

# Decision

A dedicated AI Insight Engine shall be introduced as a new layer within the Application Layer.

The AI Insight Engine will consume outputs from existing modules but will not replace or modify them.

```
Analytics

↓

Reporting

↓

AI Insight Engine

↓

Frontend

↓

User
```

The AI Insight Engine shall remain independent from:

- Data Cleaning
- Quality Assessment
- Statistical Analysis
- Database Persistence

Its sole responsibility is generating human-readable insights from structured analytics results.

---

# Objectives

The AI Insight Engine will provide:

- Executive summaries
- Natural language explanations
- Business recommendations
- Trend identification
- Data quality observations
- Risk detection
- Key findings
- Actionable next steps

The engine will enhance decision-making without modifying the underlying analytical computations.

---

# Planned Architecture

```
                Analytics Results

                        │

                        ▼

             AI Insight Engine

        ┌────────┼────────┬────────┐

        ▼        ▼        ▼

 Summary  Recommendations  Risk Detection

        └────────┼────────┘

                 ▼

       Insight Orchestrator

                 ▼

      Frontend / REST API
```

---

# Core Components

## Insight Orchestrator

Coordinates AI insight generation.

Responsibilities:

- Receive analytics outputs.
- Invoke AI components.
- Aggregate responses.
- Return structured insights.

---

## Summary Generator

Produces concise executive summaries.

Examples:

- Dataset overview
- Key statistics
- Major findings

---

## Recommendation Engine

Generates business recommendations.

Examples:

- Suggested next analyses
- Data quality improvements
- Operational recommendations

---

## Risk Detector

Identifies:

- Outliers
- Data quality risks
- Missing information
- Statistical anomalies

---

## Insight Formatter

Converts AI outputs into presentation-friendly structures for:

- Dashboard
- Reports
- REST API

---

# Design Principles

## Single Responsibility Principle

AI components generate insights only.

They do not perform analytics.

---

## Separation of Concerns

Analytics modules remain deterministic.

AI modules provide interpretation.

---

## Dependency Direction

```
Analytics

↓

Reporting

↓

AI Engine

↓

Frontend
```

The AI layer depends on analytics outputs, not the reverse.

---

## Extensibility

Future AI providers (OpenAI, local LLMs, or other models) can be introduced without changing the frontend or analytics modules.

---

# Benefits

The architecture provides:

- Explainable analytics
- Business-focused insights
- Reusable AI components
- Scalable design
- Model independence
- Enterprise-ready intelligence layer

---

# Trade-offs

## Advantages

- Clear architectural boundaries.
- Easy model replacement.
- High maintainability.
- Improved user experience.
- Supports future AI enhancements.

---

## Disadvantages

- Additional application layer.
- Increased implementation complexity.
- Dependency on AI services for advanced functionality.

These trade-offs are acceptable given the significant increase in analytical value.

---

# Alternatives Considered

## Option 1 — Embed AI into Analytics Module

**Rejected**

Reason:

- Violates SRP.
- Couples statistical analysis with AI interpretation.

---

## Option 2 — AI in Frontend

**Rejected**

Reason:

- Business logic belongs outside the presentation layer.
- Difficult to test and maintain.

---

## Option 3 — AI as Independent Application Layer

**Accepted**

Reason:

- Preserves Clean Architecture.
- Supports future AI model replacement.
- Maintains modularity.

---

# Future Roadmap

The AI Insight Engine is expected to support:

- Executive narratives
- Predictive insights
- Automated anomaly explanations
- Conversational analytics
- Explainable AI (XAI)
- Multi-model support
- Interactive insight exploration

These capabilities will be implemented incrementally in future sprints.

---

# Consequences

Following this decision:

- Existing analytics modules remain unchanged.
- AI functionality is introduced without architectural disruption.
- The frontend consumes AI-generated insights through established service interfaces.
- Future React components can display AI outputs without backend redesign.

---

# Related ADRs

- ADR-007 — Application Layer Orchestration
- ADR-011 — REST API Architecture
- ADR-014 — Dashboard Service Pattern
- ADR-015 — Streamlit Frontend Architecture
- ADR-017 — Frontend Service Layer Pattern
- ADR-018 — Report Export Architecture
- ADR-019 — Enterprise UI Navigation Pattern

---

# References

- Robert C. Martin — *Clean Architecture*
- SOLID Design Principles
- Explainable AI (XAI) Principles
- Enterprise Analytics Platform Design Patterns

---

# Decision Summary

AnalystGPT Enterprise shall introduce a dedicated AI Insight Engine as a separate application-layer component responsible for transforming structured analytics outputs into human-readable insights, recommendations, and executive summaries.

The AI Insight Engine will remain independent from analytical computations, preserving Clean Architecture principles while enabling intelligent, explainable, and extensible analytics capabilities in Sprint 11 and beyond.