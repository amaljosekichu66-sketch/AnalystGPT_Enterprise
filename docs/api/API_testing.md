# AnalystGPT Enterprise API Testing Guide

> **Purpose**
>
> This document explains how to validate and test the
> AnalystGPT Enterprise REST API.
>
> It covers local execution, Swagger UI, OpenAPI validation,
> automated testing, security validation, and endpoint verification.
>
> Current Version: **v13.0.0**

---

# API Testing Overview

The REST API is tested through multiple validation layers to ensure
correctness, reliability, and security.

Testing includes:

- Automated endpoint testing
- Authentication & JWT token verification
- Role-Based Access Control (RBAC) & 401/403 authorization checks
- Server-side IDOR prevention and data isolation checks
- Request & Response validation
- OpenAPI & Swagger UI validation
- Integration testing
- End-to-end pipeline execution
- Live API verification

---

# Prerequisites

Before testing, ensure the following are installed:

- Python 3.11+
- FastAPI & Uvicorn
- Pytest & HTTPX

Install project dependencies:

```bash
pip install -r requirements.txt
```

---

# Starting the API

Run the development server:

```bash
python -m uvicorn src.api.server:app --reload
```

Expected output:

```text
INFO:     Uvicorn running on http://127.0.0.1:8000
```

---

# Interactive Documentation

- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`
- **OpenAPI Spec**: `http://127.0.0.1:8000/openapi.json`

---

# Automated Test Execution

### Run All API and Security Tests

```bash
PYTHONPATH=. pytest tests/api/ tests/identity/ -v
```

### Run Frontend Authentication Tests

```bash
PYTHONPATH=. pytest tests/frontend/test_frontend_auth.py -v
```

### Run Full Repository Test Suite

```bash
DATABASE_ENGINE=sqlite pytest -q
```

Expected Output:

```text
535 passed in ~50s
0 failed
0 errors
```

---

# Key Test Modules

| Test Module | Coverage |
|---|---|
| `tests/api/test_auth_routes.py` | Registration, login, profile (`/me`), logout, credential validation |
| `tests/api/test_admin_routes.py` | Admin user listing, role/status mutation, last-admin safeguards |
| `tests/api/test_report_export_api.py` | Text and PDF export endpoints, ownership enforcement, IDOR checks |
| `tests/api/test_auth_dependencies.py` | Bearer token extraction, UserContext resolution, RBAC injection |
| `tests/identity/test_token_service.py` | HMAC-SHA256 token issuance, claims validation, expiration |
| `tests/identity/test_password_hasher.py` | PBKDF2-HMAC-SHA256 hashing, salting, constant-time verification |
| `tests/identity/test_rbac.py` | Declarative RBAC matrices (`ADMIN`, `ANALYST`, `VIEWER`), 401/403 errors |
| `tests/identity/test_resource_ownership.py` | Server-side query scoping, IDOR immunity, cross-user isolation |
| `tests/identity/test_audit.py` | Structured audit logging & credential sanitization |
| `tests/reporting/` | Multi-page PDF generation, text report serialization, lineage isolation |
| `tests/frontend/` | Streamlit views, session state management, tenant cleanup, export buttons |

---

# Summary & Status

| Validation | Status |
|---|---|
| REST API Endpoints | ✅ Passed |
| Authentication & Tokens | ✅ Passed |
| RBAC Authorization | ✅ Passed |
| Server-Side Data Isolation | ✅ Passed |
| Admin Safety Guards | ✅ Passed |
| Swagger & OpenAPI Spec | ✅ Passed |
| Full Automated Test Suite | ✅ **535 / 535 Passed** |

---

**API Version:** **v14.0.0**

**Testing Status:** **535 / 535 Automated Tests Passed (0 Regressions)**