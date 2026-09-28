# ADR-024 — Enterprise Identity and Multi-User Architecture

## Status

Accepted

---

## Context

Through Sprints 0–12, AnalystGPT Enterprise was architected and operated primarily as a single-user analytics system. In this model:
- The REST API, CLI, and Streamlit frontend execute without requiring user authentication.
- Resource persistence (pipeline runs, datasets, quality reports, analytics reports, and export reports) was stored globally without user association or ownership metadata.
- In-memory state and cache in `Application` assumed single-tenant execution.

As the platform transitions to an enterprise-grade multi-user environment (Sprint 13), several architectural requirements must be addressed:
1. **Identity & Authentication**: The platform must support user identity with secure credential management (cryptographic password hashing with per-user salt and constant-time verification).
2. **Role-Based Access Control (RBAC)**: Fine-grained permissions and predefined enterprise roles (`ADMIN`, `ANALYST`, `VIEWER`) to restrict administrative operations, pipeline execution, and dataset mutations.
3. **Resource Ownership & Data Isolation**: Resources (datasets, pipeline runs, reports, and AI insights) must be associated with a user ID. A user must not be able to view, access, or mutate another user's resources merely by knowing their resource ID.
4. **Decoupled Business Modules**: Core analytics and transformation modules (`UploadManager`, `CleaningManager`, `QualityManager`, `AnalyticsManager`, `ReportingManager`, `AIManager`, `DashboardService`) must remain strictly decoupled from identity, HTTP sessions, tokens, and passwords.
5. **Zero Disruption to Existing Contracts**: Existing API contracts, Power BI integrations, CLI execution, and Streamlit presentation layer must maintain backward compatibility.

---

## Decision

We adopt a **Cross-Cutting Layered Identity and Security Context Architecture**:

```text
Client (Browser / API Client)
       │
       ▼
Identity / Authentication Boundary (HTTP Headers / Bearer Tokens / Sessions)
       │
       ▼
FastAPI Dependency Injection (`get_user_context`, `get_current_active_user`, `require_role`, `require_permission`)
       │
       ▼
Security / Request Context (`UserContext`)
       │
       ▼
Application Layer (`Application.run(input_path, user_context=...)`)
       │
       ├── Business Modules (Pure Dataframes & Reports — Persistence/Auth Agnostic)
       │
       ▼
Persistence Layer (`PersistenceManager` associates `user_id` with records)
       │
       ▼
Database Repositories (`UserRepository`, `DatasetRepository`, `PipelineRunRepository`, etc.)
```

### Key Architectural Tenets

1. **Dedicated Identity Subsystem (`src/identity/`)**:
   - `models.py`: Domain entity `User`, enumerations `UserRole` (`ADMIN`, `ANALYST`, `VIEWER`) and `UserStatus` (`ACTIVE`, `INACTIVE`, `SUSPENDED`), and Pydantic schemas (`UserCreate`, `UserUpdate`, `UserResponse`, `UserLogin`).
   - `context.py`: `UserContext` carrying identity metadata, active role, and permission evaluation helpers. Thread-safe context variables (`get_current_user_context`, `set_current_user_context`) allow seamless async propagation.
   - `permissions.py`: Fine-grained `Permission` enumeration and `ROLE_PERMISSIONS` RBAC matrix.
   - `interfaces.py`: Clean abstract protocols (`IPasswordHasher`, `IUserRepository`, `IAuthenticator`, `IAuthorizationService`).
   - `password_hasher.py`: `PBKDF2PasswordHasher` utilizing PBKDF2-HMAC-SHA256 with 600,000 iterations, 16-byte cryptographic salts, and `hmac.compare_digest` constant-time verification.
   - `in_memory_user_repository.py`: Thread-safe in-memory repository for unit testing and detached operations.

2. **Persistence Schema & Repositories (`src/database/`)**:
   - `SchemaManager` creates the `users` table across SQLite and PostgreSQL with unique constraints on `username` and `email`.
   - `pipeline_runs`, `datasets`, and `reports` include optional nullable `user_id` foreign keys referencing `users(id)` with `ON DELETE SET NULL` for forward and backward compatibility.
   - `UserRepository` implements `IUserRepository` over `BaseRepository`.

3. **API Dependency Injection & Exception Handling (`src/api/`)**:
   - Fast dependency providers (`get_user_context`, `get_current_active_user`, `require_role`, `require_permission`) enforce authentication and authorization at route boundaries.
   - Centralized exception handlers map `AuthenticationError` (401), `AuthorizationError` / `PermissionDeniedError` / `UserDisabledError` (403), `UserNotFoundError` (404), and `UserAlreadyExistsError` (409) into uniform JSON error payloads.

4. **Backward-Compatible Application Orchestration (`src/application/`)**:
   - `Application.run()` accepts an optional `user_context: UserContext | None = None`. When omitted, it safely defaults to the active request context or anonymous mode.

---

## Consequences

### Advantages
- **Strict Separation of Concerns**: Business algorithms remain pure, testable, and unpolluted by authentication or session concerns.
- **Server-Side Enforcement**: Authorization and data isolation rules are verified server-side at the API, Application, and Persistence boundaries.
- **Pluggable & Extensible**: Authentication mechanisms and password hashing algorithms adhere to clear protocols, allowing seamless future addition of OAuth2, JWT, or enterprise SSO.
- **100% Backward Compatible**: Existing tests and unauthenticated API endpoints continue to operate without disruption.

### Trade-offs
- Downstream database operations will require passing `user_id` or `UserContext` when associating resource ownership in Phases 2 and 3.

---

## Implementation

- [`src/identity/models.py`](../../src/identity/models.py)
- [`src/identity/context.py`](../../src/identity/context.py)
- [`src/identity/permissions.py`](../../src/identity/permissions.py)
- [`src/identity/interfaces.py`](../../src/identity/interfaces.py)
- [`src/identity/password_hasher.py`](../../src/identity/password_hasher.py)
- [`src/identity/exceptions.py`](../../src/identity/exceptions.py)
- [`src/identity/in_memory_user_repository.py`](../../src/identity/in_memory_user_repository.py)
- [`src/database/schema_manager.py`](../../src/database/schema_manager.py)
- [`src/database/repositories/user_repository.py`](../../src/database/repositories/user_repository.py)
- [`src/api/dependencies/auth_dependencies.py`](../../src/api/dependencies/auth_dependencies.py)
- [`src/api/exceptions/exception_handlers.py`](../../src/api/exceptions/exception_handlers.py)
- [`src/application/app.py`](../../src/application/app.py)
