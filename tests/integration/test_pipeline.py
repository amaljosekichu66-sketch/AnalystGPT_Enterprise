"""
Integration test for the complete AnalystGPT Enterprise pipeline.
"""

from pathlib import Path

from pandas import DataFrame

from src.analytics.analytics_manager import AnalyticsManager
from src.cleaning.cleaning_manager import CleaningManager
from src.quality.quality_manager import QualityManager
from src.reporting.reporting_manager import ReportingManager
from src.upload.upload_manager import UploadManager


def test_complete_pipeline():
    """
    Verify the complete AnalystGPT Enterprise pipeline executes successfully.
    """

    upload_manager = UploadManager()
    cleaning_manager = CleaningManager()
    quality_manager = QualityManager()
    analytics_manager = AnalyticsManager()
    reporting_manager = ReportingManager()

    # ---------------------------------------------------------
    # Upload
    # ---------------------------------------------------------

    dataframe = upload_manager.upload(
        "sample_data/customer_data.csv"
    )

    assert isinstance(dataframe, DataFrame)

    # ---------------------------------------------------------
    # Cleaning
    # ---------------------------------------------------------

    cleaned_dataframe = cleaning_manager.clean(
        dataframe
    )

    assert isinstance(cleaned_dataframe, DataFrame)

    # ---------------------------------------------------------
    # Quality
    # ---------------------------------------------------------

    quality_report = quality_manager.assess(
        cleaned_dataframe
    )

    assert isinstance(
        quality_report,
        dict,
    )

    # ---------------------------------------------------------
    # Analytics
    # ---------------------------------------------------------

    analytics_report = analytics_manager.analyze(
        cleaned_dataframe
    )

    assert isinstance(
        analytics_report,
        dict,
    )

    expected_sections = [
        "descriptive_statistics",
        "numerical_analysis",
        "categorical_analysis",
        "correlation_analysis",
        "distribution_analysis",
    ]

    for section in expected_sections:
        assert section in analytics_report

    # ---------------------------------------------------------
    # Reporting
    # ---------------------------------------------------------

    reporting_report = reporting_manager.generate_report(
        analytics_report
    )

    assert isinstance(
        reporting_report,
        dict,
    )

    expected_report_sections = [
        "report",
        "export_path",
        "execution_time",
    ]

    for section in expected_report_sections:
        assert section in reporting_report

    report_path = Path(
        reporting_report["export_path"]
    )

    assert report_path.exists()

    report_content = report_path.read_text(
        encoding="utf-8",
    )

    assert "EXECUTIVE SUMMARY" in report_content
    assert "KEY PERFORMANCE INDICATORS" in report_content
    assert "ANALYTICS RESULTS" in report_content
    assert "RECOMMENDATIONS" in report_content