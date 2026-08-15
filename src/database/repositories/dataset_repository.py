from src.database.repositories.base_repository import BaseRepository


class DatasetRepository(BaseRepository):

    TABLE_NAME = "datasets"

    def create(
        self,
        pipeline_run_id: int,
        dataset_name: str,
        row_count: int,
        column_count: int,
        user_id: int | None = None,
    ) -> int:

        query = """
        INSERT INTO datasets(
            pipeline_run_id,
            user_id,
            dataset_name,
            row_count,
            column_count
        )
        VALUES (?, ?, ?, ?, ?);
        """

        return self.insert_and_return_id(
            query,
            (
                pipeline_run_id,
                user_id,
                dataset_name,
                row_count,
                column_count,
            ),
        )

    def get_by_id(
        self,
        record_id: int,
        user_id: int | None = None,
    ) -> dict | None:
        """
        Retrieve dataset by ID with optional user ownership constraint.
        """
        return self.get_by_id_scoped(record_id, user_id=user_id)

    def get_all(
        self,
        user_id: int | None = None,
    ) -> list[dict]:
        """
        List datasets with optional user ownership constraint.
        """
        return self.get_all_scoped(user_id=user_id)

    def get_by_pipeline_run(
        self,
        pipeline_run_id: int,
        user_id: int | None = None,
    ) -> dict | None:
        """
        Retrieve dataset associated with a pipeline run with optional user ownership constraint.
        """
        if user_id is not None:
            query = """
            SELECT *
            FROM datasets
            WHERE pipeline_run_id = ? AND user_id = ?;
            """
            return self.fetch_one(query, (pipeline_run_id, user_id))

        query = """
        SELECT *
        FROM datasets
        WHERE pipeline_run_id = ?;
        """
        return self.fetch_one(query, (pipeline_run_id,))

    def delete(
        self,
        record_id: int,
        user_id: int | None = None,
    ) -> None:
        """
        Delete a dataset with optional user ownership constraint.
        """
        self.delete_scoped(record_id, user_id=user_id)