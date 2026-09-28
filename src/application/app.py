"""

Application orchestration layer.



Coordinates the complete AnalystGPT Enterprise

processing pipeline.

"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pandas import DataFrame

# AI Layer (Sprint 11 & Sprint 14 Phase 2)
from src.ai.ai_job_service import AIJobService
from src.ai.ai_manager import AIManager
from src.ai.ai_result import AIResult
from src.ai.job_executor import AIJobExecutor
from src.analytics.analytics_manager import AnalyticsManager
from src.analytics.analytics_report import AnalyticsReport
from src.cleaning.cleaning_manager import CleaningManager
from src.core import config as _core_config
from src.core.exceptions import (
    DatasetNotFoundError,
    PipelineResultNotFoundError,
    TooManyConcurrentJobsError,
)
from src.core.logger import logger

# Governance Layer (Sprint 14 Phase 3)
from src.governance.governance_service import (
    CleaningGovernanceService,
    GovernedCleaningError,
    GovernedExecutionResult,
)
from src.governance.models import CleaningConfig, DatasetVersion, MissingValuePolicy
from src.governance.preview_service import CleaningPreviewResult, CleaningPreviewService

# Identity Layer (Sprint 13)
from src.identity.context import (
    UserContext,
    get_current_user_context,
)
from src.identity.exceptions import PermissionDeniedError
from src.identity.permissions import Permission
from src.persistence.persistence_manager import PersistenceManager
from src.quality.quality_manager import QualityManager
from src.quality.quality_report import QualityReport
from src.reporting.reporting_manager import ReportingManager
from src.reporting.reporting_report import ReportingReport
from src.storage.artifact_store import LocalArtifactStore
from src.storage.exceptions import ArtifactStoreError
from src.upload.upload_manager import UploadManager
from src.upload.upload_policy import UnparseableUploadError, UploadRejectedError, check_dataset_shape

from .pipeline_report import PipelineReport
from .pipeline_result import PipelineResult

# Application layer contracts


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
        self.ai_job_executor = AIJobExecutor(ai_manager=self.ai_manager)
        self.ai_job_service = AIJobService(job_executor=self.ai_job_executor)
        try:
            self.ai_job_service.recover_stale_jobs()
        except Exception as exc:
            logger.warning("Could not run stale AI job recovery: %s", exc)

        # --------------------------------------------
        # Persistence Layer
        # --------------------------------------------
        #
        # There is deliberately NO shared PersistenceManager. The Application
        # is a process-wide singleton serving concurrent requests, and a
        # PersistenceManager holds per-run state (connection, repositories,
        # pipeline_run_id, user_id, report_id). One shared instance let
        # concurrent runs swap and close each other's SQLite connection and
        # write rows under each other's run and user ids - reproduced as FK /
        # UNIQUE violations and a native crash of the API process (B-03).
        # Every run and every request opens its own via `persistence_session()`.

        self._persistence_factory = PersistenceManager

        # --------------------------------------------

        # Cached Pipeline Result

        # --------------------------------------------

        self._last_pipeline_result: PipelineResult | None = None

        self._cache_lock = threading.RLock()

        #: user_id -> heavy jobs in progress (SEC-10).
        self._active_jobs: dict[int | None, int] = {}

        self._cached_dataset_path: str | None = None
        self._user_pipeline_results: dict[int | None, PipelineResult] = {}
        self._user_cached_paths: dict[int | None, str] = {}
        self._report_pipeline_results: dict[int, PipelineResult] = {}

        #: (runner user_id, dataset_version_id) -> latest result, for read-only views.
        self._dataset_results: dict[tuple[int | None, str], PipelineResult] = {}

    # ==========================================================
    # Persistence sessions
    # ==========================================================

    @contextmanager
    def persistence_session(self) -> Iterator[PersistenceManager]:
        """
        Yield a PersistenceManager with its own database connection, closed
        on exit. Never share one across requests or runs.
        """
        persistence = self._persistence_factory()
        persistence.initialize()
        try:
            yield persistence
        finally:
            persistence.shutdown()

    @contextmanager
    def _job_slot(self, context: UserContext) -> Iterator[None]:
        """
        Hold one of the caller's `MAX_CONCURRENT_JOBS_PER_USER` slots (SEC-10).

        Parsing an upload and running the pipeline are the expensive
        operations; without a cap one account could occupy every worker.
        """
        user_id = context.user_id if context.is_authenticated else None
        limit = max(1, int(_core_config.MAX_CONCURRENT_JOBS_PER_USER))
        with self._cache_lock:
            if self._active_jobs.get(user_id, 0) >= limit:
                raise TooManyConcurrentJobsError(
                    f"You already have {limit} jobs in progress. Wait for one to finish and retry."
                )
            self._active_jobs[user_id] = self._active_jobs.get(user_id, 0) + 1
        try:
            yield
        finally:
            with self._cache_lock:
                remaining = self._active_jobs.get(user_id, 1) - 1
                if remaining > 0:
                    self._active_jobs[user_id] = remaining
                else:
                    self._active_jobs.pop(user_id, None)

    def purge_user_data(self, user_id: int, username: str) -> dict[str, int]:
        """
        Delete everything the account owns (SEC-20) and forget its cached results.
        """
        from src.persistence.user_data_purge import UserDataPurger

        deleted = UserDataPurger(self.artifact_store).purge(user_id, expected_username=username)
        with self._cache_lock:
            removed = self._user_pipeline_results.pop(user_id, None)
            self._user_cached_paths.pop(user_id, None)
            for key in [k for k in self._dataset_results if k[0] == user_id]:
                del self._dataset_results[key]
            if removed is not None and self._last_pipeline_result is removed:
                self._last_pipeline_result = None
            for report_id in [r for r, res in self._report_pipeline_results.items() if res is removed]:
                del self._report_pipeline_results[report_id]
        return deleted

    # ==========================================================
    # Managed datasets (server-issued identifiers)
    # ==========================================================

    def register_upload(
        self,
        content: bytes,
        filename: str,
        user_context: UserContext | None = None,
    ) -> DatasetVersion:
        """
        Store client-uploaded bytes in the managed artifact store and register
        them as a source DatasetVersion owned by the caller.

        `filename` must already have passed `upload_policy.validate_upload_filename`;
        it is a display label only. The returned `version_id` is the ONLY
        handle a client gets - the storage path never leaves the server.
        """
        context = user_context or get_current_user_context()

        with self._job_slot(context), self.persistence_session() as persistence:
            owner_id = self._persisted_user_id(persistence, context)
            if owner_id is None:
                raise PermissionDeniedError("Dataset uploads require a registered, authenticated account.")

            try:
                source_version, parsed = self.governance_service.register_source_dataset(
                    file_path_or_bytes=content,
                    filename=filename,
                    user_id=owner_id,
                )
            except ArtifactStoreError:
                raise
            except Exception as exc:
                # The artifact is discarded by the governance service; the
                # parser's message can quote server paths, so it stays in logs.
                logger.warning("Uploaded dataset '%s' could not be parsed: %s", filename, exc)
                raise UnparseableUploadError("Uploaded file could not be parsed as a dataset.") from exc

            try:
                check_dataset_shape(len(parsed), len(parsed.columns))
            except UploadRejectedError:
                self.artifact_store.discard_raw_artifact(source_version.storage_path)
                raise

            persistence.dataset_version_repository.create(source_version)

        logger.info(
            "Registered uploaded dataset version_id=%s owner=%s rows=%d",
            source_version.version_id,
            owner_id,
            source_version.row_count,
        )
        return source_version

    def resolve_source_version(
        self,
        dataset_version_id: str,
        user_context: UserContext | None = None,
    ) -> DatasetVersion:
        """
        Resolve a client-supplied dataset identifier to a stored source version.

        Enforces ownership (admins may resolve any dataset, matching the
        governance catalog) and re-checks that the stored artifact lives
        inside the managed store. Unknown, foreign and non-source versions all
        raise the same `DatasetNotFoundError`, so existence is not disclosed.
        """
        context = user_context or get_current_user_context()
        if not context.is_authenticated:
            raise DatasetNotFoundError("Dataset not found.")

        scoped_user_id = None if context.has_permission(Permission.USER_MANAGE) else context.user_id

        with self.persistence_session() as persistence:
            row = persistence.dataset_version_repository.get_by_version_id(
                dataset_version_id,
                user_id=scoped_user_id,
            )

        if row is None or not bool(row.get("is_source", 1)):
            raise DatasetNotFoundError("Dataset not found.")

        try:
            storage_path = self.artifact_store.resolve_managed_raw_path(row["storage_path"])
        except ArtifactStoreError as exc:
            logger.error("Dataset %s failed managed-store resolution: %s", dataset_version_id, exc)
            raise DatasetNotFoundError("Dataset not found.") from exc

        return DatasetVersion(
            version_id=row["version_id"],
            source_filename=row.get("source_filename") or "dataset",
            byte_size=row.get("byte_size") or 0,
            checksum_sha256=row.get("checksum_sha256") or "",
            row_count=row.get("row_count") or 0,
            column_count=row.get("column_count") or 0,
            storage_path=str(storage_path),
            is_source=True,
            content_type=row.get("content_type") or "application/octet-stream",
            parent_version_id=row.get("parent_version_id"),
            schema_json=row.get("schema_json"),
            user_id=row.get("user_id"),
            created_at=str(row.get("created_at") or ""),
        )

    def load_source_dataframe(self, source_version: DatasetVersion) -> DataFrame:
        """Parse a resolved source version from the managed store."""
        return self.upload_manager.upload(source_version.storage_path)

    def run_dataset_version(
        self,
        dataset_version_id: str,
        user_context: UserContext | None = None,
    ) -> PipelineResult:
        """
        Execute the pipeline on a previously uploaded dataset.

        This is the entry point for API callers. Resolution failures raise
        `DatasetNotFoundError` BEFORE a pipeline run record is created.
        """
        source_version = self.resolve_source_version(dataset_version_id, user_context)
        context = user_context or get_current_user_context()

        with self._job_slot(context):
            return self._execute(
                user_context=user_context,
                cache_key=self.dataset_cache_key(dataset_version_id),
                input_label=f"dataset_version_id={dataset_version_id}",
                load_source=lambda _owner_id: (source_version, self.load_source_dataframe(source_version)),
            )

    def get_result_for_dataset(
        self,
        dataset_version_id: str,
        user_context: UserContext | None = None,
    ) -> PipelineResult:
        """
        Return the latest pipeline result for an uploaded dataset. READ-ONLY.

        This never executes the pipeline. Dashboard and Power BI views are
        gated on view permissions that VIEWER holds; they used to fall through
        to `run()` on a cache miss, which let a VIEWER trigger execution
        without PIPELINE_EXECUTE. Execution is only reachable through
        `POST /api/pipeline`.

        Raises `DatasetNotFoundError` for datasets the caller may not use
        (checked first, so a cached result is never served across owners) and
        `PipelineResultNotFoundError` when the dataset has not been run yet.
        """
        context = user_context or get_current_user_context()
        self.resolve_source_version(dataset_version_id, context)

        user_id = context.user_id if context.is_authenticated else None
        with self._cache_lock:
            result = self._dataset_results.get((user_id, dataset_version_id))
            if result is None and context.has_permission(Permission.USER_MANAGE):
                for (_, cached_dataset_id), cached in reversed(list(self._dataset_results.items())):
                    if cached_dataset_id == dataset_version_id:
                        result = cached
                        break

        if result is None:
            raise PipelineResultNotFoundError(
                "No pipeline result for this dataset yet. Execute it with POST /api/pipeline first."
            )
        return result

    @staticmethod
    def dataset_cache_key(dataset_version_id: str) -> str:
        return f"dataset_version:{dataset_version_id}"

    @staticmethod
    def _persisted_user_id(
        persistence: PersistenceManager,
        context: UserContext,
    ) -> int | None:
        """Return the caller's user id if it exists in the users table, else None (FK safety)."""
        if not context.is_authenticated or context.user_id is None:
            return None
        if persistence.user_repository is None:
            return None
        if persistence.user_repository.get_by_id(context.user_id) is None:
            return None
        return context.user_id

    # ==========================================================
    # Pipeline execution
    # ==========================================================

    def run(
        self,
        input_path: str,
        user_context: UserContext | None = None,
    ) -> PipelineResult:
        """
        Execute the pipeline on a file from the server's OWN filesystem.

        Trusted, local entry point for the CLI (`main.py`) and in-process
        tests. It is deliberately not reachable from HTTP: API callers upload
        bytes and use `run_dataset_version`, so a client can never name a
        server path.

        Parameters
        ----------
        input_path:
            Dataset location on the local filesystem.
        user_context:
            Optional authenticated identity context (Sprint 13).
            If omitted, defaults to active request context.

        Returns
        -------
        PipelineResult
        """
        return self._execute(
            user_context=user_context,
            cache_key=input_path,
            input_label=input_path,
            load_source=lambda owner_id: self.governance_service.register_source_dataset(
                file_path_or_bytes=Path(input_path),
                filename=Path(input_path).name,
                user_id=owner_id,
            ),
        )

    def _execute(
        self,
        user_context: UserContext | None,
        cache_key: str,
        input_label: str,
        load_source: Callable[[int | None], tuple[DatasetVersion, DataFrame]],
    ) -> PipelineResult:
        """
        Run every pipeline stage for one source dataset.

        `load_source(owner_id)` supplies the source DatasetVersion and its
        parsed DataFrame; everything downstream is identical for the local
        and the managed-dataset entry points.
        """
        input_path = input_label
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

        # Run-local: this run's connection, repositories and ids are never
        # visible to a concurrent run.
        persistence = self._persistence_factory()

        try:

            persistence.initialize()

            # Ensure user_id exists in the database if specified (to satisfy foreign key)
            eff_user_id = user_id
            if eff_user_id is not None and persistence.user_repository is not None:
                if persistence.user_repository.get_by_id(eff_user_id) is None:
                    eff_user_id = None

            persistence.start_pipeline(user_id=eff_user_id)

            # -------------------------------------------------

            # Upload

            # -------------------------------------------------

            # -------------------------------------------------
            # Upload & Immutable Artifact Preservation (Sprint 14 Phase 3)
            # -------------------------------------------------

            source_version, raw_dataframe = load_source(eff_user_id)

            persistence.save_dataset(
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
                pipeline_run_id=persistence._pipeline_run_id,
                user_id=eff_user_id,
            )
            cleaned_dataframe = governed_result.cleaned_df

            # Persist all governance artifacts
            persistence.save_governance(governed_result)

            # -------------------------------------------------

            # Quality

            # -------------------------------------------------

            quality_report = self._assess_quality(cleaned_dataframe)

            persistence.save_quality(
                quality_report,
            )

            # -------------------------------------------------

            # Analytics

            # -------------------------------------------------

            analytics_report = self._generate_analytics(cleaned_dataframe)

            persistence.save_analytics(
                analytics_report,
            )

            # -------------------------------------------------

            # Reporting

            # -------------------------------------------------

            reporting_report = self._generate_report(
                analytics_report,
                pipeline_run_id=persistence._pipeline_run_id,
            )

            persistence.save_report(
                reporting_report,
            )

            # -------------------------------------------------
            # Finalise Pipeline – deterministic processing complete
            # -------------------------------------------------

            persistence.finish_pipeline()

            # -------------------------------------------------
            # Asynchronous AI Insight Job Creation & Dispatch (Sprint 14 Phase 2)
            # -------------------------------------------------

            ai_job = self.ai_job_service.create_and_dispatch_job(
                pipeline_run_id=persistence._pipeline_run_id,
                reporting_report=reporting_report,
                user_id=user_id,
                report_id=persistence._report_id,
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

            execution_time = time.perf_counter() - start_time

            result = self._build_pipeline_result(
                reporting_report=reporting_report,
                ai_result=None,
                execution_time=execution_time,
                ai_job_id=ai_job.job_id,
                ai_job_status=ai_job.status.value,
                dataset_version_id=source_version.version_id,
                pipeline_run_id=persistence._pipeline_run_id,
                report_id=persistence._report_id,
                cleaned_version_id=persistence._cleaned_version_id,
                cleaning_execution_id=persistence._cleaning_execution_id,
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

            self._cache_pipeline_result(
                result,
                cache_key,
                user_context=active_context,
                report_id=persistence._report_id,
            )

            return result

        except Exception as error:

            import traceback

            print("\n" + "=" * 80)
            print("APPLICATION EXCEPTION")
            print("=" * 80)

            traceback.print_exc()

            print(f"Exception Type : {type(error).__name__}")
            print(f"Exception      : {error}")

            logger.exception("Pipeline execution failed.")

            try:
                persistence.fail_pipeline()
            except Exception:
                logger.exception("Unable to mark pipeline as FAILED.")

            execution_time = time.perf_counter() - start_time

            return PipelineResult(
                success=False,
                execution_time=execution_time,
                error=error,
            )

        finally:

            persistence.shutdown()

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

        dataframe = self.upload_manager.upload(input_path)

        logger.info("Data Preview Before Cleaning:")

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

        cleaned_dataframe = self.cleaning_manager.clean(dataframe)

        logger.info("Data Preview After Cleaning:")

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

        logger.info("Data Preview After Cleaning:")
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

        return self.quality_manager.assess(dataframe)

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

        return self.analytics_manager.analyze(dataframe)

    def _generate_report(
        self,
        analytics_report: AnalyticsReport,
        pipeline_run_id: int | None = None,
    ) -> ReportingReport:
        """
        Execute the reporting stage.

        Parameters
        ----------
        analytics_report:
            Analytics report.
        pipeline_run_id:
            Optional pipeline run identifier for artifact isolation.

        Returns
        -------
        ReportingReport
        """

        logger.info("-" * 60)
        logger.info("REPORTING STAGE")
        logger.info("-" * 60)

        output_path = (
            _core_config.REPORT_OUTPUT_DIRECTORY / f"report_run_{pipeline_run_id}.txt"
            if pipeline_run_id is not None
            else None
        )

        reporting_report = self.reporting_manager.generate_report(
            analytics_report,
            output_path=output_path,
        )

        logger.info("Report successfully generated.")

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

        ai_result = self.ai_manager.generate_ai_report(reporting_report)

        if ai_result.success:

            logger.info("AI report generated successfully.")

        else:

            logger.warning("AI Insight Engine unavailable. " "Pipeline completed without AI enrichment.")

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

        descriptive = analytics_report.report["descriptive_statistics"]

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
            quality["completeness"]["complete_percentage"],
        )

        logger.info(
            "Duplicate Rows          : %s",
            quality["uniqueness"]["duplicate_rows"],
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
        dataset_version_id: str | None = None,
        pipeline_run_id: int | None = None,
        report_id: int | None = None,
        cleaned_version_id: str | None = None,
        cleaning_execution_id: str | None = None,
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
            dataset_version_id=dataset_version_id,
            pipeline_run_id=pipeline_run_id,
            report_id=report_id,
            cleaned_version_id=cleaned_version_id,
            cleaning_execution_id=cleaning_execution_id,
        )

    def _cache_pipeline_result(
        self,
        result: PipelineResult,
        dataset_path: str,
        user_context: UserContext | None = None,
        report_id: int | None = None,
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

            with self._cache_lock:
                self._user_pipeline_results[user_id] = result
                self._user_cached_paths[user_id] = dataset_path

                if result.dataset_version_id is not None:
                    key = (user_id, result.dataset_version_id)
                    # Re-insert so iteration order tracks recency.
                    self._dataset_results.pop(key, None)
                    self._dataset_results[key] = result

                if report_id is not None:
                    self._report_pipeline_results[report_id] = result

                self._last_pipeline_result = result
                self._cached_dataset_path = dataset_path

            logger.info(
                "PipelineResult cached successfully for dataset: %s (user_id=%s)",
                dataset_path,
                user_id,
            )

        else:

            logger.warning("Pipeline failed. Cache not updated.")

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

        if user_id in self._user_pipeline_results and self._user_cached_paths.get(user_id) == input_path:
            logger.info("=" * 80)
            logger.info("USING CACHED PIPELINE RESULT FOR USER: %s", active_context.username)
            logger.info("=" * 80)
            return self._user_pipeline_results[user_id]

        if user_id is None and self._last_pipeline_result is not None and self._cached_dataset_path == input_path:

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

    def set_result_for_user(
        self,
        user_id: int | None,
        result: PipelineResult,
        report_id: int | None = None,
    ) -> None:
        """
        Register a pipeline result for a specific user ID and optional report ID.
        """
        with self._cache_lock:
            if user_id is not None:
                self._user_pipeline_results[user_id] = result
            self._last_pipeline_result = result
            if report_id is not None:
                self._report_pipeline_results[report_id] = result

    def get_result_by_report_id(
        self,
        report_id: int,
    ) -> PipelineResult | None:
        """
        Retrieve cached pipeline result by report ID.
        """
        return self._report_pipeline_results.get(report_id)

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
        Gracefully shutdown application background executors.

        Persistence needs no teardown here: every run and request closes its
        own connection when its `persistence_session()` ends.
        """
        if hasattr(self, "ai_job_executor") and self.ai_job_executor is not None:
            self.ai_job_executor.shutdown(wait=False)
