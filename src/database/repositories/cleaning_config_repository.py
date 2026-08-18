"""
Cleaning Config Repository.

Sprint 14 Phase 3 — Data Cleaning Governance & Lineage.
"""

from __future__ import annotations

from src.database.database_connection import DatabaseConnection
from src.database.repositories.base_repository import BaseRepository
from src.governance.models import CleaningConfig


class CleaningConfigRepository(BaseRepository):
    TABLE_NAME = "cleaning_configs"

    def __init__(self, connection: DatabaseConnection) -> None:
        super().__init__(connection)

    def create(self, config: CleaningConfig) -> int:
        query = """
        INSERT INTO cleaning_configs (
            config_id,
            user_id,
            missing_value_policy,
            null_threshold,
            fill_value,
            affected_columns,
            custom_strategy_name,
            custom_params_json,
            config_version,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        return self.insert_and_return_id(
            query,
            (
                config.config_id,
                config.user_id,
                config.missing_value_policy.value,
                config.null_threshold,
                config.fill_value,
                config.affected_columns_json(),
                config.custom_strategy_name,
                config.custom_params_json(),
                config.config_version,
                config.created_at,
            ),
        )

    def get_by_config_id(self, config_id: str, user_id: int | None = None) -> dict | None:
        if user_id is not None:
            query = "SELECT * FROM cleaning_configs WHERE config_id = ? AND user_id = ?;"
            return self.fetch_one(query, (config_id, user_id))
        query = "SELECT * FROM cleaning_configs WHERE config_id = ?;"
        return self.fetch_one(query, (config_id,))

    def get_all(self, user_id: int | None = None) -> list[dict]:
        return self.get_all_scoped(user_id=user_id)
