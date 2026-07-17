"""
Tests for the Application orchestration layer.
"""

from pathlib import Path

from src.application.app import Application
from src.application.pipeline_result import PipelineResult
from src.reporting.reporting_report import ReportingReport


SAMPLE_DATASET = Path(
    "sample_data/customer_data.csv"
)


def test_application_run_success() -> None:
    """
    Application should successfully execute the
    complete analytics pipeline.
    """

    application = Application()

    result = application.run(
        str(SAMPLE_DATASET)
    )

    assert isinstance(
        result,
        PipelineResult,
    )

    assert result.success is True

    assert isinstance(
        result.reporting_report,
        ReportingReport,
    )

    assert result.output_path is not None

    assert Path(
        result.output_path
    ).exists()

    assert result.execution_time is not None

    assert result.execution_time > 0

    assert result.error is None


def test_application_run_invalid_path() -> None:
    """
    Application should gracefully handle an
    invalid dataset path.
    """

    application = Application()

    result = application.run(
        "sample_data/file_does_not_exist.csv"
    )

    assert isinstance(
        result,
        PipelineResult,
    )

    assert result.success is False

    assert result.reporting_report is None

    assert result.output_path is None

    assert result.error is not None

    assert result.execution_time is not None

    assert result.execution_time >= 0


def test_pipeline_result_contract() -> None:
    """
    Verify the PipelineResult contract produced
    by the Application layer.
    """

    application = Application()

    result = application.run(
        str(SAMPLE_DATASET)
    )

    assert hasattr(
        result,
        "success",
    )

    assert hasattr(
        result,
        "reporting_report",
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