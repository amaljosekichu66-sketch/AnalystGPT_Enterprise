from abc import ABC, abstractmethod


class DatabaseConnection(ABC):
    """
    Abstract contract for all database connection implementations.

    Every supported database engine (SQLite, PostgreSQL, etc.)
    must implement this interface.
    """

    @abstractmethod
    def connect(self):
        """
        Establish a connection to the database.
        """
        pass

    @abstractmethod
    def disconnect(self):
        """
        Close the active database connection.
        """
        pass

    @abstractmethod
    def get_connection(self):
        """
        Return the active database connection object.
        """
        pass

    @abstractmethod
    def commit(self):
        """
        Commit the current transaction.
        """
        pass

    @abstractmethod
    def rollback(self):
        """
        Roll back the current transaction.
        """
        pass

    @abstractmethod
    def database_type(self) -> str:
        """
        Return the database engine type.
        """
        pass