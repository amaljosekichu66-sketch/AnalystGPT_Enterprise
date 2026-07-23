# AnalystGPT Enterprise

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Tests](https://img.shields.io/badge/Tests-98%20Passed-brightgreen)
![Architecture](https://img.shields.io/badge/Architecture-Layered%20%2B%20REST%20API%20%2B%20Power%20BI-success)
![Database](https://img.shields.io/badge/Database-SQLite%20%2B%20PostgreSQL-blue)
![REST API](https://img.shields.io/badge/REST%20API-FastAPI%20%2F%20OpenAPI%203.1-blueviolet)
![Power BI](https://img.shields.io/badge/Power%20BI-Integration-yellow)
![License](https://img.shields.io/badge/License-MIT-green)
![Version](https://img.shields.io/badge/Version-v9.0.0-blue)

> **Enterprise-Grade Analytics Platform**
>
> AnalystGPT Enterprise is a modular analytics platform built using enterprise software engineering principles. The project demonstrates how a production-quality analytics application can be designed through clean architecture, layered architecture, automated testing, documentation, and scalable software engineering practices.

---

## Quick Links

- [Project Overview](#project-overview)
- [Project Goals](#project-goals)
- [Features](#features)
- [Architecture](#architecture-principles)
- [Installation](#installation)
- [Running the Project](#running-the-project)
- [REST API](#rest-api)
- [Business Intelligence API](#business-intelligence-api)
- [Testing](#running-tests)
- [Documentation](#documentation)
- [Roadmap](#project-roadmap)

---

# Project Overview

AnalystGPT Enterprise is an enterprise-grade analytics platform designed to
demonstrate modern software engineering practices while solving a complete
analytics workflow.

The platform processes datasets through a modular pipeline that performs:

- Data ingestion
- Data cleaning
- Data quality assessment
- Statistical analytics
- Business report generation
- Persistent execution tracking
- Database-agnostic persistence
- **Business Intelligence integration**
- **Power BI dashboard generation**

The persistence layer now supports multiple relational database engines
through a unified abstraction layer, enabling interchangeable SQLite
and PostgreSQL backends without changing business logic.

The platform is now accessible through a **REST API** built with **FastAPI**,
providing interactive documentation via **Swagger UI** and a standard
**OpenAPI 3.1** specification. The REST API Layer delegates all operations
to the Application Layer, preserving the separation of concerns and
layered architecture established in previous sprints.

**Sprint 9 extends the platform with a dedicated Business Intelligence
Integration Layer that exposes dashboard-ready analytics through
Power BI-compatible REST endpoints.**

The Business Intelligence layer remains independent from the business
modules and communicates only with the Application Layer, preserving
the existing layered architecture.

The project is intentionally developed sprint-by-sprint to simulate the
evolution of a production enterprise application.

---

# Why This Project?

AnalystGPT Enterprise was built as a long-term software engineering project
to progressively implement enterprise architecture, scalable analytics
workflows, automated testing, database persistence, and production-ready
engineering practices through iterative sprint-based development.

The project demonstrates the evolution from a simple analytics application
into an enterprise platform through incremental architectural improvements,
showing how clean interfaces and abstraction layers enable adaptability
and extensibility.

The project now demonstrates enterprise backend development,
database abstraction, REST API engineering, and Business
Intelligence integration suitable for external analytics platforms.

---

# Project Goals

- Demonstrate enterprise software engineering through practical implementation
- Build production-quality analytics architecture with clear separation of concerns
- Practice scalable system design and modular component development
- Maintain high automated test coverage across all modules
- Incrementally evolve through engineering sprints with stable, tested releases
- Apply SOLID principles and enterprise patterns consistently
- Create maintainable, extensible, and well-documented software
- **Build reusable Business Intelligence services**
- **Deliver dashboard-ready APIs**
- **Support enterprise reporting platforms**

---

# Key Engineering Highlights

- Enterprise layered architecture
- Repository Pattern
- Manager-Orchestrator Pattern
- Database Abstraction Layer
- DatabaseConnection abstraction
- ConnectionFactory
- Cross-database repository architecture
- SQLite and PostgreSQL support
- REST API Layer with FastAPI
- OpenAPI 3.1 specification
- Swagger UI interactive documentation
- Dependency Injection for application lifecycle
- Pydantic request validation and response serialization
- Global Exception Handling with consistent error responses
- Service-Oriented Architecture
- Automated testing (98 tests)
- Performance validation up to 1,000,000 rows
- Modular business pipeline
- Architecture Decision Records (ADRs)
- Comprehensive engineering documentation
- **Business Intelligence Layer**
- **DashboardService**
- **Power BI Integration**
- **Dashboard Response Models**
- **Dashboard APIs**
- **Performance Benchmark Framework**
- **Stress Testing Framework**
- **REST Dashboard Endpoints**

---

# Current Status

| Item | Status |
|------|--------|
| **Current Version** | **v9.0.0** |
| **Development Status** | 🟢 Active Development |
| **Current Sprint** | ✅ Sprint 9 – Power BI Integration Complete |
| **Architecture** | 🟢 Enterprise Layered Architecture + REST API + Business Intelligence Layer |
| **Application Layer** | ✅ Stable |
| **Persistence Layer** | ✅ Stable |
| **Database Abstraction Layer** | ✅ Stable |
| **Repository Layer** | ✅ Stable |
| **REST API Layer** | ✅ Stable |
| **Business Intelligence Layer** | ✅ Stable |
| **Power BI Integration** | ✅ Complete |
| **Dashboard Services** | ✅ Complete |
| **Performance Benchmarking** | ✅ Complete |
| **OpenAPI** | ✅ Operational |
| **Swagger** | ✅ Operational |
| **Automated Tests** | ✅ 98 / 98 Passed |
| **Performance Validation** | ✅ Completed |
| **Next Sprint** | 🚀 Sprint 10 – Streamlit Frontend |

---

# Features

## Completed Modules

- ✅ Upload Module
- ✅ Cleaning Module
- ✅ Quality Module
- ✅ Analytics Module
- ✅ Reporting Module
- ✅ Application Layer
- ✅ Persistence Layer
- ✅ Database Abstraction Layer
- ✅ SQLite Support
- ✅ PostgreSQL Support
- ✅ Repository Layer
- ✅ REST API Layer
- ✅ FastAPI Server
- ✅ Root Endpoint
- ✅ Health Endpoint
- ✅ Version Endpoint
- ✅ Pipeline Endpoint
- ✅ Swagger UI
- ✅ OpenAPI 3.1
- ✅ API Models
- ✅ Global Exception Handlers
- ✅ **Business Intelligence Layer**
- ✅ **DashboardService**
- ✅ **Power BI Integration**
- ✅ **Dashboard Models**
- ✅ **Dashboard Endpoints**
- ✅ **Performance Benchmark Framework**
- ✅ **Stress Testing Framework**

## Upcoming Modules

- ⏳ Streamlit Application
- ⏳ AI Insights
- ⏳ Production Deployment

---

# Architecture Principles

The architecture emphasizes maintainability, extensibility, and clear separation
of responsibilities so that new capabilities can be introduced with minimal
impact on existing business modules.

The project follows modern enterprise engineering practices:

- Layered Architecture
- Repository Pattern
- Manager-Orchestrator Pattern
- Separation of Concerns (SoC)
- SOLID Principles
- Stable Module Contracts
- High Cohesion
- Low Coupling
- Automated Testing
- Dependency Injection
- Database Abstraction
- Interface-driven Design
- REST API Design
- API-first Architecture
- Service-oriented Architecture
- **Business Intelligence Layer**
- **Integration Layer**
- **Dashboard Service Pattern**

---

# Enterprise Architecture

```text
Power BI / Browser / REST Client
                │
                ▼
          FastAPI Server
                │
                ▼
           API Routes
                │
                ▼
        Dependency Injection
                │
                ▼
         Application.run()
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
                  ▲         ▲
                  │         │
        SQLiteConnection PostgreSQLConnection
                  │         │
               sqlite3   psycopg
                  │         │
                  └────┬────┘
                       │
                       ▼
              Repository Layer
                       │
                       ▼
              PipelineResult
                       │
                       ▼
          (DashboardService)
                       │
                       ▼
         Power BI Models
                       │
                       ▼
         REST API Response
```

Business modules remain independent of the underlying database engine, the REST API Layer, and the Business Intelligence Layer, communicating only through stable contracts and abstractions.

---

# Technology Stack

| Category | Technologies |
|----------|--------------|
| Language | Python 3.11 |
| Data Processing | Pandas |
| Database | SQLite, PostgreSQL |
| Database Drivers | sqlite3, psycopg 3 |
| REST API | FastAPI |
| Validation | Pydantic |
| API Documentation | OpenAPI 3.1, Swagger UI |
| **Business Intelligence** | **Power BI** |
| **Performance** | **Benchmark Framework** |
| Testing | Pytest |
| Architecture | Layered Architecture, Repository Pattern, Manager-Orchestrator Pattern |
| Version Control | Git, GitHub |
| Development | Visual Studio Code |
| Documentation | Markdown |

---

# Current Capabilities

AnalystGPT Enterprise currently supports:

- Multi-format dataset ingestion (CSV, Excel, JSON)
- Enterprise data cleaning pipeline
- Automated data quality assessment
- Statistical analytics
- Business report generation
- Database-agnostic metadata persistence
- SQLite and PostgreSQL support
- Automatic database engine selection
- Repository abstraction
- End-to-end automated testing
- Performance validation up to 1,000,000 rows
- REST API execution
- Interactive Swagger UI
- OpenAPI specification
- Typed request validation
- Typed response serialization
- API integration testing
- Dependency Injection
- Global exception handling
- **Power BI dashboard endpoints**
- **Dashboard-ready JSON**
- **Summary APIs**
- **Statistics APIs**
- **Correlation APIs**
- **Distribution APIs**
- **Categorical APIs**
- **Business Intelligence integration**
- **Performance benchmarking**
- **Stress testing**

---

# REST API

AnalystGPT Enterprise exposes its analytics pipeline through a REST API built with FastAPI.

**Available endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API root information |
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/version` | Version information |
| POST | `/api/v1/pipeline` | Execute the analytics pipeline |

**Interactive documentation:**

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

**OpenAPI specification:**

- `http://127.0.0.1:8000/openapi.json`

The REST API Layer contains no business logic, delegates all operations to the Application Layer through dependency injection, and provides enterprise-grade error handling and request validation.

---

# Business Intelligence API

Sprint 9 introduces a dedicated Business Intelligence Layer that exposes
dashboard-ready analytics through Power BI-compatible REST endpoints.

Available endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/powerbi/dashboard` | GET | Complete dashboard payload |
| `/powerbi/summary` | GET | Executive summary |
| `/powerbi/statistics` | GET | Descriptive statistics |
| `/powerbi/correlation` | GET | Correlation analysis |
| `/powerbi/distribution` | GET | Distribution analysis |
| `/powerbi/categorical` | GET | Categorical analysis |
| `/powerbi/report` | GET | Full report |
| `/powerbi/pipeline` | POST | Execute pipeline and return dashboard data |

All endpoints are documented in OpenAPI 3.1 and accessible via Swagger UI.

---

# Repository Structure

```text
src/
├── api/
│   ├── server.py
│   ├── routes/
│   ├── models/
│   ├── dependencies/
│   └── exceptions/
├── application/
├── upload/
├── cleaning/
├── quality/
├── analytics/
├── reporting/
├── persistence/
├── database/
│   ├── database_connection.py
│   ├── sqlite_connection.py
│   ├── postgresql_connection.py
│   ├── connection_factory.py
│   ├── database_manager.py
│   ├── schema_manager.py
│   └── repositories/
├── integrations/
│   └── powerbi/
│       ├── dashboard_service.py
│       └── powerbi_models.py
├── core/
└── ... (tests, docs, performance, sample_data)

performance/
├── benchmark_results.md
├── stress_test.py
├── benchmark_results.csv
└── performance_report.md
```

---

# Future Vision

The long-term objective is to evolve AnalystGPT Enterprise from a modular
analytics pipeline into a complete enterprise analytics platform supporting
relational databases, REST APIs, dashboards, AI-assisted insights, and
production deployment.

With the database abstraction layer, REST API layer, and Business Intelligence
layer in place, future work now focuses on delivering **Streamlit frontend**,
**AI-assisted insights**, and **cloud deployment infrastructure**.

Each sprint builds upon stable architectural foundations while preserving
backward compatibility and maintainable module contracts.

---

# Project Roadmap

| Sprint | Status |
|---------|--------|
| Sprint 1 – Upload | ✅ Complete |
| Sprint 2 – Cleaning | ✅ Complete |
| Sprint 3 – Quality | ✅ Complete |
| Sprint 4 – Analytics | ✅ Complete |
| Sprint 5 – Reporting | ✅ Complete |
| Sprint 5.5 – Architecture Refactor | ✅ Complete |
| Sprint 6 – SQLite Persistence | ✅ Complete |
| Sprint 7 – PostgreSQL Integration | ✅ Complete |
| Sprint 8 – REST API | ✅ Complete |
| **Sprint 9 – Power BI Integration** | ✅ **Complete** |
| **Sprint 10 – Streamlit Frontend** | 🚀 **Next** |
| Sprint 11 – AI Insights | Planned |
| Sprint 12 – Production Deployment | Planned |

---

# Testing Status

| Validation | Status |
|-----------|--------|
| Unit Tests | ✅ 98 / 98 Passed |
| Integration Tests | ✅ Passed |
| REST API Integration Tests | ✅ Passed |
| Power BI Endpoint Tests | ✅ Passed |
| Dashboard Tests | ✅ Passed |
| Summary Tests | ✅ Passed |
| Statistics Tests | ✅ Passed |
| Correlation Tests | ✅ Passed |
| Distribution Tests | ✅ Passed |
| Categorical Tests | ✅ Passed |
| Swagger Validation | ✅ Passed |
| OpenAPI Validation | ✅ Passed |
| Performance Validation | ✅ Passed |
| Sample Dataset | ✅ Passed |
| Large Dataset (100,000 rows) | ✅ Passed |
| Stress Dataset (1,000,000 rows) | ✅ Passed |
| SQLite Runtime Validation | ✅ Passed |
| Database Abstraction Validation | ✅ Passed |

---

# Installation

```bash
git clone https://github.com/amaljosekichu66-sketch/AnalystGPT_Enterprise.git

cd AnalystGPT_Enterprise

pip install -r requirements.txt
```

For SQLite, no additional setup is required.

For PostgreSQL, configure the database connection settings in
`src/core/config.py` before switching `DATABASE_ENGINE` to `"postgresql"`.

---

# Running the Project

## Command-Line Interface

```bash
python main.py
```

## REST API Server

```bash
python -m uvicorn src.api.server:app --reload
```

Swagger UI: `http://127.0.0.1:8000/docs`  
OpenAPI: `http://127.0.0.1:8000/openapi.json`

## Power BI Endpoints

The following endpoints are available for Power BI consumption:

```
GET /powerbi/dashboard
GET /powerbi/summary
GET /powerbi/statistics
GET /powerbi/correlation
GET /powerbi/distribution
GET /powerbi/categorical
GET /powerbi/report
POST /powerbi/pipeline
```

---

# Running Tests

```bash
python -m pytest
```

Current Result:

```
98 tests passed
0 failures
0 warnings
```

---

# Documentation

Detailed engineering documentation is available under:

- `docs/project/`
- `docs/engineering/`
- `docs/adr/`
- `docs/sprints/`
- `docs/api/`
- `performance/` (benchmark results and performance reports)

These documents describe the project's architecture, engineering decisions,
release history, and development roadmap, including:

- Architecture Design
- Architecture Decision Records
- Engineering Standards
- Sprint Reports
- Project State
- Release History
- API Reference
- API Testing Guide
- **Performance Documentation**
- **Benchmark Reports**
- **Business Intelligence Documentation**
- **Power BI Integration Guide**

---

# License

This project is licensed under the MIT License.

---

For detailed architecture, engineering standards, sprint history,
and design decisions, see the documentation under `docs/`.

AnalystGPT Enterprise continues to evolve through incremental,
well-tested engineering sprints.

**Current Release:** v9.0.0

**Next Milestone:** Sprint 10 – Streamlit Frontend