# ADR-023 — Continuous Integration with GitHub Actions

## Status

Accepted

---

## Context

With the introduction of production containerization, multi-service Docker Compose topology, centralized configuration, and production logging in Sprint 12, automated verification is necessary to prevent regressions and validate build reproducibility.

The automated verification system must:
- Enforce strict Python code quality and syntax gates.
- Execute the full automated regression test suite.
- Validate multi-stage Docker image builds across all runtime targets (`api`, `frontend`, `cli`).
- Validate Docker Compose configuration and multi-service startup.
- Perform end-to-end service health checks (`postgres` $\to$ `api` $\to$ `frontend`) and live HTTP verification.
- Guarantee clean teardown of resources.

---

## Decision

Adopt **GitHub Actions** as the official continuous integration platform with a 5-job pipeline defined in [`.github/workflows/ci.yml`](file:///Users/amaljose/AnalystGPT_Enterprise/.github/workflows/ci.yml):

### 1. Job Topology
1. **`quality`:** Executes blocking Flake8 syntax checks, Flake8 style gates, Black formatting checks, isort import ordering checks, and Mypy static type analysis on Ubuntu 22.04 with Python 3.11.
2. **`test`:** Runs the full `pytest` regression suite (201 automated tests) against SQLite database engine with zero file log overhead.
3. **`docker-build`:** Uses `docker/setup-buildx-action` to build target stages `api`, `frontend`, and `cli`.
4. **`compose-validation`:** Executes `docker compose config` to validate compose schemas and service contracts.
5. **`compose-integration`:** Launches full stack with `docker compose up -d --build`, polls health states until all services report healthy, validates HTTP 200 on `/api/health` and `/_stcore/health`, and executes `docker compose down -v` under `if: always()`.

### 2. Strict Blocking Gates
All quality and test checks are blocking. Suppressions (`|| true`, `--exit-zero`) are forbidden to maintain high software quality and prevent unnoticed failures.

---

## Consequences

### Advantages
- **Automated Regression Prevention:** Every pull request and push to `main` is rigorously verified before merging.
- **Continuous Container Validation:** Resolves local development environment limitations by building and starting container stacks on standardized Linux runners.
- **Deterministic Teardown:** CI runner disks and memory are protected from dangling containers or volumes.

### Trade-offs
- CI pipeline execution requires GitHub Actions runner minutes.
- Quality tools require synchronized configuration in [`.flake8`](file:///Users/amaljose/AnalystGPT_Enterprise/.flake8) and [`pyproject.toml`](file:///Users/amaljose/AnalystGPT_Enterprise/pyproject.toml).

---

## Implementation

- [`.github/workflows/ci.yml`](file:///Users/amaljose/AnalystGPT_Enterprise/.github/workflows/ci.yml)
- [`.flake8`](file:///Users/amaljose/AnalystGPT_Enterprise/.flake8)
- [`pyproject.toml`](file:///Users/amaljose/AnalystGPT_Enterprise/pyproject.toml)
