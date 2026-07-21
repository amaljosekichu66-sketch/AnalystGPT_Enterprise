from datetime import datetime

from src.database.repositories.base_repository import BaseRepository


class ReportRepository(BaseRepository):

    TABLE_NAME = "reports"

    def create(
        self,
        pipeline_run_id: int,
        report_path: str,
    ) -> int:

        query = """
        INSERT INTO reports(
            pipeline_run_id,
            report_path,
            generated_time
        )
        VALUES (?, ?, ?);
        """

        cursor = self.execute(
            query,
            (
                pipeline_run_id,
                report_path,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )

        return cursor.lastrowid