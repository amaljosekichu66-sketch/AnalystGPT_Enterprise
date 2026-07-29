"""
Power BI Dashboard Service.

Creates strongly typed dashboard models
from AnalystGPT Enterprise PipelineResult objects.
"""

from __future__ import annotations

from src.application.pipeline_result import PipelineResult

from src.integrations.powerbi.dashboard_summary import (
    DashboardSummary,
)
from src.integrations.powerbi.dashboard_statistics import (
    DashboardStatistics,
)
from src.integrations.powerbi.dashboard_correlation import (
    DashboardCorrelation,
)
from src.integrations.powerbi.dashboard_distribution import (
    DashboardDistribution,
)
from src.integrations.powerbi.dashboard_categorical import (
    DashboardCategorical,
)

from src.integrations.powerbi.powerbi_models import (
    AIReportModel,
    DashboardResponse,
    PipelineSummary,
    ReportResponse,
)


class DashboardService:
    """
    Converts PipelineResult objects into
    Power BI dashboard responses.
    """

    # ==========================================================
    # Internal Helpers
    # ==========================================================

    def _pipeline_report(
        self,
        pipeline_result: PipelineResult,
    ):
        """
        Return PipelineReport.
        """

        return pipeline_result.pipeline_report

    def _reporting_report(
        self,
        pipeline_result: PipelineResult,
    ):
        """
        Return ReportingReport.
        """

        pipeline_report = self._pipeline_report(
            pipeline_result,
        )

        if pipeline_report is None:
            return None

        return pipeline_report.reporting_report

    def _ai_report(
        self,
        pipeline_result: PipelineResult,
    ):
        """
        Return AIReport.
        """

        pipeline_report = self._pipeline_report(
            pipeline_result,
        )

        if pipeline_report is None:
            return None

        return pipeline_report.ai_report

    def _analytics(
        self,
        pipeline_result: PipelineResult,
    ) -> dict:
        """
        Return analytics dictionary.
        """

        reporting_report = self._reporting_report(
            pipeline_result,
        )

        if reporting_report is None:
            return {}

        report = getattr(
            reporting_report,
            "report",
            {},
        )

        if isinstance(
            report,
            dict,
        ):
            return report.get(
                "analytics",
                {},
            )

        return {}

    def _analytics_section(
        self,
        pipeline_result: PipelineResult,
        section: str,
    ) -> dict:
        """
        Return an analytics section.
        """

        analytics = self._analytics(
            pipeline_result,
        )

        if not isinstance(
            analytics,
            dict,
        ):
            return {}

        return analytics.get(
            section,
            {},
        )

    def _report_dict(
        self,
        pipeline_result: PipelineResult,
    ) -> dict:
        """
        Return report as dictionary.
        """

        reporting_report = self._reporting_report(
            pipeline_result,
        )

        if reporting_report is None:
            return {}

        if hasattr(
            reporting_report,
            "to_dict",
        ):
            return reporting_report.to_dict()

        report = getattr(
            reporting_report,
            "report",
            {},
        )

        if isinstance(
            report,
            dict,
        ):
            return report

        return {}

    def _build_ai_model(
        self,
        pipeline_result: PipelineResult,
    ) -> AIReportModel | None:
        """
        Convert AIReport into AIReportModel.
        """

        ai_report = self._ai_report(
            pipeline_result,
        )

        if ai_report is None:
            return None

        return AIReportModel(
            executive_summary=ai_report.executive_summary,
            recommendations=ai_report.recommendations,
            explanations=ai_report.explanations,
            narrative=ai_report.narrative,
            model=ai_report.model,
            provider=ai_report.provider,
            execution_time=ai_report.execution_time,
        )

    def _generated_at(
        self,
        pipeline_result: PipelineResult,
    ):
        """
        Return report timestamp.
        """

        pipeline_report = self._pipeline_report(
            pipeline_result,
        )

        if pipeline_report is None:
            return None

        return getattr(
            pipeline_report,
            "generated_at",
            None,
        )

    # ==========================================================
    # Dashboard
    # ==========================================================

    def build_dashboard_response(
        self,
        pipeline_result: PipelineResult,
    ) -> DashboardResponse:

        report = self._report_dict(
            pipeline_result,
        )

        ai_model = self._build_ai_model(
            pipeline_result,
        )

        if ai_model is not None:
            report["ai"] = ai_model.model_dump()

        return DashboardResponse(
            success=pipeline_result.success,
            execution_time=pipeline_result.execution_time,
            report=report,
            ai_report=ai_model,
            output_path=pipeline_result.output_path,
            generated_at=self._generated_at(
                pipeline_result,
            ),
        )

    # ==========================================================
    # Pipeline Summary
    # ==========================================================

    def build_pipeline_summary(
        self,
        pipeline_result: PipelineResult,
    ) -> PipelineSummary:

        return PipelineSummary(
            success=pipeline_result.success,
            execution_time=pipeline_result.execution_time,
            output_path=pipeline_result.output_path,
            ai_generated=(
                self._ai_report(
                    pipeline_result,
                )
                is not None
            ),
            generated_at=self._generated_at(
                pipeline_result,
            ),
        )

    # ==========================================================
    # Report
    # ==========================================================

    def build_report(
        self,
        pipeline_result: PipelineResult,
    ) -> ReportResponse:

        report = self._report_dict(
            pipeline_result,
        )

        ai_model = self._build_ai_model(
            pipeline_result,
        )

        if ai_model is not None:
            report["ai"] = ai_model.model_dump()

        return ReportResponse(
            report=report,
            ai_report=ai_model,
            execution_time=pipeline_result.execution_time,
            output_path=pipeline_result.output_path,
            generated_at=self._generated_at(
                pipeline_result,
            ),
        )

    # ==========================================================
    # Dashboard Summary
    # ==========================================================

    def build_dashboard_summary(
        self,
        pipeline_result: PipelineResult,
    ) -> DashboardSummary:

        stats = self._analytics_section(
            pipeline_result,
            "descriptive_statistics",
        )

        return DashboardSummary(
            success=pipeline_result.success,
            execution_time=pipeline_result.execution_time,
            total_rows=stats.get(
                "total_rows",
                0,
            ),
            total_columns=stats.get(
                "total_columns",
                0,
            ),
            numeric_columns=stats.get(
                "numeric_column_count",
                0,
            ),
            categorical_columns=stats.get(
                "categorical_column_count",
                0,
            ),
            datetime_columns=stats.get(
                "datetime_column_count",
                0,
            ),
            memory_usage_mb=stats.get(
                "memory_usage_mb",
                0.0,
            ),
        )

    # ==========================================================
    # Statistics
    # ==========================================================

    def build_statistics(
        self,
        pipeline_result: PipelineResult,
    ) -> DashboardStatistics:

        return DashboardStatistics(
            descriptive_statistics=self._analytics_section(
                pipeline_result,
                "descriptive_statistics",
            ),
        )

    # ==========================================================
    # Correlation
    # ==========================================================

    def build_correlation(
        self,
        pipeline_result: PipelineResult,
    ) -> DashboardCorrelation:

        return DashboardCorrelation(
            correlation_analysis=self._analytics_section(
                pipeline_result,
                "correlation_analysis",
            ),
        )

    # ==========================================================
    # Distribution
    # ==========================================================

    def build_distribution(
        self,
        pipeline_result: PipelineResult,
    ) -> DashboardDistribution:

        return DashboardDistribution(
            distribution_analysis=self._analytics_section(
                pipeline_result,
                "distribution_analysis",
            ),
        )

    # ==========================================================
    # Categorical
    # ==========================================================

    def build_categorical(
        self,
        pipeline_result: PipelineResult,
    ) -> DashboardCategorical:

        return DashboardCategorical(
            categorical_analysis=self._analytics_section(
                pipeline_result,
                "categorical_analysis",
            ),
        )