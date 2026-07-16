from src.reporting.report_builder import ReportBuilder
from src.reporting.structured_report import StructuredReport


def test_report_builder_returns_structured_report():

    builder = ReportBuilder()

    report = builder.build_report(
        title="Sales Report",
        executive_summary=[
            "Summary",
        ],
        kpis={
            "Rows": 100,
        },
        analytics={
            "analysis": "complete",
        },
        recommendations=[
            "Recommendation",
        ],
    )

    assert isinstance(
        report,
        StructuredReport,
    )


def test_report_builder_populates_all_sections():

    builder = ReportBuilder()

    report = builder.build_report(
        title="Customer Report",
        executive_summary=[
            "Executive Summary",
        ],
        kpis={
            "Rows": 50,
        },
        analytics={
            "status": "completed",
        },
        recommendations=[
            "Review findings",
        ],
    )

    assert report.title == "Customer Report"
    assert report.executive_summary == [
        "Executive Summary",
    ]
    assert report.kpis["Rows"] == 50
    assert report.analytics["status"] == "completed"
    assert report.recommendations == [
        "Review findings",
    ]


def test_report_builder_supports_empty_sections():

    builder = ReportBuilder()

    report = builder.build_report(
        title="Empty Report",
        executive_summary=[],
        kpis={},
        analytics={},
        recommendations=[],
    )

    assert report.executive_summary == []
    assert report.kpis == {}
    assert report.analytics == {}
    assert report.recommendations == []