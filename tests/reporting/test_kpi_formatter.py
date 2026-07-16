from src.reporting.kpi_formatter import KPIFormatter


def test_kpi_formatter_returns_dictionary():

    analytics_report = {
        "descriptive_statistics": {},
        "numerical_analysis": {},
        "categorical_analysis": {},
        "correlation_analysis": {},
        "distribution_analysis": {},
    }

    formatter = KPIFormatter()

    result = formatter.format_kpis(
        analytics_report
    )

    assert isinstance(result, dict)


def test_kpi_formatter_reports_available_sections():

    analytics_report = {
        "descriptive_statistics": {},
        "numerical_analysis": {},
        "categorical_analysis": {},
        "correlation_analysis": {},
        "distribution_analysis": {},
    }

    formatter = KPIFormatter()

    result = formatter.format_kpis(
        analytics_report
    )

    assert result["Analytics Sections"] == 5
    assert result["Descriptive Statistics"] == "Available"
    assert result["Numerical Analysis"] == "Available"
    assert result["Categorical Analysis"] == "Available"
    assert result["Correlation Analysis"] == "Available"
    assert result["Distribution Analysis"] == "Available"


def test_kpi_formatter_handles_empty_report():

    formatter = KPIFormatter()

    result = formatter.format_kpis({})

    assert result["Analytics Sections"] == 0
    assert result["Descriptive Statistics"] == "Unavailable"
    assert result["Numerical Analysis"] == "Unavailable"
    assert result["Categorical Analysis"] == "Unavailable"
    assert result["Correlation Analysis"] == "Unavailable"
    assert result["Distribution Analysis"] == "Unavailable"