"""
Token revocation tracking for AnalystGPT Enterprise.

Revocation is keyed by the token's unique `jti` claim and remembered only
until the token would have expired anyway.

It used to store the whole bearer string, in a process-local set, forever:
anyone could POST arbitrary strings to `/api/auth/logout` and grow it without
bound (SEC-09), a revoked token became valid again after an API restart, and a
second worker never knew about it.

- `TokenRevocationService`       in-memory; for tests and single-process tools.
- `DatabaseTokenRevocationService` persisted in `revoked_tokens`; used by the API.
"""

from __future__ import annotations

import time
from threading import Lock

from src.database.connection_factory import ConnectionFactory
from src.database.schema_manager import SchemaManager


class TokenRevocationService:
    """In-memory registry of revoked token ids (`jti`), pruned at expiry."""

    def __init__(self) -> None:
        self._revoked: dict[str, int] = {}
        self._lock = Lock()

    def revoke(self, jti: str, expires_at: int) -> None:
        """Remember `jti` as revoked until `expires_at` (epoch seconds)."""
        if not jti:
            return
        now = int(time.time())
        with self._lock:
            self._prune(now)
            if expires_at > now:
                self._revoked[jti] = int(expires_at)

    def is_revoked(self, jti: str) -> bool:
        if not jti:
            return False
        now = int(time.time())
        with self._lock:
            self._prune(now)
            return jti in self._revoked

    def __len__(self) -> int:
        with self._lock:
            self._prune(int(time.time()))
            return len(self._revoked)

    def _prune(self, now: int) -> None:
        expired = [jti for jti, exp in self._revoked.items() if exp <= now]
        for jti in expired:
            del self._revoked[jti]


class DatabaseTokenRevocationService:
    """
    Revocations persisted in the `revoked_tokens` table.

    Survives restarts and is shared by every API worker. Each call opens its
    own connection, so the service is safe to use from concurrent requests.
    """

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

    def revoke(self, jti: str, expires_at: int) -> None:
        if not jti:
            return
        now = int(time.time())
        if expires_at <= now:
            return
        conn = self._connect()
        try:
            cursor = conn.get_connection().cursor()
            cursor.execute(self._sql(conn, "DELETE FROM revoked_tokens WHERE expires_at <= ?;"), (now,))
            cursor.execute(
                self._sql(
                    conn,
                    "INSERT INTO revoked_tokens (jti, expires_at, revoked_at) VALUES (?, ?, ?) "
                    "ON CONFLICT (jti) DO NOTHING;",
                ),
                (jti, int(expires_at), now),
            )
            conn.commit()
            cursor.close()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.disconnect()

    def is_revoked(self, jti: str) -> bool:
        if not jti:
            return False
        conn = self._connect()
        try:
            cursor = conn.get_connection().cursor()
            cursor.execute(
                self._sql(conn, "SELECT 1 FROM revoked_tokens WHERE jti = ? AND expires_at > ?;"),
                (jti, int(time.time())),
            )
            found = cursor.fetchone() is not None
            cursor.close()
            return found
        finally:
            conn.disconnect()
