from src.database.database_connection import DatabaseConnection


class SchemaManager:
    """
    Creates and manages the AnalystGPT Enterprise database schema.
    Uses dialect-specific helpers to generate SQL for SQLite or PostgreSQL.
    """

    def __init__(self, database_connection: DatabaseConnection):
        self._database_connection = database_connection
        self._database_type = database_connection.database_type()

    # ---------------------------------------------------------

    def initialize_schema(self):
        """
        Create all required database tables.
        """

        supported = {
            "sqlite",
            "postgresql",
        }

        if self._database_type not in supported:
            raise ValueError(
                f"Unsupported database type: {self._database_type}"
            )

        self._create_schema()

    # ---------------------------------------------------------

    def _primary_key_sql(self) -> str:

        if self._database_type == "sqlite":
            return "INTEGER PRIMARY KEY AUTOINCREMENT"

        return "SERIAL PRIMARY KEY"

    # ---------------------------------------------------------

    def _timestamp_sql(self) -> str:

        if self._database_type == "sqlite":
            return "TEXT"

        return "TIMESTAMP WITH TIME ZONE"

    # ---------------------------------------------------------

    def _float_sql(self) -> str:

        if self._database_type == "sqlite":
            return "REAL"

        return "DOUBLE PRECISION"

    # ---------------------------------------------------------

    def _create_schema(self):

        connection = self._database_connection.get_connection()

        cursor = connection.cursor()

        try:

            pk = self._primary_key_sql()
            ts = self._timestamp_sql()
            float_type = self._float_sql()

            if self._database_type == "sqlite":
                cursor.execute(
                    "PRAGMA foreign_keys = ON;"
                )

            # -------------------------------------------------
            # Pipeline Runs
            # -------------------------------------------------

            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS pipeline_runs(
                    id {pk},
                    execution_time {ts} NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    status TEXT NOT NULL
                );
                """
            )

            # -------------------------------------------------
            # Datasets
            # -------------------------------------------------

            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS datasets(
                    id {pk},
                    pipeline_run_id INTEGER NOT NULL,
                    dataset_name TEXT NOT NULL,
                    row_count INTEGER NOT NULL,
                    column_count INTEGER NOT NULL,
                    FOREIGN KEY (pipeline_run_id)
                        REFERENCES pipeline_runs(id)
                        ON DELETE CASCADE
                );
                """
            )

            # -------------------------------------------------
            # Quality Reports
            # -------------------------------------------------

            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS quality_reports(
                    id {pk},
                    pipeline_run_id INTEGER NOT NULL,
                    completeness {float_type},
                    validity {float_type},
                    consistency {float_type},
                    uniqueness_score {float_type},
                    FOREIGN KEY (pipeline_run_id)
                        REFERENCES pipeline_runs(id)
                        ON DELETE CASCADE
                );
                """
            )

            # -------------------------------------------------
            # Analytics Reports
            # -------------------------------------------------

            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS analytics_reports(
                    id {pk},
                    pipeline_run_id INTEGER NOT NULL,
                    total_numeric_columns INTEGER,
                    total_categorical_columns INTEGER,
                    correlation_summary TEXT,
                    FOREIGN KEY (pipeline_run_id)
                        REFERENCES pipeline_runs(id)
                        ON DELETE CASCADE
                );
                """
            )

            # -------------------------------------------------
            # Reports
            # -------------------------------------------------

            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS reports(
                    id {pk},
                    pipeline_run_id INTEGER NOT NULL,
                    report_path TEXT NOT NULL,
                    generated_time {ts} NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (pipeline_run_id)
                        REFERENCES pipeline_runs(id)
                        ON DELETE CASCADE
                );
                """
            )

            self._database_connection.commit()

        except Exception:

            self._database_connection.rollback()

            raise

        finally:

            cursor.close()