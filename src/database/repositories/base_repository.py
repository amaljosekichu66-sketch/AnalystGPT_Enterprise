import sqlite3


class BaseRepository:
    """
    Generic base repository for all database entities.
    """

    TABLE_NAME = None

    def __init__(self, connection: sqlite3.Connection):
        self._connection = connection

    def execute(self, query: str, parameters: tuple = ()):
        cursor = self._connection.cursor()
        cursor.execute(query, parameters)
        self._connection.commit()
        return cursor

    def fetch_one(self, query: str, parameters: tuple = ()):
        cursor = self._connection.cursor()
        cursor.execute(query, parameters)

        row = cursor.fetchone()

        if row is None:
            return None

        return dict(row)

    def fetch_all(self, query: str, parameters: tuple = ()):
        cursor = self._connection.cursor()
        cursor.execute(query, parameters)

        return [dict(row) for row in cursor.fetchall()]

    def get_by_id(self, record_id: int):

        query = f"""
        SELECT *
        FROM {self.TABLE_NAME}
        WHERE id = ?;
        """

        return self.fetch_one(query, (record_id,))

    def get_all(self):

        query = f"""
        SELECT *
        FROM {self.TABLE_NAME}
        ORDER BY id DESC;
        """

        return self.fetch_all(query)

    def delete(self, record_id: int):

        query = f"""
        DELETE
        FROM {self.TABLE_NAME}
        WHERE id = ?;
        """

        self.execute(query, (record_id,))