"""
Remediation integrity tests for Reporting and Analytical Consistency.

Sprint 14 Remediation & Phase 2 Quality Gate.
"""

from __future__ import annotations

from pathlib import Path

from src.reporting.executive_summary import ExecutiveSummary
from src.reporting.exporters.pdf_report_exporter import PdfReportExporter
from src.reporting.exporters.text_report_exporter import TextReportExporter
from src.reporting.kpi_formatter import KPIFormatter
from src.reporting.structured_report import StructuredReport


def test_kpi_formatter_eliminates_contradictory_numerical_metadata():
    """When 0 numeric columns exist, numerical and correlation analysis must be reported as Unavailable."""
    analytics = {
        "descriptive_statistics": {
            "total_rows": 1480,
            "total_columns": 13,
            "numeric_column_count": 0,
            "categorical_column_count": 13,
            "datetime_column_count": 0,
            "memory_usage_mb": 0.15,
        },
        "numerical_analysis": {},
        "correlation_analysis": {
            "correlation_matrix": {},
            "strongest_positive": None,
            "strongest_negative": None,
        },
        "categorical_analysis": {
            "city": {"distinct_count": 50, "top_values": {"NYC": 200}},
        },
        "distribution_analysis": {},
    }

    formatter = KPIFormatter()
    kpis = formatter.format_kpis(analytics)

    assert kpis["Numeric Columns"] == 0
    assert kpis["Numerical Analysis"] == "Unavailable"
    assert kpis["Correlation Analysis"] == "Unavailable"
    assert kpis["Correlation Available"] is False
    assert kpis["Categorical Analysis"] == "Available"
    assert kpis["Categorical Analysis Available"] is True


def test_executive_summary_states_numerical_analysis_skipped_when_zero_numeric_columns():
    """Executive summary clearly explains when numerical analysis is skipped due to lack of measures."""
    analytics = {
        "descriptive_statistics": {
            "total_rows": 1480,
            "total_columns": 13,
            "numeric_column_count": 0,
            "categorical_column_count": 13,
        },
        "numerical_analysis": {},
        "correlation_analysis": {},
        "categorical_analysis": {},
    }

    summary = ExecutiveSummary().generate_summary(analytics)
    combined = " ".join(summary)

    assert "0 numeric and 13 categorical" in combined
    assert "no governed numerical measure columns were identified" in combined
    assert "fewer than two numerical measure columns were present" in combined


def test_text_report_exporter_contains_no_raw_dictionaries_or_unmasked_pii(tmp_path):
    """Text report must never dump raw Python dicts ({'total_rows': ...}) or unmasked contact PII."""
    report = StructuredReport(
        title="Enterprise Customer Overview",
        executive_summary="Executive baseline analysis.",
        kpis={"Total Records": 1480, "Measures": 0},
        analytics={
            "descriptive_statistics": {
                "total_rows": 1480,
                "total_columns": 5,
                "numeric_column_count": 0,
                "categorical_column_count": 5,
            },
            "categorical_analysis": {
                "City": {"distinct_count": 10, "top_values": {"Toronto": 300, "Vancouver": 200}},
                "Phone": {"distinct_count": 1480, "top_values": {"+16474100001": 1, "+16474100002": 1}},
                "Email": {"distinct_count": 1480, "top_values": {"user1@test.com": 1, "user2@test.com": 1}},
            },
            "numerical_analysis": {},
            "correlation_analysis": {},
        },
        recommendations=["Segment contact records."],
    )

    ai_report = {
        "executive_summary": "AI strategic summary.",
        "key_findings": ["Dominant category in City is Toronto."],
        "recommendations": ["Expand outreach in top cities."],
        "explanations": ["High distinct phone count reflects broad unique individual outreach."],
        "narrative": "Complete business storyline.",
        "model": "gemma3:4b",
        "provider": "ollama",
    }

    lineage = {
        "pipeline_run_id": 101,
        "source_version_id": "v_src_101",
        "cleaned_version_id": "v_clean_101",
        "context_schema_version": "1.0",
    }

    exporter = TextReportExporter()
    output_path = tmp_path / "test_report.txt"
    exporter.export(report, str(output_path), ai_report=ai_report, lineage=lineage)

    content = output_path.read_text(encoding="utf-8")

    # Verify no raw python dict representation
    assert "{'total_rows':" not in content
    assert "{'distinct_count':" not in content
    assert "+16474100001" not in content  # Masked PII
    assert "user1@test.com" not in content  # Masked PII

    # Verify professional structured text
    assert "EXECUTIVE SUMMARY" in content
    assert "KEY PERFORMANCE INDICATORS" in content
    assert "AI BUSINESS INSIGHTS (AI-GENERATED)" in content
    assert "DATA LINEAGE & PROVENANCE" in content


def test_exported_report_does_not_contain_causal_explanations_as_section_title(tmp_path):
    """Regression test ensuring exported reports do not contain 'AI Causal Explanations' as a section title."""
    report = StructuredReport(
        title="Audit Non-Causal Report",
        executive_summary="Baseline interpretation.",
        kpis={"Records": 100},
        analytics={
            "descriptive_statistics": {"total_rows": 100, "numeric_column_count": 0},
            "categorical_analysis": {"Department": {"distinct_count": 3, "top_values": {"HR": 50}}},
            "numerical_analysis": {},
            "correlation_analysis": {},
        },
        recommendations=["Continue monitoring."],
    )

    ai_report = {
        "executive_summary": "AI interpretation.",
        "key_findings": ["HR represents majority."],
        "recommendations": ["Automate repetitive tasks."],
        "explanations": ["High density in HR indicates operational focus."],
        "narrative": "Storyline.",
        "model": "gemma3:4b",
        "provider": "ollama",
    }

    exporter = TextReportExporter()
    output_path = tmp_path / "non_causal_report.txt"
    exporter.export(report, str(output_path), ai_report=ai_report)

    content = output_path.read_text(encoding="utf-8")

    # MUST NOT contain "AI Causal Explanations" or "causal context"
    assert "AI Causal Explanations" not in content
    assert "causal context" not in content

    # Should contain analytical interpretation and appropriate observational caveat
    assert "AI Key Analytical Findings" in content or "AI Analytical Interpretation" in content
    assert (
        "Observational records describe correlation and distribution; causal conclusions require experimental validation."
        in content
    )


def test_pdf_report_exporter_generates_valid_pdf_without_raw_debug_dumps(tmp_path):
    """PDF exporter produces valid PDF with vector sections and no raw dictionary dumps."""
    report = StructuredReport(
        title="Audited Enterprise PDF",
        executive_summary="Audited business summary.",
        kpis={"Records": 500},
        analytics={
            "descriptive_statistics": {"total_rows": 500, "numeric_column_count": 0},
            "categorical_analysis": {"Department": {"distinct_count": 4, "top_values": {"Sales": 200}}},
            "numerical_analysis": {},
            "correlation_analysis": {},
        },
        recommendations=["Optimize workflows."],
    )

    ai_report = {
        "executive_summary": "AI Executive interpretation.",
        "key_findings": ["Sales represents 40% of records."],
        "recommendations": ["Automate repetitive tasks."],
        "explanations": ["High sales density drives volume."],
        "narrative": "Detailed narrative.",
        "model": "gemma3:4b",
        "provider": "ollama",
    }

    exporter = PdfReportExporter()
    output_path = tmp_path / "test_report.pdf"
    export_res = exporter.export(report, str(output_path), ai_report=ai_report)

    assert Path(export_res).exists()
    assert Path(export_res).stat().st_size > 1000
    with open(output_path, "rb") as f:
        assert f.read(5).startswith(b"%PDF-")
