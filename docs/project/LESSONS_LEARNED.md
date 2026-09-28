# Lessons Learned

> Permanent engineering concepts learned throughout AnalystGPT Enterprise.
>
> This document serves as a continuously growing engineering knowledge base rather than a project journal.

---

# Last Updated

**Date:** August 2026 (Sprint 14 content)

**Current version:** **v14.0.0** (prepared — not yet tagged or merged to `main`; last released v13.0.0)

**Current sprint:** Sprint 14 — Stabilization / Production Hardening (implemented and validated locally; release pending)

> The Sprint 14 section near the end of this document was written *before* the sprint began
> and records what was anticipated. The lessons drawn from actually executing Sprint 14 are
> recorded in PROJECT_JOURNAL.md under the Sprint 14 completion milestone.

---

# Engineering Philosophy

- ✅ Business before Technology
- ✅ Architecture before Code
- ✅ Think **WHY** before **HOW**
- ✅ Design before Implementation
- ✅ Build for Humans, not only Computers
- ✅ Documentation is Part of the Product
- ✅ Testing is Part of Development

---

# Software Engineering Workflow

```text
Business Problem
        ↓
Business Value
        ↓
Architecture
        ↓
Design
        ↓
Implementation
        ↓
Unit Testing
        ↓
Integration Testing
        ↓
Documentation
        ↓
Release
```

---

# Architecture Rules

- ✅ `main.py` only orchestrates
- ✅ One Module = One Responsibility
- ✅ Shared infrastructure belongs in `core`
- ✅ Business modules depend on `core`
- ✅ `core` never depends on business modules
- ✅ Managers coordinate business workflows
- ✅ Business modules communicate through stable contracts
- ✅ Business modules never access the database directly
- ✅ Persistence belongs in the Infrastructure Layer
- ✅ Infrastructure communicates through stable abstractions
- ✅ Business modules remain independent of database implementations
- ✅ REST APIs belong to the Presentation Layer
- ✅ Business logic must never exist inside API routes
- ✅ HTTP concerns must remain isolated from business modules
- ✅ Application Layer owns all orchestration
- ✅ API Layers should remain stateless
- ✅ Dependency Injection improves modularity and testability
- ✅ API contracts should remain stable across releases

---

# Stable Contracts

## Upload

### Input

- CSV
- Excel
- JSON
- Database *(Planned)*
- REST API *(Planned)*

### Output

- Pandas DataFrame

### Rule

Downstream modules should never know where the data originated.

---

## REST API

### Input

- PipelineRequest

### Output

- PipelineResponse

### Rule

Clients should depend only on stable API contracts rather than internal implementation.

---

# Core Package

## Purpose

Shared infrastructure used throughout the application.

### Components

- constants.py
- config.py
- logger.py
- exceptions.py

---

# Configuration Rules

## constants.py

Stores application identity and immutable values.

Examples:

- Application Name
- Version
- Encoding
- API Prefix
- API Documentation URLs

---

## config.py

Stores configurable runtime behavior.

Examples:

- Debug Mode
- Logging Level
- Upload Limits
- Database Engine Selection (SQLite / PostgreSQL)
- Connection Parameters
- API Settings

---

# Logging

Logger

↓

Creates log messages

Handler

↓

Determines where log messages are written

Rule

Business modules must use the shared logger.

Never create independent logging systems.

---

# Exceptions

Prefer:

Specific exceptions

Avoid:

Generic `Exception`

Examples:

- UnsupportedFileTypeError
- EmptyFileError
- FileTooLargeError

---

# Dependency Direction

Correct

```text
REST API
    ↓
Application
    ↓
Business Modules
    ↓
Persistence
    ↓
Core
```

Incorrect

```text
REST API
    ↓
Business Modules
```

```text
Core
    ↓
Business Modules
```

Reason

Prevents circular dependencies and preserves modular architecture.

Business logic and HTTP concerns must remain separated.

---

# Engineering Principles

- Separation of Concerns
- Single Responsibility Principle (SRP)
- Open / Closed Principle (OCP)
- Low Coupling
- High Cohesion
- Modular Design
- Scalability
- Maintainability
- Extensibility
- Reusability
- Testability
- API-first Architecture
- Service-oriented Architecture
- Dependency Injection
- Request Validation
- Response Validation
- Backward Compatibility
- Contract-driven Development

---

# Design Checklist

Before writing code ask:

- □ What business problem am I solving?
- □ Which module owns this responsibility?
- □ What is the module contract?
- □ What can fail?
- □ Can this be extended later?
- □ Does this violate SRP?
- □ Can another engineer understand this quickly?
- □ Does this endpoint contain business logic?
- □ Should this responsibility belong to the Application Layer instead?
- □ Is the request model strongly typed?
- □ Is the response contract stable?
- □ Can this endpoint evolve without breaking existing clients?
- □ Is this API stateless?

---

# Python Project Rules

- `src/` contains application code.
- `main.py` remains an orchestrator.
- Prefer many small modules.
- Avoid hardcoding.
- Configuration is not Constants.
- One responsibility per file.
- API routes should delegate all work.
- Keep FastAPI endpoints thin.
- Validate requests using Pydantic.
- Return typed response models.
- Centralize exception handling.
- Use dependency injection instead of manual object creation.

---

# Naming Rules

| Item | Convention |
|------|------------|
| Variables | snake_case |
| Functions | verb_noun() |
| Classes | PascalCase |
| Constants | UPPER_CASE |
| Modules | snake_case.py |

---

# Engineering Mindset

Don't ask:

> "How do I code this?"

Ask:

> "How should this system be designed?"

Don't ask:

> "How do I expose this feature?"

Ask:

> "What is the correct architectural boundary for this feature?"

---

# One-Line Reminders

- Code is for computers.
- Architecture is for humans.
- Contracts reduce coupling.
- Shared infrastructure reduces duplication.
- Good names reduce documentation.
- Design for change.
- Prefer extension over modification.
- Understand before implementing.
- Small modules scale better.
- Documentation preserves engineering knowledge.
- APIs expose capabilities—not implementations.
- HTTP is an interface, not business logic.
- Thin endpoints scale better.
- Stable contracts outlive implementations.
- Dependency Injection reduces coupling.
- Good APIs are predictable.
- Validation belongs at the system boundary.
- Documentation is part of the API.

---

# Sprint 0.75 Lessons

## Git

- Git records the complete history of a project.
- Every commit should represent one logical change.
- Use the staging area to review changes before committing.
- Annotated tags identify official releases.
- Always verify repository status before committing.

## Engineering Governance

- Good software is governed before it is expanded.
- Architectural decisions belong in ADRs.
- Every feature must satisfy the Definition of Done.
- Documentation should have clear ownership.
- Code reviews protect software quality.

---

# Sprint 1 Lessons

## Architecture

- Every module should have a single responsibility.
- Managers should orchestrate rather than implement business logic.
- Stable DataFrame contracts simplify downstream processing.
- Validation should occur before business logic.

## Engineering

- Logging should exist from the beginning.
- Build architecture before features.
- Prefer reusable components over duplicated logic.

---

# Sprint 2 Lessons

## Architecture

- Separation of Concerns improves maintainability.
- Managers coordinate work rather than perform business logic.
- Stable contracts simplify downstream development.
- Centralized infrastructure reduces duplication.

## Testing

- Automated testing provides confidence during refactoring.
- Small independent unit tests are easier to maintain.
- Every business component deserves dedicated tests.

## Engineering

- Documentation must evolve alongside implementation.
- Repository consistency is part of software quality.
- Enterprise software development extends beyond writing code.

---

# Sprint 3 Lessons

## Architecture

- Data cleaning and data quality assessment are separate responsibilities.
- Report builders improve extensibility.
- Structured outputs preserve module boundaries.
- Small focused classes are easier to maintain.

## Engineering

- Passing tests without warnings improves confidence.
- Sprint completion includes implementation, testing, documentation, and release preparation.
- Documentation should accurately reflect architecture.

---

# Sprint 4 Lessons

## Analytics

- Analytics should be implemented as independent reusable components.
- Managers coordinate analyzers rather than performing analysis directly.
- Standardized analytics reports simplify downstream reporting.

## Testing

- Integration tests validate collaboration between modules rather than individual implementations.
- Unit tests should verify public contracts instead of internal implementation details.
- Shared fixtures reduce duplicated test data and improve maintainability.

## Engineering

- Console output should communicate meaningful business information rather than raw objects.
- Resolve compatibility warnings early to reduce future maintenance effort.
- Release management is a core engineering activity, not an afterthought.
- Every sprint should conclude with repository review, documentation updates, testing, and versioned release.

---

# Current Engineering Milestone

The project's architectural layering is now permanent:

```text
Client
    ↓
REST API Layer
    ↓
Application
    ↓
Business Modules
    ↓
Persistence Layer
    ↓
Database Abstraction
    ↓
SQLite / PostgreSQL
```

This layered architecture ensures that each component has a single, well‑defined responsibility, and that business logic remains independent of infrastructure concerns. The Database Abstraction Layer isolates the application from concrete database implementations, allowing runtime engine selection without modifying business modules. The REST API Layer provides a clean HTTP interface while delegating all business operations to the Application Layer.

---

# Sprint 5 — Reporting & Performance Lessons

## Enterprise Reporting

- Reporting is a separate business capability and should remain isolated from analytics logic.
- Report generation should consume standardized outputs from upstream modules rather than reprocessing datasets.
- Export functionality should be modular so additional formats can be introduced without affecting existing components.

## Performance Validation

- Functional correctness alone is insufficient; large-scale datasets should be used to validate scalability.
- Benchmarking with small, large, and stress-test datasets helps identify performance bottlenecks early.
- Execution time, memory usage, and pipeline stability are valuable engineering metrics for evaluating production readiness.

## Engineering Practice

- Keep permanent engineering guidance separate from sprint-specific implementation details.
- Update architecture documentation only when architectural boundaries or responsibilities change.
- Use release documentation to record implementation achievements and benchmark results rather than modifying long-term engineering documents.

---

# Sprint 5.5 — Lessons Learned

## Architectural Lessons

Large software systems benefit from separating orchestration from
business logic.

Introducing a dedicated Application Layer significantly simplified
pipeline coordination while preserving module independence.

---

## Design Lessons

Stable contracts are more valuable than exposing implementation
details.

Business modules should communicate only through clearly defined
interfaces.

---

## Software Engineering Lessons

A thin application entry point improves readability, maintainability,
and extensibility.

Future presentation layers (CLI, Streamlit, APIs) can now reuse the
same Application Layer.

---

## Documentation Lessons

Maintaining a clear separation between:

- PROJECT_STATE
- ARCHITECTURE
- ROADMAP
- CHANGELOG
- PROJECT_JOURNAL

reduces duplication and improves long-term maintainability.

---

## Testing Lessons

Major architectural refactors should always be completed alongside
comprehensive automated validation.

Successfully preserving 79 / 79 passing tests throughout the refactor
provided confidence that architectural improvements did not introduce
functional regressions.

---

## Future Guidance

Future architectural work should continue to prioritize:

- Stable contracts
- Independent business modules
- Centralized orchestration
- Strong typing
- Enterprise documentation
- Automated validation

These principles established during Sprint 5.5 should remain guiding
engineering standards throughout future development.

---

# Sprint 6 — Persistence & Repository Lessons

## Persistence Architecture

- Persistence is an infrastructure concern and should remain separate from business logic.
- Business modules should not perform database operations directly.
- A dedicated Persistence Layer simplifies future database migrations.
- Database interactions should be centralized behind a single orchestration component.

---

## Repository Pattern

- Repositories isolate SQL from application logic.
- Each repository should own exactly one database entity.
- Stable repository interfaces reduce coupling between the application and the database implementation.
- Database engines can be replaced without affecting business modules when repositories remain stable.

---

## Database Design

- Normalize persistent data into focused tables rather than storing unrelated information together.
- Database schema creation should be centralized and automated.
- Database initialization should occur once during application startup.
- Application shutdown should always release database resources cleanly.

---

## Application Layer

- The Application Layer should orchestrate persistence rather than execute SQL.
- Pipeline execution should be treated as a business process whose lifecycle can be persisted.
- Infrastructure services should be coordinated centrally rather than scattered throughout business modules.

---

## Testing Lessons

- Persistence features require both functional testing and integration testing.
- Repository testing should validate database behavior rather than SQL implementation details.
- Architectural changes should preserve existing test suites to prevent regressions.
- Stress testing should include persistence operations, not only in-memory processing.

---

## Engineering Lessons

- Enterprise software evolves by adding architectural capabilities rather than modifying business modules.
- Introducing new infrastructure should minimize changes to existing components.
- Stable interfaces make large architectural extensions significantly easier.
- The Repository Pattern provides a strong foundation for future PostgreSQL integration.

---

## Future Guidance

Future infrastructure work should continue to prioritize:

- Layered Architecture
- Repository Pattern
- Stable Interfaces
- Separation of Concerns
- Centralized Orchestration
- Automated Testing
- Database Independence
- Enterprise Documentation

---

# Sprint 7 — Database Abstraction Lessons

## Database Abstraction

- Infrastructure should depend on abstractions rather than concrete database implementations.
- Business modules should remain completely unaware of the underlying database engine.
- Runtime database selection enables infrastructure flexibility without affecting business logic.
- A single abstraction can support multiple database engines when responsibilities are clearly defined.

---

## Interface Design

- Stable interfaces simplify large architectural changes.
- Design abstractions around responsibilities rather than implementations.
- A single interface can support multiple infrastructure providers when responsibilities are well defined.
- Concrete implementations should be selected at runtime through a factory pattern.

---

## Cross-Database Architecture

- SQL dialect differences should be isolated within the infrastructure layer.
- Database-specific behavior should never leak into business modules.
- Centralized connection management simplifies future expansion to additional database engines.
- Automatic placeholder conversion (e.g., `?` vs `%s`) keeps repositories database‑agnostic.

---

## Engineering Lessons

- Large architectural improvements should minimize changes to existing business modules.
- Dependency inversion enables infrastructure evolution without breaking application logic.
- Enterprise software grows through abstraction rather than duplication.
- Comprehensive testing across abstraction boundaries ensures compatibility.

---

## Future Guidance

Future infrastructure should continue to prioritize:

- Stable Interfaces
- Dependency Inversion
- Database Independence
- Replaceable Infrastructure
- Centralized Configuration
- Automated Validation
- Runtime Engine Selection

These principles established during Sprint 7 ensure that future database additions (MySQL, SQL Server, etc.) can be integrated without altering business logic, preserving the long-term maintainability of the platform.

---

# Sprint 8 — REST API Lessons

## REST API Design

- REST APIs expose services rather than business logic.
- Resource-oriented endpoints improve long-term maintainability.
- A thin API Layer simplifies future integrations.
- Stable endpoints reduce client-side changes.
- HTTP methods should align with operations.
- Status codes should communicate intent clearly.
- API versioning should be planned from the beginning.

---

## Dependency Injection

- Dependency Injection improves testability.
- Dependencies should be provided rather than constructed.
- Lifecycle management belongs to infrastructure.
- Business modules should not manage dependencies.
- Application dependencies should be centralized.
- Dependency Injection reduces global state.
- Explicit dependencies improve code clarity.

---

## Request & Response Contracts

- Validate input before business execution.
- Strong typing improves reliability.
- Request models define system boundaries.
- Response models improve consistency.
- Public contracts should evolve carefully.
- Pydantic provides robust validation.
- Contracts should be stable across releases.
- Breaking changes require careful planning.

---

## OpenAPI & Documentation

- Documentation should be generated whenever possible.
- Interactive documentation improves developer experience.
- API documentation must stay synchronized with implementation.
- Well-documented APIs reduce onboarding time.
- OpenAPI provides a standard specification format.
- Swagger UI enables API exploration.
- Documentation is part of the API contract.

---

## Exception Handling

- Errors should be standardized.
- Global exception handlers improve consistency.
- HTTP status codes communicate intent.
- Internal exceptions should not leak implementation details.
- Error responses should include actionable information.
- Consistent error formats simplify client handling.
- Logging should capture error context.

---

## API Testing

- Test endpoints independently.
- Validate request models.
- Validate response models.
- Verify OpenAPI generation.
- Verify Swagger documentation.
- Integration tests provide confidence across architectural boundaries.
- Endpoint tests should cover both success and failure cases.
- Performance testing should include HTTP endpoints.

---

## Architecture Lessons

- REST APIs are Presentation Layer components.
- Business logic belongs only in the Application Layer.
- Stable interfaces enable external integrations.
- Enterprise architecture evolves by adding layers instead of modifying business modules.
- HTTP concerns should never leak into business logic.
- API Layers should remain stateless and thin.
- The Application Layer owns orchestration.

---

## Engineering Lessons

- API-first thinking simplifies future integrations.
- External consumers should never depend on internal implementation.
- Architecture should remain technology-independent.
- Contracts are more important than frameworks.
- Service-oriented architecture improves modularity.
- FastAPI accelerates development without sacrificing quality.
- OpenAPI provides enterprise-grade documentation automatically.

---

## Future Guidance

Future API work should continue to prioritize:

- Thin Controllers
- Stable Contracts
- Dependency Injection
- Stateless Services
- OpenAPI Compliance
- Backward Compatibility
- Automated API Testing
- Enterprise Documentation
- Service-Oriented Architecture
- External Integration Readiness

These principles established during Sprint 8 ensure that the platform's REST API remains stable, well-documented, and ready for integrations with business intelligence platforms, frontend applications, and external services. The REST API Layer transforms AnalystGPT Enterprise from an internal analytics application into a service-oriented enterprise analytics platform capable of serving external consumers through well-defined, stable, and documented HTTP endpoints.

# sprint 9 - Power Bi #
## Lessons Learned

- Business Intelligence should remain an integration layer rather than a business layer.
- Dashboard services should consume existing report contracts instead of recalculating analytics.
- Stable API contracts simplify integration with external BI platforms.
- Separation of concerns enables new capabilities without modifying core business modules.
- Performance validation is as important as functional validation for enterprise software.
- Benchmarking should be automated and included in the engineering workflow.
- Enterprise APIs become more valuable when they serve multiple clients through reusable endpoints.
- Layered architecture allows new integration layers to be added with minimal architectural impact.
- Comprehensive automated testing provides confidence during platform expansion.
- Production readiness depends on functionality, performance, documentation, and maintainability rather than feature completeness alone.
---

# Sprint 10 — Enterprise Streamlit Frontend Lessons

## Frontend Architecture

- The frontend is a Presentation Layer and should remain independent from business logic.
- User interfaces should communicate exclusively through stable service interfaces or REST APIs.
- Views should coordinate presentation rather than implement business operations.
- Components should remain reusable, presentation-focused, and independent of backend implementation.
- Session State should manage only presentation state and never business state.
- Navigation should be centralized to ensure consistent user experience and maintainability.

---

## Service Layer

- Frontend Services provide a stable boundary between the user interface and the backend.
- Business modules should never be accessed directly from the frontend.
- Service-oriented frontend architecture simplifies future framework migration.
- Stable frontend contracts reduce coupling between presentation and application layers.

---

## User Interface Design

- Enterprise dashboards should prioritize clarity over visual complexity.
- Consistent layouts improve usability and reduce cognitive load.
- Interactive applications should provide immediate feedback for long-running operations.
- Data presentation should be separated from data processing.
- Reusable UI components improve consistency and reduce duplication.

---

## State Management

- Presentation state should remain isolated from application state.
- Session management should preserve user experience without affecting business workflows.
- UI state should never replace backend persistence.
- Stateless backend services simplify frontend implementation.

---

## Frontend–Backend Integration

- The frontend should treat the backend as a service rather than an internal implementation.
- REST API contracts provide a stable integration boundary.
- Backend implementations can evolve without requiring frontend redesign when contracts remain stable.
- Clear API boundaries simplify testing and future integrations.

---

## React Migration

- Frameworks should be replaceable without affecting business logic.
- Preserving service boundaries enables low-risk frontend migration.
- A well-designed backend outlives individual frontend technologies.
- Streamlit provides an effective MVP while maintaining a clear migration path to React.
- Readiness should be proven, not declared: the React migration is sequenced after product
  stabilization (Sprint 15) and a final readiness audit (Sprint 16), and happens in Sprint 17.

---

## Testing Lessons

- User interface features require functional validation in addition to automated testing.
- Frontend validation should include navigation, state management, API communication, and user workflows.
- Integration testing provides confidence that frontend and backend components collaborate correctly.
- Stable interfaces reduce regression risk during UI development.

---

## Documentation Lessons

- Frontend architecture deserves the same level of documentation as backend architecture.
- Architectural decisions should be captured through ADRs before implementation.
- Documentation should evolve together with architectural changes rather than after implementation.
- Repository documentation should accurately reflect the implemented user interface and system boundaries.

---

## Engineering Lessons

- Enterprise software extends beyond backend services to include maintainable presentation layers.
- Clean Architecture principles apply equally to frontend and backend development.
- Long-term maintainability depends on preserving architectural boundaries as new capabilities are introduced.
- Building reusable systems is more valuable than building isolated features.
- Consistent engineering standards across every layer improve scalability, onboarding, and future development.

---

## Future Guidance

Future frontend development should continue to prioritize:

- Presentation Layer Independence
- Stable REST API Contracts
- Reusable Components
- Service-Oriented Frontend Architecture
- Centralized Navigation
- Session State Isolation
- React-Ready Design
- Clean Architecture
- Separation of Concerns
- Enterprise Documentation
- Automated Validation
- User Experience Consistency

These principles established during Sprint 10 ensure that the frontend remains maintainable, extensible, and replaceable while preserving the integrity of the backend architecture. Future presentation technologies should integrate through the existing service boundaries without requiring modifications to the Application Layer, business modules, or persistence infrastructure.

---

# Sprint 11 — AI Insight Engine & Local LLM Lessons

## AI Layer Architecture

- AI insight generation should act as an enrichment stage following deterministic reporting and persistence, never replacing core analytics.
- Isolate LLM provider dependencies behind a provider-agnostic interface (`BaseLLM`) and factory (`LLMFactory`) to support seamless model or vendor migration.
- AI components must consume stable report contracts (`ReportingReport`) and return strongly typed, immutable dataclasses (`AIReport`, `AIResult`).
- AI modules must remain strictly stateless and read-only with respect to business datasets.

---

## Inference Performance & Prompt Engineering

- Sequential multi-call LLM workflows incur high latency overhead in local inference environments; a consolidated single-prompt architecture (`UnifiedReportEngine`) dramatically cuts response times.
- Strict prompt delimitations and explicit source-of-truth bounding prevent model hallucination and enforce factual consistency.
- Mandatory section headers with pre-compiled regex matching and alias mappings provide resilient parsing across different model weights.
- Context window management requires defensive serialization with depth-limited summarization and hard character caps.

---

## Output Parsing & Model Heuristics

- Modern reasoning models (e.g., Qwen, DeepSeek) emit thinking tags (`<think>`); robust sanitization (`ResponseParser`) is essential before assembling user-facing reports.
- Output truncation detection (analyzing trailing colons, incomplete punctuation, and length heuristics) is vital for actionable debugging.
- Unstructured LLM text must be parsed into strongly typed structures before integration with downstream APIs or frontends.

---

## Resilience & Production Boundaries

- Treat the LLM as an inherently unreliable dependency: encapsulate all generation calls in try-catch boundaries and return explicit failure results (`AIResult(success=False)`).
- The parent orchestrator (`Application.run()`) must gracefully complete data ingestion, processing, persistence, and reporting even when AI generation fails.
- CI/CD test suites must isolate live model calls to prevent environment-dependent build breakages.

---

## Summary of Sprint 11 Principles

- Post-Persistence AI Enrichment
- Pluggable LLM Abstraction (`BaseLLM`)
- Consolidated Single-Prompt Execution
- Strict Anti-Hallucination Guardrails
- Resilient Heading & Alias Parsing
- Reasoning Tag Sanitization
- Non-Blocking Failure Tolerance
- Immutable AI Data Contracts

---

# Sprint 12 — Production Deployment & CI/CD Lessons

## Configuration Normalization & Environment Portability

- Maintain dependency manifests (`requirements.txt`) in standard UTF-8 encoding with deterministic line endings to prevent cross-platform installation anomalies across local, container, and CI environments.
- Environment variables must serve as the single source of truth for runtime configurations (`API_HOST`, `API_PORT`, `API_BASE_URL`, `FRONTEND_PORT`), while `.env.example` provides a sanitized, comprehensive reference template without leaking credentials.

---

## Production Logging & Observability

- Log volume in production must be deterministically bounded; unmanaged log files will eventually exhaust container disk quotas. Implementing size-based rotation (`RotatingFileHandler` with `maxBytes` and `backupCount`) ensures predictable storage utilization.
- Logging frameworks must guard against duplicate handler registration across multi-module imports, reload cycles, and runtime re-configuration.

---

## Multi-Stage Containerization & Security Hardening

- Multi-stage Docker builds separate build dependencies (compilers, package managers) from runtime environments, minimizing final image attack surface and artifact size.
- Production containers must never execute as `root`. Defining a dedicated non-root user (`appuser`, UID 1000) prevents privilege escalation vulnerabilities in container runtimes.
- Build context hygiene via `.dockerignore` is essential to prevent local state, secrets (`.env`), virtual environments, bytecode caches, and logs from contaminating container layers.

---

## Multi-Service Orchestration & Network Isolation

- Docker Compose multi-service topologies must enforce health-aware dependency ordering (`condition: service_healthy`) rather than naive startup order to eliminate race conditions during database initialization.
- Isolate backing services (e.g., PostgreSQL) on internal private bridge networks without publishing host ports by default, minimizing external attack vectors.
- Inter-service networking must leverage container DNS names (`http://api:8000`) injected dynamically via environment variables rather than hardcoded `localhost` references.

---

## Strict CI/CD Quality Gates & Automated Validation

- CI quality gates must act as strict blocking controls. Suppressing errors with `|| true` or `--exit-zero` degrades quality enforcement into visual noise and permits regressions.
- When local development environments face host limitations (e.g., unavailable Docker daemon on local OS), standardized CI runners (GitHub Actions Ubuntu runners) provide the authoritative environment for container build compilation, Compose stack orchestration, health probing, and live integration testing.

---

## Summary of Sprint 12 Principles

- Standardized UTF-8 Dependency Manifests
- Centralized Environment Configuration (`.env.example`)
- Size-Bounded Rotating File Logging
- Multi-Stage Dockerfile with Dedicated Target Stages
- Non-Root Container Execution (`appuser`)
- Private Network Isolation for Backing Databases
- Health-Aware Multi-Service Startup Ordering
- Strictly Blocking CI Quality Gates (Zero Non-Blocking Suppressions)
- Continuous Integration as Authoritative Runtime Validator

---

# Sprint 13 — Enterprise Identity & Multi-User Platform Lessons

## Server-Side Authorization vs UI Gating

- Client-side visibility controls are strictly cosmetic; security must be enforced server-side.
- Insecure Direct Object Reference (IDOR) vulnerabilities arise when server endpoints trust client-supplied resource IDs without verifying ownership against the authenticated security context (`UserContext`).
- All repository queries must enforce user scoping (`WHERE user_id = ?`) directly at the database layer.

---

## Cryptographic Security & Performance Trade-offs

- Password hashing requires slow, memory-hard key derivation functions (PBKDF2-HMAC-SHA256 with 600,000 iterations). Plaintext storage or simple fast hashes (MD5, SHA-256) are dangerous and unacceptable.
- Timing attack mitigation requires constant-time verification (`secrets.compare_digest`) and dummy hashing cycles when authenticating non-existent usernames.

---

## Multi-Tenant Cache & State Isolation

- In multi-user applications, caching at the application layer must be explicitly keyed by tenant/user (`_user_pipeline_results: dict[int | None, PipelineResult]`). Single global cache variables will inadvertently leak sensitive analytical results between users.
- Frontend session management must provide atomic session purging (`clear_authenticated_session()`) upon logout to ensure subsequent logins on shared browsers start from a completely clean state.

---

## Administrative Safety Guards

- Administrative APIs must enforce protective invariants preventing the demotion, deactivation, or deletion of the last remaining active administrator, preventing irrecoverable system lockouts.
- Structured audit logs must sanitize sensitive data (passwords, tokens, hashes) at the boundary before logging to prevent credential spills in observability pipelines.

---

## Summary of Sprint 13 Principles

- Server-Side Scoped Ownership & IDOR Immunity
- Cryptographic Password Hashing (PBKDF2-HMAC-SHA256)
- Signed Stateless Tokens with Server-Side Revocation
- Declarative Role-Based Access Control (RBAC)
- Multi-User In-Memory Cache Isolation
- Last-Admin Lockout Safeguards
- Zero-Credential Leakage Security Audit Logging

---

# Sprint 14 — Architecture & Performance Insights

> **Status note.** This section was authored *before* Sprint 14 began and was originally
> headed "(Pre-Sprint)". Everything it anticipates was implemented in Sprint 14 (prepared as
> **v14.0.0**, not yet released): the
> asynchronous job state machine in `src/ai/job_executor.py` and `src/ai/models.py`, and
> cleaning governance in `src/governance/` with immutable artifact storage in
> `src/storage/artifact_store.py`.
>
> The insights below are retained as written, because their value is in the reasoning that
> preceded the design. The lessons drawn from *executing* Sprint 14 — the silent formatter
> exclusions, the skip guard that tested the wrong condition, the silent context-window
> truncation, and the documentation drift that produced four irreconcilable test totals —
> are recorded in PROJECT_JOURNAL.md under the Sprint 14 completion milestone.

## Synchronous AI Latency vs User Experience

- Coupling long-running LLM generation (45–70s) to synchronous HTTP requests severely degrades user perceived performance.
- Decoupling pipeline execution from AI generation via an asynchronous background job state machine (`PENDING → GENERATING → READY / FAILED`) allows immediate presentation of deterministic analytics while AI completes in the background.

## Data Cleaning Governance vs Silent Data Loss

- Destructive transformations (row dropping, imputation) without provenance tracking lead to silent information loss.
- Separating immutable raw source datasets from cleaned analytical datasets with explicit policy versioning and before/after quality metrics ensures data integrity and analytical reproducibility.

---

# Roadmap Re-baseline — Documentation Drift (September 2026)

- Sprint plans drifted because each document restated sprint scope independently: the roadmap
  called Sprint 15 *React Migration* while PROJECT_STATE.md and ARCHITECTURE.md called it
  *Refactoring & Architectural Evolution*. ROADMAP.md is now the single authority for
  sequencing; other documents should reference it rather than restate scope.
- "Complete" was used for three different things — code exists, tests pass, and released.
  The documents now distinguish Implemented · Tested · Verified (end-to-end through the real
  API/frontend path) · Released (tagged and merged) · Planned.
- Release status must come from Git, not from intent: v14.0.0 was recorded as the current
  baseline in several documents although no tag or merge existed.
- Product value needs its own gate. Components that were implemented and tested (governance,
  Dashboard, Admin) still had workflow or product-value gaps, which is why Sprint 15 precedes
  provider work (Sprint 16) and the React migration (Sprint 17).
