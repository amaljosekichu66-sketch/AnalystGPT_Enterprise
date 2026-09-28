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
| **Runtime** | Bare-metal Python 3.11 virtualenv (`venv`) | GitHub Actions Ubuntu 22.04 Runner | Docker / Docker Compose |
| **Database** | SQLite (`analystgpt.db`) or local Postgres | SQLite (test job) / PostgreSQL (compose job) | PostgreSQL 16 Alpine container |
| **Logging** | Console stdout (`LOG_TO_FILE=false`) | Console stdout (`LOG_TO_FILE=false`) | Console stdout or persistent rotating files |
| **Networking** | `localhost:8000` / `localhost:8501` | Host loopback & Docker bridge | Docker bridge network (`analystgpt_network`) |
| **AI / LLM** | Local Ollama instance (`localhost:11434`) | Fallback mode (mock / non-blocking) | Local/Remote Ollama or external LLM |

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
* **Image:** `postgres:16-alpine`
* **Internal Port:** `5432`
* **Host Port:** **Unmapped by default.** PostgreSQL is deliberately kept private to `analystgpt_network` to prevent accidental host exposure or security compromise.
* **Healthcheck:** `pg_isready -U postgres -d analystgpt`
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

All configuration is environment-driven via `.env` (with reference schema in [`.env.example`](../../.env.example)):

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
# become mandatory at startup.
APP_ENVIRONMENT=production

# Signing key for access tokens. The built-in default is published in this repository,
# so anyone can forge a token for any user and role with it. Startup FAILS if this is
# left unset while APP_ENVIRONMENT is not 'development'. Generate one with:
#   python -c "import secrets; print(secrets.token_urlsafe(48))"
AUTH_SECRET_KEY=

# Token signing algorithm and lifetime
AUTH_ALGORITHM=HS256
AUTH_ACCESS_TOKEN_EXPIRE_MINUTES=60
AUTH_PASSWORD_MIN_LENGTH=8

# Bootstrap administrator identity
AUTH_DEFAULT_ADMIN_USERNAME=admin
AUTH_DEFAULT_ADMIN_EMAIL=admin@analystgpt.enterprise

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
> `ADMIN_DEFAULT_EMAIL`. **None of those exists.** Setting them has no effect — in
> particular, setting `JWT_SECRET_KEY` would leave `AUTH_SECRET_KEY` at the published
> development default while appearing to have secured the deployment.
>
> The PBKDF2 iteration count is **not** configurable by environment: it is fixed at 600,000
> in `src/identity/password_hasher.py`. There is no default-admin *password* variable; the
> bootstrap administrator is created through the normal registration path.
>
> ⚠️ **Known configuration drift.** `docker-compose.yml` still pins
> `AI_CONTEXT_WINDOW: 4096` and `AI_TIMEOUT: 120`, which `src/core/config.py` and
> `.env.example` have since raised to `8192` and `600`. A container started from Compose
> without an overriding `.env` therefore runs the undersized window that silently truncates
> the prompt's analytical integrity rules. Set both explicitly in `.env` until Compose is
> updated. Similarly, `src/core/config.py` defaults `POSTGRES_PORT` to `5433` while
> `.env.example` and the Compose service use `5432`.

### Secret Security Rules
* Never commit `.env` to Git (enforced via `.gitignore` and `.dockerignore`).
* Use `.env.example` strictly as a sanitized template.
* In container environments, pass secrets via environment variables or container secret managers.

---

## 6. AI Engine & Ollama Connectivity

* **Optional / Non-Blocking Architecture:** In accordance with Sprint 11 architecture, AI insight generation is strictly post-persistence and non-blocking. If Ollama is offline, unreachable, or unconfigured, the analytics, cleaning, persistence, and reporting pipelines complete successfully with `ai_report = None`.
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

1. **`quality`:** Blocking validation using Flake8 syntax checks, Flake8 style gates, Black formatting (`black --check src tests`), isort import sorting (`isort --check src tests`), and Mypy static typing (`mypy src`). As of v14.0.0 the formatters cover **all** of `src/` and `tests/`; only non-source trees are excluded. All four gates pass — see PROJECT_STATE.md, section *Executed Validation*.
2. **`test`:** Runs the full pytest regression suite in a Python 3.11 runner — **714 passing**, with the 15 `integration`-marked tests deselected.
3. **`docker-build`:** Validates BuildKit compilation of `api`, `frontend`, and `cli` image targets.
4. **`compose-validation`:** Validates `docker compose config`.
5. **`compose-integration`:** Starts the full Compose stack, waits for healthchecks, validates live HTTP responses on `/api/health` and `/_stcore/health`, and ensures clean teardown (`docker compose down -v`).

---

## 8. Operational Procedures

### 8.1 Starting the Stack
```bash
# 1. Copy environment template
cp .env.example .env

# 2. Configure production password in .env
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
* [x] **Server-Side Data Isolation:** Scoped queries prevent IDOR across tenants.
* [x] **JWT Token Security:** Signed tokens with server-side revocation tracking.
