from src.database.repositories.base_repository import BaseRepository


class AnalyticsRepository(BaseRepository):

    TABLE_NAME = "analytics_reports"

    def create(
        self,
        pipeline_run_id: int,
        total_numeric_columns: int,
        total_categorical_columns: int,
        correlation_summary: str,
    ) -> int:

        query = """
        INSERT INTO analytics_reports(
            pipeline_run_id,
            total_numeric_columns,
            total_categorical_columns,
            correlation_summary
        )
        VALUES (?, ?, ?, ?);
        """

        cursor = self.execute(
            query,
            (
                pipeline_run_id,
                total_numeric_columns,
                total_categorical_columns,
                correlation_summary,
            ),
        )

        return cursor.lastrowid