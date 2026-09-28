from pathlib import Path

from src.analytics.analytics_report import AnalyticsReport
from src.reporting.reporting_manager import ReportingManager
from src.reporting.reporting_report import ReportingReport


def build_analytics_report():
    return AnalyticsReport(
        report={
            "descriptive_statistics": {},
            "numerical_analysis": {},
            "categorical_analysis": {},
            "correlation_analysis": {},
            "distribution_analysis": {},
        },
        execution_time=0.01,
    )


def test_reporting_manager_generates_report():
    manager = ReportingManager()
    result = manager.generate_report(build_analytics_report())
    assert isinstance(result, ReportingReport)


def test_reporting_manager_contains_required_sections():
    manager = ReportingManager()
    result = manager.generate_report(build_analytics_report())
    assert result.report is not None
    assert result.export_path is not None
    assert result.execution_time >= 0


def test_reporting_manager_exports_report():
    manager = ReportingManager()
    result = manager.generate_report(build_analytics_report())
    assert result.export_path.endswith(".txt")


def test_reporting_manager_export_text_and_pdf(tmp_path):
    manager = ReportingManager()
    rep = manager.generate_report(build_analytics_report())

    text_out = tmp_path / "custom.txt"
    pdf_out = tmp_path / "custom.pdf"

    text_path = manager.export_text(rep.report, output_path=str(text_out))
    pdf_path = manager.export_pdf(rep.report, output_path=str(pdf_out))

    assert Path(text_path).exists()
    assert Path(pdf_path).exists()
    assert Path(pdf_path).stat().st_size > 100
