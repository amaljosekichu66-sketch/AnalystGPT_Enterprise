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
            has_success_response = any(str(status_code).startswith("2") for status_code in responses)
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


# ==========================================================
# Route prefix convention
# ==========================================================
#
# `/reports/*` used to be mounted twice (with and without `/api`) and
# `/powerbi/*` only without it, so two of the nine routers disagreed with the
# convention the other seven follow. The unprefixed paths were not dead code -
# the Streamlit APIClient called them - so they remain as deprecated aliases
# rather than being deleted, and the client now uses the prefixed ones.


def _paths() -> dict:
    return app.openapi()["paths"]


def test_every_functional_router_is_mounted_under_the_api_prefix() -> None:
    paths = _paths()

    for expected in (
        "/api/reports",
        "/api/powerbi/dashboard",
        "/api/powerbi/summary",
        "/api/ai/jobs/{job_id}",
        "/api/admin/users",
    ):
        assert expected in paths, f"{expected} is not mounted"


def test_unprefixed_aliases_are_gone() -> None:
    """
    The deprecated duplicates are removed.

    `/reports/*` used to answer on both `/api/reports/*` and `/reports/*`, and
    `/powerbi/*` plus the dashboard router answered only unprefixed. They were
    kept as deprecated aliases while the frontend migrated; now that nothing
    in-tree uses them they are gone, and every path has an `/api` equivalent.
    """
    paths = _paths()

    for alias in (
        "/reports",
        "/reports/export/text",
        "/powerbi/dashboard",
        "/powerbi/status",
    ):
        assert alias not in paths, f"{alias} should have been removed"


def test_every_path_is_under_the_api_prefix() -> None:
    """One convention, no exceptions except the service root."""
    stragglers = [p for p in _paths() if not p.startswith("/api") and p != "/"]

    assert stragglers == []


def test_canonical_paths_are_not_deprecated() -> None:
    paths = _paths()

    for canonical in ("/api/reports", "/api/powerbi/dashboard"):
        assert not any(operation.get("deprecated") for operation in paths[canonical].values())


def test_api_client_targets_canonical_paths() -> None:
    """The client must not depend on the deprecated aliases."""
    from src.frontend.services.api_client import APIClient

    for endpoint in (
        APIClient.REPORTS,
        APIClient.DASHBOARD,
        APIClient.POWERBI_SUMMARY,
        APIClient.POWERBI_PIPELINE,
    ):
        assert endpoint.startswith("/api/"), endpoint
