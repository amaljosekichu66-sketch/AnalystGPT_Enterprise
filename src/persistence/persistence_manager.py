from __future__ import annotations

from typing import Any

from src.core.logger import logger


from src.database.database_manager import DatabaseManager
from src.database.schema_manager import SchemaManager
from src.database.connection_factory import ConnectionFactory

from src.database.repositories.ai_job_repository import (
    AIJobRepository,
)
from src.database.repositories.ai_report_repository import (
    AIReportRepository,
)
from src.database.repositories.analytics_repository import (
    AnalyticsRepository,
)
from src.database.repositories.cleaning_config_repository import (
    CleaningConfigRepository,
)
from src.database.repositories.cleaning_execution_repository import (
    CleaningExecutionRepository,
)
from src.database.repositories.dataset_repository import (
    DatasetRepository,
)
from src.database.repositories.dataset_version_repository import (
    DatasetVersionRepository,
)
from src.database.repositories.pipeline_run_repository import (
    PipelineRunRepository,
)
from src.analytics.analytics_report import AnalyticsReport
from src.database.repositories.quality_repository import (
    QualityRepository,
)
from src.database.repositories.report_repository import (
    ReportRepository,
)
from src.database.repositories.user_repository import (
    UserRepository,
)
from src.persistence.persistence_result import PersistenceResult
from src.quality.quality_report import QualityReport
from src.reporting.reporting_report import ReportingReport



class PersistenceManager:
    """
    Coordinates all persistence operations for AnalystGPT Enterprise.
    """

    def __init__(self):
        self._database_manager = None
        self._database_connection = None

        self._pipeline_repository = None
        self._dataset_repository = None
        self._quality_repository = None
        self._analytics_repository = None
        self._report_repository = None
        self._ai_job_repository = None
        self._ai_report_repository = None
        self._user_repository = None

        # Phase 3 — Governance repositories
        self._dataset_version_repository = None
        self._cleaning_config_repository = None
        self._cleaning_execution_repository = None


        self._pipeline_run_id = None
        self._user_id = None
        self._dataset_id = None
        self._quality_report_id = None
        self._analytics_report_id = None
        self._report_id = None

    # ---------------------------------------------------------

    def initialize(self):

        """
        Initialize database infrastructure.
        """

        # Create the configured database connection.
        self._database_connection = (
            ConnectionFactory.create_connection()
        )

        # Log the active database engine.
        engine_name = {
            "sqlite": "SQLite",
            "postgresql": "PostgreSQL",
        }.get(
            self._database_connection.database_type(),
            self._database_connection.database_type(),
        )

        logger.info(
            "Database Engine          : %s",
            engine_name,
        )

        # Create and initialize the database manager.
        self._database_manager = DatabaseManager(
            self._database_connection
        )

        self._database_manager.initialize()

        # Initialize the database schema.
        schema = SchemaManager(
            self._database_connection
        )

        schema.initialize_schema()

        # Initialize repositories.
        self._pipeline_repository = (
            PipelineRunRepository(
                self._database_connection
            )
        )

        self._dataset_repository = (
            DatasetRepository(
                self._database_connection
            )
        )

        self._quality_repository = (
            QualityRepository(
                self._database_connection
            )
        )

        self._analytics_repository = (
            AnalyticsRepository(
                self._database_connection
            )
        )

        self._report_repository = (
            ReportRepository(
                self._database_connection
            )
        )

        self._ai_job_repository = (
            AIJobRepository(
                self._database_connection
            )
        )

        self._ai_report_repository = (
            AIReportRepository(
                self._database_connection
            )
        )

        self._user_repository = (
            UserRepository(
                self._database_connection
            )
        )

        # Phase 3 — Governance repositories
        self._dataset_version_repository = (
            DatasetVersionRepository(
                self._database_connection
            )
        )

        self._cleaning_config_repository = (
            CleaningConfigRepository(
                self._database_connection
            )
        )

        self._cleaning_execution_repository = (
            CleaningExecutionRepository(
                self._database_connection
            )
        )

    # ---------------------------------------------------------

    def start_pipeline(self, user_id: int | None = None):

        """
        Start pipeline run with optional user ownership.
        """
        self._user_id = user_id
        self._pipeline_run_id = (
            self._pipeline_repository.create(
                "RUNNING",
                user_id=user_id,
            )
        )

    # ---------------------------------------------------------

    def save_dataset(
        self,
        dataset_name,
        row_count,
        column_count,
        user_id: int | None = None,
    ):
        """
        Persist dataset metadata with user ownership.
        """
        eff_user_id = user_id if user_id is not None else self._user_id
        self._dataset_id = (
            self._dataset_repository.create(
                self._pipeline_run_id,
                dataset_name,
                row_count,
                column_count,
                user_id=eff_user_id,
            )
        )

    # ---------------------------------------------------------

    def save_quality(
        self,
        quality_report,
    ):
        """
        Persist the quality assessment.
        """

        quality = quality_report.report

        self._quality_report_id = (
            self._quality_repository.create(
                self._pipeline_run_id,
                quality["completeness"][
                    "complete_percentage"
                ],
                None,
                None,
                None,
            )
        )

    # ---------------------------------------------------------

    def save_analytics(
        self,
        analytics_report,
    ):
        """
        Persist analytics results.
        """

        descriptive = analytics_report.report[
            "descriptive_statistics"
        ]

        correlation = analytics_report.report[
            "correlation_analysis"
        ]

        self._analytics_report_id = (
            self._analytics_repository.create(
                self._pipeline_run_id,
                descriptive[
                    "numeric_column_count"
                ],
                descriptive[
                    "categorical_column_count"
                ],
                str(correlation),
            )
        )

    # ---------------------------------------------------------

    def save_report(
        self,
        reporting_report: ReportingReport,
        user_id: int | None = None,
    ):
        """
        Persist reporting metadata with user ownership.
        """
        eff_user_id = user_id if user_id is not None else self._user_id
        self._report_id = (
            self._report_repository.create(
                self._pipeline_run_id,
                reporting_report.export_path,
                user_id=eff_user_id,
            )
        )

    # ---------------------------------------------------------

    def finish_pipeline(self) -> PersistenceResult:

        if self._pipeline_run_id is not None:
            self._pipeline_repository.execute(
                """
                UPDATE pipeline_runs
                SET status = ?
                WHERE id = ?;
                """,
                (
                    "SUCCESS",
                    self._pipeline_run_id,
                ),
            )

        return PersistenceResult(
            pipeline_run_id=self._pipeline_run_id,
            dataset_id=self._dataset_id,
            quality_report_id=self._quality_report_id,
            analytics_report_id=self._analytics_report_id,
            report_id=self._report_id,
            success=True,
        )

    # ---------------------------------------------------------

    def fail_pipeline(self):
        if self._pipeline_run_id is not None:
            self._pipeline_repository.execute(
                """
                UPDATE pipeline_runs
                SET status = ?
                WHERE id = ?;
                """,
                (
                    "FAILED",
                    self._pipeline_run_id,
                ),
            )

    # ---------------------------------------------------------

    @property
    def ai_job_repository(self) -> AIJobRepository | None:
        return self._ai_job_repository

    @property
    def ai_report_repository(self) -> AIReportRepository | None:
        return self._ai_report_repository

    # ---------------------------------------------------------
    # Phase 3 — Governance Persistence
    # ---------------------------------------------------------

    def save_governance(
        self,
        governed_result: Any,
    ) -> None:
        """
        Persist all Phase 3 governance artifacts:
        - Source DatasetVersion (if not already persisted)
        - CleaningConfig
        - CleaningExecution
        - Cleaned DatasetVersion
        """
        if self._dataset_version_repository is None:
            return

        # 1. Persist source version if not present
        existing_src = self._dataset_version_repository.get_by_version_id(
            governed_result.source_version.version_id
        )
        if existing_src is None:
            self._dataset_version_repository.create(
                governed_result.source_version
            )

        # 2. Persist cleaning config
        self._cleaning_config_repository.create(
            governed_result.cleaning_config
        )

        # 3. Persist cleaned version (before execution record due to FK constraint)
        self._dataset_version_repository.create(
            governed_result.cleaned_version
        )

        # 4. Persist execution record
        self._cleaning_execution_repository.create(
            governed_result.execution
        )


    def save_failed_governance_execution(
        self,
        execution: Any,
    ) -> None:
        """
        Persist a FAILED CleaningExecution record for auditability.
        """
        if self._cleaning_execution_repository is None:
            return
        try:
            self._cleaning_execution_repository.create(execution)
        except Exception:
            logger.exception("Could not persist failed cleaning execution.")

    @property
    def dataset_version_repository(self) -> DatasetVersionRepository | None:
        return self._dataset_version_repository

    @property
    def cleaning_config_repository(self) -> CleaningConfigRepository | None:
        return self._cleaning_config_repository

    @property
    def cleaning_execution_repository(self) -> CleaningExecutionRepository | None:
        return self._cleaning_execution_repository

    @property
    def user_repository(self) -> UserRepository | None:
        return self._user_repository

    # ---------------------------------------------------------

    def shutdown(self):

        if self._database_manager is not None:
            self._database_manager.shutdown()