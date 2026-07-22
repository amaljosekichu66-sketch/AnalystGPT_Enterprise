from src.database.database_connection import DatabaseConnection


class DatabaseManager:
    """
    Coordinates the application's database infrastructure.

    DatabaseManager is responsible for managing the lifecycle of a database
    connection but remains independent of the underlying database engine.
    """

    def __init__(self, database_connection: DatabaseConnection):
        """
        Initialize the DatabaseManager with any implementation of
        DatabaseConnection.

        Args:
            database_connection: A concrete implementation of
                                 DatabaseConnection.
        """
        self._database_connection = database_connection

    def initialize(self):
        """
        Establish the database connection.
        """
        self._database_connection.connect()

    def get_connection(self):
        """
        Return the active database connection.
        """
        return self._database_connection.get_connection()

    def commit(self):
        """
        Commit the current transaction.
        """
        self._database_connection.commit()

    def rollback(self):
        """
        Roll back the current transaction.
        """
        self._database_connection.rollback()

    def shutdown(self):
        """
        Close the database connection.
        """
        self._database_connection.disconnect()