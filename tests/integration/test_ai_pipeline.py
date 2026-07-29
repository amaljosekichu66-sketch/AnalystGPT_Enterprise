"""
End-to-end integration test for the AI pipeline.

Verifies the complete execution flow:

Application
    ├── Upload
    ├── Cleaning
    ├── Quality
    ├── Analytics
    ├── Reporting
    └── AI

Result:
PipelineResult
    └── PipelineReport
            └── AIReport
"""

from __future__ import annotations

from unittest.mock import patch

from src.ai.ai_report import AIReport
from src.ai.ai_result import AIResult
from src.application.app import Application


# ==========================================================
# Test
# ==========================================================


@patch(
    "src.application.app.AIManager.generate_ai_report"
)
def test_application_ai_pipeline(
    mock_generate_ai,
):

    mock_generate_ai.return_value = AIResult(
        success=True,
        ai_report=AIReport(
            executive_summary=(
                "Executive summary."
            ),
            recommendations=[
                "Recommendation 1",
                "Recommendation 2",
            ],
            explanations=[
                "Explanation 1",
                "Explanation 2",
            ],
            narrative=(
                "Business narrative."
            ),
            model="fake-model",
            provider="fake-provider",
            execution_time=0.25,
            prompt_count=4,
            generated_at="2026-07-26T20:00:00",
        ),
        execution_time=0.25,
    )

    app = Application()

    result = app.run(
        "performance/datasets/customer_data_stress_test.csv"
    )

    assert result.success

    assert result.pipeline_report is not None

    assert (
        result.pipeline_report.ai_report
        is not None
    )

    assert (
        result.pipeline_report.ai_report.executive_summary
        == "Executive summary."
    )

    assert (
        len(
            result.pipeline_report.ai_report.recommendations
        )
        == 2
    )

    assert (
        len(
            result.pipeline_report.ai_report.explanations
        )
        == 2
    )

    assert (
        result.pipeline_report.ai_report.narrative
        == "Business narrative."
    )

    assert (
        result.pipeline_report.ai_report.model
        == "fake-model"
    )

    assert (
        result.pipeline_report.ai_report.provider
        == "fake-provider"
    )

    assert (
        result.pipeline_report.ai_report.prompt_count
        == 4
    )

    assert result.execution_time >= 0