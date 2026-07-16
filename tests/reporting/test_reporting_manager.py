from src.reporting.reporting_manager import ReportingManager


def test_reporting_manager_generates_report():

    analytics_report = {
        "descriptive_statistics": {},
        "numerical_analysis": {},
        "categorical_analysis": {},
        "correlation_analysis": {},
        "distribution_analysis": {},
    }

    manager = ReportingManager()

    result = manager.generate_report(
        analytics_report
    )

    assert isinstance(result, dict)


def test_reporting_manager_contains_required_sections():

    analytics_report = {
        "descriptive_statistics": {},
        "numerical_analysis": {},
        "categorical_analysis": {},
        "correlation_analysis": {},
        "distribution_analysis": {},
    }

    manager = ReportingManager()

    result = manager.generate_report(
        analytics_report
    )

    assert "report" in result
    assert "export_path" in result
    assert "execution_time" in result


def test_reporting_manager_exports_report():

    analytics_report = {
        "descriptive_statistics": {},
        "numerical_analysis": {},
        "categorical_analysis": {},
        "correlation_analysis": {},
        "distribution_analysis": {},
    }

    manager = ReportingManager()

    result = manager.generate_report(
        analytics_report
    )

    assert result["export_path"].endswith(
        ".txt"
    )