"""
Tests for the Application orchestration layer.
"""

from pathlib import Path

from unittest.mock import patch

from src.ai.ai_report import AIReport
from src.ai.ai_result import AIResult
from src.application.app import Application
from src.application.pipeline_report import PipelineReport
from src.application.pipeline_result import PipelineResult
from src.reporting.reporting_report import ReportingReport

SAMPLE_DATASET = Path(
    "sample_data/customer_data.csv"
)


def _get_mock_ai_result():
    return AIResult(
        success=True,
        ai_report=AIReport(
            executive_summary="Summary",
            recommendations=["Rec"],
            explanations=["Expl"],
            narrative="Narrative",
            model="gemma3:4b",
            provider="ollama",
            execution_time=0.1,
        ),
    )


def test_application_run_success() -> None:
    """
    Application should successfully execute the
    complete analytics pipeline.
    """

    application = Application()

    try:
        with patch.object(
            application.ai_manager,
            "generate_ai_report",
            return_value=_get_mock_ai_result(),
        ):
            result = application.run(
                str(SAMPLE_DATASET)
            )

            assert isinstance(
                result,
                PipelineResult,
            )

            assert result.success is True

            assert result.pipeline_report is not None

            assert isinstance(
                result.pipeline_report,
                PipelineReport,
            )

            assert isinstance(
                result.pipeline_report.reporting_report,
                ReportingReport,
            )

            assert result.output_path is not None

            assert Path(
                result.output_path
            ).exists()

            assert result.execution_time is not None

            assert result.execution_time > 0

            assert result.error is None
            assert result.ai_job_id is not None
            assert result.ai_job_status in {"PENDING", "GENERATING", "READY"}
    finally:
        application.shutdown()


def test_application_run_invalid_path() -> None:
    """
    Application should gracefully handle an
    invalid dataset path.
    """

    application = Application()

    try:
        result = application.run(
            "sample_data/file_does_not_exist.csv"
        )

        assert isinstance(
            result,
            PipelineResult,
        )

        assert result.success is False

        assert result.pipeline_report is None

        assert result.output_path is None

        assert result.error is not None

        assert result.execution_time is not None

        assert result.execution_time >= 0
    finally:
        application.shutdown()


def test_pipeline_result_contract() -> None:
    """
    Verify the PipelineResult contract produced
    by the Application layer.
    """

    application = Application()

    try:
        with patch.object(
            application.ai_manager,
            "generate_ai_report",
            return_value=_get_mock_ai_result(),
        ):
            result = application.run(
                str(SAMPLE_DATASET)
            )

            assert hasattr(
                result,
                "success",
            )

            assert hasattr(
                result,
                "pipeline_report",
            )

            assert hasattr(
                result,
                "output_path",
            )

            assert hasattr(
                result,
                "execution_time",
            )

            assert hasattr(
                result,
                "error",
            )

            assert hasattr(
                result,
                "ai_job_id",
            )

            assert hasattr(
                result,
                "ai_job_status",
            )

            assert result.pipeline_report is not None

            assert hasattr(
                result.pipeline_report,
                "reporting_report",
            )

            assert hasattr(
                result.pipeline_report,
                "ai_report",
            )
    finally:
        application.shutdown()