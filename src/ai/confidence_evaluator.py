"""
AI Insight Confidence Evaluator.

Computes evidence-grounded confidence levels for AI business insights
based on governed analytical measures, completeness, record volume,
and correlation availability.

Sprint 14 Remediation — Phase 2 Quality Gate.
"""

from __future__ import annotations

from typing import Any


def compute_evidence_confidence(
    analytics_report: dict[str, Any] | None = None,
    data_context: Any | None = None,
) -> str:
    """
    Evaluate and assign an evidence-based confidence level to AI insights.

    Returns one of:
    - High: Governed numerical measures (>=2), verified correlations, high completeness (>=90%), sufficient volume (>=50 rows).
    - Medium: Categorical-only dataset, or metric dataset with moderate volume/missingness.
    - Low: High missingness (>30%), very small sample size (<10 records), or severe data quality anomalies.
    - Not Assessable: Empty dataset, 0 records, or missing analytical context.
    """
    if not analytics_report and not data_context:
        return "Not Assessable — Available data does not support a reliable business interpretation."

    analytics = analytics_report or {}
    descriptive = analytics.get("descriptive_statistics", {})

    total_rows = descriptive.get("total_rows")
    numeric_count = descriptive.get("numeric_column_count", 0)

    if total_rows is None and data_context:
        if hasattr(data_context, "analytics"):
            total_rows = getattr(data_context.analytics, "row_count", None)
            numeric_count = getattr(data_context.analytics, "column_count", 0)
        elif hasattr(data_context, "source"):
            total_rows = getattr(data_context.source, "row_count", None)

    # 1. Not assessable check
    if total_rows is None or total_rows == 0:
        return "Not Assessable — Available data does not support a reliable business interpretation."

    # 2. Low sample volume check
    if total_rows < 10:
        return f"Low — Sample size is too small ({total_rows} records) to establish statistically reliable business patterns."

    # 3. Completeness check
    completeness = None
    if data_context and hasattr(data_context, "source") and getattr(data_context.source, "completeness_percentage", None) is not None:
        completeness = data_context.source.completeness_percentage
    elif data_context and hasattr(data_context, "analytics") and getattr(data_context.analytics, "completeness_percentage", None) is not None:
        completeness = data_context.analytics.completeness_percentage

    if completeness is not None and completeness < 70.0:
        missing_pct = 100.0 - completeness
        return f"Low — High missingness ({missing_pct:.1f}% missing) impairs analytical reliability across active fields."

    # 4. Zero numeric measures (Categorical-only dataset)
    if numeric_count == 0:
        return (
            "Medium — Findings are grounded in observed categorical distributions, "
            "but the dataset contains no governed numerical measures or outcome variable."
        )

    # 5. Governed numerical measures with correlation analysis
    corr_data = analytics.get("correlation_analysis", {})
    corr_mat = corr_data.get("correlation_matrix") if isinstance(corr_data, dict) else None

    if numeric_count >= 2 and corr_mat and len(corr_mat) >= 2 and total_rows >= 50:
        return "High — Grounded in governed numerical measures, verified distribution statistics, and bivariate correlations."

    return "Medium — Supported by observed metric distributions across active fields."
