"""
Structured Report Module

Defines the canonical report structure used by the Reporting Module.
"""

from typing import Any


class StructuredReport:
    """
    Represents the structured contents of a business report.

    This object is independent of any export format
    (TXT, PDF, HTML, DOCX, etc.).
    """

    def __init__(
        self,
        title: str,
        executive_summary: list[str],
        kpis: dict[str, Any],
        analytics: dict[str, Any],
        recommendations: list[str],
    ) -> None:
        """
        Initialize a StructuredReport instance.

        Args:
            title: Human-readable report title.
            executive_summary: Executive-level summary.
            kpis: Key performance indicators.
            analytics: Complete analytics results.
            recommendations: Business recommendations.
        """

        self.title = title
        self.executive_summary = executive_summary
        self.kpis = kpis
        self.analytics = analytics
        self.recommendations = recommendations

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the structured report into a serializable dictionary.

        Returns:
            Dictionary representation of the report.
        """

        return {
            "title": self.title,
            "executive_summary": self.executive_summary,
            "kpis": self.kpis,
            "analytics": self.analytics,
            "recommendations": self.recommendations,
        }