"""
Quality Manager Module

Coordinates the execution of all data quality checks.
"""

import time

from pandas import DataFrame

from src.core.logger import logger
from src.quality.completeness_checker import CompletenessChecker
from src.quality.consistency_checker import ConsistencyChecker
from src.quality.outlier_checker import OutlierChecker
from src.quality.quality_report import QualityReport
from src.quality.uniqueness_checker import UniquenessChecker
from src.quality.validity_checker import ValidityChecker


class QualityManager:
    """
    Coordinates the execution of all data quality checks.
    """

    def __init__(self) -> None:
        """Initialize the quality assessment pipeline."""

        self.completeness_checker = CompletenessChecker()
        self.validity_checker = ValidityChecker()
        self.consistency_checker = ConsistencyChecker()
        self.uniqueness_checker = UniquenessChecker()
        self.outlier_checker = OutlierChecker()

    def assess(
        self,
        dataframe: DataFrame,
    ) -> QualityReport:
        """
        Execute the complete data quality assessment pipeline.

        Parameters
        ----------
        dataframe:
            Cleaned dataset.

        Returns
        -------
        QualityReport
            Final quality assessment report.
        """

        start_time = time.perf_counter()

        logger.info("Starting quality assessment pipeline.")

        results: dict = {}

        logger.info("Running CompletenessChecker...")
        results["completeness"] = (
            self.completeness_checker.check(dataframe)
        )

        logger.info("Running ValidityChecker...")
        results["validity"] = (
            self.validity_checker.check(dataframe)
        )

        logger.info("Running ConsistencyChecker...")
        results["consistency"] = (
            self.consistency_checker.check(dataframe)
        )

        logger.info("Running UniquenessChecker...")
        results["uniqueness"] = (
            self.uniqueness_checker.check(dataframe)
        )

        logger.info("Running OutlierChecker...")
        results["outliers"] = (
            self.outlier_checker.check(dataframe)
        )

        elapsed_time = time.perf_counter() - start_time

        logger.info(
            "Quality assessment completed successfully in %.4f seconds.",
            elapsed_time,
        )

        return QualityReport(
            report=results,
            execution_time=elapsed_time,
        )