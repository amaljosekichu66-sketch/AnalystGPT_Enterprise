"""
Export Tests for Semantic Profile, Lineage, and AI Demarcation.

Sprint 14 Remediation — Data Profiling, Null Governance & Visual Analytics.
"""

from __future__ import annotations

import tempfile
from datetime import UTC, datetime
from pathlib import Path

import pytest

from src.reporting.exporters.pdf_report_exporter import PdfReportExporter
from src.reporting.exporters.text_report_exporter import TextReportExporter
from src.reporting.structured_report import StructuredReport


@pytest.fixture
def mock_structured_report() -> StructuredReport:
    return StructuredReport(
        title="Enterprise Remediation Test Report",
        executive_summary="Executive analytical summary covering key business distributions.",
        kpis={"Total Revenue": "$45,000", "Active Accounts": "1,250"},
        analytics={
            "dataset_profile": {
                "columns": {
                    "Revenue": {
                        "physical_dtype": "object",
                        "semantic_type": "numeric_measure",
                        "analytical_role": "measure",
                        "missing_count": 0,
                        "missing_percentage": 0.0,
                        "unique_count": 50,
                        "uniqueness_percentage": 50.0,
                        "governance_recommendation": "impute_median",
                    },
                    "Phone": {
                        "physical_dtype": "object",
                        "semantic_type": "phone",
                        "analytical_role": "contact_identifier",
                        "missing_count": 2,
                        "missing_percentage": 2.0,
                        "unique_count": 98,
                        "uniqueness_percentage": 100.0,
                        "governance_recommendation": "preserve_nulls",
                    },
                }
            },
            "descriptive_statistics": {"total_rows": 100, "total_columns": 2},
        },
        recommendations=["Optimize marketing campaign focus", "Enforce contact validation"],
        generated_at=datetime.now(UTC),
    )


def test_text_report_contains_semantic_profile(mock_structured_report: StructuredReport):
    exporter = TextReportExporter()
    with tempfile.TemporaryDirectory() as tmp_dir:
        out_file = Path(tmp_dir) / "test_report.txt"
        exported_path = exporter.export(
            mock_structured_report,
            output_path=out_file,
            lineage={"pipeline_run_id": 999, "source_version_id": "src-uuid-123"},
        )
        assert Path(exported_path).exists()
        content = Path(exported_path).read_text()

        # Check semantic profile table presence
        assert "COLUMN SEMANTIC PROFILE & GOVERNANCE" in content
        assert "Revenue" in content
        assert "numeric_measure" in content
        assert "Phone" in content
        assert "contact_identifier" in content
        assert "Pipeline Run ID       : 999" in content


def test_pdf_report_generates_valid_pdf_with_semantic_profile(mock_structured_report: StructuredReport):
    exporter = PdfReportExporter()
    with tempfile.TemporaryDirectory() as tmp_dir:
        out_file = Path(tmp_dir) / "test_report.pdf"
        exported_path = exporter.export(
            mock_structured_report,
            output_path=out_file,
            lineage={"pipeline_run_id": 999, "source_version_id": "src-uuid-123"},
        )
        assert Path(exported_path).exists()
        raw_bytes = Path(exported_path).read_bytes()
        assert raw_bytes.startswith(b"%PDF-1.")
        assert b"%%EOF" in raw_bytes[-1024:]
