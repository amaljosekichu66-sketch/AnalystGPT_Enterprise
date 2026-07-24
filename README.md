<p align="center">
  <img src="docs/image/banner.png" alt="AnalystGPT Enterprise Banner" width="100%">
</p>

<h1 align="center">AnalystGPT Enterprise</h1>

<p align="center">
  <em>Enterprise‑grade analytics pipeline with REST API, Business Intelligence, and a modern Streamlit frontend.</em>
</p>

<p align="center">
  <a href="https://www.python.org/downloads/release/python-311/"><img src="https://img.shields.io/badge/python-3.11-blue" alt="Python Version"></a>
  <a href="#testing"><img src="https://img.shields.io/badge/tests-passing-brightgreen" alt="Tests"></a>
  <a href="#architecture"><img src="https://img.shields.io/badge/architecture-layered%20%2B%20REST%20%2B%20BI-success" alt="Architecture"></a>
  <a href="#database-layer"><img src="https://img.shields.io/badge/database-SQLite%20%2B%20PostgreSQL-blueviolet" alt="Database"></a>
  <a href="#rest-api"><img src="https://img.shields.io/badge/REST%20API-FastAPI%20%2F%20OpenAPI%203.1-informational" alt="REST API"></a>
  <a href="#business-intelligence"><img src="https://img.shields.io/badge/Power%20BI-integration-yellow" alt="Power BI"></a>
  <a href="#frontend"><img src="https://img.shields.io/badge/frontend-Streamlit%20%2B%20React--ready-orange" alt="Frontend"></a>
  <a href="#version"><img src="https://img.shields.io/badge/version-v10.0.0-blue" alt="Version"></a>
  <a href="#license"><img src="https://img.shields.io/badge/license-MIT-green" alt="License"></a>
</p>

---

## Project Status

| Version | Sprint | Status |
|---------|---------|--------|
| **v10.0.0** | Sprint 10 – Enterprise Streamlit Frontend | ✅ Complete |
| **Current Focus** | Sprint 11 – AI Insight Engine | 🔄 In Development |
| **Architecture** | Enterprise Layered + REST + BI + Frontend | ✅ Stable |
| **Tests** | All passing | ✅ |
| **Documentation** | Extensive | ✅ |

---

## Quick Links

- [Overview](#overview)
- [Screenshots](#screenshots)
- [Why AnalystGPT?](#why-analystgpt)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Architecture](#architecture)
- [Installation & Running](#installation--running)
- [REST API](#rest-api)
- [Roadmap](#roadmap)
- [Repository Statistics](#repository-statistics)
- [Skills Demonstrated](#skills-demonstrated)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

AnalystGPT Enterprise is a fully functional analytics platform built with enterprise software engineering principles. It ingests datasets, cleans and validates data, runs statistical analytics, generates structured reports, persists execution metadata, exposes everything through a REST API (OpenAPI/Swagger), integrates with Power BI, and now provides an interactive web interface powered by Streamlit. The architecture is modular, layered, and ready for AI enhancements and cloud deployment.

> **Current Release:** v10.0.0 (Sprint 10 completed – Enterprise Streamlit Frontend)  
> **Status:** Active development – ready for AI Insight Engine (Sprint 11)

---

## Screenshots

> *Placeholder images – replace with actual screenshots once captured.  
> You can place them in `docs/images/` and update the links below.*

| Dashboard | Upload |
|-----------|--------|
| ![](docs/images/dashboard.png) | ![](docs/images/upload.png) |

| Reports | About |
|---------|-------|
| ![](docs/images/reports.png) | ![](docs/images/about.png) |

---

## Why AnalystGPT?

AnalystGPT Enterprise was developed as a long‑term software engineering project to demonstrate how a production‑style analytics platform can evolve through disciplined architecture, modular design, automated testing, and incremental releases.

The repository showcases not only analytics functionality but also engineering practices commonly found in enterprise software systems:

- Clean separation of concerns
- Database‑agnostic persistence
- Service‑oriented architecture
- Comprehensive testing strategies
- Architecture Decision Records for every major decision
- Documentation‑as‑code approach

---

## Key Features

| Category | Features |
|----------|----------|
| **Data Pipeline** | Upload (CSV/Excel/JSON) → Cleaning → Quality → Analytics → Reporting (executive summaries, KPIs) |
| **Persistence** | SQLite (development) and PostgreSQL (production) via a unified abstraction layer; repository pattern for all database operations |
| **REST API** | FastAPI with dependency injection, Pydantic models, global exception handlers, OpenAPI 3.1, and Swagger UI |
| **Business Intelligence** | Dedicated DashboardService with Power‑BI‑ready endpoints (summary, statistics, correlation, distribution, categorical) |
| **Frontend** | Enterprise Streamlit application with dashboard, upload interface, reports centre, about page, reusable components, session management, and centralised navigation |
| **Testing & Quality** | Automated pytest suite, integration tests, stress testing, performance validation on datasets up to 1M rows |
| **Engineering** | Layered architecture, SOLID principles, ADRs, comprehensive documentation, CI/CD ready |

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

## Architecture

The system follows a strict layered architecture. For a detailed diagram and explanations, see [ARCHITECTURE.md](docs/project/ARCHITECTURE.md).

**Simplified high‑level flow:**

```text
Streamlit UI
      │
FastAPI REST API
      │
Application Layer
      │
Business Modules (Upload, Cleaning, Quality, Analytics, Reporting)
      │
Persistence Layer
      │
SQLite / PostgreSQL
```

Key principles: layered separation, repository pattern, database abstraction, dependency injection, service‑oriented frontend, and React‑ready architecture.

📖 For the complete architecture, design rationale, and dependency diagrams, see ARCHITECTURE.md.

Installation & Running
Prerequisites
Python 3.11

Git

(Optional) PostgreSQL server for production mode

Installation
bash
git clone https://github.com/amaljosekichu66-sketch/AnalystGPT_Enterprise.git
cd AnalystGPT_Enterprise
pip install -r requirements.txt
Running the CLI (Command‑Line Pipeline)
bash
python main.py
Running the REST API
bash
python -m uvicorn src.api.server:app --reload
Then open http://127.0.0.1:8000/docs for Swagger UI.

Running the Streamlit Frontend
bash
streamlit run src/frontend/streamlit_app.py
The frontend will be available at http://localhost:8501.

Running Tests
bash
pytest
REST API
The REST API is built with FastAPI and exposes the analytics pipeline through HTTP endpoints.

Method	Endpoint	Description
GET	/	API root info
GET	/api/v1/health	Health check
GET	/api/v1/version	Version info
POST	/api/v1/pipeline	Execute the full pipeline and return results
OpenAPI 3.1 specification: /openapi.json

Swagger UI: http://127.0.0.1:8000/docs

ReDoc: http://127.0.0.1:8000/redoc

The API layer is thin: it validates requests, delegates to the Application Layer, and serializes responses. It contains no business logic.

Power BI endpoints are also available under /powerbi/ – see the full API documentation.

Roadmap
Sprint	Focus	Status
1–5.5	Core analytics pipeline (Upload → Reporting)	✅ Complete
6	SQLite Persistence	✅ Complete
7	Database Abstraction & PostgreSQL	✅ Complete
8	REST API	✅ Complete
9	Power BI Integration	✅ Complete
10	Enterprise Streamlit Frontend	✅ Complete
11	AI Insight Engine – executive summaries, recommendations, narratives	🔄 Current
12	Production Deployment – Docker, CI/CD, cloud, monitoring	🔄 Planned
Full roadmap and detailed sprint plans are available in ROADMAP.md.

Repository Statistics
🏗 10 completed engineering sprints

📦 15+ major modules

📄 40+ documentation files

🧭 20+ Architecture Decision Records

🗄 SQLite & PostgreSQL support

🌐 FastAPI REST API with OpenAPI 3.1

📊 Streamlit Frontend

📈 Power BI Integration

🧪 Automated test suite with integration, stress, and large dataset validation

Skills Demonstrated
Enterprise Software Architecture

Python

FastAPI

Streamlit

Pandas

PostgreSQL

SQLite

REST API Design

OpenAPI

Dependency Injection

Repository Pattern

SOLID Principles

Data Engineering

Business Intelligence

Automated Testing

Engineering Documentation (ADRs, guides)

Documentation
Extensive documentation is maintained in the docs/ directory:

PROJECT_STATE.md – Current project status, health dashboard, version.

ARCHITECTURE.md – Detailed system architecture, layers, modules, dependencies.

ROADMAP.md – Long‑term engineering direction and release planning.

PROJECT_JOURNAL.md – Engineering journey per sprint (decisions, lessons, milestones).

CHANGELOG.md – Release notes.

ADR/ – Architecture Decision Records.

Engineering manuals – Playbook, operating manual, code review checklist, definition of done.

Sprint reports – Detailed sprint reports and retrospectives.

Contributing
Contributions are welcome! Please read our Contribution Guidelines and follow the Code Review Checklist. All changes should include tests and documentation updates.

License
This project is licensed under the MIT License – see the LICENSE file for details.

Author
Amal Jose Kichu
Principal Software Architect & Developer
GitHub · LinkedIn

<p align="center"> Built with Python • FastAPI • Streamlit • PostgreSQL • SQLite<br> Designed using Enterprise Software Engineering Principles </p><p align="center"> ⭐ If you found this project interesting, consider starring the repository.<br> For detailed engineering documentation, visit the <a href="docs/">docs/</a> directory. </p>
Built with engineering discipline, tested with rigour, and documented for enterprise.
AnalystGPT Enterprise – turning data into decisions.