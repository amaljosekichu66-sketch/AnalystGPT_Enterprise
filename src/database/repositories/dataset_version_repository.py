"""
Dataset Version Repository.

Sprint 14 Phase 3 — Data Cleaning Governance & Lineage.

Handles database persistence for immutable DatasetVersion records.
"""

from __future__ import annotations

from src.database.database_connection import DatabaseConnection
from src.database.repositories.base_repository import BaseRepository
from src.governance.models import DatasetVersion


class DatasetVersionRepository(BaseRepository):
    TABLE_NAME = "dataset_versions"

    def __init__(self, connection: DatabaseConnection) -> None:
        super().__init__(connection)

    def create(self, version: DatasetVersion) -> int:
        query = """
        INSERT INTO dataset_versions (
            version_id,
            user_id,
            source_filename,
            content_type,
            byte_size,
            checksum_sha256,
            row_count,
            column_count,
            is_source,
            parent_version_id,
            storage_path,
            schema_json,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        is_source_int = 1 if version.is_source else 0
        return self.insert_and_return_id(
            query,
            (
                version.version_id,
                version.user_id,
                version.source_filename,
                version.content_type,
                version.byte_size,
                version.checksum_sha256,
                version.row_count,
                version.column_count,
                is_source_int,
                version.parent_version_id,
                version.storage_path,
                version.schema_json,
                version.created_at,
            ),
        )

    def get_by_version_id(self, version_id: str, user_id: int | None = None) -> dict | None:
        if user_id is not None:
            query = "SELECT * FROM dataset_versions WHERE version_id = ? AND user_id = ?;"
            return self.fetch_one(query, (version_id, user_id))
        query = "SELECT * FROM dataset_versions WHERE version_id = ?;"
        return self.fetch_one(query, (version_id,))

    def get_all(self, user_id: int | None = None, is_source: bool | None = None) -> list[dict]:
        conditions = []
        params = []
        if user_id is not None:
            conditions.append("user_id = ?")
            params.append(user_id)
        if is_source is not None:
            conditions.append("is_source = ?")
            params.append(1 if is_source else 0)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT * FROM dataset_versions {where_clause} ORDER BY id DESC;"
        return self.fetch_all(query, tuple(params))

    def get_children(self, parent_version_id: str, user_id: int | None = None) -> list[dict]:
        if user_id is not None:
            query = "SELECT * FROM dataset_versions WHERE parent_version_id = ? AND user_id = ? ORDER BY id ASC;"
            return self.fetch_all(query, (parent_version_id, user_id))
        query = "SELECT * FROM dataset_versions WHERE parent_version_id = ? ORDER BY id ASC;"
        return self.fetch_all(query, (parent_version_id,))
