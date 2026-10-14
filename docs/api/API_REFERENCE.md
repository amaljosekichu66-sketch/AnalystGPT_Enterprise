# AnalystGPT Enterprise API Reference

> **Purpose**
>
> This document provides the official REST API reference for
> AnalystGPT Enterprise.
>
> It describes every available endpoint, request model,
> response model, HTTP status code, error response, and
> usage example.
>
> The REST API provides the public interface to AnalystGPT
> Enterprise while preserving the internal layered architecture.
>
> Business logic remains inside the Application Layer.
>
> Current Version: **v14.0.0** is the latest tag (released 2026-09-28). **v14.1.0**, the
> release that contains the pre-Sprint-15 hardening, is being cut from
> `pre-sprint-15-hardening`; this reference describes that code. Sprint 15 has not started.

---

# API Information

| Item | Value |
|------|--------|
| API Version | **14.1.0** (`src/core/constants.py` → `APP_VERSION`; also `info.version` in `docs/api/openapi.json`) |
| Framework | FastAPI |
| Specification | OpenAPI 3.1 |
| Exported contract | `docs/api/openapi.json` — **46 paths, 49 operations, 51 component schemas**; regenerate with `python scripts/export_openapi.py` (CI diff-checks the file against the live schema) |
| Documentation | Swagger UI & ReDoc (development only, unless `API_DOCS_ENABLED=true`) |
| Route convention | **Every functional router is mounted under `/api`.** The only unprefixed path is the service root, `/`. |
| Authentication | Bearer Token (`Authorization: Bearer <token>`) |
| Token algorithm | HMAC-SHA256 (`HS256`), signed in-house — no third-party JWT library |
| Password Hashing | PBKDF2-HMAC-SHA256, 600,000 iterations, 16-byte salt |
| Authorization | Declarative RBAC (`ADMIN`, `ANALYST`, `VIEWER`) |
| Content Type | `application/json` (export endpoints stream `text/plain` / `application/pdf`; `POST /api/datasets` takes `multipart/form-data`) |

---

# Base URL & Interactive Docs

| Resource | URL |
|---|---|
| Base API URL | `http://127.0.0.1:8000` |
| Swagger UI | `http://127.0.0.1:8000/docs` |
| ReDoc | `http://127.0.0.1:8000/redoc` |
| OpenAPI JSON | `http://127.0.0.1:8000/openapi.json` |

---

# Endpoint Summary

> **Source of truth.** The tables below list every one of the **46 paths / 49 operations** in
> `docs/api/openapi.json` (reconciled 2026-10-14). The *Auth* column is the permission each
> route's dependency enforces (`require_permission(...)` in `src/api/routes/`); "Active user"
> means any valid, non-revoked token. Every resource route is additionally scoped to its owner
> (an administrator may see all): another user's resource answers **404**.
>
> v14.0.0 exported 33 paths; the pre-Sprint-15 hardening added the dataset, cleaning-policy,
> audit, unlock, AI-cancel and account-session routes.
>
> **Outside development `/docs`, `/redoc` and `/openapi.json` are disabled** unless `API_DOCS_ENABLED=true`; use the exported `docs/api/openapi.json`.
>
> **Breaking change in v14.0.0.** The unprefixed `/reports/*` and `/powerbi/*` paths were
> removed. `/reports/*` had been mounted twice (prefixed and unprefixed) and `/powerbi/*`
> only unprefixed. Every removed path has an identical `/api`-prefixed equivalent with the
> same contract — prepend `/api`. Enforced by
> `tests/api/test_openapi_contract.py::test_every_path_is_under_the_api_prefix`.

### System & Health Endpoints
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET` | `/` | API root information | None |
| `GET` | `/api/health` | Service health status | None |
| `GET` | `/api/version` | Current application version | None |

### Authentication (`/api/auth`)
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `POST` | `/api/auth/register` | Register a new account (**201**). New accounts are always `VIEWER`; an admin promotes them with `PATCH /api/admin/users/{user_id}`. **403** when `AUTH_SELF_REGISTRATION_ENABLED=false`. | None |
| `POST` | `/api/auth/login` | Authenticate and acquire a Bearer token | None |
| `GET` | `/api/auth/me` | Current authenticated user profile | Active user |
| `POST` | `/api/auth/logout` | Revoke the presented token | Active user |
| `POST` | `/api/auth/password` | Change the caller's password | Active user |
| `POST` | `/api/auth/logout-all` | Revoke every session of the caller | Active user |

> Login and registration can answer **429** with `Retry-After` (account lockout / per-client
> rate limit); a weak password is **400**. A duplicate username *or* email answers **409** with
> one generic message — "An account with this username or email address already exists." — that
> does not say which field collided (SEC-15). Every error body carries `request_id`, echoed as
> the `X-Request-ID` header; unexpected failures return a generic message plus that id.

### Administration (`/api/admin`)
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET` | `/api/admin/users` | List users (`limit` 1–1000, `offset`) | `user:read` |
| `GET` | `/api/admin/users/{user_id}` | Get user detail | `user:read` |
| `PATCH` | `/api/admin/users/{user_id}` | Update role, status or email (last-admin safeguard) | `user:manage` |
| `DELETE` | `/api/admin/users/{user_id}` | Delete a user account and its data (last-admin safeguard) | `user:manage` |
| `POST` | `/api/admin/users/{user_id}/unlock` | Clear every failed-login counter for the account | `user:manage` |
| `GET` | `/api/admin/audit-events` | Durable audit events, newest first (`limit`, `event_type`, `actor_id`) | `audit:read` |
| `GET` | `/api/admin/audit-events/verify` | Recompute the tamper-evident hash chain over the retained audit rows | `audit:read` |

### Datasets (`/api/datasets`)
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `POST` | `/api/datasets` | Upload a dataset (`multipart/form-data`, field `file`); **201** with `dataset_version_id` | `dataset:upload` |
| `GET` | `/api/datasets/{dataset_version_id}/analysis` | Semantic profile, planned charts and cleaning-policy recommendation | `report:view` |
| `DELETE` | `/api/datasets/{dataset_version_id}` | Delete an upload and its cleaned versions; existing reports are kept | `dataset:upload` |

> **Breaking change (pre-Sprint-15 hardening).** Clients never send server paths; no endpoint
> accepts one. Upload the bytes here, then reference the dataset by `dataset_version_id`
> everywhere else. Allowed types: `.csv .xlsx .xls .json` (else 415); size limit
> `MAX_FILE_SIZE_MB` (default 100; else 413); unparseable content → 422. All three are checked
> before anything is persisted. `.xlsx` archives are also checked before decompression
> (compression ratio, expanded size, entries → 413), parsed datasets are capped at
> `MAX_UPLOAD_ROWS` / `MAX_UPLOAD_COLUMNS` (413), and a user may have at most
> `MAX_CONCURRENT_JOBS_PER_USER` uploads/runs in progress (429). The response contains no
> storage path.

### Analytics Pipeline
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `POST` | `/api/pipeline` | Execute the full analytics pipeline on `{"dataset_version_id": "<uuid>", "cleaning_policy_proposal_id": "<optional>"}` | `pipeline:execute` **and** `ai:generate` |

> **Breaking change (pre-Sprint-15 hardening).** `input_path` was removed: it let any ANALYST
> make the server read an arbitrary file. Unknown fields are rejected with 422; an unknown or
> foreign `dataset_version_id` is 404. `cleaning_policy_proposal_id`, when given, must be an
> **APPROVED** proposal for the same dataset; without it the default policy runs.
> `output_path` in the response is a bare file name.

> `src/api/routes/pipeline.py` declares a single route, `"/pipeline"`. There is no
> `/api/pipeline/run` endpoint; earlier documentation and the row label in
> `performance/phase2_benchmark_results.md` were incorrect — the benchmark script
> `performance/phase2_benchmark.py` calls `/api/pipeline`.

### Business Intelligence & Dashboard (`/api/powerbi`)
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET` | `/api/powerbi/status` | Application/BI status, including a database check | `dashboard:view` |
| `GET` | `/api/powerbi/dashboard` | Full dashboard payload | `dashboard:view` |
| `GET` | `/api/powerbi/summary` | Executive KPI summaries and metadata | `report:view` |
| `GET` | `/api/powerbi/statistics` | Descriptive statistics | `report:view` |
| `GET` | `/api/powerbi/correlation` | Numeric correlation matrices | `report:view` |
| `GET` | `/api/powerbi/distribution` | Distribution metrics and histograms | `report:view` |
| `GET` | `/api/powerbi/categorical` | Categorical frequencies and counts | `report:view` |
| `GET` | `/api/powerbi/pipeline` | Pipeline execution metadata | `report:view` |
| `GET` | `/api/powerbi/report` | Report payload for BI consumption | `report:view` |

> **Read-only (pre-Sprint-15 hardening).** Every `/api/powerbi/*` data route takes
> `?dataset_version_id=` (the old `?dataset=<path>` is gone) and only *returns* the stored
> result of a previous `POST /api/pipeline`; it never executes. A dataset that has not been run
> yet, or that belongs to another user, is 404. These routes previously ran the pipeline on a
> cache miss, which let a VIEWER execute it without `PIPELINE_EXECUTE`.
> `/api/powerbi/status` was previously unauthenticated and static; it now requires
> `dashboard:view` and reports a database check.
>
> Both `src/api/routes/dashboard.py` and `src/api/routes/powerbi.py` use `prefix="/powerbi"`.
> `/api/powerbi/status` and `/api/powerbi/dashboard` are served by the dashboard router; the
> rest by the Power BI router. There has never been an `/api/dashboard/*` prefix.

### Reports Centre (`/api/reports`)
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET` | `/api/reports` | List generated reports for the authenticated user | `report:view` |
| `GET` | `/api/reports/export/text` | Stream the latest report as plain text | `report:export` |
| `GET` | `/api/reports/export/pdf` | Stream the latest report as PDF | `report:export` |
| `GET` | `/api/reports/latest/export/text` | Alias of `/api/reports/export/text` | `report:export` |
| `GET` | `/api/reports/latest/export/pdf` | Alias of `/api/reports/export/pdf` | `report:export` |
| `GET` | `/api/reports/{report_id}/export/text` | Stream a specific report as plain text | `report:export` |
| `GET` | `/api/reports/{report_id}/export/pdf` | Stream a specific report as PDF | `report:export` |

### Asynchronous AI Insight Jobs (`/api/ai`)
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET` | `/api/ai/jobs/latest/status` | Most recent AI job for the caller | `report:view` |
| `GET` | `/api/ai/jobs/{job_id}` | Job status and generated report (`PENDING` / `GENERATING` / `READY` / `FAILED` / `CANCELLED`) | `report:view` |
| `POST` | `/api/ai/jobs/{job_id}/retry` | Re-queue a `FAILED` or `CANCELLED` job (anything else is 400) | `ai:generate` |
| `POST` | `/api/ai/jobs/{job_id}/cancel` | Cancel a `PENDING` or `GENERATING` job; a running generation's result is discarded | `ai:generate` |

> Jobs persist their input, so a job that was pending or running when the API stopped resumes
> after a restart.

### Data Cleaning Governance & Lineage (`/api/governance`)
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `POST` | `/api/governance/preview` | Non-destructive cleaning impact preview | `report:view` |
| `GET` | `/api/governance/dataset-versions` | List immutable dataset versions | `report:view` |
| `GET` | `/api/governance/dataset-versions/{version_id}` | Retrieve one dataset version and its checksum metadata | `report:view` |
| `GET` | `/api/governance/lineage/run/{pipeline_run_id}` | Provenance and lineage for a pipeline run | `report:view` |

### Cleaning Policy Workflow (`/api/governance/policies`)
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `POST` | `/api/governance/policies` | Propose a cleaning policy for one of your datasets (**201**, state `PROPOSED`) | `pipeline:execute` |
| `GET` | `/api/governance/policies` | List cleaning policy proposals | `report:view` |
| `PATCH` | `/api/governance/policies/{proposal_id}` | Modify a proposal while it is `PROPOSED` (the change is recorded) | `pipeline:execute` |
| `POST` | `/api/governance/policies/{proposal_id}/approve` | Approve a proposal | `pipeline:execute` (reviewer) |
| `POST` | `/api/governance/policies/{proposal_id}/reject` | Reject a proposal | `pipeline:execute` (reviewer) |

> Reviewers are administrators and — unless `GOVERNANCE_REQUIRE_SEPARATE_APPROVER=true` — the
> proposer themself (`src/governance/policy_approval.py`). An action on a proposal in the wrong
> state is **409**; a non-reviewer is **403**; an unknown or foreign proposal is **404**. Only an
> APPROVED proposal can be passed to `POST /api/pipeline`, and the applied configuration records
> the proposal id and approver in the run's lineage.

---

# Authentication & Security Details

## Headers

Protected endpoints require the Bearer token in the `Authorization` header:

```http
Authorization: Bearer <access_token>
```

## Permission matrix

Defined in `src/identity/permissions.py`.

| Permission | `ADMIN` | `ANALYST` | `VIEWER` |
|---|:---:|:---:|:---:|
| `dataset:upload` | ✅ | ✅ | — |
| `pipeline:execute` | ✅ | ✅ | — |
| `report:view` | ✅ | ✅ | ✅ |
| `report:export` | ✅ | ✅ | — |
| `dashboard:view` | ✅ | ✅ | ✅ |
| `ai:generate` | ✅ | ✅ | — |
| `user:read` | ✅ | — | — |
| `user:manage` | ✅ | — | — |
| `audit:read` | ✅ | — | — |
| `system:admin` | ✅ | — | — |

## Security Invariants

1. **Server-side ownership enforcement.** Queries for `datasets`, `dataset_versions`,
   `pipeline_runs`, `reports`, `ai_jobs`, `ai_reports`, cleaning policy proposals and the other
   governance tables are scoped to the authenticated `user_id` in the repositories and services
   (`src/database/repositories/`, `src/governance/`), not left to the route. Another user's
   resource answers 404. Per-user isolation is enforced and tested on every resource route —
   see `tests/identity/test_resource_ownership.py`, `tests/api/test_report_export_ownership.py`,
   `tests/api/test_export_isolation.py` and `tests/test_persistence_isolation.py`.
2. **Last-admin safeguard.** The system rejects attempts to deactivate, demote or delete the
   last remaining active administrator.
3. **Token revocation.** Logout and logout-all revoke tokens through
   `DatabaseTokenRevocationService`, which persists them in the `revoked_tokens` table; a
   revoked token is rejected even before expiry and after an API restart.
4. **Deployment guards.** When `APP_ENVIRONMENT` is anything other than `development`,
   startup fails if `AUTH_SECRET_KEY` is missing, shorter than 32 bytes, still the built-in
   development key or the `CHANGE_ME` placeholder from `.env.example`, and fails if
   `AUTH_ALLOW_HEADER_IDENTITY` is enabled. The `X-User-Id` / `X-User-Name` / `X-User-Role`
   headers are a complete authentication bypass and exist only for local development and the
   API test-suite.
5. **Audit trail.** Security events are written to the durable, hash-chained `audit_events`
   table; `GET /api/admin/audit-events/verify` recomputes the chain.

---

# HTTP Status Codes

| Code | Meaning | Usage |
|---|---|---|
| `200` | OK | Request succeeded |
| `201` | Created | User registered, dataset uploaded, or cleaning policy proposed |
| `400` | Bad Request | Invalid parameter, weak password, administrative guard violation, or an AI job in the wrong state for retry/cancel |
| `401` | Unauthorized | Missing, invalid, expired, or revoked Bearer token |
| `403` | Forbidden | Authenticated user lacks the required role/permission, the account is disabled, self-registration is off, or the caller may not review a cleaning policy |
| `404` | Not Found | Resource does not exist, or belongs to another user |
| `409` | Conflict | Username or email already registered (one generic message that names neither field), or a cleaning policy proposal is not in a valid state for the action |
| `413` | Content Too Large | Upload exceeds the size, archive, row or column limits |
| `415` | Unsupported Media Type | Upload is not `.csv`, `.xlsx`, `.xls` or `.json` |
| `422` | Unprocessable Entity | Pydantic schema validation failure, unknown request field, or unparseable upload |
| `429` | Too Many Requests | Login lockout / rate limit (with `Retry-After`), or too many uploads/runs in progress |
| `500` | Internal Server Error | Unhandled server exception (generic message plus `request_id`) |

---

# Current API Status

| Item | Status |
|------|--------|
| REST API Layer | ✅ Stable |
| FastAPI Server | ✅ Operational |
| Route convention | ✅ Single `/api` prefix; unprefixed aliases removed in v14.0.0 |
| Authentication Subsystem | ✅ Implemented & tested (v13.0.0; lockout, password change, logout-all and persistent revocation added by the pre-Sprint-15 hardening) |
| Role-Based Access Control | ✅ Implemented & tested (v13.0.0); self-registration grants `VIEWER` only |
| Admin User Management API | ✅ Implemented & tested; delete, unlock and the audit-event views are also exposed in the Streamlit Admin page |
| Resource Ownership & Isolation | Per-user isolation enforced and tested on every resource route (pre-Sprint-15 hardening). The v13.0.0 claim of complete IDOR defence was contradicted by the hardening audit (server-path reads, cross-user rows under concurrency) and has been fixed since |
| Asynchronous AI Insight Engine | ✅ Implemented & tested (cancel, retry of FAILED/CANCELLED, resume after restart); a live Ollama run is recorded in `docs/verification/live_ollama_run_2026-10-14.log` |
| Data Cleaning Governance & Lineage | 🟡 Propose → modify → approve/reject → run workflow implemented & tested over the API; end-to-end verification through the UI is Sprint 15 |
| Text & PDF Report Export Streaming | ✅ Implemented & tested (Sprint 14) |
| Swagger UI & ReDoc | ✅ Operational (development, or `API_DOCS_ENABLED=true`) |
| OpenAPI 3.1 Spec | ✅ Exported and diff-checked in CI (46 paths, 49 operations, 51 component schemas) |
| Automated API Tests | Part of the 1,242 tests in the default suite (`pytest`); see PROJECT_STATE.md (*Headline numbers*, measured 2026-10-14) |

---

**API contract version:** OpenAPI **3.1.0** (`docs/api/openapi.json`)

**Current application version:** latest tag **v14.0.0** (released 2026-09-28); **v14.1.0** (pre-Sprint-15 hardening) is being released

**Current sprint:** Sprint 14 — Enterprise Stabilization, Data Governance & Grounded Reporting (released as v14.0.0), followed by the pre-Sprint-15 hardening (v14.1.0). Sprint 15 has not started.

**Next:** Sprint 15 — Enterprise Stabilization, Governance Completion & Product/UX Remediation (planned) → Sprint 16 → Sprint 17 — see ROADMAP.md
