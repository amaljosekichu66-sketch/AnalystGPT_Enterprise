from src.database.sqlite_connection import SQLiteConnection


class DatabaseManager:
    """
    Coordinates the application's database infrastructure.
    """

    def __init__(self, database_path: str):
        self._sqlite_connection = SQLiteConnection(database_path)

    def initialize(self):
        """
        Initialize the database connection.
        """
        self._sqlite_connection.connect()

    def get_connection(self):
        """
        Return the active SQLite connection.
        """
        return self._sqlite_connection.get_connection()

    def shutdown(self):
        """
        Close the database connection.
        """
        self._sqlite_connection.close()