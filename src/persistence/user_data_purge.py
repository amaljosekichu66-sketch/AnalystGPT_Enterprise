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

import json
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

    def purge(self, user_id: int, expected_username: str, delete_account: bool = False) -> dict[str, int]:
        """
        Delete everything owned by `user_id`; return per-table row counts.

        `expected_username` must match the stored account, so a stale or
        mismatched id can never purge another user's data.

        With `delete_account`, the `users` row is deleted in the SAME
        transaction (P2-14): the purge used to commit on its own connection
        before the user row was deleted on another, so a failure in between
        left an account whose data was gone. The user's audit rows are
        pseudonymised in that transaction too.
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
            delete("cleaning_policy_proposals", "user_id = ?", (user_id,))

            if delete_account:
                deleted["audit_pseudonymised"] = self._pseudonymise_audit(cursor, q, user_id, expected_username)
                account = f"user:{user_id}"
                delete("login_failures", "scope = ? AND key = ?", ("account", account))
                delete(
                    "login_failures", "scope = ? AND SUBSTR(key, 1, ?) = ?", ("pair", len(account) + 1, account + "|")
                )
                delete("users", "id = ?", (user_id,))

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

    @staticmethod
    def _pseudonymise_audit(cursor, q, user_id: int, username: str) -> int:
        """
        Replace the deleted user's name and email in the audit trail (P2-14).

        Rows keep their ids, types, times and outcomes - and therefore their
        hash chain - but no longer name the person.
        """
        pseudonym = f"deleted-user-{user_id}"
        cursor.execute(
            q("SELECT id, details_json FROM audit_events WHERE actor_id = ? OR target_id = ?;"), (user_id, user_id)
        )
        rows = cursor.fetchall()
        cursor.execute(q("UPDATE audit_events SET actor_username = ? WHERE actor_id = ?;"), (pseudonym, user_id))
        cursor.execute(q("UPDATE audit_events SET actor_username = ? WHERE actor_username = ?;"), (pseudonym, username))
        for row in rows:
            row_id = row["id"] if hasattr(row, "keys") else row[0]
            raw = row["details_json"] if hasattr(row, "keys") else row[1]
            try:
                details = json.loads(raw or "{}")
            except ValueError:
                details = {}
            if not isinstance(details, dict):
                continue
            changed = False
            for key in ("username", "email", "deleted_username", "actor_username"):
                if key in details:
                    details[key] = pseudonym
                    changed = True
            if changed:
                cursor.execute(
                    q("UPDATE audit_events SET details_json = ? WHERE id = ?;"), (json.dumps(details), row_id)
                )
        return len(rows)

    def purge_ownerless(self, dry_run: bool = True) -> dict[str, int]:
        """
        Rows with no owner at all (P2-14 policy).

        They predate per-user ownership (Sprint 13 migration) and can never be
        reached by an account purge. Policy: an administrator removes them
        explicitly with `scripts/purge_ownerless_data.py`; `dry_run` counts.
        """
        tables = ("ai_reports", "ai_jobs", "cleaning_executions", "reports", "datasets", "pipeline_runs")
        conn = ConnectionFactory.create_connection()
        conn.connect()
        try:
            SchemaManager(conn).initialize_schema()
            cursor = conn.get_connection().cursor()
            counts: dict[str, int] = {}
            versions_sql = "SELECT COUNT(*) FROM dataset_versions WHERE user_id IS NULL;"
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE user_id IS NULL;")  # nosec B608 - constant names
                counts[table] = int(self._first(cursor.fetchone()) or 0)
            cursor.execute(versions_sql)
            counts["dataset_versions"] = int(self._first(cursor.fetchone()) or 0)
            if not dry_run:
                for table in tables:
                    cursor.execute(f"DELETE FROM {table} WHERE user_id IS NULL;")  # nosec B608 - constant names
                cursor.execute("DELETE FROM dataset_versions WHERE user_id IS NULL AND parent_version_id IS NOT NULL;")
                cursor.execute("DELETE FROM dataset_versions WHERE user_id IS NULL;")
                conn.commit()
            cursor.close()
            return counts
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.disconnect()

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
