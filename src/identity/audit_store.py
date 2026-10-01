"""
Durable audit trail (SEC-25), tamper-evident and with retention (P2-14).

Audit events used to live only in a 1,000-entry in-memory buffer and the
log stream: a restart erased them. `DatabaseAuditSink` writes every event to
the `audit_events` table (no foreign keys, so records outlive the users and
resources they describe) and reads them back for the admin audit endpoint.
Each call opens its own connection.

Tamper evidence: every row stores `row_hash = sha256(prev_hash + fields)`
over the fields that never change - id, type, time, actor and target ids,
action, outcome - and the previous row's hash. Editing or deleting a row in
the middle breaks the chain, which `verify_chain()` reports. Usernames and
details are not hashed, so pseudonymising a deleted user's rows (GDPR-style
erasure) keeps the chain valid. Writes are serialised within the process;
with several API workers the chain could fork, which verification reports.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from threading import Lock
from typing import Any

from src.database.connection_factory import ConnectionFactory
from src.database.schema_manager import SchemaManager
from src.identity.models import AuditEvent

_HASHED_FIELDS = (
    "event_id",
    "event_type",
    "occurred_at",
    "actor_id",
    "target_id",
    "target_resource",
    "action",
    "outcome",
)

#: Process-wide: every sink instance appends to the same chain.
_CHAIN_LOCK = Lock()


def chain_hash(prev_hash: str | None, row: dict[str, Any]) -> str:
    material = "|".join([prev_hash or ""] + ["" if row.get(f) is None else str(row.get(f)) for f in _HASHED_FIELDS])
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


class DatabaseAuditSink:
    def __init__(self) -> None:
        self._schema_ready = False
        self._schema_lock = Lock()

    def _connect(self):
        conn = ConnectionFactory.create_connection()
        conn.connect()
        if not self._schema_ready:
            with self._schema_lock:
                if not self._schema_ready:
                    SchemaManager(conn).initialize_schema()
                    self._schema_ready = True
        return conn

    @staticmethod
    def _sql(conn, query: str) -> str:
        return query.replace("?", "%s") if conn.database_type() == "postgresql" else query

    def write(self, event: AuditEvent) -> None:
        row = {
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "occurred_at": event.timestamp.isoformat(),
            "actor_id": event.actor_id,
            "target_id": event.target_id,
            "target_resource": event.target_resource,
            "action": event.action,
            "outcome": event.outcome,
        }
        with _CHAIN_LOCK:
            conn = self._connect()
            try:
                cursor = conn.get_connection().cursor()
                cursor.execute("SELECT row_hash FROM audit_events ORDER BY id DESC LIMIT 1;")
                last = cursor.fetchone()
                prev_hash = None if last is None else (last["row_hash"] if hasattr(last, "keys") else last[0])
                cursor.execute(
                    self._sql(
                        conn,
                        "INSERT INTO audit_events (event_id, event_type, occurred_at, actor_id, actor_username, "
                        "target_id, target_resource, action, outcome, details_json, prev_hash, row_hash) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT (event_id) DO NOTHING;",
                    ),
                    (
                        event.event_id,
                        event.event_type.value,
                        row["occurred_at"],
                        event.actor_id,
                        event.actor_username,
                        event.target_id,
                        event.target_resource,
                        event.action,
                        event.outcome,
                        json.dumps(event.details, default=str),
                        prev_hash,
                        chain_hash(prev_hash, row),
                    ),
                )
                conn.commit()
                cursor.close()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.disconnect()

    def verify_chain(self) -> dict[str, Any]:
        """
        Recompute the hash chain over the retained rows, oldest first.

        Returns `{"checked": n, "valid": bool, "first_broken_id": id | None}`.
        Rows written before the chain existed (no row_hash) are skipped. The
        oldest retained row's predecessor may have been removed by retention,
        so only links between retained rows are checked.
        """
        conn = self._connect()
        try:
            cursor = conn.get_connection().cursor()
            cursor.execute(
                f"SELECT id, prev_hash, row_hash, {', '.join(_HASHED_FIELDS)} FROM audit_events "
                "WHERE row_hash IS NOT NULL ORDER BY id ASC;"
            )
            rows = [dict(r) for r in cursor.fetchall()]
            cursor.close()
        finally:
            conn.disconnect()
        previous: str | None = None
        for index, row in enumerate(rows):
            if index > 0 and row["prev_hash"] != previous:
                return {"checked": index, "valid": False, "first_broken_id": row["id"]}
            if chain_hash(row["prev_hash"], row) != row["row_hash"]:
                return {"checked": index, "valid": False, "first_broken_id": row["id"]}
            previous = row["row_hash"]
        return {"checked": len(rows), "valid": True, "first_broken_id": None}

    def prune(self, retention_days: int) -> int:
        """Delete audit rows older than `retention_days` (0 keeps everything)."""
        if retention_days <= 0:
            return 0
        cutoff = (datetime.now(UTC) - timedelta(days=retention_days)).isoformat()
        conn = self._connect()
        try:
            cursor = conn.get_connection().cursor()
            cursor.execute(self._sql(conn, "DELETE FROM audit_events WHERE occurred_at < ?;"), (cutoff,))
            removed = max(cursor.rowcount, 0)
            conn.commit()
            cursor.close()
            return removed
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.disconnect()

    def recent(
        self,
        limit: int = 100,
        event_type: str | None = None,
        actor_id: int | None = None,
    ) -> list[dict[str, Any]]:
        conditions, params = [], []
        if event_type:
            conditions.append("event_type = ?")
            params.append(event_type)
        if actor_id is not None:
            conditions.append("actor_id = ?")
            params.append(actor_id)
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        conn = self._connect()
        try:
            cursor = conn.get_connection().cursor()
            cursor.execute(
                self._sql(conn, f"SELECT * FROM audit_events {where} ORDER BY id DESC LIMIT ?;"),
                (*params, int(limit)),
            )
            rows = [dict(r) for r in cursor.fetchall()]
            cursor.close()
        finally:
            conn.disconnect()
        for row in rows:
            row["details"] = json.loads(row.pop("details_json") or "{}")
        return rows
