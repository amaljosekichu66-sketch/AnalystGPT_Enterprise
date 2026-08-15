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

The deployment uses a unified multi-stage [`Dockerfile`](file:///Users/amaljose/AnalystGPT_Enterprise/Dockerfile) with named target stages:

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

All configuration is environment-driven via [`.env`](file:///Users/amaljose/AnalystGPT_Enterprise/.env) (with reference schema in [`.env.example`](file:///Users/amaljose/AnalystGPT_Enterprise/.env.example)):

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

# Identity & Authentication Configuration
JWT_SECRET_KEY=change_this_to_a_secure_random_64_character_hex_secret_in_production
ACCESS_TOKEN_EXPIRE_MINUTES=60
PBKDF2_ITERATIONS=600000
ADMIN_DEFAULT_USERNAME=admin
ADMIN_DEFAULT_PASSWORD=ChangeMeAdmin123!
ADMIN_DEFAULT_EMAIL=admin@analystgpt.enterprise

# AI / Ollama Configuration
LLM_PROVIDER=ollama
OLLAMA_HOST=http://host.docker.internal:11434
OLLAMA_MODEL=gemma3:4b
```

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

The GitHub Actions workflow ([`.github/workflows/ci.yml`](file:///Users/amaljose/AnalystGPT_Enterprise/.github/workflows/ci.yml)) executes automatically on pushes and pull requests targeting `main`:
1. **`quality`:** Blocking validation using Flake8 syntax checks, Flake8 style gates, Black formatting (`black --check`), isort import sorting (`isort --check`), and Mypy static typing (`mypy src`).
2. **`test`:** Runs full pytest regression suite (329 tests) in Python 3.11 runner.
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
