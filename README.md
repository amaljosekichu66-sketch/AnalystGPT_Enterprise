```markdown
# AnalystGPT Enterprise

![Python Version](https://img.shields.io/badge/python-3.11-blue)
![Tests](https://img.shields.io/badge/tests-passing-brightgreen)
![Architecture](https://img.shields.io/badge/architecture-layered%20%2B%20REST%20%2B%20BI-success)
![Database](https://img.shields.io/badge/database-SQLite%20%2B%20PostgreSQL-blueviolet)
![REST API](https://img.shields.io/badge/REST%20API-FastAPI%20%2F%20OpenAPI%203.1-informational)
![Power BI](https://img.shields.io/badge/Power%20BI-integration-yellow)
![Frontend](https://img.shields.io/badge/frontend-Streamlit%20%2B%20React--ready-orange)
![Version](https://img.shields.io/badge/version-v10.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)

> **Enterprise‑grade analytics pipeline with a modern UI, REST API, and business intelligence ready for production.**

AnalystGPT Enterprise is a fully functional analytics platform built from the ground up with enterprise software engineering principles. It ingests datasets, cleans and validates data, runs statistical analytics, generates structured reports, persists execution metadata, exposes everything through a REST API (with OpenAPI/Swagger), integrates with Power BI, and now provides an interactive web interface powered by Streamlit. The architecture is modular, layered, and ready for AI enhancements and cloud deployment.

---

## 📌 Quick Links

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Modules](#implemented-modules)
- [REST API](#rest-api)
- [Frontend](#streamlit-frontend)
- [Database & Persistence](#database-layer)
- [Business Intelligence](#business-intelligence)
- [Testing & Performance](#testing--performance)
- [Roadmap](#roadmap)
- [Installation & Running](#installation--running)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

AnalystGPT Enterprise solves a common problem: **turning raw data into actionable business insights** through a repeatable, auditable, and scalable analytics pipeline. It is designed for data engineers, analysts, and software architects who need a production‑ready reference implementation of a modern analytics platform.

The project demonstrates:

- **Clean architecture** with strict separation of concerns
- **Database abstraction** supporting SQLite and PostgreSQL
- **REST API** with OpenAPI 3.1 and Swagger UI
- **Business Intelligence** integration (Power BI)
- **Enterprise frontend** built with Streamlit and designed for React migration
- **Comprehensive testing** (unit, integration, stress, large dataset)
- **Engineering governance** via ADRs and documentation standards

> **Current Release:** v10.0.0 (Sprint 10 completed – Enterprise Streamlit Frontend)  
> **Status:** Active development – ready for AI Insight Engine (Sprint 11)

---

## Key Features

| Category | Features |
|----------|----------|
| **Data Pipeline** | Upload (CSV/Excel/JSON) → Cleaning (columns, text, missing, duplicates) → Quality (completeness, validity, consistency, outliers) → Analytics (descriptive, correlation, distribution) → Reporting (executive summaries, KPIs) |
| **Persistence** | SQLite (development) and PostgreSQL (production) via a unified abstraction layer; repository pattern for all database operations |
| **REST API** | FastAPI with dependency injection, Pydantic models, global exception handlers, OpenAPI 3.1, and Swagger UI |
| **Business Intelligence** | Dedicated DashboardService with Power‑BI‑ready endpoints (summary, statistics, correlation, distribution, categorical) |
| **Frontend** | Enterprise Streamlit application with dashboard, upload interface, reports centre, about page, reusable components, session management, and centralised navigation |
| **Testing & Quality** | Automated pytest suite, integration tests, stress testing, performance validation on datasets up to 1M rows |
| **Engineering** | Layered architecture, SOLID principles, ADRs, comprehensive documentation, CI/CD ready |

---

## Architecture

The system follows a strict layered architecture, where each layer has a single responsibility and communicates only through stable contracts.

```
Browser / Power BI / REST Client
               │
               ▼
         Streamlit Frontend
               │
               ▼
     Views → Components → Services
               │
               ▼
         FastAPI REST API
               │
               ▼
        Application Layer (Application.run())
               │
       ┌───────┼───────┐
       │       │       │
       ▼       ▼       ▼
  Upload → Cleaning → Quality
                       │
                       ▼
               AnalyticsManager
                       │
                       ▼
               ReportingManager
                       │
                       ▼
              PersistenceManager
                       │
                       ▼
              DatabaseManager
                       │
                       ▼
              ConnectionFactory
                       │
                       ▼
              DatabaseConnection
                   ▲        ▲
                   │        │
         SQLiteConnection  PostgreSQLConnection
                   │        │
                sqlite3    psycopg
                   │        │
                   └───┬────┘
                       │
                       ▼
               Repository Layer
                       │
                       ▼
               PipelineResult
                       │
                       ▼
              DashboardService
                       │
                       ▼
              Power BI Models
```

**Key architectural principles:**

- **Layered separation:** Business logic is isolated in the Application Layer and business modules; persistence, API, and UI layers are independent.
- **Repository Pattern:** All SQL is encapsulated in repositories, making database engines interchangeable.
- **Database Abstraction:** `DatabaseConnection` and `ConnectionFactory` allow runtime switching between SQLite and PostgreSQL.
- **Dependency Injection:** The REST API uses DI to manage Application lifecycle.
- **Service‑Oriented Frontend:** Streamlit views delegate to service classes that call the REST API; no business logic in the UI.
- **React‑ready:** The frontend architecture is designed to allow future replacement of Streamlit with React without backend changes.

---

## Technology Stack

| Category | Technologies |
|----------|--------------|
| **Language** | Python 3.11 |
| **Data Processing** | Pandas |
| **Web Framework** | FastAPI, Uvicorn |
| **Validation** | Pydantic |
| **API Docs** | OpenAPI 3.1, Swagger UI, ReDoc |
| **Frontend** | Streamlit, Plotly |
| **Database** | SQLite (built‑in), PostgreSQL (psycopg 3) |
| **Testing** | Pytest, pytest‑cov, HTTPX |
| **Performance** | Custom stress and benchmark framework |
| **Version Control** | Git, GitHub |
| **Documentation** | Markdown, ADRs |

---

## Project Structure

```
AnalystGPT_Enterprise/
├── src/
│   ├── api/                # REST API Layer (FastAPI)
│   │   ├── server.py
│   │   ├── routes/
│   │   ├── models/
│   │   ├── dependencies/
│   │   └── exceptions/
│   ├── application/        # Application Layer & PipelineResult
│   ├── upload/             # Upload Module
│   ├── cleaning/           # Cleaning Module
│   ├── quality/            # Quality Module
│   ├── analytics/          # Analytics Module
│   ├── reporting/          # Reporting Module
│   ├── persistence/        # Persistence Manager
│   ├── database/           # Database Abstraction & Repositories
│   │   ├── database_connection.py
│   │   ├── sqlite_connection.py
│   │   ├── postgresql_connection.py
│   │   ├── connection_factory.py
│   │   ├── database_manager.py
│   │   ├── schema_manager.py
│   │   └── repositories/
│   ├── integrations/       # External integrations
│   │   └── powerbi/        # Power BI Dashboard Service & Models
│   ├── frontend/           # Streamlit Frontend
│   │   ├── streamlit_app.py
│   │   ├── views/
│   │   ├── components/
│   │   ├── services/
│   │   ├── config/
│   │   ├── theme/
│   │   └── assets/
│   └── core/               # Shared infrastructure (config, logging, exceptions)
├── tests/                  # Pytest test suite
├── docs/                   # Architecture, ADRs, engineering manuals, sprint reports
├── performance/            # Benchmark results, stress test scripts
├── sample_data/            # Example datasets
├── reports/                # Generated reports (output)
├── main.py                 # CLI entry point
├── requirements.txt
└── README.md
```

---

## Implemented Modules

| Module | Purpose | Status | Sprint |
|--------|---------|--------|--------|
| **Upload** | Import CSV/Excel/JSON into Pandas DataFrame | ✅ Stable | 1 |
| **Cleaning** | Column, text, missing values, duplicates, data types | ✅ Stable | 2 |
| **Quality** | Completeness, validity, consistency, uniqueness, outliers | ✅ Stable | 3 |
| **Analytics** | Descriptive, numerical, categorical, correlation, distribution | ✅ Stable | 4 |
| **Reporting** | Executive summary, KPIs, structured reports, text export | ✅ Stable | 5 |
| **Application Layer** | Orchestration, PipelineResult, thin main.py | ✅ Stable | 5.5 |
| **Persistence** | Execution metadata, repositories, SQLite | ✅ Stable | 6 |
| **Database Abstraction** | ConnectionFactory, PostgreSQL support, dialect‑aware schemas | ✅ Stable | 7 |
| **REST API** | FastAPI, OpenAPI, Swagger, dependency injection | ✅ Stable | 8 |
| **Power BI Integration** | DashboardService, dashboard endpoints, benchmarking | ✅ Stable | 9 |
| **Streamlit Frontend** | Dashboard, upload, reports, about, components, services, session | ✅ Stable | 10 |
| **AI Insight Engine** | Executive summary generator, recommendations, narratives | 🔄 Planned | 11 |
| **Production Deployment** | Docker, CI/CD, monitoring | 🔄 Planned | 12 |

---

## REST API

The REST API is built with FastAPI and exposes the analytics pipeline through HTTP endpoints. All endpoints are documented interactively via Swagger UI and ReDoc.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API root info |
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/version` | Version info |
| POST | `/api/v1/pipeline` | Execute the full pipeline and return results |

- **OpenAPI 3.1** specification available at `/openapi.json`
- **Swagger UI:** `http://127.0.0.1:8000/docs`
- **ReDoc:** `http://127.0.0.1:8000/redoc`

The API layer is thin: it validates requests, delegates to the Application Layer, and serializes responses. It contains no business logic.

---

## Streamlit Frontend

The enterprise frontend is built with **Streamlit** and provides:

- **Dashboard** – KPI cards, pipeline status, dataset preview, quick actions.
- **Upload** – Drag‑and‑drop or file browser, with validation and preview.
- **Reports Centre** – List of generated reports with metadata and export.
- **About** – Project overview, tech stack, architecture summary.

### Frontend Architecture

- **Views** – Page‑level components (dashboard_page.py, upload_page.py, etc.)
- **Components** – Reusable UI elements (metrics, charts, tables, navigation)
- **Services** – API client and session manager that handle all backend communication
- **Session State** – Stores presentation state only; no business data.
- **Navigation** – Centralised sidebar navigation.

The frontend is designed to be **React‑ready**: all business logic remains in the backend, and the UI can be replaced with React without changing REST API contracts or backend modules.

---

## Database Layer

The persistence layer abstracts database engines via:

- **`DatabaseConnection`** – Abstract interface for all database operations.
- **`ConnectionFactory`** – Chooses the engine at runtime based on configuration.
- **`SchemaManager`** – Generates SQL schemas with dialect‑specific syntax.
- **Repositories** – CRUD operations for pipeline runs, datasets, quality, analytics, and reports.

**Supported databases:** SQLite (default) and PostgreSQL.  
Engine can be switched via environment variable `DATABASE_ENGINE=postgresql` (with proper credentials in `config.py`).

---

## Business Intelligence

The **Business Intelligence Layer** provides Power‑BI‑ready endpoints:

| Endpoint | Description |
|----------|-------------|
| `/powerbi/dashboard` | Complete dashboard payload |
| `/powerbi/summary` | Executive summary |
| `/powerbi/statistics` | Descriptive statistics |
| `/powerbi/correlation` | Correlation matrix |
| `/powerbi/distribution` | Distribution analysis |
| `/powerbi/categorical` | Categorical summary |
| `/powerbi/report` | Full structured report |
| `/powerbi/pipeline` | Execute pipeline and return dashboard data (POST) |

All endpoints are documented in OpenAPI and can be consumed directly by Power BI or other BI tools.

---

## Testing & Performance

### Testing Strategy

- **Unit tests** – All modules covered with pytest.
- **Integration tests** – End‑to‑end pipeline execution, REST API, and Power BI endpoints.
- **Frontend validation** – Manual and automated checks for rendering, navigation, and API integration.

All tests are passing. The suite is continuously maintained as the project evolves.

### Performance Validation

The platform has been validated on datasets of varying sizes:

- **Small** – 500 rows (sample dataset)
- **Large** – 100,000 rows
- **Stress** – 1,000,000 rows

Validation includes pipeline execution, persistence (SQLite/PostgreSQL), REST API throughput, and frontend rendering. All tests passed without architectural regressions.

Performance benchmarks are documented in `performance/benchmark_results.md`.

---

## Roadmap

| Sprint | Focus | Status |
|--------|-------|--------|
| 1–5.5 | Core analytics pipeline (Upload → Reporting) | ✅ Complete |
| 6 | SQLite Persistence | ✅ Complete |
| 7 | Database Abstraction & PostgreSQL | ✅ Complete |
| 8 | REST API | ✅ Complete |
| 9 | Power BI Integration | ✅ Complete |
| 10 | **Enterprise Streamlit Frontend** | ✅ **Complete** |
| 11 | **AI Insight Engine** – executive summaries, recommendations, narratives | 🔄 Current |
| 12 | **Production Deployment** – Docker, CI/CD, cloud, monitoring | 🔄 Planned |

---

## Installation & Running

### Prerequisites

- Python 3.11
- Git
- (Optional) PostgreSQL server for production mode

### Installation

```bash
git clone https://github.com/amaljosekichu66-sketch/AnalystGPT_Enterprise.git
cd AnalystGPT_Enterprise
pip install -r requirements.txt
```

### Running the CLI (Command‑Line Pipeline)

```bash
python main.py
```

This executes the pipeline on the default dataset in `sample_data/`.

### Running the REST API

```bash
python -m uvicorn src.api.server:app --reload
```

Then open `http://127.0.0.1:8000/docs` for Swagger UI.

### Running the Streamlit Frontend

```bash
streamlit run src/frontend/streamlit_app.py
```

The frontend will be available at `http://localhost:8501`.

### Running Tests

```bash
pytest
```

---

## Documentation

Extensive documentation is maintained in the `docs/` directory:

- **`PROJECT_STATE.md`** – Current project status, health dashboard, version.
- **`ARCHITECTURE.md`** – Detailed system architecture, layers, modules, dependencies.
- **`ROADMAP.md`** – Long‑term engineering direction and release planning.
- **`PROJECT_JOURNAL.md`** – Engineering journey per sprint (decisions, lessons, milestones).
- **`CHANGELOG.md`** – Release notes.
- **`docs/adr/`** – Architecture Decision Records (e.g., DataFrame contract, REST API design, Streamlit choice).
- **`docs/engineering/`** – Engineering Playbook, Operating Manual, Code Review Checklist, Definition of Done.
- **`docs/sprints/`** – Sprint reports and retrospectives.

---

## Engineering Principles

- **Layered Architecture** – Clear separation: Frontend → API → Application → Business → Persistence.
- **SOLID** – Each module has a single responsibility; interfaces and abstractions decouple dependencies.
- **Repository Pattern** – Encapsulates all SQL; database engines can be swapped.
- **Dependency Injection** – Used in the REST API for testability and flexibility.
- **Stable Contracts** – Module inputs/outputs are typed and versioned; changes require ADR review.
- **Automated Testing** – Every feature includes unit and integration tests.
- **Documentation as Code** – ADRs, architecture docs, and journal entries evolve with the codebase.

---

## Lessons Learned

- **Start with architecture, not code** – Early design decisions (like the Application Layer) saved significant refactoring later.
- **Stable contracts enable evolution** – Business modules remained unchanged while persistence and APIs were added.
- **Database abstraction pays off** – Switching from SQLite to PostgreSQL required minimal changes.
- **Performance testing from day one** – Validating on large datasets uncovered bottlenecks early.
- **Frontend as an independent layer** – Streamlit proved to be an effective MVP, and the service‑based architecture simplifies React migration.
- **ADRs are invaluable** – They capture context and rationale for decisions, aiding future developers.

---

## Future Work

- **Sprint 11 – AI Insight Engine**  
  Generate executive summaries, business recommendations, and natural‑language narratives from analytics outputs, using a prompt‑abstraction layer to remain model‑agnostic.

- **Sprint 12 – Production Deployment**  
  Dockerize the application, set up CI/CD pipelines, implement monitoring and logging, and deploy to cloud platforms (AWS/Azure/GCP).

- **React Migration (planned Sprint 15)**  
  Replace Streamlit with React to provide a more performant and flexible UI while preserving all backend contracts.

---

## Contributing

Contributions are welcome! Please read our [Contribution Guidelines](docs/engineering/CONTRIBUTING.md) and follow the [Code Review Checklist](docs/engineering/CODE_REVIEW_CHECKLIST.md). All changes should include tests and documentation updates.

---

## License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.

---

## Author

**Amal Jose Kichu**  
Principal Software Architect & Developer  
[GitHub](https://github.com/amaljosekichu66-sketch) · [LinkedIn](https://www.linkedin.com/in/mr-amaljose)

---

**Built with engineering discipline, tested with rigour, and documented for enterprise.**  
*AnalystGPT Enterprise – turning data into decisions.*
```
 