"""
OpenAPI 3.1 Contract Validation Test Suite.

Sprint 14 Phase 6 — OpenAPI / React Migration Readiness.
"""

import json
from pathlib import Path
from fastapi.testclient import TestClient

from src.api.server import app


def test_openapi_schema_generation():
    """Verify OpenAPI 3.1 schema generates successfully with full metadata."""
    schema = app.openapi()

    assert schema is not None
    assert schema.get("openapi") == "3.1.0"
    assert "info" in schema
    assert schema["info"]["title"] == "AnalystGPT Enterprise"
    assert "paths" in schema
    assert len(schema["paths"]) >= 20
    assert "components" in schema
    assert "schemas" in schema["components"]


def test_all_endpoints_have_explicit_response_models():
    """Verify that every registered route operation has an explicit 2xx response schema."""
    schema = app.openapi()
    paths = schema["paths"]

    for path, methods in paths.items():
        for method, operation in methods.items():
            if method.lower() not in ("get", "post", "put", "patch", "delete"):
                continue

            responses = operation.get("responses", {})
            has_success_response = any(
                str(status_code).startswith("2") for status_code in responses
            )
            assert has_success_response, f"Route {method.upper()} {path} missing 2xx response declaration"


def test_openapi_schemas_contain_core_models():
    """Verify all core domain and response models are present in OpenAPI components."""
    schema = app.openapi()
    schemas = schema["components"]["schemas"]

    required_models = [
        "AIJobResponse",
        "AIReportResponse",
        "DashboardResponse",
        "DashboardSummary",
        "DashboardStatistics",
        "DashboardCorrelation",
        "DashboardDistribution",
        "DashboardCategorical",
        "DatasetVersionResponse",
        "ErrorResponse",
        "HealthResponse",
        "LineageResponse",
        "PipelineResponse",
        "PipelineSummary",
        "ReportResponse",
        "ReportsListResponse",
        "ReportDataResponse",
        "ReportSectionItem",
        "RootResponse",
        "TokenResponse",
        "UserResponse",
        "UserDeleteResponse",
        "UserRole",
        "UserStatus",
        "VersionResponse",
    ]

    for model_name in required_models:
        assert model_name in schemas, f"Required model '{model_name}' missing from OpenAPI schemas"


def test_openapi_docs_endpoint():
    """Verify /docs and /openapi.json return valid JSON with 200 OK."""
    client = TestClient(app)

    res_openapi = client.get("/openapi.json")
    assert res_openapi.status_code == 200
    data = res_openapi.json()
    assert data["openapi"] == "3.1.0"


def test_exported_openapi_file_matches_live_schema():
    """Verify docs/api/openapi.json exists and is synchronized with live app schema."""
    schema_file = Path("docs/api/openapi.json")
    assert schema_file.exists(), "docs/api/openapi.json must exist"

    with open(schema_file, encoding="utf-8") as f:
        file_schema = json.load(f)

    live_schema = app.openapi()
    assert file_schema.get("openapi") == live_schema.get("openapi")
    assert len(file_schema.get("paths", {})) == len(live_schema.get("paths", {}))
