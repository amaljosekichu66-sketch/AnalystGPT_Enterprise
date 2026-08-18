"""
Analytics Manager Module

Coordinates the execution of all analytics modules with semantic profiling awareness.

Sprint 14 Remediation — Data Profiling, Null Governance & Visual Analytics.
"""

from __future__ import annotations

import time

from pandas import DataFrame

from src.analytics.analytics_report import AnalyticsReport
from src.analytics.categorical_analysis import CategoricalAnalysis
from src.analytics.correlation_analysis import CorrelationAnalysis
from src.analytics.descriptive_statistics import DescriptiveStatistics
from src.analytics.distribution_analysis import DistributionAnalysis
from src.analytics.numerical_analysis import NumericalAnalysis
from src.core.logger import logger
from src.profiling.data_profiler import DataProfiler
from src.profiling.models import DatasetProfile


class AnalyticsManager:
    """
    Coordinates the execution of the complete analytics pipeline.
    """

    def __init__(self) -> None:
        """
        Initialize the analytics pipeline.
        """
        self.descriptive_statistics = DescriptiveStatistics()
        self.numerical_analysis = NumericalAnalysis()
        self.categorical_analysis = CategoricalAnalysis()
        self.correlation_analysis = CorrelationAnalysis()
        self.distribution_analysis = DistributionAnalysis()
        self.profiler = DataProfiler()

    def analyze(
        self,
        dataframe: DataFrame,
        profile: DatasetProfile | None = None,
    ) -> AnalyticsReport:
        """
        Execute the complete analytics pipeline using semantic profiling awareness.

        Parameters
        ----------
        dataframe:
            Clean and validated dataset.
        profile:
            Optional pre-computed DatasetProfile.

        Returns
        -------
        AnalyticsReport
            Final analytics report.
        """
        start_time = time.perf_counter()

        logger.info("Starting analytics pipeline.")

        # Ensure dataset profile exists
        active_profile = profile or self.profiler.profile_dataset(dataframe)

        # Create analytical view casting string-encoded numeric columns safely
        analytical_df = self.profiler.create_analytical_view(dataframe, active_profile)

        logger.info("Running DescriptiveStatistics...")
        descriptive_statistics = self.descriptive_statistics.analyze(analytical_df, profile=active_profile)

        logger.info("Running NumericalAnalysis...")
        numerical_analysis = self.numerical_analysis.analyze(analytical_df, profile=active_profile)

        logger.info("Running CategoricalAnalysis...")
        categorical_analysis = self.categorical_analysis.analyze(analytical_df, profile=active_profile)

        logger.info("Running CorrelationAnalysis...")
        correlation_analysis = self.correlation_analysis.analyze(analytical_df, profile=active_profile)

        logger.info("Running DistributionAnalysis...")
        distribution_analysis = self.distribution_analysis.analyze(analytical_df, profile=active_profile)

        elapsed_time = time.perf_counter() - start_time

        logger.info(
            "Analytics pipeline completed successfully in %.4f seconds.",
            elapsed_time,
        )

        return AnalyticsReport(
            report={
                "descriptive_statistics": descriptive_statistics,
                "numerical_analysis": numerical_analysis,
                "categorical_analysis": categorical_analysis,
                "correlation_analysis": correlation_analysis,
                "distribution_analysis": distribution_analysis,
                "dataset_profile": active_profile.to_dict(),
            },
            execution_time=elapsed_time,
        )
