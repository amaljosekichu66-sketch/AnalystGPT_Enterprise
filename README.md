<!-- Banner Image -->
<p align="center">
  <img src="docs/image/banner.png" alt="AnalystGPT Enterprise Banner" width="100%">
</p>

<h1 align="center">AnalystGPT Enterprise</h1>

<p align="center">
  <strong>Enterprise AI‑powered Analytics Platform</strong><br>
  Built with Python · FastAPI · Streamlit · PostgreSQL · Ollama
</p>

<p align="center">
  <a href="#"><img src="https://img.shields.io/badge/Python-3.11-blue.svg" alt="Python 3.11"></a>
  <a href="#"><img src="https://img.shields.io/badge/FastAPI-0.115+-green.svg" alt="FastAPI"></a>
  <a href="#"><img src="https://img.shields.io/badge/Streamlit-1.48+-red.svg" alt="Streamlit"></a>
  <a href="#"><img src="https://img.shields.io/badge/Docker-Ready-2496ED.svg" alt="Docker"></a>
  <a href="#"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License MIT"></a>
  <a href="#"><img src="https://img.shields.io/badge/version-v13.0.0-brightgreen" alt="Version"></a>
  <a href="#"><img src="https://img.shields.io/badge/tests-329%20passing-success" alt="Tests"></a>
</p>

<p align="center">
  <a href="#-key-features">Features</a> •
  <a href="#-installation--quick-start">Quick Start</a> •
  <a href="#-rest-api">API Docs</a> •
  <a href="#-roadmap">Roadmap</a> •
  <a href="#-documentation">Docs</a> •
  <a href="#-license">License</a>
</p>

---

## 📊 Quick Overview

| **Data Pipeline** | **REST API** | **Business Intelligence** | **Modern UI** | **Enterprise Identity & Multi-User** | **AI‑Ready** |
| :---------------: | :----------: | :-----------------------: | :-----------: | :-----------------------------------: | :----------: |
| Ingest, clean, validate & analyse data end‑to‑end | FastAPI with OpenAPI 3.1 & interactive docs | Power BI ready endpoints & dashboard integration | Streamlit frontend – interactive & responsive | PBKDF2 hashing, JWT tokens, RBAC & cross-tenant data isolation | Built for AI insights, recommendations & automation |

- **Architecture**: Layered + REST + BI + Multi-Tenant Identity
- **Database**: SQLite (dev) + PostgreSQL (prod)  
- **Frontend**: Streamlit (React‑ready for future)  
- **AI Engine**: Ollama + Qwen/Gemma (with provider abstraction)
- **Testing**: 329 passing tests

---

## 📸 Screenshots

> **Coming soon** – once the Streamlit application is running, this section will be replaced with real screenshots of the Dashboard, Upload, Reports, and AI Insights pages.

For now, the banner above gives a preview of the enterprise interface.

---

## 📖 Table of Contents

- [🏗️ Layered Architecture](#️-layered-architecture)
- [✨ Key Features](#-key-features)
- [🤖 AI Insight Engine](#-ai-insight-engine)
- [🛠️ Technology Stack](#️-technology-stack)
- [📦 Installation & Quick Start](#-installation--quick-start)
- [🌐 REST API](#-rest-api)
- [📁 Project Structure](#-project-structure)
- [⚡ Performance & Scalability](#-performance--scalability)
- [🗺️ Roadmap](#-roadmap)
- [📚 Documentation](#-documentation)
- [🧑‍💻 Design Principles](#-design-principles)
- [🎓 Resume Value](#-resume-value)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

---

## 🏗️ Layered Architecture

The system follows a strict layered architecture ensuring separation of concerns, testability, and maintainability.

<p align="center">
  <img src="docs/image/architecture.png" alt="Layered Architecture Diagram" width="90%">
</p>

| Layer | Responsibility | Components |
|-------|----------------|------------|
| **Presentation** | User interaction, input validation | Streamlit UI, FastAPI REST endpoints |
| **Application** | Orchestration, use cases, services | PipelineService, DashboardService, AIService |
| **Business** | Core domain logic | Upload, Cleaning, Quality, Analytics, Reporting |
| **Persistence** | Data storage abstraction | Repository interfaces, SQLite/PostgreSQL adapters |
| **Infrastructure** | External services, configurations | AI providers, logging, environment config |

---

## ✨ Key Features

### 📊 Enterprise Analytics Pipeline
- **Multi‑format ingestion** – CSV, Excel, JSON with automatic type detection
- **Automated data cleaning** – Missing values, outliers, duplicate detection
- **Data quality validation** – Completeness, uniqueness, consistency, accuracy
- **Statistical analytics** – Descriptive stats, correlations, distributions
- **Structured reporting** – Executive summaries, KPIs, visualisations

### 🤖 AI Insight Engine (v11.0.0)
- **Provider abstraction** – Ollama integration with Gemma model
- **Prompt engineering** – Structured prompts for consistent output
- **Automated narrative generation** – Executive summaries, recommendations
- **Hallucination prevention** – Prompt validation, response parsing
- **Multi‑provider ready** – OpenAI, Anthropic, AWS Bedrock support planned

### 🌐 REST API
- **FastAPI** with dependency injection and global exception handling
- **OpenAPI 3.1** specification with Swagger UI and ReDoc
- **Type‑safe Pydantic models** for all requests and responses
- **Comprehensive endpoints** – Health, version, pipeline execution, Power BI

### 📈 Business Intelligence
- **Power BI integration** – Dedicated endpoints for BI tools
- **Dashboard service** – Summary statistics, correlations, distributions
- **Categorical analysis** – Value counts, percentages, visualisations
- **Pre‑aggregated metrics** – Optimised for dashboard performance

### 💾 Persistence & Database
- **Repository pattern** – Abstraction over database implementation
- **Dual database support** – SQLite (dev) and PostgreSQL (production)
- **Migration support** – Schema versioning and upgrades
- **Efficient queries** – Indexed fields, query optimisation

---

## 🤖 AI Insight Engine

The AI Insight Engine brings large language model capabilities to analytics interpretation.

### Provider Abstraction

```mermaid
graph TD
    A[AI Provider<br/>Abstract Base Class] --> B[OllamaProvider<br/>Gemma ✅ Current]
    A --> C[OpenAIProvider<br/>GPT-4 🔄 Planned]
    A --> D[AnthropicProvider<br/>Claude 🔄 Planned]
    A --> E[BedrockProvider<br/>Titan 🔄 Planned]
```

### Processing Pipeline

```mermaid
flowchart LR
    A[Analytics Module] --> B[AI Service]
    B --> C[Prompt Builder]
    C --> D[Prompt Validator]
    D --> E[LLM Provider<br/>Ollama/Gemma]
    E --> F[Parser]
    F --> G[Response Validator]
    G --> H[Report Generator]
    H --> I[API/Frontend]
```

### Core Components

| Component | Responsibility |
|-----------|----------------|
| **Provider Abstraction** | Interface for multiple LLM providers |
| **Prompt Builder** | Constructs structured, contextual prompts from analytics data |
| **Prompt Validator** | Ensures prompts meet quality and safety standards |
| **Parser** | Extracts structured data from LLM responses |
| **Response Validator** | Validates response format and consistency |
| **Report Generator** | Combines analytics and AI narratives |

---

## 🛠️ Technology Stack

| Category | Technology |
|----------|------------|
| **Language** | Python 3.11 |
| **Web Framework** | FastAPI, Uvicorn |
| **Data Processing** | Pandas, NumPy |
| **Validation** | Pydantic V2 |
| **Frontend** | Streamlit, Plotly |
| **Database** | SQLite (dev), PostgreSQL (prod) |
| **AI** | Ollama, Gemma models |
| **Testing** | pytest, pytest‑cov, HTTPX |
| **Documentation** | Markdown, Mermaid, ADRs |

---

## 📦 Installation & Quick Start

### Quick Start (30 seconds)

```bash
git clone https://github.com/amaljosekichu66-sketch/AnalystGPT_Enterprise.git
cd AnalystGPT_Enterprise
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

### Full Development Setup

```bash
# Clone and enter
git clone https://github.com/amaljosekichu66-sketch/AnalystGPT_Enterprise.git
cd AnalystGPT_Enterprise

# Virtual environment
python -m venv venv
# Linux / macOS:
source venv/bin/activate
# Windows PowerShell:
# venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Environment configuration
cp .env.example .env
# Edit .env with your settings (PostgreSQL, Ollama, etc.)

# Run the CLI pipeline
python main.py

# Run the REST API
python -m uvicorn src.api.server:app --reload
# Open http://127.0.0.1:8000/docs

# Run the Streamlit frontend
streamlit run src/frontend/streamlit_app.py
# Open http://localhost:8501

# Run tests
pytest

# Run AI Insight Engine (requires Ollama)
ollama run gemma:2b  # Pull the model first
python -c "from src.ai.ai_manager import AIManager; print(AIManager().generate_ai_report(...))"
```

---

## 🌐 REST API

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | API root information |
| `GET` | `/health` | Health check |
| `GET` | `/api/v1/version` | Version information |
| `POST` | `/api/v1/pipeline` | Execute full analytics pipeline |
| `GET` | `/api/v1/report/{id}` | Retrieve a specific report |
| `GET` | `/api/v1/reports` | List all reports |
| `GET` | `/api/v1/dashboard/summary` | Dashboard summary statistics |
| `GET` | `/api/v1/dashboard/correlations` | Correlation analysis |
| `GET` | `/api/v1/dashboard/distributions` | Distribution metrics |

*Additional Power BI endpoints are available under `/powerbi`.*

### API Documentation
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc
- **OpenAPI Spec**: http://127.0.0.1:8000/openapi.json

### Example Request

```bash
curl -X POST http://localhost:8000/api/v1/pipeline \
  -H "Content-Type: application/json" \
  -d '{"file_path": "data/sample.csv", "generate_ai": true}'
```

### Response (abridged)

```json
{
  "status": "success",
  "report_id": "abc-123",
  "analytics": {
    "summary": { "rows": 1000, "columns": 15 },
    "statistics": {...},
    "correlations": [...]
  },
  "ai_insight": {
    "executive_summary": "...",
    "key_findings": "...",
    "recommendations": "..."
  }
}
```

---

## 📁 Project Structure

```text
AnalystGPT_Enterprise/
├── src/
│   ├── api/                    # REST API Layer
│   │   ├── server.py           # FastAPI app
│   │   ├── routes/             # Endpoint definitions
│   │   ├── models/             # Pydantic schemas
│   │   └── dependencies/       # DI setup
│   ├── application/            # Application Layer
│   │   ├── pipeline_service.py # Orchestrator
│   │   ├── dashboard_service.py
│   │   └── ai_service.py
│   ├── analytics/              # Business: Analytics
│   ├── cleaning/               # Business: Data cleaning
│   ├── quality/                # Business: Quality validation
│   ├── reporting/              # Business: Report generation
│   ├── upload/                 # Business: Data ingestion
│   ├── infrastructure/         # Infrastructure Layer
│   │   ├── persistence/        # Repository pattern
│   │   ├── ai/                 # AI providers
│   │   └── config/             # Configuration
│   ├── frontend/               # Streamlit UI
│   │   ├── streamlit_app.py    # Main app
│   │   └── services/           # UI services
│   ├── llm/                    # LLM abstraction & providers
│   ├── integrations/           # External integrations (Power BI)
│   ├── database/               # Database adapters
│   └── core/                   # Core utilities (logging, settings)
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── stress/
│   └── ...
├── docs/
│   ├── adr/                    # Architecture Decision Records
│   ├── image/                  # Screenshots & diagrams
│   └── project/                # Project documentation
├── data/                       # Data storage (gitignored)
├── main.py                     # CLI entry point
├── requirements.txt
├── .env.example
├── LICENSE
└── README.md
```

---

## 🔄 Data Flow

<p align="center">
  <img src="docs/image/data_flow.png" alt="Data Flow Diagram" width="90%">
</p>

---

## ⚡ Performance & Scalability

### Performance Optimisations
- **Efficient Pandas operations** – Vectorised processing where possible.
- **Database indexing** – Foreign keys and frequently queried fields are indexed.
- **Batch inserts** – For large datasets to reduce database overhead.
- **Lazy loading** – Datasets are loaded only when needed.
- **Query optimisation** – All queries are reviewed for performance.

### Scalability Approach
- **Stateless API** – Allows horizontal scaling of web tier.
- **Database separation** – Can be moved to a dedicated server for production.
- **Asynchronous processing** – (Planned) for long‑running pipelines.
- **Caching** – (Planned) for frequently requested dashboard metrics.
- **Read replicas** – (Planned) for high‑load dashboard queries.

---

## 🗺️ Roadmap

### Project Timeline

<p align="center">
  <img src="docs/image/project_timeline.png" alt="Project Timeline" width="90%">
</p>

### Completed Sprints

```mermaid
timeline
    title AnalystGPT Enterprise Roadmap
    section Sprint 1-5.5
        Core analytics pipeline : ✅ Completed
    section Sprint 6
        SQLite persistence : ✅ Completed
    section Sprint 7
        Database abstraction & PostgreSQL : ✅ Completed
    section Sprint 8
        REST API : ✅ Completed
    section Sprint 9
        Power BI integration : ✅ Completed
    section Sprint 10
        Enterprise Streamlit frontend : ✅ Completed
    section Sprint 11
        AI Insight Engine : ✅ Completed
    section Sprint 12
        Production Deployment : ✅ Completed
```

### Current & Future Sprints

| Sprint | Focus | Status |
|--------|-------|--------|
| **12** | Production Deployment & Containerization | ✅ Completed |
| 13 | Multi‑user support | 📅 Planned |
| 14 | React frontend | 📅 Planned |
| 15 | Multi‑AI provider support | 📅 Planned |
| 16 | Real‑time streaming analytics | 📅 Planned |
| 17 | Machine learning integration | 📅 Planned |

### Progress Visual

```text
Upload     ████████████████████ 100%
Cleaning   ████████████████████ 100%
Quality    ████████████████████ 100%
Analytics  ████████████████████ 100%
Reporting  ████████████████████ 100%
SQLite     ████████████████████ 100%
PostgreSQL ████████████████████ 100%
REST API   ████████████████████ 100%
Power BI   ████████████████████ 100%
Streamlit  ████████████████████ 100%
AI Engine  ████████████████████ 100%
Deployment ████████████████████ 100%
CI/CD      ████████████████████ 100%
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [README.md](README.md) | Project overview and quick start |
| [PROJECT_STATE.md](docs/project/PROJECT_STATE.md) | Current project status and health |
| [ARCHITECTURE.md](docs/project/ARCHITECTURE.md) | Detailed system architecture |
| [ROADMAP.md](docs/project/ROADMAP.md) | Long‑term development roadmap |
| [PROJECT_JOURNAL.md](docs/project/PROJECT_JOURNAL.md) | Engineering journey per sprint |
| [CHANGELOG.md](CHANGELOG.md) | Release notes and version history |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guidelines |
| [API_GUIDE.md](docs/API_GUIDE.md) | REST API usage and examples |
| [AI_GUIDE.md](docs/AI_GUIDE.md) | AI Insight Engine usage |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | Deployment guide |
| [ADR/](docs/adr/) | Architecture Decision Records |

---

## 🧑‍💻 Design Principles

The codebase adheres to:

- **Layered Architecture** – Each layer has a distinct responsibility.
- **SOLID Principles** – Single responsibility, open/closed, Liskov substitution, interface segregation, dependency inversion.
- **Clean Code** – Readable, maintainable, and self‑documenting code.
- **Fail Fast** – Validation and error detection early.
- **Single Source of Truth** – Centralised configuration and state management.
- **Separation of Concerns** – Clear boundaries between modules.
- **Interface‑based Design** – Abstractions for extensibility.
- **Dependency Inversion** – Depend on abstractions, not concretions.
- **Testability First** – Code is designed with testing in mind.

### Why This Architecture?

| Technology | Why Chosen |
|------------|------------|
| **FastAPI** | Modern, async‑capable, automatic OpenAPI docs, dependency injection, type hints. |
| **Streamlit** | Rapid development of data apps, no frontend complexity for MVP, Python‑native. |
| **Repository Pattern** | Decouples domain from persistence, easy to swap databases, testable. |
| **SQLite + PostgreSQL** | SQLite for development (zero‑config), PostgreSQL for production (robust, scalable). |
| **Ollama** | Local LLM hosting, privacy‑friendly, open‑source models (Gemma). |
| **Pydantic** | Type‑safe data validation, serialisation, and schema enforcement. |
| **Pandas** | De facto standard for data manipulation in Python, extensive ecosystem. |

---

## 🎓 Resume Value

### Skills Demonstrated
- **Software Engineering**: Python, FastAPI, Streamlit, REST API, OpenAPI, Repository Pattern, SOLID, Clean Architecture, Dependency Injection.
- **Data Engineering**: Pandas, Data Pipelines, ETL, Data Validation, Data Quality, CSV/Excel/JSON.
- **Database**: SQLite, PostgreSQL, Schema Design, Query Optimisation, Migration Management.
- **AI/ML**: LLM Integration, Prompt Engineering, Provider Abstraction, Hallucination Prevention, Ollama/Gemma.
- **Frontend**: Streamlit, Plotly, Interactive Dashboards, Session Management.
- **Testing**: pytest, Unit Testing, Integration Testing, Stress Testing.
- **DevOps**: Environment Configuration, Docker (planned), CI/CD (planned).

### Concepts Demonstrated
- **Enterprise Software Architecture** – Layered, modular, scalable.
- **Business Analytics** – Data ingestion, cleaning, quality, analytics, reporting.
- **AI Integration** – LLM narrative generation, hallucination prevention.
- **Production Engineering** – Testing, performance, documentation.
- **Project Management** – Sprints, milestones, ADRs, versioning.

---

## 🤝 Contributing

We welcome contributions! Please review our [Contributing Guidelines](CONTRIBUTING.md).

### How to Contribute

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/amazing-feature`).
3. Commit your changes (`git commit -m 'Add amazing feature'`).
4. Push to the branch (`git push origin feature/amazing-feature`).
5. Open a Pull Request.

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests with coverage
pytest --cov=src tests/

# Run pre-commit hooks (planned)
pre-commit run --all-files
```

---

## 🙏 Acknowledgements

- **FastAPI** – For the incredible web framework.
- **Streamlit** – For the frontend framework.
- **Pandas** – For data processing capabilities.
- **Ollama** – For local LLM deployment.
- **Google Gemma** – For the open model.
- **PyTest** – For testing framework.
- **OpenAPI** – For API specification.

---

## 📄 License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.

---

## 📫 Support

- **Issues**: [GitHub Issues](https://github.com/amaljosekichu66-sketch/AnalystGPT_Enterprise/issues)
- **Discussions**: [GitHub Discussions](https://github.com/amaljosekichu66-sketch/AnalystGPT_Enterprise/discussions)
- **Documentation**: `docs/`

---

## ⭐ Star Us

If you find this project useful, please consider starring the repository to help others discover it!

---

<p align="center">
  <img src="docs/image/banner.png" alt="AnalystGPT Enterprise Footer" width="80%">
</p>

<p align="center">
  <strong>Built with Python • FastAPI • Streamlit • PostgreSQL • SQLite • Ollama • Gemma</strong><br>
  <em>Designed using Enterprise Software Engineering Principles</em>
</p>

<p align="center">
  <a href="https://github.com/amaljosekichu66-sketch/AnalystGPT_Enterprise">GitHub</a> •
  <a href="https://in.linkedin.com/in/mr-amaljose">LinkedIn</a> •
  <a href="#documentation">Documentation</a> •
  <a href="https://github.com/amaljosekichu66-sketch/AnalystGPT_Enterprise/issues">Issues</a> •
  <a href="LICENSE">License</a>
</p>

---