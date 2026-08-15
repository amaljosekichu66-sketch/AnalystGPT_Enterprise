from datetime import datetime

from src.database.repositories.base_repository import BaseRepository


class ReportRepository(BaseRepository):

    TABLE_NAME = "reports"

    def create(
        self,
        pipeline_run_id: int,
        report_path: str,
        user_id: int | None = None,
    ) -> int:

        query = """
        INSERT INTO reports(
            pipeline_run_id,
            user_id,
            report_path,
            generated_time
        )
        VALUES (?, ?, ?, ?);
        """

        return self.insert_and_return_id(
            query,
            (
                pipeline_run_id,
                user_id,
                report_path,
                datetime.now().isoformat(
                    timespec="seconds"
                ),
            ),
        )

    def get_by_id(
        self,
        record_id: int,
        user_id: int | None = None,
    ) -> dict | None:
        """
        Retrieve report by ID with optional user ownership constraint.
        """
        return self.get_by_id_scoped(record_id, user_id=user_id)

    def get_all(
        self,
        user_id: int | None = None,
    ) -> list[dict]:
        """
        List reports with optional user ownership constraint.
        """
        return self.get_all_scoped(user_id=user_id)

    def get_by_pipeline_run(
        self,
        pipeline_run_id: int,
        user_id: int | None = None,
    ) -> dict | None:
        """
        Retrieve report associated with a pipeline run with optional user ownership constraint.
        """
        if user_id is not None:
            query = """
            SELECT *
            FROM reports
            WHERE pipeline_run_id = ? AND user_id = ?;
            """
            return self.fetch_one(query, (pipeline_run_id, user_id))

        query = """
        SELECT *
        FROM reports
        WHERE pipeline_run_id = ?;
        """
        return self.fetch_one(query, (pipeline_run_id,))

    def get_latest_report(
        self,
        user_id: int | None = None,
    ) -> dict | None:
        """
        Retrieve the latest generated report with optional user ownership constraint.
        """
        if user_id is not None:
            query = """
            SELECT *
            FROM reports
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 1;
            """
            return self.fetch_one(query, (user_id,))

        query = """
        SELECT *
        FROM reports
        ORDER BY id DESC
        LIMIT 1;
        """
        return self.fetch_one(query)

    def delete(
        self,
        record_id: int,
        user_id: int | None = None,
    ) -> None:
        """
        Delete a report with optional user ownership constraint.
        """
        self.delete_scoped(record_id, user_id=user_id)