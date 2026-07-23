"""
Tests for Power BI API endpoints.
"""

from fastapi.testclient import TestClient

from src.api.dependencies.application_dependency import (
    get_application,
)
from src.api.server import app


# ==========================================================
# Fake Objects
# ==========================================================

class FakeAnalytics:
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
    def __init__(self):
        self.analytics = FakeAnalytics().analytics


class FakeReportingReport:
    def __init__(self):
        self.report = FakeStructuredReport()

    def to_dict(self):
        return {
            "report": self.report.analytics,
            "export_path": "reports/report.txt",
            "execution_time": 1.25,
        }


class FakePipelineResult:
    def __init__(self):
        self.success = True
        self.output_path = "reports/report.txt"
        self.execution_time = 1.25
        self.error = None
        self.reporting_report = FakeReportingReport()


class FakeApplication:
    def run(self, input_path: str):
        return FakePipelineResult()


# ==========================================================
# Dependency Override
# ==========================================================

app.dependency_overrides[get_application] = (
    lambda: FakeApplication()
)

client = TestClient(app)

DATASET = "sample_data/customer_data.csv"


def test_dashboard_endpoint():
    response = client.get(
        "/powerbi/dashboard",
        params={"dataset": DATASET},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "report" in body


def test_summary_endpoint():
    response = client.get(
        "/powerbi/summary",
        params={"dataset": DATASET},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["total_rows"] == 100


def test_statistics_endpoint():
    response = client.get(
        "/powerbi/statistics",
        params={"dataset": DATASET},
    )

    assert response.status_code == 200
    body = response.json()
    assert "descriptive_statistics" in body


def test_correlation_endpoint():
    response = client.get(
        "/powerbi/correlation",
        params={"dataset": DATASET},
    )

    assert response.status_code == 200
    body = response.json()
    assert "correlation_analysis" in body


def test_distribution_endpoint():
    response = client.get(
        "/powerbi/distribution",
        params={"dataset": DATASET},
    )

    assert response.status_code == 200
    body = response.json()
    assert "distribution_analysis" in body


def test_categorical_endpoint():
    response = client.get(
        "/powerbi/categorical",
        params={"dataset": DATASET},
    )

    assert response.status_code == 200
    body = response.json()
    assert "categorical_analysis" in body


def test_pipeline_endpoint():
    response = client.get(
        "/powerbi/pipeline",
        params={"dataset": DATASET},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True


def test_report_endpoint():
    response = client.get(
        "/powerbi/report",
        params={"dataset": DATASET},
    )

    assert response.status_code == 200
    body = response.json()
    assert "report" in body