from pathlib import Path

from src.reporting.exporters.text_report_exporter import (
    TextReportExporter,
)
from src.reporting.structured_report import StructuredReport


def test_text_report_exporter_creates_report_file(tmp_path):

    report = StructuredReport(
        title="Sales Report",
        executive_summary=[
            "Summary",
        ],
        kpis={
            "Rows": 100,
        },
        analytics={
            "Status": "Completed",
        },
        recommendations=[
            "Continue monitoring",
        ],
    )

    exporter = TextReportExporter()

    output_file = tmp_path / "report.txt"

    export_path = exporter.export(
        report,
        str(output_file),
    )

    assert Path(export_path).exists()


def test_text_report_exporter_writes_report_contents(tmp_path):

    report = StructuredReport(
        title="Customer Report",
        executive_summary=[
            "Executive Summary",
        ],
        kpis={
            "Rows": 50,
        },
        analytics={
            "Analysis": "Complete",
        },
        recommendations=[
            "Review findings",
        ],
    )

    exporter = TextReportExporter()

    output_file = tmp_path / "customer_report.txt"

    exporter.export(
        report,
        str(output_file),
    )

    content = output_file.read_text(
        encoding="utf-8",
    )

    assert "Customer Report" in content
    assert "EXECUTIVE SUMMARY" in content
    assert "KEY PERFORMANCE INDICATORS" in content
    assert "ANALYTICS RESULTS" in content
    assert "RECOMMENDATIONS" in content


def test_text_report_exporter_returns_export_path(tmp_path):

    report = StructuredReport(
        title="Report",
        executive_summary=[],
        kpis={},
        analytics={},
        recommendations=[],
    )

    exporter = TextReportExporter()

    output_file = tmp_path / "output.txt"

    export_path = exporter.export(
        report,
        str(output_file),
    )

    assert export_path == str(output_file)


def test_text_report_exporter_handles_empty_sections(tmp_path):

    report = StructuredReport(
        title="Empty Report",
        executive_summary=[],
        kpis={},
        analytics={},
        recommendations=[],
    )

    exporter = TextReportExporter()

    output_file = tmp_path / "empty_report.txt"

    exporter.export(
        report,
        str(output_file),
    )

    content = output_file.read_text(
        encoding="utf-8",
    )

    assert "No recommendations available." in content