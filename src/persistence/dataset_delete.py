"""
Delete one uploaded dataset and everything derived from it (I7).

Raw uploads and cleaned files were kept until the owner's account was
deleted: there was no way to remove a single dataset, and no retention. This
removes a source DatasetVersion, its derived (cleaned) versions and the
cleaning executions that link them, in one transaction, then deletes their
files from the managed artifact store only. Pipeline runs, reports and AI
insights already produced from the dataset are results, not the data, and
stay until the account is purged.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from src.core.logger import logger
from src.database.connection_factory import ConnectionFactory
from src.database.schema_manager import SchemaManager
from src.storage.artifact_store import LocalArtifactStore


class DatasetDeleter:
    def __init__(self, artifact_store: LocalArtifactStore) -> None:
        self._artifact_store = artifact_store

    def delete(self, version_id: str) -> int:
        """Delete the source version `version_id` and its derivatives; return rows removed."""
        conn = ConnectionFactory.create_connection()
        conn.connect()
        paths: list[str] = []
        try:
            SchemaManager(conn).initialize_schema()
            cursor = conn.get_connection().cursor()
            q = self._sql(conn)

            cursor.execute(q("SELECT storage_path FROM dataset_versions WHERE version_id = ?;"), (version_id,))
            row = cursor.fetchone()
            if row is None:
                return 0
            paths.append(self._first(row))

            cursor.execute(
                q("SELECT version_id, storage_path FROM dataset_versions WHERE parent_version_id = ?;"), (version_id,)
            )
            children = [(self._first(r), r[1]) for r in cursor.fetchall()]
            paths.extend(path for _, path in children)
            child_ids = [child_id for child_id, _ in children]

            removed = 0
            cursor.execute(q("DELETE FROM cleaning_executions WHERE source_version_id = ?;"), (version_id,))
            removed += max(cursor.rowcount, 0)
            for child_id in child_ids:
                cursor.execute(q("DELETE FROM cleaning_executions WHERE cleaned_version_id = ?;"), (child_id,))
                removed += max(cursor.rowcount, 0)
            cursor.execute(q("DELETE FROM dataset_versions WHERE parent_version_id = ?;"), (version_id,))
            removed += max(cursor.rowcount, 0)
            cursor.execute(q("DELETE FROM dataset_versions WHERE version_id = ?;"), (version_id,))
            removed += max(cursor.rowcount, 0)

            conn.commit()
            cursor.close()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.disconnect()

        self._remove_files(paths)
        logger.info("Deleted dataset version %s (%d rows, %d files).", version_id, removed, len(paths))
        return removed

    def expired_source_versions(self, retention_days: int) -> list[str]:
        """Source versions created more than `retention_days` ago."""
        cutoff = (datetime.now(UTC) - timedelta(days=retention_days)).isoformat()
        conn = ConnectionFactory.create_connection()
        conn.connect()
        try:
            SchemaManager(conn).initialize_schema()
            cursor = conn.get_connection().cursor()
            cursor.execute(
                self._sql(conn)("SELECT version_id FROM dataset_versions WHERE is_source = 1 AND created_at < ?;"),
                (cutoff,),
            )
            return [self._first(r) for r in cursor.fetchall()]
        finally:
            conn.disconnect()

    def _remove_files(self, paths: list[str]) -> None:
        roots = [self._artifact_store.raw_dir.resolve(), self._artifact_store.cleaned_dir.resolve()]
        for raw in paths:
            if not raw:
                continue
            path = Path(raw).resolve()
            if not any(path.is_relative_to(root) for root in roots) or not path.is_file():
                continue
            path.unlink(missing_ok=True)
            try:
                path.parent.rmdir()  # per-version directory, if now empty
            except OSError:
                pass

    @staticmethod
    def _sql(conn):
        is_pg = conn.database_type() == "postgresql"
        return lambda query: query.replace("?", "%s") if is_pg else query

    @staticmethod
    def _first(row):
        if hasattr(row, "keys"):
            return row[list(row.keys())[0]]
        return row[0]
