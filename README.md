# AnalystGPT Enterprise

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Tests](https://img.shields.io/badge/Tests-82%20Passed-brightgreen)
![Architecture](https://img.shields.io/badge/Architecture-Layered-success)
![License](https://img.shields.io/badge/License-MIT-green)

> **Enterprise-Grade Analytics Platform**
>
> AnalystGPT Enterprise is a modular analytics platform built using enterprise software engineering principles. The project demonstrates how a production-quality analytics application can be designed through clean architecture, layered architecture, automated testing, documentation, and scalable software engineering practices.

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

The project is intentionally developed sprint-by-sprint to simulate the
evolution of a production enterprise application.

---

# Why This Project?

AnalystGPT Enterprise was built as a long-term software engineering project
to progressively implement enterprise architecture, scalable analytics
workflows, automated testing, database persistence, and production-ready
engineering practices through iterative sprint-based development.

---

# Key Engineering Highlights

- Enterprise layered architecture
- Repository Pattern
- Manager-Orchestrator Pattern
- SQLite persistence layer
- Automated testing (82 tests)
- Performance validation up to 1,000,000 rows
- Modular business pipeline
- Architecture Decision Records (ADRs)
- Comprehensive engineering documentation

---

# Current Status

| Item | Status |
|------|--------|
| **Current Version** | **v6.0.0** |
| **Development Status** | 🟢 Active Development |
| **Current Sprint** | ✅ Sprint 6 – SQLite Persistence Complete |
| **Architecture** | 🟢 Enterprise Layered Architecture |
| **Application Layer** | ✅ Stable |
| **Persistence Layer** | ✅ Stable |
| **Database Infrastructure** | ✅ Stable |
| **Pipeline Contracts** | ✅ Stable |
| **Automated Tests** | ✅ 82 / 82 Passed |
| **Performance Validation** | ✅ Completed |
| **Next Sprint** | 🚀 Sprint 7 – PostgreSQL Integration |

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
- ✅ SQLite Database Infrastructure
- ✅ Repository Layer

## Upcoming Modules

- ⏳ PostgreSQL Integration
- ⏳ REST APIs
- ⏳ Power BI Integration
- ⏳ Streamlit Application
- ⏳ AI Insights
- ⏳ Production Deployment

---

# Architecture Principles

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
               Repository Layer
                        │
                 SQLite Database
                        │
                        ▼
                 PipelineResult
```

---

# Technology Stack

| Category | Technologies |
|----------|--------------|
| Language | Python 3.11 |
| Data Processing | Pandas |
| Database | SQLite |
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
- Persistent pipeline execution tracking
- SQLite-backed metadata storage
- Repository-based database abstraction
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
└── core/

tests/

docs/

performance/

sample_data/
```

---

# Future Vision

The long-term objective is to evolve AnalystGPT Enterprise from a modular
analytics pipeline into a complete enterprise analytics platform supporting
relational databases, REST APIs, dashboards, AI-assisted insights, and
production deployment.

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
| Sprint 7 – PostgreSQL | 🚀 Next |
| Sprint 8 – REST API | Planned |
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

---

# Installation

```bash
git clone https://github.com/amaljosekichu66-sketch/AnalystGPT_Enterprise.git

cd AnalystGPT_Enterprise

pip install -r requirements.txt
```

---

# Running the Project

```bash
python main.py
```

---

# Running Tests

```bash
pytest
```

Current Result:

```
82 Passed
0 Failed
0 Errors
0 Warnings
```

---

# Documentation

Detailed engineering documentation is available under:

- `docs/project/`
- `docs/engineering/`
- `docs/adr/`
- `docs/sprints/`

These documents describe the project's architecture, engineering decisions,
release history, and development roadmap.

---

# License

This project is licensed under the MIT License.

---

For detailed architecture, engineering standards, sprint history,
and design decisions, see the documentation under `docs/`.

AnalystGPT Enterprise continues to evolve through incremental,
well-tested engineering sprints.

**Current Release:** v6.0.0

**Next Milestone:** Sprint 7 – PostgreSQL Integration