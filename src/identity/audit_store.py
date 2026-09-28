"""
Durable audit trail (SEC-25).

Audit events used to live only in a 1,000-entry in-memory buffer and the
log stream: a restart erased them. `DatabaseAuditSink` writes every event to
the `audit_events` table (no foreign keys, so records outlive the users and
resources they describe) and reads them back for the admin audit endpoint.
Each call opens its own connection.
"""

from __future__ import annotations

import json
from threading import Lock
from typing import Any

from src.database.connection_factory import ConnectionFactory
from src.database.schema_manager import SchemaManager
from src.identity.models import AuditEvent


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
        conn = self._connect()
        try:
            cursor = conn.get_connection().cursor()
            cursor.execute(
                self._sql(
                    conn,
                    "INSERT INTO audit_events (event_id, event_type, occurred_at, actor_id, actor_username, "
                    "target_id, target_resource, action, outcome, details_json) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT (event_id) DO NOTHING;",
                ),
                (
                    event.event_id,
                    event.event_type.value,
                    event.timestamp.isoformat(),
                    event.actor_id,
                    event.actor_username,
                    event.target_id,
                    event.target_resource,
                    event.action,
                    event.outcome,
                    json.dumps(event.details, default=str),
                ),
            )
            conn.commit()
            cursor.close()
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
