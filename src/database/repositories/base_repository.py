from src.database.database_connection import DatabaseConnection


class BaseRepository:
    """
    Generic base repository for all database entities.

    Subclasses MUST define TABLE_NAME.
    """

    TABLE_NAME = None

    def __init__(self, connection: DatabaseConnection):

        self._connection = connection
        self._database_type = connection.database_type()

        if self.TABLE_NAME is None:
            raise ValueError(
                f"{self.__class__.__name__} must define TABLE_NAME."
            )

    # ---------------------------------------------------------

    def _prepare_query(self, query: str) -> str:
        """
        Convert SQL placeholders for the active database.
        """

        if self._database_type == "postgresql":
            return query.replace("?", "%s")

        return query

    # ---------------------------------------------------------

    def _get_cursor(self):
        """
        Return a database cursor.
        """

        return self._connection.get_connection().cursor()

    # ---------------------------------------------------------

    def execute(
        self,
        query: str,
        parameters: tuple = (),
    ):
        """
        Execute INSERT/UPDATE/DELETE statements.
        """

        query = self._prepare_query(query)

        cursor = self._get_cursor()

        try:

            cursor.execute(
                query,
                parameters,
            )

            self._connection.commit()

            return cursor

        except Exception:

            self._connection.rollback()

            raise

        finally:

            cursor.close()

    # ---------------------------------------------------------

    def insert_and_return_id(
        self,
        query: str,
        parameters: tuple = (),
    ) -> int:
        """
        Execute an INSERT statement and return the generated primary key.

        Supports both SQLite and PostgreSQL.
        """

        query = self._prepare_query(query)

        cursor = self._get_cursor()

        try:

            if self._database_type == "postgresql":

                query = query.rstrip().rstrip(";")
                query += " RETURNING id;"

            cursor.execute(
                query,
                parameters,
            )

            self._connection.commit()

            if self._database_type == "postgresql":

                row = cursor.fetchone()

                return row["id"]

            return cursor.lastrowid

        except Exception:

            self._connection.rollback()

            raise

        finally:

            cursor.close()

    # ---------------------------------------------------------

    def fetch_one(
        self,
        query: str,
        parameters: tuple = (),
    ) -> dict | None:

        query = self._prepare_query(query)

        cursor = self._get_cursor()

        try:

            cursor.execute(
                query,
                parameters,
            )

            row = cursor.fetchone()

            if row is None:
                return None

            return dict(row)

        finally:

            cursor.close()

    # ---------------------------------------------------------

    def fetch_all(
        self,
        query: str,
        parameters: tuple = (),
    ) -> list[dict]:

        query = self._prepare_query(query)

        cursor = self._get_cursor()

        try:

            cursor.execute(
                query,
                parameters,
            )

            return [
                dict(row)
                for row in cursor.fetchall()
            ]

        finally:

            cursor.close()

    # ---------------------------------------------------------

    def get_by_id(
        self,
        record_id: int,
    ) -> dict | None:

        query = f"""
        SELECT *
        FROM {self.TABLE_NAME}
        WHERE id = ?;
        """

        return self.fetch_one(
            query,
            (
                record_id,
            ),
        )

    # ---------------------------------------------------------

    def get_all(
        self,
    ) -> list[dict]:

        query = f"""
        SELECT *
        FROM {self.TABLE_NAME}
        ORDER BY id DESC;
        """

        return self.fetch_all(query)

    # ---------------------------------------------------------

    def delete(
        self,
        record_id: int,
    ):

        query = f"""
        DELETE
        FROM {self.TABLE_NAME}
        WHERE id = ?;
        """

        self.execute(
            query,
            (
                record_id,
            ),
        )