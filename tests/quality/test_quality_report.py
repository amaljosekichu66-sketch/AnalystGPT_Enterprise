"""
Unit tests for the QualityReport module.
"""

from src.quality.quality_report import QualityReport


def test_quality_report():

    results = {
        "completeness": {},
        "validity": {},
        "consistency": {},
        "uniqueness": {},
        "outliers": {},
    }

    report = QualityReport(
        report=results,
        execution_time=0.5,
    )

    assert isinstance(
        report,
        QualityReport,
    )

    assert report.report == results

    report_dict = report.to_dict()

    assert report_dict["report"] == results

    assert report_dict["execution_time"] == 0.5