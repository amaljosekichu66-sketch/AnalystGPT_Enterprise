import sqlite3

from src.database.database_connection import DatabaseConnection


class SQLiteConnection(DatabaseConnection):
    """
    SQLite implementation of the DatabaseConnection contract.

    One instance = one sqlite3 connection. Instances must not be shared
    across concurrent requests; see `Application.persistence_session()`.
    """

    BUSY_TIMEOUT_SECONDS = 30.0

    def __init__(self, database_path: str):
        self._database_path = database_path
        self._connection = None

    # ---------------------------------------------------------

    def connect(self):
        """
        Establish a connection to the SQLite database.
        """

        if self._connection is None:

            # Concurrent requests each hold their own connection to the same
            # file, so writers contend for SQLite's database lock. Wait for it
            # (up to BUSY_TIMEOUT_SECONDS) instead of failing immediately with
            # "database is locked".
            self._connection = sqlite3.connect(
                self._database_path,
                check_same_thread=False,
                timeout=self.BUSY_TIMEOUT_SECONDS,
            )

            self._connection.row_factory = sqlite3.Row

    # ---------------------------------------------------------

    def disconnect(self):
        """
        Close the SQLite connection.
        """

        if self._connection is not None:

            self._connection.close()
            self._connection = None

    # ---------------------------------------------------------

    def get_connection(self):
        """
        Return the active SQLite connection, connecting lazily if necessary.
        """
        if self._connection is None:
            self.connect()

        return self._connection

    def close(self):
        """
        Alias for disconnect.
        """
        self.disconnect()

    # ---------------------------------------------------------

    def commit(self):
        """
        Commit the current transaction.
        """

        if self._connection is not None:
            self._connection.commit()

    # ---------------------------------------------------------

    def rollback(self):
        """
        Roll back the current transaction.
        """

        if self._connection is not None:
            self._connection.rollback()

    # ---------------------------------------------------------

    def database_type(self) -> str:
        """
        Return the database engine type.
        """

        return "sqlite"
