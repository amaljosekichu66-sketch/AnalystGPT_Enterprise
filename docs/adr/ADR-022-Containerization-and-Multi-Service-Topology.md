# ADR-022 — Containerization and Multi-Service Topology

## Status

Accepted

---

## Context

AnalystGPT Enterprise has evolved across Sprints 0–11 into a comprehensive analytics platform featuring:
- Core analytics, data cleaning, and reporting engines
- Persistence layer with dual database support (SQLite and PostgreSQL)
- REST API layer powered by FastAPI and Uvicorn
- Interactive frontend dashboard built on Streamlit
- AI Insight Engine with local LLM abstraction

Deploying and operating these components reliably in production requires:
- Predictable, reproducible runtime environments
- Strict isolation of services and dependencies
- Deterministic multi-service orchestration
- Scalable networking and bounded persistent storage
- Secure non-root container execution

A bare-metal or manual virtualenv deployment is prone to environmental drift, complex dependency management, and inconsistent inter-service routing.

---

## Decision

Adopt a **Single Multi-Stage Dockerfile with Named Target Stages** coupled with a **Docker Compose Multi-Service Topology**:

### 1. Multi-Stage Dockerfile Design
A single `Dockerfile` containing target stages:
- `base`: Minimal Python 3.11-slim runtime with `curl` and non-root `appuser` (UID 1000).
- `builder`: Isolated compiler stage with `gcc` and `libpq-dev` compiling wheels to `/home/appuser/.local`.
- `runtime-base`: Slim production runtime layer combining pre-compiled packages and application source.
- `api`: Production REST API container executing `uvicorn src.api.server:app --host 0.0.0.0 --port 8000`.
- `frontend`: Production Streamlit container executing `streamlit run src/frontend/streamlit_app.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true`.
- `cli`: Batch analytics execution entrypoint running `python main.py`.

### 2. Multi-Service Docker Compose Topology
Orchestrates three core services over a private bridge network (`analystgpt_network`):
- `postgres`: PostgreSQL 16 Alpine container with `pg_isready` healthcheck and named volume `analystgpt_postgres_data`. Not exposed to host ports by default to prevent unauthorized access.
- `api`: FastAPI service depending on `postgres` (condition: `service_healthy`), mapped to host port 8000, with healthcheck on `/api/health`.
- `frontend`: Streamlit UI service depending on `api` (condition: `service_healthy`), mapped to host port 8501, configured with `API_BASE_URL: http://api:8000`, with healthcheck on `/_stcore/health`.

### 3. Persistent Volumes
- `analystgpt_postgres_data`: Database tables, indexes, and write-ahead logs.
- `analystgpt_reports_data`: Generated analytical reports.
- `analystgpt_logs_data`: Bounded rotated logs (when `LOG_TO_FILE=true`).

---

## Consequences

### Advantages
- **Reproducibility:** Eliminates host-specific dependency discrepancies.
- **Layer Caching:** Decouples dependency installation (`requirements.txt`) from source changes.
- **Minimal Image Size:** Compiler toolchains are pruned from production runtime stages.
- **Security:** Containers run as non-root `appuser` (UID 1000); PostgreSQL is protected on internal network.
- **Health-Aware Dependency Ordering:** Prevents race conditions during multi-service startup.

### Trade-offs
- Docker daemon is required on host or CI runner for container build and runtime execution.
- Inter-service networking requires internal DNS routing (`http://api:8000`) rather than `localhost`.

---

## Alternatives Considered

1. **Multiple Independent Dockerfiles (`Dockerfile.api`, `Dockerfile.frontend`):**
   * Rejected: Duplicates base layer configuration, OS updates, and dependency installation steps.
2. **Monolithic Single Container:**
   * Rejected: Conflates API and UI lifecycle, violates single responsibility principle, and complicates scaling.
3. **External Managed Database Only:**
   * Rejected: Self-contained local Compose stack is required for zero-configuration on-premise and evaluation deployments.

---

## Implementation

- [`Dockerfile`](../../Dockerfile)
- [`.dockerignore`](../../.dockerignore)
- [`docker-compose.yml`](../../docker-compose.yml)
- [`.env.example`](../../.env.example)
