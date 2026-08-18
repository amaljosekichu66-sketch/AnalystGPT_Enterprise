"""

Application orchestration layer.



Coordinates the complete AnalystGPT Enterprise

processing pipeline.

"""

from __future__ import annotations

import time
from typing import Any

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



# AI Layer (Sprint 11 & Sprint 14 Phase 2)
from src.ai.ai_job_service import AIJobService
from src.ai.ai_manager import AIManager
from src.ai.ai_result import AIResult
from src.ai.job_executor import AIJobExecutor

# Identity Layer (Sprint 13)
from src.identity.context import (
    UserContext,
    get_current_user_context,
)

# Governance Layer (Sprint 14 Phase 3)
from src.governance.governance_service import (
    CleaningGovernanceService,
    GovernedCleaningError,
    GovernedExecutionResult,
)
from src.governance.models import CleaningConfig, DatasetVersion, MissingValuePolicy
from src.governance.preview_service import CleaningPreviewResult, CleaningPreviewService
from src.storage.artifact_store import LocalArtifactStore


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
        # Storage & Governance Layer (Sprint 14 Phase 3)
        # -------------------------------------------------

        self.artifact_store = LocalArtifactStore()
        self.governance_service = CleaningGovernanceService(
            artifact_store=self.artifact_store,
            quality_manager=self.quality_manager,
            cleaning_manager=self.cleaning_manager,
        )
        self.preview_service = CleaningPreviewService(
            quality_manager=self.quality_manager,
            cleaning_manager=self.cleaning_manager,
        )

        # -------------------------------------------------
        # AI Insight Engine & Job Subsystem (Sprint 14 Phase 2)
        # -------------------------------------------------

        self.ai_manager = AIManager()
        self.ai_job_executor = AIJobExecutor(
            ai_manager=self.ai_manager
        )
        self.ai_job_service = AIJobService(
            job_executor=self.ai_job_executor
        )
        try:
            self.ai_job_service.recover_stale_jobs()
        except Exception as exc:
            logger.warning("Could not run stale AI job recovery: %s", exc)

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
        self._user_pipeline_results: dict[int | None, PipelineResult] = {}
        self._user_cached_paths: dict[int | None, str] = {}



    def run(
        self,
        input_path: str,
        user_context: UserContext | None = None,
    ) -> PipelineResult:
        """
        Execute the complete AnalystGPT Enterprise
        processing pipeline.

        Parameters
        ----------
        input_path:
            Dataset location.
        user_context:
            Optional authenticated identity context (Sprint 13).
            If omitted, defaults to active request context.

        Returns
        -------
        PipelineResult
        """
        active_context = user_context or get_current_user_context()
        user_id = active_context.user_id if active_context.is_authenticated else None




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



        logger.info(
            "Identity Context    : User=%s | Role=%s | Authenticated=%s",
            active_context.username,
            active_context.role.value,
            active_context.is_authenticated,
        )

        logger.info("=" * 80)

        logger.info("Starting AnalystGPT Enterprise...")

        logger.info("=" * 80)



        start_time = time.perf_counter()



        try:



            self.persistence.initialize()

            # Ensure user_id exists in the database if specified (to satisfy foreign key)
            eff_user_id = user_id
            if eff_user_id is not None and self.persistence.user_repository is not None:
                if self.persistence.user_repository.get_by_id(eff_user_id) is None:
                    eff_user_id = None

            self.persistence.start_pipeline(user_id=eff_user_id)



            # -------------------------------------------------

            # Upload

            # -------------------------------------------------



            # -------------------------------------------------
            # Upload & Immutable Artifact Preservation (Sprint 14 Phase 3)
            # -------------------------------------------------

            source_version, raw_dataframe = self.governance_service.register_source_dataset(
                file_path_or_bytes=Path(input_path),
                filename=Path(input_path).name,
                user_id=eff_user_id,
            )

            self.persistence.save_dataset(
                dataset_name=source_version.source_filename,
                row_count=source_version.row_count,
                column_count=source_version.column_count,
                user_id=eff_user_id,
            )

            # -------------------------------------------------
            # Cleaning Configuration & Governed Execution (Sprint 14 Phase 3)
            # -------------------------------------------------

            cleaning_config = self.governance_service.create_default_config(
                user_id=eff_user_id,
            )

            governed_result = self._clean_dataset_governed(
                raw_dataframe=raw_dataframe,
                cleaning_config=cleaning_config,
                source_version=source_version,
                pipeline_run_id=self.persistence._pipeline_run_id,
                user_id=eff_user_id,
            )
            cleaned_dataframe = governed_result.cleaned_df

            # Persist all governance artifacts
            self.persistence.save_governance(governed_result)

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
            # Finalise Pipeline – deterministic processing complete
            # -------------------------------------------------

            self.persistence.finish_pipeline()

            # -------------------------------------------------
            # Asynchronous AI Insight Job Creation & Dispatch (Sprint 14 Phase 2)
            # -------------------------------------------------

            ai_job = self.ai_job_service.create_and_dispatch_job(
                pipeline_run_id=self.persistence._pipeline_run_id,
                reporting_report=reporting_report,
                user_id=user_id,
                report_id=self.persistence._report_id,
            )

            # -------------------------------------------------
            # Pipeline Summary
            # -------------------------------------------------

            self._log_pipeline_summary(
                quality_report,
                analytics_report,
                reporting_report,
                ai_job=ai_job,
            )

            execution_time = (
                time.perf_counter() - start_time
            )

            result = self._build_pipeline_result(
                reporting_report=reporting_report,
                ai_result=None,
                execution_time=execution_time,
                ai_job_id=ai_job.job_id,
                ai_job_status=ai_job.status.value,
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



            self._cache_pipeline_result(result, input_path, user_context=active_context)



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



    def _clean_dataset_governed(
        self,
        raw_dataframe: DataFrame,
        cleaning_config: "Any",
        source_version: "Any",
        pipeline_run_id: int,
        user_id: "int | None" = None,
    ) -> "Any":
        """
        Execute the governance-aware cleaning stage (Sprint 14 Phase 3).

        Wraps CleaningGovernanceService to produce:
        - GovernedCleaningResult with cleaned DataFrame
        - Immutable source and cleaned DatasetVersions
        - CleaningProvenance audit record
        - Before/after QualityComparison

        Parameters
        ----------
        raw_dataframe:
            Unmodified raw DataFrame from UploadManager.
        cleaning_config:
            CleaningConfig with policy + parameters.
        source_version:
            Immutable DatasetVersion for the raw dataset.
        pipeline_run_id:
            Owning pipeline run.
        user_id:
            Authenticated user.

        Returns
        -------
        GovernedCleaningResult
        """
        logger.info("-" * 60)
        logger.info("CLEANING STAGE (Governance-Aware)")
        logger.info("-" * 60)

        governed_result = self.governance_service.execute_governed_cleaning(
            raw_df=raw_dataframe,
            config=cleaning_config,
            source_version=source_version,
            pipeline_run_id=pipeline_run_id,
            user_id=user_id,
        )

        logger.info(
            "Data Preview After Cleaning:"
        )
        logger.info(
            "\n%s",
            governed_result.cleaned_df.head(),
        )

        return governed_result


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
        ai_result: AIResult | None = None,
        ai_job: Any | None = None,
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
        if ai_job is not None:
            logger.info("AI Job ID               : %s", ai_job.job_id)
            logger.info("AI Job Status           : %s", ai_job.status.value)
            logger.info("AI Model                : %s", ai_job.model)
            logger.info("AI Provider             : %s", ai_job.provider)
        elif ai_result is not None and ai_result.success and ai_result.ai_report is not None:
            logger.info("AI Model                : %s", ai_result.ai_report.model)
            logger.info("AI Provider             : %s", ai_result.ai_report.provider)
            logger.info("AI Time (s)            : %.4f", ai_result.execution_time)
        else:
            logger.info("AI Stage                : Dispatched Asynchronously")

        # Final output
        logger.info(
            "Report Exported         : %s",
            reporting_report.export_path,
        )
        logger.info("=" * 60)
        logger.info("Pipeline persisted successfully.")
        logger.info("AnalystGPT Enterprise completed successfully.")

    def _build_pipeline_result(
        self,
        reporting_report: ReportingReport,
        ai_result: AIResult | None = None,
        execution_time: float = 0.0,
        ai_job_id: str | None = None,
        ai_job_status: str | None = None,
    ) -> PipelineResult:
        """
        Build the final application result.
        """
        generated_at = datetime.now(UTC)

        ai_report_obj = None
        if ai_result is not None and ai_result.success:
            ai_report_obj = ai_result.ai_report

        pipeline_report = PipelineReport(
            reporting_report=reporting_report,
            ai_report=ai_report_obj,
            generated_at=generated_at,
        )

        return PipelineResult(
            success=True,
            pipeline_report=pipeline_report,
            output_path=reporting_report.export_path,
            execution_time=execution_time,
            ai_job_id=ai_job_id,
            ai_job_status=ai_job_status,
        )

    def _cache_pipeline_result(

        self,

        result: PipelineResult,

        dataset_path: str,
        user_context: UserContext | None = None,

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
            context = user_context or get_current_user_context()
            user_id = context.user_id if context.is_authenticated else None
            self._user_pipeline_results[user_id] = result
            self._user_cached_paths[user_id] = dataset_path

            self._last_pipeline_result = result
            self._cached_dataset_path = dataset_path

            logger.info(

                "PipelineResult cached successfully for dataset: %s (user_id=%s)",

                dataset_path,
                user_id,

            )

        else:

            logger.warning(

                "Pipeline failed. Cache not updated."

            )



    def clear_cache(

        self,
        user_id: int | None = None,

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



        if user_id is not None and user_id in self._user_pipeline_results:
            del self._user_pipeline_results[user_id]
            self._user_cached_paths.pop(user_id, None)

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
        user_context: UserContext | None = None,

    ) -> PipelineResult:

        """

        Return the cached PipelineResult if it exists and matches the requested dataset.

        If no cached result exists for this dataset, execute the pipeline and cache the result.

        """
        active_context = user_context or get_current_user_context()
        user_id = active_context.user_id if active_context.is_authenticated else None

        if (
            user_id in self._user_pipeline_results
            and self._user_cached_paths.get(user_id) == input_path
        ):
            logger.info("=" * 80)
            logger.info("USING CACHED PIPELINE RESULT FOR USER: %s", active_context.username)
            logger.info("=" * 80)
            return self._user_pipeline_results[user_id]

        if (
            user_id is None
            and self._last_pipeline_result is not None
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
            user_context=active_context,

        )



    def get_result_for_user(self, user_id: int | None = None) -> PipelineResult | None:
        """
        Retrieve cached pipeline result for a specific user ID.
        """
        if user_id is not None:
            return self._user_pipeline_results.get(user_id)
        return self._last_pipeline_result

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

    def shutdown(self) -> None:
        """
        Gracefully shutdown application background executors and persistence resources.
        """
        if hasattr(self, "ai_job_executor") and self.ai_job_executor is not None:
            self.ai_job_executor.shutdown(wait=False)
        if hasattr(self, "persistence") and self.persistence is not None:
            self.persistence.shutdown()