from src.reporting.executive_summary import ExecutiveSummary


def test_executive_summary_generates_summary():

    analytics_report = {
        "descriptive_statistics": {},
        "numerical_analysis": {},
        "categorical_analysis": {},
        "correlation_analysis": {},
        "distribution_analysis": {},
    }

    summary = ExecutiveSummary().generate_summary(
        analytics_report
    )

    assert isinstance(summary, list)
    assert len(summary) > 0


def test_executive_summary_reports_completed_sections():

    analytics_report = {
        "descriptive_statistics": {},
        "numerical_analysis": {},
        "categorical_analysis": {},
        "correlation_analysis": {},
        "distribution_analysis": {},
    }

    summary = ExecutiveSummary().generate_summary(
        analytics_report
    )

    combined = " ".join(summary)

    assert "Descriptive statistics" in combined
    assert "Numerical variables" in combined
    assert "Categorical variables" in combined
    assert "Correlation analysis" in combined
    assert "Distribution analysis" in combined


def test_executive_summary_handles_empty_report():

    analytics_report = {}

    summary = ExecutiveSummary().generate_summary(
        analytics_report
    )

    assert isinstance(summary, list)
    assert len(summary) > 0