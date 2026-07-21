import sqlite3


class SQLiteConnection:
    """
    Manages the lifecycle of the application's SQLite database connection.
    """

    def __init__(self, database_path: str):
        self._database_path = database_path
        self._connection = None

    def connect(self):
        """
        Open the SQLite database connection.
        """

        if self._connection is None:
            self._connection = sqlite3.connect(self._database_path)

            # Return rows as dictionary-like objects
            self._connection.row_factory = sqlite3.Row

        return self._connection

    def get_connection(self):
        """
        Return the active SQLite connection.
        """
        return self._connection

    def close(self):
        """
        Close the active SQLite database connection.
        """
        if self._connection is not None:
            self._connection.close()
            self._connection = None