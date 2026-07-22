from src.database.repositories.base_repository import BaseRepository


class QualityRepository(BaseRepository):

    TABLE_NAME = "quality_reports"

    def create(
        self,
        pipeline_run_id: int,
        completeness: float,
        validity: float,
        consistency: float,
        uniqueness_score: float,
    ) -> int:

        query = """
        INSERT INTO quality_reports(
            pipeline_run_id,
            completeness,
            validity,
            consistency,
            uniqueness_score
        )
        VALUES (?, ?, ?, ?, ?);
        """

        return self.insert_and_return_id(
            query,
            (
                pipeline_run_id,
                completeness,
                validity,
                consistency,
                uniqueness_score,
            ),
        )