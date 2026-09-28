from datetime import datetime

from src.database.repositories.base_repository import BaseRepository


class PipelineRunRepository(BaseRepository):

    TABLE_NAME = "pipeline_runs"

    def create(
        self,
        status: str,
        user_id: int | None = None,
    ) -> int:

        query = """
        INSERT INTO pipeline_runs (
            user_id,
            execution_time,
            status
        )
        VALUES (?, ?, ?);
        """

        return self.insert_and_return_id(
            query,
            (
                user_id,
                datetime.now().isoformat(timespec="seconds"),
                status,
            ),
        )

    def get_by_id(
        self,
        record_id: int,
        user_id: int | None = None,
    ) -> dict | None:
        """
        Retrieve pipeline run by ID with optional user ownership constraint.
        """
        return self.get_by_id_scoped(record_id, user_id=user_id)

    def get_all(
        self,
        user_id: int | None = None,
    ) -> list[dict]:
        """
        List pipeline runs with optional user ownership constraint.
        """
        return self.get_all_scoped(user_id=user_id)

    def delete(
        self,
        record_id: int,
        user_id: int | None = None,
    ) -> None:
        """
        Delete a pipeline run with optional user ownership constraint.
        """
        self.delete_scoped(record_id, user_id=user_id)
