"""
AnalystGPT Enterprise

Application entry point.

Coordinates the complete data processing pipeline.
"""

from src.analytics.analytics_manager import AnalyticsManager
from src.cleaning.cleaning_manager import CleaningManager
from src.core.logger import logger
from src.quality.quality_manager import QualityManager
from src.reporting.reporting_manager import ReportingManager
from src.upload.upload_manager import UploadManager


def main() -> None:
    """
    Execute the complete data processing pipeline.
    """

    logger.info("Starting AnalystGPT Enterprise...")

    # ---------------------------------------------------------
    # Initialize Managers
    # ---------------------------------------------------------

    upload_manager = UploadManager()
    cleaning_manager = CleaningManager()
    quality_manager = QualityManager()
    analytics_manager = AnalyticsManager()
    reporting_manager = ReportingManager()

    # ---------------------------------------------------------
    # Upload
    # ---------------------------------------------------------

    dataframe = upload_manager.upload(
        "sample_data/customer_data.csv"
    )

    logger.info("Data Preview Before Cleaning:")
    logger.info("\n%s", dataframe.head())

    # ---------------------------------------------------------
    # Cleaning
    # ---------------------------------------------------------

    dataframe = cleaning_manager.clean(dataframe)

    logger.info("Data Preview After Cleaning:")
    logger.info("\n%s", dataframe.head())

    # ---------------------------------------------------------
    # Quality Assessment
    # ---------------------------------------------------------

    quality_report = quality_manager.assess(
        dataframe
    )

    # ---------------------------------------------------------
    # Analytics
    # ---------------------------------------------------------

    analytics_report = analytics_manager.analyze(
        dataframe
    )

    # ---------------------------------------------------------
    # Reporting
    # ---------------------------------------------------------

    reporting_report = reporting_manager.generate_report(
        analytics_report
    )

    # ---------------------------------------------------------
    # Pipeline Summary
    # ---------------------------------------------------------

    descriptive = analytics_report["descriptive_statistics"]

    logger.info("=" * 60)
    logger.info("PIPELINE EXECUTION SUMMARY")
    logger.info("=" * 60)

    logger.info(
        "Rows Processed          : %s",
        descriptive["total_rows"],
    )

    logger.info(
        "Columns Processed       : %s",
        descriptive["total_columns"],
    )

    logger.info(
        "Numeric Columns         : %s",
        descriptive["numeric_column_count"],
    )

    logger.info(
        "Categorical Columns     : %s",
        descriptive["categorical_column_count"],
    )

    logger.info(
        "Datetime Columns        : %s",
        descriptive["datetime_column_count"],
    )

    logger.info(
        "Memory Usage (MB)       : %.2f",
        descriptive["memory_usage_mb"],
    )

    logger.info(
        "Dataset Completeness    : %.2f%%",
        quality_report["completeness"][
            "complete_percentage"
        ],
    )

    logger.info(
        "Duplicate Rows          : %s",
        quality_report["uniqueness"][
            "duplicate_rows"
        ],
    )

    logger.info(
        "Report Exported         : %s",
        reporting_report["export_path"],
    )

    logger.info("=" * 60)

    logger.info(
        "AnalystGPT Enterprise completed successfully."
    )


if __name__ == "__main__":
    main()