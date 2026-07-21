from datetime import datetime

from src.database.repositories.base_repository import BaseRepository


class PipelineRunRepository(BaseRepository):

    TABLE_NAME = "pipeline_runs"

    def create(self, status: str) -> int:

        query = """
        INSERT INTO pipeline_runs (
            execution_time,
            status
        )
        VALUES (?, ?);
        """

        cursor = self.execute(
            query,
            (
                datetime.now().isoformat(timespec="seconds"),
                status,
            ),
        )

        return cursor.lastrowid