# AnalystGPT Enterprise

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Tests](https://img.shields.io/badge/Tests-82%20Passed-brightgreen)
![Architecture](https://img.shields.io/badge/Architecture-Layered-success)
![Database](https://img.shields.io/badge/Database-SQLite%20%2B%20PostgreSQL-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Version](https://img.shields.io/badge/Version-v7.0.0-blue)

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

The persistence layer now supports multiple relational database engines
through a unified abstraction layer, enabling interchangeable SQLite
and PostgreSQL backends without changing business logic.

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

---

# Project Goals

- Demonstrate enterprise software engineering through practical implementation
- Build production-quality analytics architecture with clear separation of concerns
- Practice scalable system design and modular component development
- Maintain high automated test coverage across all modules
- Incrementally evolve through engineering sprints with stable, tested releases
- Apply SOLID principles and enterprise patterns consistently
- Create maintainable, extensible, and well-documented software

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
- Automated testing (82 tests)
- Performance validation up to 1,000,000 rows
- Modular business pipeline
- Architecture Decision Records (ADRs)
- Comprehensive engineering documentation

---

# Current Status

| Item | Status |
|------|--------|
| **Current Version** | **v7.0.0** |
| **Development Status** | 🟢 Active Development |
| **Current Sprint** | ✅ Sprint 7 – PostgreSQL Integration Complete |
| **Architecture** | 🟢 Enterprise Layered Architecture |
| **Application Layer** | ✅ Stable |
| **Persistence Layer** | ✅ Stable |
| **Database Abstraction Layer** | ✅ Stable |
| **Repository Layer** | ✅ Stable |
| **Automated Tests** | ✅ 82 / 82 Passed |
| **Performance Validation** | ✅ Completed |
| **Next Sprint** | 🚀 Sprint 8 – REST API |

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

## Upcoming Modules

- ⏳ REST API
- ⏳ Power BI Integration
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

---

# Enterprise Architecture

```text
                     main.py
                        │
                        ▼
                 Application.run()
                        │
                        ▼
                 UploadManager
                        │
                  DataFrame
                        ▼
                CleaningManager
                        │
                  DataFrame
                        ▼
                 QualityManager
                        │
                 QualityReport
                        ▼
                AnalyticsManager
                        │
               AnalyticsReport
                        ▼
                ReportingManager
                        │
               ReportingReport
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
                    ▲          ▲
                    │          │
        SQLiteConnection PostgreSQLConnection
                    │          │
                 sqlite3     psycopg
                    │          │
                    └──────────┘
                         │
                         ▼
               Repository Layer
                         │
                         ▼
                PipelineResult
```

Business modules remain independent of the underlying database engine,
communicating only through stable contracts and abstractions.

---

# Technology Stack

| Category | Technologies |
|----------|--------------|
| Language | Python 3.11 |
| Data Processing | Pandas |
| Database | SQLite, PostgreSQL |
| Database Drivers | sqlite3, psycopg 3 |
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

---

# Repository Structure

```text
src/
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
├── core/
└── ... (tests, docs, performance, sample_data)
```

---

# Future Vision

The long-term objective is to evolve AnalystGPT Enterprise from a modular
analytics pipeline into a complete enterprise analytics platform supporting
relational databases, REST APIs, dashboards, AI-assisted insights, and
production deployment.

With the database abstraction layer in place, future work can focus on
delivering REST APIs, interactive dashboards, AI-assisted insights, and
enterprise deployment infrastructure.

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
| Sprint 8 – REST API | 🚀 Next |
| Sprint 9 – Power BI | Planned |
| Sprint 10 – Streamlit | Planned |
| Sprint 11 – AI Insights | Planned |
| Sprint 12 – Production Deployment | Planned |

---

# Testing Status

| Validation | Status |
|-----------|--------|
| Unit Tests | ✅ 82 / 82 Passed |
| Integration Tests | ✅ Passed |
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

```bash
python main.py
```

---

# Running Tests

```bash
python -m pytest
```

Current Result:

```
82 tests passed
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

These documents describe the project's architecture, engineering decisions,
release history, and development roadmap, including:

- Architecture Design
- Architecture Decision Records
- Engineering Standards
- Sprint Reports
- Project State
- Release History

---

# License

This project is licensed under the MIT License.

---

For detailed architecture, engineering standards, sprint history,
and design decisions, see the documentation under `docs/`.

AnalystGPT Enterprise continues to evolve through incremental,
well-tested engineering sprints.

**Current Release:** v7.0.0

**Next Milestone:** Sprint 8 – REST API