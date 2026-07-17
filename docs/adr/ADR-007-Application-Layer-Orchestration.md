# ADR-007 — Application Layer & Pipeline Orchestration

- **Status:** Accepted
- **Date:** 17 July 2026
- **Decision Makers:** AnalystGPT Enterprise Project

---

# Context

By the completion of Sprint 5, AnalystGPT Enterprise contained five
fully functional business modules:

- Upload
- Cleaning
- Quality
- Analytics
- Reporting

Although the pipeline was functionally complete, orchestration of the
entire workflow remained inside `main.py`.

This created several architectural concerns:

- Application entry point contained orchestration logic.
- Pipeline execution could not easily be reused.
- Future interfaces (CLI, GUI, REST API, Streamlit) would duplicate
  orchestration.
- No single application contract represented pipeline execution.
- Future database integration would become increasingly difficult.

A dedicated application orchestration layer was required.

---

# Decision

Introduce a dedicated **Application Layer**.

The Application Layer becomes the only component responsible for
coordinating business modules.

Pipeline execution is centralized inside:

```text
Application.run()
```

The application entry point (`main.py`) becomes a thin launcher that
delegates execution to the Application Layer.

Business modules remain independent and unaware of one another.

---

# Architectural Changes

Sprint 5.5 introduced:

- `src/application/`
- `Application`
- `Application.run()`
- `PipelineResult`

Pipeline execution now follows:

```text
main.py
    │
    ▼
Application.run()
    │
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
PipelineResult
```

---

# Consequences

## Positive

- Clear separation between application orchestration and business logic.
- Thin application entry point.
- Stable orchestration boundary.
- Strongly typed application result.
- Improved dependency direction.
- Easier testing.
- Easier future UI integration.
- Easier database integration.
- Easier API integration.
- Improved maintainability.

## Trade-offs

- Introduced one additional architectural layer.
- Required refactoring existing orchestration.
- Required updates to tests and documentation.

These costs were accepted in exchange for improved long-term
maintainability.

---

# Alternatives Considered

## Continue using `main.py`

Rejected.

Reasons:

- Mixed application concerns with orchestration.
- Reduced scalability.
- Difficult to reuse pipeline execution.
- Increased future maintenance cost.

## Business modules orchestrating one another

Rejected.

Reasons:

- Violates separation of concerns.
- Increases coupling.
- Makes dependency direction unclear.
- Complicates testing.

---

# Validation

Architecture was validated through:

- 79 / 79 automated tests passed
- Integration testing
- End-to-end pipeline execution
- Large dataset validation
- Stress dataset validation

No functional regressions were introduced.

---

# Related Documents

- ARCHITECTURE.md
- PROJECT_STATE.md
- ROADMAP.md
- SPRINT_5_RELEASE_REPORT.md

---

# Status

**Accepted**

This ADR establishes the Application Layer as the permanent
orchestration boundary for AnalystGPT Enterprise beginning with
Version **v5.5.0**.