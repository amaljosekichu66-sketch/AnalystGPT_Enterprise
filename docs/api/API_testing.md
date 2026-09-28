# AnalystGPT Enterprise API Testing Guide

> **Purpose**
>
> This document explains how to validate and test the
> AnalystGPT Enterprise REST API.
>
> It covers local execution, Swagger UI, OpenAPI validation,
> automated testing, security validation, and endpoint verification.
>
> Current Version: **v14.0.0** (released 2026-09-28; tag `v14.0.0`)

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
pytest -q
```

Expected output at v14.0.0:

```text
714 passed, 15 deselected, 1 warning in ~119s
```

The 15 deselected tests carry the `integration` marker and require a live Ollama server with
`gemma3:4b`. `pyproject.toml` sets `addopts = -ra -m "not integration"`, so they are excluded
by default and the suite is deterministic on any machine.

### Run the live-infrastructure tests

```bash
pytest -m integration
```

```text
15 selected  (tests/ai/test_ollama_connection.py, tests/ai/test_ollama_production_path.py)
```

The single warning is a third-party `anyio` deprecation surfaced through
`starlette.testclient`. The full accounting, including the static gates, is recorded in
PROJECT_STATE.md, section *Executed Validation*.

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

> **What the rows below represent.** Executed results at v14.0.0 (commit `d7f9eb6`). The suite
> and all four static gates were run; see PROJECT_STATE.md, section *Executed Validation*,
> for the full accounting.

| Validation | Status |
|---|---|
| REST API Endpoints | ✅ Passed |
| Authentication & Tokens | ✅ Passed |
| RBAC Authorization | ✅ Passed |
| Server-Side Data Isolation | ✅ Passed |
| Admin Safety Guards | ✅ Passed |
| Swagger & OpenAPI Spec | ✅ Passed |
| Full Automated Test Suite | ✅ **714 / 714 passing** — 729 collected, 714 passed, 0 failed, 15 deselected (`integration`), 0 collection errors |
| Static Analysis Gates | ✅ flake8 0 · black clean (341 files) · isort clean · mypy clean (210 files) |
| OpenAPI Contract Sync | ✅ 33 paths, 42 schemas — `docs/api/openapi.json` matches the live schema |

---

**Current application version:** **v14.0.0** (released 2026-09-28; tag `v14.0.0`)

**Current sprint:** Sprint 14 — Stabilization / Production Hardening (released as v14.0.0); next: Sprint 15

**Testing Status:** ✅ **Passing (executed locally).** 714 passed, 0 failed, 15 `integration`-marked tests
deselected by default. All four static gates pass. Historical totals of 535 / 531 / 529 are
superseded; see PROJECT_STATE.md, section *Executed Validation*. A passing suite is *Tested*,
not end-to-end *Verified*; establishing a trustworthy regression baseline and verifying the
core workflows through the real API/frontend path is Sprint 15 scope (ROADMAP.md).