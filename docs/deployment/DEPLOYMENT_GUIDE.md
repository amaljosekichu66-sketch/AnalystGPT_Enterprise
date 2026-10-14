# AnalystGPT Enterprise — Production Deployment Guide

## 1. Overview & Architecture

AnalystGPT Enterprise is an enterprise-grade analytics, business intelligence, and AI-driven data intelligence platform. The deployment architecture isolates presentation, compute/API, and persistence layers into containerized services coordinated via Docker Compose.

```
                             ┌──────────────────────────────────────┐
                             │             USER BROWSER             │
                             └───────────┬──────────────────────┬───┘
                                         │                      │
                                HTTP:8501│                      │HTTP:8000
                                         ▼                      ▼
┌────────────────────────────────────────┼──────────────────────┼────────────────────────────────────────┐
│ DOCKER BRIDGE NETWORK: analystgpt_network                     │                                        │
│                                        │                      │                                        │
│                   ┌────────────────────┴───┐                  │                                        │
│                   │   analystgpt-frontend  │                  │                                        │
│                   │  (Streamlit UI :8501)  │                  │                                        │
│                   └────────────┬───────────┘                  │                                        │
│                                │                              │                                        │
│                                │ HTTP: http://api:8000        │                                        │
│                                ▼                              │                                        │
│                   ┌────────────────────────┐◄─────────────────┘                                        │
│                   │     analystgpt-api     │                                                           │
│                   │  (FastAPI REST :8000)  │                                                           │
│                   └────────────┬───────────┘                                                           │
│                                │                                                                       │
│                                │ PostgreSQL Protocol (port 5432)                                      │
│                                ▼                                                                       │
│                   ┌────────────────────────┐                                                           │
│                   │   analystgpt-postgres  │                                                           │
│                   │ (PostgreSQL 16 Engine) │                                                           │
│                   └────────────┬───────────┘                                                           │
│                                │                                                                       │
│                                ▼                                                                       │
│                    analystgpt_postgres_data (Persistent Named Volume)                                  │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Environments: Local Development vs CI vs Production

| Dimension | Local Development | Continuous Integration (CI) | Production Deployment |
|---|---|---|---|
| **Runtime** | Bare-metal Python 3.11 virtualenv (`venv`) | GitHub Actions `ubuntu-latest` runners | Docker / Docker Compose |
| **Database** | SQLite (`analystgpt.db`) or local Postgres | SQLite (`test` job) / PostgreSQL 16 service (`postgres` job) / PostgreSQL in Compose (`compose-integration` job) | PostgreSQL 16 Alpine container |
| **Logging** | Console stdout (`LOG_TO_FILE=false`) | Console stdout (`LOG_TO_FILE=false`) | Console stdout or persistent rotating files |
| **Networking** | `localhost:8000` / `localhost:8501` | Host loopback & Docker bridge | Docker bridge network (`analystgpt_network`) |
| **AI / LLM** | Local Ollama instance (`localhost:11434`) | No Ollama: live-LLM tests are `integration`-marked and deselected; unit tests use fakes | Local/Remote Ollama (`LLM_PROVIDER=ollama` is the only provider today) |

---

## 3. Services & Docker Image Architecture

The deployment uses a unified multi-stage [`Dockerfile`](../../Dockerfile) with named target stages:

### 3.1 API Service (`analystgpt-api`)
* **Stage:** `target: api`
* **Entrypoint:** `uvicorn src.api.server:app --host 0.0.0.0 --port 8000`
* **Host Port:** `8000`
* **Healthcheck:** `curl -f http://localhost:8000/api/health`
* **User:** Non-root `appuser` (UID 1000, GID 1000)

### 3.2 Frontend Service (`analystgpt-frontend`)
* **Stage:** `target: frontend`
* **Entrypoint:** `streamlit run src/frontend/streamlit_app.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true`
* **Host Port:** `8501`
* **Healthcheck:** `curl -f http://localhost:8501/_stcore/health`
* **Routing:** Communicates with API over internal DNS `API_BASE_URL: http://api:8000`

### 3.3 PostgreSQL Service (`analystgpt-postgres`)
* **Image:** `postgres:16-alpine`, pinned by digest
* **Internal Port:** `5432`
* **Host Port:** **Unmapped by default.** PostgreSQL is deliberately kept private to `analystgpt_network` to prevent accidental host exposure or security compromise.
* **Healthcheck:** `pg_isready -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DATABASE:-analystgpt}`
* **Storage:** Mounted to named volume `analystgpt_postgres_data:/var/lib/postgresql/data`

---

## 4. Health Endpoints & Dependency Ordering

### Canonical Endpoints
* **REST API:** `http://localhost:8000/api/health` $\to$ Returns HTTP 200 `{"status": "healthy", "success": true}`
* **Streamlit UI:** `http://localhost:8501/_stcore/health` $\to$ Returns HTTP 200 `ok`

### Startup Sequence
1. `postgres` container initializes and performs internal schema readiness.
2. `postgres` healthcheck transitions to `healthy`.
3. `api` container launches (`depends_on: postgres: condition: service_healthy`) and connects to PostgreSQL.
4. `api` healthcheck transitions to `healthy`.
5. `frontend` container launches (`depends_on: api: condition: service_healthy`) and connects to `http://api:8000`.

---

## 5. Configuration & Secret Management

All configuration is environment-driven via `.env` (with reference schema in [`.env.example`](../../.env.example)).
`.env.example` is the production template: its `AUTH_SECRET_KEY` is a `CHANGE_ME` placeholder
that the API refuses, so it will not start as-is. For local development use
`cp .env.development.example .env` instead (SQLite, `APP_ENVIRONMENT=development`, loopback only).

The settings that matter for a deployment:

```bash
# Core Networking
API_PORT=8000
FRONTEND_PORT=8501

# Database Configuration
DATABASE_ENGINE=postgresql
POSTGRES_DATABASE=analystgpt
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_production_password

# Production Logging
LOG_LEVEL=INFO
LOG_TO_FILE=false
LOG_FILE_PATH=logs/analystgpt.log
LOG_MAX_BYTES=10485760
LOG_BACKUP_COUNT=5

# Deployment Environment & Security
# Any value other than 'development' is treated as deployed, and the guards below
# become mandatory at startup. UNSET also means production: development must be
# chosen explicitly. docker-compose.yml sets APP_ENVIRONMENT=production itself.
APP_ENVIRONMENT=production

# Signing key for access tokens (HS256). REQUIRED: the API refuses to start if it is
# missing, empty, shorter than 32 bytes, the CHANGE_ME placeholder from .env.example, or
# the built-in development key (which is published in this repository). docker-compose.yml has no fallback and refuses to
# start without it. Generate one with:
#   python -c "import secrets; print(secrets.token_urlsafe(48))"
AUTH_SECRET_KEY=

# Token signing algorithm and lifetime
AUTH_ALGORITHM=HS256
AUTH_ACCESS_TOKEN_EXPIRE_MINUTES=60
AUTH_PASSWORD_MIN_LENGTH=8

# Unauthenticated X-User-Id / X-User-Name / X-User-Role headers are a COMPLETE
# authentication bypass. Defaults to false and CANNOT be enabled unless
# APP_ENVIRONMENT=development - startup refuses the combination.
AUTH_ALLOW_HEADER_IDENTITY=false

# Explicit CORS allow-list. Never use '*': combined with credentials, Starlette
# reflects the caller's Origin instead, which trusts every site.
CORS_ALLOWED_ORIGINS=https://analytics.example.com

# AI / Ollama Configuration
LLM_PROVIDER=ollama
OLLAMA_HOST=http://host.docker.internal:11434
OLLAMA_MODEL=gemma3:4b
AI_CONTEXT_WINDOW=8192
AI_TIMEOUT=600
```

> **Variable names matter.** These are the names `src/core/config.py` actually reads.
> Earlier revisions of this guide listed `JWT_SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`,
> `PBKDF2_ITERATIONS`, `ADMIN_DEFAULT_USERNAME`, `ADMIN_DEFAULT_PASSWORD` and
> `ADMIN_DEFAULT_EMAIL`. **None of those exists.** Nor do `OPENAI_API_KEY`, `GEMINI_API_KEY`,
> `CLAUDE_API_KEY` or `AUTH_DEFAULT_ADMIN_*` any longer: they were removed from
> `src/core/config.py` during the pre-Sprint-15 hardening (nothing read them). Setting them has no effect — in
> particular, setting `JWT_SECRET_KEY` would leave `AUTH_SECRET_KEY` at the published
> development default while appearing to have secured the deployment.
>
> The PBKDF2 iteration count is **not** configurable by environment: it is fixed at 600,000
> in `src/identity/password_hasher.py`. There is no default-admin *password* variable.
>
> **Bootstrap administrator.** Public registration can no longer choose a role (it could
> previously create an ADMIN — B-01). Create the first administrator from a shell on the
> deployment; the password is read from `ADMIN_BOOTSTRAP_PASSWORD` or prompted, never printed:
>
> ```bash
> docker compose exec api python scripts/create_admin.py --username admin --email admin@example.com
> ```
>
> Self-registration (`POST /api/auth/register`) always creates a `VIEWER`; an administrator
> promotes users with `PATCH /api/admin/users/{id}`. Set `AUTH_SELF_REGISTRATION_ENABLED=false`
> to turn self-registration off.
>
> **Configuration defaults (checked 2026-10-14).** `docker-compose.yml` now defaults
> `AI_CONTEXT_WINDOW` to `8192` and `AI_TIMEOUT` to `600`, matching `src/core/config.py` and
> `.env.example` (it previously pinned `4096` / `120`). One difference remains:
> `src/core/config.py` defaults `POSTGRES_PORT` to `5433` for bare-metal runs, while
> `.env.example` and the Compose service set `5432`.

### Secret Security Rules
* Never commit `.env` to Git (enforced via `.gitignore` and `.dockerignore`).
* Use `.env.example` strictly as a sanitized template.
* In container environments, pass secrets via environment variables or container secret managers.

---

## 6. AI Engine & Ollama Connectivity

* **Asynchronous, Non-Blocking Architecture:** AI insight generation runs as a persisted background job after the deterministic pipeline has been persisted (ADR-025). `POST /api/pipeline` returns the analytics result plus `ai_job_id` / `ai_job_status`; the job moves `PENDING → GENERATING → READY / FAILED / CANCELLED`. If Ollama is offline, unreachable, or unconfigured, the pipeline still succeeds and the job ends `FAILED` (retry with `POST /api/ai/jobs/{id}/retry`). Jobs persist their input and resume after an API restart.
* **Host Connectivity:** In Docker Compose, `extra_hosts: ["host.docker.internal:host-gateway"]` allows the API container to communicate with host-running Ollama servers (`http://host.docker.internal:11434`).

---

## 7. Continuous Integration (CI/CD)

The GitHub Actions workflow ([`.github/workflows/ci.yml`](../../.github/workflows/ci.yml))
executes automatically on pushes and pull requests targeting `main`:

> Note: because the workflow triggers only on `main`, **it does not run on feature
> branches**. Branch work is validated locally until merge — see
> `docs/development/DEVELOPER_COMMANDS.md`.
>
> ℹ️ CI provisions no Ollama service. The live-LLM modules carry the `integration` marker and
> `pyproject.toml` sets `addopts = -m "not integration"`, so they are deselected there and
> the `test` job is deterministic.

The workflow has **7 jobs**:

1. **`quality`:** Blocking Flake8 syntax and style gates, Black (`black --check src tests main.py`), isort (`isort --check src tests main.py`), Mypy (`mypy src main.py`) and the vulture dead-code gate (`vulture src main.py scripts vulture_whitelist.py --min-confidence 60`). The formatters cover **all** of `src/` and `tests/`; only non-source trees are excluded.
2. **`security`:** gitleaks secret scan over the full history, `pip-audit` against `requirements.lock`, bandit failing on HIGH findings, and a reviewed-B608 count gate (57 reviewed findings; a new or removed one fails until it is reviewed).
3. **`test`:** Runs the default pytest suite (**1,242 tests**; the 16 live-Ollama `integration` tests are deselected, and the PostgreSQL ones run in the `postgres` job) with coverage and a gate of `fail_under = 85`.
4. **`postgres`:** Runs the PostgreSQL schema and concurrency integration tests against a PostgreSQL 16 service container; a skipped test fails the job.
5. **`docker-build`:** Builds the `api`, `frontend` and `cli` image targets and scans them and the pinned PostgreSQL image with Trivy (fails on fixable HIGH/CRITICAL).
6. **`compose-validation`:** Validates `docker compose config` with ephemeral secrets.
7. **`compose-integration`:** Starts the full Compose stack, waits for healthchecks, validates live HTTP responses on `/api/health` and `/_stcore/health`, and tears down (`docker compose down -v`).

---

## 8. Operational Procedures

### 8.1 Starting the Stack
```bash
# 1. Copy environment template
cp .env.example .env

# 2. Configure POSTGRES_PASSWORD AND AUTH_SECRET_KEY in .env
#    (compose refuses to start without either, and the API refuses the
#    template's CHANGE_ME placeholder key)
# nano .env

# 3. Build and launch services in detached mode
docker compose up -d --build

# 4. Verify running services and health status
docker compose ps
```

### 8.2 Viewing Logs
```bash
# View aggregated stream
docker compose logs -f

# View specific service logs
docker compose logs -f api
docker compose logs -f frontend
docker compose logs -f postgres
```

### 8.3 Stopping & Teardown
```bash
# Stop services (preserves database volumes)
docker compose down

# Stop services and remove named volumes (destructive reset)
docker compose down -v
```

### 8.4 Database Backups
```bash
# Create logical backup from running postgres container
docker compose exec -T postgres pg_dump -U postgres analystgpt > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup to running postgres container
cat backup_20260814_120000.sql | docker compose exec -T postgres psql -U postgres -d analystgpt
```

---

## 9. Security & Hardening Checklist

* [x] **Non-Root Execution:** Application processes execute as `appuser` (UID 1000).
* [x] **Context Minimization:** `.dockerignore` prevents `.git`, `.env`, and bytecode ingestion.
* [x] **Database Isolation:** PostgreSQL is inaccessible from public host ports.
* [x] **Bounded Log Growth:** `RotatingFileHandler` deterministically caps log disk usage.
* [x] **Dependency Sanitization:** `requirements.txt` normalized to standard UTF-8.
* [x] **PBKDF2 Password Hashing:** 600,000 iterations for secure password derivation.
* [x] **Server-Side Data Isolation:** Per-user isolation enforced and tested on every resource route; no endpoint accepts a server file path.
* [x] **Token Security:** HS256-signed tokens; revocations persisted in `revoked_tokens` and honoured after restarts.

## 10. Pre-Sprint-15 hardening notes

- **Required secrets.** `docker compose` refuses to start without `AUTH_SECRET_KEY` (≥ 32 bytes)
  and `POSTGRES_PASSWORD`. Neither has a fallback.
- **Exposure.** The API and frontend are published on `127.0.0.1` by default
  (`API_BIND_ADDRESS`, `FRONTEND_BIND_ADDRESS`). Expose them through a TLS-terminating reverse
  proxy rather than binding `0.0.0.0`. `/docs`, `/redoc` and `/openapi.json` are disabled outside
  development unless `API_DOCS_ENABLED=true`.
- **Single API process.** Login lockout state is stored in the database (`login_failures`), but
  the per-client rate limits, the per-user job cap and the last-admin guard lock keep their state
  in the API process. The image runs one uvicorn worker; running several would require moving
  that state to a shared store.
- **Dependencies.** The image installs `requirements.lock` with `pip --require-hashes`, from a
  digest-pinned base. After changing `requirements.txt`, regenerate the lock with the command in
  its header (it resolves inside the same base image). Development and CI install
  `requirements-dev.txt`.
- **Audit trail.** Security events are stored in `audit_events` (`GET /api/admin/audit-events`)
  and logged at WARNING with the prefix `SECURITY_ALERT` — alert on that prefix in your log
  pipeline.
