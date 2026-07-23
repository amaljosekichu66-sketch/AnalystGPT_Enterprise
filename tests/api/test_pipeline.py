"""
Integration tests for the pipeline endpoint.
"""

from fastapi.testclient import TestClient

from src.api.dependencies.application_dependency import (
    get_application,
)
from src.api.server import app


# ==========================================================
# Fake Application
# ==========================================================

class FakeAnalytics:
    """
    Fake analytics payload.
    """

    def __init__(self):
        self.analytics = {
            "descriptive_statistics": {
                "total_rows": 100,
                "total_columns": 5,
                "numeric_column_count": 2,
                "categorical_column_count": 3,
                "datetime_column_count": 0,
                "memory_usage_mb": 0.01,
            },
            "correlation_analysis": {},
            "distribution_analysis": {},
            "categorical_analysis": {},
        }


class FakeStructuredReport:
    """
    Fake structured report.
    """

    def __init__(self):
        self.analytics = FakeAnalytics().analytics


class FakeReportingReport:
    """
    Fake reporting report.
    """

    def __init__(self):
        self.report = FakeStructuredReport()

    def to_dict(self):
        return {
            "report": self.report.analytics,
            "export_path": "reports/report.txt",
            "execution_time": 1.25,
        }


class FakePipelineResult:
    """
    Fake pipeline execution result.
    """

    def __init__(self):
        self.success = True
        self.output_path = "reports/report.txt"
        self.execution_time = 1.25
        self.error = None
        self.reporting_report = FakeReportingReport()


class FakeApplication:
    """
    Fake application used for dependency injection.
    """

    def run(self, input_path: str) -> FakePipelineResult:
        return FakePipelineResult()


# ==========================================================
# Dependency Override
# ==========================================================

app.dependency_overrides[get_application] = (
    lambda: FakeApplication()
)

client = TestClient(app)


# ==========================================================
# Pipeline Endpoint Tests
# ==========================================================

def test_pipeline_endpoint_returns_success() -> None:
    """
    Verify that the pipeline endpoint executes successfully.
    """

    response = client.post(
        "/api/pipeline",
        json={
            "input_path": "sample_data/customer_data.csv",
        },
    )

    assert response.status_code == 200


def test_pipeline_endpoint_returns_expected_response() -> None:
    """
    Verify that the pipeline endpoint returns
    the expected pipeline result.
    """

    response = client.post(
        "/api/pipeline",
        json={
            "input_path": "sample_data/customer_data.csv",
        },
    )

    data = response.json()

    assert data["success"] is True
    assert data["output_path"] == "reports/report.txt"
    assert data["execution_time"] == 1.25
    assert data["error"] is None