import psycopg
from psycopg.rows import dict_row

from src.database.database_connection import DatabaseConnection


class PostgreSQLConnection(DatabaseConnection):
    """
    PostgreSQL implementation of the DatabaseConnection contract.
    Uses dict_row row factory for dictionary-like row access.
    """

    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
    ):
        self._host = host
        self._port = port
        self._database = database
        self._user = user
        self._password = password

        self._connection = None

    # ---------------------------------------------------------

    def connect(self):
        """
        Establish a connection to PostgreSQL with dict_row row factory.
        """
        if self._connection is None:
            self._connection = psycopg.connect(
                host=self._host,
                port=self._port,
                dbname=self._database,
                user=self._user,
                password=self._password,
                row_factory=dict_row,   # ← ensures rows are dict-like
            )

    # ---------------------------------------------------------

    def disconnect(self):
        """
        Close the PostgreSQL connection.
        """
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    # ---------------------------------------------------------

    def get_connection(self):
        """
        Return the active PostgreSQL connection.
        """
        return self._connection

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
        return "postgresql"