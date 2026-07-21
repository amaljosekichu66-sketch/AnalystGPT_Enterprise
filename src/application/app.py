"""
Application orchestration layer.

Coordinates the complete AnalystGPT Enterprise
processing pipeline.
"""

import time
from pathlib import Path

from pandas import DataFrame

from src.analytics.analytics_manager import AnalyticsManager
from src.analytics.analytics_report import AnalyticsReport
from src.cleaning.cleaning_manager import CleaningManager
from src.core.logger import logger
from src.persistence.persistence_manager import PersistenceManager
from src.quality.quality_manager import QualityManager
from src.quality.quality_report import QualityReport
from src.reporting.reporting_manager import ReportingManager
from src.reporting.reporting_report import ReportingReport
from src.upload.upload_manager import UploadManager

from .pipeline_result import PipelineResult


class Application:
    """
    Main application orchestrator.

    Executes the complete AnalystGPT Enterprise
    processing pipeline.
    """

    def __init__(self) -> None:
        """
        Initialize all pipeline managers.
        """

        self.upload_manager = UploadManager()
        self.cleaning_manager = CleaningManager()
        self.quality_manager = QualityManager()
        self.analytics_manager = AnalyticsManager()
        self.reporting_manager = ReportingManager()

        # --------------------------------------------
        # Persistence Layer
        # --------------------------------------------

        self.persistence = PersistenceManager()

    def run(
        self,
        input_path: str,
    ) -> PipelineResult:
        """
        Execute the complete AnalystGPT Enterprise
        processing pipeline.

        Parameters
        ----------
        input_path:
            Dataset location.

        Returns
        -------
        PipelineResult
        """

        logger.info("=" * 60)
        logger.info("Starting AnalystGPT Enterprise...")
        logger.info("=" * 60)

        start_time = time.perf_counter()

        try:

            self.persistence.initialize()

            self.persistence.start_pipeline()

            # -------------------------------------------------
            # Upload
            # -------------------------------------------------

            raw_dataframe = self._upload_dataset(
                input_path
            )

            self.persistence.save_dataset(
                dataset_name=Path(input_path).name,
                row_count=len(raw_dataframe),
                column_count=len(raw_dataframe.columns),
            )

            # -------------------------------------------------
            # Cleaning
            # -------------------------------------------------

            cleaned_dataframe = self._clean_dataset(
                raw_dataframe
            )

            # -------------------------------------------------
            # Quality
            # -------------------------------------------------

            quality_report = self._assess_quality(
                cleaned_dataframe
            )

            self.persistence.save_quality(
                quality_report,
            )

            # -------------------------------------------------
            # Analytics
            # -------------------------------------------------

            analytics_report = (
                self._generate_analytics(
                    cleaned_dataframe
                )
            )

            self.persistence.save_analytics(
                analytics_report,
            )

            # -------------------------------------------------
            # Reporting
            # -------------------------------------------------

            reporting_report = (
                self._generate_report(
                    analytics_report
                )
            )

            self.persistence.save_report(
                reporting_report,
            )

            # -------------------------------------------------
            # Pipeline Summary
            # -------------------------------------------------

            self._log_pipeline_summary(
                quality_report,
                analytics_report,
                reporting_report,
            )

            execution_time = (
                time.perf_counter() - start_time
            )

            self.persistence.finish_pipeline()

            return self._build_pipeline_result(
                reporting_report,
                execution_time,
            )

        except Exception as error:

            logger.exception(
                "Pipeline execution failed."
            )

            try:
                self.persistence.fail_pipeline()
            except Exception:
                logger.exception(
                    "Unable to mark pipeline as FAILED."
                )

            execution_time = (
                time.perf_counter() - start_time
            )

            return PipelineResult(
                success=False,
                execution_time=execution_time,
                error=error,
            )

        finally:

            self.persistence.shutdown()

    def _upload_dataset(
        self,
        input_path: str,
    ) -> DataFrame:
        """
        Upload the input dataset.

        Parameters
        ----------
        input_path:
            Dataset location.

        Returns
        -------
        DataFrame
            Uploaded dataset.
        """

        logger.info("-" * 60)
        logger.info("UPLOAD STAGE")
        logger.info("-" * 60)

        dataframe = self.upload_manager.upload(
            input_path
        )

        logger.info(
            "Data Preview Before Cleaning:"
        )

        logger.info(
            "\n%s",
            dataframe.head(),
        )

        return dataframe

    def _clean_dataset(
        self,
        dataframe: DataFrame,
    ) -> DataFrame:
        """
        Execute the cleaning stage.

        Parameters
        ----------
        dataframe:
            Raw dataset.

        Returns
        -------
        DataFrame
            Cleaned dataset.
        """

        logger.info("-" * 60)
        logger.info("CLEANING STAGE")
        logger.info("-" * 60)

        cleaned_dataframe = (
            self.cleaning_manager.clean(
                dataframe
            )
        )

        logger.info(
            "Data Preview After Cleaning:"
        )

        logger.info(
            "\n%s",
            cleaned_dataframe.head(),
        )

        return cleaned_dataframe

    def _assess_quality(
        self,
        dataframe: DataFrame,
    ) -> QualityReport:
        """
        Execute the quality assessment stage.

        Parameters
        ----------
        dataframe:
            Cleaned dataset.

        Returns
        -------
        QualityReport
        """

        logger.info("-" * 60)
        logger.info("QUALITY STAGE")
        logger.info("-" * 60)

        return self.quality_manager.assess(
            dataframe
        )

    def _generate_analytics(
        self,
        dataframe: DataFrame,
    ) -> AnalyticsReport:
        """
        Execute the analytics stage.

        Parameters
        ----------
        dataframe:
            Cleaned dataset.

        Returns
        -------
        AnalyticsReport
        """

        logger.info("-" * 60)
        logger.info("ANALYTICS STAGE")
        logger.info("-" * 60)

        return self.analytics_manager.analyze(
            dataframe
        )

    def _generate_report(
        self,
        analytics_report: AnalyticsReport,
    ) -> ReportingReport:
        """
        Execute the reporting stage.

        Parameters
        ----------
        analytics_report:
            Analytics report.

        Returns
        -------
        ReportingReport
        """

        logger.info("-" * 60)
        logger.info("REPORTING STAGE")
        logger.info("-" * 60)

        reporting_report = (
            self.reporting_manager.generate_report(
                analytics_report
            )
        )

        logger.info(
            "Report successfully generated."
        )

        logger.info(
            "Export Location: %s",
            reporting_report.export_path,
        )

        return reporting_report

    def _log_pipeline_summary(
        self,
        quality_report: QualityReport,
        analytics_report: AnalyticsReport,
        reporting_report: ReportingReport,
    ) -> None:
        """
        Log the final pipeline execution summary.

        Parameters
        ----------
        quality_report:
            Final quality assessment.

        analytics_report:
            Final analytics results.

        reporting_report:
            Final reporting results.
        """

        descriptive = analytics_report.report[
            "descriptive_statistics"
        ]

        quality = quality_report.report

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
            quality["completeness"][
                "complete_percentage"
            ],
        )

        logger.info(
            "Duplicate Rows          : %s",
            quality["uniqueness"][
                "duplicate_rows"
            ],
        )

        logger.info(
            "Quality Time (s)        : %.4f",
            quality_report.execution_time,
        )

        logger.info(
            "Analytics Time (s)      : %.4f",
            analytics_report.execution_time,
        )

        logger.info(
            "Reporting Time (s)      : %.4f",
            reporting_report.execution_time,
        )

        logger.info(
            "Report Exported         : %s",
            reporting_report.export_path,
        )

        logger.info("=" * 60)

        logger.info(
            "Pipeline persisted successfully."
        )

        logger.info(
            "AnalystGPT Enterprise completed successfully."
        )

    def _build_pipeline_result(
        self,
        reporting_report: ReportingReport,
        execution_time: float,
    ) -> PipelineResult:
        """
        Build the final application result.

        Parameters
        ----------
        reporting_report:
            Final reporting result.

        execution_time:
            Total pipeline execution time.

        Returns
        -------
        PipelineResult
            Final application execution result.
        """

        return PipelineResult(
            success=True,
            reporting_report=reporting_report,
            output_path=reporting_report.export_path,
            execution_time=execution_time,
        )