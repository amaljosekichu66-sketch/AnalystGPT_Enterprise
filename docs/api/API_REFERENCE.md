# AnalystGPT Enterprise API Reference

> **Purpose**
>
> This document provides the official REST API reference for
> AnalystGPT Enterprise.
>
> It describes every available endpoint, request model,
> response model, HTTP status code, error response, and
> usage example.
>
> The REST API provides the public interface to AnalystGPT
> Enterprise while preserving the internal layered architecture.
>
> Business logic remains inside the Application Layer.
>
> Current Version: **v8.0.0**

---

# API Information

| Item | Value |
|------|--------|
| API Version | v8.0.0 |
| Framework | FastAPI |
| Specification | OpenAPI 3.1 |
| Documentation | Swagger UI |
| Architecture | REST API |
| Authentication | Not Required (Sprint 8) |
| Content Type | application/json |

---

# Base URL

Local Development

```text
http://127.0.0.1:8000
```

---

# Interactive Documentation

Swagger UI

```text
http://127.0.0.1:8000/docs
```

ReDoc

```text
http://127.0.0.1:8000/redoc
```

OpenAPI Specification

```text
http://127.0.0.1:8000/openapi.json
```

---

# API Architecture

```text
Client
   │
   ▼
REST API
   │
   ▼
Request Validation
   │
   ▼
API Route
   │
   ▼
Dependency Injection
   │
   ▼
Application.run()
   │
   ▼
Business Modules
   │
   ▼
Persistence
   │
   ▼
Response Model
```

The API layer contains no business logic.

All business operations are delegated to the Application Layer.

---

# Common Response Format

Successful responses return JSON.

Example

```json
{
    "success": true
}
```

Failed responses return

```json
{
    "success": false,
    "message": "...",
    "error": "..."
}
```

---

# Endpoint Summary

| Method | Endpoint | Description |
|---------|----------|-------------|
| GET | / | API Root |
| GET | /api/health | Health Status |
| GET | /api/version | Current Version |
| POST | /api/pipeline | Execute Analytics Pipeline |

---

# GET /

Returns general information about the API.

## Request

```
GET /
```

No request body.

---

## Successful Response

HTTP 200

```json
{
    "success": true,
    "application": "AnalystGPT Enterprise",
    "version": "8.0.0",
    "status": "running",
    "documentation": "/docs"
}
```

---

## Response Fields

| Field | Type | Description |
|------|------|-------------|
| success | boolean | Request status |
| application | string | Application name |
| version | string | Current version |
| status | string | Application status |
| documentation | string | Swagger URL |

---

# GET /api/health

Returns current API health.

---

## Request

```
GET /api/health
```

---

## Successful Response

HTTP 200

```json
{
    "success": true,
    "status": "healthy"
}
```

---

## Response Fields

| Field | Type | Description |
|------|------|-------------|
| success | boolean | Request status |
| status | string | Health status |

---

# GET /api/version

Returns the current application version.

---

## Request

```
GET /api/version
```

---

## Successful Response

HTTP 200

```json
{
    "success": true,
    "version": "8.0.0"
}
```

---

## Response Fields

| Field | Type | Description |
|------|------|-------------|
| success | boolean | Request status |
| version | string | Application version |

---

# POST /api/pipeline

Executes the complete AnalystGPT Enterprise pipeline.

---

## Request

```http
POST /api/pipeline
Content-Type: application/json
```

---

## Request Body

```json
{
    "input_path": "sample_data/customer_data.csv"
}
```

---

## Request Fields

| Field | Type | Required | Description |
|------|------|----------|-------------|
| input_path | string | Yes | Path to dataset |

---

## Successful Response

HTTP 200

```json
{
    "success": true,
    "output_path": "reports/analystgpt_report.txt",
    "execution_time": 0.08,
    "error": null
}
```

---

## Failure Response

Example

```json
{
    "success": false,
    "output_path": null,
    "execution_time": 0.01,
    "error": "File not found: invalid.csv"
}
```

---

## Response Fields

| Field | Type | Description |
|------|------|-------------|
| success | boolean | Pipeline status |
| output_path | string/null | Generated report |
| execution_time | float | Pipeline runtime |
| error | string/null | Error message |

---

# HTTP Status Codes

| Code | Meaning |
|------|----------|
| 200 | Request completed successfully |
| 400 | Invalid request |
| 404 | Resource not found |
| 422 | Request validation failed |
| 500 | Internal server error |

---

# Validation

Input validation is performed automatically using Pydantic.

Examples include:

- Missing required fields
- Invalid JSON
- Invalid data types
- Empty dataset path

Validation failures return HTTP 422.

---

# Error Responses

Global exception handlers provide a consistent error structure.

Example

```json
{
    "success": false,
    "message": "Dataset not found.",
    "error": "File not found: customer.csv"
}
```

---

# OpenAPI

The complete API specification is generated automatically.

Location

```text
/openapi.json
```

---

# Swagger UI

Interactive API documentation is available at

```text
/docs
```

Developers can

- Execute requests
- Inspect schemas
- Validate responses
- Test endpoints

without external tools.

---

# ReDoc

Alternative documentation

```text
/redoc
```

Provides a documentation-focused interface generated directly from the OpenAPI specification.

---

# API Models

Current request models

- PipelineRequest

Current response models

- APIResponse
- RootResponse
- HealthResponse
- VersionResponse
- PipelineResponse

---

# Design Principles

The REST API follows the following principles:

- RESTful Design
- Stateless Communication
- Thin Controllers
- Dependency Injection
- Strong Typing
- Stable Contracts
- Separation of Concerns
- OpenAPI Compliance
- Consistent Error Responses

---

# Future API Enhancements

Planned for future sprints

Sprint 9

- Power BI REST integration

Sprint 10

- Streamlit frontend integration

Sprint 11

- AI Insight endpoints

Sprint 12

- Authentication
- Authorization
- Docker deployment
- Production API configuration

---

# Current API Status

| Item | Status |
|------|--------|
| REST API | ✅ Stable |
| FastAPI | ✅ Operational |
| Swagger UI | ✅ Operational |
| OpenAPI | ✅ Generated |
| Request Validation | ✅ Complete |
| Response Validation | ✅ Complete |
| Exception Handling | ✅ Complete |
| Integration Tests | ✅ Passed |
| Live Endpoint Validation | ✅ Passed |

---

**API Version:** **v8.0.0**

**Next Planned API Enhancement:** **Sprint 9 – Power BI Integration**