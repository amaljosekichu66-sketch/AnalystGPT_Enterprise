from src.database.repositories.base_repository import BaseRepository


class DatasetRepository(BaseRepository):

    TABLE_NAME = "datasets"

    def create(
        self,
        pipeline_run_id: int,
        dataset_name: str,
        row_count: int,
        column_count: int,
    ) -> int:

        query = """
        INSERT INTO datasets(
            pipeline_run_id,
            dataset_name,
            row_count,
            column_count
        )
        VALUES (?, ?, ?, ?);
        """

        cursor = self.execute(
            query,
            (
                pipeline_run_id,
                dataset_name,
                row_count,
                column_count,
            ),
        )

        return cursor.lastrowid