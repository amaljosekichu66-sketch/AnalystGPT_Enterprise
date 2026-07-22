# AnalystGPT Enterprise API Testing Guide

> **Purpose**
>
> This document explains how to validate and test the
> AnalystGPT Enterprise REST API.
>
> It covers local execution, Swagger UI, OpenAPI validation,
> automated testing, and endpoint verification.
>
> Current Version: **v8.0.0**

---

# API Testing Overview

The REST API is tested through multiple validation layers to ensure
correctness, reliability, and compatibility.

Testing includes:

- Automated endpoint testing
- Request validation
- Response validation
- OpenAPI validation
- Swagger validation
- Integration testing
- End-to-end pipeline execution
- Live API verification

---

# Prerequisites

Before testing, ensure the following are installed:

- Python 3.11+
- FastAPI
- Uvicorn
- Pytest

Install project dependencies:

```bash
pip install -r requirements.txt
```

---

# Starting the API

Run the development server:

```bash
python -m uvicorn src.api.server:app --reload
```

Expected output:

```text
INFO:     Uvicorn running on http://127.0.0.1:8000
```

---

# Swagger UI

Open your browser:

```text
http://127.0.0.1:8000/docs
```

Swagger UI allows you to:

- Explore endpoints
- Submit requests
- Inspect responses
- View schemas
- Test request validation

---

# ReDoc

Alternative documentation:

```text
http://127.0.0.1:8000/redoc
```

---

# OpenAPI Specification

Generated automatically:

```text
http://127.0.0.1:8000/openapi.json
```

Verify that:

- All endpoints appear
- Request models exist
- Response models exist
- Schemas are generated correctly

---

# Available Endpoints

| Method | Endpoint |
|---------|----------|
| GET | / |
| GET | /api/health |
| GET | /api/version |
| POST | /api/pipeline |

---

# Testing Root Endpoint

Request

```http
GET /
```

Expected Response

```json
{
    "success": true,
    "application": "AnalystGPT Enterprise",
    "version": "8.0.0",
    "status": "running",
    "documentation": "/docs"
}
```

Expected Status

```
200 OK
```

---

# Testing Health Endpoint

Request

```http
GET /api/health
```

Expected Response

```json
{
    "success": true,
    "status": "healthy"
}
```

Expected Status

```
200 OK
```

---

# Testing Version Endpoint

Request

```http
GET /api/version
```

Expected Response

```json
{
    "success": true,
    "version": "8.0.0"
}
```

Expected Status

```
200 OK
```

---

# Testing Pipeline Endpoint

Request

```http
POST /api/pipeline
```

Body

```json
{
    "input_path": "sample_data/customer_data.csv"
}
```

Expected Response

```json
{
    "success": true,
    "output_path": "...",
    "execution_time": 0.08,
    "error": null
}
```

Expected Status

```
200 OK
```

---

# Testing Invalid Dataset

Request

```json
{
    "input_path": "invalid.csv"
}
```

Expected Response

```json
{
    "success": false,
    "error": "File not found: invalid.csv"
}
```

The API should return a consistent error response.

---

# Request Validation Testing

Example

```json
{}
```

Expected Result

```
422 Unprocessable Entity
```

Validation is automatically handled by Pydantic.

---

# Automated API Tests

Run only API tests:

```bash
python -m pytest tests/api -v
```

Expected Output

```text
8 passed
```

---

Run the complete test suite:

```bash
python -m pytest
```

Expected Output

```text
90 passed
0 failed
0 errors
```

---

# Integration Testing

The Pipeline endpoint validates the complete workflow:

```text
HTTP Request
        │
        ▼
API Route
        │
        ▼
Application.run()
        │
        ▼
Upload
        │
        ▼
Cleaning
        │
        ▼
Quality
        │
        ▼
Analytics
        │
        ▼
Reporting
        │
        ▼
Persistence
        │
        ▼
PipelineResponse
```

This confirms successful integration across all architectural layers.

---

# Live Validation Checklist

Verify:

- API starts successfully
- Swagger UI loads
- ReDoc loads
- OpenAPI JSON loads
- Root endpoint responds
- Health endpoint responds
- Version endpoint responds
- Pipeline endpoint executes successfully
- Reports are generated
- Database persistence succeeds

---

# Error Handling Validation

Verify that the API returns consistent responses for:

- Missing files
- Invalid JSON
- Missing request fields
- Invalid request types
- Unexpected server errors

All errors should follow the standard error response format.

---

# Performance Validation

REST API performance has been validated using:

| Dataset | Status |
|----------|--------|
| Sample Dataset | ✅ Passed |
| Large Dataset (~100K rows) | ✅ Passed |
| Stress Dataset (~1M rows) | ✅ Passed |

Performance testing confirmed:

- Stable request processing
- Successful pipeline execution
- Correct report generation
- Reliable persistence
- Consistent API responses

---

# Test Coverage

Current API coverage includes:

- Root endpoint
- Health endpoint
- Version endpoint
- Pipeline endpoint
- Request validation
- Response validation
- Swagger generation
- OpenAPI generation
- End-to-end pipeline execution

---

# Current Validation Status

| Validation | Status |
|------------|--------|
| API Endpoints | ✅ Passed |
| Swagger UI | ✅ Passed |
| ReDoc | ✅ Passed |
| OpenAPI | ✅ Passed |
| Request Validation | ✅ Passed |
| Response Validation | ✅ Passed |
| Integration Tests | ✅ Passed |
| End-to-End Pipeline | ✅ Passed |
| Automated Tests | ✅ 90 / 90 Passed |

---

# Future Testing

Sprint 9 will extend API testing to include:

- Power BI connectivity
- External API consumption
- Dashboard integration
- API performance benchmarking

Sprint 12 will introduce:

- Load testing
- Authentication testing
- Security testing
- Docker validation
- Production deployment testing

---

# Summary

The AnalystGPT Enterprise REST API has been validated through automated testing, live endpoint verification, OpenAPI generation, and end-to-end integration testing.

The API Layer remains thin, stateless, and fully separated from business logic while exposing the complete analytics pipeline through stable, well-documented HTTP endpoints.

---

**API Version:** **v8.0.0**

**Testing Status:** **90 / 90 Automated Tests Passed**

**Next Milestone:** **Sprint 9 – Power BI Integration**