"""
Tests for Power BI API endpoints.
"""

from unittest.mock import patch

import os
import pytest
from fastapi.testclient import TestClient

from src.api.dependencies.application_dependency import (
    get_application,
)
from src.api.dependencies.auth_dependencies import (
    get_user_context,
)
from src.api.server import app
from src.application.pipeline_report import PipelineReport
from src.ai.ai_report import AIReport
from src.identity.context import UserContext
from src.identity.models import UserRole, UserStatus


# ==========================================================
# Fake Objects (minimal but sufficient)
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
        self.export_path = "reports/report.txt"
        self.execution_time = 1.25

    def to_dict(self):
        return {
            "report": self.report.analytics,
            "export_path": self.export_path,
            "execution_time": self.execution_time,
        }


class FakeAIReport(AIReport):
    def __init__(self):
        super().__init__(
            executive_summary="Executive Summary",
            recommendations=["Recommendation 1", "Recommendation 2"],
            explanations=["Explanation 1", "Explanation 2"],
            narrative="Business narrative.",
            model="qwen3:8b",
            provider="ollama",
            execution_time=0.55,
            prompt_count=4,
            generated_at="2026-07-26T00:00:00",  # string, not datetime
        )


class FakePipelineResult:
    def __init__(self):
        self.reporting_report = FakeReportingReport()
        self.ai_report = FakeAIReport()
        self.success = True
        self.output_path = self.reporting_report.export_path
        self.execution_time = 1.25
        self.error = None
        self.pipeline_report = PipelineReport(
            reporting_report=self.reporting_report,
            ai_report=self.ai_report,
        )
        self.ai_generated = True
        self.generated_at = "2026-07-29T00:00:00"  # used by models

    def to_dict(self):
        return {
            "success": self.success,
            "output_path": self.output_path,
            "execution_time": self.execution_time,
            "error": self.error,
            "ai_generated": self.ai_generated,
            "report": self.reporting_report.to_dict(),
            "ai_report": self.ai_report.to_dict() if self.ai_report else None,
            "generated_at": self.generated_at,
        }


class FakeApplication:
    def run(self, input_path: str):
        return FakePipelineResult()

    def get_or_run(self, input_path: str):
        return self.run(input_path)


# ==========================================================
# Pytest Fixture
# ==========================================================

@pytest.fixture(autouse=True)
def override_application():
    app.dependency_overrides[get_application] = lambda: FakeApplication()
    app.dependency_overrides[get_user_context] = lambda: UserContext(
        user_id=1,
        username="powerbi_user",
        email="powerbi@enterprise.com",
        role=UserRole.ANALYST,
        status=UserStatus.ACTIVE,
        is_authenticated=True,
    )
    yield
    app.dependency_overrides.clear()


# ==========================================================
# Test Client
# ==========================================================

client = TestClient(app)
DATASET = "sample_data/customer_data.csv"


# ==========================================================
# Pipeline and Report tests
# ==========================================================

@patch("os.path.exists", return_value=True)
@patch("src.api.routes.powerbi._execute_pipeline", return_value=FakePipelineResult())
def test_pipeline_endpoint(mock_execute, mock_exists):
    response = client.get("/powerbi/pipeline", params={"dataset": DATASET})
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["ai_generated"] is True


@patch("os.path.exists", return_value=True)
@patch("src.api.routes.powerbi._execute_pipeline", return_value=FakePipelineResult())
def test_report_endpoint(mock_execute, mock_exists):
    response = client.get("/powerbi/report", params={"dataset": DATASET})
    assert response.status_code == 200
    body = response.json()
    assert "report" in body
    assert "ai_report" in body
    assert body["ai_report"]["provider"] == "ollama"
    assert body["ai_report"]["executive_summary"] == "Executive Summary"


# ==========================================================
# Other endpoints (no patches needed)
# ==========================================================

def test_dashboard_endpoint():
    response = client.get("/powerbi/dashboard", params={"dataset": DATASET})
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "report" in body
    assert "ai_report" in body
    assert body["ai_report"]["model"] == "qwen3:8b"


def test_summary_endpoint():
    response = client.get("/powerbi/summary", params={"dataset": DATASET})
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    # total_rows may not always be present, but if it is, it's an int
    if "total_rows" in body:
        assert isinstance(body["total_rows"], int)


def test_statistics_endpoint():
    response = client.get("/powerbi/statistics", params={"dataset": DATASET})
    assert response.status_code == 200
    body = response.json()
    assert "descriptive_statistics" in body


def test_correlation_endpoint():
    response = client.get("/powerbi/correlation", params={"dataset": DATASET})
    assert response.status_code == 200
    body = response.json()
    assert "correlation_analysis" in body


def test_distribution_endpoint():
    response = client.get("/powerbi/distribution", params={"dataset": DATASET})
    assert response.status_code == 200
    body = response.json()
    assert "distribution_analysis" in body


def test_categorical_endpoint():
    response = client.get("/powerbi/categorical", params={"dataset": DATASET})
    assert response.status_code == 200
    body = response.json()
    assert "categorical_analysis" in body