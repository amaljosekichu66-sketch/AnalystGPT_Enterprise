"""
Factory responsible for creating database connections.
"""

from src.core import config

from src.database.sqlite_connection import SQLiteConnection
from src.database.postgresql_connection import PostgreSQLConnection


class ConnectionFactory:
    """
    Creates the appropriate DatabaseConnection implementation
    based on the application configuration.
    """

    @staticmethod
    def create_connection():
        """
        Create and return the configured database connection.
        """

        if config.DATABASE_ENGINE.lower() == "sqlite":

            return SQLiteConnection(
                config.SQLITE_DATABASE_PATH
            )

        if config.DATABASE_ENGINE.lower() == "postgresql":

            return PostgreSQLConnection(
                host=config.POSTGRES_HOST,
                port=config.POSTGRES_PORT,
                database=config.POSTGRES_DATABASE,
                user=config.POSTGRES_USER,
                password=config.POSTGRES_PASSWORD,
            )

        raise ValueError(
            f"Unsupported database engine: {config.DATABASE_ENGINE}"
        )