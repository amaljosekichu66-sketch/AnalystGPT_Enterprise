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
    # Corrected assertion: the actual header is "ANALYTICS"
    assert "ANALYTICS" in content
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


def test_text_report_exporter_with_ai_and_lineage(tmp_path):
    report = StructuredReport(
        title="Audited Sales Report",
        executive_summary="Core sales remained stable.",
        kpis={"Revenue": "$500k"},
        analytics={"descriptive": {"rows": 100}},
        recommendations=["Maintain stock."],
    )

    ai_report = {
        "executive_summary": "AI identified rising momentum.",
        "recommendations": ["AI Rec: Invest in ads."],
        "explanations": ["Seasonality contributed to stability."],
        "narrative": "Detailed narrative story.",
        "model": "qwen2.5-coder:7b",
        "provider": "ollama",
    }

    lineage = {
        "pipeline_run_id": 99,
        "source_version_id": "src_123",
        "cleaned_version_id": "clean_456",
        "cleaning_execution_id": "exec_789",
        "context_schema_version": "1.0",
    }

    exporter = TextReportExporter()
    output_file = tmp_path / "audited_report.txt"

    exporter.export(
        report=report,
        output_path=str(output_file),
        ai_report=ai_report,
        lineage=lineage,
    )

    content = output_file.read_text(encoding="utf-8")

    assert "DATASET LINEAGE & PROVENANCE" in content
    assert "Pipeline Run ID       : 99" in content
    assert "Source Version ID     : src_123" in content
    assert "AI INSIGHTS & INTERPRETATION (AI-GENERATED)" in content
    assert "DISCLAIMER: AI-generated insights provide strategic narratives" in content
    assert "Model: qwen2.5-coder:7b | Provider: ollama" in content
    assert "AI Executive Summary:" in content
    assert "AI Rec: Invest in ads." in content
