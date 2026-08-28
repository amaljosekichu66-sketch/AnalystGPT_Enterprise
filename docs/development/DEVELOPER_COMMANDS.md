# AnalystGPT Enterprise — Developer & Operational Command Guide

This guide provides the authoritative, exact copy-paste-ready commands required to configure, operate, test, validate, and develop AnalystGPT Enterprise.

---

## 1. Environment Setup

### 1.1 Prerequisites
- Python 3.11+
- Virtual environment (`venv`)
- (Optional for AI insights) Local Ollama server with `gemma3:4b`

### 1.2 Initial Setup & Virtual Environment
```bash
# Navigate to project root
cd /Users/amaljose/AnalystGPT_Enterprise

# Activate existing virtualenv
source venv/bin/activate

# Set canonical environment variables for development
export PYTHONPATH="$(pwd)"
export DATABASE_ENGINE=sqlite
export LOG_TO_FILE=false
```

---

## 2. Multi-Terminal Operational Workflow

### Terminal 1 — Full Test Suite
Executes the comprehensive automated test suite (535 tests across unit, integration, and security layers):

```bash
cd /Users/amaljose/AnalystGPT_Enterprise
source venv/bin/activate
export PYTHONPATH="$(pwd)"
export DATABASE_ENGINE=sqlite
export LOG_TO_FILE=false

pytest -q
```

---

### Terminal 2 — FastAPI Backend
Launches the FastAPI REST API with live hot-reloading:

```bash
cd /Users/amaljose/AnalystGPT_Enterprise
source venv/bin/activate
export PYTHONPATH="$(pwd)"
export DATABASE_ENGINE=sqlite
export LOG_TO_FILE=false

uvicorn src.api.server:app --host 127.0.0.1 --port 8000 --reload
```

- **Interactive Swagger Docs**: `http://127.0.0.1:8000/docs`
- **ReDoc Documentation**: `http://127.0.0.1:8000/redoc`
- **OpenAPI Schema**: `http://127.0.0.1:8000/openapi.json`

---

### Terminal 3 — Streamlit Frontend
Starts the Streamlit user interface using the project's native bootstrap (guaranteed free of `ModuleNotFoundError: No module named 'src'`):

```bash
cd /Users/amaljose/AnalystGPT_Enterprise
source venv/bin/activate
export PYTHONPATH="$(pwd)"
export DATABASE_ENGINE=sqlite
export LOG_TO_FILE=false

streamlit run src/frontend/streamlit_app.py
```

- **Local UI Address**: `http://localhost:8501`

---

### Terminal 4 — Manual API & Report Export Validation
Independent curl commands to validate root, health, authentication, pipeline execution, report listing, and binary downloads:

```bash
cd /Users/amaljose/AnalystGPT_Enterprise
source venv/bin/activate

# 1. System Health & Metadata
curl -s http://127.0.0.1:8000/ | jq .
curl -s http://127.0.0.1:8000/api/health | jq .
curl -s http://127.0.0.1:8000/api/version | jq .

# 2. Authenticate User (Replace with active credentials)
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "<USERNAME>", "password": "<PASSWORD>"}' | jq -r '.data.token')

# 3. Execute Pipeline on Sample Data
curl -s -X POST http://127.0.0.1:8000/api/pipeline \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"input_path": "sample_data/customer_data.csv"}' | jq .

# 4. List User Reports
curl -s http://127.0.0.1:8000/reports \
  -H "Authorization: Bearer $TOKEN" | jq .

# 5. Download & Validate Latest TXT Report
curl -s -w "\nHTTP Status: %{http_code}\n" -o downloaded_report.txt \
  http://127.0.0.1:8000/reports/latest/export/text \
  -H "Authorization: Bearer $TOKEN"
ls -lh downloaded_report.txt
head -n 15 downloaded_report.txt

# 6. Download & Validate Latest PDF Report
curl -s -w "\nHTTP Status: %{http_code}\n" -o downloaded_report.pdf \
  http://127.0.0.1:8000/reports/latest/export/pdf \
  -H "Authorization: Bearer $TOKEN"
ls -lh downloaded_report.pdf
head -c 8 downloaded_report.pdf; echo ""

# 7. Specific Report Export (Replace <REPORT_ID> with integer ID)
curl -s -o report_specific.txt http://127.0.0.1:8000/reports/<REPORT_ID>/export/text -H "Authorization: Bearer $TOKEN"
curl -s -o report_specific.pdf http://127.0.0.1:8000/reports/<REPORT_ID>/export/pdf -H "Authorization: Bearer $TOKEN"
```

---

## 3. Code Quality & Static Analysis Commands

Run the full static code quality pipeline before any code submission:

```bash
cd /Users/amaljose/AnalystGPT_Enterprise
source venv/bin/activate
export PYTHONPATH="$(pwd)"

# 1. Flake8 Linting (0 violations expected)
flake8 src/ tests/

# 2. Black Code Formatting Check
black --check src/ tests/

# 3. Import Ordering Check
isort --check src/ tests/

# 4. Mypy Strict Type Checking
mypy src/

# 5. Git Diff Whitespace / Format Check
git diff --check
```

### Automatic Code Formatting (Fix Mode)
```bash
black src/ tests/
isort src/ tests/
```

---

## 4. Targeted Test Suites

Run specific test modules during feature development:

```bash
cd /Users/amaljose/AnalystGPT_Enterprise
source venv/bin/activate
export DATABASE_ENGINE=sqlite

# Report Export & Lineage Isolation Tests
pytest tests/reporting/ -v
pytest tests/api/test_report_export_api.py -v

# Identity, Authentication & RBAC Tests
pytest tests/identity/ -v
pytest tests/api/test_auth_routes.py tests/api/test_admin_routes.py -v

# Frontend & Session State Tests
pytest tests/frontend/ -v

# Data Governance & Lineage Tests
pytest tests/governance/ -v
```

---

## 5. Performance & Stress Testing Tooling

> **Note**: Performance benchmarks are standalone tools and are separated from standard unit/integration test discovery in `pyproject.toml`.

```bash
cd /Users/amaljose/AnalystGPT_Enterprise
source venv/bin/activate

# Run pipeline throughput & resource benchmark
python performance/stress_test.py
```

---

## 6. Database Operations & Diagnostics

### 6.1 Database Engine Selection
The database engine is selected via the `DATABASE_ENGINE` environment variable:
- `DATABASE_ENGINE=sqlite` (default): Uses `analystgpt.db` in repository root.
- `DATABASE_ENGINE=postgresql`: Connects to PostgreSQL host configured via `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DATABASE`, `POSTGRES_USER`, `POSTGRES_PASSWORD`.

### 6.2 Safe User Inspection (SQLite)
```bash
sqlite3 analystgpt.db "SELECT id, username, email, role, status, created_at FROM users;"
```

### 6.3 Database Integrity Check
```bash
sqlite3 analystgpt.db "PRAGMA integrity_check;"
sqlite3 analystgpt.db "PRAGMA foreign_key_check;"
```

---

## 7. Docker & Containerized Deployment

```bash
# Build and start all services (API, Streamlit, PostgreSQL)
docker compose up --build -d

# View service health
docker compose ps

# Follow logs
docker compose logs -f api
docker compose logs -f frontend

# Graceful shutdown
docker compose down
```
