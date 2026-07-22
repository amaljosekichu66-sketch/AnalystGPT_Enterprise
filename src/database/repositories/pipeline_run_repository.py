from datetime import datetime

from src.database.repositories.base_repository import BaseRepository


class PipelineRunRepository(BaseRepository):

    TABLE_NAME = "pipeline_runs"

    def create(
        self,
        status: str,
    ) -> int:

        query = """
        INSERT INTO pipeline_runs (
            execution_time,
            status
        )
        VALUES (?, ?);
        """

        return self.insert_and_return_id(
            query,
            (
                datetime.now().isoformat(
                    timespec="seconds"
                ),
                status,
            ),
        )