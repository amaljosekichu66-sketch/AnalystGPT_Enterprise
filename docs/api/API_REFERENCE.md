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
> Current Version: **v13.0.0**

---

# API Information

| Item | Value |
|------|--------|
| API Version | **v13.0.0** |
| Framework | FastAPI |
| Specification | OpenAPI 3.1 |
| Documentation | Swagger UI & ReDoc |
| Architecture | REST API |
| Authentication | Bearer Token (`Authorization: Bearer <token>`) |
| Password Hashing | PBKDF2-HMAC-SHA256 (600,000 iterations) |
| Authorization | Declarative RBAC (`ADMIN`, `ANALYST`, `VIEWER`) |
| Content Type | `application/json` |

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

### System & Health Endpoints
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/` | API Root Information | No |
| `GET` | `/api/health` | Service Health Status | No |
| `GET` | `/api/version` | Current Application Version | No |

### Authentication Endpoints (`/api/auth`)
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/auth/register` | Register new user account | No |
| `POST` | `/api/auth/login` | Authenticate & acquire Bearer token | No |
| `GET` | `/api/auth/me` | Current authenticated user profile | Yes (Active User) |
| `POST` | `/api/auth/logout` | Invalidate token & logout session | Yes (Active User) |

### Administrative User Management (`/api/admin`)
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/admin/users` | List users with pagination | Yes (`ADMIN` / `USER_MANAGE`) |
| `GET` | `/api/admin/users/{user_id}` | Get detailed user metadata | Yes (`ADMIN` / `USER_MANAGE`) |
| `PATCH` | `/api/admin/users/{user_id}` | Update user role or status | Yes (`ADMIN` / `USER_MANAGE`) |
| `DELETE` | `/api/admin/users/{user_id}` | Delete user account | Yes (`ADMIN` / `USER_MANAGE`) |

### Analytics Pipeline & Execution
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/pipeline` | Execute full analytics pipeline | Yes / Scoped |
| `POST` | `/api/pipeline/run` | Execute pipeline with context & params | Yes / Scoped |

### Business Intelligence & Dashboard (`/api/dashboard`)
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/dashboard/summary` | Executive KPI summaries & metadata | Yes / Scoped |
| `GET` | `/api/dashboard/correlations` | Numeric correlation matrices | Yes / Scoped |
| `GET` | `/api/dashboard/distributions` | Distribution metrics & histograms | Yes / Scoped |
| `GET` | `/api/dashboard/categorical` | Categorical frequencies & counts | Yes / Scoped |
| `GET` | `/api/dashboard/quality` | Data quality metric scores | Yes / Scoped |

### Reports Centre (`/api/reports`)
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/reports` | List generated reports for user | Yes / Scoped |
| `GET` | `/api/reports/latest` | Retrieve latest generated report | Yes / Scoped |
| `GET` | `/api/reports/{report_id}` | Retrieve report by identifier | Yes / Scoped |

---

# Authentication & Security Details

## Headers

For protected endpoints, clients must include the Bearer token in the `Authorization` header:

```http
Authorization: Bearer <jwt_access_token>
```

## Security Invariants
1. **Server-Side Ownership Enforcement**: Requests accessing user resources (`datasets`, `pipeline_runs`, `reports`) are strictly scoped to the authenticated `user_id`. Attempting to access another user's resources returns 404 or 403 (IDOR immunity).
2. **Last-Admin Safeguard**: The system rejects administrative attempts to deactivate, demote, or delete the last remaining active system administrator.

---

# HTTP Status Codes

| Code | Meaning | Usage |
|---|---|---|
| `200` | OK | Request succeeded |
| `201` | Created | Resource (user/pipeline) created successfully |
| `400` | Bad Request | Invalid parameter or administrative guard violation |
| `401` | Unauthorized | Missing, invalid, expired, or revoked Bearer token |
| `403` | Forbidden | Authenticated user lacks required role/permission or account disabled |
| `404` | Not Found | Requested resource does not exist or belongs to another user |
| `409` | Conflict | Resource conflict (e.g., username/email already registered) |
| `422` | Unprocessable Entity | Pydantic schema validation failure |
| `500` | Internal Server Error | Unhandled server exception |

---

# Future API Enhancements (Sprint 14 Planned)

> **Status:** PLANNED / NOT YET IMPLEMENTED

The following endpoints are specified for Sprint 14 implementation:

### Asynchronous AI Job Lifecycle (`/api/ai`)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/ai/jobs/{job_id}` | Poll background AI generation job status (`PENDING`, `GENERATING`, `READY`, `FAILED`) |
| `POST` | `/api/ai/jobs/retry/{job_id}` | Retry a failed AI generation job |

### Data Cleaning Governance & Preview (`/api/cleaning`)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/cleaning/preview` | Generate cleaning impact assessment without destructive modification |
| `GET` | `/api/cleaning/lineage/{dataset_id}` | Retrieve provenance metadata and transformation lineage |

### Report Exports (`/api/reports/{id}/export`)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/reports/{id}/export/text` | Stream text report artifact |
| `GET` | `/api/reports/{id}/export/pdf` | Stream structured PDF report artifact |

---

# Current API Status

| Item | Status |
|------|--------|
| REST API Layer | ✅ Stable |
| FastAPI Server | ✅ Operational |
| Authentication Subsystem | ✅ Complete (v13.0.0) |
| Role-Based Access Control | ✅ Complete (v13.0.0) |
| Admin User Management API | ✅ Complete (v13.0.0) |
| Resource Ownership & IDOR Defense | ✅ Complete (v13.0.0) |
| Swagger UI & ReDoc | ✅ Operational |
| OpenAPI 3.1 Spec | ✅ Generated |
| Automated Integration Tests | ✅ 329 Passed |

---

**API Version:** **v13.0.0**