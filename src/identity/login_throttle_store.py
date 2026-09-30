"""
Durable login-throttle state (I3).

Lockout counters lived in process memory: a restart cleared every lockout and
each additional API worker multiplied an attacker's attempt budget.
`DatabaseThrottleStore` keeps them in the `login_failures` table. Each call
opens its own connection, like `DatabaseAuditSink`.
"""

from __future__ import annotations

from threading import Lock

from src.database.connection_factory import ConnectionFactory
from src.database.schema_manager import SchemaManager
from src.identity.login_throttle import ACCOUNT, PAIR, ThrottleState, pair_key


class DatabaseThrottleStore:
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

    def _execute(self, query: str, params: tuple = (), fetch: bool = False):
        conn = self._connect()
        try:
            cursor = conn.get_connection().cursor()
            cursor.execute(self._sql(conn, query), params)
            row = cursor.fetchone() if fetch else None
            conn.commit()
            cursor.close()
            return row
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.disconnect()

    def get(self, scope: str, key: str) -> ThrottleState | None:
        row = self._execute(
            "SELECT failures, locked_until, last_failure FROM login_failures WHERE scope = ? AND key = ?;",
            (scope, key),
            fetch=True,
        )
        if row is None:
            return None
        values = tuple(row.values()) if isinstance(row, dict) else tuple(row)
        return ThrottleState(int(values[0]), float(values[1]), float(values[2]))

    def put(self, scope: str, key: str, state: ThrottleState) -> None:
        self._execute(
            "INSERT INTO login_failures (scope, key, failures, locked_until, last_failure) VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT (scope, key) DO UPDATE SET failures = excluded.failures, "
            "locked_until = excluded.locked_until, last_failure = excluded.last_failure;",
            (scope, key, state.failures, state.locked_until, state.last_failure),
        )

    def delete(self, scope: str, key: str) -> None:
        self._execute("DELETE FROM login_failures WHERE scope = ? AND key = ?;", (scope, key))

    def delete_account(self, account: str) -> None:
        prefix = pair_key(account, "")
        self._execute(
            "DELETE FROM login_failures WHERE (scope = ? AND key = ?) OR (scope = ? AND SUBSTR(key, 1, ?) = ?);",
            (ACCOUNT, account, PAIR, len(prefix), prefix),
        )

    def prune(self, now: float, idle_seconds: float) -> None:
        self._execute(
            "DELETE FROM login_failures WHERE locked_until <= ? AND last_failure < ?;",
            (now, now - idle_seconds),
        )

    def clear(self) -> None:
        self._execute("DELETE FROM login_failures;")
