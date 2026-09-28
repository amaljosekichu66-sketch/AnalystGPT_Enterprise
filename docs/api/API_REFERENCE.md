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
> Current Version: **v14.0.0** (prepared — not yet tagged or merged to `main`; last released v13.0.0)

---

# API Information

| Item | Value |
|------|--------|
| API Version | **v14.0.0** (`src/core/constants.py` → `APP_VERSION`; prepared, not yet released) |
| Framework | FastAPI |
| Specification | OpenAPI 3.1 |
| Exported contract | `docs/api/openapi.json` — **33 paths, 42 schemas** |
| Documentation | Swagger UI & ReDoc |
| Route convention | **Every functional router is mounted under `/api`.** The only unprefixed path is the service root, `/`. |
| Authentication | Bearer Token (`Authorization: Bearer <token>`) |
| Token algorithm | HMAC-SHA256 (`HS256`), signed in-house — no third-party JWT library |
| Password Hashing | PBKDF2-HMAC-SHA256, 600,000 iterations, 16-byte salt |
| Authorization | Declarative RBAC (`ADMIN`, `ANALYST`, `VIEWER`) |
| Content Type | `application/json` (export endpoints stream `text/plain` / `application/pdf`) |

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

> **Source of truth.** The tables below were generated from the live FastAPI schema
> (`app.openapi()`) and reconciled against the route declarations under `src/api/routes/`
> and the exported contract `docs/api/openapi.json`. All three agree: **33 paths**.
>
> **Breaking change in v14.0.0.** The unprefixed `/reports/*` and `/powerbi/*` paths were
> removed. `/reports/*` had been mounted twice (prefixed and unprefixed) and `/powerbi/*`
> only unprefixed. Every removed path has an identical `/api`-prefixed equivalent with the
> same contract — prepend `/api`. Enforced by
> `tests/api/test_openapi_contract.py::test_every_path_is_under_the_api_prefix`.

### System & Health Endpoints
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/` | API root information | No |
| `GET` | `/api/health` | Service health status | No |
| `GET` | `/api/version` | Current application version | No |

### Authentication (`/api/auth`)
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/auth/register` | Register a new user account | No |
| `POST` | `/api/auth/login` | Authenticate and acquire a Bearer token | No |
| `GET` | `/api/auth/me` | Current authenticated user profile | Yes (active user) |
| `POST` | `/api/auth/logout` | Revoke the token and end the session | Yes (active user) |

### Administrative User Management (`/api/admin`)
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/admin/users` | List users with pagination | `USER_MANAGE` |
| `GET` | `/api/admin/users/{user_id}` | Get user detail | `USER_MANAGE` |
| `PATCH` | `/api/admin/users/{user_id}` | Update user role or status | `USER_MANAGE` |
| `DELETE` | `/api/admin/users/{user_id}` | Delete a user account | `USER_MANAGE` |

### Analytics Pipeline
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/pipeline` | Execute the full analytics pipeline | Yes / scoped |

> `src/api/routes/pipeline.py` declares a single route, `"/pipeline"`. There is no
> `/api/pipeline/run` endpoint; earlier documentation and the row label in
> `performance/phase2_benchmark_results.md` were incorrect — the benchmark script
> `performance/phase2_benchmark.py` calls `/api/pipeline`.

### Business Intelligence & Dashboard (`/api/powerbi`)
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/powerbi/status` | Business Intelligence layer status | Yes / scoped |
| `GET` | `/api/powerbi/dashboard` | Full dashboard payload | Yes / scoped |
| `GET` | `/api/powerbi/summary` | Executive KPI summaries and metadata | Yes / scoped |
| `GET` | `/api/powerbi/statistics` | Descriptive statistics | Yes / scoped |
| `GET` | `/api/powerbi/correlation` | Numeric correlation matrices | Yes / scoped |
| `GET` | `/api/powerbi/distribution` | Distribution metrics and histograms | Yes / scoped |
| `GET` | `/api/powerbi/categorical` | Categorical frequencies and counts | Yes / scoped |
| `GET` | `/api/powerbi/pipeline` | Pipeline execution metadata | Yes / scoped |
| `GET` | `/api/powerbi/report` | Report payload for BI consumption | Yes / scoped |

> Both `src/api/routes/dashboard.py` and `src/api/routes/powerbi.py` use `prefix="/powerbi"`.
> `/api/powerbi/status` is served by the dashboard router; the rest by the Power BI router.
> There has never been an `/api/dashboard/*` prefix.

### Reports Centre (`/api/reports`)
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/reports` | List generated reports for the authenticated user | Yes / scoped |
| `GET` | `/api/reports/export/text` | Stream the latest report as plain text | `REPORT_EXPORT` |
| `GET` | `/api/reports/export/pdf` | Stream the latest report as PDF | `REPORT_EXPORT` |
| `GET` | `/api/reports/latest/export/text` | Stream the latest pipeline run's text report | `REPORT_EXPORT` |
| `GET` | `/api/reports/latest/export/pdf` | Stream the latest pipeline run's PDF report | `REPORT_EXPORT` |
| `GET` | `/api/reports/{report_id}/export/text` | Stream a specific report as plain text | `REPORT_EXPORT` |
| `GET` | `/api/reports/{report_id}/export/pdf` | Stream a specific report as PDF | `REPORT_EXPORT` |

### Asynchronous AI Insight Jobs (`/api/ai`)
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/ai/jobs/latest/status` | Status of the most recent AI job for the caller | Yes / scoped |
| `GET` | `/api/ai/jobs/{job_id}` | AI job status and generated report (`PENDING` / `GENERATING` / `READY` / `FAILED`) | Yes / scoped |
| `POST` | `/api/ai/jobs/{job_id}/retry` | Retry a failed AI generation job | Yes / scoped |

### Data Cleaning Governance & Lineage (`/api/governance`)
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/governance/preview` | Non-destructive cleaning impact preview | Yes / scoped |
| `GET` | `/api/governance/dataset-versions` | List immutable dataset versions | `REPORT_VIEW` |
| `GET` | `/api/governance/dataset-versions/{version_id}` | Retrieve one dataset version and its checksum metadata | `REPORT_VIEW` |
| `GET` | `/api/governance/lineage/run/{pipeline_run_id}` | Provenance and lineage for a pipeline run | `REPORT_VIEW` |

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

1. **Server-side ownership enforcement.** Queries for `datasets`, `pipeline_runs`, `reports`,
   `ai_jobs`, `ai_reports` and the governance tables are scoped to the authenticated
   `user_id` inside `src/database/repositories/`, not at the route. Accessing another user's
   resource returns 404 or 403 (IDOR immunity).
2. **Last-admin safeguard.** The system rejects attempts to deactivate, demote or delete the
   last remaining active administrator.
3. **Token revocation.** Logout registers the token with `TokenRevocationService`; a revoked
   token is rejected even before expiry.
4. **Deployment guards.** When `APP_ENVIRONMENT` is anything other than `development`,
   startup fails if `AUTH_SECRET_KEY` is still the built-in development key, and fails if
   `AUTH_ALLOW_HEADER_IDENTITY` is enabled. The `X-User-Id` / `X-User-Name` / `X-User-Role`
   headers are a complete authentication bypass and exist only for local development and the
   API test-suite.

---

# HTTP Status Codes

| Code | Meaning | Usage |
|---|---|---|
| `200` | OK | Request succeeded |
| `201` | Created | Resource (user / pipeline run) created successfully |
| `400` | Bad Request | Invalid parameter or administrative guard violation |
| `401` | Unauthorized | Missing, invalid, expired, or revoked Bearer token |
| `403` | Forbidden | Authenticated user lacks the required role/permission, or the account is disabled |
| `404` | Not Found | Resource does not exist, or belongs to another user |
| `409` | Conflict | Username or email already registered |
| `422` | Unprocessable Entity | Pydantic schema validation failure |
| `500` | Internal Server Error | Unhandled server exception |

---

# Current API Status

| Item | Status |
|------|--------|
| REST API Layer | ✅ Stable |
| FastAPI Server | ✅ Operational |
| Route convention | ✅ Single `/api` prefix; unprefixed aliases removed in v14.0.0 |
| Authentication Subsystem | ✅ Complete (v13.0.0) |
| Role-Based Access Control | ✅ Complete (v13.0.0) |
| Admin User Management API | ✅ Implemented & tested (v13.0.0); `DELETE /api/admin/users/{user_id}` is not exposed in the Streamlit Admin UI — Sprint 15 |
| Resource Ownership & IDOR Defense | ✅ Complete (v13.0.0) |
| Asynchronous AI Insight Engine | ✅ Implemented & tested (Sprint 14); end-to-end verification in Sprint 15 |
| Data Cleaning Governance & Lineage | 🟡 Implemented & tested (Sprint 14); end-to-end workflow needs remediation — Sprint 15 |
| Text & PDF Report Export Streaming | ✅ Implemented & tested (Sprint 14) |
| Swagger UI & ReDoc | ✅ Operational |
| OpenAPI 3.1 Spec | ✅ Exported and in sync (33 paths, 42 schemas) |
| Automated API Tests | ✅ Passing — part of the 714-test suite (see PROJECT_STATE.md § *Executed Validation*) |

---

**API contract version:** OpenAPI **3.1.0** (`docs/api/openapi.json`)

**Current application version:** **v14.0.0** (prepared — not yet tagged or merged to `main`; last released v13.0.0)

**Current sprint:** Sprint 14 — Stabilization / Production Hardening (implemented and validated locally; release pending)

**Next:** Sprint 15 — Enterprise Stabilization, Governance Completion & Product/UX Remediation (planned) → Sprint 16 → Sprint 17 — see ROADMAP.md
