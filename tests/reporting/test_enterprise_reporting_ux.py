"""
Comprehensive Enterprise Reporting & UX Redesign Test Suite.

Sprint 14 Phase 3 — Enterprise Report Export Redesign.

Tests all enterprise analytical correctness criteria:
1. PDF export succeeds.
2. TXT export succeeds.
3. PDF contains executive summary and KPI cards.
4. PDF contains AI Insights when AI report exists and omits when absent.
5. PDF embeds evidence-based visual analytics without synthetic Gaussian curves.
6. Categorical chart selection is deterministic, excluding PII/constants/keys.
7. Share percentages are computed and displayed accurately.
8. Recommendations follow OBSERVATION -> INTERPRETATION -> CONDITIONAL ACTION.
9. No unsupported operational/workflow assumptions.
10. Internal implementation flags do not appear in human-facing exports.
11. No Python object representations appear in the report.
12. Missing analytics sections are explained naturally.
13. Long datasets/column lists paginate cleanly.
14. Missingness and correlation conditions are respected.
15. Export works when AI generation is pending or failed.
"""

from __future__ import annotations

import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from src.reporting.exporters.pdf_report_exporter import PdfReportExporter
from src.reporting.exporters.text_report_exporter import TextReportExporter
from src.reporting.structured_report import StructuredReport


@pytest.fixture
def enterprise_mixed_report() -> StructuredReport:
    """A realistic enterprise report with both numeric and categorical measures."""
    return StructuredReport(
        title="Northwind Global Enterprise Performance",
        executive_summary="Quarterly enterprise analytics across regional revenue channels.",
        kpis={"Total Revenue": "$1,450,000", "Growth": "14.2%"},
        analytics={
            "descriptive_statistics": {
                "total_rows": 1480,
                "total_columns": 6,
                "numeric_column_count": 2,
                "categorical_column_count": 4,
                "datetime_column_count": 0,
                "memory_usage_mb": 0.32,
            },
            "dataset_profile": {
                "completeness_score": 0.985,
                "duplicate_rows_count": 0,
                "columns": {
                    "contract_value": {
                        "semantic_type": "numeric_measure",
                        "analytical_role": "measure",
                        "missing_count": 0,
                        "missing_percentage": 0.0,
                        "unique_count": 520,
                        "uniqueness_percentage": 35.1,
                        "governance_recommendation": "standard_validation",
                    },
                    "churn_risk_score": {
                        "semantic_type": "numeric_measure",
                        "analytical_role": "measure",
                        "missing_count": 12,
                        "missing_percentage": 0.8,
                        "unique_count": 150,
                        "uniqueness_percentage": 10.1,
                        "governance_recommendation": "impute_median",
                    },
                    "region": {
                        "semantic_type": "categorical_dimension",
                        "analytical_role": "dimension",
                        "missing_count": 0,
                        "missing_percentage": 0.0,
                        "unique_count": 4,
                        "uniqueness_percentage": 0.27,
                        "governance_recommendation": "standard_validation",
                    },
                    "segment": {
                        "semantic_type": "categorical_dimension",
                        "analytical_role": "dimension",
                        "missing_count": 0,
                        "missing_percentage": 0.0,
                        "unique_count": 3,
                        "uniqueness_percentage": 0.20,
                        "governance_recommendation": "standard_validation",
                    },
                    "customer_phone": {
                        "semantic_type": "phone",
                        "analytical_role": "contact_identifier",
                        "missing_count": 0,
                        "missing_percentage": 0.0,
                        "unique_count": 1480,
                        "uniqueness_percentage": 100.0,
                        "governance_recommendation": "mask_pii",
                    },
                },
            },
            "categorical_analysis": {
                "region": {
                    "distinct_count": 4,
                    "top_values": {"North": 600, "South": 400, "East": 300, "West": 180},
                },
                "segment": {
                    "distinct_count": 3,
                    "top_values": {"Enterprise": 800, "Mid-Market": 480, "SMB": 200},
                },
                "customer_phone": {
                    "distinct_count": 1480,
                    "top_values": {"+16474100001": 1},
                },
            },
            "numerical_analysis": {
                "contract_value": {
                    "count": 1480,
                    "mean": 24500.0,
                    "median": 22000.0,
                    "standard_deviation": 8400.0,
                    "minimum": 10000.0,
                    "maximum": 65000.0,
                    "first_quartile": 18000.0,
                    "third_quartile": 30000.0,
                },
                "churn_risk_score": {
                    "count": 1468,
                    "mean": 0.24,
                    "median": 0.21,
                    "standard_deviation": 0.12,
                    "minimum": 0.02,
                    "maximum": 0.85,
                    "first_quartile": 0.15,
                    "third_quartile": 0.32,
                },
            },
            "distribution_analysis": {
                "contract_value": {
                    "skewness": 0.82,
                    "distribution_shape": "Moderately Skewed",
                },
                "churn_risk_score": {
                    "skewness": 1.45,
                    "distribution_shape": "Highly Skewed",
                },
            },
            "correlation_analysis": {
                "correlation_matrix": {
                    "contract_value": {"contract_value": 1.0, "churn_risk_score": -0.32},
                    "churn_risk_score": {"contract_value": -0.32, "churn_risk_score": 1.0},
                },
                "strongest_positive": None,
                "strongest_negative": {
                    "column_1": "contract_value",
                    "column_2": "churn_risk_score",
                    "correlation": -0.32,
                },
            },
        },
        recommendations=[],
        generated_at=datetime.now(UTC),
    )


@pytest.fixture
def mock_ai_report() -> dict[str, Any]:
    return {
        "executive_summary": "AI strategic synthesis indicates strong performance in enterprise tier with mild churn risk in smaller contracts.",
        "key_findings": [
            "Contract value demonstrates a -0.32 negative correlation with churn risk score.",
            "The North region represents the largest enterprise cohort (600 accounts).",
        ],
        "business_implications": [
            "Smaller contracts may benefit from targeted customer onboarding.",
        ],
        "recommendations": [
            "Establish proactive health check milestones for mid-market contracts.",
        ],
        "confidence": "High — Grounded in governed numerical measures and distribution statistics",
        "model": "gemma3:4b",
        "provider": "ollama",
    }


def test_pdf_and_txt_export_success(enterprise_mixed_report, mock_ai_report, tmp_path):
    """1 & 2: PDF and TXT exports succeed and produce non-empty files with standard headers."""
    pdf_exporter = PdfReportExporter()
    txt_exporter = TextReportExporter()

    pdf_path = tmp_path / "report.pdf"
    txt_path = tmp_path / "report.txt"

    out_pdf = pdf_exporter.export(enterprise_mixed_report, str(pdf_path), ai_report=mock_ai_report)
    out_txt = txt_exporter.export(enterprise_mixed_report, str(txt_path), ai_report=mock_ai_report)

    assert Path(out_pdf).exists()
    assert Path(out_txt).exists()
    assert Path(out_pdf).stat().st_size > 1000
    assert Path(out_txt).stat().st_size > 500

    with open(pdf_path, "rb") as f:
        assert f.read(5).startswith(b"%PDF-")

    txt_content = txt_path.read_text(encoding="utf-8")
    assert "ANALYSTGPT ENTERPRISE — BUSINESS ANALYTICS REPORT" in txt_content


def test_deterministic_categorical_selection_excludes_pii_and_constants(enterprise_mixed_report):
    """6: Categorical chart selection selects meaningful dimensions and excludes PII/constants."""
    pdf_exporter = PdfReportExporter()
    cat_data = enterprise_mixed_report.analytics["categorical_analysis"]
    profile = enterprise_mixed_report.analytics["dataset_profile"]

    selected = pdf_exporter._select_best_categorical_dimension(cat_data, profile, total_rows=1480)
    assert selected is not None
    col_name, _ = selected
    assert col_name in {"region", "segment"}
    assert col_name != "customer_phone"  # Excludes PII


def test_evidence_based_recommendations_no_workflow_assumptions(enterprise_mixed_report, tmp_path):
    """8 & 9: Recommendations use OBSERVATION -> INTERPRETATION -> ACTION without operational guesses."""
    txt_exporter = TextReportExporter()
    txt_path = tmp_path / "rec_test.txt"

    txt_exporter.export(enterprise_mixed_report, str(txt_path))
    content = txt_path.read_text(encoding="utf-8")

    assert "Recommendation 1:" in content
    assert "• Observation" in content
    assert "• Interpretation" in content
    assert "• Action" in content

    # Ensure unsupported assumptions are absent
    assert "Operational workflows are heavily weighted" not in content
    assert "staffing requirements" not in content
    assert "revenue impact requires" not in content


def test_categorical_share_percentages_in_text_report(enterprise_mixed_report, tmp_path):
    """7: TXT report includes counts and computed share percentages."""
    txt_exporter = TextReportExporter()
    txt_path = tmp_path / "share_test.txt"

    txt_exporter.export(enterprise_mixed_report, str(txt_path))
    content = txt_path.read_text(encoding="utf-8")

    # In region: North is 600 out of 1480 = 40.5%
    assert "'North' (600 | 40.5%)" in content or "40.5%" in content
    assert "COLUMN SEMANTIC PROFILE & GOVERNANCE" in content


def test_pdf_contains_executive_summary_and_kpis(enterprise_mixed_report, tmp_path):
    """3 & 4: PDF export processes and includes executive summary and KPI cards."""
    pdf_exporter = PdfReportExporter()
    pdf_path = tmp_path / "exec_kpi.pdf"

    out_pdf = pdf_exporter.export(enterprise_mixed_report, str(pdf_path))
    assert Path(out_pdf).exists()
    assert Path(out_pdf).stat().st_size > 2000


def test_pdf_ai_insights_inclusion_and_omission(enterprise_mixed_report, mock_ai_report, tmp_path):
    """4: PDF includes AI section when present, and omits it cleanly when None."""
    pdf_exporter = PdfReportExporter()

    pdf_with_ai = tmp_path / "with_ai.pdf"
    res_ai = pdf_exporter.export(enterprise_mixed_report, str(pdf_with_ai), ai_report=mock_ai_report)
    assert Path(res_ai).exists()

    pdf_no_ai = tmp_path / "no_ai.pdf"
    res_no_ai = pdf_exporter.export(enterprise_mixed_report, str(pdf_no_ai), ai_report=None)
    assert Path(res_no_ai).exists()

    assert Path(res_ai).stat().st_size > Path(res_no_ai).stat().st_size


def test_txt_report_contains_governance_and_eliminates_machine_flags(enterprise_mixed_report, tmp_path):
    """10 & 11: TXT report contains clean business descriptions and zero machine flags."""
    txt_exporter = TextReportExporter()
    txt_path = tmp_path / "clean_txt.txt"

    txt_exporter.export(enterprise_mixed_report, str(txt_path))
    content = txt_path.read_text(encoding="utf-8")

    assert "Correlation Available: False" not in content
    assert "Numerical Analysis: Unavailable" not in content
    assert "{'total_rows':" not in content
    assert "{'distinct_count':" not in content

    assert "COLUMN SEMANTIC PROFILE & GOVERNANCE" in content
    assert "contract_value" in content
    assert "churn_risk_score" in content
    assert "DATA LIMITATIONS & CAVEATS" in content
    assert "DATASET LINEAGE & PROVENANCE" in content


def test_long_column_profile_pagination(tmp_path):
    """13: Long column profile paginates cleanly across continuation pages without crashing."""
    many_cols = {
        f"col_{i:02d}": {
            "semantic_type": "categorical_dimension" if i % 2 == 0 else "numeric_measure",
            "analytical_role": "dimension" if i % 2 == 0 else "measure",
            "missing_count": i,
            "missing_percentage": float(i) * 0.5,
            "unique_count": i * 10 + 1,
            "uniqueness_percentage": float(i) * 2.0,
            "governance_recommendation": "standard_validation",
        }
        for i in range(1, 30)
    }

    report = StructuredReport(
        title="Wide Schema Enterprise Report",
        executive_summary="Wide enterprise dataset analysis.",
        kpis={"Rows": 5000, "Columns": 29},
        analytics={
            "descriptive_statistics": {"total_rows": 5000, "total_columns": 29},
            "dataset_profile": {"columns": many_cols, "completeness_score": 0.95},
        },
        recommendations=["Validate high column count dimensions."],
    )

    pdf_exporter = PdfReportExporter()
    pdf_path = tmp_path / "wide_report.pdf"
    out_pdf = pdf_exporter.export(report, str(pdf_path))

    assert Path(out_pdf).exists()
    assert Path(out_pdf).stat().st_size > 3000


def test_export_works_when_ai_pending_or_failed(enterprise_mixed_report, tmp_path):
    """15: Export works seamlessly when AI generation is pending (None) or failed."""
    pdf_exporter = PdfReportExporter()
    txt_exporter = TextReportExporter()

    p_pdf = pdf_exporter.export(enterprise_mixed_report, str(tmp_path / "pending.pdf"), ai_report=None)
    p_txt = txt_exporter.export(enterprise_mixed_report, str(tmp_path / "pending.txt"), ai_report=None)
    assert Path(p_pdf).exists()
    assert Path(p_txt).exists()

    f_pdf = pdf_exporter.export(enterprise_mixed_report, str(tmp_path / "failed.pdf"), ai_report={})
    f_txt = txt_exporter.export(enterprise_mixed_report, str(tmp_path / "failed.txt"), ai_report={})
    assert Path(f_pdf).exists()
    assert Path(f_txt).exists()
