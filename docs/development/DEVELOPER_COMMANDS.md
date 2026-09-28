# AnalystGPT Enterprise — Developer & Operational Command Guide

This guide provides the authoritative, exact copy-paste-ready commands required to configure, operate, test, validate, and develop AnalystGPT Enterprise.

---

## 0. Platform Note & Path Convention

> This guide was originally written for macOS only: every command hard-coded the absolute
> path `/Users/amaljose/AnalystGPT_Enterprise` and activated the virtualenv with
> `source venv/bin/activate`. The repository is also worked on under Windows, where neither
> runs. The commands below are therefore path-neutral, and Windows PowerShell equivalents
> are given in section 11.

Set `PROJECT_ROOT` once per shell; every later `cd "$PROJECT_ROOT"` then resolves correctly
regardless of where the repository is cloned.

**macOS / Linux (bash / zsh):**

```bash
export PROJECT_ROOT="$HOME/AnalystGPT_Enterprise"   # adjust to your clone location
```

**Windows (PowerShell):**

```powershell
$env:PROJECT_ROOT = "C:\Users\<you>\AnalystGPT_Enterprise"   # adjust to your clone location
```

Activation differs by platform:

| Platform | Activate virtualenv |
|---|---|
| macOS / Linux | `source venv/bin/activate` |
| Windows PowerShell | `.\venv\Scripts\Activate.ps1` |
| Windows cmd.exe | `venv\Scripts\activate.bat` |
| Git Bash on Windows | `source venv/Scripts/activate` |

---

## 1. Environment Setup

### 1.1 Prerequisites
- Python 3.11+
- Virtual environment (`venv`)
- (Optional for AI insights) Local Ollama server with `gemma3:4b`

### 1.2 Initial Setup & Virtual Environment
```bash
# Navigate to project root
cd "$PROJECT_ROOT"

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
Executes the comprehensive automated test suite across unit, integration, and security layers.
**695** test functions are defined across **118** modules, collecting to **729** cases.

> **Expected result:** `714 passed, 15 deselected, 1 warning in ~119s`, 0 failures,
> 0 collection errors.
>
> The 15 deselected tests carry the `integration` marker and need a live Ollama server with
> `gemma3:4b`. `pyproject.toml` sets `addopts = -ra -m "not integration"`, so the default run
> is deterministic on any machine. Exercise the live LLM path with:
>
> ```bash
> ollama pull gemma3:4b
> pytest -m integration
> ```
>
> The single warning is a third-party `anyio` deprecation surfaced through
> `starlette.testclient`.
>
> If you see a `matplotlib` import error, your virtualenv predates it being declared — run
> `pip install -r requirements.txt`.

```bash
cd "$PROJECT_ROOT"
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
cd "$PROJECT_ROOT"
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
cd "$PROJECT_ROOT"
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
cd "$PROJECT_ROOT"
source venv/bin/activate

# 1. System Health & Metadata
curl -s http://127.0.0.1:8000/ | jq .
curl -s http://127.0.0.1:8000/api/health | jq .
curl -s http://127.0.0.1:8000/api/version | jq .

# 2. Authenticate User (Replace with active credentials)
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "<USERNAME>", "password": "<PASSWORD>"}' | jq -r '.access_token')

# 3. Execute Pipeline on Sample Data
curl -s -X POST http://127.0.0.1:8000/api/pipeline \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"input_path": "sample_data/customer_data.csv"}' | jq .

# 4. List User Reports
curl -s http://127.0.0.1:8000/api/reports \
  -H "Authorization: Bearer $TOKEN" | jq .

# 5. Download & Validate Latest TXT Report
curl -s -w "\nHTTP Status: %{http_code}\n" -o downloaded_report.txt \
  http://127.0.0.1:8000/api/reports/latest/export/text \
  -H "Authorization: Bearer $TOKEN"
ls -lh downloaded_report.txt
head -n 15 downloaded_report.txt

# 6. Download & Validate Latest PDF Report
curl -s -w "\nHTTP Status: %{http_code}\n" -o downloaded_report.pdf \
  http://127.0.0.1:8000/api/reports/latest/export/pdf \
  -H "Authorization: Bearer $TOKEN"
ls -lh downloaded_report.pdf
head -c 8 downloaded_report.pdf; echo ""

# 7. Specific Report Export (Replace <REPORT_ID> with integer ID)
curl -s -o report_specific.txt http://127.0.0.1:8000/api/reports/<REPORT_ID>/export/text -H "Authorization: Bearer $TOKEN"
curl -s -o report_specific.pdf http://127.0.0.1:8000/api/reports/<REPORT_ID>/export/pdf -H "Authorization: Bearer $TOKEN"
```

---

## 3. Code Quality & Static Analysis Commands

Run the full static code quality pipeline before any code submission:

```bash
cd "$PROJECT_ROOT"
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
cd "$PROJECT_ROOT"
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
cd "$PROJECT_ROOT"
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


---

## 11. Windows PowerShell Equivalents

The commands throughout this guide use bash syntax. Under Windows PowerShell, `export` is not a
command, `source` does not exist, and `VAR=value cmd` inline prefixes are a parse error. Use the
equivalents below.

### 11.1 Session Setup (equivalent to sections 0 and 1.2)

```powershell
$env:PROJECT_ROOT = "C:\Users\<you>\AnalystGPT_Enterprise"
Set-Location $env:PROJECT_ROOT
.\venv\Scripts\Activate.ps1

$env:PYTHONPATH     = (Get-Location).Path
$env:DATABASE_ENGINE = "sqlite"
$env:LOG_TO_FILE     = "false"
```

### 11.2 Terminal Workflow (equivalent to section 2)

```powershell
# Terminal 1 - full test suite
pytest -q

# Full suite WITH a captured UTF-8 log (see 11.3 before using `>` yourself)
.\scripts\run_tests.ps1

# Terminal 2 - FastAPI backend
uvicorn src.api.server:app --host 127.0.0.1 --port 8000 --reload

# Terminal 3 - Streamlit frontend
python -m streamlit run src/frontend/streamlit_app.py
```

### 11.3 Quality Gates (equivalent to section 3)

```powershell
flake8 src tests
black --check src tests
isort --check src tests
mypy src
```

> These four gates are exactly what CI's `quality` job runs, and all four pass at
> v14.0.0: flake8 0, black 341 files unchanged, isort clean, mypy clean over 210 source files.
>
> `black` and `isort` cover **all** of `src/` and `tests/`; only non-source trees are excluded.
> (Until the Sprint 14 stabilization pass, `pyproject.toml` excluded `tests/` and 15 of 17
> `src/` packages, so a clean result meant almost nothing.)
>
> ⚠️ **On Windows, run these with `PYTHONUTF8=1`.** 35 files legitimately contain characters
> outside cp1252; without it `isort` cannot read them, **skips them silently, and still exits
> 0** — so a file can drift while the check reports clean. `scripts/lint.ps1` sets it.
> `PYTHONIOENCODING` is *not* sufficient: it affects stdio only, not the locale encoding used
> to read files.

### 11.4 Syntax Translation Reference

| bash | PowerShell |
|---|---|
| `export VAR=value` | `$env:VAR = "value"` |
| `source venv/bin/activate` | `.\venv\Scripts\Activate.ps1` |
| `DATABASE_ENGINE=sqlite pytest -q` | `$env:DATABASE_ENGINE="sqlite"; pytest -q` |
| `export PYTHONPATH="$(pwd)"` | `$env:PYTHONPATH = (Get-Location).Path` |
| `cmd1 && cmd2` | `cmd1; if ($?) { cmd2 }` |
| `curl -s URL` | `curl.exe -s URL` (PowerShell aliases `curl` to `Invoke-WebRequest`) |

---

## 12. Capturing Test Output (PowerShell)

### 12.1 Use the helper script

```powershell
.\scripts\run_tests.ps1                      # default suite -> test-results\pytest-<timestamp>.md
.\scripts\run_tests.ps1 -Integration         # also run live-Ollama / live-API tests
.\scripts\run_tests.ps1 -Verbose_            # -v instead of -q (test node ids in the log)
```

### 12.2 Why not `pytest ... > out.md 2>&1`

Three problems, all of which were present in the historical `full_pytest_output.md`
and `FULL_TEST_OUTPUT.md` captures:

| Problem | Effect | Correct form |
|---|---|---|
| `>` / `Tee-Object` default to UTF-16LE | Log is unreadable to `grep`, `git diff`, editor search | `\| Out-File -Encoding utf8` |
| `2>&1` on a native `.exe` | Streamlit's harmless stderr warning is wrapped in a `NativeCommandError` block that looks like a crash at the top of the log | redirect stderr separately, or drop it |
| `-s` (no capture) | Every application log line is interleaved into the report; files reach ~2 MB | omit `-s`; pytest shows captured output for failures only |

Captured logs are gitignored (`*_TEST_OUTPUT.md`, `pytest_output*.md`,
`test-results/`) because they contain absolute developer paths and are
regenerated on every run.

### 12.3 Integration markers

Tests that need live external infrastructure are marked `integration` and are
**deselected by default** via `addopts` in `pyproject.toml`:

```powershell
pytest -q                      # default: integration tests excluded
pytest -m integration          # only the live-infrastructure tests
pytest -m "integration or not integration"   # everything
```

`tests/ai/test_ollama_connection.py` is the current member of that group: it
drives a live Ollama server, so its result depends on model warmth and machine
load rather than on application code.
