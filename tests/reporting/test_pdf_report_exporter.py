"""
Tests for PDF Report Exporter.

Sprint 14 Phase 5 — Reporting & PDF Export Stabilization.
"""

from pathlib import Path
import pytest

from src.reporting.exporters.pdf_report_exporter import PdfReportExporter
from src.reporting.structured_report import StructuredReport


def test_pdf_report_exporter_creates_valid_pdf(tmp_path):
    report = StructuredReport(
        title="Enterprise Performance Report",
        executive_summary="Company performed well across all evaluated quarters.",
        kpis={
            "Total Revenue": "$1,250,000",
            "Active Users": 45000,
            "Growth Rate": "18.5%",
        },
        analytics={
            "descriptive_statistics": {
                "numeric_columns": 5,
                "row_count": 1000,
            },
            "correlation_analysis": {
                "revenue_vs_spend": 0.88,
            },
        },
        recommendations=[
            "Expand regional distribution channels.",
            "Optimize inventory holding costs.",
        ],
        metadata={
            "environment": "production",
            "version": "1.0",
        },
    )

    exporter = PdfReportExporter()
    output_file = tmp_path / "report.pdf"

    export_path = exporter.export(report, str(output_file))

    assert Path(export_path).exists()
    assert export_path == str(output_file.resolve())

    # Verify standard PDF magic header
    with open(output_file, "rb") as f:
        header = f.read(5)
        assert header.startswith(b"%PDF-")

    # Verify file is non-empty
    assert output_file.stat().st_size > 500


def test_pdf_report_exporter_with_ai_insights_and_lineage(tmp_path):
    report = StructuredReport(
        title="Quarterly AI-Augmented Analytics",
        executive_summary="Deterministic analytical overview.",
        kpis={"KPI_A": 100, "KPI_B": 200},
        analytics={"metrics": {"score": 99.5}},
        recommendations=["Follow deterministic guideline."],
    )

    ai_report = {
        "executive_summary": "AI identified underlying demand shifts.",
        "recommendations": ["AI Recommendation 1: Diversify suppliers."],
        "explanations": ["Revenue growth was driven by seasonal uptick."],
        "narrative": "A comprehensive operational review shows resilience.",
        "model": "qwen2.5-coder:7b",
        "provider": "ollama",
    }

    lineage = {
        "pipeline_run_id": 42,
        "source_version_id": "src_ver_abc123",
        "cleaned_version_id": "clean_ver_def456",
        "cleaning_execution_id": "clean_exec_789",
        "context_schema_version": "1.0",
    }

    exporter = PdfReportExporter()
    output_file = tmp_path / "ai_lineage_report.pdf"

    export_path = exporter.export(
        report=report,
        output_path=str(output_file),
        ai_report=ai_report,
        lineage=lineage,
    )

    assert Path(export_path).exists()
    with open(output_file, "rb") as f:
        header = f.read(5)
        assert header.startswith(b"%PDF-")


def test_pdf_report_exporter_handles_empty_sections(tmp_path):
    report = StructuredReport(
        title="Sparse Report",
        executive_summary="",
        kpis={},
        analytics={},
        recommendations=[],
        metadata={},
    )

    exporter = PdfReportExporter()
    output_file = tmp_path / "sparse.pdf"

    export_path = exporter.export(report, str(output_file))

    assert Path(export_path).exists()
    with open(output_file, "rb") as f:
        assert f.read(5).startswith(b"%PDF-")


def test_pdf_report_exporter_resolves_directory_destination(tmp_path):
    report = StructuredReport(
        title="Directory Destination Report",
        executive_summary="Summary",
        kpis={},
        analytics={},
        recommendations=[],
    )

    exporter = PdfReportExporter()
    export_path = exporter.export(report, output_path=str(tmp_path))

    assert Path(export_path).exists()
    assert Path(export_path).name == "analystgpt_report.pdf"
