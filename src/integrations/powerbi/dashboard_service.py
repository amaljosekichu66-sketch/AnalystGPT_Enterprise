"""
Power BI Dashboard Service.

Creates strongly typed dashboard models
from AnalystGPT reporting results.
"""

from src.application.pipeline_result import PipelineResult

from src.integrations.powerbi.dashboard_summary import DashboardSummary
from src.integrations.powerbi.dashboard_statistics import DashboardStatistics
from src.integrations.powerbi.dashboard_correlation import DashboardCorrelation
from src.integrations.powerbi.dashboard_distribution import DashboardDistribution
from src.integrations.powerbi.dashboard_categorical import DashboardCategorical

from src.integrations.powerbi.powerbi_models import (
    DashboardResponse,
    PipelineSummary,
    ReportResponse,
)


class DashboardService:
    """
    Converts AnalystGPT PipelineResult objects
    into Power BI dashboard responses.
    """

    def _analytics(
        self,
        pipeline_result: PipelineResult,
    ) -> dict:

        return (
            pipeline_result
            .reporting_report
            .report
            .analytics
        )

    def build_dashboard_response(
        self,
        pipeline_result: PipelineResult,
    ) -> DashboardResponse:

        report = {}

        if pipeline_result.reporting_report:

            report = (
                pipeline_result.reporting_report.to_dict()
            )

        return DashboardResponse(
            success=pipeline_result.success,
            execution_time=pipeline_result.execution_time,
            report=report,
            output_path=pipeline_result.output_path,
        )

    def build_pipeline_summary(
        self,
        pipeline_result: PipelineResult,
    ) -> PipelineSummary:

        return PipelineSummary(
            success=pipeline_result.success,
            execution_time=pipeline_result.execution_time,
            output_path=pipeline_result.output_path,
        )

    def build_report(
        self,
        pipeline_result: PipelineResult,
    ) -> ReportResponse:

        report = {}

        if pipeline_result.reporting_report:

            report = (
                pipeline_result.reporting_report.to_dict()
            )

        return ReportResponse(
            report=report,
        )

    def build_dashboard_summary(
        self,
        pipeline_result: PipelineResult,
    ) -> DashboardSummary:

        stats = self._analytics(
            pipeline_result
        )["descriptive_statistics"]

        return DashboardSummary(
            success=pipeline_result.success,
            execution_time=pipeline_result.execution_time,
            total_rows=stats["total_rows"],
            total_columns=stats["total_columns"],
            numeric_columns=stats["numeric_column_count"],
            categorical_columns=stats["categorical_column_count"],
            datetime_columns=stats["datetime_column_count"],
            memory_usage_mb=stats["memory_usage_mb"],
        )

    def build_statistics(
        self,
        pipeline_result: PipelineResult,
    ) -> DashboardStatistics:

        return DashboardStatistics(
            descriptive_statistics=self._analytics(
                pipeline_result
            )["descriptive_statistics"]
        )

    def build_correlation(
        self,
        pipeline_result: PipelineResult,
    ) -> DashboardCorrelation:

        return DashboardCorrelation(
            correlation_analysis=self._analytics(
                pipeline_result
            )["correlation_analysis"]
        )

    def build_distribution(
        self,
        pipeline_result: PipelineResult,
    ) -> DashboardDistribution:

        return DashboardDistribution(
            distribution_analysis=self._analytics(
                pipeline_result
            )["distribution_analysis"]
        )

    def build_categorical(
        self,
        pipeline_result: PipelineResult,
    ) -> DashboardCategorical:

        return DashboardCategorical(
            categorical_analysis=self._analytics(
                pipeline_result
            )["categorical_analysis"]
        )