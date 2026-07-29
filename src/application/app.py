"""

Application orchestration layer.



Coordinates the complete AnalystGPT Enterprise

processing pipeline.

"""



import time

from datetime import datetime, UTC

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



# Application layer contracts

from .pipeline_result import PipelineResult

from .pipeline_report import PipelineReport



# AI Layer

from src.ai.ai_manager import AIManager

from src.ai.ai_result import AIResult





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



        # -------------------------------------------------

        # AI Insight Engine

        # -------------------------------------------------



        self.ai_manager = AIManager()



        # --------------------------------------------

        # Persistence Layer

        # --------------------------------------------



        self.persistence = PersistenceManager()



        # --------------------------------------------

        # Cached Pipeline Result

        # --------------------------------------------



        self._last_pipeline_result: (

            PipelineResult | None

        ) = None

        self._cached_dataset_path: str | None = None



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



        logger.info("=" * 80)

        logger.info("APPLICATION.RUN() ENTERED")

        logger.info("=" * 80)



        logger.info(

            "Application Instance : %s",

            id(self),

        )



        logger.info(

            "Dataset : %s",

            input_path,

        )



        logger.info("=" * 80)

        logger.info("Starting AnalystGPT Enterprise...")

        logger.info("=" * 80)



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

            # AI Insight Engine (enhancement)

            # -------------------------------------------------



            ai_result = self._generate_ai(

                reporting_report

            )



            logger.info("=" * 60)

            logger.info("AI DEBUG")

            logger.info("=" * 60)



            logger.info("Success      : %s", ai_result.success)

            logger.info("AI Report    : %s", ai_result.ai_report)

            logger.info("Execution    : %s", ai_result.execution_time)

            logger.info("Error        : %s", ai_result.error)

            logger.info("=" * 60)



            # Optionally persist AI report (Sprint 12)

            # if ai_result.success:

            #     self.persistence.save_ai_report(ai_result)



            # -------------------------------------------------

            # Finalise Pipeline – everything is complete now

            # -------------------------------------------------



            self.persistence.finish_pipeline()



            # -------------------------------------------------

            # Pipeline Summary

            # -------------------------------------------------



            self._log_pipeline_summary(

                quality_report,

                analytics_report,

                reporting_report,

                ai_result,

            )



            execution_time = (

                time.perf_counter() - start_time

            )



            result = self._build_pipeline_result(

                reporting_report=reporting_report,

                ai_result=ai_result,

                execution_time=execution_time,

            )



            logger.info("=" * 60)

            logger.info("PIPELINE RESULT CREATED")

            logger.info("=" * 60)



            logger.info(

                "Pipeline Success : %s",

                result.success,

            )



            logger.info(

                "Pipeline Report  : %s",

                result.pipeline_report,

            )



            logger.info(

                "Reporting Report : %s",

                result.pipeline_report.reporting_report,

            )



            logger.info(

                "AI Report        : %s",

                result.pipeline_report.ai_report,

            )



            logger.info(

                "Output Path      : %s",

                result.output_path,

            )



            logger.info("=" * 60)



            # --------------------------------------------

            # Cache latest successful pipeline execution

            # --------------------------------------------



            self._cache_pipeline_result(result, input_path)



            return result



        except Exception as error:

            import traceback

            print("\n" + "=" * 80)
            print("APPLICATION EXCEPTION")
            print("=" * 80)

            traceback.print_exc()

            print(f"Exception Type : {type(error).__name__}")
            print(f"Exception      : {error}")

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



    def _generate_ai(

        self,

        reporting_report: ReportingReport,

    ) -> AIResult:

        """

        Execute the AI Insight Engine stage.



        Parameters

        ----------

        reporting_report:

            Final reporting result.



        Returns

        -------

        AIResult

            Result containing generated AI insights.

        """



        logger.info("-" * 60)

        logger.info("AI STAGE")

        logger.info("-" * 60)



        ai_result = self.ai_manager.generate_ai_report(

            reporting_report

        )



        if ai_result.success:

            logger.info(

                "AI report generated successfully."

            )

        else:

            logger.warning(

                "AI Insight Engine unavailable. "

                "Pipeline completed without AI enrichment."

            )

            if ai_result.error is not None:

                logger.warning(

                    "AI Error: %s",

                    ai_result.error,

                )



        return ai_result



    def _log_pipeline_summary(

        self,

        quality_report: QualityReport,

        analytics_report: AnalyticsReport,

        reporting_report: ReportingReport,

        ai_result: AIResult,

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



        ai_result:

            Result from the AI Insight Engine.

        """



        descriptive = analytics_report.report[

            "descriptive_statistics"

        ]



        quality = quality_report.report



        logger.info("=" * 60)

        logger.info("PIPELINE EXECUTION SUMMARY")

        logger.info("=" * 60)



        # Core ETL stages

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



        # Stage timings

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



        # AI Stage

        logger.info(

            "AI Generated            : %s",

            ai_result.success,

        )

        if ai_result.success:

            logger.info(

                "AI Model               : %s",

                ai_result.ai_report.model,

            )

            logger.info(

                "AI Provider            : %s",

                ai_result.ai_report.provider,

            )

            logger.info(

                "AI Time (s)            : %.4f",

                ai_result.execution_time,

            )

        else:

            logger.info(

                "AI Stage               : Skipped"

            )



        # Final output

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

        ai_result: AIResult,

        execution_time: float,

    ) -> PipelineResult:

        """

        Build the final application result.



        Parameters

        ----------

        reporting_report:

            Final reporting result.



        ai_result:

            Result from the AI Insight Engine.



        execution_time:

            Total pipeline execution time.



        Returns

        -------

        PipelineResult

            Final application execution result.

        """



        generated_at = datetime.now(UTC)



        pipeline_report = PipelineReport(

            reporting_report=reporting_report,

            ai_report=(

                ai_result.ai_report

                if ai_result.success

                else None

            ),

            generated_at=generated_at,

        )



        return PipelineResult(

            success=True,

            pipeline_report=pipeline_report,

            output_path=reporting_report.export_path,

            execution_time=execution_time,

        )



    def _cache_pipeline_result(

        self,

        result: PipelineResult,

        dataset_path: str,

    ) -> None:

        """

        Cache the latest successful pipeline result together with the dataset path.



        This method centralises the caching logic so that

        future persistence backends (Redis, PostgreSQL, etc.)

        can be added without modifying the orchestration.

        """



        logger.info("=" * 80)

        logger.info("PIPELINE RESULT CACHED")

        logger.info("=" * 80)



        logger.info(

            "Application Instance : %s",

            id(self),

        )



        logger.info(

            "Dataset : %s",

            dataset_path,

        )



        logger.info(

            "Cached Result : %s",

            result,

        )



        logger.info(

            "Pipeline Report : %s",

            result.pipeline_report,

        )



        logger.info(

            "AI Report : %s",

            result.pipeline_report.ai_report,

        )



        logger.info("=" * 80)



        if result.success:

            self._last_pipeline_result = result

            self._cached_dataset_path = dataset_path

            logger.info(

                "PipelineResult cached successfully for dataset: %s",

                dataset_path,

            )

        else:

            logger.warning(

                "Pipeline failed. Cache not updated."

            )



    def clear_cache(

        self,

    ) -> None:

        """

        Clear the cached PipelineResult.

        This should be called whenever a new dataset

        is uploaded so that stale dashboard data

        is never returned.

        """



        logger.info("=" * 80)

        logger.info("CLEARING PIPELINE CACHE")

        logger.info("=" * 80)



        if self._cached_dataset_path is not None:

            logger.info(

                "Clearing cached data for dataset: %s",

                self._cached_dataset_path,

            )

        else:

            logger.info("No cached dataset to clear.")



        self._last_pipeline_result = None

        self._cached_dataset_path = None



    def get_or_run(

        self,

        input_path: str,

    ) -> PipelineResult:

        """

        Return the cached PipelineResult if it exists and matches the requested dataset.

        If no cached result exists for this dataset, execute the pipeline and cache the result.

        """



        if (

            self._last_pipeline_result is not None

            and self._cached_dataset_path == input_path

        ):

            logger.info("=" * 80)

            logger.info("USING CACHED PIPELINE RESULT")

            logger.info("=" * 80)

            return self._last_pipeline_result



        logger.info("=" * 80)

        logger.info("NO CACHED PIPELINE RESULT FOR THIS DATASET")

        logger.info("RUNNING PIPELINE")

        logger.info("=" * 80)



        return self.run(

            input_path=input_path,

        )



    @property

    def last_result(self) -> PipelineResult | None:

        """

        Return the latest successful pipeline result.

        """



        return self._last_pipeline_result



    @property

    def cached_dataset_path(self) -> str | None:

        """

        Return the dataset path associated with the cached result.

        """



        return self._cached_dataset_path



    def get_last_result(

        self,

    ) -> PipelineResult | None:

        """

        Return the most recent successful pipeline result.

        """



        logger.info("=" * 80)

        logger.info("GET_LAST_RESULT()")

        logger.info("=" * 80)



        logger.info(

            "Application Instance : %s",

            id(self),

        )



        logger.info(

            "Cached Result : %s",

            self._last_pipeline_result,

        )



        if self._last_pipeline_result is not None:



            logger.info(

                "Pipeline Report : %s",

                self._last_pipeline_result.pipeline_report,

            )



            logger.info(

                "Reporting Report : %s",

                self._last_pipeline_result.pipeline_report.reporting_report,

            )



            logger.info(

                "AI Report : %s",

                self._last_pipeline_result.pipeline_report.ai_report,

            )



        logger.info("=" * 80)



        return self._last_pipeline_result