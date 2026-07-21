from src.database.database_manager import DatabaseManager
from src.database.schema_manager import SchemaManager

from src.database.repositories.pipeline_run_repository import (
    PipelineRunRepository,
)
from src.database.repositories.dataset_repository import (
    DatasetRepository,
)
from src.database.repositories.quality_repository import (
    QualityRepository,
)
from src.database.repositories.analytics_repository import (
    AnalyticsRepository,
)
from src.database.repositories.report_repository import (
    ReportRepository,
)

from src.persistence.persistence_result import PersistenceResult


class PersistenceManager:
    """
    Coordinates all persistence operations for AnalystGPT Enterprise.
    """

    def __init__(self, database_path: str = "analystgpt.db"):

        self._database_path = database_path

        self._database_manager = None

        self._pipeline_repository = None
        self._dataset_repository = None
        self._quality_repository = None
        self._analytics_repository = None
        self._report_repository = None

        self._pipeline_run_id = None
        self._dataset_id = None
        self._quality_report_id = None
        self._analytics_report_id = None
        self._report_id = None

    # ---------------------------------------------------------

    def initialize(self):
        """
        Initialize database infrastructure.
        """

        self._database_manager = DatabaseManager(
            self._database_path
        )

        self._database_manager.initialize()

        connection = self._database_manager.get_connection()

        schema = SchemaManager(connection)

        schema.initialize_schema()

        self._pipeline_repository = PipelineRunRepository(
            connection
        )

        self._dataset_repository = DatasetRepository(
            connection
        )

        self._quality_repository = QualityRepository(
            connection
        )

        self._analytics_repository = AnalyticsRepository(
            connection
        )

        self._report_repository = ReportRepository(
            connection
        )

    # ---------------------------------------------------------

    def start_pipeline(self):

        self._pipeline_run_id = (
            self._pipeline_repository.create(
                "RUNNING"
            )
        )

    # ---------------------------------------------------------

    def save_dataset(
        self,
        dataset_name,
        row_count,
        column_count,
    ):

        self._dataset_id = (
            self._dataset_repository.create(
                self._pipeline_run_id,
                dataset_name,
                row_count,
                column_count,
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
                quality["completeness"]["complete_percentage"],
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
                descriptive["numeric_column_count"],
                descriptive["categorical_column_count"],
                str(correlation),
            )
        )

    # ---------------------------------------------------------

    def save_report(
        self,
        reporting_report,
    ):
        """
        Persist reporting metadata.
        """

        self._report_id = (
            self._report_repository.create(
                self._pipeline_run_id,
                reporting_report.export_path,
            )
        )

    # ---------------------------------------------------------

    def finish_pipeline(self):

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

    def shutdown(self):

        if self._database_manager is not None:
            self._database_manager.shutdown()