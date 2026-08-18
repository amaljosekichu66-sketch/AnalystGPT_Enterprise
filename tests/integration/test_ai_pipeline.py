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
    "src.ai.ai_manager.AIManager.generate_ai_report"
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

    try:
        result = app.run(
            "performance/datasets/customer_data_stress_test.csv"
        )

        assert result.success
        assert result.pipeline_report is not None
        assert result.ai_job_id is not None
        assert result.ai_job_status in {"PENDING", "GENERATING", "READY"}

        # Fetch persisted AI report through AIJobService
        ai_job_data = app.ai_job_service.get_job_with_report(result.ai_job_id)
        assert ai_job_data is not None
        ai_rep = ai_job_data.get("ai_report")
        if ai_rep is not None:
            assert ai_rep["executive_summary"] == "Executive summary."
            assert len(ai_rep["recommendations"]) == 2
            assert len(ai_rep["explanations"]) == 2
            assert ai_rep["narrative"] == "Business narrative."
            assert ai_rep["model"] == "fake-model"
            assert ai_rep["provider"] == "fake-provider"

        assert result.execution_time >= 0
    finally:
        app.shutdown()