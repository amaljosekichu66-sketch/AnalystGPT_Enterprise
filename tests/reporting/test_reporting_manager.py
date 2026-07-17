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

    result = manager.generate_report(
        build_analytics_report()
    )

    assert isinstance(result, ReportingReport)


def test_reporting_manager_contains_required_sections():

    manager = ReportingManager()

    result = manager.generate_report(
        build_analytics_report()
    )

    assert result.report is not None
    assert result.export_path is not None
    assert result.execution_time >= 0


def test_reporting_manager_exports_report():

    manager = ReportingManager()

    result = manager.generate_report(
        build_analytics_report()
    )

    assert result.export_path.endswith(".txt")