"""
Analytics Manager Module

Coordinates the execution of all analytics modules.
"""

import time

from pandas import DataFrame

from src.analytics.descriptive_statistics import DescriptiveStatistics
from src.analytics.numerical_analysis import NumericalAnalysis
from src.analytics.categorical_analysis import CategoricalAnalysis
from src.analytics.correlation_analysis import CorrelationAnalysis
from src.analytics.distribution_analysis import DistributionAnalysis
from src.analytics.analytics_report import AnalyticsReport

from src.core.logger import logger


class AnalyticsManager:
    """
    Coordinates the execution of the complete analytics pipeline.
    """

    def __init__(self):
        """
        Initialize the analytics pipeline.
        """

        self.descriptive_statistics = DescriptiveStatistics()
        self.numerical_analysis = NumericalAnalysis()
        self.categorical_analysis = CategoricalAnalysis()
        self.correlation_analysis = CorrelationAnalysis()
        self.distribution_analysis = DistributionAnalysis()

        self.analytics_report = AnalyticsReport()

    def analyze(self, dataframe: DataFrame) -> dict:
        """
        Execute the complete analytics pipeline.

        Parameters
        ----------
        dataframe : DataFrame
            Clean and validated dataset.

        Returns
        -------
        dict
            Enterprise analytics report.
        """

        start_time = time.perf_counter()

        logger.info("Starting analytics pipeline.")

        results = {}

        logger.info("Running DescriptiveStatistics...")
        results["descriptive_statistics"] = (
            self.descriptive_statistics.analyze(dataframe)
        )

        logger.info("Running NumericalAnalysis...")
        results["numerical_analysis"] = (
            self.numerical_analysis.analyze(dataframe)
        )

        logger.info("Running CategoricalAnalysis...")
        results["categorical_analysis"] = (
            self.categorical_analysis.analyze(dataframe)
        )

        logger.info("Running CorrelationAnalysis...")
        results["correlation_analysis"] = (
            self.correlation_analysis.analyze(dataframe)
        )

        logger.info("Running DistributionAnalysis...")
        results["distribution_analysis"] = (
            self.distribution_analysis.analyze(dataframe)
        )

        logger.info("Generating AnalyticsReport...")

        report = self.analytics_report.generate(results)

        elapsed_time = time.perf_counter() - start_time

        logger.info(
            f"Analytics pipeline completed successfully in "
            f"{elapsed_time:.4f} seconds."
        )

        return report