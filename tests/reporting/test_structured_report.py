from src.reporting.structured_report import StructuredReport


def test_structured_report_stores_all_sections():

    report = StructuredReport(
        title="Sales Report",
        executive_summary=[
            "Summary 1",
            "Summary 2",
        ],
        kpis={
            "Rows": 100,
        },
        analytics={
            "analysis": "completed",
        },
        recommendations=[
            "Recommendation 1",
        ],
    )

    assert report.title == "Sales Report"
    assert report.executive_summary == [
        "Summary 1",
        "Summary 2",
    ]
    assert report.kpis["Rows"] == 100
    assert report.analytics["analysis"] == "completed"
    assert report.recommendations == [
        "Recommendation 1",
    ]


def test_structured_report_to_dict_returns_dictionary():

    report = StructuredReport(
        title="Customer Report",
        executive_summary=[
            "Completed",
        ],
        kpis={
            "Rows": 25,
        },
        analytics={
            "status": "ok",
        },
        recommendations=[
            "Continue monitoring",
        ],
    )

    result = report.to_dict()

    assert isinstance(result, dict)

    assert result["title"] == "Customer Report"
    assert result["executive_summary"] == [
        "Completed",
    ]
    assert result["kpis"]["Rows"] == 25
    assert result["analytics"]["status"] == "ok"
    assert result["recommendations"] == [
        "Continue monitoring",
    ]


def test_structured_report_supports_empty_sections():

    report = StructuredReport(
        title="Empty Report",
        executive_summary=[],
        kpis={},
        analytics={},
        recommendations=[],
    )

    result = report.to_dict()

    assert result["executive_summary"] == []
    assert result["kpis"] == {}
    assert result["analytics"] == {}
    assert result["recommendations"] == []