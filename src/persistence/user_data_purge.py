"""
Purge a user's data when their account is deleted (SEC-20).

Deleting a user used to remove only the `users` row. Foreign keys are
`ON DELETE SET NULL`, so every pipeline run, dataset, dataset version,
report, AI job and cleaning record stayed in the database with no owner,
and the uploaded files and generated reports stayed on disk.

Policy: deleting an account deletes the data it owns. Rows are removed in
one transaction, in foreign-key order; files are removed afterwards, and
only from the managed artifact store and report directory. The audit trail
(`audit_events`) is deliberately kept.
"""

from __future__ import annotations

from pathlib import Path

from src.core import config
from src.core.logger import logger
from src.database.connection_factory import ConnectionFactory
from src.database.schema_manager import SchemaManager
from src.storage.artifact_store import LocalArtifactStore

#: Bound variables per IN list; SQLite's default limit is 999 on older builds.
_IN_CHUNK = 500


class UserDataPurger:
    def __init__(self, artifact_store: LocalArtifactStore) -> None:
        self._artifact_store = artifact_store

    def purge(self, user_id: int, expected_username: str) -> dict[str, int]:
        """
        Delete everything owned by `user_id`; return per-table row counts.

        `expected_username` must match the stored account, so a stale or
        mismatched id can never purge another user's data.
        """
        conn = ConnectionFactory.create_connection()
        conn.connect()
        try:
            SchemaManager(conn).initialize_schema()
            cursor = conn.get_connection().cursor()
            q = self._sql(conn)

            cursor.execute(q("SELECT username FROM users WHERE id = ?;"), (user_id,))
            row = cursor.fetchone()
            stored = None if row is None else (row["username"] if hasattr(row, "keys") else row[0])
            if stored != expected_username:
                logger.warning("User data purge skipped: user id %s does not match '%s'.", user_id, expected_username)
                return {}

            cursor.execute(q("SELECT id FROM pipeline_runs WHERE user_id = ?;"), (user_id,))
            run_ids = [self._first(r) for r in cursor.fetchall()]
            cursor.execute(q("SELECT storage_path FROM dataset_versions WHERE user_id = ?;"), (user_id,))
            artifact_paths = [self._first(r) for r in cursor.fetchall()]
            cursor.execute(q("SELECT report_path FROM reports WHERE user_id = ?;"), (user_id,))
            report_paths = [self._first(r) for r in cursor.fetchall()]

            deleted: dict[str, int] = {}

            def delete(table: str, where: str, args: tuple) -> None:
                cursor.execute(q(f"DELETE FROM {table} WHERE {where};"), args)
                deleted[table] = deleted.get(table, 0) + max(cursor.rowcount, 0)

            def delete_owned_or_run(table: str) -> None:
                delete(table, "user_id = ?", (user_id,))
                delete_runs(table)

            def delete_runs(table: str) -> None:
                # Chunked (I14): one IN list per run id overflowed SQLite's
                # bound-variable limit for accounts with many runs.
                for start in range(0, len(run_ids), _IN_CHUNK):
                    chunk = tuple(run_ids[start : start + _IN_CHUNK])
                    delete(table, f"pipeline_run_id IN ({','.join('?' * len(chunk))})", chunk)

            # Children before parents.
            delete_owned_or_run("ai_reports")
            delete_owned_or_run("ai_jobs")
            delete_owned_or_run("cleaning_executions")
            delete("cleaning_configs", "user_id = ?", (user_id,))
            delete("dataset_versions", "user_id = ? AND parent_version_id IS NOT NULL", (user_id,))
            delete("dataset_versions", "user_id = ?", (user_id,))
            delete_runs("quality_reports")
            delete_runs("analytics_reports")
            delete_owned_or_run("reports")
            delete_owned_or_run("datasets")
            delete("pipeline_runs", "user_id = ?", (user_id,))

            conn.commit()
            cursor.close()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.disconnect()

        deleted["files"] = self._remove_files(artifact_paths, report_paths)
        logger.info("Purged data for user id %s: %s", user_id, deleted)
        return deleted

    # ------------------------------------------------------------------

    def _remove_files(self, artifact_paths: list[str], report_paths: list[str]) -> int:
        roots = [
            self._artifact_store.raw_dir.resolve(),
            self._artifact_store.cleaned_dir.resolve(),
            Path(config.REPORT_OUTPUT_DIRECTORY).resolve(),
        ]
        removed = 0
        for raw in [*artifact_paths, *report_paths]:
            if not raw:
                continue
            path = Path(raw).resolve()
            if not any(path.is_relative_to(root) for root in roots) or not path.is_file():
                continue
            path.unlink(missing_ok=True)
            removed += 1
            try:
                path.parent.rmdir()  # per-version directory, if now empty
            except OSError:
                pass
        return removed

    @staticmethod
    def _sql(conn):
        is_pg = conn.database_type() == "postgresql"
        return lambda query: query.replace("?", "%s") if is_pg else query

    @staticmethod
    def _first(row):
        if hasattr(row, "keys"):
            return row[list(row.keys())[0]]
        return row[0]
